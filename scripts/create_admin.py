#!/usr/bin/env python3
"""Create the first super administrator.

The password is read from ``ENGINEVERSE_ADMIN_PASSWORD`` or from a prompt. It
is never accepted as a command-line argument, because those appear in process
listings and in shell history.

Refuses when a super administrator already exists, unless ``--replace`` is
passed and ``ENGINEVERSE_ALLOW_ADMIN_REPLACE=yes``. Replacement updates the
password hash, revokes sessions, and clears that account's authenticator
seal. It does not print the old or new password, the seal, or a recovery code.
"""
from __future__ import annotations

import argparse
import getpass
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for path in (ROOT, os.path.join(ROOT, "backend")):
    if path not in sys.path:
        sys.path.insert(0, path)

from engineverse import auth, db  # noqa: E402
from engineverse.config import get_settings  # noqa: E402
from engineverse.security.audit import record  # noqa: E402
from engineverse.security.ids import now_ms  # noqa: E402
from engineverse.security.passwords import check_password_strength, hash_password  # noqa: E402


class AdminRefused(RuntimeError):
    """An operator error. The message never contains the password."""


def _existing_super_admin() -> dict | None:
    if not db.table_exists("users"):
        return None
    return db.query_one(
        "SELECT id, email, username FROM users WHERE role = 'super_admin' AND deleted_at IS NULL LIMIT 1"
    )


def create_super_admin(
    *,
    email: str,
    username: str,
    full_name: str,
    password: str,
    replace: bool = False,
) -> str:
    """Creates or, when explicitly allowed, re-keys the super administrator.

    Returns the user id. Raises ``AdminRefused`` for operator errors. Does not
    include the password in any exception message.
    """
    settings = get_settings()
    if settings.is_production:
        problems = settings.production_problems()
        if problems:
            raise SystemExit("refusing to create an administrator: " + "; ".join(problems))
    if not db.table_exists("users"):
        db.migrate()
    issues = check_password_strength(password, context=[email, username, full_name])
    if issues:
        raise AdminRefused("Password refused: " + "; ".join(issue.message for issue in issues))
    existing = _existing_super_admin()
    if existing and not replace:
        raise AdminRefused(
            "A super administrator already exists. Refusing to create another. "
            "Recovery is a deliberate database operation, not a second bootstrap."
        )
    if existing and replace:
        if os.environ.get("ENGINEVERSE_ALLOW_ADMIN_REPLACE") != "yes":
            raise AdminRefused(
                "Refusing to replace an existing super administrator. "
                "Set ENGINEVERSE_ALLOW_ADMIN_REPLACE=yes only for an intentional recovery."
            )
        db.execute(
            "UPDATE users SET password_hash = ?, password_changed_at = ?, failed_login_count = 0, "
            "locked_until = NULL, updated_at = ? WHERE id = ?",
            hash_password(password),
            now_ms(),
            now_ms(),
            existing["id"],
        )
        db.execute("UPDATE users SET totp_secret = NULL WHERE id = ?", existing["id"])
        db.execute(
            "UPDATE sessions SET revoked_at = ? WHERE user_id = ? AND revoked_at IS NULL",
            now_ms(),
            existing["id"],
        )
        record(
            "auth.password_changed",
            actor_id=existing["id"],
            entity_type="user",
            entity_id=existing["id"],
            meta={"via": "create_admin_replace"},
        )
        return existing["id"]
    user = auth.register(
        email=email.strip(),
        username=username.strip(),
        password=password,
        full_name=full_name.strip(),
        ip="127.0.0.1",
        user_agent="engineverse-create-admin",
    )
    db.execute(
        "UPDATE users SET role = 'super_admin', email_verified = 1, updated_at = ? WHERE id = ?",
        now_ms(),
        user["id"],
    )
    record(
        "auth.role_changed",
        actor_id=user["id"],
        entity_type="user",
        entity_id=user["id"],
        meta={"role": "super_admin", "via": "create_admin"},
    )
    return user["id"]


def _read_password() -> str:
    password = os.environ.get("ENGINEVERSE_ADMIN_PASSWORD", "")
    os.environ.pop("ENGINEVERSE_ADMIN_PASSWORD", None)
    if password:
        return password
    if not sys.stdin.isatty():
        raise SystemExit(
            "Set ENGINEVERSE_ADMIN_PASSWORD or run from a terminal. "
            "The password is not accepted as an argument."
        )
    password = getpass.getpass("Administrator password: ")
    again = getpass.getpass("Repeat password: ")
    if password != again:
        raise SystemExit("Passwords did not match.")
    return password


def main() -> int:
    parser = argparse.ArgumentParser(description="Create the first EngineVerse super administrator.")
    parser.add_argument("--email", required=True)
    parser.add_argument("--username", required=True)
    parser.add_argument("--full-name", default="Site administrator")
    parser.add_argument(
        "--replace",
        action="store_true",
        help="re-key the existing super administrator; also requires ENGINEVERSE_ALLOW_ADMIN_REPLACE=yes",
    )
    args, unknown = parser.parse_known_args()
    if unknown:
        print(
            "Unexpected arguments. The password is not accepted on the command line.",
            file=sys.stderr,
        )
        return 2
    try:
        user_id = create_super_admin(
            email=args.email,
            username=args.username,
            full_name=args.full_name,
            password=_read_password(),
            replace=args.replace,
        )
    except (AdminRefused, auth.AuthError) as exc:
        message = exc.message if isinstance(exc, auth.AuthError) else str(exc)
        if message:
            print(message, file=sys.stderr)
        return 1
    print(f"Super administrator is ready ({user_id}). The password was not printed.")
    if args.replace:
        print("Authenticator enrollment was cleared. Set it up again after signing in.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
