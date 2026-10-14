"""Data & BaaS teaching studio, with a genuinely isolated SELECT playground.

Provider SDKs are examples, not installed integrations. User SQL NEVER runs on
EngineVerse's connection. A bounded, public-column projection is copied into a
short-lived SQLite database (also when the application uses PostgreSQL). The
parser, SQLite authorizer, query_only flag, function allowlist and VM/size limits
are independent layers; neither private rows nor hidden judge cases exist there.
"""
from __future__ import annotations

import json
import sqlite3
import time
from dataclasses import dataclass
from functools import lru_cache
from typing import Any

import sqlglot
from sqlglot import exp

from . import db
from .config import REPO_ROOT


@dataclass(frozen=True)
class PublicTable:
    columns: tuple[str, ...]
    purpose: str
    where: str = ""


def table(columns: str, purpose: str, where: str = "") -> PublicTable:
    return PublicTable(tuple(columns.split()), purpose, where)


_PUBLISHED_TOPICS = "SELECT id FROM topics WHERE status='published'"
_PUBLISHED_NOTES = f"SELECT id FROM notes WHERE status='published' AND topic_id IN ({_PUBLISHED_TOPICS})"
_PUBLIC_QUESTIONS = f"SELECT id FROM questions WHERE is_active=1 AND (topic_id IS NULL OR topic_id IN ({_PUBLISHED_TOPICS}))"
_PUBLIC_PROJECTS = "SELECT id FROM projects WHERE status='published'"
_PUBLIC_PROBLEMS = "SELECT id FROM coding_problems WHERE is_premium=0"

# Deliberately exactly 26. Adding a table/column is an explicit privacy review,
# never a SELECT * over an evolving live schema. Author/reviewer ids, account
# state, credentials, payments and hidden coding_testcases are not projected.
PUBLIC_TABLES = {
    "branches": table("id slug name category description icon color order_index", "Engineering streams"),
    "semesters": table("id label year", "Semester labels"),
    "subjects": table("id slug name branch_id semester_id code credits difficulty description is_first_year status order_index", "Published subject catalogue", "status='published'"),
    "modules": table("id subject_id slug title summary order_index", "Subject modules", "subject_id IN (SELECT id FROM subjects WHERE status='published')"),
    "topics": table("id slug subject_id module_id title summary difficulty est_minutes prerequisites tags status accuracy_state order_index", "Published topics, including editorial review state", "status='published'"),
    "notes": table("id topic_id quality_level language status version", "Published reading depths", f"id IN ({_PUBLISHED_NOTES})"),
    "note_sections": table("id note_id kind title body callout order_index", "Published note passages", f"note_id IN ({_PUBLISHED_NOTES})"),
    "diagrams": table("id topic_id title kind caption source_ref", "Diagram metadata (not executable markup)", f"topic_id IN ({_PUBLISHED_TOPICS})"),
    "models_3d": table("id topic_id title caption order_index", "3D model metadata (not renderer payloads)", f"topic_id IN ({_PUBLISHED_TOPICS})"),
    "formulas": table("id slug subject_id topic_id category name latex variables meaning application constraints order_index", "Formula reference", f"topic_id IS NULL OR topic_id IN ({_PUBLISHED_TOPICS})"),
    "questions": table("id slug topic_id subject_id kind difficulty stem context tags is_active", "Active question prompts, without grading keys", f"id IN ({_PUBLIC_QUESTIONS})"),
    "question_options": table("id question_id label body order_index", "Question choices, without correctness or rationale", f"question_id IN ({_PUBLIC_QUESTIONS})"),
    "programming_languages": table("id slug name blurb runnable order_index", "Language paths"),
    "language_modules": table("id language_id slug title summary body example exercise stage order_index", "Programming lessons"),
    "language_stages": table("id language_id stage title summary order_index", "Language path stages"),
    "language_checkpoints": table("id language_id stage question_id order_index", "Checkpoint references", f"question_id IN ({_PUBLIC_QUESTIONS})"),
    "coding_problems": table("id slug title statement difficulty topics hints tags expected_time expected_space", "Public problem briefs; no judge tests", "is_premium=0"),
    "coding_problem_stubs": table("problem_id language_id stub signature", "Editor starter code", f"problem_id IN ({_PUBLIC_PROBLEMS})"),
    "coding_sheets": table("id slug title blurb level audience branch_id est_hours topic_focus status order_index", "Published practice sheets", "status='published'"),
    "coding_sheet_problems": table("sheet_id problem_id order_index note", "Practice-sheet membership", f"sheet_id IN (SELECT id FROM coding_sheets WHERE status='published') AND problem_id IN ({_PUBLIC_PROBLEMS})"),
    "projects": table("id slug title branch_id subject_id language_id difficulty category est_hours summary objective prerequisites architecture testing skills tech status order_index", "Published project briefs", "status='published'"),
    "project_steps": table("id project_id phase title body order_index", "Project phases", f"project_id IN ({_PUBLIC_PROJECTS})"),
    "project_resources": table("id project_id kind title url note", "Project resource metadata", f"project_id IN ({_PUBLIC_PROJECTS})"),
    "roadmaps": table("id slug title kind branch_id target_role summary description order_index", "Study and career paths"),
    "roadmap_nodes": table("id roadmap_id title summary ref_type ref_id is_required order_index", "Roadmap milestones"),
    "flashcards": table("id topic_id subject_id deck front hint difficulty", "Public revision prompts, not personal schedules", f"topic_id IS NULL OR topic_id IN ({_PUBLISHED_TOPICS})"),
}

