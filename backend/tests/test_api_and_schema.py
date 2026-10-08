"""The JSON API surface, plus the schema that has to survive 1.5e9 users."""
from __future__ import annotations

import re

import pytest


def _csrf(html: str) -> str:
    marker = 'name="csrf_token" value="'
    start = html.index(marker) + len(marker)
    return html[start : html.index('"', start)]


class TestApiSurface:
    @pytest.mark.parametrize(
        "path",
        [
            "/api/search?q=bernoulli",
            "/api/search/suggest?q=arr",
            "/api/coding/languages",
            "/api/coding/problems",
            "/api/catalog/branches",
            "/api/catalog/subjects",
            "/api/catalog/formulas",
            "/api/practice/dpp",
            "/api/leaderboard",
        ],
    )
    def test_public_endpoints(self, client, path):
        response = client.get(path)
        assert response.status_code == 200, f"{path} -> {response.status_code}"
        assert response.json()["ok"] is True

    @pytest.mark.parametrize(
        "path",
        [
            "/api/me",
            "/api/progress",
            "/api/mistakes",
            "/api/bookmarks",
            "/api/certificates",
            "/api/notifications",
            "/api/recommendations",
            "/api/revision/due",
            "/api/coding/submissions",
        ],
    )
    def test_private_endpoints_need_a_session(self, client, path):
        assert client.get(path).status_code == 401

    @pytest.mark.parametrize(
        "path",
        [
            "/api/me",
            "/api/progress",
            "/api/mistakes",
            "/api/bookmarks",
            "/api/certificates",
            "/api/notifications",
            "/api/recommendations",
            "/api/revision/due",
            "/api/coding/submissions",
        ],
    )
    def test_private_endpoints_work_when_signed_in(self, signed_in, path):
        response = signed_in.get(path)
        assert response.status_code == 200, f"{path} -> {response.status_code}"
        assert response.json()["ok"] is True

    def test_unknown_api_path_is_a_json_404(self, client):
        response = client.get("/api/definitely-not-real")
        assert response.status_code == 404
        assert response.json()["ok"] is False

    def test_search_returns_structured_hits(self, client):
        body = client.get("/api/search?q=bernoulli").json()
        assert isinstance(body["results"], list)


class TestCodingApi:
    @pytest.mark.slow
    def test_running_a_solution_reports_a_verdict(self, signed_in):
        token = _csrf(signed_in.get("/practice/problems/two-sum").text)
        response = signed_in.post(
            "/api/coding/run",
            json={
                "csrf_token": token,
                "problemSlug": "two-sum",
                "language": "python",
                "code": "def two_sum(nums, target):\n    seen = {}\n"
                "    for i, v in enumerate(nums):\n"
                "        if target - v in seen:\n            return [seen[target - v], i]\n"
                "        seen[v] = i\n    return []\n",
            },
            headers={"x-csrf-token": token},
        )
        assert response.status_code == 200, response.text
        body = response.json()
        assert body["ok"] is True
        assert body["result"]["status"] in ("accepted", "wrong_answer", "runtime_error")

    @pytest.mark.slow
    def test_submitting_records_a_submission(self, signed_in):
        token = _csrf(signed_in.get("/practice/problems/two-sum").text)
        response = signed_in.post(
            "/api/coding/submit",
            json={
                "csrf_token": token,
                "problemSlug": "two-sum",
                "language": "python",
                "code": "def two_sum(nums, target):\n    seen = {}\n"
                "    for i, v in enumerate(nums):\n"
                "        if target - v in seen:\n            return [seen[target - v], i]\n"
                "        seen[v] = i\n    return []\n",
            },
            headers={"x-csrf-token": token},
        )
        assert response.status_code == 200, response.text
        body = response.json()
        assert body["result"]["status"] == "accepted"
        assert body["result"]["xp"] > 0

    def test_an_unsupported_language_is_refused_cleanly(self, signed_in):
        token = _csrf(signed_in.get("/practice/problems/two-sum").text)
        response = signed_in.post(
            "/api/coding/run",
            json={
                "csrf_token": token,
                "problemSlug": "two-sum",
                "language": "brainfuck",
                "code": "++++",
            },
            headers={"x-csrf-token": token},
        )
        assert response.status_code in (200, 400, 422)


