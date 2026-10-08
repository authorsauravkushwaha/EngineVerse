"""Keeps db/postgres/schema.pg.sql in step with db/schema.sql.

The Postgres schema used to be maintained by hand and its header claimed it
mirrored the SQLite schema "1:1". It did not: 47 of 66 shared tables had
different columns, and ``certificates`` was missing kind, entity_type and
entity_id, which ``progress.issue_certificate`` inserts on every issue. Nothing
caught it because no test ever compared the two.

These tests compare them, and also check the Postgres partitioning rules the old
file violated: the partition key must appear in the primary key *and* in every
unique constraint, or CREATE TABLE fails outright.
"""
from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
SOURCE = REPO_ROOT / "db" / "schema.sql"
TARGET = REPO_ROOT / "db" / "postgres" / "schema.pg.sql"

sys.path.insert(0, str(REPO_ROOT))

from scripts import gen_pg_schema  # noqa: E402

#: FTS5's internal shadow tables, which have no Postgres counterpart.
FTS_SHADOW = re.compile(r"^search_index_(config|content|data|docsize|idx)$")

#: Created at runtime rather than by the schema file: schema_meta by
#: db.migrate(), search_log by search.ensure_tables().
RUNTIME_TABLES = {"schema_meta", "search_log"}

#: Deliberate Postgres-only additions: a generated tsvector needs a column to
#: put a GIN index on, which FTS5 keeps implicit.
ALLOWED_EXTRA_COLUMNS = {"search_index": {"tsv"}}


def _live_sqlite_schema() -> dict[str, list[str]]:
    from engineverse import db

    names = [
        row["name"]
        for row in db.query(
            "SELECT name FROM sqlite_master WHERE type = 'table' "
            "AND name NOT LIKE 'sqlite_%' ORDER BY name"
        )
    ]
    return {name: [c["name"] for c in db.query(f"PRAGMA table_info('{name}')")] for name in names}


def _pg_schema() -> dict[str, list[str]]:
    sql = gen_pg_schema.strip_comments(TARGET.read_text())
    return {t.name: [c.name for c in t.columns] for t in gen_pg_schema.parse_tables(sql)}


# ---------------------------------------------------------------------------
# The generated file must be current
# ---------------------------------------------------------------------------

class TestGeneratorIsCurrent:
    def test_check_mode_exits_zero(self):
        """CI runs this; a hand edit to the .pg.sql file makes it fail."""
        result = subprocess.run(
            [sys.executable, str(REPO_ROOT / "scripts" / "gen_pg_schema.py"), "--check"],
            capture_output=True, text=True, cwd=REPO_ROOT,
        )
        assert result.returncode == 0, (
            "db/postgres/schema.pg.sql is stale. Run: python scripts/gen_pg_schema.py\n"
            + result.stdout + result.stderr
        )

    def test_generating_is_deterministic(self):
        assert gen_pg_schema.generate() == TARGET.read_text()


# ---------------------------------------------------------------------------
# Column parity
# ---------------------------------------------------------------------------

class TestColumnParity:
    def test_every_sqlite_table_exists_in_postgres(self, seeded):
        live = _live_sqlite_schema()
        pg = _pg_schema()
        missing = sorted(
            name for name in live
            if name not in pg and not FTS_SHADOW.match(name) and name not in RUNTIME_TABLES
        )
        assert missing == [], f"tables absent from the Postgres schema: {missing}"

    def test_no_postgres_table_is_unbacked(self, seeded):
        live = _live_sqlite_schema()
        pg = _pg_schema()
        assert sorted(set(pg) - set(live)) == [], "Postgres defines a table SQLite does not"

    def test_every_column_matches(self, seeded):
        """The regression that this file exists for."""
        live = _live_sqlite_schema()
        pg = _pg_schema()
        problems = []
        for name, columns in sorted(live.items()):
            if name not in pg:
                continue
            allowed = ALLOWED_EXTRA_COLUMNS.get(name, set())
            missing = [c for c in columns if c not in pg[name]]
            extra = [c for c in pg[name] if c not in columns and c not in allowed]
            if missing or extra:
                problems.append(f"{name}: lacks {missing} extra {extra}")
        assert problems == [], "column drift:\n  " + "\n  ".join(problems)

    def test_column_order_matches(self, seeded):
        """Positional INSERTs are used in places, so order is part of the contract."""
        live = _live_sqlite_schema()
        pg = _pg_schema()
        for name, columns in sorted(live.items()):
            if name not in pg or name in ALLOWED_EXTRA_COLUMNS:
                continue
            assert pg[name] == columns, f"{name} column order differs"

    def test_certificates_carries_the_columns_the_app_inserts(self, seeded):
        """progress.issue_certificate inserts these on every certificate."""
        pg = _pg_schema()["certificates"]
        for column in ("kind", "entity_type", "entity_id", "verify_id", "tier"):
            assert column in pg, f"certificates.{column} missing from the Postgres schema"


