"""Practice: questions, Daily Practice Problems, submissions, mistakes (spec §14-§15, §68)."""
from __future__ import annotations

import json
from typing import Any

from . import db
from .security.ids import now_ms, today, ulid

DIFFICULTY_ORDER = {"easy": 0, "beginner": 0, "medium": 1, "hard": 2, "expert": 3}


def _json(value: Any, fallback: Any) -> Any:
    if value in (None, ""):
        return fallback
    if isinstance(value, (list, dict)):
        return value
    try:
        return json.loads(value)
    except (ValueError, TypeError):
        return fallback


def question_by_id(question_id: str) -> dict | None:
    return db.query_one("SELECT * FROM questions WHERE id = ? AND is_active = 1", question_id)


def question_by_slug(slug: str) -> dict | None:
    return db.query_one(
        "SELECT q.*, t.title AS topic_title, t.slug AS topic_slug, s.name AS subject_name, s.slug AS subject_slug "
        "FROM questions q LEFT JOIN topics t ON t.id = q.topic_id LEFT JOIN subjects s ON s.id = q.subject_id "
        "WHERE q.slug = ? AND q.is_active = 1",
        slug,
    )


def options_for(question_id: str, *, reveal: bool = False) -> list[dict]:
    rows = db.query("SELECT * FROM question_options WHERE question_id = ? ORDER BY order_index", question_id)
    if not reveal:
        for row in rows:
            row.pop("is_correct", None)
            row.pop("rationale", None)
    return rows


def public_question(question: dict, *, reveal: bool = False) -> dict:
    """Strips the answer unless the caller is allowed to see it."""
    payload = dict(question)
    payload["options"] = options_for(question["id"], reveal=reveal)
    if not reveal:
        for key in ("answer_index", "answer_text", "explanation"):
            payload.pop(key, None)
    payload["tags_data"] = _json(question.get("tags"), [])
    return payload


def questions_for_topic(topic_id: str, limit: int = 20) -> list[dict]:
    rows = db.query(
        "SELECT * FROM questions WHERE topic_id = ? AND is_active = 1 "
        "ORDER BY CASE difficulty WHEN 'easy' THEN 0 WHEN 'medium' THEN 1 WHEN 'hard' THEN 2 ELSE 3 END LIMIT ?",
        topic_id, limit,
    )
    return [public_question(row) for row in rows]


def list_questions(
    *, subject_id: str | None = None, topic_id: str | None = None, kind: str | None = None,
    difficulty: str | None = None, q: str | None = None, limit: int = 40, offset: int = 0,
) -> tuple[list[dict], int]:
    clauses = ["q.is_active = 1"]
    args: list[Any] = []
    if subject_id:
        clauses.append("q.subject_id = ?")
        args.append(subject_id)
    if topic_id:
        clauses.append("q.topic_id = ?")
        args.append(topic_id)
    if kind:
        clauses.append("q.kind = ?")
        args.append(kind)
    if difficulty:
        clauses.append("q.difficulty = ?")
        args.append(difficulty)
    if q:
        clauses.append("q.stem LIKE ?")
        args.append(f"%{q}%")
    where = " AND ".join(clauses)
    total = int(db.scalar(f"SELECT count(*) AS c FROM questions q WHERE {where}", *args) or 0)
    rows = db.query(
        "SELECT q.*, t.slug AS topic_slug, t.title AS topic_title, s.name AS subject_name, s.slug AS subject_slug "
        f"FROM questions q LEFT JOIN topics t ON t.id = q.topic_id LEFT JOIN subjects s ON s.id = q.subject_id "
        f"WHERE {where} ORDER BY q.difficulty, q.created_at DESC LIMIT ? OFFSET ?",
        *args, limit, offset,
    )
    return [public_question(row) for row in rows], total


# --------------------------------------------------------------------------
# DPP
# --------------------------------------------------------------------------

def dpp_for_date(date_str: str) -> dict | None:
    return db.query_one("SELECT * FROM dpp_sets WHERE date = ? AND published = 1", date_str)


def latest_dpp() -> dict | None:
    return db.query_one("SELECT * FROM dpp_sets WHERE published = 1 ORDER BY date DESC LIMIT 1")


def dpp_by_slug(slug: str) -> dict | None:
    return db.query_one(
        "SELECT * FROM dpp_sets WHERE (id = ? OR date = ?) AND published = 1", slug, slug
    )


def dpp_questions(set_id: str) -> list[dict]:
    rows = db.query(
        "SELECT q.*, dq.position FROM dpp_questions dq JOIN questions q ON q.id = dq.question_id "
        "WHERE dq.set_id = ? AND q.is_active = 1 ORDER BY dq.position",
        set_id,
    )
    return [public_question(row) for row in rows]


