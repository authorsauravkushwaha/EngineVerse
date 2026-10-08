"""Rate limiting (spec §71).

Two layers:

1. An in-process sliding window for high-frequency endpoints.
2. A **persisted** counter for authentication endpoints, so restarting the
   process cannot reset a brute-force attempt count.
"""
from __future__ import annotations

import threading
import time

from .. import db
from .ids import now_ms, ulid

_lock = threading.Lock()
_buckets: dict[str, tuple[int, float]] = {}
_last_sweep = 0.0


def _sweep() -> None:
    global _last_sweep
    now = time.monotonic()
    if now - _last_sweep < 60:
        return
    _last_sweep = now
    for key, (_, reset_at) in list(_buckets.items()):
        if reset_at <= now:
            _buckets.pop(key, None)


class RateLimitResult:
    __slots__ = ("allowed", "remaining", "retry_after", "limit")

    def __init__(self, allowed: bool, remaining: int, retry_after: int, limit: int) -> None:
        self.allowed = allowed
        self.remaining = remaining
        self.retry_after = retry_after
        self.limit = limit


def check(key: str, limit: int, window_seconds: int) -> RateLimitResult:
    with _lock:
        _sweep()
        now = time.monotonic()
        entry = _buckets.get(key)
        if entry is None or entry[1] <= now:
            _buckets[key] = (1, now + window_seconds)
            return RateLimitResult(True, limit - 1, window_seconds, limit)
        count, reset_at = entry
        count += 1
        _buckets[key] = (count, reset_at)
        if count > limit:
            return RateLimitResult(False, 0, max(1, int(reset_at - now)), limit)
        return RateLimitResult(True, limit - count, 0, limit)


def reset(key: str) -> None:
    with _lock:
        _buckets.pop(key, None)


# --------------------------------------------------------------------------
# Persisted authentication limiter
# --------------------------------------------------------------------------

AUTH_WINDOW_MS = 15 * 60_000
AUTH_MAX_PER_ACCOUNT = 8
AUTH_MAX_PER_IP = 32


def register_login_attempt(identifier: str, ip: str, success: bool, reason: str | None = None) -> None:
    db.execute(
        "INSERT INTO login_attempts (id, identifier, ip, success, reason, created_at) VALUES (?,?,?,?,?,?)",
        ulid(),
        (identifier or "").lower()[:254],
        (ip or "")[:64],
        1 if success else 0,
        reason,
        now_ms(),
    )
    if success:
        db.execute("DELETE FROM login_attempts WHERE identifier = ? AND success = 0", (identifier or "").lower())


def recent_failures(identifier: str, ip: str) -> tuple[int, int]:
    cutoff = now_ms() - AUTH_WINDOW_MS
    by_identifier = int(
        db.scalar(
            "SELECT count(*) AS c FROM login_attempts WHERE identifier = ? AND success = 0 AND created_at > ?",
            (identifier or "").lower(),
            cutoff,
        )
        or 0
    )
    by_ip = int(
        db.scalar(
            "SELECT count(*) AS c FROM login_attempts WHERE ip = ? AND success = 0 AND created_at > ?",
            (ip or "")[:64],
            cutoff,
        )
        or 0
    )
    return by_identifier, by_ip


def auth_blocked(identifier: str, ip: str) -> tuple[bool, int]:
    by_identifier, by_ip = recent_failures(identifier, ip)
    if by_identifier >= AUTH_MAX_PER_ACCOUNT or by_ip >= AUTH_MAX_PER_IP:
        cutoff = now_ms() - AUTH_WINDOW_MS
        oldest = int(
            db.scalar(
                "SELECT min(created_at) AS t FROM login_attempts "
                "WHERE success = 0 AND created_at > ? AND (identifier = ? OR ip = ?)",
                cutoff,
                (identifier or "").lower(),
                (ip or "")[:64],
                default=now_ms(),
            )
            or now_ms()
        )
        return True, max(1, int((oldest + AUTH_WINDOW_MS - now_ms()) / 1000))
    return False, 0


def prune_login_attempts() -> int:
    return db.execute("DELETE FROM login_attempts WHERE created_at < ?", now_ms() - 7 * 86_400_000)


LIMITS = {
    "login": (10, 300),
    "register": (5, 3600),
    "answer": (120, 60),
    "run_code": (30, 60),
    "submit_code": (30, 60),
    "search": (120, 60),
    "write": (120, 60),
    "ai": (30, 3600),
    "upload": (20, 3600),
}
