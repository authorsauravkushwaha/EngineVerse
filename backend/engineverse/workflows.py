"""Declarative, allowlisted study automations with real per-node execution.

Inspired by n8n: templates are data, operators are a closed local registry and
outputs flow through explicit dependencies. No arbitrary code, outbound hooks,
credentials, writes to progress, or claims that a plan was actually completed.
The same executor powers HTML, JSON, NDJSON live steps and n8n HTTP-node exports.
"""
from __future__ import annotations

import re
import time
from dataclasses import asdict, dataclass
from typing import Any, Iterator
from urllib.parse import quote, urlencode
from uuid import NAMESPACE_URL, uuid5

from . import db, public_apis, studio
from .swarm import plain


@dataclass(frozen=True)
class Node:
    id: str
    label: str
    operator: str
    depends_on: tuple[str, ...] = ()


@dataclass(frozen=True)
class Workflow:
    slug: str
    name: str
    description: str
    nodes: tuple[Node, ...]
    default_topic: str = "arrays"


WORKFLOWS = (
    Workflow("study", "Topic study pipeline", "Turn a published topic into a cited reading, formula and practice plan.", (
        Node("topic", "Choose published topic", "topics"),
        Node("notes", "Read standard-note evidence", "notes", ("topic",)),
        Node("formulas", "Collect related formulas", "formulas", ("topic",)),
        Node("questions", "Prepare practice prompts", "questions", ("topic",)),
        Node("plan", "Compose the study plan", "plan", ("topic", "notes", "formulas", "questions")),
    ), default_topic="bernoullis-equation"),
    Workflow("revision", "Revision pipeline", "Assemble public recall prompts and formulas; never alter an account's SRS schedule.", (
        Node("topic", "Choose revision topic", "topics"),
        Node("cards", "Collect recall prompts", "cards", ("topic",)),
        Node("formulas", "Build a formula checklist", "formulas", ("topic",)),
        Node("plan", "Compose the revision plan", "plan", ("topic", "cards", "formulas")),
    )),
    Workflow("placement", "Placement preparation pipeline", "Pair a topic with coding briefs and a project, without executing or grading submissions.", (
        Node("topic", "Choose focus topic", "topics"),
        Node("coding", "Select coding challenges", "coding", ("topic",)),
        Node("projects", "Find a delivery brief", "projects", ("topic",)),
        Node("plan", "Compose the placement plan", "plan", ("topic", "coding", "projects")),
    )),
    Workflow("audit", "Public catalogue audit", "Inspect public-table sizes, topic coverage gaps and directory-to-curriculum links.", (
        Node("schema", "Inspect public schema", "schema"),
        Node("coverage", "Measure topic coverage", "coverage", ("schema",)),
        Node("pairings", "Check API learning pairings", "pairings", ("schema",)),
        Node("plan", "Compose the audit report", "plan", ("schema", "coverage", "pairings")),
    ), default_topic=""),
)

MAX_ITEMS = 10
_INPUT_KEYS = frozenset({"topic_slug", "q", "difficulty", "limit"})


class WorkflowError(ValueError):
    pass


def get_workflow(slug: str) -> Workflow:
    found = next((workflow for workflow in WORKFLOWS if workflow.slug == slug), None)
    if found is None:
        raise WorkflowError("Unknown workflow. Choose study, revision, placement or audit.")
    return found


def prepare(slug: str, inputs: dict | None = None) -> tuple[Workflow, dict]:
    workflow = get_workflow(slug)
    if inputs is not None and not isinstance(inputs, dict):
        raise WorkflowError("Workflow inputs must be an object.")
    inputs = inputs or {}
    if set(inputs) - _INPUT_KEYS:
        raise WorkflowError("Only topic_slug, q, difficulty and limit are supported. Custom nodes and code are not executable.")
    clean = {}
    for key, maximum in (("topic_slug", 128), ("q", 160), ("difficulty", 16)):
        value = inputs.get(key, "")
        if not isinstance(value, str) or len(value) > maximum:
            raise WorkflowError(f"{key} must be text of at most {maximum} characters.")
        clean[key] = value.strip()
    if "topic_slug" not in inputs and not clean["q"]:
        clean["topic_slug"] = workflow.default_topic
    if clean["topic_slug"] and not db.query_one("SELECT id FROM topics WHERE slug=? AND status='published'", clean["topic_slug"]):
        raise WorkflowError("That topic is not in the published catalogue; the filter was not widened.")
    if clean["difficulty"] not in ("", "easy", "medium", "hard"):
        raise WorkflowError("Difficulty must be easy, medium or hard.")
    limit = inputs.get("limit", 5)
    if isinstance(limit, bool) or not isinstance(limit, (int, str)):
        raise WorkflowError(f"Limit must be an integer between 1 and {MAX_ITEMS}.")
    try:
        limit = int(limit)
    except (ValueError, TypeError):
        raise WorkflowError(f"Limit must be an integer between 1 and {MAX_ITEMS}.") from None
    if not 1 <= limit <= MAX_ITEMS:
        raise WorkflowError(f"Limit must be an integer between 1 and {MAX_ITEMS}.")
    clean["limit"] = limit
    return workflow, clean


