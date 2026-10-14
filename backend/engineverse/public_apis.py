"""A small, original public-API directory paired with the local curriculum.

Inspired by public-apis/public-apis, not a mirror of its dataset. Entries are
curated metadata, not uptime promises. Nothing here proxies arbitrary URLs,
contacts providers, stores keys, or makes external services a study prerequisite.
"""
from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from typing import Any

from . import db


@dataclass(frozen=True)
class PublicAPI:
    slug: str
    name: str
    category: str
    description: str
    url: str
    docs_url: str
    auth: str
    cors: str
    topic_slug: str
    project_slug: str
    exercise: str
    caveat: str


APIS = (
    PublicAPI(
        "github", "GitHub REST API", "Developer tools",
        "Repository metadata, issues and releases for a developer dashboard.",
        "https://api.github.com/repos/public-apis/public-apis", "https://docs.github.com/en/rest",
        "none", "yes", "http-requests-responses-and-safe-state-changes", "portfolio-website",
        "Display repository activity with a cache and an explicit rate-limit state.",
        "Public reads work without a token but have a smaller request budget. Authenticated and write requests need authorization.",
    ),
    PublicAPI(
        "stack-exchange", "Stack Exchange API", "Developer tools",
        "Search public programming questions and inspect structured responses.",
        "https://api.stackexchange.com/2.3/questions?order=desc&sort=activity&site=stackoverflow",
        "https://api.stackexchange.com/docs", "none", "yes", "arrays", "student-performance-dashboard",
        "Group question activity and discuss sampling bias rather than treating votes as ground truth.",
        "Optional application keys change quotas. Attribution and backoff rules still apply.",
    ),
    PublicAPI(
        "npm-downloads", "npm Downloads API", "Developer tools",
        "Package download totals for a dependency-observability exercise.",
        "https://api.npmjs.org/downloads/point/last-week/typescript",
        "https://github.com/npm/registry/blob/main/docs/download-counts.md",
        "none", "unknown", "http-requests-responses-and-safe-state-changes", "ts-task-api-client",
        "Validate the payload at runtime and distinguish adoption signals from quality.",
        "Download counts are not unique users. Confirm current browser CORS behavior before integration.",
    ),
    PublicAPI(
        "pypi", "PyPI JSON API", "Developer tools",
        "Python distribution metadata and release information.",
        "https://pypi.org/pypi/fastapi/json", "https://docs.pypi.org/api/json/",
        "none", "unknown", "software-process-models-testing", "python-field-notes-api",
        "Build a release-metadata inspector with timeout and malformed-response tests.",
        "Metadata is not a security audit. Do not download or execute packages from this exercise.",
    ),
    PublicAPI(
        "open-meteo", "Open-Meteo", "Environment & sensors",
        "Weather forecasts for sensor comparisons and an engineering dashboard.",
        "https://api.open-meteo.com/v1/forecast?latitude=28.61&longitude=77.21&hourly=temperature_2m",
        "https://open-meteo.com/en/docs", "none", "yes",
        "calibration-error-and-measurement-uncertainty", "arduino-weather-station",
        "Compare a measured temperature to a forecast, showing units and uncertainty separately.",
        "The open-access endpoint is subject to usage terms; commercial access may require a subscription. Forecasts are not measurements.",
    ),
    PublicAPI(
        "usgs-earthquakes", "USGS Earthquake GeoJSON", "Environment & sensors",
        "Geospatial event feeds for civil-engineering data exploration.",
        "https://earthquake.usgs.gov/earthquakes/feed/v1.0/summary/all_day.geojson",
        "https://earthquake.usgs.gov/earthquakes/feed/v1.0/geojson.php",
        "none", "yes", "calibration-error-and-measurement-uncertainty", "structural-load-analyser",
        "Plot magnitude and location while preserving the feed's units and timestamps.",
        "This is a data exercise, not a structural design input, hazard forecast or safety certification.",
    ),
    PublicAPI(
        "nasa-apod", "NASA Astronomy Picture of the Day", "Science & space",
        "Scientific-media metadata for a resilient API client.",
        "https://api.nasa.gov/planetary/apod?api_key=DEMO_KEY", "https://api.nasa.gov/",
        "apiKey", "yes", "http-requests-responses-and-safe-state-changes", "go-healthcheck-service",
        "Handle rate limits, alternate media types and timeouts without unbounded retries.",
        "DEMO_KEY is a public, tightly limited example key, not a production credential. Check media rights before reuse.",
    ),
    PublicAPI(
        "world-bank", "World Bank Indicators", "Research & open data",
        "Country indicator time series for SQL and visualization exercises.",
        "https://api.worldbank.org/v2/country/IND/indicator/EG.USE.ELEC.KH.PC?format=json",
        "https://datahelpdesk.worldbank.org/knowledgebase/topics/125589-developer-information",
        "none", "unknown", "sql-joins-aggregation", "sql-ops-reporting-db",
        "Model missing values explicitly and aggregate by year without inventing observations.",
        "Indicator definitions, coverage and licensing vary. Confirm CORS or use a server-side client.",
    ),
    PublicAPI(
        "crossref", "Crossref REST API", "Research & open data",
        "Scholarly-work and DOI metadata for citation-first tools.",
        "https://api.crossref.org/works?query=engineering&rows=3",
        "https://www.crossref.org/documentation/retrieve-metadata/rest-api/",
        "none", "yes", "writing-a-decision-ready-engineering-brief", "citation-first-study-agent",
        "Resolve citations and keep evidence provenance rather than assuming every indexed paper is correct.",
        "Metadata does not grant full-text access. Identify production clients and respect the provider's polite-pool guidance.",
    ),
    PublicAPI(
        "open-library", "Open Library Search", "Research & open data",
        "Book metadata for a searchable engineering reading shelf.",
        "https://openlibrary.org/search.json?q=engineering&limit=3",
        "https://openlibrary.org/developers/api", "none", "yes",
        "indexes-query-performance", "cpp-text-index-cli",
        "Index a small metadata sample, then compare linear lookup with an index.",
        "Metadata availability is not a promise of free access to the book. Cache responses and follow request limits.",
    ),
    PublicAPI(
        "nager-date", "Nager.Date", "Reference & utilities",
        "Public-holiday dates for a calendar-aware revision planner.",
        "https://date.nager.at/api/v3/PublicHolidays/2026/US",
        "https://date.nager.at/Api", "none", "yes",
        "http-requests-responses-and-safe-state-changes", "js-revision-dashboard",
        "Validate date-only values and show regional coverage instead of assuming a global calendar.",
        "Country coverage varies. Holidays and local observance need verification for consequential use.",
    ),
    PublicAPI(
        "rest-countries", "REST Countries", "Reference & utilities",
        "Country, language and currency metadata for typed client practice.",
        "https://restcountries.com/v3.1/name/india?fields=name,capital,currencies",
        "https://restcountries.com/", "none", "yes",
        "http-requests-responses-and-safe-state-changes", "ts-task-api-client",
        "Validate nested fields and render only text, never HTML supplied by a provider.",
        "Country metadata can change and should not be used as legal or geopolitical authority.",
    ),
)

