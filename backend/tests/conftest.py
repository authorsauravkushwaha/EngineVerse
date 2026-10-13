"""Shared fixtures: every test runs against a throwaway SQLite database."""
from __future__ import annotations

import os
import sys
import tempfile
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
BACKEND = REPO_ROOT / "backend"

# backend/ holds `main.py` and the `web` package; the repo root holds `seed_data`.
for entry in (str(BACKEND), str(REPO_ROOT)):
    if entry not in sys.path:
        sys.path.insert(0, entry)

# Hundreds of pre-existing tests exercise password-only login. OTP-specific
# tests opt into the required mode explicitly with monkeypatch.
#
# This has to be set while the conftest is imported, before pytest imports the
# test modules, and not inside a fixture. engineverse.config reads the
# repository's .env into the environment with os.environ.setdefault the first
# time it is imported, and the test modules import it during collection, so a
# fixture that ran later would find the variable already set: a working copy
# made with `cp .env.example .env` asks for a code at every sign-in, and every
# shared sign-in fixture would be answered with 401. Setting it here still lets
# an explicitly exported ENGINEVERSE_LOGIN_OTP win, because .env is loaded with
# setdefault too.
os.environ.setdefault("ENGINEVERSE_LOGIN_OTP", "disabled")

# Sign-in is compulsory by default. Most of the suite checks what the public
# catalogue pages render, so it runs with anonymous browsing allowed, set here
# for the same .env reason as above. test_signin_required.py switches the gate
# back on and checks the default behaviour.
os.environ.setdefault("ENGINEVERSE_SIGNIN", "optional")


@pytest.fixture(scope="session", autouse=True)
def _isolated_database(tmp_path_factory):
    """Points the app at a temporary database for the whole session."""
    workdir = tmp_path_factory.mktemp("engineverse-db")
    db_path = workdir / "test.sqlite3"

    os.environ["ENGINEVERSE_DB_PATH"] = str(db_path)
    os.environ["ENGINEVERSE_SECRET"] = "test-secret-key-for-pytest-only-0123456789"
    os.environ["ENGINEVERSE_ENV"] = "test"

    from engineverse import config

    config.reload_settings()

    from engineverse import db

    db.close_connection()
    db.migrate()
    yield
    db.close_connection()


@pytest.fixture(scope="session")
def seeded():
    """Seeds the temporary database once for the session and returns the module."""
    from scripts import seed

    seed.run(fresh=True)
    return seed


@pytest.fixture(autouse=True)
def _clear_rate_limits():
    """Empties the in-process sliding-window buckets around every test.

    The buckets are module-level and the database is session-scoped, so without
    this a test that registers five accounts leaves the ``register`` limiter
    (5 per hour per IP) exhausted and every later test sees a 403 that has
    nothing to do with what it is asserting. Test order should not matter.
    """
    from engineverse import db
    from engineverse.security import ratelimit

    with ratelimit._lock:
        ratelimit._buckets.clear()
    try:
        db.execute("DELETE FROM api_rate_limits")
    except Exception:
        pass
    yield
    with ratelimit._lock:
        ratelimit._buckets.clear()
    try:
        db.execute("DELETE FROM api_rate_limits")
    except Exception:
        pass


@pytest.fixture()
def app(seeded):
    from main import create_app

    return create_app()


@pytest.fixture()
def client(app):
    from starlette.testclient import TestClient

    with TestClient(app, raise_server_exceptions=False) as test_client:
        yield test_client


@pytest.fixture()
def demo_user(seeded):
    from engineverse import db

    row = db.query_one("SELECT id, email, username FROM users WHERE username = 'asha'")
    assert row is not None, "the seeder must create the demo student 'asha'"
    return dict(row)


@pytest.fixture()
def signed_in(client, demo_user):
    """Logs in through the real form flow and returns the authenticated client."""
    page = client.get("/login")
    token = _csrf(page.text)
    response = client.post(
        "/login",
        data={
            "csrf_token": token,
            "identifier": demo_user["email"],
            "password": "LearnBuild#2026!",
            "next": "/",
        },
        follow_redirects=False,
    )
    assert response.status_code in (302, 303), f"login failed: {response.status_code}"
    return client


def _csrf(html: str) -> str:
    marker = 'name="csrf_token" value="'
    start = html.index(marker) + len(marker)
    return html[start : html.index('"', start)]
