"""The security guarantees the platform's threat model rests on."""
from __future__ import annotations

import pytest
from starlette.testclient import TestClient

from engineverse.security import passwords, rbac
from engineverse.security.ids import ulid
from engineverse.security.sanitize import is_safe_url, safe_link, slugify, strip_html


class TestPasswordHashing:
    def test_hash_verifies(self):
        hashed = passwords.hash_password("Str0ngPassphrase#42!")
        assert passwords.verify_password("Str0ngPassphrase#42!", hashed)

    def test_wrong_password_is_rejected(self):
        hashed = passwords.hash_password("Str0ngPassphrase#42!")
        assert not passwords.verify_password("Str0ngPassphrase#43!", hashed)

    def test_hash_is_salted(self):
        """Two hashes of the same password must differ, or the store is a rainbow table."""
        first = passwords.hash_password("Str0ngPassphrase#42!")
        second = passwords.hash_password("Str0ngPassphrase#42!")
        assert first != second
        assert passwords.verify_password("Str0ngPassphrase#42!", second)

    def test_scrypt_parameters_are_recorded_in_the_hash(self):
        hashed = passwords.hash_password("Str0ngPassphrase#42!")
        assert hashed.startswith("scrypt$16384$8$1$")

    def test_plaintext_never_appears_in_the_hash(self):
        hashed = passwords.hash_password("Str0ngPassphrase#42!")
        assert "Str0ngPassphrase" not in hashed

    def test_unicode_is_normalised_before_hashing(self):
        """NFKC, so visually identical passwords from different keyboards match."""
        composed = "p\u00e4ssw\u00f6rd#1Aa"
        decomposed = "pa\u0308sswo\u0308rd#1Aa"
        hashed = passwords.hash_password(composed)
        assert passwords.verify_password(decomposed, hashed)

    def test_a_strong_password_has_no_issues(self):
        assert passwords.check_password_strength("Str0ngPassphrase#42!") == []

    @pytest.mark.parametrize(
        ("password", "expected"),
        [
            ("abc", "too_short"),
            ("password", "common"),
            ("password", "too_short"),
            ("password123", "common"),
        ],
    )
    def test_weak_passwords_are_flagged(self, password, expected):
        codes = {issue.code for issue in passwords.check_password_strength(password)}
        assert expected in codes

    def test_identity_in_password_is_flagged(self):
        """The check needs the identity as context - it cannot guess the name."""
        codes = {i.code for i in passwords.check_password_strength("Asha12345678!", ["Asha", "asha"])}
        assert "contains_identity" in codes

    def test_identity_check_needs_context(self):
        """Without context there is nothing to compare against, so no false positive."""
        codes = {i.code for i in passwords.check_password_strength("Asha12345678!")}
        assert "contains_identity" not in codes

    def test_repeated_characters_are_flagged(self):
        codes = {i.code for i in passwords.check_password_strength("Aaaaaaaaaaaa1!")}
        assert "repeats" in codes

    def test_every_issue_carries_a_user_facing_message(self):
        for issue in passwords.check_password_strength("abc"):
            assert issue.message

    def test_needs_rehash_detects_legacy_parameters(self):
        legacy = "scrypt$4096$8$1$AAAA$BBBB"
        assert passwords.needs_rehash(legacy)
        assert not passwords.needs_rehash(passwords.hash_password("Str0ngPassphrase#42!"))


class TestSafeUrls:
    """Open-redirect and javascript: URI defences."""

    @pytest.mark.parametrize(
        "url",
        ["/practice", "/topics/arrays?x=1", "https://example.com/a", "https://example.com"],
    )
    def test_safe_targets_pass(self, url):
        assert is_safe_url(url)

    @pytest.mark.parametrize(
        "url",
        [
            "javascript:alert(1)",
            "JaVaScRiPt:alert(1)",
            "data:text/html,<script>alert(1)</script>",
            "file:///etc/passwd",
            "\tjavascript:alert(1)",
            "",
        ],
    )
    def test_unsafe_targets_are_refused(self, url):
        assert not is_safe_url(url)

    @pytest.mark.parametrize("url", ["//evil.com", "///evil.com", "/\\evil.com"])
    def test_protocol_relative_urls_are_refused(self, url):
        """Browsers resolve `//host` against the current scheme, so accepting it
        would turn any `next` parameter into an open redirect."""
        assert not is_safe_url(url)

    @pytest.mark.parametrize("url", ["https://nptel.ac.in/x", "http://example.org", "mailto:a@b.c"])
    def test_external_links_are_allowed(self, url):
        """The platform legitimately links out to NPTEL, MIT OCW and publishers."""
        assert is_safe_url(url)

    def test_safe_link_falls_back(self):
        assert safe_link("javascript:alert(1)", "/") == "/"
        assert safe_link("/practice", "/") == "/practice"


