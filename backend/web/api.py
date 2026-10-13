"""JSON API.

Consumed by ``static/js/app.js`` for progressive enhancement: running code,
submitting answers, reviewing flashcards, bookmarking, voting and searching.
Every mutating endpoint requires a signed-in session plus the CSRF header.
"""
from __future__ import annotations

import re
from typing import Any

from fastapi import APIRouter, Body, Form, Request
from fastapi.responses import JSONResponse, RedirectResponse

from engineverse import (
    auth,
    catalog,
    certificates as certificates_mod,
    coding,
    community,
    db,
    judge,
    library,
    practice,
    progress,
    projects,
    recommend,
    srs,
    tutor,
)
from engineverse.security import rbac, ratelimit
from engineverse.security.audit import record
from engineverse.security.clientip import client_ip
from engineverse.security.sanitize import is_safe_url

from .deps import current_user, require_user

router = APIRouter()


def ok(**payload: Any) -> JSONResponse:
    payload["ok"] = True
    return JSONResponse(payload)


def _reject(request: Request, back_to: str, message: str):
    """Sends a navigating browser back with a flash; returns JSON to a script."""
    if wants_html(request):
        from .deps import flash

        response = RedirectResponse(back_to, status_code=303)
        flash(response, message)  # sets the cookie in place and returns None
        return response
    return fail(message)


def wants_html(request: Request) -> bool:
    """True when the caller is a browser navigating, not a script fetching."""
    return "text/html" in (request.headers.get("accept") or "")


def _account_throttle(
    request: Request, user_id: str, action: str, limit: int, window: int,
    back_to: str, message: str,
):
    """Apply a database-shared per-account budget to an authenticated write."""
    key = f"account:{action}:{user_id}"
    local = ratelimit.check(key, limit, window)
    shared = ratelimit.shared_check(key, limit, window, local_fallback=local)
    result = local if not local.allowed else shared
    if result.allowed:
        return None
    retry_after = max(1, result.retry_after)
    if wants_html(request):
        from .deps import flash

        response = RedirectResponse(back_to, status_code=303)
        flash(response, message)
    else:
        response = fail(message, 429, retryAfter=retry_after)
    response.headers["Retry-After"] = str(retry_after)
    response.headers["X-RateLimit-Limit"] = str(limit)
    response.headers["X-RateLimit-Remaining"] = "0"
    return response


def fail(message: str, status: int = 400, **extra: Any) -> JSONResponse:
    body: dict[str, Any] = {"ok": False, "error": message}
    body.update(extra)
    return JSONResponse(body, status_code=status)


async def payload(request: Request) -> dict:
    """Reads a request body as JSON, falling back to form fields.

    The community forms are plain HTML so they work without JavaScript, but they
    post to JSON endpoints. Accepting both keeps the no-JS path real instead of
    returning a 422 to anyone with scripting disabled.
    """
    content_type = (request.headers.get("content-type") or "").lower()
    if "application/json" in content_type:
        try:
            data = await request.json()
            return data if isinstance(data, dict) else {}
        except Exception:
            return {}
    try:
        form = await request.form()
    except Exception:
        return {}
    return {key: value for key, value in form.items()}


def text_field(data: dict, key: str, *, maximum: int, default: str = "") -> str:
    """Read a bounded scalar text field without trusting its JSON type."""
    value = data.get(key, default)
    if value is None:
        return default
    if not isinstance(value, str):
        return ""
    # Keep one extra character so callers can reject, rather than silently
    # accepting a value that was truncated at the validation boundary.
    return value[:maximum + 1].strip()


def split_tags(value: Any) -> list[str]:
    """Accept a bounded list, or the comma-separated string an HTML form sends."""
    if isinstance(value, list):
        items = [str(v).strip() for v in value[:12] if str(v).strip()]
    elif isinstance(value, str):
        items = [part.strip() for part in value.split(",") if part.strip()]
    else:
        return []
    return [item[:40] for item in items[:12]]


# ---------------------------------------------------------------------------
# Session and profile
# ---------------------------------------------------------------------------

@router.get("/me")
async def me(request: Request):
    viewer = current_user(request)
    if not viewer:
        return fail("Not signed in.", 401)
    return ok(
        user={"id": viewer.id, "username": viewer.username, "fullName": viewer.full_name,
              "role": viewer.role, "headline": viewer.headline},
        stats=progress.user_stats(viewer.id),
        streak=progress.heatmap(viewer.id, 60),
    )


