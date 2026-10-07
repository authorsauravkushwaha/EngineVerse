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
