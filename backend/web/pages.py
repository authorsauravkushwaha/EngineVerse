"""Server-rendered pages.

Every page works without JavaScript. Enhancement lives in ``static/js/app.js``
and talks to the JSON API under ``/api``.
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any
from urllib.parse import urlencode
from xml.sax.saxutils import escape

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import RedirectResponse

from engineverse import (
    brand,
    catalog,
    certificates,
    coding,
    community,
    db,
    hub,
    judge,
    ladders,
    library,
    navigation,
    practice,
    progress,
    projects,
    recommend,
    search,
)

from engineverse.config import get_settings
from engineverse.security import rbac

from .deps import current_user, render, require_user

router = APIRouter()

# A topic_id that cannot exist. Passed to practice.list_questions() when a link
# names a topic slug that is not in the catalogue, so the question bank answers
# "no questions match" instead of dropping the filter and showing all of them.
NO_SUCH_TOPIC = "__no_such_topic__"

# Upper bound on a ?slug= deep link before it reaches a query.
MAX_SLUG_LENGTH = 128


def deep_link_slug(slug: str | None) -> str | None:
    """Bounds a ``?slug=`` deep link, or drops it.

    Search results and the recommendation cards point at one item inside a
    library page that paginates. A URL fragment cannot do that: the browser
    sends only the path, and the item is usually several pages in, so the reader
    arrived at page one of a long list with no idea which entry they had asked
    for. Those links carry ``?slug=`` instead and the page narrows to the single
    matching row, whatever the catalogue grows to.
    """
    if not slug:
        return None
    slug = slug.strip()[:MAX_SLUG_LENGTH]
    return slug or None


# ---------------------------------------------------------------------------
# Home and exploration
# ---------------------------------------------------------------------------

@router.get("/")
async def home(request: Request):
    viewer = current_user(request)
    context = {
        "site": catalog.site_stats(),
        "branches": catalog.branch_groups(),
        "popular_subjects": catalog.popular_subjects(12),
        "cyber_security_subject": catalog.get_subject("cryptography-security"),
        "trending": search.trending(8),
    }
    if viewer:
        context["dashboard"] = recommend.dashboard(viewer.id)
        context["continue_learning"] = progress.continue_learning(viewer.id, 6)
        context["dpp"] = practice.dpp_with_context()
        # One query, and the dashboard can name the viewer's own stream with its
        # real sizes instead of a generic "browse everything" link.
        context["my_stream"] = next(
            (row for row in hub.list_streams() if row["id"] == viewer.branch_id), None
        )
        return render(request, "dashboard.html", **context)
    context["featured_topics"] = db.query(
        "SELECT t.slug, t.title, t.summary, t.difficulty, t.est_minutes, s.name AS subject, s.color AS color "
        "FROM topics t JOIN subjects s ON s.id = t.subject_id WHERE t.status='published' "
        "ORDER BY t.view_count DESC, t.order_index LIMIT 9"
    )
    context["sample_problems"] = coding.list_problems(limit=6)[0]
    context["sample_projects"] = projects.list_projects(limit=3)
    context["paths"] = catalog.featured_paths()
    context["first_year"] = catalog.list_subjects(first_year=True, limit=200)
    return render(request, "home.html", **context)


@router.get("/explore")
async def explore(
    request: Request,
    branch: str | None = None,
    semester: str | None = None,
    q: str | None = None,
    year: str | None = None,
):
    first_year = year == "1"
    semester_id = int(semester) if semester and semester.isdecimal() and len(semester) <= 3 else None
    q = q[:200] if q else None
    total = catalog.count_subjects(branch=branch, semester=semester_id, first_year=first_year, q=q)
    pager = _pager(request, total)
    return render(
        request, "explore.html",
        branches=catalog.branch_groups(),
        subjects=catalog.list_subjects(
            branch=branch,
            semester=semester_id,
            first_year=first_year,
            q=q,
            limit=pager["size"],
            offset=(pager["page"] - 1) * pager["size"],
        ),
        total_subjects=total,
        pager=pager,
        semesters=catalog.list_semesters(),
        active_branch=branch,
        active_semester=str(semester_id) if semester_id else "",
        active_q=q,
        active_year="1" if first_year else "",
    )


@router.get("/search")
async def search_page(request: Request, q: str = "", type: str | None = None, branch: str | None = None):
    result = {"results": [], "total": 0, "suggestion": None, "groups": []}
    if q.strip():
        result = search.grouped(q, type=type, branch=branch, limit=40)
        search.log_search(q, result["total"])
    return render(
        request, "search.html", q=q, results=result["results"], total=result["total"],
        suggestion=result["suggestion"], groups=result.get("groups", []),
        active_type=type, trending=search.trending(10),
    )


# ---------------------------------------------------------------------------
# Catalogue: branch -> subject -> topic
# ---------------------------------------------------------------------------

@router.get("/branches/{slug}")
async def branch_page(request: Request, slug: str):
    branch = catalog.get_branch(slug)
    if not branch:
        raise HTTPException(status_code=404, detail="Unknown branch")
    total = catalog.count_subjects(branch=slug)
    pager = _pager(request, total)
    return render(
        request, "branch.html", branch=branch,
        crumb_leaf=branch["name"],
        subjects=catalog.list_subjects(
            branch=slug, limit=pager["size"], offset=(pager["page"] - 1) * pager["size"],
        ),
        total_subjects=total, pager=pager,
        semesters=catalog.list_semesters(),
        roadmaps=library.list_roadmaps(branch_slug=slug),
        related_projects=projects.list_projects(branch=branch["id"], limit=6),
    )


@router.get("/subjects/{slug}")
async def subject_page(request: Request, slug: str):
    subject = catalog.get_subject(slug)
    if not subject:
        raise HTTPException(status_code=404, detail="Unknown subject")
    viewer = current_user(request)
    return render(
        request, "subject.html", subject=subject,
        crumb_leaf=subject["name"],
        outline=catalog.subject_outline(subject["id"]),
        stats=catalog.subject_stats(subject["id"]),
        questions=practice.list_questions(subject_id=subject["id"], limit=20)[0],
        videos=library.list_videos(subject_id=subject["id"], limit=10),
        books=library.list_books(subject_id=subject["id"], limit=10),
        roadmaps=library.list_roadmaps(kind="subject"),
        my_progress=progress.subject_progress(viewer.id, subject["id"]) if viewer else None,
    )


@router.get("/topics/{slug}")
async def topic_page(request: Request, slug: str, depth: str | None = None):
    topic = catalog.get_topic(slug)
    if not topic:
        raise HTTPException(status_code=404, detail="Unknown topic")
    viewer = current_user(request)
    quality = depth or (viewer.note_quality if viewer else "standard")
    note = catalog.get_note(topic["id"], quality) or catalog.get_note(topic["id"], "standard")
    all_depths = catalog.notes_by_depth(topic["id"]) if request.query_params.get("depths") == "all" else []
    if viewer:
        progress.mark_topic_viewed(viewer.id, topic["id"])
    questions = practice.questions_for_topic(topic["id"], 8)
    return render(
        request, "topic.html", topic=topic,
        crumb_leaf=topic["title"],
        crumb_parents=[(topic.get("subject_name") or "", f"/subjects/{topic.get('subject_slug') or ''}")],
        note=note,
        sections=catalog.sections_for_note(note["id"]) if note else [],
        diagrams=catalog.diagrams_for_topic(topic["id"]),
        models_3d=catalog.models_for_topic(topic["id"]),
        formulas=catalog.formulas_for_topic(topic["id"]),
        questions=questions,
        attempts=_attempts(viewer, questions),
        flashcards=library.flashcards_for_topic(topic["id"]),
        resources=library.topic_resources(topic["id"], topic["subject_id"]),
        related=catalog.related_topics(topic),
        siblings=catalog.topic_siblings(topic["subject_id"], topic["order_index"]),
        recommendations=recommend.for_topic(topic, viewer.id if viewer else None),
        my_progress=progress.topic_progress(viewer.id, topic["id"]) if viewer else None,
        my_notes=progress.personal_notes(viewer.id, "topic", topic["id"]) if viewer else [],
        my_certificate=(
            db.query_one(
                "SELECT id, verify_id, issued_at FROM certificates "
                "WHERE user_id = ? AND entity_type = 'topic' AND entity_id = ?",
                viewer.id, topic["id"],
            )
            if viewer else None
        ),
        quality=quality,
        all_depths=all_depths,
        available_depths=db.query(
            "SELECT quality_level FROM notes WHERE topic_id = ? ORDER BY quality_level", topic["id"]
        ),
    )


# ---------------------------------------------------------------------------
# Practice
# ---------------------------------------------------------------------------

@router.get("/practice")
async def practice_page(request: Request):
    return render(
        request, "practice.html",
        dpp=practice.dpp_with_context(),
        sets=practice.recent_practice_days(30),
        kinds=practice.question_kinds(),
        questions=practice.list_questions(limit=20)[0],
        ladder=ladders.PRACTICE,
        ladder_title="From a first look to working practice",
        ladder_note="A way to use the notes and questions that exist. Not a degree, and not a claim that every subject is fully written.",
        fields=ladders.field_starts(12),
    )


def _attempts(viewer, questions: list[dict]) -> dict[str, dict]:
    """The signed-in learner's attempt history for the questions on a page."""
    if not viewer or not questions:
        return {}
    return practice.attempt_summary(viewer.id, [q["id"] for q in questions])


