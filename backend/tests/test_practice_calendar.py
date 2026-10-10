"""The practice date is the day the visitor asked for, not the newest seeded set."""
from __future__ import annotations

from datetime import timedelta

from engineverse import practice


def test_today_is_labelled_with_today_not_the_newest_seed(client):
    today = practice.calendar_today()
    ahead = today + timedelta(days=6)
    page = client.get("/practice")
    assert page.status_code == 200
    assert practice.practice_title(today) in page.text
    assert f'href="/dpp/{today.isoformat()}"' in page.text
    assert practice.practice_title(ahead) not in page.text


def test_a_day_weeks_later_still_has_questions_labelled_with_that_day(client):
    later = practice.calendar_today() + timedelta(days=40)
    page = client.get(f"/dpp/{later.isoformat()}")
    assert page.status_code == 200
    assert practice.practice_title(later) in page.text
    assert "Check answer" in page.text
    assert f'data-set="dpp-{later.isoformat()}"' not in page.text


def test_an_exact_seeded_day_keeps_that_set(client):
    today = practice.calendar_today()
    page = client.get(f"/dpp/{today.isoformat()}")
    assert page.status_code == 200
    assert f'data-set="dpp-{today.isoformat()}"' in page.text


def test_a_date_that_is_not_a_date_is_not_invented(client):
    assert client.get("/dpp/not-a-date").status_code == 404
    assert client.get("/dpp/2026-13-40").status_code == 404


def test_every_written_depth_is_on_the_reading_page(client):
    from engineverse import db

    row = db.query_one("SELECT slug FROM topics WHERE status = 'published' ORDER BY slug LIMIT 1")
    page = client.get(f"/topics/{row['slug']}", params={"depths": "all"})
    assert page.status_code == 200
    assert 'id="depth-beginner"' in page.text
    assert 'id="depth-industry"' in page.text
    assert "Plain language" in page.text


def test_sql_is_a_path_not_an_empty_card(client):
    page = client.get("/programming/sql")
    assert page.status_code == 200
    assert "SELECT" in page.text
    assert "Professional habit" in page.text
    assert "parameter" in page.text.lower()
