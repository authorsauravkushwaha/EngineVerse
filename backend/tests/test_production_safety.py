"""Production must refuse the shortcuts that are fine on a laptop.

These checks are about what the process will and will not do. A green run is
not a deployment, a backup, or a statement that submitted code is isolated.
"""
from __future__ import annotations

import os
import sqlite3
import subprocess
import sys
from pathlib import Path

import pytest

from engineverse import db, judge
from engineverse.config import DEV_SECRET, get_settings, reload_settings

REPO_ROOT = Path(__file__).resolve().parents[2]
DEMO_PASSWORD = "Str0ngPassphrase#42!"
SECRET = "production-test-secret-value-0123456789abcdef"


@pytest.fixture
def restored(monkeypatch):
    # Alias application writes the canonical name into os.environ. monkeypatch
    # does not see that write, so a later test would keep an https site URL
    # and mark cookies Secure. Snapshot the keys and put them back.
    watched = (
        "ENGINEVERSE_ENV", "ENGINEVERSE_SECRET", "ENGINEVERSE_DB_URL", "ENGINEVERSE_DB_PATH",
        "ENGINEVERSE_SITE_URL", "ENGINEVERSE_JUDGE", "ENGINEVERSE_JUDGE0_URL",
        "ENGINEVERSE_JAVA_SANDBOX_JAR", "ENGINEVERSE_REVEAL_RESET_TOKEN",
        "SITE_URL", "JUDGE", "JAVA_SANDBOX_JAR",
    )
    before = {key: os.environ.get(key) for key in watched}
    yield monkeypatch
    monkeypatch.undo()
    for key, value in before.items():
        if value is None:
            os.environ.pop(key, None)
        else:
            os.environ[key] = value
    reload_settings()
    judge.reset_provider()


def _production(monkeypatch, **overrides: str) -> None:
    monkeypatch.setenv("ENGINEVERSE_ENV", "production")
    monkeypatch.setenv("ENGINEVERSE_SECRET", SECRET)
    monkeypatch.setenv("ENGINEVERSE_DB_URL", "postgresql://engineverse_app:secret@db:5432/engineverse")
    monkeypatch.setenv("ENGINEVERSE_SITE_URL", "https://engineverse.example")
    monkeypatch.setenv("ENGINEVERSE_JUDGE", "disabled")
    monkeypatch.setenv("ENGINEVERSE_REVEAL_RESET_TOKEN", "0")
    for key, value in overrides.items():
        if value is None:
            monkeypatch.delenv(key, raising=False)
        else:
            monkeypatch.setenv(key, value)
    reload_settings()


def test_a_valid_production_config_has_no_problems(restored):
    _production(restored)
    assert get_settings().production_problems() == []


def test_production_problems_do_not_echo_the_secret(restored):
    _production(restored, ENGINEVERSE_SECRET="tiny", ENGINEVERSE_SITE_URL="http://localhost:8000", ENGINEVERSE_JUDGE="auto")
    text = " ".join(get_settings().production_problems())
    assert "tiny" not in text
    assert SECRET not in text
    assert "https://" in text
    assert "ENGINEVERSE_JUDGE=auto" in text


@pytest.mark.parametrize("judge_mode", ["auto", "python", "java", "local", ""])
def test_production_refuses_local_judges(restored, judge_mode):
    _production(restored, ENGINEVERSE_JUDGE=judge_mode)
    text = " ".join(get_settings().production_problems())
    assert "learner code" in text


def test_production_judge0_requires_a_url_and_does_not_claim_isolation(restored):
    _production(restored, ENGINEVERSE_JUDGE="judge0", ENGINEVERSE_JUDGE0_URL="")
    assert any("JUDGE0_URL" in item for item in get_settings().production_problems())
    _production(restored, ENGINEVERSE_JUDGE="judge0", ENGINEVERSE_JUDGE0_URL="http://judge0.internal:2358")
    assert get_settings().production_problems() == []


def test_production_refuses_the_development_secret_and_reset_tokens(restored):
    _production(restored, ENGINEVERSE_SECRET=DEV_SECRET, ENGINEVERSE_REVEAL_RESET_TOKEN="1")
    text = " ".join(get_settings().production_problems())
    assert "development fallback" in text
    assert "REVEAL_RESET_TOKEN" in text
    assert DEV_SECRET not in text


