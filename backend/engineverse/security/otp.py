"""Compulsory delivered one-time codes.

Login codes are deliberately separate from authenticator (TOTP) codes.  The
plaintext exists only long enough to hand it to the configured first-party
mail or operator-run SMS transport; the challenge row contains a keyed hash
inside the same sealed payload format used by :mod:`totp`.
"""
from __future__ import annotations

import hashlib
import hmac
import secrets
from typing import Any

from .. import db
from ..config import get_settings
from . import totp

LOGIN_TTL = 300
PHONE_VERIFY_TTL = 600
# Descriptive aliases make the policy obvious to callers and tests.
LOGIN_TTL_SECONDS = LOGIN_TTL
PHONE_VERIFY_TTL_SECONDS = PHONE_VERIFY_TTL
MAX_ATTEMPTS = 5
LOGIN_PURPOSE = "login_otp"
PHONE_PURPOSE = "phone_verify"
SIGNUP_PURPOSE = "signup_verify"
RESET_PURPOSE = "password_reset"
PASSWORD_CHANGE_PURPOSE = "password_change"
OTP_TTL_SECONDS = 600
_BULLET = "•"


def generate_code() -> str:
    """Return an unbiased six-digit code, including values with leading zeroes."""
    return f"{secrets.randbelow(1_000_000):06d}"


def normalize_code(value: Any) -> str:
    """Accept six digits with human-friendly spaces, dashes or full stops.

    No other character is ignored.  In particular, accepting letters and then
    stripping them would turn a mistyped or malicious value into a different
    valid code.
    """
    if not isinstance(value, str):
        return ""
    digits: list[str] = []
    for char in value.strip():
        if char.isdigit() and char.isascii():
            digits.append(char)
        elif char in " -.":
            continue
        else:
            return ""
    result = "".join(digits)
    return result if len(result) == 6 else ""


def code_hash(code: str) -> str:
    """HMAC the canonical code with the current application secret."""
    canonical = normalize_code(code)
    if not canonical:
        return ""
    return hmac.new(
        get_settings().effective_secret(), canonical.encode("ascii"), hashlib.sha256
    ).hexdigest()


def mask_email(email: str) -> str:
    """Mask the local part while leaving the delivery domain recognisable."""
    value = (email or "").strip()
    local, separator, domain = value.partition("@")
    if not separator or not local:
        return _BULLET * max(4, len(value))
    if len(local) == 1:
        masked_local = local + _BULLET * 3
    elif len(local) == 2:
        masked_local = local[0] + _BULLET * 3
    else:
        masked_local = local[0] + _BULLET * max(2, len(local) - 2) + local[-1]
    return f"{masked_local}@{domain}"


def mask_phone(phone: str) -> str:
    """Keep only the final four digits visible and replace the rest by bullets."""
    value = (phone or "").strip()
    digits = "".join(char for char in value if char.isdigit())
    if not digits:
        return _BULLET * 6
    visible = digits[-4:]
    prefix = _BULLET * max(4, len(digits) - len(visible))
    return prefix + visible


def mask_destination(destination: str, channel: str = "email") -> str:
    """Mask an email or international phone number based on channel."""
    if channel == "phone" or (destination and str(destination).strip().startswith("+")):
        return mask_phone(destination)
    return mask_email(destination)


def _payload(
    code: str,
    *,
    channel: str,
    masked: str,
    choices: list[str] | tuple[str, ...] | None,
    extra: dict[str, Any] | None = None,
) -> str:
    body: dict[str, Any] = {
        "code_hash": code_hash(code),
        "attempts": 0,
        "channel": channel,
        "masked": masked,
        "choices": list(choices or [channel]),
    }
    if extra:
        body.update(extra)
    return totp.seal(body)


def issue_challenge(
    user_id: str,
    purpose: str,
    ttl_seconds: int,
    *,
    channel: str,
    masked: str,
    choices: list[str] | tuple[str, ...] | None = None,
    extra: dict[str, Any] | None = None,
) -> tuple[str, str]:
    """Replace any live challenge for this purpose and return token, code."""
    code = generate_code()
    token = totp.new_challenge(
        user_id,
        purpose,
        ttl_seconds,
        _payload(code, channel=channel, masked=masked, choices=choices, extra=extra),
    )
    return token, code


