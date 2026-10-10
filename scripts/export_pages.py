#!/usr/bin/env python3
"""Write a static reading copy for GitHub Pages.

GitHub Pages cannot run this application. The export is the public catalogue
only: notes, subjects, problems and projects. Accounts, saved progress and
code execution stay on a self-hosted install. This script never creates demo
accounts and refuses to finish if a known demo password appears in the output.

The brand name is whatever the seeded site configuration says. Nothing here
renames the product.
"""
from __future__ import annotations

import argparse
import html
import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BACKEND = ROOT / "backend"
FORBIDDEN = (
    "LearnBuild#2026!",
    "TeachLearn#2026!",
    "Str0ngPassphrase#42!",
    "engineverse-development-secret-not-for-production",
    "pages-export-not-a-production-secret",
)
SKIP_PREFIXES = (
    "/login",
    "/register",
    "/forgot",
    "/reset",
    "/logout",
    "/admin",
    "/settings",
    "/profile",
    "/notifications",
    "/today",
    "/onboarding",
    "/streaks",
    "/mistakes",
    "/api",
    "/certificates",
    "/portfolio",
)
AUTH_TO_HOSTING = (
    "/login",
    "/register",
    "/forgot-password",
    "/reset-password",
    "/logout",
    "/admin",
    "/settings",
    "/profile",
    "/notifications",
    "/today",
    "/onboarding",
    "/streaks",
    "/mistakes",
)
FILE_SUFFIXES = (
    ".css",
    ".js",
    ".svg",
    ".png",
    ".jpg",
    ".jpeg",
    ".webp",
    ".gif",
    ".ico",
    ".json",
    ".xml",
    ".txt",
    ".webmanifest",
    ".map",
)
ATTR_URL = re.compile(
    r"""(?P<attr>\b(?:href|src|action)\s*=\s*)(?P<q>["'])(?P<url>/[^"']*)(?P=q)"""
)
REPO = "https://github.com/authorsauravkushwaha/EngineVerse"


def repo_base(explicit: str | None = None) -> str:
    """Project Pages live under /RepoName/. A *.github.io repo is served at /."""
    if explicit is not None:
        text = explicit.strip()
        if text in ("", "/"):
            return "/"
        return "/" + text.strip("/") + "/"
    name = os.environ.get("GITHUB_REPOSITORY", "authorsauravkushwaha/EngineVerse").split("/")[-1]
    if name.endswith(".github.io"):
        return "/"
    return f"/{name}/"


def join_base(base: str, path: str) -> str:
    if not path.startswith("/"):
        path = "/" + path
    if base == "/":
        return path
    return base.rstrip("/") + path


def is_file_url(path: str) -> bool:
    clean = path.split("?", 1)[0].split("#", 1)[0].rstrip("/")
    if clean.startswith("/static/") or clean.startswith("/api/"):
        return True
    lower = clean.lower()
    return any(lower.endswith(suffix) for suffix in FILE_SUFFIXES)


def rewrite_url(url: str, base: str) -> str:
    """Map an app-root URL onto the Pages base, with a trailing slash for pages."""
    if not url.startswith("/") or url.startswith("//"):
        return url
    path, query, frag = url, "", ""
    if "#" in path:
        path, frag = path.split("#", 1)
        frag = "#" + frag
    if "?" in path:
        path, query = path.split("?", 1)
        query = "?" + query
    if path != "/" and not is_file_url(path):
        path = path.rstrip("/") + "/"
    return join_base(base, path) + query + frag


def rewrite_html(text: str, base: str) -> str:
    hosting = rewrite_url("/hosting", base)
    auth_targets = [rewrite_url(old, base) for old in AUTH_TO_HOSTING]

    def repl(match: re.Match[str]) -> str:
        url = rewrite_url(match.group("url"), base)
        if "/api/" in url or any(url == target or url.startswith(target) for target in auth_targets):
            url = hosting
        return f"{match.group('attr')}{match.group('q')}{url}{match.group('q')}"

    return ATTR_URL.sub(repl, text)


