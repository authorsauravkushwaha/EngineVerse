#!/usr/bin/env python3
"""Gate a Pages switch on an actual public HTTPS EngineVerse deployment.

This runs in GitHub Actions before publishing the gateway. It is intentionally
read-only and never attempts to create accounts or send learner data. It is not
a substitute for a human testing TLS, registration, backup restores and Judge0.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import HTTPRedirectHandler, Request, build_opener

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
from scripts.export_pages import normalise_app_url  # noqa: E402


class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, request, fp, code, msg, headers, newurl):
        return None


def fetch(origin: str, path: str, *, limit: int = 65536) -> tuple[str, str]:
    """No cross-origin redirect to a login page or an unrelated server."""
    request = Request(origin + path, headers={"User-Agent": "EngineVerse-Deployment-Check/1.0"})
    with build_opener(NoRedirect).open(request, timeout=12) as response:
        if response.status != 200:
            raise ValueError(f"{path} returned HTTP {response.status}, expected 200")
        content_type = response.headers.get("Content-Type", "")
        data = response.read(limit + 1)
        if len(data) > limit:
            raise ValueError(f"{path} exceeded the check size limit")
        return content_type, data.decode("utf-8")


def verify(origin: str, *, get=fetch) -> None:
    origin = normalise_app_url(origin)
    if not origin.startswith("https://"):
        raise ValueError("The public full app must use a real HTTPS domain")
    kind, body = get(origin, "/health")
    if "application/json" not in kind:
        raise ValueError("/health did not return JSON")
    health = json.loads(body)
    if (health.get("ok") is not True or not isinstance(health.get("brand"), str)
            or not health["brand"].strip()):
        raise ValueError("/health did not identify a running EngineVerse app")
    if "users" in health or "tables" in health:
        raise ValueError("/health exposes development-only fields: use a production deployment")
    kind, body = get(origin, "/manifest.webmanifest")
    if "application/manifest+json" not in kind and "application/json" not in kind:
        raise ValueError("Android web manifest is missing")
    manifest = json.loads(body)
    if manifest.get("start_url") != "/" or manifest.get("scope") != "/" or not manifest.get("icons"):
        raise ValueError("The full app must serve a root-scoped PWA manifest")
    for path, marker in (("/login", 'action="/login"'),
                         ("/register", 'action="/register"'),
                         ("/install", "Android")):
        kind, body = get(origin, path)
        if "text/html" not in kind or marker not in body:
            raise ValueError(f"{path} is not an accessible full-app page")
    print("Verified live HTTPS EngineVerse app: health, PWA, login, registration and install.")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--url", required=True, help="HTTPS origin for the full app")
    args = parser.parse_args()
    try:
        verify(args.url)
    except (HTTPError, URLError, TimeoutError, OSError, ValueError, json.JSONDecodeError) as exc:
        raise SystemExit(f"Full app is not ready; leaving the Pages reading copy live: {exc}") from None
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
