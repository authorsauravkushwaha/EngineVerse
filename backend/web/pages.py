"""Server-rendered pages.

Every page works without JavaScript. Enhancement lives in ``static/js/app.js``
and talks to the JSON API under ``/api``.
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, HTTPException, Request

from engineverse import (
    brand,
    catalog,
    coding,
    community,
    db,
    library,
    practice,
    progress,
    projects,
    recommend,
    search,
)

from .deps import current_user, render, require_user

router = APIRouter()


# ---------------------------------------------------------------------------
# Home and exploration
# ---------------------------------------------------------------------------

@router.get("/")
async def home(request: Request):
    viewer = current_user(request)
    context = {
        "site": catalog.site_stats(),
        "branches": catalog.branch_groups(),
        "popular_subjects": catalog.popular_subjects(8),
        "trending": search.trending(8),
    }
    if viewer:
        context["dashboard"] = recommend.dashboard(viewer.id)
        context["continue_learning"] = progress.continue_learning(viewer.id, 6)
        context["dpp"] = practice.dpp_with_context()
        return render(request, "dashboard.html", **context)
    context["featured_topics"] = db.query(
        "SELECT t.slug, t.title, t.summary, t.difficulty, t.est_minutes, s.name AS subject, s.color AS color "
        "FROM topics t JOIN subjects s ON s.id = t.subject_id WHERE t.status='published' "
        "ORDER BY t.view_count DESC, t.order_index LIMIT 9"
    )
    context["sample_problems"] = coding.list_problems(limit=6)
    context["sample_projects"] = projects.list_projects(limit=3)
    return render(request, "home.html", **context)


@router.get("/explore")
async def explore(request: Request, branch: str | None = None, semester: str | None = None, q: str | None = None):
    return render(
        request, "explore.html",
        branches=catalog.branch_groups(),
        subjects=catalog.list_subjects(branch=branch, semester=int(semester) if semester and semester.isdigit() else None, q=q, limit=200),
        semesters=catalog.list_semesters(),
        active_branch=branch,
        active_semester=semester,
        active_q=q,
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
    return render(
        request, "branch.html", branch=branch,
        subjects=catalog.list_subjects(branch=slug, limit=200),
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
    if viewer:
        progress.mark_topic_viewed(viewer.id, topic["id"])
    return render(
        request, "topic.html", topic=topic,
        note=note,
        sections=catalog.sections_for_note(note["id"]) if note else [],
        diagrams=catalog.diagrams_for_topic(topic["id"]),
        formulas=catalog.formulas_for_topic(topic["id"]),
        questions=practice.questions_for_topic(topic["id"], 8),
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
        sets=practice.list_dpp_sets(30),
        kinds=practice.question_kinds(),
        questions=practice.list_questions(limit=20)[0],
    )


@router.get("/dpp")
async def dpp_today(request: Request):
    return render(
        request, "dpp.html", dpp=practice.dpp_with_context(),
        sets=practice.list_dpp_sets(14), active_date=None,
    )


@router.get("/dpp/{date}")
async def dpp_day(request: Request, date: str):
    payload = practice.dpp_with_context(date)
    if not payload:
        raise HTTPException(status_code=404, detail="No practice set for that date")
    return render(request, "dpp.html", dpp=payload, sets=practice.list_dpp_sets(14), active_date=date)


@router.get("/practice/questions")
async def question_bank(request: Request, subject: str | None = None, kind: str | None = None,
                        difficulty: str | None = None):
    return render(
        request, "question_bank.html",
        questions=practice.list_questions(subject_id=subject, kind=kind, difficulty=difficulty, limit=60)[0],
        kinds=practice.question_kinds(),
        subjects=catalog.list_subjects(limit=200),
        active_subject=subject, active_kind=kind, active_difficulty=difficulty,
    )


@router.get("/mistakes")
async def mistakes_page(request: Request):
    viewer = require_user(request)
    return render(
        request, "mistakes.html",
        mistakes=practice.mistake_notebook(viewer.id, limit=50),
        retry=recommend.retry_plan(viewer.id),
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
    )


@router.get("/programming/{language}")
async def language_page(request: Request, language: str):
    lang = coding.language_by_slug(language)
    if not lang:
        raise HTTPException(status_code=404, detail="Unknown language")
    return render(
        request, "language.html", language=lang,
        modules=coding.modules_for_language(lang["id"]),
        problems=coding.list_problems(limit=30)[0],
    )


@router.get("/practice/problems")
async def problem_list(request: Request, difficulty: str | None = None, topic: str | None = None,
                       q: str | None = None):
    viewer = current_user(request)
    return render(
        request, "problems.html",
        problems=coding.list_problems(difficulty=difficulty, topic=topic, q=q, limit=100)[0],
        topics=coding.problem_topics(),
        solved=coding.solved_problem_ids(viewer.id) if viewer else set(),
        active_difficulty=difficulty, active_topic=topic, active_q=q,
    )


@router.get("/practice/problems/{slug}")
async def problem_page(request: Request, slug: str):
    problem = coding.get_problem(slug)
    if not problem:
        raise HTTPException(status_code=404, detail="Unknown problem")
    viewer = current_user(request)
    return render(
        request, "problem.html", problem=problem,
        stubs=coding.stubs_for(problem["id"]),
        stub_map={row["slug"]: {"stub": row["stub"], "signature": row["signature"]}
                  for row in coding.stubs_for(problem["id"])},
        samples=coding.testcases_for(problem["id"], samples_only=True),
        languages=coding.list_languages(),
        submissions=coding.submissions_for(viewer.id, problem["id"], 10) if viewer else [],
        saved=coding.saved_code(viewer.id, problem["id"], "python") if viewer else None,
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
    )


@router.get("/projects/{slug}")
async def project_page(request: Request, slug: str):
    project = projects.get_project(slug)
    if not project:
        raise HTTPException(status_code=404, detail="Unknown project")
    viewer = current_user(request)
    if viewer:
        projects.record_build(viewer.id, project["id"])
    return render(
        request, "project.html", project=project,
        steps=projects.steps(project["id"]),
        resources=projects.resources(project["id"]),
        similar=projects.suggested_for(viewer.id if viewer else None, 4),
    )


# ---------------------------------------------------------------------------
# Library and revision
# ---------------------------------------------------------------------------

@router.get("/resources")
async def resources_page(request: Request, kind: str | None = None):
    return render(
        request, "resources.html",
        resources=library.list_resources(kind=kind, limit=120),
        kinds=library.resource_kinds(), active_kind=kind,
    )


@router.get("/videos")
async def videos_page(request: Request, category: str | None = None):
    return render(
        request, "videos.html",
        videos=library.list_videos(category=category, limit=120),
        categories=library.video_categories(), active_category=category,
    )


@router.get("/books")
async def books_page(request: Request, q: str | None = None):
    return render(request, "books.html", books=library.list_books(q=q, limit=120), q=q)


@router.get("/formulas")
async def formulas_page(request: Request, category: str | None = None, q: str | None = None):
    return render(
        request, "formulas.html",
        formulas=catalog.list_formulas(category=category, q=q, limit=300),
        categories=catalog.formula_categories(), active_category=category, q=q,
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
    return render(request, "roadmap.html", roadmap=roadmap, nodes=library.roadmap_nodes(roadmap["id"]))


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


@router.get("/settings")
async def settings_page(request: Request):
    from engineverse.security.sessions import list_user_sessions

    viewer = require_user(request)
    return render(
        request, "settings.html",
        universities=catalog.list_universities(),
        colleges=catalog.list_colleges(),
        branches=catalog.list_branches(),
        semesters=catalog.list_semesters(),
        sessions=list_user_sessions(viewer.session_id and viewer.id),
        plans=db.query("SELECT * FROM plans WHERE is_active = 1 ORDER BY price_cents"),
        subscription=db.query_one(
            "SELECT s.*, p.name AS plan_name FROM subscriptions s JOIN plans p ON p.id = s.plan_id "
            "WHERE s.user_id = ? ORDER BY s.started_at DESC LIMIT 1", viewer.id,
        ),
    )


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
    return render(request, "certificate.html", certificate=record, meta=bundle.get("meta") or {})


# ---------------------------------------------------------------------------
# Admin
# ---------------------------------------------------------------------------

@router.get("/admin")
async def admin_page(request: Request):
    viewer = require_user(request)
    if not viewer.is_staff:
        raise HTTPException(status_code=403, detail="Staff only")
    return render(
        request, "admin.html",
        stats=catalog.site_stats(),
        users=db.query(
            "SELECT u.id, u.email, u.username, u.role, u.status, u.created_at, p.full_name "
            "FROM users u LEFT JOIN profiles p ON p.user_id = u.id ORDER BY u.created_at DESC LIMIT 100"
        ),
        reports=community.open_reports(30),
        recent_audit=db.query(
            "SELECT * FROM audit_logs ORDER BY created_at DESC LIMIT 40"
        ),
        pending_topics=db.query(
            "SELECT id, title, accuracy_state, updated_at FROM topics WHERE accuracy_state <> 'reviewed' "
            "ORDER BY updated_at DESC LIMIT 30"
        ),
        config=brand.all_config(),
        searches=db.query(
            "SELECT query, count(*) AS c FROM search_log GROUP BY query ORDER BY c DESC LIMIT 20"
        ) if db.table_count("search_log") else [],
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
async def sitemap(request: Request):
    from fastapi.responses import Response

    base = str(request.base_url).rstrip("/")
    urls = ["/", "/explore", "/practice", "/programming", "/projects", "/resources", "/videos", "/books",
            "/formulas", "/roadmaps", "/community", "/placements", "/leaderboard"]
    urls += [f"/branches/{row['slug']}" for row in catalog.list_branches()]
    urls += [f"/subjects/{row['slug']}" for row in catalog.list_subjects(limit=400)]
    urls += [f"/topics/{row['slug']}" for row in db.query(
        "SELECT slug FROM topics WHERE status='published' LIMIT 2000")]
    urls += [f"/projects/{row['slug']}" for row in projects.list_projects(limit=400)]
    urls += [f"/practice/problems/{row['slug']}" for row in coding.list_problems(limit=400)[0]]
    today = datetime.now(timezone.utc).date().isoformat()
    body = ['<?xml version="1.0" encoding="UTF-8"?>',
            '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">']
    for url in urls:
        body.append(f"<url><loc>{base}{url}</loc><lastmod>{today}</lastmod></url>")
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
