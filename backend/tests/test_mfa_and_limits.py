"""Authenticator, shared API limits, and the trusted-proxy flag.

These checks are about this process. A green run is not a deployment, a
backup, or a statement that a second factor is enrolled for any real account.
"""
from __future__ import annotations

import os
import re
import sqlite3
import subprocess
import sys
import time
from pathlib import Path

import pytest

from engineverse import auth, db
from engineverse.config import reload_settings
from engineverse.security import ratelimit, totp
from engineverse.security.clientip import client_ip

REPO_ROOT = Path(__file__).resolve().parents[2]
PASSWORD = "Mfa-Throwaway-Pass-9"
RFC_SECRET = "GEZDGNBVGY3TQOJQGEZDGNBVGY3TQOJQ"


def _csrf(html: str) -> str:
    marker = 'name="csrf_token" value="'
    start = html.index(marker) + len(marker)
    return html[start:html.index('"', start)]


def _field(html: str, name: str) -> str:
    match = re.search(rf'name="{name}" value="([^"]*)"', html)
    assert match, name
    return match.group(1)


class _Peer:
    def __init__(self, host: str, headers: dict | None = None) -> None:
        self.client = type("Client", (), {"host": host})()
        self.headers = headers or {}


def _register(tag: str) -> dict:
    return auth.register(
        email=f"{tag}@example.test",
        username=tag[:24],
        password=PASSWORD,
        full_name="MFA Throwaway",
        ip="203.0.113.10",
        user_agent="pytest",
    )


def _sessions(user_id: str) -> int:
    return int(db.scalar("SELECT count(*) AS c FROM sessions WHERE user_id = ?", user_id) or 0)


def test_rfc_sha1_vectors():
    assert totp.code_at(RFC_SECRET, 0) == "755224"
    assert totp.code_at(RFC_SECRET, 1) == "287082"
    assert totp.verify_totp(RFC_SECRET, "287082", now=30)
    assert totp.verify_totp(RFC_SECRET, "287 082", now=30)
    assert not totp.verify_totp(RFC_SECRET, "000000", now=30)


def test_seal_round_trip_and_a_bad_mac_does_not_open():
    stored = totp.pack(RFC_SECRET, ["abc123def0"])
    assert totp.unseal(stored)["secret"] == RFC_SECRET
    assert totp.unseal("v1:not-a-seal") is None
    assert totp.verify_factor("v1:not-a-seal", "287082") == (False, None)


