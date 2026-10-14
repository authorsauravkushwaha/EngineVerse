"""Integrated labs: useful seeded outputs, bounded execution and honest Pages UI."""
from __future__ import annotations

import ast
import html
import json
import re
import sqlite3
import time
from pathlib import Path

import pytest

from engineverse import db, navigation, public_apis, studio, swarm, workflows
from engineverse.security.ids import now_ms
from scripts import export_pages, verify_pages

pytestmark = pytest.mark.usefixtures("seeded")
LAB_PATHS = ("/apis", "/studio", "/workflows", "/swarm")


def _token(client, page: str) -> str:
    response = client.get(page)
    assert response.status_code == 200
    match = re.search(r'<meta name="csrf-token" content="([^"]+)"', response.text)
    assert match
    return html.unescape(match.group(1))


def _post(client, page: str, endpoint: str, body: dict, *, accept: str = "application/json"):
    return client.post(endpoint, json=body, headers={"X-CSRF-Token": _token(client, page), "Accept": accept})


@pytest.mark.parametrize("path,section,icon", [
    ("/apis", "code", "globe"), ("/studio", "code", "database"),
    ("/workflows", "progress", "workflow"), ("/swarm", "learn", "network"),
])
def test_labs_are_in_every_navigation_surface(path, section, icon, client):
    destination = navigation.find(path)
    assert destination and destination.icon == icon
    assert navigation.section_for(path).key == section
    assert path in navigation.indexable_paths(public_only=True)
    assert path in export_pages.public_paths()
    response = client.get(path)
    assert response.status_code == 200
    verify_pages.validate_page(response.text, capability=path.strip("/"))
    for other in LAB_PATHS:
        assert f'href="{other}"' in response.text
    index = client.get("/resources").text
    assert f'href="{path}"' in index
    icons = (Path(__file__).resolve().parents[1] / "templates" / "_icons.html").read_text()
    assert f'"{icon}"' in icons


def test_directory_has_real_learning_pairings_and_three_valid_snippets(client):
    entries = public_apis.list_apis()
    assert len(entries) == len(public_apis.APIS) == 12
    assert len({entry["slug"] for entry in entries}) == len(entries)
    for entry in entries:
        assert entry["url"].startswith("https://")
        assert entry["auth"] in public_apis.AUTH_TYPES and entry["cors"] in public_apis.CORS_TYPES
        assert entry["topic_url"] and entry["project_url"]
        assert db.scalar("SELECT COUNT(*) FROM topics WHERE slug=? AND status='published'", entry["topic_slug"]) == 1
        assert db.scalar("SELECT COUNT(*) FROM projects WHERE slug=? AND status='published'", entry["project_slug"]) == 1
        assert set(entry["snippets"]) == {"curl", "python", "javascript"}
        ast.parse(entry["snippets"]["python"])
        assert "--max-time 10" in entry["snippets"]["curl"]
        assert "AbortSignal.timeout" in entry["snippets"]["javascript"]
        response = client.get("/apis", params={"slug": entry["slug"]})
        assert response.status_code == 200
        assert response.text.count('data-api-slug="') == 1
        assert entry["name"] in html.unescape(response.text)
        assert 'filtered to' in response.text.lower()


def test_directory_filters_are_combined_and_unknown_values_do_not_widen(client):
    filtered = client.get("/api/public-apis", params={"category": "Developer tools", "auth": "none", "cors": "yes", "q": "github"}).json()
    assert filtered["ok"] and filtered["count"] == 1
    assert filtered["apis"][0]["slug"] == "github"
    for params in ({"slug": "not-real"}, {"category": "not-real"}, {"auth": "not-real"}, {"cors": "not-real"}, {"q": "zzxq-no-match"}):
        result = client.get("/api/public-apis", params=params).json()
        assert result["count"] == 0 and result["apis"] == []
    assert client.get("/api/public-apis", params={"q": "x" * 161}).status_code == 422
    assert client.get("/apis", params={"slug": "x" * 129}).status_code == 422


