"""The seed corpus has to be complete and internally consistent.

These exist because of a specific class of bug: every seeder resolves a subject
or topic key with ``dict.get()`` and skips on a miss, so a reference to something
that was never created simply disappears. Four rows keyed to a
``probability-statistics`` subject went that way, along with eleven roadmap steps
pointing at topics that do not exist and nine that named a ``resource`` ref type
no seeder handled. Each one reported success while quietly dropping content, and
twenty-one roadmap steps rendered as text with nothing to click.

So the assertions here are about *absence*: nothing referenced may be missing,
and nothing may be silently dropped on the way in.
"""

from __future__ import annotations

import json
import os
import re
import sqlite3
import subprocess
import sys
from pathlib import Path

import pytest

from engineverse import community, db, library, progress

REPO_ROOT = Path(__file__).resolve().parents[2]
from seed_data import language_curriculum, language_projects, library_data
from seed_data.catalog import SUBJECTS

#: Tables whose rows must exist for at least MIN_PER_SUBJECT entries per subject.
PER_SUBJECT_TABLES = ("videos", "books", "resources", "flashcards")

#: One entry per subject is technically "not empty" and still reads as abandoned.
#: Three is the minimum at which a shelf looks curated. Enforced here because the
#: registries in seed_data/resource_sources.py silently dropped to one book and
#: two videos for most subjects, and nothing noticed.
MIN_PER_SUBJECT = 3


def _subject_slugs() -> set[str]:
    return {row[0] for row in SUBJECTS}


def test_every_active_branch_has_a_published_subject(seeded):
    """All 45 branch paths must lead to at least one real course, not a blank tile."""
    missing = db.query(
        "SELECT b.slug FROM branches b WHERE b.is_active = 1 AND NOT EXISTS "
        "(SELECT 1 FROM subjects s WHERE s.branch_id = b.id AND s.status = 'published') ORDER BY b.slug"
    )
    assert [row["slug"] for row in missing] == []


def test_every_published_subject_has_notes_and_a_question(seeded):
    """A catalogue row is a learning path only when notes and practice reach it."""
    missing = db.query(
        "SELECT s.slug FROM subjects s WHERE s.status = 'published' AND ("
        "NOT EXISTS (SELECT 1 FROM topics t WHERE t.subject_id = s.id AND t.status = 'published') OR "
        "NOT EXISTS (SELECT 1 FROM topics t JOIN notes n ON n.topic_id = t.id "
        "  WHERE t.subject_id = s.id AND t.status = 'published' AND n.status = 'published' "
        "  AND n.quality_level = 'standard') OR "
        "NOT EXISTS (SELECT 1 FROM questions q WHERE q.subject_id = s.id AND q.is_active = 1)) "
        "ORDER BY s.slug"
    )
    assert [row["slug"] for row in missing] == []


def test_every_topic_has_a_linked_question(seeded):
    """Topic pages must not advertise practice while their question panel is empty."""
    missing = db.query(
        "SELECT t.slug FROM topics t WHERE t.status = 'published' AND NOT EXISTS "
        "(SELECT 1 FROM questions q WHERE q.topic_id = t.id AND q.is_active = 1) ORDER BY t.slug"
    )
    assert [row["slug"] for row in missing] == []


def test_generated_starters_are_published_and_flagged_for_review(seeded):
    """Generated breadth-first and depth-pass material is reachable while its editorial review state stays honest."""
    from engineverse.security.sanitize import slugify
    from seed_data import subject_paths

    expected = {slugify(topic["title"]) for topic in subject_paths.TOPICS}
    assert len(expected) == 350  # 71 breadth starters + 186 deeper lessons + 93 mastery lessons
    rows = db.query(
        "SELECT slug, status, accuracy_state FROM topics WHERE slug IN (%s) ORDER BY slug"
        % ",".join("?" for _ in expected),
        *sorted(expected),
    )
    assert {row["slug"] for row in rows} == expected
    assert all(row["status"] == "published" and row["accuracy_state"] == "needs_review" for row in rows)
    topic_ids = [row["id"] for row in db.query(
        "SELECT id FROM topics WHERE slug IN (%s)" % ",".join("?" for _ in expected), *sorted(expected)
    )]
    questions = db.query(
        "SELECT q.id, q.topic_id, q.answer_index, (SELECT count(*) FROM question_options o WHERE o.question_id = q.id) AS options, "
        "(SELECT count(*) FROM question_options o WHERE o.question_id = q.id AND o.is_correct = 1) AS correct_options "
        "FROM questions q WHERE q.topic_id IN (%s)" % ",".join("?" for _ in topic_ids),
        *topic_ids,
    )
    assert len(questions) >= len(expected)
    assert {row["topic_id"] for row in questions} >= set(topic_ids)
    assert {row["answer_index"] for row in questions} == {0, 1, 2, 3}
    assert all(row["options"] == 4 and row["correct_options"] == 1 for row in questions)


def test_every_active_question_belongs_to_a_published_subject(seeded):
    """A malformed subject slug must not silently create an orphan question."""
    missing = db.query(
        "SELECT q.id FROM questions q LEFT JOIN subjects s ON s.id = q.subject_id "
        "WHERE q.is_active = 1 AND (s.id IS NULL OR s.status <> 'published') ORDER BY q.id"
    )
    assert [row["id"] for row in missing] == []


def test_dpp_scheduler_handles_a_partial_bank_without_duplicate_questions(seeded):
    """A non-multiple-of-five bank is topped up from earlier days, not truncated."""
    from scripts.seed import _schedule_dpp_questions

    groups = [["a1", "a2", "a3"], ["b1"], ["c1"], ["d1"], ["e1"]]
    days = _schedule_dpp_questions(groups)
    expected = {question_id for group in groups for question_id in group}

    assert len(days) == 2
    assert all(len(day) == 5 for day in days)
    assert all(len(day) == len(set(day)) for day in days)
    assert {question_id for day in days for question_id in day} == expected
    assert len({question_id[0] for question_id in days[0]}) == 5
    with pytest.raises(RuntimeError, match="at least 5 active questions"):
        _schedule_dpp_questions([["only-one"]])


