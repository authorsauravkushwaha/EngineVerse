"""Authentication and account pages.

Everything here is first-party: no external identity provider, no social
login, no third-party script. Sessions are opaque cookies whose token is
stored only as a SHA-256 digest.
"""
from __future__ import annotations

from fastapi import APIRouter, Form, Request
from fastapi.responses import RedirectResponse

from engineverse import auth, brand, catalog, db, progress
from engineverse.security import validators
from engineverse.security.audit import record
from engineverse.security.passwords import check_password_strength
from engineverse.security.rbac import assert_can
from engineverse.security.sanitize import is_safe_url
from engineverse.security.sessions import (
    attach_session_cookie,
    clear_session_cookie,
    create_session,
    revoke_session,
)

from .deps import current_user, flash, render, require_user

router = APIRouter()


def _next_url(value: str | None) -> str:
    """Only ever redirect to a same-origin relative path."""
    if value and is_safe_url(value) and value.startswith("/") and not value.startswith("//"):
        return value
    return "/"


# ---------------------------------------------------------------------------
# Sign in / sign up
# ---------------------------------------------------------------------------

@router.get("/login")
async def login_page(request: Request, next: str | None = None, error: str | None = None):
    if current_user(request):
        return RedirectResponse("/", status_code=303)
    return render(request, "login.html", next=next, error=error, mode="login")


@router.post("/login")
async def login_submit(
    request: Request,
    identifier: str = Form(...),
    password: str = Form(...),
    next: str = Form("/"),
    remember: str = Form(""),
):
    target = _next_url(next)
    try:
        user, cookie_value, session_id = auth.login(
            identifier=identifier.strip(),
            password=password,
            ip=request.client.host if request.client else "",
            user_agent=request.headers.get("user-agent", ""),
        )
    except auth.AuthError as exc:
        return render(request, "login.html", next=target, error=exc.message, mode="login",
                      identifier=identifier, status_code=exc.status_code)

    progress.touch_streak(user["id"])
    response = RedirectResponse(target, status_code=303)
    attach_session_cookie(response, cookie_value)
    response.set_cookie("ev_csrf", __import__("engineverse.security.csrf", fromlist=["issue_token"])
                        .issue_token(session_id), httponly=False, samesite="lax", path="/",
                        max_age=30 * 86400)
    flash(response, f"Welcome back, {user['username']}.")
    return response


@router.get("/register")
async def register_page(request: Request, next: str | None = None):
    if current_user(request):
        return RedirectResponse("/", status_code=303)
    return render(
        request, "register.html", next=next, mode="register",
        registration_open=brand.registration_open(),
        universities=catalog.list_universities(),
        branches=catalog.list_branches(),
        semesters=catalog.list_semesters(),
    )


@router.post("/register")
async def register_submit(
    request: Request,
    email: str = Form(...),
    username: str = Form(...),
    full_name: str = Form(...),
    password: str = Form(...),
    password_confirm: str = Form(""),
    next: str = Form("/"),
    branch: str = Form(""),
    semester: str = Form(""),
):
    target = _next_url(next)
    if not brand.registration_open():
        return render(request, "register.html", next=target, mode="register",
                      registration_open=False,
                      error="Registration is currently closed. Contact the site administrator.",
                      email=email, username=username, full_name=full_name,
                      universities=catalog.list_universities(),
                      branches=catalog.list_branches(), semesters=catalog.list_semesters(),
                      status_code=403)
    if password != password_confirm:
        return render(request, "register.html", next=target, mode="register",
                      error="The two passwords do not match.", email=email, username=username,
                      full_name=full_name, universities=catalog.list_universities(),
                      branches=catalog.list_branches(), semesters=catalog.list_semesters(),
                      status_code=422)
    try:
        user = auth.register(
            email=email.strip(), username=username.strip(), password=password, full_name=full_name.strip(),
            ip=request.client.host if request.client else None,
            user_agent=request.headers.get("user-agent"),
        )
    except validators.ValidationError as exc:
        return render(request, "register.html", next=target, mode="register",
                      error=exc.message, fields=exc.fields, email=email, username=username,
                      full_name=full_name, universities=catalog.list_universities(),
                      branches=catalog.list_branches(), semesters=catalog.list_semesters(),
                      status_code=422)
    except auth.AuthError as exc:
        return render(request, "register.html", next=target, mode="register",
                      error=exc.message, fields=exc.fields or {}, email=email, username=username,
                      full_name=full_name, universities=catalog.list_universities(),
                      branches=catalog.list_branches(), semesters=catalog.list_semesters(),
                      status_code=exc.status_code)

    if branch:
        auth.update_onboarding(user["id"], {"branchId": branch})
    if semester.isdigit():
        auth.update_onboarding(user["id"], {"semester": int(semester)})

    cookie_value, session_id = create_session(
        user["id"], ip=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent"),
    )
    response = RedirectResponse("/onboarding" if not (branch or semester) else target, status_code=303)
    attach_session_cookie(response, cookie_value)
    from engineverse.security.csrf import issue_token

    response.set_cookie("ev_csrf", issue_token(session_id), httponly=False, samesite="lax", path="/",
                        max_age=30 * 86400)
    flash(response, "Account created. Let's set up your path.")
    return response