@router.get("/dpp")
async def dpp_today(request: Request):
    payload = practice.dpp_with_context()
    return render(
        request, "dpp.html", dpp=payload,
        sets=practice.recent_practice_days(30), active_date=None,
        attempts=_attempts(current_user(request), payload["questions"] if payload else []),
    )


@router.get("/dpp/archive")
async def dpp_archive(request: Request):
    total = practice.count_dpp_sets()
    pager = _pager(request, total, size=DPP_ARCHIVE_PAGE_SIZE)
    return render(
        request, "dpp_archive.html",
        crumb_leaf="Archive",
        sets=practice.list_dpp_sets(
            limit=pager["size"], offset=(pager["page"] - 1) * pager["size"]
        ),
        pager=pager,
    )


@router.get("/dpp/{date}")
async def dpp_day(request: Request, date: str):
    payload = practice.dpp_with_context(date)
    if not payload:
        raise HTTPException(status_code=404, detail="No practice set for that date")
    return render(request, "dpp.html", dpp=payload, sets=practice.recent_practice_days(30), active_date=date,
                  crumb_leaf=date,
                  attempts=_attempts(current_user(request), payload["questions"]))


@router.get("/practice/questions")
async def question_bank(request: Request, subject: str | None = None, kind: str | None = None,
                        difficulty: str | None = None, topic: str | None = None,
                        slug: str | None = None, q: str | None = None):
    # Keep the full bank reachable as it grows; filter parameters survive paging.
    #
    # topic, slug and q are addressed by links rather than by the three selects
    # in the form: global search points every question result at ?slug=, and the
    # recovery plan on /mistakes points at ?topic=...&difficulty=easy. Both
    # promised a filtered bank while this handler read only subject/kind/
    # difficulty, so a learner following either link got the whole catalogue
    # back with no sign that the filter had been dropped.
    filters: dict[str, Any] = {"subject_id": subject, "kind": kind, "difficulty": difficulty}
    if slug and len(slug) <= practice.MAX_ID_LENGTH:
        filters["slug"] = slug
    if q and len(q) <= 120:
        filters["q"] = q
    active_topic = None
    if topic and len(topic) <= practice.MAX_ID_LENGTH:
        active_topic = catalog.get_topic(topic)
        # An unknown topic slug has to read as "no questions here", not as "every
        # question": this id cannot match a row, whereas omitting the filter
        # would quietly widen the page back to the full bank.
        filters["topic_id"] = active_topic["id"] if active_topic else NO_SUCH_TOPIC
    total = practice.list_questions(**filters, limit=1)[1]
    pager = _pager(request, total)
    questions = practice.list_questions(
        **filters, limit=pager["size"], offset=(pager["page"] - 1) * pager["size"],
    )[0]
    return render(
        request, "question_bank.html",
        questions=questions,
        attempts=_attempts(current_user(request), questions),
        kinds=practice.question_kinds(),
        subjects=catalog.list_subjects(limit=200),
        active_subject=subject, active_kind=kind, active_difficulty=difficulty,
        active_topic=active_topic, active_slug=slug if filters.get("slug") else None,
        active_q=q if filters.get("q") else None,
        filtered=bool(filters.get("slug") or filters.get("q") or topic),
        pager=pager,
    )


@router.get("/mistakes")
async def mistakes_page(request: Request):
    viewer = require_user(request)
    return render(
        request, "mistakes.html",
        mistakes=practice.mistake_cards(viewer.id, limit=50),
        retry=recommend.retry_plan(viewer.id),
    )