def output_path(site: Path, url_path: str) -> Path:
    path = url_path.split("?", 1)[0].split("#", 1)[0]
    if path in ("", "/"):
        return site / "index.html"
    return site / path.strip("/") / "index.html"


def prepare_env(db_path: Path) -> dict[str, str]:
    env = os.environ.copy()
    # A developer .env must not redirect this export at a live database.
    env["ENGINEVERSE_ENV"] = "development"
    env["ENGINEVERSE_DB_PATH"] = str(db_path)
    env["ENGINEVERSE_DB_URL"] = ""
    env["ENGINEVERSE_JUDGE"] = "disabled"
    env["ENGINEVERSE_SITE_URL"] = "http://127.0.0.1:8765"
    env["ENGINEVERSE_SECRET"] = "pages-export-local-only-not-published-0001"
    env["ENGINEVERSE_REVEAL_RESET_TOKEN"] = ""
    env["ENGINEVERSE_TRUST_PROXY"] = ""
    return env


def seed(env: dict[str, str], db_path: Path) -> None:
    db_path.parent.mkdir(parents=True, exist_ok=True)
    if db_path.exists():
        db_path.unlink()
    subprocess.check_call(
        [sys.executable, str(ROOT / "scripts" / "seed.py"), "--fresh", "--no-demo"],
        cwd=ROOT,
        env=env,
    )


def load_app():
    for path in (str(BACKEND), str(ROOT)):
        if path not in sys.path:
            sys.path.insert(0, path)
    os.chdir(ROOT)
    from main import app  # noqa: WPS433

    return app


def public_paths() -> list[str]:
    from engineverse import catalog, coding, db, library, projects

    paths = [
        "/",
        "/explore",
        "/about",
        "/practice",
        "/dpp",
        "/programming",
        "/projects",
        "/resources",
        "/videos",
        "/books",
        "/formulas",
        "/roadmaps",
        "/community",
        "/placements",
        "/leaderboard",
        "/terms",
        "/privacy",
        "/install",
        "/offline",
        "/search",
    ]
    paths += [f"/branches/{row['slug']}" for row in catalog.list_branches()]
    paths += [f"/subjects/{row['slug']}" for row in catalog.list_subjects(limit=500)]
    paths += [
        f"/topics/{row['slug']}"
        for row in db.query("SELECT slug FROM topics WHERE status = 'published' ORDER BY slug")
    ]
    paths += [f"/projects/{row['slug']}" for row in projects.list_projects(limit=400)]
    problems, _total = coding.list_problems(limit=400)
    paths += [f"/practice/problems/{row['slug']}" for row in problems]
    paths.append("/practice/problems")
    paths += ["/practice/questions", "/revision", "/tutor"]
    for row in db.query("SELECT date FROM dpp_sets ORDER BY date"):
        if row["date"]:
            paths.append(f"/dpp/{row['date']}")
    for lang in coding.list_languages():
        slug = lang.get("slug")
        if slug:
            paths.append(f"/programming/{slug}")
    for roadmap in library.list_roadmaps():
        slug = roadmap.get("slug")
        if slug:
            paths.append(f"/roadmaps/{slug}")
    # First-year filter is a query on the live app. Pages has no query router,
    # so the same list is saved at its own path and the home link is rewritten.
    paths.append("/explore/first-year")
    seen: list[str] = []
    for path in paths:
        if path not in seen and not any(path.startswith(prefix) for prefix in SKIP_PREFIXES):
            seen.append(path)
    return seen


