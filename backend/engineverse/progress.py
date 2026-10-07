"""XP, levels, streaks, badges, heatmaps, weak areas and certificates (spec §34-§36, §55, §68)."""
from __future__ import annotations

import json
from datetime import date, timedelta
from typing import Any

from . import db
from .security.ids import now_ms, today, ulid

DAY = 86_400_000

ENGINEERING_RANKS = (
    (1, "First-Year Explorer"),
    (3, "Circuit Beginner"),
    (5, "Problem Solver"),
    (8, "Concept Builder"),
    (12, "Circuit Builder"),
    (16, "Systems Thinker"),
    (20, "Algorithm Architect"),
    (25, "Design Engineer"),
    (32, "Core Engineering Master"),
    (40, "Principal Engineer"),
)

ACTIVITY_FIELDS = ("notes_studied", "questions_solved", "coding_submissions", "projects_touched", "revisions")


def xp_for_level(level: int) -> int:
    return sum(100 + (lvl - 1) * 60 for lvl in range(1, max(1, level)))


def level_from_xp(xp: int) -> int:
    level = 1
    while xp_for_level(level + 1) <= xp:
        level += 1
    return level


def level_progress(xp: int) -> dict[str, int]:
    level = level_from_xp(xp)
    current = xp_for_level(level)
    nxt = xp_for_level(level + 1)
    span = max(1, nxt - current)
    return {
        "level": level,
        "current": current,
        "next": nxt,
        "pct": max(0, min(100, round((xp - current) / span * 100))),
        "intoLevel": xp - current,
        "neededForNext": max(0, nxt - xp),
    }


def rank_name(level: int) -> str:
    name = ENGINEERING_RANKS[0][1]
    for minimum, label in ENGINEERING_RANKS:
        if level >= minimum:
            name = label
    return name


def total_xp(user_id: str) -> int:
    return int(db.scalar("SELECT total_xp AS v FROM streaks WHERE user_id = ?", user_id, default=0) or 0)


def award_xp(user_id: str, amount: int, reason: str, entity_type: str | None = None, entity_id: str | None = None) -> int:
    clean = max(0, min(500, round(amount)))
    if clean <= 0:
        return 0
    ts = now_ms()
    with db.transaction():
        db.execute(
            "INSERT INTO xp_events (id,user_id,amount,reason,entity_type,entity_id,created_at) VALUES (?,?,?,?,?,?,?)",
            ulid(), user_id, clean, reason, entity_type, entity_id, ts,
        )
        new_total = total_xp(user_id) + clean
        db.execute(
            "INSERT INTO streaks (user_id,total_xp,level) VALUES (?,?,?) "
            "ON CONFLICT(user_id) DO UPDATE SET total_xp = excluded.total_xp, "
            "level = MAX(streaks.level, excluded.level)",
            user_id, new_total, level_from_xp(new_total),
        )
    return clean


def bump_activity(user_id: str, field: str, *, minutes: int = 0, xp: int = 0) -> None:
    if field not in ACTIVITY_FIELDS:
        raise ValueError(f"unknown activity field: {field}")
    db.execute(
        f"INSERT INTO activity (user_id,day,{field},minutes,xp) VALUES (?,?,?,?,?) "
        f"ON CONFLICT(user_id,day) DO UPDATE SET {field} = activity.{field} + 1, "
        "minutes = activity.minutes + excluded.minutes, xp = activity.xp + excluded.xp",
        user_id, today(), 1, minutes, xp,
    )


def mark_topic_viewed(user_id: str, topic_id: str, minutes: int = 0) -> None:
    db.execute(
        "INSERT INTO user_progress (user_id,topic_id,status,mastery,time_spent_s,last_viewed_at) "
        "VALUES (?,?,'started',0,?,?) "
        "ON CONFLICT(user_id,topic_id) DO UPDATE SET last_viewed_at = excluded.last_viewed_at, "
        "time_spent_s = user_progress.time_spent_s + excluded.time_spent_s, "
        "status = CASE WHEN user_progress.status = 'started' THEN 'in_progress' ELSE user_progress.status END",
        user_id, topic_id, minutes * 60, now_ms(),
    )
    bump_activity(user_id, "notes_studied", minutes=max(1, minutes), xp=2)
    award_xp(user_id, 2, "topic.viewed", "topic", topic_id)
    touch_streak(user_id)


