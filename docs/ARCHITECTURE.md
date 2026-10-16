# Architecture

EngineVerse is one deployable unit: a Python web application over a SQL data
layer, with a separate JVM process for executing learner code. There is no
message broker, no search service, no CDN and no SaaS dependency — everything
runs on hardware you control.

```
                        ┌────────────────────────────────────────────┐
   browser / PWA ──────►│  Python (FastAPI + Jinja2 SSR)             │
   (no build step)      │                                            │
                        │  web/pages.py       52 server-rendered     │
                        │  web/auth_pages.py  auth + settings + CMS  │
                        │  web/api.py         38 JSON endpoints      │
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

The visual system in `backend/static/css/app.css` is neumorphic on purpose, and
still has no framework. Raised controls and inset wells are painted with paired
shadows on a single clay colour, in both the light and dark themes. A phone
gets a fixed bottom nav (Home, Learn, Practice, Projects, Profile) rather than
a shrunk desktop bar.

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
| `engineverse/catalog.py` | Branches → subjects → topics → notes → diagrams → 3D models → formulas |
| `engineverse/models3d.py` | The 3D scene vocabulary and its validator |
| `engineverse/practice.py` | Questions, DPP sets, grading, the mistake notebook |
| `engineverse/hub.py` | The per-stream study hub: which subjects, sheets, projects and readings a branch gets |
| `engineverse/coding.py` | Coding problems, curated sheets, stubs, run/submit, XP awards |
| `engineverse/drivers.py` | The stdin/stdout harness appended to each submission |
| `engineverse/judge/` | Sandbox providers: local, Java bridge, Judge0 |
| `engineverse/library.py` | Videos, books, resources, flashcards |
| `engineverse/srs.py` | SM-2 spaced repetition scheduling |
| `engineverse/progress.py` | XP, levels, streaks, heatmaps, badges, certificates |
| `engineverse/search.py` | Fuzzy search over the SQL full-text index |
| `engineverse/tutor.py` | Retrieval-grounded AI tutor; refuses rather than inventing |
| `engineverse/recommend.py` | Weak-topic detection and next-step suggestions |
| `engineverse/community.py` | Threads, comments, votes, reports |
| `engineverse/markdown.py` | Markdown + LaTeX rendering with **no dependency** |
| `engineverse/brand.py` | Site-wide branding read from `site_config` |
| `engineverse/navigation.py` | The site's information architecture: every destination, its group, and the prefixes that own its child pages |
| `web/deps.py` | Request-scoped viewer, template context, filters |
| `static/js/engine3d.js` | The WebGL renderer: linear algebra, 14 mesh builders, Phong shading, orbit controls |
| `seed_data/`, `scripts/seed.py` | The seeded catalogue and demo accounts |

## Request lifecycle

1. **`SecurityHeadersMiddleware`** — mints a per-request CSP nonce onto
   `request.state.csp_nonce`, then sets X-Frame-Options, nosniff, Referrer-Policy,
   Permissions-Policy, COOP/CORP, and HSTS when the request is HTTPS.
2. **`RateLimitMiddleware`** — shared-IP budgets for login (10/5 min), register
   and reset-link requests (5/hour), reset-token checks (10/5 min), feedback
   (5/hour), practice answers (120/min), coding run/submit (30/min), tutor
   (30/hour), and other API routes (300/min). Password/MFA settings and community
   writes also have per-account budgets.
3. **`CsrfMiddleware`** — rejects state-changing requests without a valid token,
   bound to the authenticated session or an anonymous browser's HttpOnly CSRF
   cookie; reads the token from the `x-csrf-token` header *or* the
   `csrf_token` form field (an HTML form cannot set a header).
4. **Router** — resolves the current session into a `Viewer`, calls services,
   renders a template.

Templates never touch the database. Everything they need arrives through
`deps.base_context()`, which supplies `brand`, `user`, `csrf_token`, `flash`,
`due_cards`, `unread` and `stats`, plus the navigation and breadcrumb structures
described below.

## Navigation is data

The site has roughly sixty pages. For most of its life the list of them was
written out four separate times — the desktop top bar, the five footer columns,
the mobile bottom bar and the sitemap — and each copy was edited on its own. They
drifted until:

* the top bar said **Practice** and the footer heading said **Practise**;
* the top bar said **Code** for `/programming` while the footer said **Learn to
  code** for the same URL, beside a different item called **Learn**;
* the bottom bar lit up **My stream** while the reader was on `/explore` and
  **Sheets** while they were on `/projects`, because each link tested its own
  overlapping prefixes independently;
* about fifteen pages — the mistake notebook, the heatmap, today's plan, the
  leaderboard, onboarding, installing the app, videos, books — were reachable
  only from the footer, if at all;
* all 45 branch hubs at `/branches/{slug}` had no inbound link anywhere, because
  the catalogue's branch picker only ever filtered the page it was on;
* `/sitemap.xml` listed twenty paths and omitted `/sheets`, a top-bar item, and
  every sheet slug with it.

`engineverse/navigation.py` replaces the four copies with one ordered table of
`Destination` records grouped into `Section` records. Everything else is derived:

| Surface | Built by |
|---|---|
| Desktop top bar (6 grouped entries with menus) | `primary_nav()` |
| Mobile bottom bar (5 items, exactly one active) | `mobile_nav()` + `active_mobile()` |
| Mobile menu panel (every group, expanded) | `index_sections()` |
| Footer columns | `footer_columns()` |
| Breadcrumb trail on every page | `breadcrumb_trail()` |
| The full index at `/resources` | `index_sections()` |
| `/sitemap.xml` | `indexable_paths()` |
| The GitHub Pages export list | `indexable_paths(public_only=True)` |

Three properties make the derivation work rather than just move the duplication:

**A destination owns its child pages.** `match` lists the URL prefixes that mean
"you are here", compared on a path-segment boundary with the longest match
winning. So `Practice sheets` claims `/sheets` *and* `/sheets/arrays-hashing`,
while `/practice` does not swallow `/practice/problems` and `/stream` does not
swallow `/streams`. Active-link highlighting and the breadcrumb trail both read
this, which is why neither is hand-written per template any more.

**A group label is a real link.** Each section names a `landing` page, so the top
bar is one click from the most useful page in every group for a reader who never
opens a menu. The menus themselves open on `:hover` and `:focus-within`; because
the label sits *inside* the group, tabbing to it opens the menu and puts its links
in the tab order. No JavaScript, and no link is ever focusable while invisible.

**Audience is part of the data.** `signed_in` records that the application
redirects an anonymous request to `/login`, and
`test_navigation.py::test_signed_in_flags_match_what_the_application_actually_does`
checks that claim against the running app — six destinations were originally
marked as gated merely because they work *better* with an account, which would
have hidden working pages from signed-out readers and dropped them from the
static export. `member_only` is the separate, weaker claim that a page renders
but the label would be a lie: `/stream` answers an anonymous request by
redirecting to some default branch, which is not what "My stream" promises.
`Section.for_audience()` filters both and re-points each group label at a public
landing page, so no surface ever offers a signed-out reader a link whose only
effect is a bounce.

Two surfaces exist to answer "what is on this site?" rather than "where next?".
`/resources` lists every destination in its group with the blurb from the table
and the row count this instance actually holds, read from the database, so a
deployment seeded with less shows less. It opens with three ways in by intent —
just started, revising for an exam, preparing for interviews — because a taxonomy
is not an answer to "I have twenty minutes". `/explore` carries the branch
browser: all 45 branch hubs with links to both `/branches/{slug}` and their study
hub, collapsed by default. Before it those 45 pages had no inbound link anywhere,
because the catalogue's branch picker only ever filtered the page it sat on.

## The page outline is part of the interface

A reader who navigates by heading hears the outline, and a page that goes from
`<h1>` to `<h4>` tells them three levels of structure are missing. Nearly every
page did, for two separate reasons.

The footer's column headings were `<h4>`, and the footer is on every page, so the
skip was site-wide from the bottom of every document. They are `<h2>` now;
`.footer h2` in the stylesheet keeps them at the size the design wanted.

The other reason was `markdown.py`, which shifted every heading by a flat `+2` on
the assumption that content is rendered inside a section that is itself an `<h2>`
under the page's `<h1>`. That holds for topic notes. It does not hold for a
problem statement, which sits directly under the `<h1>` and writes its first
heading as `###` — so +2 made it an `<h5>` with no `<h2>`, `<h3>` or `<h4>`
before it, on all 95 coding problems. `render()` now takes a `base` level and
aligns the block's *shallowest* heading to it, keeping the relative depth the
author wrote and guaranteeing the block starts where its container expects.
`_heading_shift()` ignores fenced code blocks, because a `#` comment inside one
is not a heading.

