"""CSRF protection (defence in depth).

Cookies are SameSite=Lax, *and* every state-changing request must send an
``X-CSRF-Token`` header whose value is an HMAC over the session id. An attacker
on another origin can neither read the header value nor forge it, because the
MAC key is ENGINEVERSE_SECRET.
"""
from __future__ import annotations

import hashlib
import hmac
import os

from starlette.requests import Request

from ..config import get_settings
from .sessions import CSRF_COOKIE

CSRF_HEADER = "x-csrf-token"
SAFE_METHODS = {"GET", "HEAD", "OPTIONS"}


def _key() -> bytes:
    return get_settings().effective_secret()


def issue_token(session_id: str) -> str:
    nonce = os.urandom(16).hex()
    mac = hmac.new(_key(), f"{session_id}:{nonce}".encode("utf-8"), hashlib.sha256).hexdigest()
    return f"{nonce}.{mac}"


def verify_token(token: str | None, session_id: str) -> bool:
    if not token or "." not in token:
        return False
    nonce, _, mac = token.partition(".")
    expected = hmac.new(_key(), f"{session_id}:{nonce}".encode("utf-8"), hashlib.sha256).hexdigest()
    return hmac.compare_digest(mac, expected)


def request_csrf(request: Request) -> str | None:
    return request.headers.get(CSRF_HEADER) or request.headers.get(CSRF_HEADER.upper())


def check(request: Request, session_id: str | None) -> bool:
    """True when the request is safe to process."""
    if request.method.upper() in SAFE_METHODS:
        return True
    if not session_id:
        # Anonymous mutations (register/login) are protected by rate limiting
        # plus SameSite=Lax; they cannot carry a session-bound token yet.
        return True
    return verify_token(request_csrf(request), session_id)


def cookie_options() -> dict:
    settings = get_settings()
    return {
        "httponly": False,  # the page must echo it back in a header
        "secure": settings.is_https or settings.cookie_secure,
        "samesite": "strict",
        "path": "/",
        "max_age": 30 * 86_400,
    }
