"""Study paths that point at pages which already exist.

These are ways to use the library. They are not a degree, a placement track,
or a claim that every subject has a finished course.
"""
from __future__ import annotations

PRACTICE = [
    {
        "n": "1",
        "title": "If the subject is new",
        "body": "Open a topic and read Beginner before the formal definition. The same idea is written again for someone who already works with it.",
        "href": "/explore",
        "label": "Choose a subject",
    },
    {
        "n": "2",
        "title": "Do the set for this calendar day",
        "body": "The heading is today's date, including a visit weeks from now. Check the explanation even when you were right.",
        "href": "/dpp",
        "label": "Today's set",
    },
    {
        "n": "3",
        "title": "When you miss one",
        "body": "Read why the answer is what it is, then try a similar question from the bank. A miss is the lesson.",
        "href": "/practice/questions",
        "label": "Question bank",
    },
    {
        "n": "4",
        "title": "Then read the working and job versions",
        "body": "Standard is the working explanation. Advanced is for someone who already uses the idea. Industry is how it shows up in a job, not a promise of a job.",
        "href": "/explore",
        "label": "Back to the notes",
    },
]

CODE = [
    {
        "n": "1",
        "title": "Pick one language and stay with it",
        "body": "Each language page is in order: first program, then structure, then the habit a working engineer uses. Switching language in the first week throws away the path.",
        "href": "/programming/python",
        "label": "Start with Python",
    },
    {
        "n": "2",
        "title": "Copy every example and run it yourself",
        "body": "The reading copy cannot execute code. The self-hosted app can run the languages whose toolchain is installed. Either way, type the example. Reading it is not the same as running it.",
        "href": "/programming",
        "label": "All languages",
    },
    {
        "n": "3",
        "title": "Then the problems",
        "body": "Easy problems first. A professional can explain a failing case. Memorising keywords is not that skill.",
        "href": "/practice/problems",
        "label": "Problems",
    },
    {
        "n": "4",
        "title": "Then one project",
        "body": "Pick a brief in the field you care about. Follow it through testing and the interview questions on that page.",
        "href": "/projects",
        "label": "Projects",
    },
]

PROJECTS = [
    {
        "n": "1",
        "title": "Read the field first",
        "body": "A project brief assumes the notes. If the subject is new, read Beginner. If you already work in it, read Industry before you design anything.",
        "href": "/explore",
        "label": "Fields and subjects",
    },
    {
        "n": "2",
        "title": "Follow the brief in order",
        "body": "Problem, architecture, data, build steps, tests, the résumé line, then the questions someone will ask. Do not skip the tests to make the demo look finished.",
        "href": "/projects",
        "label": "Project briefs",
    },
    {
        "n": "3",
        "title": "Write the résumé line yourself",
        "body": "The brief suggests a line. Change it so it describes what you actually built. A line for work you did not do is not a portfolio.",
        "href": "/projects",
        "label": "Choose a brief",
    },
]


def field_starts(limit: int = 12) -> list[dict]:
    """Branches that already have notes, with the first topics to open."""
    from . import catalog, db

    found: list[dict] = []
    for branch in catalog.list_branches():
        topics = db.query(
            "SELECT t.slug, t.title FROM topics t "
            "JOIN subjects s ON s.id = t.subject_id "
            "WHERE s.branch_id = ? AND t.status = 'published' "
            "ORDER BY CASE t.difficulty WHEN 'easy' THEN 0 WHEN 'medium' THEN 1 ELSE 2 END, "
            "t.order_index LIMIT 3",
            branch["id"],
        )
        if not topics:
            continue
        found.append({
            "name": branch["name"],
            "slug": branch["slug"],
            "topics": topics,
        })
        if len(found) >= limit:
            break
    return found
