#!/usr/bin/env python3
"""One-shot release step for a production database.

Applies migrations with the connection in ``ENGINEVERSE_DB_URL`` (the bootstrap
role in ``deploy/docker-compose.yml``) and seeds the catalogue only when it is
empty. Never creates demo accounts. Never resets the database.

The web container does not run this. Compose runs it as the ``release`` service
before the web process starts. Re-running it does not overwrite CMS edits:
once ``subjects`` has rows, the catalogue is left alone. Refreshing seeded
content is an explicit ``python scripts/seed.py``, which upserts and therefore
overwrites CMS edits to those ids.

When ``APP_DB_PASSWORD`` is set and the connection is a superuser, this also
creates or updates the ``engineverse_app`` login and grants it DML only. The
official Postgres image does not re-run ``docker-entrypoint-initdb.d`` on an
existing data volume, so this is what repairs a volume created before that
role existed. The password is not printed.
"""
from __future__ import annotations

import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for path in (ROOT, os.path.join(ROOT, "backend"), os.path.join(ROOT, "scripts")):
    if path not in sys.path:
        sys.path.insert(0, path)

from engineverse import db  # noqa: E402
from engineverse.config import RUNTIME_DB_ROLE, get_settings  # noqa: E402
from engineverse.security.ids import now_ms  # noqa: E402

_PASSWORD_RE = re.compile(r"[A-Za-z0-9_-]{16,128}")


def _exec(sql: str, secret: str) -> None:
    try:
        db.execute(sql)
    except Exception as exc:
        text = str(exc)
        if secret and secret in text:
            raise RuntimeError("database role setup failed; the database error included a secret and was omitted") from None
        raise


def ensure_runtime_role() -> None:
    """Creates the DML-only login when this connection is allowed to."""
    password = os.environ.get("APP_DB_PASSWORD", "").strip()
    if not password or not get_settings().uses_postgres:
        return
    if not _PASSWORD_RE.fullmatch(password):
        raise SystemExit(
            "APP_DB_PASSWORD must be 16-128 characters from A-Za-z0-9_-. "
            "That keeps it out of shell expansion and out of the connection URL's reserved characters."
        )
    superuser = db.scalar(
        "SELECT rolsuper AS s FROM pg_roles WHERE rolname = current_user",
        default=False,
    )
    if not superuser:
        print("Connected role cannot create the runtime login; assuming it already exists.")
        return
    literal = "'" + password.replace("'", "''") + "'"
    exists = db.scalar(
        "SELECT 1 AS c FROM pg_roles WHERE rolname = ?",
        RUNTIME_DB_ROLE,
        default=None,
    )
    if exists:
        _exec(
            f"ALTER ROLE {RUNTIME_DB_ROLE} WITH LOGIN NOSUPERUSER NOCREATEDB NOCREATEROLE PASSWORD {literal}",
            password,
        )
    else:
        _exec(
            f"CREATE ROLE {RUNTIME_DB_ROLE} LOGIN NOSUPERUSER NOCREATEDB NOCREATEROLE PASSWORD {literal}",
            password,
        )
    dbname = str(db.scalar("SELECT current_database() AS d"))
    if not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", dbname):
        raise SystemExit("unexpected database name; refusing to interpolate it")
    _exec(f"GRANT CONNECT ON DATABASE {dbname} TO {RUNTIME_DB_ROLE}", password)
    _exec(f"GRANT USAGE ON SCHEMA public TO {RUNTIME_DB_ROLE}", password)
    _exec(
        f"GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO {RUNTIME_DB_ROLE}",
        password,
    )
    _exec(f"GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO {RUNTIME_DB_ROLE}", password)
    _exec(
        "ALTER DEFAULT PRIVILEGES IN SCHEMA public "
        f"GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO {RUNTIME_DB_ROLE}",
        password,
    )
    _exec(
        f"ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT USAGE, SELECT ON SEQUENCES TO {RUNTIME_DB_ROLE}",
        password,
    )
    _exec(f"REVOKE CREATE ON SCHEMA public FROM {RUNTIME_DB_ROLE}", password)
    print(f"Runtime role {RUNTIME_DB_ROLE} is present. Its password was not printed.")


def catalogue_present() -> bool:
    if not db.table_exists("subjects"):
        return False
    return int(db.scalar("SELECT count(*) AS c FROM subjects", default=0) or 0) > 0


def mark_catalogue() -> None:
    db.execute(
        "INSERT INTO site_config (key, value, updated_at) VALUES ('catalogue_seeded_at', ?, ?) "
        "ON CONFLICT(key) DO UPDATE SET value = excluded.value, updated_at = excluded.updated_at",
        "1",
        now_ms(),
    )


def main() -> int:
    settings = get_settings()
    if settings.is_production:
        problems = settings.production_problems()
        if problems:
            for item in problems:
                print(item, file=sys.stderr)
            return 1
    try:
        ensure_runtime_role()
        db.migrate()
        # Grants have to follow migrate(), which creates search_log and schema_meta.
        ensure_runtime_role()
    except (SystemExit, RuntimeError) as exc:
        if str(exc):
            print(exc, file=sys.stderr)
        return 1
    if catalogue_present():
        print(
            "Catalogue already present; not overwriting. "
            "python scripts/seed.py refreshes seeded rows and overwrites CMS edits to those ids."
        )
        mark_catalogue()
        return 0
    import seed

    seed.run(fresh=False, demo=False)
    mark_catalogue()
    print("Catalogue seeded. Demo accounts were not created.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
