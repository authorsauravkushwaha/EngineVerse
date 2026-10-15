"""Capstone project briefs: one substantial, shippable build per language path.

Each brief is a full ``projects`` row in the shape ``library_data.PROJECTS``
uses, plus a ``language`` key that links it to its programming path. The
language page links forward to the brief; the brief links back to the path.

A capstone here is deliberately more than a title. Every entry describes:

* a real problem worth solving and why the naive solution fails;
* prerequisites (which path stages to finish) and the outcomes the build proves;
* ordered build milestones (``steps``) that each end in something testable;
* testing expectations, including the security assertions that must exist;
* resources (external links, checked by ``scripts/check_links.py``);
* a shippable result (``expected_output``) a learner can demo and put on a résumé.

The briefs match the capstone module of each path but stand alone: the module
teaches the shape, the project brief is the six-milestone build with its own
tests, resources and definition of done.
"""
from __future__ import annotations

CAPSTONES: list[dict] = [
    # ---------------------------------------------------------------- Python
    {
        "slug": "python-field-notes-api",
        "title": "Tested Field-Notes API with a Bounded Summarizer",
        "language": "python",
        "branch": "computer-science",
        "subject": None,
        "difficulty": "advanced",
        "category": "software",
        "est_hours": 36,
        "summary": "Build a small, fully tested Python service that records field or lab observations, "
                   "stores them safely in SQLite, exposes a validated HTTP API, and offers one strictly "
                   "bounded summarizer tool - the capstone for the Python path.",
        "problem_statement": "A field team captures observations in chat threads and camera rolls, then loses "
                             "them: nothing is searchable, nothing is attributed, and the end-of-day summary "
                             "is whoever remembers to write one. Off-the-shelf note apps need connectivity the "
                             "site does not have, and exporting everything into a model account is not allowed "
                             "because the observations are sensitive.\n\nThe team needs a local-first tool they "
                             "trust: observations recorded with a timestamp and tags, stored on the device, "
                             "searchable without a network, and a daily summary that is generated from their "
                             "own data by code they can read - not by a service they cannot audit.",
        "objective": "Ship a Python package plus FastAPI service where a user can record, tag, list and search "
                     "observations; data persists in SQLite through parameterized queries only; every input "
                     "crossing the HTTP boundary is validated server-side; and a single allowlisted summarizer "
                     "tool composes a day's notes deterministically (no model call required). Outcomes the "
                     "build proves: you can structure a Python project into modules with tests, you treat every "
                     "boundary as untrusted, and you can bound an automation so its worst case is acceptable.",
        "prerequisites": [
            "Python path: Foundations and Working Practice stages complete (functions, collections, errors, modules, pytest)",
            "Python path: Advanced Engineering modules on FastAPI validation and SQLite persistence",
            "Comfortable running pytest and reading a traceback to the failing assertion",
        ],
        "hardware": "Any laptop that runs Python 3.11+. No server, GPU or paid API account is required.",
        "software": "Python 3.11+, FastAPI, uvicorn, SQLite (standard library sqlite3), pytest, Git.",
        "architecture": "Three layers with one direction of dependency. A storage layer owns SQLite and exposes "
                        "typed functions (add_observation, search_observations) built only from parameterized "
                        "queries. A service layer holds the rules - required fields, timestamp handling, tag "
                        "normalisation, the summarizer - and knows nothing about HTTP. A FastAPI layer validates "
                        "request bodies with Pydantic models, maps service errors to deliberate status codes, "
                        "and never trusts a value that arrived from a client. The summarizer is a plain "
                        "function over the day's rows: counts, tags and the first line of each observation - "
                        "deterministic, offline and auditable. An optional later milestone may put a model "
                        "behind that same function signature, with an allowlist and confirmation, but the "
                        "shipped default never calls out.",
        "source_code": "Suggested layout:\n\n```\nfieldnotes/\n  __init__.py\n  storage.py      # sqlite3 connection, schema, parameterized queries only\n  service.py      # rules: validation, tagging, search, summarize_day()\n  api.py          # FastAPI app: Pydantic models, status codes, error mapping\n  cli.py          # optional offline entry point for the same service\ntests/\n  test_storage.py # round-trips, injection attempts, concurrent writes\n  test_service.py # rules incl. boundaries: empty day, huge tag list, unicode\n  test_api.py     # 400/401/404/413 paths, response shapes\n```\n\nWrite the storage layer against a file-based database in tests "
                       "(tmp_path), not an in-memory singleton, so connection handling is exercised. Keep every "
                       "SQL string in storage.py with `?` placeholders; a code review rule of 'no f-string "
                       "touches SQL' is easy to enforce and easy to grep.",
        "database_design": "One table is enough to start: `observations(id TEXT PRIMARY KEY, recorded_at "
                           "INTEGER NOT NULL, body TEXT NOT NULL, tags TEXT NOT NULL DEFAULT '[]')` with tags "
                           "as a JSON list, plus an FTS5 virtual table over body/tags if you add search. Every "
                           "write goes through a helper that binds parameters. Never interpolate a tag or a "
                           "search term into SQL, and store timestamps as UTC epoch milliseconds so ordering "
                           "and 'today' queries do not depend on the device's locale.",
        "testing": "pytest from milestone one, not at the end. Unit tests cover the service rules including "
                   "boundaries (empty day, exactly midnight, 200 tags, emoji and RTL text in bodies). Storage "
                   "tests include an injection attempt: an observation body of `'); DROP TABLE observations; "
                   "--` must round-trip as inert text. API tests use FastAPI's TestClient and assert the "
                   "status codes you chose - 400 for malformed bodies, 413 for oversized ones, 404 for unknown "
                   "ids - and that an oversized request is rejected before it is parsed. The summarizer test "
                   "pins the exact output for a fixed input day so a refactor that changes behaviour fails "
                   "loudly.",
        "expected_output": "A running local service: `uvicorn fieldnotes.api:app` answers POST /observations, "
                           "GET /observations?tag=..., and GET /summary?day=2026-10-11 with validated JSON; a "
                           "pytest suite passes with the security cases included; a README shows the curl "
                           "commands and the test output. Someone else can clone it, seed a day of notes and "
                           "read the summary the tool produced - and point at the function that produced it.",
        "improvements": [
            "Add full-text search (SQLite FTS5) and measure query time on 10k seeded rows.",
            "Put a model behind the summarizer signature with an allowlist, a hard output bound and a confirmation step - then write the threat model for it.",
            "Package with pyproject.toml and publish to a private index; add a GitHub Actions workflow that runs pytest on push.",
            "Add an export endpoint that streams JSONL with a bounded response size.",
        ],
        "resume_md": "**Field-Notes API** | Python, FastAPI, SQLite, pytest\n"
                     "- Built a validated local-first observation service: parameterized persistence, server-side "
                     "input bounds and a deterministic summarizer.\n"
                     "- Wrote the test suite first for the storage and rules layers, including SQL-injection and "
                     "oversized-request cases.",
        "interview_questions": [
            "Why does validation live in the API layer when the service layer also checks its rules?",
            "Show the exact line where a search term enters SQL. Why can it not change the query's meaning?",
            "What is the worst thing the summarizer can do, and which line of code makes that the worst thing?",
            "How do your tests prove a 10 MB request body is rejected before being parsed?",
        ],
        "tech": ["Python", "FastAPI", "SQLite", "pytest", "Pydantic"],
        "skills": ["project structure", "parameterized SQL", "input validation", "test-first development", "bounding automation"],
        "steps": [
            ("1. Shape and rules", "Define the observation and write the service rules with tests",
             "Create the package layout and a plain dataclass for an observation (body, tags, recorded_at). In "
             "service.py write add_observation() and list_for_day() with the rules you want - non-empty body, "
             "bounded length, tag normalisation (lowercase, dedupe, max count) - and write tests/test_service.py "
             "against an in-memory fake storage first. Done when pytest is green with boundary cases: empty "
             "body, 5,000-character body, duplicate tags, unicode."),
            ("2. Persistence", "Implement the SQLite storage layer with parameterized queries only",
             "Write storage.py: connect to a file database, create the schema if absent, and implement "
             "insert/search with `?` placeholders everywhere. Swap the service's fake for the real storage in "
             "tests. Add the injection test (hostile body text round-trips as data) and a re-open test (data "
             "survives a new connection). Done when the same suite passes against a real file on disk."),
            ("3. Search", "Add tag and text search without touching SQL construction",
             "Implement search_observations(term, tag) with bound LIKE parameters or an FTS5 table. Test that a "
             "search term containing `%` or `'` matches literally and cannot widen the query. Decide and "
             "document the case-sensitivity rule. Done when search tests pass, including the hostile-term "
             "case."),
            ("4. HTTP boundary", "Expose the service through FastAPI with validation and honest status codes",
             "Build api.py with Pydantic request models, a size bound on bodies, and explicit status codes: "
             "201 on create, 400 malformed, 404 unknown, 413 too large. Map service exceptions with an "
             "exception handler so stack traces never reach a response. TestClient tests assert each code and "
             "that error bodies carry no internals. Done when tests/test_api.py covers every branch you "
             "defined."),
            ("5. The bounded summarizer", "Compose summarize_day() deterministically, then pin it with a test",
             "Implement summarize_day(day): counts per tag, first lines of each observation, earliest/latest "
             "timestamps - pure function over storage rows, no network, no model. Write a golden test: a fixed "
             "seeded day must produce byte-identical summary JSON. Add GET /summary with the same validation "
             "discipline. Done when the golden test passes and the README shows the endpoint's output."),
            ("6. Ship it", "Harden, document and hand it over",
             "Run the whole suite under `pytest -q` and fix the skips. Add a rate limit or a concurrency guard "
             "on writes if you served it anywhere real. Write the README: setup, curl examples, test "
             "instructions, and a short threat model naming what the API refuses to do. Tag v1.0.0. Done when "
             "a classmate can clone, install, test and run it without asking you a question."),
        ],
        "resources": [
            ("documentation", "sqlite3 - DB-API 2.0 interface for SQLite", "https://docs.python.org/3/library/sqlite3.html",
             "The standard-library driver: parameter binding, row factories and the warnings about sharing connections across threads."),
            ("documentation", "FastAPI security and validation docs", "https://fastapi.tiangolo.com/tutorial/security/",
             "Official guidance for the patterns used at the HTTP boundary: validation, dependency-injected auth and error handling."),
        ],
    },
    # ------------------------------------------------------------------ Java
    {
        "slug": "java-room-booking-service",
        "title": "Room-Booking Service with JDBC Persistence and Proven Authorization",
        "language": "java",
        "branch": "computer-science",
        "subject": None,
        "difficulty": "advanced",
        "category": "software",
        "est_hours": 40,
        "summary": "Build a Java HTTP service that ends double-booked rooms: domain rules proved by JUnit, "
                   "JDBC persistence with prepared statements, and an authorization check on every endpoint - "
                   "the capstone for the Java path.",
        "problem_statement": "A department books rooms through a shared spreadsheet. Two societies regularly "
                             "claim the same hall for the same evening, the 'booked' column is edited by "
                             "anyone, and when a clash is noticed nobody can say who made the booking. The "
                             "fix everyone proposes - 'lock the sheet' - does not survive the first deadline "
                             "week.\n\nWhat the department actually needs is a small booking service with a "
                             "rule the spreadsheet cannot break: a room cannot hold two overlapping bookings. "
                             "The rule has to be enforced where the data is written, proved by tests, and "
                             "protected so that only the right people can create or cancel bookings.",
        "objective": "Ship a Java service where a booking is created only if it does not overlap an existing "
                     "one, every SQL statement is a PreparedStatement, every endpoint checks a capability "
                     "server-side, and a JUnit suite proves each rule - including the overlap rule at its "
                     "exact boundaries. Outcomes the build proves: you can express a domain invariant in code "
                     "and tests, you can persist through JDBC without opening an injection, and you treat "
                     "authentication and authorization as two different checks.",
        "prerequisites": [
            "Java path: Foundations and Working Practice stages complete (classes, interfaces, exceptions, JUnit, build tool)",
            "Java path: Advanced Engineering modules on HTTP services, JDBC and capability checks",
            "A build tool (Maven or Gradle) running tests from the command line",
        ],
        "hardware": "Any machine with a JDK 17+ and a build tool. SQLite keeps the setup single-file.",
        "software": "JDK 17+, the built-in com.sun.net.httpserver (or Javalin/Spark if you prefer a framework), "
                    "SQLite via JDBC, JUnit 5, Maven or Gradle.",
        "architecture": "A Booking domain type validates its own invariants in its constructor (end after "
                        "start, non-blank room and organiser). A BookingRepository owns the database and "
                        "exposes findOverlapping(room, start, end) and save(booking) - both prepared "
                        "statements, the overlap check expressed in SQL with bound timestamps. A BookingService "
                        "runs the use case: look for overlaps, refuse with a typed BookingConflictException, "
                        "or save. The HTTP layer parses JSON, authenticates the session, then checks the "
                        "required capability per route before calling the service - a 401 for no session, a "
                        "403 for a session without the capability. Dependency direction is one-way: HTTP -> "
                        "service -> repository -> database.",
        "source_code": "Suggested layout:\n\n```\nsrc/main/java/booking/\n  domain/Booking.java, BookingConflictException.java\n  repo/BookingRepository.java        # JDBC, prepared statements only\n  service/BookingService.java        # the overlap use case\n  web/BookingHttpServer.java, Session.java, Capabilities.java\nsrc/test/java/booking/\n  BookingTest.java                   # domain invariants\n  BookingRepositoryTest.java         # against a temp SQLite file\n  BookingServiceTest.java            # overlap boundaries with a fake repo\n  BookingHttpTest.java               # 401/403/409/201 paths\n```\n\nName tests after behaviour: `createRefusesOverlappingBooking`, "
                       "`cancelRequiresBookingCancelCapability`. The capability check lives in one method the "
                       "HTTP layer calls per route, so a new route cannot forget it silently - and a test "
                       "asserts every registered route declares one.",
        "database_design": "`bookings(id TEXT PRIMARY KEY, room TEXT NOT NULL, starts_at INTEGER NOT NULL, "
                           "ends_at INTEGER NOT NULL, organiser_id TEXT NOT NULL, created_at INTEGER NOT NULL)` "
                           "with an index on (room, starts_at). The overlap query is the heart of the system: "
                           "`SELECT id FROM bookings WHERE room = ? AND starts_at < ? AND ends_at > ?` with "
                           "bound values - two intervals overlap exactly when each starts before the other "
                           "ends. Timestamps are UTC epoch millis so comparisons are plain integer "
                           "comparisons. A UNIQUE partial constraint cannot express interval overlap in "
                           "SQLite, so the service check plus a serialized write path is the invariant "
                           "keeper - document that trade-off in the README.",
        "testing": "JUnit from milestone one. The domain tests pin the constructor rules. The service tests "
                   "use a fake repository and cover the four boundary relationships: new booking ends exactly "
                   "when an existing one starts (allowed), starts exactly when one ends (allowed), overlaps by "
                   "one millisecond at either end (refused), and fully contains one (refused). Repository "
                   "tests run against a temporary SQLite file and include an organiser named `Robert'); DROP "
                   "TABLE bookings;--` that must persist as inert text. HTTP tests assert 401 without a "
                   "session, 403 with a session lacking the capability, 409 on conflict and 201 on success.",
        "expected_output": "A service that starts with one command, answers POST /bookings, GET "
                           "/bookings?room=... and DELETE /bookings/{id} over HTTP, refuses overlapping "
                           "bookings with a 409 that names the clash, and rejects unauthorized callers with "
                           "401/403 - with a green `mvn test` (or `gradle test`) covering every rule above. "
                           "The README shows a curl session that books a hall, tries to double-book it and "
                           "gets refused.",
        "improvements": [
            "Add recurring bookings and extend the overlap rule to a date series - the boundary tests get interesting.",
            "Move the write path into a serializable transaction (or Postgres exclusion constraint) and document what each guarantees.",
            "Add an audit log of who created and cancelled what, written in the same transaction as the booking.",
            "Expose an iCalendar feed of a room's bookings.",
        ],
        "resume_md": "**Room-Booking Service** | Java, JDBC, SQLite, JUnit 5\n"
                     "- Enforced a no-double-booking invariant in service code and SQL, proved by boundary tests "
                     "(touching intervals allowed, one-millisecond overlap refused).\n"
                     "- Prepared-statement-only persistence and a per-route capability check with 401/403/409 paths "
                     "covered end to end.",
        "interview_questions": [
            "Write the overlap condition for two intervals and explain why `<` and `>` (not `<=`) are correct for touching bookings.",
            "A valid session arrives at DELETE /bookings/{id}. Walk through every check before the row is deleted.",
            "Why can a UNIQUE constraint not enforce 'no overlapping interval' in SQLite, and what did you do instead?",
            "Your repository test stores a SQL injection string as an organiser name. What exactly does that prove?",
        ],
        "tech": ["Java 17", "com.sun.net.httpserver", "SQLite JDBC", "JUnit 5", "Maven"],
        "skills": ["domain modelling", "prepared statements", "authentication vs authorization", "boundary testing", "HTTP status design"],
        "steps": [
            ("1. The domain rule", "Model Booking and prove its invariants with tests",
             "Write Booking as an immutable type whose constructor rejects end-before-start, blank rooms and "
             "blank organisers. Write BookingTest first if you like the red-green discipline. Done when `mvn "
             "test` shows the invariant tests passing and a deliberately broken constructor makes them fail."),
            ("2. The overlap use case", "Implement BookingService against a fake repository",
             "Define the repository interface (findOverlapping, save, deleteById) and a fake in test scope. "
             "Implement the create use case: refuse with BookingConflictException when findOverlapping returns "
             "anything. Write the four boundary tests (touching allowed at both ends, one-millisecond overlap "
             "refused at both ends, containment refused). Done when the fake-backed suite is green."),
            ("3. Real persistence", "Implement the repository with JDBC prepared statements",
             "Create the schema on startup, implement the three methods with `?` placeholders only, and run "
             "the service tests against a temp-file SQLite database. Add the hostile-organiser round-trip "
             "test and a restart test (bookings survive a new connection). Done when every SQL string in the "
             "repository is a prepared statement and the tests prove the injection string is inert."),
            ("4. The HTTP layer", "Serve JSON with deliberate status codes",
             "Wire com.sun.net.httpserver (or your framework): parse JSON bodies with a size bound, map "
             "BookingConflictException to 409, malformed input to 400, unknown ids to 404, success to 201 with "
             "the created booking. Errors return a small JSON reason - never a stack trace. Done when curl "
             "exercises every code and the HTTP tests assert them."),
            ("5. Authn then authz", "Add sessions and a per-route capability check",
             "Implement a minimal session (a signed token or a server-side map keyed by a random id) and a "
             "capability check: bookings.create for POST, bookings.cancel for DELETE. No session -> 401; "
             "session without capability -> 403; the check runs before the service call on every route. Add a "
             "test that enumerates registered routes and fails if one lacks a declared capability. Done when "
             "the 401/403 tests pass and the route audit test is green."),
            ("6. Ship it", "Document, package and hand over",
             "Write the README: run instructions, the curl double-booking demo, the status-code table and the "
             "known limitation (interval uniqueness enforced in the service, not the schema). Package a "
             "runnable jar. Tag v1.0.0. Done when a classmate follows the README, reproduces the refused "
             "double-booking, and the full suite passes on their machine."),
        ],
        "resources": [
            ("documentation", "JDBC Basics (Oracle Java tutorial)", "https://dev.java/learn/jdbc/",
             "Official walkthrough of connections, statements and prepared statements - the patterns the repository layer uses."),
            ("documentation", "JUnit 5 User Guide", "https://junit.org/junit5/docs/current/user-guide/",
             "Assertions, parameterized tests and the lifecycle annotations used to prove the booking rules."),
        ],
    },
    # ------------------------------------------------------------ JavaScript
    {
        "slug": "js-revision-dashboard",
        "title": "Revision Dashboard with a Node Service and Safe DOM Rendering",
        "language": "javascript",
        "branch": "computer-science",
        "subject": None,
        "difficulty": "intermediate",
        "category": "software",
        "est_hours": 30,
        "summary": "Build a study dashboard: a Node HTTP service with bounded, validated requests, a browser "
                   "front end that renders untrusted text safely, and node:test suites on both sides - the "
                   "capstone for the JavaScript path.",
        "problem_statement": "A student keeps revision cards in a JSON file and reviews them by scrolling the "
                             "raw file. They want a dashboard: what is due today, a card count per subject, "
                             "and a way to add a card from the browser. Two earlier attempts failed in "
                             "instructive ways. The first pasted card text with innerHTML and a card "
                             "containing `<img src=x onerror=...>` (copied from a lecture slide about XSS) "
                             "ran script in their own browser. The second crashed the Node server whenever a "
                             "malformed JSON body was posted, because nothing caught the parse error.\n\nThe "
                             "dashboard has to treat both the browser and the network as sources of untrusted "
                             "input, and it has to keep working when either misbehaves.",
        "objective": "Ship a two-part app: a Node HTTP API (no framework required) that validates and bounds "
                     "every request, stores cards in a JSON file through atomic writes, and a front end that "
                     "fetches and renders with textContent only. node:test suites cover the API's status "
                     "codes and the due-today rule with an injected clock. Outcomes the build proves: you can "
                     "run a real event-loop service without a framework, you render untrusted data without "
                     "opening an XSS hole, and your tests do not depend on the wall clock.",
        "prerequisites": [
            "JavaScript path: Foundations and Working Practice stages complete (objects, arrays, DOM, async, Node service, node:test)",
            "Comfortable with fetch, promises and the difference between microtasks and timers",
        ],
        "hardware": "Any machine with Node.js 20+ (for the built-in test runner). A browser.",
        "software": "Node.js 20+ (node:http, node:test), no npm dependencies required; a static file server or `npx serve` for the front end during development.",
        "architecture": "The Node service owns cards.json: it loads once, keeps the array in memory, and "
                        "writes atomically (write a temp file, then rename) so a crash cannot truncate the "
                        "store. Routes: GET /api/cards?due=today, POST /api/cards, and a tiny GET / handler "
                        "serving the static page. Every request body is size-bounded (e.g. 16 KB, respond 413 "
                        "before buffering more), parsed inside try/catch (400 on failure), and validated "
                        "against an explicit shape - front, back, subject, dueDate - with types and bounds "
                        "checked by hand or a small schema function. The browser page fetches JSON and builds "
                        "DOM nodes with createElement/textContent; user-provided strings never reach "
                        "innerHTML. The due-today rule lives in a pure function `isDue(card, today)` so the "
                        "server and the tests share one definition of 'today'.",
        "source_code": "Suggested layout:\n\n```\nserver.js        # node:http server, routes, bounds, atomic writes\nstore.js         # load/save cards.json, addCard with validation\nrules.js         # isDue(card, today) - pure, shared with tests\npublic/index.html, public/app.js   # fetch + safe DOM rendering\ntest/store.test.js, test/rules.test.js, test/server.test.js\n```\n\nIn app.js, one helper does all rendering: `function cardElement(card)` that builds the "
                       "node tree with textContent. Code review rule: innerHTML appears nowhere; a grep in CI "
                       "proves it. server.test.js boots the server on port 0 (ephemeral) and exercises it "
                       "with fetch, so tests never fight over a fixed port.",
        "database_design": "cards.json is an array of objects: `{id, front, back, subject, dueDate}` where id "
                           "is a randomUUID() and dueDate is an ISO date string. Atomic save: write "
                           "cards.json.tmp then fs.renameSync over cards.json - rename is atomic on the same "
                           "filesystem, so readers never see a half-written file. Keep a schema version field "
                           "at the top level so a future migration can detect old files.",
        "testing": "node:test throughout. rules.test.js pins isDue with an injected today: due yesterday "
                   "(true), due today (true), due tomorrow (false), missing dueDate (false, and document the "
                   "choice). store.test.js covers validation rejections (missing front, 100 KB back, dueDate "
                   "that is not a date) and the atomic-write behaviour after a simulated failure. "
                   "server.test.js asserts the status-code contract: 200 list, 201 create, 400 malformed "
                   "JSON, 400 schema-invalid, 413 oversized body - posting a card whose front is `<img "
                   "src=x onerror=alert(1)>` must be stored verbatim and rendered inert by the front end.",
        "expected_output": "`node server.js` serves the dashboard; adding a card from the browser persists it "
                           "across restarts; a card containing HTML markup displays as literal text; `node "
                           "--test` passes on server, store and rules; the README shows the XSS card demo and "
                           "explains in two sentences why it is inert.",
        "improvements": [
            "Add subject filters and a due-today badge count, keeping every render through the one textContent helper.",
            "Swap cards.json for SQLite via node:sqlite (Node 22+) and keep the same API contract.",
            "Add an import route that accepts a pasted list of cards - then treat the paste as the untrusted boundary it is: bound it, validate every row, render a preview before saving.",
            "Serve with HTTP caching headers and measure what the browser re-fetches.",
        ],
        "resume_md": "**Revision Dashboard** | JavaScript, Node.js, node:test\n"
                     "- Built a dependency-free Node API with bounded, validated requests and atomic JSON "
                     "persistence; every status code covered by tests.\n"
                     "- Front end renders user-supplied card text through textContent only - an XSS payload "
                     "stored verbatim displays inert, with a test proving both halves.",
        "interview_questions": [
            "Where does an attacker-controlled string enter your server, and what are the three bounds applied before it is stored?",
            "Why is writing a temp file and renaming safer than writing cards.json directly?",
            "Your front end never uses innerHTML. What does it use for a card title with `<b>` in it, and what does the user see?",
            "How does isDue stay testable, and what would break if it read new Date() internally?",
        ],
        "tech": ["JavaScript", "Node.js", "node:http", "node:test", "fetch API"],
        "skills": ["event-loop services", "input bounding", "XSS-safe rendering", "atomic file writes", "deterministic testing"],
        "steps": [
            ("1. The rule first", "Write isDue(card, today) and its tests before any server code",
             "Create rules.js with the pure function and test/rules.test.js with an injected today covering "
             "yesterday/today/tomorrow/missing dueDate. `node --test` must pass. Done when you can explain why "
             "the function takes today as a parameter instead of reading the clock."),
            ("2. The store", "Load, validate and atomically save cards.json",
             "Implement store.js: load on start, addCard with explicit validation (non-empty strings, bounded "
             "lengths, ISO date check), randomUUID ids, and the temp-file-plus-rename save. Tests cover each "
             "rejection path and a round-trip through a real temp directory. Done when a malformed card can "
             "never reach the file."),
            ("3. The server", "Serve the API with bounded bodies and honest status codes",
             "Wire node:http routes over the store: GET /api/cards (optionally ?due=today via isDue), POST "
             "/api/cards. Accumulate request bytes with a hard cap - destroy the request and answer 413 past "
             "the cap - and parse JSON inside try/catch answering 400. Tests boot on port 0 and assert every "
             "code. Done when posting 1 MB or `{bad json` cannot crash or stall the server."),
            ("4. The safe front end", "Render the dashboard with createElement and textContent only",
             "Build public/app.js: fetch the cards, construct each card node through one helper that uses "
             "textContent for every user string, and show the due-today section using the same isDue logic "
             "(served by the API or re-implemented from rules.js in a shared module). Add the XSS card from a "
             "test fixture and confirm it displays as literal text. Done when `grep -rn innerHTML public/` "
             "finds nothing and the demo card is inert."),
            ("5. Failure paths", "Make the UI honest when the service misbehaves",
             "Handle fetch rejections and non-2xx responses in the UI: a visible error banner (also built with "
             "textContent), a disabled save button while a request is in flight, and no silent retries. Add a "
             "test that stops the server and asserts the page's error state function returns the right "
             "message. Done when killing the server mid-session produces a clear message, not a blank page or "
             "a console-only error."),
            ("6. Ship it", "Document, demo and hand over",
             "Write the README with run and test instructions, the status-code table, and the two-paragraph "
             "XSS demo walkthrough (store a payload, show it inert, show the test that proves it). Add `npm "
             "test` wiring to `node --test`. Tag v1.0.0. Done when a classmate runs the demo from the README "
             "alone and the suite passes on their machine."),
        ],
        "resources": [
            ("documentation", "MDN: Node.textContent", "https://developer.mozilla.org/en-US/docs/Web/API/Node/textContent",
             "The rendering primitive that keeps user text inert, and the documented difference from innerHTML."),
            ("documentation", "Node.js test runner (node:test)", "https://nodejs.org/api/test.html",
             "The built-in suite runner: test structure, assertions and the ephemeral-port pattern used by the API tests."),
        ],
    },
    # ------------------------------------------------------------ TypeScript
    {
        "slug": "ts-task-api-client",
        "title": "Typed Task API and Client with Runtime Validation and a Release Check",
        "language": "typescript",
        "branch": "computer-science",
        "subject": None,
        "difficulty": "advanced",
        "category": "software",
        "est_hours": 34,
        "summary": "Build a TypeScript task service and a typed client where every value crossing a boundary "
                   "is parsed at runtime, authorization is checked per route, and one command type-checks, "
                   "lints and tests before release - the capstone for the TypeScript path.",
        "problem_statement": "A student team shipped a JavaScript dashboard that broke three times in a "
                             "semester, each time because the API changed a field and the front end found out "
                             "at runtime: `task.due` became `task.dueDate`, `priority` started arriving as a "
                             "number instead of a string, and one deploy served tasks with `owner: null` to a "
                             "page that called `owner.name`. Nobody could say which side was wrong, because "
                             "neither side checked.\n\nThe rebuild has to make the contract explicit and "
                             "enforced twice: once by the compiler inside each codebase, and once at runtime "
                             "where data actually crosses the wire - including the case where a logged-in "
                             "student tries to delete someone else's task by calling the API directly.",
        "objective": "Ship a Node task API and a browser client, both TypeScript strict, sharing one schema "
                     "package: zod schemas define Task at the boundary, the API validates every input and "
                     "checks authorization per route, the client parses every response and renders only "
                     "narrowed values. A single `npm run check` runs tsc, eslint and vitest; CI refuses a "
                     "release when it fails. Outcomes the build proves: you know what types guarantee (and "
                     "what they do not), you can enforce authn/authz on a server whose clients you do not "
                     "control, and you can make quality gates one command wide.",
        "prerequisites": [
            "TypeScript path: Foundations and Working Practice stages complete (unions, narrowing, strict null checks, runtime schemas)",
            "TypeScript path: Advanced Engineering modules on Node authorization and typed agent/tool boundaries",
            "Working knowledge of npm scripts and a Git host with CI",
        ],
        "hardware": "Any machine with Node.js 20+.",
        "software": "Node.js 20+, TypeScript (strict), zod, vitest, eslint, a tiny HTTP layer (node:http or Hono/Express). No database server: a JSON file or in-memory store behind a repository interface.",
        "architecture": "Three packages in one repo (npm workspaces): `shared/` holds the zod schemas and the "
                        "inferred types (Task, TaskInput, ApiError) - the single source of the contract; "
                        "`server/` implements routes that parse req bodies with TaskInput, authorize every "
                        "mutation against the session's user (owner or admin), and answer with typed JSON; "
                        "`client/` parses every fetch response with the shared schema before rendering, so a "
                        "contract drift fails as a parse error with a clear message instead of a blank page. "
                        "The repository interface lets the server run against an in-memory store in tests and "
                        "a JSON file in development. Authorization lives in one `requireOwner(task, user)` "
                        "guard used by every mutating route.",
        "source_code": "Suggested layout:\n\n```\nshared/schema.ts        # zod schemas + inferred types (the contract)\nserver/routes.ts        # parse -> authorize -> act -> typed response\nserver/auth.ts          # session resolution, requireOwner guard\nserver/store.ts         # repository interface, JSON-file and memory impls\nclient/api.ts           # fetch wrapper: timeout, parse with shared schema\nclient/render.ts        # renders only schema-validated values\neach package: vitest tests next to the code\n```\n\nThe fetch wrapper sets an AbortController timeout (e.g. 5 s) and "
                       "returns a discriminated result - `{ok: true, task}` or `{ok: false, kind: "
                       "'network'|'schema'|'http'}` - so the UI branches on failure kinds the compiler knows. "
                       "The release gate is one script: `\"check\": \"tsc -b && eslint . && vitest run\"`, "
                       "wired into CI on every push.",
        "database_design": "Task: `{id: string (uuid), title: string (1..200), due: string (ISO date) | null, "
                           "priority: enum ['low','medium','high'], ownerId: string, done: boolean}`. Persist "
                           "as a JSON file with atomic rename, or an in-memory Map behind the repository "
                           "interface. The schema in shared/ is authoritative: the store re-validates on load "
                           "so a hand-edited file fails loudly at startup instead of serving `owner: null` to "
                           "the client - the exact third outage from the problem statement.",
        "testing": "vitest per package. Server tests: malformed bodies answer 400 with a schema-shaped error; "
                   "a session user deleting another user's task answers 403 (and the test calls the route "
                   "directly, not through the UI, to prove the guard is server-side); admin override works; "
                   "the timeout path returns the typed network error. Client tests: a mocked fetch returning "
                   "`due` instead of `dueDate` produces a schema failure result, not a render; a valid "
                   "response renders. Contract test: the same shared schema validates fixtures used by both "
                   "sides. `npm run check` must pass with zero eslint errors - configure the rules that "
                   "catch real defects (no-floating-promises, no-explicit-any as error).",
        "expected_output": "`npm run check` green in CI; `npm run dev` starts server and client; creating, "
                           "completing and deleting tasks works in the browser; a direct API call to delete "
                           "another user's task returns 403; renaming a field in shared/schema.ts breaks both "
                           "sides at compile time and, for untyped callers, at runtime parse - with the "
                           "failure named. The README documents the contract, the check command and the three "
                           "original outages with the mechanism that now prevents each.",
        "improvements": [
            "Generate an OpenAPI document from the zod schemas and validate responses against it in CI.",
            "Add optimistic updates in the client with rollback when the parsed response disagrees.",
            "Replace the JSON store with SQLite and keep every boundary parse unchanged - count how many files the swap touches.",
            "Add a typed webhook outbox so a second consumer gets schema-validated events.",
        ],
        "resume_md": "**Typed Task API + Client** | TypeScript, zod, Node.js, vitest\n"
                     "- Shared zod contract enforced at compile time and at runtime on both sides; three "
                     "historical field-drift outages each mapped to a gate that now fails the build.\n"
                     "- Per-route server-side authorization proven by direct API tests (owner-only mutations, "
                     "403 for other users), with one-command type-check/lint/test release gate in CI.",
        "interview_questions": [
            "A response parses against the shared schema at build A and fails at build B. List every mechanism in your repo that could have caught the drift earlier.",
            "Why is the 403 test written against the raw API instead of clicking the hidden button in the UI?",
            "What does `strict: true` plus strictNullChecks force in client/render.ts when task.due is `string | null`?",
            "Explain the discriminated result type your fetch wrapper returns and why the UI is safer with it than with try/catch alone.",
        ],
        "tech": ["TypeScript", "zod", "Node.js", "vitest", "eslint", "npm workspaces"],
        "skills": ["contract-first design", "runtime validation", "server-side authorization", "CI quality gates", "monorepo structure"],
        "steps": [
            ("1. The contract", "Write the shared zod schemas before either side exists",
             "Create the workspace and shared/schema.ts: Task, TaskInput (the create/update shape), ApiError "
             "and the inferred types. Pin the fields that caused the historical outages: dueDate naming, "
             "priority as an enum, ownerId non-nullable. Add schema unit tests with valid and invalid "
             "fixtures. Done when `tsc -b` and the schema tests pass with nothing else built."),
            ("2. The server core", "Parse, authorize, act - in that order, on every route",
             "Implement the store behind a repository interface, then routes that (1) parse the body with "
             "TaskInput answering 400 on failure, (2) resolve the session user, (3) call requireOwner for "
             "mutations answering 401/403, (4) act and return typed JSON. Tests call routes directly with "
             "crafted sessions, including the other-user's-task deletion that must 403. Done when every route "
             "test passes and no route reaches the store before its parse and guard."),
            ("3. The client boundary", "Parse every response; render only narrowed values",
             "Implement client/api.ts with the timeout, the discriminated result and shared-schema parsing of "
             "every response. render.ts consumes only validated Tasks - due is rendered through a null-check "
             "the compiler enforces. Tests mock fetch: a legacy `due` field must produce a schema-failure "
             "result, a hostile `<script>` title must render as text (textContent or your framework's "
             "escaping). Done when both tests pass and `no-explicit-any` is clean."),
            ("4. Failure kinds in the UI", "Make network, schema and HTTP failures visibly different",
             "Branch the UI on the result kind: network failure offers retry, schema failure says 'the server "
             "sent an unexpected shape' (a bug report, not a user error), HTTP failure shows the ApiError "
             "message. Each branch has a test. Done when stopping the server mid-session and serving a "
             "deliberately malformed fixture each produce the correct banner."),
            ("5. The release gate", "One command, wired to CI, that must pass before merge",
             "Add `check: tsc -b && eslint . && vitest run` at the root, configure eslint with "
             "no-floating-promises and no-explicit-any as errors, and add the CI workflow running `npm ci && "
             "npm run check` on push and pull request. Break something on purpose in a branch (rename a "
             "schema field) and confirm CI names the failing package. Done when the gate has caught a "
             "deliberate defect end to end."),
            ("6. Ship it", "Document the contract and the outage-to-gate map",
             "Write the README: the three historical outages, the mechanism preventing each (compile-time "
             "types, runtime parse, server-side guard), how to run check/dev, and the API's status-code "
             "table. Tag v1.0.0 after a green CI run. Done when a teammate can add a new field to the "
             "contract and both sides fail loudly until they update - and the README told them that would "
             "happen."),
        ],
        "resources": [
            ("documentation", "TypeScript Handbook: narrowing and object types", "https://www.typescriptlang.org/docs/handbook/2/narrowing.html",
             "The narrowing mechanics the client relies on when turning parsed JSON into values the compiler trusts."),
            ("documentation", "zod schema-validation library", "https://github.com/colinhacks/zod",
             "The runtime schema library used at both boundaries: parsing, inferred types and error shapes."),
        ],
    },
    # -------------------------------------------------------------------- C
    {
        "slug": "c-sensor-ringlog",
        "title": "Fixed-Capacity Sensor Ring Log with a Validated Binary Format",
        "language": "c",
        "branch": "computer-science",
        "subject": None,
        "difficulty": "advanced",
        "category": "software",
        "est_hours": 32,
        "summary": "Build a memory-bounded C logger for sensor readings: a ring buffer, a documented binary "
                   "file format, loading that validates every field, and a clean bill of health from "
                   "sanitizers - the capstone for the C path.",
        "problem_statement": "A workshop rig samples a temperature probe many times a second. The current "
                             "sketch appends every reading to an ever-growing file until the SD card fills "
                             "and the rig silently stops logging during the interesting part of the "
                             "experiment. A rewrite that loads the file into a malloc'd array crashed twice "
                             "in a week: once on a truncated file after a power cut, once on a file whose "
                             "header claimed more records than the card contained - the allocation math "
                             "wrapped and the loader wrote past a tiny buffer.\n\nThe replacement must run in "
                             "bounded memory no matter how long the rig runs, must write a format another "
                             "program can read, and must refuse - cleanly, with a message - any file that is "
                             "corrupt, truncated or hostile.",
        "objective": "Ship a small C library plus CLI: a fixed-capacity ring buffer of readings (overwrite "
                     "oldest when full), binary dump and load with a documented format and full validation "
                     "of untrusted files, and a test harness that runs clean under AddressSanitizer and "
                     "UBSan. Outcomes the build proves: you manage memory with explicit ownership, you treat "
                     "file contents as hostile input, and you use tooling to catch what the compiler "
                     "permits.",
        "prerequisites": [
            "C path complete: all three stages (pointers, structs, dynamic memory, files, defensive checks)",
            "Comfortable with a Makefile and running a debugger or sanitizer output",
        ],
        "hardware": "Any machine with gcc or clang. Optional: an actual microcontroller to port the ring buffer to later.",
        "software": "gcc or clang with -Wall -Wextra -Werror, GNU make, AddressSanitizer/UBSan, Valgrind (optional second opinion). No external libraries.",
        "architecture": "One module, ringlog.h/ringlog.c, with no global state: a RingLog struct holds a "
                        "fixed-capacity array of Reading (timestamp, value), head and count. The API is "
                        "total - every function returns a status code and never dereferences a NULL or "
                        "out-of-range argument: ringlog_init(log, capacity), ringlog_push(log, reading), "
                        "ringlog_get(log, index), ringlog_dump(log, path), ringlog_load(log, path, max_bytes). "
                        "The file format is documented in FORMAT.md: a magic number, a version byte, a "
                        "record count, then packed fixed-size records. The loader trusts nothing: it checks "
                        "magic and version, compares the declared count against the file's actual size "
                        "before any allocation, bounds the capacity against a compiled maximum, and verifies "
                        "each record's fields after reading. The CLI (main.c) drives record-from-stdin, "
                        "dump, load and report subcommands.",
        "source_code": "Suggested layout:\n\n```\nringlog.h        # struct + API, every function documented with its failure modes\nringlog.c        # the implementation - the only file that touches memory arithmetic\nformat.h         # magic, version, packed record layout, static asserts on sizes\nmain.c           # CLI: record | dump | load | report\ntest_ringlog.c   # a check() harness: ring semantics, overflow wrap, dump/load round-trip\ntest_loader.c    # hostile files: truncated, huge declared count, bad magic, bad version\nMakefile         # all, test, sanitize (ASan+UBSan), valgrind targets\nFORMAT.md        # the byte-level contract another program can implement from\n```\n\nUse `_Static_assert(sizeof(Record) == 12, ...)` (or your layout's real size) so the packed format "
                       "cannot silently change between compilers, and read/write fields explicitly rather "
                       "than dumping raw structs when endianness could ever differ.",
        "database_design": "The binary format is this project's schema, so it gets the same rigor: bytes 0-3 "
                           "magic 'RLOG', byte 4 version (1), bytes 5-8 record count (big-endian uint32), "
                           "then count x 12-byte records (uint32 timestamp, float value, uint32 flags). "
                           "Document invariants: count <= RINGLOG_MAX_RECORDS (a compiled bound, e.g. 65536); "
                           "file size must equal header + count*12 exactly - a larger file is refused as "
                           "unknown trailing data, a smaller one as truncated. Version mismatch is a clean "
                           "refusal with a message, never an attempt to interpret.",
        "testing": "A small check() harness (the pattern from the path's testing module) or a single-header "
                   "framework. Ring semantics: push past capacity overwrites oldest, get() refuses "
                   "out-of-range with a status code, count never exceeds capacity. Round-trip: dump then "
                   "load into a fresh log gives identical readings. Loader hostility, one crafted file per "
                   "case: zero-length, header only, count larger than the file supports, count above the "
                   "compiled maximum (the allocation-wrap attack from the problem statement), bad magic, "
                   "bad version, trailing garbage. Every test target also runs under -fsanitize=address,"
                   "undefined with -Werror, and `make valgrind` is clean. A crash in any hostile-file test "
                   "is a failing grade, not a partial credit.",
        "expected_output": "`make test sanitize` green; the CLI records simulated readings (or a piped CSV), "
                           "dumps to a .rlog file, loads it back and prints a report (min/max/mean, oldest "
                           "and newest timestamps); a hand-corrupted file is refused with a one-line "
                           "diagnostic and exit code, and the process exits 0-or-documented under sanitizers "
                           "with no leaks. FORMAT.md is complete enough that a classmate can write a Python "
                           "reader from it alone - and the demo includes their reader parsing your file.",
        "improvements": [
            "Add a checksum per record and refuse files whose records fail it, distinguishing corruption from hostility.",
            "Port the ring buffer to a microcontroller and log real probe data for a day.",
            "Add a merge subcommand that combines two log files in timestamp order with bounded memory.",
            "Fuzz the loader (e.g. a simple random-mutation loop over a seed file) for ten minutes and fix everything it finds.",
        ],
        "resume_md": "**Sensor Ring Log (C)** | C11, binary formats, ASan/UBSan/Valgrind\n"
                     "- Fixed-capacity ring buffer and a documented binary log format; loader validates magic, "
                     "version, declared counts against actual file size and every record field.\n"
                     "- Hostile-file test suite (truncated, wrapped allocation counts, bad versions) runs clean "
                     "under AddressSanitizer, UBSan and Valgrind with -Werror.",
        "interview_questions": [
            "A file's header claims 4 billion records. Walk through your loader's next three decisions, in order.",
            "Why does the format document byte order and padding instead of writing the struct with fwrite?",
            "When the ring is full, which reading does push() overwrite, and how do head and count stay consistent?",
            "Name two bugs sanitizers catch that -Wall does not, and one bug neither catches.",
        ],
        "tech": ["C11", "GCC/Clang sanitizers", "GNU make", "Valgrind"],
        "skills": ["bounded memory design", "binary format design", "hostile input validation", "ownership discipline", "sanitizer-driven testing"],
        "steps": [
            ("1. The ring, in bounds", "Implement RingLog with push/get and a test harness",
             "Write ringlog.h with the struct and status-code API, then ringlog.c: init validates capacity "
             "(0 < capacity <= compiled max), push overwrites oldest when full, get refuses out-of-range. "
             "Build test_ringlog.c with a check() macro covering wrap-around, capacity edges and NULL "
             "arguments. Done when `make test` passes with -Wall -Wextra -Werror."),
            ("2. The format contract", "Design, document and static-assert the binary layout",
             "Write FORMAT.md first: magic, version, count, record layout with byte offsets and endianness. "
             "Implement format.h with packed accessors (explicit byte assembly, not raw struct I/O) and "
             "_Static_assert on sizes. Round-trip a single record to bytes and back in a test. Done when the "
             "document and the code agree byte for byte and a test proves it."),
            ("3. Dump", "Write ringlog_dump with checked I/O at every step",
             "Implement dump: fopen checked, every fwrite's return compared against the requested count, "
             "fclose's status checked (flush errors surface there), temp-file-plus-rename for crash safety. "
             "Tests cover a full ring, an empty ring and an unwritable path (each a clean status code). Done "
             "when a kill -9 mid-dump can never leave a half-written .rlog that a later load accepts."),
            ("4. The hostile loader", "Implement ringlog_load that trusts no byte of the file",
             "Load checks in order: file opens; size >= header; magic; version; declared count <= compiled "
             "max; header + count*record == actual size exactly; then reads records with per-record field "
             "validation. No allocation is computed from the file's count before the size check passes. "
             "Write test_loader.c crafting each refusal case, including the allocation-wrap file from the "
             "problem statement. Done when every crafted file produces a documented status code and message, "
             "never a crash."),
            ("5. Sanitizers and the CLI", "Prove cleanliness and make the tool usable",
             "Add Makefile targets: sanitize (ASan+UBSan test run) and valgrind. Fix everything they report, "
             "including leaks on error paths - the loader's early refusals must free nothing they have not "
             "allocated. Build main.c: record (read CSV from stdin), dump, load, report (min/max/mean). Done "
             "when both sanitizer and Valgrind runs are clean and the CLI demo works end to end."),
            ("6. Ship it", "Hand over a format someone else can implement",
             "Polish FORMAT.md, add an README with build/test/demo commands, and have a classmate write a "
             "reader in Python from the document alone; fix whatever their reader exposes. Tag v1.0.0. Done "
             "when their reader parses your dump file byte-for-byte correctly and `make test sanitize "
             "valgrind` is green on a fresh clone."),
        ],
        "resources": [
            ("documentation", "Beej's Guide to C", "https://beej.us/guide/bgc/html/single/bgc.html",
             "A practical free C reference covering the file I/O, struct and pointer mechanics this project runs on."),
            ("documentation", "Valgrind quick start", "https://valgrind.org/docs/manual/quick-start.html",
             "The second-opinion memory checker: how to run it and how to read its leak and invalid-access reports."),
        ],
    },
    # ------------------------------------------------------------------- C++
    {
        "slug": "cpp-text-index-cli",
        "title": "RAII Text-Index CLI: Build, Query and Test a Positional Search Tool",
        "language": "cpp",
        "branch": "computer-science",
        "subject": None,
        "difficulty": "advanced",
        "category": "software",
        "est_hours": 34,
        "summary": "Build a grep-like CLI in modern C++: a positional index over text files with RAII "
                   "resource handling, safe parsing of untrusted input, phrase and AND queries, and a test "
                   "suite driven by CMake/CTest - the capstone for the C++ path.",
        "problem_statement": "A research group keeps thousands of small text logs and wants to find where a "
                             "phrase appears across them, with file and line numbers. `grep -r` answers the "
                             "simple case but not the ones they actually ask: 'papers containing both "
                             "\"phase transition\" AND \"hysteresis\", ranked by proximity', run repeatedly "
                             "over an unchanging corpus where rescanning every file each time is wasteful.\n\n"
                             "A student's first prototype did exactly that - rescanned everything per query - "
                             "and leaked file handles on every error path because raw FILE* pointers were "
                             "closed by hand at the bottom of long functions that returned early in the "
                             "middle. The rebuild should index once, query many times, and let resource "
                             "lifetimes be structural rather than a matter of remembering.",
        "objective": "Ship a CLI (`tindex build <dir>`, `tindex query <terms...>`, `tindex phrase \"exact "
                     "words\"`) that builds a positional index (term -> sorted (doc, position) postings) from "
                     "a directory of text files, persists it to a binary file it can reload safely, and "
                     "answers AND/phrase queries with file:line output. All resources are RAII-managed; "
                     "untrusted inputs (file contents, index files, CLI arguments) are parsed with bounds "
                     "checks; CTest runs a suite covering tokenization, query logic and hostile index files. "
                     "Outcomes the build proves: you can design with value semantics and ownership, parse "
                     "without undefined behaviour, and structure a multi-file C++ project with a real build.",
        "prerequisites": [
            "C++ path complete: all three stages (vectors/maps, RAII, smart pointers, multi-file builds, safe parsing)",
            "A compiler with C++20 support and CMake installed",
        ],
        "hardware": "Any machine with a C++20 compiler (gcc 11+, clang 14+, MSVC 2022).",
        "software": "CMake 3.20+, a C++20 compiler, CTest. No third-party libraries - the standard library is the point.",
        "architecture": "Library plus CLI. `Tokenizer` turns a string_view into lowercase terms with "
                        "positions (pure, unit-testable). `Index` holds `std::unordered_map<std::string, "
                        "std::vector<Posting>>` where Posting is {docId, position}, plus a document table "
                        "(id -> path); postings are kept sorted so AND-intersection and phrase-adjacency are "
                        "linear merges. `IndexFile` handles persistence: a documented binary format written "
                        "through an RAII stream wrapper, and a loader that validates every count and offset "
                        "before use - the same hostility the C capstone demands, expressed with std::optional "
                        "and exceptions-as-errors at the boundary. The CLI (`main.cpp`) uses std::expected-"
                        "style status returns internally and translates failures to exit codes and one-line "
                        "messages; nothing crosses the C-style boundary except main's exit code. File handles "
                        "are std::ifstream (RAII); heap ownership is by value or std::unique_ptr; raw "
                        "new/delete appear nowhere.",
        "source_code": "Suggested layout:\n\n```\ninclude/tindex/tokenizer.hpp, index.hpp, index_file.hpp, query.hpp\nsrc/tokenizer.cpp, index.cpp, index_file.cpp, query.cpp, main.cpp\ntests/test_tokenizer.cpp, test_index.cpp, test_query.cpp, test_index_file.cpp\nCMakeLists.txt          # library target, CLI target, CTest registration\nFORMAT.md               # the binary index format\n```\n\nHeaders declare, exactly one .cpp defines (the one-definition discipline from the path). CMake "
                       "registers each test file with CTest and adds a `sanitize` preset "
                       "(-fsanitize=address,undefined) that CI and `ctest` can run. Code review rule: a grep "
                       "for `new ` and `delete ` finds nothing outside comments.",
        "database_design": "The index file is the schema: magic 'TIDX', version, docCount, termCount, then a "
                           "document table (length-prefixed paths) and per-term postings (term string, "
                           "posting count, count x {uint32 docId, uint32 position}). All counts are "
                           "length-prefixed with explicit bounds: the loader checks each declared count "
                           "against the remaining bytes before allocating a vector, uses `resize` with "
                           "validated sizes (or reserve+emplace in a checked loop), and refuses trailing "
                           "data. Strings are UTF-8 bytes with lengths - never NUL-terminated guesses.",
        "testing": "CTest suites. Tokenizer: case folding, punctuation splits, position accuracy, empty "
                   "input. Index/query: single-term lookup, AND intersection (including disjoint terms), "
                   "phrase adjacency (positions differ by exactly one, same doc), duplicate documents, a "
                   "document with one very long line (positions beyond 65535 still work - uint32). "
                   "IndexFile: round-trip equality; hostile files - truncated header, termCount larger than "
                   "the file can support, a posting count that would exceed remaining bytes, bad magic, bad "
                   "version - each refused with an error, none crashing. Everything also runs under the "
                   "sanitize preset. A performance sanity test indexes a generated 1k-file corpus in bounded "
                   "time so an accidental O(n^2) merge fails the suite.",
        "expected_output": "`cmake --preset sanitize && ctest` green; `tindex build ./corpus` writes "
                           "corpus.tidx; `tindex query phase transition` lists file:line hits; `tindex "
                           "phrase \"phase transition\"` lists only adjacent matches; a corrupted .tidx is "
                           "refused with one diagnostic line and a non-zero exit; no raw new/delete in the "
                           "source; the README shows the workflow and the format doc lets a classmate write "
                           "a reader in another language.",
        "improvements": [
            "Add proximity ranking (score by minimum gap between AND-ed terms) and a --json output mode.",
            "Incremental builds: detect unchanged files by size+mtime and merge their old postings.",
            "Parallelize the build with std::async over files, keeping the merge single-threaded and deterministic.",
            "Memory-map the index for queries (with the same validation) and measure the difference.",
        ],
        "resume_md": "**Text Index CLI (C++20)** | CMake/CTest, RAII, sanitizers\n"
                     "- Positional index with AND/phrase queries over large corpora; binary index format with a "
                     "loader that validates every declared count against actual bytes.\n"
                     "- Zero raw new/delete: ifstream and value/unique_ptr ownership throughout; full CTest "
                     "suite including hostile-index cases, green under ASan/UBSan.",
        "interview_questions": [
            "Where does an exception leave a partially built Index in your code, and why is the object still safe to destroy?",
            "A postings vector holds 10M entries. When does push_back invalidate iterators, and where in your query loop did you have to respect that?",
            "Your loader sees termCount = 2^32 - 1 in a 40-byte file. Trace the exact checks that refuse it before any allocation.",
            "Why do phrase queries need positions in the posting rather than just doc ids, and how does the adjacency merge stay linear?",
        ],
        "tech": ["C++20", "CMake", "CTest", "AddressSanitizer/UBSan"],
        "skills": ["RAII and ownership", "STL data structures", "binary format validation", "multi-file build hygiene", "linear merge algorithms"],
        "steps": [
            ("1. Tokenizer, purely", "Turn text into positioned terms and test it exhaustively",
             "Implement Tokenizer over std::string_view: lowercase, split on non-alphanumerics, emit (term, "
             "position). No I/O, no state. CTest suite covers folding, punctuation, unicode bytes passing "
             "through safely, empty input. Done when the suite is green under the sanitize preset."),
            ("2. Index in memory", "Build the postings map and the document table",
             "Index::addDocument(path, contents) tokenizes and appends sorted postings; keep postings sorted "
             "by (docId, position) as you insert or sort once at seal(). Handle duplicate paths (re-index "
             "replaces the docId's postings). Tests build a tiny corpus in tmp and assert exact posting "
             "lists. Done when positions are exactly right for a hand-checked three-file corpus."),
            ("3. Queries", "AND intersection and phrase adjacency as linear merges",
             "query(terms) intersects sorted posting lists by docId; phrase(terms) additionally requires "
             "consecutive positions within one doc. Return file:line by mapping position -> line via the "
             "stored document text or a line-offset table built at index time. Tests cover disjoint terms, "
             "phrases spanning lines (refused or documented), and a 1M-position doc. Done when the "
             "performance sanity test stays inside its bound."),
            ("4. Persistence, written", "Design FORMAT.md, then write the index through RAII streams",
             "Document the byte layout first. Implement save() with std::ofstream (RAII - no manual close "
             "dances), length-prefixed strings, explicit little-endian byte assembly, and a check of the "
             "stream state after every write. Round-trip test: save, load into a fresh Index, compare "
             "postings for equality. Done when the round-trip is byte-stable across two runs."),
            ("5. Persistence, hostile", "Make the loader refuse everything it cannot prove",
             "Implement load(): magic, version, then each count validated against remaining file size before "
             "any vector allocation; refuse trailing bytes; report one-line diagnostics via std::optional / "
             "status returns - no exception escapes the CLI boundary. Craft each hostile file in tests "
             "(truncated, inflated counts, bad magic/version). Done when every crafted file is refused "
             "cleanly under sanitizers."),
            ("6. Ship it", "CLI polish, presets and handover",
             "Finish main.cpp subcommands with usage text and exit codes (0 ok, 1 usage, 2 runtime, 3 bad "
             "input file). Add CMake presets (default, sanitize), a CI-friendly ctest invocation, and the "
             "README workflow demo. Grep the tree for `new `/`delete ` and remove any hits. Tag v1.0.0. Done "
             "when a fresh clone builds, tests green under both presets, and the demo reproduces the README "
             "output exactly."),
        ],
        "resources": [
            ("documentation", "cppreference: RAII", "https://en.cppreference.com/w/cpp/language/raii.html",
             "The reference page for the idiom the whole project is organized around, with the standard-library types that implement it."),
            ("documentation", "An Introduction to Modern CMake", "https://cliutils.gitlab.io/modern-cmake/",
             "Target-based CMake: library/CLI targets, CTest registration and the sanitizer preset pattern."),
        ],
    },
    # -------------------------------------------------------------------- Go
    {
        "slug": "go-healthcheck-service",
        "title": "Concurrent URL Health-Check Service with Contexts and Bounded Workers",
        "language": "go",
        "branch": "computer-science",
        "subject": None,
        "difficulty": "advanced",
        "category": "software",
        "est_hours": 32,
        "summary": "Build a Go service that periodically checks a list of URLs with a bounded worker pool, "
                   "per-check timeouts via context, SQL-persisted history and a JSON API - then shuts down "
                   "gracefully on signal - the capstone for the Go path.",
        "problem_statement": "A student society runs six small services (site, wiki, ticketing, two event "
                             "pages, a status page) and finds out they are down when members complain. A "
                             "first fix - a cron script that curls each URL in sequence with no timeout - "
                             "hung for twenty minutes on one stalled server, so the checks after it never "
                             "ran that hour. A second attempt fired one goroutine per URL per minute with no "
                             "limit; when someone pasted a 4,000-URL list into the config, the machine ran "
                             "out of file descriptors and the script died mid-check, corrupting its CSV "
                             "output.\n\nThe replacement must check concurrently but within explicit limits, "
                             "give up on any single check after a deadline, keep history that survives "
                             "restarts, and stop cleanly when the host reboots.",
        "objective": "Ship a Go service: it reads a bounded list of targets, runs checks on an interval "
                     "through a fixed worker pool with per-check contexts (timeout and cancellation), records "
                     "each result (status, latency, error class) in SQL via parameterized queries, serves a "
                     "small JSON API for current status and recent history, and performs a graceful shutdown "
                     "on SIGTERM/SIGINT. A table-driven test suite plus `-race` runs cover the pool, the "
                     "timeout behaviour (against a local test server that stalls) and the API. Outcomes the "
                     "build proves: you can bound concurrency deliberately, propagate cancellation, persist "
                     "safely, and operate a service's lifecycle.",
        "prerequisites": [
            "Go path: Foundations and Working Practice stages complete (error values, packages/tests, HTTP, database/sql)",
            "Go path: Advanced Engineering modules on contexts, bounded concurrency and shutdown",
        ],
        "hardware": "Any machine with Go 1.22+. The service checks URLs, so it needs outbound network in production; tests use a local httptest server instead.",
        "software": "Go 1.22+, modernc.org/sqlite (pure-Go driver, no cgo) or a Postgres you already run, net/http, database/sql, the standard testing package.",
        "architecture": "Four pieces behind interfaces so each is testable alone. `Checker` performs one HTTP "
                        "GET with the request bound to a context (http.NewRequestWithContext) and returns a "
                        "typed result: status code, latency, error class (timeout, dns, connect, tls, other) "
                        "- never a raw error string as the classification. `Pool` runs N workers reading "
                        "targets from a channel; the scheduler feeds one round of targets per interval and "
                        "the round has an overall deadline, so a slow round cannot pile onto the next. "
                        "`Store` persists results with parameterized INSERTs and serves history queries. "
                        "`API` exposes GET /status (latest per target) and GET /history?target=...&limit=... "
                        "with bound limits. main wires them, installs signal.NotifyContext, and on cancel: "
                        "stops the scheduler, waits for in-flight checks up to the shutdown timeout "
                        "(pool.Wait with a context), closes the HTTP server (Server.Shutdown) and the "
                        "database, in that order.",
        "source_code": "Suggested layout:\n\n```\ncmd/healthd/main.go        # wiring, signals, shutdown order\ninternal/checker/checker.go    # one bounded HTTP check -> typed Result\ninternal/pool/pool.go          # fixed workers, jobs channel, WaitGroup\ninternal/scheduler/scheduler.go# interval rounds with an overall deadline\ninternal/store/store.go        # database/sql, prepared statements, migrations\ninternal/api/api.go            # JSON handlers with bounded query params\neach package: *_test.go, table-driven\nconfig.example.json            # targets, interval, pool size, per-check timeout, max targets\n```\n\nConfiguration is validated at startup: pool size 1..64, per-check timeout 1..30s, interval >= "
                       "timeout, target list bounded (e.g. <= 512) - a config beyond a bound fails fast with "
                       "a message naming the bound. Every function that can fail returns an error; nothing "
                       "is assigned to _ outside tests that say why.",
        "database_design": "`checks(id INTEGER PRIMARY KEY AUTOINCREMENT, target TEXT NOT NULL, checked_at "
                           "INTEGER NOT NULL, status INTEGER, latency_ms INTEGER, error_class TEXT)` with an "
                           "index on (target, checked_at DESC) so the history query is a bounded index scan. "
                           "All writes and reads bind parameters (`?` placeholders); target strings never "
                           "enter SQL text. A retention job (or a DELETE with a bound) keeps the table from "
                           "growing forever - the same unbounded-growth mistake the CSV version made, "
                           "addressed in the schema's operating plan.",
        "testing": "Table-driven tests per package. Checker: against httptest servers - 200 fast, 500, a "
                   "handler that sleeps longer than the check timeout (must classify as timeout, and the "
                   "test proves the check returned before the handler finished), an unroutable address "
                   "(connect error class). Pool: N workers process M jobs with max concurrency observed <= N "
                   "(an atomic counter in the test), and cancelling the round context stops workers promptly. "
                   "Store: round-trip a result, history respects limit and ordering, a target containing `'; "
                   "DROP TABLE checks;--` persists as inert text. API: status and history shapes, limit "
                   "clamped to the documented maximum, 404 for unknown targets. The whole suite runs under "
                   "`go test -race ./...` in CI.",
        "expected_output": "One binary: `healthd -config config.json` checks the society's six URLs every "
                           "minute with a four-worker pool and a five-second per-check deadline; `curl "
                           "localhost:8080/status` answers with the latest state per target; a stalled "
                           "target shows error_class 'timeout' five seconds later while the other checks "
                           "continue; `kill -TERM` drains in-flight checks and exits 0 within the shutdown "
                           "timeout; `go test -race ./...` is green; the README documents every config "
                           "bound and the shutdown order.",
        "improvements": [
            "Add alerting: a target down for K consecutive rounds posts to a webhook - with the webhook call itself bounded and classified like any check.",
            "Expose Prometheus metrics (round duration, pool saturation, error classes) and a /healthz for the service itself.",
            "Persist to Postgres and compare query plans for the history endpoint at 1M rows.",
            "Add per-target retry-with-backoff inside the round deadline and measure how it changes latency percentiles.",
        ],
        "resume_md": "**URL Health-Check Service** | Go, database/sql, contexts\n"
                     "- Bounded worker pool with per-check and per-round contexts: a stalled target times out "
                     "in seconds while other checks proceed; concurrency cap proven by a race-detector test.\n"
                     "- Parameterized SQL history with retention bounds, JSON API with clamped limits, and "
                     "signal-driven graceful shutdown with a documented close order.",
        "interview_questions": [
            "A check's context deadline fires while the HTTP round trip is in flight. What exactly happens to the goroutine, the connection and the result row?",
            "Why does the scheduler give each round an overall deadline in addition to per-check timeouts?",
            "How does your pool test prove concurrency never exceeded N, and why does it need -race to mean anything?",
            "SIGTERM arrives mid-round. List the shutdown steps in order and what bounds each one.",
        ],
        "tech": ["Go 1.22", "net/http", "database/sql", "modernc.org/sqlite", "httptest"],
        "skills": ["bounded concurrency", "context propagation", "graceful shutdown", "parameterized SQL", "table-driven testing with -race"],
        "steps": [
            ("1. One honest check", "Implement Checker against local test servers",
             "Write the Checker: build the request with http.NewRequestWithContext, a client with the "
             "context-bound timeout, classify the outcome into the typed Result (status, latency, error "
             "class). Table-driven tests against httptest: fast 200, 500, a stalling handler that must "
             "produce 'timeout' before it finishes, a bad address. Done when `go test -race ./internal/"
             "checker` is green and no error is discarded."),
            ("2. The bounded pool", "Run checks through N workers reading a jobs channel",
             "Implement Pool: New(size), Submit(targets) feeding a channel, Wait() on a WaitGroup, and a "
             "round context that cancels everything on deadline. The concurrency-cap test uses an atomic "
             "counter inside fake jobs. Done when the cap test passes under -race and cancelling mid-round "
             "returns promptly (assert the elapsed time)."),
            ("3. Persistence", "Store results with database/sql and prepared statements",
             "Add the schema migration, Insert(result) and History(target, limit) with `?` placeholders and "
             "a clamped limit. Tests: round-trip, ordering by checked_at DESC, limit enforcement, and the "
             "hostile target string persisting inert. Done when the store tests pass against a temp-file "
             "SQLite database."),
            ("4. The API", "Serve /status and /history with bounded parameters",
             "Handlers read from the Store: latest-per-target for /status (one query with a window function "
             "or a bounded loop), clamped limit for /history, 404 for unknown targets, JSON errors with no "
             "internals. Configure http.Server timeouts (read header, read, write). Tests use httptest "
             "around the handler and assert shapes and clamping. Done when the API tests pass and the "
             "server refuses a slow-loris style request within the configured timeout."),
            ("5. Scheduler and signals", "Run rounds on an interval; shut down gracefully",
             "The scheduler ticks per interval, skips a round if the previous one is still running (document "
             "the policy), and applies the round deadline. main installs signal.NotifyContext and on cancel "
             "executes the shutdown order: stop scheduling -> pool.Wait with timeout -> Server.Shutdown -> "
             "store.Close, logging each step. A test drives one round against a local server, sends the "
             "cancel and asserts exit within the bound. Done when the shutdown test passes and config "
             "validation rejects out-of-bound values at startup with named limits."),
            ("6. Ship it", "Operate it for a day and hand it over",
             "Run the service against your own six real URLs for a day; keep the log and fix what it exposes "
             "(a flaky DNS classified wrong, a retention DELETE you forgot). Write the README: config "
             "reference with every bound, the shutdown order, the error-class taxonomy, and how to read "
             "/status. Tag v1.0.0. Done when the day-long run needed no manual intervention and `go vet "
             "./... && go test -race ./...` is green on a fresh clone."),
        ],
        "resources": [
            ("documentation", "Go tutorial: accessing a relational database", "https://go.dev/doc/tutorial/database-access",
             "The official database/sql walkthrough: connecting, parameterized queries and the transaction patterns the store uses."),
            ("documentation", "Go package context", "https://pkg.go.dev/context",
             "The canonical docs for deadlines and cancellation - the package every bounded operation in this project threads through."),
        ],
    },
    # ----------------------------------------------------------------- Rust
    {
        "slug": "rust-logscan-cli",
        "title": "Ownership-Safe Log Scanner CLI with Typed Errors and a Full Test Suite",
        "language": "rust",
        "branch": "computer-science",
        "subject": None,
        "difficulty": "advanced",
        "category": "software",
        "est_hours": 30,
        "summary": "Build a Rust CLI that scans application logs for error patterns and prints aggregates, "
                   "with typed errors instead of panics, iterator-based parsing, and cargo test/clippy/fmt "
                   "as the release gate - the capstone for the Rust path.",
        "problem_statement": "After an overnight incident, an on-call student faces 2 GB of interleaved "
                             "application logs and needs three answers fast: which error messages appeared, "
                             "how often, and when the first and last occurrence of each was. `grep | sort | "
                             "uniq -c` gets counts but loses time order, mangles multi-line stack traces and "
                             "gives no per-hour picture.\n\nTheir first Rust attempt panicked on the first "
                             "malformed line - a truncated UTF-8 sequence from a killed writer - taking the "
                             "whole scan down forty minutes into an incident. A tool used during incidents "
                             "must be the most boring program in the room: it reports what it finds, says "
                             "what it could not parse, and never crashes.",
        "objective": "Ship `logscan`: given one or more log files, parse timestamped lines (with a documented "
                     "expected format), classify lines matching error patterns, aggregate counts per pattern "
                     "with first/last timestamps and a per-hour histogram, and print a report (text or "
                     "--json). Malformed lines are counted and reported, never fatal; unreadable files "
                     "produce typed errors with context; no unwrap() outside tests. cargo fmt, clippy "
                     "(-D warnings) and cargo test form the release gate. Outcomes the build proves: you can "
                     "model failures as values, use iterators and ownership deliberately on real data, and "
                     "hold a Rust project to its standard toolchain.",
        "prerequisites": [
            "Rust path: Foundations and Working Practice stages complete (ownership, Result/? , iterators, modules, cargo test)",
            "Rust path: Advanced Engineering modules on boundary parsing and typed error design",
        ],
        "hardware": "Any machine with the stable Rust toolchain.",
        "software": "Rust stable (rustup), cargo, cargo-clippy, rustfmt. No required external crates - std only is the point; optionally clap for argument parsing as a stretch.",
        "architecture": "A binary crate with library-style modules so everything is testable: `format` "
                        "defines the expected line grammar (ISO-8601 timestamp, level, message) and a "
                        "total parse function returning Result<ParsedLine, LineError> - malformed lines are "
                        "values, not exceptions to the program's existence. `scan` owns the I/O: it reads "
                        "files line-by-line with BufReader::lines (lossy handling of invalid UTF-8 is "
                        "explicit: read bytes and use String::from_utf8_lossy so a truncated sequence "
                        "becomes a replacement character and a counted malformed line, never a crash), "
                        "chains iterator adaptors to filter and map, and folds into an `Report` struct "
                        "(counts, first/last per pattern, hourly buckets). `patterns` holds the default "
                        "error patterns plus user-supplied ones from --pattern (validated: non-empty, "
                        "bounded count and length). `cli` translates a typed top-level Error enum - "
                        "Io{path, source}, NoInputs, BadPattern{reason} - into exit codes and one-line "
                        "messages. No panics: unwrap/expect appear only in #[cfg(test)] code.",
        "source_code": "Suggested layout:\n\n```\nsrc/main.rs        # thin: parse args, call run(), map Error -> exit code\nsrc/lib.rs         # pub fn run(...) -> Result<Report, Error>\nsrc/format.rs      # ParsedLine, LineError, the total line parser\nsrc/scan.rs        # file walking, lossy decoding, iterator pipeline, Report fold\nsrc/patterns.rs    # defaults + validation of user patterns\nsrc/report.rs      # text and JSON rendering of Report\ntests/             # integration tests: fixtures incl. malformed-line and multi-file cases\nbenches/           # optional: throughput on a generated 100 MB log\n```\n\nUnit tests live beside the code under #[cfg(test)]; integration tests in tests/ exercise the public "
                       "API only - the split from the path's testing module. `cargo clippy -- -D warnings` "
                       "and `cargo fmt --check` run in CI on every push.",
        "database_design": "No database; the report is the schema. Define it explicitly: `Report { total_lines: "
                           "u64, malformed: u64, files: Vec<FileSummary>, patterns: Vec<PatternSummary> }` "
                           "with PatternSummary { pattern, count, first_seen, last_seen, hourly: [u64; 24] } "
                           "and a documented JSON shape (serde-free: hand-write the JSON with proper "
                           "string escaping, or add serde_json as the one allowed dependency and justify "
                           "it). The JSON output is part of the contract - a test pins its shape so a "
                           "refactor cannot silently rename fields.",
        "testing": "Unit tests: the line parser accepts the documented format and rejects (as values) an "
                   "empty line, a missing timestamp, a wrong-level string, and a line with invalid UTF-8 "
                   "bytes (constructed with a byte vector, decoded lossily, counted malformed). Pattern "
                   "validation: empty pattern refused, 1,000 patterns refused, a 10 KB pattern refused. "
                   "Integration tests over fixture files: a mixed log produces the exact expected Report "
                   "(counts, first/last, hourly buckets - pin a golden JSON); two files merge correctly; a "
                   "missing file yields Error::Io naming the path with exit code 2; a directory as input is "
                   "refused clearly. A generated-large-file test proves streaming: memory stays flat (the "
                   "process never holds the whole file) while a 100 MB scan completes in bounded time.",
        "expected_output": "`cargo install --path .` gives a logscan binary; scanning the incident log "
                           "prints the pattern table with first/last timestamps and the hourly histogram; "
                           "--json emits the pinned shape; a file with truncated UTF-8 scans to completion "
                           "with the malformed count reported; a missing file prints `logscan: cannot read "
                           "<path>: <reason>` and exits 2; `cargo fmt --check && cargo clippy -- -D warnings "
                           "&& cargo test` is the green release gate; grep finds no unwrap() outside tests.",
        "improvements": [
            "Add multi-line stack-trace grouping: continuation lines attach to the previous event.",
            "Stream from stdin (`-`) so it composes in pipelines: `journalctl -u app | logscan -`.",
            "Parallelize across files with rayon (the one added dependency) and measure the speedup honestly.",
            "Add a --since/--until window filter and a diff mode comparing two reports.",
        ],
        "resume_md": "**Log Scanner CLI (Rust)** | Rust stable, iterators, typed errors\n"
                     "- Incident-grade log aggregator: streaming parse of multi-GB files with flat memory, "
                     "lossy UTF-8 decoding and malformed lines reported as values - zero panics, no unwrap "
                     "outside tests.\n"
                     "- Typed error enum mapped to exit codes; golden-JSON report contract pinned by "
                     "integration tests; fmt/clippy -D warnings/test gate in CI.",
        "interview_questions": [
            "A log line contains a truncated UTF-8 sequence. Trace exactly what your scanner does, and why reading bytes instead of str is what makes that possible.",
            "Why is a malformed line a LineError value rather than a Result that aborts the scan, and where does the distinction show up in the Report?",
            "Your iterator pipeline is lazy until the fold. Which adaptor chain builds it, and what would happen if you forgot the consuming step?",
            "The tool must never crash during an incident. What does the codebase forbid to make that claim checkable, and how does CI enforce the ban?",
        ],
        "tech": ["Rust stable", "cargo", "clippy", "rustfmt"],
        "skills": ["ownership and borrowing in practice", "iterator pipelines", "typed error design", "lossy decoding at boundaries", "golden-file testing"],
        "steps": [
            ("1. The line contract", "Define the format and write the total parser with tests",
             "Document the expected line grammar in the crate docs, then implement format.rs: parse returns "
             "Result<ParsedLine, LineError> covering every rejection as a value. Unit tests first for "
             "accepts/rejects including edge timestamps. Done when `cargo test` covers each LineError "
             "variant and clippy is clean."),
            ("2. Lossy scanning", "Read files as bytes, decode lossily, fold into a Report",
             "Implement scan.rs over BufReader bytes: from_utf8_lossy per line, malformed count, iterator "
             "adaptors filtering pattern matches, and a fold building Report (counts, first/last, hourly). "
             "A test constructs a file with invalid UTF-8 bytes and asserts the scan completes with "
             "malformed == 1. Done when no code path can panic on any byte sequence."),
            ("3. Patterns and validation", "Defaults plus bounded user patterns",
             "Implement patterns.rs: sensible defaults (ERROR, FATAL, panic, exception), and validation of "
             "--pattern inputs (non-empty, <= 64 patterns, <= 512 bytes each) returning BadPattern errors. "
             "Tests pin every bound. Done when an empty pattern and a 10 KB pattern are refused with named "
             "limits, not silently accepted."),
            ("4. Errors to exit codes", "The typed Error enum and a thin main",
             "Define Error { Io{path, source}, NoInputs, BadPattern{..} } with Display messages that name "
             "the path or the bound; main maps each to an exit code (2 I/O, 3 usage, 4 pattern) and prints "
             "one line - no Debug dumps, no stack traces. Integration tests assert code and message per "
             "failure. Done when `grep -rn 'unwrap()' src/` shows only test-gated hits."),
            ("5. The report contract", "Text and JSON output pinned by a golden test",
             "Implement report.rs: a human table and --json with exact field names. Write the golden JSON "
             "fixture test over a mixed log (correct lines, malformed lines, two patterns, known hours) so "
             "any rename or reordering fails CI. Add the streaming test: a generated 100 MB file scans with "
             "flat memory in bounded time. Done when both goldens pass and the large-file test documents "
             "its bound."),
            ("6. Ship it", "CI gate, docs and handover",
             "Add CI running fmt --check, clippy -D warnings and cargo test on push; write the README (the "
             "incident story, usage, exit-code table, format grammar) and `cargo doc` clean crate docs. Tag "
             "v1.0.0. Done when a classmate installs from the repo, scans a log you hand them including a "
             "corrupted one, and every behaviour they see is documented."),
        ],
        "resources": [
            ("documentation", "The Rust Book: error handling", "https://doc.rust-lang.org/book/ch09-00-error-handling.html",
             "The canonical chapters on Result, ? and when panicking is (and is not) acceptable - the design basis for the typed error enum."),
            ("documentation", "The Cargo Book", "https://doc.rust-lang.org/cargo/",
             "Workspaces, tests, benches and the publish/CI workflows the release gate is built from."),
        ],
    },
    # ------------------------------------------------------------------ SQL
    {
        "slug": "sql-ops-reporting-db",
        "title": "Operations Reporting Database: Schema, Window-Function Reports and Query Tests",
        "language": "sql",
        "branch": "computer-science",
        "subject": None,
        "difficulty": "intermediate",
        "category": "software",
        "est_hours": 26,
        "summary": "Turn a support team's ticket dump into a reporting database: a normalized schema with "
                   "real constraints, seeded data, window-function reports, an index-and-EXPLAIN performance "
                   "pass, and a test script that pins every report's expected output - the capstone for the "
                   "SQL path.",
        "problem_statement": "A support team exports tickets to a spreadsheet every Monday and builds the "
                             "weekly report by hand: first-response times, backlog age, agent load. It "
                             "takes two hours, the pivot tables break whenever a column is renamed, 'average "
                             "first response' silently ignores tickets that were never answered (they have "
                             "no response timestamp, and the spreadsheet average skips blanks), and nobody "
                             "can reproduce last month's numbers because the sheet was edited in place.\n\n"
                             "The team needs the report to be a database with a schema that rejects bad "
                             "data on the way in, queries that answer the real questions (including the "
                             "never-answered tickets), and numbers that are reproducible to the byte.",
        "objective": "Ship a SQLite (or PostgreSQL) project: `schema.sql` with a normalized tickets model "
                     "and enforcing constraints, `seed.sql` (or a generator) with a realistic fixture, a "
                     "library of report queries - weekly volume, first-response distribution that counts "
                     "never-answered tickets explicitly, backlog age buckets, per-agent load with window "
                     "functions (ROW_NUMBER, moving averages) - and `verify.sql` plus a runner script that "
                     "asserts each report against pinned expected outputs. An index-and-EXPLAIN pass "
                     "documents why each index exists. Outcomes the build proves: you can design a schema "
                     "whose constraints make whole bug classes impossible, write analytical SQL including "
                     "window functions, and treat query results as a tested contract.",
        "prerequisites": [
            "SQL path complete: all three stages (joins, aggregates, NULL semantics, indexes, transactions)",
            "Comfortable running sqlite3 (or psql) from a terminal and reading EXPLAIN output",
        ],
        "hardware": "Any machine with sqlite3 installed (or a PostgreSQL server you already run).",
        "software": "SQLite 3.40+ (window functions and STRICT tables) or PostgreSQL 14+; a shell or Python runner for the verification step; Git.",
        "architecture": "Files, in load order: `schema.sql` (tables, constraints, indexes - idempotent with "
                        "IF NOT EXISTS), `seed.sql` (deterministic fixture: fixed ids and timestamps so "
                        "reports have pinned answers), `reports/*.sql` (one file per report, each a single "
                        "SELECT with a comment stating the question it answers), `verify.sql` (each report "
                        "wrapped in an assertion: computed value compared against the expected literal, "
                        "raising on mismatch), and `run.sh` (build a fresh temp database, load, run every "
                        "report, run verify, print a summary). The schema is the contract: CHECK constraints "
                        "and foreign keys make invalid states unrepresentable, so reports never need to "
                        "defend against them. Every report query is parameter-free and deterministic - no "
                        "CURRENT_DATE - taking 'as of' dates as literals the runner supplies, so the same "
                        "inputs always produce the same outputs.",
        "source_code": "Suggested layout:\n\n```\nschema.sql          # agents, tickets, ticket_events + constraints + indexes\nseed.sql            # ~200 deterministic rows incl. edge cases named in comments\nreports/weekly_volume.sql, first_response.sql, backlog_age.sql, agent_load.sql\nverify.sql          # pinned assertions per report\nrun.sh              # fresh DB -> schema -> seed -> reports -> verify\nNOTES.md            # the question each report answers + the EXPLAIN findings\n```\n\nWith SQLite, enable the guards the schema depends on: `PRAGMA foreign_keys = ON;` at the top of "
                       "every session (it is per-connection!), and consider STRICT tables so type affinity "
                       "cannot quietly coerce. With PostgreSQL, the equivalents are on by default - document "
                       "which engine the project targets and keep the SQL to the common dialect where "
                       "possible.",
        "database_design": "`agents(id INTEGER PRIMARY KEY, name TEXT NOT NULL UNIQUE, hired_at TEXT NOT NULL)`; "
                           "`tickets(id INTEGER PRIMARY KEY, subject TEXT NOT NULL, requester INTEGER NOT "
                           "NULL REFERENCES agents(id), priority INTEGER NOT NULL CHECK (priority IN "
                           "(1,2,3)), status TEXT NOT NULL CHECK (status IN ('open','pending','closed')), "
                           "created_at TEXT NOT NULL, first_response_at TEXT, closed_at TEXT, CHECK "
                           "(first_response_at IS NULL OR first_response_at >= created_at), CHECK (closed_at "
                           "IS NULL OR closed_at >= created_at))`; `ticket_events(id INTEGER PRIMARY KEY, "
                           "ticket_id INTEGER NOT NULL REFERENCES tickets(id) ON DELETE CASCADE, agent_id "
                           "INTEGER REFERENCES agents(id), kind TEXT NOT NULL CHECK (kind IN "
                           "('note','reply','status_change')), created_at TEXT NOT NULL)`. Note what the "
                           "constraints make impossible: a response before the ticket exists, a priority of "
                           "7, an event pointing at a deleted ticket. Indexes: (status, created_at) for the "
                           "backlog query, (requestee_id, created_at) for agent load - each justified in "
                           "NOTES.md by an EXPLAIN QUERY PLAN before and after.",
        "testing": "verify.sql is the test suite, and the seed contains the edge cases on purpose: tickets "
                   "never answered (first_response_at NULL - the report must count them in a separate "
                   "bucket, reproducing the spreadsheet's silent-average bug as an explicit number), a "
                   "ticket answered in the same minute it was created (zero first-response), status changes "
                   "without events, an agent with zero tickets (LEFT JOIN from agents - they appear with 0, "
                   "not vanished), two tickets with identical timestamps (the ORDER BY tiebreaker makes "
                   "paging deterministic). Each report has at least one pinned expected value asserted with "
                   "a CASE/RAISE (SQLite: SELECT RAISE) or an exception-raising DO block (PostgreSQL). "
                   "Negative tests too: run.sh attempts three invalid inserts (response before creation, "
                   "bad priority, event for a missing ticket) and asserts each is rejected by the schema. "
                   "CI runs run.sh on every push.",
        "expected_output": "`./run.sh` builds a fresh database, prints all four reports with correct, "
                           "pinned numbers - including the never-answered bucket the spreadsheet lost - "
                           "then reports `verify: 12/12 assertions passed, 3/3 invalid inserts rejected`. "
                           "NOTES.md states the question each report answers, the EXPLAIN evidence for each "
                           "index, and the Monday-report time the team saves. The whole project rebuilds "
                           "identically on any machine, which is the reproducibility the edited spreadsheet "
                           "could never offer.",
        "improvements": [
            "Add a moving 4-week average of ticket volume per agent with a window frame, and pin it in verify.",
            "Import the team's real CSV export through a staging table with validation queries that report (not silently drop) rejected rows.",
            "Port to PostgreSQL: partition ticket_events by month and compare the EXPLAIN plans.",
            "Wrap run.sh output in a small static HTML page the team can open instead of the spreadsheet.",
        ],
        "resume_md": "**Operations Reporting Database** | SQL, SQLite/PostgreSQL, schema design\n"
                     "- Normalized ticket schema whose CHECK/FK constraints make invalid states "
                     "unrepresentable; negative tests prove bad rows are rejected.\n"
                     "- Window-function reports (first-response distribution, agent load, moving averages) "
                     "with never-answered tickets counted explicitly; every report pinned by a verification "
                     "suite that runs in CI.",
        "interview_questions": [
            "The old spreadsheet's average first-response time was wrong. What exactly did it do to NULLs, and what does your report show instead?",
            "Why does an agent with zero tickets need a LEFT JOIN from agents, and what would the INNER JOIN version of the report claim?",
            "Your backlog query uses the (status, created_at) index. Show the EXPLAIN QUERY PLAN evidence and explain why the column order matters.",
            "Two tickets share a timestamp and the report pages through them. What guarantees page 2 does not repeat a row from page 1?",
        ],
        "tech": ["SQLite", "PostgreSQL (portable target)", "shell scripting", "Git"],
        "skills": ["schema design with constraints", "window functions", "NULL semantics in aggregates", "EXPLAIN-driven indexing", "query result testing"],
        "steps": [
            ("1. Schema that refuses garbage", "Design the tables and constraints before any query",
             "Write schema.sql from the questions the report must answer. Add the CHECK constraints (priority "
             "domain, timestamp ordering) and foreign keys, and decide nullability deliberately: "
             "first_response_at is nullable because never-answered tickets are real. Write the three "
             "negative-insert tests in run.sh immediately. Done when each invalid insert is rejected by the "
             "schema, not by a query convention."),
            ("2. Deterministic seed", "Build a fixture that contains every edge case on purpose",
             "Write seed.sql (or a small generator with a fixed seed): ~200 tickets across ~6 agents and 8 "
             "weeks, explicitly including the never-answered tickets, the zero-minute response, the "
             "identical timestamps, the agent with no tickets and the closed-without-events ticket. Each "
             "edge case gets a comment naming the report behaviour it exercises. Done when the same seed "
             "file produces byte-identical databases on two runs."),
            ("3. The core reports", "Volume, first response, backlog age - with NULL semantics handled",
             "Write reports/weekly_volume.sql, first_response.sql (COUNT(*) vs COUNT(first_response_at), the "
             "never-answered bucket as its own row), backlog_age.sql (age buckets via CASE over date "
             "differences, filtered on status). Each file starts with a comment stating the question. Add "
             "the pinned assertions to verify.sql as you go. Done when verify passes and the "
             "never-answered count matches a hand-count of the seed."),
            ("4. Window functions", "Agent load, ranking and a moving average",
             "Write agent_load.sql: tickets per agent with LEFT JOIN from agents (zero-ticket agents "
             "visible), ROW_NUMBER ranking within a week, and a 4-week moving average with an explicit "
             "window frame (ROWS BETWEEN 3 PRECEDING AND CURRENT ROW). Include the deterministic tiebreaker "
             "in every ORDER BY. Pin each in verify.sql. Done when the frame boundaries are provable: the "
             "first week's 'moving average' equals that week alone."),
            ("5. The performance pass", "EXPLAIN, add justified indexes, document the evidence",
             "Run EXPLAIN QUERY PLAN (SQLite) or EXPLAIN ANALYZE (PostgreSQL) for every report on the seeded "
             "data, then on a generated 100k-row version. Add the two indexes, re-run and capture before/"
             "after plans in NOTES.md - including any report where the index did not help and why you kept "
             "or dropped it. Done when every index in schema.sql has a plan in NOTES.md justifying it."),
            ("6. Ship it", "CI, documentation and handover",
             "Wire run.sh into CI (fresh temp database, load, reports, verify, negative tests, summary "
             "line). Write NOTES.md fully: each report's question, its edge cases, the index evidence, and "
             "the engine portability notes (PRAGMA foreign_keys per connection in SQLite). Tag v1.0.0. Done "
             "when a classmate runs ./run.sh on a clean checkout and gets `12/12 assertions passed, 3/3 "
             "invalid inserts rejected` - the same numbers you documented."),
        ],
        "resources": [
            ("documentation", "PostgreSQL tutorial: window functions", "https://www.postgresql.org/docs/current/tutorial-window.html",
             "The official walkthrough of ROW_NUMBER, frames and moving averages - the mechanics behind the agent-load report, portable to SQLite."),
            ("documentation", "SQLite language reference: EXPLAIN QUERY PLAN", "https://www.sqlite.org/eqp.html",
             "How to read SQLite's plan output - the evidence each index in NOTES.md is justified with."),
        ],
    },
    # ------------------------------------------------------------------ C#
    {
        "slug": "csharp-tasks-api",
        "title": "Tested Minimal-API Task Service with a Bounded Reminder Tool",
        "language": "csharp",
        "branch": "computer-science",
        "subject": None,
        "difficulty": "advanced",
        "category": "software",
        "est_hours": 34,
        "summary": "Build a small, fully tested C# service that records tasks, stores them safely in SQLite, "
                   "exposes a validated minimal API with per-user ownership, and offers one strictly bounded "
                   "reminder tool - the capstone for the C# path.",
        "problem_statement": "A study group coordinates in a chat thread: task lists scroll away, nobody knows "
                             "who owns what, and the weekly 'what is overdue' message is whoever remembers to "
                             "write one. A shared spreadsheet was tried and failed the same week two people "
                             "edited it at once - one person's rows were silently overwritten, and the file "
                             "has no history of who changed what.\\n\\nThe group needs a tool they trust: tasks "
                             "recorded with an owner and a due date, stored locally with a real schema, served "
                             "over HTTP so every member's client sees the same state, and an overdue digest "
                             "that is generated from their own data by code they can read - with each member "
                             "able to touch only their own tasks.",
        "objective": "Ship a .NET solution (API project plus xUnit test project) where a user can create, "
                     "list, complete and delete tasks; data persists in SQLite through parameterized "
                     "queries only; every input crossing the HTTP boundary is validated server-side; "
                     "requests carry a simple API key that the service maps to an owner, and every "
                     "read and write is scoped to that owner in the query itself; and a single "
                     "allowlisted reminder tool composes the overdue digest deterministically (no model "
                     "call required). Outcomes the build proves: you can structure a C# solution into "
                     "projects with xUnit tests, you treat every boundary as untrusted, and you can "
                     "bound an automation so its worst case is acceptable.",
        "prerequisites": [
            "C# path: Foundations and Working Practice stages complete (methods, collections, LINQ, errors, testing)",
            "C# path: Advanced Engineering modules on async and minimal APIs",
            "Comfortable running dotnet test and reading a failing xUnit assertion",
        ],
        "hardware": "Any laptop that runs the .NET 8 SDK. No server, GPU or paid API account is required.",
        "software": ".NET 8 SDK, Microsoft.Data.Sqlite, xUnit, SQLite (bundled via the NuGet package), Git.",
        "architecture": "Three layers with one direction of dependency. A storage layer owns SQLite and "
                        "exposes typed async functions (AddTaskAsync, ListOverdueAsync) built only from "
                        "parameterized commands. A service layer holds the rules - required fields, due-date "
                        "handling, owner scoping, the reminder digest - and knows nothing about HTTP. A "
                        "minimal-API layer validates request DTOs (records with required members), resolves "
                        "the API key to an owner id, and returns typed results (Results.Ok / Results.BadRequest "
                        "/ Results.NotFound / Results.Forbid). Nullable reference types are enabled and the "
                        "build treats warnings as errors, so a missing null check fails the build instead of "
                        "the demo. The reminder tool is a pure function over the service layer's data: it "
                        "reads, formats and returns text - it cannot write, call the network or touch the "
                        "file system, which is stated in its signature (no I/O types in, no Task out).",
        "source_code": "Suggested layout:\\n\\n```\\nTasks.Api/Program.cs            # endpoints, validation, key->owner mapping\\nTasks.Api/Storage.cs            # parameterized SQLite access, async\\nTasks.Api/TasksService.cs        # rules + the reminder digest (pure)\\nTasks.Api/Models.cs              # request/response records\\nTasks.Tests/StorageTests.cs      # temp-file SQLite per test\\nTasks.Tests/ServiceTests.cs      # rules incl. ownership scoping\\nTasks.Tests/ApiTests.cs          # WebApplicationFactory: status codes + bodies\\n```\\n\\nKeep Program.cs thin: parse, validate, authorize, delegate. The service layer must be "
                       "testable without HTTP (plain method calls in ServiceTests) and the storage layer "
                       "without the service (temp databases in StorageTests). ApiTests prove the wiring: "
                       "401 without a key, 403 across owners, 400 on invalid DTOs, 404 on missing tasks.",
        "database_design": "`owners(api_key TEXT PRIMARY KEY, name TEXT NOT NULL)`; `tasks(id INTEGER PRIMARY "
                           "KEY, owner_key TEXT NOT NULL REFERENCES owners(api_key) ON DELETE CASCADE, title "
                           "TEXT NOT NULL CHECK (length(title) BETWEEN 1 AND 200), due_at TEXT NOT NULL, "
                           "done INTEGER NOT NULL DEFAULT 0 CHECK (done IN (0,1)), created_at TEXT NOT NULL "
                           "DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ','now')))`. Every task query carries "
                           "`WHERE owner_key = @owner` - ownership is enforced in SQL, not by filtering in "
                           "C# after the fact. Index on (owner_key, due_at) for the overdue listing, justified "
                           "with an EXPLAIN QUERY PLAN captured in the test output. PRAGMA foreign_keys = ON "
                           "is set on every connection the storage layer opens.",
        "testing": "xUnit across three projects-of-concern. StorageTests run against a fresh temp-file SQLite "
                   "database per test: round-trip a task, prove cross-owner rows are invisible to "
                   "ListOverdueAsync, prove the CHECK constraints reject empty titles. ServiceTests cover "
                   "the rules with no I/O: validation refusals (empty title, due date in unparsable form), "
                   "the overdue digest's exact text for a fixed clock (the clock is injected - the digest "
                   "takes a DateTimeOffset parameter, never DateTimeOffset.UtcNow), and the empty-digest "
                   "message. ApiTests spin up the app with WebApplicationFactory: missing key returns 401, "
                   "a key reading another owner's task returns 404 (not 403 - ids are not enumerable), "
                   "invalid JSON returns 400 with a useful problem body, and the happy path returns the "
                   "created task with its owner-scoped id. Security assertions are explicit tests, not "
                   "comments: cross-owner read, cross-owner delete and SQL-injection-shaped titles "
                   "(`x'; DROP TABLE tasks;--` stored as a harmless title) each have a named test. "
                   "`dotnet test` plus `dotnet build -warnaserror` is the one-command gate.",
        "expected_output": "`dotnet test` reports all suites green (20+ tests, including the named security "
                           "tests), and `dotnet run --project Tasks.Api` serves the API: creating two tasks "
                           "under different keys and fetching the overdue digest shows each owner exactly "
                           "their own overdue items with the deterministic digest text. A short DEMO.md shows "
                           "the curl commands and the expected status codes. The reminder tool's signature "
                           "documents its bounds - pure function, no I/O - which is the audit story when "
                           "someone asks what the automation is allowed to do.",
        "improvements": [
            "Replace API keys with signed tokens (Data Protection or JWT) with expiry, keeping the per-request ownership check untouched.",
            "Add pagination with keyset links (not OFFSET) to the task listing, and pin the ordering with a tiebreaker test.",
            "Add a second bounded tool - a weekly summary - behind the same pure-function contract, and prove in tests it cannot write.",
            "Containerize the API with a published port and a health endpoint, and assert the health check in CI.",
        ],
        "resume_md": "**Task Service API** | C#, ASP.NET Core minimal APIs, SQLite, xUnit\\n"
                     "- Owner-scoped task API with validated DTOs, parameterized SQLite access and nullable "
                     "reference types enforced as build errors.\\n"
                     "- 20+ xUnit tests including named security tests (cross-owner isolation, injection-shaped "
                     "input stored harmlessly); deterministic overdue digest behind a pure-function tool contract.",
        "interview_questions": [
            "Your delete endpoint returns 404 when the task belongs to another owner instead of 403. Why is that the safer choice?",
            "The reminder tool cannot write to the database. How does its signature prove that, and what would have to change for it to gain write access?",
            "A title containing SQL metacharacters is stored harmlessly. Walk me through the exact mechanism - where does the boundary between code and data live?",
            "The digest takes the clock as a parameter instead of reading the time itself. What test does that enable that a hidden clock would not?",
        ],
        "tech": ["C# 12", ".NET 8", "ASP.NET Core minimal APIs", "Microsoft.Data.Sqlite", "xUnit", "Git"],
        "skills": ["minimal API design", "server-side validation", "owner-scoped authorization", "parameterized data access", "xUnit testing at three layers", "bounding automations by construction"],
        "steps": [
            ("1. Slice zero: models, storage, one endpoint", "Prove the database round-trip before any rules",
             "Create the solution with the API and test projects, enable nullable + warnings-as-errors, and "
             "write Models.cs (TaskItem and CreateTaskRequest records with required members), the tasks table "
             "in Storage.cs with PRAGMA foreign_keys = ON, and POST/GET endpoints that round-trip one task. "
             "Write the first StorageTests against temp-file databases. Done when dotnet test is green and a "
             "curl POST followed by GET returns the stored task."),
            ("2. Ownership and validation", "Keys, scoping and refusal tests",
             "Add the owners table and the key-to-owner mapping middleware (missing key -> 401), scope every "
             "task query with WHERE owner_key = @owner, and validate request DTOs (title length, parsable "
             "due date -> 400 with a problem body). Write the cross-owner ApiTests: reading or deleting "
             "another owner's task returns 404, and ids are not enumerable. Done when the named security "
             "tests exist and pass."),
            ("3. Rules and the digest", "Service layer with an injected clock",
             "Move the rules into TasksService: due-date handling, done transitions, and the overdue digest "
             "as a pure function of (tasks, now) with now injected. Write ServiceTests with a fixed clock "
             "pinning the digest's exact text, including the empty-digest message and the boundary task due "
             "exactly now. Done when the digest text is byte-pinned and the service has no I/O types in its "
             "signatures."),
            ("4. The bounded tool", "One automation with a provable worst case",
             "Expose the digest as the single reminder tool behind an allowlist: the API surface offers "
             "exactly one tool name, unknown names are refused with a typed error, and the tool's "
             "implementation calls only the pure digest function. Write tests proving the tool cannot write "
             "(no storage calls in its path - assert with a spy or by construction review in DEMO.md) and "
             "that an unknown tool name returns the typed refusal. Done when the tool's bounds are stated "
             "in DEMO.md and enforced by tests."),
            ("5. Hardening pass", "Injection, constraints and the query plan",
             "Add the injection-shaped-title test (stored harmlessly, rendered back exactly), the CHECK-"
             "constraint negative tests (empty title rejected by the schema), and the (owner_key, due_at) "
             "index with its EXPLAIN QUERY PLAN captured into the test output. Turn on build warnings as "
             "errors if not already done and clear every nullable warning honestly (no `!` suppressions "
             "without a comment stating the proof). Done when dotnet build -warnaserror and dotnet test "
             "are both clean."),
            ("6. Ship it", "CI, DEMO.md and handover",
             "Wire the one-command gate (build with warnings-as-errors plus full test run) into CI. Write "
             "DEMO.md: the curl sequence for two owners, the expected status codes (401/403/404/400 each "
             "shown once), the digest output, and the tool-bounds statement. Tag v1.0.0. Done when a "
             "classmate clones fresh, runs the gate and the curl sequence, and sees the documented "
             "results - including the 404 (not 403) on a cross-owner read."),
        ],
        "resources": [
            ("documentation", "Microsoft Learn: minimal APIs tutorial", "https://learn.microsoft.com/en-us/aspnet/core/tutorials/min-web-api",
             "The official walkthrough: routing, parameter binding, typed results and validation - the mechanics behind the endpoints."),
            ("documentation", "Microsoft Learn: SQLite in .NET", "https://learn.microsoft.com/en-us/dotnet/standard/data/sqlite/",
             "Microsoft.Data.Sqlite usage including parameterized commands - the code/data boundary the storage layer depends on."),
            ("documentation", "Microsoft Learn: unit testing with dotnet test", "https://learn.microsoft.com/en-us/dotnet/core/testing/unit-testing-with-dotnet-test",
             "xUnit project setup and the test/explore/debug loop the three test projects follow."),
        ],
    },
]


