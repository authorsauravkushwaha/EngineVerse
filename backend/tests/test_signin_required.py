"""Compulsory sign-in, and the practice cards that sit behind it.

The rest of the suite runs with ENGINEVERSE_SIGNIN=optional (see conftest) so
it can check what the catalogue pages render. These tests switch the default
gate back on and check:

* a signed-out visitor reaches only the account pages and is returned to the
  page they asked for after signing in;
* the API answers 401 JSON, and protected pages never leak FastAPI's raw
  ``{"detail": ...}`` body;
* every practice card can actually be answered, with or without JavaScript,
  including the mistake notebook, which used to post the wrong id and render
  no options.
"""
from __future__ import annotations

import re

import pytest
from starlette.testclient import TestClient

from engineverse import db
from engineverse.config import reload_settings

PASSWORD = "LearnBuild#2026!"


def _csrf(html: str) -> str:
    marker = 'name="csrf_token" value="'
    start = html.index(marker) + len(marker)
    return html[start : html.index('"', start)]


@pytest.fixture
def gated_app(seeded, monkeypatch):
    monkeypatch.setenv("ENGINEVERSE_SIGNIN", "required")
    reload_settings()
    from main import create_app

    yield create_app()
    monkeypatch.undo()
    reload_settings()


@pytest.fixture
def gated(gated_app):
    with TestClient(gated_app, raise_server_exceptions=False, follow_redirects=False) as client:
        yield client


def _sign_in(client, identifier="asha@example.com", next_url=None):
    page = client.get("/login" + (f"?next={next_url}" if next_url else ""))
    assert page.status_code == 200
    data = {"csrf_token": _csrf(page.text), "identifier": identifier, "password": PASSWORD}
    if next_url:
        data["next"] = next_url
    return client.post("/login", data=data)


def _page_csrf(html: str) -> str:
    return re.search(r'csrf: "([^"]+)"', html).group(1)


# ---------------------------------------------------------------------------
# The gate
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("path", [
    "/", "/explore", "/practice", "/practice/questions", "/dpp", "/topics/ohms-law",
    "/programming", "/projects", "/search?q=beam", "/tutor", "/streams", "/flashcards",
    "/community", "/leaderboard", "/sitemap.xml",
])
def test_signed_out_pages_go_to_sign_in(gated, path):
    response = gated.get(path)
    assert response.status_code == 303, path
    location = response.headers["location"]
    assert location.startswith("/login"), (path, location)


def test_the_requested_page_is_kept_as_next(gated):
    response = gated.get("/practice/questions?difficulty=easy")
    assert response.headers["location"] == "/login?next=/practice/questions%3Fdifficulty%3Deasy"
    assert gated.get("/").headers["location"] == "/login"


@pytest.mark.parametrize("path", [
    "/login", "/register", "/forgot-password", "/reset-password", "/terms", "/privacy",
    "/offline", "/health", "/robots.txt", "/sw.js", "/manifest.webmanifest", "/static/css/app.css",
])
def test_account_legal_and_asset_paths_stay_open(gated, path):
    assert gated.get(path).status_code == 200, path


def test_api_answers_401_json_when_signed_out(gated):
    response = gated.post("/api/practice/answer", json={"questionId": "x", "optionIndex": 0})
    assert response.status_code == 401
    assert response.json() == {"ok": False, "error": "Sign in to continue.", "signIn": "/login"}
    assert gated.get("/api/me").status_code == 401


def test_robots_does_not_advertise_gated_pages(gated):
    body = gated.get("/robots.txt").text
    assert "Disallow: /\n" in body and "Sitemap" not in body


def test_sign_in_returns_to_the_requested_page(gated):
    response = _sign_in(gated, next_url="/practice/questions")
    assert response.status_code == 303
    assert response.headers["location"] == "/practice/questions"
    assert gated.get("/practice/questions").status_code == 200
    assert gated.get("/").status_code == 200


def test_an_offsite_next_is_ignored(gated):
    response = _sign_in(gated, next_url="//evil.example/steal")
    assert response.headers["location"] == "/"


def test_already_signed_in_login_follows_next(gated):
    _sign_in(gated)
    response = gated.get("/login?next=/dpp")
    assert response.status_code == 303 and response.headers["location"] == "/dpp"


def test_sign_out_lands_on_the_sign_in_form(gated):
    _sign_in(gated)
    home = gated.get("/")
    response = gated.post("/logout", data={"csrf_token": _csrf(home.text)})
    assert response.status_code == 303 and response.headers["location"] == "/login"
    assert gated.get("/").headers["location"] == "/login"


def test_gated_layout_hides_navigation_that_would_bounce(gated):
    page = gated.get("/login").text
    assert "data-signin-gate" in page
    assert 'class="mainnav"' not in page and 'class="bottomnav"' not in page
    assert 'id="global-search"' not in page
    assert 'href="/register"' in page


def test_signed_in_layout_keeps_navigation(gated):
    _sign_in(gated)
    page = gated.get("/practice").text
    assert "data-signin-gate" not in page and 'class="mainnav"' in page