@router.post("/me/progress/topic")
async def mark_topic(request: Request, topicId: str = Body(..., embed=True), status: str = Body("completed", embed=True)):
    viewer = require_user(request)
    wanted = status.strip()
    # Both progress functions insert into user_progress, whose topic_id is a
    # foreign key, so a topic that does not exist raised sqlite3.IntegrityError
    # out of the handler and answered 500 - a server error for a bad id in the
    # request. Check first and answer 404.
    if not topicId or len(topicId) > 128:
        return fail("Invalid topic identifier.", 400)
    topic = db.query_one("SELECT id FROM topics WHERE slug = ? OR id = ?", topicId, topicId)
    if not topic:
        return fail("No such topic.", 404)
    if wanted not in ("completed", "mastered", "started", "in_progress", "viewed"):
        return fail("That is not a progress state this accepts.", 400)
    if wanted in ("completed", "mastered"):
        progress.complete_topic(viewer.id, topic["id"])
    else:
        progress.mark_topic_viewed(viewer.id, topic["id"])
    return ok(stats=progress.user_stats(viewer.id))


# ---------------------------------------------------------------------------
# Search
# ---------------------------------------------------------------------------

@router.get("/search")
async def api_search(request: Request, q: str = "", type: str | None = None, branch: str | None = None,
                     limit: int = 20):
    if len(q) > 256 or (type is not None and len(type) > 32) or (branch is not None and len(branch) > 128):
        return fail("Search filters are too long.", 413)
    if not q.strip():
        return ok(results=[], total=0, suggestion=None)
    result = search_grouped(q, type=type, branch=branch, limit=max(1, min(limit, 60)))
    return ok(**result)


def search_grouped(q: str, **options: Any) -> dict:
    from engineverse import search

    payload = search.grouped(q, **options)
    search.log_search(q, payload["total"])
    return payload


@router.get("/search/suggest")
async def api_suggest(request: Request, q: str = ""):
    from engineverse import search

    if len(q) > 200:
        return fail("Keep search suggestions under 200 characters.", 413)
    if len(q.strip()) < 2:
        return ok(suggestions=[])
    rows = db.query(
        "SELECT DISTINCT entity_type, title FROM search_index WHERE title LIKE ? LIMIT 8", f"%{q.strip()}%"
    )
    return ok(suggestions=[{"type": r["entity_type"], "title": r["title"]} for r in rows],
              didYouMean=search.did_you_mean(q))


# ---------------------------------------------------------------------------
# Practice
# ---------------------------------------------------------------------------

@router.get("/practice/questions/{question_id}")
async def api_question(request: Request, question_id: str):
    if not question_id or len(question_id) > practice.MAX_ID_LENGTH:
        return fail("Invalid question identifier.", 400)
    question = practice.question_by_id(question_id)
    if not question:
        return fail("Unknown question.", 404)
    return ok(question=practice.public_question(question))


@router.post("/practice/answer")
async def api_answer(request: Request, questionId: str = Body(...), optionIndex: int | None = Body(None),
                     answerText: str | None = Body(None), setId: str | None = Body(None),
                     timeMs: int | None = Body(None)):
    viewer = require_user(request)
    if not questionId or len(questionId) > practice.MAX_ID_LENGTH:
        return fail("Invalid question identifier.", 400)
    if answerText is not None and len(answerText) > 2000:
        return fail("Keep a written answer under 2,000 characters.", 413)
    if timeMs is not None and not 0 <= timeMs <= 86_400_000:
        return fail("Invalid answer duration.", 400)

    question = practice.question_by_id(questionId)
    if not question:
        return fail("Unknown question.", 404)
    options = practice.options_for(questionId)
    if options:
        if optionIndex is None or not 0 <= optionIndex < len(options):
            return fail("Choose one of the listed options.", 400)
        if answerText is not None:
            return fail("Send either an option or written answer, not both.", 400)
    elif optionIndex is not None or not (answerText or "").strip():
        return fail("Enter a written answer.", 400)

    if setId is not None:
        setId = setId.strip()
        if not setId or len(setId) > practice.MAX_ID_LENGTH:
            return fail("Invalid practice-set identifier.", 400)
        membership = db.query_one(
            "SELECT 1 FROM dpp_questions dq JOIN dpp_sets d ON d.id = dq.set_id "
            "WHERE dq.set_id = ? AND dq.question_id = ? AND d.published = 1",
            setId, questionId,
        )
        if not membership:
            return fail("That question is not in this published practice set.", 404)

    result = practice.record_answer(
        viewer.id, questionId, option_index=optionIndex, answer_text=answerText,
        set_id=setId, time_ms=timeMs,
    )
    progress.evaluate_badges(viewer.id)
    return ok(**result, stats=progress.user_stats(viewer.id))


