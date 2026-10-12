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


class MfaRequired(Exception):
    """Password matched and a second factor is enrolled. No session exists yet."""

    def __init__(self, token: str, message: str = "Enter the code from your authenticator.") -> None:
        super().__init__(message)
        self.token = token
        self.message = message


class OtpRequired(Exception):
    """Password matched and a delivered one-time code is required."""

    def __init__(
        self,
        token: str,
        channel: str,
        masked: str,
        choices: list[str] | tuple[str, ...],
        message: str = "Enter the 6-digit code we sent.",
        revealed_code: str = "",
        attempts_left: int = 5,
    ) -> None:
        super().__init__(message)
        self.token = token
        self.channel = channel
        self.masked = masked
        self.choices = list(choices)
        self.message = message
        self.revealed_code = revealed_code
        self.attempts_left = attempts_left


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
        f"SELECT {_USER_COLUMNS}, password_hash, locked_until, totp_secret, phone, phone_verified FROM users "
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

def _finish_login(row: dict, identifier: str, ip: str, user_agent: str) -> tuple[dict, str, str]:
    ts = now_ms()
    db.execute("UPDATE users SET failed_login_count = 0, locked_until = NULL, updated_at = ? WHERE id = ?", ts, row["id"])
    register_login_attempt(identifier, ip, True)
    cookie_value, session_id = create_session(row["id"], ip=ip, user_agent=user_agent)
    touch_streak(row["id"])
    record("auth.login", actor_id=row["id"], entity_type="user", entity_id=row["id"], ip=ip)
    user = {k: row[k] for k in ("id", "email", "username", "role", "status", "email_verified", "created_at")}
    return user, cookie_value, session_id


def _store_mfa_replacement(row: dict, replacement: str | None) -> None:
    """Compare-and-set MFA state so concurrent/replayed factors cannot both win."""
    if replacement is None:
        return
    changed = db.execute(
        "UPDATE users SET totp_secret = ?, updated_at = ? WHERE id = ? AND totp_secret = ?",
        replacement, now_ms(), row["id"], row["totp_secret"],
    )
    if changed != 1:
        raise AuthError(
            "That authenticator code was already used or the factor changed. Try again with a fresh code.",
            401,
            code="mfa_replay",
        )


def _reject_factor(row: dict, identifier: str, ip: str) -> None:
    ts = now_ms()
    failures = int(db.scalar("SELECT failed_login_count AS c FROM users WHERE id = ?", row["id"]) or 0) + 1
    db.execute(
        "UPDATE users SET failed_login_count = ?, locked_until = ?, updated_at = ? WHERE id = ?",
        failures,
        ts + 15 * 60_000 if failures >= 8 else None,
        ts,
        row["id"],
    )
    register_login_attempt(identifier, ip, False, "bad_mfa")
    record("auth.login_failed", actor_id=row["id"], ip=ip, meta={"reason": "bad_mfa", "failures": failures})
    if failures >= 8:
        raise AuthError("Too many failed attempts. The account is locked for 15 minutes.", 423)
    raise AuthError("That authenticator code was not accepted.", 401, code="mfa_invalid")


def _otp_choices(row: dict) -> list[str]:
    """Return channels that can actually be selected for this account."""
    from . import notify

    # Email is always a choice: it is the normal default and a deployment may
    # configure it after an account has enrolled a phone. A phone is offered
    # only when both the number and the operator SMS gateway are ready.
    choices: list[str] = ["email"]
    if int(row.get("phone_verified") or 0) and notify.sms_is_configured():
        choices.append("phone")
    return choices


def _otp_mask(row: dict, channel: str) -> str:
    from .security import otp

    return otp.mask_phone(row.get("phone") or "") if channel == "phone" else otp.mask_email(row["email"])


def _otp_issue_allowed(user_id: str) -> None:
    from .security import ratelimit

    limited = ratelimit.shared_check(f"otp-issue:{user_id}", 5, 15 * 60)
    if not limited.allowed:
        raise AuthError(
            "Too many sign-in codes have been requested. Try again later.",
            429,
            code="otp_rate_limited",
        )