`test_links.py::test_no_page_skips_a_heading_level` walks every indexable
destination plus a sample of detail pages and fails on any skip, so a new
template cannot reintroduce one.

## The judge

Submissions never run in the web process. `engineverse/judge` picks a provider:

- **`local`** — a development runner that executes in a scrubbed child process
  with resource ceilings, no outbound network, a private PID namespace/procfs,
  and tmpfs mounts over the app tree and home directory. It is available only
  when the network, PID and mount namespace probes succeed; otherwise it refuses
  to run learner code. It is not a separate container or a production boundary.
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

## The tutor

`engineverse/tutor.py` answers study questions from the platform's own content.
There is no model call and no external service, which is a consequence of the
self-hosting constraint rather than a shortcut around it.

The sequence is retrieve, filter, compose:

1. **Retrieve** through `search.search()`, the same index the search box uses, so
   the tutor can never surface content a student could not have found themselves.
2. **Filter** to hits that actually contain the question's subject words. This
   step is the reason the tutor is safe to trust. The search deliberately falls
   back from an AND match to an OR match to a LIKE match so a search box is never
   empty — correct behaviour there, and dangerous here, because the OR fallback
   answered "how do I bake a souffle" with CPU scheduling notes. Requiring
   overlap with the question's content words is what turns "found something" into
   "found something about this".
