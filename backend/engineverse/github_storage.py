"""GitHub repository & BaaS learner progress storage.

Allows learners who use the public GitHub Pages site or the Android APK without
cloning/installing the repository to save and sync their progress with the
repository owner's GitHub (`authorsauravkushwaha/EngineVerse` in
`data/learners/registry.json`), or via optional Supabase, Appwrite, or n8n
endpoints.

Only validated, non-sensitive progress records and password SHA-256 digests are
accepted into the registry; raw passwords, session tokens, and server secrets
are rejected.
"""
from __future__ import annotations

import base64
import hashlib
import json
import os
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from . import coding, db, progress
from .config import REPO_ROOT
from .security.sanitize import strip_html

DEFAULT_REPO = "authorsauravkushwaha/EngineVerse"
REGISTRY_REL_PATH = "data/learners/registry.json"
DEFAULT_REGISTRY_PATH = REPO_ROOT / REGISTRY_REL_PATH

_USERNAME_RE = re.compile(r"^[A-Za-z0-9_.-]{3,24}\Z")
_SLUG_RE = re.compile(r"^[A-Za-z0-9_.:/-]{1,128}\Z")
_DIGEST_RE = re.compile(r"^(?:sha256:[0-9a-f]{64}|[0-9a-f]{64})\Z")
_DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}\Z")
_FORBIDDEN_KEYS = frozenset({"password", "raw_password", "secret", "token", "cookie", "session_token", "totp_secret"})


class LearnerSyncError(ValueError):
    """Raised when a learner progress snapshot fails validation."""


def _utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _clean_text(value: Any, max_len: int = 120) -> str:
    if not isinstance(value, str):
        return ""
    cleaned = re.sub(r"\s+", " ", strip_html(value)).strip()
    return cleaned[:max_len]


def _clean_slug_list(values: Any, max_items: int = 500) -> list[str]:
    if not isinstance(values, list):
        return []
    out: list[str] = []
    seen: set[str] = set()
    for item in values:
        if not isinstance(item, str):
            continue
        slug = item.strip()
        if _SLUG_RE.fullmatch(slug) and slug not in seen:
            seen.add(slug)
            out.append(slug)
            if len(out) >= max_items:
                break
    return sorted(out)


def _clean_days(days: Any) -> dict[str, int]:
    if not isinstance(days, dict):
        return {}
    out: dict[str, int] = {}
    for key, val in days.items():
        if isinstance(key, str) and _DATE_RE.fullmatch(key):
            try:
                count = max(1, min(1000, int(val)))
            except (TypeError, ValueError):
                count = 1
            out[key] = count
            if len(out) >= 730:
                break
    return dict(sorted(out.items()))


def hash_password_digest(username: str, password: str) -> str:
    """Deterministic salted SHA-256 digest matching the browser Web Crypto helper."""
    material = f"engineverse-v1:{username.strip().lower()}:{password}".encode("utf-8")
    return "sha256:" + hashlib.sha256(material).hexdigest()


def verify_password_digest(username: str, password: str, expected_digest: str) -> bool:
    """Verify a password against either `sha256:<hex>` or `<hex>` digest."""
    if not expected_digest:
        return False
    expected = expected_digest.strip().lower()
    if not expected.startswith("sha256:"):
        expected = "sha256:" + expected
    actual = hash_password_digest(username, password)
    return actual == expected


StorageValidationError = LearnerSyncError


