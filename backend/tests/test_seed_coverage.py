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

#: Tables whose rows must exist for at least one entry per subject.
PER_SUBJECT_TABLES = ("videos", "books", "resources", "flashcards")


def _subject_slugs() -> set[str]:
    return {row[0] for row in SUBJECTS}


@pytest.mark.parametrize("table", PER_SUBJECT_TABLES)
def test_every_subject_has_at_least_one_entry(seeded, table):
    """No subject may have an empty shelf.

    An empty subject page looks abandoned, and it is the failure mode the
    generated corpus exists to prevent.
    """
    empty = db.query(
        f"SELECT s.slug FROM subjects s WHERE NOT EXISTS "
        f"(SELECT 1 FROM {table} t WHERE t.subject_id = s.id) ORDER BY s.slug"
    )
    assert [row["slug"] for row in empty] == [], f"subjects with no {table}"


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
