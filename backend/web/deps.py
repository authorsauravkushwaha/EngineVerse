"""Request-scoped helpers shared by the page and API routers."""
from __future__ import annotations

import json
import os
from dataclasses import dataclass
from urllib.parse import quote, unquote
from datetime import datetime, timezone
from typing import Any

from fastapi import HTTPException, Request
from fastapi.templating import Jinja2Templates

from engineverse import auth, brand, db, markdown, progress
from engineverse.config import get_settings
from engineverse.security import csrf
from engineverse.security.rbac import is_staff
from engineverse.security.sessions import SESSION_COOKIE, session_from_request

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TEMPLATES_DIR = os.path.join(_ROOT, "templates")
STATIC_DIR = os.path.join(_ROOT, "static")

templates = Jinja2Templates(directory=TEMPLATES_DIR)
templates.env.autoescape = True
templates.env.trim_blocks = True
templates.env.lstrip_blocks = True


# ---------------------------------------------------------------------------
# The signed-in viewer, flattened for templates
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class Viewer:
    id: str
    username: str
    email: str
    role: str
    full_name: str
    headline: str
    avatar_seed: str
    branch_id: str | None
    semester_id: int | None
    note_quality: str
    session_id: str
    current_streak: int
    total_xp: int
    level: int
    email_verified: int = 0

    @property
    def is_staff(self) -> bool:
        return is_staff(self.role)

    @property
    def initial(self) -> str:
        return (self.full_name or self.username or "?")[:1].upper()


def _viewer(current: auth.CurrentUser) -> Viewer:
    profile = current.profile
    return Viewer(
        id=current.user.id,
        username=current.user.username,
        email=current.user.email,
        role=current.user.role,
        full_name=profile.get("full_name") or current.user.username,
        headline=profile.get("headline") or "",
        avatar_seed=profile.get("avatar_seed") or current.user.username,
        branch_id=profile.get("branch_id"),
        semester_id=profile.get("semester_id"),
        note_quality=profile.get("note_quality") or "standard",
        session_id=current.session_id,
        current_streak=int(current.streak.get("current_streak") or 0),
        total_xp=int(current.streak.get("total_xp") or 0),
        level=int(current.streak.get("level") or 1),
        email_verified=int(current.user.email_verified or 0),
    )


def current_user(request: Request) -> Viewer | None:
    """Resolves the signed-in viewer from the session cookie, or None."""
    cached = getattr(request.state, "ev_user", "__unset__")
    if cached != "__unset__":
        return cached
    viewer = None
    current = auth.current_user_from_session(session_from_request(request))
    if current is not None:
        viewer = _viewer(current)
    request.state.ev_user = viewer
    return viewer


def require_user(request: Request) -> Viewer:
    viewer = current_user(request)
    if viewer is None:
        raise HTTPException(status_code=401, detail="Sign in to continue.")
    return viewer


def session_id(request: Request) -> str:
    viewer = current_user(request)
    return viewer.session_id if viewer else ""


# ---------------------------------------------------------------------------
# Template filters
# ---------------------------------------------------------------------------

def _from_json(value: Any, fallback: Any) -> Any:
    if isinstance(value, (list, dict)):
        return value
    if not value:
        return fallback
    try:
        return json.loads(value)
    except (TypeError, ValueError):
        return fallback


def _title_case(value: str) -> str:
    return (value or "").replace("-", " ").replace("_", " ").strip().title()


def _ago(ms: int | None) -> str:
    if not ms:
        return ""
    seconds = max(0, int(datetime.now(timezone.utc).timestamp() - int(ms) / 1000))
    if seconds < 60:
        return "just now"
    if seconds < 3600:
        return f"{seconds // 60}m ago"
    if seconds < 86400:
        return f"{seconds // 3600}h ago"
    if seconds < 604800:
        return f"{seconds // 86400}d ago"
    if seconds < 2592000:
        return f"{seconds // 604800}w ago"
    return f"{seconds // 2592000}mo ago"


def register_filters() -> None:
    env = templates.env
    env.filters["fromjson"] = _from_json
    env.filters["titlecase"] = _title_case
    env.filters["ago"] = _ago
    env.filters["md"] = markdown.render
    env.filters["excerpt"] = markdown.excerpt
    env.filters["today"] = lambda: datetime.now(timezone.utc).strftime("%Y-%m-%d")


register_filters()


# ---------------------------------------------------------------------------
# Context
# ---------------------------------------------------------------------------

def base_context(request: Request, **extra: Any) -> dict[str, Any]:
    viewer = current_user(request)
    context: dict[str, Any] = {
        "request": request,
        "brand": brand.brand(),
        "user": viewer,
        "is_staff": viewer.is_staff if viewer else False,
        "csrf_token": csrf.issue_token(session_id(request)),
        "path": request.url.path,
        "query": dict(request.query_params),
        "flash": read_flash(request),
        "show_demo_accounts": get_settings().allows_demo_accounts,
        "mail_configured": bool(get_settings().smtp_url),
        "due_cards": 0,
        "unread": 0,
        "stats": None,
    }
    if viewer:
        context["stats"] = progress.user_stats(viewer.id)
        context["due_cards"] = int(
            db.scalar("SELECT count(*) AS c FROM user_flashcards WHERE user_id = ? AND due_at <= ?",
                      viewer.id, auth.now_ms()) or 0
        )
        context["unread"] = int(
            db.scalar("SELECT count(*) AS c FROM notifications WHERE user_id = ? AND read_at IS NULL",
                      viewer.id) or 0
        )
    context.update(extra)
    return context


def render(request: Request, template: str, status_code: int = 200, **extra: Any):
    """Renders a template.

    ``status_code`` is pulled out of the kwargs on purpose. Every kwarg lands in
    the template context, so passing it through the way the other values do would
    silently bind it as a template variable and the response would still be 200 -
    which is exactly what made the login and register error paths report success
    to clients that check the status code.

    A signed-in response is marked non-cacheable. Most pages render the viewer's
    own data - /today, /profile, /notifications, /mistakes - and the service
    worker keeps a copy for offline use, so on a shared machine the next person
    to open the app offline would be shown the previous user's dashboard. The
    header is set here rather than by a per-route denylist because a new page
    added next year would otherwise be forgotten; the server knows whether the
    response belongs to somebody, so the server says so.
    """
    context = base_context(request, **extra)
    response = templates.TemplateResponse(
        request, template, context, status_code=status_code
    )
    if context.get("user") is not None:
        response.headers["Cache-Control"] = "private, no-store, max-age=0"
    return response


def flash(response, message: str) -> None:
    """Stores a one-shot message in a short-lived cookie.

    HTTP header values must be latin-1, so the text is percent-encoded first.
    Without that, an em dash or any non-ASCII glyph raises UnicodeEncodeError
    from inside set_cookie and turns the response into a 500.
    """
    from engineverse.security.sessions import public_cookie_kwargs

    encoded = quote(message[:200], safe="")
    response.set_cookie("ev_flash", encoded, **public_cookie_kwargs(8))


def read_flash(request) -> str:
    """Returns and clears the pending flash message, if any."""
    raw = request.cookies.get("ev_flash")
    if not raw:
        return ""
    try:
        return unquote(raw)
    except Exception:
        return raw