def _begin_otp_challenge(row: dict, channel: str | None = None) -> OtpRequired:
    """Issue and deliver the compulsory factor without creating a session."""
    from . import notify
    from .security import otp

    choices = _otp_choices(row)
    if channel and channel not in choices:
        raise AuthError("That sign-in delivery option is not available.", 422, code="otp_channel_invalid")
    if channel:
        selected = channel
    elif "email" in choices and notify.is_configured():
        selected = "email"
    elif "phone" in choices:
        # With SMS as the only configured transport, use the verified phone on
        # the first step while retaining both choices for a later switch.
        selected = "phone"
    else:
        selected = "email"

    _otp_issue_allowed(row["id"])
    masked = _otp_mask(row, selected)
    token, code = otp.issue_login_challenge(
        row["id"], channel=selected, masked=masked, choices=choices
    )
    try:
        delivered = (
            notify.send_phone_otp(row["phone"], code, minutes=5)
            if selected == "phone"
            else notify.send_login_otp(row["email"], code, minutes=5)
        )
    except Exception:  # delivery is fail-closed even if an adapter misbehaves
        delivered = False
    record("auth.otp_issued", actor_id=row["id"], entity_type="user", entity_id=row["id"],
           meta={"channel": selected})
    if delivered:
        record("auth.otp_delivered", actor_id=row["id"], entity_type="user", entity_id=row["id"],
               meta={"channel": selected})
        return OtpRequired(token, selected, masked, choices, attempts_left=otp.MAX_ATTEMPTS)

    settings = get_settings()
    can_reveal = (
        settings.allows_demo_accounts
        and not settings.is_production
        and not notify.is_configured()
        and not notify.sms_is_configured()
    )
    if can_reveal:
        record("auth.otp_dev_revealed", actor_id=row["id"], entity_type="user", entity_id=row["id"],
               meta={"channel": selected})
        return OtpRequired(
            token,
            selected,
            masked,
            choices,
            revealed_code=code,
            attempts_left=otp.MAX_ATTEMPTS,
        )

    otp.kill_challenge(token, otp.LOGIN_PURPOSE, row["id"])
    record("auth.otp_delivery_failed", actor_id=row["id"], entity_type="user", entity_id=row["id"],
           meta={"channel": selected})
    raise AuthError(
        "We could not deliver a sign-in code. Try again later or contact the site operator.",
        503,
        code="otp_undeliverable",
    )


def describe_otp_challenge(token: str, user_id: str | None = None) -> OtpRequired | None:
    """Build the safe code-step state after a failed code submission."""
    from .security import otp

    details = otp.describe_challenge(token, otp.LOGIN_PURPOSE, user_id)
    if details is None:
        return None
    return OtpRequired(
        token,
        details["channel"],
        details["masked"],
        details["choices"],
        attempts_left=details["attempts_left"],
    )


def _otp_row(user_id: str) -> dict | None:
    return db.query_one(
        f"SELECT {_USER_COLUMNS}, password_hash, locked_until, totp_secret, phone, phone_verified "
        "FROM users WHERE id = ? AND deleted_at IS NULL",
        user_id,
    )


def _reject_otp(row: dict, identifier: str, ip: str, token: str, result: dict) -> None:
    """Record a bad delivered code and either re-render or kill the challenge."""
    from .security import otp

    ts = now_ms()
    failures = int(db.scalar("SELECT failed_login_count AS c FROM users WHERE id = ?", row["id"]) or 0) + 1
    db.execute(
        "UPDATE users SET failed_login_count = ?, locked_until = ?, updated_at = ? WHERE id = ?",
        failures,
        ts + 15 * 60_000 if failures >= 8 else None,
        ts,
        row["id"],
    )
    register_login_attempt(identifier, ip, False, "bad_otp")
    record("auth.login_failed", actor_id=row["id"], ip=ip,
           meta={"reason": "bad_otp", "failures": failures})

    if result.get("status") == "exhausted":
        raise AuthError("That sign-in code has been used too many times. Start again.", 401,
                        code="otp_exhausted")
    if failures >= 8:
        otp.kill_challenge(token, otp.LOGIN_PURPOSE, row["id"])
        raise AuthError("Too many failed attempts. The account is locked for 15 minutes.", 423)
    challenge = describe_otp_challenge(token, row["id"])
    if challenge is None:
        raise AuthError("That sign-in code has expired. Start again.", 401, code="otp_expired")
    raise challenge


