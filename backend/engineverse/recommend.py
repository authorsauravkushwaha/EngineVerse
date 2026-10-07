"""Content recommendations (spec §54, §78).

Recommendations are derived from the learner's own data - weak topics, recent
activity, subject progress - and always point at real catalogue rows.
"""
from __future__ import annotations

from typing import Any

from . import catalog, db, practice, progress


def for_topic(topic: dict, user_id: str | None = None) -> list[dict[str, Any]]:
    items: list[dict[str, Any]] = []
    topic_id = topic["id"]

    question_count = int(
        db.scalar("SELECT count(*) AS c FROM questions WHERE topic_id = ? AND is_active = 1", topic_id) or 0
    )
    if question_count:
        items.append({
            "kind": "practice", "title": f"Practice {topic['title']}",
            "url": f"/practice?topic={topic['slug']}",
            "reason": f"{question_count} questions to lock this concept in.",
        })

    formula = db.query_one("SELECT slug, name FROM formulas WHERE topic_id = ? LIMIT 1", topic_id)
    if formula:
        items.append({
            "kind": "formula", "title": f"{formula['name']} formula card",
            "url": f"/formulas#{formula['slug']}", "reason": "Keep the equation one glance away.",
        })

    video = db.query_one(
        "SELECT slug, title FROM videos WHERE topic_id = ? ORDER BY rating DESC LIMIT 1", topic_id
    )
    if video:
        items.append({
            "kind": "video", "title": video["title"], "url": f"/videos?q={video['slug']}",
            "reason": "Highest rated video for this topic.",
        })

    cards = int(db.scalar("SELECT count(*) AS c FROM flashcards WHERE topic_id = ?", topic_id) or 0)
    if cards:
        items.append({
            "kind": "revision", "title": f"{cards} flashcards to revise", "url": "/flashcards",
            "reason": "Spaced repetition beats re-reading.",
        })

    project = db.query_one(
        "SELECT p.slug, p.title FROM projects p WHERE p.subject_id = ? AND p.status='published' "
        "ORDER BY p.order_index LIMIT 1",
        topic["subject_id"],
    )
    if project:
        items.append({
            "kind": "project", "title": project["title"], "url": f"/projects/{project['slug']}",
            "reason": "Apply it in a real build.",
        })

    interview = db.query_one(
        "SELECT slug FROM questions WHERE topic_id = ? AND kind = 'interview' AND is_active = 1 LIMIT 1", topic_id
    )
    if interview:
        items.append({
            "kind": "interview", "title": "Interview questions on this topic",
            "url": f"/practice/questions/{interview['slug']}", "reason": "Recruiters ask exactly this.",
        })

    siblings = catalog.topic_siblings(topic["subject_id"], topic["order_index"])
    if siblings.get("next"):
        items.append({
            "kind": "next_topic", "title": siblings["next"]["title"],
            "url": f"/topics/{siblings['next']['slug']}", "reason": "Next topic in this subject.",
        })

    if user_id:
        accuracy = practice.topic_accuracy(user_id, topic_id)
        if accuracy["total"] >= 2 and accuracy["accuracy"] < 60:
            items.insert(0, {
                "kind": "revision",
                "title": f"Your accuracy here is {accuracy['accuracy']}%",
                "url": "/revision",
                "reason": "Review the mistakes notebook and retry these questions.",
            })
    return items[:8]


def dashboard(user_id: str) -> dict[str, Any]:
    weak = progress.weak_topics(user_id, 3)
    continue_rows = progress.continue_learning(user_id, 3)
    profile = db.query_one("SELECT branch_id, semester_id FROM profiles WHERE user_id = ?", user_id) or {}

    lessons: list[dict] = []
    if continue_rows:
        lessons = continue_rows
    else:
        rows = db.query(
            "SELECT t.slug, t.title, t.difficulty, s.name AS subject, s.slug AS subject_slug "
            "FROM topics t JOIN subjects s ON s.id = t.subject_id "
            "WHERE t.status='published' AND (? IS NULL OR s.branch_id = ?) "
            "ORDER BY t.order_index LIMIT 3",
            profile.get("branch_id"), profile.get("branch_id"),
        )
        lessons = rows

    subject_rows = []
    if profile.get("branch_id"):
        subjects = db.query(
            "SELECT id, slug, name FROM subjects WHERE branch_id = ? AND status='published' LIMIT 6",
            profile["branch_id"],
        )
        for subject in subjects:
            state = progress.subject_progress(user_id, subject["id"])
            subject_rows.append({**subject, **state})

    return {
        "weak": weak,
        "continue": continue_rows,
        "lessons": lessons,
        "subjects": subject_rows,
        "projects": db.query(
            "SELECT slug, title, difficulty, summary, category FROM projects WHERE status='published' "
            "AND (? IS NULL OR branch_id = ?) ORDER BY order_index LIMIT 3",
            profile.get("branch_id"), profile.get("branch_id"),
        ),
    }


def next_topics_for(user_id: str, limit: int = 5) -> list[dict]:
    """Un-started topics in the learner's subjects, in syllabus order."""
    profile = db.query_one("SELECT branch_id FROM profiles WHERE user_id = ?", user_id) or {}
    return db.query(
        "SELECT t.slug, t.title, t.difficulty, t.est_minutes, s.name AS subject, s.slug AS subject_slug "
        "FROM topics t JOIN subjects s ON s.id = t.subject_id "
        "WHERE t.status='published' AND (? IS NULL OR s.branch_id = ?) "
        "AND t.id NOT IN (SELECT topic_id FROM user_progress WHERE user_id = ?) "
        "ORDER BY s.order_index, t.order_index LIMIT ?",
        profile.get("branch_id"), profile.get("branch_id"), user_id, limit,
    )


def retry_plan(user_id: str) -> list[dict]:
    """Builds the 'you keep failing X' recovery plan described in spec §78."""
    plan: list[dict] = []
    for weak in progress.weak_topics(user_id, 3):
        topic = catalog.get_topic(weak["slug"])
        if not topic:
            continue
        cards = int(db.scalar("SELECT count(*) AS c FROM flashcards WHERE topic_id = ?", topic["id"]) or 0)
        easy = int(
            db.scalar(
                "SELECT count(*) AS c FROM questions WHERE topic_id = ? AND difficulty IN ('easy','beginner') AND is_active = 1",
                topic["id"],
            )
            or 0
        )
        plan.append({
            "topic": weak,
            "message": f"Your {weak['subject']} · {weak['title']} accuracy is {weak['accuracy']}%.",
            "steps": [
                {"label": "Re-read the note", "url": f"/topics/{weak['slug']}"},
                {"label": f"Solve {max(easy, 1)} easy questions", "url": f"/practice?topic={weak['slug']}&difficulty=easy"},
                {"label": "Revise with flashcards", "url": "/flashcards"},
                {"label": "Retry today's DPP", "url": "/dpp/today"},
            ],
            "flashcards": cards,
            "easyQuestions": easy,
        })
    return plan
