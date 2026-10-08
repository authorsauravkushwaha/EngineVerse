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

import pytest

from engineverse import db, library
from seed_data import library_data
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


@pytest.mark.parametrize("table", PER_SUBJECT_TABLES)
def test_every_subject_has_a_usable_shelf(seeded, table):
    """No subject may have a shelf thin enough to look abandoned.

    An empty subject page is the obvious failure; a one-item page is the
    subtler one, and it was the actual state of 67 of 73 subjects' books.
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


def test_every_standard_note_carries_all_thirteen_sections(seeded):
    """The template promises thirteen sections; 42 topics were missing several."""
    incomplete = db.query(
        "SELECT n.id, count(*) AS have FROM notes n "
        "JOIN note_sections s ON s.note_id = n.id "
        "WHERE n.quality_level = 'standard' GROUP BY n.id HAVING have < 13"
    )
    assert [(r["id"], r["have"]) for r in incomplete] == [], "standard notes with fewer than 13 sections"


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
    from seed_data import notes_extra, topics_core, topics_cse
    from engineverse.security.sanitize import slugify

    known = {slugify(t["title"]) for t in list(topics_core.TOPICS) + list(topics_cse.TOPICS)}
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
