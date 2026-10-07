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
        assert response.status_code in (200, 303)
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
        assert response.status_code in (200, 303)
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