SERVICES = (
    {
        "name": "Supabase", "model": "PostgreSQL + Auth + Storage + Realtime + Functions",
        "access": "Postgres row-level policies plus storage policies", "hosting": "Managed or self-hosted",
        "fit": "Relational engineering data and SQL-first applications", "docs": "https://supabase.com/docs",
        "sdk": "import { createClient } from '@supabase/supabase-js';\nconst db = createClient('https://PROJECT.supabase.co', 'PUBLIC_ANON_KEY');\nconst { data, error } = await db.from('topics')\n  .select('slug,title').eq('status', 'published').limit(10);\nif (error) throw error;\n// Public anon key only. Enforce RLS; never expose a service-role key.",
    },
    {
        "name": "Appwrite", "model": "Document data + Auth + Storage + Realtime + Functions",
        "access": "Collection/document permissions and server-side authorization", "hosting": "Managed or self-hosted",
        "fit": "Permissioned document apps with an integrated SDK", "docs": "https://appwrite.io/docs",
        "sdk": "import { Client, Databases, Query } from 'appwrite';\nconst client = new Client()\n  .setEndpoint('https://APPWRITE_HOST/v1').setProject('PROJECT_ID');\nconst db = new Databases(client);\nconst result = await db.listDocuments('CATALOGUE_DB', 'TOPICS', [\n  Query.equal('status', 'published'), Query.limit(10)\n]);\n// Configure public read permissions; project IDs are not server API keys.",
    },
    {
        "name": "Firebase", "model": "Firestore + Auth + Storage + Functions",
        "access": "Security Rules for client requests; separate server IAM", "hosting": "Managed; local emulators for development",
        "fit": "Client-centric realtime document applications", "docs": "https://firebase.google.com/docs",
        "sdk": "import { initializeApp } from 'firebase/app';\nimport { getFirestore, collection, query, where, limit, getDocs }\n  from 'firebase/firestore';\nconst app = initializeApp({ projectId: 'PROJECT_ID', apiKey: 'PUBLIC_CONFIG_KEY' });\nconst db = getFirestore(app);\nconst result = await getDocs(query(collection(db, 'topics'),\n  where('status', '==', 'published'), limit(10)));\n// Provision the full project config and Security Rules; config is not authorization.",
    },
    {
        "name": "PocketBase", "model": "SQLite + Auth + Files + Realtime",
        "access": "Collection API rules; privileged server access is separate", "hosting": "Self-hosted single-server service",
        "fit": "Small apps with a compact operational footprint", "docs": "https://pocketbase.io/docs/",
        "sdk": "import PocketBase from 'pocketbase';\nconst db = new PocketBase('https://POCKETBASE_HOST');\nconst result = await db.collection('topics').getList(1, 10, {\n  filter: 'status = \"published\"', fields: 'id,slug,title'\n});\n// Configure collection rules. Do not put superuser credentials in a client.",
    },
    {
        "name": "Nhost", "model": "PostgreSQL + GraphQL + Auth + Storage + Functions",
        "access": "Role-based GraphQL permissions and storage rules", "hosting": "Managed or self-hosted stack",
        "fit": "GraphQL-first relational applications", "docs": "https://docs.nhost.io/",
        "sdk": "import { NhostClient } from '@nhost/nhost-js';\nconst db = new NhostClient({ subdomain: 'PROJECT', region: 'REGION' });\nconst result = await db.graphql.request(`query {\n  topics(where: {status: {_eq: \"published\"}}, limit: 10) { slug title }\n}`);\n// Configure the public role. Admin secrets belong only on trusted servers.",
    },
)

