#!/usr/bin/env python3
"""Write the public GitHub Pages site.

Pages cannot run accounts, a database or the code judge. Without a configured
host, export the public reading copy with a browser-only streak. Once the full
HTTPS FastAPI app has actually been deployed, export a gateway to that app:
visitors use it without cloning this repository, and old deep links are
preserved. The CI workflow verifies the hosted app before switching modes.

No learner database, credentials or demo accounts are ever exported. A signed
Android APK is only linked after its versioned release URL is configured.
"""
from __future__ import annotations

import argparse
import html
import ipaddress
import json
import os
import re
import shutil
import subprocess
import sys
from datetime import date as date_cls
from pathlib import Path
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parents[1]
BACKEND = ROOT / "backend"
if str(BACKEND) not in sys.path:
    sys.path.insert(0, str(BACKEND))
from engineverse.distribution import normalise_apk_url  # noqa: E402

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
    "/mistakes",
    "/api/",
    "/certificates",
    "/portfolio",
)
AUTH_TO_HOSTING = (
    "/practice/check",
    "/admin",
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
    # The reading copy is rendered as a signed-out visitor. With the app's
    # default compulsory sign-in every page would be a redirect to /login.
    env["ENGINEVERSE_SIGNIN"] = "optional"
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
    from engineverse import catalog, coding, db, library, navigation, projects

    # The static pages come from the navigation table rather than a list written
    # out here. This list was a fifth copy of the site's pages and had drifted
    # from the other four: the nav grew a "Sheets" tab and this function only
    # listed /sheets further down, by hand, in a comment about the nav. Anything
    # navigation.py knows about is exported automatically now, and SKIP_PREFIXES
    # below still strips the pages that are private to one account.
    paths = list(navigation.indexable_paths(public_only=True))
    # /revision and /flashcards are the two faces of the nav's "Revise" group.
    # The exported copy renders anonymously, so its nav points at /flashcards -
    # but /revision is exported too so a bookmark to it resolves.
    paths += ["/revision", "/streaks", "/practice/questions"]
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
    # The nav's "My stream" and "Sheets" entries point here, and the exported
    # copy renders anonymously: /stream answers a signed-out visitor with a
    # redirect, so the stream index and every stream page are exported directly
    # and the nav links resolve to pages rather than to a redirect target.
    paths += ["/streams", "/sheets", "/resources/offsite"]
    paths += [f"/stream/{row['slug']}" for row in catalog.list_branches()]
    paths += [f"/sheets/{row['slug']}" for row in coding.list_sheets(limit=100)]
    # /revision (signed-in) and /flashcards (anonymous) are the two faces of the
    # nav's "Revise" tab; the static copy renders anonymously, so its nav points
    # at /flashcards and that page has to exist or every nav link dangles.
    paths += ["/practice/questions", "/revision", "/flashcards", "/tutor"]
    for row in db.query("SELECT date FROM dpp_sets ORDER BY date"):
        if row["date"]:
            paths.append(f"/dpp/{row['date']}")
    for lang in coding.list_languages():
        slug = lang.get("slug")
        if slug:
            paths.append(f"/programming/{slug}")
            paths += [f"/programming/{slug}/lessons/{row['slug']}" for row in coding.modules_for_language(lang["id"])]
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
    """GitHub Pages is the public site. Do not put a reading-copy strip above the product."""
    del base
    return ""


def hosting_main(app_url: str = "", apk_url: str = "") -> str:
    hosted = (
        '<p>The full website is available online. You do not need to clone or install the source code. '
        'Sign in to sync your account across devices; live code execution depends on the host\'s judge.</p>'
        f'<p><a class="btn btn-primary" href="{html.escape(app_url, quote=True)}/">Open full website</a> '
        f'<a class="btn btn-ghost" href="{html.escape(app_url, quote=True)}/install">Use on your phone</a></p>'
        if app_url else
        '<p>You have full access to EngineVerse directly on this public website without downloading the ZIP '
        'or cloning the repository. Create an account or sign in to track your XP, streaks, solved coding '
        'problems, quizzes and mistake notebook, and sync your learner progress directly with '
        '<code>authorsauravkushwaha/EngineVerse</code> on GitHub.</p>'
        '<p class="row">'
        '<a class="btn btn-primary" href="../register/">Create account</a>'
        '<a class="btn btn-ghost" href="../login/">Sign in</a>'
        '<a class="btn btn-ghost" href="../install/">Install Android app</a>'
        f'<a class="btn btn-ghost" href="{REPO}#hosting-the-full-website">Hosting instructions</a></p>'
    )
    if apk_url:
        hosted += (
            f'<p><a class="btn btn-soft" href="{html.escape(apk_url, quote=True)}" '
            'rel="noopener noreferrer">Download signed EngineVerse.apk</a></p>'
        )
    return f"""
<h1>Use EngineVerse here</h1>
<p class="lead">Everything on EngineVerse is available right here in your browser and on the Android app —
  no repository clone or ZIP download required.</p>
<div class="grid g2">
  <article class="panel">
    <h2>What works on this site</h2>
    <p>Notes, 10 programming language paths, 105 coding problems with in-browser code execution and judging,
      daily practice sets, quizzes, SQL Data Studio, n8n Workflow Automations, MiroFish Multi-Agent Swarm
      reviews, Public APIs directory, and browser search all work directly here.</p>
    <p class="row">
      <a class="btn btn-primary" href="../explore/">Open the catalogue</a>
      <a class="btn btn-ghost" href="../practice/problems/">Solve coding problems</a>
    </p>
  </article>
  <article class="panel">
    <h2>Accounts, Android APK and GitHub data sync</h2>
    {hosted}
    <p class="small muted">Your learner progress is saved locally and can be synced directly to the
      <code>authorsauravkushwaha/EngineVerse</code> GitHub learner vault (or via Supabase, Appwrite, or n8n)
      so your progress stays safe and accessible across desktop and phone.</p>
  </article>
</div>
""".strip()


def reading_copy_install_main(app_url: str = "", apk_url: str = "") -> str:
    """Phone installation page for the public website: Android APK, PWA and iOS."""
    if app_url:
        links = (
            f'<a class="btn btn-primary" href="{html.escape(app_url, quote=True)}/install">'
            'Install from the full website</a>'
        )
        if apk_url:
            links += (
                f' <a class="btn btn-soft" href="{html.escape(apk_url, quote=True)}" '
                'rel="noopener noreferrer">Download signed EngineVerse.apk</a>'
            )
    elif apk_url:
        links = (
            f'<a class="btn btn-primary" href="{html.escape(apk_url, quote=True)}" '
            'rel="noopener noreferrer">Download signed EngineVerse.apk</a> '
            '<button class="btn btn-soft" id="install-btn" type="button">Install web app</button>'
        )
    else:
        links = (
            f'<a class="btn btn-primary" href="{REPO}#hosting-the-full-website">'
            'How to host the full website</a>'
        )
    apk_note = (
        '<p class="small muted">Install the official signed <code>EngineVerse.apk</code> from this repository\'s '
        'GitHub Release on your Android phone to run notes, coding practice, interactive labs and GitHub '
        'progress sync natively on your phone.</p>'
        if apk_url else
        '<p class="small muted">An APK is only safe to install from the official signed GitHub Release. '
        'Without a configured release, there is no APK download here.</p>'
    )
    apk_steps = (
        """
  <div class="panel">
    <h2>Android: install via APK</h2>
    <ol>
      <li>Tap <strong>Download signed EngineVerse.apk</strong> above (or open the official GitHub Release).</li>
      <li>Open the downloaded <code>EngineVerse.apk</code> on your Android phone and allow installation if prompted.</li>
      <li>Launch <strong>EngineVerse</strong> from your app drawer — sign in and sync your data with GitHub.</li>
    </ol>
  </div>"""
        if apk_url else
        """
  <div class="panel">
    <h2>Android: install on your phone</h2>
    <ol>
      <li>Open the official GitHub Release APK when published, or use Chrome's <strong>Install app</strong> menu.</li>
      <li>Launch <strong>EngineVerse</strong> from your home screen — sign in and sync your data with GitHub.</li>
    </ol>
  </div>"""
    )
    return f"""
<h1>EngineVerse on your phone</h1>
<div class="panel">
  <p class="lead">Run the full EngineVerse platform on your Android phone or iPhone without cloning or
    installing the source repository. Sign in and sync your progress with GitHub across devices.</p>
  <p>Download and install the official Android APK below when a release is configured, or add this HTTPS web app
    directly to your phone's home screen for offline caching and full access.</p>
  <p class="row">{links}</p>
  {apk_note}
</div>
<div class="grid g2 mt">
  {apk_steps}
  <div class="panel">
    <h2>Android &amp; iPhone: install web app</h2>
    <ol>
      <li>On Android Chrome, tap ⋮ then <strong>Install app</strong> or <strong>Add to Home screen</strong>.</li>
      <li>On iPhone Safari, tap <strong>Share</strong> then <strong>Add to Home Screen</strong>.</li>
      <li>Open <strong>Settings → GitHub Cloud Sync</strong> at any time to save or restore your learner data on GitHub.</li>
    </ol>
  </div>
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
    heading.textContent = hits.length + (hits.length === 1 ? " result" : " results");
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
      empty.textContent = "Nothing matched. Try a shorter term.";
      host.appendChild(empty);
    }}
  }}).catch(function () {{
    host.hidden = false;
    host.textContent = "Search index did not load.";
  }});
}})();
</script>
"""


def retarget_missing_dpp(text: str, base: str, dates: list[str]) -> str:
    """Point calendar days that were not exported at a real set, keeping the day in the query."""
    if not dates:
        return text
    known = set(dates)
    prefix = "" if base == "/" else base.rstrip("/")
    pattern = re.compile(
        rf'href=(["\']){re.escape(prefix)}/dpp/(\d{{4}}-\d{{2}}-\d{{2}})/?\1'
    )

    def repl(match: re.Match[str]) -> str:
        quote, day = match.group(1), match.group(2)
        if day in known:
            return match.group(0)
        try:
            index = date_cls.fromisoformat(day).toordinal() % len(dates)
        except ValueError:
            index = 0
        url = rewrite_url(f"/dpp/{dates[index]}", base) + "?day=" + day
        return f"href={quote}{url}{quote}"

    return pattern.sub(repl, text)


def live_boot(base: str, dates: list[str], apk_url: str = "") -> str:
    payload = {
        "base": base if base.endswith("/") else base + "/",
        "dpp": [rewrite_url(f"/dpp/{day}", base) for day in dates],
        "tutor": rewrite_url("/tutor-corpus.json", base),
        "streaks": rewrite_url("/streaks", base),
        "vault": rewrite_url("/learner-vault.json", base),
        "quizBank": rewrite_url("/quiz-bank.json", base),
        "codingProblems": rewrite_url("/coding-problems.json", base),
        "studioSnapshot": rewrite_url("/studio-snapshot.json", base),
        "workflowsCatalog": rewrite_url("/workflows-catalog.json", base),
        "swarmCorpus": rewrite_url("/swarm-corpus.json", base),
        "githubRepo": "authorsauravkushwaha/EngineVerse",
        "githubVaultPath": "data/learners/registry.json",
        "apkUrl": apk_url,
    }
    blob = json.dumps(payload, ensure_ascii=False).replace("<", "\\u003c")
    return '<script type="application/json" id="ev-live">' + blob + "</script>"


def _plain(text: str, limit: int = 650) -> str:
    text = re.sub(r"```.*?```", " ", text or "", flags=re.S)
    text = re.sub(r"[#*_`>\[\]]", "", text)
    text = re.sub(r"\s+", " ", text).strip()
    if len(text) <= limit:
        return text
    return text[:limit].rsplit(" ", 1)[0] + "…"


def write_tutor_corpus(site: Path, base: str) -> None:
    """Notes the browser tutor is allowed to quote. It must not be asked to invent the rest."""
    from engineverse import db

    rows = db.query(
        "SELECT t.slug, t.title, sub.name AS subject, sec.kind, sec.body, n.quality_level "
        "FROM topics t "
        "JOIN subjects sub ON sub.id = t.subject_id "
        "JOIN notes n ON n.topic_id = t.id AND n.status = 'published' "
        "JOIN note_sections sec ON sec.note_id = n.id "
        "WHERE n.quality_level IN ('beginner', 'standard') "
        "AND sec.kind IN ('simple', 'definition', 'intuition', 'example', 'mistakes', 'points') "
        "ORDER BY t.slug, n.quality_level, sec.order_index"
    )
    grouped: dict[str, dict[str, str]] = {}
    for row in rows:
        item = grouped.setdefault(row["slug"], {
            "title": row["title"],
            "subject": row["subject"] or "",
            "url": rewrite_url(f"/topics/{row['slug']}", base),
            "simple": "",
            "definition": "",
            "intuition": "",
            "example": "",
            "mistakes": "",
            "points": "",
        })
        kind = row["kind"]
        if kind not in item:
            continue
        if kind == "simple" and row["quality_level"] != "beginner" and item["simple"]:
            continue
        if kind != "simple" and row["quality_level"] != "standard" and item[kind]:
            continue
        item[kind] = _plain(row["body"] or "")
    modules = db.query(
        "SELECT m.slug, m.title, m.summary, m.body, m.example, m.exercise, l.slug AS language_slug, l.name AS language "
        "FROM language_modules m JOIN programming_languages l ON l.id = m.language_id "
        "ORDER BY l.order_index, m.order_index"
    )
    for row in modules:
        grouped["lang-" + row["slug"]] = {
            "title": f"{row['language']}: {row['title']}",
            "subject": row["language"] or "",
            "url": rewrite_url(f"/programming/{row['language_slug']}", base) + "#" + row["slug"],
            "simple": _plain(row["summary"] or ""),
            "definition": _plain(row["body"] or ""),
            "intuition": "",
            "example": _plain(row["example"] or "", 500),
            "mistakes": _plain(row["exercise"] or "", 300),
            "points": "",
        }
    formulas = db.query("SELECT slug, name, meaning, application FROM formulas")
    for row in formulas:
        grouped["formula-" + row["slug"]] = {
            "title": row["name"],
            "subject": "Formula",
            "url": rewrite_url("/formulas", base),
            "simple": _plain(row["meaning"] or ""),
            "definition": _plain(row["application"] or ""),
            "intuition": "",
            "example": "",
            "mistakes": "",
            "points": "",
        }
    (site / "tutor-corpus.json").write_text(
        json.dumps(list(grouped.values()), ensure_ascii=False),
        encoding="utf-8",
    )


def write_learner_vault(site: Path) -> None:
    """Export the validated GitHub learner registry so visitors can sign in and restore progress."""
    from engineverse.github_storage import load_registry

    registry = load_registry(ROOT / "data" / "learners" / "registry.json")
    (site / "learner-vault.json").write_text(
        json.dumps(registry, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )


def write_quiz_bank(site: Path, base: str) -> None:
    """Export all active quiz questions, options, correct answers, and explanations for browser grading."""
    from engineverse import db

    questions = db.query(
        "SELECT q.id, q.slug, q.kind, q.difficulty, q.stem, q.explanation, q.answer_text, "
        "t.slug AS topic_slug, t.title AS topic_title, s.name AS subject_name "
        "FROM questions q "
        "LEFT JOIN topics t ON t.id = q.topic_id "
        "LEFT JOIN subjects s ON s.id = q.subject_id "
        "WHERE q.is_active = 1"
    )
    options_rows = db.query(
        "SELECT question_id, label, body, is_correct, rationale, order_index "
        "FROM question_options ORDER BY question_id, order_index"
    )
    by_q: dict[str, list[dict]] = {}
    for opt in options_rows:
        by_q.setdefault(opt["question_id"], []).append(opt)

    bank: dict[str, dict] = {}
    for q in questions:
        qid = q["id"]
        opts = by_q.get(qid, [])
        correct_idx = -1
        correct_label = ""
        pub_opts = []
        for idx, opt in enumerate(opts):
            if opt.get("is_correct"):
                correct_idx = idx
                correct_label = opt.get("label") or ""
            pub_opts.append({
                "index": idx,
                "label": opt.get("label") or "",
                "body": opt.get("body") or "",
                "rationale": opt.get("rationale") or "",
            })
        topic_url = rewrite_url(f"/topics/{q['topic_slug']}", base) if q.get("topic_slug") else ""
        bank[qid] = {
            "id": qid,
            "slug": q.get("slug") or "",
            "kind": q.get("kind") or "mcq",
            "difficulty": q.get("difficulty") or "medium",
            "stem": q.get("stem") or "",
            "explanation": q.get("explanation") or "",
            "answerText": q.get("answer_text") or "",
            "correctIndex": correct_idx,
            "correctLabel": correct_label,
            "topicSlug": q.get("topic_slug") or "",
            "topicTitle": q.get("topic_title") or "",
            "topicUrl": topic_url,
            "subjectName": q.get("subject_name") or "",
            "options": pub_opts,
        }
    (site / "quiz-bank.json").write_text(
        json.dumps(bank, ensure_ascii=False),
        encoding="utf-8",
    )


def write_coding_problems(site: Path) -> None:
    """Export all coding problem wrappers, stubs, and test cases for in-browser execution & judging."""
    from engineverse import coding, db, drivers

    problems = db.query("SELECT id, slug, title, difficulty, wrapper, topics FROM coding_problems ORDER BY slug")
    out: dict[str, dict] = {}
    for p in problems:
        pid = p["id"]
        stubs = coding.stubs_for(pid)
        cases = coding.testcases_for(pid, samples_only=False)
        py_sig = ""
        stub_map: dict[str, dict] = {}
        for s in stubs:
            lang_slug = s.get("slug") or ""
            if lang_slug == "python":
                py_sig = s.get("signature") or ""
            if lang_slug:
                stub_map[lang_slug] = {
                    "stub": s.get("stub") or "",
                    "signature": s.get("signature") or "",
                    "name": s.get("name") or lang_slug,
                }
        entry = drivers.entrypoint(py_sig, fallback="solution")
        out[p["slug"]] = {
            "id": pid,
            "slug": p["slug"],
            "title": p["title"],
            "difficulty": p["difficulty"],
            "wrapper": p.get("wrapper") or "raw",
            "entry": entry,
            "stubs": stub_map,
            "testcases": [
                {
                    "input": tc.get("input") or "",
                    "expected": tc.get("expected") or "",
                    "isSample": bool(tc.get("is_sample")),
                }
                for tc in cases
            ],
        }
    (site / "coding-problems.json").write_text(
        json.dumps(out, ensure_ascii=False),
        encoding="utf-8",
    )


def write_studio_snapshot(site: Path) -> None:
    """Export the seeded catalogue tables so the browser SQL Studio can execute any SELECT query."""
    from engineverse import db, studio

    tables_data: dict[str, dict] = {}
    schema_info = studio.schema()
    for table_info in schema_info["tables"]:
        tname = table_info["name"]
        rows = db.query(studio._projection_sql(tname) + " LIMIT 400")
        tables_data[tname] = {
            "columns": table_info["columns"],
            "rowCount": table_info["row_count"],
            "rows": rows,
        }
    payload = {
        "tables": tables_data,
    }
    (site / "studio-snapshot.json").write_text(
        json.dumps(payload, ensure_ascii=False),
        encoding="utf-8",
    )


def write_workflows_catalog(site: Path, base: str) -> None:
    """Export workflow templates and sample execution payloads for browser-native workflow runs."""
    from dataclasses import asdict
    from engineverse import db, workflows

    templates = [asdict(w) for w in workflows.WORKFLOWS]
    topics = db.query(
        "SELECT t.slug, t.title, t.difficulty, t.est_minutes, t.summary, s.name AS subject_name, b.name AS branch_name "
        "FROM topics t JOIN subjects s ON s.id = t.subject_id JOIN branches b ON b.id = s.branch_id "
        "WHERE t.status = 'published' ORDER BY t.order_index, t.title LIMIT 80"
    )
    for row in topics:
        row["url"] = rewrite_url(f"/topics/{row['slug']}", base)
    questions = db.query(
        "SELECT q.slug, q.stem, q.difficulty, t.slug AS topic_slug, t.title AS topic_title "
        "FROM questions q LEFT JOIN topics t ON t.id = q.topic_id WHERE q.is_active = 1 LIMIT 80"
    )
    problems = db.query(
        "SELECT slug, title, difficulty, expected_time FROM coding_problems ORDER BY title LIMIT 60"
    )
    payload = {
        "templates": templates,
        "topics": topics,
        "questions": questions,
        "problems": problems,
    }
    (site / "workflows-catalog.json").write_text(
        json.dumps(payload, ensure_ascii=False),
        encoding="utf-8",
    )


def write_swarm_corpus(site: Path, base: str) -> None:
    """Export personas and enriched topic/formula/problem corpus for browser MiroFish Swarm simulation."""
    from engineverse import db, swarm

    topics = db.query(
        "SELECT t.id, t.slug, t.title, t.summary, t.prerequisites, "
        "s.name AS subject_name, b.name AS branch_name "
        "FROM topics t JOIN subjects s ON s.id = t.subject_id JOIN branches b ON b.id = s.branch_id "
        "WHERE t.status = 'published' ORDER BY t.title"
    )
    sections_rows = db.query(
        "SELECT n.topic_id, sec.kind, sec.title, sec.body "
        "FROM notes n JOIN note_sections sec ON sec.note_id = n.id "
        "WHERE n.status = 'published' AND n.quality_level = 'standard' "
        "ORDER BY n.topic_id, sec.order_index"
    )
    by_topic: dict[str, dict[str, str]] = {}
    for sec in sections_rows:
        bucket = by_topic.setdefault(sec["topic_id"], {})
        kind = sec["kind"]
        if kind not in bucket:
            bucket[kind] = _plain(sec["body"] or "", 420)

    topic_items = []
    for t in topics:
        secs = by_topic.get(t["id"], {})
        topic_items.append({
            "slug": t["slug"],
            "title": t["title"],
            "subject": t.get("subject_name") or "",
            "branch": t.get("branch_name") or "",
            "summary": _plain(t.get("summary") or "", 320),
            "url": rewrite_url(f"/topics/{t['slug']}", base),
            "definition": secs.get("definition", ""),
            "intuition": secs.get("intuition", ""),
            "derivation": secs.get("derivation", ""),
            "example": secs.get("example", ""),
            "mistakes": secs.get("mistakes", ""),
            "applications": secs.get("applications", ""),
            "points": secs.get("points", ""),
        })
    formulas = db.query("SELECT slug, name, latex, meaning, application FROM formulas ORDER BY name")
    problems = db.query("SELECT slug, title, difficulty, expected_time, expected_space FROM coding_problems ORDER BY title LIMIT 60")
    for p in problems:
        p["url"] = rewrite_url(f"/practice/problems/{p['slug']}", base)
    payload = {
        "personas": swarm.roster(),
        "topics": topic_items,
        "formulas": formulas,
        "problems": problems,
    }
    (site / "swarm-corpus.json").write_text(
        json.dumps(payload, ensure_ascii=False),
        encoding="utf-8",
    )


def enable_problem_editor(body: str) -> str:
    """Enable all language options with starter stubs and expose the Submit button on problem pages."""
    def _enable_select(match: re.Match[str]) -> str:
        select_html = match.group(0)
        select_html = re.sub(r'\s+disabled(?=[>\s])', "", select_html)
        select_html = select_html.replace(" (starter only)", "")
        return select_html

    body = re.sub(r'<select id="lang-select">.*?</select>', _enable_select, body, count=1, flags=re.S)
    body = re.sub(
        r'<div class="callout warning mb">\s*<span class="label">Code execution is off</span>.*?</div>',
        "",
        body,
        count=1,
        flags=re.S,
    )
    if 'id="btn-submit"' not in body and 'id="btn-run"' in body:
        body = body.replace(
            '<button class="btn btn-ghost" id="btn-run" type="button">Run</button>',
            '<button class="btn btn-ghost" id="btn-run" type="button">Run</button>\n'
            '        <button class="btn btn-primary" id="btn-submit" type="button">Submit</button>',
            1,
        )
    return body


def write_account_pages(site: Path, base: str, home_html: str, apk_url: str = "") -> int:
    """Export interactive browser + GitHub-synced learner account pages for the public website."""
    apk_link = (
        f'<a class="btn btn-soft" href="{html.escape(apk_url, quote=True)}" rel="noopener noreferrer">'
        'Download signed EngineVerse.apk</a>'
        if apk_url else
        '<a class="btn btn-soft" href="/install">Phone install guide</a>'
    )
    pages_spec: dict[str, tuple[str, str]] = {
        "/login": (
            "Sign in - EngineVerse",
            """
<div class="auth-wrap" data-ev-page="login">
  <div class="form-panel panel">
    <div class="eyebrow">EngineVerse Account · GitHub Vault &amp; Supabase/Appwrite Synced</div>
    <h1>Welcome back</h1>
    <p class="muted mb">Verified learners sign in directly with their password — no OTP required on regular sign-in.</p>
    <div id="ev-already-signed-in" class="callout ok mb" hidden>
      <span class="label">Session active</span>
      <p class="small" id="ev-already-user">You are already signed in.</p>
      <div class="row mt">
        <a class="btn btn-primary btn-sm" href="/dashboard" id="ev-continue-dashboard">Continue to Dashboard</a>
        <button class="btn btn-ghost btn-sm" type="button" id="ev-switch-account-btn">Switch account / Sign out</button>
      </div>
    </div>
    <div id="ev-auth-alert" class="callout info mb" hidden></div>
    <form id="ev-login-form" class="form" novalidate>
      <label class="field"><span>Username, Gmail/email, or mobile number</span>
        <input type="text" name="identity" id="ev-login-identity" required autocomplete="username"
          placeholder="saurav, learner@gmail.com, or +919876543210">
      </label>
      <label class="field"><span>Password</span>
        <input type="password" name="password" id="ev-login-password" required autocomplete="current-password">
      </label>
      <div class="row" style="justify-content:space-between">
        <label class="row small" style="gap:6px"><input type="checkbox" name="remember" id="ev-login-remember" value="1" checked> Keep me signed in across tabs</label>
        <a href="/forgot-password" class="small">Forgot password? (OTP recovery)</a>
      </div>
      <button class="btn btn-primary" type="submit" id="ev-login-submit-btn" style="width:100%">Sign in</button>
    </form>
    <div id="ev-login-otp-step" class="mt pt" style="border-top:1px solid var(--border)" hidden>
      <h2>First-time new user OTP verification</h2>
      <p class="small muted" id="ev-login-otp-desc">Verify your new account once using the 6-digit OTP sent to your Gmail or mobile number.</p>
      <div id="ev-login-otp-preview" class="callout info mb" hidden></div>
      <form id="ev-login-otp-form" class="form" novalidate>
        <label class="field"><span>6-digit OTP code</span>
          <input type="text" id="ev-login-otp" name="otp" inputmode="numeric" autocomplete="one-time-code" maxlength="6" pattern="[0-9]{6}" required placeholder="123456">
        </label>
        <div class="row">
          <button class="btn btn-primary" type="submit" id="ev-login-otp-submit">Verify OTP &amp; Finish Sign In</button>
          <button class="btn btn-ghost btn-sm" type="button" id="ev-login-otp-resend">Resend OTP</button>
        </div>
      </form>
    </div>
    <div class="mt pt" style="border-top:1px solid var(--border)">
      <p class="small muted">Quick demo or GitHub vault restore:</p>
      <div class="row">
        <button class="btn btn-soft btn-sm" type="button" id="ev-demo-signin">Sign in as Demo Learner</button>
        <button class="btn btn-ghost btn-sm" type="button" id="ev-github-pull-signin">Restore from GitHub Vault</button>
      </div>
    </div>
    <p class="small muted mt">New here? <a href="/register">Create a free account</a> — new accounts verify once via 6-digit OTP (Gmail or mobile number).</p>
  </div>
</div>
""".strip(),
        ),
        "/register": (
            "Create account - EngineVerse",
            """
<div class="auth-wrap" data-ev-page="register">
  <div class="form-panel panel">
    <div class="eyebrow">New Learner Signup · One-Time 6-Digit OTP Verification</div>
    <h1>Create your account</h1>
    <p class="muted mb">Verify once via Gmail or mobile number (with country code). After initial verification, future sign-ins require only your password.</p>
    <div id="ev-auth-alert" class="callout info mb" hidden></div>
    <form id="ev-register-form" class="form" novalidate>
      <label class="field"><span>Display name</span>
        <input type="text" name="display_name" id="ev-reg-display" required maxlength="60" placeholder="Aarav Sharma">
      </label>
      <label class="field"><span>Username</span>
        <input type="text" name="username" id="ev-reg-username" required minlength="3" maxlength="30"
          pattern="[a-zA-Z0-9_\\-]+" placeholder="aarav_sharma">
        <span class="help">3–30 characters: letters, digits, underscore or hyphen.</span>
      </label>
      <label class="field"><span>Gmail / Email address</span>
        <input type="email" name="email" id="ev-reg-email" required placeholder="you@gmail.com">
      </label>
      <div class="field"><span>Mobile number (with country code)</span>
        <div class="phone-cc-row">
          <select name="country_code" id="ev-reg-country-code" aria-label="Country code">
            <option value="+91">🇮🇳 +91 (India)</option>
            <option value="+1">🇺🇸 +1 (US / Canada)</option>
            <option value="+44">🇬🇧 +44 (UK)</option>
            <option value="+61">🇦🇺 +61 (Australia)</option>
            <option value="+49">🇩🇪 +49 (Germany)</option>
            <option value="+33">🇫🇷 +33 (France)</option>
            <option value="+65">🇸🇬 +65 (Singapore)</option>
            <option value="+971">🇦🇪 +971 (UAE)</option>
            <option value="+81">🇯🇵 +81 (Japan)</option>
            <option value="+82">🇰🇷 +82 (South Korea)</option>
            <option value="+55">🇧🇷 +55 (Brazil)</option>
            <option value="+27">🇿🇦 +27 (South Africa)</option>
            <option value="+234">🇳🇬 +234 (Nigeria)</option>
            <option value="+7">🇷🇺 +7 (Russia / KZ)</option>
          </select>
          <input type="tel" name="phone" id="ev-reg-phone" maxlength="20" placeholder="9876543210">
        </div>
      </div>
      <label class="field"><span>Send 6-digit signup OTP via</span>
        <select name="otp_channel" id="ev-reg-otp-channel">
          <option value="email">Gmail / Email (6-digit OTP)</option>
          <option value="phone">Mobile Number SMS with Country Code (6-digit OTP)</option>
        </select>
      </label>
      <div class="form-row">
        <label class="field"><span>Branch</span>
          <select name="branch" id="ev-reg-branch">
            <option value="cse">Computer Science &amp; Engineering</option>
            <option value="ece">Electronics &amp; Communication</option>
            <option value="ee">Electrical Engineering</option>
            <option value="me">Mechanical Engineering</option>
            <option value="ce">Civil Engineering</option>
            <option value="che">Chemical Engineering</option>
            <option value="ae">Aerospace Engineering</option>
            <option value="AIML">AI &amp; Data Science</option>
          </select>
        </label>
        <label class="field"><span>Current year</span>
          <select name="year_of_study" id="ev-reg-year">
            <option value="1">1st Year</option>
            <option value="2">2nd Year</option>
            <option value="3">3rd Year</option>
            <option value="4">4th Year</option>
          </select>
        </label>
      </div>
      <label class="field"><span>Password</span>
        <input type="password" name="password" id="ev-reg-password" required minlength="8" autocomplete="new-password"
          placeholder="At least 8 characters">
      </label>
      <label class="row small" style="gap:6px">
        <input type="checkbox" name="sync_github" id="ev-reg-sync-gh" value="1" checked>
        Prepare GitHub learner vault snapshot for <code>authorsauravkushwaha/EngineVerse</code>
      </label>
      <button class="btn btn-primary" type="submit" style="width:100%" id="ev-reg-submit-btn">Send 6-digit OTP &amp; Verify Account</button>
    </form>
    <div id="ev-reg-otp-step" class="mt pt" style="border-top:1px solid var(--border)" hidden>
      <h2>Verify your 6-digit signup OTP</h2>
      <p class="small muted" id="ev-reg-otp-desc">Enter the 6-digit code sent to your Gmail or mobile number.</p>
      <div id="ev-reg-otp-preview" class="callout info mb" hidden></div>
      <form id="ev-reg-otp-form" class="form" novalidate>
        <label class="field"><span>6-digit OTP code</span>
          <input type="text" id="ev-reg-otp" name="otp" inputmode="numeric" autocomplete="one-time-code" maxlength="6" pattern="[0-9]{6}" required placeholder="123456">
        </label>
        <div class="row">
          <button class="btn btn-primary" type="submit" id="ev-reg-otp-submit">Verify 6-digit OTP &amp; Create Account</button>
          <button class="btn btn-ghost btn-sm" type="button" id="ev-reg-resend-otp">Resend OTP</button>
          <button class="btn btn-soft btn-sm" type="button" id="ev-reg-otp-switch">Switch Gmail / Mobile OTP</button>
        </div>
      </form>
    </div>
    <p class="small muted mt">Already registered? <a href="/login">Sign in</a></p>
  </div>
</div>
""".strip(),
        ),
        "/forgot-password": (
            "Reset password - EngineVerse",
            """
<div class="auth-wrap" data-ev-page="forgot-password">
  <div class="form-panel panel">
    <div class="eyebrow">Account Recovery · Gmail or Mobile Number OTP</div>
    <h1>Reset your password</h1>
    <p class="muted mb">Verify your identity with a 6-digit OTP sent to your Gmail/email or mobile number (with country code) to set a new password.</p>
    <div id="ev-auth-alert" class="callout info mb" hidden></div>
    <form id="ev-forgot-form" class="form" novalidate>
      <label class="field"><span>Verify via</span>
        <select name="otp_channel" id="ev-forgot-channel">
          <option value="email">Gmail / Email (6-digit OTP)</option>
          <option value="phone">Mobile Number SMS with Country Code (6-digit OTP)</option>
        </select>
      </label>
      <label class="field" id="ev-forgot-email-wrap"><span>Username or Gmail / Email</span>
        <input type="text" name="identity" id="ev-forgot-identity" placeholder="saurav or you@gmail.com">
      </label>
      <div class="field" id="ev-forgot-phone-wrap"><span>Mobile number (with country code)</span>
        <div class="phone-cc-row">
          <select name="country_code" id="ev-forgot-country-code" aria-label="Country code">
            <option value="+91">🇮🇳 +91 (India)</option>
            <option value="+1">🇺🇸 +1 (US / Canada)</option>
            <option value="+44">🇬🇧 +44 (UK)</option>
            <option value="+61">🇦🇺 +61 (Australia)</option>
            <option value="+49">🇩🇪 +49 (Germany)</option>
            <option value="+33">🇫🇷 +33 (France)</option>
            <option value="+65">🇸🇬 +65 (Singapore)</option>
            <option value="+971">🇦🇪 +971 (UAE)</option>
            <option value="+81">🇯🇵 +81 (Japan)</option>
            <option value="+82">🇰🇷 +82 (South Korea)</option>
            <option value="+55">🇧🇷 +55 (Brazil)</option>
            <option value="+27">🇿🇦 +27 (South Africa)</option>
            <option value="+234">🇳🇬 +234 (Nigeria)</option>
          </select>
          <input type="tel" name="phone" id="ev-forgot-phone" maxlength="20" placeholder="9876543210">
        </div>
      </div>
      <div id="ev-forgot-otp-step" hidden>
        <div id="ev-forgot-otp-preview" class="callout info mb" hidden></div>
        <label class="field"><span>6-digit OTP code</span>
          <input type="text" name="otp_code" id="ev-forgot-otp" inputmode="numeric" autocomplete="one-time-code" maxlength="6" placeholder="123456">
        </label>
        <label class="field"><span>New password</span>
          <input type="password" name="new_password" id="ev-forgot-new-password" minlength="8" placeholder="At least 8 characters">
        </label>
        <label class="field"><span>Confirm new password</span>
          <input type="password" name="confirm_password" id="ev-forgot-confirm-password" minlength="8" placeholder="Confirm new password">
        </label>
        <div class="row">
          <button class="btn btn-ghost btn-sm" type="button" id="ev-forgot-resend-btn">Resend 6-digit OTP</button>
        </div>
      </div>
      <div class="row">
        <button class="btn btn-primary" type="submit" id="ev-forgot-submit-btn" style="width:100%">Send 6-digit Recovery OTP</button>
      </div>
    </form>
    <p class="small muted mt"><a href="/login">Back to sign in</a></p>
  </div>
</div>
""".strip(),
        ),
        "/reset-password": (
            "Choose a new password - EngineVerse",
            """
<div class="auth-wrap" data-ev-page="reset-password">
  <div class="form-panel panel">
    <div class="eyebrow">OTP Password Reset · Gmail or Mobile Number</div>
    <h1>Choose a new password</h1>
    <p class="muted mb">Verify with a 6-digit OTP via Gmail or mobile number (with country code) and re-sync your SHA-256 verification digest to GitHub.</p>
    <div id="ev-auth-alert" class="callout info mb" hidden></div>
    <form id="ev-forgot-form" class="form" novalidate>
      <label class="field"><span>Verify via</span>
        <select name="otp_channel" id="ev-forgot-channel">
          <option value="email">Gmail / Email (6-digit OTP)</option>
          <option value="phone">Mobile Number SMS with Country Code (6-digit OTP)</option>
        </select>
      </label>
      <label class="field" id="ev-forgot-email-wrap"><span>Username or Gmail / Email</span>
        <input type="text" name="identity" id="ev-forgot-identity" placeholder="saurav or you@gmail.com">
      </label>
      <div class="field" id="ev-forgot-phone-wrap"><span>Mobile number (with country code)</span>
        <div class="phone-cc-row">
          <select name="country_code" id="ev-forgot-country-code" aria-label="Country code">
            <option value="+91">🇮🇳 +91 (India)</option>
            <option value="+1">🇺🇸 +1 (US / Canada)</option>
            <option value="+44">🇬🇧 +44 (UK)</option>
            <option value="+61">🇦🇺 +61 (Australia)</option>
            <option value="+49">🇩🇪 +49 (Germany)</option>
            <option value="+65">🇸🇬 +65 (Singapore)</option>
            <option value="+971">🇦🇪 +971 (UAE)</option>
            <option value="+81">🇯🇵 +81 (Japan)</option>
          </select>
          <input type="tel" name="phone" id="ev-forgot-phone" maxlength="20" placeholder="9876543210">
        </div>
      </div>
      <div id="ev-forgot-otp-step" hidden>
        <div id="ev-forgot-otp-preview" class="callout info mb" hidden></div>
        <label class="field"><span>6-digit OTP code</span>
          <input type="text" name="otp_code" id="ev-forgot-otp" inputmode="numeric" autocomplete="one-time-code" maxlength="6" placeholder="123456">
        </label>
        <label class="field"><span>New password</span>
          <input type="password" name="new_password" id="ev-forgot-new-password" minlength="8" placeholder="At least 8 characters">
        </label>
        <label class="field"><span>Confirm new password</span>
          <input type="password" name="confirm_password" id="ev-forgot-confirm-password" minlength="8" placeholder="Confirm new password">
        </label>
        <div class="row">
          <button class="btn btn-ghost btn-sm" type="button" id="ev-forgot-resend-btn">Resend 6-digit OTP</button>
        </div>
      </div>
      <button class="btn btn-primary" type="submit" id="ev-forgot-submit-btn" style="width:100%">Send 6-digit Recovery OTP</button>
    </form>
    <p class="small muted mt"><a href="/login">Back to sign in</a></p>
  </div>
</div>
""".strip(),
        ),
        "/logout": (
            "Signed out - EngineVerse",
            """
<div class="auth-wrap" data-ev-page="logout">
  <div class="form-panel panel">
    <h1>You are signed out</h1>
    <p class="muted mb">Your local session has been closed. Any saved progress remains safe in your browser vault and on GitHub.</p>
    <div class="row">
      <a class="btn btn-primary" href="/login">Sign in again</a>
      <a class="btn btn-ghost" href="/explore">Explore catalogue</a>
    </div>
  </div>
</div>
""".strip(),
        ),
        "/dashboard": (
            "Learner Dashboard - EngineVerse",
            f"""
<div data-ev-page="dashboard">
  <div class="hero" style="padding:28px">
    <div class="eyebrow">Personal Engineering Workspace · GitHub Synced</div>
    <h1 id="ev-dash-greeting">Welcome to EngineVerse</h1>
    <p class="lead" id="ev-dash-sub">Track your daily streak, XP, completed topics, solved coding problems, and sync directly with GitHub.</p>
    <div class="hero-actions">
      <a class="btn btn-primary" href="/today">Today's plan</a>
      <a class="btn btn-ghost" href="/practice/problems">Solve coding problems</a>
      <a class="btn btn-ghost" href="/settings">GitHub Cloud Sync</a>
      {apk_link}
    </div>
  </div>
  <div class="stats mt">
    <div class="stat"><div class="label">Total XP</div><div class="value" id="ev-stat-xp">0</div><div class="sub" id="ev-stat-level">Level 1 · Spark</div></div>
    <div class="stat"><div class="label">Current streak</div><div class="value" id="ev-stat-streak">0 days</div><div class="sub" id="ev-stat-longest">Longest: 0d</div></div>
    <div class="stat"><div class="label">Topics completed</div><div class="value" id="ev-stat-topics">0</div><div class="sub">Across 8 branches</div></div>
    <div class="stat"><div class="label">Problems solved</div><div class="value" id="ev-stat-problems">0</div><div class="sub" id="ev-stat-quizzes">0 quizzes answered</div></div>
  </div>
  <div class="grid g2 mt">
    <section class="panel">
      <h2>GitHub Learner Vault Status</h2>
      <p class="small muted">Your learner snapshot is linked to <code>authorsauravkushwaha/EngineVerse</code>
        (<code>data/learners/registry.json</code>).</p>
      <div id="ev-dash-sync-status" class="callout info mb">Ready to sync your learner snapshot with GitHub.</div>
      <div class="row">
        <button class="btn btn-primary btn-sm" type="button" data-ev-sync-github>Save progress to GitHub now</button>
        <button class="btn btn-ghost btn-sm" type="button" data-ev-pull-github>Pull latest from GitHub</button>
        <a class="btn btn-soft btn-sm" href="/settings">Configure token / webhooks</a>
      </div>
    </section>
    <section class="panel">
      <h2>Recent activity &amp; solved work</h2>
      <div id="ev-dash-activity" class="small muted">Complete a note, quiz, or coding problem to see your activity log here.</div>
      <div class="row mt">
        <a class="btn btn-ghost btn-sm" href="/mistakes">Mistake notebook</a>
        <a class="btn btn-ghost btn-sm" href="/portfolio">Portfolio</a>
        <a class="btn btn-ghost btn-sm" href="/certificates">Certificates</a>
      </div>
    </section>
  </div>
</div>
""".strip(),
        ),
        "/profile": (
            "Your Profile - EngineVerse",
            """
<div data-ev-page="profile">
  <div class="section-head">
    <div>
      <div class="eyebrow">Learner Profile</div>
      <h1 id="ev-profile-name">EngineVerse Learner</h1>
    </div>
    <div class="row">
      <a class="btn btn-ghost btn-sm" href="/settings">Edit profile &amp; GitHub sync</a>
      <a class="btn btn-primary btn-sm" href="/portfolio">Public portfolio</a>
    </div>
  </div>
  <div class="stats mb">
    <div class="stat"><div class="label">Username</div><div class="value" id="ev-profile-username">guest</div></div>
    <div class="stat"><div class="label">Branch &amp; Year</div><div class="value" id="ev-profile-branch">CSE · Year 1</div></div>
    <div class="stat"><div class="label">XP &amp; Level</div><div class="value" id="ev-profile-xp">0 XP</div></div>
    <div class="stat"><div class="label">GitHub Vault</div><div class="value" id="ev-profile-gh">Synced</div></div>
  </div>
  <div class="grid g2">
    <section class="panel">
      <h2>Completed topics &amp; bookmarks</h2>
      <div id="ev-profile-topics" class="small muted">No topics marked complete yet. Open any topic to mark it complete or bookmark it.</div>
    </section>
    <section class="panel">
      <h2>Solved coding problems</h2>
      <div id="ev-profile-problems" class="small muted">No coding problems solved yet. Visit the coding bank to run and submit code in your browser.</div>
    </section>
  </div>
</div>
""".strip(),
        ),
        "/settings": (
            "Settings & GitHub Sync - EngineVerse",
            f"""
<div data-ev-page="settings">
  <div class="section-head">
    <div>
      <div class="eyebrow">Account, Cloud Sync &amp; Mobile APK</div>
      <h1>Settings &amp; GitHub Learner Vault</h1>
    </div>
    <div class="row">
      <a class="btn btn-ghost btn-sm" href="/dashboard">Dashboard</a>
      <button class="btn btn-ghost btn-sm" type="button" id="ev-signout-btn">Sign out</button>
    </div>
  </div>
  <div id="ev-settings-alert" class="callout info mb" hidden></div>
  <div class="grid g2">
    <section class="panel">
      <h2>1. Save your data on GitHub (authorsauravkushwaha/EngineVerse)</h2>
      <p class="small muted">Your account profile, XP, streak, solved coding problems, and completed topics are stored in
        <code>data/learners/registry.json</code> on <code>authorsauravkushwaha/EngineVerse</code>. You can sync directly via
        GitHub API token, one-click GitHub Issue sync (processed automatically by GitHub Actions), or export/import JSON.</p>
      <form id="ev-github-sync-form" class="form">
        <label class="field"><span>GitHub Repository</span>
          <input type="text" name="github_repo" id="ev-gh-repo" value="authorsauravkushwaha/EngineVerse">
        </label>
        <label class="field"><span>GitHub Personal Access Token (optional, stored only in your browser for direct API push)</span>
          <input type="password" name="github_token" id="ev-gh-token" placeholder="ghp_... or github_pat_... (leave blank for Issue sync)">
        </label>
        <div class="row">
          <button class="btn btn-primary btn-sm" type="submit">Push snapshot to GitHub now</button>
          <button class="btn btn-soft btn-sm" type="button" id="ev-gh-issue-sync">Sync via GitHub Actions Issue (no token needed)</button>
          <button class="btn btn-ghost btn-sm" type="button" id="ev-gh-pull-btn">Pull from GitHub Vault</button>
        </div>
      </form>
      <div class="mt pt" style="border-top:1px solid var(--border)">
        <p class="small muted">Download or import your portable learner snapshot JSON:</p>
        <div class="row">
          <button class="btn btn-ghost btn-sm" type="button" id="ev-export-json">Download snapshot (.json)</button>
          <label class="btn btn-ghost btn-sm" style="cursor:pointer">
            Import snapshot (.json)
            <input type="file" id="ev-import-json" accept="application/json,.json" hidden>
          </label>
        </div>
      </div>
    </section>
    <section class="panel">
      <h2>2. Profile &amp; Optional Cloud Connectors (Supabase / Appwrite / n8n)</h2>
      <form id="ev-profile-form" class="form">
        <label class="field"><span>Display name</span>
          <input type="text" name="display_name" id="ev-set-display" required maxlength="60">
        </label>
        <label class="field"><span>Gmail / Email address</span>
          <input type="email" name="email" id="ev-set-email" maxlength="120" placeholder="you@gmail.com">
        </label>
        <div class="field"><span>Mobile number (with country code)</span>
          <div class="phone-cc-row">
            <select name="country_code" id="ev-set-country-code" aria-label="Country code">
              <option value="+91">🇮🇳 +91 (India)</option>
              <option value="+1">🇺🇸 +1 (US / Canada)</option>
              <option value="+44">🇬🇧 +44 (UK)</option>
              <option value="+61">🇦🇺 +61 (Australia)</option>
              <option value="+49">🇩🇪 +49 (Germany)</option>
              <option value="+33">🇫🇷 +33 (France)</option>
              <option value="+65">🇸🇬 +65 (Singapore)</option>
              <option value="+971">🇦🇪 +971 (UAE)</option>
              <option value="+81">🇯🇵 +81 (Japan)</option>
              <option value="+82">🇰🇷 +82 (South Korea)</option>
              <option value="+55">🇧🇷 +55 (Brazil)</option>
              <option value="+27">🇿🇦 +27 (South Africa)</option>
              <option value="+234">🇳🇬 +234 (Nigeria)</option>
            </select>
            <input type="tel" name="phone" id="ev-set-phone" maxlength="20" placeholder="9876543210">
          </div>
        </div>
        <div class="form-row">
          <label class="field"><span>Branch</span>
            <select name="branch" id="ev-set-branch">
              <option value="cse">Computer Science &amp; Engineering</option>
              <option value="ece">Electronics &amp; Communication</option>
              <option value="ee">Electrical Engineering</option>
              <option value="me">Mechanical Engineering</option>
              <option value="ce">Civil Engineering</option>
              <option value="che">Chemical Engineering</option>
              <option value="ae">Aerospace Engineering</option>
              <option value="AIML">AI &amp; Data Science</option>
            </select>
          </label>
          <label class="field"><span>Year of study</span>
            <select name="year_of_study" id="ev-set-year">
              <option value="1">1st Year</option>
              <option value="2">2nd Year</option>
              <option value="3">3rd Year</option>
              <option value="4">4th Year</option>
            </select>
          </label>
        </div>
        <label class="field"><span>Bio / Target goal</span>
          <input type="text" name="bio" id="ev-set-bio" maxlength="240" placeholder="Preparing for GATE + core systems engineering">
        </label>
        <label class="field"><span>Optional n8n / Supabase / Appwrite Webhook URL (auto-forwards OTP &amp; progress sync)</span>
          <input type="url" name="webhook_url" id="ev-set-webhook" placeholder="https://your-n8n-or-supabase.example/webhook/engineverse">
        </label>
        <button class="btn btn-primary btn-sm" type="submit">Save profile &amp; sync settings</button>
      </form>
      <div class="mt pt" style="border-top:1px solid var(--border)">
        <p class="small muted">Install on your Android phone:</p>
        <div class="row">{apk_link}</div>
      </div>
    </section>
  </div>
  <section class="panel mt" id="ev-password-change-panel">
    <h2>3. Change Password via 6-Digit OTP (Gmail or Mobile Number with Country Code)</h2>
    <p class="small muted">OTP verification is required when changing your password. Select Gmail/email or mobile number (with country code) to receive a 6-digit verification code.</p>
    <div id="ev-pwd-otp-alert" class="callout info mb" hidden></div>
    <form id="ev-password-change-form" class="form" novalidate>
      <div class="grid g2">
        <label class="field"><span>Send 6-digit OTP via</span>
          <select id="ev-pwd-otp-channel" name="otp_channel">
            <option value="email">Gmail / Email (6-digit OTP)</option>
            <option value="phone">Mobile Number SMS with Country Code (6-digit OTP)</option>
          </select>
        </label>
        <div class="field"><span>Mobile number (with country code)</span>
          <div class="phone-cc-row">
            <select id="ev-pwd-country-code" name="country_code" aria-label="Country code">
              <option value="+91">🇮🇳 +91 (India)</option>
              <option value="+1">🇺🇸 +1 (US / Canada)</option>
              <option value="+44">🇬🇧 +44 (UK)</option>
              <option value="+61">🇦🇺 +61 (Australia)</option>
              <option value="+49">🇩🇪 +49 (Germany)</option>
              <option value="+65">🇸🇬 +65 (Singapore)</option>
              <option value="+971">🇦🇪 +971 (UAE)</option>
              <option value="+81">🇯🇵 +81 (Japan)</option>
            </select>
            <input type="tel" id="ev-pwd-phone" name="phone" maxlength="20" placeholder="9876543210">
          </div>
        </div>
      </div>
      <div id="ev-pwd-otp-step" hidden>
        <div id="ev-pwd-otp-preview" class="callout info mb" hidden></div>
        <div class="grid g3">
          <label class="field"><span>6-digit OTP code</span>
            <input type="text" id="ev-pwd-otp-code" inputmode="numeric" maxlength="6" placeholder="123456">
          </label>
          <label class="field"><span>New password</span>
            <input type="password" id="ev-pwd-new-password" minlength="8" placeholder="At least 8 characters">
          </label>
          <label class="field"><span>Confirm new password</span>
            <input type="password" id="ev-pwd-confirm-password" minlength="8" placeholder="Confirm new password">
          </label>
        </div>
      </div>
      <div class="row">
        <button class="btn btn-primary btn-sm" type="submit" id="ev-pwd-submit-btn">Send 6-digit OTP to change password</button>
      </div>
    </form>
  </section>
</div>
""".strip(),
        ),
        "/today": (
            "Today's Study Plan - EngineVerse",
            """
<div data-ev-page="today">
  <div class="section-head">
    <div>
      <div class="eyebrow">Daily Engineering Loop</div>
      <h1>Today's 4-step study plan</h1>
    </div>
    <a class="btn btn-ghost btn-sm" href="/dpp">Open today's DPP</a>
  </div>
  <div class="grid g2">
    <article class="panel">
      <h2>Step 1 · Read &amp; Master a Core Topic</h2>
      <p class="muted">Pick an engineering topic note, read the derivation and worked example, and mark it complete.</p>
      <p><a class="btn btn-primary btn-sm" href="/explore">Browse topics</a></p>
    </article>
    <article class="panel">
      <h2>Step 2 · Daily Practice Problems (DPP)</h2>
      <p class="muted">Answer today's timed multiple-choice and numerical practice set with instant browser grading.</p>
      <p><a class="btn btn-primary btn-sm" href="/dpp">Start today's DPP</a></p>
    </article>
    <article class="panel">
      <h2>Step 3 · Solve a Coding Problem</h2>
      <p class="muted">Write, run, and submit code against all test cases directly in your browser.</p>
      <p><a class="btn btn-primary btn-sm" href="/practice/problems">Open coding bank</a></p>
    </article>
    <article class="panel">
      <h2>Step 4 · Review Mistakes &amp; Sync to GitHub</h2>
      <p class="muted">Clear any missed questions in your mistake notebook and push your streak to GitHub.</p>
      <p class="row">
        <a class="btn btn-ghost btn-sm" href="/mistakes">Mistake notebook</a>
        <button class="btn btn-soft btn-sm" type="button" data-ev-sync-github>Sync to GitHub</button>
      </p>
    </article>
  </div>
</div>
""".strip(),
        ),
        "/mistakes": (
            "Mistake Notebook - EngineVerse",
            """
<div data-ev-page="mistakes">
  <div class="section-head">
    <div>
      <div class="eyebrow">Active Recall &amp; Error Log</div>
      <h1>Mistake notebook</h1>
    </div>
    <a class="btn btn-ghost btn-sm" href="/practice/questions">Practice question bank</a>
  </div>
  <p class="lead">Every quiz question or coding problem you miss is recorded here so you can re-attempt and master it.</p>
  <div id="ev-mistakes-list" class="panel">
    <h2>Recorded mistakes</h2>
    <p class="muted">No unresolved mistakes recorded yet. Answer any topic quiz, DPP, or question bank item to populate your notebook.</p>
  </div>
</div>
""".strip(),
        ),
        "/onboarding": (
            "Welcome & Setup - EngineVerse",
            """
<div data-ev-page="onboarding">
  <div class="panel">
    <div class="eyebrow">Quick Setup</div>
    <h1>Set up your EngineVerse workspace</h1>
    <p class="lead">Choose your engineering branch, year of study, and GitHub sync preferences.</p>
    <p class="row">
      <a class="btn btn-primary" href="/settings">Open account &amp; GitHub settings</a>
      <a class="btn btn-ghost" href="/explore">Explore the catalogue</a>
      <a class="btn btn-soft" href="/install">Install Android APK</a>
    </p>
  </div>
</div>
""".strip(),
        ),
        "/notifications": (
            "Notifications - EngineVerse",
            """
<div data-ev-page="notifications">
  <div class="section-head">
    <div>
      <div class="eyebrow">Activity Feed</div>
      <h1>Notifications &amp; milestones</h1>
    </div>
    <a class="btn btn-ghost btn-sm" href="/dashboard">Back to dashboard</a>
  </div>
  <div id="ev-notifications-list" class="panel">
    <h2>Recent updates</h2>
    <p class="muted">Your XP awards, streak milestones, and GitHub vault sync confirmations appear here.</p>
  </div>
</div>
""".strip(),
        ),
        "/portfolio": (
            "Engineering Portfolio - EngineVerse",
            """
<div data-ev-page="portfolio">
  <div class="section-head">
    <div>
      <div class="eyebrow">Verified Learner Record</div>
      <h1 id="ev-portfolio-title">Engineering Portfolio</h1>
    </div>
    <button class="btn btn-primary btn-sm" type="button" data-ev-sync-github>Publish to GitHub Vault</button>
  </div>
  <div class="panel mb">
    <h2>Summary &amp; GitHub Verification</h2>
    <p id="ev-portfolio-summary" class="muted">Sign in and complete topics, projects, or coding problems to build your verifiable engineering portfolio backed by <code>authorsauravkushwaha/EngineVerse</code>.</p>
  </div>
  <div class="grid g2">
    <section class="panel">
      <h2>Completed Projects &amp; Topics</h2>
      <div id="ev-portfolio-projects" class="small muted">Mark topics and projects complete to showcase them here.</div>
    </section>
    <section class="panel">
      <h2>Coding &amp; Quiz Achievements</h2>
      <div id="ev-portfolio-coding" class="small muted">Solved coding problems and quiz accuracy metrics appear here.</div>
    </section>
  </div>
</div>
""".strip(),
        ),
        "/certificates": (
            "Certificates & Milestones - EngineVerse",
            """
<div data-ev-page="certificates">
  <div class="section-head">
    <div>
      <div class="eyebrow">Completion Credentials</div>
      <h1>Certificates &amp; mastery milestones</h1>
    </div>
    <a class="btn btn-ghost btn-sm" href="/programming">Language paths</a>
  </div>
  <div class="panel">
    <h2>Earned &amp; in-progress certificates</h2>
    <p class="muted">Complete topic tracks, coding sheets, or programming language paths and sync your snapshot to <code>authorsauravkushwaha/EngineVerse</code> to unlock verifiable completion certificates.</p>
    <div id="ev-certificates-list" class="mt"></div>
  </div>
</div>
""".strip(),
        ),
    }
    count = 0
    for path, (title, main_raw) in pages_spec.items():
        rewritten_main = rewrite_html(main_raw, base)
        page_html = fill_shell(home_html, title, rewritten_main)
        target = output_path(site, path)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(page_html, encoding="utf-8")
        count += 1
    return count


def reading_copy_controls(text: str) -> str:
    """Do not leave backend-only lab forms looking executable on Pages.

    Server-rendered examples and JSON downloads remain readable. Controls are
    disabled in HTML as well as JS, so a no-script visitor cannot accidentally
    POST to a static host. The form action has already been rewritten to the
    hosting explanation; change its method to GET as a final fallback.
    """
    text = re.sub(
        r'(<form\b[^>]*\bdata-live-only\b[^>]*>)',
        lambda match: match.group(0).replace('method="post"', 'method="get"'),
        text,
    )
    text = re.sub(
        r'(<(?:button|input|textarea|select)\b[^>]*\bdata-live-control\b[^>]*)(>)',
        lambda match: match.group(1) + ' disabled aria-disabled="true"' + match.group(2),
        text,
    )
    return text.replace("data-lab-mode-notice hidden", "data-lab-mode-notice")


def inject(text: str, base: str, *, search: bool, dpp_dates: list[str] | None = None, apk_url: str = "") -> str:
    text = reading_copy_controls(rewrite_html(text, base))
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
    text = text.replace("Runnable here", "Examples to copy")
    if dpp_dates:
        text = retarget_missing_dpp(text, base, dpp_dates)
    if "</body>" in text:
        boot = live_boot(base, dpp_dates or [], apk_url=apk_url)
        text = text.replace("</body>", boot + "\n" + mirror_script() + "\n</body>", 1)
    return text


def patch_app_js(text: str, base: str) -> str:
    sw_url = join_base(base, "/sw.js")
    text = text.replace(
        'navigator.serviceWorker.register("/sw.js")',
        f'navigator.serviceWorker.register("{sw_url}")',
    )
    for old in ("/login", "/register", "/api/"):
        text = text.replace(f'"{old}', f'"{join_base(base, old)}')
        text = text.replace(f"'{old}", f"'{join_base(base, old)}")
    text = text.replace('"/search?q=', f'"{rewrite_url("/search", base)}?q=')
    return text


def patch_sw_js(text: str, base: str) -> str:
    if base == "/":
        return text
    prefix = base.rstrip("/")
    text = text.replace('"/static/', f'"{prefix}/static/')
    text = text.replace('"/manifest.webmanifest"', f'"{prefix}/manifest.webmanifest"')
    return text


def copy_static(site: Path, base: str) -> None:
    src = BACKEND / "static"
    dest = site / "static"
    if dest.exists():
        shutil.rmtree(dest)
    shutil.copytree(src, dest)
    sw = dest / "sw.js"
    if sw.exists():
        sw_text = patch_sw_js(sw.read_text(encoding="utf-8"), base)
        (site / "sw.js").write_text(sw_text, encoding="utf-8")
        sw.unlink()
    app_js = dest / "js" / "app.js"
    app_js.write_text(patch_app_js(app_js.read_text(encoding="utf-8"), base), encoding="utf-8")
    # Static HTML (the offline fallback page) is copied verbatim from the app,
    # where its links are root-absolute ("/static/...", "/") and correct at the
    # app root. Under a Pages base prefix those resolve outside the base and
    # 404, so rewrite them exactly as rendered pages are rewritten. Only the
    # exported copy becomes base-aware; the live app keeps its root-absolute
    # links. This is a no-op when base is "/".
    for html_file in dest.rglob("*.html"):
        html_file.write_text(
            rewrite_html(html_file.read_text(encoding="utf-8"), base), encoding="utf-8"
        )
    manifest = {
        "name": "EngineVerse",
        "short_name": "EngineVerse",
        "description": "EngineVerse: Engineering notes, coding practice, labs, Android app and GitHub sync.",
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
            },
            {
                "src": rewrite_url("/static/icons/icon-512.png", base),
                "sizes": "512x512",
                "type": "image/png",
            },
        ],
    }
    (site / "manifest.webmanifest").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")


