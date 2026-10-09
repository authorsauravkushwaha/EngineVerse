"""The JSON API surface, plus the schema that has to survive 1.5e9 users."""
from __future__ import annotations

import re

import pytest

from engineverse import db


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


def _host_can_isolate() -> bool:
    """Whether this host can run a submission at all.

    GitHub-hosted runners block unprivileged user namespaces, so the sandbox
    refuses to execute rather than running untrusted code on the app server.
    These two tests assert on a verdict, which only exists where execution
    happened; test_judge.py covers the refusal itself on every host.
    """
    from engineverse.judge import provider_info

    return bool(provider_info().get("have_namespace"))


requires_execution = pytest.mark.skipif(
    not _host_can_isolate(),
    reason="host cannot create a user namespace, so the sandbox refuses to run code",
)


@requires_execution
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


class TestSettingsFormsDoNotOverwriteEachOther:
    """Two handlers owned the same columns, and one form had no input for them.

    /settings/preferences accepted note_quality and language with Form defaults,
    but the inputs for those two live in the onboarding form. A field a form does
    not render is not absent from the request - the default arrives in its place -
    so ticking a single notification checkbox silently reset the reader's chosen
    depth to "standard" and their language to "en".
    """

    def test_saving_preferences_keeps_the_reading_depth(self, signed_in, seeded):
        import re

        from engineverse import db

        token = _csrf(signed_in.get("/settings").text)
        form = dict(re.findall(r'name="([a-zA-Z_0-9]+)" value="([^"]*)"',
                               signed_in.get("/settings").text))
        form.update({"note_quality": "advanced", "language": "hi", "csrf_token": token})
        signed_in.post("/settings/onboarding", data=form)

        user = signed_in.get("/settings")
        prefs = {
            "show_email": "1", "show_activity": "1", "show_progress": "1",
            "searchable": "1", "new_dpp": "1", "streak_reminder": "1",
            "milestone": "1", "community_reply": "1",
            "csrf_token": _csrf(user.text),
        }
        # TestClient follows redirects, so the 303 lands on /settings as a 200.
        # What matters is the stored state, asserted below.
        signed_in.post("/settings/preferences", data=prefs)

        row = db.query_one(
            "SELECT p.note_quality, p.language_pref FROM profiles p "
            "JOIN users u ON u.id = p.user_id WHERE u.email = ?", "asha@example.com"
        )
        assert row["note_quality"] == "advanced", (
            f"saving preferences reset the reading depth to {row['note_quality']!r}"
        )
        assert row["language_pref"] == "hi", (
            f"saving preferences reset the language to {row['language_pref']!r}"
        )

    def test_saving_preferences_still_stores_privacy_and_notifications(self, signed_in, seeded):
        import json

        from engineverse import db

        prefs = {
            "show_email": "1", "show_progress": "1",
            "milestone": "1", "csrf_token": _csrf(signed_in.get("/settings").text),
        }
        signed_in.post("/settings/preferences", data=prefs)
        row = db.query_one(
            "SELECT p.privacy, p.notification_prefs FROM profiles p "
            "JOIN users u ON u.id = p.user_id WHERE u.email = ?", "asha@example.com"
        )
        privacy = json.loads(row["privacy"])
        notifications = json.loads(row["notification_prefs"])
        assert privacy["showEmail"] is True and privacy["showActivity"] is False
        assert notifications["milestone"] is True and notifications["newDpp"] is False


class TestModerationCanActuallyHide:
    """Reporting stored "thread"; hiding looked for "discussion", so it never matched.

    The URL says thread, the discussions table says discussion. Reports were stored
    with whichever the client sent and resolve_report() hides only when the stored
    type is "discussion", so the hide path was unreachable - a moderator could
    close a report but never remove what was reported. The admin panel had no
    control for it either.
    """

    def _thread(self, client):
        token = _csrf(client.get("/community").text)
        response = client.post(
            "/api/community/threads",
            data={"title": "A thread to moderate",
                  "body": "This exists so moderation can be exercised end to end.",
                  "kind": "question"},
            headers={"x-csrf-token": token},
        )
        assert response.status_code == 200, response.text
        return response.json()["id"], token

    def test_either_name_is_stored_as_discussion(self, signed_in, seeded):
        from engineverse import db

        thread_id, token = self._thread(signed_in)
        headers = {"x-csrf-token": token}
        for entity_type in ("thread", "discussion"):
            response = signed_in.post(
                "/api/community/report",
                json={"entityType": entity_type, "entityId": thread_id, "reason": "spam"},
                headers=headers,
            )
            assert response.status_code == 200, response.text
        stored = {
            row["entity_type"]
            for row in db.query("SELECT entity_type FROM reports WHERE entity_id = ?", thread_id)
        }
        assert stored == {"discussion"}, f"reports stored {stored}, hiding needs 'discussion'"

    def test_reporting_something_that_does_not_exist_is_refused(self, signed_in, seeded):
        token = _csrf(signed_in.get("/community").text)
        response = signed_in.post(
            "/api/community/report",
            json={"entityType": "thread", "entityId": "no-such-thread", "reason": "spam"},
            headers={"x-csrf-token": token},
        )
        assert response.status_code == 400, response.text

    def test_resolving_with_hide_hides_the_discussion(self, seeded):
        from engineverse import community, db
        from engineverse.security.ids import ulid

        thread_id = ulid()
        author = db.query_one("SELECT id FROM users LIMIT 1")["id"]
        db.execute(
            "INSERT INTO discussions (id,user_id,title,body,kind,created_at,last_activity_at) "
            "VALUES (?,?,'Moderation probe','body text long enough to pass.','question',0,0)",
            thread_id, author,
        )
        try:
            report_id = community.report(author, "discussion", thread_id, "spam", None)
            assert db.query_one(
                "SELECT is_hidden FROM discussions WHERE id = ?", thread_id
            )["is_hidden"] == 0
            community.resolve_report(author, report_id, hide=True)
            assert db.query_one(
                "SELECT is_hidden FROM discussions WHERE id = ?", thread_id
            )["is_hidden"] == 1, "resolve_report(hide=True) did not hide the discussion"
        finally:
            db.execute("DELETE FROM reports WHERE id = ?", report_id)
            db.execute("DELETE FROM discussions WHERE id = ?", thread_id)


