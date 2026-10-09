"""Authentication service (spec §71).

Fully self-hosted: EngineVerse never redirects to a third-party identity
provider, never stores a recoverable password, and never returns one.
"""
from __future__ import annotations

import hashlib
import json
import secrets
from dataclasses import dataclass
from typing import Any

from . import db
from .config import get_settings
from .security import validators
from .security.audit import record
from .security.ids import now_ms, today, ulid
from .security.passwords import check_password_strength, hash_password, needs_rehash, verify_password
from .security.ratelimit import auth_blocked, register_login_attempt
from .security.sessions import create_session

DAY = 86_400_000


class AuthError(Exception):
    """A refused authentication or admin operation.

    ``code`` is a stable machine-readable reason. It exists so a caller can tell
    *why* something failed without the ``message`` having to be safe to show:
    registration maps ``email_taken`` to a generic reply, because echoing
    "that email already exists" tells an attacker which addresses have
    accounts. ``message`` is only guaranteed to be internal-facing.
    """

    def __init__(
        self,
        message: str,
        status_code: int = 400,
        fields: dict[str, str] | None = None,
        code: str = "",
    ) -> None:
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.fields = fields or {}
        self.code = code


@dataclass(frozen=True)
class User:
    id: str
    email: str
    username: str
    role: str
    status: str
    email_verified: int
    created_at: int


@dataclass(frozen=True)
class CurrentUser:
    user: User
    profile: dict
    session_id: str
    streak: dict


# --------------------------------------------------------------------------
# Lookups
# --------------------------------------------------------------------------

_USER_COLUMNS = "id, email, username, role, status, email_verified, created_at"


def find_by_email(email: str) -> dict | None:
    return db.query_one(
        f"SELECT {_USER_COLUMNS} FROM users WHERE email = ? AND deleted_at IS NULL", email.strip().lower()
    )


def find_by_username(username: str) -> dict | None:
    return db.query_one(
        f"SELECT {_USER_COLUMNS} FROM users WHERE username = ? AND deleted_at IS NULL", username.strip().lower()
    )


def find_by_id(user_id: str) -> dict | None:
    return db.query_one(f"SELECT {_USER_COLUMNS} FROM users WHERE id = ? AND deleted_at IS NULL", user_id)


def find_by_email_or_username(identifier: str) -> dict | None:
    value = identifier.strip().lower()
    return db.query_one(
        f"SELECT {_USER_COLUMNS}, password_hash, locked_until FROM users "
        "WHERE (email = ? OR username = ?) AND deleted_at IS NULL",
        value,
        value,
    )


def get_profile(user_id: str) -> dict | None:
    return db.query_one("SELECT * FROM profiles WHERE user_id = ?", user_id)


def get_streak(user_id: str) -> dict:
    return db.query_one(
        "SELECT current_streak, longest_streak, total_xp, level, last_active_day FROM streaks WHERE user_id = ?",
        user_id,
    ) or {"current_streak": 0, "longest_streak": 0, "total_xp": 0, "level": 1, "last_active_day": None}


# --------------------------------------------------------------------------
# Registration
# --------------------------------------------------------------------------