class TestAnswerApi:
    @staticmethod
    def _option_indexes(question_id: str) -> tuple[int, int]:
        """Returns (correct_index, wrong_index) in the order the UI shows them."""
        from engineverse import db

        options = db.query(
            "SELECT is_correct FROM question_options WHERE question_id = ? ORDER BY order_index",
            question_id,
        )
        correct = next(i for i, o in enumerate(options) if o["is_correct"])
        wrong = next(i for i, o in enumerate(options) if not o["is_correct"])
        return correct, wrong

    def test_answering_an_mcq_correctly_is_marked_correct(self, signed_in):
        from engineverse import db

        question = db.query_one(
            "SELECT q.id FROM questions q WHERE q.kind = 'mcq' AND q.is_active = 1 "
            "AND (SELECT count(*) FROM question_options o WHERE o.question_id = q.id AND o.is_correct = 1) = 1 "
            "LIMIT 1"
        )
        assert question is not None, "no seeded MCQ with exactly one correct option"
        correct_index, _ = self._option_indexes(question["id"])
        token = _csrf(signed_in.get("/practice/questions").text)
        response = signed_in.post(
            "/api/practice/answer",
            json={
                "csrf_token": token,
                "questionId": question["id"],
                "optionIndex": correct_index,
            },
            headers={"x-csrf-token": token},
        )
        assert response.status_code == 200, response.text
        body = response.json()
        assert body["ok"] is True
        assert body["correct"] is True, f"a correct answer was marked wrong: {body}"
        assert body["xp"] > 0

    def test_answering_incorrectly_is_marked_wrong(self, signed_in):
        from engineverse import db

        question = db.query_one(
            "SELECT q.id FROM questions q WHERE q.kind = 'mcq' AND q.is_active = 1 "
            "AND (SELECT count(*) FROM question_options o WHERE o.question_id = q.id AND o.is_correct = 0) >= 1 "
            "LIMIT 1"
        )
        assert question is not None
        _, wrong_index = self._option_indexes(question["id"])
        token = _csrf(signed_in.get("/practice/questions").text)
        response = signed_in.post(
            "/api/practice/answer",
            json={
                "csrf_token": token,
                "questionId": question["id"],
                "optionIndex": wrong_index,
            },
            headers={"x-csrf-token": token},
        )
        assert response.status_code == 200, response.text
        body = response.json()
        assert body["correct"] is False
        assert body["correctLabel"], "the learner must be told which option was right"

    def test_an_unknown_question_is_a_404(self, signed_in):
        token = _csrf(signed_in.get("/practice/questions").text)
        response = signed_in.post(
            "/api/practice/answer",
            json={"csrf_token": token, "questionId": "nope", "answerText": "x"},
            headers={"x-csrf-token": token},
        )
        assert response.status_code in (400, 404, 422)


class TestRateLimiting:
    def test_the_limiter_reports_a_budget(self, client):
        response = client.get("/api/search?q=x")
        assert response.status_code == 200
        assert "x-ratelimit-remaining" in response.headers


class TestSqliteSchema:
    """The development schema must actually migrate and hold the seed data."""

    def test_migration_is_idempotent(self):
        from engineverse import db

        db.migrate()
        db.migrate()  # a second run must be a no-op, not an error
        assert db.row_count("users") > 0

    def test_every_table_the_seeder_reports_exists(self):
        from engineverse import db
        from scripts.seed import TABLES

        for table in TABLES:
            assert db.row_count(table) >= 0, f"{table} is not a real table"

    def test_the_seed_data_is_substantial(self):
        """Guards against shipping an empty platform."""
        from engineverse import db

        for table, minimum in [
            ("branches", 40),
            ("subjects", 50),
            ("topics", 40),
            ("notes", 100),
            ("note_sections", 500),
            ("questions", 30),
            ("coding_problems", 10),
            ("coding_testcases", 40),
            ("projects", 5),
            ("flashcards", 20),
            ("roadmaps", 4),
            ("badges", 8),
        ]:
            assert db.row_count(table) >= minimum, f"{table} has too few rows"

    def test_search_index_covers_the_catalogue(self, seeded):
        from engineverse import db

        assert db.row_count("search_index") > 200

    def test_foreign_keys_are_enforced(self):
        import sqlite3

        from engineverse import db

        with pytest.raises((sqlite3.IntegrityError, db.DatabaseError)):
            db.execute(
                "INSERT INTO submissions (id, user_id, question_id, is_correct, created_at) "
                "VALUES ('x', 'no-such-user', 'no-such-question', 0, 0)"
            )


class TestPostgresSchema:
    """There is no PostgreSQL server here, so the production schema is verified
    by parsing it. .github/workflows/ci.yml applies it to a real server."""

    SCHEMA = "db/postgres/schema.pg.sql"

    @pytest.fixture(scope="class")
    def text(self):
        from pathlib import Path

        path = Path(__file__).resolve().parents[2] / self.SCHEMA
        assert path.exists(), "db/postgres/schema.pg.sql is missing"
        return path.read_text()

    def test_it_parses_as_postgres(self, text):
        sqlglot = pytest.importorskip("sqlglot")
        # DO $$ ... $$ blocks are opaque to the parser; lift them out.
        lifted = re.sub(r"\$\w*\$.*?\$\w*\$", "'__body__'", text, flags=re.S)
        statements = sqlglot.parse(lifted, read="postgres")
        assert statements, "the schema parsed to nothing"
        assert all(s is not None for s in statements), "a statement failed to parse"

    def test_it_creates_every_table_the_sqlite_schema_does(self, text):
        from pathlib import Path

        root = Path(__file__).resolve().parents[2]
        sqlite_schema = (root / "db" / "schema.sql").read_text()
        sqlite_tables = set(re.findall(r"CREATE TABLE IF NOT EXISTS (\w+)", sqlite_schema))
        pg_tables = set(re.findall(r"CREATE TABLE IF NOT EXISTS (\w+)", text))
        missing = sqlite_tables - pg_tables
        assert not missing, f"tables absent from the Postgres schema: {sorted(missing)}"

    def test_the_hot_tables_are_partitioned(self, text):
        for table in ("submissions", "activity", "audit_logs", "coding_submissions"):
            assert f"CREATE TABLE IF NOT EXISTS {table} (" in text
            assert f"engineverse_create_partitions('{table}'" in text, f"{table} is not partitioned"

    def test_partition_counts_are_declared_for_scale(self, text):
        assert "engineverse_create_partitions('submissions', 256)" in text
        assert "engineverse_create_partitions('activity', 256)" in text

    def test_emails_are_case_insensitive(self, text):
        assert "CITEXT NOT NULL UNIQUE" in text

    def test_the_helper_functions_exist(self, text):
        assert "CREATE OR REPLACE FUNCTION engineverse_create_partitions" in text
        assert "CREATE OR REPLACE FUNCTION engineverse_prune_before" in text