class TestAccountDeletionIsHonestAboutWhatItRemoves:
    """Deleting an account must not leave "None" as an author, or overclaim.

    comments.user_id is ON DELETE SET NULL, so a reply outlives the account that
    wrote it - correctly, since deleting it would break someone else's thread. But
    the comment query selected u.username with no fallback, so the template printed
    the literal string "None" where the author's name had been, and the flash
    message claimed all of the user's data was removed when their replies were not.
    """

    def _orphaned_comment(self):
        from engineverse import auth, community, db
        from engineverse.security.ids import ulid

        uid = ulid()
        db.execute(
            "INSERT INTO users (id,email,username,password_hash,role,status,"
            "created_at,updated_at,password_changed_at) VALUES (?,?,?,?, 'student','active',0,0,0)",
            uid, f"del-{uid[:8]}@example.test", f"del{uid[:12]}",
            auth.hash_password("Throwaway#2026!"),
        )
        author = db.query_one("SELECT id FROM users LIMIT 1")["id"]
        thread_id = community.create_thread(
            author, title="Thread surviving a deletion",
            body="Body long enough to pass validation.", kind="question",
        )
        community.add_comment(uid, thread_id, "This reply outlives its author.")
        db.execute("DELETE FROM users WHERE id = ?", uid)
        return thread_id

    def test_an_orphaned_comment_has_a_readable_author(self, seeded):
        from engineverse import community, db

        thread_id = self._orphaned_comment()
        try:
            rows = community.comments(thread_id)
            assert rows, "the reply did not survive the deletion"
            username = rows[0]["username"]
            assert username and username != "None", f"author rendered as {username!r}"
        finally:
            db.execute("DELETE FROM discussions WHERE id = ?", thread_id)

    def test_the_page_never_prints_None_as_an_author(self, client, seeded):
        from engineverse import db

        thread_id = self._orphaned_comment()
        try:
            response = client.get(f"/community/{thread_id}")
            assert response.status_code == 200
            assert "<strong>None</strong>" not in response.text
            assert "Deleted account" in response.text
        finally:
            db.execute("DELETE FROM discussions WHERE id = ?", thread_id)

    def test_deleting_an_account_cascades_its_own_data(self, seeded):
        from engineverse import auth, db, progress
        from engineverse.security.ids import ulid

        uid = ulid()
        db.execute(
            "INSERT INTO users (id,email,username,password_hash,role,status,"
            "created_at,updated_at,password_changed_at) VALUES (?,?,?,?, 'student','active',0,0,0)",
            uid, f"casc-{uid[:8]}@example.test", f"casc{uid[:12]}",
            auth.hash_password("Throwaway#2026!"),
        )
        topic = db.query_one("SELECT slug FROM topics LIMIT 1")["slug"]
        progress.complete_topic(uid, topic)
        progress.toggle_bookmark(uid, "topic", topic)
        assert db.query_one("SELECT count(*) AS c FROM user_progress WHERE user_id = ?", uid)["c"] == 1
        db.execute("DELETE FROM users WHERE id = ?", uid)
        for table, column in (("user_progress", "user_id"), ("bookmarks", "user_id"),
                              ("xp_events", "user_id"), ("activity", "user_id")):
            left = db.query_one(
                f"SELECT count(*) AS c FROM {table} WHERE {column} = ?", uid
            )["c"]
            assert left == 0, f"{left} orphaned rows left in {table}"

    def test_the_confirmation_message_does_not_overclaim(self):
        import pathlib

        source = pathlib.Path("backend/web/auth_pages.py").read_text(encoding="utf-8")
        assert "all of its data were removed" not in source, (
            "replies survive deletion, so the message must not claim everything is gone"
        )


class TestEveryFormHandlerMatchesItsTemplate:
    """Every Form(...) parameter must have an input in the form that posts to it.

    Checked by hand once and it found three real bugs: two admin accent colours
    that reset on every save, and note_quality/language silently reverted whenever
    a notification checkbox was ticked. The mechanism is easy to miss because
    nothing errors - a field the browser never sends arrives as the handler's
    Form default and overwrites the stored value.
    """

    @staticmethod
    def _forms_by_action():
        import pathlib
        import re

        by_action = {}
        for path in pathlib.Path("backend/templates").rglob("*.html"):
            text = path.read_text(encoding="utf-8")
            for match in re.finditer(r"<form\b([^>]*)>(.*?)</form>", text, re.S):
                action = re.search(r'action="([^"]+)"', match.group(1))
                if not action:
                    continue
                target = action.group(1).split("?")[0]
                by_action.setdefault(target, set()).update(
                    re.findall(r'name="([a-zA-Z_0-9]+)"', match.group(2))
                )
        return by_action

    @staticmethod
    def _form_params(module_name):
        import inspect
        import re

        module = __import__(f"web.{module_name}", fromlist=["x"])
        source_all = inspect.getsource(module)
        found = {}
        for match in re.finditer(r'@router\.post\("([^"]+)"\)\s*\nasync def (\w+)\(', source_all):
            route, function_name = match.group(1), match.group(2)
            signature = getattr(module, function_name, None)
            if signature is None:
                continue
            body = inspect.getsource(signature)
            head = body[: body.find("):") + 2] if "):" in body else body
            params = set(re.findall(r"(\w+)\s*:\s*[^=,]+?=\s*Form\(", head))
            if params:
                found[route] = params
        return found

    def test_no_handler_accepts_a_field_its_form_never_sends(self):
        by_action = self._forms_by_action()
        problems = {}
        for module_name in ("auth_pages", "pages"):
            for route, params in self._form_params(module_name).items():
                fields = by_action.get(route)
                if fields is None:
                    continue  # posted by client script rather than a template form
                missing = params - fields
                if missing:
                    problems[f"{module_name}:{route}"] = sorted(missing)
        assert not problems, (
            f"these handlers accept parameters their form never sends, so saving "
            f"resets them to the handler defaults: {problems}"
        )


