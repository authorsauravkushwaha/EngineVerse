"""Append-only audit trail for security-relevant events (spec §71)."""
from __future__ import annotations

import json
from typing import Any

from .. import db
from .ids import now_ms, ulid

ACTIONS = (
    "auth.register", "auth.login", "auth.login_failed", "auth.logout",
    "auth.password_changed", "auth.session_revoked", "auth.role_changed",
    "content.created", "content.updated", "content.published", "content.deleted",
    "admin.config_changed", "community.deleted", "code.submitted", "admin.user_updated",
)


def record(
    action: str,
    *,
    actor_id: str | None = None,
    entity_type: str | None = None,
    entity_id: str | None = None,
    meta: dict[str, Any] | None = None,
    ip: str | None = None,
) -> None:
    """Best-effort: auditing must never break the request it records."""
    try:
        db.execute(
            "INSERT INTO audit_logs (id, actor_id, action, entity_type, entity_id, meta, ip, created_at) "
            "VALUES (?,?,?,?,?,?,?,?)",
            ulid(),
            actor_id,
            action,
            entity_type,
            entity_id,
            json.dumps(meta or {}, default=str)[:4000],
            (ip or "")[:64] or None,
            now_ms(),
        )
    except Exception:  # pragma: no cover - auditing is best-effort
        pass


def recent(limit: int = 50) -> list[dict]:
    return db.query(
        "SELECT a.*, u.username AS actor_username FROM audit_logs a "
        "LEFT JOIN users u ON u.id = a.actor_id ORDER BY a.created_at DESC LIMIT ?",
        limit,
    )