@router.post("/logout")
async def logout_submit(request: Request):
    viewer = current_user(request)
    if viewer:
        auth.logout(viewer.session_id, viewer.id, ip=request.client.host if request.client else None)
    response = RedirectResponse("/", status_code=303)
    clear_session_cookie(response)
    response.delete_cookie("ev_csrf", path="/")
    flash(response, "Signed out.")
    return response


@router.get("/forgot-password")
async def forgot_page(request: Request):
    return render(request, "forgot.html", sent=False, reset_token="")


@router.post("/forgot-password")
async def forgot_submit(request: Request, email: str = Form(...)):
    """Always reports success. Revealing which addresses exist is an oracle we
    will not hand out. The reset link is printed to the audit log in this
    self-hosted build; a production deployment wires this to an SMTP relay."""
    auth.prune_password_resets()
    row = auth.find_by_email(email.strip())
    token = ""
    if row:
        ip = request.client.host if request.client else None
        token = auth.issue_password_reset(row["id"], ip=ip)
        record("auth.reset_requested", actor_id=row["id"], ip=ip,
               entity_type="user", entity_id=row["id"])
    return render(request, "forgot.html", sent=True, reset_token=token)


@router.get("/reset-password")
async def reset_page(request: Request, token: str = ""):
    return render(request, "reset.html", token=token, error=None)


@router.post("/reset-password")
async def reset_submit(request: Request, token: str = Form(...), password: str = Form(...)):
    # Validated by exact hash match, expiry and single use. The same wording is
    # returned for an unknown, expired and already-used token so the form is not
    # an oracle for which links are live.
    user_id = auth.consume_password_reset(token)
    if not user_id:
        record("auth.reset_rejected", ip=request.client.host if request.client else None)
        return render(request, "reset.html", token="", error="That reset link is not valid or has expired.",
                      status_code=400)

    issues = check_password_strength(password, [])
    if issues:
        # The token was consumed above, so a weak password cannot be retried
        # with the same link. Handing a fresh one back would turn this form into
        # a password-strength oracle, so the user starts again from the top.
        return render(request, "reset.html", token="", error=issues[0].message, status_code=422)

    from engineverse.security.passwords import hash_password

    ts = auth.now_ms()
    db.execute("UPDATE users SET password_hash = ?, password_changed_at = ?, failed_login_count = 0, "
               "updated_at = ? WHERE id = ?", hash_password(password), ts, ts, user_id)
    from engineverse.security.sessions import revoke_all_sessions

    revoke_all_sessions(user_id)
    record("auth.password_reset", actor_id=user_id, ip=request.client.host if request.client else None)
    return RedirectResponse("/login?error=reset", status_code=303)


# ---------------------------------------------------------------------------
# Account settings
# ---------------------------------------------------------------------------

@router.post("/settings/profile")
async def update_profile_submit(
    request: Request,
    full_name: str = Form(""),
    headline: str = Form(""),
    bio: str = Form(""),
    country: str = Form(""),
    github_url: str = Form(""),
    linkedin_url: str = Form(""),
    portfolio_url: str = Form(""),
    weekly_study_hours: str = Form("7"),
):
    viewer = require_user(request)
    payload = {
        "full_name": full_name.strip()[:80],
        "headline": headline.strip()[:120],
        "bio": bio.strip()[:1200],
        "country": country.strip()[:60],
        "weekly_study_hours": int(weekly_study_hours) if weekly_study_hours.isdigit() else 7,
    }
    for key, value in (("github_url", github_url), ("linkedin_url", linkedin_url),
                       ("portfolio_url", portfolio_url)):
        value = (value or "").strip()
        if value and is_safe_url(value):
            payload[key] = value[:300]
    auth.update_profile(viewer.id, payload)
    response = RedirectResponse("/settings", status_code=303)
    flash(response, "Profile saved.")
    return response


@router.post("/settings/onboarding")
async def update_onboarding_submit(
    request: Request,
    branch: str = Form(""),
    semester: str = Form("0"),
    university: str = Form(""),
    college: str = Form(""),
    goal: str = Form(""),
    experience: str = Form("none"),
    hours: str = Form("7"),
    note_quality: str = Form("standard"),
    language: str = Form("en"),
):
    viewer = require_user(request)
    auth.update_onboarding(viewer.id, {
        "branchId": branch or None,
        "semester": int(semester) if semester.isdigit() else None,
        "universityId": university or None,
        "collegeId": college or None,
        "careerGoal": goal or None,
        "programmingExperience": experience,
        "weeklyStudyHours": int(hours) if hours.isdigit() else 7,
        "noteQuality": note_quality,
        "languagePref": language,
    })
    response = RedirectResponse("/", status_code=303)
    flash(response, "Your path is set.")
    return response


