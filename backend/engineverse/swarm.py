"""A deterministic, citation-first multi-persona engineering review lab.

Inspired by MiroFish's (`666ghj/MiroFish`) multi-agent framing and PentAGI's
(`vxcontrol/pentagi`) autonomous security/verification auditing, not a model or
forecasting service. No network, LLM, private learner data, agent tools or
arbitrary execution. Every engineering finding is an extract from one of six
public catalogue source kinds. Trade-offs are explicitly review questions, not
invented engineering conclusions.
"""
from __future__ import annotations

import re
from dataclasses import asdict, dataclass
from typing import Any
from urllib.parse import quote

from . import db
from .security.sanitize import strip_html


@dataclass(frozen=True)
class Persona:
    slug: str
    name: str
    lens: str
    kinds: tuple[str, ...]
    section_kinds: tuple[str, ...]
    question: str


PERSONAS = (
    Persona("architect", "Systems architect", "Interfaces, dependencies and overall structure",
            ("topics", "projects", "note_sections"), ("definition", "industry", "applications"),
            "Which boundary or prerequisite needs to be fixed before integrating the parts?"),
    Persona("analyst", "Quantitative analyst", "Equations, units, assumptions and measurement",
            ("formulas", "note_sections", "topics"), ("formula", "derivation", "example"),
            "Which assumptions and units must be checked before using this evidence quantitatively?"),
    Persona("implementer", "Implementation engineer", "Algorithms, interfaces and a testable build",
            ("coding_problems", "projects", "note_sections"), ("example", "industry", "applications"),
            "What is the smallest implementation whose behavior can be checked against the cited brief?"),
    Persona("reviewer", "Safety & reliability reviewer", "Failure modes, constraints and verification",
            ("note_sections", "questions", "formulas"), ("mistakes", "points", "exam"),
            "Which failure case or constraint needs an explicit test rather than an assumption?"),
    Persona("coach", "Learning & delivery coach", "Prerequisites, assessment and delivery scope",
            ("questions", "projects", "topics"), ("interview", "exam", "simple"),
            "What evidence would demonstrate understanding before increasing the delivery scope?"),
)

SOURCE_KINDS = frozenset({"topics", "note_sections", "formulas", "questions", "coding_problems", "projects"})
MAX_PROMPT_CHARS = 400
MAX_SOURCES = 15
MAX_EXCERPT_CHARS = 520
DISCLOSURE = (
    "Deterministic multi-persona simulation assembled only from EngineVerse's public seeded catalogue. "
    "No external model or autonomous agents are running. Quotes are evidence; the cross-agent trade-offs "
    "are review prompts, not predictions, expert approval or safety advice. Check the source and its review state."
)
_STOP = frozenset("a an and are as at be by can could do does explain for from how i in into is it me my of on or our please should show tell that the their then this to us use we what when where which why will with would you your design build engineering reliable system compare help need about".split())


def plain(text: str, maximum: int = MAX_EXCERPT_CHARS) -> str:
    text = re.sub(r"\s+", " ", strip_html(text or "")).strip()
    if len(text) > maximum:
        return text[:maximum].rsplit(" ", 1)[0] + "…"
    return text


def _tokens(prompt: str) -> list[str]:
    return list(dict.fromkeys(word for word in re.findall(r"[a-z0-9]+", prompt.casefold())
                              if len(word) > 2 and word not in _STOP))[:10]


def _like(fields: tuple[str, ...], tokens: list[str]) -> tuple[str, list[str]]:
    clauses, params = [], []
    for token in tokens:
        for field in fields:
            clauses.append(f"LOWER(COALESCE({field}, '')) LIKE ?")
            params.append(f"%{token}%")
    return "(" + " OR ".join(clauses) + ")" if clauses else "0=1", params


