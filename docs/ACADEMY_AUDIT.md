# Programming academy audit and implementation boundary

Audit: 2026-10-15, baseline `813f02a`. The working tree was clean; GitHub's
remote HEAD is `main`. This session works on `arena/91583572-engineverse`.

## Architecture inspected

- FastAPI routes in `backend/web/{pages,api,auth_pages}.py`, Jinja templates,
  locally served CSS/vanilla JavaScript. No Node application or frontend build.
- SQLite development; PostgreSQL production schema is generated from
  `db/schema.sql`. `engineverse.db.migrate` supports additive upgrades.
- Password authentication, signed sessions, optional OTP/MFA, CSRF, RBAC and
  rate limits already exist. Preserve them; no new authentication system.
- `seed_data/language_foundations.py`, `library_data.py`, `language_paths.py`
  and seven language-book files feed `scripts/seed.py`. Existing tables are
  `programming_languages`, `language_modules`, `language_stages`,
  `language_checkpoints`, coding banks, projects and learner records.
- 225 modules: Python 35, Java 31, JavaScript 23, TypeScript 16, C++ 27,
  Go 17, Rust 17, C 26, C# 18, SQL 15. Three stages per path, 90 stage
  checkpoint questions, 105 problems and ten language-linked capstone briefs.
  These are inventory counts, not proof of comprehensive instruction.
- GitHub Pages exports the public catalogue using `scripts/export_pages.py`;
  it has no backend, accounts, compiler or cross-device persistence.
  Self-hosted releases use `scripts/release.py` and Docker deployment files.
- Tests: `python -m pytest`; CI also checks links, reference problems, schemas,
  static exports, scenes and Java service tests. Python dependencies are pinned
  in `requirements.txt`. Installed them in ignored `.venv` (system Python is
  externally managed). Baseline full Python suite passed; a Starlette/httpx
  deprecation warning exists before this change.

## Educational and UX findings

- All modules render inline on a single language page; advanced paths are long,
  lack a lesson TOC, and have no focused previous/next reader.
- Modules have body/example/exercise, not a validated A–O learning-unit schema.
  Stage quizzes are genuine server-graded questions, but do not prove each
  individual subtopic. Most modules lack progressive hints, execution traces,
  precise independent specifications and per-objective mastery rubrics.
- Problem availability is uneven: many algorithm problems only have Python
  starters. A module's generic practice link is not evidence that a matching
  implementation exists in that language. C# and SQL have no local judge key.
- Example: Python's complexity lesson wrongly equates Big-O with worst case;
  a duplicated template claim also appears in other books. Big-O is an upper
  bound on a chosen cost function, not a case selection. Absolute string
  concatenation performance statements also require qualification.
- The README's “full book depth” overstates verified completeness. Existing
  authored content should be preserved, labelled as legacy where it has not
  been upgraded, and expanded incrementally rather than counted as complete.
- Content link checks are structural/offline here. Official documentation hosts
  are outside this environment's outbound allowlist; live reference content
  and availability cannot be certified in this change.

## Execution and privacy boundary

The judge facade supports disabled, local development, Java-service and Judge0
providers. Production defaults to disabled; unsafe local/auto modes are refused
in production. Local namespace/resource checks fail closed. A separate process
alone is not a production isolation guarantee; production deployments must
review their external runner. Do not enable a new public executor here.

Existing user progress is topic-keyed, not language-module-keyed. Coding attempts
and checkpoint answers already persist per account. Do not misrepresent a local
self-review as a graded mastery event, or seed over production user records.
The seed tool upserts seeded content ids (overwriting CMS edits); --fresh
resets the database. Neither should be used casually as a production content
refresh. Document a narrowly scoped academy update instead.

## Plan / scope for this review

1. Extend existing language modules with optional structured lesson JSON through
   an additive migration. Validate authored units and preserve legacy fallback.
2. Provide a focused reader, TOC, language-specific examples, traces, progressive
   hints and attempt-before-reference local practice without executing code.
3. Upgrade an initial unit for **every** existing language and priority-language
   complexity units. Publish a seven-level syllabus/coverage map that separates
   authored units from expansion work. No complete-course claim.
4. Preserve old fragment URLs, stage quizzes, coding routes and projects;
   export the new reader routes to Pages and include them in the sitemap.
5. Verify trusted authored examples with available local toolchains, test schema,
   navigation, escaping, migration, static export and existing security policies.
6. Document actual checks, missing tools and follow-up work; open an unmerged PR.

Not delivered in this increment: exhaustive A–O treatment of all 225 modules,
complete per-language problem banks, new production runner, adaptive module
mastery persistence, timed interview grading or multi-level project acceptance
suites. Existing features remain available; these are explicit follow-up tasks.
