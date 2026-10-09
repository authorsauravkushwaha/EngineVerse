"""JSON API.

Consumed by ``static/js/app.js`` for progressive enhancement: running code,
submitting answers, reviewing flashcards, bookmarking, voting and searching.
Every mutating endpoint requires a signed-in session plus the CSRF header.
"""
from __future__ import annotations

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
from engineverse.security.audit import record

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


def split_tags(value: Any) -> list[str]:
    """Accepts a list, or the comma-separated string an HTML form sends."""
    if isinstance(value, list):
        return [str(v).strip() for v in value if str(v).strip()]
    if isinstance(value, str):
        return [part.strip() for part in value.split(",") if part.strip()]
    return []


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
    if not db.query_one("SELECT 1 FROM topics WHERE slug = ? OR id = ?", topicId, topicId):
        return fail("No such topic.", 404)
    if wanted not in ("completed", "mastered", "started", "in_progress", "viewed"):
        return fail("That is not a progress state this accepts.", 400)
    if wanted in ("completed", "mastered"):
        progress.complete_topic(viewer.id, topicId)
    else:
        progress.mark_topic_viewed(viewer.id, topicId)
    progress.evaluate_badges(viewer.id)
    return ok(stats=progress.user_stats(viewer.id))


# ---------------------------------------------------------------------------
# Search
# ---------------------------------------------------------------------------

@router.get("/search")
async def api_search(request: Request, q: str = "", type: str | None = None, branch: str | None = None,
                     limit: int = 20):
    if not q.strip():
        return ok(results=[], total=0, suggestion=None)
    result = search_grouped(q, type=type, branch=branch, limit=min(limit, 60))
    return ok(**result)


def search_grouped(q: str, **options: Any) -> dict:
    from engineverse import search

    payload = search.grouped(q, **options)
    search.log_search(q, payload["total"])
    return payload


@router.get("/search/suggest")
async def api_suggest(request: Request, q: str = ""):
    from engineverse import search

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
    question = practice.question_by_id(question_id)
    if not question:
        return fail("Unknown question.", 404)
    return ok(question=practice.public_question(question))


@router.post("/practice/answer")
async def api_answer(request: Request, questionId: str = Body(...), optionIndex: int | None = Body(None),
                     answerText: str | None = Body(None), setId: str | None = Body(None),
                     timeMs: int | None = Body(None)):
    viewer = require_user(request)
    question = practice.question_by_id(questionId)
    if not question:
        return fail("Unknown question.", 404)
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
    return ok(mistakes=practice.mistake_notebook(viewer.id, limit=min(limit, 100)))


# ---------------------------------------------------------------------------
# Coding
# ---------------------------------------------------------------------------

@router.get("/coding/languages")
async def api_languages(request: Request):
    return ok(languages=coding.list_languages(), runnable=judge.runnable_languages())


@router.get("/coding/problems")
async def api_problems(request: Request, difficulty: str | None = None, topic: str | None = None,
                       q: str | None = None, limit: int = 50):
    return ok(problems=coding.list_problems(difficulty=difficulty, topic=topic, q=q, limit=min(limit, 200))[0])


@router.get("/coding/problems/{slug}")
async def api_problem(request: Request, slug: str):
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
    if len(code) > 64_000:
        return fail("That program is too long to run.", 413)
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
    problem_id = None
    if problemSlug:
        problem = coding.get_problem(problemSlug)
        problem_id = problem["id"] if problem else None
    return ok(submissions=coding.submissions_for(viewer.id, problem_id, min(limit, 50)))


# ---------------------------------------------------------------------------
# Flashcards / spaced repetition
# ---------------------------------------------------------------------------

@router.get("/revision/due")
async def api_due(request: Request, limit: int = 20):
    viewer = require_user(request)
    return ok(cards=library.due_flashcards(viewer.id, min(limit, 50)),
              stats=library.flashcard_stats(viewer.id))