3. **Compose** from note sections and formulae, minting numbered citations as it
   goes. The citation cap is applied when a reference is minted rather than by
   truncating the list afterwards, so the answer can never cite a `[6]` the
   reader cannot look up.

If nothing survives the filter the tutor says so and returns no prose. It would
be easy to produce a fluent paragraph anyway; a study tool that invents
explanations is worse than one that admits a gap, so it does not.

Two invariants the tests hold: every source is a relative platform URL, and note
bodies are stripped of markup server-side before they enter an answer, so a
stored `<script>` cannot reach a client even one that trusted the response.

## The search index is derived data

`search_index` is a rebuildable projection of the content tables, not a table
anyone writes to directly. Both the search box and the tutor read it, so when it
falls behind, content exists but cannot be found — which is why staleness is
handled rather than assumed away.

Nothing indexes a row at the moment it is written. Two things close that gap:

- `search.refresh_if_stale()` runs at startup and compares hashes of the exact
  indexed source fields — including timestamp-free module/card tables, note
  sections, project steps and searchable profile settings — against the marker
  written at the last build. Inserts, edits and deletes invalidate it. The stored
  marker contains counts and digests, not source text. The schema-version marker
  alone is not enough: it records which *shape* of index the code produces, and
  once it matches it stays matched.
- `scripts/reindex.py` rebuilds on demand, which is what an operator runs after
  inserting catalogue rows by hand. `--check` reports what the index holds
  without changing it.

Notes are indexed once per topic, merging every published note that topic has.
They used to be indexed one entry per note keyed by the topic slug; since
`index_entity()` deletes before inserting, a topic's notes overwrote each other
and only the last one read survived. Prose is capped at `MAX_BODY_CHARS`, sized
from measurement: merged topic notes run to a median of 5.4k characters and a
maximum of 11.3k, and the previous 4000-character cap truncated 47 of 48 topics.
The same index includes each public programming module and flashcard prompt, so a
search can deep-link to a module section or the public card browser. Flashcard
answers are deliberately excluded from indexed text and search snippets.

`ENTITY_URLS` is the only place that knows how to turn an indexed row into a
link, and four of its sixteen entries were wrong in a way a 404 check cannot
see. A URL that resolves to *something else* still answers 200:

| Entry | Was | Why it failed |
|---|---|---|
| `question` | `/practice/questions/{slug}` | no such page; that path exists only under `/api` |
| `video` | `/videos#{slug}` | the page renders no ids, and paginates 400 rows 24 at a time |
| `book` | `/books#{slug}` | same, over 395 rows |
| `resource` | `/resources#{slug}` | `/resources` is the site index; the shelf is `/resources/offsite` |
| `formula` | `/formulas#{slug}` | the sheet capped at 300 of 365 rows, so 65 had no anchor anywhere |

The four collection entries now carry `?slug=` and the pages filter on it, which
is the one approach that survives pagination: a fragment is never sent to the
server, so the reader landed on page one of a long list with the item they had
clicked several pages in. `backend/tests/test_links.py` asserts the property
that was missing — not that a URL resolves, but that it *shows the thing it
named* — and picks its sample from the far end of each collection, where a
fragment could never reach.

## 3D models are data, not markup

Every topic carries an interactive 3D model. The split is deliberate:

- **The renderer is code** (`static/js/engine3d.js`). ~900 lines of vanilla
  WebGL with no three.js and no CDN: `mat4`/`vec3` algebra, 14 mesh builders
  (box, sphere, cylinder, truncated cone, torus, plane, grid, axes, polyline,
  point cloud, swept tube, helix, arrow, parametric surface), Blinn–Phong
  shading with a key and fill light, and orbit/zoom/keyboard controls.