def test_studio_schema_only_exposes_26_explicit_public_projections(client):
    schema = client.get("/api/studio/schema").json()
    assert schema["ok"] and schema["table_count"] == 26
    assert {table["name"] for table in schema["tables"]} == set(studio.PUBLIC_TABLES)
    assert len(studio.SERVICES) == 5
    forbidden = {"users", "sessions", "profiles", "payments", "personal_notes", "coding_testcases", "audit_logs"}
    assert not forbidden.intersection(studio.PUBLIC_TABLES)
    for table in schema["tables"]:
        assert {column["name"] for column in table["columns"]} == set(studio.PUBLIC_TABLES[table["name"]].columns)
        assert table["row_count"] > 0
        assert not {"author_id", "reviewer_id", "password_hash", "answer_text", "answer_index", "is_correct", "rationale"}.intersection(column["name"] for column in table["columns"])
        for key in table["foreign_keys"]:
            assert key["table"] in studio.PUBLIC_TABLES
        result = studio.run_query(f"SELECT * FROM {table['name']} LIMIT 1")
        assert len(result["columns"]) == len(table["columns"])
    assert "not native Postgres RLS" in schema["disclosure"]


@pytest.mark.parametrize("sql", [
    "DELETE FROM topics", "UPDATE topics SET title='bad'", "INSERT INTO topics(id) VALUES('bad')",
    "CREATE TABLE stolen(x)", "DROP TABLE topics", "ALTER TABLE topics ADD COLUMN stolen TEXT",
    "ATTACH DATABASE '/tmp/leak' AS stolen", "PRAGMA table_info(users)", "VACUUM", "BEGIN",
    "SELECT * FROM topics; SELECT * FROM users", "SELECT * FROM users", 'SELECT * FROM "sessions"',
    "SELECT * FROM user_flashcards", "SELECT * FROM coding_testcases", "SELECT * FROM sqlite_master",
    "SELECT * FROM main.topics", "SELECT * FROM pragma_table_info('users')",
    "SELECT load_extension('anything')", "SELECT readfile('/etc/passwd')", "SELECT writefile('x', 'y')",
    "SELECT randomblob(1000000000)", "SELECT zeroblob(1000000000)", "SELECT printf('%999999999s', 'x')",
    "SELECT author_id FROM topics", "SELECT answer_text FROM questions", "SELECT is_correct FROM question_options",
    "WITH x AS (DELETE FROM topics RETURNING *) SELECT * FROM x",
    "SELECT slug FROM topics UNION SELECT password_hash FROM users",
])
def test_sql_sandbox_blocks_writes_private_data_and_unsafe_functions(sql):
    with pytest.raises(studio.QueryError):
        studio.run_query(sql)


@pytest.mark.parametrize("sql", [
    "SELECT slug, title FROM topics WHERE slug='arrays'",
    "-- harmless comment\nWITH chosen AS (SELECT slug FROM topics WHERE slug='arrays') SELECT * FROM chosen",
    "SELECT 'DELETE; DROP TABLE users' AS harmless_string",
    "SELECT s.name, COUNT(t.id) AS n FROM subjects s JOIN topics t ON t.subject_id=s.id GROUP BY s.id, s.name LIMIT 5",
    "SELECT slug FROM topics WHERE title LIKE '%Array%' LIMIT 5",
    "SELECT 1 AS n UNION ALL SELECT 2 AS n",
])
def test_sql_sandbox_executes_real_selects_and_explain(sql):
    result = studio.run_query(sql)
    assert result["read_only"] and result["row_count"] > 0
    assert isinstance(result["plan"], list)
    assert isinstance(result["rows"][0], list)
    assert "never on the application database" in result["disclosure"]


def test_sql_is_never_submitted_to_the_live_connection(monkeypatch):
    calls = []
    real_query = db.query
    marker = "untrusted-query-marker"

    def observe(sql, *params):
        calls.append(sql)
        assert marker not in sql
        return real_query(sql, *params)

    monkeypatch.setattr(db, "query", observe)
    result = studio.run_query(f"SELECT '{marker}' AS marker, slug FROM topics LIMIT 1")
    assert result["rows"][0][0] == marker and calls