@router.get("/practice/dpp")
async def api_dpp(request: Request, date: str | None = None):
    payload = practice.dpp_with_context(date)
    if not payload:
        return fail("No practice set for that date.", 404)
    return ok(dpp=payload)


@router.get("/mistakes")
async def api_mistakes(request: Request, limit: int = 30):
    viewer = require_user(request)
    return ok(mistakes=practice.mistake_notebook(viewer.id, limit=max(1, min(limit, 100))))


# ---------------------------------------------------------------------------
# Coding
# ---------------------------------------------------------------------------

@router.get("/coding/languages")
async def api_languages(request: Request):
    return ok(languages=coding.list_languages(), runnable=judge.runnable_languages())


@router.get("/coding/problems")
async def api_problems(request: Request, difficulty: str | None = None, topic: str | None = None,
                       q: str | None = None, limit: int = 50):
    if (difficulty is not None and len(difficulty) > 32) or (topic is not None and len(topic) > 128) \
            or (q is not None and len(q) > 200):
        return fail("Problem filters are too long.", 413)
    return ok(problems=coding.list_problems(
        difficulty=difficulty, topic=topic, q=q, limit=max(1, min(limit, 200))
    )[0])


@router.get("/coding/problems/{slug}")
async def api_problem(request: Request, slug: str):
    if not slug or len(slug) > 128:
        return fail("Invalid problem identifier.", 400)
    problem = coding.get_problem(slug)
    if not problem:
        return fail("Unknown problem.", 404)
    return ok(
        problem=problem,
        stubs=coding.stubs_for(problem["id"]),
        samples=coding.testcases_for(problem["id"], samples_only=True),
    )


@router.post("/coding/run")
async def api_run(request: Request, language: str = Body(...), code: str = Body(...),
                  input: str = Body(""), problemSlug: str | None = Body(None)):
    viewer = current_user(request)
    if len(language) > 32 or (problemSlug is not None and len(problemSlug) > 128):
        return fail("Invalid coding-run identifier.", 400)
    if len(code) > 64_000 or len(input) > 64_000:
        return fail("Program and input must each stay under 64,000 characters.", 413)
    if problemSlug:
        problem = coding.get_problem(problemSlug)
        if not problem:
            return fail("Unknown problem.", 404)
        result = coding.run(problem["id"], language, code, input)
    else:
        # run_custom returns a RunResult dataclass, which is not JSON
        # serialisable on its own.
        result = judge.as_dict(judge.run_custom(language, code, input))
    if viewer:
        db.execute(
            "INSERT INTO activity (user_id,day,coding_submissions) VALUES (?,?,1) "
            # Qualified: PostgreSQL calls an unqualified column ambiguous here.
            "ON CONFLICT(user_id,day) DO UPDATE SET coding_submissions = activity.coding_submissions + 1",
            viewer.id, auth.today(),
        )
    return ok(result=result)


@router.post("/coding/submit")
async def api_submit(request: Request, problemSlug: str = Body(...), language: str = Body(...),
                     code: str = Body(...)):
    viewer = require_user(request)
    if len(problemSlug) > 128 or len(language) > 32:
        return fail("Invalid coding-submission identifier.", 400)
    problem = coding.get_problem(problemSlug)
    if not problem:
        return fail("Unknown problem.", 404)
    if len(code) > 64_000:
        return fail("That program is too long to submit.", 413)
    result = coding.submit(viewer.id, problem["id"], language, code)
    progress.evaluate_badges(viewer.id)
    return ok(result=result, stats=progress.user_stats(viewer.id))


@router.get("/coding/submissions")
async def api_submissions(request: Request, problemSlug: str | None = None, limit: int = 20):
    viewer = require_user(request)
    if problemSlug is not None and len(problemSlug) > 128:
        return fail("Invalid problem identifier.", 400)
    problem_id = None
    if problemSlug:
        problem = coding.get_problem(problemSlug)
        problem_id = problem["id"] if problem else None
    return ok(submissions=coding.submissions_for(viewer.id, problem_id, max(1, min(limit, 50))))