def test_startup_refuses_before_touching_a_database(restored):
    from main import prepare_runtime

    _production(restored, ENGINEVERSE_SITE_URL="http://localhost:8000", ENGINEVERSE_DB_URL=None)
    with pytest.raises(RuntimeError) as caught:
        prepare_runtime()
    assert "https://" in str(caught.value)
    assert SECRET not in str(caught.value)


def test_reset_database_refuses_in_production(restored):
    _production(restored)
    with pytest.raises(db.DatabaseError, match="production"):
        db.reset_database()


def test_disabled_judge_does_not_run_code(restored):
    restored.setenv("ENGINEVERSE_JUDGE", "disabled")
    reload_settings()
    judge.reset_provider()
    result = judge.run_custom("python", "print('pwned')")
    assert result.status == "unsupported_language"
    assert result.stdout == ""
    assert "pwned" not in result.stderr
    assert "disabled" in result.stderr.lower()
    info = judge.provider_info()
    assert info["runs_on_this_server"] is False
    assert "not a separate container" not in info["isolation"]


def test_production_auto_judge_fails_closed(restored):
    _production(restored, ENGINEVERSE_JUDGE="auto")
    judge.reset_provider()
    provider = judge.resolve_provider()
    assert provider.name == "disabled"
    result = provider.run("python", "print('pwned')")
    assert "pwned" not in result.stdout


def test_site_url_alias_is_read_when_the_canonical_name_is_unset(restored):
    restored.delenv("ENGINEVERSE_SITE_URL", raising=False)
    restored.setenv("SITE_URL", "https://alias.example")
    reload_settings()
    assert get_settings().site_url == "https://alias.example"


def test_deploy_files_do_not_embed_demo_passwords_or_seed_on_start():
    dockerfile = (REPO_ROOT / "deploy" / "Dockerfile.web").read_text(encoding="utf-8")
    compose = (REPO_ROOT / "deploy" / "docker-compose.yml").read_text(encoding="utf-8")
    combined = dockerfile + compose
    assert DEMO_PASSWORD not in combined
    assert "LearnBuild#2026!" not in combined
    command = next(line for line in dockerfile.splitlines() if line.startswith("CMD"))
    assert "seed.py" not in command
    assert "uvicorn" in command
    assert "ENGINEVERSE_SITE_URL" in compose
    assert "ENGINEVERSE_JUDGE" in compose
    assert "ENGINEVERSE_JAVA_SANDBOX_JAR" in compose
    assert "postgresql://engineverse_app:" in compose
    assert "engineverse_app" in (REPO_ROOT / "deploy" / "postgres" / "20-runtime-role.sh").read_text(encoding="utf-8")


def test_runtime_role_script_does_not_grant_create_or_embed_a_password():
    script = (REPO_ROOT / "deploy" / "postgres" / "20-runtime-role.sh").read_text(encoding="utf-8")
    assert "NOSUPERUSER" in script
    assert "REVOKE CREATE ON SCHEMA public FROM engineverse_app" in script
    assert "APP_DB_PASSWORD" in script
    assert "password123" not in script.lower()


def _run(args: list[str], env: dict[str, str]) -> subprocess.CompletedProcess[str]:
    merged = os.environ.copy()
    merged.pop("ENGINEVERSE_DB_URL", None)
    merged.update(env)
    return subprocess.run(
        [sys.executable, *args],
        cwd=REPO_ROOT,
        env=merged,
        capture_output=True,
        text=True,
    )


def test_production_seed_refuses_fresh_and_demo_without_printing_passwords(tmp_path):
    env = {
        "ENGINEVERSE_ENV": "production",
        "ENGINEVERSE_DB_PATH": str(tmp_path / "prod.sqlite"),
        "ENGINEVERSE_SECRET": SECRET,
    }
    fresh = _run(["scripts/seed.py", "--fresh"], env)
    demo = _run(["scripts/seed.py", "--demo"], env)
    for result in (fresh, demo):
        assert result.returncode == 2, result.stdout + result.stderr
        blob = result.stdout + result.stderr
        assert "refusing" in blob.lower()
        assert DEMO_PASSWORD not in blob
        assert "LearnBuild#2026!" not in blob


