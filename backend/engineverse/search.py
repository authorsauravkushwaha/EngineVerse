"""Universal search (spec §8).

Backed by SQLite FTS5 (porter stemming + unicode folding) with bm25 column
weighting so titles outrank body text. Queries degrade gracefully:

  1. AND of prefix-expanded tokens  -> precise
  2. OR  of prefix-expanded tokens  -> recall
  3. LIKE substring scan            -> fallback
  4. Levenshtein "did you mean"     -> typo correction

The generated Postgres schema (db/postgres/schema.pg.sql) gives search_index the
same columns plus a stored ``tsvector`` with a GIN index, so the *data* migrates
unchanged. The SQL below does not: ``MATCH`` and ``bm25()`` are FTS5-only, so a
Postgres deployment needs a ``tsquery``/``ts_rank`` branch in ``search()`` before
this module will run there. Page code is unaffected either way.
"""
from __future__ import annotations

import hashlib
import json
import re
from typing import Any

from . import db

ENTITY_URLS = {
    "note": "/topics/{id}",   # a note is read on its topic's page
    "topic": "/topics/{id}",
    "subject": "/subjects/{id}",
    # These four point at one item inside a collection page that paginates, so
    # they filter rather than fragment. A URL fragment cannot survive that: the
    # browser sends only the path, and with 400 videos, 395 books, 544 off-site
    # resources and 365 formulas the item is nearly always on a later page than
    # the one that renders - the reader landed at the top of a 24-item page and
    # had to hunt. The formulas page was worse, truncating at 300 of 365, so 65
    # formulas had no anchor anywhere. ?slug= narrows the page to the one row.
    "formula": "/formulas?slug={id}",
    # The bank is filtered, not addressed by path: there is no page at
    # /practice/questions/{slug} (only a JSON route under /api), so a question
    # search result used to link to a 404.
    "question": "/practice/questions?slug={id}",
    "problem": "/practice/problems/{id}",
    "project": "/projects/{id}",
    "video": "/videos?slug={id}",
    "book": "/books?slug={id}",
    # /resources is the site index; the off-site collection these rows belong to
    # lives at /resources/offsite, so this used to land on a page that does not
    # list the resource at all.
    "resource": "/resources/offsite?slug={id}",
    "roadmap": "/roadmaps/{id}",
    "language": "/programming/{id}",
    "branch": "/branches/{id}",
    "module": "/programming/{id}#{module}",
    "flashcard": "/flashcards?card={id}",
    "user": "/portfolio/{id}",
}


def url_for(entity_type: str, entity_id: str) -> str:
    if entity_type == "module":
        language_slug, separator, module_slug = entity_id.partition("::")
        if separator:
            from urllib.parse import quote
            return f"/programming/{quote(language_slug, safe='-')}#{quote(module_slug, safe='-')}"
        return "/programming"
    template = ENTITY_URLS.get(entity_type, "/explore")
    if entity_type == "flashcard":
        from urllib.parse import quote
        return template.format(id=quote(entity_id, safe="-"))
    return template.format(id=entity_id)


# Ceiling on indexed prose. Sized from measurement, not taste: merging a topic's
# published notes produces a median of 5.4k characters and a maximum of 11.3k, so
# the 4000 this used to be truncated 47 of 48 topics and kept 71% of the text.
# The mastery pass then gave the deepest topic a second worked check and authored
# practice prompts, which moved the measured median to 12.5k and the maximum to
# 19.7k; the cap moves with it so no seeded note is cut off mid-sentence.
MAX_BODY_CHARS = 24000


def index_entity(
    *, entity_type: str, entity_id: str, title: str, body: str = "",
    branch: str = "", semester: str = "", difficulty: str = "", tags: str = "",
    body_limit: int = MAX_BODY_CHARS,
) -> None:
    db.execute("DELETE FROM search_index WHERE entity_type = ? AND entity_id = ?", entity_type, entity_id)
    db.execute(
        "INSERT INTO search_index (entity_type,entity_id,title,body,branch,semester,difficulty,tags) "
        "VALUES (?,?,?,?,?,?,?,?)",
        entity_type, entity_id, title[:500], body[:body_limit], branch or "",
        semester or "", difficulty or "", tags or "",
    )