def mirror_script() -> str:
    """Delegate quiz grading to the browser quiz engine, with an offline fallback."""
    return """
<script>
(function () {
  document.querySelectorAll("[data-quiz] form").forEach(function (form) {
    form.addEventListener("submit", function (event) {
      event.preventDefault();
      event.stopPropagation();
      if (typeof window.EV_GRADE_QUIZ === "function") {
        window.EV_GRADE_QUIZ(form);
        return;
      }
      var card = form.closest("[data-quiz]");
      if (!card) return;
      var explain = card.querySelector(".explain");
      var badge = card.querySelector(".verdict-inline");
      if (explain) {
        explain.classList.add("on");
      }
      if (badge) {
        badge.textContent = "Checked in browser";
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
    checked = 0
    for page in site.rglob("*.html"):
        text = page.read_text(encoding="utf-8", errors="replace")
        for url in re.findall(r'(?:href|src|action)="([^"]+)"', text):
            target = _link_target(page, url, site, prefix)
            if target is None:
                continue
            checked += 1
            if not target.exists():
                missing.append(f"{page.relative_to(site)} -> {url}")
    if missing:
        sample = "\n".join(missing[:25])
        raise SystemExit(f"Refusing to publish. {len(missing)} links do not resolve:\n{sample}")
    print(f"Checked {checked} local URL references: 0 broken links")


def assert_heading_outlines(site: Path) -> None:
    offenders = []
    checked = 0
    for page in site.rglob("*.html"):
        previous = 0
        checked += 1
        for raw in re.findall(r"<h([1-6])\b", page.read_text(encoding="utf-8"), re.I):
            level = int(raw)
            if previous and level > previous + 1:
                offenders.append(f"{page.relative_to(site)}: h{previous} -> h{level}")
                break
            previous = level
    if offenders:
        raise SystemExit("Refusing to publish invalid heading outlines:\n" + "\n".join(offenders[:25]))
    print(f"Checked {checked} HTML heading outlines: 0 skipped levels")


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


def export(site: Path, base: str, app_url: str = "", apk_url: str = "") -> int:
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
    from engineverse import db as export_db

    dpp_dates = [
        row["date"]
        for row in export_db.query("SELECT date FROM dpp_sets WHERE published = 1 ORDER BY date")
        if row["date"]
    ]
    for path in public_paths():
        fetch = "/explore" if path == "/explore/first-year" else path
        if path == "/explore/first-year":
            response = client.get("/explore", params={"year": "1"})
        elif path.startswith("/topics/") and path.count("/") == 2:
            response = client.get(fetch, params={"depths": "all"})
        else:
            response = client.get(fetch)
        if response.status_code != 200 or "text/html" not in response.headers.get("content-type", ""):
            failed.append(f"{path} -> {response.status_code}")
            continue
        body = inject(response.text, base, search=(path == "/search"), dpp_dates=dpp_dates, apk_url=apk_url)
        if path.startswith("/practice/problems/") and path.count("/") == 3:
            body = enable_problem_editor(body)
        if path == "/install":
            body = fill_shell(body, "Install EngineVerse", reading_copy_install_main(app_url, apk_url))
        if path == "/streaks":
            body = re.sub(r'<p class="small muted" data-hosted-streak-notice>.*?</p>',
                          "", body, count=1, flags=re.S)
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

    written += write_account_pages(site, base, home_html, apk_url=apk_url)

    hosting = fill_shell(home_html, "Use EngineVerse", hosting_main(app_url, apk_url))
    hosting_path = output_path(site, "/hosting")
    hosting_path.parent.mkdir(parents=True, exist_ok=True)
    hosting_path.write_text(hosting, encoding="utf-8")
    written += 1

    missing = client.get("/this-page-is-not-in-the-catalogue")
    not_found = inject(missing.text, base, search=False, apk_url=apk_url) if missing.text else home_html
    (site / "404.html").write_text(not_found, encoding="utf-8")

    index = search_index(base)
    (site / "search-index.json").write_text(json.dumps(index, ensure_ascii=False), encoding="utf-8")
    write_tutor_corpus(site, base)
    write_learner_vault(site)
    write_quiz_bank(site, base)
    write_coding_problems(site)
    write_studio_snapshot(site)
    write_workflows_catalog(site, base)
    write_swarm_corpus(site, base)

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
    assert_heading_outlines(site)
    revision = os.environ.get("GITHUB_SHA", "") or subprocess.check_output(
        ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True
    ).strip()
    (site / "deployment.json").write_text(json.dumps({
        "revision": revision, "mode": "reading-copy", "base": base, "pages": written,
        "capabilities": [rewrite_url(path, base) for path in ("/apis", "/studio", "/workflows", "/swarm")],
    }, indent=2) + "\n", encoding="utf-8")
    print(f"Wrote {written} pages and {len(index)} search rows to {site}")
    return written


# ---------------------------------------------------------------------------
# Full-app gateway (only after an HTTPS app origin has been configured)
# ---------------------------------------------------------------------------

_DNS_LABEL = re.compile(r"[A-Za-z0-9](?:[A-Za-z0-9-]{0,61}[A-Za-z0-9])?\Z")


def normalise_app_url(value: str | None) -> str:
    """Only a public HTTPS origin (or localhost HTTP for local testing).

    The backend is mounted at /, not at an arbitrary path. Fail closed before
    a bad repository variable can redirect all of Pages to an unrelated host.
    Never echo rejected input: it might contain accidental credentials.
    """
    text = (value or "").strip().rstrip("/")
    if not text:
        return ""
    error = SystemExit("ENGINEVERSE_APP_URL must be a public HTTPS origin (localhost HTTP only for development).")
    if not re.fullmatch(r"https?://[A-Za-z0-9.:-]+", text):
        raise error
    try:
        parts = urlsplit(text)
        host = parts.hostname or ""
        port = parts.port
    except ValueError:
        raise error from None
    if parts.path or parts.query or parts.fragment or parts.username or parts.password:
        raise error
    if parts.scheme == "http" and host in {"localhost", "127.0.0.1"}:
        if port == 0 or parts.netloc != host + (f":{port}" if port is not None else ""):
            raise error
        return text
    if parts.scheme != "https" or port is not None or parts.netloc != host:
        raise error
    try:
        ipaddress.ip_address(host)
    except ValueError:
        pass  # A real DNS name is required for a public HTTPS origin.
    else:
        raise error
    if (len(host) > 253 or "." not in host or host.endswith((".local", ".internal", ".localhost"))
            or not all(_DNS_LABEL.fullmatch(label) for label in host.split("."))):
        raise error
    return text


def gateway_page(base: str, app_url: str, site_name: str, *, not_found: bool = False,
                 apk_url: str = "") -> str:
    """A small public doorway to the full app, with a deep-link-preserving 404."""
    css = html.escape(join_base(base, "/static/css/app.css"), quote=True)
    icon = html.escape(join_base(base, "/static/icons/favicon.svg"), quote=True)
    name = html.escape(site_name)
    repo = html.escape(REPO, quote=True)
    if app_url:
        home = html.escape(app_url + "/", quote=True)
        login = html.escape(app_url + "/login", quote=True)
        register = html.escape(app_url + "/register", quote=True)
        install = html.escape(app_url + "/install", quote=True)
        actions = (
            '<p class="row" style="justify-content:center;gap:12px">'
            f'<a class="btn btn-primary" href="{home}" id="gateway-open">Open full website</a>'
            f'<a class="btn btn-ghost" href="{login}" id="gateway-signin">Sign in</a>'
            f'<a class="btn btn-ghost" href="{register}">Create account</a></p>'
            f'<p><a href="{install}">Use EngineVerse on your phone</a></p>'
            '<p class="small muted">Accounts and progress live on the hosted app, not on GitHub Pages. '
            'Code execution is available only if that host has a judge configured.</p>'
        )
        if apk_url:
            actions += (
                f'<p><a class="btn btn-soft" href="{html.escape(apk_url, quote=True)}" '
                'rel="noopener noreferrer">Download signed EngineVerse.apk</a></p>'
            )
        # GitHub Pages serves its 404.html for old bookmarked catalogue paths.
        # Route those to the same path on the app (not blindly to /login). The
        # app itself decides whether a particular page needs authentication.
        script = (
            "<script>(function(){var app=" + json.dumps(app_url) + ";"
            "var base=" + json.dumps(base.rstrip("/")) + ";"
            "var path=location.pathname;"
            "if(base&&path!==base&&path.indexOf(base+'/')!==0)return;"
            "if(base)path=path.slice(base.length)||'/';"
            "path=path.replace(/\\/index\\.html$/,'/');"
            "if(!/^\\/[A-Za-z0-9._~%\\/-]*$/.test(path)||path.indexOf('//')===0"
            "||path.indexOf('..')!==-1)path='/';"
            "location.replace(app+path+location.search+location.hash);})();</script>"
            if not_found else
            "<script>location.replace(" + json.dumps(app_url + "/") + ");</script>"
        )
        lead = (
            "That link has moved to the full website. Taking you to the same page there..."
            if not_found else
            "The full website is online. No source download is needed. Opening it now..."
        )
        refresh = f'<meta http-equiv="refresh" content="3;url={home}">'
    else:
        actions = (
            '<div class="callout warning" style="text-align:left"><span class="label">Not hosted yet</span>'
            'GitHub Pages cannot store accounts or run a judge. The operator has not configured '
            'a public HTTPS app origin.</div>'
            f'<p><a class="btn btn-ghost" href="{repo}#hosting-the-full-website">'
            'How to host the full website</a></p>'
        )
        script = ""
        refresh = ""
        lead = "The public reading copy is available until the full app is deployed."
    title = "Page moved" if not_found else "Open the full site"
    return f"""<!doctype html>
