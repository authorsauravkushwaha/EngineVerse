# Academy verification record

Verified locally on 2026-10-15. This is a record of observed checks, not a claim
that every course or supported deployment is complete. No production data,
credentials or learner submissions were used.

## Application and compatibility

| Check | Observed result |
|---|---|
| Baseline Python suite, before code changes | Passed; existing Starlette/httpx deprecation warning |
| Final full Python suite (`python -m pytest -o addopts='--strict-markers' -q --tb=short`) | **1519 passed, 1 skipped, 1 warning**, 442.02 s |
| New academy tests | 47 collected, included in the full-suite result |
| Existing judge/API tests rerun with skip details | 224 passed, 1 skipped; PostgreSQL-only test at `test_api_and_schema.py:2698` requires psycopg in the PostgreSQL CI job |
| Existing compulsory-sign-in tests rerun | 55 passed |
| PostgreSQL schema generation (`gen_pg_schema.py --check`) | Up to date; schema/parser compatibility tests included in Python suite |
| Python compile checks and JavaScript `node --check` | Passed for new modules/scripts |
| `git diff --check` | Passed |

The first integration run caught a duplicated Jinja scripts block; it was fixed
before the final suite. The first full-suite run caught the new reader missing
from the crawler's parameter sources. The crawler now supports both language
and module parameters and requests every reader. Final full-suite result above
has no failing tests. These were integration defects, not tests disabled to get
a passing result.

The new tests exercise A–O fields, every language's coverage/goals, all 225
reader routes, old fragment ids, previous/next links, source and prerequisite
validation, cycles, cross-language/unknown routes, safe escaping and lossless
code coloring, malformed payload fallback, no learner-data writes on reading,
additive/idempotent migration, dry-run and targeted update preservation, sitemap,
static URL rewriting, authentication and realistic incorrect algorithms.

The Python suite runs on SQLite. A live PostgreSQL server/driver and Maven/JDK
were not available locally; do not interpret schema-generation checks as an
actual PostgreSQL deployment or Java sandbox build. No Java-service source was
changed.

## Authored example/reference execution

Command: `python scripts/verify_academy.py`

**574 checks passed; 9 units passed; 6 units skipped. No example failures.**
These are individual expected-output/oracle assertions, not 574 distinct lessons.
Every structured unit passes schema validation even when its compiler is absent.

| Language | Units executed | Result and toolchain |
|---|---:|---|
| Python | 2 | 7 loop checks + 177 bounds checks; Python 3.11.2 |
| C | 2 | 7 loop checks + 177 bounds checks; GCC 12.2.0, C17, warnings-as-errors |
| C++ | 2 | 7 loop checks + 177 bounds checks; G++ 12.2.0, C++17, warnings-as-errors |
| JavaScript | 1 | 7 checks; Node 22.22.3 |
| TypeScript | 1 | 7 checks; TypeScript 5.9.3 strict compilation, ES2022, then Node |
| SQL | 1 | 8 checks; SQLite 3.40.1 via Python's sqlite3 |
| Java | 0 of 2 | SKIP: javac/java unavailable |
| C# | 0 of 2 | SKIP: dotnet unavailable |
| Go | 0 of 1 | SKIP: Go compiler unavailable |
| Rust | 0 of 1 | SKIP: rustc unavailable |

For each executed loop unit, the verifier checks the deterministic example and
six challenge fixtures, including empty input, mixed signs, duplicates and a
maximum total of one billion. Bounds verification checks the halving example,
two reference demo outputs and 175 array/target combinations against
`bisect_left` (all sorted multisets of length 0–4 over {-1,0,1}, with five target
values). This is useful boundary evidence, not a proof over all possible inputs;
the lesson separately gives an invariant and termination argument.

SQL checks execute the authored example/reference, five independent fixtures
and a counterexample to SUM(DISTINCT). The deliberately incorrect fragment
examples are teaching snippets, not claimed to be independently compilable
programs. Separate tests show fixtures rejecting sum-all, last-positive-only,
deduplicating totals and return-on-equality boundary logic.

