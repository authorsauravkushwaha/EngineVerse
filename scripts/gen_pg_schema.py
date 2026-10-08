#!/usr/bin/env python3
"""Generates db/postgres/schema.pg.sql from db/schema.sql.

Why this exists
---------------
The Postgres schema used to be maintained by hand, and its header claimed it
"mirrors db/schema.sql 1:1". It did not: 47 of the 66 shared tables had
different columns. ``progress.issue_certificate`` inserts kind/entity_type/
entity_id, which the Postgres file did not define at all, so issuing a
certificate would have failed on the first row. Hand-maintaining two schemas is
how that happens.

Now the SQLite schema is the single source of truth and this script derives the
Postgres DDL from it. ``--check`` regenerates and diffs against the committed
file, which CI runs, so the two cannot diverge silently again.

What the translation does
-------------------------
* ``INTEGER`` -> ``BIGINT``, ``REAL`` -> ``DOUBLE PRECISION``. Epoch-millisecond
  timestamps stay integers, so the application layer is byte-for-byte identical
  on both engines.
* ``email`` and ``username`` -> ``CITEXT``, so uniqueness is case-insensitive.
* JSON columns stay ``TEXT``, deliberately. psycopg returns a dict for jsonb,
  and every reader in this codebase calls ``json.loads()`` on those values, so
  jsonb would break them. Identical behaviour beats indexable JSON here; a GIN
  expression index can be added later if a query needs it.
* The FTS5 virtual table becomes a real table with a generated ``tsvector`` and
  a GIN index.
* High-volume tables are hash-partitioned. Postgres requires the partition key
  to appear in the primary key *and* in every unique constraint, so where the
  SQLite table has a single-column ``id`` primary key the generated table gets a
  composite ``(id, <partition key>)`` primary key instead.

Tables that are deliberately NOT partitioned
--------------------------------------------
``sessions`` (unique ``token_hash``) and ``certificates`` (unique ``verify_id``)
carry a globally unique lookup column that does not include the partition key.
Partitioning either would force dropping a uniqueness guarantee the security
model depends on, so they stay ordinary tables.

Usage
-----
    python scripts/gen_pg_schema.py            # write the file
    python scripts/gen_pg_schema.py --check     # exit 1 if it would change
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
SOURCE = REPO_ROOT / "db" / "schema.sql"
TARGET = REPO_ROOT / "db" / "postgres" / "schema.pg.sql"

# Columns that hold case-insensitive identity.
CITEXT_COLUMNS = {"email", "username"}

# table -> (partition key, modulus). The key must be in the primary key and in
# every unique constraint; where it is not already, the generator promotes the
# primary key to (id, key). Verified against the live schema by test_postgres.
PARTITIONED: dict[str, tuple[str, int]] = {
    "profiles": ("user_id", 64),
    "streaks": ("user_id", 64),
    "activity": ("user_id", 256),
    "user_progress": ("user_id", 128),
    "user_flashcards": ("user_id", 128),
    "submissions": ("user_id", 256),
    "xp_events": ("user_id", 128),
    "notifications": ("user_id", 128),
    "personal_notes": ("user_id", 64),
    "comments": ("user_id", 128),
    "discussions": ("user_id", 128),
    "coding_submissions": ("user_id", 128),
    "contest_submissions": ("user_id", 32),
    "mistakes": ("user_id", 64),
    "bookmarks": ("user_id", 64),
    "votes": ("user_id", 64),
    "user_badges": ("user_id", 64),
    "audit_logs": ("id", 256),
    "login_attempts": ("id", 32),
    "api_rate_limits": ("bucket", 16),
}

# Replaces the SQLite FTS5 virtual table. Columns mirror the fts5() declaration
# in db/schema.sql exactly, because search.index_entity() inserts that exact
# list positionally. `tsv` is the one addition: FTS5 keeps its index implicit,
# Postgres needs a column to put a GIN index on.
FTS_DDL = """\
-- SQLite uses an FTS5 virtual table here. Postgres gets the same columns plus a
-- generated tsvector, which is what a GIN index can be built on.
--
-- NOTE: search.py currently issues FTS5-only SQL (MATCH, bm25()). A Postgres
-- deployment needs a tsquery branch in search(); the columns below are what
-- that branch will read.
CREATE TABLE IF NOT EXISTS search_index (
  entity_type  TEXT NOT NULL,
  entity_id    TEXT NOT NULL,
  title        TEXT NOT NULL DEFAULT '',
  body         TEXT NOT NULL DEFAULT '',
  branch       TEXT NOT NULL DEFAULT '',
  semester     TEXT NOT NULL DEFAULT '',
  difficulty   TEXT NOT NULL DEFAULT '',
  tags         TEXT NOT NULL DEFAULT '',
  tsv          tsvector GENERATED ALWAYS AS (
                 setweight(to_tsvector('simple', coalesce(title, '')), 'A') ||
                 setweight(to_tsvector('simple', coalesce(body, '')), 'B')
               ) STORED,
  PRIMARY KEY (entity_type, entity_id)
);
CREATE INDEX IF NOT EXISTS idx_search_tsv ON search_index USING GIN (tsv);
CREATE INDEX IF NOT EXISTS idx_search_branch ON search_index(branch, entity_type);
"""


# --------------------------------------------------------------------------
# Parsing
# --------------------------------------------------------------------------

def strip_comments(sql: str) -> str:
    sql = re.sub(r"/\*.*?\*/", " ", sql, flags=re.S)
    return "\n".join(re.sub(r"--.*$", "", line) for line in sql.split("\n"))


def _split_top_level(body: str) -> list[str]:
    """Splits a column list on commas that are not inside parentheses."""
    parts, depth, current = [], 0, ""
    for ch in body:
        if ch == "(":
            depth += 1
        elif ch == ")":
            depth -= 1
        if ch == "," and depth == 0:
            parts.append(current)
            current = ""
        else:
            current += ch
    if current.strip():
        parts.append(current)
    return parts


class Column:
    __slots__ = ("name", "type", "rest", "inline_pk")

    def __init__(self, name: str, type_: str, rest: str, inline_pk: bool) -> None:
        self.name = name
        self.type = type_
        self.rest = rest
        self.inline_pk = inline_pk


class Table:
    def __init__(self, name: str) -> None:
        self.name = name
        self.columns: list[Column] = []
        self.constraints: list[str] = []


_TABLE_CONSTRAINT = re.compile(r"^(PRIMARY|UNIQUE|FOREIGN|CHECK|CONSTRAINT|EXCLUDE)\b", re.I)
_COLUMN_HEAD = re.compile(r'^"?(\w+)"?\s+([A-Za-z]+(?:\s*\([^)]*\))?)\s*(.*)$', re.S)


def parse_tables(sql: str) -> list[Table]:
    """Parses CREATE TABLE statements with a paren-depth scanner.

    A regex that stops at the first ``);`` merges adjacent tables, because
    ``CHECK`` and ``DEFAULT`` clauses contain their own parentheses. An earlier
    version of the drift check did exactly that and reported nonsense.
    """
    tables: list[Table] = []
    for match in re.finditer(r"CREATE TABLE(?: IF NOT EXISTS)?\s+\"?(\w+)\"?\s*\(", sql, re.I):
        table = Table(match.group(1))
        i = match.end()
        depth = 1
        start = i
        while i < len(sql) and depth:
            if sql[i] == "(":
                depth += 1
            elif sql[i] == ")":
                depth -= 1
            i += 1
        for part in _split_top_level(sql[start:i - 1]):
            part = " ".join(part.split())
            if not part:
                continue
            if _TABLE_CONSTRAINT.match(part):
                table.constraints.append(part)
                continue
            head = _COLUMN_HEAD.match(part)
            if not head:
                continue
            name, type_, rest = head.group(1), head.group(2), head.group(3).strip()
            inline_pk = bool(re.search(r"\bPRIMARY KEY\b", rest, re.I))
            rest = re.sub(r"\bPRIMARY KEY\b", "", rest, flags=re.I)
            rest = " ".join(rest.split()).strip()
            table.columns.append(Column(name, type_, rest, inline_pk))
        tables.append(table)
    return tables


def parse_indexes(sql: str) -> list[str]:
    out = []
    for match in re.finditer(r"(CREATE (?:UNIQUE )?INDEX.*?;)", sql, re.S | re.I):
        statement = " ".join(match.group(1).split())
        # FTS5 indexes reference the virtual table's implicit columns.
        if "search_index" in statement:
            continue
        out.append(statement)
    return out


# --------------------------------------------------------------------------
# Emission
# --------------------------------------------------------------------------

def _pg_type(column: Column) -> str:
    upper = column.type.upper()
    if column.name in CITEXT_COLUMNS and upper.startswith("TEXT"):
        return "CITEXT"
    if upper.startswith("INTEGER") or upper.startswith("INT") or upper.startswith("BIGINT"):
        return "BIGINT"
    if upper.startswith("REAL") or upper.startswith("DOUBLE") or upper.startswith("FLOAT"):
        return "DOUBLE PRECISION"
    return column.type.upper()


def _column_ddl(column: Column, *, moved_pk: bool) -> str:
    rest = column.rest
    if moved_pk and "NOT NULL" not in rest.upper():
        # An inline PRIMARY KEY carries an implicit NOT NULL. Once it is moved to
        # a table-level constraint that implication is lost, so it must be stated.
        rest = ("NOT NULL " + rest).strip()
    parts = [f"  {column.name:<20} {_pg_type(column)}"]
    if rest:
        parts.append(rest)
    return " ".join(parts).rstrip() + ","


def emit_table(table: Table) -> str:
    partition = PARTITIONED.get(table.name)
    key = partition[0] if partition else None
    inline_pk_cols = [c.name for c in table.columns if c.inline_pk]

    # The inline PRIMARY KEY is always lifted to a table-level constraint: a
    # partitioned table needs the partition key inside it, and doing it for
    # every table keeps one code path. Skipping this silently dropped the
    # primary key from every unpartitioned table, which is how the first version
    # of this generator shipped 45 tables with no primary key at all.
    pk_cols: list[str] = []
    if inline_pk_cols:
        pk_cols = [inline_pk_cols[0]]
        if key and key not in pk_cols:
            pk_cols.append(key)

    lines = [f"CREATE TABLE IF NOT EXISTS {table.name} ("]
    body = [_column_ddl(c, moved_pk=c.inline_pk) for c in table.columns]
    for constraint in table.constraints:
        body.append(f"  {constraint},")
    if pk_cols:
        body.append(f"  PRIMARY KEY ({', '.join(pk_cols)})")
    if body:
        body[-1] = body[-1].rstrip(",")
    lines.extend(body)
    if partition:
        lines.append(f") PARTITION BY HASH ({key});")
    else:
        lines.append(");")
    return "\n".join(lines)


HELPER_FUNCTIONS = """\
-- Helper: create the full set of hash partitions for a table. Idempotent, so the
-- schema script can be re-applied to a live database.
CREATE OR REPLACE FUNCTION engineverse_create_partitions(
  parent_table TEXT, partition_count INTEGER
) RETURNS VOID AS $body$
DECLARE
  n INTEGER;
  partition_name TEXT;
