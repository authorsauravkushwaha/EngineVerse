"""Crawls every reachable page and fails on a broken one.

Individual route tests assert on one page each. This walks the whole site as a
signed-in user - every topic, subject, project, language and library page - and
fails if anything 404s, returns 5xx, or writes an ``app.error`` audit row. It
exists because a template that renders for the fixture data and crashes on the
twelfth topic is indistinguishable from a working one until something walks all
twelve.

403 is allowed and deliberately so: the crawl runs as a student, and
``/admin`` returning 403 is the authorisation working, not a broken page.
"""
from __future__ import annotations

from engineverse import db


def _route_paths() -> list[str]:
    """Every path the application serves, read from its own router.

    Taken from the OpenAPI schema rather than written out here, because a
    hardcoded list rots in the direction that hurts. This file listed
    ``/subjects``, ``/certificates``, ``/flashcards`` and ``/interview`` for a
    long time and no route served any of them; they 404'd on every single run
    and nothing noticed, because the crawl only failed on 5xx. Deriving the list
    means a new route is crawled automatically and a renamed one cannot leave a
    stale entry behind.
    """
    from main import app

    # Only routes that accept GET. A crawl walks by requesting, and the
    # POST-only form targets (/logout, /settings/password, /admin/users/role)
    # correctly answer a GET with 405 - that is the CSRF-protected endpoint
    # working, not a page that is broken.
    return sorted(
        path for path, methods in app.openapi()["paths"].items()
        if "get" in {str(method).lower() for method in methods}
    )


def _static_page_paths() -> list[str]:
    """Page routes that take no parameter, so they can be requested as written."""
    return [p for p in _route_paths() if not p.startswith("/api") and "{" not in p]


#: How to fill each parametrised page route from the seeded data. A route with
#: no entry here is not crawled, and ``test_every_parametrised_route_is_covered``
#: fails rather than letting that happen quietly.
PARAM_SOURCES = {
    "/branches/{slug}": "SELECT slug FROM branches",
    "/certificates/{verify_id}": "SELECT verify_id FROM certificates",
    "/community/{thread_id}": "SELECT id AS thread_id FROM discussions",
    "/dpp/{date}": "SELECT date FROM dpp_sets",
    "/portfolio/{username}": "SELECT username FROM users",
    "/practice/problems/{slug}": "SELECT slug FROM coding_problems",
    "/programming/{language}": "SELECT slug AS language FROM programming_languages",
    "/projects/{slug}": "SELECT slug FROM projects",
    "/roadmaps/{slug}": "SELECT slug FROM roadmaps",
    "/subjects/{slug}": "SELECT slug FROM subjects",
    "/topics/{slug}": "SELECT slug FROM topics",
}


def _every_url() -> list[str]:
    urls = list(_static_page_paths())
    for pattern, sql in PARAM_SOURCES.items():
        name = pattern.rsplit("{", 1)[1].rstrip("}")
        for row in db.query(sql):
            urls.append(pattern.replace("{" + name + "}", str(row[name])))
    # Deep enough to reach the last page of every paginated shelf.
    urls += [f"/resources?page={page}" for page in range(1, 20)]
    urls += [f"/books?page={page}" for page in range(1, 15)]
    urls += [f"/videos?page={page}" for page in range(1, 15)]
    return urls


def test_every_page_renders(signed_in):
    broken = []
    for url in _every_url():
        response = signed_in.get(url)
        # 404 and 405 mean the URL does not exist or the method is wrong; 5xx
        # means it exists and failed. 403 is a working authorisation check.
        if response.status_code in (404, 405) or response.status_code >= 500:
            broken.append((url, response.status_code))
    assert not broken, f"broken pages: {broken[:10]}"


def _error_count() -> int:
    return db.scalar("SELECT count(*) FROM audit_logs WHERE action = 'app.error'")


def test_no_page_wrote_an_error_to_the_audit_log(signed_in):
    """DebugUndefined makes a broken template render blank rather than raise.

    Measured as a delta, not an absolute count: the database is session-scoped
    and another suite deliberately provokes the 500 handler, so asserting zero
    outright fails for a reason this crawl had nothing to do with.
    """
    before = _error_count()
    for url in _every_url():
        signed_in.get(url)
    after = _error_count()
    assert after == before, (
        f"the crawl produced {after - before} app.error row(s); "
        "a page raised and the error handler swallowed it"
    )


def test_every_parametrised_route_is_covered(seeded):
    """A route with no entry in PARAM_SOURCES would simply never be requested."""
    uncovered = [
        path for path in _route_paths()
        if not path.startswith("/api") and "{" in path and path not in PARAM_SOURCES
    ]
    assert uncovered == [], f"parametrised routes the crawl silently skips: {uncovered}"


def test_the_crawl_is_actually_walking_the_site(seeded):
    """A crawl of an empty site passes without testing anything."""
    assert len(db.query("SELECT id FROM topics")) >= 48
    assert len(db.query("SELECT id FROM subjects")) >= 73
    assert len(_every_url()) > 150
    # The list is derived, so prove the derivation is reaching the router and
    # not returning an empty table that the crawl then walks straight through.
    static = _static_page_paths()
    for expected in ("/", "/practice", "/revision", "/community", "/explore"):
        assert expected in static, f"{expected} is not a registered route"
    assert not [u for u in static if "{" in u], "a parametrised path cannot be requested as-is"
