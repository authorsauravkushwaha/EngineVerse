# Programming academy: delivered scope, authoring and rollout

This is an incremental educational upgrade, **not ten complete textbooks**.
The [audit](ACADEMY_AUDIT.md) records the baseline and implementation decisions.
The [verification report](ACADEMY_VERIFICATION.md) separates executed examples
from unavailable toolchains and remaining review work.

## What learners can use now

- `/programming/{language}` is a searchable course index with the original
  module fragment ids, three stages, real stage quizzes and existing capstone.
  A seven-level syllabus names language-specific learning goals, explicitly
  labelled as expansion goals rather than completed coverage.
- `/programming/{language}/lessons/{module}` reads one existing module, with
  previous/next links. All 225 modules have readers; no existing ids or accounts
  were replaced. Search's old course-fragment URLs still resolve.
- Fifteen existing modules now have complete **structured learning-unit fields**:
  objectives, intuition, technical reasoning, visual trace, syntax/version rules,
  examples, walkthrough, applications, debugging, alternatives, conceptual check,
  guided exercise, independent challenge, mastery rubric and next steps (A–O).
  Field completeness is not expert sign-off or evidence of learner mastery.
- Every structured unit includes exact exercise contracts, progressive hints,
  edge-case coverage, a reference implementation and correctness/cost reasoning.
  Source links and review notes distinguish references from execution results.
- Native HTML tables and details work without JavaScript. Progressive tools add
  a step-through trace, safe copy buttons, module filtering, code drafts and a
  reference reveal after an attempt. Lightweight escaped syntax colors are a
  reading aid, not compiler parsing.

## Actual structured coverage

| Language | Structured modules | Legacy modules still awaiting expansion |
|---|---|---:|
| Python | `python-loops-from-scratch`, `python-complexity-big-o` | 33 |
| C | `c-loops`, `c-complexity-big-o` | 24 |
| C++ | `cpp-decisions-loops`, `cpp-complexity-big-o` | 25 |
| Java | `java-loops-from-scratch`, `java-complexity-big-o` | 29 |
| C# | `csharp-decisions-loops`, `csharp-complexity-big-o` | 16 |
| JavaScript | `js-decisions-loops` | 22 |
| TypeScript | `ts-decisions-loops` | 15 |
| Go | `go-decisions-loops` | 16 |
| Rust | `rust-decisions-loops` | 16 |
| SQL | `sql-real-world-1` (relational filtering/aggregation, not an imperative-loop imitation) | 14 |

The common accumulator algorithm is intentionally shared, with language-specific
syntax, arithmetic rules, tool commands, errors and idioms. SQL instead teaches
bag semantics, NULL, aggregate contracts and query-plan assumptions. This is
cross-language transfer, not ten generic pages with renamed buttons.

The five priority-language complexity units distinguish O/Ω/Θ from case
selection, state the cost model, prove a half-open boundary search, compare
linear scanning, and handle first duplicates and empty arrays. The C contract
explicitly scopes integer/index widths rather than assuming all C targets are
32-bit. C++ and managed-language library search contracts are not presented as
identical to a first-duplicate search.

## Honest practice and persistence boundaries

This reader is a **local-execution/reference-solution experience**. It does not
accept uploads, compile drafts, run hidden tests, save attempts, award XP or
record module mastery. Drafts and checkboxes live in the current document only;
there is no localStorage or cross-account browser progress cache. Navigating away
loses drafts. Browsers may independently restore form state through their own
history/autofill; shared-device users should clear it and never paste secrets.

“Record attempt for self-review” checks only for a nonblank attempt, opens the
reference and explicitly says nothing was executed or graded. Reset clears the
draft and closes the reference. Without JavaScript, learners can write locally
and open the reference directly. The gate is pedagogical, not answer security:
reference code is shipped with this public reading material.