POLICIES = (
    {"scope": "Published catalogue", "read": "Public when anonymous browsing is enabled", "write": "Staff-only validated CMS routes", "enforcement": "Explicit published-row and public-column projections"},
    {"scope": "Draft content and grading keys", "read": "Never exposed by the studio", "write": "Privileged content/assessment flow", "enforcement": "Not copied into the SQL sandbox"},
    {"scope": "Progress, bookmarks, personal notes", "read": "Owner session only in the real app", "write": "Owner session + CSRF", "enforcement": "Per-user route queries; no studio tables"},
    {"scope": "Sessions, OTP, credentials, payments", "read": "No studio access, including for staff", "write": "Dedicated trusted server flows", "enforcement": "No schema, rows or functions exposing these tables"},
    {"scope": "SQL playground", "read": "SELECT on 26 public projections", "write": "Denied for every caller", "enforcement": "Disposable database + parser + authorizer + bounded execution"},
)

EXAMPLES = (
    {"title": "Topics by subject", "sql": "SELECT s.name, COUNT(t.id) AS topics\nFROM subjects s JOIN topics t ON t.subject_id = s.id\nGROUP BY s.id, s.name ORDER BY topics DESC LIMIT 10"},
    {"title": "Index-aware topic lookup", "sql": "SELECT slug, title, difficulty FROM topics\nWHERE slug = 'arrays'"},
    {"title": "Project delivery budget", "sql": "SELECT slug, title, difficulty, est_hours FROM projects\nORDER BY est_hours, slug LIMIT 10"},
    {"title": "Practice mix", "sql": "SELECT kind, difficulty, COUNT(*) AS questions FROM questions\nGROUP BY kind, difficulty ORDER BY kind, difficulty"},
)

MAX_SQL_CHARS = 8000
MAX_RESULT_ROWS = 100
MAX_TABLE_ROWS = 20000
MAX_CELL_CHARS = 2000
MAX_VM_STEPS = 200000
MAX_QUERY_SECONDS = 1.5
_ALLOWED_ROOTS = (exp.Select, exp.Union, exp.Intersect, exp.Except)
_SAFE_FUNCTIONS = frozenset("abs avg coalesce count ifnull iif like glob length lower max min nullif round sum total upper substr substring trim ltrim rtrim replace instr date datetime strftime julianday unixepoch typeof json json_valid json_extract json_array_length group_concat row_number rank dense_rank lag lead first_value last_value".split())


class QueryError(ValueError):
    """A safe, user-facing SQL refusal."""


@lru_cache(maxsize=1)
def _declared_schema() -> dict[str, dict]:
    """Inspect local DDL only: no private live-database introspection."""
    with sqlite3.connect(":memory:") as conn:
        conn.row_factory = sqlite3.Row
        conn.executescript((REPO_ROOT / "db" / "schema.sql").read_text(encoding="utf-8"))
        result = {}
        for name, spec in PUBLIC_TABLES.items():
            columns = [dict(row) for row in conn.execute(f'PRAGMA table_info("{name}")') if row["name"] in spec.columns]
            if {col["name"] for col in columns} != set(spec.columns):
                raise RuntimeError(f"Studio public projection has drifted from the declared schema: {name}")
            foreign_keys = [dict(row) for row in conn.execute(f'PRAGMA foreign_key_list("{name}")')
                            if row["from"] in spec.columns and row["table"] in PUBLIC_TABLES
                            and row["to"] in PUBLIC_TABLES[row["table"]].columns]
            indexes = []
            for row in conn.execute(f'PRAGMA index_list("{name}")'):
                index_columns = [r["name"] for r in conn.execute(f'PRAGMA index_info("{row["name"]}")')]
                if index_columns and all(col in spec.columns for col in index_columns):
                    indexes.append({"columns": index_columns, "unique": bool(row["unique"])})
            result[name] = {"columns": columns, "foreign_keys": foreign_keys, "indexes": indexes}
        return result


