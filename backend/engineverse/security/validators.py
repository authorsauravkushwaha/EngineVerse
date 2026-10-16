"""Input validation.

Small, explicit validators instead of a schema library - every value that
crosses a trust boundary is checked here, and unknown keys are rejected rather
than silently ignored.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any, Callable

from .sanitize import sanitize_text

EMAIL_RE = re.compile(r"^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$")
USERNAME_RE = re.compile(r"^[a-z0-9](?:[a-z0-9._-]{1,22}[a-z0-9])?$")
SLUG_RE = re.compile(r"^[a-z0-9](?:[a-z0-9-]{0,94}[a-z0-9])?$")
PHONE_RE = re.compile(r"^\+[1-9][0-9]{6,14}$")
COUNTRY_CODE_RE = re.compile(r"^\+[1-9][0-9]{0,3}$")
_PHONE_ALLOWED = frozenset("0123456789 +-().")

COUNTRY_CODES: tuple[tuple[str, str], ...] = (
    ("+91", "India (+91)"),
    ("+1", "United States / Canada (+1)"),
    ("+44", "United Kingdom (+44)"),
    ("+61", "Australia (+61)"),
    ("+49", "Germany (+49)"),
    ("+33", "France (+33)"),
    ("+65", "Singapore (+65)"),
    ("+971", "UAE (+971)"),
    ("+81", "Japan (+81)"),
    ("+82", "South Korea (+82)"),
    ("+86", "China (+86)"),
    ("+55", "Brazil (+55)"),
    ("+27", "South Africa (+27)"),
    ("+234", "Nigeria (+234)"),
    ("+7", "Russia / Kazakhstan (+7)"),
)

RESERVED_USERNAMES = {
    "admin", "root", "engineverse", "api", "www", "mail", "support", "login",
    "register", "dashboard", "profile", "settings", "null", "undefined",
    "system", "about", "help", "search", "community", "projects", "practice",
}


class ValidationError(Exception):
    status_code = 422

    def __init__(self, message: str, fields: dict[str, str] | None = None) -> None:
        super().__init__(message)
        self.message = message
        self.fields = fields or {}


@dataclass
class Errors:
    items: dict[str, str] = field(default_factory=dict)

    def add(self, key: str, message: str) -> None:
        self.items.setdefault(key, message)

    @property
    def ok(self) -> bool:
        return not self.items

    def raise_if_any(self, message: str = "Please fix the highlighted fields.") -> None:
        if not self.ok:
            raise ValidationError(message, self.items)


def normalize_phone(value: Any) -> str:
    """Normalise display punctuation without inventing a country code.

    A plus is allowed anywhere in a pasted number because people commonly copy
    values such as ``(+44) ...``. It is moved to the front; all other allowed
    punctuation is discarded. Letters and every other character are refused,
    rather than silently stripped into a different number.
    """
    raw = str(value or "").strip()
    if not raw or any(char not in _PHONE_ALLOWED for char in raw):
        raise ValidationError("Enter a valid phone number.", {"phone": "Enter a valid phone number."})
    digits = "".join(char for char in raw if char.isdigit())
    if not digits:
        raise ValidationError("Enter a valid phone number.", {"phone": "Enter a valid phone number."})
    return ("+" if "+" in raw else "") + digits


def validate_phone(value: Any, key: str = "phone", errors: Errors | None = None) -> str:
    try:
        normalized = normalize_phone(value)
    except ValidationError as exc:
        message = "Enter a phone number in international format, for example +14155552671."
        if errors is not None:
            errors.add(key, message)
            return ""
        raise ValidationError(message, {key: message}) from exc
    if not PHONE_RE.fullmatch(normalized):
        message = "Enter a phone number in international format, for example +14155552671."
        if errors is not None:
            errors.add(key, message)
            return ""
        raise ValidationError(message, {key: message})
    return normalized


def normalize_phone_with_country_code(
    value: Any,
    country_code: Any = "+91",
    key: str = "phone",
    errors: Errors | None = None,
) -> str:
    """Combine a country dialing code (e.g. ``+91``, ``+1``) with a subscriber number.

    If ``value`` already starts with ``+``, validates it directly as E.164.
    Otherwise strips leading trunk ``0`` and prepends the validated country code.
    """
    raw = str(value or "").strip()
    if not raw:
        message = "Enter a mobile number with country code, for example +919876543210."
        if errors is not None:
            errors.add(key, message)
            return ""
        raise ValidationError(message, {key: message})
    if "+" in raw:
        return validate_phone(raw, key=key, errors=errors)
    cc_raw = str(country_code or "+91").strip().replace(" ", "")
    if cc_raw and not cc_raw.startswith("+"):
        cc_raw = "+" + cc_raw
    if not COUNTRY_CODE_RE.fullmatch(cc_raw):
        message = "Select a valid country code (for example +91, +1, +44)."
        if errors is not None:
            errors.add(key, message)
            return ""
        raise ValidationError(message, {key: message})
    if any(char not in _PHONE_ALLOWED for char in raw):
        message = "Enter a valid mobile number with country code."
        if errors is not None:
            errors.add(key, message)
            return ""
        raise ValidationError(message, {key: message})
    digits = "".join(char for char in raw if char.isdigit()).lstrip("0")
    combined = f"{cc_raw}{digits}"
    return validate_phone(combined, key=key, errors=errors)


def validate_email(value: Any, key: str = "email", errors: Errors | None = None) -> str:
    text = str(value or "").strip().lower()
    if not EMAIL_RE.match(text) or len(text) > 254:
        message = "Enter a valid email address."
        if errors:
            errors.add(key, message)
        else:
            raise ValidationError(message, {key: message})
        return ""
    return text


def validate_username(value: Any, key: str = "username", errors: Errors | None = None) -> str:
    text = str(value or "").strip().lower()
    if not USERNAME_RE.match(text):
        message = "Use 3-24 characters: letters, numbers, dot, dash or underscore."
    elif text in RESERVED_USERNAMES:
        message = "That username is reserved. Please choose another."
    else:
        message = ""
    if message:
        if errors:
            errors.add(key, message)
        else:
            raise ValidationError(message, {key: message})
        return ""
    return text


def validate_password(value: Any, key: str = "password", errors: Errors | None = None, min_length: int = 10) -> str:
    text = str(value or "")
    if len(text) < min_length:
        message = f"Use at least {min_length} characters."
    elif len(text) > 256:
        message = "Use at most 256 characters."
    else:
        message = ""
    if message:
        if errors:
            errors.add(key, message)
        else:
            raise ValidationError(message, {key: message})
    return text


def validate_slug(value: Any, key: str = "slug", errors: Errors | None = None) -> str:
    text = str(value or "").strip().lower()
    if not SLUG_RE.match(text):
        message = "Use lower-case letters, numbers and dashes."
        if errors:
            errors.add(key, message)
        else:
            raise ValidationError(message, {key: message})
        return ""
    return text


def validate_choice(value: Any, allowed: tuple[str, ...] | list[str], key: str, errors: Errors, default: str | None = None) -> str:
    text = str(value or default or "")
    if text not in allowed:
        if default is not None and not text:
            return default
        errors.add(key, f"Choose one of: {', '.join(allowed)}.")
        return default or ""
    return text


def validate_int(value: Any, key: str, errors: Errors, *, minimum: int, maximum: int, default: int = 0) -> int:
    try:
        number = int(value)
    except (TypeError, ValueError):
        errors.add(key, "Enter a whole number.")
        return default
    if number < minimum or number > maximum:
        errors.add(key, f"Enter a value between {minimum} and {maximum}.")
        return default
    return number


def validate_text(value: Any, key: str, errors: Errors, *, min_length: int = 0, max_length: int = 2000, required: bool = True) -> str:
    text = sanitize_text(str(value or ""), max_length)
    if required and len(text) < min_length:
        errors.add(key, f"Enter at least {min_length} characters.")
        return ""
    if len(text) > max_length:
        errors.add(key, f"Keep it under {max_length} characters.")
    return text


def require_fields(payload: dict, fields: tuple[str, ...]) -> Errors:
    errors = Errors()
    for name in fields:
        if not str(payload.get(name) or "").strip():
            errors.add(name, "This field is required.")
    return errors


def as_dict(payload: Any) -> dict:
    """Rejects non-object JSON bodies outright."""
    if not isinstance(payload, dict):
        raise ValidationError("Expected a JSON object.")
    return payload


Rule = Callable[[Any, Errors], Any]