def _items(rows: list[dict], url) -> dict:
    return {"items": [dict(row, url=url(row)) for row in rows], "count": len(rows)}


def _topic_ids(state: dict) -> list[str]:
    return [item["id"] for item in state.get("topic", {}).get("items", [])]


def _subject_ids(state: dict) -> list[str]:
    return sorted({item["subject_id"] for item in state.get("topic", {}).get("items", [])})


def _topic_select(table: str, projection: str, state: dict, inputs: dict, *, extra: str = "", order: str = "id") -> list[dict]:
    ids = _topic_ids(state)
    if not ids:
        return []
    where = f"topic_id IN ({','.join('?' for _ in ids)})"
    params: list[Any] = list(ids)
    if extra:
        where += " AND " + extra
    if table == "questions" and inputs["difficulty"]:
        where += " AND difficulty=?"
        params.append(inputs["difficulty"])
    return db.query(f"SELECT {projection} FROM {table} WHERE {where} ORDER BY {order} LIMIT ?", *params, inputs["limit"])


def _operate(node: Node, state: dict, inputs: dict, workflow: Workflow) -> dict:
    op = node.operator
    if op == "topics":
        sql = "SELECT id, slug, subject_id, title, summary, est_minutes, accuracy_state FROM topics WHERE status='published'"
        params = []
        if inputs["topic_slug"]:
            sql += " AND slug=?"
            params.append(inputs["topic_slug"])
        elif inputs["q"]:
            sql += " AND (LOWER(title) LIKE ? OR LOWER(COALESCE(summary, '')) LIKE ?)"
            params.extend([f"%{inputs['q'].lower()}%"] * 2)
        else:
            # A blank selection is not a request for an unbounded general plan.
            return {"items": [], "count": 0, "message": "Choose a published topic or provide a search query."}
        return _items(db.query(sql + " ORDER BY slug LIMIT ?", *params, inputs["limit"]), lambda row: f"/topics/{row['slug']}")
    if op == "notes":
        ids = _topic_ids(state)
        if not ids:
            return {"items": [], "count": 0, "message": "No matching topic, so no notes were selected."}
        rows = db.query(
            "SELECT sec.id, sec.title, sec.kind, sec.body, t.slug AS topic_slug "
            "FROM note_sections sec JOIN notes n ON n.id=sec.note_id JOIN topics t ON t.id=n.topic_id "
            f"WHERE t.id IN ({','.join('?' for _ in ids)}) AND t.status='published' "
            "AND n.status='published' AND n.quality_level='standard' "
            "AND sec.kind IN ('definition', 'example', 'mistakes') ORDER BY t.slug, sec.order_index LIMIT ?",
            *ids, inputs["limit"],
        )
        for row in rows:
            row["body"] = plain(row["body"])
        return _items(rows, lambda row: f"/topics/{row['topic_slug']}")
    if op == "formulas":
        rows = _topic_select("formulas", "id, slug, name AS title, latex, meaning, constraints", state, inputs, order="slug")
        scope = "topic"
        if not rows:
            subjects = _subject_ids(state)
            if subjects:
                rows = db.query(
                    "SELECT id, slug, name AS title, latex, meaning, constraints FROM formulas "
                    f"WHERE topic_id IS NULL AND subject_id IN ({','.join('?' for _ in subjects)}) "
                    "ORDER BY slug LIMIT ?", *subjects, inputs["limit"],
                )
                scope = "subject (formulas are not linked to an individual topic)"
        return _items(rows, lambda row: "/formulas?slug=" + quote(row["slug"], safe="")) | {"scope": scope}
    if op == "questions":
        rows = _topic_select("questions", "id, slug, stem AS title, kind, difficulty", state, inputs, extra="is_active=1", order="slug")
        return _items(rows, lambda row: "/practice/questions?slug=" + quote(row["slug"], safe=""))
    if op == "cards":
        rows = _topic_select("flashcards", "id, front AS title, deck, hint, difficulty", state, inputs)
        scope = "topic"
        if not rows:
            subjects = _subject_ids(state)
            if subjects:
                rows = db.query(
                    "SELECT id, front AS title, deck, hint, difficulty FROM flashcards "
                    f"WHERE topic_id IS NULL AND subject_id IN ({','.join('?' for _ in subjects)}) "
                    "ORDER BY id LIMIT ?", *subjects, inputs["limit"],
                )
                scope = "subject (cards are not linked to an individual topic)"
        return _items(rows, lambda row: "/flashcards?card=" + quote(row["id"], safe="")) | {"scope": scope}
    if op in ("coding", "projects"):
        topics = state.get("topic", {}).get("items", [])
        text = inputs["q"] or " ".join(topic["title"] for topic in topics)
        tokens = list(dict.fromkeys(token.removesuffix("s") if len(token) > 4 else token
                                   for token in re.findall(r"[a-z0-9]+", text.lower()) if len(token) > 2))[:8]
        if not tokens:
            return {"items": [], "count": 0, "message": "No matching focus; nothing was selected."}
        table_name = "coding_problems" if op == "coding" else "projects"
        fields = ("title", "topics", "statement") if op == "coding" else ("title", "skills", "summary")
        conditions, params = [], []
        for token in tokens:
            for field in fields:
                conditions.append(f"LOWER(COALESCE({field}, '')) LIKE ?")
                params.append(f"%{token}%")
        where = "is_premium=0" if op == "coding" else "status='published'"
        where += " AND (" + " OR ".join(conditions) + ")"
        if op == "coding" and inputs["difficulty"]:
            where += " AND difficulty=?"
            params.append(inputs["difficulty"])
        projection = "id, slug, title, difficulty, statement" if op == "coding" else "id, slug, title, difficulty, summary, est_hours"
        rows = db.query(f"SELECT {projection} FROM {table_name} WHERE {where} ORDER BY slug LIMIT ?", *params, inputs["limit"])
        for row in rows:
            if "statement" in row:
                row["statement"] = plain(row["statement"])
        prefix = "/practice/problems/" if op == "coding" else "/projects/"
        return _items(rows, lambda row: prefix + row["slug"])
    if op == "schema":
        inspected = studio.schema()
        return {"items": [{"title": item["name"], "rows": item["row_count"], "columns": len(item["columns"]), "url": "/studio#table-" + item["name"]}
                          for item in inspected["tables"]], "count": inspected["table_count"]}
    if op == "coverage":
        rows = db.query(
            "SELECT t.slug, t.title, "
            "(SELECT COUNT(*) FROM notes n WHERE n.topic_id=t.id AND n.status='published') AS notes, "
            "(SELECT COUNT(*) FROM questions q WHERE q.topic_id=t.id AND q.is_active=1) AS questions, "
            "(SELECT COUNT(*) FROM formulas f WHERE f.topic_id=t.id) AS formulas "
            "FROM topics t WHERE t.status='published' ORDER BY t.slug"
        )
        gaps = [row for row in rows if not row["notes"] or not row["questions"]]
        return {"topics_checked": len(rows), "gap_count": len(gaps),
                "items": [dict(row, url=f"/topics/{row['slug']}") for row in gaps[:inputs["limit"]]],
                "count": len(gaps[:inputs["limit"]]), "message": "Gaps mean missing published notes or active questions, not a judgment of content correctness. Not every topic needs a formula."}
    if op == "pairings":
        entries = public_apis.list_apis()
        missing = [entry for entry in entries if not entry["topic_url"] or not entry["project_url"]]
        return {"checked": len(entries), "broken_pairings": len(missing), "count": len(missing),
                "items": [{"title": item["name"], "url": "/apis?slug=" + item["slug"]} for item in missing],
                "message": "Checks local topic/project pairings only; no external provider uptime check was performed."}
    if op == "plan":
        actions = []
        for dependency in node.depends_on:
            for item in state[dependency].get("items", []):
                actions.append({"title": item.get("title") or item.get("name") or "Catalogue item",
                                "url": item["url"], "step": dependency})
        return {"title": workflow.name, "summary": [{"step": key, "items": state[key].get("count", 0)} for key in node.depends_on],
                "items": actions, "count": len(actions),
                "message": "This is a suggested plan or inspection report. No answers were graded, no code was run, no progress or SRS state was changed."}
    raise WorkflowError("The template references an unsupported operator.")