def search_index(base: str) -> list[dict[str, str]]:
    from engineverse import db

    rows: list[dict[str, str]] = []

    def add(kind: str, title: str, text: str, path: str) -> None:
        title = (title or "").strip()
        if not title:
            return
        rows.append(
            {
                "kind": kind,
                "title": title,
                "text": (text or "")[:240],
                "url": rewrite_url(path, base),
            }
        )

    for row in db.query(
        "SELECT t.slug, t.title, t.summary, s.name AS subject FROM topics t "
        "JOIN subjects s ON s.id = t.subject_id WHERE t.status = 'published'"
    ):
        add("Topic", row["title"], f"{row['subject']}. {row['summary'] or ''}", f"/topics/{row['slug']}")
    for row in db.query("SELECT slug, name, description FROM subjects"):
        add("Subject", row["name"], row["description"] or "", f"/subjects/{row['slug']}")
    for row in db.query("SELECT slug, title, summary FROM projects"):
        add("Project", row["title"], row["summary"] or "", f"/projects/{row['slug']}")
    for row in db.query("SELECT slug, title, statement FROM coding_problems"):
        add("Problem", row["title"], row["statement"] or "", f"/practice/problems/{row['slug']}")
    for row in db.query("SELECT name, latex, meaning FROM formulas"):
        add("Formula", row["name"], row["meaning"] or row["latex"] or "", "/formulas")
    return rows


def banner(base: str) -> str:
    home = html.escape(rewrite_url("/hosting", base), quote=True)
    source = html.escape(REPO, quote=True)
    return (
        '<div class="announce">This address is a public reading copy on GitHub Pages. '
        "Sign-in, saved progress and code execution are not running here. "
        f'<a href="{home}">What this copy is</a> | '
        f'<a href="{source}">Source</a>.</div>'
    )


def hosting_main() -> str:
    return """
<h1>This is the reading copy</h1>
<p class="lead">GitHub Pages can only serve files. It cannot run the EngineVerse server, a database, or the code judge.</p>
<div class="grid g2">
  <article class="panel">
    <h2>What you can do here</h2>
    <p>Read the notes, diagrams and catalogue that ship in the repository. Search works in the browser, against that same catalogue. Nothing on this copy is a university degree, and nothing here is a certificate.</p>
    <p><a class="btn btn-primary" href="../explore/">Open the catalogue</a></p>
  </article>
  <article class="panel">
    <h2>What needs the real app</h2>
    <p>An account, saved progress, the mistake notebook, community posts and code execution all need a self-hosted install. This page does not deploy that install and does not claim one is public.</p>
    <p>The install steps are in the repository README. Core learning stays free. A certificate from the app, when you run it yourself, is a platform record, not accreditation.</p>
    <p><a class="btn btn-ghost" href="https://github.com/authorsauravkushwaha/EngineVerse">Repository</a></p>
  </article>
</div>
""".strip()


def search_script(base: str) -> str:
    index_url = html.escape(rewrite_url("/search-index.json", base), quote=True)
    return f"""
<script>
(function () {{
  var params = new URLSearchParams(location.search);
  var q = (params.get("q") || "").trim().toLowerCase();
  var host = document.getElementById("pages-results");
  if (!host || !q) return;
  fetch("{index_url}").then(function (res) {{ return res.json(); }}).then(function (rows) {{
    var terms = q.split(/\\s+/).filter(Boolean);
    var hits = rows.filter(function (row) {{
      var hay = (row.title + " " + row.text + " " + row.kind).toLowerCase();
      return terms.every(function (term) {{ return hay.indexOf(term) !== -1; }});
    }}).slice(0, 48);
    host.hidden = false;
    var heading = document.createElement("p");
    heading.className = "muted";
    heading.textContent = hits.length + (hits.length === 1 ? " result" : " results") + " in this reading copy";
    host.appendChild(heading);
    var grid = document.createElement("div");
    grid.className = "grid g3";
    hits.forEach(function (row) {{
      var card = document.createElement("a");
      card.className = "card";
      card.href = row.url;
      var title = document.createElement("span");
      title.className = "title";
      title.textContent = row.title;
      var desc = document.createElement("span");
      desc.className = "desc";
      desc.textContent = row.text;
      var tags = document.createElement("div");
      tags.className = "tags";
      var chip = document.createElement("span");
      chip.className = "chip";
      chip.textContent = row.kind;
      tags.appendChild(chip);
      card.appendChild(title);
      card.appendChild(desc);
      card.appendChild(tags);
      grid.appendChild(card);
    }});
    host.appendChild(grid);
    if (!hits.length) {{
      var empty = document.createElement("div");
      empty.className = "empty";
      empty.textContent = "Nothing in this reading copy matched. Try a shorter term.";
      host.appendChild(empty);
    }}
  }}).catch(function () {{
    host.hidden = false;
    host.textContent = "Search index did not load.";
  }});
}})();
</script>
"""


