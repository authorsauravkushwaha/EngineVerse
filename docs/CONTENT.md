# Content model and licensing

How content is added, reviewed, published, and what may legally be hosted.

## The content lifecycle

Tables that participate in the editorial workflow carry `status`, `version` and
`author_id`. Those records move through:

```
draft ──► under_review ──► approved ──► published ──► archived
  ▲            │                                        │
  └────────────┴──────────── changes requested ─────────┘
```

Only `published` rows from those editorial tables reach learners. Queries filter
on the relevant status field — for example, `topics.status = 'published'` and
`subjects.status = 'published'` — so a draft remains invisible. Seeded reference
content such as formula rows and flashcards does not currently use this workflow.

Capability to move content along that path is defined in `security/rbac.py`, not
in the UI. `subject_expert` and `content_admin` hold `content.publish`;
`project_reviewer` holds `projects.review`; `student` holds none of them. A
learner cannot publish by crafting a request, because the check is on the server
and fails closed.

## What may be hosted

The rule is simple: **EngineVerse hosts what it creates, and links to everything
else.**

| Content | Policy |
|---|---|
| Notes, diagrams authored here, questions, coding problems, roadmaps | Hosted. Original work, CC-BY-4.0 unless stated otherwise. |
| Videos | **Linked only.** `videos.url` points at NPTEL, MIT OpenCourseWare, freeCodeCamp, Khan Academy. `videos.embed_id` exists in the model but is deliberately never populated. |
| Books | **Linked only.** `books.url` points at the publisher, or at the open-access source when the book is genuinely open. `books.is_free` says which. |
| External articles and documentation | **Linked only.** `resources.url`, with `is_free` marking open material. |
| Third-party diagrams | Only with a recorded `license` and `source_url`. |

No copyrighted book, paper or video is stored on EngineVerse servers, mirrored,
proxied, or embedded. A link to a legal source is not a substitute for hosting,
and it is the only thing this platform does with third-party media.

This is also why there is no upload pipeline for media: there is nothing to
upload.

## Checking the links

Every external URL in the library is checked by `scripts/check_links.py`. It
scans the `resources`, `videos`, `books` and `project_resources` tables (so the
documentation links inside project and capstone briefs are covered too), plus the
URLs declared in the seed registries, so a link can be checked before it is ever
seeded.

```
python scripts/check_links.py --offline   # structural, no network, runs on every push
python scripts/check_links.py             # also fetches each URL, runs weekly in CI
python scripts/check_links.py --json      # machine-readable report
```

Offline mode validates the scheme, rejects private and loopback hosts, embedded
whitespace and placeholders, and warns on plain `http` and bare site roots. It
runs on every push because it needs no network and cannot flake.

The networked mode runs on a weekly schedule and on demand, not per pull request:
fetching a few hundred publisher URLs is slow, and a rate-limited response would
fail a change that touched nothing. HTTP 403, 429 and 451 are warnings rather
than failures for the same reason — many publishers refuse automated clients, and
failing on that would make the whole check noise. 404 and 410 are failures.

Nothing verifies the *content* behind a link. A URL that resolves to a parked
domain passes, so the checker is a floor rather than a guarantee.

## Certificates

Certificates carry a `verify_id` and are verifiable at
`/certificates/{verify_id}`. They state what the learner completed on
EngineVerse. They do **not** claim university accreditation, professional
licensure, or equivalence to any awarding body's qualification, and no template
or copy in the repository implies it. Anyone who needs that distinction can check
the verification URL.

## Seeding

`scripts/seed.py` builds the public catalogue. The following snapshot was
regenerated from a fresh `--no-demo` seed; it describes seeded rows, not a claim
that every branch is a complete syllabus:

```
universities 10 · colleges 13 · branches 45 · semesters 9 · curricula 180
curriculum_subjects 2836 · subjects 93 · modules 93 · topics 406 · notes 1624
note_sections 10556 · diagrams 406 · models_3d 406 · formulas 365 · questions 534
question_options 2136 · dpp_sets 107 · dpp_questions 535 · programming_languages 10
language_modules 225 · language_stages 30 · language_checkpoints 90
coding_problems 105 · coding_sheets 14 · coding_sheet_problems 135 ·
coding_problem_stubs 108 · coding_testcases 461 · projects 17
project_steps 98 · project_resources 30 · videos 400 · books 395 · resources 544
roadmaps 5 · roadmap_nodes 57 · flashcards 281 · plans 3 · site_config 12
badges 12 · search index 3836
```

Every active branch has at least one published subject, every published subject
has a published lesson and active question, and every active question appears in
the 107-set DPP rotation, covering all 93 subjects and all ten language tracks.
The archive is paginated at
`/dpp/archive`, so older seeded sets remain discoverable. All 281 seeded
flashcards can be browsed at `/flashcards`, searched without exposing their
answers in search snippets, and opened individually; personal SM-2 scheduling
remains at `/revision`. `/sitemap.xml` includes published branches, subjects,
topics, languages, roadmaps, projects, coding problems, dated DPPs, individual
flashcards and later pages of public shelves; its canonical origin comes from
`ENGINEVERSE_SITE_URL`, not the request `Host` header.
`robots.txt` advertises that sitemap using the same configured origin.
Each of the 406 topics has four published reading-depth notes; the standard-depth
note contains all thirteen sections. Topic-linked
questions, a validated diagram and an interactive 3D model are seeded for every
lesson. Cyber Security has thirteen public lessons and is readable without signing
in. The generated catalogue runs in three passes: 71 breadth-first starter topics
that give every published subject an entry point, then two deeper lessons per
subject from `seed_data/deeper_lessons.py` (186 topics) that work one
high-leverage theme each with a real formula, derivation, worked example and
pitfall, then one mastery lesson per subject from `seed_data/mastery_lessons.py`
(93 topics) which carries two independent worked checks, several applications
and pitfalls, and exam and interview prompts written for that relation instead
of being templated from its name. All 350 generated topics are marked
`needs_review` in editorial metadata; publication makes them reachable but does
not imply expert sign-off, and three generated lessons per subject is starter
depth, not exhaustive coverage.