def test_gate_can_be_turned_off(seeded, monkeypatch):
    monkeypatch.setenv("ENGINEVERSE_SIGNIN", "optional")
    reload_settings()
    try:
        from main import create_app

        with TestClient(create_app(), follow_redirects=False) as client:
            assert client.get("/explore").status_code == 200
    finally:
        monkeypatch.undo()
        reload_settings()


def test_a_typo_in_the_setting_keeps_the_gate_closed(monkeypatch):
    monkeypatch.setenv("ENGINEVERSE_SIGNIN", "optinal")
    try:
        assert reload_settings().signin_required
    finally:
        monkeypatch.undo()
        reload_settings()


def test_production_rejects_an_unknown_signin_mode(monkeypatch):
    monkeypatch.setenv("ENGINEVERSE_ENV", "production")
    monkeypatch.setenv("ENGINEVERSE_SIGNIN", "sometimes")
    try:
        problems = reload_settings().production_problems()
        assert any("ENGINEVERSE_SIGNIN" in p for p in problems)
    finally:
        monkeypatch.undo()
        reload_settings()


# ---------------------------------------------------------------------------
# Sign-in page messages (gate-independent)
# ---------------------------------------------------------------------------

def test_protected_page_redirects_instead_of_raw_json(client):
    response = client.get("/mistakes", follow_redirects=False)
    assert response.status_code == 303
    assert response.headers["location"] == "/login?next=/mistakes"
    assert "detail" not in response.text


@pytest.mark.parametrize("code, expected", [
    ("csrf", "That form had expired"),
    ("reset", "Your password was changed"),
])
def test_login_error_codes_are_sentences_not_codes(client, code, expected):
    page = client.get(f"/login?error={code}").text
    assert expected in page
    assert f"Could not sign you in</span>{code}" not in page


def test_unknown_login_error_code_is_not_echoed(client):
    page = client.get("/login?error=<b>owned</b>").text
    assert "owned" not in page


# ---------------------------------------------------------------------------
# Practice cards
# ---------------------------------------------------------------------------

def _first_card(html: str) -> tuple[str, str | None]:
    match = re.search(r'data-quiz="([^"]+)"(?: data-set="([^"]+)")?', html)
    assert match, "no question card on the page"
    return match.group(1), match.group(2)


@pytest.mark.parametrize("path", ["/practice/questions", "/dpp", "/programming/python"])
def test_cards_post_to_a_real_endpoint_without_the_answer_key(gated, path):
    _sign_in(gated)
    page = gated.get(path).text
    assert 'action="/practice/check"' in page, path
    assert 'name="question_id"' in page
    question_id, _ = _first_card(page)
    explanation = db.scalar("SELECT explanation FROM questions WHERE id = ?", question_id)
    assert explanation and explanation[:40] not in page, "the explanation must not ship before an answer"
    assert "is_correct" not in page


def test_json_answer_records_and_reveals_after_submit(gated):
    _sign_in(gated)
    page = gated.get("/dpp").text
    question_id, set_id = _first_card(page)
    response = gated.post(
        "/api/practice/answer",
        json={"questionId": question_id, "optionIndex": 0, "setId": set_id},
        headers={"X-CSRF-Token": _page_csrf(page)},
    )
    body = response.json()
    assert response.status_code == 200 and body["ok"] is True
    assert body["correctLabel"] and body["explanation"]
    again = gated.get("/dpp").text
    assert "data-attempt-chip" in again


def test_no_javascript_form_grades_and_links_back(gated):
    _sign_in(gated)
    page = gated.get("/practice/questions").text
    question_id, _ = _first_card(page)
    correct_index = db.scalar(
        "SELECT order_index FROM question_options WHERE question_id = ? AND is_correct = 1", question_id
    )
    labels = [r["order_index"] for r in db.query(
        "SELECT order_index FROM question_options WHERE question_id = ? ORDER BY order_index", question_id
    )]
    response = gated.post("/practice/check", data={
        "csrf_token": _csrf(page), "question_id": question_id,
        "option": str(labels.index(correct_index)), "next": "/practice/questions",
    })
    assert response.status_code == 200
    assert "<h1>Correct</h1>" in response.text
    assert f'href="/practice/questions#q-{question_id}"' in response.text


def test_no_javascript_form_without_a_choice_asks_for_one(gated):
    _sign_in(gated)
    page = gated.get("/practice/questions").text
    question_id, _ = _first_card(page)
    response = gated.post("/practice/check", data={
        "csrf_token": _csrf(page), "question_id": question_id, "next": "/practice/questions",
    })
    assert response.status_code == 422
    assert "Choose one of the listed options" in response.text


def test_no_javascript_form_keeps_next_on_site(gated):
    _sign_in(gated)
    page = gated.get("/practice/questions").text
    question_id, _ = _first_card(page)
    response = gated.post("/practice/check", data={
        "csrf_token": _csrf(page), "question_id": question_id, "option": "0",
        "next": "https://evil.example/",
    })
    assert "evil.example" not in response.text