def complete_topic(user_id: str, topic_id: str) -> None:
    db.execute(
        "INSERT INTO user_progress (user_id,topic_id,status,mastery,completed_at,last_viewed_at) "
        "VALUES (?,?,'completed',60,?,?) "
        "ON CONFLICT(user_id,topic_id) DO UPDATE SET status='completed', "
        "mastery = MAX(user_progress.mastery, 60), "
        "completed_at = COALESCE(user_progress.completed_at, excluded.completed_at), "
        "last_viewed_at = excluded.last_viewed_at",
        user_id, topic_id, now_ms(), now_ms(),
    )
    award_xp(user_id, 20, "topic.completed", "topic", topic_id)
    bump_activity(user_id, "notes_studied", minutes=5, xp=20)
    evaluate_badges(user_id)


def update_topic_mastery(user_id: str, topic_id: str) -> None:
    row = db.query_one(
        "SELECT COALESCE(sum(s.is_correct),0) AS correct, count(*) AS total FROM submissions s "
        "JOIN questions q ON q.id = s.question_id WHERE s.user_id = ? AND q.topic_id = ?",
        user_id, topic_id,
    ) or {"correct": 0, "total": 0}
    total = int(row["total"] or 0)
    correct = int(row["correct"] or 0)
    accuracy = round(correct / total * 100) if total else 0
    mastery = max(25, min(100, round(accuracy * 0.7 + min(total, 10) * 3)))
    status = "mastered" if mastery >= 85 else ("completed" if mastery >= 50 else "in_progress")
    db.execute(
        "INSERT INTO user_progress (user_id,topic_id,status,mastery,last_viewed_at) VALUES (?,?,?,?,?) "
        "ON CONFLICT(user_id,topic_id) DO UPDATE SET mastery = MAX(user_progress.mastery, excluded.mastery), "
        "status = excluded.status, last_viewed_at = excluded.last_viewed_at",
        user_id, topic_id, status, mastery, now_ms(),
    )


def topic_progress(user_id: str, topic_id: str) -> dict | None:
    return db.query_one("SELECT * FROM user_progress WHERE user_id = ? AND topic_id = ?", user_id, topic_id)


def touch_streak(user_id: str) -> int:
    from .auth import touch_streak as _touch

    return _touch(user_id)


# --------------------------------------------------------------------------
# Stats
# --------------------------------------------------------------------------