class TestSanitising:
    def test_strip_html_removes_tags(self):
        assert strip_html("<b>hi</b><script>x</script>") == "hix"

    @pytest.mark.parametrize(
        ("value", "expected"),
        [
            ("Bernoulli's Equation", "bernoullis-equation"),
            ("Kirchhoff's Laws", "kirchhoffs-laws"),
            ("  Two   Sum  ", "two-sum"),
            ("St. John's College", "st-johns-college"),
            ("!!!", "item"),
        ],
    )
    def test_slugify(self, value, expected):
        assert slugify(value) == expected

    def test_slugify_caps_length(self):
        assert len(slugify("x" * 500)) <= 96


class TestRbac:
    @pytest.mark.parametrize(
        ("role", "capability", "allowed"),
        [
            # super_admin holds every capability
            ("super_admin", "content.publish", True),
            ("super_admin", "users.manage", True),
            ("super_admin", "settings.manage", True),
            # students hold none
            ("student", "content.publish", False),
            ("student", "users.manage", False),
            ("student", "community.moderate", False),
            # subject_expert authors content but cannot administer users
            ("subject_expert", "content.publish", True),
            ("subject_expert", "content.create", True),
            ("subject_expert", "users.manage", False),
            # moderators moderate but do not publish
            ("moderator", "community.moderate", True),
            ("moderator", "content.publish", False),
            # analytics_admin is read-only
            ("analytics_admin", "analytics.view", True),
            ("analytics_admin", "content.delete", False),
            # unknown roles fail closed
            ("anonymous", "content.publish", False),
            ("", "content.publish", False),
        ],
    )
    def test_capabilities(self, role, capability, allowed):
        assert rbac.can(role, capability) is allowed

    def test_staff_roles(self):
        assert rbac.is_staff("super_admin")
        assert rbac.is_staff("subject_expert")
        assert not rbac.is_staff("student")

    def test_unknown_capability_denies(self):
        """Fail closed: an unrecognised capability must not be granted."""
        assert rbac.can("super_admin", "not.a.real.capability") is False

    def test_assert_can_raises(self):
        with pytest.raises(rbac.Forbidden):
            rbac.assert_can("student", "users.manage")

    def test_every_role_has_a_label(self):
        """A role that renders as 'Student' by fallback is a misconfiguration."""
        for role in rbac.ROLES:
            assert rbac.role_label(role) != "Student" or role == "student"

    def test_every_seeded_role_is_known(self):
        """Guards the bug where the seeder minted a 'faculty' role that rbac
        does not define, leaving that account with zero capabilities."""
        from engineverse import db

        for row in db.query("SELECT DISTINCT role FROM users"):
            assert row["role"] in rbac.ROLES, f"unknown role in the users table: {row['role']}"


class TestIdentifiers:
    def test_ulids_are_unique(self):
        ids = {ulid() for _ in range(5000)}
        assert len(ids) == 5000

    def test_ulids_sort_chronologically(self):
        """The point of a ULID: lexicographic order matches creation order."""
        first, second = ulid(), ulid()
        assert sorted([second, first]) == [first, second]

    def test_ulid_shape(self):
        value = ulid()
        assert len(value) == 26
        assert value.isalnum()


def _csrf(html: str) -> str:
    """Pulls the token out of a rendered form."""
    marker = 'name="csrf_token" value="'
    return html[html.index(marker) + len(marker):].split('"')[0]