def test_mistake_notebook_cards_can_be_answered_again(gated):
    _sign_in(gated, identifier="ravi@example.com")
    page = gated.get("/practice/questions").text
    question_id, _ = _first_card(page)
    wrong_index = next(
        i for i, row in enumerate(db.query(
            "SELECT is_correct FROM question_options WHERE question_id = ? ORDER BY order_index", question_id
        )) if not row["is_correct"]
    )
    gated.post("/api/practice/answer", json={"questionId": question_id, "optionIndex": wrong_index},
               headers={"X-CSRF-Token": _page_csrf(page)})

    notebook = gated.get("/mistakes")
    assert notebook.status_code == 200
    html = notebook.text
    # The card carries the question's id, not the mistake row's id ...
    assert f'data-quiz="{question_id}"' in html
    # ... it renders options to pick from ...
    card = html[html.index(f'data-quiz="{question_id}"'):]
    card = card[: card.index("</form>")]
    assert card.count('class="opt"') >= 2
    # ... a real wrong count, and no explanation before the retry.
    assert re.search(r"Wrong \d+×", html)
    explanation = db.scalar("SELECT explanation FROM questions WHERE id = ?", question_id)
    assert explanation[:40] not in html

    retry = gated.post("/api/practice/answer", json={"questionId": question_id, "optionIndex": wrong_index},
                       headers={"X-CSRF-Token": _page_csrf(html)})
    assert retry.status_code == 200 and retry.json()["ok"] is True


def test_every_seeded_question_id_fits_the_answer_endpoints(seeded):
    from engineverse import practice

    too_long = db.query(
        "SELECT id FROM questions WHERE is_active = 1 AND length(id) > ?", practice.MAX_ID_LENGTH
    )
    assert not too_long, f"{len(too_long)} questions could never be answered, e.g. {too_long[0]['id']}"
    too_long_sets = db.query("SELECT id FROM dpp_sets WHERE length(id) > ?", practice.MAX_ID_LENGTH)
    assert not too_long_sets


def test_a_long_concept_check_id_can_be_answered(gated):
    """The 65+ character mastery ids were refused with "Invalid question identifier."."""
    row = db.query_one(
        "SELECT id FROM questions WHERE is_active = 1 AND length(id) > 64 ORDER BY length(id) DESC LIMIT 1"
    )
    if row is None:
        pytest.skip("no long question ids in this seed")
    _sign_in(gated)
    page = gated.get("/practice/questions").text
    response = gated.post(
        "/api/practice/answer", json={"questionId": row["id"], "optionIndex": 0},
        headers={"X-CSRF-Token": _page_csrf(page)},
    )
    assert response.status_code == 200, response.text
    assert response.json()["ok"] is True
    form = gated.post("/practice/check", data={
        "csrf_token": _csrf(page), "question_id": row["id"], "option": "0", "next": "/practice/questions",
    })
    assert form.status_code == 200
    assert "<h1>Not quite</h1>" in form.text or "<h1>Correct</h1>" in form.text


def test_a_solved_question_pays_full_xp_only_once(gated):
    """A wrong answer reveals the right option; re-answering must not farm full XP."""
    from engineverse import progress

    _sign_in(gated, identifier="priya@example.com")
    user_id = db.scalar("SELECT id FROM users WHERE email = 'priya@example.com'")
    page = gated.get("/practice/questions?difficulty=hard").text
    question_id, _ = _first_card(page)
    rows = db.query(
        "SELECT is_correct FROM question_options WHERE question_id = ? ORDER BY order_index", question_id
    )
    right = next(i for i, row in enumerate(rows) if row["is_correct"])
    wrong = next(i for i, row in enumerate(rows) if not row["is_correct"])
    headers = {"X-CSRF-Token": _page_csrf(page)}

    def answer(index):
        return gated.post("/api/practice/answer", json={"questionId": question_id, "optionIndex": index},
                          headers=headers).json()

    before = progress.total_xp(user_id)
    assert answer(wrong)["xp"] == 1
    first = answer(right)
    assert first["correct"] is True and first["alreadySolved"] is False and first["xp"] == 15
    for _ in range(3):
        again = answer(right)
        assert again["correct"] is True and again["alreadySolved"] is True
        assert again["xp"] == 1, "a question already solved must pay only the attempt XP"
    assert progress.total_xp(user_id) == before + 1 + 15 + 3
    full = db.scalar(
        "SELECT count(*) FROM xp_events WHERE user_id = ? AND reason = 'question.correct' AND entity_id = ?",
        user_id, question_id,
    )
    assert full == 1


def test_the_flash_message_is_shown_once(gated):
    response = _sign_in(gated)
    assert response.status_code == 303
    first = gated.get("/")
    assert 'class="flash"' in first.text
    assert "ev_flash=" in first.headers.get("set-cookie", "")
    assert 'class="flash"' not in gated.get("/practice").text