The disclosed test table describes fixtures/coverage, not a hidden online
judging service. The Python, C, C++, Java, C#, JavaScript, Go and Rust filtered
sum references use stdin; TypeScript uses a typed function; SQL uses table
fixtures. Binary-search units use a function contract with complete demo
programs. Some parsers store all input: their total space is O(n) even though
the accumulator itself uses constant auxiliary space.

Existing account-backed stage quizzes, mistake history, coding submissions,
notes/bookmarks and topic progress remain unchanged. A topic-keyed progress
record is not falsely repurposed as a language-module score. Related coding
problems may lack a starter in the course language; the course index labels
them as related practice. A complete per-language problem bank remains work.

No new executor is enabled. Existing production default remains disabled;
external Judge0/Java deployments need an operator-reviewed isolation boundary.
Trusted-source verification below is a developer check, **not a learner-code
execution endpoint**.

## Content and schema architecture

- `seed_data/academy.py`: original authored units keyed by **existing** module slug.
- `backend/engineverse/lesson_schema.py`: versioned JSON contract and field validation.
- `language_modules.lesson_data`: optional TEXT containing JSON, NULL for legacy.
  SQLite and generated PostgreSQL schema both contain the additive field.
- `engineverse.academy`: read-only loading, validation, coverage, syllabus goals.
  Bad/mismatched payloads fall back to the legacy reader and do not count as
  structured units. It has no dependency on authoring files at request time.
- Existing `body`, `example`, `exercise` hold searchable authored material for
  upgraded modules. Search uses its existing content-change fingerprint; the
  targeted updater also reindexes immediately.
- No new tables, user foreign keys, authentication logic or runtime dependencies.

### Add or expand a lesson

1. Select the real language-module slug; do not create an unrelated competing
   course catalogue. For a genuinely new module, add its normal six-field seed
   row and stage assignment in `language_curriculum.py` first.
2. Add an original unit to `UNITS`, with `schema_version: 1`, actual language and
   runtime/version scope, estimated reading/practice minutes, level and valid
   same-language prerequisites. A future feature goal is not an implemented unit.
3. Fill all A–O fields; include runnable deterministic examples with expected
   output, a realistic bug, correction explanation, trace rows, progressive
   hints, independent specification, reference, fixture rationale and sources.
4. Distinguish numeric ranges, implementation assumptions, error modes,
   average/worst/amortized costs, input-storage costs and deliberate simplifications.
5. Add tests that reject plausible wrong approaches and verify the references
   against actual boundary cases. For a new lesson kind, extend the trusted
   verifier; do not reuse a sum-specific harness for an unrelated exercise.
6. Run validation, the focused tests, verifier and static export. Review the
   content as a teacher; passing a length/schema check is not sufficient.
7. Record what actually ran, skipped compilers and expert review status. Never
   mark unavailable examples verified. Update this coverage table after seeding.

`validate_catalogue` rejects unseeded units, cross-language navigation, unknown
prerequisites and prerequisite cycles. `validate_unit` enforces fields, trace
shape, tests, hints, version and source metadata. It does not prove that prose,
algorithms or external documents are correct.

## Development verification

Use the existing pinned Python environment from the README. No new dependency
is required for server operation or Python tests.

```sh
python -m pytest backend/tests/test_academy.py
python scripts/verify_academy.py
python scripts/verify_academy.py --require-all  # provision every compiler first
python scripts/check_links.py --offline       # point at a seeded DB
python scripts/export_pages.py --out site/review --reading-copy
```

`verify_academy.py` runs only trusted checked-in source in disposable temporary
folders, using subprocess timeouts and real compilers/interpreters. It tests
sum fixtures and boundary-search functions against a linear-library oracle over
small sorted arrays. It never loads a learner draft or application submission.
Missing compilers are SKIP by default, or failures with `--require-all`. The CI
workflow runs it after the Python suite; CI tool availability may differ.

Optional real-browser smoke test (development tools stay ignored):

```sh
npm install --prefix .toolchain/browser playwright-core@1.56.1 @sparticuz/chromium@141.0.0
node scripts/check_academy_browser.js http://127.0.0.1:8000
```