class TestEveryFormCarriesAToken:
    """Static check over the templates.

    A POST form without a csrf_token field is rejected by CsrfMiddleware with a
    403, so the button looks live and does nothing. The community "Ask a
    question" and "Reply" forms shipped that way.
    """

    def test_every_post_form_in_every_template_has_a_csrf_field(self):
        import pathlib
        import re

        template_dir = pathlib.Path(__file__).resolve().parents[1] / "templates"
        assert template_dir.is_dir(), f"template directory missing: {template_dir}"

        offenders = []
        checked = 0
        for path in sorted(template_dir.glob("*.html")):
            text = path.read_text()
            for match in re.finditer(r"<form\b[^>]*>(.*?)</form>", text, re.S):
                opening = text[match.start():text.index(">", match.start()) + 1]
                method_match = re.search(r'method="([^"]+)"', opening)
                method = (method_match.group(1) if method_match else "get").lower()
                if method != "post":
                    continue
                checked += 1
                if 'name="csrf_token"' not in match.group(1):
                    action = re.search(r'action="([^"]+)"', opening)
                    offenders.append(
                        f"{path.name}:{text[:match.start()].count(chr(10)) + 1} "
                        f"-> {action.group(1) if action else '(no action)'}"
                    )

        assert checked >= 20, f"only found {checked} POST forms - the pattern probably broke"
        assert not offenders, "POST forms missing a csrf_token field:\n  " + "\n  ".join(offenders)

    def test_a_no_javascript_reply_is_accepted_not_refused(self, signed_in):
        """Submits the reply form exactly as a browser without scripting would:
        urlencoded, with the token in the body and no X-CSRF-Token header."""
        from engineverse import db

        token = _csrf(signed_in.get("/community").text)
        created = signed_in.post(
            "/api/community/threads",
            json={"title": "Thread for a plain reply", "body": "Body text for the post.",
                  "kind": "question"},
            headers={"x-csrf-token": token},
        )
        thread_id = created.json()["id"]

        response = signed_in.post(
            "/api/community/comments",
            # No X-CSRF-Token header on purpose - a plain form cannot set one.
            data={"csrf_token": token, "threadId": thread_id,
                  "body": "Replying without any JavaScript at all."},
            follow_redirects=False,
        )
        assert response.status_code != 403, "the reply form was rejected for a missing token"
        assert response.status_code in (200, 303), response.text
        row = db.query_one("SELECT id FROM comments WHERE parent_id IS NOT NULL OR 1=1 ORDER BY created_at DESC LIMIT 1")
        assert row is not None

    def test_a_no_javascript_question_is_accepted_not_refused(self, signed_in):
        token = _csrf(signed_in.get("/community").text)
        response = signed_in.post(
            "/api/community/threads",
            data={"csrf_token": token, "title": "Asked without JavaScript",
                  "body": "Posting from a browser with scripting disabled.",
                  "kind": "question", "tags": "no-js, forms"},
            follow_redirects=False,
        )
        assert response.status_code != 403, "the question form was rejected for a missing token"
        assert response.status_code in (200, 303), response.text