def test_a_recovery_code_works_once():
    code = "abc123def0"
    stored = totp.pack(RFC_SECRET, [code, "bbbbbbbbbb"])
    accepted, replacement = totp.verify_factor(stored, code)
    assert accepted and replacement
    assert totp.verify_factor(replacement, code) == (False, None)
    again, untouched = totp.verify_factor(replacement, totp.code_at(RFC_SECRET, int(time.time()) // 30))
    assert again and untouched is None


def test_password_match_creates_no_session_until_the_factor_passes(seeded):
    user = _register("mfaunit" + totp.random_secret()[:6].lower())
    codes = ["abc123def0", "bbbbbbbbbb"]
    db.execute("UPDATE users SET totp_secret = ? WHERE id = ?", totp.pack(RFC_SECRET, codes), user["id"])
    before = _sessions(user["id"])
    with pytest.raises(auth.MfaRequired) as caught:
        auth.login(identifier=user["email"], password=PASSWORD, ip="203.0.113.8")
    assert not isinstance(caught.value, auth.AuthError)
    assert PASSWORD not in caught.value.token
    assert _sessions(user["id"]) == before

    with pytest.raises(auth.AuthError):
        auth.login(identifier=user["email"], password="", ip="203.0.113.8", otp="000000", mfa_token=caught.value.token)
    assert _sessions(user["id"]) == before
    assert int(db.scalar("SELECT failed_login_count AS c FROM users WHERE id = ?", user["id"]) or 0) == 1

    logged_in, cookie, session_id = auth.login(
        identifier=user["email"],
        password="",
        ip="203.0.113.8",
        otp=totp.code_at(RFC_SECRET, int(time.time()) // 30),
        mfa_token=caught.value.token,
    )
    assert logged_in["id"] == user["id"]
    assert cookie and session_id
    assert _sessions(user["id"]) == before + 1
    db.execute("UPDATE users SET totp_secret = NULL WHERE id = ?", user["id"])


def test_an_unreadable_seal_does_not_create_a_session(seeded):
    user = _register("mfaseal" + totp.random_secret()[:6].lower())
    db.execute("UPDATE users SET totp_secret = ? WHERE id = ?", "v1:not-a-seal", user["id"])
    with pytest.raises(auth.MfaRequired) as caught:
        auth.login(identifier=user["email"], password=PASSWORD, ip="203.0.113.8")
    with pytest.raises(auth.AuthError):
        auth.login(
            identifier=user["email"], password="", ip="203.0.113.8",
            otp="123456", mfa_token=caught.value.token,
        )
    assert _sessions(user["id"]) == 0
    db.execute("UPDATE users SET totp_secret = NULL WHERE id = ?", user["id"])


def test_login_form_does_not_echo_the_password_into_the_second_step(client, seeded):
    tag = "mfaform" + totp.random_secret()[:6].lower()
    user = _register(tag)
    secret = totp.random_secret()
    codes = totp.recovery_codes()
    db.execute("UPDATE users SET totp_secret = ? WHERE id = ?", totp.pack(secret, codes), user["id"])
    try:
        page = client.get("/login")
        challenge = client.post(
            "/login",
            data={"csrf_token": _csrf(page.text), "identifier": user["email"], "password": PASSWORD},
            follow_redirects=False,
        )
        assert challenge.status_code == 401
        assert "ev_session" not in challenge.headers.get("set-cookie", "")
        assert "ev_session" not in client.cookies
        assert PASSWORD not in challenge.text
        assert 'name="password"' not in challenge.text
        assert "mfa_token" in challenge.text

        wrong = client.post(
            "/login",
            data={
                "csrf_token": _csrf(challenge.text),
                "identifier": user["email"],
                "mfa_token": _field(challenge.text, "mfa_token"),
                "otp": "000000",
            },
            follow_redirects=False,
        )
        assert wrong.status_code == 401
        assert "ev_session" not in client.cookies

        done = client.post(
            "/login",
            data={
                "csrf_token": _csrf(wrong.text),
                "identifier": user["email"],
                "mfa_token": _field(wrong.text, "mfa_token"),
                "otp": codes[0],
            },
            follow_redirects=False,
        )
        assert done.status_code == 303
        assert "ev_session" in client.cookies
        client.post("/logout", data={"csrf_token": _csrf(client.get("/settings").text)}, follow_redirects=False)
        reused = client.post(
            "/login",
            data={"csrf_token": _csrf(client.get("/login").text), "identifier": user["email"], "password": PASSWORD},
            follow_redirects=False,
        )
        refused = client.post(
            "/login",
            data={
                "csrf_token": _csrf(reused.text),
                "mfa_token": _field(reused.text, "mfa_token"),
                "otp": codes[0],
            },
            follow_redirects=False,
        )
        assert refused.status_code == 401
        assert "ev_session" not in client.cookies
    finally:
        db.execute("UPDATE users SET totp_secret = NULL WHERE id = ?", user["id"])


def test_settings_enrol_confirm_and_disable_round_trip(client, seeded):
    tag = "mfaweb" + totp.random_secret()[:6].lower()
    user = _register(tag)
    page = client.get("/login")
    assert client.post(
        "/login",
        data={"csrf_token": _csrf(page.text), "identifier": user["email"], "password": PASSWORD},
        follow_redirects=False,
    ).status_code == 303
    try:
        settings = client.get("/settings")
        started = client.post(
            "/settings/mfa/start",
            data={"csrf_token": _csrf(settings.text), "current_password": PASSWORD},
            follow_redirects=False,
        )
        assert started.status_code == 200
        secret = re.search(r'id="mfa-secret">([^<]+)', started.text).group(1)
        confirmed = client.post(
            "/settings/mfa/confirm",
            data={
                "csrf_token": _csrf(started.text),
                "token": _field(started.text, "token"),
                "otp": totp.code_at(secret, int(time.time()) // 30),
            },
            follow_redirects=False,
        )
        assert confirmed.status_code == 200
        codes = re.findall(r'class="recovery-code">([^<]+)', confirmed.text)
        assert len(codes) == 8
        assert db.query_one("SELECT totp_secret FROM users WHERE id = ?", user["id"])["totp_secret"]
        bad = client.post(
            "/settings/mfa/confirm",
            data={"csrf_token": _csrf(confirmed.text), "token": "not-a-token", "otp": "000000"},
            follow_redirects=False,
        )
        assert bad.status_code == 303
        disabled = client.post(
            "/settings/mfa/disable",
            data={
                "csrf_token": _csrf(client.get("/settings").text),
                "current_password": PASSWORD,
                "otp": totp.code_at(secret, int(time.time()) // 30),
            },
            follow_redirects=False,
        )
        assert disabled.status_code == 303
        assert db.query_one("SELECT totp_secret FROM users WHERE id = ?", user["id"])["totp_secret"] is None
    finally:
        db.execute("UPDATE users SET totp_secret = NULL WHERE id = ?", user["id"])


def test_client_ip_ignores_forwarded_headers_unless_the_peer_is_the_proxy(monkeypatch):
    monkeypatch.delenv("ENGINEVERSE_TRUST_PROXY", raising=False)
    reload_settings()
    try:
        forwarded = {"x-forwarded-for": "203.0.113.9, 10.0.0.2"}
        assert client_ip(_Peer("127.0.0.1", forwarded)) == "127.0.0.1"
        monkeypatch.setenv("ENGINEVERSE_TRUST_PROXY", "yes")
        reload_settings()
        assert client_ip(_Peer("127.0.0.1", forwarded)) == "203.0.113.9"
        assert client_ip(_Peer("10.1.2.3", forwarded)) == "203.0.113.9"
        assert client_ip(_Peer("8.8.8.8", forwarded)) == "8.8.8.8"
        assert client_ip(_Peer("testclient", forwarded)) == "testclient"
        assert client_ip(_Peer("127.0.0.1", {"x-forwarded-for": "not-an-ip"})) == "127.0.0.1"
    finally:
        monkeypatch.undo()
        reload_settings()


def test_shared_counter_survives_an_empty_process_window(client):
    for _ in range(300):
        assert ratelimit.shared_check("api:testclient", 300, 60).allowed
    with ratelimit._lock:
        ratelimit._buckets.clear()
    blocked = client.get("/api/search", params={"q": "ohm"})
    assert blocked.status_code == 429


def test_shared_check_falls_back_or_raises(monkeypatch):
    def missing(*_args, **_kwargs):
        raise RuntimeError("no such table: api_rate_limits")

    monkeypatch.setattr(ratelimit.db, "execute", missing)
    assert ratelimit.shared_check("missing-table", 5, 60).allowed

    def disk(*_args, **_kwargs):
        raise db.DatabaseError("disk")

    monkeypatch.setattr(ratelimit.db, "execute", disk)
    assert ratelimit.shared_check("disk-full", 5, 60).allowed

    def malformed(*_args, **_kwargs):
        raise RuntimeError("syntax error near SELECT")

    monkeypatch.setattr(ratelimit.db, "execute", malformed)
    with pytest.raises(RuntimeError):
        ratelimit.shared_check("malformed", 5, 60)


def test_production_staff_posts_wait_for_an_authenticator(client, seeded, monkeypatch):
    tag = "mfagate" + totp.random_secret()[:6].lower()
    user = _register(tag)
    db.execute("UPDATE users SET role = 'super_admin' WHERE id = ?", user["id"])
    try:
        assert client.post(
            "/login",
            data={"csrf_token": _csrf(client.get("/login").text), "identifier": user["email"], "password": PASSWORD},
            follow_redirects=False,
        ).status_code == 303
        monkeypatch.setenv("ENGINEVERSE_ENV", "production")
        reload_settings()
        assert client.get("/admin").status_code == 200
        token = _csrf(client.get("/admin").text)
        blocked = client.post(
            "/admin/users/status",
            data={"csrf_token": token, "user_id": user["id"], "status": "active"},
            follow_redirects=False,
        )
        assert blocked.status_code == 303
        assert blocked.headers["location"].endswith("/settings")

        started = client.post(
            "/settings/mfa/start",
            data={"csrf_token": _csrf(client.get("/settings").text), "current_password": PASSWORD},
        )
        secret = re.search(r'id="mfa-secret">([^<]+)', started.text).group(1)
        client.post(
            "/settings/mfa/confirm",
            data={
                "csrf_token": _csrf(started.text),
                "token": _field(started.text, "token"),
                "otp": totp.code_at(secret, int(time.time()) // 30),
            },
        )
        allowed = client.post(
            "/admin/users/status",
            data={"csrf_token": _csrf(client.get("/admin").text), "user_id": user["id"], "status": "active"},
            follow_redirects=False,
        )
        assert allowed.status_code == 303
        assert allowed.headers["location"].endswith("/admin")
    finally:
        db.execute("UPDATE users SET totp_secret = NULL, role = 'student' WHERE id = ?", user["id"])
        monkeypatch.undo()
        reload_settings()


def test_a_student_admin_post_is_not_turned_into_a_settings_redirect(signed_in, monkeypatch):
    monkeypatch.setenv("ENGINEVERSE_ENV", "production")
    reload_settings()
    try:
        token = _csrf(signed_in.get("/settings").text)
        response = signed_in.post(
            "/admin/users/role",
            data={"csrf_token": token, "user_id": "x", "role": "super_admin"},
            follow_redirects=False,
        )
        assert response.status_code == 403
        assert response.headers.get("location") is None
    finally:
        monkeypatch.undo()
        reload_settings()


def test_replace_clears_the_admin_authenticator_without_printing_it(tmp_path):
    path = tmp_path / "admin.sqlite"
    password = "A-long-admin-passphrase-9"
    seal = "SEAL-SHOULD-NOT-APPEAR"
    env = os.environ.copy()
    env.pop("ENGINEVERSE_DB_URL", None)
    env.update({
        "ENGINEVERSE_ENV": "development",
        "ENGINEVERSE_DB_PATH": str(path),
        "ENGINEVERSE_SECRET": "production-test-secret-value-0123456789abcdef",
        "ENGINEVERSE_ADMIN_PASSWORD": password,
    })
    created = subprocess.run(
        [sys.executable, "scripts/create_admin.py", "--email", "ops@example.test", "--username", "ops", "--full-name", "Ops"],
        cwd=REPO_ROOT, env=env, capture_output=True, text=True,
    )
    assert created.returncode == 0, created.stderr
    with sqlite3.connect(path) as conn:
        conn.execute("UPDATE users SET totp_secret = ? WHERE username = 'ops'", (seal,))
    env["ENGINEVERSE_ALLOW_ADMIN_REPLACE"] = "yes"
    replaced = subprocess.run(
        [sys.executable, "scripts/create_admin.py", "--replace", "--email", "ops@example.test", "--username", "ops"],
        cwd=REPO_ROOT, env=env, capture_output=True, text=True,
    )
    combined = replaced.stdout + replaced.stderr
    assert replaced.returncode == 0, combined
    assert "Authenticator enrollment was cleared" in replaced.stdout
    assert password not in combined
    assert seal not in combined
    with sqlite3.connect(path) as conn:
        assert conn.execute("SELECT totp_secret FROM users WHERE username = 'ops'").fetchone()[0] is None