class TestCommunityEndpoints:
    """Regression coverage for the community forms.

    These post from plain HTML to JSON endpoints, so both body shapes and both
    response shapes have to work: a browser navigating gets a redirect, a script
    fetching gets JSON.
    """

    BROWSER = {"Accept": "text/html,application/xhtml+xml"}

    def _token(self, client):
        return _csrf(client.get("/community").text)

    def test_a_form_post_creates_a_thread(self, signed_in):
        token = self._token(signed_in)
        response = signed_in.post(
            "/api/community/threads",
            data={
                "title": "Why does Bernoulli assume inviscid flow?",
                "body": "I am unclear on when the assumption breaks down.",
                "kind": "question",
                "tags": "fluid-mechanics, exam",
            },
            headers={"x-csrf-token": token},
        )
        assert response.status_code == 200, response.text
        thread_id = response.json()["id"]

        from engineverse import db

        row = db.query_one("SELECT tags, kind FROM discussions WHERE id = ?", thread_id)
        assert row is not None
        assert row["kind"] == "question"
        # The form sends a comma-separated string; it must be stored as a list.
        assert "fluid-mechanics" in row["tags"]

    def test_a_json_post_creates_a_thread(self, signed_in):
        token = self._token(signed_in)
        response = signed_in.post(
            "/api/community/threads",
            json={"title": "Posted from the JS client", "body": "Body from a fetch call.",
                  "kind": "discussion", "tags": ["a", "b"]},
            headers={"x-csrf-token": token},
        )
        assert response.status_code == 200, response.text
        assert response.json()["id"]

    def test_a_navigating_browser_is_redirected_not_shown_json(self, signed_in):
        token = self._token(signed_in)
        response = signed_in.post(
            "/api/community/threads",
            data={"title": "Browser navigation", "body": "Submitted without scripting.",
                  "kind": "question"},
            headers={**self.BROWSER, "x-csrf-token": token},
            follow_redirects=False,
        )
        assert response.status_code == 303
        assert response.headers["location"].startswith("/community/")

    def test_a_navigating_browser_gets_a_flash_on_a_bad_post(self, signed_in):
        token = self._token(signed_in)
        response = signed_in.post(
            "/api/community/threads",
            data={"title": "hi", "body": "x", "kind": "question"},
            headers={**self.BROWSER, "x-csrf-token": token},
            follow_redirects=False,
        )
        assert response.status_code == 303
        assert response.headers["location"] == "/community"
        followed = signed_in.get("/community")
        assert "at least 5 characters" in followed.text

    def test_a_script_gets_json_on_a_bad_post(self, signed_in):
        token = self._token(signed_in)
        response = signed_in.post(
            "/api/community/threads",
            json={"title": "hi", "body": "x", "kind": "question"},
            headers={"Accept": "application/json", "x-csrf-token": token},
        )
        assert response.status_code == 400
        assert response.json()["ok"] is False

    def test_a_reply_is_stored_and_renders(self, signed_in):
        token = self._token(signed_in)
        created = signed_in.post(
            "/api/community/threads",
            json={"title": "Thread that gets a reply", "body": "Original post body here.",
                  "kind": "question"},
            headers={"x-csrf-token": token},
        )
        thread_id = created.json()["id"]
        response = signed_in.post(
            "/api/community/comments",
            data={"threadId": thread_id,
                  "body": "Because viscosity is negligible at high Reynolds number."},
            headers={"x-csrf-token": token},
        )
        assert response.status_code == 200, response.text
        page = signed_in.get(f"/community/{thread_id}")
        assert page.status_code == 200
        assert "Reynolds" in page.text

    def test_replying_to_a_missing_thread_is_404_not_500(self, signed_in):
        """A foreign-key violation must not surface as an internal error."""
        token = self._token(signed_in)
        response = signed_in.post(
            "/api/community/comments",
            json={"threadId": "no-such-thread", "body": "orphan reply"},
            headers={"x-csrf-token": token},
        )
        assert response.status_code == 404
        assert response.json()["ok"] is False

    def test_an_empty_reply_is_refused(self, signed_in):
        token = self._token(signed_in)
        created = signed_in.post(
            "/api/community/threads",
            json={"title": "Thread for an empty reply", "body": "Body text for the post.",
                  "kind": "question"},
            headers={"x-csrf-token": token},
        )
        response = signed_in.post(
            "/api/community/comments",
            json={"threadId": created.json()["id"], "body": "   "},
            headers={"x-csrf-token": token},
        )
        assert response.status_code == 400