def test_catalogue_seed_can_skip_demo_accounts(tmp_path):
    path = tmp_path / "catalogue.sqlite"
    result = _run(
        ["scripts/seed.py", "--no-demo"],
        {"ENGINEVERSE_ENV": "development", "ENGINEVERSE_DB_PATH": str(path), "ENGINEVERSE_SECRET": SECRET},
    )
    assert result.returncode == 0, result.stdout[-1500:] + result.stderr[-1500:]
    blob = result.stdout + result.stderr
    assert DEMO_PASSWORD not in blob
    assert "No demo accounts" in blob
    conn = sqlite3.connect(path)
    try:
        assert conn.execute("SELECT count(*) FROM users").fetchone()[0] == 0
        assert conn.execute("SELECT count(*) FROM subjects").fetchone()[0] > 0
    finally:
        conn.close()


def test_fresh_refuses_to_delete_non_demo_users(tmp_path):
    path = tmp_path / "people.sqlite"
    env = {"ENGINEVERSE_ENV": "development", "ENGINEVERSE_DB_PATH": str(path), "ENGINEVERSE_SECRET": SECRET}
    created = _run(
        ["-c", "import sys; sys.path[:0]=['backend','.']; from engineverse import db; "
         "db.migrate(); db.execute(\"INSERT INTO users (id,email,username,password_hash,password_changed_at,created_at,updated_at) "
         "VALUES ('real','real@example.test','realperson','hash',0,0,0)\")"],
        env,
    )
    assert created.returncode == 0, created.stderr
    refused = _run(["scripts/seed.py", "--fresh"], env)
    assert refused.returncode == 2, refused.stdout + refused.stderr
    assert "non-demo" in refused.stderr.lower() or "not the development demo" in refused.stderr
    assert path.exists()
    conn = sqlite3.connect(path)
    try:
        assert conn.execute("SELECT count(*) FROM users WHERE email = 'real@example.test'").fetchone()[0] == 1
    finally:
        conn.close()


def test_release_does_not_overwrite_an_existing_catalogue(tmp_path):
    path = tmp_path / "kept.sqlite"
    env = {"ENGINEVERSE_ENV": "development", "ENGINEVERSE_DB_PATH": str(path), "ENGINEVERSE_SECRET": SECRET}
    created = _run(
        ["-c", "import sys; sys.path[:0]=['backend','.']; from engineverse import db; "
         "db.migrate(); db.execute(\"INSERT INTO subjects (id,slug,name) VALUES ('kept','kept','Kept subject')\")"],
        env,
    )
    assert created.returncode == 0, created.stderr
    result = _run(["scripts/release.py"], env)
    assert result.returncode == 0, result.stdout + result.stderr
    assert "already present" in result.stdout
    assert DEMO_PASSWORD not in result.stdout + result.stderr
    conn = sqlite3.connect(path)
    try:
        assert conn.execute("SELECT name FROM subjects WHERE id = 'kept'").fetchone()[0] == "Kept subject"
    finally:
        conn.close()


def test_release_refuses_a_production_config_without_connecting(tmp_path):
    result = _run(
        ["scripts/release.py"],
        {
            "ENGINEVERSE_ENV": "production",
            "ENGINEVERSE_SECRET": SECRET,
            "ENGINEVERSE_DB_URL": "postgresql://engineverse:secret@db:5432/engineverse",
            "ENGINEVERSE_SITE_URL": "http://engineverse.example",
            "ENGINEVERSE_JUDGE": "disabled",
            "ENGINEVERSE_DB_PATH": str(tmp_path / "unused.sqlite"),
        },
    )
    assert result.returncode == 1
    assert "https://" in result.stderr
    assert SECRET not in result.stderr
    assert "postgresql://" not in result.stderr
    assert ":secret@" not in result.stderr


