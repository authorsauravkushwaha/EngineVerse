"""Configurable branding (spec §1).

The product name, tagline and accent colour live in the ``site_config`` table,
so a white-label deployment is a data change rather than a code change.
"""
from __future__ import annotations

from . import db
from .security.ids import now_ms

DEFAULTS = {
    "brand_name": "EngineVerse",
    "tagline": "Learn Engineering. Practice Everything. Build the Real World.",
    "support_email": "hello@engineverse.dev",
    "accent": "#4f7cff",
    "accent_2": "#8b5cf6",
}

PUBLIC_KEYS = ("brand_name", "tagline", "support_email", "accent", "accent_2")


def get(key: str, default: str | None = None) -> str:
    value = db.scalar("SELECT value AS v FROM site_config WHERE key = ?", key, default=None)
    if value is None:
        return DEFAULTS.get(key, default or "")
    return str(value)


def brand() -> dict[str, str]:
    return {key: get(key) for key in PUBLIC_KEYS}


def set_many(values: dict[str, str]) -> None:
    ts = now_ms()
    for key, value in values.items():
        if not isinstance(value, str):
            continue
        db.execute(
            "INSERT INTO site_config (key, value, updated_at) VALUES (?,?,?) "
            "ON CONFLICT(key) DO UPDATE SET value = excluded.value, updated_at = excluded.updated_at",
            key,
            value[:400],
            ts,
        )


def all_config() -> dict[str, str]:
    rows = db.query("SELECT key, value FROM site_config ORDER BY key")
    return {row["key"]: row["value"] for row in rows}
