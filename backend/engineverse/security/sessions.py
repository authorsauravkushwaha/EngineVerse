"""Session management.

Cookie value: ``<sessionId>.<token>``

* ``token`` is 256 bits of CSPRNG output that is **never stored in clear**:
  only its SHA-256 digest is persisted, so a database dump cannot be replayed
  as a login.
* The cookie is HttpOnly, SameSite=Lax, Secure over https, Path=/.
* Absolute lifetime cap plus an idle timeout; ``last_seen_at`` is refreshed at
  most once every 5 minutes so the hot path stays cheap.
* Password or role changes revoke every other session for that user.
"""
from __future__ import annotations

import hashlib
import hmac
import os
import re
from dataclasses import dataclass

from starlette.requests import Request
from starlette.responses import Response

from .. import db
from ..config import get_settings
from .audit import record
from .ids import now_ms, ulid

SESSION_COOKIE = "ev_session"
CSRF_COOKIE = "ev_csrf"
SESSION_ID_RE = re.compile(r"^[0-9A-HJKMNP-TV-Z]{26}$")

_DAY = 86_400_000


@dataclass(frozen=True)
class Session:
    id: str
    user_id: str
    created_at: int
    expires_at: int
    last_seen_at: int
    ip: str | None
    user_agent: str | None


def _hash_token(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def create_session(user_id: str, *, ip: str | None = None, user_agent: str | None = None) -> tuple[str, str]:
    """Creates a session row and returns ``(cookie_value, session_id)``."""
    session_id = ulid()
    token = os.urandom(32).hex()
    created = now_ms()
    settings = get_settings()
    expires = created + settings.session_max_age_days * _DAY
    db.execute(
        "INSERT INTO sessions (id, token_hash, user_id, created_at, expires_at, last_seen_at, ip, user_agent) "
        "VALUES (?,?,?,?,?,?,?,?)",
        session_id,
        _hash_token(token),
        user_id,
        created,
        expires,
        created,
        (ip or "")[:64] or None,
        (user_agent or "")[:300] or None,
    )
    return f"{session_id}.{token}", session_id


def read_session(cookie_value: str | None) -> Session | None:
    if not cookie_value or "." not in cookie_value:
        return None
    session_id, _, token = cookie_value.partition(".")
    if not SESSION_ID_RE.match(session_id) or len(token) < 32:
        return None
    row = db.query_one(
        "SELECT id, user_id, token_hash, created_at, expires_at, last_seen_at, revoked_at, ip, user_agent "
        "FROM sessions WHERE id = ?",
        session_id,
    )
    if not row or row["revoked_at"]:
        return None
    if not hmac.compare_digest(_hash_token(token), row["token_hash"]):
        return None
    ts = now_ms()
    settings = get_settings()
    if row["expires_at"] <= ts:
        return None
    if ts - row["last_seen_at"] > settings.session_idle_days * _DAY:
        db.execute("UPDATE sessions SET revoked_at = ? WHERE id = ?", ts, session_id)
        return None
    if ts - row["last_seen_at"] > 5 * 60_000:
        db.execute("UPDATE sessions SET last_seen_at = ? WHERE id = ?", ts, session_id)
    return Session(
        id=row["id"],
        user_id=row["user_id"],
        created_at=row["created_at"],
        expires_at=row["expires_at"],
        last_seen_at=row["last_seen_at"],
        ip=row["ip"],
        user_agent=row["user_agent"],
    )


def revoke_session(session_id: str) -> None:
    db.execute("UPDATE sessions SET revoked_at = ? WHERE id = ? AND revoked_at IS NULL", now_ms(), session_id)


def revoke_all_sessions(user_id: str, *, except_session_id: str | None = None) -> int:
    rows = db.query(
        "SELECT id FROM sessions WHERE user_id = ? AND revoked_at IS NULL AND id <> ?",
        user_id,
        except_session_id or "",
    )
    ts = now_ms()
    for row in rows:
        db.execute("UPDATE sessions SET revoked_at = ? WHERE id = ?", ts, row["id"])
    return len(rows)


def prune_sessions() -> int:
    cutoff = now_ms() - 7 * _DAY
    return db.execute("DELETE FROM sessions WHERE expires_at < ? OR (revoked_at IS NOT NULL AND revoked_at < ?)", now_ms(), cutoff)


def list_user_sessions(user_id: str) -> list[dict]:
    return db.query(
        "SELECT id, created_at, expires_at, last_seen_at, ip, user_agent FROM sessions "
        "WHERE user_id = ? AND revoked_at IS NULL AND expires_at > ? ORDER BY last_seen_at DESC LIMIT 25",
        user_id,
        now_ms(),
    )


def cookie_options(max_age_seconds: int) -> dict:
    settings = get_settings()
    return {
        "httponly": True,
        "secure": settings.is_https or settings.cookie_secure,
        "samesite": "lax",
        "path": "/",
        "max_age": max_age_seconds,
    }


def attach_session_cookie(response: Response, cookie_value: str) -> None:
    settings = get_settings()
    response.set_cookie(SESSION_COOKIE, cookie_value, **cookie_options(settings.session_max_age_days * 86_400))


def clear_session_cookie(response: Response) -> None:
    response.delete_cookie(SESSION_COOKIE, path="/")


def session_from_request(request: Request) -> Session | None:
    return read_session(request.cookies.get(SESSION_COOKIE))


def audit_session_revoked(actor_id: str, ip: str | None = None) -> None:
    record("auth.session_revoked", actor_id=actor_id, ip=ip)
