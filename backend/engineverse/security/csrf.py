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


CSRF_FIELD = "csrf_token"


def request_csrf(request: Request) -> str | None:
    return request.headers.get(CSRF_HEADER) or request.headers.get(CSRF_HEADER.upper())


async def form_csrf(request: Request) -> str | None:
    """Reads the token from a form-encoded body.

    A plain HTML form submission cannot set a custom header, so every
    server-rendered form carries the token as a field instead. Without this the
    check would reject every non-JavaScript form POST.

    ``body()`` is awaited first on purpose: under Starlette's BaseHTTPMiddleware
    the request is a ``_CachedRequest``, and caching the body here is what lets
    the downstream handler read it again. Going straight to ``form()`` would
    consume the stream and leave the handler with an empty body.
    """
    try:
        await request.body()
        form = await request.form()
    except Exception:
        return None
    value = form.get(CSRF_FIELD)
    return value if isinstance(value, str) and value else None


def check(request: Request, session_id: str | None, token: str | None = None) -> bool:
    """True when the request is safe to process.

    ``token`` lets an async caller (the middleware) supply a token it read from
    the form body; falling back to the header keeps XHR clients working.
    """
    if request.method.upper() in SAFE_METHODS:
        return True
    if not session_id:
        # Anonymous mutations (register/login) are protected by rate limiting
        # plus SameSite=Lax; they cannot carry a session-bound token yet.
        return True
    return verify_token(token or request_csrf(request), session_id)


def cookie_options() -> dict:
    settings = get_settings()
    return {
        "httponly": False,  # the page must echo it back in a header
        "secure": settings.is_https or settings.cookie_secure,
        "samesite": "strict",
        "path": "/",
        "max_age": 30 * 86_400,
    }