def login(
    *,
    identifier: str,
    password: str,
    ip: str = "",
    user_agent: str = "",
    otp: str = "",
    mfa_token: str = "",
) -> tuple[dict, str, str]:
    """Verify a password and the enrolled second factor, if any."""
    from . import notify
    from .security import otp as delivered_otp
    from .security import totp

    identifier = (identifier or "").strip().lower()
    if mfa_token:
        # Authenticator challenges are intentionally checked first. A token is
        # opaque and can only be resolved by its purpose-specific database row.
        user_id = totp.read_login_token(mfa_token)
        if user_id:
            row = db.query_one(
                f"SELECT {_USER_COLUMNS}, password_hash, locked_until, totp_secret FROM users "
                "WHERE id = ? AND deleted_at IS NULL",
                user_id,
            )
            if row is None or not row.get("totp_secret"):
                raise AuthError("That sign-in step expired. Start again.", 401, code="mfa_expired")
            if row["status"] != "active":
                raise AuthError("This account is suspended. Contact support.", 403)
            identifier = row["email"]
            locked_until = row.get("locked_until")
            if locked_until and locked_until > now_ms():
                raise AuthError("Account temporarily locked after repeated failures. Try again shortly.", 423)
            blocked, retry_after = auth_blocked(identifier, ip)
            if blocked:
                raise AuthError(f"Too many failed attempts. Try again in {retry_after // 60 + 1} minute(s).", 429)
            accepted, replacement = totp.verify_factor(row["totp_secret"], otp)
            if not accepted:
                _reject_factor(row, identifier, ip)
            with db.transaction():
                if not totp.consume_login_token(mfa_token, row["id"]):
                    raise AuthError("That sign-in step expired or was already used. Start again.", 401,
                                    code="mfa_replayed")
                _store_mfa_replacement(row, replacement)
            return _finish_login(row, identifier, ip, user_agent)

        # If it was not an authenticator token, try the delivered-code purpose.
        challenge_row = totp.active_challenge(mfa_token, delivered_otp.LOGIN_PURPOSE)
        if challenge_row:
            row = _otp_row(str(challenge_row["user_id"]))
            if row is None:
                raise AuthError("That sign-in code has expired. Start again.", 401, code="otp_expired")
            if row["status"] != "active":
                raise AuthError("This account is suspended. Contact support.", 403)
            identifier = row["email"]
            locked_until = row.get("locked_until")
            if locked_until and locked_until > now_ms():
                raise AuthError("Account temporarily locked after repeated failures. Try again shortly.", 423)
            blocked, retry_after = auth_blocked(identifier, ip)
            if blocked:
                raise AuthError(f"Too many failed attempts. Try again in {retry_after // 60 + 1} minute(s).", 429)
            result = delivered_otp.check_code(mfa_token, delivered_otp.LOGIN_PURPOSE, row["id"], otp)
            if result["status"] == "bad":
                _reject_otp(row, identifier, ip, mfa_token, result)
            if result["status"] == "ok":
                return _finish_login(row, identifier, ip, user_agent)
            if result["status"] == "exhausted":
                raise AuthError("That sign-in code has been used too many times. Start again.", 401,
                                code="otp_exhausted")
            if result["status"] == "replayed":
                raise AuthError("That sign-in step expired or was already used. Start again.", 401,
                                code="otp_expired")
            raise AuthError("That sign-in code has expired. Start again.", 401, code="otp_expired")

        # The row may still exist but be expired or consumed. Distinguish a
        # delivered-code token so the page can return to the password step with
        # the OTP-specific dead-challenge reason.
        old_challenge = db.query_one(
            "SELECT purpose FROM security_challenges WHERE token_hash = ?",
            totp._challenge_hash(mfa_token),
        )
        if old_challenge and old_challenge.get("purpose") == delivered_otp.LOGIN_PURPOSE:
            raise AuthError("That sign-in code has expired. Start again.", 401, code="otp_expired")
        raise AuthError("That sign-in step expired. Start again.", 401, code="mfa_expired")

    blocked, retry_after = auth_blocked(identifier, ip)
    if blocked:
        record("auth.login_failed", ip=ip, meta={"reason": "rate_limited"})
        raise AuthError(
            f"Too many failed attempts. Try again in {retry_after // 60 + 1} minute(s).", 429
        )

    row = find_by_email_or_username(identifier)
    if row is None:
        # Spend comparable time so "no such user" is not measurable.
        verify_password(password, "scrypt$16384$8$1$AAAAAAAAAAAAAAAAAAAAAA==$" + "A" * 88)
        register_login_attempt(identifier, ip, False, "no_such_user")
        record("auth.login_failed", ip=ip, meta={"reason": "no_such_user"})
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

    if needs_rehash(row["password_hash"]):
        db.execute("UPDATE users SET password_hash = ? WHERE id = ?", hash_password(password), row["id"])
    if row.get("totp_secret"):
        if otp:
            accepted, replacement = totp.verify_factor(row["totp_secret"], otp)
            if not accepted:
                _reject_factor(row, identifier, ip)
            _store_mfa_replacement(row, replacement)
        else:
            raise MfaRequired(totp.issue_login_token(row["id"]))
    elif get_settings().login_otp_required:
        raise _begin_otp_challenge(row)
    return _finish_login(row, identifier, ip, user_agent)


