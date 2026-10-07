"""Video library, books, free resources, roadmaps and flashcards (spec §23-§28)."""
from __future__ import annotations

import json
from typing import Any

from . import db


def _json(value: Any, fallback: Any) -> Any:
    if value in (None, ""):
        return fallback
    if isinstance(value, (list, dict)):
        return value
    try:
        return json.loads(value)
    except (ValueError, TypeError):
        return fallback


# ---- videos ---------------------------------------------------------------

def list_videos(
    *, topic_id: str | None = None, subject_id: str | None = None, category: str | None = None,
    q: str | None = None, limit: int = 60,
) -> list[dict]:
    clauses = ["1=1"]
    args: list[Any] = []
    if topic_id:
        clauses.append("v.topic_id = ?")
        args.append(topic_id)
    if subject_id:
        clauses.append("v.subject_id = ?")
        args.append(subject_id)
    if category:
        clauses.append("v.category = ?")
        args.append(category)
    if q:
        clauses.append("(v.title LIKE ? OR v.channel LIKE ?)")
        args += [f"%{q}%"] * 2
    args.append(limit)
    return db.query(
        "SELECT v.*, s.name AS subject_name, s.slug AS subject_slug, t.title AS topic_title, t.slug AS topic_slug "
        f"FROM videos v LEFT JOIN subjects s ON s.id = v.subject_id LEFT JOIN topics t ON t.id = v.topic_id "
        f"WHERE {' AND '.join(clauses)} ORDER BY v.rating DESC, v.title LIMIT ?",
        *args,
    )


def video_categories() -> list[dict]:
    return db.query("SELECT category, count(*) AS count FROM videos GROUP BY category ORDER BY count DESC")


# ---- books ----------------------------------------------------------------

def list_books(*, subject_id: str | None = None, branch_id: str | None = None, q: str | None = None, limit: int = 80) -> list[dict]:
    clauses = ["1=1"]
    args: list[Any] = []
    if subject_id:
        clauses.append("b.subject_id = ?")
        args.append(subject_id)
    if branch_id:
        clauses.append("b.branch_id = ?")
        args.append(branch_id)
    if q:
        clauses.append("(b.title LIKE ? OR b.author LIKE ?)")
        args += [f"%{q}%"] * 2
    args.append(limit)
    rows = db.query(
        "SELECT b.*, s.name AS subject_name FROM books b LEFT JOIN subjects s ON s.id = b.subject_id "
        f"WHERE {' AND '.join(clauses)} ORDER BY b.title LIMIT ?",
        *args,
    )
    for row in rows:
        row["topics_data"] = _json(row.get("topics_covered"), [])
    return rows


# ---- resources ------------------------------------------------------------

def list_resources(
    *, kind: str | None = None, branch_id: str | None = None, subject_id: str | None = None,
    free_only: bool = False, q: str | None = None, limit: int = 80,
) -> list[dict]:
    clauses = ["1=1"]
    args: list[Any] = []
    if kind:
        clauses.append("r.kind = ?")
        args.append(kind)
    if branch_id:
        clauses.append("r.branch_id = ?")
        args.append(branch_id)
    if subject_id:
        clauses.append("r.subject_id = ?")
        args.append(subject_id)
    if free_only:
        clauses.append("r.is_free = 1")
    if q:
        clauses.append("(r.title LIKE ? OR r.description LIKE ?)")
        args += [f"%{q}%"] * 2
    args.append(limit)
    return db.query(
        "SELECT r.*, s.name AS subject_name, b.name AS branch_name FROM resources r "
        "LEFT JOIN subjects s ON s.id = r.subject_id LEFT JOIN branches b ON b.id = r.branch_id "
        f"WHERE {' AND '.join(clauses)} ORDER BY r.kind, r.title LIMIT ?",
        *args,
    )


def resource_kinds() -> list[dict]:
    return db.query("SELECT kind, count(*) AS count FROM resources GROUP BY kind ORDER BY kind")


def topic_resources(topic_id: str, subject_id: str | None = None) -> dict[str, list[dict]]:
    videos = db.query("SELECT * FROM videos WHERE topic_id = ? OR subject_id = ? ORDER BY rating DESC LIMIT 6", topic_id, subject_id)
    resources = db.query("SELECT * FROM resources WHERE subject_id = ? LIMIT 6", subject_id) if subject_id else []
    books = db.query("SELECT * FROM books WHERE subject_id = ? LIMIT 4", subject_id) if subject_id else []
    return {"videos": videos, "resources": resources, "books": books}


# ---- roadmaps -------------------------------------------------------------

def list_roadmaps(*, kind: str | None = None, branch_slug: str | None = None) -> list[dict]:
    clauses = ["1=1"]
    args: list[Any] = []
    if kind:
        clauses.append("r.kind = ?")
        args.append(kind)
    if branch_slug:
        clauses.append("(b.slug = ? OR r.branch_id IS NULL)")
        args.append(branch_slug)
    return db.query(
        "SELECT r.*, b.name AS branch_name, b.slug AS branch_slug, "
        "(SELECT count(*) FROM roadmap_nodes rn WHERE rn.roadmap_id = r.id) AS node_count "
        f"FROM roadmaps r LEFT JOIN branches b ON b.id = r.branch_id WHERE {' AND '.join(clauses)} "
        "ORDER BY r.order_index, r.title",
        *args,
    )


def get_roadmap(slug: str) -> dict | None:
    return db.query_one(
        "SELECT r.*, b.name AS branch_name, b.slug AS branch_slug FROM roadmaps r "
        "LEFT JOIN branches b ON b.id = r.branch_id WHERE r.slug = ?",
        slug,
    )


def roadmap_nodes(roadmap_id: str) -> list[dict]:
    return db.query("SELECT * FROM roadmap_nodes WHERE roadmap_id = ? ORDER BY order_index", roadmap_id)


# ---- flashcards -----------------------------------------------------------

def flashcards_for_topic(topic_id: str) -> list[dict]:
    return db.query("SELECT * FROM flashcards WHERE topic_id = ? ORDER BY rowid", topic_id)


def flashcard_by_id(flashcard_id: str) -> dict | None:
    return db.query_one("SELECT * FROM flashcards WHERE id = ?", flashcard_id)


def decks() -> list[dict]:
    return db.query("SELECT deck, count(*) AS count FROM flashcards GROUP BY deck ORDER BY count DESC")


def due_flashcards(user_id: str, limit: int = 20) -> list[dict]:
    from .security.ids import now_ms

    return db.query(
        "SELECT f.*, uf.ease_factor, uf.interval_days, uf.repetitions, uf.due_at FROM flashcards f "
        "LEFT JOIN user_flashcards uf ON uf.flashcard_id = f.id AND uf.user_id = ? "
        "WHERE uf.due_at IS NULL OR uf.due_at <= ? "
        "ORDER BY (uf.due_at IS NULL) DESC, uf.due_at LIMIT ?",
        user_id, now_ms(), limit,
    )


def flashcard_stats(user_id: str) -> dict[str, int]:
    from .security.ids import now_ms

    total = int(db.scalar("SELECT count(*) AS c FROM flashcards") or 0)
    studied = int(db.scalar("SELECT count(*) AS c FROM user_flashcards WHERE user_id = ?", user_id) or 0)
    due = int(db.scalar("SELECT count(*) AS c FROM user_flashcards WHERE user_id = ? AND due_at <= ?", user_id, now_ms()) or 0)
    return {"total": total, "studied": studied, "due": due}