def calendar_today():
    """The app clock. The public reading copy replaces this with the visitor's clock."""
    from datetime import datetime, timezone

    return datetime.now(timezone.utc).date()


def practice_title(day) -> str:
    return f"Daily Practice - {day.day} {day.strftime('%B %Y')}"


def published_sets() -> list[dict]:
    return db.query("SELECT * FROM dpp_sets WHERE published = 1 ORDER BY date")


def set_for_calendar_day(date_str: str) -> tuple[dict | None, bool]:
    """The set published for that day, or a stable set from the library if none was.

    A visit weeks later still has questions. The caller labels them with the
    requested calendar day rather than the day the set was seeded.
    """
    from datetime import date as date_cls

    try:
        day = date_cls.fromisoformat(date_str)
    except ValueError:
        return None, False
    exact = dpp_for_date(date_str)
    if exact:
        return exact, False
    sets = published_sets()
    if not sets:
        return None, False
    return sets[day.toordinal() % len(sets)], True


def dpp_with_context(date_str: str | None = None) -> dict | None:
    """The practice set for a calendar day, defaulting to today.

    This used to fall back to the newest seeded set, which is several days
    ahead of the seed clock. The heading is always the requested day.
    """
    if not date_str:
        date_str = calendar_today().isoformat()
    row, rotated = set_for_calendar_day(date_str)
    if not row:
        return None
    from datetime import date as date_cls

    day = date_cls.fromisoformat(date_str)
    shown = dict(row)
    shown["title"] = practice_title(day)
    shown["date"] = date_str
    subject = (
        db.query_one("SELECT name, slug FROM subjects WHERE id = ?", row["subject_id"])
        if row["subject_id"]
        else None
    )
    questions = dpp_questions(row["id"])
    return {
        "set": shown,
        "subject": subject,
        "questions": questions,
        "count": len(questions),
        "rotated": rotated,
        "source_date": row["date"],
        "calendar_date": date_str,
    }


def recent_practice_days(count: int = 14) -> list[dict]:
    """The last `count` calendar days, each with a set a visitor can open."""
    from datetime import timedelta

    today = calendar_today()
    days: list[dict] = []
    for offset in range(max(1, count)):
        day = today - timedelta(days=offset)
        iso = day.isoformat()
        row, rotated = set_for_calendar_day(iso)
        if not row:
            continue
        question_count = int(db.scalar(
            "SELECT count(*) AS c FROM dpp_questions WHERE set_id = ?", row["id"]
        ) or 0)
        days.append({
            "date": iso,
            "title": f"{day.day} {day.strftime('%B %Y')}",
            "question_count": question_count,
            "duration_minutes": row["duration_minutes"],
            "rotated": rotated,
        })
    return days


def list_dpp_sets(limit: int = 30) -> list[dict]:
    return db.query(
        "SELECT d.*, s.name AS subject_name, s.slug AS subject_slug, "
        "(SELECT count(*) FROM dpp_questions dq WHERE dq.set_id = d.id) AS question_count "
        "FROM dpp_sets d LEFT JOIN subjects s ON s.id = d.subject_id "
        "WHERE d.published = 1 ORDER BY d.date DESC LIMIT ?",
        limit,
    )


def user_dpp_state(user_id: str, set_id: str) -> dict:
    rows = db.query(
        "SELECT question_id, is_correct, answer_index, answer_text FROM submissions "
        "WHERE user_id = ? AND dpp_set_id = ?",
        user_id, set_id,
    )
    answered = {row["question_id"]: row for row in rows}
    return {
        "answered": answered,
        "count": len(answered),
        "correct": sum(1 for row in rows if row["is_correct"]),
    }


# --------------------------------------------------------------------------
# Submission recording
# --------------------------------------------------------------------------

def grade(question: dict, option_index: int | None, answer_text: str | None) -> tuple[bool, str]:
    options = db.query(
        "SELECT id, label, is_correct FROM question_options WHERE question_id = ? ORDER BY order_index",
        question["id"],
    )
    if options:
        chosen = options[option_index] if option_index is not None and 0 <= option_index < len(options) else None
        correct = bool(chosen and chosen["is_correct"])
        correct_label = next((o["label"] for o in options if o["is_correct"]), "")
        return correct, correct_label

    expected = (question.get("answer_text") or "").strip()
    if not expected:
        return False, ""
    given = (answer_text or "").strip()
    try:
        expected_value = float(expected)
        given_value = float(given)
        tolerance = float(question.get("tolerance") or 0.02)
        return abs(given_value - expected_value) <= max(abs(expected_value) * tolerance, 1e-9), expected
    except ValueError:
        return given.lower() == expected.lower(), expected


