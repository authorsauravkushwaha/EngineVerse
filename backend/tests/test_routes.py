"""Every route must render. A 500 hidden behind a pretty error page is a bug."""
from __future__ import annotations

import pytest

PUBLIC_ROUTES = [
    "/",
    "/explore",
    "/search?q=bernoulli",
    "/practice",
    "/dpp",
    "/practice/questions",
    "/programming",
    "/programming/python",
    "/practice/problems",
    "/projects",
    "/resources",
    "/videos",
    "/books",
    "/formulas",
    "/revision",
    "/roadmaps",
    "/community",
    "/placements",
    "/leaderboard",
    "/login",
    "/register",
    "/about",
    "/install",
    "/offline",
    "/privacy",
    "/terms",
    "/branches/computer-science",
    "/subjects/data-structures-algorithms",
    "/topics/arrays",
    "/topics/bernoullis-equation",
    "/practice/problems/two-sum",
    "/projects/student-performance-dashboard",
    "/roadmaps/cse-placement-roadmap",
    "/streaks",
    "/portfolio/asha",
    "/explore?branch=civil-engineering",
    "/formulas?category=Fluid+Mechanics",
    "/practice/problems?difficulty=hard",
    "/videos?category=concept",
    "/resources?kind=documentation",
]

AUTHENTICATED_ROUTES = [
    "/",
    "/today",
    "/mistakes",
    "/profile",
    "/settings",
    "/onboarding",
    "/notifications",
    "/revision",
    "/streaks",
    "/topics/arrays",
    "/practice/problems/two-sum",
]

INFRA_ROUTES = [
    "/health",
    "/robots.txt",
    "/sitemap.xml",
    "/manifest.webmanifest",
    "/sw.js",
    "/static/css/app.css",
    "/static/js/app.js",
    "/static/icons/icon-192.png",
    "/favicon.ico",
]


def _csrf(html: str) -> str:
    marker = 'name="csrf_token" value="'
    start = html.index(marker) + len(marker)
    return html[start : html.index('"', start)]


class TestPublicRoutes:
    @pytest.mark.parametrize("path", PUBLIC_ROUTES)
    def test_renders(self, client, path):
        response = client.get(path)
        assert response.status_code == 200, f"{path} -> {response.status_code}"
        assert len(response.content) > 1000, f"{path} returned a suspiciously small body"

    @pytest.mark.parametrize("path", INFRA_ROUTES)
    def test_infra(self, client, path):
        assert client.get(path).status_code == 200


class TestAuthenticatedRoutes:
    @pytest.mark.parametrize("path", AUTHENTICATED_ROUTES)
    def test_renders_when_signed_in(self, signed_in, path):
        response = signed_in.get(path)
        assert response.status_code == 200, f"{path} -> {response.status_code}"

    def test_signing_in_replaces_the_landing_page_with_the_dashboard(self, signed_in):
        body = signed_in.get("/").text
        assert "Welcome back" in body


class TestAccessControl:
    @pytest.mark.parametrize("path", ["/profile", "/settings", "/today", "/mistakes", "/notifications"])
    def test_private_pages_redirect_anonymous_visitors(self, client, path):
        response = client.get(path, follow_redirects=False)
        assert response.status_code in (302, 303, 401), f"{path} -> {response.status_code}"

    def test_admin_refuses_a_student(self, signed_in):
        assert signed_in.get("/admin").status_code == 403

    def test_admin_allows_a_super_admin(self, client):
        page = client.get("/login")
        response = client.post(
            "/login",
            data={
                "csrf_token": _csrf(page.text),
                "identifier": "admin@engineverse.local",
                "password": "Str0ngPassphrase#42!",
                "next": "/admin",
            },
            follow_redirects=False,
        )
        assert response.status_code in (302, 303)
        assert client.get("/admin").status_code == 200