# ---------------------------------------------------------------------------
# Flashcards / spaced repetition
# ---------------------------------------------------------------------------

@router.get("/revision/due")
async def api_due(request: Request, limit: int = 20):
    viewer = require_user(request)
    return ok(cards=library.due_flashcards(viewer.id, max(1, min(limit, 50))),
              stats=library.flashcard_stats(viewer.id))


@router.post("/revision/review")
async def api_review(request: Request, cardId: str = Body(...), rating: str = Body("good")):
    viewer = require_user(request)
    # srs.review raises ValueError on an unknown rating and there is no handler
    # registered for ValueError, so it surfaced as a 500. A card that does not
    # exist is worse: the insert into user_flashcards has a foreign key, so the
    # database raised IntegrityError out of the handler. Validate both here.
    if not cardId or len(cardId) > 128 or len(rating) > 32:
        return fail("Invalid flashcard review.", 400)
    wanted = rating.strip()
    if wanted not in srs.RATINGS:
        return fail(f"Rating must be one of {', '.join(srs.RATINGS)}.", 400)
    if not db.query_one("SELECT 1 FROM flashcards WHERE id = ?", cardId):
        return fail("No such flashcard.", 404)
    state = srs.review(viewer.id, cardId, wanted)
    progress.award_xp(viewer.id, 2, "flashcard", "flashcard", cardId)
    progress.bump_activity(viewer.id, "revisions")
    return ok(state=state, stats=library.flashcard_stats(viewer.id))


# ---------------------------------------------------------------------------
# AI tutor
# ---------------------------------------------------------------------------


@router.post("/tutor/ask")
async def api_tutor_ask(request: Request):
    """Answers from platform content only, with the sources it used.

    Available signed in or out so a visitor can judge the platform before
    registering; the per-IP limit in RateLimitMiddleware is what stops it being
    used as a free query hose.
    """
    viewer = current_user(request)
    data = await payload(request)
    question = text_field(data, "question", maximum=400)
    if not question:
        return fail("Ask a question first.", status=422)
    if len(question) > 400:
        return fail("Keep the question under 400 characters.", status=422)

    result = tutor.answer(question, user_id=viewer.id if viewer else None)
    record("tutor.asked", actor_id=viewer.id if viewer else None,
           ip=client_ip(request),
           meta={"question_chars": len(question), "grounded": result["grounded"],
                 "sources": len(result["sources"])})
    return ok(question=question, answer=result["answer"], sources=result["sources"],
              grounded=result["grounded"], disclosure=result["disclosure"],
              message=result["message"])


# ---------------------------------------------------------------------------
# Bookmarks, notes, notifications
# ---------------------------------------------------------------------------

# What can be bookmarked, and the table each one lives in. The editor only ever
# offers topic and project; anything else used to be stored and then rendered on
# the profile as "banana · whatever", unreachable and meaningless.
BOOKMARKABLE = {"topic": "topics", "project": "projects"}


@router.post("/bookmarks")
async def api_bookmark(request: Request, entityType: str = Body(...), entityId: str = Body(...),
                       note: str | None = Body(None)):
    viewer = require_user(request)
    if len(entityType) > 32 or len(entityId) > 128 or (note is not None and len(note) > 500):
        return fail("Bookmark details are too long.", 413)
    entity_type = entityType.strip()
    entity_id = entityId.strip()
    table = BOOKMARKABLE.get(entity_type)
    if not table:
        return fail(f"That is not something you can bookmark. Try {', '.join(sorted(BOOKMARKABLE))}.", 400)
    if not entity_id:
        return fail("No such item to bookmark.", 404)
    if not db.query_one(f"SELECT 1 FROM {table} WHERE id = ? OR slug = ?", entity_id, entity_id):
        return fail("No such item to bookmark.", 404)
    added = progress.toggle_bookmark(viewer.id, entity_type, entity_id, note)
    return ok(bookmarked=added)


@router.get("/bookmarks")
async def api_bookmarks(request: Request, entityType: str | None = None):
    viewer = require_user(request)
    if entityType is not None and (len(entityType) > 32 or entityType not in BOOKMARKABLE):
        return fail("Invalid bookmark filter.", 400)
    return ok(bookmarks=progress.bookmarks(viewer.id, entityType))


