"""EngineVerse application entry point.

FastAPI app factory. Mounts:

* ``/``      server-rendered pages (``web/``)
* ``/api``   JSON endpoints (``api/``)
* ``/static`` vanilla CSS/JS, icons, PWA manifest and service worker

Every response carries a hardened set of security headers. No third-party
origin is ever contacted by the browser, so the CSP can stay strict: no
inline script beyond the one nonce'd bootstrap, no external fonts, no
analytics.
"""
from __future__ import annotations

import os
import re
import sys
import time
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse, RedirectResponse, Response
from fastapi.staticfiles import StaticFiles
from starlette.middleware.base import BaseHTTPMiddleware

_ROOT = os.path.dirname(os.path.abspath(__file__))
for _path in (_ROOT, os.path.dirname(_ROOT)):
    if _path not in sys.path:
        sys.path.insert(0, _path)

from engineverse import auth, brand, db  # noqa: E402
from engineverse.config import get_settings  # noqa: E402
from engineverse.security import csrf, ratelimit  # noqa: E402
from engineverse.security.clientip import client_ip  # noqa: E402
from engineverse.security import rbac  # noqa: E402
from engineverse.security.audit import record  # noqa: E402
from web import api as api_router  # noqa: E402
from web import auth_pages, pages  # noqa: E402
from web.deps import STATIC_DIR  # noqa: E402

# Nonce placeholder replaced per response.
_CSP_TEMPLATE = (
    "default-src 'self'; "
    "script-src 'self' 'nonce-{nonce}'; "
    "style-src 'self' 'unsafe-inline'; "
    "img-src 'self' data:; "
    "font-src 'self'; "
    "connect-src 'self'; "
    "media-src 'self'; "
    "object-src 'none'; "
    "frame-src 'none'; "
    "base-uri 'self'; "
    "form-action 'self'; "
    "frame-ancestors 'none'; "
    "upgrade-insecure-requests"
)


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Adds CSP with a per-request nonce plus the standard hardening headers."""

    async def dispatch(self, request: Request, call_next):
        nonce = os.urandom(16).hex()
        request.state.csp_nonce = nonce
        started = time.perf_counter()
        response = await call_next(request)
        response.headers["Content-Security-Policy"] = _CSP_TEMPLATE.format(nonce=nonce)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = "camera=(), microphone=(), geolocation=(), payment=()"
        response.headers["Cross-Origin-Opener-Policy"] = "same-origin"
        response.headers["Cross-Origin-Resource-Policy"] = "same-origin"
        response.headers["X-XSS-Protection"] = "0"
        if get_settings().is_https:
            response.headers["Strict-Transport-Security"] = "max-age=63072000; includeSubDomains; preload"
        response.headers["X-Response-Time-Ms"] = f"{(time.perf_counter() - started) * 1000:.1f}"
        return response


class CsrfMiddleware(BaseHTTPMiddleware):
    """Rejects state-changing requests without a valid CSRF token."""

    async def dispatch(self, request: Request, call_next):
        if request.method in csrf.SAFE_METHODS:
            return await call_next(request)
        session = getattr(request.state, "ev_session_id", None)
        if session is None:
            viewer = _peek_session(request)
            session = viewer.session_id if viewer else ""
        token = csrf.request_csrf(request)
        if not token:
            token = await csrf.form_csrf(request)
        if not csrf.check(request, session, token):
            record("security.csrf_rejected", ip=client_ip(request),
                   meta={"path": request.url.path, "method": request.method})
            accepts_html = "text/html" in (request.headers.get("accept") or "")
            if accepts_html:
                return RedirectResponse("/login?error=csrf", status_code=303)
            return JSONResponse({"ok": False, "error": "CSRF token missing or invalid."}, status_code=403)
        return await call_next(request)


def _peek_session(request: Request):
    from engineverse import auth
    from engineverse.security.sessions import session_from_request

    return auth.current_user_from_session(session_from_request(request))


class AdminMfaMiddleware(BaseHTTPMiddleware):
    """In production, staff cannot mutate /admin until an authenticator is enrolled.

    Students are not redirected. A missing CSRF token is rejected by the
    middleware outside this one, so this never turns a forged post into a
    settings change. Enrollment itself lives under /settings, which stays open.
    """

    async def dispatch(self, request: Request, call_next):
        if not get_settings().is_production or request.method != "POST":
            return await call_next(request)
        if not request.url.path.startswith("/admin"):
            return await call_next(request)
        viewer = _peek_session(request)
        if viewer is None or not rbac.is_staff(viewer.user.role):
            return await call_next(request)
        row = db.query_one("SELECT totp_secret FROM users WHERE id = ?", viewer.user.id)
        if row and row.get("totp_secret"):
            return await call_next(request)
        from web.deps import flash

        response = RedirectResponse("/settings", status_code=303)
        flash(response, "Enrol an authenticator in Settings before using admin tools.")
        return response


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Sliding-window limiter for the hot, abuse-prone endpoints."""

    async def dispatch(self, request: Request, call_next):
        path = request.url.path
        limit = None
        if path.startswith("/api/run") or path.startswith("/api/submit"):
            limit = ("judge", 30, 60)
        elif path.startswith("/api/tutor/"):
            # Reads the configured ceiling rather than a literal, so the "ai"
            # entry in LIMITS - defined but previously unused - is what applies.
            count, window = ratelimit.LIMITS["ai"]
            limit = ("ai", count, window)
        elif path.startswith("/api/"):
            limit = ("api", 300, 60)
        if limit is None:
            return await call_next(request)
        key, count, window = limit
        ident = client_ip(request)
        local = ratelimit.check(f"{key}:{ident}", count, window)
        shared = ratelimit.shared_check(f"{key}:{ident}", count, window)
        result = local if not local.allowed else shared
        if not result.allowed:
            return JSONResponse(
                {"ok": False, "error": "Too many requests. Please slow down."},
                status_code=429,
                headers={"Retry-After": str(window), "X-RateLimit-Remaining": "0"},
            )
        response = await call_next(request)
        response.headers["X-RateLimit-Remaining"] = str(result.remaining)
        return response