def _retrieve(prompt: str, topic_slug: str = "", project_slug: str = "") -> list[dict]:
    tokens = _tokens(prompt)
    selected_topic = db.query_one("SELECT id, slug FROM topics WHERE slug=? AND status='published'", topic_slug) if topic_slug else None
    selected_project = db.query_one("SELECT id, slug FROM projects WHERE slug=? AND status='published'", project_slug) if project_slug else None
    if topic_slug and not selected_topic:
        raise ValueError("That topic is not in the published catalogue.")
    if project_slug and not selected_project:
        raise ValueError("That project is not in the published catalogue.")
    if not tokens and not (selected_topic or selected_project):
        return []

    specs = (
        ("topics", "SELECT t.id, t.slug, t.title, t.summary AS body, t.accuracy_state, '' AS section_kind FROM topics t",
         "t.status='published'", ("t.title", "t.summary", "t.tags"), "t.id", "t.slug"),
        ("note_sections", "SELECT sec.id, t.slug, sec.title, sec.body, t.accuracy_state, sec.kind AS section_kind FROM note_sections sec JOIN notes n ON n.id=sec.note_id JOIN topics t ON t.id=n.topic_id",
         "t.status='published' AND n.status='published' AND n.quality_level='standard'",
         ("t.title", "t.summary", "sec.title", "sec.body"), "t.id", "t.slug, sec.order_index"),
        ("formulas", "SELECT f.id, f.slug, f.name AS title, f.meaning AS body, f.latex, f.constraints, t.accuracy_state, '' AS section_kind FROM formulas f LEFT JOIN topics t ON t.id=f.topic_id",
         "f.topic_id IS NULL OR t.status='published'", ("f.name", "f.meaning", "f.application", "t.title"), "t.id", "f.slug"),
        ("questions", "SELECT q.id, q.slug, q.stem AS title, q.context AS body, t.accuracy_state, '' AS section_kind FROM questions q LEFT JOIN topics t ON t.id=q.topic_id",
         "q.is_active=1 AND (q.topic_id IS NULL OR t.status='published')", ("q.stem", "q.context", "q.tags", "t.title"), "t.id", "q.slug"),
        ("coding_problems", "SELECT p.id, p.slug, p.title, p.statement AS body, '' AS accuracy_state, '' AS section_kind FROM coding_problems p",
         "p.is_premium=0", ("p.title", "p.statement", "p.topics", "p.tags"), "", "p.slug"),
        ("projects", "SELECT p.id, p.slug, p.title, p.summary AS body, p.testing, p.architecture, '' AS accuracy_state, '' AS section_kind FROM projects p",
         "p.status='published'", ("p.title", "p.summary", "p.skills", "p.objective"), "", "p.slug"),
    )
    candidates = []
    for kind, select, public_where, fields, topic_key, order in specs:
        match, params = _like(fields, tokens)
        if selected_topic and topic_key:
            match, params = f"{topic_key}=?", [selected_topic["id"]]
        elif selected_project and kind == "projects":
            match, params = "p.id=?", [selected_project["id"]]
        rows = db.query(f"{select} WHERE ({public_where}) AND ({match}) ORDER BY {order} LIMIT 48", *params)
        for row in rows:
            body = row["body"] or (row["title"] if kind == "questions" else "")
            if kind == "formulas":
                body = f"{row['latex']} — {body}" + (f" Constraints: {row['constraints']}" if row.get("constraints") else "")
            elif kind == "projects":
                body += f" Testing: {row['testing']}" if row.get("testing") else ""
            haystack = f"{row['title']} {body}".casefold()
            matched = [token for token in tokens if token in haystack]
            score = sum(4 if token in row["title"].casefold() else 1 for token in matched)
            if (selected_topic and topic_key) or (selected_project and kind == "projects"):
                score += 20
            if not score:
                continue
            url = {
                "topics": f"/topics/{row['slug']}",
                "note_sections": f"/topics/{row['slug']}",
                "formulas": f"/formulas?slug={quote(row['slug'], safe='')}",
                "questions": f"/practice/questions?slug={quote(row['slug'], safe='')}",
                "coding_problems": f"/practice/problems/{row['slug']}",
                "projects": f"/projects/{row['slug']}",
            }[kind]
            candidates.append({"kind": kind, "entity_id": row["id"], "title": plain(row["title"], 180),
                               "url": url, "excerpt": plain(body), "review_state": row["accuracy_state"] or "not specified",
                               "section_kind": row["section_kind"], "score": score, "matched_terms": matched})
    # A stray word in a long note (e.g. frameworks "bake" in a pattern) is
    # not subject coverage. Require an independently matching catalogue entity.
    if not any(row["kind"] != "note_sections" for row in candidates):
        return []
    candidates.sort(key=lambda row: (-row["score"], row["kind"], row["entity_id"]))
    return candidates


