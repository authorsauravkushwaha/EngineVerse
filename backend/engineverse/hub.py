"""The per-stream study hub (spec §3, §23-§28).

Every engineering branch gets the same shape of page, assembled from the same
tables the rest of the platform reads: the branch's published subjects, their
topics and notes, the question bank and topic practice, the coding sheet matched
to that stream, the formula sheets, flashcards, projects and roadmaps.

Two rules shaped this module.

*Nothing here links to another website.* The hub is a map of what EngineVerse
already contains, so a learner never has to leave the site to study a subject.
The curated external shelf still exists at ``/resources/offsite`` for people who
want it, but it is not what the hub is made of and nothing in it is required.

*The counts are queries, not decoration.* A card that claims "12 subjects" reads
the number out of the database in the same request that renders it, so a branch
with an empty shelf says so instead of showing a dead link. Where a stream has
genuinely thin coverage the page says that plainly - EngineVerse's catalogue is
starter material, and pretending otherwise would be the dishonest version of
this page.
"""
from __future__ import annotations

from typing import Any

from . import db

#: Which coding sheets a stream should be pointed at, keyed by the branch
#: category in ``branches.category``. The slugs live in the seeder; a slug that
#: no longer exists is skipped rather than rendered as a broken link.
STREAM_SHEETS: dict[str, tuple[str, ...]] = {
    "cse": ("arrays-hashing", "two-pointers-window", "stacks-search",
            "linked-trees-heaps", "graphs-traversal", "dynamic-programming",
            "software-web", "security-systems", "interview-core"),
    "electronics": ("digital-signals", "engineering-computing", "security-systems",
                    "interview-core"),
    "mechanical": ("engineering-computing", "interview-core"),
    "civil": ("engineering-computing", "interview-core"),
    "chemical": ("engineering-computing", "data-analysis", "interview-core"),
    "bio": ("data-analysis", "engineering-computing", "interview-core"),
    "other": ("engineering-computing", "data-analysis", "interview-core"),
}

#: Reading order inside a semester when the catalogue does not supply one.
_SEMESTER_FALLBACK = ("semester_id IS NULL", "semester_id")


def _count(sql: str, *args: Any) -> int:
    return int(db.scalar(sql, *args) or 0)


def branch_row(slug: str | None) -> dict | None:
    if not slug:
        return None
    return db.query_one(
        "SELECT id, slug, name, category, description, icon, color FROM branches "
        "WHERE slug = ? AND is_active = 1",
        slug,
    )


def branch_by_id(branch_id: str | None) -> dict | None:
    if not branch_id:
        return None
    return db.query_one(
        "SELECT id, slug, name, category, description, icon, color FROM branches WHERE id = ?",
        branch_id,
    )


def default_branch_slug(preferred_id: str | None = None) -> str:
    """The stream to open the hub on.

    A signed-in learner's own branch wins, which is what makes the page
    personal. Without one, the first branch in catalogue order is used: the hub
    is publicly readable, so there is no such thing as "no stream" - only an
    unstated one.
    """
    row = branch_by_id(preferred_id) if preferred_id else None
    if row:
        return str(row["slug"])
    fallback = db.query_one("SELECT slug FROM branches WHERE is_active = 1 ORDER BY order_index, name LIMIT 1")
    return str(fallback["slug"]) if fallback else ""


def list_streams(*, limit: int = 60) -> list[dict]:
    """Every branch with the size of the in-app shelf behind it.

    One query per count would be dozens of round trips for a page that only
    needs totals, so each number is a correlated subquery keyed on the branch.
    """
    rows = db.query(
        "SELECT b.id, b.slug, b.name, b.category, b.description, b.icon, b.color, "
        "  (SELECT count(*) FROM subjects s WHERE s.branch_id = b.id AND s.status = 'published') AS subjects, "
        "  (SELECT count(*) FROM topics t JOIN subjects s2 ON s2.id = t.subject_id "
        "     WHERE s2.branch_id = b.id AND t.status = 'published') AS topics, "
        "  (SELECT count(*) FROM notes n JOIN topics t2 ON t2.id = n.topic_id "
        "     JOIN subjects s3 ON s3.id = t2.subject_id "
        "     WHERE s3.branch_id = b.id AND n.status = 'published') AS notes, "
        "  (SELECT count(*) FROM questions q WHERE q.is_active = 1 AND q.subject_id IN "
        "     (SELECT id FROM subjects s4 WHERE s4.branch_id = b.id)) AS questions, "
        "  (SELECT count(*) FROM flashcards f WHERE f.subject_id IN "
        "     (SELECT id FROM subjects s5 WHERE s5.branch_id = b.id)) AS flashcards, "
        "  (SELECT count(*) FROM formulas fo WHERE fo.subject_id IN "
        "     (SELECT id FROM subjects s6 WHERE s6.branch_id = b.id)) AS formulas, "
        "  (SELECT count(*) FROM projects p WHERE p.branch_id = b.id AND p.status = 'published') AS projects "
        "FROM branches b WHERE b.is_active = 1 ORDER BY b.order_index, b.name LIMIT ?",
        limit,
    )
    for row in rows:
        row["category_name"] = _category_name(row["category"])
    return rows


