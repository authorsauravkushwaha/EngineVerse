# Architecture

EngineVerse is one deployable unit: a Python web application over a SQL data
layer, with a separate JVM process for executing learner code. There is no
message broker, no search service, no CDN and no SaaS dependency — everything
runs on hardware you control.

```
                        ┌────────────────────────────────────────────┐
   browser / PWA ──────►│  Python (FastAPI + Jinja2 SSR)             │
   (no build step)      │                                            │
                        │  web/pages.py       ~50 server-rendered    │
                        │  web/auth_pages.py  auth + settings + CMS  │
                        │  web/api.py         37 JSON endpoints      │
                        │  engineverse/*      services & domain      │
                        └───────┬───────────────────────┬────────────┘
                                │                       │
                    ┌───────────▼──────────┐   ┌────────▼─────────────┐
                    │ SQL                  │   │ Java sandbox (JVM)   │
                    │ SQLite   (dev)       │   │ one process per run  │
                    │ Postgres (prod,      │   │ javac + killable     │
                    │   hash-partitioned)  │   │ child, no deps       │
                    └──────────────────────┘   └──────────────────────┘
```

## Why this shape

**Server-side rendering.** Every page is HTML from Jinja2. There is no client
bundle to build, no hydration step, and no CDN — `backend/static/js/app.js` is
one dependency-free file that adds progressive enhancement (search suggestions,
the code editor, flashcard flipping, PWA install). If JavaScript is disabled,
the site still reads and still works. That is also what makes the app
installable on a phone without an app store: `manifest.webmanifest` plus a
service worker.

**One process, one database.** A learner platform is dominated by reads of
content that changes rarely. Splitting it into services early would add latency
and operational surface without relieving a real bottleneck. The seams that
*matter* are already clean — services in `engineverse/` never import from
`web/`, and the data layer is behind `engineverse/db.py` — so extracting a
service later is a refactor, not a rewrite.

**SQL as the data layer, not an ORM.** Queries are explicit SQL in the service
modules, so the query that runs is the query you can read. `db.py` translates
`?` placeholders to `%s` for Postgres, which is the only dialect difference the
rest of the codebase sees.

## Module map

| Path | Responsibility |
|---|---|
| `engineverse/config.py` | Frozen settings, `.env` loading, environment predicates |
| `engineverse/db.py` | Connection handling, transactions, migration, SQLite/Postgres |
| `engineverse/auth.py` | Registration, login, sessions, profiles, roles |
| `engineverse/security/` | Passwords, ids, sanitising, RBAC, audit, sessions, CSRF, rate limits, validation |
| `engineverse/catalog.py` | Branches → subjects → topics → notes → diagrams → formulas |
| `engineverse/practice.py` | Questions, DPP sets, grading, the mistake notebook |
| `engineverse/coding.py` | Coding problems, stubs, run/submit, XP awards |
| `engineverse/drivers.py` | The stdin/stdout harness appended to each submission |
| `engineverse/judge/` | Sandbox providers: local, Java bridge, Judge0 |
| `engineverse/library.py` | Videos, books, resources, flashcards |
| `engineverse/srs.py` | SM-2 spaced repetition scheduling |
| `engineverse/progress.py` | XP, levels, streaks, heatmaps, badges, certificates |
| `engineverse/search.py` | Fuzzy search over the SQL full-text index |
| `engineverse/recommend.py` | Weak-topic detection and next-step suggestions |
| `engineverse/community.py` | Threads, comments, votes, reports |
| `engineverse/markdown.py` | Markdown + LaTeX rendering with **no dependency** |
| `engineverse/brand.py` | Site-wide branding read from `site_config` |
| `web/deps.py` | Request-scoped viewer, template context, filters |
| `seed_data/`, `scripts/seed.py` | The seeded catalogue and demo accounts |

## Request lifecycle

1. **`SecurityHeadersMiddleware`** — mints a per-request CSP nonce onto
   `request.state.csp_nonce`, then sets X-Frame-Options, nosniff, Referrer-Policy,
   Permissions-Policy, COOP/CORP, and HSTS when the request is HTTPS.
2. **`RateLimitMiddleware`** — sliding window, 30/min for the judge and 300/min
   for the rest of `/api`.
3. **`CsrfMiddleware`** — rejects state-changing requests without a valid token,
   read from the `x-csrf-token` header *or* the `csrf_token` form field (an HTML
   form cannot set a header).
4. **Router** — resolves the current session into a `Viewer`, calls services,
   renders a template.

Templates never touch the database. Everything they need arrives through
`deps.base_context()`, which supplies `brand`, `user`, `csrf_token`, `flash`,
`due_cards`, `unread` and `stats`.

## The judge

Submissions never run in the web process. `engineverse/judge` picks a provider:

- **`local`** — runs the program in a scrubbed child process with CPU, memory,
  file-size and wall-clock ceilings, no writable path outside a temp directory,
  and no outbound network. Used for Python, JavaScript, C, C++ and Bash.
- **`java-sandbox`** — shells out to `sandbox-java/`, which compiles with the
  ToolProvider API and runs the result in a second, killable JVM.
- **`judge0`** — an optional bridge for deployments that want a dedicated judge
  host. It is not required and nothing depends on it.

A coding stub only *declares* an entry point, so nothing would call it. Each
problem therefore names a wrapper (`coding_problems.wrapper`) and
`drivers.compose()` appends a driver that reads stdin, calls the entry point and
prints in exactly the shape the expected output uses. Thirteen wrappers cover the
current catalogue — arrays, linked lists, cycles, trees, graphs, an LRU cache and
plain stdin. Adding a new problem shape means adding one wrapper; the judge, the
editor and the stored test cases are untouched.

## Data layer

`db/schema.sql` is the development schema (SQLite, 63 tables) and
`db/postgres/schema.pg.sql` mirrors it for production. They share the model
exactly and differ only where scale demands it: hash partitioning on the hot
tables, `citext` for case-insensitive emails, `jsonb` for indexed payloads,
`tsvector` for full-text search, and `BIGINT` for counters that a 32-bit integer
would overflow. See `db/postgres/README.md`.

## What is deliberately absent

- **No ORM.** The SQL is the interface.
- **No client build step.** No npm, no bundler, no CDN.
- **No third-party auth.** Credentials, sessions and CSRF are implemented here.
- **No hosted services.** Videos link out to NPTEL, MIT OCW and freeCodeCamp;
  books link to the publisher or the open-access source. Nothing copyrighted is
  re-hosted.
- **No dependency for LaTeX.** `markdown.py` renders fractions, roots,
  subscripts, superscripts and Greek letters to HTML directly.