def remove_entity(entity_type: str, entity_id: str) -> None:
    db.execute("DELETE FROM search_index WHERE entity_type = ? AND entity_id = ?", entity_type, entity_id)


def _tokens(query: str) -> list[str]:
    cleaned = re.sub(r"[^\w\s+#.-]", " ", query.lower(), flags=re.UNICODE)
    return [t.strip("-.") for t in cleaned.split() if len(t.strip("-.")) > 1][:8]


def _match(tokens: list[str], operator: str) -> str:
    return f" {operator} ".join('"' + t.replace('"', "") + '"*' for t in tokens)


def _fts(expression: str, options: dict[str, Any], limit: int) -> list[dict]:
    clauses: list[str] = []
    args: list[Any] = [expression]
    for column, key in (("entity_type", "type"), ("branch", "branch"), ("difficulty", "difficulty")):
        value = options.get(key)
        if value and value != "all":
            clauses.append(f"{column} = ?")
            args.append(value)
    if options.get("semester"):
        clauses.append("semester = ?")
        args.append(str(options["semester"]))
    where = f" AND {' AND '.join(clauses)}" if clauses else ""
    args.append(limit)
    return db.query(
        "SELECT entity_type, entity_id, title, body, branch, semester, difficulty, "
        "bm25(search_index, 0.0, 0.0, 8.0, 1.0, 0.5, 0.5, 0.5, 0.5) AS score "
        f"FROM search_index WHERE search_index MATCH ?{where} ORDER BY score LIMIT ?",
        *args,
    )


def _like(tokens: list[str], options: dict[str, Any], limit: int) -> list[dict]:
    pattern = "%" + "%".join(tokens) + "%"
    clauses: list[str] = ["(title LIKE ? OR body LIKE ?)"]
    args: list[Any] = [pattern, pattern]
    if options.get("type") and options["type"] != "all":
        clauses.append("entity_type = ?")
        args.append(options["type"])
    if options.get("branch"):
        clauses.append("branch = ?")
        args.append(options["branch"])
    args.append(limit)
    return db.query(
        f"SELECT entity_type, entity_id, title, body, branch, semester, difficulty, 0 AS score "
        f"FROM search_index WHERE {' AND '.join(clauses)} LIMIT ?",
        *args,
    )


def _snippet(body: str, tokens: list[str]) -> str:
    if not body:
        return ""
    lowered = body.lower()
    position = -1
    for token in tokens:
        found = lowered.find(token)
        if found >= 0:
            position = found
            break
    start = max(0, position - 60) if position >= 0 else 0
    chunk = re.sub(r"\s+", " ", body[start:start + 220]).strip()
    return ("…" if start > 0 else "") + chunk + ("…" if start + 220 < len(body) else "")


def levenshtein(a: str, b: str, maximum: int = 3) -> int:
    if abs(len(a) - len(b)) > maximum:
        return maximum + 1
    previous = list(range(len(b) + 1))
    for i, char_a in enumerate(a, start=1):
        current = [i]
        for j, char_b in enumerate(b, start=1):
            current.append(min(current[j - 1] + 1, previous[j] + 1, previous[j - 1] + (char_a != char_b)))
        previous = current
    return previous[-1]


def did_you_mean(query: str) -> str | None:
    term = query.strip().lower()
    if not (3 <= len(term) <= 40):
        return None
    maximum = 1 if len(term) <= 6 else (2 if len(term) <= 12 else 3)
    best: tuple[int, str] | None = None
    for row in db.query("SELECT title FROM search_index LIMIT 5000"):
        title = row["title"].lower()
        if title == term:
            continue
        if term in title:
            return row["title"]
        distance = levenshtein(term, title, maximum)
        if distance <= maximum and (best is None or distance < best[0]):
            best = (distance, row["title"])
    return best[1] if best else None


