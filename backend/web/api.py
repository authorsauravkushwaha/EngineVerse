"""JSON API.

Consumed by ``static/js/app.js`` for progressive enhancement: running code,
submitting answers, reviewing flashcards, bookmarking, voting and searching.
Every mutating endpoint requires a signed-in session plus the CSRF header.
"""
from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Body, Form, Request
from fastapi.responses import JSONResponse

from engineverse import (
    auth,
    catalog,
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
)
from engineverse.security.audit import record

from .deps import current_user, require_user

router = APIRouter()


def ok(**payload: Any) -> JSONResponse:
    payload["ok"] = True
    return JSONResponse(payload)


def fail(message: str, status: int = 400, **extra: Any) -> JSONResponse:
    body: dict[str, Any] = {"ok": False, "error": message}
    body.update(extra)
    return JSONResponse(body, status_code=status)


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
    if status in ("completed", "mastered"):
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
            "ON CONFLICT(user_id,day) DO UPDATE SET coding_submissions = coding_submissions + 1",
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
    state = srs.review(viewer.id, cardId, rating)
    progress.award_xp(viewer.id, 2, "flashcard", "flashcard", cardId)
    progress.bump_activity(viewer.id, "revisions")
    return ok(state=state, stats=library.flashcard_stats(viewer.id))


# ---------------------------------------------------------------------------
# Bookmarks, notes, notifications
# ---------------------------------------------------------------------------

@router.post("/bookmarks")
async def api_bookmark(request: Request, entityType: str = Body(...), entityId: str = Body(...),
                       note: str | None = Body(None)):
    viewer = require_user(request)
    added = progress.toggle_bookmark(viewer.id, entityType, entityId, note)
    return ok(bookmarked=added)


@router.get("/bookmarks")
async def api_bookmarks(request: Request, entityType: str | None = None):
    viewer = require_user(request)
    return ok(bookmarks=progress.bookmarks(viewer.id, entityType))


@router.post("/notes/personal")
async def api_personal_note(request: Request, entityType: str = Body(...), entityId: str = Body(...),
                            content: str = Body(...)):
    viewer = require_user(request)
    if len(content) > 20_000:
        return fail("That note is too long.", 413)
    note_id = progress.save_personal_note(viewer.id, entityType, entityId, content)
    return ok(id=note_id)


@router.get("/notifications")
async def api_notifications(request: Request, limit: int = 30):
    viewer = require_user(request)
    return ok(notifications=progress.notifications(viewer.id, min(limit, 60)))


@router.post("/notifications/read")
async def api_notifications_read(request: Request, notificationId: str | None = Body(None)):
    viewer = require_user(request)
    progress.mark_notifications_read(viewer.id, notificationId)
    return ok()


# ---------------------------------------------------------------------------
# Community
# ---------------------------------------------------------------------------

@router.post("/community/threads")
async def api_create_thread(request: Request, title: str = Body(...), body: str = Body(...),
                            kind: str = Body("question"), tags: list[str] = Body(default_factory=list),
                            subjectId: str | None = Body(None), topicId: str | None = Body(None)):
    viewer = require_user(request)
    thread_id = community.create_thread(
        viewer.id, title=title, body=body, kind=kind, tags=tags, subject_id=subjectId, topic_id=topicId
    )
    return ok(id=thread_id, url=f"/community/{thread_id}")


@router.post("/community/comments")
async def api_comment(request: Request, threadId: str = Body(...), body: str = Body(...),
                      parentId: str | None = Body(None)):
    viewer = require_user(request)
    comment_id = community.add_comment(viewer.id, threadId, body, parentId)
    return ok(id=comment_id)


@router.post("/community/vote")
async def api_vote(request: Request, entityType: str = Body(...), entityId: str = Body(...),
                   value: int = Body(1)):
    viewer = require_user(request)
    score = community.vote(viewer.id, entityType, entityId, value)
    return ok(score=score)


@router.post("/community/report")
async def api_report(request: Request, entityType: str = Body(...), entityId: str = Body(...),
                     reason: str = Body(...), detail: str | None = Body(None)):
    viewer = require_user(request)
    report_id = community.report(viewer.id, entityType, entityId, reason, detail)
    return ok(id=report_id)


# ---------------------------------------------------------------------------
# Projects
# ---------------------------------------------------------------------------

@router.post("/projects/track")
async def api_project_track(request: Request, projectSlug: str = Body(...)):
    viewer = require_user(request)
    project = projects.get_project(projectSlug)
    if not project:
        return fail("Unknown project.", 404)
    projects.record_build(viewer.id, project["id"])
    return ok()


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


@router.post("/certificates/issue")
async def api_issue_certificate(request: Request, kind: str = Body(...), entityType: str = Body(...),
                                entityId: str = Body(...), title: str = Body(...)):
    viewer = require_user(request)
    if not db.query_one(
        "SELECT 1 FROM user_progress WHERE user_id = ? AND topic_id = ? AND status IN ('completed','mastered')",
        viewer.id, entityId,
    ) and entityType == "topic":
        return fail("Complete the topic before claiming a certificate.", 403)
    cert_id = progress.issue_certificate(viewer.id, kind, entityType, entityId, title)
    row = progress.verify_certificate(cert_id)
    return ok(certificate=row)


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
async def api_feedback(request: Request, message: str = Body(..., embed=True), path: str = Body("", embed=True)):
    """Public feedback channel. Stored for staff review; never executed."""
    viewer = current_user(request)
    record("app.feedback", actor_id=viewer.id if viewer else None,
           meta={"message": message[:2000], "path": path[:200]})
    return ok()