def user_stats(user_id: str) -> dict[str, Any]:
    streak = db.query_one(
        "SELECT total_xp, level, current_streak, longest_streak FROM streaks WHERE user_id = ?", user_id
    ) or {"total_xp": 0, "level": 1, "current_streak": 0, "longest_streak": 0}

    questions = db.query_one(
        "SELECT count(*) AS total, COALESCE(sum(is_correct),0) AS correct FROM submissions WHERE user_id = ?", user_id
    ) or {"total": 0, "correct": 0}
    coding = db.query_one(
        "SELECT count(*) AS total, COALESCE(sum(is_accepted),0) AS accepted, "
        "count(DISTINCT CASE WHEN is_accepted = 1 THEN problem_id END) AS solved "
        "FROM coding_submissions WHERE user_id = ?",
        user_id,
    ) or {"total": 0, "accepted": 0, "solved": 0}
    progress = db.query_one(
        "SELECT COALESCE(sum(CASE WHEN status IN ('completed','mastered') THEN 1 ELSE 0 END),0) AS completed, "
        "count(*) AS started FROM user_progress WHERE user_id = ?",
        user_id,
    ) or {"completed": 0, "started": 0}

    total_questions = int(questions["total"] or 0)
    correct = int(questions["correct"] or 0)
    xp = int(streak["total_xp"] or 0)
    level = level_from_xp(xp)

    return {
        "xp": xp,
        "level": level,
        "rank": rank_name(level),
        "levelPct": level_progress(xp)["pct"],
        "neededForNext": level_progress(xp)["neededForNext"],
        "currentStreak": int(streak["current_streak"] or 0),
        "longestStreak": int(streak["longest_streak"] or 0),
        "questionsAnswered": total_questions,
        "questionsCorrect": correct,
        "accuracy": round(correct / total_questions * 100) if total_questions else 0,
        "codingSubmissions": int(coding["total"] or 0),
        "codingAccepted": int(coding["accepted"] or 0),
        "problemsSolved": int(coding["solved"] or 0),
        "topicsCompleted": int(progress["completed"] or 0),
        "topicsStarted": int(progress["started"] or 0),
        "minutes": int(db.scalar("SELECT COALESCE(sum(minutes),0) AS m FROM activity WHERE user_id = ?", user_id) or 0),
        "bookmarks": int(db.scalar("SELECT count(*) AS c FROM bookmarks WHERE user_id = ?", user_id) or 0),
        "badges": int(db.scalar("SELECT count(*) AS c FROM user_badges WHERE user_id = ?", user_id) or 0),
        "dppCompleted": int(
            db.scalar("SELECT count(DISTINCT dpp_set_id) AS c FROM submissions WHERE user_id = ? AND dpp_set_id IS NOT NULL", user_id) or 0
        ),
    }


def subject_progress(user_id: str, subject_id: str) -> dict[str, Any]:
    row = db.query_one(
        "SELECT count(*) AS total, "
        "COALESCE(sum(CASE WHEN up.status IN ('completed','mastered') THEN 1 ELSE 0 END),0) AS done, "
        "COALESCE(avg(up.mastery),0) AS mastery FROM topics t "
        "LEFT JOIN user_progress up ON up.topic_id = t.id AND up.user_id = ? "
        "WHERE t.subject_id = ? AND t.status='published'",
        user_id, subject_id,
    ) or {"total": 0, "done": 0, "mastery": 0}
    total = int(row["total"] or 0)
    done = int(row["done"] or 0)
    return {
        "total": total,
        "completed": done,
        "pct": round(done / total * 100) if total else 0,
        "mastery": round(float(row["mastery"] or 0)),
    }


def heatmap(user_id: str, days: int = 182) -> list[dict]:
    rows = db.query(
        "SELECT day, notes_studied, questions_solved, coding_submissions, revisions, projects_touched, minutes, xp "
        "FROM activity WHERE user_id = ?",
        user_id,
    )
    by_day = {row["day"]: row for row in rows}
    start = date.today() - timedelta(days=days - 1)
    out = []
    for offset in range(days):
        day = (start + timedelta(days=offset)).isoformat()
        row = by_day.get(day)
        count = 0
        if row:
            count = sum(int(row[field] or 0) for field in ACTIVITY_FIELDS)
        out.append(
            {
                "day": day,
                "count": count,
                "minutes": int(row["minutes"] or 0) if row else 0,
                "xp": int(row["xp"] or 0) if row else 0,
            }
        )
    return out


def weak_topics(user_id: str, limit: int = 5) -> list[dict]:
    return db.query(
        "SELECT q.topic_id, t.title, t.slug, sub.name AS subject, sub.slug AS subject_slug, "
        "CAST(100.0 * sum(sm.is_correct) / count(*) AS INTEGER) AS accuracy, count(*) AS attempts "
        "FROM submissions sm JOIN questions q ON q.id = sm.question_id "
        "JOIN topics t ON t.id = q.topic_id JOIN subjects sub ON sub.id = t.subject_id "
        "WHERE sm.user_id = ? AND q.topic_id IS NOT NULL "
        "GROUP BY q.topic_id HAVING attempts >= 2 ORDER BY accuracy ASC, attempts DESC LIMIT ?",
        user_id, limit,
    )


