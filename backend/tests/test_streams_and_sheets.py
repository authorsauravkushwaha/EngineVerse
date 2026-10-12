"""The per-stream study hub, curated sheets and the in-app resource directory.

These cover the parts a learner actually feels:

* ``/stream`` opens on the branch on their profile, and a stream can be switched
  without JavaScript;
* a stream page only claims what the database holds, and says so when a shelf is
  empty rather than offering a dead link;
* every sheet in the bank is reachable, its problems resolve, and its progress
  counters agree with the real submissions table;
* the resources page is a directory of this site, and the one page that does
  link out is labelled as optional.
"""
from __future__ import annotations

import re

import pytest

from engineverse import coding, db, hub

PASSWORD = "Stream-Hub-Test-Password-9!"


def _csrf(html: str) -> str:
    marker = 'name="csrf_token" value="'
    start = html.index(marker) + len(marker)
    return html[start : html.index('"', start)]


def _register(client, *, branch: str, username: str) -> None:
    page = client.get("/register")
    response = client.post(
        "/register",
        data={
            "csrf_token": _csrf(page.text),
            "email": f"{username}@example.test",
            "username": username,
            "full_name": "Stream Tester",
            "password": PASSWORD,
            "password_confirm": PASSWORD,
            "next": "/",
            "branch": branch,
            "semester": "3",
        },
        follow_redirects=False,
    )
    assert response.status_code in (302, 303), response.status_code


# ---------------------------------------------------------------------------
# The stream hub
# ---------------------------------------------------------------------------

class TestStreamHub:
    def test_it_opens_on_the_branch_on_the_profile(self, client, seeded):
        _register(client, branch="mechanical-engineering", username="hubmech")
        response = client.get("/stream", follow_redirects=True)
        assert response.status_code == 200
        assert "Mechanical Engineering" in response.text
        assert "Engineering Computing" in response.text, "the stream's own sheet is not offered"

    def test_an_account_with_no_branch_still_gets_a_stream(self, client, seeded):
        """The hub is public: a missing branch is a picker, not an error page."""
        response = client.get("/stream", follow_redirects=True)
        assert response.status_code == 200
        assert "/stream/" in str(response.url)
        assert "Jump to a stream" in response.text

    def test_the_picker_switches_streams_and_stays_on_site(self, client, seeded):
        response = client.get("/stream", params={"to": "/stream/civil-engineering"}, follow_redirects=False)
        assert response.status_code == 303
        assert response.headers["location"] == "/stream/civil-engineering"

    @pytest.mark.parametrize(
        "hostile",
        ["https://evil.example", "//evil.example", "/admin", "/stream/../admin", "/stream/nope-nope"],
    )
    def test_the_picker_refuses_anything_that_is_not_a_stream(self, client, seeded, hostile):
        """The picker value is a redirect target, so it must not be free-form."""
        response = client.get("/stream", params={"to": hostile}, follow_redirects=False)
        assert response.status_code == 303
        assert not response.headers["location"].startswith("//")
        assert "evil.example" not in response.headers["location"]
        assert response.headers["location"].startswith("/stream/")

    def test_an_unknown_stream_is_a_404(self, client, seeded):
        assert client.get("/stream/not-a-branch").status_code == 404

    def test_counts_match_the_tables_behind_them(self, client, seeded):
        """A hub that overstates its shelves sends learners to empty pages."""
        branch = hub.branch_row("computer-science")
        data = hub.stream(branch["id"])
        assert data["cards"]["subjects"] == len(data["subjects"])
        assert data["cards"]["topics"] == sum(row["topics"] for row in data["subjects"])
        assert data["cards"]["notes"] == db.scalar(
            "SELECT count(*) FROM notes n JOIN topics t ON t.id = n.topic_id "
            "JOIN subjects s ON s.id = t.subject_id WHERE s.branch_id = ? AND n.status = 'published'",
            branch["id"],
        )

    def test_every_active_branch_renders(self, client, seeded):
        for row in db.query("SELECT slug FROM branches WHERE is_active = 1"):
            response = client.get(f"/stream/{row['slug']}")
            assert response.status_code == 200, row["slug"]

    def test_the_streams_index_lists_every_branch(self, client, seeded):
        response = client.get("/streams")
        assert response.status_code == 200
        assert response.text.count("subjects") >= 40

    def test_a_semester_filter_narrows_without_emptying_the_page(self, client, seeded):
        branch = hub.branch_row("computer-science")
        whole = hub.stream(branch["id"])
        narrowed = hub.stream(branch["id"], semester_id=3)
        assert len(narrowed["subjects"]) <= len(whole["subjects"])
        assert narrowed["subjects"], "filtering to an untagged semester must fall back to the branch"