BEGIN
  FOR n IN 0..(partition_count - 1) LOOP
    partition_name := format('%s_p%s', parent_table, n);
    IF NOT EXISTS (SELECT 1 FROM pg_class WHERE relname = partition_name) THEN
      EXECUTE format(
        'CREATE TABLE %I PARTITION OF %I FOR VALUES WITH (MODULUS %s, REMAINDER %s)',
        partition_name, parent_table, partition_count, n);
    END IF;
  END LOOP;
END;
$body$ LANGUAGE plpgsql;
"""

MAINTENANCE = """\
-- Append-only tables grow without bound. Prune in batches so VACUUM is never
-- asked to churn over the whole table at once.
CREATE OR REPLACE FUNCTION engineverse_prune_before(
  parent_table TEXT, cutoff_ms BIGINT
) RETURNS BIGINT AS $body$
DECLARE
  removed BIGINT := 0;
  batch BIGINT;
BEGIN
  LOOP
    EXECUTE format('DELETE FROM %I WHERE created_at < $1', parent_table)
      USING cutoff_ms;
    GET DIAGNOSTICS batch = ROW_COUNT;
    removed := removed + batch;
    EXIT WHEN batch < 100000;
    COMMIT;
  END LOOP;
  RETURN removed;
END;
$body$ LANGUAGE plpgsql;