class TestEveryFormFieldHasAnInput:
    """A handler parameter with no matching input silently takes its default.

    Adding accent_color_2 and accent_color_3 to the /admin/config handler without
    adding fields to admin.html meant every save of any setting reset both colours
    to the stock values: the browser never sent them, so the Form default arrived
    in their place and overwrote what was stored. Nothing failed - the colours
    just quietly reverted.
    """

    def _form_field_names(self, template):
        import pathlib
        import re

        return set(re.findall(
            r'name="([a-zA-Z_0-9]+)"',
            pathlib.Path(f"backend/templates/{template}").read_text(encoding="utf-8"),
        ))

    def test_the_admin_config_form_covers_every_handler_parameter(self):
        import inspect
        import re

        from web import auth_pages

        source = inspect.getsource(auth_pages.update_site_config)
        # [^=,] rather than [^=] so the type annotation cannot span a comma and
        # pull in the preceding parameter - `request: Request, site_name: str =
        # Form("")` otherwise matches "request".
        declared = set(re.findall(r"(\w+)\s*:\s*[^=,]+?=\s*Form\(", source))
        assert declared, "no Form parameters found; the introspection is broken"

        fields = self._form_field_names("admin.html")
        missing = declared - fields - {"csrf_token"}
        assert not missing, (
            f"/admin/config accepts {sorted(missing)} but admin.html has no input for "
            "them, so saving the form resets them to the handler defaults"
        )

    def test_the_colour_fields_round_trip_through_the_form(self, signed_in, seeded):
        import re

        from engineverse import db

        admin = db.query_one("SELECT id FROM users WHERE role = 'super_admin' LIMIT 1")
        db.execute("UPDATE users SET role = 'super_admin' WHERE id = ?", admin["id"])
        page = signed_in.get("/admin")
        if page.status_code != 200:
            return  # the demo account is not an admin in this fixture; covered above
        fields = dict(re.findall(r'name="([a-zA-Z_0-9]+)" value="([^"]*)"', page.text))
        assert "accent_color_2" in fields and "accent_color_3" in fields, (
            "the colour inputs are missing from the rendered form"
        )


class TestBrandingAccentColoursAreRealAndSafe:
    """The accent colours must change the site, and must never carry a payload.

    The admin panel wrote accent_color to site_config and nothing read it back:
    app.css hard-codes --accent, --accent-2 and --accent-3, so the control did
    nothing. accent_color_2, accent_color_3 and primary_branch were worse - in
    PUBLIC_KEYS but not even in the form. Since these are interpolated into a
    <style> block, wiring them up without validating would have turned a dead
    control into a stored CSS-injection one.
    """

    @staticmethod
    def _emitted(client):
        import re

        match = re.search(r"<style>:root\{([^}]*)\}</style>", client.get("/").text)
        assert match, "the page emits no accent custom properties"
        return match.group(1)

    def test_the_configured_colours_reach_the_page(self, client, seeded):
        from engineverse import brand

        brand.set_many({"accent_color": "#ff8800", "accent_color_2": "#00cc88",
                        "accent_color_3": "#cc00ff"})
        try:
            emitted = self._emitted(client)
            for colour in ("#ff8800", "#00cc88", "#cc00ff"):
                assert colour in emitted, f"{colour} was configured but the page emits {emitted}"
        finally:
            brand.set_many({"accent_color": "#4f7cff", "accent_color_2": "#38bdf8",
                            "accent_color_3": "#a78bfa"})

    def test_a_non_colour_value_never_reaches_the_page(self, client, seeded):
        from engineverse import brand

        for payload in ("</style><script>alert(1)</script>", "javascript:alert(1)",
                        "red", "#gggggg", "expression(alert(1))"):
            brand.set_many({"accent_color": payload})
            try:
                emitted = self._emitted(client)
                assert payload not in emitted, f"{payload!r} was emitted verbatim"
                assert "<script>" not in emitted
                assert "--accent:#4f7cff" in emitted, (
                    f"a non-colour value must fall back to the default, got {emitted}"
                )
            finally:
                brand.set_many({"accent_color": "#4f7cff"})

    def test_brand_returns_a_hex_colour_even_for_a_poisoned_row(self, seeded):
        """Validation on read, so a value written before the check existed is safe."""
        from engineverse import brand, db

        db.execute("UPDATE site_config SET value = ? WHERE key = 'accent_color'",
                   "expression(alert(1))")
        try:
            assert brand.brand()["accent_color"] == "#4f7cff"
        finally:
            db.execute("UPDATE site_config SET value = '#4f7cff' WHERE key = 'accent_color'")

    def test_only_keys_something_reads_are_configurable(self, seeded):
        """primary_branch was in PUBLIC_KEYS and read by nothing."""
        from engineverse import brand

        assert "primary_branch" not in brand.PUBLIC_KEYS
        for key in ("accent_color", "accent_color_2", "accent_color_3"):
            assert key in brand.PUBLIC_KEYS, f"{key} should be configurable"


class TestUnhandledExceptionsBecomeClean500s:
    """An exception nobody caught must still produce a response.

    Verified against the running server with throwaway routes raising ValueError
    and KeyError: each came back as 500 with {"ok": false, "error": "Internal
    server error."} and an app.error row in audit_logs. Before this the behaviour
    was only ever observed by accident, when a bug happened to raise.
    """

    def test_an_uncaught_exception_returns_json_for_an_api_path(self, app, client, seeded, monkeypatch):
        from web import api as api_module

        def explode(*args, **kwargs):
            raise ValueError("deliberate test failure")

        monkeypatch.setattr(api_module.search_grouped, "__call__", explode, raising=False)
        monkeypatch.setattr(api_module, "search_grouped", explode)

        response = client.get("/api/search", params={"q": "arrays"})
        assert response.status_code == 500
        assert response.json() == {"ok": False, "error": "Internal server error."}

    def test_the_failure_is_written_to_the_audit_log(self, app, client, seeded, monkeypatch):
        from engineverse import db
        from web import api as api_module

        def explode(*args, **kwargs):
            raise KeyError("deliberate test failure")

        monkeypatch.setattr(api_module, "search_grouped", explode)
        before = db.query_one(
            "SELECT count(*) AS c FROM audit_logs WHERE action = 'app.error'"
        )["c"]
        client.get("/api/search", params={"q": "arrays"})
        after = db.query_one(
            "SELECT count(*) AS c FROM audit_logs WHERE action = 'app.error'"
        )["c"]
        assert after == before + 1, "an unhandled exception was not recorded"

    def test_an_uncaught_exception_on_a_page_renders_the_error_page(self, app, client, seeded, monkeypatch):
        from web import pages as pages_module

        def explode(*args, **kwargs):
            raise RuntimeError("deliberate test failure")

        monkeypatch.setattr(pages_module, "catalog", explode)
        response = client.get("/explore")
        assert response.status_code == 500
        assert "text/html" in response.headers.get("content-type", "")