def test_dpp_rotation_covers_all_questions_and_keeps_five_mixed_questions_per_day(seeded):
    """The archive should rotate the full bank, balanced across subjects."""
    missing_subjects = db.query(
        "SELECT s.slug FROM subjects s WHERE s.status = 'published' AND NOT EXISTS ("
        "SELECT 1 FROM questions q JOIN dpp_questions dq ON dq.question_id = q.id "
        "JOIN dpp_sets d ON d.id = dq.set_id AND d.published = 1 "
        "WHERE q.subject_id = s.id AND q.is_active = 1) ORDER BY s.slug"
    )
    assert [row["slug"] for row in missing_subjects] == []

    active_questions = {row["id"] for row in db.query("SELECT id FROM questions WHERE is_active = 1")}
    scheduled_questions = {row["id"] for row in db.query(
        "SELECT DISTINCT q.id FROM questions q JOIN dpp_questions dq ON dq.question_id = q.id "
        "JOIN dpp_sets d ON d.id = dq.set_id AND d.published = 1"
    )}
    assert scheduled_questions == active_questions

    active_count = len(active_questions)
    published_sets = int(db.scalar("SELECT count(*) FROM dpp_sets WHERE published = 1") or 0)
    assert published_sets == (active_count + 4) // 5

    thin = db.query(
        "SELECT d.id, count(dq.question_id) AS n FROM dpp_sets d LEFT JOIN dpp_questions dq ON dq.set_id = d.id "
        "WHERE d.published = 1 GROUP BY d.id HAVING n <> 5"
    )
    assert [dict(row) for row in thin] == []

    subject_count = int(db.scalar("SELECT count(*) FROM subjects WHERE status = 'published'") or 0)
    first_pass_days = (subject_count + 4) // 5
    repeated_subjects = db.query(
        "SELECT d.id, q.subject_id, count(*) AS n FROM ("
        "SELECT id FROM dpp_sets WHERE published = 1 ORDER BY date LIMIT ?"
        ") d JOIN dpp_questions dq ON dq.set_id = d.id "
        "JOIN questions q ON q.id = dq.question_id "
        "GROUP BY d.id, q.subject_id HAVING n > 1",
        first_pass_days,
    )
    assert [dict(row) for row in repeated_subjects] == []


def test_dpp_archive_paginates_over_every_published_set(client, seeded):
    """A set older than the recent-days widget must still have a visible archive link."""
    expected = [row["date"] for row in db.query(
        "SELECT date FROM dpp_sets WHERE published = 1 ORDER BY date DESC"
    )]
    page_size = 30
    pages = (len(expected) + page_size - 1) // page_size
    seen: list[str] = []
    for page in range(1, pages + 1):
        response = client.get(f"/dpp/archive?page={page}")
        assert response.status_code == 200
        seen.extend(re.findall(r'href="/dpp/(\d{4}-\d{2}-\d{2})"', response.text))
        if pages > 1:
            assert f"Page {page} of {pages}" in response.text
    assert len(seen) == len(expected)
    assert seen == expected

    sitemap = client.get("/sitemap.xml")
    assert sitemap.status_code == 200
    assert "/dpp/archive</loc>" in sitemap.text
    assert all(f"/dpp/{date}</loc>" in sitemap.text for date in expected)


def test_cyber_security_notes_are_published_and_public(client, seeded):
    """Cyber Security is readable anonymously, with the full note available on every lesson."""
    subject = db.query_one("SELECT id, status FROM subjects WHERE slug = 'cryptography-security'")
    assert subject and subject["status"] == "published"
    topics = db.query(
        "SELECT id, slug, status FROM topics WHERE subject_id = ? ORDER BY order_index", subject["id"]
    )
    assert len(topics) >= 5
    for topic in topics:
        assert topic["status"] == "published"
        note = db.query_one(
            "SELECT id, status FROM notes WHERE topic_id = ? AND quality_level = 'standard'", topic["id"]
        )
        assert note and note["status"] == "published"
        assert len(db.query("SELECT id FROM note_sections WHERE note_id = ?", note["id"])) == 13
        response = client.get(f"/topics/{topic['slug']}")
        assert response.status_code == 200, f"public Cyber Security lesson {topic['slug']} was not readable"
    assert client.get("/subjects/cryptography-security").status_code == 200


def test_homepage_and_explore_reach_every_branch_and_subject(client, seeded):
    """The homepage points to a paginated catalogue that exposes every subject."""
    response = client.get("/")
    assert response.status_code == 200
    branches = db.query("SELECT slug FROM branches WHERE is_active = 1")
    for row in branches:
        assert f'href="/branches/{row["slug"]}"' in response.text
    assert 'href="/explore">All subjects</a>' in response.text

    expected = _subject_slugs()
    seen: set[str] = set()
    page = 1
    while True:
        listing = client.get(f"/explore?page={page}")
        assert listing.status_code == 200
        found = set(re.findall(r'href="/subjects/([a-z0-9-]+)"', listing.text))
        assert found, f"subject catalogue page {page} has no subject links"
        assert not (found & seen), f"subject catalogue page {page} repeats earlier subjects"
        seen |= found
        if 'rel="next"' not in listing.text:
            break
        page += 1
        assert page < 100, "subject catalogue pagination did not terminate"

    assert len(branches) == 45
    assert seen == expected
    assert len(expected) == 93