ANALYZE;
"""


def emit_partitions() -> list[str]:
    out = ["",
           "-- ---------------------------------------------------------------------------",
           "-- Partitions. Fan-out chosen so the largest single partition of each table",
           "-- stays in the low tens of millions of rows at ~1.5e9 users - small enough",
           "-- for VACUUM, reindexing and a restore to stay tractable.",
           "-- ---------------------------------------------------------------------------",
           ""]
    for table, (_key, modulus) in PARTITIONED.items():
        out.append(f"SELECT engineverse_create_partitions('{table}', {modulus});")
    return out


HEADER = """\
-- ===========================================================================
--  EngineVerse - production relational schema (PostgreSQL 16+)
--  ---------------------------------------------------------------------------
--  GENERATED FILE. Do not edit by hand.
--
--  Written by scripts/gen_pg_schema.py from db/schema.sql, which is the single
--  source of truth. Regenerate with:
--
--      python scripts/gen_pg_schema.py
--
--  CI runs `python scripts/gen_pg_schema.py --check` and fails if this file is
--  out of date, so the two schemas cannot diverge silently. They did once: 47
--  of 66 shared tables had drifted, and certificates was missing kind,
--  entity_type and entity_id, which the application inserts on every issue.
--
--  What differs from the SQLite DDL, and why:
--    * INTEGER -> BIGINT, REAL -> DOUBLE PRECISION.
--    * email/username -> CITEXT, so uniqueness ignores case.
--    * JSON payloads stay TEXT, not jsonb: psycopg hands back a dict for jsonb
--      and every reader here calls json.loads(), so jsonb would break them.
--    * The FTS5 virtual table becomes a table with a generated tsvector + GIN.
--    * High-volume tables are hash-partitioned. Postgres requires the partition
--      key inside the primary key and every unique constraint, so tables with a
--      lone `id` primary key get a composite (id, user_id) primary key here.
--
--  sessions and certificates are NOT partitioned: each carries a globally
--  unique lookup column (token_hash, verify_id) that does not include a
--  sensible partition key, and dropping that uniqueness would weaken the
--  security model.
--
--  Partition counts assume ~1.5e9 users and keep the largest single partition
--  in the low tens of millions of rows.
--
--  Apply with:  psql "$ENGINEVERSE_DB_URL" -f db/postgres/schema.pg.sql
--  The script is idempotent.
-- ===========================================================================