def _category_name(key: str) -> str:
    from . import catalog

    return catalog.category_name(key)


def _subjects_for(branch_id: str, semester_id: int | None) -> list[dict]:
    """Published subjects for a branch, with everything the cards show.

    ``semester_id`` filters to the learner's current semester when one is set
    and the branch actually has subjects tagged with it. Filtering to an empty
    list would be worse than not filtering at all, so an untagged catalogue
    falls back to the whole branch.
    """
    args: list[Any] = [branch_id]
    clause = ""
    if semester_id:
        tagged = _count(
            "SELECT count(*) FROM subjects WHERE branch_id = ? AND semester_id = ? AND status = 'published'",
            branch_id, semester_id,
        )
        if tagged:
            clause = " AND s.semester_id = ?"
            args.append(semester_id)
    return db.query(
        "SELECT s.id, s.slug, s.name, s.code, s.semester_id, s.description, s.icon, s.color, s.difficulty, "
        "  (SELECT count(*) FROM topics t WHERE t.subject_id = s.id AND t.status = 'published') AS topics, "
        "  (SELECT count(*) FROM notes n JOIN topics t2 ON t2.id = n.topic_id "
        "     WHERE t2.subject_id = s.id AND n.status = 'published') AS notes, "
        "  (SELECT count(*) FROM questions q WHERE q.subject_id = s.id AND q.is_active = 1) AS questions, "
        "  (SELECT count(*) FROM formulas f WHERE f.subject_id = s.id) AS formulas "
        "FROM subjects s WHERE s.branch_id = ? AND s.status = 'published'" + clause +
        " ORDER BY s.is_first_year DESC, " + ", ".join(_SEMESTER_FALLBACK) + ", s.order_index, s.name",
        *args,
    )


def _reading_list(branch_id: str, *, semester_id: int | None = None, limit: int = 8) -> list[dict]:
    """The next few topics to read, newest seminar first.

    Ordered by the subject's place in the branch rather than by popularity: a
    first-year learner should meet the first subject advertised for the branch,
    not whichever topic happens to have the most views.
    """
    args: list[Any] = [branch_id]
    clause = ""
    if semester_id:
        clause = " AND s.semester_id = ?"
        args.append(semester_id)
    args.append(limit)
    return db.query(
        "SELECT t.id, t.slug, t.title, t.summary, t.difficulty, t.est_minutes, "
        "       s.name AS subject_name, s.slug AS subject_slug "
        "FROM topics t JOIN subjects s ON s.id = t.subject_id "
        "WHERE s.branch_id = ? AND s.status = 'published' AND t.status = 'published'" + clause +
        " ORDER BY s.is_first_year DESC, s.order_index, t.order_index LIMIT ?",
        *args,
    )


def _questions_by_subject(branch_id: str, limit: int = 6) -> list[dict]:
    return db.query(
        "SELECT s.slug, s.name, count(q.id) AS count FROM questions q "
        "JOIN subjects s ON s.id = q.subject_id "
        "WHERE s.branch_id = ? AND q.is_active = 1 GROUP BY s.id ORDER BY count(q.id) DESC, s.name LIMIT ?",
        branch_id, limit,
    )


def _question_kinds(branch_id: str) -> list[dict]:
    return db.query(
        "SELECT q.kind, count(*) AS count FROM questions q JOIN subjects s ON s.id = q.subject_id "
        "WHERE s.branch_id = ? AND q.is_active = 1 GROUP BY q.kind ORDER BY count DESC",
        branch_id,
    )


