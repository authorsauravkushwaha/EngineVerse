"""Coding problems, test cases and submissions (spec §16-§18)."""
from __future__ import annotations

import json
from typing import Any

from . import db
from .drivers import compose
from .judge import evaluate as judge_evaluate
from .judge import provider_info, run_custom
from .security.ids import now_ms, ulid


def _json(value: Any, fallback: Any) -> Any:
    if value in (None, ""):
        return fallback
    if isinstance(value, (list, dict)):
        return value
    try:
        return json.loads(value)
    except (ValueError, TypeError):
        return fallback


def list_languages() -> list[dict]:
    return db.query(
        "SELECT id, slug, name, icon, color, blurb, judge_slug, runnable, "
        "(SELECT count(*) FROM language_modules lm WHERE lm.language_id = programming_languages.id) AS module_count "
        "FROM programming_languages ORDER BY order_index, name"
    )


def language_by_slug(slug: str) -> dict | None:
    return db.query_one("SELECT * FROM programming_languages WHERE slug = ?", slug)


def modules_for_language(language_id: str) -> list[dict]:
    return db.query("SELECT * FROM language_modules WHERE language_id = ? ORDER BY order_index", language_id)


def list_problems(
    *, difficulty: str | None = None, topic: str | None = None, q: str | None = None,
    limit: int = 60, offset: int = 0,
) -> tuple[list[dict], int]:
    clauses = ["1=1"]
    args: list[Any] = []
    if difficulty:
        clauses.append("difficulty = ?")
        args.append(difficulty)
    if topic:
        clauses.append("(topics LIKE ? OR tags LIKE ?)")
        args += [f"%{topic}%"] * 2
    if q:
        clauses.append("(title LIKE ? OR statement LIKE ?)")
        args += [f"%{q}%"] * 2
    where = " AND ".join(clauses)
    total = int(db.scalar(f"SELECT count(*) AS c FROM coding_problems WHERE {where}", *args) or 0)
    rows = db.query(
        "SELECT id, slug, title, difficulty, topics, tags, expected_time, expected_space, solve_count, attempt_count "
        f"FROM coding_problems WHERE {where} "
        "ORDER BY CASE difficulty WHEN 'easy' THEN 0 WHEN 'medium' THEN 1 WHEN 'hard' THEN 2 ELSE 3 END, title "
        "LIMIT ? OFFSET ?",
        *args, limit, offset,
    )
    for row in rows:
        row["topics_data"] = _json(row.get("topics"), [])
        row["acceptance"] = round(row["solve_count"] / row["attempt_count"] * 100) if row["attempt_count"] else 0
    return rows, total


def get_problem(slug: str) -> dict | None:
    row = db.query_one("SELECT * FROM coding_problems WHERE slug = ?", slug)
    if not row:
        return None
    row["topics_data"] = _json(row.get("topics"), [])
    row["hints_data"] = _json(row.get("hints"), [])
    row["tags_data"] = _json(row.get("tags"), [])
    row["stubs"] = stubs_for(row["id"])
    row["samples"] = testcases_for(row["id"], samples_only=True)
    row["acceptance"] = round(row["solve_count"] / row["attempt_count"] * 100) if row["attempt_count"] else 0
    return row


def problem_by_id(problem_id: str) -> dict | None:
    return db.query_one("SELECT * FROM coding_problems WHERE id = ?", problem_id)


def stubs_for(problem_id: str) -> list[dict]:
    return db.query(
        "SELECT cs.language_id, cs.stub, cs.signature, l.slug, l.name, l.runnable, l.color "
        "FROM coding_problem_stubs cs JOIN programming_languages l ON l.id = cs.language_id "
        "WHERE cs.problem_id = ? ORDER BY l.order_index",
        problem_id,
    )


def testcases_for(problem_id: str, *, samples_only: bool = False) -> list[dict]:
    sql = "SELECT * FROM coding_testcases WHERE problem_id = ?"
    if samples_only:
        sql += " AND is_sample = 1"
    return db.query(sql + " ORDER BY order_index", problem_id)


def _program(problem_id: str, language: str, code: str) -> str:
    """Appends the problem's stdin/stdout harness to the learner's code."""
    problem = db.query_one("SELECT wrapper FROM coding_problems WHERE id = ?", problem_id) or {}
    stub = db.query_one(
        "SELECT s.signature FROM coding_problem_stubs s JOIN programming_languages l "
        "ON l.id = s.language_id WHERE s.problem_id = ? AND l.slug = ?",
        problem_id, language,
    ) or {}
    return compose(language, code, problem.get("wrapper") or "raw", stub.get("signature"))