def test_sql_snapshot_filters_unpublished_rows_and_their_children():
    stamp = now_ms()
    subject = db.scalar("SELECT id FROM subjects WHERE status='published' LIMIT 1")
    db.execute("INSERT INTO topics(id,slug,subject_id,title,status,created_at,updated_at) VALUES(?,?,?,?,?,?,?)",
               "studio-private-topic", "studio-private-topic", subject, "PRIVATE DRAFT SENTINEL", "draft", stamp, stamp)
    db.execute("INSERT INTO notes(id,topic_id,status,created_at,updated_at) VALUES(?,?,?,?,?)",
               "studio-private-note", "studio-private-topic", "published", stamp, stamp)
    db.execute("INSERT INTO note_sections(id,note_id,kind,title,body) VALUES(?,?,?,?,?)",
               "studio-private-section", "studio-private-note", "definition", "Private", "PRIVATE DRAFT SENTINEL")
    try:
        assert studio.run_query("SELECT title FROM topics WHERE slug='studio-private-topic'")["rows"] == []
        assert studio.run_query("SELECT body FROM note_sections WHERE id='studio-private-section'")["rows"] == []
    finally:
        db.execute("DELETE FROM topics WHERE id='studio-private-topic'")


def test_sql_budget_and_result_bounds_are_enforced():
    result = studio.run_query("SELECT slug FROM topics ORDER BY slug")
    assert result["row_count"] == studio.MAX_RESULT_ROWS and result["truncated"]
    result = studio.run_query("SELECT '" + "a" * 2500 + "' AS text")
    assert result["clipped_cells"] == 1 and len(result["rows"][0][0]) == studio.MAX_CELL_CHARS + 1
    for sql in ("SELECT 1 " + " " * studio.MAX_SQL_CHARS, "", None):
        with pytest.raises(studio.QueryError):
            studio.run_query(sql)
    started = time.monotonic()
    with pytest.raises(studio.QueryError, match="execution budget"):
        studio.run_query("WITH RECURSIVE seq(n) AS (SELECT 1 UNION ALL SELECT n+1 FROM seq) SELECT SUM(n) FROM seq")
    assert time.monotonic() - started < 3


def test_studio_post_requires_csrf_and_cannot_mutate(client):
    assert client.post("/api/studio/query", json={"sql": "SELECT 1"}).status_code == 403
    result = _post(client, "/studio", "/api/studio/query", {"sql": "SELECT slug FROM topics WHERE slug='arrays'"})
    assert result.status_code == 200 and result.json()["rows"] == [["arrays"]]
    count = db.scalar("SELECT COUNT(*) FROM topics")
    result = _post(client, "/studio", "/api/studio/query", {"sql": "DELETE FROM topics"})
    assert result.status_code == 400 and not result.json()["ok"]
    assert db.scalar("SELECT COUNT(*) FROM topics") == count


def test_workflow_graphs_execute_real_seeded_operators():
    assert len(workflows.WORKFLOWS) == 4
    for workflow in workflows.WORKFLOWS:
        seen = set()
        for node in workflow.nodes:
            assert node.id not in seen and set(node.depends_on).issubset(seen)
            seen.add(node.id)
        result = workflows.run(workflow.slug)
        assert result["read_only"] and result["status"] == "succeeded"
        assert [step["id"] for step in result["steps"]] == [node.id for node in workflow.nodes]
        assert result["steps"][-1]["output"] == result["report"]
    study = workflows.run("study")
    assert study["steps"][1]["output"]["count"] > 0  # note evidence
    assert study["steps"][2]["output"]["count"] > 0  # formulas
    revision = workflows.run("revision")
    assert revision["steps"][1]["output"]["count"] > 0
    assert revision["steps"][1]["output"]["scope"].startswith("subject")
    assert workflows.run("placement")["steps"][1]["output"]["count"] > 0
    assert workflows.run("audit")["steps"][2]["output"]["broken_pairings"] == 0


@pytest.mark.parametrize("inputs", [
    {"topic_slug": "unknown-topic"}, {"limit": 0}, {"limit": 11}, {"limit": True}, {"limit": 1.5},
    {"difficulty": "expert"}, {"q": ["array"]}, {"q": "x" * 161}, {"code": "arbitrary()"},
    {"webhook": "https://example.org"}, {"topic_slug": "x" * 129}, ["not-an-object"],
])
def test_workflows_reject_arbitrary_execution_and_bad_inputs(inputs):
    with pytest.raises(workflows.WorkflowError):
        workflows.run("study", inputs)


def test_workflow_unknown_search_never_turns_into_a_general_plan():
    result = workflows.run("study", {"q": "zxq-unique-no-topic"})
    assert all(not step["output"]["items"] for step in result["steps"])
    with pytest.raises(workflows.WorkflowError):
        workflows.run("arbitrary")


