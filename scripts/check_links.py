#!/usr/bin/env python3
"""Checks every external URL the platform links to.

The library points at a few hundred external resources. A dead link is worse
than no link: the reader clicks, gets a 404, and stops trusting the shelf. Until
now nothing ever checked, so every URL shipped unverified.

Two modes, because the network is not always available:

    python scripts/check_links.py --offline
        Structural validation only. No network. Runs anywhere, including CI on
        every push, and catches malformed URLs, non-https links, private or
        loopback hosts, embedded whitespace and placeholders.

    python scripts/check_links.py
        Also fetches every URL. Runs on a weekly schedule in CI, where outbound
        network is available and a slow run does not block a pull request.

Exit status is non-zero only for problems that are actually broken. HTTP 403,
429 and 451 are reported as warnings: publishers block automated clients
routinely, and treating that as a dead link would make the check useless.

Usage
-----
    python scripts/check_links.py --offline
    python scripts/check_links.py --timeout 15 --concurrency 12
    python scripts/check_links.py --json > links.json
"""
from __future__ import annotations

import argparse
import ipaddress
import json
import re
import sys
from collections import Counter
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from urllib.parse import urlparse

REPO_ROOT = Path(__file__).resolve().parents[1]

#: Statuses that mean "the server refused an automated client", not "gone".
BLOCKED_STATUSES = {401, 403, 405, 429, 451}

#: Statuses that mean the resource is genuinely unavailable.
DEAD_STATUSES = {400, 404, 410, 415, 501}

PRIVATE_HOSTS = {"localhost", "localhost.localdomain", "example.com", "example.org",
                 "test", "invalid", "engineverse.local"}


# --------------------------------------------------------------------------
# Collecting URLs
# --------------------------------------------------------------------------

def collect_from_database() -> dict[str, list[dict]]:
    """Every URL stored in the seeded database, labelled by where it came from."""
    sys.path.insert(0, str(REPO_ROOT / "backend"))
    try:
        from engineverse import db
        db.query_one("SELECT 1")
    except Exception:
        return {}

    found: dict[str, list[dict]] = {}
    queries = (
        ("resources", "SELECT id, title, url FROM resources WHERE url IS NOT NULL AND url <> ''"),
        ("videos", "SELECT id, title, url FROM videos WHERE url IS NOT NULL AND url <> ''"),
        ("books", "SELECT id, title, legal_url AS url FROM books "
                  "WHERE legal_url IS NOT NULL AND legal_url <> ''"),
    )
    for label, sql in queries:
        for row in db.query(sql):
            found.setdefault(row["url"], []).append({"table": label, "id": row["id"],
                                                     "title": row["title"]})
    return found


def collect_from_source() -> dict[str, list[dict]]:
    """URLs from the registries, so a link can be checked before it is seeded."""
    sys.path.insert(0, str(REPO_ROOT))
    try:
        from seed_data import resource_sources
    except Exception:
        return {}
    return {url: [{"table": "seed_data", "id": "", "title": ""}]
            for url in resource_sources.all_urls() if url}


def collect_urls() -> dict[str, list[dict]]:
    merged: dict[str, list[dict]] = {}
    for source in (collect_from_database(), collect_from_source()):
        for url, refs in source.items():
            merged.setdefault(url, []).extend(refs)
    return merged


# --------------------------------------------------------------------------
# Offline structural checks
# --------------------------------------------------------------------------

def check_structure(url: str) -> tuple[list[str], list[str]]:
    """Returns (errors, warnings) for a URL, without touching the network."""
    errors: list[str] = []
    warnings: list[str] = []

    if any(ch.isspace() for ch in url):
        errors.append("contains whitespace")
    if any(ord(ch) < 32 for ch in url):
        errors.append("contains a control character")

    parsed = urlparse(url)
    if parsed.scheme not in ("http", "https"):
        errors.append(f"scheme is {parsed.scheme!r}, expected http or https")
        return errors, warnings
    if parsed.scheme == "http":
        warnings.append("plain http; prefer https")

    host = (parsed.hostname or "").lower()
    if not host:
        errors.append("no host")
        return errors, warnings
    if host in PRIVATE_HOSTS or host.endswith(".local"):
        errors.append(f"host {host!r} is not publicly reachable")
    if "." not in host:
        errors.append(f"host {host!r} has no dot")
    try:
        address = ipaddress.ip_address(host)
        if address.is_private or address.is_loopback or address.is_link_local:
            errors.append(f"host {host!r} is a private or loopback address")
    except ValueError:
        pass  # a hostname, which is what we want

    if not parsed.path or parsed.path == "/":
        warnings.append("links to a site root rather than a specific resource")
    if re.search(r"(TODO|FIXME|your-domain|placeholder|changeme)", url, re.I):
        errors.append("looks like an unfinished placeholder")
    return errors, warnings


