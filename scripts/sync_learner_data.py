#!/usr/bin/env python3
"""Validate and merge a learner progress snapshot into data/learners/registry.json.

Used by `.github/workflows/learner-data-sync.yml` when a learner on the public
GitHub Pages site or the Android APK saves their progress to the owner's GitHub
repository (`authorsauravkushwaha/EngineVerse`).
"""
from __future__ import annotations

import argparse
import json
import re
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BACKEND = ROOT / "backend"
if str(BACKEND) not in sys.path:
    sys.path.insert(0, str(BACKEND))

from engineverse import github_storage  # noqa: E402

_JSON_BLOCK = re.compile(r"```(?:json|engineverse-learner-snapshot)?\s*(\{.*?\})\s*```", re.S)


def extract_snapshot(raw: str) -> dict:
    """Extract a JSON object from either raw JSON or a markdown fenced block."""
    text = (raw or "").strip()
    if not text:
        raise github_storage.LearnerSyncError("Empty learner sync payload.")
    match = _JSON_BLOCK.search(text)
    candidate = match.group(1) if match else text
    try:
        parsed = json.loads(candidate)
    except json.JSONDecodeError as exc:
        raise github_storage.LearnerSyncError("Invalid JSON in learner sync payload.") from exc
    if not isinstance(parsed, dict):
        raise github_storage.LearnerSyncError("Learner sync payload must be a JSON object.")
    if isinstance(parsed.get("snapshot"), dict):
        parsed = parsed["snapshot"]
    return parsed


def self_check() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        reg_path = Path(tmp) / "registry.json"
        digest = github_storage.hash_password_digest("saurav", "Engineer#2026!")
        first = github_storage.save_snapshot_to_registry(
            {
                "username": "Saurav",
                "full_name": "Saurav Kushwaha",
                "password_digest": digest,
                "xp": 120,
                "streak": 3,
                "completed_topics": ["arrays", "ohms-law"],
                "solved_problems": ["two-sum"],
                "days": {"2026-10-15": 2},
            },
            path=reg_path,
        )
        assert first["username"] == "saurav"
        assert first["xp"] == 120
        assert first["completed_topics"] == ["arrays", "ohms-law"]

        # Monotonic merge keeps previous topics and increases XP
        second = github_storage.save_snapshot_to_registry(
            {
                "username": "saurav",
                "password_digest": digest,
                "xp": 260,
                "streak": 4,
                "completed_topics": ["bernoullis-equation"],
                "solved_problems": ["valid-parentheses"],
                "days": {"2026-10-16": 1},
            },
            path=reg_path,
        )
        assert second["completed_topics"] == ["arrays", "bernoullis-equation", "ohms-law"]
        assert second["solved_problems"] == ["two-sum", "valid-parentheses"]
        assert second["xp"] == 260
        assert second["level"] == 2

        # Wrong password digest is rejected
        try:
            github_storage.save_snapshot_to_registry(
                {
                    "username": "saurav",
                    "password_digest": github_storage.hash_password_digest("saurav", "WrongPass#123"),
                    "xp": 999,
                },
                path=reg_path,
            )
        except github_storage.LearnerSyncError:
            pass
        else:
            raise AssertionError("Accepted mismatched password digest")

        # Raw password is rejected
        try:
            github_storage.validate_snapshot({"username": "saurav", "password": "secret"})
        except github_storage.LearnerSyncError:
            pass
        else:
            raise AssertionError("Accepted raw password in snapshot")

        # Markdown fenced extraction works
        extracted = extract_snapshot("Sync request:\n```json\n{\"username\": \"learner1\", \"xp\": 50}\n```")
        assert extracted["username"] == "learner1"
    print("Learner GitHub storage self-check ok")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--payload", default="", help="Raw JSON or markdown issue body containing snapshot")
    parser.add_argument("--file", default="", help="Path to file containing payload")
    parser.add_argument("--registry", default=str(github_storage.DEFAULT_REGISTRY_PATH))
    parser.add_argument("--self-check", action="store_true")
    args = parser.parse_args()

    if args.self_check:
        self_check()
        return 0

    raw = args.payload
    if args.file:
        raw = Path(args.file).read_text(encoding="utf-8")
    try:
        snapshot = extract_snapshot(raw)
        merged = github_storage.save_snapshot_to_registry(snapshot, path=Path(args.registry))
    except github_storage.LearnerSyncError as exc:
        print(f"Refusing learner sync payload: {exc}", file=sys.stderr)
        return 1

    print(
        f"Saved learner @{merged['username']} ({merged['xp']} XP, "
        f"{len(merged['completed_topics'])} topics, {len(merged['solved_problems'])} problems) "
        f"to {args.registry}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
