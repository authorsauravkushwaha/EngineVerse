# Integrated engineering and developer labs

Four new destinations are part of the same navigation table, breadcrumbs,
resource index, sitemap and GitHub Pages reading-copy export as the catalogue.
They are original, local implementations inspired by the named projects, not
embedded copies of those services or new hosted dependencies.

| Capability | Page | JSON interface |
|---|---|---|
| Public APIs directory | `/apis` | `GET /api/public-apis` |
| Data & BaaS studio | `/studio` | `GET /api/studio/schema`, `POST /api/studio/query` |
| Workflow automations | `/workflows` | `GET /api/workflows`, `POST /api/workflows/run` |
| Engineering swarm lab | `/swarm` | `POST /api/swarm/simulate` |

The normal sign-in policy still applies. With `ENGINEVERSE_SIGNIN=required`,
these pages and APIs require an account. With `optional`, the public catalogue
and its read-only labs are browsable anonymously. All three POST operators
require the existing browser-bound/session-bound CSRF token. The SQL and workflow
POSTs have a shared per-IP 60/minute budget; the swarm shares the tutor's
30/hour budget. Normal API rate limits also apply. None of these operators awards
XP, grades a submission, changes SRS state, or writes to learner progress.

## Public APIs directory

Inspired by [`public-apis/public-apis`](https://github.com/public-apis/public-apis),
this deliberately small directory has 12 engineering/developer APIs in five
categories. Each entry contains HTTPS endpoint and documentation metadata,
`auth`, `cors`, paired `topic_slug` and `project_slug`, an engineering exercise,
provider caveats and cURL/Python/JavaScript examples. API keys are never stored
or used by EngineVerse. External availability and CORS are not live-monitored.

The HTML page and JSON endpoint accept the same AND-combined filters:

```text
/api/public-apis?q=github&category=Developer%20tools&auth=none&cors=yes
/apis?slug=open-meteo
```

Unknown filter values return no entries, not an unfiltered directory. Public
reads may have a smaller provider quota than authenticated reads. CORS means a
browser may be allowed to read a response; it is not authorization. Python
examples use the optional `requests` package. NASA's `DEMO_KEY` is a public,
rate-limited demonstration; a private key belongs only in server-side code.

## Data & BaaS studio

Inspired by [`supabase/supabase`](https://github.com/supabase/supabase) and
[`appwrite/appwrite`](https://github.com/appwrite/appwrite), the five-service
matrix compares Supabase, Appwrite, Firebase, PocketBase and Nhost. SDK snippets
are teaching examples: no provider SDK or service is installed by this feature.
Provision a compatible schema and access policies before using an example.

The inspector exposes exactly 26 reviewed table projections, with public row
counts, column types, public foreign-key relationships and reproducible indexes:

```text
branches, semesters, subjects, modules, topics, notes, note_sections,
diagrams, models_3d, formulas, questions, question_options,
programming_languages, language_modules, language_stages,
language_checkpoints, coding_problems, coding_problem_stubs,
coding_sheets, coding_sheet_problems, projects, project_steps,
project_resources, roadmaps, roadmap_nodes, flashcards
```

Projections explicitly exclude author/reviewer account IDs, quiz grading keys,
hidden coding test cases, personal schedules, sessions, credentials and payments.
Published-row filters also apply to children of published notes/topics/projects.
The schema contract comes from the repository DDL; it does not enumerate a live
private schema. Adding a table or column requires an explicit projection change.

The policy matrix distinguishes provider/native row-level controls from the
application's existing route authorization. SQLite has no native Postgres RLS.
The matrix describes the access boundary; it does not claim that a provider's
policies were applied or audit every route in EngineVerse.

### SQL execution boundary

`POST /api/studio/query` accepts `{"sql": "SELECT ..."}`. The response includes
column names, row arrays, counts, truncation flags, elapsed setup+execution time,
and `EXPLAIN QUERY PLAN` output. A SELECT-only CTE or compound SELECT is supported.

**Untrusted SQL never reaches the application database connection.** The runner:

1. Parses a single SELECT and resolves only allowed public tables/CTE references.
2. Copies the referenced, explicit public projections into a disposable SQLite
   database, even when EngineVerse itself is backed by PostgreSQL.
3. Reproduces public catalogue indexes; these plans are teaching plans, not
   measurements of production performance.
4. Enables `query_only` and installs an authorizer that denies writes,
   introspection, extension/file functions and non-allowlisted functions.
5. Bounds SQL to 8,000 characters, snapshots to 20,000 rows per referenced table
   and 32 MiB of copied values, output to 100 rows and 2,000 characters per text
   cell, and SQLite execution to 200,000 VM steps / 1.5 seconds (not including
   snapshot setup). Applied truncation is disclosed in the response.

DDL, DML, ATTACH, PRAGMA, private tables, hidden columns, `load_extension`,
`readfile`, `writefile`, huge blob constructors and formatting functions are
rejected. The sandbox cannot make network requests or run submitted code.

## Declarative workflow automations

Inspired by [`n8n-io/n8n`](https://github.com/n8n-io/n8n), four immutable blueprints
compose allowlisted local operators:

- **Study:** published topic → note evidence / formulas / questions → study plan.
- **Revision:** published topic → recall prompts / formulas → revision plan.
- **Placement:** focus topic → coding briefs / project briefs → placement plan.
- **Audit:** public schema → topic coverage / directory pairing checks → report.

Nodes have IDs, operators and explicit dependencies. The executor passes real
node outputs through those dependencies. Subject-level flashcards or unlinked
formulas are used only when there are no topic-linked ones, and that broader
scope is identified in the output. Missing matches remain empty; no unknown
slug silently broadens the request.

```json
{
  "slug": "study",
  "inputs": {"topic_slug": "bernoullis-equation", "difficulty": "easy", "limit": 3}
}
```

Inputs are limited to `topic_slug`, `q`, `difficulty` and an item `limit` of 1–10.
Custom graphs, code and webhooks cannot execute. Ordinary requests receive a
JSON result. `Accept: application/x-ndjson` receives real completed-step events
followed by a completion event; the browser updates the graph as those arrive,
without replaying fake execution delays. Plain HTML form POSTs render results
server-side if JavaScript is unavailable.

### n8n JSON export

`GET /api/workflows?slug=study&format=n8n` returns an importable document using
standard Manual Trigger and HTTP Request nodes. The page also embeds the same
document for offline/static downloads.

Set the n8n variable `engineverse_url` to the self-hosted app's origin without a
trailing slash; `engineverse_topic` optionally selects a published topic. For an
account-gated app, configure an authenticated Cookie header/credential on the
HTTP nodes and manage session expiry yourself. The export includes no credential.
Each node calls `GET /api/workflows?slug=...&node=...` and recomputes its read-only
dependencies; the transport is sequential even where the local graph branches.
No scheduler or notification delivery is included.

## Multi-agent engineering swarm lab & security verification

Inspired by [`666ghj/MiroFish`](https://github.com/666ghj/MiroFish) and [`vxcontrol/pentagi`](https://github.com/vxcontrol/pentagi), the lab uses
five deterministic review lenses: systems architect, quantitative analyst,
implementation engineer, safety/reliability reviewer and learning/delivery coach.
They are not real specialists and do not make an external model call. Alongside
the lab, PentAGI-style security verification patterns inform EngineVerse's
scoped 6-digit OTP verification (required only for new-user registration,
password recovery, and password change via Gmail or mobile number with country
code) and multi-layer session persistence (`localStorage`, `sessionStorage`,
`IndexedDB`, cookies, and GitHub/Supabase/Appwrite/n8n sync).

`POST /api/swarm/simulate` accepts a 4–400 character `prompt`, with optional
published `topic_slug` and `project_slug` grounding. Retrieval is limited to
`topics`, `note_sections`, `formulas`, `questions`, `coding_problems` and `projects`.
Questions contribute prompts, not grading keys. Drafts and private learner data
are excluded.

Round one quotes seeded evidence with numbered, resolvable catalogue citations
and visible editorial review states. Round two pairs personas' review questions
around integration, measurement, reliability and scope. These are explicitly
**unresolved review prompts**, not invented engineering conclusions, safety
advice, forecasts or approval. Personas abstain when their lens has no evidence;
requests without relevant catalogue coverage receive no fabricated answer.
Partial keyword matches are identified as partial coverage, not verification of
an entire request. The deterministic output is reproducible for the same data.

## GitHub Pages is not the Python backend

While no hosted app is configured, `pages.yml` exports the public reading copy.
All four pages are then published at the project Pages base path. Directory and
schema filtering, copy buttons and n8n JSON downloads work locally in the browser.
SQL, workflow and swarm examples are precomputed from the seeded public data.

Backend-only forms are disabled in the exported HTML, their fallback actions
point at the hosting explanation with GET, and a visible notice says that new
execution requires a self-hosted app. This remains honest with JavaScript off.
There are no accounts, live SQL, live workflows, live simulations or judge on
GitHub Pages. Once `ENGINEVERSE_APP_URL` points to a verified HTTPS FastAPI app,
the workflow switches Pages to a small gateway to that app instead; these four
pages then live on the hosted app, not in the Pages artifact.

Export validates local links, heading outlines and forbidden demo-password
leaks. A `deployment.json` records the published commit and mode. After
deployment, `scripts/verify_pages.py` verifies that exact commit and either the
four reading-copy pages with their shared assets or the gateway's app links and
404 deep-link handoff over HTTPS, retrying briefly for CDN propagation.

## Regression checks

```bash
pytest backend/tests/test_navigation.py backend/tests/test_links.py backend/tests/test_capabilities.py
python scripts/export_pages.py --self-check
python scripts/verify_pages.py --self-check
python scripts/export_pages.py --out site --reading-copy
```

Generated `site/`, runtime databases and virtual environments remain ignored.