@router.post("/notes/personal")
async def api_personal_note(request: Request):
    viewer = require_user(request)
    data = await payload(request)
    entity_type = text_field(data, "entityType", maximum=32)
    entity_id = text_field(data, "entityId", maximum=128)
    content = text_field(data, "content", maximum=20_000)
    entity_tables = {
        "topic": "topics", "problem": "coding_problems",
        "project": "projects", "flashcard": "flashcards",
    }
    table = entity_tables.get(entity_type)
    if not table:
        return _reject(request, "/", "That is not something you can attach a note to.")
    if not entity_id or len(entity_id) > 128:
        return fail("Invalid note target.", 400)
    if table == "flashcards":
        entity = db.query_one("SELECT id FROM flashcards WHERE id = ?", entity_id)
    else:
        entity = db.query_one(f"SELECT id FROM {table} WHERE id = ? OR slug = ?", entity_id, entity_id)
    if not entity:
        return fail("That item does not exist.", 404)
    entity_id = entity["id"]
    if len(content) < 2:
        return _reject(request, _entity_url(entity_type, entity_id), "Write something first.")
    if len(content) > 20_000:
        return _reject(request, _entity_url(entity_type, entity_id), "That note is too long.")
    note_id = progress.save_personal_note(viewer.id, entity_type, entity_id, content)
    if wants_html(request):
        return RedirectResponse(_entity_url(entity_type, entity_id), status_code=303)
    return ok(id=note_id, message="Note saved.")


def _entity_url(entity_type: str, entity_id: str) -> str:
    """Best-effort path back to the thing a note was attached to."""
    if entity_type == "topic":
        row = db.query_one("SELECT slug FROM topics WHERE id = ?", entity_id)
        if row:
            return f"/topics/{row['slug']}"
    if entity_type == "project":
        row = db.query_one("SELECT slug FROM projects WHERE id = ?", entity_id)
        if row:
            return f"/projects/{row['slug']}"
    return "/library"


@router.get("/notifications")
async def api_notifications(request: Request, limit: int = 30):
    viewer = require_user(request)
    return ok(notifications=progress.notifications(viewer.id, max(1, min(limit, 60))))


@router.post("/notifications/read")
async def api_notifications_read(request: Request):
    """Marks one notification read, or all of them when no id is given.

    Reads the body the way every sibling handler does. This one declared
    ``notificationId: str | None = Body(None)``, which without ``embed=True``
    means the *entire* body must be a bare JSON string. So the object
    ``{"notificationId": "..."}`` that ``app.js`` produces was rejected with a
    422, and so was the natural no-argument body ``{}``.

    No learner saw a symptom, because nothing in the UI called this endpoint and
    ``/notifications`` marks everything read on load - which is exactly how a
    broken endpoint stays broken.

    Going through ``payload`` also accepts form fields, so a no-JS form works.
    """
    viewer = require_user(request)
    data = await payload(request)
    notification_id = text_field(data, "notificationId", maximum=128) or None
    progress.mark_notifications_read(viewer.id, notification_id)
    return ok(unread=len(progress.notifications(viewer.id, unread_only=True)))


# ---------------------------------------------------------------------------
# Community
# ---------------------------------------------------------------------------

@router.post("/community/threads")
async def api_create_thread(request: Request):
    viewer = require_user(request)
    limited = _account_throttle(
        request, viewer.id, "community-thread", 10, 3600, "/community",
        "Too many new posts. Try again later.",
    )
    if limited:
        return limited
    data = await payload(request)
    title = text_field(data, "title", maximum=160)
    body = text_field(data, "body", maximum=20_000)
    kind = text_field(data, "kind", maximum=32, default="question") or "question"
    tags = split_tags(data.get("tags"))
    subjectId = text_field(data, "subjectId", maximum=128) or None
    topicId = text_field(data, "topicId", maximum=128) or None
    if len(title) < 5:
        return _reject(request, "/community", "Give your post a title of at least 5 characters.")
    if len(title) > 160:
        return _reject(request, "/community", "Keep the title under 160 characters.")
    if len(body) < 10:
        return _reject(request, "/community", "Add a little more detail so people can help.")
    if len(body) > 20_000:
        return _reject(request, "/community", "Keep the post under 20,000 characters.")
    if kind not in {"question", "discussion", "resource", "showcase"}:
        return _reject(request, "/community", "Choose a supported post type.")
    # create_thread attaches a thread to one entity, so a topic wins over a
    # subject when both are supplied. Check the reference before the foreign-key
    # insert so bad caller input stays a 4xx rather than an application error.
    entity_type, entity_id = (None, None)
    if topicId:
        referenced = db.query_one("SELECT id FROM topics WHERE id = ? OR slug = ?", topicId, topicId)
        if not referenced:
            return fail("That topic does not exist.", 404)
        entity_type, entity_id = "topic", referenced["id"]
    elif subjectId:
        referenced = db.query_one("SELECT id FROM subjects WHERE id = ? OR slug = ?", subjectId, subjectId)
        if not referenced:
            return fail("That subject does not exist.", 404)
        entity_type, entity_id = "subject", referenced["id"]
    thread_id = community.create_thread(
        viewer.id, title=title, body=body, kind=kind, tags=tags,
        entity_type=entity_type, entity_id=entity_id,
    )
    url = f"/community/{thread_id}"
    if wants_html(request):
        return RedirectResponse(url, status_code=303)
    return ok(id=thread_id, url=url)


