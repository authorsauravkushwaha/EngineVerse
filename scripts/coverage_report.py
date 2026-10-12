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

from engineverse import catalog, db  # noqa: E402

# Order the stream sections the way the site lists them rather than
# alphabetically, so the report reads like the navigation.
CATEGORY_ORDER = ("core", "cse", "electronics", "mechanical", "civil", "chemical", "bio", "other")


def _count(sql: str, *params: object) -> int:
    return int(db.scalar(sql, *params, default=0) or 0)


def _audience_args(category: str) -> list[str]:
    """Wildcards for one category inside the sheets' comma-separated audience.

    A plain ``LIKE '%bio%'`` would match a sheet aimed at ``biotech``, so the
    four cases (the whole value, first, last, middle) are spelled out.
    """
    return [category, f"{category},%", f"%,{category}", f"%,{category},%"]


def _audience_sql(column: str = "audience") -> str:
    return f"({column} = 'all' OR {column} = ? OR {column} LIKE ? OR {column} LIKE ? OR {column} LIKE ?)"


def _has_sheets() -> bool:
    """The sheet tables are newer than the original schema; an old database
    simply does not have them, and the report says so instead of crashing."""
    return db.table_exists("coding_sheets") and db.table_exists("coding_sheet_problems")


def render() -> str:
    if not db.table_exists("branches"):
        return (
            "# Curriculum coverage\n\n"
            "No catalogue is loaded. Run `python scripts/seed.py` against a development "
            "database, then run this script again. This file does not invent subjects.\n"
        )

    totals = {
        "branches": _count("SELECT count(*) AS c FROM branches"),
        "subjects": _count("SELECT count(*) AS c FROM subjects WHERE status = 'published'"),
        "topics": _count("SELECT count(*) AS c FROM topics WHERE status = 'published'"),
        "notes": _count("SELECT count(*) AS c FROM notes WHERE status = 'published'"),
        "sections": _count("SELECT count(*) AS c FROM note_sections"),
        "full_notes": _count(
            "SELECT count(*) AS c FROM notes n WHERE n.status = 'published' "
            "AND n.quality_level = 'standard' "
            "AND (SELECT count(*) FROM note_sections ns WHERE ns.note_id = n.id) = 13"
        ),
        "diagrams": _count("SELECT count(*) AS c FROM diagrams"),
        "models": _count("SELECT count(*) AS c FROM models_3d"),
        "formulas": _count("SELECT count(*) AS c FROM formulas"),
        "questions": _count("SELECT count(*) AS c FROM questions WHERE is_active = 1"),
        "dpp_sets": _count("SELECT count(*) AS c FROM dpp_sets WHERE published = 1"),
        "dpp_slots": _count(
            "SELECT count(*) AS c FROM dpp_questions dq JOIN dpp_sets d ON d.id = dq.set_id "
            "WHERE d.published = 1"
        ),
        "dpp_subjects": _count(
            "SELECT count(DISTINCT q.subject_id) AS c FROM dpp_questions dq "
            "JOIN dpp_sets d ON d.id = dq.set_id JOIN questions q ON q.id = dq.question_id "
            "WHERE d.published = 1 AND q.is_active = 1"
        ),
        "dpp_languages": _count(
            "SELECT count(DISTINCT lc.language_id) AS c FROM dpp_questions dq "
            "JOIN dpp_sets d ON d.id = dq.set_id JOIN language_checkpoints lc ON lc.question_id = dq.question_id "
            "WHERE d.published = 1"
        ),
        "coding_problems": _count("SELECT count(*) AS c FROM coding_problems"),
        "coding_sheets": _count("SELECT count(*) AS c FROM coding_sheets WHERE status = 'published'")
        if _has_sheets()
        else 0,
        "sheet_slots": _count("SELECT count(*) AS c FROM coding_sheet_problems") if _has_sheets() else 0,
        # A problem in no sheet is invisible to anyone browsing by sheet rather
        # than by difficulty, which is most learners, so it is called out.
        "unplaced_problems": _count(
            "SELECT count(*) AS c FROM coding_problems cp WHERE NOT EXISTS "
            "(SELECT 1 FROM coding_sheet_problems sp WHERE sp.problem_id = cp.id)"
        )
        if _has_sheets()
        else 0,
        "languages": _count("SELECT count(*) AS c FROM programming_languages"),
        "language_modules": _count("SELECT count(*) AS c FROM language_modules"),
        "staged_modules": _count(
            "SELECT count(*) AS c FROM language_modules WHERE stage IN "
            "('foundations', 'working_practice', 'advanced_engineering')"
        ),
        "language_stages": _count("SELECT count(*) AS c FROM language_stages"),
        "checkpoints": _count("SELECT count(*) AS c FROM language_checkpoints"),
        "checkpoint_questions": _count(
            "SELECT count(*) AS c FROM language_checkpoints lc JOIN questions q ON q.id = lc.question_id "
            "WHERE q.is_active = 1"
        ),
        "projects": _count("SELECT count(*) AS c FROM projects WHERE status = 'published'"),
        "project_steps": _count(
            "SELECT count(*) AS c FROM project_steps ps JOIN projects p ON p.id = ps.project_id "
            "WHERE p.status = 'published'"
        ),
        "project_resources": _count(
            "SELECT count(*) AS c FROM project_resources pr JOIN projects p ON p.id = pr.project_id "
            "WHERE p.status = 'published'"
        ),
        "capstones": _count(
            "SELECT count(*) AS c FROM projects WHERE status = 'published' AND language_id IS NOT NULL"
        ),
    }
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
        f"- Branches: {totals['branches']}",
        f"- Published subjects: {totals['subjects']}",
        f"- Published topics: {totals['topics']}",
        f"- Published notes across all reading depths: {totals['notes']}",
        f"- Note sections: {totals['sections']}",
        f"- Standard notes with all 13 sections: {totals['full_notes']}",
        f"- Diagrams: {totals['diagrams']}",
        f"- 3D models: {totals['models']}",
        f"- Formulas: {totals['formulas']}",
        f"- Active questions: {totals['questions']}",
        f"- Published DPP sets: {totals['dpp_sets']}",
        f"- Published DPP question slots: {totals['dpp_slots']}",
        f"- Subjects represented in published DPPs: {totals['dpp_subjects']}",
        f"- Language tracks represented in published DPPs: {totals['dpp_languages']}",
        f"- Coding problems: {totals['coding_problems']}",
        f"- Curated coding sheets: {totals['coding_sheets']} "
        f"({totals['sheet_slots']} problem slots; "
        f"{totals['unplaced_problems']} problems in no sheet)"
        if _has_sheets()
        else "- Curated coding sheets: this database predates the sheet tables",
        f"- Programming languages: {totals['languages']}",
        f"- Language modules: {totals['language_modules']} "
        f"({totals['staged_modules']} assigned to a stage)",
        f"- Language stages: {totals['language_stages']}",
        f"- Stage checkpoint links: {totals['checkpoints']} "
        f"({totals['checkpoint_questions']} pointing at active questions)",
        f"- Published project briefs: {totals['projects']}",
        f"- Project steps: {totals['project_steps']}",
        f"- Project resources: {totals['project_resources']}",
        f"- Language-linked capstone briefs: {totals['capstones']}",
        "",
        "## Coding sheets by stream",
        "",
        "Each row is one branch category. A sheet is reachable from a stream when it",
        "is written for everyone or names that category; the problem count is the",
        "distinct bank problems those sheets reach, so a problem in two sheets is",
        "counted once.",
        "",
        "| Stream | Sheets | Problems reachable |",
        "|---|---:|---:|",
    ]
    if _has_sheets():
        present = [
            row["category"]
            for row in db.query(
                "SELECT DISTINCT category FROM branches WHERE is_active = 1 AND category IS NOT NULL"
            )
        ]
        present.sort(
            key=lambda key: (
                CATEGORY_ORDER.index(key) if key in CATEGORY_ORDER else len(CATEGORY_ORDER),
                key,
            )
        )
        for category in present:
            args = _audience_args(category)
            sheets = _count(
                "SELECT count(*) AS c FROM coding_sheets WHERE status = 'published' AND "
                + _audience_sql(),
                *args,
            )
            reachable = _count(
                "SELECT count(DISTINCT sp.problem_id) AS c FROM coding_sheet_problems sp "
                "JOIN coding_sheets s ON s.id = sp.sheet_id "
                "JOIN coding_problems cp ON cp.id = sp.problem_id "
                "WHERE s.status = 'published' AND " + _audience_sql("s.audience"),
                *args,
            )
            lines.append(f"| {catalog.category_name(category)} | {sheets} | {reachable} |")
    else:
        lines.append("| — | 0 | 0 |")
    lines.extend([
        "",
        "A stream with no sheet of its own still gets the sheets written for every",
        "branch - the pattern sheets and the interview set - so a learner is never left",
        "with an empty page.",
        "",
        "## Programming paths",
        "",
        "Each path progresses through Foundations, Working Practice and Advanced Engineering. "
        "A stage with modules but no checkpoint, or a capstone column that is empty, is a gap - "
        "not a variant.",
        "",
        "| Language | Modules | Foundations | Working Practice | Advanced Engineering | Checkpoints | Capstone |",
        "|---|---:|---:|---:|---:|---:|---|",
    ])
    for language in db.query("SELECT id, name FROM programming_languages ORDER BY order_index, name"):
        language_id = language["id"]

        def stage_modules(stage: str) -> int:
            return _count(
                "SELECT count(*) AS c FROM language_modules WHERE language_id = ? AND stage = ?",
                language_id, stage,
            )

        capstone = db.query_one(
            "SELECT slug FROM projects WHERE language_id = ? AND status = 'published' "
            "ORDER BY order_index LIMIT 1",
            language_id,
        )
        lines.append(
            "| {name} | {modules} | {foundations} | {working} | {advanced} | {checkpoints} | {capstone} |".format(
                name=str(language["name"]).replace("|", "\\|"),
                modules=_count("SELECT count(*) AS c FROM language_modules WHERE language_id = ?", language_id),
                foundations=stage_modules("foundations"),
                working=stage_modules("working_practice"),
                advanced=stage_modules("advanced_engineering"),
                checkpoints=_count("SELECT count(*) AS c FROM language_checkpoints WHERE language_id = ?", language_id),
                capstone=f"[{capstone['slug']}](/projects/{capstone['slug']})" if capstone else "—",
            )
        )
    lines.extend([
        "",
        "## By branch",
        "",
        "| Branch | Subjects | Topics | Notes | Questions |",
        "|---|---:|---:|---:|---:|",
    ])
    branches = db.query("SELECT id, name FROM branches ORDER BY name")
    for branch in branches:
        branch_id = branch["id"]
        lines.append(
            "| {name} | {subjects} | {topics} | {notes} | {questions} |".format(
                name=str(branch["name"]).replace("|", "\\|"),
                subjects=_count(
                    "SELECT count(*) AS c FROM subjects WHERE branch_id = ? AND status = 'published'", branch_id
                ),
                topics=_count(
                    "SELECT count(*) AS c FROM topics t JOIN subjects s ON s.id = t.subject_id "
                    "WHERE s.branch_id = ? AND s.status = 'published' AND t.status = 'published'",
                    branch_id,
                ),
                notes=_count(
                    "SELECT count(*) AS c FROM notes n JOIN topics t ON t.id = n.topic_id "
                    "JOIN subjects s ON s.id = t.subject_id WHERE s.branch_id = ? "
                    "AND s.status = 'published' AND t.status = 'published' AND n.status = 'published'",
                    branch_id,
                ),
                questions=_count(
                    "SELECT count(*) AS c FROM questions q JOIN subjects s ON s.id = q.subject_id "
                    "WHERE s.branch_id = ? AND s.status = 'published' AND q.is_active = 1",
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