def register(
    *,
    email: str,
    username: str,
    password: str,
    full_name: str,
    ip: str | None = None,
    user_agent: str | None = None,
) -> dict:
    errors = validators.Errors()
    email = validators.validate_email(email, "email", errors)
    username = validators.validate_username(username, "username", errors)
    full_name = validators.validate_text(full_name, "fullName", errors, min_length=2, max_length=80)
    validators.validate_password(password, "password", errors)
    errors.raise_if_any("Please fix the highlighted fields.")

    issues = check_password_strength(password, [username, email, email.split("@")[0], full_name])
    if issues:
        raise AuthError(issues[0].message, 422, {"password": issues[0].message}, code="weak_password")

    # Hashed before the existence checks, not after. scrypt costs ~50 ms, so
    # returning early on a duplicate email made "does this address have an
    # account" measurable from the response time alone even with an identical
    # reply. Both paths now pay the same cost.
    password_hash = hash_password(password)

    if find_by_email(email):
        raise AuthError(
            "An account with that email already exists.",
            409,
            {"email": "Already registered."},
            code="email_taken",
        )
    if find_by_username(username):
        # Usernames are shown publicly throughout the site, so confirming one is
        # taken reveals nothing an attacker could not read off a leaderboard.
        raise AuthError("That username is taken.", 409, {"username": "Already taken."}, code="username_taken")

    user_id = ulid()
    ts = now_ms()
    privacy = json.dumps({"showEmail": False, "showActivity": True, "showProgress": True, "searchable": True})
    notifications = json.dumps(
        {"newDpp": True, "streakReminder": True, "milestone": True, "communityReply": True, "contest": False, "content": False}
    )

    with db.transaction():
        db.execute(
            "INSERT INTO users (id,email,username,password_hash,role,status,email_verified,failed_login_count,"
            "password_changed_at,created_at,updated_at) VALUES (?,?,?,?,?,?,?,?,?,?,?)",
            user_id, email, username, password_hash, "student", "active", 0, 0, ts, ts, ts,
        )
        db.execute(
            "INSERT INTO profiles (user_id, full_name, avatar_seed, skill_level, programming_xp, weekly_study_hours,"
            " language_pref, note_quality, skills, privacy, notification_prefs, updated_at) "
            "VALUES (?,?,?,?,?,?,?,?,?,?,?,?)",
            user_id, full_name, username, "beginner", "none", 7, "en", "standard", "[]", privacy, notifications, ts,
        )
        db.execute(
            "INSERT INTO streaks (user_id, current_streak, longest_streak, last_active_day, total_xp, level) "
            "VALUES (?,0,0,NULL,0,1)",
            user_id,
        )
        db.execute(
            "INSERT INTO notifications (id,user_id,type,title,body,url,created_at) VALUES (?,?,?,?,?,?,?)",
            ulid(), user_id, "welcome", "Welcome to EngineVerse",
            "Finish onboarding to generate your personal engineering roadmap.", "/onboarding", ts,
        )
        db.execute(
            "INSERT INTO activity (user_id, day) VALUES (?,?) ON CONFLICT(user_id,day) DO NOTHING", user_id, today()
        )

    record("auth.register", actor_id=user_id, entity_type="user", entity_id=user_id, ip=ip, meta={"username": username})
    return find_by_id(user_id) or {}


# --------------------------------------------------------------------------
# Login
# --------------------------------------------------------------------------