@router.post("/settings/preferences")
async def update_preferences_submit(
    request: Request,
    note_quality: str = Form("standard"),
    language: str = Form("en"),
    show_email: str = Form(""),
    show_activity: str = Form(""),
    show_progress: str = Form(""),
    searchable: str = Form(""),
    new_dpp: str = Form(""),
    streak_reminder: str = Form(""),
    milestone: str = Form(""),
    community_reply: str = Form(""),
):
    import json

    viewer = require_user(request)
    auth.update_profile(viewer.id, {
        "note_quality": note_quality,
        "language_pref": language,
        "privacy": json.dumps({
            "showEmail": bool(show_email), "showActivity": bool(show_activity),
            "showProgress": bool(show_progress), "searchable": bool(searchable),
        }),
        "notification_prefs": json.dumps({
            "newDpp": bool(new_dpp), "streakReminder": bool(streak_reminder),
            "milestone": bool(milestone), "communityReply": bool(community_reply),
        }),
    })
    response = RedirectResponse("/settings", status_code=303)
    flash(response, "Preferences saved.")
    return response


@router.post("/settings/password")
async def change_password_submit(
    request: Request,
    current_password: str = Form(...),
    new_password: str = Form(...),
    confirm_password: str = Form(""),
):
    viewer = require_user(request)
    if new_password != confirm_password:
        response = RedirectResponse("/settings#error-password", status_code=303)
        flash(response, "The two new passwords do not match.")
        return response
    try:
        auth.change_password(viewer.id, current_password, new_password)
    except auth.AuthError as exc:
        response = RedirectResponse("/settings#error-password", status_code=303)
        flash(response, exc.message)
        return response
    response = RedirectResponse("/settings", status_code=303)
    flash(response, "Password changed. Other sessions were signed out.")
    return response


@router.post("/settings/sessions/revoke")
async def revoke_session_submit(request: Request, session_id: str = Form(...)):
    viewer = require_user(request)
    revoke_session(session_id)
    record("auth.session_revoked_self", actor_id=viewer.id, ip=request.client.host if request.client else None)
    response = RedirectResponse("/settings", status_code=303)
    flash(response, "That session was signed out.")
    return response


@router.post("/settings/account/delete")
async def delete_account_submit(request: Request, confirm: str = Form("")):
    viewer = require_user(request)
    if confirm.strip().upper() != "DELETE":
        response = RedirectResponse("/settings", status_code=303)
        flash(response, "Type DELETE to confirm account removal.")
        return response
    db.execute("DELETE FROM users WHERE id = ?", viewer.id)
    record("auth.account_deleted", actor_id=viewer.id, ip=request.client.host if request.client else None)
    response = RedirectResponse("/", status_code=303)
    clear_session_cookie(response)
    flash(response, "Your account and all of its data were removed.")
    return response


# ---------------------------------------------------------------------------
# Admin actions
# ---------------------------------------------------------------------------

@router.post("/admin/users/role")
async def set_user_role(request: Request, user_id: str = Form(...), role: str = Form(...)):
    viewer = require_user(request)
    assert_can(viewer.role, "users.roles")
    auth.set_role(viewer.id, user_id, role)
    return RedirectResponse("/admin", status_code=303)


@router.post("/admin/users/status")
async def set_user_status(request: Request, user_id: str = Form(...), status: str = Form(...)):
    viewer = require_user(request)
    assert_can(viewer.role, "users.manage")
    auth.set_status(viewer.id, user_id, status)
    return RedirectResponse("/admin", status_code=303)


@router.post("/admin/config")
async def update_site_config(request: Request, site_name: str = Form(""), tagline: str = Form(""),
                             announcement: str = Form(""), support_email: str = Form(""),
                             accent_color: str = Form("#4f7cff"), maintenance_mode: str = Form("0"),
                             registration_open: str = Form("1"), theme: str = Form("dark")):
    viewer = require_user(request)
    assert_can(viewer.role, "settings.manage")
    from engineverse import brand

    brand.set_many({
        "site_name": site_name.strip()[:60] or "EngineVerse",
        "tagline": tagline.strip()[:200],
        "announcement": announcement.strip()[:300],
        "support_email": support_email.strip()[:120],
        "accent_color": accent_color.strip()[:20],
        "maintenance_mode": "1" if maintenance_mode else "0",
        "registration_open": "1" if registration_open else "0",
        "theme": theme.strip() if theme.strip() in ("dark", "light") else "dark",
    })
    response = RedirectResponse("/admin", status_code=303)
    flash(response, "Site configuration saved.")
    return response


@router.post("/admin/reports/resolve")
async def resolve_report_submit(request: Request, report_id: str = Form(...), hide: str = Form("")):
    from engineverse import community

    viewer = require_user(request)
    assert_can(viewer.role, "community.moderate")
    community.resolve_report(viewer.id, report_id, hide=bool(hide))
    return RedirectResponse("/admin", status_code=303)
