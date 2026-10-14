"""Every URL the application hands to a reader resolves - and shows what it named.

A link that answers 404 is easy to catch. The failures this file exists for are
worse: they answer 200 and then show the reader something other than what the
link promised.

An audit of the URLs the application *generates* - as opposed to the ones
written into templates, which ``test_navigation.py`` and the publisher's
``assert_links()`` already cover - found five:

* ``search.ENTITY_URLS["question"]`` was ``/practice/questions/{slug}``. There
  is no such page; that path exists only under the JSON API as
  ``/api/practice/questions/{id}``. Every question in every search result was a
  404, and search is in the top bar.
* ``video``, ``book``, ``resource`` and ``formula`` results used ``#slug``
  fragments into pages that paginate 24 rows at a time. A browser sends only the
  path, so the reader landed at the top of a long list with the item they had
  asked for several pages in. ``/formulas`` was worse: it capped at 300 rows
  while the seeder ships 365, so 65 formulas rendered nowhere at all.
* ``resource`` results pointed at ``/resources``, which is the site index - the
  off-site collection lives at ``/resources/offsite``.
* ``recommend.retry_plan()`` emitted ``/dpp/today``, a route that does not exist
  (``/dpp`` is today's set, ``/dpp/{date}`` takes a date), and
  ``/practice?topic=...&difficulty=easy`` on a page that reads no query
  parameters at all - so the recovery plan on ``/mistakes`` promised easy
  questions on the weak topic and delivered the unfiltered practice home.
* ``recommend.for_topic()`` emitted ``/videos?q={slug}``, and the video library
  searches title and channel but never slug, so it matched nothing. Two of its
  branches - the interview question and the topic video - cannot fire against
  the seed data, which is why neither was ever caught; see
  ``test_the_recommendation_branches_the_seed_data_never_exercised``.

The same audit found ``recommend.dashboard()`` returning one list twice, under
two different headings. That is a link that works and still misleads, so it is
asserted here too.
"""
from __future__ import annotations

import html
import re

import pytest

from engineverse import catalog, db, recommend, search
from engineverse.security.ids import now_ms, ulid


def _unescaped(client, url: str) -> str:
    """Fetches a page and undoes HTML escaping, so a title with an apostrophe
    or an ampersand in it can be compared against the database's copy."""
    return html.unescape(client.get(url).text)


def _shows(client, url: str, needle: str) -> None:
    """Asserts a URL both resolves and actually contains the thing it named.

    Checking only the status code is what let four of these bugs ship: an
    ignored filter and a fragment into a paginated page both answer 200.
    """
    response = client.get(url)
    assert response.status_code == 200, f"{url} answered {response.status_code}"
    assert needle.lower() in html.unescape(response.text).lower(), (
        f"{url} rendered but never showed {needle!r} - the link resolved to the "
        f"wrong thing rather than to nothing"
    )


# ---------------------------------------------------------------------------
# Search results
# ---------------------------------------------------------------------------

def test_every_search_result_url_resolves(signed_in):
    """A search result is the one link a reader trusts to be about their query."""
    rows = db.query("SELECT entity_type, entity_id FROM search_index")
    assert rows, "the search index is empty, so this test cannot check anything"
    by_type: dict[str, list[str]] = {}
    for row in rows:
        by_type.setdefault(row["entity_type"], []).append(row["entity_id"])
    for entity_type, entity_ids in sorted(by_type.items()):
        for entity_id in entity_ids[:3]:
            url = search.url_for(entity_type, entity_id)
            status = signed_in.get(url).status_code
            assert status == 200, (
                f"a search result for {entity_type} {entity_id!r} links to {url}, "
                f"which answered {status}"
            )


def test_every_fragment_target_is_rendered_by_the_page_it_points_into(signed_in):
    """A ``#slug`` link is only as good as the ``id`` the page renders.

    Three collection pages rendered no ids at all, so their fragments scrolled
    nowhere and the browser stayed at the top of the list.
    """
    fragment_types = sorted(t for t, template in search.ENTITY_URLS.items() if "#" in template)
    assert fragment_types, "no URL in the table uses a fragment any more"
    checked = 0
    for entity_type in fragment_types:
        rows = db.query(
            "SELECT entity_id FROM search_index WHERE entity_type = ? LIMIT 3", entity_type
        )
        for row in rows:
            url = search.url_for(entity_type, row["entity_id"])
            path, _, fragment = url.partition("#")
            assert fragment, f"{entity_type} built {url} with no fragment to check"
            assert f'id="{fragment}"' in signed_in.get(path).text, (
                f"{url} points at #{fragment}, which the page does not render"
            )
            checked += 1
    assert checked, "no fragment links were checked"


