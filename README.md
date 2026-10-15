# EngineVerse

EngineVerse is a self-hostable learning platform for engineering students and
working professionals. It brings together a growing subject catalogue, structured
notes, practice, programming paths, projects, revision tools and a community in
one progressively enhanced web app.

**The seeded catalogue is starter material, not a complete degree syllabus.**
Some expanded entries are explicitly marked `needs_review`; publication means a
learner can read them, not that an expert has signed them off. EngineVerse is not
an accredited institution and its certificates are not academic or professional
qualifications.

## Run locally

Requirements: Python 3.11 or newer. The default development database is SQLite;
PostgreSQL and container setup are documented separately.

```bash
python -m venv .venv
. .venv/bin/activate
python -m pip install -r requirements.txt
cp .env.example .env
```

Set a private development signing secret in `.env` (do not commit the file):

```bash
python -c "import secrets; print(secrets.token_hex(32))"
```

Copy the output into `ENGINEVERSE_SECRET` in `.env`. Seed the local SQLite
catalogue, then start the app:

```bash
python scripts/seed.py --fresh --no-demo
uvicorn main:app --app-dir backend --host 0.0.0.0 --port 8000 --reload
```

`--fresh` is destructive: use it only with a disposable development database.
`--no-demo` avoids creating sample accounts. Open <http://127.0.0.1:8000> and
create an account through **Register**. Do not use development demo credentials
on a public instance. The login page may show demo-account details only when the
application is configured for development or tests.