def resend_login_otp(
    token: str,
    *,
    channel: str | None = None,
    ip: str = "",
    user_agent: str = "",
) -> OtpRequired:
    """Resend or switch the delivered factor without invalidating it on cooldown."""
    from .security import otp, ratelimit, totp

    current = totp.active_challenge(token, otp.LOGIN_PURPOSE)
    if not current:
        raise AuthError("That sign-in code has expired. Start again.", 401, code="otp_expired")
    user_id = str(current["user_id"])
    row = _otp_row(user_id)
    if row is None or row["status"] != "active":
        raise AuthError("That sign-in code has expired. Start again.", 401, code="otp_expired")
    cooldown = ratelimit.shared_check(f"otp-resend:{user_id}", 1, 60)
    if not cooldown.allowed:
        raise AuthError("A new code was sent recently. Try again in a minute.", 429,
                        code="otp_rate_limited")
    # _begin_otp_challenge replaces the live row only after both limits have
    # passed. A blocked cooldown therefore leaves the old code usable. Without
    # an explicit switch, resend on the same channel as the live challenge.
    if not channel:
        details = otp.describe_challenge(token, otp.LOGIN_PURPOSE, user_id) or {}
        channel = details.get("channel") or None
    return _begin_otp_challenge(row, channel=channel)


# ---------------------------------------------------------------------------
# Phone number management
# ---------------------------------------------------------------------------

def _check_current_password(user_id: str, current_password: str) -> dict:
    row = db.query_one("SELECT id, password_hash FROM users WHERE id = ? AND deleted_at IS NULL", user_id)
    if row is None:
        raise AuthError("Account not found.", 404)
    if not current_password or not verify_password(current_password, row["password_hash"]):
        raise AuthError("Your current password is incorrect.", 403)
    return row


def set_phone(user_id: str, phone: str, current_password: str | None = None) -> str:
    """Save an unverified E.164 phone after a password check when supplied."""
    from .security import otp

    # Be tolerant of the natural ``(user_id, current_password, phone)`` calling
    # order used by a few integrations while keeping the documented order
    # ``(user_id, phone, current_password)``. Try the phone validator rather
    # than looking only for a leading plus, because pasted values may contain
    # formatting such as ``(+44)``.
    if current_password is not None:
        first_is_phone = True
        second_is_phone = True
        try:
            validators.validate_phone(phone)
        except validators.ValidationError:
            first_is_phone = False
        try:
            validators.validate_phone(current_password)
        except validators.ValidationError:
            second_is_phone = False
        if not first_is_phone and second_is_phone:
            phone, current_password = current_password, phone
        _check_current_password(user_id, current_password)
    normalized = validators.validate_phone(phone)
    try:
        with db.transaction():
            db.execute(
                "UPDATE users SET phone = ?, phone_verified = 0, updated_at = ? WHERE id = ? AND deleted_at IS NULL",
                normalized, now_ms(), user_id,
            )
            old = db.query_one(
                "SELECT token_hash FROM security_challenges WHERE user_id = ? AND purpose = ? "
                "AND consumed_at IS NULL",
                user_id, otp.PHONE_PURPOSE,
            )
            if old:
                # A changed number must not inherit a live challenge for the
                # previous number.
                db.execute("UPDATE security_challenges SET consumed_at = ? WHERE token_hash = ?",
                           now_ms(), old["token_hash"])
    except Exception as exc:
        if "unique" in str(exc).lower() or "duplicate" in str(exc).lower():
            raise AuthError("That phone number could not be saved.", 409, code="phone_taken") from exc
        raise
    record("auth.phone_set", actor_id=user_id, entity_type="user", entity_id=user_id)
    return normalized


