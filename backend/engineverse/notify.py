"""Outbound mail, self-hosted.

Uses the standard library's ``smtplib`` and ``email`` packages, so there is no
third-party client and no hosted email service - consistent with everything else
here being self-hosted.

The important behaviour is what happens when nothing is configured, which is the
default. ``send()`` returns ``False`` and the message is not delivered. Callers
must handle that, and must not substitute showing the content to the user: a
password reset link rendered into an HTTP response is an account-takeover
endpoint, because anyone can POST the victim's address and read the link back.

Configure with::

    ENGINEVERSE_SMTP_URL=smtp://user:password@mail.internal:587/?tls=1
    ENGINEVERSE_MAIL_FROM="EngineVerse <no-reply@example.org>"
"""
from __future__ import annotations

import json
import smtplib
import ssl
from dataclasses import dataclass
from email.message import EmailMessage
from urllib import request as urllib_request
from urllib.parse import parse_qs, unquote, urlparse, urlunparse

from .config import get_settings
from .security.audit import record


@dataclass(frozen=True)
class Message:
    to: str
    subject: str
    body: str


class MailNotConfigured(RuntimeError):
    """Raised when a caller demands delivery but no transport is configured."""


def is_configured() -> bool:
    return bool(get_settings().smtp_url.strip())


def _parse(url: str) -> dict:
    parsed = urlparse(url)
    query = parse_qs(parsed.query)
    scheme = (parsed.scheme or "smtp").lower()
    return {
        "host": parsed.hostname or "localhost",
        "port": parsed.port or (465 if scheme == "smtps" else 587),
        "user": unquote(parsed.username) if parsed.username else "",
        "password": unquote(parsed.password) if parsed.password else "",
        "tls": scheme == "smtps" or query.get("tls", ["1"])[0].lower() in ("1", "true", "yes"),
        "starttls": query.get("starttls", ["1"])[0].lower() in ("1", "true", "yes"),
    }


def _build(message: Message) -> EmailMessage:
    settings = get_settings()
    mail = EmailMessage()
    mail["From"] = settings.mail_from
    mail["To"] = message.to
    mail["Subject"] = message.subject
    mail["Auto-Submitted"] = "auto-generated"
    mail.set_content(message.body)
    return mail


def send(message: Message, *, timeout: float = 10.0) -> bool:
    """Delivers a message. Returns False, without raising, if unconfigured.

    Failures are recorded and swallowed rather than propagated: a mail relay
    being down must not turn "request a password reset" into a 500, and the
    response has to look the same whether or not an account exists.
    """
    settings = get_settings()
    if not settings.smtp_url.strip():
        record("mail.not_configured", entity_type="subject", entity_id="mail",
               meta={"subject": message.subject})
        return False

    try:
        config = _parse(settings.smtp_url)
        context = ssl.create_default_context()
        if config["tls"] and not config["starttls"]:
            client = smtplib.SMTP_SSL(config["host"], config["port"], timeout=timeout,
                                      context=context)
        else:
            client = smtplib.SMTP(config["host"], config["port"], timeout=timeout)
        with client:
            if config["starttls"] and not config["tls"]:
                client.starttls(context=context)
            if config["user"]:
                client.login(config["user"], config["password"])
            client.send_message(_build(message))
    except (smtplib.SMTPException, OSError, ValueError) as exc:
        # Never log the body: a reset link in the logs is a credential.
        record("mail.failed", entity_type="subject", entity_id="mail",
               meta={"subject": message.subject, "error": exc.__class__.__name__})
        return False

    record("mail.sent", entity_type="subject", entity_id="mail",
           meta={"subject": message.subject})
    return True


def _site_name() -> str:
    from . import brand

    return brand.get("site_name") or "this site"