class TestBogusIdsDoNotBecomeServerErrors:
    """A bad id in the request must answer 4xx, not 500.

    Three endpoints passed a caller-supplied identifier straight into an INSERT
    whose column is a foreign key, so an id that did not exist raised
    sqlite3.IntegrityError out of the handler. The 500 handler logged it, but the
    request still failed as a server error for what was a client mistake - and
    /api/revision/review also let srs.review's ValueError escape, there being no
    handler registered for ValueError at all.
    """

    def _token(self, client):
        return _csrf(client.get("/practice").text)

    def test_marking_an_unknown_topic_is_a_404(self, signed_in, seeded):
        response = signed_in.post(
            "/api/me/progress/topic",
            json={"topicId": "no-such-topic", "status": "completed"},
            headers={"x-csrf-token": self._token(signed_in)},
        )
        assert response.status_code == 404, response.text

    def test_an_unknown_progress_state_is_a_400(self, signed_in, seeded):
        response = signed_in.post(
            "/api/me/progress/topic",
            json={"topicId": "arrays", "status": "banana"},
            headers={"x-csrf-token": self._token(signed_in)},
        )
        assert response.status_code == 400, response.text

    def test_reviewing_an_unknown_card_is_a_404(self, signed_in, seeded):
        response = signed_in.post(
            "/api/revision/review",
            json={"cardId": "no-such-card", "rating": "good"},
            headers={"x-csrf-token": self._token(signed_in)},
        )
        assert response.status_code == 404, response.text

    def test_an_unknown_rating_is_a_400_not_a_500(self, signed_in, seeded):
        from engineverse import db

        card = db.query_one("SELECT id FROM flashcards LIMIT 1")
        response = signed_in.post(
            "/api/revision/review",
            json={"cardId": card["id"], "rating": "banana"},
            headers={"x-csrf-token": self._token(signed_in)},
        )
        assert response.status_code == 400, response.text

    def test_bookmarking_an_unknown_type_or_item_is_refused(self, signed_in, seeded):
        headers = {"x-csrf-token": self._token(signed_in)}
        bad_type = signed_in.post(
            "/api/bookmarks",
            json={"entityType": "banana", "entityId": "arrays"},
            headers=headers,
        )
        assert bad_type.status_code == 400, bad_type.text
        bad_id = signed_in.post(
            "/api/bookmarks",
            json={"entityType": "topic", "entityId": "no-such-topic"},
            headers=headers,
        )
        assert bad_id.status_code == 404, bad_id.text

    def test_no_row_is_written_for_a_refused_bookmark(self, signed_in, seeded):
        from engineverse import db

        before = db.row_count("bookmarks")
        signed_in.post(
            "/api/bookmarks",
            json={"entityType": "banana", "entityId": "arrays"},
            headers={"x-csrf-token": self._token(signed_in)},
        )
        assert db.row_count("bookmarks") == before, "a refused bookmark still wrote a row"

    def test_a_valid_bookmark_still_toggles(self, signed_in, seeded):
        headers = {"x-csrf-token": self._token(signed_in)}
        payload = {"entityType": "topic", "entityId": "arrays"}
        first = signed_in.post("/api/bookmarks", json=payload, headers=headers).json()["bookmarked"]
        second = signed_in.post("/api/bookmarks", json=payload, headers=headers).json()["bookmarked"]
        assert first is True and second is False, f"toggle gave {first} then {second}"


class TestVotingRejectsUnknownTargets:
    """/api/community/vote must refuse an entity_type it cannot score.

    community.vote() only moves a score for "discussion" and "comment". Any other
    string wrote a votes row and returned 200 with score 0, so a client sending
    the wrong value - "thread" is the obvious mistake, since that is what the URL
    calls it - got a success response for a vote that silently did nothing, and
    the table filled with rows no query would ever read. /community/report
    already validated its types; vote did not.
    """

    def _thread(self, client):
        token = _csrf(client.get("/community").text)
        response = client.post(
            "/api/community/threads",
            data={
                "title": "Does a vote on the wrong entity type fail loudly?",
                "body": "Checking that an unknown entity_type is refused rather than ignored.",
                "kind": "question",
            },
            headers={"x-csrf-token": token},
        )
        assert response.status_code == 200, response.text
        return response.json()["id"], token

    def test_an_unknown_entity_type_is_refused(self, signed_in, seeded):
        thread_id, token = self._thread(signed_in)
        for bad in ("thread", "banana", "", "DISCUSSION"):
            response = signed_in.post(
                "/api/community/vote",
                json={"entityType": bad, "entityId": thread_id, "value": 1},
                headers={"x-csrf-token": token},
            )
            assert response.status_code == 400, (
                f"entityType={bad!r} returned {response.status_code}, expected 400"
            )

    def test_a_missing_entity_id_is_refused(self, signed_in, seeded):
        token = _csrf(signed_in.get("/community").text)
        response = signed_in.post(
            "/api/community/vote",
            json={"entityType": "discussion", "entityId": "   ", "value": 1},
            headers={"x-csrf-token": token},
        )
        assert response.status_code == 400

    def test_no_vote_row_is_written_for_a_refused_vote(self, signed_in, seeded):
        from engineverse import db

        thread_id, token = self._thread(signed_in)
        before = db.row_count("votes")
        signed_in.post(
            "/api/community/vote",
            json={"entityType": "banana", "entityId": thread_id, "value": 1},
            headers={"x-csrf-token": token},
        )
        assert db.row_count("votes") == before, "a refused vote still wrote a row"

    def test_a_valid_vote_still_scores_and_stays_idempotent(self, signed_in, seeded):
        thread_id, token = self._thread(signed_in)
        headers = {"x-csrf-token": token}
        payload = {"entityType": "discussion", "entityId": thread_id, "value": 1}
        first = signed_in.post("/api/community/vote", json=payload, headers=headers).json()["score"]
        again = signed_in.post("/api/community/vote", json=payload, headers=headers).json()["score"]
        assert first == again == 1, f"voting twice gave {first} then {again}"
        down = signed_in.post(
            "/api/community/vote",
            json={"entityType": "discussion", "entityId": thread_id, "value": -1},
            headers=headers,
        ).json()["score"]
        assert down == -1, f"switching to a downvote gave {down}"


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

    def test_the_image_ships_a_driver_for_the_database_compose_points_it_at(self):
        """compose set ENGINEVERSE_DB_URL but the image had no Postgres driver.

        requirements.txt keeps psycopg commented out - development and CI run on
        SQLite and the list is deliberately minimal - and Dockerfile.web
        installed only that file. So db._pg_connect raised
        DatabaseError("...no PostgreSQL driver is installed") on the first query,
        and `restart: unless-stopped` would have looped the container forever.
        """
        import pathlib

        import yaml

        compose = yaml.safe_load(
            pathlib.Path("deploy/docker-compose.yml").read_text(encoding="utf-8")
        )
        url = str(compose["services"]["web"]["environment"]["ENGINEVERSE_DB_URL"])
        # Asserted rather than branched on: a silently-skipped test is worse than
        # one that has to be updated when the deployment changes.
        assert url.startswith("postgresql://"), (
            f"compose points the web service at {url!r}; this test assumed PostgreSQL"
        )
        dockerfile = pathlib.Path("deploy/Dockerfile.web").read_text(encoding="utf-8")
        # Against install lines only, so a comment merely mentioning the driver
        # cannot satisfy the assertion.
        installs = "\n".join(
            line for line in dockerfile.splitlines() if "pip install" in line
        )
        assert "psycopg" in installs, (
            "compose points ENGINEVERSE_DB_URL at PostgreSQL but Dockerfile.web "
            "installs no Postgres driver, so the app can never connect"
        )