def inject(text: str, base: str, *, search: bool) -> str:
    text = rewrite_html(text, base)
    text = text.replace('href="/explore?year=1"', f'href="{rewrite_url("/explore/first-year", base)}"', 1)
    # The year link may already have been rewritten before this replacement.
    year = rewrite_url("/explore", base)
    text = text.replace(f'href="{year}?year=1"', f'href="{rewrite_url("/explore/first-year", base)}"')
    text = text.replace(f"href='{year}?year=1'", f"href='{rewrite_url('/explore/first-year', base)}'")
    notice = banner(base)
    text = text.replace("<header class=\"topbar\">", notice + "\n<header class=\"topbar\">", 1)
    if search:
        slot = '<div id="pages-results" hidden></div>\n' + search_script(base)
        text = text.replace("</main>", slot + "\n</main>", 1)
    if "</body>" in text:
        text = text.replace("</body>", mirror_script() + "\n</body>", 1)
    return text


def patch_app_js(text: str, base: str) -> str:
    text = text.replace(
        'navigator.serviceWorker.register("/sw.js")',
        'navigator.serviceWorker.register("/sw.js-disabled")',
    )
    # Drop the registration entirely so a missing worker cannot take the page.
    text = re.sub(
        r"if \(\"serviceWorker\" in navigator && location\.protocol !== \"file:\"\) \{\s*"
        r"window\.addEventListener\(\"load\", \(\) => \{\s*"
        r"navigator\.serviceWorker\.register\(\"/sw\.js-disabled\"\)\.catch\(\(\) => \{[^}]*\}\);\s*"
        r"\}\);\s*"
        r"\}",
        "/* No service worker on the GitHub Pages reading copy. */",
        text,
        count=1,
    )
    for old in ("/login", "/register", "/api/"):
        text = text.replace(f'"{old}', f'"{join_base(base, old)}')
        text = text.replace(f"'{old}", f"'{join_base(base, old)}")
    text = text.replace('"/search?q=', f'"{rewrite_url("/search", base)}?q=')
    return text


def copy_static(site: Path, base: str) -> None:
    src = BACKEND / "static"
    dest = site / "static"
    if dest.exists():
        shutil.rmtree(dest)
    shutil.copytree(src, dest)
    sw = dest / "sw.js"
    if sw.exists():
        sw.unlink()
    app_js = dest / "js" / "app.js"
    app_js.write_text(patch_app_js(app_js.read_text(encoding="utf-8"), base), encoding="utf-8")
    manifest = {
        "name": "EngineVerse",
        "short_name": "EngineVerse",
        "description": "Public reading copy of the EngineVerse catalogue.",
        "start_url": rewrite_url("/", base),
        "scope": rewrite_url("/", base),
        "display": "standalone",
        "background_color": "#e4e9f1",
        "theme_color": "#e4e9f1",
        "icons": [
            {
                "src": rewrite_url("/static/icons/icon-192.png", base),
                "sizes": "192x192",
                "type": "image/png",
            }
        ],
    }
    (site / "manifest.webmanifest").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")


