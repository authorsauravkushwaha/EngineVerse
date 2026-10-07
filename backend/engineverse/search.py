"""Universal search (spec §8).

Backed by SQLite FTS5 (porter stemming + unicode folding) with bm25 column
weighting so titles outrank body text. Queries degrade gracefully:

  1. AND of prefix-expanded tokens  -> precise
  2. OR  of prefix-expanded tokens  -> recall
  3. LIKE substring scan            -> fallback
  4. Levenshtein "did you mean"     -> typo correction

The same interface maps onto PostgreSQL ``tsvector`` + ``pg_trgm`` in
production (db/postgres/README.md), so no page code changes on migration.
"""
from __future__ import annotations

import re
from typing import Any

from . import db

ENTITY_URLS = {
    "note": "/topics/{id}",   # a note is read on its topic's page
    "topic": "/topics/{id}",
    "subject": "/subjects/{id}",
    "formula": "/formulas#{id}",
    "question": "/practice/questions/{id}",
    "problem": "/practice/problems/{id}",
    "project": "/projects/{id}",
    "video": "/videos#{id}",
    "book": "/books#{id}",
    "resource": "/resources#{id}",
    "roadmap": "/roadmaps/{id}",
    "language": "/programming/{id}",
    "branch": "/branches/{id}",
    "user": "/portfolio/{id}",
}


def url_for(entity_type: str, entity_id: str) -> str:
    template = ENTITY_URLS.get(entity_type, "/explore")
    return template.format(id=entity_id)


def index_entity(
    *, entity_type: str, entity_id: str, title: str, body: str = "",
    branch: str = "", semester: str = "", difficulty: str = "", tags: str = "",
) -> None:
    db.execute("DELETE FROM search_index WHERE entity_type = ? AND entity_id = ?", entity_type, entity_id)
    db.execute(
        "INSERT INTO search_index (entity_type,entity_id,title,body,branch,semester,difficulty,tags) "
        "VALUES (?,?,?,?,?,?,?,?)",
        entity_type, entity_id, title[:500], body[:4000], branch or "", semester or "", difficulty or "", tags or "",
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
    db.execute(
        "CREATE TABLE IF NOT EXISTS search_log (id TEXT PRIMARY KEY, query TEXT NOT NULL, "
        "results INTEGER NOT NULL, created_at INTEGER NOT NULL)"
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
# upgraded in place silently keeps searching the old, narrower index. Notes were
# exactly that case: added to the indexer, absent from every existing index.
INDEX_SCHEMA_VERSION = 2


def refresh_if_stale() -> int:
    """Rebuilds the index when the code indexes more than the stored index does.

    Records the version it wrote in site_config so the check is cheap on every
    later start. Returns the number of entities reindexed, or 0 when the index
    was already current.
    """
    from .security.ids import now_ms

    row = db.query_one("SELECT value FROM site_config WHERE key = 'search_index_version'")
    if row and row["value"] == str(INDEX_SCHEMA_VERSION):
        return 0
    count = reindex_all()
    if row:
        db.execute("UPDATE site_config SET value = ?, updated_at = ? WHERE key = 'search_index_version'",
                   str(INDEX_SCHEMA_VERSION), now_ms())
    else:
        db.execute("INSERT INTO site_config (key, value, updated_at) VALUES (?,?,?)",
                   "search_index_version", str(INDEX_SCHEMA_VERSION), now_ms())
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
    # concept found the topic page but not the writing that explains it. The
    # body is capped: the index is a pointer into the note, not a copy of it.
    for row in db.query(
        "SELECT n.id, n.quality_level, t.slug AS topic_slug, t.title AS topic_title, s.name AS subject, "
        "       b.slug AS branch, s.semester_id AS semester, t.difficulty "
        "FROM notes n JOIN topics t ON t.id = n.topic_id JOIN subjects s ON s.id = t.subject_id "
        "LEFT JOIN branches b ON b.id = s.branch_id WHERE n.status = 'published'"
    ):
        sections = db.query(
            "SELECT title, body FROM note_sections WHERE note_id = ? ORDER BY order_index", row["id"]
        )
        body = " ".join(f"{sec['title']}. {sec['body']}" for sec in sections)[:4000]
        index_entity(
            entity_type="note", entity_id=row["topic_slug"],
            title=f"{row['topic_title']} — {row['quality_level']} notes",
            body=f"{row['subject']}. {body}", branch=row["branch"] or "",
            semester=str(row["semester"] or ""), difficulty=row["difficulty"],
            tags=row["quality_level"],
        )
        count += 1

    for row in db.query("SELECT slug, title, statement, difficulty, topics FROM coding_problems"):
        index_entity(entity_type="problem", entity_id=row["slug"], title=row["title"],
                     body=f"{row['statement'][:600]} {row['topics']}", difficulty=row["difficulty"], tags=row["topics"])
        count += 1

    for row in db.query(
        "SELECT p.slug, p.title, p.summary, p.difficulty, p.tech, b.slug AS branch FROM projects p "
        "LEFT JOIN branches b ON b.id = p.branch_id WHERE p.status='published'"
    ):
        index_entity(entity_type="project", entity_id=row["slug"], title=row["title"],
                     body=f"{row['summary'] or ''} {row['tech']}", branch=row["branch"] or "",
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

    for row in db.query("SELECT slug, name, blurb FROM programming_languages"):
        index_entity(entity_type="language", entity_id=row["slug"], title=row["name"], body=row["blurb"] or "")
        count += 1

    for row in db.query("SELECT slug, name, category, description FROM branches WHERE is_active = 1"):
        index_entity(entity_type="branch", entity_id=row["slug"], title=row["name"],
                     body=f"{row['category']}. {row['description'] or ''}", tags=row["category"])
        count += 1

    for row in db.query(
        "SELECT u.username, p.full_name, p.headline, b.slug AS branch FROM users u "
        "JOIN profiles p ON p.user_id = u.id LEFT JOIN branches b ON b.id = p.branch_id "
        "WHERE u.status='active' AND COALESCE(json_extract(p.privency,'$.searchable'),1) = 1"
        .replace("privency", "privacy")
    ):
        index_entity(entity_type="user", entity_id=row["username"], title=row["full_name"],
                     body=f"{row['username']}. {row['headline'] or ''}", branch=row["branch"] or "")
        count += 1

    return count
