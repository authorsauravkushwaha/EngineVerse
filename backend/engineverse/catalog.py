"""Catalogue repositories: branches -> subjects -> modules -> topics -> notes.

The relationship chain (spec §53) powers recommendations, roadmaps and
progress roll-ups across the whole site.
"""
from __future__ import annotations

import json
from typing import Any

from . import db

NOTE_ORDER = ("beginner", "standard", "advanced", "industry")


def _json(value: Any, fallback: Any) -> Any:
    if value in (None, ""):
        return fallback
    if isinstance(value, (list, dict)):
        return value
    try:
        return json.loads(value)
    except (ValueError, TypeError):
        return fallback


# --------------------------------------------------------------------------
# Branches / universities / semesters
# --------------------------------------------------------------------------

def list_branches() -> list[dict]:
    return db.query(
        "SELECT b.*, (SELECT count(*) FROM subjects s WHERE s.branch_id = b.id) AS subject_count "
        "FROM branches b WHERE b.is_active = 1 ORDER BY b.order_index, b.name"
    )


def get_branch(slug: str) -> dict | None:
    return db.query_one("SELECT * FROM branches WHERE slug = ? AND is_active = 1", slug)


def branch_by_id(branch_id: str) -> dict | None:
    return db.query_one("SELECT * FROM branches WHERE id = ?", branch_id)


def branch_groups() -> list[dict]:
    """Branches grouped by category, for the explore page."""
    branches = list_branches()
    grouped: dict[str, list[dict]] = {}
    for branch in branches:
        grouped.setdefault(branch["category"], []).append(branch)
    return [{"category": key, "branches": value} for key, value in grouped.items()]


def list_universities() -> list[dict]:
    return db.query("SELECT id, name, code, country, region FROM universities ORDER BY country, name")


def university_by_id(university_id: str) -> dict | None:
    return db.query_one("SELECT * FROM universities WHERE id = ?", university_id)


def list_colleges(university_id: str | None = None) -> list[dict]:
    if university_id:
        return db.query(
            "SELECT id, name, city, country FROM colleges WHERE university_id = ? ORDER BY name", university_id
        )
    return db.query("SELECT id, name, city, country FROM colleges ORDER BY name LIMIT 300")


def list_semesters() -> list[dict]:
    return db.query("SELECT id, label, year FROM semesters ORDER BY CASE WHEN id = 0 THEN 99 ELSE id END")


def curriculum(university_id: str, branch_id: str) -> list[dict]:
    return db.query(
        "SELECT cs.subject_id, cs.semester_id, cs.is_core, s.name, s.slug, s.code "
        "FROM curriculum_subjects cs "
        "JOIN curricula c ON c.id = cs.curriculum_id "
        "JOIN subjects s ON s.id = cs.subject_id "
        "WHERE c.university_id = ? AND c.branch_id = ? AND c.is_active = 1 "
        "ORDER BY cs.semester_id, s.order_index",
        university_id,
        branch_id,
    )


# --------------------------------------------------------------------------
# Subjects
# --------------------------------------------------------------------------

def list_subjects(
    *, branch: str | None = None, semester: int | None = None, first_year: bool = False,
    q: str | None = None, limit: int = 200,
) -> list[dict]:
    clauses = ["s.status = 'published'"]
    args: list[Any] = []
    if branch:
        clauses.append("b.slug = ?")
        args.append(branch)
    if semester:
        clauses.append("s.semester_id = ?")
        args.append(semester)
    if first_year:
        clauses.append("s.is_first_year = 1")
    if q:
        clauses.append("(s.name LIKE ? OR s.description LIKE ? OR s.code LIKE ?)")
        args += [f"%{q}%"] * 3
    args.append(limit)
    rows = db.query(
        "SELECT s.*, b.name AS branch_name, b.slug AS branch_slug, b.color AS branch_color, "
        "(SELECT count(*) FROM topics t WHERE t.subject_id = s.id AND t.status='published') AS topic_count, "
        "(SELECT count(*) FROM questions qn WHERE qn.subject_id = s.id AND qn.is_active = 1) AS question_count "
        f"FROM subjects s LEFT JOIN branches b ON b.id = s.branch_id WHERE {' AND '.join(clauses)} "
        "ORDER BY s.is_first_year DESC, s.order_index, s.name LIMIT ?",
        *args,
    )
    return rows


def get_subject(slug: str) -> dict | None:
    return db.query_one(
        "SELECT s.*, b.name AS branch_name, b.slug AS branch_slug FROM subjects s "
        "LEFT JOIN branches b ON b.id = s.branch_id WHERE s.slug = ? AND s.status = 'published'",
        slug,
    )