def mirror_script() -> str:
    """Show a note's explanation without calling the server. Does not grade the answer."""
    return """
<script>
(function () {
  document.querySelectorAll("[data-quiz] form").forEach(function (form) {
    form.addEventListener("submit", function (event) {
      event.preventDefault();
      event.stopPropagation();
      var card = form.closest("[data-quiz]");
      if (!card) return;
      var explain = card.querySelector(".explain");
      if (explain) explain.classList.add("on");
      var badge = card.querySelector(".verdict-inline");
      if (badge) {
        badge.textContent = "Shown from the note";
        badge.className = "verdict-inline chip";
        badge.style.display = "inline-block";
      }
    }, true);
  });
})();
</script>
"""


def assert_links(site: Path, base: str) -> None:
    prefix = "" if base == "/" else base.rstrip("/")
    missing: list[str] = []
    for page in site.rglob("*.html"):
        text = page.read_text(encoding="utf-8", errors="replace")
        for url in re.findall(r'(?:href|src|action)="([^"]+)"', text):
            target = _link_target(page, url, site, prefix)
            if target is None:
                continue
            if not target.exists():
                missing.append(f"{page.relative_to(site)} -> {url}")
    if missing:
        sample = "\n".join(missing[:25])
        raise SystemExit(f"Refusing to publish. {len(missing)} links do not resolve:\n{sample}")


def _link_target(page: Path, url: str, site: Path, prefix: str) -> Path | None:
    raw = url.strip()
    if not raw or raw.startswith(("#", "mailto:", "javascript:", "data:", "http://", "https://")):
        return None
    path = raw.split("#", 1)[0].split("?", 1)[0]
    if not path:
        return None
    if path.startswith("/"):
        if prefix and path != prefix and not path.startswith(prefix + "/"):
            return site / "__outside_base__"
        rel = path[len(prefix):].lstrip("/") if prefix else path.lstrip("/")
        if not rel:
            return site / "index.html"
        candidate = site / rel
    else:
        candidate = (page.parent / path).resolve()
        try:
            candidate.relative_to(site.resolve())
        except ValueError:
            return site / "__outside_tree__"
    if candidate.is_dir() or path.endswith("/") or not candidate.suffix:
        if candidate.suffix:
            return candidate
        return candidate / "index.html"
    return candidate


def assert_clean(site: Path) -> None:
    bad: list[str] = []
    for path in site.rglob("*"):
        if not path.is_file() or path.suffix.lower() in {".png", ".jpg", ".jpeg", ".webp", ".gif", ".ico"}:
            continue
        text = path.read_text(encoding="utf-8", errors="replace")
        for secret in FORBIDDEN:
            if secret in text:
                bad.append(f"{path.relative_to(site)} contains a forbidden token")
                break
    if bad:
        raise SystemExit("Refusing to publish:\n" + "\n".join(bad))


def fill_shell(home_html: str, title: str, main: str) -> str:
    text = re.sub(r"<title>.*?</title>", f"<title>{html.escape(title)}</title>", home_html, count=1, flags=re.S)
    text = re.sub(
        r'(<main id="main" class="wrap">).*?(</main>)',
        lambda match: match.group(1) + "\n" + main + "\n" + match.group(2),
        text,
        count=1,
        flags=re.S,
    )
    return text