def test_workflow_stream_reports_actual_steps_and_matches_json(client):
    body = {"slug": "study", "inputs": {"topic_slug": "bernoullis-equation", "limit": 3}}
    response = _post(client, "/workflows", "/api/workflows/run", body, accept="application/x-ndjson")
    assert response.status_code == 200 and "application/x-ndjson" in response.headers["content-type"]
    events = [json.loads(line) for line in response.text.splitlines()]
    assert [event["type"] for event in events] == ["step"] * 5 + ["complete"]
    streamed = events[-1]["result"]
    ordinary = _post(client, "/workflows", "/api/workflows/run", body).json()
    assert streamed["report"] == ordinary["report"]
    assert [event["step"]["output"] for event in events[:-1]] == [step["output"] for step in ordinary["steps"]]
    assert client.post("/api/workflows/run", json=body).status_code == 403
    bad = _post(client, "/workflows", "/api/workflows/run", {"slug": "study", "nodes": [{"code": "unsafe"}]})
    assert bad.status_code == 422


def test_workflow_stream_failure_is_explicit_and_does_not_disclose_database_details(client, monkeypatch):
    token = _token(client, "/workflows")
    first = workflows.run("study")["steps"][0]

    def interrupted(workflow, inputs):
        yield first
        raise sqlite3.DatabaseError("PRIVATE DATABASE FAILURE DETAILS")

    monkeypatch.setattr(workflows, "iter_steps", interrupted)
    response = client.post("/api/workflows/run", json={"slug": "study"},
                           headers={"X-CSRF-Token": token, "Accept": "application/x-ndjson"})
    events = [json.loads(line) for line in response.text.splitlines()]
    assert [event["type"] for event in events] == ["step", "error"]
    assert "No state was changed" in events[-1]["error"]
    assert "PRIVATE DATABASE" not in response.text


def test_n8n_exports_are_importable_and_use_read_only_server_nodes(client):
    for workflow in workflows.WORKFLOWS:
        export = client.get("/api/workflows", params={"slug": workflow.slug, "format": "n8n"}).json()
        assert not export["active"] and export["settings"]["executionOrder"] == "v1"
        assert len(export["nodes"]) == len(workflow.nodes) + 1
        names = {node["name"] for node in export["nodes"]}
        assert len({node["id"] for node in export["nodes"]}) == len(names)
        for node in export["nodes"][1:]:
            assert node["type"] == "n8n-nodes-base.httpRequest" and node["parameters"]["method"] == "GET"
            assert "$vars.engineverse_url" in node["parameters"]["url"]
            assert "/api/workflows?" in node["parameters"]["url"]
            assert "credentials" not in node
        for name, output in export["connections"].items():
            assert name in names
            assert all(edge["node"] in names for edges in output["main"] for edge in edges)
        for node in workflow.nodes:
            response = client.get("/api/workflows", params={"slug": workflow.slug, "node": node.id})
            assert response.status_code == 200 and response.json()["step"]["id"] == node.id
    assert client.get("/api/workflows", params={"slug": "unknown"}).status_code == 404
    assert client.get("/api/workflows", params={"format": "n8n"}).status_code == 422


def test_swarm_is_deterministic_and_every_finding_has_a_real_catalogue_citation(client):
    prompt = "Explain arrays and memory locality"
    result = swarm.simulate(prompt)
    assert result == swarm.simulate(prompt)
    assert result["grounded"] and len(result["agents"]) == 5
    assert len(result["sources"]) <= swarm.MAX_SOURCES
    assert result["tradeoffs"]
    numbers = {source["n"] for source in result["sources"]}
    assert numbers == set(range(1, len(numbers) + 1))
    for source in result["sources"]:
        assert source["kind"] in swarm.SOURCE_KINDS
        assert db.scalar(f"SELECT COUNT(*) FROM {source['kind']} WHERE id=?", source["entity_id"]) == 1
        assert source["excerpt"] and "<script" not in source["excerpt"]
        assert client.get(source["url"]).status_code == 200
    for agent in result["agents"]:
        assert agent["status"] in ("evidence-found", "insufficient-evidence")
        for finding in agent["findings"]:
            assert finding["source"] in numbers
            source = next(source for source in result["sources"] if source["n"] == finding["source"])
            assert finding["quote"] == source["excerpt"]
    for tradeoff in result["tradeoffs"]:
        assert set(tradeoff["citations"]).issubset(numbers)
        assert "Unresolved review prompt" in tradeoff["resolution"]