class TestAdminCapabilityNames:
    """The admin write routes used to check capabilities that do not exist.

    assert_can(viewer.role, "admin.users") and "admin.config" and
    "content.moderate" are not in rbac.CAPABILITIES, so every check failed -
    including for super_admin - and because rbac.Forbidden had no exception
    handler the refusal surfaced as a 500.
    """

    def test_every_capability_checked_in_the_web_layer_exists(self):
        import pathlib
        import re

        from engineverse.security import rbac

        web_dir = pathlib.Path(__file__).resolve().parents[1] / "web"
        used = set()
        for path in sorted(web_dir.glob("*.py")):
            used.update(re.findall(r'assert_can\([^,]+,\s*"([^"]+)"', path.read_text()))

        assert used, "no assert_can calls found - the pattern probably broke"
        unknown = used - set(rbac.CAPABILITIES)
        assert not unknown, f"web layer checks capabilities that do not exist: {sorted(unknown)}"

    def _admin(self, app):
        from starlette.testclient import TestClient

        client = TestClient(app, raise_server_exceptions=False)
        page = client.get("/login").text
        client.post(
            "/login",
            data={"csrf_token": _csrf(page), "identifier": "admin@engineverse.local",
                  "password": "Str0ngPassphrase#42!", "next": "/"},
            follow_redirects=False,
        )
        return client, _csrf(client.get("/admin").text)

    def test_a_super_admin_can_actually_use_the_admin_forms(self, app, seeded):
        from engineverse import db

        client, token = self._admin(app)
        target = db.query_one("SELECT id FROM users WHERE email = 'ravi@example.com'")["id"]

        role = client.post("/admin/users/role",
                           data={"user_id": target, "role": "mentor", "csrf_token": token},
                           follow_redirects=False)
        assert role.status_code == 303, role.text
        assert db.query_one("SELECT role FROM users WHERE id = ?", target)["role"] == "mentor"

        status = client.post("/admin/users/status",
                             data={"user_id": target, "status": "active", "csrf_token": token},
                             follow_redirects=False)
        assert status.status_code == 303, status.text

        config = client.post("/admin/config",
                             data={"site_name": "EngineVerse", "tagline": "Learn everything.",
                                   "csrf_token": token},
                             follow_redirects=False)
        assert config.status_code == 303, config.text
        assert db.query_one("SELECT value FROM site_config WHERE key = 'tagline'")["value"] == "Learn everything."

    def test_a_moderator_can_resolve_a_report(self, app, seeded):
        from engineverse import community, db

        client, token = self._admin(app)
        reporter = db.query_one("SELECT id FROM users WHERE email = 'asha@example.com'")["id"]
        thread = db.query_one("SELECT id FROM discussions LIMIT 1")
        report_id = community.report(reporter, "thread", thread["id"], "Spam posting")

        response = client.post("/admin/reports/resolve",
                               data={"report_id": report_id, "csrf_token": token},
                               follow_redirects=False)
        assert response.status_code == 303, response.text
        assert db.query_one("SELECT status FROM reports WHERE id = ?", report_id)["status"] == "resolved"

    def test_a_student_is_refused_with_403_not_a_500(self, app, seeded):
        from starlette.testclient import TestClient

        client = TestClient(app, raise_server_exceptions=False)
        page = client.get("/login").text
        client.post(
            "/login",
            data={"csrf_token": _csrf(page), "identifier": "asha@example.com",
                  "password": "LearnBuild#2026!", "next": "/"},
            follow_redirects=False,
        )
        token = _csrf(client.get("/community").text)
        for path, data in [("/admin/users/role", {"user_id": "x", "role": "super_admin"}),
                           ("/admin/users/status", {"user_id": "x", "status": "banned"}),
                           ("/admin/config", {"site_name": "Hijacked"}),
                           ("/admin/reports/resolve", {"report_id": "x"})]:
            response = client.post(path, data={**data, "csrf_token": token}, follow_redirects=False)
            assert response.status_code == 403, f"{path} -> {response.status_code}"
            assert response.status_code != 500

    def test_a_refusal_is_audited_not_logged_as_a_crash(self, app, seeded):
        from starlette.testclient import TestClient

        from engineverse import db

        client = TestClient(app, raise_server_exceptions=False)
        page = client.get("/login").text
        client.post(
            "/login",
            data={"csrf_token": _csrf(page), "identifier": "asha@example.com",
                  "password": "LearnBuild#2026!", "next": "/"},
            follow_redirects=False,
        )
        token = _csrf(client.get("/community").text)
        client.post("/admin/config", data={"site_name": "Hijacked", "csrf_token": token},
                    follow_redirects=False)

        forbidden = db.query_one(
            "SELECT id FROM audit_logs WHERE action = 'security.forbidden' ORDER BY id DESC LIMIT 1"
        )
        assert forbidden is not None, "the refusal was not audited"
        crash = db.query_one(
            "SELECT id FROM audit_logs WHERE action = 'app.error' AND meta LIKE '%Forbidden%'"
        )
        assert crash is None, "an authorisation refusal was recorded as an application error"