class TestBranding:
    """The brand keys must line up across the seed data, brand() and the templates.

    They drifted apart once (brand_name vs site_name), which rendered an empty
    product name on every page without raising an error.
    """

    def test_site_name_is_populated_on_every_page(self, client):
        for path in ("/", "/explore", "/about"):
            html = client.get(path).text
            title = html[html.index("<title>") + 7:html.index("</title>")]
            assert "EngineVerse" in title, f"{path} rendered {title!r}"

    def test_brand_exposes_every_key_the_templates_use(self, seeded):
        from engineverse import brand

        data = brand.brand()
        required = {"site_name", "tagline", "description", "support_email",
                    "free_tier_note", "announcement", "accent_color"}
        missing = required - set(data)
        assert not missing, f"brand() is missing keys the templates read: {missing}"
        for key in ("site_name", "tagline", "accent_color"):
            assert data[key].strip(), f"brand['{key}'] is blank"

    def test_an_unset_key_falls_back_rather_than_rendering_blank(self, seeded):
        from engineverse import brand

        assert brand.get("site_name") == "EngineVerse"

    def test_the_registration_toggle_is_enforced(self, app, seeded):
        """Each attempt uses a fresh client: a successful sign-up leaves a session
        cookie behind, and /register redirects a signed-in visitor home, which
        would hide the very banner this asserts on."""
        from starlette.testclient import TestClient

        from engineverse import brand, db

        def signup(email, username):
            with TestClient(app, raise_server_exceptions=False) as anon:
                return anon.post(
                    "/register",
                    data={"email": email, "username": username, "full_name": "Toggle Test",
                          "password": "FreshStart#2026!", "password_confirm": "FreshStart#2026!"},
                    follow_redirects=False,
                )

        original = brand.get("registration_open")
        try:
            brand.set_many({"registration_open": "1"})
            assert signup("toggle-open@example.com", "toggleopen").status_code == 303

            brand.set_many({"registration_open": "0"})
            with TestClient(app, raise_server_exceptions=False) as anon:
                page = anon.get("/register")
            assert "Registration closed" in page.text
            refused = signup("toggle-closed@example.com", "toggleclosed")
            assert refused.status_code == 403
            assert db.query_one(
                "SELECT id FROM users WHERE email = 'toggle-closed@example.com'"
            ) is None, "an account was created while registration was closed"

            brand.set_many({"registration_open": "1"})
            assert signup("toggle-reopen@example.com", "togglereopen").status_code == 303
        finally:
            # The database is session-scoped; leaving this closed would 403 every
            # later registration test in the run.
            brand.set_many({"registration_open": original or "1"})

    def test_a_validation_error_does_not_look_like_a_closure(self, app, seeded):
        from starlette.testclient import TestClient

        from engineverse import brand

        brand.set_many({"registration_open": "1"})
        client = TestClient(app, raise_server_exceptions=False)
        response = client.post(
            "/register",
            data={"email": "mismatch@example.com", "username": "mismatchuser",
                  "full_name": "Mismatch Person", "password": "SomePass#2026!",
                  "password_confirm": "DifferentPass#2026!"},
            follow_redirects=False,
        )
        assert response.status_code == 422
        assert "do not match" in response.text
        assert "Registration closed" not in response.text


class TestErrorStatusCodes:
    """render() must honour status_code, not swallow it into the template context."""

    def test_a_bad_login_is_401_not_200(self, client):
        page = client.get("/login")
        response = client.post(
            "/login",
            data={"csrf_token": _csrf(page.text), "identifier": "asha@example.com",
                  "password": "DefinitelyWrong#9"},
            follow_redirects=False,
        )
        assert response.status_code == 401

    def test_a_weak_password_is_422_not_200(self, client):
        page = client.get("/register")
        response = client.post(
            "/register",
            data={"csrf_token": _csrf(page.text), "email": "weak@example.com",
                  "username": "weakuser", "full_name": "Weak User",
                  "password": "abc", "password_confirm": "abc"},
            follow_redirects=False,
        )
        assert response.status_code == 422


class TestFlashCookie:
    """Cookie values must be latin-1; a flash containing an em dash used to 500."""

    def test_a_non_ascii_flash_does_not_raise(self, signed_in):
        response = signed_in.post(
            "/api/feedback",
            json={"message": "The explanation is cut off on mobile.", "path": "/dpp"},
            headers={"Accept": "application/json", "x-csrf-token": _csrf(signed_in.get("/community").text)},
        )
        assert response.status_code == 200

        # The message that used to break it: an em dash is U+2014, not latin-1.
        from starlette.responses import RedirectResponse

        from web.deps import flash, read_flash

        redir = RedirectResponse("/dpp", status_code=303)
        flash(redir, "Thanks — that reached the team.")  # must not raise

        raw = redir.headers["set-cookie"]
        assert "Thanks" in raw

        class FakeRequest:
            cookies = {"ev_flash": raw.split("ev_flash=")[1].split(";")[0]}

        assert read_flash(FakeRequest()).startswith("Thanks — ")