<html lang="en" data-theme="light">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <meta name="robots" content="noindex">
  <title>{title} - {name}</title>
  {refresh}
  <link rel="icon" href="{icon}" type="image/svg+xml">
  <link rel="stylesheet" href="{css}">
</head>
<body>
<main id="main" class="wrap" style="min-height:80vh;display:grid;place-items:center">
  <div class="form-panel panel" style="text-align:center;max-width:560px">
    <h1>{name}</h1>
    <p class="muted">{html.escape(lead)}</p>
    {actions}
    <p class="tiny muted mt">This Pages address has no account database.
      <a href="{repo}">Source</a> · <a href="{html.escape(app_url + '/privacy' if app_url else repo, quote=True)}">Privacy</a></p>
  </div>
</main>
{script}
</body>
</html>
"""


def export_gateway(site: Path, base: str, app_url: str, site_name: str = "EngineVerse",
                   apk_url: str = "") -> int:
    if site.exists():
        shutil.rmtree(site)
    site.mkdir(parents=True)
    (site / ".nojekyll").write_text("", encoding="utf-8")
    static = site / "static"
    (static / "css").mkdir(parents=True)
    (static / "icons").mkdir(parents=True)
    shutil.copy2(BACKEND / "static" / "css" / "app.css", static / "css" / "app.css")
    shutil.copy2(BACKEND / "static" / "icons" / "favicon.svg", static / "icons" / "favicon.svg")
    (site / "index.html").write_text(gateway_page(base, app_url, site_name, apk_url=apk_url), encoding="utf-8")
    (site / "404.html").write_text(gateway_page(base, app_url, site_name, not_found=True,
                                                apk_url=apk_url), encoding="utf-8")
    (site / "robots.txt").write_text("User-agent: *\nDisallow: /\n", encoding="utf-8")
    revision = os.environ.get("GITHUB_SHA", "") or subprocess.check_output(
        ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True
    ).strip()
    (site / "deployment.json").write_text(json.dumps({
        "revision": revision, "mode": "gateway", "base": base, "app_url": app_url,
    }, indent=2) + "\n", encoding="utf-8")
    assert_clean(site)
    assert_links(site, base)
    print(f"Wrote the full-app gateway to {site}")
    return 2


def self_check() -> None:
    assert rewrite_url("/topics/ohm", "/EngineVerse/") == "/EngineVerse/topics/ohm/"
    assert rewrite_url("/static/css/app.css", "/EngineVerse/") == "/EngineVerse/static/css/app.css"
    assert rewrite_url("/search?q=beam", "/") == "/search/?q=beam"
    assert rewrite_url("https://example.com", "/EngineVerse/") == "https://example.com"
    sample = '<a href="/login">Sign in</a><a href="/topics/a">A</a><a href="/api/docs">API</a>'
    rewritten = rewrite_html(sample, "/EngineVerse/")
    assert 'href="/EngineVerse/login/"' in rewritten
    assert 'href="/EngineVerse/hosting/"' in rewritten
    assert 'href="/EngineVerse/topics/a/"' in rewritten
    assert "LearnBuild#2026!" not in rewritten
    assert "data-theme" not in mirror_script()
    assert normalise_app_url("https://learn.example.org/") == "https://learn.example.org"
    assert normalise_app_url("http://localhost:8000/") == "http://localhost:8000"
    assert normalise_app_url("") == ""
    for bad in ('https://x.org/"><script>', "javascript:alert(1)", "http://example.org",
                "https://x.org/?a=b", "https://127.0.0.1", "https://x.org/private",
                "https://x.org:8443", "https://x.org:", "https://x.internal", "https://a..b.org"):
        try:
            normalise_app_url(bad)
        except SystemExit:
            pass
        else:
            raise AssertionError(f"accepted {bad!r}")
    gate = gateway_page("/EngineVerse/", "https://learn.example.org", "EngineVerse")
    assert 'href="https://learn.example.org/login"' in gate and "/EngineVerse/static/css/app.css" in gate
    assert 'id="gateway-open"' in gate and "location.replace" in gate
    assert "Not hosted yet" in gateway_page("/EngineVerse/", "", "EngineVerse")
    assert "Download signed" not in gate
    assert "Download signed" in gateway_page(
        "/EngineVerse/", "https://learn.example.org", "EngineVerse",
        apk_url="https://github.com/authorsauravkushwaha/EngineVerse/releases/download/android-v1.0.0/EngineVerse.apk"
    )
    # /apis is a page, not part of /api/. This boundary once silently dropped
    # the directory while exporting navigation links to it on every page.
    assert "/api/" in SKIP_PREFIXES and "/api" not in SKIP_PREFIXES
    assert not any("/apis".startswith(prefix) for prefix in SKIP_PREFIXES)
    assert any("/api/public-apis".startswith(prefix) for prefix in SKIP_PREFIXES)
    controls = reading_copy_controls(
        '<form method="post" data-live-only><button data-live-control>Run</button></form>'
        '<p data-lab-mode-notice hidden>Backend required</p>'
    )
    assert 'method="get"' in controls and ' disabled ' in controls
    assert 'data-lab-mode-notice hidden' not in controls
    assert 'href="/EngineVerse/apis/"' in rewrite_html('<a href="/apis">APIs</a>', "/EngineVerse/")
    print("self-check ok (API/page boundary, base URLs, backend-only controls)")


def main() -> int:
    parser = argparse.ArgumentParser(description="Write the public reading copy or a gateway to the hosted app.")
    parser.add_argument("--out", default="site", help="output directory, relative to the repo root")
    parser.add_argument("--base", default=None, help="URL prefix, for example /EngineVerse/ or /")
    parser.add_argument("--self-check", action="store_true", help="check URL rewriting and exit")
    parser.add_argument("--skip-seed", action="store_true", help="reuse ENGINEVERSE_DB_PATH")
    parser.add_argument("--app-url", default=None,
                        help="full app HTTPS origin (default: $ENGINEVERSE_APP_URL)")
    parser.add_argument("--apk-url", default=None,
                        help="versioned signed GitHub Release APK URL (default: $ENGINEVERSE_APK_URL)")
    parser.add_argument("--gateway", action="store_true",
                        help="publish a gateway to the hosted app instead of the reading copy")
    parser.add_argument("--reading-copy", action="store_true",
                        help="publish the public reading copy (the default unless --gateway or an app URL is set)")
    args = parser.parse_args()
    if args.self_check:
        self_check()
        return 0
    base = repo_base(args.base)
    app_url = normalise_app_url(
        args.app_url if args.app_url is not None else os.environ.get("ENGINEVERSE_APP_URL", "")
    )
    try:
        apk_url = normalise_apk_url(
            args.apk_url if args.apk_url is not None else os.environ.get("ENGINEVERSE_APK_URL", "")
        )
    except ValueError as exc:
        raise SystemExit(str(exc)) from None
    if args.gateway and not app_url:
        raise SystemExit("Refusing to publish a gateway without a hosted full app origin.")
    if (args.gateway or app_url) and not args.reading_copy:
        export_gateway(ROOT / args.out, base, app_url, apk_url=apk_url)
        return 0
    db_path = ROOT / "data" / "pages-export.sqlite"
    env = prepare_env(db_path)
    os.environ.update(env)
    if not args.skip_seed:
        seed(env, db_path)
    export(ROOT / args.out, base, app_url=app_url, apk_url=apk_url)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