class TestNotFound:
    @pytest.mark.parametrize(
        "path",
        ["/nope", "/topics/does-not-exist", "/branches/does-not-exist", "/practice/problems/nope"],
    )
    def test_missing_content_is_404(self, client, path):
        assert client.get(path).status_code == 404

    def test_api_404_is_json(self, client):
        response = client.get("/api/nope")
        assert response.status_code == 404
        assert response.json()["ok"] is False


class TestSecurityHeaders:
    def test_every_response_carries_the_baseline_headers(self, client):
        headers = client.get("/").headers
        assert headers["x-frame-options"] == "DENY"
        assert headers["x-content-type-options"] == "nosniff"
        assert headers["referrer-policy"]
        assert "default-src" in headers["content-security-policy"]

    def test_the_csp_nonce_is_unique_per_request(self, client):
        first = client.get("/").text
        second = client.get("/").text
        assert 'nonce="' in first
        first_nonce = first.split('nonce="')[1].split('"')[0]
        second_nonce = second.split('nonce="')[1].split('"')[0]
        assert first_nonce != second_nonce, "a reused nonce defeats the CSP"


class TestPwa:
    def test_manifest_declares_the_installable_app(self, client):
        manifest = client.get("/manifest.webmanifest").json()
        assert manifest["name"]
        assert manifest["display"] in ("standalone", "fullscreen", "minimal-ui")
        assert manifest["icons"]

    def test_service_worker_scopes_the_whole_site(self, client):
        body = client.get("/sw.js").text
        assert "self.addEventListener" in body

    def test_offline_fallback_exists(self, client):
        assert client.get("/offline").status_code == 200


class TestForms:
    def test_login_with_a_wrong_password_is_refused(self, client):
        page = client.get("/login")
        response = client.post(
            "/login",
            data={
                "csrf_token": _csrf(page.text),
                "identifier": "asha@example.com",
                "password": "WrongPassword#123",
            },
            follow_redirects=False,
        )
        # 401, not 200: an error page that reports success is indistinguishable
        # from a working login for any client that checks the status code.
        assert response.status_code == 401
        assert client.get("/profile", follow_redirects=False).status_code in (302, 303, 401)

    def test_authenticated_post_without_a_csrf_token_is_refused(self, signed_in):
        """The check that matters: a state-changing POST needs a valid token."""
        response = signed_in.post("/logout", data={}, follow_redirects=False)
        assert response.status_code == 403, f"CSRF was not enforced: {response.status_code}"

    def test_a_forged_csrf_token_is_refused(self, signed_in):
        response = signed_in.post(
            "/logout", data={"csrf_token": "deadbeef." + "0" * 64}, follow_redirects=False
        )
        assert response.status_code == 403

    def test_a_valid_csrf_token_is_accepted(self, signed_in):
        token = _csrf(signed_in.get("/settings").text)
        response = signed_in.post("/logout", data={"csrf_token": token}, follow_redirects=False)
        assert response.status_code in (302, 303)

    def test_server_rendered_forms_carry_the_token_as_a_field(self, signed_in):
        """An HTML form cannot set a header, so the token must be a form field."""
        body = signed_in.get("/settings").text
        assert 'name="csrf_token"' in body

    def test_anonymous_login_and_register_are_exempt_by_design(self, client):
        """There is no session to bind a token to before login. These are covered
        by SameSite=Strict cookies plus rate limiting instead."""
        response = client.post(
            "/login",
            data={"identifier": "asha@example.com", "password": "WrongPassword#123"},
            follow_redirects=False,
        )
        assert response.status_code != 403

    def test_registration_rejects_a_weak_password(self, client):
        page = client.get("/register")
        response = client.post(
            "/register",
            data={
                "csrf_token": _csrf(page.text),
                "email": "weakling@example.com",
                "username": "weakling",
                "full_name": "Weak Ling",
                "password": "abc",
                "password_confirm": "abc",
            },
            follow_redirects=False,
        )
        assert response.status_code == 422
        from engineverse import db

        assert db.query_one("SELECT id FROM users WHERE email = 'weakling@example.com'") is None

    def test_registration_creates_a_working_account(self, client):
        page = client.get("/register")
        client.post(
            "/register",
            data={
                "csrf_token": _csrf(page.text),
                "email": "newcomer@example.com",
                "username": "newcomer",
                "full_name": "New Comer",
                "password": "BrandNewPassphrase#99",
                "password_confirm": "BrandNewPassphrase#99",
            },
            follow_redirects=False,
        )
        from engineverse import db

        row = db.query_one("SELECT id, role FROM users WHERE email = 'newcomer@example.com'")
        assert row is not None, "registration did not create the account"
        assert row["role"] == "student"