def login(*, identifier: str, password: str, ip: str = "", user_agent: str = "") -> tuple[dict, str, str]:
    """Verifies credentials. Returns ``(user_row, cookie_value, session_id)``.

    Raises AuthError with a deliberately generic message so the response cannot
    be used to enumerate accounts.
    """
    identifier = (identifier or "").strip().lower()
    blocked, retry_after = auth_blocked(identifier, ip)
    if blocked:
        record("auth.login_failed", ip=ip, meta={"identifier": identifier, "reason": "rate_limited"})
        raise AuthError(
            f"Too many failed attempts. Try again in {retry_after // 60 + 1} minute(s).", 429
        )

    row = find_by_email_or_username(identifier)
    if row is None:
        # Spend comparable time so "no such user" is not measurable.
        verify_password(password, "scrypt$16384$8$1$AAAAAAAAAAAAAAAAAAAAAA==$" + "A" * 88)
        register_login_attempt(identifier, ip, False, "no_such_user")
        record("auth.login_failed", ip=ip, meta={"identifier": identifier, "reason": "no_such_user"})
        raise AuthError("Incorrect email or password.", 401)

    if row["status"] != "active":
        register_login_attempt(identifier, ip, False, "suspended")
        record("auth.login_failed", actor_id=row["id"], ip=ip, meta={"reason": "suspended"})
        raise AuthError("This account is suspended. Contact support.", 403)

    locked_until = row.get("locked_until")
    if locked_until and locked_until > now_ms():
        register_login_attempt(identifier, ip, False, "locked")
        raise AuthError("Account temporarily locked after repeated failures. Try again shortly.", 423)

    if not verify_password(password, row["password_hash"]):
        ts = now_ms()
        failures = int(db.scalar("SELECT failed_login_count AS c FROM users WHERE id = ?", row["id"]) or 0) + 1
        db.execute(
            "UPDATE users SET failed_login_count = ?, locked_until = ?, updated_at = ? WHERE id = ?",
            failures,
            ts + 15 * 60_000 if failures >= 8 else None,
            ts,
            row["id"],
        )
        register_login_attempt(identifier, ip, False, "bad_password")
        record("auth.login_failed", actor_id=row["id"], ip=ip, meta={"reason": "bad_password", "failures": failures})
        if failures >= 8:
            raise AuthError("Too many failed attempts. The account is locked for 15 minutes.", 423)
        raise AuthError("Incorrect email or password.", 401)

    ts = now_ms()
    db.execute("UPDATE users SET failed_login_count = 0, locked_until = NULL, updated_at = ? WHERE id = ?", ts, row["id"])
    if needs_rehash(row["password_hash"]):
        db.execute("UPDATE users SET password_hash = ? WHERE id = ?", hash_password(password), row["id"])

    register_login_attempt(identifier, ip, True)
    cookie_value, session_id = create_session(row["id"], ip=ip, user_agent=user_agent)
    touch_streak(row["id"])
    record("auth.login", actor_id=row["id"], entity_type="user", entity_id=row["id"], ip=ip)

    user = {k: row[k] for k in ("id", "email", "username", "role", "status", "email_verified", "created_at")}
    return user, cookie_value, session_id


def logout(session_id: str, user_id: str, ip: str | None = None) -> None:
    from .security.sessions import revoke_session

    revoke_session(session_id)
    record("auth.logout", actor_id=user_id, ip=ip)


def change_password(user_id: str, current_password: str, new_password: str) -> None:
    row = db.query_one("SELECT password_hash, username, email FROM users WHERE id = ?", user_id)
    if row is None:
        raise AuthError("Account not found.", 404)
    if not verify_password(current_password, row["password_hash"]):
        raise AuthError("Your current password is incorrect.", 403)
    issues = check_password_strength(new_password, [row["username"], row["email"], row["email"].split("@")[0]])
    if issues:
        raise AuthError(issues[0].message, 422, {"newPassword": issues[0].message})
    if verify_password(new_password, row["password_hash"]):
        raise AuthError("Choose a password you have not used before.", 422)
    db.execute(
        "UPDATE users SET password_hash = ?, password_changed_at = ?, updated_at = ? WHERE id = ?",
        hash_password(new_password), now_ms(), now_ms(), user_id,
    )
    from .security.sessions import revoke_all_sessions

    revoke_all_sessions(user_id)
    record("auth.password_changed", actor_id=user_id, entity_type="user", entity_id=user_id)


# --------------------------------------------------------------------------
# Session / current user
# --------------------------------------------------------------------------

def current_user_from_session(session) -> CurrentUser | None:
    if session is None:
        return None
    row = find_by_id(session.user_id)
    if row is None or row["status"] != "active":
        return None
    profile = get_profile(session.user_id)
    if profile is None:
        return None
    return CurrentUser(
        user=User(**{k: row[k] for k in ("id", "email", "username", "role", "status", "email_verified", "created_at")}),
        profile=profile,
        session_id=session.id,
        streak=get_streak(session.user_id),
    )


