"""The exported account pages and the browser runtime are one contract.

``scripts/export_pages.py`` writes the GitHub Pages copies of ``/login``,
``/register``, ``/forgot-password`` and ``/settings`` as HTML strings, and
``backend/static/js/pages-live.js`` drives those pages by element id. Nothing
links the two files, so they drifted apart silently:

* the runtime looked for ``#ev-login-otp``, the page had ``#ev-login-otp-code``;
* the 6-digit code was typed into a ``<form>`` that had no submit handler, so
  pressing "Verify OTP" reloaded the page and the learner stayed signed out;
* the "already signed in" box was never filled because it looked for
  ``#ev-already-user``.

None of those are syntax errors, so ``node --check`` stayed green while the
whole flow could not be completed. These tests fail loudly when the two sides
disagree again. ``scripts/check_auth_flow.js`` covers the same ground by
actually running the exported pages under jsdom; this file is the fast, always-on
guard that needs no browser.
"""
from __future__ import annotations

import pathlib
import re

import pytest

from scripts import export_pages

ROOT = pathlib.Path(__file__).resolve().parents[2]
JS = ROOT / "backend" / "static" / "js" / "pages-live.js"

# Ids the runtime creates itself, or that only exist on the live server build.
# Anything else it looks up must be in the exported markup.
CREATED_BY_THE_RUNTIME = {
    "ev-community-post-form",
    "ev-live-community-composer",
    "ev-rev-back",
    "ev-rev-card",
    "ev-rev-counter",
    "ev-rev-flip",
    "ev-rev-front",
    "ev-rev-rate",
    "ev-rev-subject",
}


@pytest.fixture(scope="module")
def runtime_source() -> str:
    return JS.read_text(encoding="utf-8")


@pytest.fixture(scope="module")
def templates() -> dict[str, str]:
    """The server-rendered templates the exporter rebuilds for Pages."""
    return {
        path.name: path.read_text(encoding="utf-8")
        for path in sorted((ROOT / "backend" / "templates").rglob("*.html"))
    }


@pytest.fixture(scope="module")
def exported(tmp_path_factory) -> dict[str, str]:
    """Writes the exported account pages and returns ``path -> html``."""
    site = tmp_path_factory.mktemp("pages-export")
    # fill_shell() swaps whatever is inside `<main id="main" class="wrap">`, so
    # the stub has to use that exact opening tag.
    shell = (
        "<!doctype html><html><head><title>EngineVerse</title></head><body>"
        '<header class="topbar"><div class="topbar-right"></div></header>'
        '<main id="main" class="wrap"></main>'
        '<script type="application/json" id="ev-live">{}</script>'
        "</body></html>"
    )
    export_pages.write_account_pages(site, "/EngineVerse/", shell)
    pages = {}
    for path in sorted(site.rglob("*.html")):
        pages[str(path.relative_to(site))] = path.read_text(encoding="utf-8")
    assert len(pages) >= 8, f"the exporter wrote only {len(pages)} account pages"
    return pages


def _ids_referenced(source: str) -> set[str]:
    found = set(re.findall(r'getElementById\(\s*["`]([^"`$]+)["`]', source))
    found |= set(re.findall(r'querySelector(?:All)?\(\s*["`]#([A-Za-z0-9_-]+)["`]', source))
    return found


def _flexible_lookups(source: str) -> list[tuple[str, ...]]:
    """Every ``firstEl("a", "b")`` group of accepted ids for one control."""
    groups: list[tuple[str, ...]] = []
    for match in re.finditer(r"firstEl\(([^)]*)\)", source):
        ids = tuple(re.findall(r'"([A-Za-z0-9_-]+)"', match.group(1)))
        if len(ids) > 1:
            groups.append(ids)
    return groups


def _ids_in(html: str) -> set[str]:
    return set(re.findall(r'\bid="([^"]+)"', html))


class TestExportedMarkupAndRuntimeAgree:
    def test_every_id_the_runtime_looks_up_exists_in_the_exported_pages(self, runtime_source, exported, templates):
        # The runtime also drives pages the exporter copies from the templates
        # (the code editor on a problem page, the mobile menu button in the
        # shell), so both sources count as "the markup".
        markup = set()
        for html in list(exported.values()) + list(templates.values()):
            markup |= _ids_in(html)
        referenced = _ids_referenced(runtime_source)
        missing = sorted(
            ident
            for ident in referenced
            if ident not in markup and ident not in CREATED_BY_THE_RUNTIME
        )
        assert not missing, (
            "pages-live.js looks these ids up but no exported page defines them: "
            f"{missing}"
        )

    def test_every_flexible_lookup_has_at_least_one_of_its_ids_present(self, runtime_source, exported):
        markup = set()
        for html in exported.values():
            markup |= _ids_in(html)
        broken = [
            " / ".join(group)
            for group in _flexible_lookups(runtime_source)
            if not any(ident in markup for ident in group)
        ]
        assert not broken, f"firstEl() accepts only ids no page has: {broken}"

    def test_the_new_user_otp_step_is_reachable_on_login_and_register(self, exported):
        """A new account is verified with a 6-digit code before it can sign in."""
        for page, input_id, form_id, preview_id in (
            ("login/index.html", "ev-login-otp", "ev-login-otp-form", "ev-login-otp-preview"),
            ("register/index.html", "ev-reg-otp", "ev-reg-otp-form", "ev-reg-otp-preview"),
        ):
            html = exported[page]
            assert f'id="{input_id}"' in html, f"{page} has no OTP field ({input_id})"
            assert f'id="{form_id}"' in html, f"{page} has no OTP form ({form_id})"
            assert f'id="{preview_id}"' in html, f"{page} has no OTP preview ({preview_id})"
            form = re.search(rf'<form id="{form_id}".*?</form>', html, re.S)
            assert form and 'type="submit"' in form.group(0), (
                f"{form_id} has no submit button, so the code cannot be sent"
            )

    def test_password_recovery_offers_otp_to_email_or_phone(self, exported):
        html = exported["forgot-password/index.html"]
        assert 'id="ev-forgot-otp"' in html
        assert 'id="ev-forgot-resend-btn"' in html, "recovery has no way to request a fresh code"
        assert 'id="ev-forgot-channel"' in html
        assert 'id="ev-forgot-country-code"' in html, "no country code selector for an SMS code"

    def test_password_change_offers_otp_to_email_or_phone(self, exported):
        html = exported["settings/index.html"]
        assert 'id="ev-password-change-form"' in html
        assert 'id="ev-pwd-otp-code"' in html
        assert 'id="ev-pwd-country-code"' in html

    def test_the_exported_login_page_names_the_previous_session(self, exported):
        """A signed-in visitor who opens /login is told who is signed in."""
        html = exported["login/index.html"]
        assert 'id="ev-already-user"' in html
        assert 'id="ev-switch-account-btn"' in html

    def test_no_exported_account_page_posts_to_a_server(self, exported):
        """The Pages copy has no backend: every account form is handled in-page."""
        for page, html in exported.items():
            for action in re.findall(r'<form[^>]*action="([^"]*)"', html):
                assert not action.startswith("/"), f"{page} posts to {action} with no server to answer"
