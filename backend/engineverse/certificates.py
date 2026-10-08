"""Tiered completion certificates.

A certificate here is a *record of measured work*, not a credential. The tier
is computed from data the platform already holds — topic completion, practice
accuracy, streak length, mastery — and every certificate carries a public
verify id so anyone can check what it claims.

Two things this module deliberately does not do:

* It never implies university or government accreditation. The page says so in
  plain words, and the wording is the same on every tier.
* It never issues on request. `evaluate()` reads the database and returns the
  highest tier the evidence supports; if the evidence is not there the answer
  is `None`, and the API refuses.

The issuer name is configurable through `site_config` because the rest of the
branding is; it is read at render time, not baked in.
"""

from __future__ import annotations

from typing import Any

from . import brand, db, progress
from .security.ids import now_ms, ulid

DEFAULT_ISSUER = "Saurav Kushwaha"

#: Tiers in ascending order. Each entry names what it adds on top of the tier
#: below, so `evaluate()` can walk up and stop at the first one that fails.
#: The thresholds are data rather than code so they can be tuned without
#: touching the logic that reads them.
TIERS: list[dict[str, Any]] = [
    {
        "name": "bronze",
        "label": "Bronze",
        "summary": "Completed every topic in the subject.",
        "requirements": {"completion_pct": 100},
    },
    {
        "name": "silver",
        "label": "Silver",
        "summary": "Completed the subject and kept a 14-day learning streak.",
        "requirements": {"completion_pct": 100, "longest_streak_days": 14},
    },
    {
        "name": "gold",
        "label": "Gold",
        "summary": "Completed the subject, 14-day streak, and 85% practice accuracy.",
        "requirements": {"completion_pct": 100, "longest_streak_days": 14, "accuracy_pct": 85},
    },
    {
        "name": "platinum",
        "label": "Platinum",
        "summary": "Completed the subject, 30-day streak, 85% accuracy and 90% mastery.",
        "requirements": {"completion_pct": 100, "longest_streak_days": 30,
                         "accuracy_pct": 85, "mastery_pct": 90},
    },
]

TIER_ORDER = [tier["name"] for tier in TIERS]
TIER_LABELS = {tier["name"]: tier["label"] for tier in TIERS}


def tier_by_name(name: str) -> dict[str, Any]:
    for tier in TIERS:
        if tier["name"] == name:
            return tier
    raise KeyError(f"unknown certificate tier {name!r}; expected one of {TIER_ORDER}")


def issuer_name() -> str:
    """The name printed as issuer. Configurable, so branding stays data-driven."""
    try:
        value = brand.get("certificate_issuer")
    except Exception:      # a missing config row must not break a certificate page
        value = None
    return (value or DEFAULT_ISSUER).strip() or DEFAULT_ISSUER


# ---------------------------------------------------------------------------
# Evidence
# ---------------------------------------------------------------------------

def evidence(user_id: str, subject_id: str) -> dict[str, int]:
    """The four numbers every tier decision is made from.

    Kept separate from `evaluate()` so the certificate page can show the
    learner exactly what was measured and what is still missing.
    """
    subject = progress.subject_progress(user_id, subject_id)
    stats = progress.user_stats(user_id)
    # ``user_stats`` uses camelCase keys. Reading one that does not exist would
    # return None, default to zero, and quietly stop anyone ever reaching
    # silver — so the two cross-module keys are asserted rather than defaulted.
    for key in ("longestStreak", "accuracy"):
        if key not in stats:
            raise KeyError(f"user_stats no longer provides {key!r}; certificate tiers depend on it")
    return {
        "completion_pct": int(subject.get("pct") or 0),
        "mastery_pct": int(subject.get("mastery") or 0),
        "longest_streak_days": int(stats.get("longestStreak") or 0),
        "accuracy_pct": int(stats.get("accuracy") or 0),
        "topics_completed": int(subject.get("completed") or 0),
        "topics_total": int(subject.get("total") or 0),
    }


def _meets(requirements: dict[str, int], evidence_map: dict[str, int]) -> bool:
    return all(int(evidence_map.get(key, 0)) >= int(value) for key, value in requirements.items())