class TestAdminInputValidation:
    """Admin forms must refuse bad input with a 4xx, never a 500.

    set_role() inserted into user_roles without checking the target existed, so
    a stale or mistyped user id raised a raw FOREIGN KEY constraint failure.
    """

    def _admin(self, app):
        from starlette.testclient import TestClient

        client = TestClient(app, raise_server_exceptions=False)
        page = client.get("/login").text
        client.post(
            "/login",
            data={"csrf_token": _csrf(page), "identifier": "admin@engineverse.local",
                  "password": "Str0ngPassphrase#42!", "next": "/"},
            follow_redirects=False,
        )
        return client, _csrf(client.get("/admin").text)

    def test_a_missing_user_is_404_not_a_crash(self, app, seeded):
        client, token = self._admin(app)
        for path in ("/admin/users/role", "/admin/users/status"):
            data = {"user_id": "no-such-user", "csrf_token": token}
            data["role" if "role" in path else "status"] = "mentor" if "role" in path else "active"
            response = client.post(path, data=data, follow_redirects=False)
            assert response.status_code == 404, f"{path} -> {response.status_code}"

    def test_an_unknown_role_is_422(self, app, seeded):
        from engineverse import db

        client, token = self._admin(app)
        target = db.query_one("SELECT id FROM users WHERE email = 'ravi@example.com'")["id"]
        response = client.post("/admin/users/role",
                               data={"user_id": target, "role": "emperor", "csrf_token": token},
                               follow_redirects=False)
        assert response.status_code == 422
        assert db.query_one("SELECT role FROM users WHERE id = ?", target)["role"] != "emperor"

    def test_an_unknown_status_is_422(self, app, seeded):
        from engineverse import db

        client, token = self._admin(app)
        target = db.query_one("SELECT id FROM users WHERE email = 'ravi@example.com'")["id"]
        response = client.post("/admin/users/status",
                               data={"user_id": target, "status": "exploded", "csrf_token": token},
                               follow_redirects=False)
        assert response.status_code == 422

    def test_a_valid_change_still_applies(self, app, seeded):
        from engineverse import db

        client, token = self._admin(app)
        target = db.query_one("SELECT id FROM users WHERE email = 'priya@example.com'")["id"]
        response = client.post("/admin/users/role",
                               data={"user_id": target, "role": "moderator", "csrf_token": token},
                               follow_redirects=False)
        assert response.status_code == 303
        assert db.query_one("SELECT role FROM users WHERE id = ?", target)["role"] == "moderator"

    def test_no_admin_misstep_is_recorded_as_an_application_error(self, app, seeded):
        from starlette.testclient import TestClient

        from engineverse import db

        client, token = self._admin(app)
        for data in ({"user_id": "ghost", "role": "mentor"},
                     {"user_id": "ghost", "status": "active"},
                     {"user_id": "x", "role": "emperor"}):
            path = "/admin/users/role" if "role" in data else "/admin/users/status"
            client.post(path, data={**data, "csrf_token": token}, follow_redirects=False)

        crashes = db.query(
            "SELECT meta FROM audit_logs WHERE action = 'app.error' AND meta LIKE '%IntegrityError%'"
        )
        assert not crashes, f"foreign-key failures reached the error log: {crashes}"


@pytest.fixture()
def restore_password():
    """Restores every demo password a reset test changes.

    The database is session-scoped, so a test that resets the student 'asha'
    leaves the password changed for the rest of the run - and `signed_in`, which
    later suites depend on, logs in as asha. Without this the failure surfaces
    far from its cause as a 401 in an unrelated test.
    """
    from engineverse import db

    before = {row["id"]: row["password_hash"]
              for row in db.query("SELECT id, password_hash FROM users")}
    try:
        yield
    finally:
        for user_id, hashed in before.items():
            db.execute("UPDATE users SET password_hash = ? WHERE id = ?", hashed, user_id)
        db.execute("DELETE FROM password_resets")