def continue_learning(user_id: str, limit: int = 5) -> list[dict]:
    return db.query(
        "SELECT t.slug, t.title, t.difficulty, up.status, up.mastery, up.last_viewed_at, "
        "s.name AS subject, s.slug AS subject_slug "
        "FROM user_progress up JOIN topics t ON t.id = up.topic_id JOIN subjects s ON s.id = t.subject_id "
        "WHERE up.user_id = ? AND up.status IN ('started','in_progress') "
        "ORDER BY up.last_viewed_at DESC LIMIT ?",
        user_id, limit,
    )


def weekly_stats(user_id: str) -> dict[str, int]:
    cutoff = now_ms() - 7 * DAY
    row = db.query_one(
        "SELECT COALESCE(sum(questions_solved),0) AS q, COALESCE(sum(notes_studied),0) AS n, "
        "COALESCE(sum(coding_submissions),0) AS c, COALESCE(sum(projects_touched),0) AS p, "
        "COALESCE(sum(revisions),0) AS r, COALESCE(sum(minutes),0) AS m, COALESCE(sum(xp),0) AS x "
        "FROM activity WHERE user_id = ? AND day >= ?",
        user_id, (date.today() - timedelta(days=6)).isoformat(),
    ) or {}
    total_questions = int(
        db.scalar(
            "SELECT count(*) AS c FROM submissions WHERE user_id = ? AND created_at > ?", user_id, cutoff
        )
        or 0
    )
    correct = int(
        db.scalar(
            "SELECT COALESCE(sum(is_correct),0) AS c FROM submissions WHERE user_id = ? AND created_at > ?",
            user_id, cutoff,
        )
        or 0
    )
    return {
        "questions": total_questions,
        "notes": int(row.get("n") or 0),
        "coding": int(row.get("c") or 0),
        "projects": int(row.get("p") or 0),
        "revisions": int(row.get("r") or 0),
        "minutes": int(row.get("m") or 0),
        "xp": int(row.get("x") or 0),
        "accuracy": round(correct / total_questions * 100) if total_questions else 0,
    }


# --------------------------------------------------------------------------
# Badges
# --------------------------------------------------------------------------

def _count(sql: str, *args: Any) -> int:
    return int(db.scalar(sql, *args) or 0)