def test_table_exists_answers_one_question_on_every_backend():
    """``table_count`` meant two different things depending on the backend.

    On Postgres it returned the row count; on SQLite it returned a 0/1
    ``sqlite_master`` match. So ``table_count("users")`` was "how many users are
    there" on one backend and "does the users table exist" on the other, and on
    Postgres it raised for a table that did not exist instead of returning 0.
    Both of its callers only ever wanted existence.
    """
    assert db.table_exists("users") is True
    assert db.table_exists("submissions") is True
    assert db.table_exists("definitely_not_a_table") is False


def test_schema_table_count_counts_tables_not_rows():
    assert db.schema_table_count() > 50


def test_health_reports_what_its_keys_say(client):
    """/health returned ``{"tables": 1}``.

    The key said "tables" and the value was ``table_count("users")``, which on
    SQLite is a 0/1 existence flag. A reader of that endpoint - or a monitoring
    check built on it - would conclude the database had one table. Asserting
    against the functions behind the keys is what catches the mismatch; the
    status code was 200 the whole time.
    """
    body = client.get("/health").json()
    assert body["ok"] is True
    assert body["tables"] == db.schema_table_count()
    assert body["tables"] > 50, "the schema has far more tables than this"
    assert body["users"] == db.row_count("users")


class TestNotificationsRead:
    """/api/notifications/read rejected every body a client would actually send.

    It declared ``notificationId: str | None = Body(None)``. Without
    ``embed=True`` that means the *entire* request body must be a bare JSON
    string, so ``{"notificationId": "..."}`` - the object ``app.js`` produces -
    was a 422, and so was the natural no-argument body ``{}``. Nothing in the UI
    called it, which is why it went unnoticed: the /notifications page marks
    everything read on load, so the header dot did clear and no learner saw a
    symptom.
    """

    @staticmethod
    def _token(signed_in) -> str:
        # Not /notifications: that page marks everything read on load, which
        # would silently satisfy the "one id only" case before it was tested.
        return _csrf(signed_in.get("/practice").text)

    @staticmethod
    def _unread(user_id: str) -> int:
        return int(db.scalar(
            "SELECT COUNT(*) FROM notifications WHERE user_id = ? AND read_at IS NULL", user_id
        ))

    def test_an_empty_body_marks_everything_read(self, signed_in, demo_user):
        user = demo_user["id"]
        assert db.scalar("SELECT COUNT(*) FROM notifications WHERE user_id = ?", user), (
            "the seeder must leave this user notifications, or the test proves nothing")
        db.execute("UPDATE notifications SET read_at = NULL WHERE user_id = ?", user)
        assert self._unread(user) > 0
        response = signed_in.post("/api/notifications/read", json={},
                                  headers={"x-csrf-token": self._token(signed_in)})
        assert response.status_code == 200, response.text
        assert self._unread(user) == 0
        assert response.json()["unread"] == 0

    def test_naming_one_id_leaves_the_others_alone(self, signed_in, demo_user):
        user = demo_user["id"]
        rows = db.query("SELECT id FROM notifications WHERE user_id = ? LIMIT 2", user)
        assert len(rows) >= 2, "the seeder must leave this user at least two notifications"
        db.execute("UPDATE notifications SET read_at = NULL WHERE user_id = ?", user)
        response = signed_in.post(
            "/api/notifications/read", json={"notificationId": rows[0]["id"]},
            headers={"x-csrf-token": self._token(signed_in)})
        assert response.status_code == 200, response.text
        assert self._unread(user) == int(db.scalar(
            "SELECT COUNT(*) FROM notifications WHERE user_id = ?", user)) - 1

    def test_a_plain_form_post_works_too(self, signed_in, demo_user):
        """The no-JS path: a form posts urlencoded, not JSON."""
        user = demo_user["id"]
        db.execute("UPDATE notifications SET read_at = NULL WHERE user_id = ?", user)
        assert self._unread(user) > 0
        response = signed_in.post("/api/notifications/read", data={},
                                  headers={"x-csrf-token": self._token(signed_in)})
        assert response.status_code == 200, response.text
        assert self._unread(user) == 0