# --------------------------------------------------------------------------
# Network checks
# --------------------------------------------------------------------------

def fetch_status(url: str, timeout: float) -> tuple[int, str]:
    """Returns (status, detail). status 0 means the request never completed."""
    import httpx

    headers = {
        # A honest user agent. Some publishers 403 anything that announces
        # itself as a bot, and an accurate one is more likely to be allowed.
        "User-Agent": "EngineVerse-LinkChecker/1.0 (+https://github.com/authorsauravkushwaha/EngineVerse)",
        "Accept": "*/*",
    }
    try:
        with httpx.Client(timeout=timeout, follow_redirects=True, headers=headers,
                          verify=True) as client:
            try:
                response = client.head(url)
                # Many hosts reject HEAD but serve GET; retry before calling it dead.
                if response.status_code in DEAD_STATUSES or response.status_code >= 500:
                    response = client.get(url)
                return response.status_code, str(response.url)
            except httpx.HTTPStatusError as exc:
                return exc.response.status_code, url
    except httpx.TimeoutException:
        return 0, "timeout"
    except httpx.ConnectError as exc:
        return 0, f"connect error: {exc.__class__.__name__}"
    except httpx.HTTPError as exc:
        return 0, f"{exc.__class__.__name__}"


def check_network(urls: list[str], *, timeout: float, concurrency: int) -> dict[str, tuple[int, str]]:
    results: dict[str, tuple[int, str]] = {}
    with ThreadPoolExecutor(max_workers=concurrency) as pool:
        for url, outcome in zip(urls, pool.map(lambda u: fetch_status(u, timeout), urls)):
            results[url] = outcome
    return results


# --------------------------------------------------------------------------

def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--offline", action="store_true", help="structural checks only, no network")
    parser.add_argument("--timeout", type=float, default=20.0, help="per-request seconds")
    parser.add_argument("--concurrency", type=int, default=10, help="parallel requests")
    parser.add_argument("--limit", type=int, default=0, help="check at most N URLs (0 = all)")
    parser.add_argument("--json", action="store_true", help="emit a machine-readable report")
    parser.add_argument("--strict", action="store_true",
                        help="treat warnings (http, site roots) as failures")
    args = parser.parse_args()

    urls = collect_urls()
    if args.limit:
        urls = dict(sorted(urls.items())[: args.limit])

    report: dict[str, dict] = {}
    errors: list[str] = []
    warnings: list[str] = []

    for url in sorted(urls):
        url_errors, url_warnings = check_structure(url)
        entry: dict = {"refs": urls[url], "errors": url_errors, "warnings": url_warnings}
        errors += [f"{url}: {e}" for e in url_errors]
        warnings += [f"{url}: {w}" for w in url_warnings]
        report[url] = entry

    if not args.offline:
        reachable = [u for u in sorted(urls) if not report[u]["errors"]]
        for url, (status, detail) in check_network(
            reachable, timeout=args.timeout, concurrency=args.concurrency,
        ).items():
            report[url]["status"] = status
            report[url]["detail"] = detail
            if status in DEAD_STATUSES:
                report[url]["errors"].append(f"HTTP {status}")
                errors.append(f"{url}: HTTP {status}")
            elif status == 0:
                report[url]["warnings"].append(detail)
                warnings.append(f"{url}: {detail}")
            elif status in BLOCKED_STATUSES or status >= 500:
                report[url]["warnings"].append(f"HTTP {status} (server refused an automated client)")
                warnings.append(f"{url}: HTTP {status}")

    if args.json:
        print(json.dumps({"total": len(urls), "errors": errors, "warnings": warnings,
                          "urls": report}, indent=2))
        return 1 if errors or (args.strict and warnings) else 0

    by_status = Counter(r.get("status") for r in report.values() if r.get("status"))
    print(f"Checked {len(urls)} distinct URLs"
          + (" (offline, structural only)" if args.offline else ""))
    if by_status:
        print("  status codes: " + ", ".join(f"{k}:{v}" for k, v in sorted(by_status.items())))
    for line in errors:
        print(f"  FAIL  {line}")
    if warnings:
        print(f"  {len(warnings)} warning(s); first few:")
        for line in warnings[:10]:
            print(f"    warn  {line}")
    if errors or (args.strict and warnings):
        print(f"\n{len(errors)} error(s), {len(warnings)} warning(s)")
        return 1
    print(f"\nOK  {len(errors)} error(s), {len(warnings)} warning(s)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