BADGES: list[dict[str, Any]] = [
    {
        "slug": "first-dpp", "name": "First DPP", "icon": "flame", "tier": "bronze",
        "description": "Completed your first Daily Practice Problem set.",
        "check": lambda u: _count("SELECT count(DISTINCT dpp_set_id) AS c FROM submissions WHERE user_id = ? AND dpp_set_id IS NOT NULL", u) >= 1,
    },
    {
        "slug": "problems-100", "name": "Century Club", "icon": "target", "tier": "silver",
        "description": "Answered 100 practice questions.",
        "check": lambda u: _count("SELECT count(*) AS c FROM submissions WHERE user_id = ?", u) >= 100,
    },
    {
        "slug": "streak-7", "name": "7-Day Streak", "icon": "zap", "tier": "silver",
        "description": "Studied 7 days in a row.",
        "check": lambda u: _count("SELECT longest_streak AS c FROM streaks WHERE user_id = ?", u) >= 7,
    },
    {
        "slug": "streak-30", "name": "30-Day Streak", "icon": "flame", "tier": "gold",
        "description": "Studied 30 days in a row.",
        "check": lambda u: _count("SELECT longest_streak AS c FROM streaks WHERE user_id = ?", u) >= 30,
    },
    {
        "slug": "first-project", "name": "First Build", "icon": "hammer", "tier": "bronze",
        "description": "Saved or started your first real-world project.",
        "check": lambda u: _count("SELECT count(*) AS c FROM bookmarks WHERE user_id = ? AND entity_type='project'", u) >= 1,
    },
    {
        "slug": "notes-25", "name": "Scholar", "icon": "book-open", "tier": "silver",
        "description": "Completed 25 engineering topics.",
        "check": lambda u: _count("SELECT count(*) AS c FROM user_progress WHERE user_id = ? AND status IN ('completed','mastered')", u) >= 25,
    },
    {
        "slug": "coding-master", "name": "Coding Master", "icon": "code-2", "tier": "gold",
        "description": "Solved 25 coding problems.",
        "check": lambda u: _count("SELECT count(DISTINCT problem_id) AS c FROM coding_submissions WHERE user_id = ? AND is_accepted = 1", u) >= 25,
    },
    {
        "slug": "first-accept", "name": "Accepted!", "icon": "check-circle", "tier": "bronze",
        "description": "Got your first Accepted verdict on a coding problem.",
        "check": lambda u: _count("SELECT count(*) AS c FROM coding_submissions WHERE user_id = ? AND is_accepted = 1", u) >= 1,
    },
    {
        "slug": "core-engineer", "name": "Core Engineering Master", "icon": "cpu", "tier": "gold",
        "description": "Mastered topics across 3 different subjects.",
        "check": lambda u: _count(
            "SELECT count(DISTINCT t.subject_id) AS c FROM user_progress up JOIN topics t ON t.id = up.topic_id "
            "WHERE up.user_id = ? AND up.mastery >= 80", u) >= 3,
    },
    {
        "slug": "branch-explorer", "name": "Branch Explorer", "icon": "compass", "tier": "silver",
        "description": "Studied topics from 3 different branches.",
        "check": lambda u: _count(
            "SELECT count(DISTINCT s.branch_id) AS c FROM user_progress up JOIN topics t ON t.id = up.topic_id "
            "JOIN subjects s ON s.id = t.subject_id WHERE up.user_id = ?", u) >= 3,
    },
    {
        "slug": "perfect-dpp", "name": "Flawless", "icon": "award", "tier": "gold",
        "description": "Scored 100% on a DPP set of 5 or more questions.",
        "check": lambda u: _count(
            "SELECT count(*) AS c FROM (SELECT dpp_set_id FROM submissions WHERE user_id = ? AND dpp_set_id IS NOT NULL "
            "GROUP BY dpp_set_id HAVING sum(is_correct) = count(*) AND count(*) >= 5)", u) >= 1,
    },
    {
        "slug": "interview-ready", "name": "Interview Ready", "icon": "video", "tier": "gold",
        "description": "Answered 20 interview-style questions correctly.",
        "check": lambda u: _count(
            "SELECT count(*) AS c FROM submissions s JOIN questions q ON q.id = s.question_id "
            "WHERE s.user_id = ? AND s.is_correct = 1 AND q.kind = 'interview'", u) >= 20,
    },
]


def ensure_badges() -> None:
    for badge in BADGES:
        db.execute(
            "INSERT INTO badges (id,slug,name,description,icon,tier,criterion) VALUES (?,?,?,?,?,?,?) "
            "ON CONFLICT(slug) DO UPDATE SET name=excluded.name, description=excluded.description, "
            "icon=excluded.icon, tier=excluded.tier",
            ulid(), badge["slug"], badge["name"], badge["description"], badge["icon"], badge["tier"], "{}",
        )


def evaluate_badges(user_id: str) -> list[str]:
    earned: list[str] = []
    for badge in BADGES:
        row = db.query_one(
            "SELECT ub.badge_id FROM user_badges ub JOIN badges b ON b.id = ub.badge_id "
            "WHERE ub.user_id = ? AND b.slug = ?",
            user_id, badge["slug"],
        )
        if row:
            continue
        try:
            satisfied = bool(badge["check"](user_id))
        except Exception:
            satisfied = False
        if not satisfied:
            continue
        badge_row = db.query_one("SELECT id FROM badges WHERE slug = ?", badge["slug"])
        if not badge_row:
            continue
        db.execute(
            "INSERT OR IGNORE INTO user_badges (user_id,badge_id,earned_at) VALUES (?,?,?)",
            user_id, badge_row["id"], now_ms(),
        )
        db.execute(
            "INSERT INTO notifications (id,user_id,type,title,body,url,created_at) VALUES (?,?,?,?,?,?,?)",
            ulid(), user_id, "badge", f"Badge unlocked: {badge['name']}", badge["description"], "/profile", now_ms(),
        )
        earned.append(badge["slug"])
    return earned