def _projection_sql(name: str, *, count: bool = False) -> str:
    spec = PUBLIC_TABLES[name]
    projection = "COUNT(*) AS n" if count else ", ".join(f'"{column}"' for column in spec.columns)
    return f'SELECT {projection} FROM "{name}"' + (f" WHERE {spec.where}" if spec.where else "")


def schema() -> dict[str, Any]:
    declared = _declared_schema()
    tables = []
    for name, spec in PUBLIC_TABLES.items():
        metadata = declared[name]
        tables.append({
            "name": name, "purpose": spec.purpose,
            "row_count": int(db.scalar(_projection_sql(name, count=True))),
            "columns": [{"name": col["name"], "type": col["type"],
                         "nullable": not bool(col["notnull"] or col["pk"]), "primary_key": bool(col["pk"])}
                        for col in metadata["columns"]],
            "foreign_keys": [{"column": key["from"], "table": key["table"], "target": key["to"]}
                             for key in metadata["foreign_keys"]],
            "indexes": metadata["indexes"],
        })
    return {
        "tables": tables, "table_count": len(tables), "policies": list(POLICIES),
        "dialect": "SQLite (isolated public snapshot, including on PostgreSQL deployments)",
        "limits": {"sql_chars": MAX_SQL_CHARS, "result_rows": MAX_RESULT_ROWS,
                   "rows_per_table": MAX_TABLE_ROWS, "cell_chars": MAX_CELL_CHARS,
                   "vm_steps": MAX_VM_STEPS, "execution_seconds": MAX_QUERY_SECONDS},
        "disclosure": "Teaching snapshot, not a production SQL console. EngineVerse SQLite uses application authorization, not native Postgres RLS. The policy matrix describes access boundaries, not installed provider policies.",
    }


def _validate_sql(sql: str) -> set[str]:
    if not isinstance(sql, str) or not sql.strip() or len(sql) > MAX_SQL_CHARS:
        raise QueryError(f"Enter one SELECT query of at most {MAX_SQL_CHARS} characters.")
    try:
        statements = [node for node in sqlglot.parse(sql, read="sqlite") if node is not None]
    except (sqlglot.errors.SqlglotError, RecursionError, ValueError):
        raise QueryError("The SQL could not be parsed as a single SELECT query.") from None
    if len(statements) != 1 or not isinstance(statements[0], _ALLOWED_ROOTS):
        raise QueryError("Only one read-only SELECT query is allowed; DDL, DML and PRAGMA are blocked.")
    root = statements[0]
    forbidden = (exp.Insert, exp.Update, exp.Delete, exp.Create, exp.Drop, exp.Alter, exp.Command, exp.Into, exp.Lock)
    if any(isinstance(node, forbidden) for node in root.walk()):
        raise QueryError("Writes, SELECT INTO and locking statements are not allowed.")
    if any(not isinstance(cte.this, _ALLOWED_ROOTS) for cte in root.find_all(exp.CTE)):
        raise QueryError("Every CTE must also be a read-only SELECT.")
    aliases = {cte.alias.casefold() for cte in root.find_all(exp.CTE)}
    used = set()
    for node in root.find_all(exp.Table):
        if node.db or node.catalog or not isinstance(node.this, exp.Identifier):
            raise QueryError("Database qualifiers and table-valued functions are not allowed.")
        name = node.name.casefold()
        if name in PUBLIC_TABLES:
            used.add(name)
        elif name not in aliases:
            raise QueryError("Only the 26 public catalogue tables are queryable; private tables are blocked.")
    return used


def _value(value: Any) -> Any:
    if isinstance(value, (list, dict)):
        return json.dumps(value, ensure_ascii=False)
    if isinstance(value, (bytes, memoryview)):
        return "[binary omitted]"
    return value