def prepare_runtime() -> None:
    """Validates production config, or migrates when this is not production.

    Production must not ``CREATE`` or ``ALTER`` on startup. The schema is
    applied by ``scripts/release.py`` with the bootstrap role before this
    process starts. Development and the test suite still migrate here so a
    laptop and CI keep working without a separate release step.
    """
    settings = get_settings()
    if settings.is_production:
        problems = settings.production_problems()
        if problems:
            raise RuntimeError("Refusing to start: " + "; ".join(problems))
        if not db.table_exists("users"):
            raise RuntimeError(
                "Schema is missing. Run scripts/release.py with the migration "
                "role before starting the web process."
            )
        return
    db.migrate()
    from engineverse import search

    search.refresh_if_stale()


@asynccontextmanager
async def lifespan(app: FastAPI):
    prepare_runtime()
    # Search freshness is data, not DDL. In production the runtime role may
    # rebuild the index; it must not be able to change the schema to do so.
    if get_settings().is_production:
        from engineverse import search

        search.refresh_if_stale()
    app.state.started_at = time.time()
    yield
    db.close_connection()


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(
        title="EngineVerse",
        description="Structured engineering education: notes, practice, coding, projects and revision.",
        version="1.0.0",
        lifespan=lifespan,
        docs_url="/api/docs" if not settings.is_production else None,
        redoc_url=None,
        openapi_url="/api/openapi.json" if not settings.is_production else None,
    )

    app.add_middleware(SecurityHeadersMiddleware)
    app.add_middleware(RateLimitMiddleware)
    app.add_middleware(AdminMfaMiddleware)
    app.add_middleware(CsrfMiddleware)

    app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")
    app.include_router(pages.router)
    app.include_router(auth_pages.router)
    app.include_router(api_router.router, prefix="/api")

    @app.exception_handler(404)
    async def not_found(request: Request, _exc):
        if request.url.path.startswith("/api/"):
            return JSONResponse({"ok": False, "error": "Not found."}, status_code=404)
        from web.deps import render

        response = render(request, "error.html", status=404, message="That page does not exist.")
        response.status_code = 404
        return response

    @app.exception_handler(auth.AuthError)
    async def auth_error(request: Request, exc):
        """A refused auth or admin operation carries its own status code.

        These are validation failures - unknown role, unknown status, no such
        user - so they must reach the client as 4xx. Left unhandled they fall
        through to the 500 handler, which also writes a misleading app.error
        audit entry for something that is not a crash.
        """
        status = getattr(exc, "status_code", 400)
        message = getattr(exc, "message", str(exc))
        if request.url.path.startswith("/api/"):
            return JSONResponse({"ok": False, "error": message}, status_code=status)
        from web.deps import render

        response = render(request, "error.html", status=status, message=message)
        response.status_code = status
        return response

    @app.exception_handler(rbac.Forbidden)
    async def forbidden(request: Request, exc):
        """A capability check failed. This is a refusal, not a server fault.

        Without this handler rbac.Forbidden propagates to the 500 handler, which
        both misreports an authorisation problem as a crash and writes a bogus
        app.error audit entry.
        """
        record("security.forbidden", actor_id=getattr(request.state, "ev_user_id", None),
               ip=client_ip(request),
               meta={"path": request.url.path})
        if request.url.path.startswith("/api/"):
            return JSONResponse({"ok": False, "error": "You do not have permission to do that."},
                                status_code=403)
        from web.deps import render

        response = render(request, "error.html", status=403,
                          message="You do not have permission to do that.")
        response.status_code = 403
        return response

    @app.exception_handler(RequestValidationError)
    async def validation_error(request: Request, exc: RequestValidationError):
        """A form submitted with a missing or malformed field.

        FastAPI answers these with a raw JSON body describing its own internals.
        For the 53 form fields on the auth pages that means a student who leaves
        one box empty is shown ``{"detail":[{"type":"missing",...}]}`` instead of
        a page telling them what to fill in. API clients keep the machine-readable
        shape, with the same keys the rest of /api uses.
        """
        problems = []
        for err in getattr(exc, "errors", lambda: [])() or []:
            loc = [str(part) for part in err.get("loc", ()) if part not in ("body", "form", "query")]
            field = loc[-1] if loc else ""
            kind = err.get("type", "")
            if kind == "missing":
                detail = "is required"
            elif kind.startswith("string_type"):
                detail = "must be text"
            else:
                detail = "is not valid"
            problems.append(f"{field} {detail}".strip() if field else detail)

        if request.url.path.startswith("/api/"):
            return JSONResponse(
                {"ok": False, "error": "Some of the submitted values were not accepted.",
                 "fields": problems},
                status_code=422,
            )

        message = "Please check the form and try again."
        if problems:
            message = "Could not read that submission: " + "; ".join(dict.fromkeys(problems)) + "."
        from web.deps import render

        response = render(request, "error.html", status=422, message=message)
        response.status_code = 422
        return response

    @app.exception_handler(500)
    async def server_error(request: Request, exc):
        record("app.error", ip=client_ip(request),
               meta={"path": request.url.path, "error": f"{type(exc).__name__}: {exc}"[:400]})
        if request.url.path.startswith("/api/"):
            return JSONResponse({"ok": False, "error": "Internal server error."}, status_code=500)
        from web.deps import render

        try:
            response = render(request, "error.html", status=500, message="Something went wrong on our side.")
        except Exception:  # never let the error page itself fail
            return Response("Internal server error", status_code=500, media_type="text/plain")
        response.status_code = 500
        return response

    @app.get("/health", include_in_schema=False)
    async def health() -> dict:
        payload = {
            "ok": True,
            "uptime_s": round(time.time() - app.state.started_at, 1),
            "brand": brand.get("site_name", "EngineVerse"),
        }
        # Row counts are useful on a laptop and noisy on a public health check.
        if not get_settings().is_production:
            payload["tables"] = db.schema_table_count()
            payload["users"] = db.row_count("users")
        return payload

    @app.get("/favicon.ico", include_in_schema=False)
    async def favicon() -> Response:
        return RedirectResponse("/static/icons/favicon.svg", status_code=302)

    @app.get("/manifest.webmanifest", include_in_schema=False)
    async def manifest() -> Response:
        from fastapi.responses import FileResponse

        return FileResponse(os.path.join(STATIC_DIR, "manifest.webmanifest"),
                            media_type="application/manifest+json")

    @app.get("/sw.js", include_in_schema=False)
    async def service_worker() -> Response:
        # Must be served from the origin root so its scope covers the whole site.
        from fastapi.responses import FileResponse

        return FileResponse(os.path.join(STATIC_DIR, "sw.js"),
                            media_type="application/javascript",
                            headers={"Service-Worker-Allowed": "/"})

    @app.get("/.well-known/assetlinks.json", include_in_schema=False)
    async def assetlinks() -> Response:
        """Digital Asset Links for an Android Trusted Web Activity.

        Empty unless the operator sets both variables. Nothing here is a
        claim that a Play listing exists. An invalid value is a 404 that does
        not echo the input.
        """
        package = os.environ.get("ENGINEVERSE_TWA_PACKAGE", "").strip()
        fingerprint = os.environ.get("ENGINEVERSE_TWA_SHA256", "").strip().upper()
        package_ok = bool(re.fullmatch(r"[A-Za-z][A-Za-z0-9_]*(\.[A-Za-z][A-Za-z0-9_]*)+", package))
        fingerprint_ok = bool(re.fullmatch(r"[0-9A-F]{2}(:[0-9A-F]{2}){31}", fingerprint))
        if not package_ok or not fingerprint_ok:
            return JSONResponse({"ok": False, "error": "TWA asset links are not configured."}, status_code=404)
        return JSONResponse([{
            "relation": ["delegate_permission/common.handle_all_urls"],
            "target": {
                "namespace": "android_app",
                "package_name": package,
                "sha256_cert_fingerprints": [fingerprint],
            },
        }])

    @app.get("/robots.txt", include_in_schema=False)
    async def robots() -> Response:
        body = "User-agent: *\nAllow: /\nDisallow: /api/\nDisallow: /settings\n"
        return Response(body, media_type="text/plain")

    return app


app = create_app()


if __name__ == "__main__":
    import uvicorn

    settings = get_settings()
    uvicorn.run("main:app", host=settings.host, port=settings.port, reload=settings.debug)
