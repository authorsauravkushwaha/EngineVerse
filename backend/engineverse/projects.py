"""Real-world project hub (spec §19-§22)."""
from __future__ import annotations

import json
from typing import Any

from . import db
from .security.ids import now_ms


def _json(value: Any, fallback: Any) -> Any:
    if value in (None, ""):
        return fallback
    if isinstance(value, (list, dict)):
        return value
    try:
        return json.loads(value)
    except (ValueError, TypeError):
        return fallback


def list_projects(
    *, difficulty: str | None = None, category: str | None = None, branch: str | None = None,
    q: str | None = None, limit: int = 60,
) -> list[dict]:
    clauses = ["p.status = 'published'"]
    args: list[Any] = []
    if difficulty:
        clauses.append("p.difficulty = ?")
        args.append(difficulty)
    if category:
        clauses.append("p.category = ?")
        args.append(category)
    if branch:
        clauses.append("b.slug = ?")
        args.append(branch)
    if q:
        clauses.append("(p.title LIKE ? OR p.summary LIKE ? OR p.tech LIKE ?)")
        args += [f"%{q}%"] * 3
    args.append(limit)
    rows = db.query(
        "SELECT p.*, b.name AS branch_name, b.slug AS branch_slug FROM projects p "
        f"LEFT JOIN branches b ON b.id = p.branch_id WHERE {' AND '.join(clauses)} "
        "ORDER BY p.order_index, p.title LIMIT ?",
        *args,
    )
    for row in rows:
        row["tech_data"] = _json(row.get("tech"), [])
        row["skills_data"] = _json(row.get("skills"), [])
    return rows


def get_project(slug: str) -> dict | None:
    row = db.query_one(
        "SELECT p.*, b.name AS branch_name, b.slug AS branch_slug, s.name AS subject_name, s.slug AS subject_slug "
        "FROM projects p LEFT JOIN branches b ON b.id = p.branch_id LEFT JOIN subjects s ON s.id = p.subject_id "
        "WHERE p.slug = ? AND p.status = 'published'",
        slug,
    )
    if not row:
        return None
    for key, column in (("tech_data", "tech"), ("skills_data", "skills"), ("interview_data", "interview_questions"), ("prereq_data", "prerequisites")):
        row[key] = _json(row.get(column), [])
    row["steps"] = steps(row["id"])
    row["resources"] = resources(row["id"])
    return row


def steps(project_id: str) -> list[dict]:
    return db.query(
        "SELECT id, phase, title, body, order_index FROM project_steps WHERE project_id = ? ORDER BY order_index",
        project_id,
    )


def resources(project_id: str) -> list[dict]:
    return db.query(
        "SELECT id, kind, title, url, note FROM project_resources WHERE project_id = ? ORDER BY rowid", project_id
    )


def categories() -> list[dict]:
    return db.query(
        "SELECT category, count(*) AS count FROM projects WHERE status='published' GROUP BY category ORDER BY count DESC"
    )


def difficulties() -> list[dict]:
    return db.query(
        "SELECT difficulty, count(*) AS count FROM projects WHERE status='published' GROUP BY difficulty ORDER BY count DESC"
    )


def record_build(user_id: str, project_id: str) -> None:
    db.execute("UPDATE projects SET build_count = build_count + 1 WHERE id = ?", project_id)
    from .progress import bump_activity

    bump_activity(user_id, "projects_touched", minutes=30, xp=5)


def suggested_for(user_id: str | None, limit: int = 3) -> list[dict]:
    branch_id = db.scalar("SELECT branch_id AS b FROM profiles WHERE user_id = ?", user_id, default=None) if user_id else None
    return db.query(
        "SELECT slug, title, difficulty, summary, category, est_hours FROM projects "
        "WHERE status='published' AND (? IS NULL OR branch_id = ?) "
        "ORDER BY CASE WHEN branch_id = ? THEN 0 ELSE 1 END, order_index LIMIT ?",
        branch_id, branch_id, branch_id, limit,
    )