def subject_by_id(subject_id: str) -> dict | None:
    return db.query_one("SELECT * FROM subjects WHERE id = ?", subject_id)


def popular_subjects(limit: int = 8) -> list[dict]:
    return db.query(
        "SELECT s.*, b.slug AS branch_slug, b.name AS branch_name, "
        "(SELECT count(*) FROM topics t WHERE t.subject_id = s.id AND t.status='published') AS topic_count "
        "FROM subjects s LEFT JOIN branches b ON b.id = s.branch_id "
        "WHERE s.status='published' AND s.is_first_year = 0 ORDER BY s.order_index LIMIT ?",
        limit,
    )


def subject_stats(subject_id: str) -> dict[str, int]:
    def count(sql: str, *args: Any) -> int:
        return int(db.scalar(sql, *args) or 0)

    return {
        "topics": count("SELECT count(*) AS c FROM topics WHERE subject_id = ? AND status='published'", subject_id),
        "notes": count(
            "SELECT count(*) AS c FROM notes n JOIN topics t ON t.id = n.topic_id "
            "WHERE t.subject_id = ? AND n.status='published'",
            subject_id,
        ),
        "questions": count("SELECT count(*) AS c FROM questions WHERE subject_id = ? AND is_active=1", subject_id),
        "formulas": count("SELECT count(*) AS c FROM formulas WHERE subject_id = ?", subject_id),
        "videos": count("SELECT count(*) AS c FROM videos WHERE subject_id = ?", subject_id),
        "resources": count("SELECT count(*) AS c FROM resources WHERE subject_id = ?", subject_id),
        "projects": count("SELECT count(*) AS c FROM projects WHERE subject_id = ?", subject_id),
        "problems": count(
            "SELECT count(DISTINCT cp.id) AS c FROM coding_problems cp JOIN topics t ON t.subject_id = ? "
            "WHERE cp.topics LIKE '%' || t.title || '%'",
            subject_id,
        ),
        "flashcards": count("SELECT count(*) AS c FROM flashcards WHERE subject_id = ?", subject_id),
    }


# --------------------------------------------------------------------------
# Modules & topics
# --------------------------------------------------------------------------

def modules_for_subject(subject_id: str) -> list[dict]:
    return db.query(
        "SELECT * FROM modules WHERE subject_id = ? ORDER BY order_index", subject_id
    )


def topics_for_subject(subject_id: str) -> list[dict]:
    return db.query(
        "SELECT * FROM topics WHERE subject_id = ? AND status='published' ORDER BY order_index, title", subject_id
    )


def subject_outline(subject_id: str) -> list[dict]:
    """Modules with their topics; topics without a module go into a default group."""
    modules = modules_for_subject(subject_id)
    topics = topics_for_subject(subject_id)
    by_module: dict[str, list[dict]] = {}
    loose: list[dict] = []
    for topic in topics:
        if topic["module_id"]:
            by_module.setdefault(topic["module_id"], []).append(topic)
        else:
            loose.append(topic)
    outline = [{"id": m["id"], "title": m["title"], "summary": m["summary"], "topics": by_module.get(m["id"], [])} for m in modules]
    if loose:
        outline.insert(0, {"id": "core", "title": "Core Topics", "summary": None, "topics": loose})
    return outline


def get_topic(slug: str) -> dict | None:
    return db.query_one(
        "SELECT t.*, s.name AS subject_name, s.slug AS subject_slug, s.branch_id, "
        "b.name AS branch_name, b.slug AS branch_slug, m.title AS module_title "
        "FROM topics t JOIN subjects s ON s.id = t.subject_id "
        "LEFT JOIN branches b ON b.id = s.branch_id LEFT JOIN modules m ON m.id = t.module_id "
        "WHERE t.slug = ? AND t.status='published'",
        slug,
    )


def topic_by_id(topic_id: str) -> dict | None:
    return db.query_one("SELECT * FROM topics WHERE id = ?", topic_id)


def topic_siblings(subject_id: str, order_index: int) -> dict[str, dict | None]:
    return {
        "prev": db.query_one(
            "SELECT slug, title FROM topics WHERE subject_id = ? AND status='published' AND order_index < ? "
            "ORDER BY order_index DESC LIMIT 1",
            subject_id, order_index,
        ),
        "next": db.query_one(
            "SELECT slug, title FROM topics WHERE subject_id = ? AND status='published' AND order_index > ? "
            "ORDER BY order_index ASC LIMIT 1",
            subject_id, order_index,
        ),
    }