def validate_snapshot(payload: dict[str, Any]) -> dict[str, Any]:
    """Validate and canonicalize a learner progress snapshot."""
    if not isinstance(payload, dict):
        raise LearnerSyncError("Learner snapshot must be a JSON object.")
    bad_keys = _FORBIDDEN_KEYS.intersection({str(k).lower() for k in payload})
    if bad_keys:
        raise LearnerSyncError("Refusing snapshot containing raw credentials or session secrets.")

    username_raw = str(payload.get("username") or "").strip()
    if not _USERNAME_RE.fullmatch(username_raw):
        raise LearnerSyncError("Username must be 3–24 characters (letters, numbers, ., _, -).")
    username = username_raw.lower()

    full_name = _clean_text(
        payload.get("full_name") or payload.get("display_name") or username_raw, 80
    ) or username_raw
    branch_id = _clean_text(payload.get("branch_id") or payload.get("branch") or "", 64)
    semester_id = _clean_text(
        str(payload.get("semester_id") or payload.get("semester") or payload.get("year_of_study") or ""),
        16,
    )
    headline = _clean_text(payload.get("headline") or "", 120)
    bio = _clean_text(payload.get("bio") or "", 600)
    country = _clean_text(payload.get("country") or "", 60)

    digest = str(payload.get("password_digest") or payload.get("password_sha256") or "").strip().lower()
    if digest and not _DIGEST_RE.fullmatch(digest):
        raise LearnerSyncError("password_digest must be a 64-character hex SHA-256 digest.")
    if digest and not digest.startswith("sha256:"):
        digest = "sha256:" + digest

    email_hash = str(payload.get("email_sha256") or "").strip().lower()
    if not email_hash and isinstance(payload.get("email"), str) and "@" in payload["email"]:
        email_hash = hashlib.sha256(payload["email"].strip().lower().encode("utf-8")).hexdigest()
    elif email_hash and not re.fullmatch(r"[0-9a-f]{64}", email_hash):
        email_hash = ""

    def _bounded_int(key: str, default: int = 0, maximum: int = 10_000_000) -> int:
        val = payload.get(key, default)
        if isinstance(val, bool):
            return default
        try:
            return max(0, min(maximum, int(val)))
        except (TypeError, ValueError):
            return default

    xp = _bounded_int("xp", 0, 5_000_000)
    level = max(1, (xp // 250) + 1)
    streak = _bounded_int("streak", _bounded_int("streak_days", 0, 3650), 3650)
    longest_streak = max(streak, _bounded_int("longest_streak", streak, 3650))
    checks = _bounded_int("checks", _bounded_int("quiz_attempts", 0, 500_000), 500_000)
    correct_checks = min(checks, _bounded_int("correct_checks", _bounded_int("quiz_correct", 0, 500_000), 500_000))
    minutes = _bounded_int("minutes", 0, 1_000_000)

    completed_topics = _clean_slug_list(payload.get("completed_topics", []), 600)
    solved_problems = _clean_slug_list(payload.get("solved_problems", []), 400)
    mistakes = _clean_slug_list(payload.get("mistakes", []), 400)
    bookmarks = _clean_slug_list(payload.get("bookmarks", []), 400)
    reviewed_cards = _clean_slug_list(payload.get("reviewed_cards", []), 600)
    raw_days = payload.get("days", {})
    if not raw_days and isinstance(payload.get("activity_days"), list):
        raw_days = {str(d): 1 for d in payload["activity_days"] if isinstance(d, str)}
    days = _clean_days(raw_days)

    country_code = _clean_text(payload.get("country_code") or "+91", 8)
    if not re.fullmatch(r"\+[1-9][0-9]{0,3}", country_code):
        country_code = "+91"
    phone_hash = str(payload.get("phone_sha256") or "").strip().lower()
    if not phone_hash and isinstance(payload.get("phone"), str) and payload["phone"].strip():
        phone_hash = hashlib.sha256(payload["phone"].strip().encode("utf-8")).hexdigest()
    elif phone_hash and not re.fullmatch(r"[0-9a-f]{64}", phone_hash):
        phone_hash = ""
    otp_verified = bool(payload.get("otp_verified", True))
    year_of_study = max(1, min(6, _bounded_int("year_of_study", 1, 6)))

    return {
        "username": username,
        "display_username": username_raw,
        "full_name": full_name,
        "display_name": full_name,
        "email_sha256": email_hash,
        "phone_sha256": phone_hash,
        "country_code": country_code,
        "otp_verified": otp_verified,
        "password_digest": digest,
        "password_sha256": digest.removeprefix("sha256:") if digest else "",
        "branch_id": branch_id,
        "branch": branch_id or "cse",
        "semester_id": semester_id,
        "year_of_study": year_of_study,
        "headline": headline,
        "bio": bio,
        "country": country,
        "xp": xp,
        "level": level,
        "streak": streak,
        "streak_days": streak,
        "longest_streak": longest_streak,
        "checks": checks,
        "quiz_attempts": checks,
        "correct_checks": correct_checks,
        "quiz_correct": correct_checks,
        "minutes": minutes,
        "completed_topics": completed_topics,
        "solved_problems": solved_problems,
        "mistakes": mistakes,
        "bookmarks": bookmarks,
        "reviewed_cards": reviewed_cards,
        "days": days,
        "activity_days": sorted(days.keys()),
        "updated_at": _utc_now(),
    }


normalize_learner_snapshot = validate_snapshot


def merge_records(existing: dict[str, Any] | None, incoming: dict[str, Any]) -> dict[str, Any]:
    """Merge an incoming validated snapshot with an existing record monotonically."""
    clean = validate_snapshot(incoming)
    if not existing:
        return clean

    prev_digest = existing.get("password_digest") or ""
    otp_override = bool(incoming.get("password_changed_via_otp"))
    if prev_digest and clean["password_digest"] and prev_digest != clean["password_digest"] and not otp_override:
        raise LearnerSyncError("Password digest does not match the registered GitHub learner account.")

    days = dict(existing.get("days") or {})
    for day, count in clean["days"].items():
        days[day] = max(days.get(day, 0), count)

    completed_topics = sorted(set(existing.get("completed_topics") or []) | set(clean["completed_topics"]))
    solved_problems = sorted(set(existing.get("solved_problems") or []) | set(clean["solved_problems"]))
    bookmarks = sorted(set(existing.get("bookmarks") or []) | set(clean["bookmarks"]))
    reviewed_cards = sorted(set(existing.get("reviewed_cards") or []) | set(clean["reviewed_cards"]))
    # Mistakes can be resolved, so prefer the incoming mistake list if non-empty or explicitly updated
    mistakes = clean["mistakes"] if "mistakes" in incoming else list(existing.get("mistakes") or [])

    xp = max(int(existing.get("xp") or 0), clean["xp"], len(completed_topics) * 20 + len(solved_problems) * 25)
    level = max(1, (xp // 250) + 1)
    streak = max(int(existing.get("streak") or 0), clean["streak"])
    longest_streak = max(int(existing.get("longest_streak") or 0), clean["longest_streak"], streak)
    checks = max(int(existing.get("checks") or 0), clean["checks"])
    correct_checks = max(int(existing.get("correct_checks") or 0), clean["correct_checks"])
    minutes = max(int(existing.get("minutes") or 0), clean["minutes"])

    full_name = clean["full_name"] or existing.get("full_name") or clean["username"]
    merged_digest = (clean["password_digest"] if otp_override and clean["password_digest"] else (prev_digest or clean["password_digest"]))
    sorted_days = dict(sorted(days.items()))
    return {
        "username": clean["username"],
        "display_username": clean["display_username"] or existing.get("display_username") or clean["username"],
        "full_name": full_name,
        "display_name": full_name,
        "email_sha256": clean["email_sha256"] or existing.get("email_sha256") or "",
        "phone_sha256": clean["phone_sha256"] or existing.get("phone_sha256") or "",
        "country_code": clean["country_code"] or existing.get("country_code") or "+91",
        "otp_verified": bool(clean.get("otp_verified", True) or existing.get("otp_verified", True)),
        "password_digest": merged_digest,
        "password_sha256": merged_digest.removeprefix("sha256:") if merged_digest else "",
        "branch_id": clean["branch_id"] or existing.get("branch_id") or "",
        "branch": clean["branch_id"] or existing.get("branch_id") or "cse",
        "semester_id": clean["semester_id"] or existing.get("semester_id") or "",
        "year_of_study": clean.get("year_of_study") or existing.get("year_of_study") or 1,
        "headline": clean["headline"] or existing.get("headline") or "",
        "bio": clean["bio"] or existing.get("bio") or "",
        "country": clean["country"] or existing.get("country") or "",
        "xp": xp,
        "level": level,
        "streak": streak,
        "streak_days": streak,
        "longest_streak": longest_streak,
        "checks": checks,
        "quiz_attempts": checks,
        "correct_checks": correct_checks,
        "quiz_correct": correct_checks,
        "minutes": minutes,
        "completed_topics": completed_topics,
        "solved_problems": solved_problems,
        "mistakes": mistakes,
        "bookmarks": bookmarks,
        "reviewed_cards": reviewed_cards,
        "days": sorted_days,
        "activity_days": sorted(sorted_days.keys()),
        "updated_at": _utc_now(),
    }


def load_registry(path: Path = DEFAULT_REGISTRY_PATH) -> dict[str, Any]:
    if not path.exists():
        return {"version": 1, "repository": DEFAULT_REPO, "updated_at": _utc_now(), "learners": {}}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(data, dict) or not isinstance(data.get("learners"), dict):
            raise ValueError("invalid registry")
        return data
    except (OSError, ValueError):
        return {"version": 1, "repository": DEFAULT_REPO, "updated_at": _utc_now(), "learners": {}}


def save_snapshot_to_registry(snapshot: dict[str, Any], path: Path = DEFAULT_REGISTRY_PATH) -> dict[str, Any]:
    registry = load_registry(path)
    learners = registry.setdefault("learners", {})
    validated = validate_snapshot(snapshot)
    key = validated["username"]
    merged = merge_records(learners.get(key), snapshot)
    learners[key] = merged
    registry["updated_at"] = _utc_now()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(registry, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return merged


def build_db_user_snapshot(user_id: str) -> dict[str, Any]:
    """Export a database-backed learner's progress into the portable GitHub snapshot format."""
    user = db.query_one("SELECT id, username, email, role FROM users WHERE id = ?", user_id)
    if not user:
        raise LearnerSyncError("User not found.")
    prof = db.query_one("SELECT * FROM profiles WHERE user_id = ?", user_id) or {}
    stats = progress.user_stats(user_id)
    topics = [
        row["slug"]
        for row in db.query(
            "SELECT t.slug FROM user_progress up JOIN topics t ON t.id = up.topic_id "
            "WHERE up.user_id = ? AND up.status = 'completed' ORDER BY t.slug",
            user_id,
        )
    ]
    solved = [
        row["slug"]
        for row in db.query(
            "SELECT DISTINCT p.slug FROM coding_submissions cs JOIN coding_problems p ON p.id = cs.problem_id "
            "WHERE cs.user_id = ? AND cs.is_accepted = 1 ORDER BY p.slug",
            user_id,
        )
    ]
    bms = [
        f"{row['entity_type']}:{row['entity_id']}"
        for row in db.query("SELECT entity_type, entity_id FROM bookmarks WHERE user_id = ?", user_id)
    ]
    heat = {
        row["day"]: max(1, int(row.get("xp") or 1))
        for row in db.query("SELECT day, xp FROM activity WHERE user_id = ?", user_id)
        if row.get("day")
    }
    return validate_snapshot({
        "username": user["username"],
        "full_name": prof.get("full_name") or user["username"],
        "email": user.get("email") or "",
        "branch_id": prof.get("branch_id") or "",
        "semester_id": prof.get("semester_id") or "",
        "headline": prof.get("headline") or "",
        "bio": prof.get("bio") or "",
        "country": prof.get("country") or "",
        "xp": stats.get("xp", 0),
        "streak": stats.get("currentStreak", 0),
        "longest_streak": stats.get("longestStreak", 0),
        "minutes": stats.get("minutes", 0),
        "completed_topics": topics,
        "solved_problems": solved,
        "bookmarks": bms,
        "days": heat,
    })


def push_registry_to_github(
    path: Path = DEFAULT_REGISTRY_PATH,
    *,
    repo: str | None = None,
    token: str | None = None,
    branch: str = "main",
) -> dict[str, Any]:
    """Push `data/learners/registry.json` to the GitHub repository via the Contents API."""
    repo = (repo or os.environ.get("ENGINEVERSE_GITHUB_STORAGE_REPO") or DEFAULT_REPO).strip()
    token = (token or os.environ.get("ENGINEVERSE_GITHUB_TOKEN") or os.environ.get("GH_TOKEN") or "").strip()
    if not re.fullmatch(r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+", repo):
        raise LearnerSyncError("Invalid GitHub repository slug.")
    if not token:
        return {"pushed": False, "reason": "local_registry_saved_no_token", "repository": repo}

    content_bytes = path.read_bytes()
    api_url = f"https://api.github.com/repos/{repo}/contents/{REGISTRY_REL_PATH}"
    headers = {
        "Accept": "application/vnd.github+json",
        "Authorization": f"Bearer {token}",
        "User-Agent": "EngineVerse-GitHub-Storage/1.0",
        "X-GitHub-Api-Version": "2022-11-28",
    }
    sha = None
    try:
        req = Request(f"{api_url}?ref={branch}", headers=headers)
        with urlopen(req, timeout=10) as res:
            existing = json.loads(res.read().decode("utf-8"))
            sha = existing.get("sha")
    except HTTPError as exc:
        if exc.code != 404:
            return {"pushed": False, "reason": f"github_read_http_{exc.code}", "repository": repo}
    except (URLError, TimeoutError, OSError):
        return {"pushed": False, "reason": "github_unreachable", "repository": repo}

    body: dict[str, Any] = {
        "message": f"chore(learners): sync EngineVerse learner progress ({_utc_now()})",
        "content": base64.b64encode(content_bytes).decode("ascii"),
        "branch": branch,
    }
    if sha:
        body["sha"] = sha

    try:
        put_req = Request(
            api_url,
            data=json.dumps(body).encode("utf-8"),
            headers={**headers, "Content-Type": "application/json"},
            method="PUT",
        )
        with urlopen(put_req, timeout=12) as res:
            result = json.loads(res.read().decode("utf-8"))
            return {
                "pushed": True,
                "repository": repo,
                "commit_sha": (result.get("commit") or {}).get("sha", ""),
            }
    except (HTTPError, URLError, TimeoutError, OSError) as exc:
        return {"pushed": False, "reason": str(exc)[:120], "repository": repo}


def sync_status(path: Path = DEFAULT_REGISTRY_PATH) -> dict[str, Any]:
    registry = load_registry(path)
    learners = registry.get("learners") or {}
    return {
        "ok": True,
        "repository": registry.get("repository") or DEFAULT_REPO,
        "registry_path": REGISTRY_REL_PATH,
        "learner_count": len(learners),
        "updated_at": registry.get("updated_at") or "",
        "providers": {
            "github": {
                "repository": DEFAULT_REPO,
                "contents_api": f"https://api.github.com/repos/{DEFAULT_REPO}/contents/{REGISTRY_REL_PATH}",
                "issue_sync_url": f"https://github.com/{DEFAULT_REPO}/issues/new",
                "workflow": ".github/workflows/learner-data-sync.yml",
            },
            "supabase": {"supported": True, "table": "engineverse_learners"},
            "appwrite": {"supported": True, "collection": "engineverse_learners"},
            "n8n": {"supported": True, "webhook_event": "engineverse.learner.sync"},
        },
    }
