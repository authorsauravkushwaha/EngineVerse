"""Crawls every reachable page and fails on a server error.

Individual route tests assert on one page each. This walks the whole site as a
signed-in user - every topic, subject, project, language and library page - and
fails if anything returns 5xx or writes an ``app.error`` audit row. It exists
because a template that renders for the fixture data and crashes on the twelfth
topic is indistinguishable from a working one until something walks all twelve.
"""
from __future__ import annotations

from engineverse import db


def _every_url() -> list[str]:
    urls = [
        "/", "/subjects", "/videos", "/books", "/resources", "/formulas", "/roadmaps",
        "/practice", "/programming", "/projects", "/community", "/streaks", "/profile",
        "/certificates", "/forgot-password", "/login", "/register", "/flashcards",
        "/interview", "/admin", "/search?q=bernoulli",
    ]
    for table in ("topics", "subjects", "projects", "programming_languages"):
        urls += [f"/{table.rstrip('s')}/{row['id']}" for row in db.query(f"SELECT id FROM {table}")]
    # Deep enough to reach the last page of every paginated shelf.
    urls += [f"/resources?page={page}" for page in range(1, 20)]
    urls += [f"/books?page={page}" for page in range(1, 15)]
    urls += [f"/videos?page={page}" for page in range(1, 15)]
    return urls


def test_every_page_renders(signed_in):
    broken = []
    for url in _every_url():
        response = signed_in.get(url)
        if response.status_code >= 500:
            broken.append((url, response.status_code))
    assert not broken, f"pages returning 5xx: {broken[:10]}"


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


def test_the_crawl_is_actually_walking_the_site(seeded):
    """A crawl of an empty site passes without testing anything."""
    assert len(db.query("SELECT id FROM topics")) >= 48
    assert len(db.query("SELECT id FROM subjects")) >= 73
    assert len(_every_url()) > 150
