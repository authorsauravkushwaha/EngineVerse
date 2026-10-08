"""The AI tutor: grounded answers, honest refusals, no markup, labelled output."""
from __future__ import annotations

import pytest
from starlette.testclient import TestClient


@pytest.fixture()
def fresh_client(app):
    """A separate client so the rate-limit test cannot exhaust the shared one."""
    return TestClient(app, raise_server_exceptions=False, follow_redirects=False)


def _csrf(html: str) -> str:
    marker = 'name="csrf_token" value="'
    return html[html.index(marker) + len(marker):].split('"')[0]


def _ask(client, question: str, csrf: str | None = None):
    token = csrf or _csrf(client.get("/login").text)
    return client.post("/api/tutor/ask", json={"question": question},
                       headers={"Accept": "*/*", "x-csrf-token": token})


class TestTutorGrounding:
    def test_a_covered_topic_is_answered_with_sources(self, client):
        response = _ask(client, "explain Bernoulli's equation and when it applies")
        assert response.status_code == 200
        body = response.json()
        assert body["grounded"] is True
        assert body["answer"].strip()
        assert body["sources"], "a grounded answer must cite what it came from"

    def test_every_citation_in_the_answer_resolves_to_a_source(self, client):
        body = _ask(client, "explain Bernoulli's equation").json()
        cited = {int(n) for n in __import__("re").findall(r"\[(\d+)\]", body["answer"])}
        listed = {src["n"] for src in body["sources"]}
        assert cited, "the answer should carry numbered citations"
        assert cited <= listed, f"citations {cited - listed} have no matching source"

    def test_sources_are_real_platform_urls(self, client):
        body = _ask(client, "explain Bernoulli's equation").json()
        for src in body["sources"]:
            assert src["url"].startswith("/"), f"source points off-platform: {src['url']}"
            assert not src["url"].startswith("//"), "source is a protocol-relative external URL"

    def test_an_uncovered_subject_is_refused_not_invented(self, client):
        body = _ask(client, "how do I bake a chocolate souffle at altitude").json()
        assert body["grounded"] is False
        assert not body["answer"], "an ungrounded reply must not contain prose to read"
        assert "not going to guess" in body["message"] or "could not find" in body["message"]

    def test_an_empty_question_is_rejected(self, client):
        response = _ask(client, "")
        assert response.status_code == 422
        assert response.json()["ok"] is False

    def test_an_oversized_question_is_rejected(self, client):
        response = _ask(client, "x" * 401)
        assert response.status_code == 422


class TestTutorSafety:
    def test_note_markup_never_reaches_the_client(self, client):
        """A note body is authored content; the API must not return it as markup.

        The client escapes too, but the contract is plain text, so a stored
        <script> cannot survive even for a client that trusted the response.
        """
        from engineverse import db as db_conn, search
        from engineverse.security.ids import ulid

        topic = db_conn.query_one("SELECT id FROM topics LIMIT 1")
        note = db_conn.query_one("SELECT id FROM notes WHERE topic_id = ?", topic["id"])
        payloads = [
            "<script>alert(1)</script> arrays are contiguous",
            '<img src=x onerror=alert(2)> arrays explained',
            '"><svg/onload=alert(3)> about arrays',
        ]
        for offset, payload in enumerate(payloads):
            db_conn.execute(
                "INSERT INTO note_sections (id, note_id, kind, title, body, order_index) "
                "VALUES (?,?,?,?,?,?)",
                ulid(), note["id"], "concept", "arrays safety note", payload, 900 + offset,
            )
        try:
            search.reindex_all()
            body = _ask(client, "explain arrays in detail please").json()
            for needle in ("<script>", "onerror=", "<svg", "<img"):
                assert needle not in body["answer"], f"markup leaked into the answer: {needle}"
        finally:
            db_conn.execute("DELETE FROM note_sections WHERE title = 'arrays safety note'")
            search.reindex_all()

    def test_the_answer_is_labelled_as_ai_generated(self, client):
        body = _ask(client, "explain Bernoulli's equation").json()
        assert "AI-generated" in body["disclosure"]

    def test_the_rate_limit_applies(self, fresh_client):
        client = fresh_client
        csrf = _csrf(client.get("/login").text)
        last = None
        for _ in range(32):
            last = _ask(client, "arrays", csrf)
        assert last.status_code == 429, "the configured 30/hour AI limit did not engage"


class TestTutorPage:
    def test_the_page_renders_for_an_anonymous_visitor(self, client):
        response = client.get("/tutor")
        assert response.status_code == 200
        for marker in ("tutor-form", "tutor-question", "AI-generated", "callout-ai"):
            assert marker in response.text, f"{marker} missing from the tutor page"

    def test_the_form_carries_a_csrf_token(self, client):
        html = client.get("/tutor").text
        assert 'name="csrf_token"' in html

    def test_the_page_is_reachable_from_the_navigation(self, client):
        assert 'href="/tutor"' in client.get("/").text

    def test_the_route_handler_exists_in_the_javascript(self):
        """The template's controls are inert unless app.js wires them."""
        from pathlib import Path

        script = Path("backend/static/js/app.js").read_text(encoding="utf-8")
        assert "#tutor-form" in script
        assert "/api/tutor/ask" in script
        assert "escapeHtml" in script, "the answer must be escaped before innerHTML"