def test_create_admin_does_not_accept_or_print_a_password(tmp_path):
    path = tmp_path / "admin.sqlite"
    password = "A-long-admin-passphrase-9"
    env = {
        "ENGINEVERSE_ENV": "development",
        "ENGINEVERSE_DB_PATH": str(path),
        "ENGINEVERSE_SECRET": SECRET,
        "ENGINEVERSE_ADMIN_PASSWORD": password,
    }
    leaked = _run(
        ["scripts/create_admin.py", "--email", "ops@example.test", "--username", "ops", "--password", password],
        env,
    )
    assert leaked.returncode != 0
    assert password not in leaked.stdout + leaked.stderr
    created = _run(
        ["scripts/create_admin.py", "--email", "ops@example.test", "--username", "ops", "--full-name", "Ops"],
        env,
    )
    assert created.returncode == 0, created.stdout + created.stderr
    assert password not in created.stdout + created.stderr
    assert "not printed" in created.stdout
    again = _run(
        ["scripts/create_admin.py", "--email", "other@example.test", "--username", "other"],
        env,
    )
    assert again.returncode == 1
    assert "already exists" in again.stderr
    assert password not in again.stderr


def test_login_page_hides_demo_passwords_outside_development(restored):
    from starlette.requests import Request
    from web.deps import render

    restored.setenv("ENGINEVERSE_ENV", "staging")
    reload_settings()
    scope = {
        "type": "http", "http_version": "1.1", "method": "GET", "scheme": "http",
        "path": "/login", "raw_path": b"/login", "query_string": b"", "headers": [],
        "client": ("127.0.0.1", 1234), "server": ("test", 80),
    }
    body = render(Request(scope), "login.html", next="/", error=None, mode="login").body.decode()
    assert DEMO_PASSWORD not in body
    assert "LearnBuild#2026!" not in body
    assert "TeachLearn#2026!" not in body


def test_login_page_shows_demo_passwords_in_the_test_environment(client):
    body = client.get("/login").text
    assert "asha@example.com" in body
    assert "LearnBuild#2026!" in body


def test_pwa_is_served_from_the_origin_root(client):
    manifest = client.get("/manifest.webmanifest")
    assert manifest.status_code == 200
    assert "manifest" in manifest.headers["content-type"]
    assert manifest.json()["start_url"] == "/"
    assert manifest.json()["scope"] == "/"
    worker = client.get("/sw.js")
    assert worker.status_code == 200
    assert "javascript" in worker.headers["content-type"]
    assert "Service-Worker-Allowed" in worker.headers


def test_assetlinks_are_absent_until_configured(client, restored):
    missing = client.get("/.well-known/assetlinks.json")
    assert missing.status_code == 404
    assert "not configured" in missing.text
    restored.setenv("ENGINEVERSE_TWA_PACKAGE", "not a package")
    restored.setenv("ENGINEVERSE_TWA_SHA256", "not-a-fingerprint")
    rejected = client.get("/.well-known/assetlinks.json")
    assert rejected.status_code == 404
    assert "not a package" not in rejected.text
    fingerprint = ":".join(["AB"] * 32)
    restored.setenv("ENGINEVERSE_TWA_PACKAGE", "org.example.engineverse")
    restored.setenv("ENGINEVERSE_TWA_SHA256", fingerprint.lower())
    ready = client.get("/.well-known/assetlinks.json")
    assert ready.status_code == 200
    body = ready.json()
    assert body[0]["target"]["package_name"] == "org.example.engineverse"
    assert body[0]["target"]["sha256_cert_fingerprints"] == [fingerprint]


def test_judge_status_is_staff_only_and_does_not_claim_a_container(client):
    import re

    assert client.get("/api/ops/judge").status_code == 403
    page = client.get("/login").text
    token = re.search(r'name="csrf_token" value="([^"]+)"', page).group(1)
    signed_in = client.post(
        "/login",
        data={"csrf_token": token, "identifier": "admin@engineverse.local",
              "password": DEMO_PASSWORD, "next": "/"},
        follow_redirects=False,
    )
    assert signed_in.status_code == 303, signed_in.text
    body = client.get("/api/ops/judge").json()
    assert body["ok"] is True, body
    assert body["runs_on_this_server"] is True, body
    assert "not a separate container" in body["isolation"], body
    assert "url" not in body
    assert "key" not in body