@router.post("/practice/check")
async def practice_check(request: Request):
    """Grades one answer from a plain HTML form and shows the result.

    This is the no-JavaScript path for every question card. Before it existed
    the card's form had no action, so submitting without the script (or with a
    stale cached copy of it) quietly reloaded the page with ``?option=N`` and
    nothing was graded. It records the attempt exactly like
    ``POST /api/practice/answer`` - same grading, XP and mistake notebook - and
    renders the outcome with a link back to the card.
    """
    viewer = require_user(request)
    form = await request.form()
    question_id = str(form.get("question_id") or "").strip()
    set_id = str(form.get("set_id") or "").strip() or None
    raw_option = str(form.get("option") or "").strip()
    back = str(form.get("next") or "/practice/questions")
    if not back.startswith("/") or back.startswith("//") or len(back) > 1024:
        back = "/practice/questions"

    question = practice.question_by_id(question_id) if 0 < len(question_id) <= practice.MAX_ID_LENGTH else None
    if not question:
        raise HTTPException(status_code=404, detail="Unknown question")
    options = practice.options_for(question_id)
    if set_id is not None and (len(set_id) > practice.MAX_ID_LENGTH or not db.query_one(
        "SELECT 1 FROM dpp_questions dq JOIN dpp_sets d ON d.id = dq.set_id "
        "WHERE dq.set_id = ? AND dq.question_id = ? AND d.published = 1",
        set_id, question_id,
    )):
        set_id = None
    option_index = int(raw_option) if raw_option.isdigit() else None
    if not options or option_index is None or not 0 <= option_index < len(options):
        return render(
            request, "practice_result.html", status_code=422,
            question=practice.public_question(question), result=None, chosen=None,
            back=back, error="Choose one of the listed options, then check your answer.",
        )
    result = practice.record_answer(viewer.id, question_id, option_index=option_index, set_id=set_id)
    progress.evaluate_badges(viewer.id)
    return render(
        request, "practice_result.html",
        question=practice.public_question(question), result=result,
        chosen=options[option_index], back=back, error=None,
    )


# ---------------------------------------------------------------------------
# Coding
# ---------------------------------------------------------------------------

@router.get("/programming")
async def programming_home(request: Request):
    viewer = current_user(request)
    return render(
        request, "programming.html",
        languages=coding.list_languages(),
        problems=coding.list_problems(limit=60)[0],
        topics=coding.problem_topics(),
        solved=coding.solved_problem_ids(viewer.id) if viewer else set(),
        submissions=coding.submissions_for(viewer.id, limit=15) if viewer else [],
        ladder=ladders.CODE,
        ladder_title="From scratch to a working habit",
        ladder_note="Each language is a path you can finish. It is not every feature of that language, and it is not a job offer.",
        fields=ladders.field_starts(12),
    )


@router.get("/programming/{language}")
async def language_page(request: Request, language: str):
    lang = coding.language_by_slug(language)
    if not lang:
        raise HTTPException(status_code=404, detail="Unknown language")
    stages = coding.stages_for_language(lang["id"])
    viewer = current_user(request)
    # Attempt history for the stage checkpoints, so a signed-in learner sees
    # which gates they have already answered. Read-only; the answer key never
    # reaches the page - checkpoints are graded by the normal practice API.
    checkpoint_ids = [q["id"] for stage in stages for q in stage["checkpoints"]]
    attempts = practice.attempt_summary(viewer.id, checkpoint_ids) if viewer else {}
    return render(
        request, "language.html", language=lang,
        crumb_leaf=lang["name"],
        stages=stages,
        modules=coding.modules_for_language(lang["id"]),
        capstone=coding.capstone_for_language(lang["id"]),
        # Only problems this language has a starter for: a problem without a
        # stub renders an editor that cannot run in the page's language.
        problems=coding.problems_with_starter(lang["id"], limit=30),
        attempts=attempts,
    )


@router.get("/practice/problems")
async def problem_list(request: Request, difficulty: str | None = None, topic: str | None = None,
                       q: str | None = None, sheet: str | None = None):
    viewer = current_user(request)
    branch = hub.branch_by_id(viewer.branch_id) if viewer else None
    if sheet:
        chosen = coding.sheet_by_slug(sheet)
        if chosen:
            rows = coding.problems_for_sheet(chosen["id"])
            if difficulty:
                rows = [row for row in rows if row["difficulty"] == difficulty]
            if topic:
                rows = [row for row in rows if topic in (row["topics_data"] or [])]
            return render(
                request, "problems.html",
                problems=rows, topics=coding.problem_topics(),
                solved=coding.solved_problem_ids(viewer.id) if viewer else set(),
                active_difficulty=difficulty, active_topic=topic, active_q=None,
                active_sheet=chosen, sheet_options=coding.list_sheets(),
                my_branch=branch,
                stream_sheets=coding.list_sheets(audience=branch["category"]) if branch else [],
            )
    return render(
        request, "problems.html",
        problems=coding.list_problems(difficulty=difficulty, topic=topic, q=q, limit=100)[0],
        topics=coding.problem_topics(),
        solved=coding.solved_problem_ids(viewer.id) if viewer else set(),
        active_difficulty=difficulty, active_topic=topic, active_q=q,
        active_sheet=None,
        sheet_options=coding.list_sheets(),
        my_branch=branch,
        stream_sheets=coding.list_sheets(audience=branch["category"]) if branch else [],
    )


@router.get("/practice/problems/{slug}")
async def problem_page(request: Request, slug: str):
    problem = coding.get_problem(slug)
    if not problem:
        raise HTTPException(status_code=404, detail="Unknown problem")
    viewer = current_user(request)
    return render(
        request, "problem.html", problem=problem,
        crumb_leaf=problem["title"],
        stubs=coding.stubs_for(problem["id"]),
        stub_map={row["slug"]: {"stub": row["stub"], "signature": row["signature"]}
                  for row in coding.stubs_for(problem["id"])},
        samples=coding.testcases_for(problem["id"], samples_only=True),
        languages=coding.list_languages(),
        # What this host can execute right now, not just what the catalogue
        # claims. The database flag is a property of the content; a missing JVM
        # is a property of the machine. Offering Java on a host with no javac
        # produced the same dead button as SQL did.
        runnable_now=set(judge.runnable_languages()),
        submissions=coding.submissions_for(viewer.id, problem["id"], 10) if viewer else [],
        saved=coding.saved_code(viewer.id, problem["id"], "python") if viewer else None,
        sheets=coding.sheets_for_problem(problem["id"]),
        solved_by_user=bool(viewer) and problem["id"] in coding.solved_problem_ids(viewer.id)
        if viewer else False,
    )