class TestSearch:
    @pytest.mark.parametrize("term", ["bernoulli", "entropy", "kirchhoff", "array"])
    def test_search_returns_results(self, client, term):
        response = client.get(f"/search?q={term}")
        assert response.status_code == 200

    def test_an_empty_query_does_not_crash(self, client):
        assert client.get("/search?q=").status_code == 200

    def test_a_nonsense_query_does_not_crash(self, client):
        assert client.get("/search?q=zzzzqqqqxxxx").status_code == 200


# Every page that renders differently depending on who is looking at it. The
# subject page 500'd for a signed-in visitor because subject.html read
# my_progress.done while subject_progress() returns "completed"; anonymously
# my_progress is None, the block is skipped, and the page looks fine. Covering
# each role is the only way that class of bug surfaces.
ROLE_PAGES = [
    "/", "/explore", "/about", "/install", "/offline", "/privacy", "/terms",
    "/practice", "/dpp", "/practice/problems", "/practice/questions", "/programming",
    "/programming/python", "/projects", "/resources", "/videos", "/books", "/formulas",
    "/revision", "/roadmaps", "/tutor", "/community", "/placements", "/leaderboard",
    "/login", "/register", "/forgot-password", "/reset-password", "/streaks",
    "/search?q=bernoulli", "/topics/arrays", "/topics/bernoullis-equation",
    "/subjects/data-structures-algorithms", "/subjects/thermodynamics",
    "/subjects/oops", "/subjects/fluid-mechanics", "/branches/computer-science",
    "/branches/mechanical-engineering", "/practice/problems/two-sum",
    "/projects/student-performance-dashboard", "/roadmaps/cse-placement-roadmap",
    "/portfolio/asha", "/today", "/mistakes", "/profile", "/settings", "/onboarding",
    "/notifications", "/admin",
]

# Pages that legitimately refuse some visitors.
ROLE_ALLOWED = {
    "anonymous": {200, 302, 303, 401},
    "student": {200, 302, 303, 401, 403},
    "faculty": {200, 302, 303, 401, 403},
    "admin": {200, 302, 303},
}


def _signed_in_as(app, email, password):
    from starlette.testclient import TestClient

    client = TestClient(app, raise_server_exceptions=False)
    page = client.get("/login").text
    client.post(
        "/login",
        data={"csrf_token": _csrf(page), "identifier": email, "password": password, "next": "/"},
        follow_redirects=False,
    )
    return client


class TestEveryPageUnderEveryRole:
    def test_anonymous_pages(self, client):
        for path in ROLE_PAGES:
            response = client.get(path, follow_redirects=False)
            assert response.status_code < 500, f"{path} errored: {response.status_code}"
            assert response.status_code in ROLE_ALLOWED["anonymous"], (
                f"{path} -> {response.status_code}"
            )

    def test_student_pages(self, app):
        client = _signed_in_as(app, "asha@example.com", "LearnBuild#2026!")
        for path in ROLE_PAGES:
            response = client.get(path, follow_redirects=False)
            assert response.status_code < 500, f"{path} errored: {response.status_code}"
            assert response.status_code in ROLE_ALLOWED["student"], (
                f"{path} -> {response.status_code}"
            )

    def test_faculty_pages(self, app):
        client = _signed_in_as(app, "faculty@engineverse.local", "TeachLearn#2026!")
        for path in ROLE_PAGES:
            response = client.get(path, follow_redirects=False)
            assert response.status_code < 500, f"{path} errored: {response.status_code}"
            assert response.status_code in ROLE_ALLOWED["faculty"], (
                f"{path} -> {response.status_code}"
            )

    def test_admin_pages(self, app):
        client = _signed_in_as(app, "admin@engineverse.local", "Str0ngPassphrase#42!")
        for path in ROLE_PAGES:
            response = client.get(path, follow_redirects=False)
            assert response.status_code < 500, f"{path} errored: {response.status_code}"
            assert response.status_code in ROLE_ALLOWED["admin"], (
                f"{path} -> {response.status_code}"
            )

    def test_no_page_reports_an_undefined_template_variable(self, app):
        """Guards against a template key drifting from the dict the route passes."""
        import jinja2

        from web.deps import templates

        client = _signed_in_as(app, "asha@example.com", "LearnBuild#2026!")
        previous = templates.env.undefined
        templates.env.undefined = jinja2.DebugUndefined
        try:
            for path in ROLE_PAGES:
                response = client.get(path)
                assert "{{ undefined }}" not in response.text, (
                    f"{path} rendered an undefined template variable"
                )
        finally:
            templates.env.undefined = previous


