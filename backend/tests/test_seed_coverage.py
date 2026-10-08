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