@router.post("/community/comments")
async def api_comment(request: Request):
    viewer = require_user(request)
    limited = _account_throttle(
        request, viewer.id, "community-comment", 30, 3600, "/community",
        "Too many replies. Try again later.",
    )
    if limited:
        return limited
    data = await payload(request)
    threadId = text_field(data, "threadId", maximum=128)
    body = text_field(data, "body", maximum=10_000)
    parentId = text_field(data, "parentId", maximum=128) or None
    back_to = f"/community/{threadId}" if re.fullmatch(r"[0-9A-HJKMNP-TV-Z]{26}", threadId) else "/community"
    if not body:
        return _reject(request, back_to, "Write something before posting.")
    if len(body) > 10_000:
        return _reject(request, back_to, "Keep replies under 10,000 characters.")
    thread = community.get_thread(threadId)
    if not thread:
        return fail("That discussion does not exist.", 404)
    if parentId and not db.query_one("SELECT 1 FROM comments WHERE id = ? AND discussion_id = ?", parentId, threadId):
        return fail("That reply does not exist in this discussion.", 404)
    comment_id = community.add_comment(viewer.id, threadId, body, parentId)
    url = f"/community/{threadId}#c-{comment_id}"
    if wants_html(request):
        return RedirectResponse(url, status_code=303)
    return ok(id=comment_id, url=url, message="Reply posted.")


@router.post("/community/vote")
async def api_vote(request: Request, entityType: str = Body(...), entityId: str = Body(...),
                   value: int = Body(1)):
    viewer = require_user(request)
    limited = _account_throttle(
        request, viewer.id, "community-vote", 300, 3600, "/community",
        "Too many votes. Try again later.",
    )
    if limited:
        return limited
    # community.vote() only moves a score for "discussion" and "comment"; any
    # other entity_type wrote a votes row and returned 200 with score 0, so a
    # client sending the wrong string got a success response for a vote that
    # silently did nothing. Refuse it instead, the way /community/report does.
    if len(entityType) > 32 or len(entityId) > 128 or value not in (-1, 0, 1):
        return fail("Invalid vote details.", 400)
    entity_type = entityType.strip()
    if entity_type not in ("discussion", "comment"):
        return fail("That is not something you can vote on.", 400)
    if not entityId.strip():
        return fail("That is not something you can vote on.", 400)
    table = "discussions" if entity_type == "discussion" else "comments"
    if not db.query_one(f"SELECT 1 FROM {table} WHERE id = ?", entityId):
        return fail("That item no longer exists.", 404)
    score = community.vote(viewer.id, entity_type, entityId, value)
    return ok(score=score)