# Pages that list a whole collection 24 rows at a time. A deep link into one of
# these has to survive pagination, which a fragment cannot: the item is usually
# on a later page than the one that renders.
PAGINATED_COLLECTIONS = (
    ("video", "videos", "title", "/videos"),
    ("book", "books", "title", "/books"),
    ("resource", "resources", "title", "/resources/offsite"),
    ("formula", "formulas", "name", "/formulas"),
)


@pytest.mark.parametrize("entity_type,table,label_column,listing", PAGINATED_COLLECTIONS)
def test_a_deep_link_to_an_item_beyond_the_first_page_still_shows_it(
    signed_in, entity_type, table, label_column, listing,
):
    """The item a fragment could never reach is the one worth testing."""
    rendered = set(re.findall(r'id="([a-z0-9\-]+)"', signed_in.get(listing).text))
    rows = db.query(f"SELECT slug, {label_column} AS label FROM {table}")
    beyond = [row for row in rows if row["slug"] not in rendered]
    assert beyond, (
        f"every {entity_type} fits on the first page of {listing}, so this test "
        f"cannot check what it was written for"
    )
    target = beyond[0]
    _shows(signed_in, search.url_for(entity_type, target["slug"]), target["label"])


def test_the_formula_centre_shows_every_formula_and_says_how_many(signed_in):
    """The sheet rendered one page and dropped the rest.

    It had no pager, so a hard-coded limit of 300 against a catalogue of 365
    silently deleted 65 rows: they were not on the sheet, and the ?slug= links
    that point into it resolved to a page that did not contain them. The pager
    now covers the catalogue, and its own count is the evidence.
    """
    total = int(db.scalar("SELECT count(*) AS c FROM formulas") or 0)
    assert total, "the seeder ships formulas; an empty table makes this vacuous"
    page = signed_in.get("/formulas").text
    rendered = len(re.findall(r'class="panel" id="', page))
    counter = re.search(r'class="pager-count">\s*[\d–-]+\s*of\s*(\d+)', page)
    assert counter, "the formula centre must page, or it cannot show the whole catalogue"
    assert int(counter.group(1)) == total, (
        f"{total} formulas exist but the pager counts {counter.group(1)}"
    )
    assert 0 < rendered <= 24, f"a page of the sheet rendered {rendered} formulas"


def test_every_formula_is_reachable_from_the_sheet(signed_in):
    """Paging is only acceptable if nothing becomes unreachable by it.

    The last formula in the catalogue is the one a truncated limit used to drop,
    so it is the one worth following.
    """
    last = db.query_one("SELECT slug, name FROM formulas ORDER BY category DESC, name DESC LIMIT 1")
    assert last, "no formulas to check"
    _shows(signed_in, f"/formulas?slug={last['slug']}", last["name"])


# ---------------------------------------------------------------------------
# Recommendations
# ---------------------------------------------------------------------------

def test_every_topic_recommendation_url_resolves(signed_in):
    """``for_topic()`` renders on every topic page, so a bad URL is site-wide."""
    topics = db.query("SELECT slug FROM topics WHERE status='published' LIMIT 60")
    assert topics, "no published topics to recommend from"
    checked = 0
    for row in topics:
        topic = catalog.get_topic(row["slug"])
        for item in recommend.for_topic(topic):
            url = item.get("url")
            if not url:
                continue
            checked += 1
            status = signed_in.get(url).status_code
            assert status != 404, f"'{item['title']}' on /topics/{row['slug']} links to {url}, a 404"
            # A recommendation that ends in a fragment is only worth clicking if
            # the page renders that anchor - /formulas#slug scrolls to a formula
            # card because formulas.html gives every card an id.
            path, _, fragment = url.partition("#")
            if fragment:
                assert f'id="{fragment}"' in signed_in.get(path).text, (
                    f"'{item['title']}' links to {url}, but {path} renders no #{fragment} anchor"
                )
    assert checked > 20, f"only {checked} recommendation URLs were checked"


