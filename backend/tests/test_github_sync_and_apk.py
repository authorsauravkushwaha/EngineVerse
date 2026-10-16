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


def _csrf(html: str) -> str:
    marker = 'name="csrf_token" value="'
    start = html.index(marker) + len(marker)
    return html[start : html.index('"', start)]


def _field(html: str, name: str) -> str:
    import re
    match = re.search(rf'name="{re.escape(name)}" value="([^"]*)"', html)
    assert match, f"missing field {name}"
    return match.group(1)


def test_country_code_phone_normalization_and_validation():
    from engineverse.security.validators import COUNTRY_CODES, normalize_phone_with_country_code

    assert any(code == "+91" for code, _ in COUNTRY_CODES)
    assert any(code == "+1" for code, _ in COUNTRY_CODES)
    assert any(code == "+44" for code, _ in COUNTRY_CODES)
    assert normalize_phone_with_country_code("9876543210", "+91") == "+919876543210"
    assert normalize_phone_with_country_code("09876543210", "+91") == "+919876543210"
    assert normalize_phone_with_country_code("+447911123456", "+91") == "+447911123456"
    assert normalize_phone_with_country_code("415-555-2671", "+1") == "+14155552671"


def test_scoped_otp_signup_only_mode_verifies_new_user_and_skips_otp_on_returning_login(client, seeded, monkeypatch):
    import os
    from engineverse import notify
    from engineverse.config import reload_settings

    monkeypatch.setenv("ENGINEVERSE_LOGIN_OTP", "signup_only")
    monkeypatch.setenv("ENGINEVERSE_SMS_URL", "https://sms.example/send")
    reload_settings()
    try:
        sent_codes: list[str] = []
        monkeypatch.setattr(
            notify,
            "send_phone_otp",
            lambda to, code, minutes=10: sent_codes.append(code) or True,
        )
        monkeypatch.setattr(
            notify,
            "send_login_otp",
            lambda to, code, minutes=10: sent_codes.append(code) or True,
        )

        tag = f"newotp{os.urandom(3).hex()}"
        reg_page = client.get("/register")
        assert 'name="country_code"' in reg_page.text
        assert 'name="otp_channel"' in reg_page.text

        # 1. New user registers with mobile number + country code (+91) and requests SMS OTP
        reg_res = client.post(
            "/register",
            data={
                "csrf_token": _csrf(reg_page.text),
                "full_name": "New Verified Learner",
                "username": tag,
                "email": f"{tag}@gmail.com",
                "country_code": "+91",
                "phone": "9876543210",
                "otp_channel": "phone",
                "password": "StrongOtpPassword#2026",
                "password_confirm": "StrongOtpPassword#2026",
                "branch": "cse",
                "semester": "1",
                "next": "/dashboard",
            },
            follow_redirects=False,
        )
        assert reg_res.status_code == 401
        assert sent_codes, "Expected 6-digit OTP to be sent for new user signup"
        otp_code = sent_codes[-1]
        assert len(otp_code) == 6 and otp_code.isdigit()
        assert "ev_session" not in reg_res.headers.get("set-cookie", "")

        # 2. Complete the 6-digit OTP verification on /login
        token = _field(reg_res.text, "otp_token")
        verify_res = client.post(
            "/login",
            data={
                "csrf_token": _csrf(reg_res.text),
                "identifier": f"{tag}@gmail.com",
                "mfa_token": token,
                "otp": otp_code,
                "next": "/dashboard",
                "remember": "1",
            },
            follow_redirects=False,
        )
        assert verify_res.status_code == 303
        assert verify_res.headers["location"] == "/dashboard"

        # 3. Sign out, then log back in as a returning verified user:
        # must sign in directly with password WITHOUT requiring another OTP!
        dash = client.get("/dashboard")
        client.post("/logout", data={"csrf_token": _csrf(dash.text)}, follow_redirects=False)

        sent_codes.clear()
        login_page = client.get("/login")
        login_res = client.post(
            "/login",
            data={
                "csrf_token": _csrf(login_page.text),
                "identifier": f"{tag}@gmail.com",
                "password": "StrongOtpPassword#2026",
                "next": "/dashboard",
            },
            follow_redirects=False,
        )
        assert login_res.status_code == 303
        assert login_res.headers["location"] == "/dashboard"
        assert sent_codes == [], "Returning verified user must NOT be challenged for OTP on normal login"
    finally:
        os.environ["ENGINEVERSE_LOGIN_OTP"] = "disabled"
        os.environ.pop("ENGINEVERSE_SMS_URL", None)
        reload_settings()