def run_query(sql: str) -> dict[str, Any]:
    used = _validate_sql(sql)
    started = time.perf_counter()
    conn = sqlite3.connect(":memory:")
    try:
        declared = _declared_schema()
        snapshot_bytes = 0
        truncated_tables = []
        for name in sorted(used):
            spec = PUBLIC_TABLES[name]
            metadata = declared[name]
            definitions = ", ".join(f'"{col["name"]}" {col["type"]}' for col in metadata["columns"])
            conn.execute(f'CREATE TABLE "{name}" ({definitions})')
            rows = db.query(_projection_sql(name) + f" LIMIT {MAX_TABLE_ROWS + 1}")
            if len(rows) > MAX_TABLE_ROWS:
                truncated_tables.append(name)
            values = []
            for row in rows[:MAX_TABLE_ROWS]:
                record = tuple(_value(row[column]) for column in spec.columns)
                snapshot_bytes += sum(len(str(value).encode("utf-8")) for value in record if value is not None)
                if snapshot_bytes > 32 * 1024 * 1024:
                    raise QueryError("This snapshot is too large. Select fewer catalogue tables.")
                values.append(record)
            if values:
                columns = ", ".join(f'"{column}"' for column in spec.columns)
                placeholders = ",".join("?" for _ in spec.columns)
                conn.executemany(f'INSERT INTO "{name}" ({columns}) VALUES ({placeholders})', values)
            for index, item in enumerate(metadata["indexes"]):
                columns = ", ".join(f'"{column}"' for column in item["columns"])
                conn.execute(f'CREATE INDEX "studio_{name}_{index}" ON "{name}" ({columns})')
        conn.commit()
        conn.execute("PRAGMA query_only=ON")
        conn.setlimit(sqlite3.SQLITE_LIMIT_LENGTH, 1024 * 1024)
        conn.setlimit(sqlite3.SQLITE_LIMIT_SQL_LENGTH, MAX_SQL_CHARS + 32)
        conn.setlimit(sqlite3.SQLITE_LIMIT_COLUMN, 64)
        conn.setlimit(sqlite3.SQLITE_LIMIT_EXPR_DEPTH, 80)
        conn.setlimit(sqlite3.SQLITE_LIMIT_COMPOUND_SELECT, 10)
        conn.setlimit(sqlite3.SQLITE_LIMIT_ATTACHED, 0)

        def authorize(action, arg1, arg2, database, trigger):
            if action in (sqlite3.SQLITE_SELECT, sqlite3.SQLITE_RECURSIVE):
                return sqlite3.SQLITE_OK
            if action == sqlite3.SQLITE_READ and arg1 in used and (not arg2 or arg2 in PUBLIC_TABLES[arg1].columns):
                return sqlite3.SQLITE_OK
            if action == sqlite3.SQLITE_FUNCTION and (arg2 or "").casefold() in _SAFE_FUNCTIONS:
                return sqlite3.SQLITE_OK
            return sqlite3.SQLITE_DENY

        conn.set_authorizer(authorize)
        ticks = 0
        deadline = time.perf_counter() + MAX_QUERY_SECONDS

        def progress():
            nonlocal ticks
            ticks += 1000
            return int(ticks > MAX_VM_STEPS or time.perf_counter() > deadline)

        conn.set_progress_handler(progress, 1000)
        plan = [dict(zip(("id", "parent", "notused", "detail"), row))
                for row in conn.execute("EXPLAIN QUERY PLAN " + sql).fetchall()]
        cursor = conn.execute(sql)
        columns = [column[0] for column in cursor.description or ()]
        raw_rows = cursor.fetchmany(MAX_RESULT_ROWS + 1)
        clipped_cells = 0
        result_rows = []
        for row in raw_rows[:MAX_RESULT_ROWS]:
            cells = []
            for value in row:
                if isinstance(value, str) and len(value) > MAX_CELL_CHARS:
                    value = value[:MAX_CELL_CHARS] + "…"
                    clipped_cells += 1
                cells.append(value)
            result_rows.append(cells)
        return {
            "columns": columns, "rows": result_rows, "row_count": len(result_rows),
            "truncated": len(raw_rows) > MAX_RESULT_ROWS, "clipped_cells": clipped_cells,
            "snapshot_truncated_tables": truncated_tables,
            "plan": plan, "tables": sorted(used), "elapsed_ms": round((time.perf_counter() - started) * 1000, 2),
            "read_only": True, "disclosure": "Executed on a disposable public snapshot, never on the application database. Plan indexes are reproduced catalogue indexes, not production performance measurements.",
        }
    except sqlite3.Error as exc:
        if "interrupt" in str(exc).lower():
            raise QueryError("Query exceeded the execution budget. Add a filter or simplify the joins.") from None
        if "authoriz" in str(exc).lower():
            raise QueryError("This query uses a blocked column, table or function.") from None
        raise QueryError("Query refused by the sandbox: " + str(exc)[:180]) from None
    finally:
        conn.close()