# ---------------------------------------------------------------------------
# Partitioning legality
# ---------------------------------------------------------------------------

def _effective_partitions() -> dict[str, tuple[str, int]]:
    """The partitions the generator actually emits, not the ones it declares."""
    sql = gen_pg_schema.strip_comments(SOURCE.read_text())
    tables = [t for t in gen_pg_schema.parse_tables(sql) if t.name != "search_index"]
    partitions, _skipped = gen_pg_schema.effective_partitions(tables)
    return partitions


def _pg_constraints() -> dict[str, dict[str, list[list[str]]]]:
    """Extracts the primary key and unique column lists per Postgres table."""
    sql = gen_pg_schema.strip_comments(TARGET.read_text())
    out: dict[str, dict[str, list[list[str]]]] = {}
    for table in gen_pg_schema.parse_tables(sql):
        pk: list[list[str]] = []
        uniques: list[list[str]] = []
        for column in table.columns:
            if column.inline_pk:
                pk.append([column.name])
            if re.search(r"\bUNIQUE\b", column.rest, re.I):
                uniques.append([column.name])
        for constraint in table.constraints:
            match = re.match(r"^(PRIMARY KEY|UNIQUE)\s*\(([^)]*)\)", constraint, re.I)
            if not match:
                continue
            cols = [c.strip().strip('"') for c in match.group(2).split(",")]
            (pk if match.group(1).upper().startswith("PRIMARY") else uniques).append(cols)
        out[table.name] = {"pk": pk, "unique": uniques}
    return out


class TestPartitioning:
    def test_partition_key_is_in_the_primary_key(self):
        """Postgres rejects the CREATE TABLE otherwise."""
        constraints = _pg_constraints()
        for table, (key, _modulus) in _effective_partitions().items():
            pk = constraints[table]["pk"]
            assert pk, f"{table} is partitioned but declares no primary key"
            for pk_cols in pk:
                assert key in pk_cols, (
                    f"{table} is partitioned by {key} but its primary key {pk_cols} "
                    "does not include it - Postgres will refuse this table"
                )

    def test_partition_key_is_in_every_unique_constraint(self):
        """This is what made the old file's `sessions` partitioning invalid."""
        constraints = _pg_constraints()
        for table, (key, _modulus) in _effective_partitions().items():
            for unique_cols in constraints[table]["unique"]:
                assert key in unique_cols, (
                    f"{table} is partitioned by {key} but has a unique constraint "
                    f"on {unique_cols} without it - Postgres will refuse this table"
                )

    def test_unpartitioned_tables_are_the_ones_with_global_unique_lookups(self):
        """Documents why sessions and certificates stay ordinary tables."""
        for table in ("sessions", "certificates"):
            assert table not in gen_pg_schema.PARTITIONED, (
                f"{table} carries a globally unique lookup column and must not be partitioned"
            )

    def test_every_partitioned_table_actually_exists(self):
        pg = _pg_schema()
        assert set(gen_pg_schema.PARTITIONED) <= set(pg), "partition config names a missing table"


# ---------------------------------------------------------------------------
# Type translation
# ---------------------------------------------------------------------------