The ten programming paths are staged — 225 modules assigned across 30
Foundations / Working Practice / Advanced Engineering stages — and each stage
ends with three checkpoint questions (90 total). Checkpoints are ordinary bank
questions linked through `language_checkpoints`, so they run through the normal
practice-answer flow: the answer key, correct-option flag and explanation are
stripped from the page and only returned after a submission, and a wrong attempt
still awards attempt XP and lands in the mistake notebook. Their correct-answer
positions are rotated deterministically, so a reseed reproduces the same bank.
Legacy book modules store a `practice_slug` linking related coding practice;
this does not prove language-specific exercise coverage. Fifteen existing modules
now have validated `lesson_data` with A–O sections; 210 remain legacy format.
Every module has a focused reader. See [Academy authoring and scope](ACADEMY.md)
for coverage, validation and deployment instructions. The seventeen project briefs span hardware and engineering
tools as well as
software, and include a substantial capstone linked to each language path
(forward from the path page, back from the brief); the study-planner brief starts
model-free and treats an optional agent as an allowlisted, confirmation-gated
layer, not a production-ready reference design.

Section bodies are assembled from the original and expanded topic entries, and
the coverage tests assert all thirteen sections on every standard note. Notes are
keyed by topic slug; `seed.py` raises if authored content names a topic that no
longer exists, so a renamed topic cannot silently drop content.

### The coding bank

Problems live in four authored modules and are assembled by `seed.py`:

| Module | Holds |
|---|---|
| `seed_data/practice_data.py` | The 13 original problems, with their hand-written stubs and wrappers. |
| `seed_data/coding_core.py` | 44 interview-pattern problems (arrays, windows, trees, graphs, DP, SQL). |
| `seed_data/coding_streams.py` | 38 problems written for a branch: signals, control, surveying, process calculations and the like. Each names its audience category. |
| `seed_data/coding_book.py` | 10 problems for the book-depth language paths: six raw beginner drills plus the pattern staples (merge intervals, rain water, word ladder, tree codec) the stage plans reference. |
| `seed_data/coding_sheets.py` | The 14 curated sheets: title, audience categories, estimated hours and the ordered problem slugs. |

`scripts/check_problems.py` runs every reference solution against its own test
cases through the same wrapper the judge uses, so an expected output that no
correct program can produce fails in the scripts rather than in a learner's
editor. `--sheets` additionally asserts that every problem in the bank appears in
at least one sheet. A sheet that names a slug outside the bank is refused by
`coding_sheets.validate()` at seed time.

A new problem needs a test case, an entry point and a reference solution; a
problem whose input is not one of the wrapper shapes also needs a wrapper in
`engineverse/drivers.py` (see above). It does *not* carry an XP value: XP is
decided by the judge result (30 first accepted, 8 on a later accepted run, 3 for
a wrong answer), so the same problem pays the same amount whichever sheet it is
reached through.

```bash
python scripts/seed.py --fresh    # drop and rebuild
python scripts/seed.py --stats    # print row counts
```

The seeder is idempotent: re-running it without `--fresh` upserts rather than
duplicating, so it is safe to run against a database that already has learner
data.

## Extending without a redesign

Nothing about the catalogue is hard-coded in the frontend. Branches, subjects,
topics, questions, problems and projects are rows, and the templates iterate
them. Adding a branch means inserting into `branches` and `subjects`; no template
changes.

### After you insert rows, the search index has to catch up

Global search and the AI tutor both read a derived index, not the content tables.
Nothing indexes a row at the moment it is written, so a subject you just inserted
is not searchable until the index is rebuilt. Two things do that:

```bash
python scripts/reindex.py            # rebuild now
python scripts/reindex.py --check    # report what the index holds, change nothing
```

and the application rebuilds on startup when it notices the content has changed.
`search.refresh_if_stale()` hashes the exact source fields used by the indexer,
including timestamp-free tables and joined content such as note sections, project
steps, language modules and searchable profile settings. Inserts, edits and
removals therefore invalidate the marker; the stored marker contains table
counts and digests, not source text.

Both are worth knowing about because the version marker alone is not enough.
It records which *schema* of index the code produces, and once it matches it
stays matched, so relying on it would have left newly added content invisible
until a schema change happened to force a rebuild.

When the indexer starts using a new source column or table, update its
fingerprint projection and bump `INDEX_SCHEMA_VERSION` in `engineverse/search.py`.
`scripts/seed.py` reindexes as part of seeding; a manual catalogue edit is detected
on the next startup when it changes one of the indexed source fields.

The one place a new *shape* of content needs code is the coding judge: a problem
whose input is not one of the thirteen known forms needs a new wrapper in
`engineverse/drivers.py`. Everything else is data.

## AI-assisted content

Two rules, both enforced in the UI rather than left to convention:

1. **AI-generated prose is labelled.** A reader can always tell which text was
   machine-assisted.
2. **AI answers cite their sources.** The tutor grounds responses in platform
   content and references it, rather than answering from the model alone.

An unlabelled or unsourced AI answer on an education platform is worse than no
answer, because the learner cannot weigh it.
