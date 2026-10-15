"""Tests for GitHub learner vault storage, Android APK builder, and full public-site access."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from engineverse import github_storage
from scripts import build_android_apk, export_pages, sync_learner_data

ROOT = Path(__file__).resolve().parents[2]
APK = "https://github.com/authorsauravkushwaha/EngineVerse/releases/download/android-v1.0.0/EngineVerse.apk"


def test_github_storage_normalizes_and_merges_monotonically(tmp_path):
    reg_path = tmp_path / "registry.json"
    digest = github_storage.hash_password_digest("aarav_sharma", "StrongPass#2026")
    assert github_storage.verify_password_digest("aarav_sharma", "StrongPass#2026", digest)
    assert not github_storage.verify_password_digest("aarav_sharma", "WrongPass#2026", digest)

    snap1 = {
        "username": "Aarav_Sharma",
        "display_name": "Aarav Sharma",
        "branch": "cse",
        "year_of_study": 2,
        "xp": 150,
        "level": 2,
        "streak_days": 3,
        "longest_streak": 4,
        "activity_days": ["2026-10-14"],
        "completed_topics": ["ohms-law-and-kirchhoff"],
        "solved_problems": ["two-sum"],
        "quiz_attempts": 4,
        "quiz_correct": 3,
        "password_sha256": digest,
    }
    res1 = github_storage.save_snapshot_to_registry(snap1, path=reg_path)
    assert res1["username"] == "aarav_sharma"
    assert res1["display_name"] == "Aarav Sharma"

    snap2 = {
        "username": "aarav_sharma",
        "display_name": "Aarav S.",
        "xp": 320,
        "streak_days": 5,
        "activity_days": ["2026-10-15"],
        "completed_topics": ["time-complexity-and-asymptotics"],
        "solved_problems": ["valid-parentheses"],
        "quiz_attempts": 8,
        "quiz_correct": 7,
    }
    merged = github_storage.save_snapshot_to_registry(snap2, path=reg_path)
    assert merged["xp"] == 320
    assert merged["longest_streak"] == 5
    assert set(merged["completed_topics"]) == {"ohms-law-and-kirchhoff", "time-complexity-and-asymptotics"}
    assert set(merged["solved_problems"]) == {"two-sum", "valid-parentheses"}
    assert set(merged["activity_days"]) == {"2026-10-14", "2026-10-15"}
    assert merged["password_digest"] == digest


def test_github_storage_rejects_sensitive_keys():
    with pytest.raises(github_storage.StorageValidationError):
        github_storage.normalize_learner_snapshot({
            "username": "valid_user",
            "password": "plaintext-password-never-allowed",
        })


def test_sync_learner_data_script_extracts_issue_payload():
    sync_learner_data.self_check()
    issue = (
        "Automated sync\n"
        "```engineverse-learner-snapshot\n"
        '{"username": "priya_ec", "display_name": "Priya", "xp": 210}\n'
        "```\n"
    )
    extracted = sync_learner_data.extract_snapshot(issue)
    norm = github_storage.normalize_learner_snapshot(extracted)
    assert norm["username"] == "priya_ec"
    assert norm["xp"] == 210


def test_android_apk_builder_self_check_and_manifest():
    build_android_apk.self_check()
    cfg = build_android_apk.validate_config("https://authorsauravkushwaha.github.io/EngineVerse/")
    text = build_android_apk.generate_manifest(cfg)
    assert "io.github.authorsauravkushwaha.engineverse" in text
    assert "android.permission.INTERNET" in text


def test_public_pages_support_accounts_code_runner_and_apk_download():
    rewritten = export_pages.rewrite_html(
        '<a href="/login">Sign in</a><a href="/register">Register</a>'
        '<a href="/settings">GitHub Sync</a><a href="/dashboard">Dashboard</a>',
        "/EngineVerse/",
    )
    assert 'href="/EngineVerse/login/"' in rewritten
    assert 'href="/EngineVerse/register/"' in rewritten
    assert 'href="/EngineVerse/settings/"' in rewritten
    assert 'href="/EngineVerse/dashboard/"' in rewritten

    install_with_apk = export_pages.reading_copy_install_main("", APK)
    assert f'href="{APK}"' in install_with_apk
    assert "Download signed EngineVerse.apk" in install_with_apk

    hosting_with_apk = export_pages.hosting_main("", APK)
    assert f'href="{APK}"' in hosting_with_apk

    problem_html = (
        '<select id="lang-select">'
        '<option value="python">Python</option>'
        '<option value="cpp" disabled>C++ (starter only)</option>'
        '</select>'
        '<button class="btn btn-ghost" id="btn-run" type="button">Run</button>'
    )
    enabled = export_pages.enable_problem_editor(problem_html)
    assert "disabled" not in enabled
    assert "(starter only)" not in enabled
    assert 'id="btn-submit"' in enabled

    boot = export_pages.live_boot("/EngineVerse/", ["2026-10-15"], apk_url=APK)
    payload = json.loads(boot.split(">", 1)[1].rsplit("<", 1)[0])
    assert payload["vault"] == "/EngineVerse/learner-vault.json"
    assert payload["quizBank"] == "/EngineVerse/quiz-bank.json"
    assert payload["codingProblems"] == "/EngineVerse/coding-problems.json"
    assert payload["studioSnapshot"] == "/EngineVerse/studio-snapshot.json"
    assert payload["workflowsCatalog"] == "/EngineVerse/workflows-catalog.json"
    assert payload["swarmCorpus"] == "/EngineVerse/swarm-corpus.json"
    assert payload["githubRepo"] == "authorsauravkushwaha/EngineVerse"
    assert payload["apkUrl"] == APK


def test_sync_api_endpoints(client):
    status_res = client.get("/api/sync/status")
    assert status_res.status_code == 200
    body = status_res.json()
    assert body["ok"] is True
    assert body["repository"] == "authorsauravkushwaha/EngineVerse"

    get_snap = client.get("/api/sync/snapshot?username=saurav")
    assert get_snap.status_code == 200
    assert get_snap.json()["ok"] is True
    assert get_snap.json()["snapshot"]["username"] == "saurav"
