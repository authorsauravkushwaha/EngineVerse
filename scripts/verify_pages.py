#!/usr/bin/env python3
"""Verify the *deployed* Pages site, including its exact Git revision.

The reading copy and the full-app gateway have different contracts. An upload
is not success until the CDN serves the expected mode, links and assets.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import time
from urllib.error import HTTPError, URLError
from urllib.parse import urlparse
from urllib.request import Request, urlopen

CAPABILITIES = ("apis", "studio", "workflows", "swarm")


def normalise_url(url: str) -> str:
    parts = urlparse(url)
    if parts.scheme != "https" or not parts.hostname or not parts.hostname.endswith(".github.io"):
        raise ValueError("Expected an HTTPS GitHub Pages URL.")
    if parts.username or parts.password or parts.query or parts.fragment or parts.port:
        raise ValueError("Pages URL must not contain credentials, a port, query or fragment.")
    return url.rstrip("/") + "/"


def validate_page(text: str, *, capability: str | None = None) -> None:
    if capability and f'data-engineverse-capability="{capability}"' not in text:
        raise ValueError(f"{capability}: published capability marker missing")
    if len(re.findall(r"<h1\b", text, re.I)) != 1:
        raise ValueError("Expected exactly one h1 in the published page")
    previous = 0
    for raw in re.findall(r"<h([1-6])\b", text, re.I):
        level = int(raw)
        if previous and level > previous + 1:
            raise ValueError(f"Invalid published heading outline: h{previous} -> h{level}")
        previous = level


def _fetch(url: str, sha: str, attempt: int, content_type: str) -> str:
    request = Request(url + f"?deployment={sha}&attempt={attempt}", headers={
        "User-Agent": "EngineVerse-Pages-Verification/1.0", "Cache-Control": "no-cache",
    })
    with urlopen(request, timeout=20) as response:
        if response.status != 200 or content_type not in (response.headers.get("Content-Type") or ""):
            raise ValueError(f"Unexpected published response at {url}: HTTP {response.status}")
        return response.read(4 * 1024 * 1024).decode("utf-8")


def verify(url: str, sha: str, *, attempts: int = 12, delay: float = 15,
           mode: str = "reading-copy", app_url: str = "") -> None:
    url = normalise_url(url)
    if not re.fullmatch(r"[0-9a-f]{40}", sha):
        raise ValueError("Expected the full 40-character deployment commit SHA.")
    if mode not in {"reading-copy", "gateway"}:
        raise ValueError("Unknown Pages deployment mode.")
    if mode == "gateway" and not app_url.startswith("https://"):
        raise ValueError("Gateway verification needs its HTTPS hosted app origin.")
    last_error = None
    for attempt in range(1, attempts + 1):
        try:
            manifest = json.loads(_fetch(url + "deployment.json", sha, attempt, "application/json"))
            if manifest.get("revision") != sha or manifest.get("mode") != mode:
                raise ValueError("CDN is not serving this commit's expected Pages mode yet")
            if mode == "gateway":
                if manifest.get("app_url") != app_url:
                    raise ValueError("Gateway is not pointing at the configured app")
                home = _fetch(url, sha, attempt, "text/html")
                moved = _fetch(url + "404.html", sha, attempt, "text/html")
                for page in (home, moved):
                    validate_page(page)
                    if f'href="{app_url}/"' not in page or f'href="{app_url}/login"' not in page:
                        raise ValueError("Gateway full-app links are missing")
                if "location.replace(app+path+location.search+location.hash)" not in moved:
                    raise ValueError("Old deep links do not reach the full app")
                if "/topics/" in home:
                    raise ValueError("Gateway unexpectedly includes reading-copy content")
                _fetch(url + "static/css/app.css", sha, attempt, "text/css")
                print(f"Verified live full-app gateway for {sha} at {url}", flush=True)
                return
            expected = [urlparse(url).path + capability + "/" for capability in CAPABILITIES]
            if manifest.get("capabilities") != expected:
                raise ValueError("Deployment manifest is missing capability paths")
            home = _fetch(url, sha, attempt, "text/html")
            if "<header" not in home.lower() and "EngineVerse" not in home:
                raise ValueError("Home page is not the published EngineVerse site")
            validate_page(home)
            for capability in CAPABILITIES:
                text = _fetch(url + capability + "/", sha, attempt, "text/html")
                validate_page(text, capability=capability)
                for path in expected:
                    if f'href="{path}"' not in text:
                        raise ValueError(f"{capability}: navigation link missing: {path}")
                if capability != "apis" and 'data-lab-mode-notice hidden' in text:
                    raise ValueError(f"{capability}: backend-only controls are not disclosed")
                print(f"HTTP 200 · valid headings and navigation · {url}{capability}/", flush=True)
            for asset in ("static/css/capabilities.css", "static/js/capabilities.js"):
                body = _fetch(url + asset, sha, attempt, "text/css" if asset.endswith(".css") else "javascript")
                if not body.strip():
                    raise ValueError(f"Published asset is empty: {asset}")
                print(f"HTTP 200 · {url}{asset}", flush=True)
            print(f"Verified live GitHub Pages deployment for {sha} at {url}", flush=True)
            return
        except (HTTPError, URLError, TimeoutError, OSError, ValueError) as exc:
            last_error = exc
            print(f"Deployment verification attempt {attempt}/{attempts}: {exc}", flush=True)
            if attempt < attempts:
                time.sleep(delay)
    raise SystemExit(f"Live Pages verification failed: {last_error}")


def self_check() -> None:
    assert normalise_url("https://authorsauravkushwaha.github.io/EngineVerse") == "https://authorsauravkushwaha.github.io/EngineVerse/"
    validate_page('<h1>Studio</h1><h2>Schema</h2><h3>Columns</h3><h2>SQL</h2>')
    for page in ('<h1>X</h1><h3>Skipped</h3>', '<h1>X</h1><h1>Y</h1>'):
        try:
            validate_page(page)
        except ValueError:
            pass
        else:
            raise AssertionError("Invalid published outline was accepted")
    for url in ("http://x.github.io/", "https://example.org/", "https://x.github.io/?q=1"):
        try:
            normalise_url(url)
        except ValueError:
            pass
        else:
            raise AssertionError("Invalid Pages origin was accepted")
    print("Pages verifier self-check ok")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--url", default="https://authorsauravkushwaha.github.io/EngineVerse/")
    parser.add_argument("--sha", default=os.environ.get("GITHUB_SHA", ""))
    parser.add_argument("--attempts", type=int, default=12)
    parser.add_argument("--delay", type=float, default=15)
    parser.add_argument("--mode", choices=("reading-copy", "gateway"), default="reading-copy")
    parser.add_argument("--app-url", default="", help="expected HTTPS full-app origin in gateway mode")
    parser.add_argument("--self-check", action="store_true")
    args = parser.parse_args()
    if args.self_check:
        self_check()
    else:
        if not 1 <= args.attempts <= 30 or not 0 <= args.delay <= 60:
            parser.error("attempts must be 1–30; delay must be 0–60 seconds")
        verify(args.url, args.sha, attempts=args.attempts, delay=args.delay,
               mode=args.mode, app_url=args.app_url.rstrip("/"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