def user_badges(user_id: str) -> list[dict]:
    return db.query(
        "SELECT b.slug, b.name, b.description, b.icon, b.tier, ub.earned_at FROM user_badges ub "
        "JOIN badges b ON b.id = ub.badge_id WHERE ub.user_id = ? ORDER BY ub.earned_at DESC",
        user_id,
    )


def all_badges(user_id: str | None) -> list[dict]:
    ensure_badges()
    earned = {row["slug"] for row in user_badges(user_id)} if user_id else set()
    rows = db.query("SELECT slug, name, description, icon, tier FROM badges ORDER BY tier, name")
    for row in rows:
        row["earned"] = row["slug"] in earned
    return rows


# --------------------------------------------------------------------------
# Bookmarks, personal notes, leaderboard, certificates, notifications
# --------------------------------------------------------------------------

def toggle_bookmark(user_id: str, entity_type: str, entity_id: str, note: str | None = None) -> bool:
    existing = db.query_one(
        "SELECT entity_id FROM bookmarks WHERE user_id = ? AND entity_type = ? AND entity_id = ?",
        user_id, entity_type, entity_id,
    )
    if existing:
        db.execute(
            "DELETE FROM bookmarks WHERE user_id = ? AND entity_type = ? AND entity_id = ?",
            user_id, entity_type, entity_id,
        )
        return False
    db.execute(
        "INSERT INTO bookmarks (user_id,entity_type,entity_id,note,created_at) VALUES (?,?,?,?,?)",
        user_id, entity_type, entity_id, note, now_ms(),
    )
    return True


def bookmarks(user_id: str, entity_type: str | None = None) -> list[dict]:
    if entity_type:
        return db.query(
            "SELECT * FROM bookmarks WHERE user_id = ? AND entity_type = ? ORDER BY created_at DESC",
            user_id, entity_type,
        )
    return db.query("SELECT * FROM bookmarks WHERE user_id = ? ORDER BY created_at DESC", user_id)


def bookmarked_ids(user_id: str) -> set[str]:
    rows = db.query("SELECT entity_type, entity_id FROM bookmarks WHERE user_id = ?", user_id)
    return {f"{row['entity_type']}:{row['entity_id']}" for row in rows}


def save_personal_note(user_id: str, entity_type: str, entity_id: str, content: str) -> str:
    note_id = ulid()
    db.execute(
        "INSERT INTO personal_notes (id,user_id,entity_type,entity_id,content,is_private,created_at,updated_at) "
        "VALUES (?,?,?,?,?,1,?,?)",
        note_id, user_id, entity_type, entity_id, content, now_ms(), now_ms(),
    )
    return note_id


def personal_notes(user_id: str, entity_type: str | None = None, entity_id: str | None = None) -> list[dict]:
    if entity_type and entity_id:
        return db.query(
            "SELECT * FROM personal_notes WHERE user_id = ? AND entity_type = ? AND entity_id = ? ORDER BY updated_at DESC",
            user_id, entity_type, entity_id,
        )
    return db.query("SELECT * FROM personal_notes WHERE user_id = ? ORDER BY updated_at DESC LIMIT 100", user_id)


def delete_personal_note(user_id: str, note_id: str) -> None:
    db.execute("DELETE FROM personal_notes WHERE id = ? AND user_id = ?", note_id, user_id)