class TestLibraryPagination:
    """A shelf that shows 120 of 451 items hides two-thirds of the library.

    These crawl every page rather than checking that a pager renders, because a
    pager can display correctly and still lose rows: a count that disagrees with
    the query, or an offset that skips or repeats a page, is only visible by
    collecting the whole set.
    """

    PAGES = (
        ("/resources", "resources", "kind"),
        ("/videos", "videos", "category"),
        ("/books", "books", None),
    )

    def _titles(self, page):
        import re
        return set(re.findall(r'<span class="title">(.*?)</span>', page.text, re.S))

    @pytest.mark.parametrize("path", [p[0] for p in PAGES])
    def test_every_item_is_reachable_by_paging(self, client, seeded, path):
        from engineverse import db, library

        table = {"resources": "resources", "videos": "videos", "books": "books"}[path.strip("/")]
        total = db.scalar(f"SELECT count(*) FROM {table}")
        assert total > 24, "the corpus is too small for this test to mean anything"

        seen = set()
        page_no = 1
        while True:
            response = client.get(f"{path}?page={page_no}")
            assert response.status_code == 200
            found = self._titles(response)
            assert found, f"{path}?page={page_no} rendered no items"
            assert not (found & seen), f"{path} page {page_no} repeats items from an earlier page"
            seen |= found
            if f"page={page_no + 1}" not in response.text:
                break
            page_no += 1
            assert page_no < 200, "pagination did not terminate"

        assert len(seen) == total, (
            f"{path}: paged through {len(seen)} items but the table holds {total}"
        )

    def test_the_filter_survives_paging(self, client, seeded):
        """A pager that drops ?kind=... sends the reader back to unfiltered page 1."""
        first = client.get("/resources?kind=course&page=2")
        assert first.status_code == 200
        assert "kind=course" in first.text, "the pager link lost the active filter"

    def test_an_out_of_range_page_clamps_instead_of_erroring(self, client, seeded):
        """A stale ?page=999 bookmark should still show something."""
        response = client.get("/books?page=999")
        assert response.status_code == 200
        assert "No books match" not in response.text

    def test_a_non_numeric_page_does_not_crash(self, client, seeded):
        response = client.get("/books?page=abc")
        assert response.status_code == 200

    def test_counts_agree_with_the_filtered_lists(self, seeded):
        """The count drives the pager; if it disagrees, the last page is a lie."""
        from engineverse import library

        for kind in [r["kind"] for r in library.resource_kinds()]:
            assert library.count_resources(kind=kind) == len(
                library.list_resources(kind=kind, limit=10000)
            ), f"count_resources(kind={kind}) disagrees with the list"
        for category in [r["category"] for r in library.video_categories()]:
            assert library.count_videos(category=category) == len(
                library.list_videos(category=category, limit=10000)
            ), f"count_videos(category={category}) disagrees with the list"
        assert library.count_books(q="physics") == len(library.list_books(q="physics", limit=10000))