def test_the_recommendation_branches_the_seed_data_never_exercised(signed_in):
    """Two ``for_topic()`` branches cannot fire against the seeded catalogue.

    The interview branch needs a question with ``kind='interview'`` and the seed
    data ships only ``mcq``; the video branch needs ``videos.topic_id`` and all
    400 seeded videos have it NULL. Both were emitting URLs that did not work,
    and no test could reach them. This builds the two rows, runs the branches
    and removes the rows again.
    """
    topic = catalog.get_topic(
        db.query_one("SELECT slug FROM topics WHERE status='published' AND subject_id IS NOT NULL LIMIT 1")["slug"]
    )
    assert topic is not None
    question_id, video_id = ulid(), ulid()
    stem = "Link audit interview stem, unique enough to search for"
    video_title = "Link Audit Topic Video"
    try:
        db.execute(
            "INSERT INTO questions (id, slug, topic_id, subject_id, kind, difficulty, stem, "
            "time_weight, tags, is_active, created_at) VALUES (?, ?, ?, ?, 'interview', 'easy', ?, 1, '[]', 1, ?)",
            question_id, "link-audit-interview-question", topic["id"], topic["subject_id"], stem, now_ms(),
        )
        db.execute(
            "INSERT INTO question_options (id, question_id, label, body, is_correct, order_index) "
            "VALUES (?, ?, 'A', 'Link audit option', 1, 0)",
            ulid(), question_id,
        )
        db.execute(
            "INSERT INTO videos (id, slug, title, channel, url, duration_s, language, level, category, "
            "topic_id, rating, embeddable, created_at) "
            "VALUES (?, 'link-audit-topic-video', ?, 'Link Audit Channel', 'https://example.invalid/link-audit', "
            "600, 'en', 'beginner', 'lecture', ?, 5, 0, ?)",
            video_id, video_title, topic["id"], now_ms(),
        )

        items = {item["kind"]: item for item in recommend.for_topic(topic)}
        assert "interview" in items, f"the interview branch still did not fire: {sorted(items)}"
        assert "video" in items, f"the video branch still did not fire: {sorted(items)}"
        # Both have to land on the item they name, not merely on a page that
        # happens to contain it. The video library renders page one of 400 rows
        # when it is given a parameter it does not read, and a freshly inserted
        # row can sit on that page, so "the title is in the HTML" passes for a
        # link that filtered nothing. The narrowing banner is what proves the
        # page was told which row to show.
        _shows(signed_in, items["interview"]["url"], stem)
        assert "Filtered to" in signed_in.get(items["interview"]["url"]).text, (
            f"{items['interview']['url']} did not narrow the question bank to the one question"
        )
        _shows(signed_in, items["video"]["url"], video_title)
        assert "Narrowed to one video" in signed_in.get(items["video"]["url"]).text, (
            f"{items['video']['url']} showed the video by luck, from the unfiltered "
            f"first page - the link must narrow the library to that one row"
        )
    finally:
        db.execute("DELETE FROM question_options WHERE question_id = ?", question_id)
        db.execute("DELETE FROM questions WHERE id = ?", question_id)
        db.execute("DELETE FROM videos WHERE id = ?", video_id)


def test_every_recovery_plan_step_resolves(signed_in, demo_user):
    """The plan on /mistakes is what a struggling learner is told to do next.

    ``retry_plan()`` returns nothing until somebody has actually got questions
    wrong, and a freshly seeded database has no submissions at all - so the test
    records two wrong answers of its own rather than borrowing state that the
    demo data does not have, and clears them again.
    """
    row = db.query_one(
        "SELECT q.topic_id FROM questions q JOIN topics t ON t.id = q.topic_id "
        "WHERE q.is_active = 1 AND t.status = 'published' AND q.topic_id IS NOT NULL "
        "GROUP BY q.topic_id HAVING count(*) >= 2 LIMIT 1"
    )
    assert row, "no topic carries two active questions, so no weak topic can be constructed"
    siblings = db.query(
        "SELECT id FROM questions WHERE topic_id = ? AND is_active = 1 LIMIT 2", row["topic_id"]
    )
    assert len(siblings) >= 2, "a weak topic needs two attempts against it"
    written = []
    try:
        for question in siblings:
            submission_id = ulid()
            written.append(submission_id)
            db.execute(
                "INSERT INTO submissions (id, user_id, question_id, answer_index, is_correct, created_at) "
                "VALUES (?, ?, ?, 0, 0, ?)",
                submission_id, demo_user["id"], question["id"], now_ms(),
            )
        plan = recommend.retry_plan(demo_user["id"])
        assert plan, "two wrong answers on one topic must produce a recovery plan"
        steps = 0
        for entry in plan:
            for step in entry["steps"]:
                steps += 1
                status = signed_in.get(step["url"]).status_code
                assert status != 404, (
                    f"'{step['label']}' links to {step['url']}, which answered {status}"
                )
        assert steps >= 4, f"expected a full plan, got {steps} steps"
    finally:
        for submission_id in written:
            db.execute("DELETE FROM submissions WHERE id = ?", submission_id)