def test_forgot_and_reset_password_via_6_digit_otp_email_and_phone(client, seeded, monkeypatch):
    import os
    from engineverse import auth, notify

    sent: dict[str, str] = {}
    monkeypatch.setattr(
        notify,
        "send_phone_otp",
        lambda to, code, minutes=10: sent.update(to=to, code=code, channel="phone") or True,
    )
    monkeypatch.setattr(
        notify,
        "send_login_otp",
        lambda to, code, minutes=10: sent.update(to=to, code=code, channel="email") or True,
    )

    tag = f"resetotp{os.urandom(3).hex()}"
    user = auth.register(
        email=f"{tag}@gmail.com",
        username=tag,
        password="InitialPassword#2026",
        full_name="Reset Learner",
        phone="9876543211",
        country_code="+91",
    )
    assert user["phone"] == "+919876543211"

    # Request 6-digit password reset OTP via mobile number with country code
    forgot_page = client.get("/forgot-password")
    assert 'name="country_code"' in forgot_page.text
    forgot_res = client.post(
        "/forgot-password",
        data={
            "csrf_token": _csrf(forgot_page.text),
            "email": "",
            "otp_channel": "phone",
            "country_code": "+91",
            "phone": "9876543211",
        },
        follow_redirects=False,
    )
    assert forgot_res.status_code == 200
    assert sent.get("code") and len(sent["code"]) == 6
    assert 'name="otp_code"' in forgot_res.text

    # Submit the 6-digit OTP + new password to /reset-password
    reset_res = client.post(
        "/reset-password",
        data={
            "csrf_token": _csrf(forgot_res.text),
            "otp_token": _field(forgot_res.text, "otp_token"),
            "otp_code": sent["code"],
            "password": "UpdatedViaOtpPassword#2026",
            "confirm_password": "UpdatedViaOtpPassword#2026",
        },
        follow_redirects=False,
    )
    assert reset_res.status_code == 303
    assert reset_res.headers["location"] == "/login?error=reset"

    # Log in directly with the new password
    login_page = client.get("/login")
    login_res = client.post(
        "/login",
        data={
            "csrf_token": _csrf(login_page.text),
            "identifier": f"{tag}@gmail.com",
            "password": "UpdatedViaOtpPassword#2026",
            "next": "/dashboard",
        },
        follow_redirects=False,
    )
    assert login_res.status_code == 303


def test_change_password_via_6_digit_otp_in_settings(client, seeded, monkeypatch):
    import os
    from engineverse import auth, notify

    sent: dict[str, str] = {}
    monkeypatch.setattr(
        notify,
        "send_login_otp",
        lambda to, code, minutes=10: sent.update(to=to, code=code, channel="email") or True,
    )

    tag = f"chgpwd{os.urandom(3).hex()}"
    auth.register(
        email=f"{tag}@gmail.com",
        username=tag,
        password="BeforeChange#2026",
        full_name="Settings OTP Learner",
        phone="9876543212",
        country_code="+91",
    )

    login_page = client.get("/login")
    login_res = client.post(
        "/login",
        data={
            "csrf_token": _csrf(login_page.text),
            "identifier": tag,
            "password": "BeforeChange#2026",
        },
        follow_redirects=False,
    )
    assert login_res.status_code == 303

    settings_page = client.get("/settings")
    assert settings_page.status_code == 200
    assert "/settings/password/otp" in settings_page.text
    assert 'name="country_code"' in settings_page.text

    # 1. Request 6-digit OTP to change password via Gmail
    otp_req = client.post(
        "/settings/password/otp",
        data={
            "csrf_token": _csrf(settings_page.text),
            "channel": "email",
            "country_code": "+91",
            "phone": "9876543212",
        },
        follow_redirects=False,
    )
    assert otp_req.status_code == 200
    assert sent.get("code") and len(sent["code"]) == 6

    # 2. Verify 6-digit OTP and set new password
    chg_res = client.post(
        "/settings/password",
        data={
            "csrf_token": _csrf(otp_req.text),
            "otp_token": _field(otp_req.text, "otp_token"),
            "otp_code": sent["code"],
            "new_password": "AfterOtpChange#2026",
            "confirm_password": "AfterOtpChange#2026",
        },
        follow_redirects=False,
    )
    assert chg_res.status_code == 303
    assert chg_res.headers["location"] == "/settings"


def test_topbar_account_icon_and_cross_tab_session_persistence(signed_in):
    # Check server-rendered tabs when signed in: topbar shows avatar account icon, not Sign in / Start free,
    # and switching tabs never renders anonymous "Sign in to..." prompts.
    for tab_path in ("/", "/explore", "/revision", "/sheets", "/dpp", "/community", "/settings"):
        res = signed_in.get(tab_path)
        assert res.status_code == 200, tab_path
        assert 'class="avatar"' in res.text, f"Missing account avatar icon on {tab_path}"
        assert 'class="whoami"' in res.text, f"Missing account menu on {tab_path}"
        assert 'data-ev-anon-auth' not in res.text, f"Anonymous Sign in / Start free still rendered on {tab_path}"
        assert "Sign in to start revising" not in res.text, f"Anonymous revision prompt rendered on {tab_path}"
        assert "Sign in to have your progress on this sheet tracked" not in res.text

    # Check static/exported JS runtime for .topbar-right account icon replacement & multi-layer DB sync
    pages_live_js = (ROOT / "backend" / "static" / "js" / "pages-live.js").read_text(encoding="utf-8")
    assert 'document.querySelector(".topbar-right")' in pages_live_js
    assert "data-live-account-menu" in pages_live_js
    assert "data-live-avatar" in pages_live_js
    assert "hydrateSignedInPageContent" in pages_live_js
    assert "EngineVerseVaultDB" in pages_live_js
    assert "BroadcastChannel" in pages_live_js