def search(query: str, **options: Any) -> dict[str, Any]:
    tokens = _tokens(query)
    if not tokens:
        return {"results": [], "total": 0, "suggestion": None}
    limit = int(options.get("limit") or 20)

    rows: list[dict] = []
    if len(tokens) > 1:
        try:
            rows = _fts(_match(tokens, "AND"), options, limit)
        except Exception:
            rows = []
    if not rows:
        try:
            rows = _fts(_match(tokens, "OR"), options, limit)
        except Exception:
            rows = []
    if not rows:
        rows = _like(tokens, options, limit)

    results = [
        {
            "type": row["entity_type"],
            "id": row["entity_id"],
            "title": row["title"],
            "snippet": _snippet(row["body"] or "", tokens),
            "url": url_for(row["entity_type"], row["entity_id"]),
            "branch": row["branch"] or None,
            "semester": row["semester"] or None,
            "difficulty": row["difficulty"] or None,
        }
        for row in rows
    ]
    suggestion = did_you_mean(query) if not results else None
    log_search(query, len(results))
    return {"results": results, "total": len(results), "suggestion": suggestion}


def grouped(query: str, **options: Any) -> dict[str, list[dict]]:
    """Results bucketed by entity type - powers the categorised search UI."""
    payload = search(query, limit=int(options.get("limit") or 40), **{k: v for k, v in options.items() if k != "limit"})
    buckets: dict[str, list[dict]] = {}
    for result in payload["results"]:
        buckets.setdefault(result["type"], []).append(result)
    payload["groups"] = buckets
    return payload


def ensure_log_table() -> None:
    # created_at is an epoch-millisecond value, so its type has to follow the
    # backend: this table is created inline and never passes through the schema
    # generator that widens INTEGER to BIGINT. See db.epoch_ms_column_type.
    db.execute(
        "CREATE TABLE IF NOT EXISTS search_log (id TEXT PRIMARY KEY, query TEXT NOT NULL, "
        f"results INTEGER NOT NULL, created_at {db.epoch_ms_column_type()} NOT NULL)"
    )
    db.execute("CREATE INDEX IF NOT EXISTS idx_search_log_query ON search_log(query)")


def log_search(query: str, result_count: int) -> None:
    """Records the query for the admin analytics view. Never fails a search."""
    try:
        ensure_log_table()
        from .security.ids import now_ms, ulid

        db.execute(
            "INSERT INTO search_log (id, query, results, created_at) VALUES (?,?,?,?)",
            ulid(), query[:160], result_count, now_ms(),
        )
    except Exception:  # pragma: no cover - analytics are best-effort
        pass


def trending(limit: int = 10) -> list[dict]:
    try:
        ensure_log_table()
        return db.query(
            "SELECT query, count(*) AS hits FROM search_log GROUP BY query ORDER BY hits DESC, query LIMIT ?", limit
        )
    except Exception:  # pragma: no cover
        return []


def indexed_count() -> int:
    return int(db.scalar("SELECT count(*) AS c FROM search_index") or 0)


# Bump whenever reindex_all() starts covering a new entity type or changes what
# a body contains. The search index is derived data, so a deployment whose code
# indexes more than its stored index holds must rebuild it; without this a site
# upgraded in place silently keeps searching the old, narrower index.
INDEX_SCHEMA_VERSION = 3


# The exact columns used to build each public search entity, in deterministic
# order. The first column is each table's stable primary key and is used to order
# rows before hashing. This includes joined content sources and intentionally
# excludes flashcard backs: answers are never copied into the public search index.
# Keep this list aligned with the source reads in reindex_all().
_FINGERPRINT_TABLES = {
    "branches": ("id", "slug", "name", "category", "description", "is_active"),
    "subjects": ("id", "branch_id", "slug", "name", "description", "status", "difficulty", "semester_id"),
    "topics": ("id", "subject_id", "slug", "title", "summary", "status", "difficulty", "tags"),
    "notes": ("id", "topic_id", "status", "quality_level"),
    "note_sections": ("id", "note_id", "title", "body", "order_index"),
    "formulas": ("id", "slug", "name", "meaning", "category"),
    "questions": ("id", "subject_id", "slug", "stem", "kind", "difficulty", "is_active"),
    "coding_problems": ("id", "slug", "title", "statement", "difficulty", "topics"),
    "projects": (
        "id", "branch_id", "slug", "title", "summary", "problem_statement", "objective",
        "prerequisites", "hardware", "software", "architecture", "database_design", "testing",
        "expected_output", "improvements", "difficulty", "tech", "skills", "status",
    ),
    "project_steps": ("id", "project_id", "phase", "title", "body", "order_index"),
    "project_resources": ("id", "project_id", "title", "note"),
    "videos": ("id", "slug", "title", "channel", "category", "level"),
    "books": ("id", "slug", "title", "author", "description"),
    "resources": ("id", "slug", "title", "kind", "level", "description"),
    "roadmaps": ("id", "slug", "title", "kind", "summary"),
    "programming_languages": ("id", "slug", "name", "blurb"),
    "language_modules": ("id", "language_id", "slug", "title", "summary", "body", "example", "exercise", "order_index"),
    "flashcards": ("id", "subject_id", "front", "hint", "deck", "difficulty"),
    "users": ("id", "username", "status"),
    "profiles": ("user_id", "full_name", "headline", "branch_id", "privacy"),
}


