"""The security guarantees the platform's threat model rests on."""
from __future__ import annotations

import pytest

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