class TestThemeAndJsonForms:
    """Two controls that existed but did nothing.

    base.html hard-coded data-theme="dark", so the admin theme setting and the
    whole [data-theme="light"] variable set in app.css were unreachable. And
    data-json-form was an attribute with no handler in app.js.
    """

    def test_the_html_element_carries_the_configured_theme(self, client, seeded):
        from engineverse import brand

        original = brand.get("theme")
        try:
            brand.set_many({"theme": "light"})
            assert 'data-theme="light"' in client.get("/").text
            brand.set_many({"theme": "dark"})
            assert 'data-theme="dark"' in client.get("/").text
        finally:
            brand.set_many({"theme": original or "dark"})

    def test_the_admin_form_can_change_the_theme(self, app, seeded):
        from starlette.testclient import TestClient

        from engineverse import brand, db

        original = brand.get("theme")
        try:
            client = TestClient(app, raise_server_exceptions=False)
            page = client.get("/login").text
            client.post(
                "/login",
                data={"csrf_token": _csrf(page), "identifier": "admin@engineverse.local",
                      "password": "Str0ngPassphrase#42!", "next": "/"},
                follow_redirects=False,
            )
            admin = client.get("/admin")
            assert 'name="theme"' in admin.text, "the admin form has no theme control"

            response = client.post(
                "/admin/config",
                data={"site_name": "EngineVerse", "theme": "light",
                      "csrf_token": _csrf(admin.text)},
                follow_redirects=False,
            )
            assert response.status_code == 303
            assert db.query_one("SELECT value FROM site_config WHERE key = 'theme'")["value"] == "light"

            # A value that is not a real theme must not reach the page.
            admin = client.get("/admin")
            client.post("/admin/config",
                        data={"site_name": "EngineVerse", "theme": "chartreuse",
                              "csrf_token": _csrf(admin.text)},
                        follow_redirects=False)
            assert db.query_one("SELECT value FROM site_config WHERE key = 'theme'")["value"] == "dark"
        finally:
            brand.set_many({"theme": original or "dark"})

    def test_a_stored_preference_is_restored_before_first_paint(self, client, seeded):
        """Without this the page flashes the default theme for one frame."""
        html = client.get("/").text
        assert 'localStorage.getItem("ev-theme")' in html
        assert 'id="theme-toggle"' in html

    def test_every_data_json_form_attribute_has_a_handler(self, seeded):
        """The attribute implied a handler that did not exist for several commits."""
        import pathlib

        js = (pathlib.Path(__file__).resolve().parents[1] / "static" / "js" / "app.js").read_text()
        assert "form[data-json-form]" in js, "app.js has no data-json-form handler"
        assert "theme-toggle" in js, "app.js has no theme toggle handler"

    def test_json_clients_get_a_destination_and_a_message(self, signed_in):
        """The fetch handler navigates using url and toasts using message."""
        from engineverse import db

        token = _csrf(signed_in.get("/community").text)
        headers = {"Accept": "*/*", "x-csrf-token": token}
        topic = db.query_one("SELECT id FROM topics LIMIT 1")

        created = signed_in.post(
            "/api/community/threads",
            json={"title": "Thread for a JSON reply", "body": "Body text for the post.",
                  "kind": "question"},
            headers=headers,
        )
        thread_id = created.json()["id"]
        assert created.json()["url"] == f"/community/{thread_id}"

        reply = signed_in.post(
            "/api/community/comments",
            json={"threadId": thread_id, "body": "A reply from the fetch handler."},
            headers=headers,
        )
        body = reply.json()
        assert body["url"].startswith(f"/community/{thread_id}#c-"), body
        assert body["message"]

        note = signed_in.post(
            "/api/notes/personal",
            json={"entityType": "topic", "entityId": topic["id"], "content": "A JSON note."},
            headers=headers,
        )
        assert note.json()["message"]

        feedback = signed_in.post(
            "/api/feedback",
            json={"message": "Feedback from the fetch handler.", "path": "/dpp"},
            headers=headers,
        )
        assert feedback.json()["message"]