def remove_phone(user_id: str, current_password: str | None = None) -> None:
    from .security import otp

    if current_password is not None:
        _check_current_password(user_id, current_password)
    db.execute("UPDATE users SET phone = NULL, phone_verified = 0, updated_at = ? WHERE id = ?", now_ms(), user_id)
    row = db.query_one(
        "SELECT token_hash FROM security_challenges WHERE user_id = ? AND purpose = ? AND consumed_at IS NULL",
        user_id, otp.PHONE_PURPOSE,
    )
    if row:
        db.execute("UPDATE security_challenges SET consumed_at = ? WHERE token_hash = ?", now_ms(), row["token_hash"])
    record("auth.phone_removed", actor_id=user_id, entity_type="user", entity_id=user_id)


def start_phone_verification(user_id: str, *, ip: str = "") -> str:
    from . import notify
    from .security import otp, ratelimit

    row = db.query_one("SELECT phone, phone_verified FROM users WHERE id = ? AND deleted_at IS NULL", user_id)
    if row is None or not row.get("phone"):
        raise AuthError("Add a phone number before requesting verification.", 422, code="phone_missing")
    if not notify.sms_is_configured():
        raise AuthError("This instance has no SMS transport.", 503, code="sms_unavailable")
    limited = ratelimit.shared_check(f"phone-verify:{user_id}", 5, 3600)
    if not limited.allowed:
        raise AuthError("Too many phone verification codes. Try again later.", 429,
                        code="phone_rate_limited")
    token, code = otp.issue_phone_challenge(
        user_id, masked=otp.mask_phone(row["phone"]), phone=row["phone"]
    )
    try:
        delivered = notify.send_phone_otp(row["phone"], code, minutes=10)
    except Exception:
        delivered = False
    if not delivered:
        otp.kill_challenge(token, otp.PHONE_PURPOSE, user_id)
        raise AuthError("We could not send a phone verification code.", 503,
                        code="phone_otp_undeliverable")
    record("auth.phone_verification_issued", actor_id=user_id, entity_type="user", entity_id=user_id)
    return token


def confirm_phone_verification(user_id: str, token: str, code: str) -> bool:
    from .security import otp

    result = otp.check_code(token, otp.PHONE_PURPOSE, user_id, code)
    if result["status"] == "ok":
        payload = result.get("payload") or {}
        phone = payload.get("phone")
        changed = db.execute(
            "UPDATE users SET phone_verified = 1, updated_at = ? "
            "WHERE id = ? AND phone = ? AND phone IS NOT NULL",
            now_ms(), user_id, phone,
        )
        if changed != 1:
            raise AuthError("That phone number changed. Start verification again.", 409, code="phone_changed")
        record("auth.phone_verified", actor_id=user_id, entity_type="user", entity_id=user_id)
        return True
    if result["status"] == "bad":
        raise AuthError(
            f"That code was not accepted. {result.get('attempts_left', 0)} attempts left.",
            401,
            code="phone_code_invalid",
        )
    if result["status"] == "exhausted":
        raise AuthError("That phone verification code has been used too many times.", 401,
                        code="otp_exhausted")
    raise AuthError("That phone verification step expired or was already used.", 401,
                    code="otp_expired")


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
    lock = " FOR UPDATE" if db.uses_postgres() else ""
    with db.transaction():
        db.query_one("SELECT id FROM users WHERE id = ?" + lock, user_id)
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
    digest = _hash_reset_token(token)
    ts = now_ms()
    with db.transaction():
        row = db.query_one(
            "SELECT user_id, expires_at FROM password_resets "
            "WHERE token_hash = ? AND used_at IS NULL",
            digest,
        )
        if not row:
            return None
        if int(row["expires_at"]) < ts:
            db.execute(
                "DELETE FROM password_resets WHERE token_hash = ? AND used_at IS NULL", digest
            )
            return None
        claimed = db.execute(
            "UPDATE password_resets SET used_at = ? "
            "WHERE token_hash = ? AND used_at IS NULL AND expires_at >= ?",
            ts, digest, ts,
        )
        return str(row["user_id"]) if claimed == 1 else None