def leaderboard(*, branch: str | None = None, country: str | None = None, period: str = "all", limit: int = 20) -> list[dict]:
    args: list[Any] = []
    if period in ("weekly", "monthly"):
        days = 7 if period == "weekly" else 30
        xp_expr = "(SELECT COALESCE(sum(x.amount),0) FROM xp_events x WHERE x.user_id = u.id AND x.created_at > ?)"
        args.append(now_ms() - days * DAY)
    else:
        xp_expr = "s.total_xp"
    clauses = ["u.status = 'active'"]
    if branch:
        clauses.append("b.slug = ?")
        args.append(branch)
    if country:
        clauses.append("p.country = ?")
        args.append(country)
    args.append(limit)
    return db.query(
        "SELECT u.username, p.full_name, p.avatar_seed, s.level, s.current_streak AS streak, b.slug AS branch, "
        f"{xp_expr} AS xp FROM users u JOIN profiles p ON p.user_id = u.id "
        "JOIN streaks s ON s.user_id = u.id LEFT JOIN branches b ON b.id = p.branch_id "
        f"WHERE {' AND '.join(clauses)} ORDER BY xp DESC, s.current_streak DESC LIMIT ?",
        *args,
    )


def certificates(user_id: str) -> list[dict]:
    return db.query(
        "SELECT id, kind, title, verify_id, issued_at, entity_type, entity_id FROM certificates "
        "WHERE user_id = ? ORDER BY issued_at DESC",
        user_id,
    )


def issue_certificate(user_id: str, kind: str, entity_type: str, entity_id: str, title: str, meta: dict | None = None) -> str:
    existing = db.query_one(
        "SELECT id FROM certificates WHERE user_id = ? AND entity_type = ? AND entity_id = ?",
        user_id, entity_type, entity_id,
    )
    if existing:
        return existing["id"]
    cert_id = ulid()
    verify_id = f"EV-{now_ms():X}-{cert_id[-6:].upper()}"
    db.execute(
        "INSERT INTO certificates (id,user_id,kind,entity_type,entity_id,title,verify_id,issued_at,meta) "
        "VALUES (?,?,?,?,?,?,?,?,?)",
        cert_id, user_id, kind, entity_type, entity_id, title, verify_id, now_ms(), json.dumps(meta or {}),
    )
    notify(user_id, "certificate", "Certificate earned", title, f"/verify/{verify_id}")
    return cert_id


def verify_certificate(verify_id: str) -> dict | None:
    row = db.query_one("SELECT * FROM certificates WHERE verify_id = ?", verify_id)
    if not row:
        return None
    holder = db.query_one(
        "SELECT p.full_name, u.username, p.branch_id "
        "FROM profiles p JOIN users u ON u.id = p.user_id "
        "WHERE p.user_id = ?",
        row["user_id"],
    )
    branch = db.query_one("SELECT name FROM branches WHERE id = ?", holder["branch_id"]) if holder and holder.get("branch_id") else None
    try:
        meta = json.loads(row["meta"] or "{}")
    except ValueError:
        meta = {}
    return {"certificate": row, "holder": holder, "branch": branch, "meta": meta}


def notify(user_id: str, kind: str, title: str, body: str, url: str | None = None) -> None:
    db.execute(
        "INSERT INTO notifications (id,user_id,type,title,body,url,created_at) VALUES (?,?,?,?,?,?,?)",
        ulid(), user_id, kind, title[:200], body[:500], url, now_ms(),
    )


def notifications(user_id: str, limit: int = 30, unread_only: bool = False) -> list[dict]:
    sql = "SELECT * FROM notifications WHERE user_id = ?"
    if unread_only:
        sql += " AND read_at IS NULL"
    return db.query(sql + " ORDER BY created_at DESC LIMIT ?", user_id, limit)


def mark_notifications_read(user_id: str, notification_id: str | None = None) -> None:
    if notification_id:
        db.execute("UPDATE notifications SET read_at = ? WHERE user_id = ? AND id = ?", now_ms(), user_id, notification_id)
    else:
        db.execute("UPDATE notifications SET read_at = ? WHERE user_id = ? AND read_at IS NULL", now_ms(), user_id)