def iter_steps(workflow: Workflow, inputs: dict) -> Iterator[dict]:
    state: dict[str, dict] = {}
    for node in workflow.nodes:
        if node.id in state or any(dependency not in state for dependency in node.depends_on):
            raise WorkflowError("The workflow dependency graph is invalid.")
        started = time.perf_counter()
        output = _operate(node, state, inputs, workflow)
        state[node.id] = output
        yield {"id": node.id, "label": node.label, "operator": node.operator,
               "depends_on": list(node.depends_on), "status": "succeeded", "output": output,
               "elapsed_ms": round((time.perf_counter() - started) * 1000, 2)}


def finish(workflow: Workflow, inputs: dict, steps: list[dict]) -> dict:
    return {"slug": workflow.slug, "name": workflow.name, "inputs": inputs, "steps": steps,
            "status": "succeeded", "report": steps[-1]["output"] if steps else {}, "read_only": True}


def run(slug: str, inputs: dict | None = None) -> dict:
    workflow, clean = prepare(slug, inputs)
    return finish(workflow, clean, list(iter_steps(workflow, clean)))


def run_node(slug: str, node_id: str, inputs: dict | None = None) -> dict:
    workflow, clean = prepare(slug, inputs)
    if not any(node.id == node_id for node in workflow.nodes):
        raise WorkflowError("Unknown node in this workflow.")
    for step in iter_steps(workflow, clean):
        if step["id"] == node_id:
            return step
    raise WorkflowError("The node could not be executed.")