def prune_password_resets() -> int:
    """Deletes expired rows; called opportunistically rather than by a cron job."""
    return db.execute("DELETE FROM password_resets WHERE expires_at < ?", now_ms() - DAY)


# ---------------------------------------------------------------------------
# Email confirmation
# ---------------------------------------------------------------------------

VERIFY_TOKEN_TTL_MS = 24 * 60 * 60_000


def issue_email_verification(user_id: str, ip: str | None = None) -> str:
    """Creates a confirmation token and returns the plaintext, once."""
    token = secrets.token_urlsafe(32)
    ts = now_ms()
    lock = " FOR UPDATE" if db.uses_postgres() else ""
    with db.transaction():
        db.query_one("SELECT id FROM users WHERE id = ?" + lock, user_id)
        db.execute("DELETE FROM email_verifications WHERE user_id = ?", user_id)
        db.execute(
            "INSERT INTO email_verifications (token_hash, user_id, created_at, expires_at, ip) "
            "VALUES (?,?,?,?,?)",
            _hash_reset_token(token), user_id, ts, ts + VERIFY_TOKEN_TTL_MS, ip,
        )
    record("auth.verification_issued", actor_id=user_id, ip=ip)
    return token


def revoke_email_verification(token: str) -> None:
    """Drops a token that was never delivered. Does not confirm the address."""
    if not token:
        return
    db.execute("DELETE FROM email_verifications WHERE token_hash = ?", _hash_reset_token(token))


def consume_email_verification(token: str) -> str | None:
    """Marks the address confirmed. Returns the user id, or None.

    A wildcard such as ``%`` cannot match a row: the lookup is the SHA-256 of
    the submitted token, compared exactly.
    """
    if not token or len(token) > 200:
        return None
    digest = _hash_reset_token(token)
    ts = now_ms()
    with db.transaction():
        row = db.query_one(
            "SELECT user_id, expires_at FROM email_verifications "
            "WHERE token_hash = ? AND used_at IS NULL",
            digest,
        )
        if not row:
            return None
        if int(row["expires_at"]) < ts:
            db.execute(
                "DELETE FROM email_verifications WHERE token_hash = ? AND used_at IS NULL", digest
            )
            return None
        claimed = db.execute(
            "UPDATE email_verifications SET used_at = ? "
            "WHERE token_hash = ? AND used_at IS NULL AND expires_at >= ?",
            ts, digest, ts,
        )
        if claimed != 1:
            return None
        user_id = str(row["user_id"])
        db.execute(
            "UPDATE users SET email_verified = 1, updated_at = ? WHERE id = ?",
            ts, user_id,
        )
    record("auth.email_verified", actor_id=user_id, entity_type="user", entity_id=user_id)
    return user_id


def deliver_email_verification(user_id: str, email: str, ip: str | None = None) -> tuple[str, str]:
    """Send a confirmation link, or refuse to invent one.

    Returns ``(status, dev_token)``. ``dev_token`` is non-empty only in a
    development/test environment when mail is not configured and
    ``ENGINEVERSE_REVEAL_RESET_TOKEN`` is on. Staging and production never
    reveal it. A failed send deletes the token.
    The token is never returned on the sent path.
    """
    from . import notify

    row = db.query_one("SELECT email_verified FROM users WHERE id = ?", user_id)
    if row is None:
        return "unavailable", ""
    if int(row["email_verified"] or 0):
        return "verified", ""
    settings = get_settings()
    reveal = bool(settings.reveal_reset_token and settings.allows_demo_accounts and not notify.is_configured())
    if not notify.is_configured() and not reveal:
        return "unavailable", ""
    token = issue_email_verification(user_id, ip=ip)
    if notify.is_configured():
        url = f"{settings.site_url}/verify-email?token={token}"
        if notify.send_email_verification(email=email, verify_url=url):
            return "sent", ""
        revoke_email_verification(token)
        return "unavailable", ""
    return "reveal", token


def site_url() -> str:
    return get_settings().site_url