def touch_streak(user_id: str) -> int:
    """Keeps the streak row aligned with today. Returns the new streak length."""
    day = today()
    row = db.query_one(
        "SELECT last_active_day, current_streak, longest_streak FROM streaks WHERE user_id = ?", user_id
    )
    if row is None:
        db.execute(
            "INSERT INTO streaks (user_id, current_streak, longest_streak, last_active_day) VALUES (?,1,1,?)",
            user_id, day,
        )
        return 1
    if row["last_active_day"] == day:
        return int(row["current_streak"] or 0)
    consecutive = False
    if row["last_active_day"]:
        try:
            previous = datetime_from_day(row["last_active_day"])
            current = datetime_from_day(day)
            consecutive = (current - previous).days == 1
        except ValueError:
            consecutive = False
    streak = (int(row["current_streak"] or 0) + 1) if consecutive else 1
    # sql_greatest repeats its arguments, so the streak placeholder appears
    # twice in the CASE and is passed twice here.
    db.execute(
        "UPDATE streaks SET current_streak = ?, "
        f"longest_streak = {db.sql_greatest('longest_streak', '?')}, last_active_day = ? "
        "WHERE user_id = ?",
        streak, streak, streak, day, user_id,
    )
    return streak


def datetime_from_day(value: str):
    from datetime import date

    return date.fromisoformat(value)


# --------------------------------------------------------------------------
# Profile / onboarding
# --------------------------------------------------------------------------

def update_onboarding(user_id: str, data: dict[str, Any]) -> None:
    fields: list[str] = []
    values: list[Any] = []
    mapping = {
        "branchId": "branch_id",
        "universityId": "university_id",
        "collegeId": "college_id",
        "semester": "semester_id",
        "skillLevel": "skill_level",
        "careerGoal": "career_goal",
        "programmingExperience": "programming_xp",
        "weeklyStudyHours": "weekly_study_hours",
        "languagePref": "language_pref",
        "noteQuality": "note_quality",
    }
    for key, column in mapping.items():
        if key in data and data[key] is not None:
            fields.append(f"{column} = ?")
            values.append(data[key])
    if not fields:
        return
    fields.append("onboarded_at = ?")
    values.append(now_ms())
    fields.append("updated_at = ?")
    values.append(now_ms())
    values.append(user_id)
    db.execute(f"UPDATE profiles SET {', '.join(fields)} WHERE user_id = ?", *values)


def update_profile(user_id: str, data: dict[str, Any]) -> None:
    allowed = {
        "full_name", "headline", "bio", "country", "branch_id", "university_id", "semester_id",
        "github_url", "linkedin_url", "portfolio_url", "skills", "privacy", "notification_prefs",
        "note_quality", "language_pref", "weekly_study_hours", "skill_level", "career_goal",
    }
    fields: list[str] = []
    values: list[Any] = []
    for key, value in data.items():
        if key not in allowed:
            continue
        if isinstance(value, (dict, list)):
            value = json.dumps(value)
        fields.append(f"{key} = ?")
        values.append(value)
    if not fields:
        return
    fields.append("updated_at = ?")
    values.append(now_ms())
    values.append(user_id)
    db.execute(f"UPDATE profiles SET {', '.join(fields)} WHERE user_id = ?", *values)


def list_users(limit: int = 100, q: str | None = None) -> list[dict]:
    if q:
        like = f"%{q}%"
        return db.query(
            "SELECT u.id,u.email,u.username,u.role,u.status,u.email_verified,u.created_at,p.full_name,"
            "p.branch_id,p.university_id FROM users u JOIN profiles p ON p.user_id = u.id "
            "WHERE u.deleted_at IS NULL AND (u.username LIKE ? OR u.email LIKE ? OR p.full_name LIKE ?) "
            "ORDER BY u.created_at DESC LIMIT ?",
            like, like, like, limit,
        )
    return db.query(
        "SELECT u.id,u.email,u.username,u.role,u.status,u.email_verified,u.created_at,p.full_name,"
        "p.branch_id,p.university_id FROM users u JOIN profiles p ON p.user_id = u.id "
        "WHERE u.deleted_at IS NULL ORDER BY u.created_at DESC LIMIT ?",
        limit,
    )