@router.post("/community/report")
async def api_report(request: Request):
    viewer = require_user(request)
    limited = _account_throttle(
        request, viewer.id, "community-report", 10, 3600, "/community",
        "Too many reports. Try again later.",
    )
    if limited:
        return limited
    data = await payload(request)
    entity_type = text_field(data, "entityType", maximum=32)
    entity_id = text_field(data, "entityId", maximum=128)
    reason = text_field(data, "reason", maximum=120)
    detail = text_field(data, "detail", maximum=2_000) or None
    # The URL calls it a thread, the discussions table calls it a discussion, and
    # community.resolve_report() hides the content only when the stored type is
    # "discussion". Accepting "thread" here and storing it verbatim meant the hide
    # path could never match, so a moderator could close a report but not remove
    # what was reported. Normalise to the name the rest of the code uses.
    if entity_type == "thread":
        entity_type = "discussion"
    if entity_type not in ("discussion", "comment") or not entity_id:
        return _reject(request, "/community", "That is not something you can report.")
    table = "discussions" if entity_type == "discussion" else "comments"
    if not db.query_one(f"SELECT 1 FROM {table} WHERE id = ?", entity_id):
        return fail("That item no longer exists.", 404)
    if len(reason) < 3:
        return _reject(request, "/community", "Give a reason so a moderator can act on it.")
    if len(reason) > 120 or (detail and len(detail) > 2_000):
        return _reject(request, "/community", "Keep the report reason under 120 and details under 2,000 characters.")
    if not db.query_one(
        "SELECT 1 FROM discussions WHERE id = ?" if entity_type == "discussion"
        else "SELECT 1 FROM comments WHERE id = ?", entity_id,
    ):
        return _reject(request, "/community", "That is not something you can report.")
    report_id = community.report(viewer.id, entity_type, entity_id, reason, detail)
    if wants_html(request):
        response = RedirectResponse("/community", status_code=303)
        from .deps import flash

        flash(response, "Reported. A moderator will review it.")
        return response
    return ok(id=report_id)


# ---------------------------------------------------------------------------
# Projects
# ---------------------------------------------------------------------------

@router.post("/projects/track")
async def api_project_track(request: Request):
    viewer = require_user(request)
    data = await payload(request)
    slug = text_field(data, "projectSlug", maximum=128)
    project = projects.get_project(slug)
    if not project:
        return fail("Unknown project.", 404)
    recorded = projects.record_build(viewer.id, project["id"])
    if wants_html(request):
        from .deps import flash

        response = RedirectResponse(f"/projects/{slug}", status_code=303)
        flash(response, "Build logged — +5 XP." if recorded else "This project is already in your build log.")
        return response
    return ok(
        message="Build logged — +5 XP." if recorded else "This project is already in your build log.",
        xpAwarded=5 if recorded else 0,
        alreadyLogged=not recorded,
    )


# ---------------------------------------------------------------------------
# Progress, leaderboard, certificates
# ---------------------------------------------------------------------------

@router.get("/progress")
async def api_progress(request: Request):
    viewer = require_user(request)
    return ok(
        stats=progress.user_stats(viewer.id),
        heatmap=progress.heatmap(viewer.id, 182),
        weekly=progress.weekly_stats(viewer.id),
        weak=progress.weak_topics(viewer.id, 8),
        badges=progress.all_badges(viewer.id),
        continueLearning=progress.continue_learning(viewer.id, 6),
    )


@router.get("/leaderboard")
async def api_leaderboard(request: Request, branch: str | None = None, period: str = "all"):
    if (branch is not None and len(branch) > 128) or period not in ("all", "weekly", "monthly"):
        return fail("Invalid leaderboard filter.", 400)
    return ok(rows=progress.leaderboard(branch=branch, period=period, limit=50))


@router.get("/certificates")
async def api_certificates(request: Request):
    viewer = require_user(request)
    return ok(certificates=progress.certificates(viewer.id))


@router.post("/certificates/refresh")
async def api_refresh_certificates(request: Request):
    """Re-evaluate every subject the learner has progress in.

    Certificates are earned automatically when a topic is completed, but streak
    length and practice accuracy change without any topic being finished, so a
    learner can outgrow their tier without triggering that path. This lets the
    dashboard settle the account rather than leaving a stale tier on screen.
    """
    viewer = require_user(request)
    issued = certificates_mod.refresh_for_user(viewer.id)
    return ok(
        certificates=[{"id": c["id"], "tier": c["tier"], "title": c["title"],
                       "verifyId": c["verify_id"]} for c in issued],
        message=f"{len(issued)} certificate(s) up to date.",
    )