def content_fingerprint() -> str:
    """Hash indexed source fields so inserts, edits and deletes all invalidate it.

    The old COUNT/SUM(updated_at) shortcut silently treated a table without an
    ``updated_at`` column as empty. Row-count fingerprints then fixed inserts but
    still missed in-place edits. A deterministic hash of only the columns used by
    reindex_all() handles tables with and without timestamps, including edits to
    note sections, language modules, project steps, and searchable profile privacy.
    The catalogue is small enough for this single scan at startup; the hashes are
    stable per table and contain no source text.
    """
    parts = []
    for table, columns in _FINGERPRINT_TABLES.items():
        fields = ", ".join(columns)
        rows = db.query(f"SELECT {fields} FROM {table} ORDER BY {columns[0]}")
        digest = hashlib.sha256()
        for row in rows:
            values = [row[column] for column in columns]
            digest.update(json.dumps(
                values, ensure_ascii=False, separators=(",", ":"), default=str,
            ).encode("utf-8"))
            digest.update(b"\n")
        parts.append(f"{table}:{len(rows)}:{digest.hexdigest()}")
    return "|".join(parts)


def refresh_if_stale() -> int:
    """Rebuilds the index when it no longer describes the content tables.

    Two independent reasons to rebuild:

    - the code indexes more entity types than the stored index holds, tracked by
      INDEX_SCHEMA_VERSION, which covers a schema change on upgrade;
    - the content has changed since the index was built, tracked by
      content_fingerprint(). This is the one that matters operationally: nothing
      indexes a row when it is inserted, and docs/CONTENT.md tells you to extend
      the catalogue by inserting rows. Without this, a subject added that way
      would be invisible to global search and to the AI tutor until the process
      restarted with a bumped version - which it never would.

    Returns the number of entities reindexed, or 0 when the index was current.
    """
    from .security.ids import now_ms

    fingerprint = content_fingerprint()
    version_row = db.query_one("SELECT value FROM site_config WHERE key = 'search_index_version'")
    marker_row = db.query_one("SELECT value FROM site_config WHERE key = 'search_index_marker'")
    version_ok = bool(version_row) and version_row["value"] == str(INDEX_SCHEMA_VERSION)
    marker_ok = bool(marker_row) and marker_row["value"] == fingerprint
    if version_ok and marker_ok:
        return 0

    count = reindex_all()
    stamp = now_ms()
    for key, value in (("search_index_version", str(INDEX_SCHEMA_VERSION)),
                       ("search_index_marker", fingerprint)):
        db.execute(
            "INSERT INTO site_config (key, value, updated_at) VALUES (?,?,?) "
            "ON CONFLICT(key) DO UPDATE SET value = excluded.value, updated_at = excluded.updated_at",
            key, value, stamp,
        )
    return count