def related_topics(topic: dict, limit: int = 6) -> list[dict]:
    tags = _json(topic.get("tags"), [])
    siblings = db.query(
        "SELECT slug, title, difficulty, est_minutes FROM topics "
        "WHERE subject_id = ? AND id <> ? AND status='published' ORDER BY ABS(order_index - ?) LIMIT ?",
        topic["subject_id"], topic["id"], topic["order_index"], limit,
    )
    if not tags:
        return siblings
    others = db.query(
        "SELECT t.slug, t.title, t.difficulty, t.est_minutes FROM topics t "
        "WHERE t.id <> ? AND t.status='published' AND t.subject_id <> ? AND t.tags LIKE ? "
        "ORDER BY t.updated_at DESC LIMIT ?",
        topic["id"], topic["subject_id"], f"%{tags[0]}%", max(2, limit // 2),
    )
    seen: set[str] = set()
    merged = []
    for row in siblings + others:
        if row["slug"] not in seen:
            seen.add(row["slug"])
            merged.append(row)
    return merged[:limit]


# --------------------------------------------------------------------------
# Notes / diagrams / formulas
# --------------------------------------------------------------------------

def notes_for_topic(topic_id: str) -> list[dict]:
    rows = db.query("SELECT * FROM notes WHERE topic_id = ? AND status='published'", topic_id)
    rows.sort(key=lambda r: NOTE_ORDER.index(r["quality_level"]) if r["quality_level"] in NOTE_ORDER else 9)
    return rows


def get_note(topic_id: str, quality: str) -> dict | None:
    exact = db.query_one(
        "SELECT * FROM notes WHERE topic_id = ? AND quality_level = ? AND status='published'", topic_id, quality
    )
    if exact:
        return exact
    return db.query_one(
        "SELECT * FROM notes WHERE topic_id = ? AND status='published' "
        "ORDER BY CASE quality_level WHEN ? THEN 0 WHEN 'standard' THEN 1 ELSE 2 END LIMIT 1",
        topic_id, quality,
    )


def sections_for_note(note_id: str) -> list[dict]:
    return db.query("SELECT * FROM note_sections WHERE note_id = ? ORDER BY order_index", note_id)


def diagrams_for_topic(topic_id: str) -> list[dict]:
    rows = db.query("SELECT * FROM diagrams WHERE topic_id = ? ORDER BY rowid", topic_id)
    for row in rows:
        row["hotspots_data"] = _json(row.get("hotspots"), [])
    return rows


def formulas_for_topic(topic_id: str) -> list[dict]:
    rows = db.query("SELECT * FROM formulas WHERE topic_id = ? ORDER BY order_index", topic_id)
    for row in rows:
        row["variables_data"] = _json(row.get("variables"), [])
    return rows


def list_formulas(*, category: str | None = None, subject_id: str | None = None, q: str | None = None, limit: int = 300) -> list[dict]:
    clauses = ["1=1"]
    args: list[Any] = []
    if category:
        clauses.append("f.category = ?")
        args.append(category)
    if subject_id:
        clauses.append("f.subject_id = ?")
        args.append(subject_id)
    if q:
        clauses.append("(f.name LIKE ? OR f.latex LIKE ? OR f.meaning LIKE ?)")
        args += [f"%{q}%"] * 3
    args.append(limit)
    rows = db.query(
        "SELECT f.*, s.name AS subject_name FROM formulas f LEFT JOIN subjects s ON s.id = f.subject_id "
        f"WHERE {' AND '.join(clauses)} ORDER BY f.category, f.order_index, f.name LIMIT ?",
        *args,
    )
    for row in rows:
        row["variables_data"] = _json(row.get("variables"), [])
    return rows


def formula_categories() -> list[dict]:
    return db.query("SELECT category, count(*) AS count FROM formulas GROUP BY category ORDER BY category")


def get_formula(slug: str) -> dict | None:
    row = db.query_one("SELECT * FROM formulas WHERE slug = ?", slug)
    if row:
        row["variables_data"] = _json(row.get("variables"), [])
    return row


def site_stats() -> dict[str, int]:
    def count(table: str, where: str = "") -> int:
        return int(db.scalar(f"SELECT count(*) AS c FROM {table} {where}") or 0)

    return {
        "branches": count("branches", "WHERE is_active = 1"),
        "subjects": count("subjects"),
        "topics": count("topics"),
        "notes": count("notes"),
        "questions": count("questions"),
        "problems": count("coding_problems"),
        "projects": count("projects"),
        "formulas": count("formulas"),
        "videos": count("videos"),
        "books": count("books"),
        "resources": count("resources"),
        "flashcards": count("flashcards"),
        "roadmaps": count("roadmaps"),
        "languages": count("programming_languages"),
    }
