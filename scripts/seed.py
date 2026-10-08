#!/usr/bin/env python3
"""EngineVerse database seeder.

Builds a complete, realistic content library from the modules in ``seed_data/``.
Safe to re-run: it wipes content tables first and rebuilds from scratch, so a
fresh checkout and a developer machine converge on exactly the same data.

Usage
-----
    python scripts/seed.py            # seed into the configured database
    python scripts/seed.py --fresh    # drop and recreate the schema first
    python scripts/seed.py --stats    # print a row count summary and exit
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import datetime, timedelta, timezone

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for path in (ROOT, os.path.join(ROOT, "backend")):
    if path not in sys.path:
        sys.path.insert(0, path)

from engineverse import auth, brand, db, diagrams, models3d, progress, search  # noqa: E402
from engineverse.judge import local as judge_local  # noqa: E402
from engineverse.security.ids import ulid  # noqa: E402
from engineverse.security.sanitize import slugify  # noqa: E402

from seed_data import branches as branch_data  # noqa: E402
from seed_data import catalog as catalog_data  # noqa: E402
from seed_data import library_data  # noqa: E402
from seed_data import models_3d as model_content  # noqa: E402
from seed_data import flashcards_extra as flashcard_content  # noqa: E402
from seed_data import diagrams_data  # noqa: E402
from seed_data import resource_sources  # noqa: E402
from seed_data import practice_data  # noqa: E402
from seed_data import topics_core  # noqa: E402
from seed_data import topics_cse  # noqa: E402


def now_ms() -> int:
    return int(datetime.now(timezone.utc).timestamp() * 1000)


def jdump(value) -> str:
    return json.dumps(value, ensure_ascii=False)


# ---------------------------------------------------------------------------
# The 13-section engineering note template.
#
#   1 simple        2 definition     3 intuition      4 points
#   5 formula       6 derivation     7 example        8 applications
#   9 mistakes     10 exam          11 interview     12 diagram
#  13 industry
#
# Every topic is expanded into up to four reading depths. Each depth is a real,
# distinct document assembled from the authored material, not a copy with a
# different label:
#
#   beginner -> sections 1, 4, 7, 9          (short first read)
#   standard -> all 13 sections              (the full note)
#   advanced -> 2, 5, 6, 7, 10               (rigour and derivation)
#   industry -> 8, 13, 11, 9                 (how it is used at work)
# ---------------------------------------------------------------------------

SECTIONS = [
    ("simple", "Explain it simply", "remember"),
    ("definition", "Formal definition", None),
    ("intuition", "Intuition - why it works", "remember"),
    ("points", "Key points", None),
    ("formula", "Formula and variables", "exam"),
    ("derivation", "Derivation", None),
    ("example", "Worked example", "exam"),
    ("applications", "Real-world applications", "realworld"),
    ("mistakes", "Common mistakes", "warning"),
    ("exam", "Exam questions", "exam"),
    ("interview", "Interview questions", "interview"),
    ("diagram", "Diagram", None),
    ("industry", "Industry practice", "realworld"),
]

DEPTHS = {
    "beginner": ["simple", "points", "example", "mistakes"],
    "standard": [kind for kind, _, _ in SECTIONS],
    "advanced": ["definition", "formula", "derivation", "example", "exam"],
    "industry": ["applications", "industry", "interview", "mistakes"],
}


def formula_body(formula: dict) -> str:
    lines = [f"**{formula['name']}**", "", f"$$ {formula['latex']} $$", "", "| Symbol | Meaning | Unit |",
             "| --- | --- | --- |"]
    for variable in formula.get("variables", []):
        lines.append(f"| ${variable['s']}$ | {variable['n']} | {variable['u']} |")
    if formula.get("conditions"):
        lines += ["", f"**Valid when:** {formula['conditions']}"]
    return "\n".join(lines)


def example_body(example: dict) -> str:
    parts = [f"**Problem.** {example['problem']}"]
    if example.get("approach"):
        parts.append(f"\n**Approach.** {example['approach']}")
    if example.get("solution"):
        parts.append(f"\n**Solution.**\n\n{example['solution']}")
    if example.get("answer"):
        parts.append(f"\n**Answer.** {example['answer']}")
    return "\n".join(parts)


def bullet_list(items: list[str]) -> str:
    return "\n".join(f"- {item}" for item in items)


def numbered_list(items: list[str]) -> str:
    return "\n".join(f"{index}. {item}" for index, item in enumerate(items, start=1))


def section_body(kind: str, topic: dict, diagram: dict | None) -> str:
    if kind == "simple":
        return topic["simple"] or topic["summary"]
    if kind == "definition":
        return topic["definition"]
    if kind == "intuition":
        return topic["intuition"]
    if kind == "points":
        return bullet_list(topic["points"])
    if kind == "formula":
        return formula_body(topic["formula"]) if topic["formula"] else ""
    if kind == "derivation":
        return topic["derivation"]
    if kind == "example":
        return example_body(topic["example"]) if topic["example"] else ""
    if kind == "applications":
        return bullet_list(topic["applications"])
    if kind == "mistakes":
        return bullet_list(topic["mistakes"])
    if kind == "exam":
        return numbered_list(topic["exam"])
    if kind == "interview":
        return numbered_list(topic["interview"])
    if kind == "industry":
        return topic["industry"]
    if kind == "diagram":
        if diagram:
            return f"_See the interactive diagram: **{diagram['title']}** below._\n\n{diagram['caption']}"
        return ""
    return ""


# ---------------------------------------------------------------------------
# Catalogue
# ---------------------------------------------------------------------------

def seed_config() -> None:
    brand.set_many(library_data.SITE_CONFIG)


COLLEGE_IDS: dict[str, str] = {}


def seed_universities() -> dict[str, str]:
    university_ids: dict[str, str] = {}
    with db.transaction():
        for slug, name, code, country, region in catalog_data.UNIVERSITIES:
            university_ids[slug] = slug
            db.execute(
                "INSERT INTO universities (id,name,code,country,region,website,created_at) VALUES (?,?,?,?,?,NULL,?) "
                "ON CONFLICT(id) DO NOTHING",
                slug, name, code, country, region, now_ms(),
            )
        for university_slug, name, city in catalog_data.COLLEGES:
            country = next(
                (entry[3] for entry in catalog_data.UNIVERSITIES if entry[0] == university_slug), "India"
            )
            college_id = slugify(name)
            COLLEGE_IDS[name] = college_id
            db.execute(
                "INSERT INTO colleges (id,university_id,name,city,country) VALUES (?,?,?,?,?) "
                "ON CONFLICT(id) DO NOTHING",
                college_id, university_ids.get(university_slug), name, city, country,
            )
    return university_ids


def seed_branches() -> dict[str, str]:
    ids: dict[str, str] = {}
    with db.transaction():
        for index, (slug, name, category, icon, color, description) in enumerate(branch_data.BRANCHES):
            ids[slug] = slug
            db.execute(
                "INSERT INTO branches (id,slug,name,category,description,icon,color,order_index,is_active) "
                "VALUES (?,?,?,?,?,?,?,?,1) ON CONFLICT(id) DO UPDATE SET name=excluded.name, "
                "category=excluded.category, description=excluded.description, icon=excluded.icon, "
                "color=excluded.color",
                slug, slug, name, category, description, icon, color, index,
            )
    return ids


def seed_semesters() -> None:
    with db.transaction():
        for semester_id, label, year in catalog_data.SEMESTERS:
            db.execute(
                "INSERT INTO semesters (id,label,year) VALUES (?,?,?) ON CONFLICT(id) DO UPDATE SET label=excluded.label",
                semester_id, label, year,
            )


def seed_subjects(branch_ids: dict[str, str]) -> dict[str, str]:
    ids: dict[str, str] = {}
    with db.transaction():
        for index, entry in enumerate(catalog_data.SUBJECTS):
            slug, name, branch_slug, semester, first_year, code, credits, difficulty, icon, color, description = entry
            subject_id = slug
            ids[slug] = subject_id
            db.execute(
                "INSERT INTO subjects (id,slug,name,branch_id,semester_id,code,credits,difficulty,description,icon,"
                "color,is_first_year,order_index,status) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,'published') "
                "ON CONFLICT(id) DO UPDATE SET name=excluded.name, description=excluded.description",
                subject_id, slug, name, branch_ids.get(branch_slug) if branch_slug else None, semester,
                code, credits, difficulty, description, icon, color, 1 if first_year else 0, index,
            )
    return ids


def seed_curricula(subject_ids: dict[str, str], branch_ids: dict[str, str], university_ids: dict[str, str]) -> None:
    """Bind a real subject list to each (university, branch) so nothing is hard-coded in the UI."""
    by_branch: dict[str, list[tuple[str, int]]] = {}
    for entry in catalog_data.SUBJECTS:
        slug, branch_slug, semester = entry[0], entry[2], entry[3]
        if branch_slug:
            by_branch.setdefault(branch_slug, []).append((slug, semester))
        else:
            # First-year common subjects belong to every branch.
            for every in branch_ids:
                by_branch.setdefault(every, []).append((slug, semester))

    with db.transaction():
        for university_slug in ("generic", "NPTEL", "MITOCW", "IIT"):
            university_id = university_ids.get(university_slug)
            if not university_id:
                continue
            for branch_slug, subjects in by_branch.items():
                branch_id = branch_ids.get(branch_slug)
                if not branch_id:
                    continue
                branch_name = branch_slug.replace("-", " ").title()
                curriculum_id = f"{university_slug}-{branch_slug}"
                db.execute(
                    "INSERT INTO curricula (id,university_id,branch_id,name,effective_year,is_active) "
                    "VALUES (?,?,?,?,2024,1) ON CONFLICT(id) DO NOTHING",
                    curriculum_id, university_id, branch_id, f"{branch_name} Syllabus 2024",
                )
                for subject_slug, semester in subjects:
                    subject_id = subject_ids.get(subject_slug)
                    if not subject_id:
                        continue
                    db.execute(
                        "INSERT INTO curriculum_subjects (curriculum_id,subject_id,semester_id,is_core) "
                        "VALUES (?,?,?,1) ON CONFLICT(curriculum_id,subject_id) DO NOTHING",
                        curriculum_id, subject_id, semester,
                    )


# ---------------------------------------------------------------------------
# Topics, modules, notes, diagrams, formulas
# ---------------------------------------------------------------------------

def seed_topics(subject_ids: dict[str, str]) -> dict[str, str]:
    """Returns slug -> topic id for every seeded topic."""
    all_topics = list(topics_cse.TOPICS) + list(topics_core.TOPICS)
    topic_ids: dict[str, str] = {}
    module_ids: dict[str, str] = {}
    per_subject_index: dict[str, int] = {}
    ts = now_ms()

    with db.transaction():
        for entry in all_topics:
            subject_slug = entry["subject"]
            subject_id = subject_ids.get(subject_slug)
            if not subject_id:
                print(f"  ! skipped topic '{entry['title']}' - unknown subject '{subject_slug}'")
                continue
            slug = slugify(entry["title"])
            if slug in topic_ids:
                continue
            order = per_subject_index.get(subject_slug, 0)
            per_subject_index[subject_slug] = order + 1
            topic_id = slug
            topic_ids[slug] = topic_id
            db.execute(
                "INSERT INTO topics (id,slug,subject_id,module_id,title,summary,difficulty,est_minutes,order_index,"
                "prerequisites,tags,status,accuracy_state,version,view_count,created_at,updated_at) "
                "VALUES (?,?,?,?,?,?,?,?,?,'[]',?,'published','reviewed',1,0,?,?) "
                "ON CONFLICT(id) DO UPDATE SET title=excluded.title, summary=excluded.summary",
                topic_id, slug, subject_id, None, entry["title"], entry["summary"], entry["difficulty"],
                entry["minutes"], order, jdump(entry["tags"]), ts, ts,
            )

        # One module per subject so the subject page can group its topics.
        for subject_slug, subject_id in subject_ids.items():
            count = db.scalar("SELECT count(*) AS c FROM topics WHERE subject_id = ?", subject_id)
            if not count:
                continue
            name = db.scalar("SELECT name FROM subjects WHERE id = ?", subject_id) or subject_slug
            module_id = f"{subject_slug}::essentials"
            module_ids[subject_slug] = module_id
            db.execute(
                "INSERT INTO modules (id,subject_id,slug,title,summary,order_index) VALUES (?,?,?,?,?,0) "
                "ON CONFLICT(id) DO NOTHING",
                module_id, subject_id, "essentials", f"{name} Essentials",
                f"The core topics of {name}, in reading order.",
            )
            db.execute("UPDATE topics SET module_id = ? WHERE subject_id = ?", module_id, subject_id)

    return topic_ids


def seed_notes(topic_ids: dict[str, str]) -> int:
    all_topics = {slugify(entry["title"]): entry for entry in list(topics_cse.TOPICS) + list(topics_core.TOPICS)}
    ts = now_ms()
    notes = 0
    with db.transaction():
        for slug, topic_id in topic_ids.items():
            entry = all_topics.get(slug)
            if not entry:
                continue
            diagram = library_data.DIAGRAMS.get(entry.get("diagram") or "")
            for depth, kinds in DEPTHS.items():
                wanted = [k for k in kinds if section_body(k, entry, diagram)]
                if not wanted:
                    continue
                note_id = f"{slug}::{depth}"
                db.execute(
                    "INSERT INTO notes (id,topic_id,quality_level,language,status,version,created_at,updated_at) "
                    "VALUES (?,?,?,'en','published',1,?,?) ON CONFLICT(id) DO NOTHING",
                    note_id, topic_id, depth, ts, ts,
                )
                for order, kind in enumerate(wanted):
                    title = next(t for k, t, _ in SECTIONS if k == kind)
                    callout = next(c for k, _, c in SECTIONS if k == kind)
                    db.execute(
                        "INSERT INTO note_sections (id,note_id,kind,title,body,callout,order_index) VALUES (?,?,?,?,?,?,?) "
                        "ON CONFLICT(id) DO UPDATE SET body=excluded.body",
                        f"{note_id}::{kind}", note_id, kind, title, section_body(kind, entry, diagram), callout, order,
                    )
                notes += 1
    return notes


def seed_diagrams(topic_ids: dict[str, str]) -> int:
    """Render one diagram per topic from ``diagrams_data`` and store it.

    Every diagram is built through ``diagrams.render()``, which validates the
    scene and rebuilds the SVG from scratch. A topic with no diagram authored
    raises rather than being skipped: six of forty-eight topics had a diagram
    under the old hand-written path, and the other forty-two rendered their
    notes with no picture at all while the seed reported success.
    """
    missing = sorted(set(topic_ids) - set(diagrams_data.all_slugs()))
    if missing:
        raise KeyError(f"{len(missing)} topics have no diagram authored: {missing[:6]}")
    count = 0
    with db.transaction():
        for slug, topic_id in topic_ids.items():
            scene = diagrams_data.build(slug)
            spec, hotspots = diagrams.render(scene)
            db.execute(
                "INSERT INTO diagrams (id,topic_id,title,kind,spec,caption,hotspots,source_ref,created_at) "
                "VALUES (?,?,?,?,?,?,?,'EngineVerse',?) ON CONFLICT(id) DO UPDATE SET spec=excluded.spec",
                f"{slug}::diagram", topic_id, scene["title"], "svg", spec, scene["caption"],
                hotspots, now_ms(),
            )
            count += 1
    return count


def seed_models_3d(topic_ids: dict[str, str]) -> int:
    """Write the 3D models, validating each one on the way in.

    A scene that does not survive ``validate_scene()`` is skipped with a
    warning rather than stored, so a bad edit to seed_data/models_3d.py shows
    up here instead of as a broken page later.
    """
    count = 0
    with db.transaction():
        for slug, topic_id in sorted(topic_ids.items()):
            entry = model_content.MODELS_3D.get(slug)
            if not entry:
                continue
            encoded = models3d.scene_json(entry["scene"])
            if not encoded:
                print(f"  ! skipped 3D model for {slug}: the scene did not validate")
                continue
            db.execute(
                "INSERT INTO models_3d (id,topic_id,title,caption,scene,source_ref,order_index,created_at) "
                "VALUES (?,?,?,?,?, 'EngineVerse', 0, ?) "
                "ON CONFLICT(id) DO UPDATE SET title=excluded.title, caption=excluded.caption, scene=excluded.scene",
                f"{slug}::3d", topic_id, entry["title"], entry["caption"], encoded, now_ms(),
            )
            count += 1
    return count


def seed_formulas(subject_ids: dict[str, str], topic_ids: dict[str, str]) -> None:
    with db.transaction():
        for index, entry in enumerate(library_data.FORMULAS):
            slug, subject_slug, category, name, latex, variables, meaning, application, example, constraints = entry
            db.execute(
                "INSERT INTO formulas (id,slug,subject_id,topic_id,category,name,latex,variables,meaning,application,"
                "example_latex,constraints,order_index) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?) "
                "ON CONFLICT(slug) DO UPDATE SET latex=excluded.latex, meaning=excluded.meaning",
                slug, slug, subject_ids.get(subject_slug), topic_ids.get(slug), category, name, latex,
                jdump([{"symbol": s, "name": n, "unit": u} for s, n, u in variables]),
                meaning, application, example, constraints, index,
            )


# ---------------------------------------------------------------------------
# Practice
# ---------------------------------------------------------------------------

def seed_questions(subject_ids: dict[str, str]) -> dict[str, str]:
    ids: dict[str, str] = {}
    with db.transaction():
        for entry in practice_data.QUESTIONS:
            slug = slugify(entry["title"])
            if slug in ids:
                continue
            question_id = slug
            ids[slug] = question_id
            db.execute(
                "INSERT INTO questions (id,slug,topic_id,subject_id,kind,difficulty,stem,explanation,answer_index,"
                "tags,time_weight,is_active,created_at) VALUES (?,?,NULL,?,'mcq',?,?,?,?,?,1,1,?) "
                "ON CONFLICT(id) DO NOTHING",
                question_id, slug, subject_ids.get(entry["subject"]), entry["difficulty"], entry["statement"],
                entry["explanation"], entry["correct"], jdump(entry["tags"] + [entry["source"]]), now_ms(),
            )
            for position, option in enumerate(entry["options"]):
                label = chr(ord("A") + position)
                db.execute(
                    "INSERT INTO question_options (id,question_id,label,body,is_correct,order_index) "
                    "VALUES (?,?,?,?,?,?) ON CONFLICT(id) DO UPDATE SET body=excluded.body",
                    f"{question_id}::{label}", question_id, label, option,
                    1 if position == entry["correct"] else 0, position,
                )
    return ids


def seed_dpp(question_ids: dict[str, str], subject_ids: dict[str, str]) -> int:
    """Fourteen days of Daily Practice Problem sets, five questions each."""
    by_subject: dict[str, list[str]] = {}
    for entry in practice_data.QUESTIONS:
        slug = slugify(entry["title"])
        if slug in question_ids:
            by_subject.setdefault(entry["subject"], []).append(slug)
    if not by_subject:
        return 0

    ordered: list[tuple[str, str]] = []
    for subject_slug, slugs in by_subject.items():
        for slug in slugs:
            ordered.append((subject_slug, slug))

    sets = 0
    today = datetime.now(timezone.utc).date()
    with db.transaction():
        for day_offset in range(-7, 7):
            day = today + timedelta(days=day_offset)
            window = ordered[(day_offset + 7) * 5:(day_offset + 7) * 5 + 5]
            if not window:
                window = ordered[:5]
            set_id = f"dpp-{day.isoformat()}"
            db.execute(
                "INSERT INTO dpp_sets (id,date,title,subject_id,difficulty,duration_minutes,published,created_at) "
                "VALUES (?,?,?,NULL,'mixed',30,1,?) ON CONFLICT(id) DO NOTHING",
                set_id, day.isoformat(), f"Daily Practice - {day.strftime('%d %B %Y')}", now_ms(),
            )
            for position, (_subject, slug) in enumerate(window):
                db.execute(
                    "INSERT OR IGNORE INTO dpp_questions (set_id,question_id,position) VALUES (?,?,?)",
                    set_id, question_ids[slug], position,
                )
            sets += 1
    return sets


# ---------------------------------------------------------------------------
# Coding
# ---------------------------------------------------------------------------

def seed_languages() -> dict[str, str]:
    ids: dict[str, str] = {}
    with db.transaction():
        for index, (slug, name, icon, color, blurb, judge) in enumerate(library_data.LANGUAGES):
            ids[slug] = slug
            # runnable is derived, not asserted. It used to be hard-coded to 1,
            # which offered SQL in the code editor's language picker with no
            # warning and then returned "unsupported_language" on Run - the data
            # already says judge_slug is None for SQL, so the honest value was
            # sitting right there and being thrown away.
            runnable = 1 if judge in judge_local.RUNNERS else 0
            db.execute(
                "INSERT INTO programming_languages (id,slug,name,icon,color,blurb,judge_slug,runnable,order_index) "
                "VALUES (?,?,?,?,?,?,?,?,?) ON CONFLICT(id) DO UPDATE SET blurb=excluded.blurb, "
                "judge_slug=excluded.judge_slug, runnable=excluded.runnable",
                slug, slug, name, icon, color, blurb, judge, runnable, index,
            )
        for language_slug, modules in library_data.LANGUAGE_MODULES.items():
            language_id = ids.get(language_slug)
            if not language_id:
                continue
            for order, (slug, title, summary, body, example, exercise) in enumerate(modules):
                db.execute(
                    "INSERT INTO language_modules (id,language_id,slug,title,summary,body,example,exercise,order_index) "
                    "VALUES (?,?,?,?,?,?,?,?,?) ON CONFLICT(id) DO UPDATE SET body=excluded.body",
                    slug, language_id, slug, title, summary, body, example, exercise, order,
                )
    return ids


def seed_problems(language_ids: dict[str, str]) -> dict[str, str]:
    ids: dict[str, str] = {}
    with db.transaction():
        for entry in practice_data.CODING_PROBLEMS:
            slug = entry["slug"]
            ids[slug] = slug
            examples = "\n\n".join(
                f"**Input.** `{example['input']}`\n**Output.** `{example['output']}`"
                + (f"\n{example['explain']}" if example.get("explain") else "")
                for example in entry["examples"]
            )
            db.execute(
                "INSERT INTO coding_problems (id,slug,title,statement,difficulty,topics,hints,editorial,solution_md,"
                "tags,expected_time,expected_space,wrapper,solve_count,attempt_count,is_premium,created_at) "
                "VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,'0','0',0,?) "
                "ON CONFLICT(id) DO UPDATE SET statement=excluded.statement, wrapper=excluded.wrapper",
                slug, slug, entry["title"],
                f"{entry['statement']}\n\n### Examples\n\n{examples}",
                entry["difficulty"], jdump(entry["topics"]), jdump(entry["hints"]), entry["editorial"],
                entry["solution"].get("python", ""), jdump([entry["company"]]), "O(n)", "O(n)",
                entry.get("wrapper", "raw"), now_ms(),
            )
            for language_slug, stub in entry["stub"].items():
                language_id = language_ids.get(language_slug)
                if not language_id:
                    continue
                db.execute(
                    "INSERT INTO coding_problem_stubs (problem_id,language_id,stub,signature) VALUES (?,?,?,?) "
                    "ON CONFLICT(problem_id,language_id) DO UPDATE SET stub=excluded.stub",
                    slug, language_id, stub, entry["signature"].get(language_slug, ""),
                )
            for order, test in enumerate(entry["tests"]):
                db.execute(
                    "INSERT INTO coding_testcases (id,problem_id,input,expected,is_sample,explanation,order_index) "
                    "VALUES (?,?,?,?,?,?,?) ON CONFLICT(id) DO UPDATE SET expected=excluded.expected",
                    f"{slug}::tc{order}", slug, test["input"], test["expected"], 1 if order < 2 else 0,
                    test.get("explain"), order,
                )
    return ids


# ---------------------------------------------------------------------------
# Projects
# ---------------------------------------------------------------------------

def seed_projects(subject_ids: dict[str, str], branch_ids: dict[str, str]) -> None:
    with db.transaction():
        for index, entry in enumerate(library_data.PROJECTS):
            slug = entry["slug"]
            db.execute(
                "INSERT INTO projects (id,slug,title,branch_id,subject_id,difficulty,category,est_hours,summary,"
                "problem_statement,objective,prerequisites,hardware,software,architecture,source_code,"
                "database_design,testing,expected_output,improvements,resume_md,interview_questions,tech,skills,"
                "build_count,status,order_index,created_at) "
                "VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,'0','published',?,?) ON CONFLICT(id) DO NOTHING",
                slug, slug, entry["title"], branch_ids.get(entry["branch"] or ""),
                subject_ids.get(entry["subject"] or ""), entry["difficulty"], entry["category"], entry["est_hours"],
                entry["summary"], entry["problem_statement"], entry["objective"], jdump(entry["prerequisites"]),
                entry["hardware"], entry["software"], entry["architecture"], entry["source_code"],
                entry["database_design"], entry["testing"], entry["expected_output"], jdump(entry["improvements"]),
                entry["resume_md"], jdump(entry["interview_questions"]), jdump(entry["tech"]), jdump(entry["skills"]),
                index, now_ms(),
            )
            for order, (phase, title, body) in enumerate(entry.get("steps", [])):
                db.execute(
                    "INSERT INTO project_steps (id,project_id,phase,title,body,order_index) VALUES (?,?,?,?,?,?) "
                    "ON CONFLICT(id) DO UPDATE SET body=excluded.body",
                    f"{slug}::step{order}", slug, phase, title, body, order,
                )
            for kind, title, url, note in entry.get("resources", []):
                db.execute(
                    "INSERT INTO project_resources (id,project_id,kind,title,url,note) VALUES (?,?,?,?,?,?) "
                    "ON CONFLICT(id) DO UPDATE SET url=excluded.url",
                    f"{slug}::res-{slugify(title)}", slug, kind, title, url, note,
                )


# ---------------------------------------------------------------------------
# Library
# ---------------------------------------------------------------------------

def seed_videos(subject_ids: dict[str, str]) -> None:
    with db.transaction():
        rows = list(library_data.VIDEOS) + resource_sources.build_videos(_subject_rows())
        for title, channel, url, minutes, level, category, subject_slug, why in rows:
            slug = slugify(title)
            db.execute(
                "INSERT INTO videos (id,slug,title,channel,url,duration_s,language,level,category,topic_id,"
                "subject_id,rating,why_useful,embeddable,created_at) VALUES (?,?,?,?,?,?,'en',?,?,NULL,?,4,?,0,?) "
                "ON CONFLICT(slug) DO NOTHING",
                slug, slug, title, channel, url, minutes * 60, level, category, subject_ids.get(subject_slug), why,
                now_ms(),
            )


def seed_books(subject_ids: dict[str, str]) -> None:
    with db.transaction():
        for entry in list(library_data.BOOKS) + resource_sources.build_books(_subject_rows()):
            title, author, subject_slug, level, description, why, topics, url, access, publisher = entry
            slug = slugify(title)
            db.execute(
                "INSERT INTO books (id,slug,title,author,subject_id,branch_id,level,description,why_read,"
                "topics_covered,legal_url,access_kind,publisher,created_at) "
                "VALUES (?,?,?,?,?,NULL,?,?,?,?,?,?,?,?) ON CONFLICT(slug) DO NOTHING",
                slug, slug, title, author, subject_ids.get(subject_slug), level, description, why, jdump(topics),
                url, access, publisher, now_ms(),
            )


def _subject_rows() -> list[dict]:
    """Every subject with its branch category, for per-discipline expansion."""
    return db.query(
        "SELECT s.slug AS slug, s.name AS name, COALESCE(b.category, 'core') AS category "
        "FROM subjects s LEFT JOIN branches b ON b.id = s.branch_id ORDER BY s.slug"
    )


def seed_resources(subject_ids: dict[str, str]) -> None:
    with db.transaction():
        rows = list(library_data.RESOURCES) + resource_sources.build(_subject_rows())
        for title, url, kind, category, subject_slug, level, description in rows:
            slug = slugify(title)
            db.execute(
                "INSERT INTO resources (id,slug,title,url,kind,category,branch_id,subject_id,level,format,language,"
                "is_free,description,created_at) VALUES (?,?,?,?,?,?,NULL,?,?,'web','en',1,?,?) "
                "ON CONFLICT(slug) DO NOTHING",
                slug, slug, title, url, kind, category, subject_ids.get(subject_slug) if subject_slug else None,
                level, description, now_ms(),
            )


def _assert_known_refs(subject_ids: dict[str, str], topic_ids: dict[str, str],
                       problem_ids: dict[str, str]) -> None:
    """Fail the seed if any content row points at something that does not exist.

    Every seeder resolves a key with ``dict.get()`` and a miss becomes NULL. A
    NULL subject means the row never appears on any subject page, and a NULL
    roadmap reference renders as a node that links nowhere — in both cases the
    seed reports success. That is how four rows keyed to a
    ``probability-statistics`` subject that was never created went unnoticed:
    a book, a formula, a roadmap step and a flashcard, all silently dropped.

    Checking up front turns that into a clear error naming the offender.
    """
    problems: list[str] = []

    def check(value: str | None, known: dict[str, str], what: str, where: str) -> None:
        if value is None:
            return                       # a genuinely unassigned row is allowed
        if value not in known:
            problems.append(f"{where}: {what} {value!r} does not exist")

    for index, row in enumerate(library_data.VIDEOS):
        check(row[6], subject_ids, "subject", f"VIDEOS[{index}] {row[0]!r}")
    for index, row in enumerate(library_data.BOOKS):
        check(row[2], subject_ids, "subject", f"BOOKS[{index}] {row[0]!r}")
    for index, row in enumerate(library_data.RESOURCES):
        check(row[4], subject_ids, "subject", f"RESOURCES[{index}] {row[0]!r}")
    for index, row in enumerate(library_data.FLASHCARDS):
        check(row[0], subject_ids, "subject", f"FLASHCARDS[{index}] {row[2]!r}")
    for index, row in enumerate(library_data.FORMULAS):
        check(row[1], subject_ids, "subject", f"FORMULAS[{index}] {row[3]!r}")

    project_slugs = {r["slug"] for r in db.query("SELECT slug FROM projects")}
    module_slugs = {r["slug"] for r in db.query("SELECT slug FROM language_modules")}
    lookups = {"subject": subject_ids, "topic": topic_ids, "coding": problem_ids,
               "project": project_slugs, "module": module_slugs}
    for entry in library_data.ROADMAPS:
        for order, node in enumerate(entry["nodes"]):
            ref_type, ref_key = node[2], node[3]
            if ref_type not in lookups:
                problems.append(f"{entry['slug']} node {order}: unknown ref_type {ref_type!r}")
                continue
            check(ref_key, lookups[ref_type], ref_type, f"{entry['slug']} node {order} {node[0]!r}")

    if problems:
        raise SystemExit("Seed data references things that do not exist:\n  " + "\n  ".join(problems))


def seed_roadmaps(branch_ids: dict[str, str], topic_ids: dict[str, str],
                  problem_ids: dict[str, str], subject_ids: dict[str, str]) -> None:
    lookup = {
        "topic": topic_ids, "coding": problem_ids, "subject": subject_ids,
        # A node may point at a project or at a language module. Neither was in
        # the lookup before, so those references resolved to NULL and the step
        # rendered with nothing to click. These map slug -> slug to match the
        # convention the other three use: roadmap_nodes.ref_id holds a slug,
        # which is what the URL needs.
        "project": {r["slug"]: r["slug"] for r in db.query("SELECT slug FROM projects")},
        "module": {r["slug"]: r["slug"] for r in db.query("SELECT slug FROM language_modules")},
    }
    with db.transaction():
        for index, entry in enumerate(library_data.ROADMAPS):
            slug = entry["slug"]
            db.execute(
                "INSERT INTO roadmaps (id,slug,title,kind,branch_id,target_role,summary,description,order_index) "
                "VALUES (?,?,?,?,?,?,?,?,?) ON CONFLICT(id) DO UPDATE SET description=excluded.description",
                slug, slug, entry["title"], entry["kind"], branch_ids.get(entry["branch"] or ""),
                entry["target_role"], entry["summary"], entry["description"], index,
            )
            for order, (title, summary, ref_type, ref_key, required) in enumerate(entry["nodes"]):
                ref_id = lookup.get(ref_type, {}).get(ref_key)
                if ref_key and not ref_id:
                    raise KeyError(f"roadmap {slug!r} node {order} references unknown {ref_type} {ref_key!r}")
                db.execute(
                    "INSERT INTO roadmap_nodes (id,roadmap_id,title,summary,ref_type,ref_id,is_required,order_index) "
                    "VALUES (?,?,?,?,?,?,?,?) ON CONFLICT(id) DO UPDATE SET ref_id=excluded.ref_id",
                    f"{slug}::n{order}", slug, title, summary, ref_type, ref_id, 1 if required else 0, order,
                )


def seed_flashcards(subject_ids: dict[str, str]) -> None:
    with db.transaction():
        counts: dict[str, int] = {}
        for row in library_data.FLASHCARDS:
            counts[row[0]] = counts.get(row[0], 0) + 1
        rows = list(library_data.FLASHCARDS) + flashcard_content.build(_subject_rows(), counts)
        for subject_slug, deck, front, back, hint, difficulty in rows:
            # Keyed by subject as well as the question, because two subjects can
            # legitimately ask the same thing. With the subject left out, the
            # second card's ON CONFLICT clause overwrote the first instead of
            # adding it — machine-learning silently lost a card to a shared
            # "What is the bias-variance trade-off?" stem.
            card_id = f"fc-{slugify(subject_slug)}-{slugify(front)}"
            db.execute(
                "INSERT INTO flashcards (id,topic_id,subject_id,deck,front,back,hint,difficulty,created_at) "
                "VALUES (?,NULL,?,?,?,?,?,?,?) ON CONFLICT(id) DO UPDATE SET back=excluded.back",
                card_id, subject_ids.get(subject_slug), deck, front, back, hint, difficulty, now_ms(),
            )


def seed_plans() -> None:
    with db.transaction():
        for slug, name, price_inr, tagline, features, _is_default in library_data.PLANS:
            db.execute(
                "INSERT INTO plans (id,slug,name,price_cents,currency,interval,features,is_active) "
                "VALUES (?,?,?,?,?,'month',?,1) ON CONFLICT(id) DO UPDATE SET features=excluded.features, "
                "price_cents=excluded.price_cents",
                slug, slug, f"{name} - {tagline}", price_inr * 100, "INR", jdump(features),
            )


# ---------------------------------------------------------------------------
# Demo accounts
# ---------------------------------------------------------------------------

DEMO_USERS = [
    ("admin@engineverse.local", "evadmin", "EngineVerse Admin", "Str0ngPassphrase#42!", "super_admin"),
    # subject_expert is the authored-content role: create, update and publish.
    # There is no "faculty" role in rbac.ROLES, so using one here would leave the
    # account with zero capabilities and a "Student" label.
    ("faculty@engineverse.local", "profsharma", "Dr. Meera Sharma", "TeachLearn#2026!", "subject_expert"),
    ("asha@example.com", "asha", "Asha Verma", "LearnBuild#2026!", "student"),
    ("ravi@example.com", "ravi", "Ravi Kumar", "LearnBuild#2026!", "student"),
    ("priya@example.com", "priya", "Priya Nair", "LearnBuild#2026!", "student"),
]

DEMO_PROFILES = {
    "asha": {"branchId": "computer-science", "semester": 5, "college": "IIT Bombay",
             "careerGoal": "placement", "weeklyStudyHours": 12,
             "headline": "Third year CSE. Building towards a backend engineering role."},
    "ravi": {"branchId": "mechanical-engineering", "semester": 6, "college": "IIT Delhi",
             "careerGoal": "gate", "weeklyStudyHours": 15,
             "headline": "Mechanical undergraduate preparing for GATE."},
    "priya": {"branchId": "electronics-communication", "semester": 3, "college": "VJTI Mumbai",
              "careerGoal": "placement", "weeklyStudyHours": 10,
              "headline": "ECE student interested in embedded systems and VLSI."},
}


def seed_users() -> dict[str, str]:
    ids: dict[str, str] = {}
    for email, username, full_name, password, role in DEMO_USERS:
        existing = auth.find_by_email(email)
        if existing:
            ids[username] = existing.get("id", "")
            continue
        user = auth.register(email=email, username=username, password=password, full_name=full_name,
                             ip="127.0.0.1", user_agent="engineverse-seeder")
        ids[username] = user["id"]
        if role != "student":
            db.execute("UPDATE users SET role = ? WHERE id = ?", role, user["id"])
        profile = DEMO_PROFILES.get(username)
        if profile:
            onboarding = {key: value for key, value in profile.items() if key not in ("college", "headline")}
            college_id = COLLEGE_IDS.get(profile["college"])
            if college_id:
                onboarding["collegeId"] = college_id
            auth.update_onboarding(user["id"], onboarding)
            auth.update_profile(user["id"], {"headline": profile["headline"]})
    return ids


def seed_demo_activity(user_ids: dict[str, str], topic_ids: dict[str, str]) -> None:
    """Give the demo students a believable history so leaderboards and heatmaps are not empty."""
    topic_slugs = list(topic_ids)
    ts = now_ms()
    with db.transaction():
        for username, count in (("asha", 14), ("ravi", 9), ("priya", 6)):
            user_id = user_ids.get(username)
            if not user_id:
                continue
            for index in range(count):
                topic_id = topic_ids[topic_slugs[index % len(topic_slugs)]]
                status = "completed" if index < count - 2 else "in_progress"
                mastery = 85 if status == "completed" else 40
                day = (datetime.now(timezone.utc) - timedelta(days=index)).strftime("%Y-%m-%d")
                db.execute(
                    "INSERT INTO user_progress (user_id,topic_id,status,mastery,time_spent_s,last_viewed_at,"
                    "completed_at) VALUES (?,?,?,?,?,?,?) "
                    "ON CONFLICT(user_id,topic_id) DO UPDATE SET status=excluded.status, mastery=excluded.mastery",
                    user_id, topic_id, status, mastery, 1800 if status == "completed" else 420, ts,
                    ts if status == "completed" else None,
                )
                db.execute(
                    "INSERT INTO xp_events (id,user_id,amount,reason,entity_type,entity_id,created_at) "
                    "VALUES (?,?,?,?,?,?,?)",
                    ulid(), user_id, 20 if status == "completed" else 2, "topic", "topic", topic_id, ts,
                )
                db.execute(
                    "INSERT INTO activity (user_id,day,notes_studied,minutes,xp) VALUES (?,?,1,35,22) "
                    "ON CONFLICT(user_id,day) DO UPDATE SET notes_studied = notes_studied + 1, "
                    "minutes = minutes + 35, xp = xp + 22",
                    user_id, day,
                )
            db.execute(
                "UPDATE streaks SET total_xp = (SELECT COALESCE(sum(amount),0) FROM xp_events WHERE user_id = ?), "
                "longest_streak = ?, current_streak = ? WHERE user_id = ?",
                user_id, count, min(count, 5), user_id,
            )


# ---------------------------------------------------------------------------
# Orchestration
# ---------------------------------------------------------------------------

TABLES = [
    "universities", "colleges", "branches", "semesters", "curricula", "curriculum_subjects", "subjects",
    "modules", "topics", "notes", "note_sections", "diagrams", "models_3d", "formulas", "questions",
    "question_options",
    "dpp_sets", "dpp_questions", "programming_languages", "language_modules", "coding_problems",
    "coding_problem_stubs", "coding_testcases", "projects", "project_steps", "project_resources", "videos",
    "books", "resources", "roadmaps", "roadmap_nodes", "flashcards", "plans", "site_config", "badges",
    "users", "user_progress", "xp_events",
]


def print_stats() -> None:
    print(f"\n{'table':<26}{'rows':>8}")
    print("-" * 34)
    for table in TABLES:
        try:
            count = db.row_count(table)
        except db.DatabaseError:
            count = -1
        print(f"{table:<26}{count:>8}")
    print("-" * 34)
    print(f"{'search index':<26}{search.indexed_count():>8}\n")


def run(fresh: bool) -> None:
    started = datetime.now()
    if fresh:
        print("Resetting database ...")
        db.reset_database()
    db.migrate()

    print("Seeding site configuration ...")
    seed_config()

    print("Seeding universities and colleges ...")
    university_ids = seed_universities()

    print("Seeding branches and semesters ...")
    branch_ids = seed_branches()
    seed_semesters()

    print("Seeding subjects and curricula ...")
    subject_ids = seed_subjects(branch_ids)
    seed_curricula(subject_ids, branch_ids, university_ids)

    print("Seeding topics, notes and diagrams ...")
    topic_ids = seed_topics(subject_ids)
    notes = seed_notes(topic_ids)
    diagrams = seed_diagrams(topic_ids)
    models = seed_models_3d(topic_ids)
    seed_formulas(subject_ids, topic_ids)
    print(f"  {len(topic_ids)} topics, {notes} notes, {diagrams} diagrams, {models} 3D models")

    print("Seeding practice questions and DPP sets ...")
    question_ids = seed_questions(subject_ids)
    sets = seed_dpp(question_ids, subject_ids)
    print(f"  {len(question_ids)} questions, {sets} daily sets")

    print("Seeding programming languages and problems ...")
    language_ids = seed_languages()
    problem_ids = seed_problems(language_ids)
    print(f"  {len(language_ids)} languages, {len(problem_ids)} problems")

    print("Seeding projects ...")
    seed_projects(subject_ids, branch_ids)

    # Runs before the library phase so a bad cross-reference fails the seed
    # with the offending row named, instead of quietly dropping it.
    _assert_known_refs(subject_ids, topic_ids, problem_ids)

    print("Seeding library (videos, books, resources, roadmaps, flashcards) ...")
    seed_videos(subject_ids)
    seed_books(subject_ids)
    seed_resources(subject_ids)
    seed_roadmaps(branch_ids, topic_ids, problem_ids, subject_ids)
    seed_flashcards(subject_ids)
    seed_plans()

    print("Creating demo accounts ...")
    user_ids = seed_users()
    seed_demo_activity(user_ids, topic_ids)

    print("Issuing badges and building the search index ...")
    progress.ensure_badges()
    indexed = search.reindex_all()

    print_stats()
    elapsed = (datetime.now() - started).total_seconds()
    print(f"Done in {elapsed:.1f}s. {indexed} searchable entities indexed.")
    print("\nDemo accounts (change these passwords before any real deployment):")
    for email, username, _name, password, role in DEMO_USERS:
        print(f"  {role:<12} {email:<28} {password}")


def main() -> int:
    parser = argparse.ArgumentParser(description="Seed the EngineVerse database.")
    parser.add_argument("--fresh", action="store_true", help="drop all data before seeding")
    parser.add_argument("--stats", action="store_true", help="print row counts and exit")
    args = parser.parse_args()

    if args.stats:
        db.migrate()
        print_stats()
        return 0
    run(args.fresh)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