class TestSearchIndexSelfHeal:
    """The search index is derived data and must not go stale on an upgrade.

    Notes were added to the indexer, but a deployment upgraded in place kept the
    index it already had, so its note content stayed unsearchable until someone
    remembered to reseed. The version marker makes that automatic.
    """

    def test_a_stale_index_is_rebuilt(self, seeded):
        from engineverse import db, search

        original = db.query_one(
            "SELECT value FROM site_config WHERE key = 'search_index_version'"
        )
        db.execute("DELETE FROM search_index")
        db.execute("UPDATE site_config SET value = '0' WHERE key = 'search_index_version'")
        try:
            reindexed = search.refresh_if_stale()
            assert reindexed > 0, "a stale index was not rebuilt"
            assert db.query_one(
                "SELECT count(*) AS c FROM search_index WHERE entity_type = 'note'"
            )["c"] > 0, "notes are still missing from the rebuilt index"
        finally:
            search.refresh_if_stale()
            assert db.query_one(
                "SELECT value AS v FROM site_config WHERE key = 'search_index_version'"
            )["v"] == str(search.INDEX_SCHEMA_VERSION)

    def test_a_current_index_is_left_alone(self, seeded):
        from engineverse import search

        search.refresh_if_stale()
        assert search.refresh_if_stale() == 0, "an up-to-date index was rebuilt needlessly"

    def test_notes_are_searchable(self, seeded):
        from engineverse import search

        search.refresh_if_stale()
        types = {row["type"] for row in search.search("array", limit=10)["results"]}
        assert "note" in types, "a search for a covered concept returns no notes"

    def test_content_added_after_boot_becomes_searchable(self, seeded):
        """docs/CONTENT.md says to extend the catalogue by inserting rows.

        Nothing indexes a row when it is written, and refresh_if_stale() used to
        consult only the schema-version marker, which it writes on first boot. So
        once a process had booted once the marker matched forever and a subject
        added afterwards stayed invisible to global search and to the AI tutor -
        not until a restart, permanently.
        """
        from engineverse import db, search
        from engineverse.security.ids import now_ms, ulid

        search.refresh_if_stale()
        assert search.refresh_if_stale() == 0, "precondition: the index is current"

        subject = db.query_one("SELECT id FROM subjects LIMIT 1")
        topic_id = ulid()
        try:
            db.execute(
                "INSERT INTO topics (id, subject_id, slug, title, summary, status, "
                "difficulty, created_at, updated_at) "
                "VALUES (?,?,?,?,?,'published','intermediate',?,?)",
                topic_id, subject["id"], "zz-reindex-probe-topic",
                "Quantum Tunnelling Rate Probe",
                "How tunnelling probability depends on barrier width and height.",
                now_ms(), now_ms(),
            )
            assert search.refresh_if_stale() > 0, "an inserted topic did not trigger a rebuild"
            titles = [r["title"] for r in search.search("quantum tunnelling probe", limit=5)["results"]]
            assert any("Quantum Tunnelling Rate Probe" in t for t in titles), (
                f"the inserted topic is not searchable: {titles}"
            )
        finally:
            db.execute("DELETE FROM topics WHERE id = ?", topic_id)
            search.refresh_if_stale()

    def test_edited_and_deleted_content_leaves_the_index(self, seeded):
        from engineverse import db, search
        from engineverse.security.ids import now_ms, ulid

        search.refresh_if_stale()
        subject = db.query_one("SELECT id FROM subjects LIMIT 1")
        topic_id = ulid()
        try:
            db.execute(
                "INSERT INTO topics (id, subject_id, slug, title, summary, status, "
                "difficulty, created_at, updated_at) "
                "VALUES (?,?,?,?,?,'published','intermediate',?,?)",
                topic_id, subject["id"], "zz-reindex-probe-two",
                "Tunnelling Probe Two", "probe body", now_ms(), now_ms(),
            )
            search.refresh_if_stale()

            db.execute(
                "UPDATE topics SET title = 'Tunnelling Probe Two Renamed', updated_at = ? "
                "WHERE id = ?", now_ms(), topic_id,
            )
            assert search.refresh_if_stale() > 0, "an edit did not trigger a rebuild"
            titles = [r["title"] for r in search.search("tunnelling probe two", limit=5)["results"]]
            assert any("Renamed" in t for t in titles), f"the edit is not in the index: {titles}"

            db.execute("DELETE FROM topics WHERE id = ?", topic_id)
            assert search.refresh_if_stale() > 0, "a delete did not trigger a rebuild"
            titles = [r["title"] for r in search.search("tunnelling probe two", limit=5)["results"]]
            assert not any("Tunnelling Probe Two" in t for t in titles), (
                f"a deleted topic is still indexed: {titles}"
            )
        finally:
            db.execute("DELETE FROM topics WHERE id = ?", topic_id)
            search.refresh_if_stale()

    def test_a_unchanged_catalogue_is_not_reindexed_on_every_boot(self, seeded):
        """The fingerprint check must not cause a rebuild on every start."""
        from engineverse import search

        search.refresh_if_stale()
        for _ in range(3):
            assert search.refresh_if_stale() == 0, "a rebuild storm: nothing changed"


class TestNoteIndexing:
    """Notes are indexed once per topic, merging every published note it has.

    It used to index one entry per note keyed by the topic slug. index_entity()
    deletes before inserting, so a topic's four notes overwrote each other and
    only the last one read survived - 192 notes produced 48 index rows, and which
    quality level won depended on row order rather than anything a reader could
    rely on.
    """

    def test_reindex_reports_the_number_of_rows_it_actually_wrote(self, seeded):
        from engineverse import db, search

        claimed = search.reindex_all()
        actual = db.row_count("search_index")
        assert claimed == actual, (
            f"reindex_all() claimed {claimed} entities but wrote {actual} rows; "
            "the gap was notes overwriting each other"
        )

    def test_every_published_note_contributes_to_its_topic_entry(self, seeded):
        from engineverse import db, search

        search.reindex_all()
        for topic in db.query(
            "SELECT t.id, t.slug FROM topics t "
            "WHERE EXISTS (SELECT 1 FROM notes n WHERE n.topic_id = t.id AND n.status='published') "
            "LIMIT 12"
        ):
            levels = {
                row["quality_level"]
                for row in db.query(
                    "SELECT quality_level FROM notes WHERE topic_id = ? AND status='published'",
                    topic["id"],
                )
            }
            entry = db.query_one(
                "SELECT body, tags FROM search_index WHERE entity_type='note' AND entity_id=?",
                topic["slug"],
            )
            assert entry, f"topic {topic['slug']} has published notes but no index entry"
            assert levels <= set(entry["tags"].split()), (
                f"topic {topic['slug']}: indexed tags {entry['tags']!r} are missing {sorted(levels)}"
            )

    def test_one_entry_per_topic_so_a_search_does_not_repeat_itself(self, seeded):
        from engineverse import db, search

        search.reindex_all()
        dupes = db.query(
            "SELECT entity_id, count(*) AS c FROM search_index WHERE entity_type='note' "
            "GROUP BY entity_id HAVING c > 1"
        )
        assert not dupes, f"note results are keyed by topic but appear more than once: {dupes}"

    def test_note_bodies_are_not_truncated_away(self, seeded):
        """The 4000-character cap cut 47 of 48 topics and kept 71% of the prose."""
        from engineverse import db, search

        search.reindex_all()
        truncated = db.query_one(
            "SELECT count(*) AS c FROM search_index "
            "WHERE entity_type='note' AND length(body) >= ?", search.MAX_BODY_CHARS,
        )["c"]
        assert truncated == 0, (
            f"{truncated} note entries hit the {search.MAX_BODY_CHARS}-character cap; "
            "raise it or the tail of those notes is unsearchable"
        )


