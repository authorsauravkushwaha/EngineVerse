"""Community: discussions, comments, votes, reports and moderation (spec §38-§39)."""
from __future__ import annotations

import json
from typing import Any

from . import db
from .security.ids import now_ms, ulid
from .security.rbac import can


def _json(value: Any, fallback: Any) -> Any:
    if value in (None, ""):
        return fallback
    if isinstance(value, (list, dict)):
        return value
    try:
        return json.loads(value)
    except (ValueError, TypeError):
        return fallback


def list_threads(
    *, kind: str | None = None, tag: str | None = None, q: str | None = None,
    resolved: bool | None = None, limit: int = 30, offset: int = 0,
) -> tuple[list[dict], int]:
    clauses = ["d.is_hidden = 0"]
    args: list[Any] = []
    if kind:
        clauses.append("d.kind = ?")
        args.append(kind)
    if tag:
        clauses.append("d.tags LIKE ?")
        args.append(f'%"{tag}"%')
    if q:
        clauses.append("(d.title LIKE ? OR d.body LIKE ?)")
        args += [f"%{q}%"] * 2
    if resolved is not None:
        clauses.append("d.is_resolved = ?")
        args.append(1 if resolved else 0)
    where = " AND ".join(clauses)
    total = int(db.scalar(f"SELECT count(*) AS c FROM discussions d WHERE {where}", *args) or 0)
    rows = db.query(
        "SELECT d.*, u.username, p.full_name, p.avatar_seed FROM discussions d "
        "JOIN users u ON u.id = d.user_id JOIN profiles p ON p.user_id = d.user_id "
        f"WHERE {where} ORDER BY d.is_resolved, d.last_activity_at DESC LIMIT ? OFFSET ?",
        *args, limit, offset,
    )
    for row in rows:
        row["tags_data"] = _json(row.get("tags"), [])
    return rows, total


def get_thread(thread_id: str) -> dict | None:
    row = db.query_one(
        "SELECT d.*, u.username, u.role, p.full_name, p.avatar_seed FROM discussions d "
        "JOIN users u ON u.id = d.user_id JOIN profiles p ON p.user_id = d.user_id WHERE d.id = ?",
        thread_id,
    )
    if not row:
        return None
    row["tags_data"] = _json(row.get("tags"), [])
    row["comments"] = comments(thread_id)
    return row


def comments(thread_id: str) -> list[dict]:
    rows = db.query(
        # comments.user_id is ON DELETE SET NULL, so a reply outlives the account
        # that wrote it. Without COALESCE the template printed the literal string
        # "None" as the author.
        "SELECT c.*, COALESCE(u.username, 'Deleted account') AS username, p.full_name, "
        "p.avatar_seed, u.role FROM comments c "
        "LEFT JOIN users u ON u.id = c.user_id LEFT JOIN profiles p ON p.user_id = c.user_id "
        "WHERE c.discussion_id = ? AND c.is_deleted = 0 ORDER BY c.created_at",
        thread_id,
    )
    return rows


def create_thread(user_id: str, *, title: str, body: str, kind: str = "question",
                  tags: list[str] | None = None, entity_type: str | None = None, entity_id: str | None = None) -> str:
    thread_id = ulid()
    ts = now_ms()
    db.execute(
        "INSERT INTO discussions (id,user_id,title,body,kind,tags,entity_type,entity_id,created_at,last_activity_at) "
        "VALUES (?,?,?,?,?,?,?,?,?,?)",
        thread_id, user_id, title, body, kind, json.dumps(tags or []), entity_type, entity_id, ts, ts,
    )
    from .progress import award_xp

    award_xp(user_id, 5, "community.posted", "discussion", thread_id)
    return thread_id


def add_comment(user_id: str, thread_id: str, body: str, parent_id: str | None = None) -> str:
    comment_id = ulid()
    ts = now_ms()
    db.execute(
        "INSERT INTO comments (id,discussion_id,parent_id,user_id,body,created_at) VALUES (?,?,?,?,?,?)",
        comment_id, thread_id, parent_id, user_id, body, ts,
    )
    db.execute("UPDATE discussions SET reply_count = reply_count + 1, last_activity_at = ? WHERE id = ?", ts, thread_id)
    owner = db.scalar("SELECT user_id AS u FROM discussions WHERE id = ?", thread_id, default=None)
    if owner and owner != user_id:
        from .progress import notify

        author = db.scalar("SELECT username AS u FROM users WHERE id = ?", user_id, default="Someone")
        notify(owner, "community_reply", "New reply to your thread", f"{author} replied to your post.", f"/community/{thread_id}")
    from .progress import award_xp

    award_xp(user_id, 3, "community.comment", "discussion", thread_id)
    return comment_id


