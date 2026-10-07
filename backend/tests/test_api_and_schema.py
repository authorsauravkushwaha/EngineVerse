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

    def test_search_index_covers_the_catalogue(self):
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