AUTH_TYPES = ("none", "apiKey", "OAuth")
CORS_TYPES = ("yes", "no", "unknown")


def snippets(entry: PublicAPI) -> dict[str, str]:
    """Copyable examples; timeout/error handling is real and secrets stay server-side."""
    url = entry.url
    py_url = repr(url)
    curl_url = url
    js_url = json.dumps(url)
    python_prelude = "import requests\n"
    if entry.auth == "apiKey":
        curl_url = url.replace("DEMO_KEY", "${NASA_API_KEY}")
        python_prelude += "import os\nfrom urllib.parse import quote\n"
        py_url = repr(url) + '.replace("DEMO_KEY", quote(os.environ["NASA_API_KEY"], safe=""))'
        # No private provider key belongs in browser code. The demo is explicit.
    return {
        "curl": f'curl --fail --show-error --max-time 10 \\\n  -H "Accept: application/json" \\\n  "{curl_url}"',
        "python": (
            python_prelude + f"url = {py_url}\n"
            'response = requests.get(url, headers={"Accept": "application/json"}, timeout=10)\n'
            "response.raise_for_status()\ndata = response.json()\nprint(data)"
        ),
        "javascript": (
            "// Browser example: confirm CORS; never embed a private key.\n"
            + ("// DEMO_KEY is public and rate-limited. Use a server for your own key.\n" if entry.auth == "apiKey" else "")
            + f"const response = await fetch({js_url}, {{\n"
            '  headers: { "Accept": "application/json" },\n'
            "  signal: AbortSignal.timeout(10000)\n});\n"
            "if (!response.ok) throw new Error(`HTTP ${response.status}`);\n"
            "const data = await response.json();\nconsole.log(data);"
        ),
    }


def categories() -> list[str]:
    return sorted({entry.category for entry in APIS})


def list_apis(*, q: str = "", category: str = "", auth: str = "", cors: str = "", slug: str = "") -> list[dict[str, Any]]:
    """Combine filters with AND. Unknown slugs/categories narrow to nothing."""
    terms = q.casefold().split()
    topics = {r["slug"]: r["title"] for r in db.query("SELECT slug, title FROM topics WHERE status='published'")}
    projects = {r["slug"]: r["title"] for r in db.query("SELECT slug, title FROM projects WHERE status='published'")}
    result = []
    for entry in APIS:
        if slug and entry.slug != slug:
            continue
        if category and entry.category.casefold() != category.casefold():
            continue
        if auth and entry.auth.casefold() != auth.casefold():
            continue
        if cors and entry.cors.casefold() != cors.casefold():
            continue
        haystack = " ".join((entry.name, entry.slug, entry.category, entry.description, entry.exercise, entry.topic_slug, entry.project_slug)).casefold()
        if not all(term in haystack for term in terms):
            continue
        row = asdict(entry)
        row.update(
            topic_title=topics.get(entry.topic_slug), project_title=projects.get(entry.project_slug),
            topic_url=f"/topics/{entry.topic_slug}" if entry.topic_slug in topics else None,
            project_url=f"/projects/{entry.project_slug}" if entry.project_slug in projects else None,
            snippets=snippets(entry),
        )
        result.append(row)
    return result