class TestPasswordResetTokens:
    """Reset tokens used to be looked up with a LIKE pattern against the audit log.

    ``meta LIKE '%"<token>"%'`` meant a submitted LIKE wildcard matched whichever
    account had requested a reset most recently, so posting ``%`` as the token
    reset that account's password - a full takeover with no credential at all.
    """

    @staticmethod
    def _token(html: str) -> str:
        import re

        found = re.search(r"token=([A-Za-z0-9_\-]+)", html)
        assert found, "the development build should surface the reset link"
        return found.group(1)

    def test_a_like_wildcard_does_not_match_any_pending_reset(self, client):
        from engineverse import db

        victim = db.query_one("SELECT id, email FROM users WHERE role = 'student' LIMIT 1")
        client.post("/forgot-password", data={"email": victim["email"]})

        attacker = TestClient(app=client.app, raise_server_exceptions=False)
        page = attacker.get("/reset-password").text
        csrf = _csrf(page)
        for guess in ["%", "_", '%"%', "' OR '1'='1", "*"]:
            response = attacker.post(
                "/reset-password",
                data={"token": guess, "password": "AttackerControlled#2026!", "csrf_token": csrf},
                follow_redirects=False,
            )
            assert response.status_code == 400, (
                f"token {guess!r} was accepted - the wildcard takeover is back"
            )

    def test_a_valid_token_resets_the_password_once(self, client, restore_password):
        from engineverse import auth, db

        victim = db.query_one("SELECT id, email FROM users WHERE role = 'student' LIMIT 1")
        page = client.post("/forgot-password", data={"email": victim["email"]}).text
        token = self._token(page)

        fresh = TestClient(app=client.app, raise_server_exceptions=False)
        response = fresh.post(
            "/reset-password",
            data={"token": token, "password": "BrandNewPassphrase#2026!", "csrf_token": _csrf(fresh.get("/reset-password").text)},
            follow_redirects=False,
        )
        assert response.status_code == 303
        assert response.headers["location"] == "/login?error=reset"

        # The token is single use.
        replay = TestClient(app=client.app, raise_server_exceptions=False)
        again = replay.post(
            "/reset-password",
            data={"token": token, "password": "Replayed#2026!xx", "csrf_token": _csrf(replay.get("/reset-password").text)},
            follow_redirects=False,
        )
        assert again.status_code == 400, "a used reset token was accepted again"

    def test_an_expired_token_is_refused(self, client, restore_password):
        from engineverse import auth, db

        victim = db.query_one("SELECT id, email FROM users WHERE role = 'student' LIMIT 1")
        page = client.post("/forgot-password", data={"email": victim["email"]}).text
        token = self._token(page)
        db.execute("UPDATE password_resets SET expires_at = ?", auth.now_ms() - 1000)

        fresh = TestClient(app=client.app, raise_server_exceptions=False)
        response = fresh.post(
            "/reset-password",
            data={"token": token, "password": "BrandNewPassphrase#2026!", "csrf_token": _csrf(fresh.get("/reset-password").text)},
            follow_redirects=False,
        )
        assert response.status_code == 400

    def test_a_new_request_supersedes_the_previous_link(self, client, restore_password):
        from engineverse import db

        victim = db.query_one("SELECT id, email FROM users WHERE role = 'student' LIMIT 1")
        first = self._token(client.post("/forgot-password", data={"email": victim["email"]}).text)
        second = self._token(client.post("/forgot-password", data={"email": victim["email"]}).text)
        assert first != second

        stale = TestClient(app=client.app, raise_server_exceptions=False)
        response = stale.post(
            "/reset-password",
            data={"token": first, "password": "BrandNewPassphrase#2026!", "csrf_token": _csrf(stale.get("/reset-password").text)},
            follow_redirects=False,
        )
        assert response.status_code == 400, "a superseded reset link still worked"

    def test_tokens_are_stored_hashed(self, client, restore_password):
        from engineverse import db

        victim = db.query_one("SELECT id, email FROM users WHERE role = 'student' LIMIT 1")
        token = self._token(client.post("/forgot-password", data={"email": victim["email"]}).text)
        rows = db.query("SELECT token_hash FROM password_resets")
        assert rows, "no reset row was written"
        assert all(token not in row["token_hash"] for row in rows), "the plaintext token is stored"
        assert all(len(row["token_hash"]) == 64 for row in rows), "not a SHA-256 digest"


class TestFormValidationErrors:
    """A blank required field must not answer with FastAPI's internal JSON."""

    def test_blank_form_fields_render_a_page(self, client):
        page = client.get("/login").text
        response = client.post(
            "/login",
            data={"identifier": "", "password": "", "csrf_token": _csrf(page)},
            follow_redirects=False,
            headers={"Accept": "text/html"},
        )
        assert response.status_code == 422
        assert not response.text.lstrip().startswith("{"), (
            "a browser form was answered with raw JSON"
        )
        assert "identifier" in response.text

    def test_api_clients_still_get_json(self, client):
        response = client.post("/api/coding/run", data={"nope": "1"}, headers={"Accept": "*/*"})
        assert response.status_code == 422
        assert response.json()["ok"] is False
        assert "fields" in response.json()