# ---------------------------------------------------------------------------
# Sheets
# ---------------------------------------------------------------------------

class TestSheets:
    def test_every_sheet_renders_with_its_problems(self, client, seeded):
        for sheet in coding.list_sheets():
            response = client.get(f"/sheets/{sheet['slug']}")
            assert response.status_code == 200, sheet["slug"]
            # Jinja escapes the ampersand in a title such as "Arrays & Hashing".
            assert sheet["title"].replace("&", "&amp;") in response.text
            for problem in coding.problems_for_sheet(sheet["id"]):
                assert f"/practice/problems/{problem['slug']}" in response.text

    def test_the_index_lists_every_published_sheet(self, client, seeded):
        response = client.get("/sheets")
        assert response.status_code == 200
        for sheet in coding.list_sheets():
            assert f"/sheets/{sheet['slug']}" in response.text

    def test_a_sheets_problem_count_matches_its_membership(self, client, seeded):
        for sheet in coding.list_sheets():
            assert sheet["problem_count"] == len(coding.problems_for_sheet(sheet["id"])), sheet["slug"]

    def test_the_bank_is_covered_by_sheets(self, seeded):
        """A problem in no sheet is a problem nobody will find."""
        placed = {
            row["problem_id"]
            for row in db.query("SELECT problem_id FROM coding_sheet_problems")
        }
        all_problems = {row["id"] for row in db.query("SELECT id FROM coding_problems")}
        assert all_problems <= placed, sorted(all_problems - placed)[:5]

    def test_progress_follows_real_submissions(self, client, seeded):
        """The counter is a query, not a guess: it must move when a problem is solved."""
        _register(client, branch="computer-science", username="sheetprog")
        sheet = coding.sheet_by_slug("arrays-hashing")
        before = coding.sheet_progress(
            db.scalar("SELECT id FROM users WHERE username = 'sheetprog'"), sheet["id"]
        )
        assert before["solved"] == 0
        assert before["total"] == len(coding.problems_for_sheet(sheet["id"]))

        user_id = db.scalar("SELECT id FROM users WHERE username = 'sheetprog'")
        problem = coding.problems_for_sheet(sheet["id"])[0]
        db.execute(
            "INSERT INTO coding_submissions (id,user_id,problem_id,language,code,status,passed,total,"
            "is_accepted,created_at) VALUES (?,?,?,?,?,?,?,?,?,?)",
            "sheetprog-accepted", user_id, problem["id"], "python", "pass", "accepted", 1, 1, 1,
            db.scalar("SELECT 1") and 1,
        )
        after = coding.sheet_progress(user_id, sheet["id"])
        assert after["solved"] == 1
        assert after["percent"] == round(1 / after["total"] * 100)

    def test_the_problems_page_filters_to_one_sheet(self, client, seeded):
        sheet = coding.sheet_by_slug("graphs-traversal")
        response = client.get("/practice/problems", params={"sheet": sheet["slug"]})
        assert response.status_code == 200
        for problem in coding.problems_for_sheet(sheet["id"]):
            assert f"/practice/problems/{problem['slug']}" in response.text

    def test_a_problem_names_the_sheets_it_belongs_to(self, client, seeded):
        response = client.get("/practice/problems/two-sum")
        assert response.status_code == 200
        for sheet in coding.sheets_for_problem("two-sum"):
            assert f"/sheets/{sheet['slug']}" in response.text

    def test_an_unknown_sheet_is_a_404(self, client, seeded):
        assert client.get("/sheets/not-a-sheet").status_code == 404


# ---------------------------------------------------------------------------
# Resources
# ---------------------------------------------------------------------------

class TestResourceDirectory:
    def test_the_directory_lists_streams_rather_than_other_sites(self, client, seeded):
        response = client.get("/resources")
        assert response.status_code == 200
        assert "/stream/computer-science" in response.text
        assert "/sheets" in response.text

    def test_the_external_shelf_is_separate_and_labelled(self, client, seeded):
        response = client.get("/resources/offsite")
        assert response.status_code == 200
        assert "You do not need any of this" in response.text
        assert "optional" in response.text.lower()

    def test_old_bookmarks_still_reach_the_shelf(self, client, seeded):
        """?kind= and ?page= belong to the paginated shelf, not to the directory."""
        response = client.get("/resources?kind=course&page=2")
        assert response.status_code == 200
        assert "kind=course" in response.text, "the filter was dropped on the way"

    def test_shapes_in_the_header_are_not_external_links_in_the_hub(self, client, seeded):
        """Nothing on a stream page should send a learner to another site."""
        response = client.get("/stream/computer-science")
        external = [
            url for url in re.findall(r'href="(https?://[^"]+)"', response.text)
        ]
        assert external == [], external
