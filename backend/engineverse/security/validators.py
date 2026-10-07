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
