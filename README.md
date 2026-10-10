# EngineVerse

**A complete learning platform for engineering students.**

Structured notes for every branch, daily practice problems, a LeetCode-style
coding judge, real-world projects, spaced-repetition revision, skill roadmaps, a
community, and a portfolio — in one installable app. Built for students and for
working professionals who are filling a gap.

```bash
python -m venv .venv && . .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env                       # then set ENGINEVERSE_SECRET
python scripts/seed.py --fresh             # ~0.4s, builds the whole catalogue
uvicorn main:app --app-dir backend --reload
```

Open https://authorsauravkushwaha.github.io/EngineVerse/ . On a development machine, sign in as
`asha@example.com` / `LearnBuild#2026!`, or `admin@engineverse.local` /
`Str0ngPassphrase#42!` for the CMS. Those accounts are created only when
`ENGINEVERSE_ENV` is `development` or `test`. Production seed does not create
them, does not print the passwords, and the login page does not show them.
`python scripts/seed.py --no-demo` builds the catalogue without them.

Production is a separate step, and it has not been claimed as deployed. See
[docs/DEPLOYMENT.md](docs/DEPLOYMENT.md).

## What is here

| Area | What it does |
|---|---|
| **Notes** | 93 published subjects across all 45 branches, with 121 published starter topics in the current seed snapshot. All 121 topics have four public reading depths; each standard note carries the full [13-section template](docs/NOTE_TEMPLATE.md), with LaTeX rendered by a dependency-free renderer. |
| **Diagrams & 3D** | One topic-linked SVG diagram and one interactive 3D learning model per topic (121 of each in the current snapshot), drawn by a dependency-free WebGL renderer (`engine3d.js`, no three.js, no CDN). Drag to orbit, scroll to zoom, labels projected from 3D. Each model is JSON geometry stored in the database. |
| **Practice** | 159 active questions plus 19 Daily Practice Problem sets (95 question slots), with every published subject represented in the rotation. The question bank is filterable and paginated so all questions are reachable. |
| **Coding** | 13 problems with an in-browser editor, real execution in an isolated sandbox, per-test verdicts, and stubs in Python, Java, JavaScript and C++. |
| **Projects** | 6 end-to-end builds with steps, skills and resources — not "make a todo app". |
| **Revision** | 281 flashcards in the current seed snapshot, on SM-2 spaced repetition, alongside a formula centre and a mistake notebook that turns wrong answers into a recovery plan. |
| **Roadmaps** | 5 skill trees with 57 prerequisite-linked nodes. |
| **Tutor** | A retrieval-grounded AI tutor. It answers only from this platform's own notes, formulas and topics, cites every source it used, is labelled AI-generated, and refuses rather than inventing when the library has nothing on a subject. Self-hosted — no external model call. |
| **Community** | Threads, comments, votes, answers, moderation. |
| **Placements** | Interview questions by topic, company tags, contest scaffolding. |
| **Gamification** | XP, 40 levels, streaks, 12 badges, a contribution heatmap, a leaderboard. |
| **Portfolio** | A public page per learner with progress, solved problems and verifiable certificates. |
| **Admin** | Content lifecycle, roles, audit log, branding. |

Everything in that table works. There are no dead buttons and no stub pages: the
route suite renders all 49 pages as anonymous, student, faculty *and* admin, and
asserts none of them errors or renders an undefined template variable. Pages that
look fine to a visitor but break for a signed-in user are the easy ones to miss,
so every role is covered separately. The suite also checks 9 infrastructure
routes and 20 authenticated API endpoints, and the coding judge is exercised end
to end by 13 real reference solutions.

## Stack

**Python** for the application, **SQL** for the data, **Java** for the sandbox.
No CDN, no npm build step, no SaaS, no third-party auth.

```
browser / PWA ──► FastAPI + Jinja2 SSR ──► SQL (SQLite dev / Postgres prod)
                        │
                        └──► Java sandbox (one JVM per submission)
```

- ~5,800 lines of Python in `backend/engineverse/` — the domain and services
- ~1,650 lines in `backend/web/` — routing and the JSON API
- Jinja2 templates, one dependency-free CSS file, one dependency-free JS file

The interface is **neumorphic and self-contained**. Surfaces share one clay colour;
volume is a light shadow from the top-left and a dark shadow to the bottom-right.
Fields, tracks and the active nav are inset. Nothing is loaded from a CDN, an
icon font, or a component library — including the LaTeX renderer and the WebGL
models. Light is the default; dark is the same system with a deeper clay.
- 63 SQL tables; `db/schema.sql` for development, `db/postgres/schema.pg.sql`
  hash-partitioned for production