# ---------------------------------------------------------------------------
# Practice sheets and the per-stream study hub
# ---------------------------------------------------------------------------

def _group_streams(rows: list[dict]) -> list[dict]:
    """Branches grouped by category, in the catalogue's own order.

    Twelve cards is a page; forty-five is a wall. Grouping also answers the
    question a learner actually has - "which of these is mine?" - without
    needing the branch picker to be the first thing on the page.
    """
    grouped: dict[str, dict] = {}
    for row in rows:
        entry = grouped.setdefault(row["category"], {"key": row["category"], "name": row["category_name"], "branches": []})
        entry["branches"].append(row)
    return list(grouped.values())


@router.get("/sheets")
async def sheets_page(request: Request, audience: str | None = None):
    """Curated problem sheets, ordered for the viewer's own stream.

    A sheet names the branch categories it is for. Showing a mechanical learner
    the dynamic-programming sheet first is not wrong, but showing them the
    engineering-computing sheet first is the difference between a catalogue and
    a study plan, so stream sheets come first for a viewer whose branch is known.
    """
    viewer = current_user(request)
    branch = hub.branch_by_id(viewer.branch_id) if viewer else None
    my_category = branch["category"] if branch else None
    sheets = coding.list_sheets()
    progress_by_sheet = coding.solved_by_sheet(viewer.id) if viewer else {}

    def relevant(sheet: dict) -> bool:
        if not my_category:
            return True
        names = [part.strip() for part in (sheet["audience"] or "").split(",")]
        return "all" in names or my_category in names

    mine = [sheet for sheet in sheets if relevant(sheet)]
    others = [sheet for sheet in sheets if not relevant(sheet)]
    for sheet in sheets:
        sheet["progress"] = progress_by_sheet.get(sheet["id"], {"total": sheet["problem_count"], "solved": 0, "percent": 0})
    if audience:
        wanted = [sheet for sheet in sheets if audience in sheet["audience"].split(",") or sheet["audience"] == "all"]
        mine, others = wanted, []
    return render(
        request, "sheets.html",
        my_sheets=mine, other_sheets=others,
        my_branch=branch, viewer_branch_category=my_category,
        active_audience=audience,
        audiences=[row["key"] for row in _group_streams(hub.list_streams())],
        total_problems=int(db.scalar("SELECT count(*) AS c FROM coding_problems") or 0),
    )


@router.get("/sheets/{slug}")
async def sheet_page(request: Request, slug: str):
    sheet = coding.sheet_by_slug(slug)
    if not sheet:
        raise HTTPException(status_code=404, detail="Unknown sheet")
    viewer = current_user(request)
    problems = coding.problems_for_sheet(sheet["id"])
    solved = coding.solved_problem_ids(viewer.id) if viewer else set()
    return render(
        request, "sheet.html", sheet=sheet, problems=problems, solved=solved,
        crumb_leaf=sheet["title"],
        progress=coding.sheet_progress(viewer.id, sheet["id"]) if viewer else {
            "total": len(problems), "solved": 0, "percent": 0},
        all_sheets=coding.list_sheets(),
        runnable_now=set(judge.runnable_languages()),
    )


@router.get("/stream")
async def my_stream(request: Request, to: str | None = None):
    """Opens the hub on the viewer's own stream.

    No branch on the profile falls back to the first in catalogue order rather
    than to an error page: the hub is public, and a visitor who has not said
    which stream they are in still gets the same page with a picker.

    ``to`` is the stream picker's own value, so switching streams works with
    JavaScript disabled as well as with it. It is only ever accepted as a
    same-site ``/stream/...`` path, never as an arbitrary redirect target.
    """
    if to:
        candidate = to.strip()
        if candidate.startswith("/stream/") and "//" not in candidate and chr(92) not in candidate:
            slug = candidate[len("/stream/"):].strip("/")
            if slug and "/" not in slug and hub.branch_row(slug):
                return RedirectResponse(f"/stream/{slug}", status_code=303)
    viewer = current_user(request)
    slug = hub.default_branch_slug(viewer.branch_id if viewer else None)
    if not slug:
        return RedirectResponse("/streams", status_code=303)
    return RedirectResponse(f"/stream/{slug}", status_code=303)


@router.get("/streams")
async def streams_page(request: Request):
    """Every stream with the size of its in-app shelf."""
    viewer = current_user(request)
    streams = hub.list_streams()
    branch = hub.branch_by_id(viewer.branch_id) if viewer else None
    return render(
        request, "streams.html",
        streams=streams, categories=_group_streams(streams),
        my_branch=branch, my_slug=branch["slug"] if branch else "",
    )


@router.get("/stream/{slug}")
async def stream_page(request: Request, slug: str, semester: int | None = None):
    """Everything this stream can study, without leaving the site."""
    branch = hub.branch_row(slug)
    if not branch:
        raise HTTPException(status_code=404, detail="Unknown stream")
    viewer = current_user(request)
    # The learner's own semester narrows the subject list when they ask for it,
    # or when their profile has one and the branch actually tags subjects with
    # it. hub._subjects_for falls back to the whole branch when nothing matches.
    if semester is None and viewer and viewer.branch_id == branch["id"]:
        semester = viewer.semester_id
    data = hub.stream(branch["id"], semester_id=semester, viewer_id=viewer.id if viewer else None)
    if not data:
        raise HTTPException(status_code=404, detail="Unknown stream")
    streams = hub.list_streams()
    return render(
        request, "stream.html",
        **data,
        crumb_leaf=branch["name"],
        streams=streams, categories=_group_streams(streams),
        my_branch=hub.branch_by_id(viewer.branch_id) if viewer else None,
        active_semester=semester,
        semesters=catalog.list_semesters(),
        shows_semester_hint=bool(data["subjects"]) and any(row["semester_id"] for row in data["subjects"]),
    )


# ---------------------------------------------------------------------------
# Projects
# ---------------------------------------------------------------------------

@router.get("/projects")
async def projects_page(request: Request, difficulty: str | None = None, branch: str | None = None):
    return render(
        request, "projects.html",
        projects=projects.list_projects(difficulty=difficulty, branch=branch, limit=60),
        categories=projects.categories(),
        difficulties=projects.difficulties(),
        branches=catalog.list_branches(),
        active_difficulty=difficulty, active_branch=branch,
        ladder=ladders.PROJECTS,
        ladder_title="From the notes to a brief you can defend",
        ladder_note="Build only what you can explain. The briefs are practice, not a claim that the field is fully covered.",
        fields=ladders.field_starts(12),
    )