Run against a disposable optionally browsable catalogue with judging disabled.
On minimal hosts without NSS/NSPR libraries, extract the package's bundled
`al2023.tar.br` with its `inflate` helper and set
`LD_LIBRARY_PATH=/tmp/al2023/lib` for this QA command. The verification report
records that workaround. This browser binary is a developer test tool, not a
production browser or an application sandbox. `ACADEMY_SCREENSHOTS=path` saves
optional desktop/mobile screenshots. No screenshot dependency ships to users.

## Non-destructive rollout and rollback

**Do not use `--fresh` on an existing installation.** Normal seeding upserts many
catalogue ids and may overwrite CMS edits; it is broader than this update.

1. Back up the database with the existing backup procedure. Record existing
   values of body/example/exercise/lesson_data for the fifteen module ids if a
   content-only rollback is required. Review CMS changes before replacement.
2. Deploy the code, then use the existing privileged release step
   `python scripts/release.py` (or `db.migrate()` on a development database).
   It adds the nullable column idempotently and leaves existing rows intact.
   The production runtime role must not perform DDL.
3. With the reviewed database configuration, run `python scripts/update_academy.py`
   for a **dry run**. It validates all targets and prints ids without writes.
4. Run `python scripts/update_academy.py --apply` only after approval. It changes
   exactly four authored fields on the fifteen existing modules in a transaction,
   then rebuilds derived search data. If indexing fails, retry the existing
   reindex command; the committed content remains intact. No user rows are touched.
5. Smoke-test a legacy and structured reader, old course fragments, stage quizzes
   and sign-in policy. Keep public code execution disabled unless independently
   provisioned and reviewed. No new environment setting is required.
6. Without `ENGINEVERSE_APP_URL`, the Pages workflow makes a no-demo seed and
   exports all 225 reader routes, asset URLs and sitemap links as a static
   reading copy (no accounts/judge). Once a verified full app is hosted, Pages
   becomes a gateway instead; those routes are served by the hosted app.

Rollback: deploy the preceding application version; it ignores the nullable new
column. Restore only the four content fields from the pre-update snapshot and
reindex if reverting lesson text too. Do not drop language modules or restore an
old whole database over newer learner submissions merely to undo content.

## Follow-up backlog (not completed)

- [ ] Expand the remaining 210 legacy modules into substantive A–O units, with
  objective/exercise coverage review rather than module-count targets.
- [ ] Priority-language mastery: Python descriptors/protocols/async; C lifetime,
  aliasing and portability; C++ move/RAII/templates/atomics; Java generics/JVM/
  virtual threads; C# LINQ/nullability/disposal/cancellation, all with versioned tests.
- [ ] Bring JavaScript, TypeScript, Go, Rust and SQL mastery/software-engineering
  units to the same depth. SQL needs dialect-specific plan/transaction exercises,
  not forced syntax translations of pointer or loop lessons.
- [ ] Map language-specific stubs and explanations to each problem pattern;
  add brute-force versus optimized references, adversarial tests and progression
  metadata. Preserve original problem descriptions and licensing policy.
- [ ] Add beginner/intermediate/advanced project briefs with runnable starters
  and automated acceptance tests per priority language; existing capstones are
  preserved but do not fulfill this entire project ladder.
- [ ] Design account-scoped module/objective attempt and mastery records with
  migrations, authorization tests, retry/review rules and a privacy threat model.
- [ ] Add safe timed interview simulations and prerequisite-aware recommendations
  using meaningful assessment signals, not self-checked completion.
- [ ] Provision all compilers in a dedicated content-verification job, require no
  skips, and independently review official docs and content with language experts.
- [ ] Audit remaining legacy factual claims and loosely matched practice links.
- [ ] Independently audit any future public runner's filesystem/network/process/
  resource isolation. Do not convert this developer verifier into a web API.

No phase covering exhaustive curricula, adaptive module persistence, complete
per-language problem banks or multi-level project ladders is declared complete.