def evaluate(user_id: str, subject_id: str) -> tuple[dict[str, Any], dict[str, int]] | None:
    """The highest tier the learner's record supports, and the numbers behind it.

    Returns ``None`` when even bronze is not earned. Walks the tiers in order
    and stops at the first failure, because the requirements are cumulative by
    construction: platinum implies gold implies silver implies bronze.
    """
    numbers = evidence(user_id, subject_id)
    earned: dict[str, Any] | None = None
    for tier in TIERS:
        if _meets(tier["requirements"], numbers):
            earned = tier
        else:
            break
    return (earned, numbers) if earned else None


def next_requirement(tier_name: str) -> list[tuple[str, int]]:
    """What the next tier up asks for, as (metric, threshold) pairs."""
    index = TIER_ORDER.index(tier_name) if tier_name in TIER_ORDER else -1
    if index + 1 >= len(TIERS):
        return []
    return sorted(TIERS[index + 1]["requirements"].items())


# ---------------------------------------------------------------------------
# Issuing
# ---------------------------------------------------------------------------

def issue_for_subject(user_id: str, subject_id: str) -> dict[str, Any] | None:
    """Issue or upgrade the certificate for a subject. Returns the row, or None.

    A learner who improves is upgraded rather than given a second certificate:
    one record per subject, at the highest tier their evidence supports. That
    keeps a portfolio honest and stops the same completion being counted twice.
    """
    result = evaluate(user_id, subject_id)
    if not result:
        return None
    tier, numbers = result
    subject = db.query_one("SELECT id, name FROM subjects WHERE id = ?", subject_id)
    if not subject:
        return None
    title = f"{subject['name']} - {tier['label']} Certificate of Completion"

    existing = db.query_one(
        "SELECT id, tier FROM certificates WHERE user_id = ? AND entity_type = 'subject' AND entity_id = ?",
        user_id, subject_id,
    )
    if existing:
        if TIER_ORDER.index(tier["name"]) <= TIER_ORDER.index(existing["tier"] or "bronze"):
            return db.query_one("SELECT * FROM certificates WHERE id = ?", existing["id"])
        db.execute(
            "UPDATE certificates SET tier = ?, title = ?, meta = ? WHERE id = ?",
            tier["name"], title, _meta(numbers, subject["name"]), existing["id"],
        )
        progress.notify(user_id, "certificate", f"{tier['label']} certificate earned", title,
                        _verify_url(existing["id"]))
        return db.query_one("SELECT * FROM certificates WHERE id = ?", existing["id"])

    cert_id = ulid()
    verify_id = _new_verify_id()
    db.execute(
        "INSERT INTO certificates (id,user_id,kind,entity_type,entity_id,title,verify_id,issued_at,meta,tier) "
        "VALUES (?,?,?,?,?,?,?,?,?,?)",
        cert_id, user_id, "subject", "subject", subject_id, title, verify_id,
        now_ms(), _meta(numbers, subject["name"]), tier["name"],
    )
    progress.notify(user_id, "certificate", f"{tier['label']} certificate earned", title,
                    _verify_url(cert_id))
    return db.query_one("SELECT * FROM certificates WHERE id = ?", cert_id)


def refresh_for_user(user_id: str) -> list[dict[str, Any]]:
    """Re-evaluate every subject the learner has touched. Called after progress changes."""
    rows = db.query(
        "SELECT DISTINCT t.subject_id AS subject_id FROM user_progress up "
        "JOIN topics t ON t.id = up.topic_id WHERE up.user_id = ? AND t.subject_id IS NOT NULL",
        user_id,
    )
    issued = []
    for row in rows:
        result = issue_for_subject(user_id, row["subject_id"])
        if result:
            issued.append(result)
    return issued


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _meta(numbers: dict[str, int], subject_name: str) -> str:
    import json

    return json.dumps({
        "subject": subject_name,
        "issuer": issuer_name(),
        "evidence": numbers,
        # Stated on the certificate itself, not only in the footer, so the
        # record cannot be cropped into something it is not.
        "disclaimer": "Platform completion record. Not a university, government or professional accreditation.",
    }, ensure_ascii=False)


def _new_verify_id() -> str:
    """A verify id that is public but not guessable."""
    import secrets

    return f"EV-{now_ms():X}-{secrets.token_hex(4).upper()}"


def _verify_url(cert_id: str) -> str:
    row = db.query_one("SELECT verify_id FROM certificates WHERE id = ?", cert_id)
    return f"/certificates/{row['verify_id']}" if row else "/certificates"
