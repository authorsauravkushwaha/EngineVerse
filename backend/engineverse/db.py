"""Database access layer.

Two drivers share one interface:

* ``sqlite3`` (standard library) - zero-dependency default, WAL mode, FTS5.
  Suitable for development and single-node deployments.
* PostgreSQL via any DB-API 2.0 driver (psycopg) - production. The DDL in
  ``db/postgres/schema.sql`` is hash-partitioned for the multi-hundred-million
  user case; see db/postgres/README.md.

All SQL in the application lives in this module or in ``repositories``-style
modules that call these helpers, so a driver swap touches one file.
"""
from __future__ import annotations

import os
import sqlite3
import threading
from contextlib import contextmanager
from datetime import date, datetime
from pathlib import Path
from typing import Any, Iterable, Iterator, Sequence

from .config import REPO_ROOT, get_settings

_local = threading.local()
_write_lock = threading.RLock()


class DatabaseError(RuntimeError):
    """Raised when the database layer cannot satisfy a request."""


def _adapt(value: Any) -> Any:
    if value is None or isinstance(value, (str, int, float, bytes)):
        return value
    if isinstance(value, bool):
        return 1 if value else 0
    if isinstance(value, (datetime,)):
        return int(value.timestamp() * 1000)
    if isinstance(value, date):
        return value.isoformat()
    if isinstance(value, (list, tuple, dict, set)):
        import json

        return json.dumps(value, default=str)
    return str(value)


def _params(values: Sequence[Any]) -> tuple:
    return tuple(_adapt(v) for v in values)