def test_projects_are_branch_discoverable_and_the_agent_brief_is_practical(client, seeded):
    """Project links must follow their real subject branch, not a category placeholder.

    Library briefs are tied to a subject and must sit on that subject's branch.
    The nine language capstones carry a language link instead of a subject, so
    they are branch-linked (computer-science) with no subject to reconcile -
    the subject/branch equality only applies where a subject exists.
    """
    rows = db.query(
        "SELECT p.slug, p.branch_id, p.language_id, s.branch_id AS subject_branch "
        "FROM projects p LEFT JOIN subjects s ON s.id = p.subject_id "
        "WHERE p.status = 'published' ORDER BY p.slug"
    )
    assert len(rows) == len(library_data.PROJECTS) + len(language_projects.CAPSTONES)
    capstone_slugs = {c["slug"] for c in language_projects.CAPSTONES}
    for project in rows:
        assert project["branch_id"], f"{project['slug']} has no branch link"
        if project["subject_branch"] is not None:
            assert project["branch_id"] == project["subject_branch"], project["slug"]
        # The branch page shows a capped "related projects" teaser. Every
        # subject-linked library brief sits on its own branch and must appear
        # there. The nine capstones all share the computer-science branch, so
        # they overflow the teaser by design - their discoverability is the
        # language path's forward/back links, asserted in
        # test_language_capstone_links_forward_and_back.
        if project["slug"] not in capstone_slugs:
            branch_page = client.get(f"/branches/{project['branch_id']}")
            assert branch_page.status_code == 200
            assert f'href="/projects/{project["slug"]}"' in branch_page.text

    agent = client.get("/projects/citation-first-study-agent")
    assert agent.status_code == 200
    assert "search_public_notes" in agent.text
    assert "prompt injection" in agent.text.lower()
    assert "confirmation" in agent.text.lower()
    assert db.scalar(
        "SELECT count(*) FROM project_steps WHERE project_id = 'citation-first-study-agent'"
    ) == 6
    assert db.scalar(
        "SELECT count(*) FROM project_resources WHERE project_id = 'citation-first-study-agent'"
    ) == 3

    filtered = client.get("/projects?branch=software-engineering")
    assert filtered.status_code == 200
    assert '/projects/citation-first-study-agent' in filtered.text