**Sign-in is compulsory.** With the default `ENGINEVERSE_SIGNIN=required`, a
signed-out visitor can reach only the sign-in, registration, password-recovery
and legal pages (plus certificate verification and static assets); every other
page redirects to `/login` and returns to the requested page after sign-in, and
the JSON API answers `401`. Set `ENGINEVERSE_SIGNIN=optional` to allow anonymous
browsing of the public catalogue instead. The current GitHub Pages workflow
publishes the public catalogue (notes, language paths, problems). It is not the
Python backend: accounts, live judging and cross-device progress need a
self-hosted install. An optional sign-in gateway export is also available; see
[Deployment](docs/DEPLOYMENT.md#github-pages-sign-in-gateway).

Sign-in is password-only by default (`ENGINEVERSE_LOGIN_OTP=disabled`): no mail
or SMS transport is needed, and a second factor is per account - enrol an
authenticator app under **Settings -> Security** and that account is then asked
for a six-digit code at every sign-in. Operators who want a *delivered* code at
every sign-in can set `ENGINEVERSE_LOGIN_OTP=required`, which production accepts
only alongside `ENGINEVERSE_SMTP_URL` or `ENGINEVERSE_SMS_URL`.

For Windows/Git Bash, Docker Compose, PostgreSQL and production configuration,
see [Deployment](docs/DEPLOYMENT.md) and [the Compose topology](deploy/README.md).

## Learning catalogue

The catalogue is data-driven: pages enumerate the subjects and learning material
present in the database rather than assuming there are only one or two fixed
subjects. The following counts come from a fresh, no-demo seed; they describe
what is seeded today, not a completeness guarantee.

| Area | Current seeded coverage |
|---|---|
| **Engineering subjects** | 45 branches and 93 published subjects. The catalogue includes computing, electrical, mechanical, civil, chemical, aerospace, biomedical, agricultural, cybersecurity and other engineering fields. Browse what is available in the app; missing material is not implied by this snapshot. |
| **Notes** | 406 published topics, 1,624 notes across four reading depths, and 10,556 note sections. Standard notes use the [13-section note template](docs/NOTE_TEMPLATE.md). |
| **Cyber Security** | 13 published starter topics; on an instance run with `ENGINEVERSE_SIGNIN=optional` learners can read them without signing in. They remain starter material and need expert review. |
| **Diagrams and models** | 406 topic-linked SVG diagrams and 406 interactive 3D learning models. The WebGL renderer has no external runtime dependency. |
| **Practice** | 534 active questions and 107 published Daily Practice Problem sets (535 slots); every active question, all 93 subjects and all ten language tracks appear in the seeded DPP archive. Practice XP is attempt-based: wrong and correct answer attempts both award XP, subject to the API rate limit; a question's full XP is paid only for its first correct answer, and later attempts earn the flat attempt XP. |
| **Programming paths** | 10 learning paths and 225 staged, searchable modules across Python, Java, JavaScript, TypeScript, C, C++, C#, Go, Rust and SQL. Each path is staged — Foundations, then Working Practice, then Advanced Engineering — across 30 stages, and each stage ends with three checkpoint questions (90 total) answered through the normal practice flow, with feedback, explanation and XP only after submission. The five flagship paths (Python, Java, C, C++, C#) run to full book depth, and every depth module ends with a linked judged problem so reading always turns into coding. |
| **Coding practice** | 105 problems with language stubs and test cases, grouped into 14 curated sheets (first drills, arrays, two pointers and windows, stacks and search, linked lists, trees and heaps, graphs, dynamic programming, advanced patterns, SQL and stream sets) plus a 30-problem interview set. Every problem appears in at least one sheet, and every sheet is reachable at `/sheets` in a recommended order with hints, editorials and progress. Which languages can execute depends on the configured judge and installed toolchains; see [Code execution](#code-execution). |
| **My stream** | Each branch has a study hub at `/stream/{slug}` that gathers the subjects, notes, formula sheets, flashcards, question mix, sheets and projects that branch actually has, with the counts taken from the database rather than promised. `/stream` opens on the branch saved in the profile and `/streams` switches between them. Every stream also reaches the branch-neutral pattern sheets and the interview set, so no branch gets an empty page. |
| **Projects** | 17 project briefs with ordered steps, skills and resources, spanning hardware, engineering software, full-stack apps and a model-free study planner with an optional allowlisted, confirmation-gated agent — including a substantial capstone brief linked to each of the ten language paths. |
| **Revision and roadmaps** | 281 public flashcards are browsable at `/flashcards` and searchable without indexing their answers; personal SM-2 schedules are at `/revision`. The seed also includes 5 roadmaps and 57 roadmap nodes. |
| **Study helper** | A retrieval-grounded tutor that composes answers from EngineVerse's own indexed material and cites its sources. It does not make an external model call by default and should say when the catalogue has no relevant coverage. |

Studying does not require leaving the site. Notes, worked examples, diagrams and
3D models, formula sheets, flashcards, the practice bank, the coding judge and
the projects are all served from this application, and `/resources` is the
complete index of those in-app shelves rather than a page of outbound links. An
older shelf of external reading still exists at `/resources/offsite` and is
labelled as optional: no navigation, lesson or practice flow depends on it, and a
deployment that never visits it loses no learning material.

## Integrated engineering and developer labs

Four advanced capabilities are wired into the existing catalogue and navigation:

| Lab | What is integrated |
|---|---|
| **Public APIs directory** (`/apis`) | 12 curated developer/engineering APIs with category, auth, CORS, search and exact-slug filters; paired local topics/projects and cURL, Python and JavaScript examples. Inspired by `public-apis/public-apis`. |
| **Data & BaaS studio** (`/studio`) | Five-service comparison and SDK snippets, a 26-table public schema inspector, an access/RLS policy matrix, and a bounded SELECT runner with `EXPLAIN QUERY PLAN`. SQL runs only on a disposable public snapshot—never the live app database. Inspired by Supabase and Appwrite. |
| **Workflow automations** (`/workflows`) | Declarative study, revision, placement and catalogue-audit pipelines with real streamed step outputs and importable n8n JSON. Operators are allowlisted and read-only; custom code and webhooks cannot execute. Inspired by n8n. |
| **Engineering swarm lab** (`/swarm`) | Five deterministic specialist review lenses, using only seeded topics, note sections, formulas, questions, coding briefs and projects. Quotes have citations; trade-offs are explicitly unresolved review prompts. No external model or autonomous tools are running. Inspired by MiroFish. |

On GitHub Pages these pages show the directory, schema, blueprints, JSON downloads
and clearly labelled seeded examples. New SQL queries, workflow runs and swarm
reviews require a self-hosted backend; exported controls are disabled rather than
pretending to execute. Normal account policy, CSRF and rate limits apply on the
real app. No operator changes learner progress, grading or SRS state.

See [Advanced capabilities](docs/ADVANCED_CAPABILITIES.md) for endpoint contracts,
isolation limits, grounding guarantees, n8n setup and deployment verification.

## Finding things

Sixty pages is only useful if a learner can find the one they want. The whole
site is described once, in `engineverse/navigation.py`: every destination, the
group it belongs to, a one-line description, and the URL prefixes that mean "you
are here". Everything the reader sees is derived from that table — the desktop
top bar, the mobile bottom bar, the slide-down menu, the footer columns, the
breadcrumb trail on every page, the index at `/resources`, `/sitemap.xml` and the
GitHub Pages export list — so they cannot disagree about what exists or what
something is called. See [Architecture](docs/ARCHITECTURE.md#navigation-is-data)
for what this replaced.

The top bar is six grouped entries rather than ten flat links. Each group label
is itself a link to that group's landing page, so the bar is one click from the
most useful page in every group even for a reader who never opens a menu:

| Group | Landing page | Also in the menu |
|---|---|---|
| **My stream** | `/stream` | the full index |
| **Learn** | `/explore` | formulas, videos, books, roadmaps, the study tutor, engineering swarm lab |
| **Practice** | `/practice` | the daily set and its archive, the question bank, the mistake notebook |
| **Code** | `/programming` | coding problems, practice sheets, projects, public APIs, data & BaaS studio |
| **Revise** | `/revision` | public flashcards, formulas, roadmaps |
| **More** | `/resources` | today's plan, streaks, leaderboard, profile, workflow automations, community, placements, about |

On a phone the menu button opens every group expanded, which puts all sixty pages
one tap away instead of leaving the last fifteen to the footer. Menus open on
hover *and* on keyboard focus, so the whole navigation works with no JavaScript —
as does every other page on the site.

`/resources` is the page that answers *what is actually on this site?*: every
destination in its group with the description and the count this instance holds,
opened by three ways in by intent. `/explore` carries the branch browser, which
lists all 45 branch hubs with links to both the branch page and its study hub.
Both were reachable from nowhere before.

Deep links from search and from the recommendation cards narrow the page they
land on — `/videos?slug=…`, `/books?slug=…`, `/formulas?slug=…` and
`/practice/questions?slug=…` — rather than using a `#fragment`. The library pages
paginate 24 rows at a time, and a fragment is never sent to the server, so a
fragment link dropped the reader at the top of a long list with the item they had
clicked several pages in. `backend/tests/test_links.py` asserts not just that
these URLs resolve but that they *show the thing they named*, which is the
property a status-code check cannot see.

Every collection pages, including `/formulas`, which used to render all 365
formulas as a 1.3 MB page while a hard-coded limit of 300 quietly deleted the
last 65. Every page also keeps a clean heading outline: a reader who navigates by
heading hears the structure, and the footer's headings and the markdown
renderer's heading offset both used to make most pages skip two or three levels.

Every page below the top level carries a breadcrumb, derived from the same table.
It is audience-aware: a signed-out reader is never shown a link whose only effect
would be a bounce to `/login`, and `/stream/{branch}` reads
"Home › Streams › …" for them rather than pointing at a page they cannot open.

`/resources` is the page that answers *"what is actually on this site?"*. It lists
every destination in its group with the description and the count this instance
really has — read from the database, so a deployment seeded with less shows less —
and opens with three ways in by intent: just started, studying for an exam,
preparing for interviews.

The generated [curriculum coverage report](docs/CURRICULUM_COVERAGE.md) lists the
current snapshot by branch and by stream. Use
`python scripts/coverage_report.py` after seeding to regenerate it for a
database. Do not read the counts as evidence that every
subject has a complete semester or degree curriculum.

## Practical programming

The programming paths are intended to build from syntax toward useful software,
not stop at isolated language trivia. Each path runs through the same three
stages — **Foundations** (the language and its first programs), **Working
Practice** (the habits of small correct programs: testing, error handling, safe
input) and **Advanced Engineering** (structure, concurrency, persistence,
authorization and the tooling a maintainer relies on). Every stage ends with a
three-question checkpoint answered through the normal practice flow, and every
path ends with a capstone project brief: a real problem with prerequisites,
ordered milestones, testing expectations, resources and a shippable result.
Depending on the path, modules cover collections, functions, object-oriented
design, error handling, testing, safe input handling, APIs, persistence,
concurrency, authorization and project structure. C and C++ paths also emphasize
memory/resource safety and undefined-behavior avoidance. The Python, Java, C,
C++ and C# paths continue to full book depth — complexity analysis, strings,
recursion, sorting, stacks, linked lists, trees, heaps, graphs and dynamic
programming — and every depth module ends with a linked judged problem ("Code
what you learned"), so each subtopic is learned and then coded before moving on.

The coding problems on a language page are limited to the ones that language has
a usable editor starter for; where a path has no starter yet the page says so
rather than opening an editor that cannot run that language. The modules,
checkpoints and capstone brief are fully usable regardless.

Runnable support is a deployment property, not just a curriculum promise. The
UI marks a language runnable only when the active provider supports it on that
host. Missing compilers or blocked isolation cause the runner to refuse execution
rather than silently run code with weaker controls.

## Code execution

Learner code is untrusted. **Production does not run code in the web process.**
The production default is `ENGINEVERSE_JUDGE=disabled`; operators may instead
configure a separately managed Judge0 endpoint. This application delegates to
that endpoint but does not certify or independently verify its isolation.

For development, `ENGINEVERSE_JUDGE=auto` may select the Java sandbox or the
built-in local runner. The local runner only becomes available when the host
proves it can create network, PID and mount namespaces, mount private procfs,
and perform the filesystem-isolation mount. It applies bounded process
resources, scrubs the child environment and refuses if required controls fail.
It is still a child
process on the same host—not a container or VM—and is not a production security
boundary. A restrictive kernel/container may make it unavailable, in which
case submissions are refused. See [Security](docs/SECURITY.md) for its limits.

## Security overview

Security is part of the application design, not a deployment afterthought. The
current implementation includes:

- scrypt password hashing with bounded password length and bounded verification
  parameters; a modest local exact-match common-password list is used, not a
  breached-password lookup service;
- opaque sessions whose random tokens are stored as HMAC-SHA-256 hashes under
  `ENGINEVERSE_SECRET`, session- or browser-bound CSRF tokens, secure cookie
  flags when served over HTTPS, and revocation on sensitive account changes;
- a compulsory six-digit one-time code at every password sign-in, delivered by
  configured email or an operator-run SMS gateway. An enrolled TOTP authenticator
  satisfies that sign-in step without stacking another delivered code; codes are
  short-lived, single-use, keyed and sealed, and public reading remains public;
- authentication-factor replay controls for TOTP steps, one-use recovery codes
  and short-lived one-use authentication/reset tokens. Practice answers are
  intentionally repeatable and continue to earn attempt-based XP;
- server-side authorization, parameterized SQL, request/input bounds,
  autoescaped templates and CSP/security headers. There is currently no
  user-controlled file-upload feature or dynamic file-serving route;
- rate limits for login (10 per 5 minutes), registration (5/hour), reset-link
  requests (5/hour/IP plus 3/hour per keyed address), reset-token checks
  (10 per 5 minutes), feedback
  (5 per hour per IP), practice answers (120 per minute per IP), and coding
  execution (30 per minute); sign-in code resends are capped at 5 issues per
  15 minutes with a 60-second resend cooldown; per-account limits also bound
  password/MFA/email actions and community posts, replies, reports and votes;
- proxy trust disabled by default. Enable it only behind a trusted proxy that
  overwrites forwarding headers.

These protections reduce risk but do not make an application invulnerable.
Review the threat model, operational requirements, key rotation effects and
known limitations in [docs/SECURITY.md](docs/SECURITY.md) before deployment.
Never commit `.env`, database files, private keys or real learner data.

### Known limitations

Production refuses to start with compulsory sign-in codes unless at least one
mail or SMS transport is configured. SMS is deliberately an operator-run HTTP
gateway: EngineVerse does not provide a hosted SMS service, queue, delivery
receipt or carrier fallback, so the operator owns its availability and abuse
controls. A verified phone is optional; email remains the default channel when
mail is configured. An enrolled TOTP authenticator satisfies the every-login
check without a delivered code.

## Architecture

```text
Browser / PWA  ──► FastAPI + Jinja2 server-rendered pages ──► SQLite or PostgreSQL
                                         │
                                         └──► configured judge provider
```

The Python application uses server-rendered HTML with progressive enhancement.
The default SQLite setup needs no database service; PostgreSQL is intended for
production. Static assets are served by the application without a JavaScript
build step or third-party CDN. The application also includes a service worker
for offline reading; personalized responses are excluded from offline caching.

See [Architecture](docs/ARCHITECTURE.md) for the module map, request lifecycle,
search/tutor flow and judge providers.

## Tests and checks

```bash
python -m pytest backend/tests -q
python -m pytest backend/tests -q -m "not slow"
node scripts/check_engine3d.js
python scripts/dump_scenes.py | node scripts/check_scenes.js
```

The Python suite covers API and page behavior, authorization, request validation,
rate limiting, authentication, seeded catalogue coverage and judge isolation.
The scene checks validate both the renderer's geometry/math and the seeded 3D
models. CI also builds and tests the Java sandbox and validates the PostgreSQL
schema; those checks do not substitute for deployment testing against your own
infrastructure.

## Documentation

- [Architecture](docs/ARCHITECTURE.md) — code map and request lifecycle
- [Security](docs/SECURITY.md) — threat model, controls and limitations
- [Deployment](docs/DEPLOYMENT.md) — local, Compose and production setup
- [Compose topology](deploy/README.md) — services and code-execution boundary
- [Curriculum coverage](docs/CURRICULUM_COVERAGE.md) — generated seeded-content snapshot
- [Content and licensing](docs/CONTENT.md) — review lifecycle and third-party material policy
- [Note template](docs/NOTE_TEMPLATE.md) — the 13-section note format
- [PostgreSQL](db/postgres/README.md) — schema and partitioning notes
- [Java sandbox](sandbox-java/README.md) — sandbox implementation and caveats

## Known limitations

- Seeded content is broad starter coverage, not a complete engineering-degree
  syllabus. The generated additions, including Cyber Security, are public but
  marked for expert review. See the [coverage snapshot](docs/CURRICULUM_COVERAGE.md).
- Toolchains and kernel features vary by host. A seeded language may have a
  learning path without being executable on the current judge host. Production
  refuses local code execution by default.
- The local runner shares a host with the web application and is not a container
  boundary. A configured external judge's isolation is the operator's
  responsibility.
- Email delivery requires an SMTP URL. Without a mail transport, account
  confirmation and self-service password reset cannot deliver links; reset
  tokens are not exposed in public responses by default.
- A passing test suite does not certify the deployment, backups, TLS proxy,
  content review or security configuration. No production deployment is claimed
  by this repository documentation.

## Content and software licensing

Third-party books, videos and articles are linked rather than copied or hosted.
Content authors should follow [the content policy](docs/CONTENT.md). Check the
repository for applicable software licensing before redistribution.