def reindex_all() -> int:
    """Rebuilds the whole index from the content tables."""
    db.execute("DELETE FROM search_index")
    count = 0

    for row in db.query(
        "SELECT t.slug, t.title, t.summary, t.difficulty, t.tags, b.slug AS branch, s.semester_id AS semester, s.name AS subject "
        "FROM topics t JOIN subjects s ON s.id = t.subject_id LEFT JOIN branches b ON b.id = s.branch_id "
        "WHERE t.status='published'"
    ):
        index_entity(
            entity_type="topic", entity_id=row["slug"], title=row["title"],
            body=f"{row['subject']}. {row['summary'] or ''}", branch=row["branch"] or "",
            semester=str(row["semester"] or ""), difficulty=row["difficulty"], tags=row["tags"] or "",
        )
        count += 1

    for row in db.query(
        "SELECT s.slug, s.name, s.description, s.difficulty, s.semester_id, b.slug AS branch FROM subjects s "
        "LEFT JOIN branches b ON b.id = s.branch_id WHERE s.status='published'"
    ):
        index_entity(
            entity_type="subject", entity_id=row["slug"], title=row["name"], body=row["description"] or "",
            branch=row["branch"] or "", semester=str(row["semester_id"] or ""), difficulty=row["difficulty"],
        )
        count += 1

    for row in db.query("SELECT slug, name, meaning, category FROM formulas"):
        index_entity(entity_type="formula", entity_id=row["slug"], title=row["name"],
                     body=f"{row['category']}. {row['meaning'] or ''}", tags=row["category"])
        count += 1

    for row in db.query(
        "SELECT q.slug, q.stem, q.kind, q.difficulty, b.slug AS branch FROM questions q "
        "LEFT JOIN subjects s ON s.id = q.subject_id LEFT JOIN branches b ON b.id = s.branch_id WHERE q.is_active = 1"
    ):
        index_entity(entity_type="question", entity_id=row["slug"], title=row["stem"][:300],
                     body=row["kind"], branch=row["branch"] or "", difficulty=row["difficulty"], tags=row["kind"])
        count += 1

    # Notes were never indexed, so the 192 published notes and their 957
    # sections were invisible to global search - a student searching for a
    # concept found the topic page but not the writing that explains it.
    #
    # One entry per topic, merging every published note it has. This used to
    # index one entry per note keyed by the topic slug, and index_entity()
    # deletes before inserting, so the four notes a topic carries silently
    # overwrote each other and only the last one read survived - 192 notes
    # produced 48 index rows and which quality level won depended on row order.
    # Merging keeps every note's prose searchable while still returning one
    # result per topic, which is what ENTITY_URLS["note"] points at anyway.
    # The body is capped at MAX_BODY_CHARS, which the measured sizes above fit.
    for row in db.query(
        "SELECT t.slug AS topic_slug, t.title AS topic_title, s.name AS subject, "
        "       b.slug AS branch, s.semester_id AS semester, t.difficulty "
        "FROM topics t JOIN subjects s ON s.id = t.subject_id "
        "LEFT JOIN branches b ON b.id = s.branch_id "
        "WHERE EXISTS (SELECT 1 FROM notes n WHERE n.topic_id = t.id AND n.status = 'published')"
    ):
        parts = []
        levels = []
        for note in db.query(
            "SELECT id, quality_level FROM notes WHERE topic_id = "
            "(SELECT id FROM topics WHERE slug = ?) AND status = 'published' "
            "ORDER BY quality_level, id", row["topic_slug"]
        ):
            sections = db.query(
                "SELECT title, body FROM note_sections WHERE note_id = ? ORDER BY order_index",
                note["id"],
            )
            levels.append(note["quality_level"])
            parts.append(" ".join(f"{sec['title']}. {sec['body']}" for sec in sections))
        body = " ".join(parts)[:MAX_BODY_CHARS]
        index_entity(
            entity_type="note", entity_id=row["topic_slug"],
            title=f"{row['topic_title']} — {len(levels)} notes",
            body=f"{row['subject']}. {body}", branch=row["branch"] or "",
            semester=str(row["semester"] or ""), difficulty=row["difficulty"],
            tags=" ".join(levels),
        )
        count += 1

    for row in db.query("SELECT slug, title, statement, difficulty, topics FROM coding_problems"):
        index_entity(entity_type="problem", entity_id=row["slug"], title=row["title"],
                     body=f"{row['statement'][:600]} {row['topics']}", difficulty=row["difficulty"], tags=row["topics"])
        count += 1

    for row in db.query(
        "SELECT p.id, p.slug, p.title, p.summary, p.problem_statement, p.objective, "
        "p.prerequisites, p.hardware, p.software, p.architecture, p.database_design, "
        "p.testing, p.expected_output, p.improvements, p.difficulty, p.tech, p.skills, "
        "b.slug AS branch FROM projects p LEFT JOIN branches b ON b.id = p.branch_id "
        "WHERE p.status='published'"
    ):
        parts = [row[key] or "" for key in (
            "summary", "problem_statement", "objective", "prerequisites", "hardware",
            "software", "architecture", "database_design", "testing", "expected_output",
            "improvements", "tech", "skills",
        )]
        parts.extend(
            f"{step['title']}. {step['body']}"
            for step in db.query(
                "SELECT title, body FROM project_steps WHERE project_id = ? ORDER BY order_index",
                row["id"],
            )
        )
        parts.extend(
            f"{resource['title']}. {resource['note'] or ''}"
            for resource in db.query(
                "SELECT title, note FROM project_resources WHERE project_id = ? ORDER BY title",
                row["id"],
            )
        )
        index_entity(entity_type="project", entity_id=row["slug"], title=row["title"],
                     body=" ".join(parts), branch=row["branch"] or "",
                     difficulty=row["difficulty"], tags=row["tech"])
        count += 1

    for row in db.query("SELECT slug, title, channel, category, level FROM videos"):
        index_entity(entity_type="video", entity_id=row["slug"], title=row["title"], body=row["channel"],
                     difficulty=row["level"], tags=row["category"])
        count += 1

    for row in db.query("SELECT slug, title, author, description FROM books"):
        index_entity(entity_type="book", entity_id=row["slug"], title=row["title"],
                     body=f"{row['author']}. {row['description'] or ''}")
        count += 1

    for row in db.query("SELECT slug, title, kind, level, description FROM resources"):
        index_entity(entity_type="resource", entity_id=row["slug"], title=row["title"],
                     body=f"{row['kind']}. {row['description'] or ''}", difficulty=row["level"], tags=row["kind"])
        count += 1

    for row in db.query("SELECT slug, title, kind, summary FROM roadmaps"):
        index_entity(entity_type="roadmap", entity_id=row["slug"], title=row["title"],
                     body=f"{row['kind']}. {row['summary'] or ''}", tags=row["kind"])
        count += 1

    for row in db.query("SELECT id, slug, name, blurb FROM programming_languages"):
        index_entity(entity_type="language", entity_id=row["slug"], title=row["name"], body=row["blurb"] or "")
        count += 1
        for module in db.query(
            "SELECT slug, title, summary, body, example, exercise FROM language_modules "
            "WHERE language_id = ? ORDER BY order_index, title", row["id"],
        ):
            index_entity(
                entity_type="module", entity_id=f"{row['slug']}::{module['slug']}",
                title=f"{row['name']}: {module['title']}",
                body=" ".join(filter(None, (
                    module["summary"], module["body"], module["example"], module["exercise"],
                ))),
                tags=row["name"],
            )
            count += 1

    # Public search exposes prompts and hints, never the flashcard back/answer.
    # The browse page intentionally separates answers behind a reveal control.
    for row in db.query(
        "SELECT f.id, f.front, f.hint, f.deck, f.difficulty, s.name AS subject "
        "FROM flashcards f LEFT JOIN subjects s ON s.id = f.subject_id "
        "ORDER BY f.id"
    ):
        index_entity(
            entity_type="flashcard", entity_id=row["id"], title=row["front"],
            body=" ".join(filter(None, (row["deck"], row["subject"], row["hint"]))),
            difficulty=row["difficulty"], tags=row["deck"],
        )
        count += 1

    for row in db.query("SELECT slug, name, category, description FROM branches WHERE is_active = 1"):
        index_entity(entity_type="branch", entity_id=row["slug"], title=row["name"],
                     body=f"{row['category']}. {row['description'] or ''}", tags=row["category"])
        count += 1

    for row in db.query(
        "SELECT u.username, p.full_name, p.headline, b.slug AS branch FROM users u "
        "JOIN profiles p ON p.user_id = u.id LEFT JOIN branches b ON b.id = p.branch_id "
        f"WHERE u.status='active' AND {db.json_flag('p.privacy', 'searchable')}"
    ):
        index_entity(entity_type="user", entity_id=row["username"], title=row["full_name"],
                     body=f"{row['username']}. {row['headline'] or ''}", branch=row["branch"] or "")
        count += 1

    return count