def test_the_practice_recommendation_lands_on_filtered_questions(signed_in):
    """/practice reads no query parameters, so a ?topic= link to it is a link to
    the unfiltered practice home whatever it claims."""
    row = db.query_one(
        "SELECT t.slug AS topic_slug, t.title AS topic_title, count(*) AS n "
        "FROM topics t JOIN questions q ON q.topic_id = t.id "
        "WHERE q.is_active = 1 AND t.status='published' GROUP BY t.slug, t.title "
        "HAVING n >= 2 ORDER BY n DESC LIMIT 1"
    )
    assert row, "no topic carries questions, so the practice recommendation cannot be checked"
    items = {item["kind"]: item for item in recommend.for_topic(catalog.get_topic(row["topic_slug"]))}
    assert "practice" in items
    url = items["practice"]["url"]
    assert url.startswith("/practice/questions"), (
        f"{url} points at a page that ignores ?topic=; the question bank is the one that filters"
    )
    page = signed_in.get(url).text
    assert page.count("data-quiz=") == row["n"], (
        f"{url} rendered {page.count('data-quiz=')} questions but the topic has {row['n']}"
    )


# ---------------------------------------------------------------------------
# The dashboard
# ---------------------------------------------------------------------------

def test_the_dashboard_does_not_recommend_what_it_just_said(demo_user):
    """``dashboard()['lessons']`` used to be ``dashboard()['continue']`` verbatim.

    dashboard.html renders them under two headings - "Continue where you left
    off" and "Recommended for you" - so the page told a learner the same thing
    twice and never showed anything they had not started.
    """
    data = recommend.dashboard(demo_user["id"])
    assert data["continue"] and data["lessons"], "both panels are empty, so this proves nothing"
    continuing = {row["slug"] for row in data["continue"]}
    recommended = {row["slug"] for row in data["lessons"]}
    weak = {row["slug"] for row in data["weak"]}
    assert not (continuing & recommended), (
        f"'Recommended for you' repeats 'Continue where you left off': {sorted(continuing & recommended)}"
    )
    assert not (weak & recommended), (
        f"'Recommended for you' repeats 'Needs another pass': {sorted(weak & recommended)}"
    )


def test_the_rendered_dashboard_panels_list_different_topics(signed_in):
    """The same property, on the page the reader actually sees."""
    page = signed_in.get("/").text

    def topics_under(heading: str) -> set[str]:
        block = re.search(re.escape(f"<h2>{heading}</h2>") + r"(.*?)</section>", page, re.S)
        return set(re.findall(r'href="/topics/([a-z0-9\-]+)"', block.group(1))) if block else set()

    continuing = topics_under("Continue where you left off")
    recommended = topics_under("Recommended for you")
    assert continuing and recommended, (
        f"expected both panels on the dashboard, found "
        f"continue={sorted(continuing)} recommended={sorted(recommended)}"
    )
    assert not (continuing & recommended), f"both panels list {sorted(continuing & recommended)}"


# ---------------------------------------------------------------------------
# Page structure
# ---------------------------------------------------------------------------

def _representative_paths(limit_per_kind: int = 3) -> list[str]:
    """A spread of pages: every indexable destination plus one of each detail kind."""
    from engineverse import navigation

    paths = list(navigation.indexable_paths())
    for table, template in (
        ("topics", "/topics/{}"), ("subjects", "/subjects/{}"), ("branches", "/branches/{}"),
        ("projects", "/projects/{}"), ("roadmaps", "/roadmaps/{}"),
    ):
        column = "status = 'published'" if table in ("topics", "subjects") else "1=1"
        for row in db.query(f"SELECT slug FROM {table} WHERE {column} LIMIT ?", limit_per_kind):
            paths.append(template.format(row["slug"]))
    for row in db.query("SELECT slug FROM coding_problems LIMIT ?", limit_per_kind):
        paths.append(f"/practice/problems/{row['slug']}")
    for row in db.query("SELECT slug FROM coding_sheets LIMIT ?", limit_per_kind):
        paths.append(f"/sheets/{row['slug']}")
    for row in db.query("SELECT slug FROM formulas LIMIT ?", limit_per_kind):
        paths.append(f"/formulas?slug={row['slug']}")
    return paths