TypeScript was installed only in ignored `.toolchain/typescript`, not added as
an application dependency. Java/C#/Go/Rust examples have authored reasoning and
version labels but **are not compiler-verified here**. Run the verifier with
`--require-all` on a provisioned host before marking them verified.

`python scripts/check_problems.py --sheets` also passed: all existing Python
problem-bank reference solutions matched their expected outputs; all 14 sheets
cover the existing 105 problems. It does not verify every language starter.

## Static export and links

`python scripts/export_pages.py --out site/academy-review --reading-copy`:

- 1108 pages exported, including all 225 new lesson-reader destinations.
- 150786 local URL references checked: **0 broken links**.
- 1110 HTML heading outlines checked: **0 skipped levels**.
- Exporter and Pages-verifier self-checks passed separately.
- Exports and temporary databases remain ignored; they are not committed.

`python scripts/check_links.py --offline` against the disposable seeded database:
**0 errors, 40 warnings** (existing general catalogue links, chiefly bare roots).
Academy source URLs are now included in that check. An initial invocation against
an unseeded default database failed with “no such table: resources”; rerunning
against the intended seeded review database passed. No checker behavior was
weakened to suppress that setup error.

Official language-documentation hosts are outside the environment's outbound
allowlist. Source URLs were structurally checked, but live availability and
current document contents were **not** fetched or independently certified.

## Browser/mobile/keyboard verification

`LD_LIBRARY_PATH=/tmp/al2023/lib node scripts/check_academy_browser.js`
against a no-demo development catalogue, optional browsing and judge disabled:

- Chromium 141 with Playwright Core 1.56.1; widths **1440, 768, 390**.
- No document-level horizontal overflow at those widths.
- Keyboard Tab → Enter records a local attempted approach; Enter on the focused
  summary opens the reference. Reset clears code and closes/hides the reference.
- Trace stepping highlights one row and announces the current step.
- Course filtering gives one, zero and all matching modules as expected.
- With JavaScript disabled, all trace rows and the native reference disclosure
  remain available; no execution capability is implied.
- No non-GET requests during local practice; no browser JavaScript errors.
- Final browser smoke rerun passed after the sticky-TOC offset adjustment.

The first browser launch failed because the minimal host lacked NSS/NSPR. The
optional Chromium npm package includes those libraries; its bundled archive was
extracted to `/tmp/al2023`, and the QA process used LD_LIBRARY_PATH. No application
security setting or dependency was changed. Development browser tools remain
ignored under `.toolchain/browser`.

Screenshots (actual rendered pages, not generated mockups):

- [Desktop, 1440px](images/academy-1440.png)
- [Mobile, 390px](images/academy-390.png)

This is a functional smoke test, not a complete WCAG or screen-reader audit.
Dark-mode contrast, every browser/assistive technology and every long legacy
lesson still need broader manual review.

## Security/privacy review and limits

- No new public execution service, eval, dynamic Function, network request or
  draft storage in academy.js. Production judge defaults/security are unchanged.
- Read-only lesson routes inherit existing compulsory/optional sign-in policy;
  module lookup is parameterized and language-scoped.
- Content Markdown and code-color formatting escape untrusted text. Only fixed
  formatting spans are emitted; injected HTML is covered by tests.
- Migration adds one nullable field; targeted content update keeps module ids,
  account records, submissions, bookmarks and progress. Production backup and
  explicit content-replacement approval remain required.
- Existing static exports publish references intentionally. The attempt gate is
  pedagogical and cannot protect public reference source from inspection.
- Existing external judge infrastructure was inspected, not penetration-tested
  or certified. Do not enable a public runner based on these content tests.
- No exhaustive module mastery, per-language problem bank, adaptive persistence
  or expanded project ladder is claimed complete; see the follow-up checklist.