- `sandbox-java/` — a Maven project with zero runtime dependencies

The client is progressively enhanced: with JavaScript disabled the site still
reads, still navigates, still works. That is also what makes it installable on a
phone without an app store — `manifest.webmanifest` plus a service worker, no
store submission.

## The coding judge

A coding stub only *declares* an entry point, so nothing would call it. Each
problem names a **wrapper** and the judge appends a driver that reads stdin, calls
the entry point, and prints in exactly the shape the expected output uses.

```
two-sum               list-target      '[2, 7, 11, 15]\n9'      -> '[0, 1]'
reverse-linked-list   linked-list      '1 2 3 4 5'              -> '5 4 3 2 1'
detect-cycle          cycle            '1 2 3 2'                -> 'True'
level-order-traversal tree             '3 9 20 None None 15 7'  -> '[[3], [9, 20], [15, 7]]'
lru-cache             lru              '2\nput 1 1\nget 1'      -> '1'
dijkstra-shortest-path graph           'A:B1,C4\n...\nA\nD'     -> '4'
```

Thirteen wrappers cover arrays, linked lists, cycles, trees, graphs, an LRU cache
and plain stdin. Adding a new problem shape means adding one wrapper — the judge,
the editor and the stored test cases are untouched. Drivers carry their own node
and tree types, so a submission still runs if the learner deletes the stub's
helpers.

Submissions never execute in the web process. They run in a child process with a
scrubbed environment, CPU/memory/wall-clock ceilings, no writable path outside a
temp directory, and no outbound network. Java goes through a second JVM entirely.

## Scale

The Postgres schema hash-partitions the sixteen tables that a global platform
actually stresses:

| Table | Partitions |
|---|---|
| `submissions`, `activity`, `audit_logs` | 256 |
| `coding_submissions`, `user_flashcards`, `user_progress`, `xp_events`, `notifications` | 128 |
| `sessions`, `profiles`, `mistakes`, `bookmarks`, `personal_notes`, `user_badges`, `votes` | 64 |
| `login_attempts`, `contest_submissions` | 32 |

Hash rather than range, so writes spread evenly from the first row to the
billionth with no rebalancing, and every per-user query prunes to one partition.
Fan-out is chosen so the largest partition stays in the low tens of millions of
rows — small enough for `VACUUM`, `REINDEX` and a restore to stay tractable.
ULID keys are kept so ids can be minted on any node without sequence contention.

Details and the scaling path beyond partitioning: [`db/postgres/README.md`](db/postgres/README.md).

## Security

scrypt password hashing (N=16384, measured 52 ms), opaque sessions stored as
SHA-256 digests, HMAC CSRF tokens bound to the session, an 8-role × 10-capability
RBAC that fails closed, parameterised SQL throughout, autoescaped templates, a
per-request CSP nonce, and an append-only audit log.

Full detail, including the honest limitations — authenticator enrolment is
optional for learners, the password blocklist is small, and a proxy hides
every client behind one address unless you explicitly trust it — is in
[`docs/SECURITY.md`](docs/SECURITY.md).

## Testing

```bash
python -m pytest backend/tests -q          # 431 tests
python -m pytest backend/tests -q -m "not slow"   # skip the sandbox runs

node scripts/check_engine3d.js             # the WebGL renderer's maths
python scripts/dump_scenes.py | node scripts/check_scenes.js   # every scene is drawable
```

The last two matter because the 3D layer has no browser in CI. The first runs
the shipped mesh builders under a DOM stub and asserts finite geometry,
parameter clamping, the arrow-orientation algebra and the projection maths.
The second feeds all 56 stored scenes to that same renderer and fails if any
object cannot be built — which is how a model that validated as JSON but named
a mesh the renderer does not have gets caught before it ships.

| Suite | Tests | Covers |
|---|---|---|
| `test_security.py` | 100 | Hashing, salting, NFKC, policy, RBAC, safe URLs, ULIDs; every POST form carries a CSRF token; every capability the web layer checks actually exists |
| `test_judge.py` | 53 | All 13 reference solutions through the real sandbox; rlimits read back from inside a submission; fork bomb containment; the checkout is invisible to submitted code |
| `test_tutor.py` | 13 | Grounded answers cite only listed sources; uncovered subjects are refused, not invented; stored markup never reaches the client; the rate limit engages |
| `test_routes.py` | 97 | Every page renders; access control; headers; CSP nonce uniqueness; forms |
| `test_models3d.py` | 48 | Python and JavaScript agree on the mesh vocabulary; the validator refuses junk, clamps absurd numbers and emits attribute-safe JSON; **validation drops no object from any seeded scene**; a corrupted row is dropped, not rendered |
| `test_api_and_schema.py` | 120 | 20 authenticated endpoints; coding run/submit; grading; community forms both ways; branding keys; theme wiring; registration toggle; flash cookie encoding; migration idempotence; Postgres schema parsed |