- **The models are data** (`models_3d.scene`, one JSON document per row).
  A scene is a camera, a list of objects and a list of labels — nothing else.

A scene cannot carry script the way an SVG can, because `validate_scene()` does
not sanitise it; it *rebuilds* it. Unknown keys are discarded, mesh names must
be on the allowlist, every number is clamped to a range, colours pass through
`safe_css_color()`, and label text loses anything that looks like markup or a
quote. What comes out contains only finite numbers, hex colours and allowlisted
strings, so there is no escaping step to get wrong — and a hand-edited row
cannot make a phone build a ten-million-vertex mesh.

The bounds are enforced on both sides, because a bound on one side is not a
bound. `test_models3d.py` reads the mesh names straight out of the JavaScript
and fails if the two vocabularies drift; `scripts/check_scenes.js` builds all 56
shipped scenes with the browser's own code.

One lesson is encoded as a permanent test. `validate_scene()` drops objects it
cannot understand rather than failing, which is right for untrusted input and
dangerous for your own content: a stray `*` in front of a helper returning a
dict unpacked the dict's *keys*, eight objects became junk strings, the
validator dropped them, and the Venturi model shipped without its streamlines.
Nothing errored. `test_validation_drops_nothing_from_a_seeded_scene` now asserts
that the object count going in equals the object count coming out.

Progressive enhancement still holds: without JavaScript or WebGL the page shows
the title, the caption and the written notes. The caption carries the lesson;
the canvas carries the intuition.

## Data layer

`db/schema.sql` is the development schema (SQLite, 68 tables; a migrated
database holds 75, because `db.migrate()` adds `schema_meta`, `search_log`,
`search_index` and that table's five FTS shadow tables) and
`db/postgres/schema.pg.sql` mirrors it for production. They share the model
exactly and differ only where scale demands it: hash partitioning on the hot
tables, `citext` for case-insensitive emails, `jsonb` for indexed payloads,
`tsvector` for full-text search, and `BIGINT` for counters that a 32-bit integer
would overflow. See `db/postgres/README.md`.

## Sessions and the signed-in tab bar

EngineVerse is served two ways, and both have to answer "am I signed in?" before
the first paint:

* **The FastAPI app** issues one opaque session cookie (`ev_session`), stored as
  an HMAC of its random token in `sessions`; `read_session()` is the only way a
  request learns who the caller is, and every page renders the top bar from that
  answer. Nothing about the header is decided in JavaScript here.
* **The exported reading copy** on GitHub Pages has no server and no database, so
  `pages-live.js` keeps the learner record itself: `localStorage` and
  `sessionStorage` under `ev:learner-store:v2`, mirrored into a first-party
  cookie, `window.name`, IndexedDB and a `BroadcastChannel`, with the learner
  vault (`data/learners/registry.json`) as the shared, repository-backed copy.
  A nonce'd inline script in `base.html` reads that state and sets
  `html[data-ev-signed-in="true"]` *before* paint, which is what hides
  "Sign in / Start free" (CSS) while `hydrateNavigation()` swaps in the account
  icon, streak and XP chips. If any of those lookups fails, the page still
  loads, so the failure is silent: `backend/tests/test_pages_live_contract.py`
  checks the exported markup against every id the runtime looks up, and
  `scripts/check_auth_flow.js` drives the real exported pages under jsdom.

A six-digit delivered code is required in exactly three places - creating a new
account, recovering a forgotten password, and changing a password - and never on
an ordinary sign-in by a learner whose account is already verified. On the server
that is `ENGINEVERSE_LOGIN_OTP=signup_only` (see
[Deployment](DEPLOYMENT.md#sign-in-factors-and-optional-delivered-codes)); in the reading copy the code is shown
on the page, because a static host has no mail or SMS transport behind it.

## What is deliberately absent

- **No ORM.** The SQL is the interface.
- **No client build step.** No npm, no bundler, no CDN.
- **No 3D library.** The WebGL renderer is written here rather than vendoring
  three.js, for the same reason LaTeX is: one less supply chain, and the whole
  of it is readable.
- **No third-party auth.** Credentials, sessions and CSRF are implemented here.
- **No hosted services.** Videos link out to NPTEL, MIT OCW and freeCodeCamp;
  books link to the publisher or the open-access source. Nothing copyrighted is
  re-hosted.
- **No dependency for LaTeX.** `markdown.py` renders fractions, roots,
  subscripts, superscripts and Greek letters to HTML directly.
