"""Email confirmation, authenticator recovery, and backup tooling.

A green run is not a mail delivery, a production dump, or a Play listing.
"""
from __future__ import annotations

import os
import sqlite3
import subprocess
import sys
from pathlib import Path

import pytest

from engineverse import auth, db
from engineverse.config import reload_settings
from engineverse.security.passwords import COMMON_PASSWORDS

REPO_ROOT = Path(__file__).resolve().parents[2]
PASSWORD = "Verify-Throwaway-Pass-9"


def _csrf(html: str) -> str:
    marker = 'name="csrf_token" value="'
    start = html.index(marker) + len(marker)
    return html[start:html.index('"', start)]


def _register(tag: str) -> dict:
    return auth.register(
        email=f"{tag}@example.test",
        username=tag[:24],
        password=PASSWORD,
        full_name="Verify Throwaway",
        ip="203.0.113.10",
        user_agent="pytest",
    )


def test_the_local_blocklist_is_more_than_a_handful():
    assert len(COMMON_PASSWORDS) >= 300
    assert "password" in COMMON_PASSWORDS
    assert "trustno1" in COMMON_PASSWORDS
    assert "str0ngpassphrase#42!" not in COMMON_PASSWORDS


def test_confirmation_token_is_hashed_and_a_wildcard_does_not_match(seeded):
    user = _register("verify" + os.urandom(3).hex())
    token = auth.issue_email_verification(user["id"], ip="203.0.113.9")
    rows = db.query("SELECT token_hash FROM email_verifications WHERE user_id = ?", user["id"])
    assert rows and rows[0]["token_hash"] != token
    assert token not in rows[0]["token_hash"]
    assert auth.consume_email_verification("%") is None
    assert int(db.query_one("SELECT email_verified FROM users WHERE id = ?", user["id"])["email_verified"]) == 0
    assert auth.consume_email_verification(token) == user["id"]
    assert int(db.query_one("SELECT email_verified FROM users WHERE id = ?", user["id"])["email_verified"]) == 1
    assert auth.consume_email_verification(token) is None


def test_a_failed_send_does_not_leave_a_live_token(seeded, monkeypatch):
    user = _register("verfail" + os.urandom(3).hex())
    monkeypatch.setenv("ENGINEVERSE_SMTP_URL", "smtp://mail.internal:587")
    reload_settings()
    try:
        monkeypatch.setattr("engineverse.notify.send_email_verification", lambda **_kwargs: False)
        status, shown = auth.deliver_email_verification(user["id"], user["email"], ip="203.0.113.9")
        assert status == "unavailable"
        assert shown == ""
        assert db.query("SELECT token_hash FROM email_verifications WHERE user_id = ?", user["id"]) == []
        assert int(db.query_one("SELECT email_verified FROM users WHERE id = ?", user["id"])["email_verified"]) == 0
    finally:
        monkeypatch.undo()
        reload_settings()


def test_confirmation_link_is_not_rendered_unless_development_reveal_is_on(client, seeded, monkeypatch):
    user = _register("verpage" + os.urandom(3).hex())
    monkeypatch.delenv("ENGINEVERSE_SMTP_URL", raising=False)
    monkeypatch.delenv("ENGINEVERSE_REVEAL_RESET_TOKEN", raising=False)
    reload_settings()
    try:
        page = client.get("/login")
        assert client.post(
            "/login",
            data={"csrf_token": _csrf(page.text), "identifier": user["email"], "password": PASSWORD},
            follow_redirects=False,
        ).status_code == 303
        settings = client.get("/settings")
        refused = client.post(
            "/settings/email/verify",
            data={"csrf_token": _csrf(settings.text)},
            follow_redirects=False,
        )
        assert refused.status_code == 303
        assert "verify-email?token=" not in refused.text
        assert db.query("SELECT token_hash FROM email_verifications WHERE user_id = ? AND used_at IS NULL", user["id"]) == []

        monkeypatch.setenv("ENGINEVERSE_REVEAL_RESET_TOKEN", "1")
        reload_settings()
        shown = client.post(
            "/settings/email/verify",
            data={"csrf_token": _csrf(client.get("/settings").text)},
            follow_redirects=False,
        )
        assert shown.status_code == 200
        assert "verify-email?token=" in shown.text
        start = shown.text.index("verify-email?token=") + len("verify-email?token=")
        token = shown.text[start:shown.text.index('"', start)]
        assert PASSWORD not in shown.text
        confirmed = client.get(f"/verify-email?token={token}", follow_redirects=False)
        assert confirmed.status_code == 303
        assert int(db.query_one("SELECT email_verified FROM users WHERE id = ?", user["id"])["email_verified"]) == 1
        again = client.get(f"/verify-email?token={token}")
        assert again.status_code == 400
        assert token not in again.text or "not valid" in again.text
    finally:
        monkeypatch.undo()
        reload_settings()


def test_production_does_not_reveal_a_confirmation_link(client, seeded, monkeypatch):
    user = _register("verprod" + os.urandom(3).hex())
    monkeypatch.setenv("ENGINEVERSE_ENV", "production")
    monkeypatch.setenv("ENGINEVERSE_REVEAL_RESET_TOKEN", "1")
    monkeypatch.delenv("ENGINEVERSE_SMTP_URL", raising=False)
    reload_settings()
    try:
        assert client.post(
            "/login",
            data={"csrf_token": _csrf(client.get("/login").text), "identifier": user["email"], "password": PASSWORD},
            follow_redirects=False,
        ).status_code == 303
        page = client.post(
            "/settings/email/verify",
            data={"csrf_token": _csrf(client.get("/settings").text)},
            follow_redirects=False,
        )
        body = page.text + page.headers.get("location", "")
        assert "verify-email?token=" not in body
        assert db.query("SELECT token_hash FROM email_verifications WHERE user_id = ?", user["id"]) == []
    finally:
        monkeypatch.undo()
        reload_settings()