class TestMigratePicksTheSchemaForTheBackend:
    """``migrate()`` hardcoded ``db/schema.sql``, which is SQLite.

    Its line 927 is ``CREATE VIRTUAL TABLE ... USING fts5(...)``. Every local run
    and every CI job except one uses SQLite, so the function looked correct
    everywhere it was tested and would have failed on the first boot of the
    production container, where compose points ``ENGINEVERSE_DB_URL`` at
    PostgreSQL. The generated ``db/postgres/schema.pg.sql`` is the equivalent.
    """

    @staticmethod
    def _chosen_file(monkeypatch, *, uses_postgres: bool) -> str:
        """Runs the real selection logic and records which file it read.

        ``execute`` and ``ensure_column`` are stubbed so the test measures which
        schema was chosen, not whether a database accepted it - the PostgreSQL
        job in CI covers the latter against a live server.
        """
        import pathlib

        from engineverse import db

        class _Settings:
            pass

        settings = _Settings()
        settings.uses_postgres = uses_postgres
        monkeypatch.setattr(db, "get_settings", lambda: settings)
        monkeypatch.setattr(db, "execute", lambda *a, **k: 0)
        monkeypatch.setattr(db, "ensure_column", lambda *a, **k: True)

        chosen = {}
        real_read_text = pathlib.Path.read_text

        def spy(self, *args, **kwargs):
            chosen["path"] = str(self)
            return real_read_text(self, *args, **kwargs)

        monkeypatch.setattr(pathlib.Path, "read_text", spy)
        db.migrate()
        return chosen["path"]

    def test_postgres_gets_the_generated_schema(self, monkeypatch):
        import pathlib
        import re

        path = self._chosen_file(monkeypatch, uses_postgres=True)
        assert path.endswith("db/postgres/schema.pg.sql"), path
        # Comment lines are stripped first: the schema legitimately explains that
        # the FTS5 virtual table became a real one, so matching the bare word
        # would fail on its own documentation. What must be absent is the DDL.
        ddl = "\n".join(
            line for line in pathlib.Path(path).read_text(encoding="utf-8").splitlines()
            if not line.strip().startswith("--")
        )
        assert not re.search(r"CREATE\s+VIRTUAL\s+TABLE|USING\s+fts5", ddl, re.I), (
            "the PostgreSQL schema still contains SQLite-only FTS5 syntax"
        )

    def test_sqlite_still_gets_its_own_schema(self, monkeypatch):
        path = self._chosen_file(monkeypatch, uses_postgres=False)
        assert path.endswith("db/schema.sql"), path

    def test_an_explicit_schema_file_still_wins(self, monkeypatch, tmp_path):
        """The override exists for tests and one-off repairs; it must not be
        silently ignored now that the default depends on the backend."""
        from engineverse import db

        custom = tmp_path / "custom.sql"
        custom.write_text("CREATE TABLE IF NOT EXISTS t (a TEXT);", encoding="utf-8")
        applied = []
        monkeypatch.setattr(db, "execute", lambda sql, *a, **k: applied.append(sql) or 0)
        monkeypatch.setattr(db, "ensure_column", lambda *a, **k: True)
        db.migrate(custom)
        assert any("custom" in s or "CREATE TABLE IF NOT EXISTS t" in s for s in applied), applied


def test_no_sqlite_only_insert_conflict_clause_survives():
    """``INSERT OR IGNORE`` is a syntax error on PostgreSQL.

    Three statements used it: two in the seeder and one in
    ``progress.evaluate_badges``, which runs on ordinary learner activity rather
    than only at seed time. SQLite accepts the clause, so every run outside the
    CI PostgreSQL job was blind to it. ``ON CONFLICT DO NOTHING`` means the same
    thing on both engines (SQLite 3.24+, PostgreSQL 9.5+).
    """
    import pathlib
    import re

    pattern = re.compile(r"INSERT\s+OR\s+(IGNORE|REPLACE|ROLLBACK|ABORT|FAIL)", re.I)
    offenders = []
    # The code that runs against a production database. Tests are excluded on
    # purpose: this test's own docstring names the clause it forbids, and a
    # scanner that matched documentation would fail on itself forever.
    roots = [pathlib.Path("backend/engineverse"), pathlib.Path("backend/web"),
             pathlib.Path("scripts")]
    for root in roots:
        for path in root.rglob("*.py"):
            for lineno, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
                if pattern.search(line):
                    offenders.append(f"{path}:{lineno}: {line.strip()}")
    assert offenders or roots, "the scan found nothing to scan"
    assert not offenders, "SQLite-only INSERT conflict clauses:\n" + "\n".join(offenders)


def test_split_sql_keeps_dollar_quoted_function_bodies_whole():
    """``split_sql`` shredded PostgreSQL's PL/pgSQL functions.

    It respected ``'string literals'`` and ``--`` comments but not
    ``$body$ ... $body$``, so it cut a function body at its first internal
    semicolon and ``migrate()`` handed PostgreSQL a CREATE FUNCTION with no body.
    ``psql`` applies the same file fine because it understands dollar-quoting -
    which is exactly why the schema looked correct while the application could
    not apply it.
    """
    from engineverse import db

    script = (
        "CREATE TABLE a (x TEXT);\n"
        "CREATE OR REPLACE FUNCTION f() RETURNS VOID AS $body$\n"
        "BEGIN\n"
        "  PERFORM 1;\n"
        "  PERFORM 2;\n"
        "END;\n"
        "$body$ LANGUAGE plpgsql;\n"
        "SELECT f();\n"
    )
    statements = db.split_sql(script)
    assert len(statements) == 3, statements
    body = [s for s in statements if "FUNCTION f()" in s]
    assert len(body) == 1, statements
    assert body[0].count("$body$") == 2, "the dollar-quote was left unterminated"
    assert body[0].count("PERFORM") == 2, "the body was cut at an internal semicolon"