@router.get("/projects/{slug}")
async def project_page(request: Request, slug: str):
    project = projects.get_project(slug)
    if not project:
        raise HTTPException(status_code=404, detail="Unknown project")
    viewer = current_user(request)
    return render(
        request, "project.html", project=project,
        crumb_leaf=project["title"],
        has_built=projects.has_build(viewer.id, project["id"]) if viewer else False,
        steps=projects.steps(project["id"]),
        resources=projects.resources(project["id"]),
        similar=projects.suggested_for(viewer.id if viewer else None, 4),
    )


# ---------------------------------------------------------------------------
# Library and revision
# ---------------------------------------------------------------------------

#: Items per page on the library shelves. Large enough that a subject's whole
#: shelf usually fits on one page, small enough that 451 resources do not.
LIBRARY_PAGE_SIZE = 24
DPP_ARCHIVE_PAGE_SIZE = 30


def _pager(request: Request, total: int, *, size: int = LIBRARY_PAGE_SIZE) -> dict:
    """Builds the pagination context for a library page.

    The query string is carried across so paging keeps the active filter; a
    pager that drops ``?kind=book`` sends the reader back to page one of
    everything.
    """
    from urllib.parse import parse_qsl, urlencode

    raw_page = request.query_params.get("page") or "1"
    pages = max(1, -(-total // size)) if total else 1
    try:
        page = int(raw_page)
    except ValueError:
        page = 1
    # Clamped rather than 404'd: a stale bookmarked ?page=99 should still show
    # something rather than an error page.
    page = min(max(1, page), pages)

    base = {k: v for k, v in parse_qsl(request.url.query, keep_blank_values=True) if k != "page"}

    def link(target: int) -> str:
        params = dict(base, page=str(target))
        return f"{request.url.path}?{urlencode(params)}"

    return {
        "page": page, "pages": pages, "total": total, "size": size,
        "first": (page - 1) * size + 1 if total else 0,
        "last": min(page * size, total),
        "has_prev": page > 1, "has_next": page < pages,
        "prev_url": link(page - 1), "next_url": link(page + 1),
    }


def _index_totals() -> dict[str, int]:
    """The headline counts for the index page, read from the database.

    These are what the site actually has right now, not what it promises. A
    deployment seeded with less shows less.
    """
    stats = catalog.site_stats()
    return {
        "branches": int(stats.get("branches") or 0),
        "subjects": int(stats.get("subjects") or 0),
        "topics": int(stats.get("topics") or 0),
        "notes": int(db.scalar("SELECT count(*) AS c FROM notes WHERE status = 'published'") or 0),
        "questions": int(db.scalar("SELECT count(*) AS c FROM questions WHERE is_active = 1") or 0),
        "problems": int(db.scalar("SELECT count(*) AS c FROM coding_problems") or 0),
        "sheets": len(coding.list_sheets()),
        "flashcards": int(db.scalar("SELECT count(*) AS c FROM flashcards") or 0),
        "formulas": int(stats.get("formulas") or 0),
        "projects": int(db.scalar("SELECT count(*) AS c FROM projects WHERE status = 'published'") or 0),
        "roadmaps": int(db.scalar("SELECT count(*) AS c FROM roadmaps") or 0),
        "languages": int(stats.get("languages") or 0),
    }


def _index_counts() -> dict[str, str]:
    """A short count label per destination path, for the index page.

    Keyed by URL so the template can look one up for whatever the navigation
    table produced, without the table itself having to know about the database.
    Paths with nothing worth counting simply have no entry and render no badge.
    """
    totals = _index_totals()
    counts = {
        "/explore": f"{totals['subjects']} subjects",
        "/formulas": f"{totals['formulas']} formulas",
        "/videos": f"{int(catalog.site_stats().get('videos') or 0)} videos",
        "/books": f"{int(catalog.site_stats().get('books') or 0)} books",
        "/roadmaps": f"{totals['roadmaps']} roadmaps",
        "/practice": f"{totals['questions']} questions",
        "/dpp": f"{practice.count_dpp_sets()} sets",
        "/dpp/archive": f"{practice.count_dpp_sets()} sets",
        "/practice/questions": f"{totals['questions']} questions",
        "/programming": f"{totals['languages']} languages",
        "/practice/problems": f"{totals['problems']} problems",
        "/sheets": f"{totals['sheets']} sheets",
        "/projects": f"{totals['projects']} briefs",
        "/flashcards": f"{totals['flashcards']} cards",
        "/community": f"{int(db.scalar('SELECT count(*) AS c FROM discussions') or 0)} threads",
        "/streams": f"{totals['branches']} branches",
        "/stream": f"{totals['branches']} branches",
        "/resources/offsite": f"{library.count_resources()} links",
    }
    return counts


@router.get("/resources")
async def resources_page(request: Request):
    """The in-app resource hub.

    Until now "Resources" was a shelf of links to other websites: documentation
    hosts, open textbooks, course catalogues. That is a library catalogue, not a
    resource for a student who was told the whole course lives here, and every
    entry in it ended the session somewhere else.

    This page is now a directory of what EngineVerse itself contains, by stream,
    with the counts read from the database. The curated external shelf still
    exists at ``/resources/offsite`` for anyone who wants it, but it is labelled
    as optional reading and nothing else on the site depends on it.
    """
    # Bookmarks to the old link shelf asked for ?kind=... or ?page=N. Those
    # parameters mean nothing to the new directory, and dropping them silently
    # would land a reader on a page that is not what they bookmarked, so they
    # are forwarded to the shelf that still paginates.
    forwarded = request.url.query
    if "kind=" in forwarded or "page=" in forwarded:
        target = "/resources/offsite" + (f"?{forwarded}" if forwarded else "")
        return RedirectResponse(target, status_code=302)
    viewer = current_user(request)
    streams = hub.list_streams()
    return render(
        request, "resources.html",
        streams=streams,
        categories=_group_streams(streams),
        my_branch=viewer.branch_id if viewer else None,
        totals=_index_totals(),
        counts=_index_counts(),
        # The whole page is generated from the navigation table, so it lists the
        # same destinations, with the same labels, in the same groups as the top
        # bar and the footer. A page added to navigation.py appears here too.
        index_sections=navigation.index_sections(viewer is not None),
        offsite_total=library.count_resources(),
    )


@router.get("/resources/offsite")
async def offsite_resources_page(request: Request, kind: str | None = None, slug: str | None = None):
    """The optional external shelf, kept but marked as optional.

    These are host roots and long-lived index pages rather than deep links, and
    ``scripts/check_links.py`` verifies them in CI. Nothing in the learning
    path requires visiting any of them.
    """
    slug = deep_link_slug(slug)
    total = library.count_resources(kind=kind, slug=slug)
    pager = _pager(request, total)
    return render(
        request, "resources_offsite.html",
        resources=library.list_resources(
            kind=kind, slug=slug, limit=pager["size"], offset=(pager["page"] - 1) * pager["size"],
        ),
        kinds=library.resource_kinds(), active_kind=kind, active_slug=slug, pager=pager,
    )


@router.get("/videos")
async def videos_page(request: Request, category: str | None = None, slug: str | None = None):
    slug = deep_link_slug(slug)
    total = library.count_videos(category=category, slug=slug)
    pager = _pager(request, total)
    return render(
        request, "videos.html",
        videos=library.list_videos(
            category=category, slug=slug, limit=pager["size"], offset=(pager["page"] - 1) * pager["size"],
        ),
        categories=library.video_categories(), active_category=category, active_slug=slug, pager=pager,
    )


@router.get("/books")
async def books_page(request: Request, q: str | None = None, slug: str | None = None):
    slug = deep_link_slug(slug)
    total = library.count_books(q=q, slug=slug)
    pager = _pager(request, total)
    return render(
        request, "books.html",
        books=library.list_books(q=q, slug=slug, limit=pager["size"], offset=(pager["page"] - 1) * pager["size"]),
        q=q, active_slug=slug, pager=pager,
    )


@router.get("/formulas")
async def formulas_page(request: Request, category: str | None = None, q: str | None = None,
                        slug: str | None = None):
    slug = deep_link_slug(slug)
    # The sheet used to render every formula at once, capped by a hard-coded 300
    # against a catalogue of 365 - so 65 formulas rendered nowhere at all, and
    # the page was 1.3 MB of rendered LaTeX for the rest. It pages now, which is
    # what the other collection pages do, and ?slug= still resolves any single
    # formula to the one page that shows it.
    total = catalog.count_formulas(category=category, q=q, slug=slug)
    pager = _pager(request, total)
    return render(
        request, "formulas.html",
        formulas=catalog.list_formulas(
            category=category, q=q, slug=slug,
            limit=pager["size"], offset=(pager["page"] - 1) * pager["size"],
        ),
        categories=catalog.formula_categories(), active_category=category, q=q,
        active_slug=slug, pager=pager,
    )


@router.get("/tutor")
async def tutor_page(request: Request):
    """The AI tutor. Retrieval-grounded and labelled; see engineverse/tutor.py."""
    return render(
        request, "tutor.html",
        prompts=[
            "Explain Bernoulli's equation and when it applies",
            "What is an array and when is it faster than a linked list?",
            "How does cache locality affect my code's speed?",
            "Summarise the second law of thermodynamics",
        ],
    )


@router.get("/revision")
async def revision_page(request: Request):
    viewer = current_user(request)
    return render(
        request, "revision.html",
        stats=library.flashcard_stats(viewer.id) if viewer else None,
        due=[dict(row) for row in library.due_flashcards(viewer.id, 20)] if viewer else [],
        decks=library.decks(),
        weak=progress.weak_topics(viewer.id, 8) if viewer else [],
        heatmap=progress.heatmap(viewer.id, 182) if viewer else [],
    )


@router.get("/flashcards")
async def flashcards_page(
    request: Request, card: str | None = None, deck: str | None = None, q: str | None = None,
):
    """Public browse/search for cards; personal SM-2 scheduling stays at /revision."""
    if card:
        selected = library.flashcard_by_id(card[:160])
        if not selected:
            raise HTTPException(status_code=404, detail="Unknown flashcard")
        return render(request, "flashcards.html", selected=selected)

    deck = deck[:120].strip() if deck else None
    q = q[:120].strip() if q else None
    deck = deck or None
    q = q or None
    total = library.count_flashcards(deck=deck, q=q)
    pager = _pager(request, total)
    return render(
        request, "flashcards.html", selected=None,
        cards=library.list_flashcards(
            deck=deck, q=q, limit=pager["size"], offset=(pager["page"] - 1) * pager["size"],
        ),
        decks=library.decks(), active_deck=deck, q=q, pager=pager,
    )


@router.get("/roadmaps")
async def roadmaps_page(request: Request):
    return render(
        request, "roadmaps.html",
        roadmaps=library.list_roadmaps(),
        branches=catalog.list_branches(),
    )


@router.get("/roadmaps/{slug}")
async def roadmap_page(request: Request, slug: str):
    roadmap = library.get_roadmap(slug)
    if not roadmap:
        raise HTTPException(status_code=404, detail="Unknown roadmap")
    return render(request, "roadmap.html", roadmap=roadmap,
                  crumb_leaf=roadmap["title"],
                  nodes=library.roadmap_nodes(roadmap["id"]))


# ---------------------------------------------------------------------------
# Community
# ---------------------------------------------------------------------------

@router.get("/community")
async def community_page(request: Request, kind: str | None = None, tag: str | None = None,
                         sort: str = "recent"):
    return render(
        request, "community.html",
        threads=community.list_threads(kind=kind, tag=tag, limit=40)[0],
        kinds=community.kinds(), tags=community.tags(),
        active_kind=kind, active_tag=tag, active_sort=sort,
    )


@router.get("/community/{thread_id}")
async def thread_page(request: Request, thread_id: str):
    thread = community.get_thread(thread_id)
    if not thread:
        raise HTTPException(status_code=404, detail="Unknown discussion")
    viewer = current_user(request)
    return render(
        request, "thread.html", thread=thread,
        crumb_leaf=thread["title"],
        comments=community.comments(thread_id),
        my_votes=community.user_votes(viewer.id) if viewer else {},
    )


# ---------------------------------------------------------------------------
# Placements, portfolio, profile
# ---------------------------------------------------------------------------

@router.get("/placements")
async def placements_page(request: Request):
    viewer = current_user(request)
    return render(
        request, "placements.html",
        interview_topics=db.query(
            "SELECT s.slug AS subject_slug, s.name AS subject, count(*) AS total FROM questions q "
            "JOIN subjects s ON s.id = q.subject_id WHERE q.is_active = 1 GROUP BY s.id "
            "ORDER BY total DESC LIMIT 12"
        ),
        problems=coding.list_problems(limit=25)[0],
        projects=projects.list_projects(limit=6),
        roadmaps=library.list_roadmaps(kind="career"),
        my_stats=progress.user_stats(viewer.id) if viewer else None,
        # The interview sheets lead the coding section: a curated order beats a
        # list sorted by difficulty for someone preparing for a placement round.
        interview_sheets=coding.list_sheets(level="interview") or coding.list_sheets(),
        core_sheets=[sheet for sheet in coding.list_sheets(level="core")][:3],
    )


@router.get("/portfolio/{username}")
async def portfolio_page(request: Request, username: str):
    from engineverse import auth

    row = auth.find_by_username(username)
    if not row:
        raise HTTPException(status_code=404, detail="No such member")
    profile = auth.get_profile(row["id"]) or {}
    privacy = profile.get("privacy")
    if isinstance(privacy, str):
        import json

        try:
            privacy = json.loads(privacy)
        except ValueError:
            privacy = {}
    privacy = privacy or {}
    viewer = current_user(request)
    is_self = bool(viewer and viewer.id == row["id"])
    if privacy.get("showProgress") is False and not is_self:
        stats = None
        badges = []
        solved = []
    else:
        stats = progress.user_stats(row["id"])
        badges = progress.all_badges(row["id"])
        solved = coding.submissions_for(row["id"], limit=20)
    return render(
        request, "portfolio.html", member=row, profile=profile, stats=stats, badges=badges,
        crumb_leaf=profile.get("full_name") or row["username"],
        solved=solved, is_self=is_self,
        projects=db.query(
            "SELECT p.slug, p.title, p.difficulty, p.summary FROM bookmarks b "
            "JOIN projects p ON p.id = b.entity_id WHERE b.user_id = ? AND b.entity_type='project' LIMIT 12",
            row["id"],
        ),
    )


@router.get("/profile")
async def profile_page(request: Request):
    viewer = require_user(request)
    return render(
        request, "profile.html",
        stats=progress.user_stats(viewer.id),
        badges=progress.all_badges(viewer.id),
        heatmap=progress.heatmap(viewer.id, 182),
        bookmarks=progress.bookmarks(viewer.id),
        notes=progress.personal_notes(viewer.id),
        notifications=progress.notifications(viewer.id, 20),
        submissions=coding.submissions_for(viewer.id, limit=15),
        certificates=progress.certificates(viewer.id),
    )


@router.get("/notifications")
async def notifications_page(request: Request):
    viewer = require_user(request)
    progress.mark_notifications_read(viewer.id)
    return render(request, "notifications.html", notifications=progress.notifications(viewer.id, 60))


@router.get("/leaderboard")
async def leaderboard_page(request: Request, branch: str | None = None, period: str = "all"):
    return render(
        request, "leaderboard.html",
        rows=progress.leaderboard(branch=branch, period=period, limit=50),
        branches=catalog.list_branches(),
        active_branch=branch, active_period=period,
    )


def settings_context(viewer) -> dict:
    from engineverse.security.sessions import list_user_sessions

    enrolled = db.query_one("SELECT totp_secret FROM users WHERE id = ?", viewer.id)
    account = db.query_one("SELECT phone, phone_verified FROM users WHERE id = ?", viewer.id) or {}
    return {
        "universities": catalog.list_universities(),
        "colleges": catalog.list_colleges(),
        "branches": catalog.list_branches(),
        "semesters": catalog.list_semesters(),
        "sessions": list_user_sessions(viewer.session_id and viewer.id),
        "plans": db.query("SELECT * FROM plans WHERE is_active = 1 ORDER BY price_cents"),
        "subscription": db.query_one(
            "SELECT s.*, p.name AS plan_name FROM subscriptions s JOIN plans p ON p.id = s.plan_id "
            "WHERE s.user_id = ? ORDER BY s.started_at DESC LIMIT 1", viewer.id,
        ),
        "mfa_enabled": bool(enrolled and enrolled.get("totp_secret")),
        "phone": account.get("phone") or "",
        "phone_verified": bool(account.get("phone_verified")),
        "sms_available": get_settings().sms_configured,
        "login_otp_required": get_settings().login_otp_required,
    }


@router.get("/settings")
async def settings_page(request: Request):
    viewer = require_user(request)
    return render(request, "settings.html", **settings_context(viewer))


@router.get("/certificates/{verify_id}")
async def certificate_page(request: Request, verify_id: str):
    bundle = progress.verify_certificate(verify_id)
    if not bundle:
        raise HTTPException(status_code=404, detail="No certificate with that id")
    # verify_certificate returns {"certificate", "holder", "branch", "meta"};
    # the template reads one flat record, so merge them here.
    holder = bundle.get("holder") or {}
    branch = bundle.get("branch") or {}
    record = dict(bundle["certificate"])
    record["full_name"] = holder.get("full_name")
    record["username"] = holder.get("username")
    record["branch"] = branch.get("name")
    record["tier_label"] = certificates.TIER_LABELS.get(record.get("tier") or "bronze", "Bronze")
    record["issuer"] = certificates.issuer_name()
    return render(request, "certificate.html", certificate=record, meta=bundle.get("meta") or {},
                  crumb_leaf=verify_id)


# ---------------------------------------------------------------------------
# Admin
# ---------------------------------------------------------------------------

@router.get("/admin")
async def admin_page(request: Request):
    """Render only the admin data the signed-in role is allowed to inspect."""
    viewer = require_user(request)
    permissions = {
        "users_manage": rbac.can(viewer.role, "users.manage"),
        "users_roles": rbac.can(viewer.role, "users.roles"),
        "community_moderate": rbac.can(viewer.role, "community.moderate"),
        "content_review": rbac.can(viewer.role, "content.update") or rbac.can(viewer.role, "content.publish"),
        "analytics_view": rbac.can(viewer.role, "analytics.view"),
        "settings_manage": rbac.can(viewer.role, "settings.manage"),
    }
    if not any(permissions.values()):
        raise HTTPException(status_code=403, detail="Staff only")

    can_view_users = permissions["users_manage"] or permissions["users_roles"]
    can_view_audit = permissions["users_manage"] or permissions["settings_manage"]
    stats = catalog.site_stats()
    if permissions["users_manage"] or permissions["analytics_view"]:
        stats["users"] = int(db.scalar("SELECT count(*) FROM users WHERE deleted_at IS NULL") or 0)

    return render(
        request, "admin.html",
        permissions=permissions,
        role_options=rbac.ROLES,
        stats=stats,
        users=db.query(
            "SELECT u.id, u.email, u.username, u.role, u.status, u.created_at, p.full_name, "
            "CASE WHEN u.totp_secret IS NULL OR u.totp_secret = '' THEN 0 ELSE 1 END AS mfa_enrolled "
            "FROM users u LEFT JOIN profiles p ON p.user_id = u.id "
            "WHERE u.deleted_at IS NULL ORDER BY u.created_at DESC LIMIT 100"
        ) if can_view_users else [],
        reports=community.open_reports(30) if permissions["community_moderate"] else [],
        # Audit payloads can hold security metadata; the UI needs only action
        # names and timestamps, and only user/security administrators see them.
        recent_audit=db.query(
            "SELECT action, created_at FROM audit_logs ORDER BY created_at DESC LIMIT 40"
        ) if can_view_audit else [],
        pending_topics=db.query(
            "SELECT id, title, accuracy_state, updated_at FROM topics WHERE accuracy_state <> 'reviewed' "
            "ORDER BY updated_at DESC LIMIT 30"
        ) if permissions["content_review"] else [],
        config=brand.all_config() if permissions["settings_manage"] else {},
        searches=db.query(
            "SELECT query, count(*) AS c FROM search_log GROUP BY query ORDER BY c DESC LIMIT 20"
        ) if permissions["analytics_view"] and db.table_exists("search_log") else [],
    )


@router.get("/onboarding")
async def onboarding_page(request: Request):
    viewer = require_user(request)
    return render(
        request, "onboarding.html",
        universities=catalog.list_universities(),
        colleges=catalog.list_colleges(),
        branches=catalog.list_branches(),
        semesters=catalog.list_semesters(),
    )


@router.get("/about")
async def about_page(request: Request):
    return render(request, "about.html", stats=catalog.site_stats())


@router.get("/sitemap.xml", include_in_schema=False)
async def sitemap():
    from fastapi.responses import Response

    # Canonical URLs come from deployment configuration, never the untrusted
    # Host header supplied with this request.
    base = get_settings().site_url.rstrip("/")
    # Derived from the navigation table rather than written out here. This list
    # used to be a fourth copy of the site's pages and had fallen behind: it
    # omitted /sheets - a top-bar item - and every sheet slug, plus /stream,
    # /streams, /install and /search. A page added to navigation.py is now in the
    # sitemap automatically, and one removed from it cannot leave a stale entry.
    #
    # The full list is published even where sign-in is compulsory: robots.txt
    # already disallows everything in that mode, and a sitemap describing content
    # that becomes public the moment an operator sets ENGINEVERSE_SIGNIN=optional
    # is more useful than one that has to be regenerated.
    urls = list(navigation.indexable_paths())

    # Include the later pages of every paginated public shelf. Dated DPP URLs
    # and content slugs below remain direct links; these pages also let a crawler
    # discover every resource, video, book, subject and practice question.
    def add_page_urls(path: str, total: int, page_size: int = LIBRARY_PAGE_SIZE) -> None:
        page_count = max(1, (max(0, int(total)) + page_size - 1) // page_size)
        urls.extend(f"{path}?page={page}" for page in range(2, page_count + 1))

    add_page_urls("/explore", catalog.count_subjects())
    add_page_urls("/practice/questions", int(db.scalar(
        "SELECT count(*) FROM questions WHERE is_active = 1") or 0))
    add_page_urls("/dpp/archive", practice.count_dpp_sets(), DPP_ARCHIVE_PAGE_SIZE)
    add_page_urls("/resources", library.count_resources())
    add_page_urls("/videos", library.count_videos())
    add_page_urls("/books", library.count_books())
    add_page_urls("/flashcards", library.count_flashcards())

    urls += [
        "/flashcards?" + urlencode({"card": row["id"]})
        for row in db.query("SELECT id FROM flashcards ORDER BY id")
    ]
    urls += [f"/dpp/{row['date']}" for row in practice.list_dpp_sets(
        limit=practice.count_dpp_sets())]
    urls += [f"/branches/{row['slug']}" for row in catalog.list_branches()]
    urls += [f"/subjects/{row['slug']}" for row in db.query(
        "SELECT slug FROM subjects WHERE status = 'published' ORDER BY slug")]
    urls += [f"/topics/{row['slug']}" for row in db.query(
        "SELECT slug FROM topics WHERE status = 'published' ORDER BY slug")]
    urls += [f"/sheets/{row['slug']}" for row in coding.list_sheets(limit=200)]
    urls += [f"/programming/{row['slug']}" for row in coding.list_languages()]
    urls += [f"/roadmaps/{row['slug']}" for row in library.list_roadmaps()]
    urls += [f"/projects/{row['slug']}" for row in db.query(
        "SELECT slug FROM projects WHERE status = 'published' ORDER BY order_index, title")]
    urls += [f"/practice/problems/{row['slug']}" for row in db.query(
        "SELECT slug FROM coding_problems ORDER BY title")]

    today = datetime.now(timezone.utc).date().isoformat()
    body = ['<?xml version="1.0" encoding="UTF-8"?>',
            '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">']
    for url in urls:
        body.append(f"<url><loc>{escape(base + url)}</loc><lastmod>{today}</lastmod></url>")
    body.append("</urlset>")
    return Response("\n".join(body), media_type="application/xml")


@router.get("/offline")
async def offline_page(request: Request):
    return render(request, "offline.html")


@router.get("/install")
async def install_page(request: Request):
    return render(request, "install.html")


@router.get("/terms")
async def terms_page(request: Request):
    return render(request, "legal.html", which="terms")


@router.get("/privacy")
async def privacy_page(request: Request):
    return render(request, "legal.html", which="privacy")


@router.get("/streaks")
async def streaks_page(request: Request):
    viewer = current_user(request)
    return render(
        request, "streaks.html",
        mine=progress.heatmap(viewer.id, 182) if viewer else [],
        stats=progress.user_stats(viewer.id) if viewer else None,
    )


@router.get("/today")
async def today_page(request: Request):
    """A single 'what should I do today' page - the daily entry point."""
    viewer = require_user(request)
    today = (datetime.now(timezone.utc)).date()
    yesterday = today - timedelta(days=1)
    return render(
        request, "today.html",
        dpp=practice.dpp_with_context(),
        cards=[dict(row) for row in library.due_flashcards(viewer.id, 20)],
        next_topics=recommend.next_topics_for(viewer.id, 5),
        retry=recommend.retry_plan(viewer.id),
        yesterday_count=int(db.scalar(
            "SELECT count(*) AS c FROM activity WHERE user_id = ? AND day = ?", viewer.id, yesterday.isoformat()
        ) or 0),
    )