@pytest.mark.parametrize("prompt", ["bake a souffle with saffron", "zxqvz unicorn recipes", "please explain the zzxxqqnonsense"])
def test_swarm_refuses_unsupported_requests_instead_of_padding(prompt):
    result = swarm.simulate(prompt)
    assert not result["grounded"] and result["sources"] == [] and result["tradeoffs"] == []
    assert all(agent["status"] == "insufficient-evidence" and not agent["findings"] for agent in result["agents"])


def test_swarm_has_six_and_only_six_grounding_source_kinds():
    found = set()
    for prompt in ("Explain arrays and memory locality", "Review SQL database performance and testing", "calibration uncertainty"):
        found.update(source["kind"] for source in swarm.simulate(prompt)["sources"])
    assert found == swarm.SOURCE_KINDS


def test_swarm_post_is_bounded_and_csrf_protected(client):
    assert client.post("/api/swarm/simulate", json={"prompt": "arrays"}).status_code == 403
    result = _post(client, "/swarm", "/api/swarm/simulate", {"prompt": "Explain arrays", "topic_slug": "arrays"})
    assert result.status_code == 200 and result.json()["grounded"]
    for body in ({"prompt": "x" * 401}, {"prompt": "a"}, {"prompt": []}, {"prompt": "arrays", "topic_slug": "unknown"}, {"prompt": "arrays", "topic_slug": []}):
        assert _post(client, "/swarm", "/api/swarm/simulate", body).status_code == 422


@pytest.mark.parametrize("page,endpoint,body,needle", [
    ("/studio", "/api/studio/query", {"sql": "SELECT 'no-js-result' AS result"}, "no-js-result"),
    ("/workflows", "/api/workflows/run", {"slug": "study", "topic_slug": "arrays", "limit": "2"}, "Pipeline executed."),
    ("/swarm", "/api/swarm/simulate", {"prompt": "Explain arrays"}, "Simulation executed against"),
])
def test_labs_have_real_server_rendered_form_fallbacks(client, page, endpoint, body, needle):
    token = _token(client, page)
    response = client.post(endpoint, data=dict(body, csrf_token=token), headers={"Accept": "text/html"})
    assert response.status_code == 200 and "text/html" in response.headers["content-type"]
    assert needle in html.unescape(response.text)


def test_reading_copy_does_not_claim_backend_operators_are_running(client):
    assert "/api/" in export_pages.SKIP_PREFIXES and "/api" not in export_pages.SKIP_PREFIXES
    assert set(LAB_PATHS).issubset(export_pages.public_paths())
    for path in LAB_PATHS:
        text = export_pages.inject(client.get(path).text, "/EngineVerse/", search=False)
        assert f'href="/EngineVerse{path}/"' in text
        verify_pages.validate_page(text, capability=path.strip("/"))
        if path != "/apis":
            assert "data-lab-mode-notice hidden" not in text
            assert re.search(r'<button[^>]*data-live-control[^>]*disabled', text)
            assert 'method="post" data-live-only' not in text
            assert 'action="/EngineVerse/hosting/"' in text
        else:
            assert text.count('data-api-slug="') == len(public_apis.APIS)


def test_exporter_rejects_skipped_heading_levels_and_verifier_checks_revision_paths(tmp_path):
    export_pages.self_check()
    verify_pages.self_check()
    page = tmp_path / "index.html"
    page.write_text("<h1>Valid</h1><h2>Section</h2><h3>Detail</h3>")
    export_pages.assert_heading_outlines(tmp_path)
    page.write_text("<h1>Invalid</h1><h3>Skipped</h3>")
    with pytest.raises(SystemExit, match="invalid heading outlines"):
        export_pages.assert_heading_outlines(tmp_path)
    workflow = (Path(__file__).resolve().parents[2] / ".github" / "workflows" / "pages.yml").read_text()
    assert "verify_pages.py --url" in workflow and 'PAGES_URL: ${{ steps.deployment.outputs.page_url }}' in workflow