#: Every key a capstone must carry to satisfy the seeder and the project page.
REQUIRED_KEYS = (
    "slug", "title", "language", "branch", "subject", "difficulty", "category", "est_hours",
    "summary", "problem_statement", "objective", "prerequisites", "hardware", "software",
    "architecture", "source_code", "database_design", "testing", "expected_output",
    "improvements", "resume_md", "interview_questions", "tech", "skills", "steps", "resources",
)

MIN_STEPS = 5


def all_urls() -> list[str]:
    """Every external URL in the capstone briefs, for the link checker."""
    return [url for entry in CAPSTONES for _kind, _title, url, _note in entry.get("resources", []) if url]


def validate(languages: set[str], known_projects: set[str]) -> None:
    """Fail the seed on an incomplete, duplicated or mislinked capstone brief."""
    problems: list[str] = []
    slugs: set[str] = set()
    per_language: dict[str, int] = {}
    for index, entry in enumerate(CAPSTONES):
        where = f"CAPSTONES[{index}] {entry.get('slug', '?')!r}"
        missing = [key for key in REQUIRED_KEYS if key not in entry]
        if missing:
            problems.append(f"{where}: missing keys {missing}")
            continue
        if entry["slug"] in slugs:
            problems.append(f"{where}: duplicate slug")
        slugs.add(entry["slug"])
        if entry["slug"] in known_projects:
            problems.append(f"{where}: slug collides with a library_data project")
        if entry["language"] not in languages:
            problems.append(f"{where}: unknown language {entry['language']!r}")
        per_language[entry["language"]] = per_language.get(entry["language"], 0) + 1
        if not 1 <= len(entry["steps"]) or len(entry["steps"]) < MIN_STEPS:
            problems.append(f"{where}: {len(entry['steps'])} steps, at least {MIN_STEPS} required")
        for order, step in enumerate(entry["steps"]):
            if len(step) != 3 or not all(str(part).strip() for part in step):
                problems.append(f"{where}: step {order} is not a (phase, title, body) triple of non-empty text")
        if not entry["resources"]:
            problems.append(f"{where}: a capstone without resources sends the learner nowhere")
        for kind, title, url, _note in entry["resources"]:
            if not kind or not title:
                problems.append(f"{where}: resource with an empty kind or title")
            if not url.startswith("https://"):
                problems.append(f"{where}: resource URL {url!r} must be a specific https page")
        for field in ("problem_statement", "objective", "testing", "expected_output", "architecture"):
            if len(str(entry[field]).strip()) < 120:
                problems.append(f"{where}: {field} is stub-thin ({len(str(entry[field]).strip())} chars)")
        if not entry["prerequisites"] or not entry["improvements"] or not entry["interview_questions"]:
            problems.append(f"{where}: prerequisites, improvements and interview questions must be non-empty lists")

    uncovered = sorted(languages - set(per_language))
    if uncovered:
        problems.append(f"languages without a capstone brief: {uncovered}")
    doubled = sorted(language for language, count in per_language.items() if count > 1)
    if doubled:
        problems.append(f"languages with more than one capstone brief: {doubled}")

    if problems:
        raise ValueError(
            "language_projects.py is incomplete or inconsistent:\n  " + "\n  ".join(problems)
        )