def _sqlite_connect(path: Path) -> sqlite3.Connection:
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(path, timeout=30.0, isolation_level=None, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode = WAL;")
    conn.execute("PRAGMA synchronous = NORMAL;")
    conn.execute("PRAGMA foreign_keys = ON;")
    conn.execute("PRAGMA busy_timeout = 10000;")
    conn.execute("PRAGMA temp_store = MEMORY;")
    conn.execute("PRAGMA cache_size = -32000;")
    conn.execute("PRAGMA mmap_size = 268435456;")
    return conn


class PostgresConnection:
    """Thin DB-API adapter so callers can use the same `?` placeholders."""

    def __init__(self, raw: Any) -> None:
        self._raw = raw

    @staticmethod
    def _convert(sql: str) -> str:
        out = []
        in_string = False
        for ch in sql:
            if ch == "'":
                in_string = not in_string
                out.append(ch)
            elif ch == "?" and not in_string:
                out.append("%s")
            else:
                out.append(ch)
        return "".join(out)

    def cursor(self):
        return _PgCursor(self._raw.cursor())

    def commit(self) -> None:
        self._raw.commit()

    def rollback(self) -> None:
        self._raw.rollback()

    def close(self) -> None:
        self._raw.close()


class _PgCursor:
    def __init__(self, cur: Any) -> None:
        self._cur = cur

    def execute(self, sql: str, params: Sequence[Any] = ()) -> "_PgCursor":
        self._cur.execute(PostgresConnection._convert(sql), tuple(params))
        return self

    @property
    def description(self):
        return self._cur.description

    @property
    def rowcount(self) -> int:
        return self._cur.rowcount

    def fetchone(self):
        row = self._cur.fetchone()
        return dict(zip([d[0] for d in self._cur.description], row)) if row else None

    def fetchall(self):
        cols = [d[0] for d in self._cur.description] if self._cur.description else []
        return [dict(zip(cols, r)) for r in self._cur.fetchall()]

    def close(self) -> None:
        self._cur.close()


def _pg_connect(url: str) -> PostgresConnection:
    try:
        import psycopg  # type: ignore
    except ImportError as exc:  # pragma: no cover - depends on deployment
        raise DatabaseError(
            "ENGINEVERSE_DB_URL is set but no PostgreSQL driver is installed. "
            "Run: pip install 'psycopg[binary]'"
        ) from exc
    return PostgresConnection(psycopg.connect(url, autocommit=False))


def connection() -> Any:
    """Returns a thread-local connection."""
    settings = get_settings()
    existing = getattr(_local, "conn", None)
    if existing is not None:
        return existing
    conn = _pg_connect(settings.db_url) if settings.uses_postgres else _sqlite_connect(settings.sqlite_path)
    _local.conn = conn
    return conn


def close_connection() -> None:
    conn = getattr(_local, "conn", None)
    if conn is not None:
        try:
            conn.close()
        finally:
            _local.conn = None


@contextmanager
def transaction() -> Iterator[None]:
    """Serialises writes (SQLite is single-writer) and rolls back on error."""
    with _write_lock:
        conn = connection()
        if isinstance(conn, sqlite3.Connection):
            conn.execute("BEGIN IMMEDIATE;")
        else:  # pragma: no cover - postgres path
            pass
        try:
            yield
        except Exception:
            try:
                conn.rollback()
            except Exception:
                pass
            raise
        else:
            if isinstance(conn, sqlite3.Connection):
                conn.execute("COMMIT;")
            else:  # pragma: no cover
                conn.commit()


def query(sql: str, *params: Any) -> list[dict]:
    cur = connection().cursor()
    try:
        cur.execute(sql, _params(params))
        rows = cur.fetchall()
        if rows and not isinstance(rows[0], dict):
            cols = [d[0] for d in cur.description]
            return [dict(zip(cols, r)) for r in rows]
        return list(rows or [])
    finally:
        cur.close()


def query_one(sql: str, *params: Any) -> dict | None:
    rows = query(sql, *params)
    return rows[0] if rows else None


def scalar(sql: str, *params: Any, default: Any = 0) -> Any:
    row = query_one(sql, *params)
    if not row:
        return default
    return next(iter(row.values()), default)


def execute(sql: str, *params: Any) -> int:
    with _write_lock:
        cur = connection().cursor()
        try:
            cur.execute(sql, _params(params))
            conn = connection()
            if isinstance(conn, sqlite3.Connection):
                return cur.rowcount if cur.rowcount is not None else 0
            conn.commit()
            return cur.rowcount
        finally:
            cur.close()


def execute_many(sql: str, rows: Iterable[Sequence[Any]]) -> None:
    with _write_lock:
        conn = connection()
        cur = conn.cursor()
        try:
            for row in rows:
                cur.execute(sql, _params(row))
            if not isinstance(conn, sqlite3.Connection):  # pragma: no cover
                conn.commit()
        finally:
            cur.close()


def executescript(script: str) -> None:
    """Runs a multi-statement SQL script (migrations, schema)."""
    conn = connection()
    if isinstance(conn, sqlite3.Connection):
        with _write_lock:
            conn.executescript(script)
    else:  # pragma: no cover - postgres path
        with _write_lock:
            for statement in split_sql(script):
                cur = conn.cursor()
                try:
                    cur.execute(statement)
                finally:
                    cur.close()
            conn.commit()


def split_sql(script: str) -> list[str]:
    """Splits SQL on `;` while respecting string literals and `--` comments."""
    statements: list[str] = []
    buffer: list[str] = []
    in_string = False
    i = 0
    while i < len(script):
        ch = script[i]
        if in_string:
            if ch == "'":
                if i + 1 < len(script) and script[i + 1] == "'":
                    buffer.append("''")
                    i += 2
                    continue
                in_string = False
            buffer.append(ch)
            i += 1
            continue
        if ch == "'":
            in_string = True
            buffer.append(ch)
            i += 1
            continue
        if ch == "-" and i + 1 < len(script) and script[i + 1] == "-":
            while i < len(script) and script[i] != "\n":
                i += 1
            continue
        if ch == ";":
            statement = "".join(buffer).strip()
            if statement:
                statements.append(statement)
            buffer = []
            i += 1
            continue
        buffer.append(ch)
        i += 1
    tail = "".join(buffer).strip()
    if tail:
        statements.append(tail)
    return statements


def migrate(schema_file: str | Path | None = None) -> int:
    """Applies the schema (idempotent: everything is CREATE ... IF NOT EXISTS)."""
    path = Path(schema_file) if schema_file else (REPO_ROOT / "db" / "schema.sql")
    if not path.exists():
        raise DatabaseError(f"schema file not found: {path}")
    statements = split_sql(path.read_text(encoding="utf-8"))
    for statement in statements:
        execute(statement)
    execute(
        "CREATE TABLE IF NOT EXISTS schema_meta (key TEXT PRIMARY KEY, value TEXT NOT NULL, updated_at INTEGER NOT NULL)"
    )
    # Columns added after the table was first created. Kept here so a database
    # that was seeded by an older build picks them up on the next migrate().
    ensure_column("certificates", "tier", "TEXT NOT NULL DEFAULT 'bronze'")
    import time

    execute(
        "INSERT INTO schema_meta (key, value, updated_at) VALUES ('schema_version', '1.0.0', ?) "
        "ON CONFLICT(key) DO UPDATE SET value = excluded.value, updated_at = excluded.updated_at",
        int(time.time() * 1000),
    )
    return len(statements)


def ensure_column(table: str, column: str, ddl: str) -> bool:
    """Adds a column if the table does not already have it. Returns True if added.

    The schema file is entirely ``CREATE TABLE IF NOT EXISTS``, so it can add
    tables on an existing database but never add a column to one. Without this,
    a new field means every deployment has to be rebuilt from scratch to pick
    it up. Idempotent on both engines: PostgreSQL supports the clause directly,
    SQLite does not, so it is checked against ``PRAGMA table_info`` first.
    """
    if get_settings().uses_postgres:  # pragma: no cover - exercised in the CI postgres job
        execute(f"ALTER TABLE {table} ADD COLUMN IF NOT EXISTS {column} {ddl}")
        return True
    existing = {row["name"] for row in query(f"PRAGMA table_info({table})")}
    if column in existing:
        return False
    execute(f"ALTER TABLE {table} ADD COLUMN {column} {ddl}")
    return True


def table_count(name: str) -> int:
    settings = get_settings()
    if settings.uses_postgres:  # pragma: no cover
        return int(scalar("SELECT count(*) AS c FROM " + name))
    row = query_one("SELECT count(*) AS c FROM sqlite_master WHERE type='table' AND name = ?", name)
    return int(row["c"]) if row else 0


def row_count(name: str) -> int:
    return int(scalar(f"SELECT count(*) AS c FROM {name}"))


def reset_database() -> None:
    """Deletes the local SQLite file. Never call this against production."""
    close_connection()
    settings = get_settings()
    if settings.uses_postgres:
        raise DatabaseError("refusing to reset a PostgreSQL database automatically")
    for suffix in ("", "-wal", "-shm"):
        target = Path(str(settings.sqlite_path) + suffix)
        if target.exists():
            os.unlink(target)