def test_an_admin_can_clear_someone_elses_authenticator_without_seeing_the_seal(client, seeded):
    owner = _register("verown" + os.urandom(3).hex())
    seal = "SEAL-MUST-NOT-APPEAR-" + os.urandom(4).hex()
    db.execute("UPDATE users SET totp_secret = ? WHERE id = ?", seal, owner["id"])
    page = client.get("/login")
    assert client.post(
        "/login",
        data={
            "csrf_token": _csrf(page.text),
            "identifier": "admin@engineverse.local",
            "password": "Str0ngPassphrase#42!",
        },
        follow_redirects=False,
    ).status_code == 303
    try:
        admin = client.get("/admin").text
        assert seal not in admin
        cleared = client.post(
            "/admin/users/mfa/clear",
            data={"csrf_token": _csrf(admin), "user_id": owner["id"]},
            follow_redirects=False,
        )
        assert cleared.status_code == 303
        assert seal not in cleared.text
        assert db.query_one("SELECT totp_secret FROM users WHERE id = ?", owner["id"])["totp_secret"] is None
        self_clear = client.post(
            "/admin/users/mfa/clear",
            data={
                "csrf_token": _csrf(client.get("/admin").text),
                "user_id": db.query_one("SELECT id FROM users WHERE email = 'admin@engineverse.local'")["id"],
            },
            follow_redirects=False,
        )
        assert self_clear.headers["location"].endswith("/settings#mfa")
    finally:
        db.execute("UPDATE users SET totp_secret = NULL WHERE id = ?", owner["id"])


def test_a_student_cannot_clear_an_authenticator(signed_in):
    response = signed_in.post(
        "/admin/users/mfa/clear",
        data={"csrf_token": _csrf(signed_in.get("/settings").text), "user_id": "x"},
        follow_redirects=False,
    )
    assert response.status_code == 403


def test_sqlite_backup_copies_rows_and_refuses_to_overwrite(tmp_path):
    from scripts.backup_sqlite import BackupRefused, backup_sqlite

    source = tmp_path / "src.sqlite"
    dest = tmp_path / "nested" / "copy.sqlite"
    with sqlite3.connect(source) as conn:
        conn.execute("CREATE TABLE notes (id INTEGER PRIMARY KEY, body TEXT)")
        conn.execute("INSERT INTO notes (body) VALUES ('keep')")
    backup_sqlite(source, dest)
    with sqlite3.connect(dest) as conn:
        assert conn.execute("SELECT body FROM notes").fetchone()[0] == "keep"
    with pytest.raises(BackupRefused):
        backup_sqlite(source, dest)


def test_postgres_backup_script_does_not_print_the_url(tmp_path):
    stub = tmp_path / "bin"
    stub.mkdir()
    log = tmp_path / "args"
    dump = stub / "pg_dump"
    dump.write_text(
        "#!/bin/sh\nprintf '%s\\n' \"$*\" > \"$DUMP_LOG\"\n"
        "for arg in \"$@\"; do\n"
        "  case \"$arg\" in\n"
        "    --file=*) touch \"${arg#--file=}\" ;;\n"
        "  esac\ndone\n",
        encoding="utf-8",
    )
    dump.chmod(0o755)
    url = "postgresql://engineverse:secret-not-printed@127.0.0.1:5432/engineverse"
    env = os.environ.copy()
    env.update({"PATH": f"{stub}:{env.get('PATH', '')}", "ENGINEVERSE_DB_URL": url, "DUMP_LOG": str(log)})
    out = tmp_path / "out.dump"
    result = subprocess.run(
        ["sh", "scripts/backup_postgres.sh", str(out)],
        cwd=REPO_ROOT, env=env, capture_output=True, text=True,
    )
    combined = result.stdout + result.stderr
    assert result.returncode == 0, combined
    assert "secret-not-printed" not in combined
    assert url not in combined
    assert out.is_file()
    again = subprocess.run(
        ["sh", "scripts/backup_postgres.sh", str(out)],
        cwd=REPO_ROOT, env=env, capture_output=True, text=True,
    )
    assert again.returncode == 2
    assert "secret-not-printed" not in again.stdout + again.stderr


def test_backup_loop_does_not_print_the_password(tmp_path):
    stub = tmp_path / "bin"
    stub.mkdir()
    dump = stub / "pg_dump"
    dump.write_text(
        "#!/bin/sh\nfor arg in \"$@\"; do\n"
        "  case \"$arg\" in --file=*) touch \"${arg#--file=}\" ;; esac\ndone\n",
        encoding="utf-8",
    )
    dump.chmod(0o755)
    password = "loop-secret-not-printed"
    env = os.environ.copy()
    env.update({
        "PATH": f"{stub}:{env.get('PATH', '')}",
        "PGPASSWORD": password,
        "PGHOST": "db",
        "PGUSER": "engineverse",
        "PGDATABASE": "engineverse",
        "BACKUP_DIR": str(tmp_path / "backups"),
        "BACKUP_ONCE": "1",
    })
    result = subprocess.run(
        ["sh", "scripts/backup_loop.sh"],
        cwd=REPO_ROOT, env=env, capture_output=True, text=True,
    )
    combined = result.stdout + result.stderr
    assert result.returncode == 0, combined
    assert password not in combined
    assert list((tmp_path / "backups").glob("engineverse-*.dump"))