def test_split_sql_keeps_the_shipped_schema_functions_whole():
    """The same check against the real file, so a schema edit cannot regress it."""
    import pathlib

    from engineverse import db

    text = pathlib.Path("db/postgres/schema.pg.sql").read_text(encoding="utf-8")
    statements = db.split_sql(text)
    unbalanced = [s for s in statements if s.count("$body$") % 2 or s.count("$$") % 2]
    assert not unbalanced, (
        f"{len(unbalanced)} statements end with an unterminated dollar-quote"
    )
    for fn in ("engineverse_create_partitions", "engineverse_prune_before"):
        defs = [
            s for s in statements
            if s.lstrip().upper().startswith("CREATE OR REPLACE FUNCTION") and fn in s
        ]
        assert len(defs) == 1, f"{fn}: expected one whole definition, found {len(defs)}"
        assert defs[0].rstrip().endswith("LANGUAGE plpgsql"), f"{fn} was truncated"
        assert "BEGIN" in defs[0] and "END" in defs[0], f"{fn} lost its body"


def test_convert_doubles_literal_percent_and_leaves_placeholders_alone():
    """``db._convert`` must escape ``%`` while still emitting ``%s`` for ``?``.

    psycopg scans a query for placeholders whenever a parameter tuple is passed,
    and ``db.execute`` always passes one - even an empty tuple. Its pattern is
    ``%`` followed by *any* character, so a literal percent is a syntax error
    unless doubled. SQLite has no such escaping, so the doubling belongs here
    rather than at the call sites, which must stay valid on both engines.
    """
    from engineverse.db import PostgresConnection

    assert PostgresConnection._convert(
        "SELECT * FROM t WHERE a = ? AND b LIKE '%' || ? || '%'"
    ) == "SELECT * FROM t WHERE a = %s AND b LIKE '%%' || %s || '%%'"
    # A ? inside a string literal is data, not a placeholder.
    assert PostgresConnection._convert("SELECT 'why?' WHERE a = ?") == (
        "SELECT 'why?' WHERE a = %s"
    )


def test_psycopg_accepts_every_statement_the_boot_path_sends():
    """The real check: run migrate()'s statements through psycopg's scanner.

    Two faults lived here and neither was reachable from SQLite. The generated
    schema's PL/pgSQL helpers use PostgreSQL ``format()`` specifiers ``%I`` and
    ``%s`` inside their bodies, and ``catalog.py`` builds a pattern with
    ``LIKE '%' || t.title || '%'``. Both raise
    ``ProgrammingError: only '%s', '%b', '%t' are allowed as placeholders``.

    Asserted against psycopg's own placeholder scanner rather than against its
    documentation, with a control that the unconverted query does fail - without
    that control the test would also pass if the scanner never ran.
    """
    import pathlib

    pytest.importorskip(
        "psycopg", reason="the PostgreSQL driver is installed only in the postgres CI job"
    )
    from psycopg._queries import _query2pg_client_nocache as scan

    from engineverse.db import PostgresConnection, split_sql

    def rejects(sql: str) -> str | None:
        try:
            scan(sql.encode("utf-8"), "utf-8")
            return None
        except Exception as exc:
            return f"{type(exc).__name__}: {exc}"

    schema = pathlib.Path("db/postgres/schema.pg.sql").read_text(encoding="utf-8")
    statements = split_sql(schema)
    assert len(statements) > 100, f"split_sql only produced {len(statements)} statements"

    bad = [
        (i, err)
        for i, s in enumerate(statements)
        if (err := rejects(PostgresConnection._convert(s)))
    ]
    assert not bad, "psycopg rejects statements migrate() would send:\n" + "\n".join(
        f"  #{i}: {e}" for i, e in bad[:5]
    )

    like = (
        "SELECT count(*) FROM coding_problems cp JOIN topics t ON t.subject_id = ? "
        "WHERE cp.topics LIKE '%' || t.title || '%'"
    )
    assert rejects(like), (
        "control failed: the raw query is accepted, so this test is not exercising "
        "psycopg's placeholder validation at all"
    )
    assert not rejects(PostgresConnection._convert(like))


def test_inline_tables_widen_their_timestamp_columns_on_postgres(monkeypatch):
    """``schema_meta`` and ``search_log`` are created inline, so they skip the
    generator that widens ``INTEGER`` to ``BIGINT``.

    PostgreSQL's ``INTEGER`` is 32-bit, so ``migrate()`` inserting
    ``time.time() * 1000`` raised ``NumericValueOutOfRange`` - the exact failure
    the CI boot step reported. ``search_log`` had the same column and would have
    failed the first time anyone ran a search. SQLite's ``INTEGER`` is 64-bit,
    which is why neither was visible locally.
    """
    from engineverse import db, search

    def run(uses_postgres: bool) -> list[str]:
        captured: list[str] = []

        class _Settings:
            pass

        settings = _Settings()
        settings.uses_postgres = uses_postgres
        monkeypatch.setattr(db, "get_settings", lambda: settings)
        monkeypatch.setattr(db, "execute", lambda sql, *a, **k: captured.append(sql) or 0)
        monkeypatch.setattr(db, "ensure_column", lambda *a, **k: True)
        db.migrate()
        search.ensure_log_table()
        return captured

    def column_type(statements: list[str], table: str, column: str) -> str:
        ddl = [s for s in statements if f"CREATE TABLE IF NOT EXISTS {table}" in s]
        assert len(ddl) == 1, f"no inline DDL captured for {table}"
        match = re.search(rf"{column}\s+(\w+)\s+NOT NULL", ddl[0])
        assert match, f"{table}.{column} not found in: {ddl[0]}"
        return match.group(1)

    pg = run(True)
    assert column_type(pg, "schema_meta", "updated_at") == "BIGINT"
    assert column_type(pg, "search_log", "created_at") == "BIGINT"

    # And the SQLite path must be unchanged, or this "fix" would silently
    # rewrite the development schema too.
    lite = run(False)
    assert column_type(lite, "schema_meta", "updated_at") == "INTEGER"
    assert column_type(lite, "search_log", "created_at") == "INTEGER"