def issue_login_challenge(
    user_id: str,
    *,
    channel: str,
    masked: str,
    choices: list[str] | tuple[str, ...] | None = None,
) -> tuple[str, str]:
    return issue_challenge(
        user_id,
        LOGIN_PURPOSE,
        LOGIN_TTL,
        channel=channel,
        masked=masked,
        choices=choices,
    )


def issue_phone_challenge(
    user_id: str,
    *,
    masked: str,
    phone: str,
) -> tuple[str, str]:
    return issue_challenge(
        user_id,
        PHONE_PURPOSE,
        PHONE_VERIFY_TTL,
        channel="phone",
        masked=masked,
        choices=["phone"],
        extra={"phone": phone},
    )


def challenge_payload(token: str, purpose: str, user_id: str | None = None) -> dict | None:
    row = totp.active_challenge(token, purpose, user_id)
    if not row or not row.get("payload"):
        return None
    payload = totp.unseal(row["payload"])
    if not payload or not isinstance(payload.get("code_hash"), str):
        return None
    return payload


def describe_challenge(token: str, purpose: str, user_id: str | None = None) -> dict | None:
    """Return safe display metadata for a live challenge, never its code."""
    payload = challenge_payload(token, purpose, user_id)
    if payload is None:
        return None
    choices = payload.get("choices")
    if not isinstance(choices, list) or not all(isinstance(item, str) for item in choices):
        choices = [str(payload.get("channel") or "email")]
    attempts = payload.get("attempts", 0)
    try:
        attempts = max(0, min(MAX_ATTEMPTS, int(attempts)))
    except (TypeError, ValueError, OverflowError):
        attempts = 0
    return {
        "channel": str(payload.get("channel") or "email"),
        "masked": str(payload.get("masked") or ""),
        "choices": choices,
        "attempts_left": max(0, MAX_ATTEMPTS - attempts),
        "phone": payload.get("phone"),
    }


def kill_challenge(token: str, purpose: str, user_id: str | None = None) -> bool:
    row = totp.active_challenge(token, purpose, user_id)
    if not row:
        return False
    return totp.consume_challenge(token, purpose, str(row["user_id"]))


def check_code(token: str, purpose: str, user_id: str, submitted: str) -> dict[str, Any]:
    """Check one code and atomically update or consume the challenge.

    The result status is one of ``ok``, ``bad``, ``exhausted``, ``expired`` or
    ``replayed``.  No result includes the expected code or its digest.
    """
    row = totp.active_challenge(token, purpose, user_id)
    if not row:
        return {"status": "expired", "attempts_left": 0}
    stored_payload = row.get("payload")
    payload = totp.unseal(stored_payload) if stored_payload else None
    if not payload or not isinstance(payload.get("code_hash"), str):
        # A rotated root secret makes the seal unreadable. Treat it as dead,
        # rather than allowing a challenge to linger indefinitely.
        totp.consume_challenge(token, purpose, user_id)
        return {"status": "expired", "attempts_left": 0}

    submitted_hash = code_hash(submitted)
    if submitted_hash and hmac.compare_digest(submitted_hash, payload["code_hash"]):
        if totp.consume_challenge(token, purpose, user_id):
            return {"status": "ok", "attempts_left": MAX_ATTEMPTS, "payload": payload}
        return {"status": "replayed", "attempts_left": 0}

    try:
        attempts = int(payload.get("attempts", 0))
    except (TypeError, ValueError, OverflowError):
        attempts = 0
    attempts += 1
    if attempts >= MAX_ATTEMPTS:
        totp.consume_challenge(token, purpose, user_id)
        return {"status": "exhausted", "attempts_left": 0}

    payload["attempts"] = attempts
    updated = totp.update_challenge_payload(
        token,
        purpose,
        user_id,
        totp.seal(payload),
        expected_payload=stored_payload,
    )
    if not updated:
        return {"status": "replayed", "attempts_left": 0}
    return {"status": "bad", "attempts_left": MAX_ATTEMPTS - attempts, "payload": payload}

# Small compatibility spellings for callers that prefer verb-first helpers.
new_code = generate_code
_hash_code = code_hash
_code_hash = code_hash