def send_password_reset(*, email: str, reset_url: str, minutes: int = 30) -> bool:
    name = _site_name()
    return send(Message(
        to=email,
        subject=f"Reset your {name} password",
        body=(
            f"A password reset was requested for this address on {name}.\n\n"
            f"Reset your password: {reset_url}\n\n"
            f"The link expires in {minutes} minutes and works once. If you did not "
            "request this, ignore this message and your password will not change."
        ),
    ))


def send_email_verification(*, email: str, verify_url: str, hours: int = 24) -> bool:
    name = _site_name()
    return send(Message(
        to=email,
        subject=f"Confirm your {name} email",
        body=(
            f"Confirm this address for {name}.\n\n"
            f"Confirm: {verify_url}\n\n"
            f"The link expires in {hours} hours and works once. It does not change "
            "your password. If you did not create this account, ignore this message."
        ),
    ))


def sms_is_configured() -> bool:
    return bool(get_settings().sms_url.strip())


def _sms_request_url(raw_url: str) -> tuple[str, str]:
    """Return a URL without userinfo and the password used as bearer secret."""
    parsed = urlparse(raw_url)
    password = unquote(parsed.password) if parsed.password is not None else ""
    # Do not put credentials back into the URL.  ``hostname`` also removes the
    # userinfo, but rebuilding from parsed pieces makes the guarantee explicit.
    hostname = parsed.hostname or ""
    if ":" in hostname and not hostname.startswith("["):
        hostname = f"[{hostname}]"
    if parsed.port:
        hostname = f"{hostname}:{parsed.port}"
    clean = urlunparse((
        parsed.scheme,
        hostname,
        parsed.path,
        parsed.params,
        parsed.query,
        parsed.fragment,
    ))
    return clean, password


def send_sms(to: str, body: str, *, timeout: float = 10.0) -> bool:
    """POST a phone message to the operator's JSON SMS gateway.

    The gateway is intentionally tiny: it receives ``{"to", "body"}`` and
    returns any successful 2xx response. Every failure is converted to False;
    callers must fail closed when a sign-in code could not be delivered. The
    message body and the credential-bearing URL are never written to the audit
    log.
    """
    settings = get_settings()
    raw_url = settings.sms_url.strip()
    if not raw_url:
        return False
    try:
        parsed = urlparse(raw_url)
        if not parsed.scheme or not parsed.hostname:
            return False
        if settings.is_production and parsed.scheme.lower() != "https":
            return False
        clean_url, bearer = _sms_request_url(raw_url)
        headers = {"Content-Type": "application/json", "Accept": "application/json"}
        if bearer:
            headers["Authorization"] = f"Bearer {bearer}"
        payload = json.dumps({"to": to, "body": body}).encode("utf-8")
        req = urllib_request.Request(clean_url, data=payload, headers=headers, method="POST")
        response = urllib_request.urlopen(req, timeout=timeout)
        try:
            status_value = getattr(response, "status", None)
            if status_value is None:
                status_value = response.getcode()
            status = int(status_value)
            if status < 200 or status >= 300:
                return False
        finally:
            close = getattr(response, "close", None)
            if callable(close):
                close()
    except Exception as exc:  # noqa: BLE001 - transport failures are fail-closed
        record("sms.failed", entity_type="transport", entity_id="sms",
               meta={"error": exc.__class__.__name__})
        return False
    record("sms.sent", entity_type="transport", entity_id="sms")
    return True


def send_login_otp(email: str, code: str, minutes: int = 5) -> bool:
    name = _site_name()
    return send(Message(
        to=email,
        subject=f"Your {name} sign-in code",
        body=(
            f"Your {name} sign-in code is {code}.\n\n"
            f"It expires in {minutes} minutes and works once. If you did not "
            "try to sign in, you can ignore this message."
        ),
    ))


def send_phone_otp(to: str, code: str, minutes: int = 5) -> bool:
    name = _site_name()
    return send_sms(
        to,
        f"Your {name} sign-in code is {code}. It expires in {minutes} minutes and works once.",
    )