def n8n_export(slug: str) -> dict:
    """Importable standard n8n nodes; EngineVerse operators remain server-side.

    Set the n8n variable engineverse_url to a self-hosted origin. Optional
    engineverse_topic chooses a topic. On account-gated instances configure an
    authenticated Cookie header/credential on the HTTP nodes. No credential or
    private dataset is exported; each GET recomputes its read-only dependencies.
    """
    workflow = get_workflow(slug)
    nodes = [{"id": str(uuid5(NAMESPACE_URL, f"engineverse:{slug}:trigger")), "name": "Start",
              "type": "n8n-nodes-base.manualTrigger", "typeVersion": 1, "position": [0, 0], "parameters": {}}]
    connections = {"Start": {"main": [[{"node": workflow.nodes[0].label, "type": "main", "index": 0}]]}}
    for index, node in enumerate(workflow.nodes):
        query = urlencode({"slug": workflow.slug, "node": node.id})
        url = "={{ $vars.engineverse_url + '/api/workflows?" + query + "&topic_slug=' + encodeURIComponent($vars.engineverse_topic || '" + workflow.default_topic + "') }}"
        nodes.append({"id": str(uuid5(NAMESPACE_URL, f"engineverse:{slug}:{node.id}")), "name": node.label,
                      "type": "n8n-nodes-base.httpRequest", "typeVersion": 4.2, "position": [(index + 1) * 260, 0],
                      "parameters": {"method": "GET", "url": url, "options": {"timeout": 10000}},
                      "notes": f"EngineVerse allowlisted operator: {node.operator}. Dependencies are recomputed read-only by the server.", "notesInFlow": True})
        if index + 1 < len(workflow.nodes):
            connections[node.label] = {"main": [[{"node": workflow.nodes[index + 1].label, "type": "main", "index": 0}]]}
    return {"name": "EngineVerse · " + workflow.name, "nodes": nodes, "connections": connections,
            "active": False, "settings": {"executionOrder": "v1"}, "pinData": {},
            "meta": {"templateCredsSetupCompleted": False}}


def catalogue(slug: str = "") -> list[dict]:
    result = []
    for workflow in WORKFLOWS:
        if slug and slug != workflow.slug:
            continue
        data = asdict(workflow)
        data["edges"] = [{"from": dependency, "to": node.id} for node in workflow.nodes for dependency in node.depends_on]
        data["n8n"] = n8n_export(workflow.slug)
        result.append(data)
    return result
