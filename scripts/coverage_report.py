#!/usr/bin/env python3
"""Print what the current database actually contains.

This is a count of seeded rows, not a claim that an engineering degree is
covered. Absence of a subject is not a roadmap and is not filled in here.

    python scripts/coverage_report.py
    python scripts/coverage_report.py --write docs/CURRICULUM_COVERAGE.md
"""
from __future__ import annotations

import argparse
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for path in (ROOT, os.path.join(ROOT, "backend")):
    if path not in sys.path:
        sys.path.insert(0, path)

from engineverse import db  # noqa: E402


def _count(sql: str, *params: object) -> int:
    return int(db.scalar(sql, *params, default=0) or 0)


def render() -> str:
    if not db.table_exists("branches"):
        return (
            "# Curriculum coverage\n\n"
            "No catalogue is loaded. Run `python scripts/seed.py` against a development "
            "database, then run this script again. This file does not invent subjects.\n"
        )
    lines = [
        "# Curriculum coverage",
        "",
        "This is a count of rows in the database this script was pointed at. It is not a",
        "statement that EngineVerse covers an engineering degree, a university syllabus,",
        "or a placement season. Subjects that are absent are simply absent — this report",
        "does not list planned or imagined ones.",
        "",
        "Regenerate it with `python scripts/coverage_report.py --write docs/CURRICULUM_COVERAGE.md`",
        "after seeding a development database. Do not treat a committed snapshot as live",
        "production content unless you just generated it from that database.",
        "",
        "## Totals",
        "",
        f"- Branches: {_count('SELECT count(*) AS c FROM branches')}",
        f"- Subjects: {_count('SELECT count(*) AS c FROM subjects')}",
        f"- Topics: {_count('SELECT count(*) AS c FROM topics')}",
        f"- Notes: {_count('SELECT count(*) AS c FROM notes')}",
        f"- Questions: {_count('SELECT count(*) AS c FROM questions')}",
        f"- Coding problems: {_count('SELECT count(*) AS c FROM coding_problems')}",
        "",
        "## By branch",
        "",
        "| Branch | Subjects | Topics | Questions |",
        "|---|---:|---:|---:|",
    ]
    branches = db.query("SELECT id, name FROM branches ORDER BY name")
    for branch in branches:
        branch_id = branch["id"]
        lines.append(
            "| {name} | {subjects} | {topics} | {questions} |".format(
                name=str(branch["name"]).replace("|", "\\|"),
                subjects=_count("SELECT count(*) AS c FROM subjects WHERE branch_id = ?", branch_id),
                topics=_count(
                    "SELECT count(*) AS c FROM topics t JOIN subjects s ON s.id = t.subject_id "
                    "WHERE s.branch_id = ?",
                    branch_id,
                ),
                questions=_count(
                    "SELECT count(*) AS c FROM questions q JOIN subjects s ON s.id = q.subject_id "
                    "WHERE s.branch_id = ?",
                    branch_id,
                ),
            )
        )
    lines.extend([
        "",
        "A branch with a handful of subjects is a sample, not a semester. Core learning",
        "stays free. Certificates issued by this application are not university degrees",
        "and must not be described as accredited.",
        "",
    ])
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description="Report seeded catalogue coverage.")
    parser.add_argument("--write", help="write the report to this path instead of stdout")
    args = parser.parse_args()
    body = render()
    if args.write:
        target = args.write if os.path.isabs(args.write) else os.path.join(ROOT, args.write)
        os.makedirs(os.path.dirname(target), exist_ok=True)
        with open(target, "w", encoding="utf-8") as handle:
            handle.write(body)
        print(f"Wrote {target}")
        return 0
    sys.stdout.write(body)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