@router.post("/certificates/issue")
async def api_issue_certificate(request: Request):
    viewer = require_user(request)
    data = await payload(request)
    kind = text_field(data, "kind", maximum=32, default="topic") or "topic"
    entity_type = text_field(data, "entityType", maximum=32)
    entity_id = text_field(data, "entityId", maximum=128)
    back_to = _entity_url("topic", entity_id) if entity_type == "topic" else "/"
    if kind != "topic" or entity_type != "topic" or not entity_id:
        return _reject(request, back_to, "That certificate type is not available.")
    topic = db.query_one("SELECT id, title, slug FROM topics WHERE id = ? OR slug = ?", entity_id, entity_id)
    if not topic:
        return fail("Unknown topic.", 404)
    back_to = f"/topics/{topic['slug']}"
    entity_id = topic["id"]
    if not db.query_one(
        "SELECT 1 FROM user_progress WHERE user_id = ? AND topic_id = ? AND status IN ('completed','mastered')",
        viewer.id, entity_id,
    ):
        return _reject(request, back_to, "Complete the topic before claiming a certificate.")
    # Never issue a credential whose type, subject, or display name came from
    # an untrusted browser field.
    title = f"{topic['title']} completion"
    cert_id = progress.issue_certificate(viewer.id, kind, entity_type, entity_id, title)
    # verify_certificate looks a certificate up by its public verify_id, not its id,
    # and returns {"certificate", "holder", "branch", "meta"} rather than a bare row.
    issued = db.query_one("SELECT verify_id FROM certificates WHERE id = ?", cert_id)
    verify_id = issued["verify_id"] if issued else None
    bundle = progress.verify_certificate(verify_id) if verify_id else None
    url = f"/certificates/{verify_id}" if verify_id else None
    if wants_html(request) and url:
        return RedirectResponse(url, status_code=303)
    return ok(certificate=bundle, verifyId=verify_id, url=url, message="Certificate issued.")


# ---------------------------------------------------------------------------
# Recommendations
# ---------------------------------------------------------------------------

@router.get("/recommendations")
async def api_recommendations(request: Request):
    viewer = require_user(request)
    return ok(
        dashboard=recommend.dashboard(viewer.id),
        next=recommend.next_topics_for(viewer.id, 8),
        retry=recommend.retry_plan(viewer.id),
    )


# ---------------------------------------------------------------------------
# Catalogue helpers
# ---------------------------------------------------------------------------

@router.get("/catalog/branches")
async def api_branches(request: Request):
    return ok(groups=catalog.branch_groups())


@router.get("/catalog/subjects")
async def api_subjects(request: Request, branch: str | None = None, semester: str | None = None):
    if (branch is not None and len(branch) > 128) or (
        semester not in (None, "") and (len(semester) > 3 or not semester.isdecimal())
    ):
        return fail("Invalid subject filter.", 400)
    semester_number = int(semester) if semester else None
    if semester_number is not None and semester_number > 100:
        return fail("Invalid subject filter.", 400)
    return ok(subjects=catalog.list_subjects(branch=branch, semester=semester_number, limit=300))


@router.get("/catalog/formulas")
async def api_formulas(request: Request, category: str | None = None, q: str | None = None):
    if (category is not None and len(category) > 80) or (q is not None and len(q) > 200):
        return fail("Formula filters are too long.", 413)
    return ok(formulas=catalog.list_formulas(category=category, q=q, limit=300))


@router.post("/feedback")
async def api_feedback(request: Request):
    """Public feedback channel. Stored for staff review; never executed."""
    viewer = current_user(request)
    data = await payload(request)
    message = text_field(data, "message", maximum=2000)
    candidate_path = text_field(data, "path", maximum=200, default="/about")
    back_to = (
        candidate_path
        if len(candidate_path) <= 200
        and candidate_path.startswith("/")
        and is_safe_url(candidate_path)
        else "/about"
    )
    if len(message) < 5:
        return _reject(request, back_to, "Tell us a little more than that.")
    if len(message) > 2000:
        return _reject(request, back_to, "Keep feedback under 2,000 characters.")
    record("app.feedback", actor_id=viewer.id if viewer else None,
           meta={"message": message, "path": back_to})
    message = "Thanks — that reached the team."
    if wants_html(request):
        from .deps import flash

        response = RedirectResponse(back_to, status_code=303)
        flash(response, message)
        return response
    return ok(message=message)


@router.get("/ops/judge")
async def judge_status(request: Request):
    """What this process will do with submitted code. Staff only.

    The payload names the provider and the isolation claim. It does not include
    the Judge0 URL or key. ``isolation`` is a description, not a verification
    that a remote judge is sandboxed.
    """
    viewer = current_user(request)
    if viewer is None or not rbac.can(viewer.role, "settings.manage"):
        return JSONResponse({"ok": False, "error": "You do not have permission to view operations status."},
                            status_code=403)
    info = judge.provider_info()
    return ok(
        judge=info.get("name"),
        available=bool(info.get("available")),
        runs_on_this_server=bool(info.get("runs_on_this_server")),
        isolation=info.get("isolation") or "",
    )