class TestTypeTranslation:
    def test_no_column_keeps_a_sqlite_type(self):
        """INTEGER and REAL must become BIGINT and DOUBLE PRECISION.

        Asserted over the parsed column list, not with a regex over the file:
        INTEGER is also valid inside a PL/pgSQL DECLARE block, and a textual
        scan flagged the partition helper's loop counter.
        """
        sql = gen_pg_schema.strip_comments(TARGET.read_text())
        offenders = []
        for table in gen_pg_schema.parse_tables(sql):
            for column in table.columns:
                if column.type.upper() in ("INTEGER", "INT", "REAL"):
                    offenders.append(f"{table.name}.{column.name} is {column.type}")
        assert offenders == [], "columns left on SQLite types:\n  " + "\n  ".join(offenders)

    def test_timestamps_are_bigint(self):
        """Epoch milliseconds need 64 bits; INTEGER would wrap in 2038."""
        sql = gen_pg_schema.strip_comments(TARGET.read_text())
        checked = 0
        for table in gen_pg_schema.parse_tables(sql):
            for column in table.columns:
                if column.name.endswith("_at") or column.name.endswith("_ms"):
                    assert column.type.upper() == "BIGINT", (
                        f"{table.name}.{column.name} is {column.type}, not BIGINT"
                    )
                    checked += 1
        assert checked > 50, f"only {checked} timestamp columns found - the check is not looking"

    def test_identity_columns_are_citext(self):
        ddl = TARGET.read_text()
        for column in ("email", "username"):
            assert re.search(rf"^\s+{column}\s+CITEXT", ddl, re.M), (
                f"{column} must be CITEXT so uniqueness ignores case"
            )

    def test_json_columns_stay_text(self):
        """psycopg returns a dict for jsonb; every reader calls json.loads()."""
        # Comments are stripped: the file's own header explains the choice and
        # contains the word, which made the first version of this test fail on a
        # file that was actually correct.
        ddl = gen_pg_schema.strip_comments(TARGET.read_text())
        assert "jsonb" not in ddl.lower(), (
            "a jsonb column would hand back a dict and break json.loads() in the app"
        )


@pytest.mark.parametrize("table,key", sorted(gen_pg_schema.PARTITIONED.items()))
def test_partition_counts_are_sane(table, key):
    modulus = gen_pg_schema.PARTITIONED[table][1]
    assert modulus >= 8, f"{table} has only {modulus} partitions"
    assert modulus & (modulus - 1) == 0, f"{table} modulus {modulus} is not a power of two"


# ---------------------------------------------------------------------------
# The DDL must actually be valid PostgreSQL
# ---------------------------------------------------------------------------

class TestGeneratedDdlParses:
    """Parsed with sqlglot rather than eyeballed.

    No PostgreSQL server is available in CI, so this is the strongest check
    obtainable here: it proves the file is syntactically valid PostgreSQL, not
    merely plausible. It would have caught the missing primary keys and the
    invalid partition declarations immediately.
    """

    def test_every_statement_parses_under_the_postgres_dialect(self):
        import sqlglot

        # PL/pgSQL DO blocks and CREATE EXTENSION are outside sqlglot's grammar;
        # both are exercised by the partitioning tests above.
        body = re.sub(r"DO \$\$.*?\$\$;", "", TARGET.read_text(), flags=re.S)
        body = re.sub(r"CREATE EXTENSION[^;]*;", "", body, flags=re.I)
        statements = [s for s in sqlglot.parse(body, read="postgres") if s is not None]
        assert len(statements) > 100, f"only {len(statements)} statements parsed"

    def test_it_round_trips_through_the_postgres_dialect(self):
        import sqlglot

        body = re.sub(r"DO \$\$.*?\$\$;", "", TARGET.read_text(), flags=re.S)
        body = re.sub(r"CREATE EXTENSION[^;]*;", "", body, flags=re.I)
        sqlglot.transpile(body, read="postgres", write="postgres")

    def test_the_sqlite_source_also_parses(self):
        """Guards the other direction: the generator's input must stay parseable."""
        import sqlglot

        body = re.sub(r"CREATE VIRTUAL TABLE.*?\);", "", SOURCE.read_text(), flags=re.S | re.I)
        statements = [s for s in sqlglot.parse(body, read="sqlite") if s is not None]
        assert len(statements) > 100, f"only {len(statements)} statements parsed"