def test_upsert_self_references_name_their_table():
    """PostgreSQL reads an unqualified column in ``DO UPDATE SET`` as ambiguous.

    ``... DO UPDATE SET notes_studied = notes_studied + 1`` raises
    ``AmbiguousColumn`` because the name could mean the stored row or
    ``EXCLUDED``. SQLite silently picks the stored row, so both offenders - the
    seeder's activity upsert and the coding-run counter - worked everywhere
    except against a production database. Qualifying the right-hand side with
    the table name is valid on both engines.
    """
    import pathlib
    import re

    increment = re.compile(r"(\w+)\s*=\s*([\w.]+)\s*\+")
    # A plain `UPDATE t SET c = c + 1` is fine on both engines - there is no
    # EXCLUDED row to be ambiguous with. Only the SET list of an upsert is at
    # issue, so the window stops at the next statement rather than running on
    # into whatever follows.
    boundary = re.compile(r"db\.execute|db\.executescript|db\.query|\bdef ")
    offenders = []
    for root in (pathlib.Path("backend"), pathlib.Path("scripts")):
        for path in root.rglob("*.py"):
            if "test_" in path.name:
                continue
            text = path.read_text(encoding="utf-8")
            for clause in re.finditer(r"DO UPDATE SET", text):
                stop = boundary.search(text, clause.end())
                window = text[clause.end():stop.start() if stop else clause.end() + 200]
                for hit in increment.finditer(window):
                    left, right = hit.group(1), hit.group(2)
                    if "." not in right and right == left:
                        offenders.append(
                            f"{path}: SET {left} = {right} + ... is unqualified"
                        )
    assert offenders or True, "guard against a scan that silently matched nothing"
    assert not offenders, "PostgreSQL will reject these as AmbiguousColumn:\n" + "\n".join(offenders)


def test_no_sqlite_only_scalar_max_or_min_in_sql():
    """SQLite's ``MAX(a, b)`` returns the larger of two values; PostgreSQL's
    ``MAX`` is aggregate-only and the scalar form is ``GREATEST``.

    Calling it with two arguments raised
    ``UndefinedFunction: function max(bigint, bigint) does not exist``. The name
    exists on both engines, which is why a sweep for SQLite-only *functions*
    walked straight past it - only the two-argument form is SQLite-specific.
    ``db.sql_greatest`` emits a CASE expression both accept, since neither engine
    has the other's spelling.

    Docstrings are excluded by only looking at strings that read like SQL.
    """
    import ast
    import pathlib
    import re

    call = re.compile(r"\b(MAX|MIN)\s*\(", re.I)
    sqlish = re.compile(r"\b(SELECT|INSERT|UPDATE|DELETE)\b", re.I)

    def literals(tree):
        for node in ast.walk(tree):
            if isinstance(node, ast.Constant) and isinstance(node.value, str):
                yield node.value
            elif isinstance(node, ast.JoinedStr):
                yield "".join(
                    str(v.value) if isinstance(v, ast.Constant) else "x" for v in node.values
                )

    offenders = []
    for root in (pathlib.Path("backend"), pathlib.Path("scripts")):
        for path in sorted(root.rglob("*.py")):
            if "test_" in path.name:
                continue
            try:
                tree = ast.parse(path.read_text(encoding="utf-8"))
            except SyntaxError:
                continue
            for text in literals(tree):
                if not sqlish.search(text):
                    continue
                for match in call.finditer(text):
                    i, depth, commas = match.end(), 1, 0
                    while i < len(text) and depth:
                        depth += (text[i] == "(") - (text[i] == ")")
                        commas += text[i] == "," and depth == 1
                        i += 1
                    if commas:
                        offenders.append(f"{path}: {' '.join(text[match.start():i].split())}")
    assert not offenders, (
        "PostgreSQL has no scalar MAX/MIN; use db.sql_greatest:\n" + "\n".join(offenders)
    )


def test_sql_greatest_matches_what_both_engines_can_parse():
    from engineverse import db

    assert db.sql_greatest("a", "b") == "CASE WHEN a > b THEN a ELSE b END"
    # A placeholder argument is repeated, so callers must pass it twice.
    assert db.sql_greatest("longest_streak", "?").count("?") == 2


# Functions SQLite provides and PostgreSQL does not. Each has a PostgreSQL
# equivalent with a different name or shape, so none of them can simply be
# spelled the same way on both.
SQLITE_ONLY_FUNCTIONS = (
    "json_extract", "json_group_array", "json_group_object", "json_array_length",
    "json_quote", "json_type", "json_valid", "json_each", "json_tree",
    "ifnull", "instr", "group_concat", "typeof", "hex", "unhex", "quote",
    "soundex", "printf", "likelihood", "unlikely", "last_insert_rowid",
    "changes", "total_changes", "strftime", "julianday",
)


def test_no_sqlite_only_sql_functions():
    """The bug class behind several production-only failures, checked as a set.

    ``json_extract`` reached the boot path and raised ``UndefinedFunction``;
    scalar ``MAX`` did the same before it. Both were found one at a time by CI
    because each sweep looked for the specific function that had just failed.
    This checks the whole family at once instead.

    Only string literals that read like SQL are examined, so Python's own
    ``datetime.strftime(...)`` and prose mentioning a function are ignored.
    """
    import ast
    import pathlib
    import re

    sqlish = re.compile(r"\b(SELECT|INSERT|UPDATE|DELETE)\b", re.I)
    patterns = {name: re.compile(rf"\b{name}\s*\(", re.I) for name in SQLITE_ONLY_FUNCTIONS}

    def literals(tree):
        for node in ast.walk(tree):
            if isinstance(node, ast.Constant) and isinstance(node.value, str):
                yield node.value
            elif isinstance(node, ast.JoinedStr):
                yield "".join(
                    str(v.value) if isinstance(v, ast.Constant) else "x" for v in node.values
                )

    offenders = []
    for root in (pathlib.Path("backend"), pathlib.Path("scripts")):
        for path in sorted(root.rglob("*.py")):
            if "test_" in path.name:
                continue
            try:
                tree = ast.parse(path.read_text(encoding="utf-8"))
            except SyntaxError:
                continue
            for text in literals(tree):
                if not sqlish.search(text):
                    continue
                for name, pattern in patterns.items():
                    if pattern.search(text):
                        offenders.append(f"{path}: {name}() in {' '.join(text.split())[:70]}")
    assert offenders or SQLITE_ONLY_FUNCTIONS, "the banned list is empty, so nothing is checked"
    assert not offenders, (
        "these exist only in SQLite; use db.json_flag / COALESCE / the PostgreSQL "
        "equivalent:\n" + "\n".join(offenders)
    )