def export(site: Path, base: str) -> int:
    if site.exists():
        shutil.rmtree(site)
    site.mkdir(parents=True)
    (site / ".nojekyll").write_text("", encoding="utf-8")
    copy_static(site, base)

    from fastapi.testclient import TestClient

    app = load_app()
    client = TestClient(app, follow_redirects=False)
    written = 0
    failed: list[str] = []
    home_html = ""
    for path in public_paths():
        fetch = "/explore" if path == "/explore/first-year" else path
        if path == "/explore/first-year":
            response = client.get("/explore", params={"year": "1"})
        else:
            response = client.get(fetch)
        if response.status_code != 200 or "text/html" not in response.headers.get("content-type", ""):
            failed.append(f"{path} -> {response.status_code}")
            continue
        body = inject(response.text, base, search=(path == "/search"))
        # First-year page should not keep a query-string link to itself as the only year view.
        if path == "/explore/first-year":
            body = body.replace("<title>", "<title>First year - ", 1)
        target = output_path(site, path)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(body, encoding="utf-8")
        written += 1
        if path == "/":
            home_html = body

    if not home_html:
        raise SystemExit("Home page did not render. Nothing was published.")

    hosting = fill_shell(home_html, "Reading copy", hosting_main())
    hosting_path = output_path(site, "/hosting")
    hosting_path.parent.mkdir(parents=True, exist_ok=True)
    hosting_path.write_text(hosting, encoding="utf-8")
    written += 1

    missing = client.get("/this-page-is-not-in-the-catalogue")
    not_found = inject(missing.text, base, search=False) if missing.text else home_html
    (site / "404.html").write_text(not_found, encoding="utf-8")

    index = search_index(base)
    (site / "search-index.json").write_text(json.dumps(index, ensure_ascii=False), encoding="utf-8")

    origin = "https://authorsauravkushwaha.github.io" + ("" if base == "/" else base.rstrip("/"))
    locs = [origin + "/"]
    for path in sorted(site.rglob("index.html")):
        rel = path.relative_to(site).as_posix()
        if rel == "index.html":
            continue
        locs.append(origin + "/" + rel[: -len("index.html")])
    xml = ["<?xml version=\"1.0\" encoding=\"UTF-8\"?>", '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">']
    xml += [f"<url><loc>{html.escape(loc)}</loc></url>" for loc in locs]
    xml.append("</urlset>")
    (site / "sitemap.xml").write_text("\n".join(xml) + "\n", encoding="utf-8")
    if failed:
        raise SystemExit("Refusing to publish. These pages did not render:\n" + "\n".join(failed))
    assert_clean(site)
    assert_links(site, base)
    print(f"Wrote {written} pages and {len(index)} search rows to {site}")
    return written


def self_check() -> None:
    assert rewrite_url("/topics/ohm", "/EngineVerse/") == "/EngineVerse/topics/ohm/"
    assert rewrite_url("/static/css/app.css", "/EngineVerse/") == "/EngineVerse/static/css/app.css"
    assert rewrite_url("/search?q=beam", "/") == "/search/?q=beam"
    assert rewrite_url("https://example.com", "/EngineVerse/") == "https://example.com"
    sample = '<a href="/login">Sign in</a><a href="/topics/a">A</a><a href="/api/docs">API</a>'
    rewritten = rewrite_html(sample, "/EngineVerse/")
    assert rewritten.count('href="/EngineVerse/hosting/"') == 2
    assert 'href="/EngineVerse/topics/a/"' in rewritten
    assert "LearnBuild#2026!" not in rewritten
    assert "data-theme" not in mirror_script()
    print("self-check ok")


def main() -> int:
    parser = argparse.ArgumentParser(description="Export the public catalogue for GitHub Pages.")
    parser.add_argument("--out", default="site", help="output directory, relative to the repo root")
    parser.add_argument("--base", default=None, help="URL prefix, for example /EngineVerse/ or /")
    parser.add_argument("--self-check", action="store_true", help="check URL rewriting and exit")
    parser.add_argument("--skip-seed", action="store_true", help="reuse ENGINEVERSE_DB_PATH")
    args = parser.parse_args()
    if args.self_check:
        self_check()
        return 0
    base = repo_base(args.base)
    db_path = ROOT / "data" / "pages-export.sqlite"
    env = prepare_env(db_path)
    os.environ.update(env)
    if not args.skip_seed:
        seed(env, db_path)
    export(ROOT / args.out, base)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
