"""Spaced repetition (spec §27) - SM-2 with an ease-factor floor."""
from __future__ import annotations

from . import db
from .security.ids import now_ms

DAY = 86_400_000
RATINGS = ("again", "hard", "good", "easy")


def review(user_id: str, flashcard_id: str, rating: str) -> dict:
    if rating not in RATINGS:
        raise ValueError(f"rating must be one of {RATINGS}")

    existing = db.query_one(
        "SELECT ease_factor, interval_days, repetitions FROM user_flashcards WHERE user_id = ? AND flashcard_id = ?",
        user_id, flashcard_id,
    )
    ease = float(existing["ease_factor"]) if existing else 2.5
    interval = float(existing["interval_days"]) if existing else 0.0
    repetitions = int(existing["repetitions"]) if existing else 0

    if rating == "again":
        repetitions = 0
        interval = 0.0
        ease = max(1.3, ease - 0.2)
    elif rating == "hard":
        repetitions += 1
        interval = 1.0 if repetitions == 1 else max(1.0, interval * 1.2)
        ease = max(1.3, ease - 0.15)
    elif rating == "good":
        repetitions += 1
        interval = 1.0 if repetitions == 1 else (6.0 if repetitions == 2 else interval * ease)
    else:  # easy
        repetitions += 1
        interval = 3.0 if repetitions == 1 else interval * ease * 1.3
        ease += 0.15

    interval = min(max(interval, 0.0007 if rating == "again" else 1.0), 730.0)
    due_at = now_ms() + (10 * 60_000 if rating == "again" else int(interval * DAY))

    db.execute(
        "INSERT INTO user_flashcards (user_id,flashcard_id,ease_factor,interval_days,repetitions,due_at,last_reviewed_at) "
        "VALUES (?,?,?,?,?,?,?) "
        "ON CONFLICT(user_id,flashcard_id) DO UPDATE SET ease_factor=excluded.ease_factor, "
        "interval_days=excluded.interval_days, repetitions=excluded.repetitions, due_at=excluded.due_at, "
        "last_reviewed_at=excluded.last_reviewed_at",
        user_id, flashcard_id, ease, interval, repetitions, due_at, now_ms(),
    )

    from .progress import award_xp, bump_activity

    award_xp(user_id, 2, "flashcard.reviewed", "flashcard", flashcard_id)
    bump_activity(user_id, "revisions", minutes=1, xp=2)
    return {"ease": ease, "intervalDays": interval, "repetitions": repetitions, "dueAt": due_at}


def due_count(user_id: str) -> int:
    return int(db.scalar("SELECT count(*) AS c FROM user_flashcards WHERE user_id = ? AND due_at <= ?", user_id, now_ms()) or 0)