class TestLanguagePickerMatchesTheJudge:
    """Every language the editor offers must be one the judge can actually run.

    seed.py hard-coded runnable = 1 for every row, so SQL appeared in the code
    editor's language picker looking exactly like Python or C, and pressing Run
    returned "unsupported_language". The seed data already carried judge_slug =
    None for SQL - the honest signal was there and being discarded.
    """

    def test_the_runnable_flag_matches_the_judges_runners(self, seeded):
        from engineverse import db
        from engineverse.judge import local as judge_local

        for row in db.query("SELECT slug, judge_slug, runnable FROM programming_languages"):
            can_run = row["judge_slug"] in judge_local.RUNNERS
            assert bool(row["runnable"]) == can_run, (
                f"{row['slug']}: advertised runnable={row['runnable']} but the judge "
                f"{'can' if can_run else 'cannot'} run judge_slug={row['judge_slug']!r}"
            )

    def test_the_editor_labels_a_language_it_cannot_run(self, seeded):
        from engineverse import coding, db

        languages = coding.list_languages()
        unrunnable = [l for l in languages if not l["runnable"]]
        assert unrunnable, "expected at least one non-runnable language in the seed"
        for language in unrunnable:
            row = db.query_one(
                "SELECT judge_slug FROM programming_languages WHERE slug = ?", language["slug"]
            )
            assert not row["judge_slug"], (
                f"{language['slug']} is marked non-runnable but has judge_slug="
                f"{row['judge_slug']!r}"
            )


class TestEditorOffersOnlyWhatTheHostCanRun:
    """The picker must reflect this machine, not just what the catalogue claims.

    The database `runnable` flag is a property of the content; a missing JVM is a
    property of the host. `judge.runnable_languages()` already probed the real
    toolchain and `/api/coding/languages` already returned it, but the editor page
    passed only the static flag - so Java was offered and selectable on a machine
    with no javac, and Run returned "unsupported_language". Same dead button as
    SQL, different cause.
    """

    def test_the_page_marks_a_language_the_host_cannot_run(self, seeded, client):
        import re

        from engineverse import judge

        runnable = set(judge.runnable_languages())
        response = client.get("/practice/problems/binary-search")
        assert response.status_code == 200
        options = re.findall(
            r'<option value="([a-z+]+)"([^>]*)>(.*?)</option>', response.text, re.S
        )
        assert options, "the editor rendered no language options"
        for slug, attrs, label in options:
            label = " ".join(label.split())
            if slug in runnable:
                assert "disabled" not in attrs, f"{slug} can run but is disabled"
                assert "(no runtime here)" not in label, f"{slug} can run but says it cannot"
            else:
                assert "disabled" in attrs, (
                    f"{slug} cannot run on this host but is selectable"
                )
                assert "(no runtime here)" in label, (
                    f"{slug} cannot run on this host but is not labelled"
                )

    def test_the_picker_and_the_api_agree(self, seeded, client):
        import re

        from engineverse import judge

        runnable = set(judge.runnable_languages())
        html = client.get("/practice/problems/binary-search").text
        selectable = {
            slug
            for slug, attrs, _ in re.findall(
                r'<option value="([a-z+]+)"([^>]*)>(.*?)</option>', html, re.S
            )
            if "disabled" not in attrs
        }
        offered = {
            slug for slug, _, _ in re.findall(
                r'<option value="([a-z+]+)"([^>]*)>(.*?)</option>', html, re.S
            )
        }
        assert selectable == runnable & offered, (
            f"the page lets you pick {sorted(selectable)} but the judge can run "
            f"{sorted(runnable & offered)}"
        )


class TestNoDeadLinks:
    """Every internal URL a template or the client script points at must exist.

    "No fake buttons" is a stated requirement, and a link to a route that was
    renamed or never written is the quietest way to break it: the page renders,
    the control looks live, and clicking it lands on a 404.
    """

    @staticmethod
    def _registered_routes():
        from main import create_app

        routes = set()
        for route in create_app().routes:
            if type(route).__name__ == "_IncludedRouter":
                prefix = route.include_context.prefix or ""
                for sub in route.original_router.routes:
                    routes.add(prefix + getattr(sub, "path", ""))
            elif hasattr(route, "path"):
                routes.add(route.path)
        return routes

    @staticmethod
    def _matches(url, routes):
        parts = url.strip("/").split("/")
        for route in routes:
            segments = route.strip("/").split("/")
            if len(segments) != len(parts):
                continue
            if all(
                a == b or a.startswith("{") or b == "*"
                for a, b in zip(segments, parts)
            ):
                return True
        return False

    def test_every_referenced_internal_url_resolves(self):
        import pathlib
        import re

        routes = self._registered_routes()
        assert len(routes) > 50, f"route enumeration looks broken: {len(routes)}"

        sources = list(pathlib.Path("backend/templates").rglob("*.html"))
        sources.append(pathlib.Path("backend/static/js/app.js"))
        referenced = {}
        for source in sources:
            for match in re.finditer(
                r'(?:href|action|fetch)\s*[=(]\s*["\'`]([^"\'`]+)["\'`]', source.read_text()
            ):
                url = match.group(1)
                if not url.startswith("/") or url.startswith("//"):
                    continue
                # A complete `{{ ... }}` becomes a wildcard segment. An
                # unterminated one means the regex stopped at a quote inside the
                # expression - `/register{{ '?next=' + next ... }}` - so cut
                # there and treat the remainder as dynamic.
                url = re.sub(r"\{\{.*?\}\}", "*", url)
                url = url.split("{{")[0]
                url = re.sub(r"\$\{[^}]*\}", "*", url)
                url = url.split("?")[0].split("#")[0].rstrip("/") or "/"
                referenced.setdefault(url, set()).add(source.name)

        static = {u for u in referenced if u.startswith("/static/")}
        dead = {
            u: sorted(f) for u, f in referenced.items()
            if u not in static and not self._matches(u, routes)
        }
        assert not dead, f"these internal URLs match no route: {dead}"

    def test_static_assets_actually_serve(self, client):
        for path in ("/static/css/app.css", "/static/js/app.js",
                     "/static/icons/icon-192.png", "/static/icons/favicon.svg"):
            response = client.get(path)
            assert response.status_code == 200, f"{path} -> {response.status_code}"