def record_answer(
    user_id: str,
    question_id: str,
    *,
    option_index: int | None = None,
    answer_text: str | None = None,
    time_ms: int | None = None,
    set_id: str | None = None,
) -> dict:
    """Grades and stores one answer. Returns the graded outcome (no answer leaked on failure paths)."""
    question = question_by_id(question_id)
    if question is None:
        raise ValueError("unknown question")

    correct, correct_label = grade(question, option_index, answer_text)
    options = db.query(
        "SELECT label FROM question_options WHERE question_id = ? ORDER BY order_index", question_id
    )
    given = (
        options[option_index]["label"]
        if options and option_index is not None and 0 <= option_index < len(options)
        else (answer_text or "")
    )

    ts = now_ms()
    with db.transaction():
        db.execute(
            "INSERT INTO submissions (id,user_id,question_id,dpp_set_id,answer_index,answer_text,is_correct,time_ms,created_at) "
            "VALUES (?,?,?,?,?,?,?,?,?)",
            ulid(), user_id, question_id, set_id, option_index, answer_text, 1 if correct else 0, time_ms, ts,
        )
        if not correct:
            db.execute(
                "INSERT INTO mistakes (id,user_id,question_id,given,correct,created_at) VALUES (?,?,?,?,?,?) "
                "ON CONFLICT(user_id,question_id) DO UPDATE SET given=excluded.given, correct=excluded.correct, "
                "resolved_at=NULL, created_at=excluded.created_at",
                ulid(), user_id, question_id, given[:400], correct_label[:400], ts,
            )
        else:
            db.execute(
                "UPDATE mistakes SET resolved_at = ? WHERE user_id = ? AND question_id = ? AND resolved_at IS NULL",
                ts, user_id, question_id,
            )

    xp = {"easy": 5, "beginner": 5, "medium": 10, "hard": 15, "expert": 25}.get(question["difficulty"], 10) if correct else 1

    from .progress import award_xp, bump_activity, evaluate_badges, update_topic_mastery

    award_xp(user_id, xp, "question.correct" if correct else "question.attempt", "question", question_id)
    bump_activity(user_id, "questions_solved", minutes=1, xp=xp)
    if question.get("topic_id"):
        update_topic_mastery(user_id, question["topic_id"])
    evaluate_badges(user_id)

    return {
        "correct": correct,
        "correctLabel": correct_label,
        "explanation": question.get("explanation"),
        "xp": xp,
        "topicSlug": db.scalar("SELECT slug AS s FROM topics WHERE id = ?", question.get("topic_id"), default=None),
    }


def topic_accuracy(user_id: str, topic_id: str) -> dict:
    row = db.query_one(
        "SELECT count(*) AS total, COALESCE(sum(is_correct),0) AS correct FROM submissions s "
        "JOIN questions q ON q.id = s.question_id WHERE s.user_id = ? AND q.topic_id = ?",
        user_id, topic_id,
    ) or {"total": 0, "correct": 0}
    total = int(row["total"] or 0)
    correct = int(row["correct"] or 0)
    return {"total": total, "correct": correct, "accuracy": round(correct / total * 100) if total else 0}


def mistake_notebook(
    user_id: str, *, topic_id: str | None = None, kind: str | None = None,
    difficulty: str | None = None, limit: int = 60,
) -> list[dict]:
    clauses = ["m.user_id = ?"]
    args: list[Any] = [user_id]
    if topic_id:
        clauses.append("q.topic_id = ?")
        args.append(topic_id)
    if kind:
        clauses.append("q.kind = ?")
        args.append(kind)
    if difficulty:
        clauses.append("q.difficulty = ?")
        args.append(difficulty)
    args.append(limit)
    return db.query(
        "SELECT m.id, m.question_id, m.given, m.correct, m.created_at, m.resolved_at, q.slug AS question_slug, "
        "q.stem, q.difficulty, q.kind, q.explanation, t.title AS topic_title, t.slug AS topic_slug, s.name AS subject "
        f"FROM mistakes m JOIN questions q ON q.id = m.question_id "
        f"LEFT JOIN topics t ON t.id = q.topic_id LEFT JOIN subjects s ON s.id = t.subject_id "
        f"WHERE {' AND '.join(clauses)} ORDER BY (m.resolved_at IS NOT NULL), m.created_at DESC LIMIT ?",
        *args,
    )


def question_kinds() -> list[dict]:
    return db.query("SELECT kind, count(*) AS count FROM questions WHERE is_active=1 GROUP BY kind ORDER BY count DESC")
