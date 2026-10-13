"""Sign-in with a password and nothing else.

Complements ``test_login_otp.py`` and ``test_mfa_and_limits.py``, which cover
the two opt-in second factors. These cover the default paths:

* a fresh instance signs a learner in with a password even though nothing is
  configured to deliver mail, because the delivered-code step is opt-in;
* the header states the signed-in identity - a visible profile control and a
  sign-out button, not only an avatar to be discovered;
* "keep me signed in" actually changes the session lifetime, and the session row
  and the cookie agree on it;
* signing out ends the session on the server, not only in the browser.
"""
from __future__ import annotations

import itertools
import re

import pytest

from engineverse import db
from engineverse.config import reload_settings
from engineverse.security.sessions import SESSION_COOKIE, session_lifetime_seconds

PASSWORD = "Sign-In-Flow-Password-9!"

# The database is seeded once per session, so two tests cannot claim the same
# username. A module-private counter keeps every account here distinct while
# leaving other modules' names alone.
_counter = itertools.count(1)


def _csrf(html: str) -> str:
    marker = 'name="csrf_token" value="'
    start = html.index(marker) + len(marker)
    return html[start : html.index('"', start)]


def _register(client, username: str | None = None) -> str:
    """Creates a learner through the real form and returns their username."""
    username = username or f"siflow{next(_counter)}"
    page = client.get("/register")
    response = client.post(
        "/register",
        data={
            "csrf_token": _csrf(page.text),
            "email": f"{username}@example.test",
            "username": username,
            "full_name": "Sign In Flow",
            "password": PASSWORD,
            "password_confirm": PASSWORD,
            "next": "/",
        },
        follow_redirects=False,
    )
    assert response.status_code in (302, 303), response.status_code
    return username


def _sign_out(client) -> None:
    page = client.get("/")
    client.post("/logout", data={"csrf_token": _csrf(page.text)}, follow_redirects=False)


def _max_age(response) -> int:
    match = re.search(r"Max-Age=(\d+)", response.headers.get("set-cookie", ""))
    assert match, "the session cookie carried no Max-Age"
    return int(match.group(1))


@pytest.fixture
def no_delivery(monkeypatch):
    """A default instance: no SMTP, no SMS, and no LOGIN_OTP override."""
    monkeypatch.delenv("ENGINEVERSE_LOGIN_OTP", raising=False)
    monkeypatch.delenv("ENGINEVERSE_SMTP_URL", raising=False)
    monkeypatch.delenv("ENGINEVERSE_SMS_URL", raising=False)
    reload_settings()
    yield
    import os

    os.environ["ENGINEVERSE_LOGIN_OTP"] = "disabled"
    reload_settings()


class TestPasswordSignIn:
    def test_password_alone_creates_a_session(self, client, seeded, no_delivery):
        """The regression this exists for: a sign-in that cannot complete.

        With no transport configured, a compulsory delivered code made every
        sign-in on a fresh instance a dead end. Signing in has to work here.
        """
        username = _register(client)
        _sign_out(client)
        page = client.get("/login")
        response = client.post(
            "/login",
            data={
                "csrf_token": _csrf(page.text),
                "identifier": username,
                "password": PASSWORD,
                "next": "/",
            },
            follow_redirects=False,
        )
        assert response.status_code in (302, 303), response.text[:400]
        assert SESSION_COOKIE in response.cookies or SESSION_COOKIE in str(response.headers.get("set-cookie", ""))
        # And the session is usable, not merely present.
        assert client.get("/settings").status_code == 200

    def test_the_landing_page_says_who_is_signed_in(self, client, seeded, no_delivery):
        _register(client)
        html = client.get("/").text
        assert 'class="whoami"' in html
        assert ">Sign out<" in html
        assert ">Sign in<" not in html, "a signed-in page still advertises the sign-in button"
        assert 'class="avatar"' in html, "the account menu should still be there"

    def test_signing_out_returns_the_anonymous_header(self, client, seeded, no_delivery):
        _register(client)
        _sign_out(client)
        html = client.get("/").text
        assert ">Sign in<" in html
        assert ">Sign out<" not in html
        assert 'class="whoami"' not in html

    def test_signing_out_revokes_the_session_server_side(self, client, seeded, no_delivery):
        _register(client)
        cookie = client.cookies.get(SESSION_COOKIE)
        session_id = cookie.split(".")[0]
        _sign_out(client)
        row = db.query_one("SELECT revoked_at FROM sessions WHERE id = ?", session_id)
        assert row and row["revoked_at"], "the session row is still live after signing out"

    def test_a_stale_cookie_cannot_be_replayed(self, client, seeded, no_delivery):
        """Clearing the cookie client-side is not what ends a session.

        The browser copy is replayed after signing out and must be treated
        exactly like no cookie at all: ``/settings`` answers the anonymous
        request (a redirect to the sign-in form, the same as a fresh client)
        and the header is anonymous again.
        """
        _register(client)
        cookie = client.cookies.get(SESSION_COOKIE)
        _sign_out(client)
        client.cookies.set(SESSION_COOKIE, cookie)
        response = client.get("/settings", follow_redirects=False)
        assert response.status_code == 303, "a revoked session still opened a private page"
        assert response.headers["location"] == "/login?next=/settings"
        assert client.get("/").text.count(">Sign in<") == 1

    def test_the_login_page_does_not_advertise_codes_it_cannot_send(self, client, seeded, no_delivery):
        html = client.get("/login").text
        assert "We sent a 6-digit code" not in html
        assert "Authenticator code" not in html


class TestRememberMe:
    def test_ticked_gets_the_long_session(self, client, seeded, no_delivery):
        username = _register(client)
        _sign_out(client)
        page = client.get("/login")
        response = client.post(
            "/login",
            data={
                "csrf_token": _csrf(page.text),
                "identifier": username,
                "password": PASSWORD,
                "next": "/",
                "remember": "1",
            },
            follow_redirects=False,
        )
        assert _max_age(response) == session_lifetime_seconds(True)

    def test_unticked_gets_the_short_session(self, client, seeded, no_delivery):
        """An unticked box sends no field at all, which used to be ignored."""
        username = _register(client)
        _sign_out(client)
        page = client.get("/login")
        response = client.post(
            "/login",
            data={
                "csrf_token": _csrf(page.text),
                "identifier": username,
                "password": PASSWORD,
                "next": "/",
            },
            follow_redirects=False,
        )
        age = _max_age(response)
        assert age == session_lifetime_seconds(False)
        assert age < session_lifetime_seconds(True)

    def test_the_session_row_expires_with_the_cookie(self, client, seeded, no_delivery):
        """A cookie outliving its row is a session that dies unexpectedly."""
        username = _register(client)
        _sign_out(client)
        page = client.get("/login")
        response = client.post(
            "/login",
            data={
                "csrf_token": _csrf(page.text),
                "identifier": username,
                "password": PASSWORD,
                "next": "/",
            },
            follow_redirects=False,
        )
        max_age = _max_age(response)
        cookie = client.cookies.get(SESSION_COOKIE)
        row = db.query_one(
            "SELECT created_at, expires_at FROM sessions WHERE id = ?", cookie.split(".")[0]
        )
        assert row
        assert abs((row["expires_at"] - row["created_at"]) // 1000 - max_age) <= 2