def simulate(prompt: str, *, topic_slug: str = "", project_slug: str = "") -> dict[str, Any]:
    if not isinstance(prompt, str) or not 4 <= len(prompt.strip()) <= MAX_PROMPT_CHARS:
        raise ValueError(f"Describe a task in 4–{MAX_PROMPT_CHARS} characters.")
    if len(topic_slug) > 128 or len(project_slug) > 128:
        raise ValueError("Catalogue slugs must be at most 128 characters.")
    prompt = prompt.strip()
    candidates = _retrieve(prompt, topic_slug, project_slug)
    sources: list[dict] = []
    numbered: dict[tuple[str, str], int] = {}

    def cite(source: dict) -> int:
        key = (source["kind"], source["entity_id"])
        if key not in numbered:
            numbered[key] = len(sources) + 1
            sources.append({key: value for key, value in source.items() if key != "score"} | {"n": numbered[key]})
        return numbered[key]

    agents = []
    for persona in PERSONAS:
        eligible = [source for source in candidates if source["kind"] in persona.kinds and source["excerpt"]]
        eligible.sort(key=lambda source: (
            0 if source["section_kind"] in persona.section_kinds else 1,
            persona.kinds.index(source["kind"]), -source["score"], source["entity_id"],
        ))
        # Different source kinds when available, instead of two duplicate notes.
        chosen = []
        for source in eligible:
            if chosen and source["kind"] == chosen[0]["kind"]:
                continue
            chosen.append(source)
            if len(chosen) == 2:
                break
        findings = [{"quote": source["excerpt"], "source": cite(source)} for source in chosen]
        agents.append({"slug": persona.slug, "name": persona.name, "lens": persona.lens,
                       "status": "evidence-found" if findings else "insufficient-evidence",
                       "findings": findings, "review_question": persona.question,
                       "message": "Review the quoted evidence; no unquoted technical conclusion was generated." if findings
                       else "No suitable published evidence for this lens. This persona abstains."})

    tradeoffs = []
    pairs = (
        ("architect", "implementer", "Integration breadth versus a small, testable implementation"),
        ("analyst", "reviewer", "Quantitative usefulness versus validated assumptions and failure cases"),
        ("implementer", "coach", "Delivery pace versus demonstrated prerequisite understanding"),
    )
    by_slug = {agent["slug"]: agent for agent in agents}
    for left, right, tension in pairs:
        first, second = by_slug[left], by_slug[right]
        if not first["findings"] or not second["findings"]:
            continue
        refs = list(dict.fromkeys([first["findings"][0]["source"], second["findings"][0]["source"]]))
        tradeoffs.append({
            "agents": [first["name"], second["name"]], "tension": tension, "citations": refs,
            "challenge": first["review_question"] + " " + second["review_question"],
            "resolution": "Unresolved review prompt: use the cited briefs to specify a test or measurement. The catalogue alone does not justify a winning design.",
        })
    matched = sorted({term for source in sources for term in source["matched_terms"]})
    return {
        "prompt": prompt, "grounded": bool(sources), "agents": agents, "tradeoffs": tradeoffs,
        "sources": sources[:MAX_SOURCES], "rounds": ["Evidence review", "Cross-agent challenge"],
        "matched_terms": matched, "disclosure": DISCLOSURE,
        "message": "Evidence found for part of the request; gaps and design decisions remain unverified." if sources
        else "No relevant evidence in the public seeded catalogue. The swarm will not invent an answer.",
    }


def roster() -> list[dict]:
    return [asdict(persona) for persona in PERSONAS]