def vote(user_id: str, entity_type: str, entity_id: str, value: int) -> int:
    """Applies an up/down vote idempotently and returns the new score."""
    value = 1 if value > 0 else (-1 if value < 0 else 0)
    existing = db.query_one(
        "SELECT value FROM votes WHERE user_id = ? AND entity_type = ? AND entity_id = ?",
        user_id, entity_type, entity_id,
    )
    previous = int(existing["value"]) if existing else 0
    delta = value - previous
    with db.transaction():
        if value == 0 and existing:
            db.execute(
                "DELETE FROM votes WHERE user_id = ? AND entity_type = ? AND entity_id = ?",
                user_id, entity_type, entity_id,
            )
        else:
            db.execute(
                "INSERT INTO votes (user_id,entity_type,entity_id,value,created_at) VALUES (?,?,?,?,?) "
                "ON CONFLICT(user_id,entity_type,entity_id) DO UPDATE SET value = excluded.value",
                user_id, entity_type, entity_id, value, now_ms(),
            )
        if entity_type == "discussion":
            db.execute("UPDATE discussions SET upvotes = upvotes + ? WHERE id = ?", delta, entity_id)
        elif entity_type == "comment":
            db.execute("UPDATE comments SET upvotes = upvotes + ? WHERE id = ?", delta, entity_id)
    if entity_type == "discussion":
        return int(db.scalar("SELECT upvotes AS v FROM discussions WHERE id = ?", entity_id, default=0) or 0)
    return int(db.scalar("SELECT upvotes AS v FROM comments WHERE id = ?", entity_id, default=0) or 0)


def user_votes(user_id: str) -> dict[str, int]:
    rows = db.query("SELECT entity_type, entity_id, value FROM votes WHERE user_id = ?", user_id)
    return {f"{row['entity_type']}:{row['entity_id']}": int(row["value"]) for row in rows}


def report(user_id: str, entity_type: str, entity_id: str, reason: str, detail: str | None = None) -> str:
    report_id = ulid()
    db.execute(
        "INSERT INTO reports (id,reporter_id,entity_type,entity_id,reason,detail,created_at) VALUES (?,?,?,?,?,?,?)",
        report_id, user_id, entity_type, entity_id, reason[:200], (detail or "")[:2000], now_ms(),
    )
    return report_id


def open_reports(limit: int = 50) -> list[dict]:
    return db.query(
        "SELECT r.*, u.username FROM reports r JOIN users u ON u.id = r.reporter_id "
        "WHERE r.status = 'open' ORDER BY r.created_at DESC LIMIT ?",
        limit,
    )


def resolve_report(actor_id: str, report_id: str, *, hide: bool = False) -> None:
    row = db.query_one("SELECT entity_type, entity_id FROM reports WHERE id = ?", report_id)
    db.execute("UPDATE reports SET status = 'resolved' WHERE id = ?", report_id)
    if row and hide and row["entity_type"] == "discussion":
        db.execute("UPDATE discussions SET is_hidden = 1 WHERE id = ?", row["entity_id"])
    from .security.audit import record

    record("community.deleted", actor_id=actor_id, entity_type=row["entity_type"] if row else None,
           entity_id=row["entity_id"] if row else None, meta={"hidden": hide})


def delete_comment(actor_id: str, actor_role: str, comment_id: str) -> None:
    row = db.query_one("SELECT user_id, discussion_id FROM comments WHERE id = ?", comment_id)
    if not row:
        return
    if row["user_id"] != actor_id and not can(actor_role, "community.moderate"):
        from .security.rbac import Forbidden

        raise Forbidden("You can only delete your own comments.")
    db.execute("UPDATE comments SET is_deleted = 1 WHERE id = ?", comment_id)
    db.execute("UPDATE discussions SET reply_count = MAX(0, reply_count - 1) WHERE id = ?", row["discussion_id"])


def tags() -> list[dict]:
    counts: dict[str, int] = {}
    for row in db.query("SELECT tags FROM discussions"):
        for tag in _json(row["tags"], []):
            counts[tag] = counts.get(tag, 0) + 1
    return [{"tag": key, "count": value} for key, value in sorted(counts.items(), key=lambda kv: -kv[1])][:24]


def kinds() -> list[dict]:
    return db.query(
        "SELECT kind, count(*) AS count FROM discussions WHERE is_hidden = 0 GROUP BY kind ORDER BY count DESC"
    )