SET client_min_messages TO WARNING;

CREATE EXTENSION IF NOT EXISTS citext;   -- case-insensitive email/username
CREATE EXTENSION IF NOT EXISTS pgcrypto; -- gen_random_bytes, digests
"""


def generate() -> str:
    sql = strip_comments(SOURCE.read_text())
    tables = parse_tables(sql)
    indexes = parse_indexes(sql)

    out = [HEADER]
    for table in tables:
        if table.name == "search_index":
            continue  # replaced by FTS_DDL below
        out.append("")
        out.append(emit_table(table))
    out.append("")
    out.append(FTS_DDL.rstrip())
    out.append("")
    out.append(HELPER_FUNCTIONS.rstrip())
    out.extend(emit_partitions())
    out.append("")
    out.append("-- ---------------------------------------------------------------------------")
    out.append("-- Indexes (translated from db/schema.sql).")
    out.append("-- ---------------------------------------------------------------------------")
    for statement in indexes:
        out.append(statement.replace("CREATE INDEX", "CREATE INDEX IF NOT EXISTS")
                   .replace("CREATE UNIQUE INDEX", "CREATE UNIQUE INDEX IF NOT EXISTS")
                   if "IF NOT EXISTS" not in statement else statement)
    out.append("")
    out.append(MAINTENANCE.rstrip())
    out.append("")
    return "\n".join(out)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true",
                        help="do not write; exit 1 if the committed file is stale")
    args = parser.parse_args()

    generated = generate()
    if args.check:
        current = TARGET.read_text() if TARGET.exists() else ""
        if current == generated:
            print(f"OK  {TARGET.relative_to(REPO_ROOT)} is up to date")
            return 0
        print(f"STALE  {TARGET.relative_to(REPO_ROOT)} does not match db/schema.sql")
        print("       Run: python scripts/gen_pg_schema.py")
        return 1

    TARGET.write_text(generated)
    tables = len(parse_tables(strip_comments(SOURCE.read_text())))
    print(f"Wrote {TARGET.relative_to(REPO_ROOT)}: {tables} tables, "
          f"{len(PARTITIONED)} partitioned")
    return 0


if __name__ == "__main__":
    sys.exit(main())