class TestForeignKeyOrdering:
    """Postgres resolves REFERENCES during CREATE TABLE.

    SQLite checks foreign keys at DML time, so db/schema.sql can list tables in
    any order at all. Five of them point at a table defined later, which SQLite
    accepts and Postgres rejects outright - so a file generated in source order
    parses cleanly, passes sqlglot, and still will not apply.
    """

    def _order(self):
        import re

        src = TARGET.read_text()
        return [(m.group(1), set(re.findall(r"REFERENCES (\w+)\s*\(", m.group(2))))
                for m in re.finditer(r"CREATE TABLE IF NOT EXISTS (\w+)\s*\((.*?)\n\)", src, re.S)]

    def test_no_table_references_one_created_later(self):
        forward = []
        seen = set()
        for name, deps in self._order():
            for dep in deps:
                if dep not in seen and dep != name:
                    forward.append((name, dep))
            seen.add(name)
        assert forward == [], f"forward references Postgres will reject: {forward}"

    def test_the_source_schema_really_does_need_reordering(self):
        """Guards the test above against becoming vacuous.

        If db/schema.sql were ever reordered so every reference pointed
        backwards, the sort would be doing nothing and the test above would pass
        whether or not it worked. This asserts the source order is genuinely
        unusable on Postgres as it stands.
        """
        sql = gen_pg_schema.strip_comments(SOURCE.read_text())
        tables = [t for t in gen_pg_schema.parse_tables(sql) if t.name != "search_index"]
        by_name = {t.name for t in tables}

        forward = []
        seen: set[str] = set()
        for table in tables:  # source order, deliberately not the sorted one
            for dep in gen_pg_schema._dependencies(table):
                if dep in by_name and dep not in seen:
                    forward.append((table.name, dep))
            seen.add(table.name)
        assert forward, (
            "db/schema.sql is already in dependency order, so the topological "
            "sort in the generator is dead code and the test above proves nothing"
        )

    def test_every_table_is_emitted_exactly_once(self):
        import re

        names = re.findall(r"CREATE TABLE IF NOT EXISTS (\w+)", TARGET.read_text())
        assert len(names) == len(set(names)), "a table was emitted twice"


class TestForeignKeyTargetsPartitionedTables:
    """A foreign key must cover a partitioned table's *whole* key.

    Partitioning forces the partition column into the primary key, so a table
    partitioned by user_id has key (id, user_id). ``REFERENCES that_table(id)``
    then covers only part of the key and CREATE TABLE rejects it. This is what
    made the generated schema unappliable after the ordering was fixed.
    """

    def _keys_and_partitioned(self):
        gen_pg_schema.generate()  # applies the same eligibility filtering
        sql = gen_pg_schema.strip_comments(TARGET.read_text())
        tables = gen_pg_schema.parse_tables(sql)
        keys = {}
        for table in tables:
            pk = [c.name for c in table.columns if c.inline_pk]
            for constraint in table.constraints:
                match = re.match(r"PRIMARY KEY\s*\(([^)]*)\)", constraint, re.I)
                if match:
                    pk = [c.strip() for c in match.group(1).split(",")]
            keys[table.name] = set(pk)
        return tables, keys, set(gen_pg_schema.PARTITIONED)

    def test_no_foreign_key_points_at_part_of_a_partitioned_key(self):
        tables, keys, partitioned = self._keys_and_partitioned()
        bad = []
        for table in tables:
            text = " ".join([c.rest for c in table.columns] + table.constraints)
            for match in re.finditer(r"REFERENCES\s+(\w+)\s*\(([^)]*)\)", text, re.I):
                target = match.group(1)
                cols = {c.strip() for c in match.group(2).split(",")}
                if target in partitioned and cols != keys.get(target, set()):
                    bad.append((table.name, target, sorted(cols), sorted(keys[target])))
        assert bad == [], (
            "foreign keys referencing part of a partitioned table's key - "
            "Postgres will reject these:\n  " + "\n  ".join(map(str, bad))
        )

    def test_the_generator_derives_rather_than_hardcodes_eligibility(self):
        """Adding a foreign key must not silently produce a schema that won't apply."""
        from scripts.gen_pg_schema import unpartitionable

        sql = gen_pg_schema.strip_comments(SOURCE.read_text())
        tables = [t for t in gen_pg_schema.parse_tables(sql) if t.name != "search_index"]
        referenced = unpartitionable(tables)
        # comments self-references and references discussions; both are high volume
        # and both must therefore be given up.
        assert "discussions" in referenced, referenced
        assert "comments" in referenced, referenced
        assert referenced["comments"] == ["comments"], "self-references must count"