class TestSvgSanitising:
    """Diagram specs are stored markup rendered with `| safe`.

    CSP with a per-request nonce stops an injected script from running, but that
    is a header doing the work of a sanitiser. The admin CMS is meant to grow a
    diagram editor, so the markup is cleaned where it is read instead.
    """

    def test_script_elements_are_removed(self):
        from engineverse.security.sanitize import sanitize_svg

        out = sanitize_svg('<svg><rect x="1" /><script>alert(1)</script></svg>')
        assert "<script" not in out
        assert "<rect" in out, "legitimate drawing elements must survive"

    def test_event_handlers_are_removed(self):
        from engineverse.security.sanitize import sanitize_svg

        out = sanitize_svg('<svg><circle onload="alert(1)" r="4" onclick="x()" /></svg>')
        assert "onload" not in out
        assert "onclick" not in out
        assert 'r="4"' in out

    def test_script_urls_are_removed(self):
        from engineverse.security.sanitize import sanitize_svg

        for payload in ('javascript:alert(1)', 'JaVaScRiPt:alert(1)', 'data:text/html;base64,PHN2Zz4=',
                        'vbscript:msgbox(1)'):
            out = sanitize_svg(f'<svg><a href="{payload}"><text>x</text></a></svg>')
            assert "alert" not in out and "msgbox" not in out, f"{payload} survived"

    def test_foreign_elements_are_dropped(self):
        from engineverse.security.sanitize import sanitize_svg

        out = sanitize_svg('<svg><foreignObject><iframe src="//evil"></iframe></foreignObject>'
                           '<text>keep</text></svg>')
        assert "<iframe" not in out and "<foreignobject" not in out.lower()
        assert "keep" in out

    def test_markup_that_is_not_svg_is_refused(self):
        from engineverse.security.sanitize import sanitize_svg

        assert sanitize_svg("<div onclick=alert(1)>hi</div>") == ""
        assert sanitize_svg("") == ""

    def test_the_seeded_diagrams_survive_intact(self):
        """A sanitiser that mangles the real diagrams is not a fix."""
        import re

        from engineverse import db
        from engineverse.security.sanitize import sanitize_svg

        rows = db.query("SELECT title, spec FROM diagrams")
        assert rows, "expected seeded diagrams to compare against"
        for row in rows:
            before = len(re.findall(r"<[a-zA-Z]", row["spec"]))
            after = len(re.findall(r"<[a-zA-Z]", sanitize_svg(row["spec"])))
            assert before == after, f"{row['title']} lost {before - after} elements"

    def test_the_read_path_returns_sanitised_markup(self):
        from engineverse import catalog, db

        topic = db.query_one(
            "SELECT topic_id FROM diagrams LIMIT 1"
        )
        if not topic:
            pytest.skip("no seeded diagrams")
        diagrams = catalog.diagrams_for_topic(topic["topic_id"])
        assert diagrams
        for diagram in diagrams:
            assert diagram["spec"].lstrip().startswith("<svg")
            assert "<script" not in diagram["spec"]


class TestPersonalPagesAreNotCacheable:
    """A signed-in page must not end up in a cache another user can read.

    The service worker keeps a copy of fetched pages for offline use. Its
    denylist covered /api/, /settings and /admin, but most pages render the
    viewer's own data - /today, /profile, /notifications, /mistakes - so on a
    shared machine the next person to open the app offline was shown the
    previous user's dashboard. The server now says which responses belong to
    somebody, and the worker honours it.
    """

    PERSONAL = ["/today", "/profile", "/notifications", "/mistakes",
                "/streaks", "/onboarding", "/revision", "/community"]

    @pytest.mark.parametrize("path", PERSONAL)
    def test_a_signed_in_page_is_marked_no_store(self, signed_in, path):
        response = signed_in.get(path)
        assert response.status_code == 200, f"{path} -> {response.status_code}"
        cache_control = response.headers.get("cache-control", "")
        assert "no-store" in cache_control, (
            f"{path} is personalised but sent Cache-Control: {cache_control!r}"
        )

    def test_an_anonymous_page_is_still_cacheable(self, client):
        response = client.get("/explore")
        assert response.status_code == 200
        assert "no-store" not in response.headers.get("cache-control", ""), (
            "a public page was needlessly marked non-cacheable"
        )

    def test_the_service_worker_honours_the_header(self):
        """The worker is the thing that would store the page, so it must check."""
        from pathlib import Path

        script = Path("backend/static/sw.js").read_text(encoding="utf-8")
        assert "no-store" in script, "the service worker ignores Cache-Control"
        assert "storable" in script
        # Every place that writes to the cache has to go through the check.
        writes = script.count("c.put(")
        guards = script.count("storable(")
        assert writes > 0 and guards >= writes, (
            f"{writes} cache writes but only {guards} storable() checks"
        )