def test_no_page_skips_a_heading_level(signed_in, client):
    """A reader who navigates by heading hears the outline, and a page that goes
    from h1 to h4 tells them three levels of structure are missing.

    Nearly every page did. The footer's column headings were ``<h4>`` and the
    footer is on every page, so the skip was site-wide; ``/formulas`` went h1 to
    h3 for all 365 formula names, and ``/explore`` reached h4 for its branch
    groups. The level is the outline, not the font size - ``.h-sub`` keeps a
    promoted heading at the size the design wanted.
    """
    offenders: dict[str, str] = {}
    checked = 0
    for label, viewer in (("signed-in", signed_in), ("anon", client)):
        for path in _representative_paths():
            response = viewer.get(path)
            if response.status_code != 200:
                continue
            checked += 1
            previous = 0
            for level in (int(x) for x in re.findall(r"<h([1-6])\b", response.text)):
                if previous and level > previous + 1:
                    offenders[f"{label}:{path}"] = f"h{previous} -> h{level}"
                    break
                previous = level
    assert checked > 20, f"only {checked} pages were checked"
    assert not offenders, f"{len(offenders)} page(s) skip a heading level: {offenders}"


def test_no_rendered_link_is_empty(signed_in, client):
    """A link with no text is invisible to a screen reader and, when it is the
    only thing in a table cell, invisible to everyone.

    /programming and /profile both rendered ``<a href="/practice/problems/"></a>``
    as the Problem column of every submission, because the query selected the
    problem's ``title`` and ``slug`` while the templates read ``problem_title``
    and ``problem_slug``. Jinja renders a missing attribute as nothing, so the
    column was blank and the link pointed at ``/practice/problems/``.
    """
    offenders: dict[str, int] = {}
    for label, viewer in (("signed-in", signed_in), ("anon", client)):
        for path in _representative_paths():
            response = viewer.get(path)
            if response.status_code != 200:
                continue
            for match in re.finditer(r"<a\b([^>]*)>(.*?)</a>", response.text, re.S):
                attrs, inner = match.group(1), match.group(2)
                if "aria-label" in attrs or "title=" in attrs:
                    continue
                if not re.sub(r"<[^>]+>", "", inner).strip():
                    key = f"{label}:{path}"
                    offenders[key] = offenders.get(key, 0) + 1
    assert not offenders, f"pages render links with no text: {offenders}"


def test_anonymous_home_renders_real_sample_problems(client, seeded):
    """``coding.list_problems()`` returns ``(rows, total)``. Passing the tuple
    straight to ``home.html`` made ``sample_problems`` a two-element tuple on
    the landing page and on the GitHub Pages reading copy, rendering blank
    cards that linked to ``/practice/problems/`` with no slug."""
    page = client.get("/").text
    assert 'href="/practice/problems/"' not in page
    problem_links = re.findall(r'href="/practice/problems/([a-z0-9\-]+)"', page)
    assert len(problem_links) >= 6, f"expected sample problems on home.html, found {problem_links}"


def test_pages_workflow_exports_reading_copy():
    from pathlib import Path

    workflow = (Path(__file__).resolve().parents[2] / ".github" / "workflows" / "pages.yml").read_text(encoding="utf-8")
    assert "export_pages.py --out site --reading-copy" in workflow


# ---------------------------------------------------------------------------
# The question bank's filters
# ---------------------------------------------------------------------------

def test_the_question_bank_honours_a_slug_filter(signed_in):
    """This is what every question search result now points at."""
    row = db.query_one("SELECT slug, stem FROM questions WHERE is_active = 1 LIMIT 1")
    assert row
    page = signed_in.get(f"/practice/questions?slug={row['slug']}").text
    assert page.count("data-quiz=") == 1, "a ?slug= link must narrow the bank to that one question"
    assert html.unescape(row["stem"]).lower() in html.unescape(page).lower()
    assert "Filtered to" in page, "the page must say why only one question is showing"


def test_the_question_bank_filters_by_topic_and_difficulty(signed_in):
    row = db.query_one(
        "SELECT t.slug AS topic_slug, q.difficulty, count(*) AS n "
        "FROM topics t JOIN questions q ON q.topic_id = t.id "
        "WHERE q.is_active = 1 AND t.status='published' GROUP BY t.slug, q.difficulty "
        "HAVING n >= 1 ORDER BY n DESC LIMIT 1"
    )
    assert row
    url = f"/practice/questions?topic={row['topic_slug']}&difficulty={row['difficulty']}"
    assert signed_in.get(url).text.count("data-quiz=") == row["n"]


def test_an_unknown_topic_filter_narrows_to_nothing_rather_than_everything(signed_in):
    """Dropping a filter it cannot resolve would silently widen the page back to
    the whole catalogue, which reads as an answer to a question nobody asked."""
    whole_bank = signed_in.get("/practice/questions").text.count("data-quiz=")
    assert whole_bank > 1, "the bank is too small for this test to mean anything"
    page = signed_in.get("/practice/questions?topic=not-a-real-topic").text
    assert page.count("data-quiz=") == 0
    assert "No questions match" in page