The tests are how the platform's worst defects were found: every `/api/*` request
500ing on a rate-limit unpacking error, every authenticated form POST 403ing
because the CSRF check only read a header an HTML form cannot set, an open
redirect through protocol-relative URLs, a seeded role that RBAC did not define,
every subject page 500ing for a signed-in user, the entire admin panel refusing
even a `super_admin`, a judge with no resource limits at all, and an account
takeover through the password reset form.

## Repository

```
backend/
  engineverse/        domain, services, security, judge, markdown renderer
  web/                pages.py (SSR), auth_pages.py, api.py (JSON)
  templates/          48 Jinja2 templates
  static/             one CSS file, two JS files (app.js, engine3d.js), PWA manifest, service worker, icons
  tests/              431 tests
db/
  schema.sql          SQLite, 66 tables (development)
  postgres/           hash-partitioned Postgres schema (production)
seed_data/            the catalogue as data
scripts/seed.py       builds the database
scripts/reindex.py    rebuilds the search index after you insert content rows
scripts/check_engine3d.js · check_scenes.js
                      headless verification of the 3D renderer and its scenes
sandbox-java/         the JVM sandbox (Maven, zero runtime deps)
deploy/               Dockerfiles and compose topology (web, Postgres)
docs/                 ARCHITECTURE · SECURITY · NOTE_TEMPLATE · CONTENT
.github/workflows/    Python tests, Postgres schema, Java build, JS + 3D checks
```

## Documentation

- [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md) — module map, request lifecycle, why this shape
- [`docs/SECURITY.md`](docs/SECURITY.md) — threat model and what is actually implemented
- [`docs/NOTE_TEMPLATE.md`](docs/NOTE_TEMPLATE.md) — the 13-section note structure
- [`docs/CONTENT.md`](docs/CONTENT.md) — lifecycle, licensing, what may be hosted
- [`db/postgres/README.md`](db/postgres/README.md) — partitioning rationale and scaling path
- [`sandbox-java/README.md`](sandbox-java/README.md) — the judge's isolation model
- [`deploy/README.md`](deploy/README.md) — containers, hardening flags, scaling out

## Known limitations

Stated plainly rather than discovered later:

- **The Java sandbox cannot be built in this workspace.** No JDK is installable
  here, so `javac` is absent and `LocalSandboxProvider.supports("java")` returns
  `False`; Java problems report `unsupported_language` instead of failing
  silently. It is not unverified: `.github/workflows/java.yml` compiles it, runs
  its tests and smoke-tests the jar on JDK 21 and JDK 25. Note that its optional
  security policy is inert on JDK 24+ (JEP 486 killed the Security Manager) — see
  `docs/SECURITY.md`.
- **The Postgres schema has not been applied to a live server here.** It is
  parsed with `sqlglot` locally and applied to a real PostgreSQL 16 service in CI.
- **Authenticator enrolment is optional for learners.** Production blocks staff
  `POST`s to `/admin` until that account has enrolled. A password alone still
  signs in every account that has not.
- **API rate limits are shared via the database**, but the client address is the
  TCP peer unless `ENGINEVERSE_TRUST_PROXY` is on. The compose file leaves it off.
- **Email confirmation is sent only when `ENGINEVERSE_SMTP_URL` is set.**
  Without it the address stays unconfirmed and sign-in still works.
- **The seeded catalogue is broad starter coverage, not a complete degree.** The
  current seed covers 45 active branches and 93 subjects with 121 published
  starter topics. Sixty-five topics were added to previously uncovered subject
  paths; generated starter material is marked `needs_review` in editorial
  metadata, including the five public Cyber Security lessons. Every topic has a
  standard note with all 13 sections, a linked SVG diagram, a 3D learning model,
  and a question. Nineteen five-question DPPs represent all 93 subjects across
  the dated rotation. See the generated [coverage snapshot](docs/CURRICULUM_COVERAGE.md);
  a full degree is still thousands of carefully reviewed topics.

## Licence

Original content is CC-BY-4.0. Third-party videos, books and articles are linked,
never hosted — see [`docs/CONTENT.md`](docs/CONTENT.md).