def test_question_bank_pages_cover_the_entire_question_set(client, seeded):
    """The bank's page links must make every question reachable, not just the first 60."""
    total = db.scalar("SELECT count(*) FROM questions WHERE is_active = 1")
    assert total > 24
    seen = []
    for page in range(1, (total + 23) // 24 + 1):
        response = client.get(f"/practice/questions?page={page}")
        assert response.status_code == 200
        seen.extend(re.findall(r'data-quiz="([^"]+)"', response.text))
        if page == 1:
            assert f"1–24 of {total}" in response.text
        else:
            assert f"Page {page} of {(total + 23) // 24}" in response.text
    assert len(seen) == total
    assert len(set(seen)) == total


@pytest.mark.parametrize("table", PER_SUBJECT_TABLES)
def test_every_subject_has_a_usable_shelf(seeded, table):
    """No subject may have a shelf thin enough to look abandoned.

    An empty subject page is the obvious failure; a one-item page is subtler.
    Before the catalogue expansion, 67 of the original 73 subjects had only one book.
    """
    thin = db.query(
        f"SELECT s.slug, (SELECT count(*) FROM {table} t WHERE t.subject_id = s.id) AS n "
        f"FROM subjects s ORDER BY s.slug"
    )
    offenders = [(row["slug"], row["n"]) for row in thin if row["n"] < MIN_PER_SUBJECT]
    assert offenders == [], (
        f"subjects with fewer than {MIN_PER_SUBJECT} {table}: {offenders[:10]}"
        + (f" (+{len(offenders) - 10} more)" if len(offenders) > 10 else "")
    )


SLUGGED_TABLES = ("videos", "books", "resources")


@pytest.mark.parametrize("table", SLUGGED_TABLES)
def test_no_duplicate_slugs(seeded, table):
    """A duplicate slug collides with ON CONFLICT and the row vanishes.

    ``ON CONFLICT(slug) DO NOTHING`` turns a repeated slug into a silently
    missing row rather than an error, so generated titles have to be unique.
    """
    dupes = db.query(
        f"SELECT slug, count(*) AS n FROM {table} GROUP BY slug HAVING n > 1"
    )
    assert [(row["slug"], row["n"]) for row in dupes] == [], f"duplicate {table} slugs"


def test_no_subject_is_assigned_twice_by_the_same_source(seeded):
    """Every resource slug must be globally unique, including across sources.

    Guards the generated corpus specifically: if two registries emit the same
    slug for different subjects, one of them is dropped without a trace.
    """
    total = db.query_one("SELECT count(*) AS n FROM resources")["n"]
    distinct = db.query_one("SELECT count(DISTINCT slug) AS n FROM resources")["n"]
    assert total == distinct, f"{total} rows but {distinct} distinct slugs"


def _referenced_subject_keys():
    """Yields (where, slug) for every subject key used by the library data.

    A row with no subject at all is legitimate: site-wide and branch-level
    resources are not attached to a subject. Only a *named* subject that does
    not exist is a bug.
    """
    for index, row in enumerate(library_data.VIDEOS):
        yield f"VIDEOS[{index}] {row[0]!r}", row[6]
    for index, row in enumerate(library_data.BOOKS):
        yield f"BOOKS[{index}] {row[0]!r}", row[2]
    for index, row in enumerate(library_data.RESOURCES):
        yield f"RESOURCES[{index}] {row[0]!r}", row[4]
    for index, row in enumerate(library_data.FLASHCARDS):
        yield f"FLASHCARDS[{index}] {row[2]!r}", row[0]
    for index, row in enumerate(library_data.FORMULAS):
        yield f"FORMULAS[{index}] {row[3]!r}", row[1]


def test_every_referenced_subject_exists():
    """The regression test for the silently-dropped-row class.

    Runs against the data alone, so it fails before the seed can drop anything.
    """
    known = _subject_slugs()
    missing = sorted(
        {f"{where} -> {slug!r}" for where, slug in _referenced_subject_keys()
         if slug is not None and slug not in known}
    )
    assert missing == [], "seed data references subjects that do not exist:\n  " + "\n  ".join(missing)


def test_every_roadmap_reference_resolves(seeded):
    """No roadmap step may point at something that was never created.

    A NULL ref_id renders the step as plain text with nothing to click, which
    reads as a dead button.
    """
    problems = []
    for roadmap in library.list_roadmaps():
        for node in library.roadmap_nodes(roadmap["id"]):
            if not node["ref_id"]:
                problems.append(f"{roadmap['slug']} {node['title']!r} has no target")
            elif not node["href"]:
                problems.append(
                    f"{roadmap['slug']} {node['title']!r} has ref_type {node['ref_type']!r} "
                    "which maps to no URL"
                )
    assert problems == [], "unresolvable roadmap steps:\n  " + "\n  ".join(problems)


def test_every_roadmap_link_loads(client):
    """Following a roadmap step must land on a real page, not a 404.

    Checking that a slug exists is not enough: this proves the URL the template
    actually renders is served.
    """
    checked = 0
    for roadmap in library.list_roadmaps():
        for node in library.roadmap_nodes(roadmap["id"]):
            response = client.get(node["href"], follow_redirects=False)
            assert response.status_code < 400, (
                f"{roadmap['slug']} step {node['title']!r} -> {node['href']} "
                f"returned {response.status_code}"
            )
            checked += 1
    # If this ever drops to zero the loop above proves nothing.
    assert checked >= 50, f"only {checked} roadmap links checked"


@pytest.mark.parametrize("table", PER_SUBJECT_TABLES)
def test_no_orphan_subject_references(seeded, table):
    """Rows pointing at a deleted subject must not linger.

    Branch-level rows legitimately have no subject, so NULL is allowed; a
    non-NULL value that matches no subject is not.
    """
    orphans = db.query(
        f"SELECT count(*) AS n FROM {table} t WHERE t.subject_id IS NOT NULL "
        f"AND NOT EXISTS (SELECT 1 FROM subjects s WHERE s.id = t.subject_id)"
    )[0]["n"]
    assert orphans == 0, f"{table} has {orphans} rows pointing at a missing subject"


def test_flashcard_corpus_is_not_trivially_small(seeded):
    """Each subject should have a deck worth reviewing, not a single token card."""
    thin = db.query(
        "SELECT s.slug, count(*) AS n FROM subjects s JOIN flashcards f ON f.subject_id = s.id "
        "GROUP BY s.slug HAVING n < 3 ORDER BY n"
    )
    assert [(row["slug"], row["n"]) for row in thin] == [], "subjects with a stub deck"


def test_no_two_flashcards_share_an_id(seeded):
    """A shared id does not fail — it silently overwrites the earlier card.

    ``ON CONFLICT(id) DO UPDATE`` makes a collision invisible: the row count
    just comes out lower than the corpus holds. This catches it by counting the
    corpus the seeder was handed.
    """
    import re

    from seed_data import flashcards_extra, library_data
    from scripts.seed import _subject_rows

    def slugify(text: str) -> str:
        return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")

    counts: dict[str, int] = {}
    for row in library_data.FLASHCARDS:
        counts[row[0]] = counts.get(row[0], 0) + 1
    corpus = list(library_data.FLASHCARDS) + flashcards_extra.build(_subject_rows(), counts)
    ids = [f"fc-{slugify(r[0])}-{slugify(r[2])}" for r in corpus]
    assert len(ids) == len(set(ids)), f"{len(ids) - len(set(ids))} flashcard ids collide"

    stored = db.query_one("SELECT count(*) AS n FROM flashcards")["n"]
    assert stored == len(corpus), f"{len(corpus)} cards authored but {stored} stored"


# ---------------------------------------------------------------------------
# Note completeness
# ---------------------------------------------------------------------------

#: The thirteen sections every standard note is specified to carry.
REQUIRED_SECTIONS = [
    "simple", "definition", "intuition", "points", "formula", "derivation",
    "example", "applications", "mistakes", "exam", "interview", "diagram", "industry",
]


def test_every_published_topic_has_all_four_published_note_depths(seeded):
    """Each lesson must have all public reading modes, not just a standard note."""
    missing = []
    for depth in ("beginner", "standard", "advanced", "industry"):
        rows = db.query(
            "SELECT t.slug FROM topics t WHERE t.status = 'published' AND NOT EXISTS ("
            "SELECT 1 FROM notes n WHERE n.topic_id = t.id AND n.quality_level = ? "
            "AND n.status = 'published') ORDER BY t.slug", depth,
        )
        missing.extend((depth, row["slug"]) for row in rows)
    assert missing == []


def test_every_standard_note_carries_all_thirteen_sections(seeded):
    """The full reading mode has exactly thirteen sections, including every generated lesson."""
    incomplete = db.query(
        "SELECT n.id, count(s.id) AS have FROM notes n "
        "LEFT JOIN note_sections s ON s.note_id = n.id "
        "WHERE n.quality_level = 'standard' AND n.status = 'published' "
        "GROUP BY n.id HAVING have <> 13"
    )
    assert [(r["id"], r["have"]) for r in incomplete] == [], "standard notes with other than 13 sections"


def test_every_topic_has_the_four_previously_missing_fields(seeded):
    """Derivation, industry, formula and example must exist for every topic."""
    for kind in ("derivation", "industry", "formula", "example"):
        missing = db.query(
            "SELECT t.slug FROM topics t WHERE NOT EXISTS ("
            "  SELECT 1 FROM notes n JOIN note_sections s ON s.note_id = n.id "
            "  WHERE n.topic_id = t.id AND s.kind = ?) ORDER BY t.slug", kind,
        )
        assert [r["slug"] for r in missing] == [], f"topics with no {kind} section"


def test_no_section_body_is_empty_or_a_placeholder(seeded):
    """A section that renders nothing is worse than one that is absent."""
    rows = db.query("SELECT id, kind, body FROM note_sections")
    assert rows
    for row in rows:
        stripped = (row["body"] or "").strip()
        assert len(stripped) >= 40, f"{row['id']} ({row['kind']}) body is {len(stripped)} chars"


def test_latex_delimiters_are_balanced(seeded):
    """An unbalanced $$ breaks KaTeX rendering for the whole section."""
    for row in db.query("SELECT id, body FROM note_sections"):
        body = row["body"] or ""
        assert body.count("$$") % 2 == 0, f"{row['id']} has an odd number of $$ delimiters"


def test_formula_sections_render_a_variable_table(seeded):
    """formula_body() builds a table; a formula with no variables has nothing to show."""
    rows = db.query("SELECT id, body FROM note_sections WHERE kind = 'formula'")
    assert rows
    for row in rows:
        assert "| Symbol | Meaning | Unit |" in row["body"], f"{row['id']} has no variable table"


def test_notes_extra_has_no_stale_topic_keys(seeded):
    """Content keyed to a topic that no longer exists must fail the seed."""
    from seed_data import foundations, notes_extra, topics_core, topics_cse
    from engineverse.security.sanitize import slugify

    known = {
        slugify(t["title"])
        for t in list(topics_core.TOPICS) + list(topics_cse.TOPICS) + list(foundations.TOPICS)
    }
    assert notes_extra.unknown_keys(known) == {}


def test_notes_extra_shapes_match_the_topic_table(seeded):
    """The fallback must be interchangeable with topic["formula"] and ["example"]."""
    from seed_data import notes_extra

    for slug, formula in notes_extra.FORMULAS.items():
        assert formula.get("name") and formula.get("latex"), f"{slug} formula incomplete"
        for variable in formula.get("variables", []):
            assert set(variable) == {"s", "n", "u"}, f"{slug} has a malformed variable: {variable}"
    for slug, example in notes_extra.EXAMPLES.items():
        assert example.get("problem") and example.get("solution") and example.get("answer"), (
            f"{slug} example incomplete"
        )


def test_diagram_section_present_for_every_topic(seeded):
    """6 of 48 notes had this section; the diagram itself now exists for all."""
    missing = db.query(
        "SELECT t.slug FROM topics t WHERE NOT EXISTS ("
        "  SELECT 1 FROM notes n JOIN note_sections s ON s.note_id = n.id "
        "  WHERE n.topic_id = t.id AND s.kind = 'diagram')"
    )
    assert [r["slug"] for r in missing] == []


def _usable_hotspots(raw: str | None) -> bool:
    """Whether a diagram's hotspot payload describes something clickable."""
    try:
        data = json.loads(raw) if raw else None
    except ValueError:
        return False
    return isinstance(data, list) and bool(data)


def _visual_coverage_problems() -> list[str]:
    """Everything wrong with the per-topic visuals, as a list of complaints."""
    problems = [
        f"diagram {row['topic_id']} has no usable hotspots"
        for row in db.query("SELECT topic_id, hotspots FROM diagrams")
        if not _usable_hotspots(row["hotspots"])
    ]
    topics = db.scalar("SELECT COUNT(*) FROM topics")
    for table in ("diagrams", "models_3d"):
        covered = db.scalar(f"SELECT COUNT(DISTINCT topic_id) FROM {table}")
        if covered != topics:
            problems.append(f"{table} covers {covered} of {topics} topics")
    return problems


def test_every_topic_has_a_diagram_with_hotspots(seeded):
    """The docs claim every topic's SVG diagram is interactive.

    An empty ``hotspots`` column still renders a perfectly good picture, so
    nothing else would notice the interactivity going missing - and the claim
    had already rotted once, in the other direction, when a stale count of 6 was
    left standing in the README after all 48 had been filled in.
    """
    assert _visual_coverage_problems() == []


@pytest.mark.parametrize(
    "raw", [None, "", "[]", "{{{", "null", '"a string"', '{"a": 1}', "[{}]"]
)
def test_the_hotspot_predicate_rejects_payloads_that_render_but_are_not_clickable(raw):
    """Pinned directly, because the fixture above reseeds and would swallow any
    attempt to break the data underneath it."""
    if raw == "[{}]":
        assert _usable_hotspots(raw), "one empty hotspot object is still a hotspot"
    else:
        assert not _usable_hotspots(raw), f"{raw!r} should not count as interactive"


@pytest.mark.parametrize("table,column", [("videos", "category"), ("resources", "kind"), ("books", "level")])
def test_filter_facets_are_not_degenerate(seeded, table, column):
    """A filter with one option is decoration.

    Every generated video was filed under "concept", which left /videos with a
    single category for all 320 rows and a control that could never change the
    page.
    """
    facets = db.query(f"SELECT {column}, count(*) AS n FROM {table} GROUP BY {column}")
    assert len(facets) >= 3, (
        f"{table}.{column} has only {len(facets)} distinct value(s): "
        f"{[row[column] for row in facets]}"
    )


# ---------------------------------------------------------------------------
# External URLs
# ---------------------------------------------------------------------------

def _check_links():
    import subprocess
    import sys
    from pathlib import Path

    root = Path(__file__).resolve().parents[2]
    return subprocess.run(
        [sys.executable, str(root / "scripts" / "check_links.py"), "--offline"],
        capture_output=True, text=True, cwd=root,
    )


def test_every_stored_url_is_well_formed(seeded):
    """Run on every push; the networked variant runs weekly in CI.

    Nothing checked these before, so every one of the several hundred resource
    links shipped unverified.
    """
    result = _check_links()
    assert result.returncode == 0, result.stdout + result.stderr
    assert "0 error" in result.stdout


def test_the_checker_actually_finds_urls(seeded):
    """A checker that scans nothing exits 0 and proves nothing."""
    import sys
    from pathlib import Path

    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
    from scripts import check_links

    urls = check_links.collect_urls()
    assert len(urls) > 200, f"only {len(urls)} URLs collected - the checker is not looking"
    assert all(url.startswith(("http://", "https://")) for url in urls)


@pytest.mark.parametrize("url,reason", [
    ("ftp://example.org/book.pdf", "wrong scheme"),
    ("https://localhost/resources", "loopback host"),
    ("https://192.168.1.5/x", "private address"),
    ("https://example.com/x", "non-routable example host"),
    ("https://nodot", "host without a dot"),
    ("https://site.org/TODO", "unfinished placeholder"),
])
def test_the_checker_rejects_a_bad_url(url, reason):
    import sys
    from pathlib import Path

    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
    from scripts import check_links

    errors, _ = check_links.check_structure(url)
    assert errors, f"{url} ({reason}) was accepted"


def test_the_checker_accepts_a_good_url():
    import sys
    from pathlib import Path

    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
    from scripts import check_links

    errors, warnings = check_links.check_structure("https://openstax.org/details/books/calculus-volume-1")
    assert errors == []
    assert warnings == []


@pytest.fixture(scope="module")
def fresh_seed(tmp_path_factory):
    """A database the seeder produced on its own, with no other test near it.

    The session database is shared and mutable: other suites post discussions
    that have no replies and delete submissions outright, so an absolute count
    read from it measures the suite's history rather than the seeder's output.
    Both directions broke - nine reply-less threads appeared, and 194 seeded
    submissions fell to 82. Seeding a throwaway database in a subprocess is the
    only way to assert on what the seeder actually writes.
    """
    path = tmp_path_factory.mktemp("fresh-seed") / "fresh.sqlite3"
    env = {
        **os.environ,
        "ENGINEVERSE_DB_PATH": str(path),
        "ENGINEVERSE_SECRET": "test-secret-key-for-pytest-only-0123456789",
        "ENGINEVERSE_ENV": "test",
    }
    result = subprocess.run(
        [sys.executable, "scripts/seed.py", "--fresh"],
        cwd=REPO_ROOT, env=env, capture_output=True, text=True,
    )
    assert result.returncode == 0, result.stdout[-1500:] + result.stderr[-1500:]
    conn = sqlite3.connect(path)
    try:
        yield conn
    finally:
        conn.close()


def _scalar(conn, sql: str) -> int:
    return int(conn.execute(sql).fetchone()[0])


def test_the_community_is_seeded(fresh_seed):
    """The forum shipped rendering "No discussions yet" on a fresh install.

    Nothing seeded ``discussions``, ``comments`` or ``votes``, so a visitor
    reached an empty page for a headline feature and had no way to judge whether
    it worked.
    """
    assert _scalar(fresh_seed, "SELECT COUNT(*) FROM discussions") >= 10
    assert _scalar(fresh_seed, "SELECT COUNT(*) FROM comments") >= 20
    assert _scalar(fresh_seed, "SELECT COUNT(*) FROM votes") >= 50
    # A thread with no replies is a noticeboard, not a forum.
    assert _scalar(fresh_seed, "SELECT COUNT(*) FROM discussions WHERE reply_count = 0") == 0
    # Both filter states must be populated, or the resolved/unresolved toggle is
    # a control that can never change the page.
    assert _scalar(fresh_seed, "SELECT COUNT(*) FROM discussions WHERE is_resolved = 1") >= 5
    assert _scalar(fresh_seed, "SELECT COUNT(*) FROM discussions WHERE is_resolved = 0") >= 3


def test_reply_counts_match_the_comments_that_exist(seeded):
    """``discussions.reply_count`` is denormalised, so nothing else keeps it true."""
    wrong = db.query(
        "SELECT d.id, d.title, d.reply_count, COUNT(c.id) AS actual FROM discussions d "
        "LEFT JOIN comments c ON c.discussion_id = d.id AND c.is_deleted = 0 "
        "GROUP BY d.id HAVING d.reply_count <> COUNT(c.id)"
    )
    assert [dict(r) for r in wrong] == []


# The table is plural and the vote's entity_type is singular; passing one where
# the other belongs joins nothing and every row looks mismatched.
@pytest.mark.parametrize("table,entity_type", [("discussions", "discussion"), ("comments", "comment")])
def test_vote_tallies_match_the_votes_cast(seeded, table, entity_type):
    """The displayed score must equal the votes actually stored against it."""
    wrong = db.query(
        f"SELECT t.id, t.upvotes, COALESCE(SUM(v.value), 0) AS actual FROM {table} t "
        "LEFT JOIN votes v ON v.entity_type = ? AND v.entity_id = t.id "
        "GROUP BY t.id HAVING t.upvotes <> COALESCE(SUM(v.value), 0)",
        entity_type,
    )
    assert [dict(r) for r in wrong] == [], f"{table}.upvotes disagrees with the votes table"


def test_every_thread_is_anchored_to_content_that_exists(seeded):
    dangling = db.query(
        "SELECT d.id, d.title, d.entity_id FROM discussions d "
        "WHERE d.entity_id IS NOT NULL AND NOT EXISTS "
        "(SELECT 1 FROM topics t WHERE t.id = d.entity_id)"
    )
    assert [dict(r) for r in dangling] == []
    # list_threads INNER JOINs profiles, so a thread whose author has no profile
    # row would vanish from the page rather than error - the quiet kind of bug.
    assert db.scalar(
        "SELECT COUNT(*) FROM discussions d LEFT JOIN profiles p ON p.user_id = d.user_id "
        "WHERE p.user_id IS NULL"
    ) == 0


def test_certificates_are_seeded_and_verify(seeded):
    """A certificate nobody has been issued leaves /certificates/{verify_id} untestable."""
    rows = db.query("SELECT verify_id FROM certificates")
    assert len(rows) >= 3
    for row in rows:
        assert progress.verify_certificate(row["verify_id"]), f"{row['verify_id']} does not verify"


def test_badges_can_actually_be_earned(seeded):
    """Twelve badges existed and the seeded history satisfied exactly one criterion.

    The criteria are real queries over submissions, coding_submissions,
    bookmarks and user_progress, so the history has to be real for the badge
    catalogue to mean anything. Not all of them should be earned either: a
    badge nobody has yet is believable, and awarding every badge would suggest
    the criteria were never evaluated.
    """
    earned = db.scalar("SELECT COUNT(DISTINCT badge_id) FROM user_badges")
    assert earned >= 5
    assert earned < db.scalar("SELECT COUNT(*) FROM badges")


def test_the_seeded_history_is_not_perfect(fresh_seed):
    """A learner with 100% accuracy over 190 answers is not a learner.

    Accuracy is shown on the profile and drives the gold certificate tier, so a
    flawless seeded record would both look synthetic and quietly promote every
    demo student.
    """
    total = _scalar(fresh_seed, "SELECT COUNT(*) FROM submissions")
    correct = _scalar(fresh_seed, "SELECT COUNT(*) FROM submissions WHERE is_correct = 1")
    assert total >= 100
    assert 0.6 < correct / total < 0.95, f"{correct}/{total} correct is not a believable record"
    # And no individual student should be spotless either.
    for (username,) in fresh_seed.execute(
        "SELECT u.username FROM users u JOIN submissions s ON s.user_id = u.id "
        "GROUP BY u.username HAVING COUNT(*) >= 20"
    ).fetchall():
        wrong = int(fresh_seed.execute(
            "SELECT COUNT(*) FROM submissions s JOIN users u ON u.id = s.user_id "
            "WHERE u.username = ? AND s.is_correct = 0", (username,)
        ).fetchone()[0])
        assert wrong >= 3, f"{username} has no wrong answers in the seeded history"


def test_the_community_page_shows_the_counts_it_was_given(seeded, client):
    """Every thread rendered "0 replies" and a score of 0.

    ``list_threads`` returns rows keyed ``upvotes`` and ``reply_count``; the
    template asked for ``thread.score`` and ``thread.comment_count``. Jinja runs
    with ``DebugUndefined``, which turns a missing key into a falsy value
    instead of raising, so ``or 0`` swallowed it and every thread looked brand
    new and unloved whatever the database held.

    Compared as multisets against the database rather than by status code: a 200
    says nothing about whether the numbers on the page are the numbers that were
    queried, and that is the whole failure mode here.
    """
    page = client.get("/community").text
    # -? because a downvoted thread has a negative score, and \d+ would silently
    # drop it from the list instead of failing the comparison.
    shown_scores = [int(n) for n in re.findall(r'<span class="n">(-?\d+)</span>', page)]
    shown_replies = [
        int(n) for n in re.findall(r'<span class="chip">(\d+) repl(?:y|ies)</span>', page)
    ]
    # Compared against the call the view itself makes, not against the whole
    # table: other suites post and hide threads in the shared session database,
    # so "everything in discussions" is not the same set as "everything the page
    # was asked to render". The point of the test is that the template draws the
    # numbers it was handed.
    rows, _total = community.list_threads(limit=40)
    assert sorted(shown_scores) == sorted(int(r["upvotes"]) for r in rows), (
        "the vote scores on the page are not the ones the view queried")
    assert sorted(shown_replies) == sorted(int(r["reply_count"]) for r in rows), (
        "the reply counts on the page are not the ones the view queried")
    # Guard the guard: if the seed produced nothing, the comparison above would
    # pass on two empty lists.
    assert sum(shown_replies) > 0, "the seed produced no replies to display"


# ---------------------------------------------------------------------------
# Staged language curriculum: stages, checkpoints, rotation and capstones.
#
# These guard the guarantees the path pages make to a learner: every module
# sits in exactly one real stage, every stage gates on three live checkpoint
# questions with a single correct answer, the answer key is rotated (and a
# reseed reproduces the same rotation), and every language path ends in a
# capstone brief that links forward and back.
# ---------------------------------------------------------------------------

_STAGE_SLUGS = tuple(language_curriculum.STAGE_SLUGS)


def _recomputed_checkpoints() -> list[dict]:
    return language_curriculum.checkpoint_questions()


def test_every_language_module_sits_in_exactly_one_real_stage(seeded):
    """A module with no stage, or a stage assignment drifting from the source,
    renders as a silently shorter path. Assert the DB matches the catalogue."""
    valid = set(_STAGE_SLUGS)
    rows = db.query("SELECT id, stage FROM language_modules")
    assert rows, "no language modules were seeded"
    for module in rows:
        assert module["stage"] in valid, f"{module['id']} has non-stage {module['stage']!r}"

    lang_ids = {row["slug"]: row["id"] for row in db.query("SELECT id, slug FROM programming_languages")}
    for language, assignment in language_curriculum.module_stage_map().items():
        assert language in lang_ids, f"{language} is not a seeded language"
        for slug, expected in assignment.items():
            actual = db.scalar("SELECT stage FROM language_modules WHERE id = ?", slug)
            assert actual == expected, f"{language}/{slug}: DB stage {actual!r} != source {expected!r}"


def test_each_language_has_three_stages_and_three_checkpoints_each(seeded):
    languages = db.query("SELECT id, slug FROM programming_languages")
    assert len(languages) == 10
    for language in languages:
        stages = db.query(
            "SELECT stage FROM language_stages WHERE language_id = ? ORDER BY order_index", language["id"]
        )
        assert [s["stage"] for s in stages] == list(_STAGE_SLUGS), language["slug"]
        for stage in stages:
            n = int(db.scalar(
                "SELECT count(*) FROM language_checkpoints WHERE language_id = ? AND stage = ?",
                language["id"], stage["stage"],
            ) or 0)
            assert n == 3, f"{language['slug']}/{stage['stage']} has {n} checkpoints, expected 3"
    assert int(db.scalar("SELECT count(*) FROM language_stages") or 0) == 30
    assert int(db.scalar("SELECT count(*) FROM language_checkpoints") or 0) == 90


def test_checkpoint_questions_are_active_with_one_correct_option(seeded):
    links = db.query(
        "SELECT lc.question_id, q.is_active, q.answer_index FROM language_checkpoints lc "
        "JOIN questions q ON q.id = lc.question_id"
    )
    assert len(links) == 90
    for link in links:
        qid = link["question_id"]
        assert link["is_active"] == 1, f"checkpoint question {qid} is not active"
        options = db.query(
            "SELECT body, is_correct, order_index FROM question_options WHERE question_id = ? "
            "ORDER BY order_index", qid,
        )
        assert len(options) == 4, f"{qid} has {len(options)} options, expected 4"
        assert sum(int(o["is_correct"]) for o in options) == 1, f"{qid} does not have exactly one correct option"
        correct = next(o for o in options if int(o["is_correct"]) == 1)
        assert correct["order_index"] == link["answer_index"], f"{qid}: answer_index disagrees with the flagged option"


def test_checkpoint_answer_positions_are_rotated_and_reproducible(seeded):
    """The key must not sit at a fixed visible position, and a reseed must
    reproduce the same bank. Compare the DB against a fresh recomputation."""
    entries = _recomputed_checkpoints()
    assert len(entries) == 90
    positions = [entry["correct"] for entry in entries]
    counts = {pos: positions.count(pos) for pos in range(4)}
    assert set(counts) == {0, 1, 2, 3}, f"not all four answer positions are used: {counts}"
    for pos, n in counts.items():
        assert n <= 30, f"position {pos} carries {n}/90 checkpoints - the rotation is not spreading the key"

    for entry in entries:
        qid = entry["slug"]
        row = db.query_one("SELECT answer_index FROM questions WHERE id = ?", qid)
        assert row is not None, f"checkpoint question {qid!r} was not seeded"
        assert row["answer_index"] == entry["correct"], (
            f"{qid}: stored answer_index {row['answer_index']} != recomputed {entry['correct']}"
        )
        options = db.query(
            "SELECT body FROM question_options WHERE question_id = ? ORDER BY order_index", qid
        )
        assert [o["body"] for o in options] == list(entry["options"]), (
            f"{qid}: stored option order drifted from the recomputed rotation"
        )


def test_language_capstone_links_forward_and_back(client, seeded):
    languages = db.query("SELECT id, slug FROM programming_languages")
    assert len(languages) == 10
    for language in languages:
        capstone = db.query_one(
            "SELECT slug FROM projects WHERE language_id = ? AND status = 'published' "
            "ORDER BY order_index LIMIT 1", language["id"],
        )
        assert capstone, f"{language['slug']} has no published capstone project"
        lang_page = client.get(f"/programming/{language['slug']}")
        assert lang_page.status_code == 200
        assert f'/projects/{capstone["slug"]}' in lang_page.text, (
            f"{language['slug']} path page does not link forward to its capstone"
        )
        proj_page = client.get(f"/projects/{capstone['slug']}")
        assert proj_page.status_code == 200
        assert f'/programming/{language["slug"]}' in proj_page.text, (
            f"capstone {capstone['slug']} does not link back to the {language['slug']} path"
        )


def test_published_dpps_cover_all_ten_language_tracks(seeded):
    covered = db.query(
        "SELECT DISTINCT lc.language_id FROM dpp_questions dq "
        "JOIN dpp_sets d ON d.id = dq.set_id AND d.published = 1 "
        "JOIN language_checkpoints lc ON lc.question_id = dq.question_id"
    )
    language_ids = {row["id"] for row in db.query("SELECT id FROM programming_languages")}
    assert {row["language_id"] for row in covered} == language_ids, (
        "not every language track has a checkpoint question in the published DPP archive"
    )


def test_fresh_seed_reproduces_the_expected_curriculum_counts(seeded):
    """One number per acceptance criterion, so a regression in any seeder is
    named by count rather than discovered by a broken page."""
    assert int(db.scalar("SELECT count(*) FROM programming_languages") or 0) == 10
    assert int(db.scalar("SELECT count(*) FROM language_modules") or 0) == 225
    assert int(db.scalar("SELECT count(*) FROM language_stages") or 0) == 30
    assert int(db.scalar("SELECT count(*) FROM language_checkpoints") or 0) == 90
    assert int(db.scalar("SELECT count(*) FROM questions WHERE is_active = 1") or 0) == 534
    assert int(db.scalar("SELECT count(*) FROM dpp_sets WHERE published = 1") or 0) == 107
    assert int(db.scalar("SELECT count(*) FROM projects WHERE status = 'published'") or 0) == 17
    assert int(db.scalar(
        "SELECT count(*) FROM projects WHERE status = 'published' AND language_id IS NOT NULL") or 0) == 10


def test_every_module_practice_link_resolves_to_a_seeded_problem(seeded):
    """A practice button that 404s is worse than no button. Every stored
    practice_slug must name a coding problem that was actually seeded."""
    from seed_data import (language_book_c, language_book_cpp,
                           language_book_csharp, language_book_java,
                           language_book_js, language_book_other,
                           language_book_py)

    books = (language_book_py, language_book_java, language_book_c,
             language_book_cpp, language_book_csharp, language_book_js,
             language_book_other)
    authored = {}
    for book in books:
        for module_slug, problem_slug in book.MODULE_PRACTICE.items():
            assert module_slug not in authored, f"two books map {module_slug!r}"
            authored[module_slug] = problem_slug
    assert len(authored) == 96, f"{len(authored)} book modules mapped, expected 96"

    stored = {
        row["slug"]: row["practice_slug"]
        for row in db.query("SELECT slug, practice_slug FROM language_modules WHERE practice_slug IS NOT NULL")
    }
    assert stored == authored, (
        f"stored practice links drifted from the authored maps: "
        f"missing {sorted(set(authored) - set(stored))[:5]}, "
        f"extra {sorted(set(stored) - set(authored))[:5]}"
    )
    problems = {row["slug"] for row in db.query("SELECT slug FROM coding_problems")}
    dangling = sorted(set(authored.values()) - problems)
    assert dangling == [], f"practice links name unseeded problems: {dangling}"


def test_language_pages_render_the_practice_buttons(client, seeded):
    """The staged path page must carry each module's 'code what you learned'
    button through to the browser, for a legacy path and the all-new C# one."""
    python_page = client.get("/programming/python")
    assert python_page.status_code == 200
    assert "/practice/problems/binary-search" in python_page.text
    csharp_page = client.get("/programming/csharp")
    assert csharp_page.status_code == 200
    assert "/practice/problems/drill-times-table" in csharp_page.text
    assert "csharp-interview-mastery" in csharp_page.text