class TestDeployTopologyIsCoherent:
    """The compose file must describe a topology that can actually run.

    It used to define a `sandbox` container hardened with network_mode "none"
    that nothing could reach: the bridge invokes the sandbox with subprocess.run,
    which cannot cross a container boundary, and the service had no network and
    no published port. Its ENTRYPOINT read stdin, so with none attached it exited
    at once and restart: unless-stopped looped it forever. The hardening flags
    read as a security guarantee that was never in force.
    """

    def test_compose_defines_only_reachable_services(self):
        import pathlib

        import yaml

        compose = yaml.safe_load(
            pathlib.Path("deploy/docker-compose.yml").read_text(encoding="utf-8")
        )
        assert set(compose["services"]) == {"web", "db"}, (
            f"unexpected services: {sorted(compose['services'])}"
        )

    def test_the_jar_path_the_app_is_given_actually_exists_in_the_image(self):
        """JAVA_SANDBOX_JAR pointed at a file Dockerfile.web never created."""
        import pathlib
        import re

        import yaml

        compose = yaml.safe_load(
            pathlib.Path("deploy/docker-compose.yml").read_text(encoding="utf-8")
        )
        jar = compose["services"]["web"]["environment"]["JAVA_SANDBOX_JAR"]
        dockerfile = pathlib.Path("deploy/Dockerfile.web").read_text(encoding="utf-8")
        assert re.search(rf"COPY\s+--from=\S+\s+\S+\s+{re.escape(jar)}\b", dockerfile), (
            f"compose sets JAVA_SANDBOX_JAR={jar} but Dockerfile.web never copies a jar there"
        )

    def test_the_web_image_provides_the_toolchains_the_judge_invokes(self):
        """The bridge calls java, gcc and python3 as subprocesses.

        Matched against the package list rather than the whole file, so a word
        appearing only in a comment does not satisfy it. Tokens are compared
        whole rather than with \\b anchors, because `g++` ends in a non-word
        character and \\b never matches after it.
        """
        import pathlib

        dockerfile = pathlib.Path("deploy/Dockerfile.web").read_text(encoding="utf-8")
        tokens = {
            tok
            for line in dockerfile.splitlines()
            if "apt-get install" in line
            for tok in line.replace("\\", " ").split()
        }
        for toolchain in ("gcc", "g++", "openjdk-21-jdk-headless"):
            assert toolchain in tokens, (
                f"the judge needs {toolchain} in the web image and it is not installed"
            )

    def test_the_web_image_ships_a_jdk_not_a_jre(self):
        """The judge compiles Java with javac before it runs.

        A JRE has no compiler, so openjdk-21-jre-headless would have made Java the
        same dead option SQL was - listed in the editor's picker, failing on Run.
        """
        import pathlib

        dockerfile = pathlib.Path("deploy/Dockerfile.web").read_text(encoding="utf-8")
        assert "openjdk" in dockerfile and "jdk" in dockerfile, "no JDK is installed"
        assert "-jre-headless" not in dockerfile, (
            "a JRE is installed but the judge needs javac to compile submissions"
        )

    def test_no_comment_breaks_a_dockerfile_line_continuation(self):
        """A comment inside a `\`-continued RUN silently ends the instruction.

        Everything after it stops being part of the command, so the image builds
        without the steps that were meant to run.
        """
        import pathlib
        import re

        for name in ("deploy/Dockerfile.web", "deploy/Dockerfile.sandbox"):
            in_continuation = False
            for lineno, raw in enumerate(
                pathlib.Path(name).read_text(encoding="utf-8").splitlines(), 1
            ):
                line = raw.strip()
                if in_continuation:
                    assert not (line.startswith("#") and not line.endswith("\\")), (
                        f"{name}:{lineno} - a comment terminates a continued instruction"
                    )
                    if not line.endswith("\\"):
                        in_continuation = False
                elif re.match(r"^(RUN|COPY|ENV|ARG)\b", line) and line.endswith("\\"):
                    in_continuation = True

    def test_the_judge_can_write_when_the_root_filesystem_is_read_only(self):
        import pathlib

        import yaml

        compose = yaml.safe_load(
            pathlib.Path("deploy/docker-compose.yml").read_text(encoding="utf-8")
        )
        web = compose["services"]["web"]
        assert web.get("read_only") is True
        # tempfile.mkdtemp() defaults to /tmp, so that is the path that must be
        # writable or every submission fails to get a work directory.
        assert any(mount.startswith("/tmp") for mount in web.get("tmpfs", [])), (
            "read_only root with no writable /tmp would break the judge"
        )
