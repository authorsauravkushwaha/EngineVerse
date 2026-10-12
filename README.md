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
| **Notes** | 313 published topics, 1,252 notes across four reading depths, and 8,138 note sections. Standard notes use the [13-section note template](docs/NOTE_TEMPLATE.md). |
| **Cyber Security** | 13 published starter topics with public notes; learners can read them without signing in. They remain starter material and need expert review. |
| **Diagrams and models** | 313 topic-linked SVG diagrams and 313 interactive 3D learning models. The WebGL renderer has no external runtime dependency. |
| **Practice** | 432 active questions and 87 published Daily Practice Problem sets (435 slots); every active question, all 93 subjects and all nine language tracks appear in the seeded DPP archive. Practice XP is attempt-based: wrong and correct answer attempts both award XP, subject to the API rate limit. |
| **Programming paths** | 9 learning paths and 68 public, searchable modules across Python, Java, JavaScript, TypeScript, C, C++, Go, Rust and SQL. Each path is staged — Foundations, then Working Practice, then Advanced Engineering — across 27 stages, and each stage ends with three checkpoint questions (81 total) answered through the normal practice flow, with feedback, explanation and XP only after submission. |
| **Coding practice** | 13 problems with language stubs and test cases. Which languages can execute depends on the configured judge and installed toolchains; see [Code execution](#code-execution). |
| **Projects** | 16 project briefs with ordered steps, skills and resources, spanning hardware, engineering software, full-stack apps and a model-free study planner with an optional allowlisted, confirmation-gated agent — including a substantial capstone brief linked to each of the nine language paths. |
| **Revision and roadmaps** | 281 public flashcards are browsable at `/flashcards` and searchable without indexing their answers; personal SM-2 schedules are at `/revision`. The seed also includes 5 roadmaps and 57 roadmap nodes. |
| **Study helper** | A retrieval-grounded tutor that composes answers from EngineVerse's own indexed material and cites its sources. It does not make an external model call by default and should say when the catalogue has no relevant coverage. |

The generated [curriculum coverage report](docs/CURRICULUM_COVERAGE.md) lists the
current snapshot by branch. Use `python scripts/coverage_report.py` after seeding
to regenerate it for a database. Do not read the counts as evidence that every
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
memory/resource safety and undefined-behavior avoidance.

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