@router.post("/revision/review")
async def api_review(request: Request, cardId: str = Body(...), rating: str = Body("good")):
    viewer = require_user(request)
    # srs.review raises ValueError on an unknown rating and there is no handler
    # registered for ValueError, so it surfaced as a 500. A card that does not
    # exist is worse: the insert into user_flashcards has a foreign key, so the
    # database raised IntegrityError out of the handler. Validate both here.
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
    question = (data.get("question") or "").strip()
    if not question:
        return fail("Ask a question first.", status=422)
    if len(question) > 400:
        return fail("Keep the question under 400 characters.", status=422)

    result = tutor.answer(question, user_id=viewer.id if viewer else None)
    record("tutor.asked", actor_id=viewer.id if viewer else None,
           ip=request.client.host if request.client else None,
           meta={"question": question[:200], "grounded": result["grounded"],
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
    return ok(bookmarks=progress.bookmarks(viewer.id, entityType))


@router.post("/notes/personal")
async def api_personal_note(request: Request):
    viewer = require_user(request)
    data = await payload(request)
    entity_type = (data.get("entityType") or "").strip()
    entity_id = (data.get("entityId") or "").strip()
    content = (data.get("content") or "").strip()
    if entity_type not in ("topic", "problem", "project", "flashcard"):
        return _reject(request, "/", "That is not something you can attach a note to.")
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
    return ok(notifications=progress.notifications(viewer.id, min(limit, 60)))


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
    notification_id = (data.get("notificationId") or "").strip() or None
    progress.mark_notifications_read(viewer.id, notification_id)
    return ok(unread=len(progress.notifications(viewer.id, unread_only=True)))


# ---------------------------------------------------------------------------
# Community
# ---------------------------------------------------------------------------

@router.post("/community/threads")
async def api_create_thread(request: Request):
    viewer = require_user(request)
    data = await payload(request)
    title = (data.get("title") or "").strip()
    body = (data.get("body") or "").strip()
    kind = (data.get("kind") or "question").strip() or "question"
    tags = split_tags(data.get("tags"))
    subjectId = data.get("subjectId") or None
    topicId = data.get("topicId") or None
    if len(title) < 5:
        return _reject(request, "/community", "Give your post a title of at least 5 characters.")
    if len(body) < 10:
        return _reject(request, "/community", "Add a little more detail so people can help.")
    # create_thread attaches a thread to one entity, so a topic wins over a
    # subject when both are supplied.
    entity_type, entity_id = (None, None)
    if topicId:
        entity_type, entity_id = "topic", topicId
    elif subjectId:
        entity_type, entity_id = "subject", subjectId
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
    data = await payload(request)
    threadId = (data.get("threadId") or "").strip()
    body = (data.get("body") or "").strip()
    parentId = data.get("parentId") or None
    if not body:
        return _reject(request, f"/community/{threadId}", "Write something before posting.")
    if not community.get_thread(threadId):
        return fail("That discussion does not exist.", 404)
    comment_id = community.add_comment(viewer.id, threadId, body, parentId)
    url = f"/community/{threadId}#c-{comment_id}"
    if wants_html(request):
        return RedirectResponse(url, status_code=303)
    return ok(id=comment_id, url=url, message="Reply posted.")


@router.post("/community/vote")
async def api_vote(request: Request, entityType: str = Body(...), entityId: str = Body(...),
                   value: int = Body(1)):
    viewer = require_user(request)
    # community.vote() only moves a score for "discussion" and "comment"; any
    # other entity_type wrote a votes row and returned 200 with score 0, so a
    # client sending the wrong string got a success response for a vote that
    # silently did nothing. Refuse it instead, the way /community/report does.
    entity_type = entityType.strip()
    if entity_type not in ("discussion", "comment"):
        return fail("That is not something you can vote on.", 400)
    if not entityId.strip():
        return fail("That is not something you can vote on.", 400)
    score = community.vote(viewer.id, entity_type, entityId, value)
    return ok(score=score)


@router.post("/community/report")
async def api_report(request: Request):
    viewer = require_user(request)
    data = await payload(request)
    entity_type = (data.get("entityType") or "").strip()
    entity_id = (data.get("entityId") or "").strip()
    reason = (data.get("reason") or "").strip()
    detail = (data.get("detail") or "").strip() or None
    # The URL calls it a thread, the discussions table calls it a discussion, and
    # community.resolve_report() hides the content only when the stored type is
    # "discussion". Accepting "thread" here and storing it verbatim meant the hide
    # path could never match, so a moderator could close a report but not remove
    # what was reported. Normalise to the name the rest of the code uses.
    if entity_type == "thread":
        entity_type = "discussion"
    if entity_type not in ("discussion", "comment") or not entity_id:
        return _reject(request, "/community", "That is not something you can report.")
    if len(reason) < 3:
        return _reject(request, "/community", "Give a reason so a moderator can act on it.")
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
    slug = (data.get("projectSlug") or "").strip()
    project = projects.get_project(slug)
    if not project:
        return fail("Unknown project.", 404)
    projects.record_build(viewer.id, project["id"])
    if wants_html(request):
        return RedirectResponse(f"/projects/{slug}", status_code=303)
    return ok(message="Logged. Nice build.")


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
    kind = (data.get("kind") or "topic").strip() or "topic"
    entity_type = (data.get("entityType") or "").strip()
    entity_id = (data.get("entityId") or "").strip()
    title = (data.get("title") or "").strip() or "EngineVerse completion"
    back_to = _entity_url(entity_type, entity_id)
    if not title or len(title) > 160:
        return _reject(request, back_to, "That certificate title is not usable.")
    if entity_type == "topic" and not db.query_one(
        "SELECT 1 FROM user_progress WHERE user_id = ? AND topic_id = ? AND status IN ('completed','mastered')",
        viewer.id, entity_id,
    ):
        return _reject(request, back_to, "Complete the topic before claiming a certificate.")
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
    return ok(subjects=catalog.list_subjects(branch=branch, semester=int(semester) if semester and str(semester).isdigit() else None, limit=300))


@router.get("/catalog/formulas")
async def api_formulas(request: Request, category: str | None = None, q: str | None = None):
    return ok(formulas=catalog.list_formulas(category=category, q=q, limit=300))


@router.post("/feedback")
async def api_feedback(request: Request):
    """Public feedback channel. Stored for staff review; never executed."""
    viewer = current_user(request)
    data = await payload(request)
    message = (data.get("message") or "").strip()
    path = (data.get("path") or "")[:200]
    back_to = path if path.startswith("/") and not path.startswith("//") else "/about"
    if len(message) < 5:
        return _reject(request, back_to, "Tell us a little more than that.")
    record("app.feedback", actor_id=viewer.id if viewer else None,
           meta={"message": message[:2000], "path": path})
    message = "Thanks — that reached the team."
    if wants_html(request):
        from .deps import flash

        response = RedirectResponse(back_to, status_code=303)
        flash(response, message)
        return response
    return ok(message=message)