def set_role(actor_id: str, user_id: str, role: str) -> None:
    if role not in ("student", "mentor", "moderator", "subject_expert", "project_reviewer", "analytics_admin", "content_admin", "super_admin"):
        raise AuthError("Unknown role.", 422)
    # Check the target first: the INSERT into user_roles below would otherwise
    # raise a raw FOREIGN KEY constraint failure and surface as a 500.
    if not db.query_one("SELECT id FROM users WHERE id = ? AND deleted_at IS NULL", user_id):
        raise AuthError("No such user.", 404)
    db.execute("UPDATE users SET role = ?, updated_at = ? WHERE id = ?", role, now_ms(), user_id)
    db.execute(
        "INSERT INTO user_roles (user_id, role, granted_by, granted_at) VALUES (?,?,?,?) "
        "ON CONFLICT(user_id, role) DO NOTHING",
        user_id, role, actor_id, now_ms(),
    )
    from .security.sessions import revoke_all_sessions

    revoke_all_sessions(user_id)
    record("auth.role_changed", actor_id=actor_id, entity_type="user", entity_id=user_id, meta={"role": role})


def set_status(actor_id: str, user_id: str, status: str) -> None:
    if status not in ("active", "suspended"):
        raise AuthError("Unknown status.", 422)
    if not db.query_one("SELECT id FROM users WHERE id = ? AND deleted_at IS NULL", user_id):
        raise AuthError("No such user.", 404)
    db.execute("UPDATE users SET status = ?, updated_at = ? WHERE id = ?", status, now_ms(), user_id)
    if status == "suspended":
        from .security.sessions import revoke_all_sessions

        revoke_all_sessions(user_id)
    record("admin.user_updated", actor_id=actor_id, entity_type="user", entity_id=user_id, meta={"status": status})


# ---------------------------------------------------------------------------
# Password reset tokens
# ---------------------------------------------------------------------------

RESET_TOKEN_TTL_MS = 30 * 60_000  # 30 minutes


def _hash_reset_token(token: str) -> str:
    """Hashes a reset token the way session cookies are hashed.

    Only the digest is stored, so reading the table does not hand an attacker a
    working reset link.
    """
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def issue_password_reset(user_id: str, ip: str | None = None) -> str:
    """Creates a reset token and returns the plaintext, once.

    Any token already outstanding for this user is invalidated first, so there
    is never a choice of valid links and an older emailed link cannot be replayed
    after a newer one is issued.
    """
    token = secrets.token_urlsafe(32)
    ts = now_ms()
    db.execute("DELETE FROM password_resets WHERE user_id = ?", user_id)
    db.execute(
        "INSERT INTO password_resets (token_hash, user_id, created_at, expires_at, ip) VALUES (?,?,?,?,?)",
        _hash_reset_token(token), user_id, ts, ts + RESET_TOKEN_TTL_MS, ip,
    )
    record("auth.reset_token_issued", actor_id=user_id, ip=ip)
    return token


def consume_password_reset(token: str) -> str | None:
    """Returns the user id a reset token belongs to, or None.

    The token is matched by exact hash equality. It is deliberately not looked
    up with a LIKE pattern: reset tokens used to be found with
    ``meta LIKE '%"<token>"%'`` against the audit log, so submitting a single
    ``%`` matched whichever account had requested a reset most recently and let
    anyone take that account over.

    Expired tokens are refused, and the token is marked used in the same
    transaction that returns it so it cannot be replayed.
    """
    if not token or len(token) > 200:
        return None
    row = db.query_one(
        "SELECT user_id, expires_at FROM password_resets "
        "WHERE token_hash = ? AND used_at IS NULL",
        _hash_reset_token(token),
    )
    if not row:
        return None
    if int(row["expires_at"]) < now_ms():
        db.execute("DELETE FROM password_resets WHERE token_hash = ?", _hash_reset_token(token))
        return None
    db.execute(
        "UPDATE password_resets SET used_at = ? WHERE token_hash = ?",
        now_ms(), _hash_reset_token(token),
    )
    return row["user_id"]


def prune_password_resets() -> int:
    """Deletes expired rows; called opportunistically rather than by a cron job."""
    return db.execute("DELETE FROM password_resets WHERE expires_at < ?", now_ms() - DAY)


def site_url() -> str:
    return get_settings().site_url