def _related_projects(branch_id: str, limit: int = 6) -> list[dict]:
    return db.query(
        "SELECT slug, title, difficulty, category, est_hours, summary FROM projects "
        "WHERE status = 'published' AND (branch_id = ? OR branch_id IS NULL) "
        "ORDER BY (branch_id = ?) DESC, order_index, title LIMIT ?",
        branch_id, branch_id, limit,
    )


def _related_roadmaps(branch_id: str, limit: int = 4) -> list[dict]:
    return db.query(
        "SELECT r.slug, r.title, r.kind, r.target_role, r.summary, "
        "  (SELECT count(*) FROM roadmap_nodes n WHERE n.roadmap_id = r.id) AS nodes "
        "FROM roadmaps r WHERE r.branch_id = ? OR r.branch_id IS NULL "
        "ORDER BY (r.branch_id = ?) DESC, r.order_index, r.title LIMIT ?",
        branch_id, branch_id, limit,
    )


def _sheets_for(category: str, limit: int = 6) -> list[dict]:
    """Coding sheets this stream should practise, with progress for a viewer."""
    from . import coding

    wanted = STREAM_SHEETS.get(category or "", STREAM_SHEETS["other"])
    by_slug = {row["slug"]: row for row in coding.list_sheets()}
    return [by_slug[slug] for slug in wanted if slug in by_slug][:limit]


def stream(branch_id: str, *, semester_id: int | None = None, viewer_id: str | None = None) -> dict:
    """Everything the hub renders for one stream."""
    from . import coding, library

    branch = branch_by_id(branch_id)
    if branch is None:
        return {}
    subjects = _subjects_for(branch_id, semester_id)
    subject_ids = [row["id"] for row in subjects]
    questions = _count(
        "SELECT count(*) FROM questions WHERE is_active = 1 AND subject_id IN "
        f"({','.join('?' * len(subject_ids))})", *subject_ids
    ) if subject_ids else 0
    cards = {
        "notes": sum(int(row["notes"] or 0) for row in subjects),
        "topics": sum(int(row["topics"] or 0) for row in subjects),
        "subjects": len(subjects),
        "questions": questions,
        "flashcards": _count(
            "SELECT count(*) FROM flashcards WHERE subject_id IN "
            f"({','.join('?' * len(subject_ids))})", *subject_ids
        ) if subject_ids else 0,
        "formulas": _count(
            "SELECT count(*) FROM formulas WHERE subject_id IN "
            f"({','.join('?' * len(subject_ids))})", *subject_ids
        ) if subject_ids else 0,
        "projects": _count(
            "SELECT count(*) FROM projects WHERE status = 'published' AND branch_id = ?", branch_id
        ),
    }
    progress = {"started": 0, "completed": 0}
    if viewer_id and subject_ids:
        row = db.query_one(
            "SELECT count(*) AS started, "
            "  sum(CASE WHEN p.status IN ('completed','mastered') THEN 1 ELSE 0 END) AS completed "
            "FROM user_progress p JOIN topics t ON t.id = p.topic_id "
            "WHERE p.user_id = ? AND t.subject_id IN "
            f"({','.join('?' * len(subject_ids))})",
            viewer_id, *subject_ids,
        ) or {}
        progress = {"started": int(row.get("started") or 0), "completed": int(row.get("completed") or 0)}
    return {
        "branch": branch,
        "category_name": _category_name(branch["category"]),
        "subjects": subjects,
        "cards": cards,
        "progress": progress,
        "reading": _reading_list(branch_id, semester_id=semester_id, limit=9),
        "question_mix": _question_kinds(branch_id),
        "questions_by_subject": _questions_by_subject(branch_id),
        "projects": _related_projects(branch_id),
        "roadmaps": _related_roadmaps(branch_id),
        "sheets": _sheets_for(branch["category"]),
        "videos": _count(
            "SELECT count(*) FROM videos WHERE subject_id IN "
            f"({','.join('?' * len(subject_ids))})", *subject_ids
        ) if subject_ids else 0,
        "books": _count(
            "SELECT count(*) FROM books WHERE branch_id = ? OR subject_id IN "
            f"({','.join('?' * len(subject_ids))})", branch_id, *subject_ids
        ) if subject_ids else 0,
        "offsite_total": library.count_resources(),
    }