def run(problem_id: str, language: str, code: str, custom_input: str = "") -> dict:
    """Runs against custom input, or the first sample test case."""
    code = _program(problem_id, language, code)
    samples = testcases_for(problem_id, samples_only=True)
    stdin = custom_input if custom_input else (samples[0]["input"] if samples else "")
    result = run_custom(language, code, stdin)
    expected = samples[0]["expected"] if (samples and not custom_input) else None
    from .judge import outputs_match

    return {
        "status": result.status,
        "stdout": result.stdout,
        "stderr": result.stderr,
        "runtimeMs": result.runtime_ms,
        "expected": expected,
        "passed": (outputs_match(result.stdout, expected) if expected is not None and result.status == "accepted" else None),
        "judge": provider_info(),
    }


def submit(user_id: str, problem_id: str, language: str, code: str) -> dict:
    cases = testcases_for(problem_id)
    if not cases:
        raise ValueError("problem has no test cases")

    evaluation = judge_evaluate(language, _program(problem_id, language, code), cases)

    accepted = evaluation.status == "accepted"
    first_accepted = (
        accepted
        and int(
            db.scalar(
                "SELECT count(*) AS c FROM coding_submissions WHERE user_id = ? AND problem_id = ? AND is_accepted = 1",
                user_id, problem_id,
            )
            or 0
        )
        == 0
    )

    submission_id = ulid()
    with db.transaction():
        db.execute(
            "INSERT INTO coding_submissions (id,user_id,problem_id,language,code,status,passed,total,runtime_ms,"
            "memory_kb,stderr,is_accepted,created_at) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)",
            submission_id, user_id, problem_id, language, code, evaluation.status, evaluation.passed,
            evaluation.total, evaluation.runtime_ms, evaluation.memory_kb, evaluation.stderr[:4000],
            1 if accepted else 0, now_ms(),
        )
        db.execute("UPDATE coding_problems SET attempt_count = attempt_count + 1 WHERE id = ?", problem_id)
        if first_accepted:
            db.execute("UPDATE coding_problems SET solve_count = solve_count + 1 WHERE id = ?", problem_id)

    xp = 30 if first_accepted else (8 if accepted else 3)
    from .progress import award_xp, bump_activity, evaluate_badges

    award_xp(user_id, xp, "code.accepted" if accepted else "code.submitted", "problem", problem_id)
    bump_activity(user_id, "coding_submissions", minutes=2, xp=xp)
    evaluate_badges(user_id)

    return {
        "id": submission_id,
        "status": evaluation.status,
        "passed": evaluation.passed,
        "total": evaluation.total,
        "runtimeMs": evaluation.runtime_ms,
        "memoryKb": evaluation.memory_kb,
        "stderr": evaluation.stderr,
        "xp": xp,
        "firstAccepted": first_accepted,
        "cases": [
            {
                "input": c.input,
                "expected": c.expected,
                "actual": c.actual,
                "passed": c.passed,
                "isSample": c.is_sample,
                "runtimeMs": c.runtime_ms,
            }
            for c in evaluation.cases
        ],
        "judge": provider_info(),
    }


def submissions_for(user_id: str, problem_id: str | None = None, limit: int = 20) -> list[dict]:
    if problem_id:
        return db.query(
            "SELECT id, language, status, passed, total, runtime_ms, memory_kb, is_accepted, created_at "
            "FROM coding_submissions WHERE user_id = ? AND problem_id = ? ORDER BY created_at DESC LIMIT ?",
            user_id, problem_id, limit,
        )
    return db.query(
        "SELECT cs.id, cs.language, cs.status, cs.passed, cs.total, cs.runtime_ms, cs.is_accepted, cs.created_at, "
        "cp.title, cp.slug FROM coding_submissions cs JOIN coding_problems cp ON cp.id = cs.problem_id "
        "WHERE cs.user_id = ? ORDER BY cs.created_at DESC LIMIT ?",
        user_id, limit,
    )


def saved_code(user_id: str, problem_id: str, language: str) -> str | None:
    row = db.query_one(
        "SELECT code FROM coding_submissions WHERE user_id = ? AND problem_id = ? AND language = ? "
        "ORDER BY created_at DESC LIMIT 1",
        user_id, problem_id, language,
    )
    return row["code"] if row else None


def solved_problem_ids(user_id: str) -> set[str]:
    rows = db.query(
        "SELECT DISTINCT problem_id FROM coding_submissions WHERE user_id = ? AND is_accepted = 1", user_id
    )
    return {row["problem_id"] for row in rows}


def problem_topics() -> list[dict]:
    rows = db.query("SELECT topics FROM coding_problems")
    counts: dict[str, int] = {}
    for row in rows:
        for topic in _json(row["topics"], []):
            counts[topic] = counts.get(topic, 0) + 1
    return [{"topic": key, "count": value} for key, value in sorted(counts.items(), key=lambda kv: -kv[1])]
