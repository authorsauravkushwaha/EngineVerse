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

import smtplib
import ssl
from dataclasses import dataclass
from email.message import EmailMessage
from urllib.parse import parse_qs, unquote, urlparse

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
    return bool(get_settings().smtp_url)


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
    if not settings.smtp_url:
        record("mail.not_configured", entity_type="subject", entity_id="mail",
               meta={"subject": message.subject})
        return False

    config = _parse(settings.smtp_url)
    try:
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
    except (smtplib.SMTPException, OSError) as exc:
        # Never log the body: a reset link in the logs is a credential.
        record("mail.failed", entity_type="subject", entity_id="mail",
               meta={"subject": message.subject, "error": exc.__class__.__name__})
        return False

    record("mail.sent", entity_type="subject", entity_id="mail",
           meta={"subject": message.subject, "to": message.to})
    return True


def send_password_reset(*, email: str, reset_url: str, minutes: int = 30) -> bool:
    return send(Message(
        to=email,
        subject="Reset your EngineVerse password",
        body=(
            "A password reset was requested for this address.\n\n"
            f"Reset your password: {reset_url}\n\n"
            f"The link expires in {minutes} minutes and works once. If you did not "
            "request this, ignore this message and your password will not change."
        ),
    ))
