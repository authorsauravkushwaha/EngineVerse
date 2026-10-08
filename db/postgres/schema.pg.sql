-- ===========================================================================
--  EngineVerse - production relational schema (PostgreSQL 16+)
--  ---------------------------------------------------------------------------
--  GENERATED FILE. Do not edit by hand.
--
--  Written by scripts/gen_pg_schema.py from db/schema.sql, which is the single
--  source of truth. Regenerate with:
--
--      python scripts/gen_pg_schema.py
--
--  CI runs `python scripts/gen_pg_schema.py --check` and fails if this file is
--  out of date, so the two schemas cannot diverge silently. They did once: 47
--  of 66 shared tables had drifted, and certificates was missing kind,
--  entity_type and entity_id, which the application inserts on every issue.
--
--  What differs from the SQLite DDL, and why:
--    * INTEGER -> BIGINT, REAL -> DOUBLE PRECISION.
--    * email/username -> CITEXT, so uniqueness ignores case.
--    * JSON payloads stay TEXT, not jsonb: psycopg hands back a dict for jsonb
--      and every reader here calls json.loads(), so jsonb would break them.
--    * The FTS5 virtual table becomes a table with a generated tsvector + GIN.
--    * High-volume tables are hash-partitioned. Postgres requires the partition
--      key inside the primary key and every unique constraint, so tables with a
--      lone `id` primary key get a composite (id, user_id) primary key here.
--
--  sessions and certificates are NOT partitioned: each carries a globally
--  unique lookup column (token_hash, verify_id) that does not include a
--  sensible partition key, and dropping that uniqueness would weaken the
--  security model.
--
--  Partition counts assume ~1.5e9 users and keep the largest single partition
--  in the low tens of millions of rows.
--
--  Apply with:  psql "$ENGINEVERSE_DB_URL" -f db/postgres/schema.pg.sql
--  The script is idempotent.
-- ===========================================================================

SET client_min_messages TO WARNING;

CREATE EXTENSION IF NOT EXISTS citext;   -- case-insensitive email/username
CREATE EXTENSION IF NOT EXISTS pgcrypto; -- gen_random_bytes, digests


CREATE TABLE IF NOT EXISTS users (
  id                   TEXT NOT NULL,
  email                CITEXT NOT NULL UNIQUE,
  username             CITEXT NOT NULL UNIQUE,
  password_hash        TEXT NOT NULL,
  role                 TEXT NOT NULL DEFAULT 'student',
  status               TEXT NOT NULL DEFAULT 'active',
  email_verified       BIGINT NOT NULL DEFAULT 0,
  failed_login_count   BIGINT NOT NULL DEFAULT 0,
  locked_until         BIGINT,
  password_changed_at  BIGINT NOT NULL,
  totp_secret          TEXT,
  created_at           BIGINT NOT NULL,
  updated_at           BIGINT NOT NULL,
  deleted_at           BIGINT,
  PRIMARY KEY (id)
);

CREATE TABLE IF NOT EXISTS user_roles (
  user_id              TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  role                 TEXT NOT NULL,
  granted_by           TEXT,
  granted_at           BIGINT NOT NULL,
  PRIMARY KEY (user_id, role)
);

CREATE TABLE IF NOT EXISTS profiles (
  user_id              TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  full_name            TEXT NOT NULL,
  avatar_seed          TEXT,
  headline             TEXT,
  bio                  TEXT,
  country              TEXT,
  university_id        TEXT REFERENCES universities(id) ON DELETE SET NULL,
  college_id           TEXT REFERENCES colleges(id) ON DELETE SET NULL,
  branch_id            TEXT REFERENCES branches(id) ON DELETE SET NULL,
  semester_id          BIGINT REFERENCES semesters(id) ON DELETE SET NULL,
  skill_level          TEXT NOT NULL DEFAULT 'beginner',
  career_goal          TEXT,
  programming_xp       TEXT NOT NULL DEFAULT 'none',
  weekly_study_hours   BIGINT NOT NULL DEFAULT 7,
  language_pref        TEXT NOT NULL DEFAULT 'en',
  note_quality         TEXT NOT NULL DEFAULT 'standard',
  github_url           TEXT,
  linkedin_url         TEXT,
  portfolio_url        TEXT,
  skills               TEXT NOT NULL DEFAULT '[]',
  privacy              TEXT NOT NULL DEFAULT '{}',
  notification_prefs   TEXT NOT NULL DEFAULT '{}',
  onboarded_at         BIGINT,
  updated_at           BIGINT NOT NULL,
  PRIMARY KEY (user_id)
) PARTITION BY HASH (user_id);

CREATE TABLE IF NOT EXISTS sessions (
  id                   TEXT NOT NULL,
  token_hash           TEXT NOT NULL UNIQUE,
  user_id              TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  created_at           BIGINT NOT NULL,
  expires_at           BIGINT NOT NULL,
  last_seen_at         BIGINT NOT NULL,
  ip                   TEXT,
  user_agent           TEXT,
  revoked_at           BIGINT,
  PRIMARY KEY (id)
);

CREATE TABLE IF NOT EXISTS password_resets (
  token_hash           TEXT NOT NULL,
  user_id              TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  created_at           BIGINT NOT NULL,
  expires_at           BIGINT NOT NULL,
  used_at              BIGINT,
  ip                   TEXT,
  PRIMARY KEY (token_hash)
);

CREATE TABLE IF NOT EXISTS login_attempts (
  id                   TEXT NOT NULL,
  identifier           TEXT NOT NULL,
  ip                   TEXT NOT NULL,
  success              BIGINT NOT NULL,
  reason               TEXT,
  created_at           BIGINT NOT NULL,
  PRIMARY KEY (id)
) PARTITION BY HASH (id);

CREATE TABLE IF NOT EXISTS api_rate_limits (
  bucket               TEXT NOT NULL,
  count                BIGINT NOT NULL DEFAULT 0,
  window_start         BIGINT NOT NULL,
  PRIMARY KEY (bucket)
) PARTITION BY HASH (bucket);

CREATE TABLE IF NOT EXISTS audit_logs (
  id                   TEXT NOT NULL,
  actor_id             TEXT,
  action               TEXT NOT NULL,
  entity_type          TEXT,
  entity_id            TEXT,
  meta                 TEXT NOT NULL DEFAULT '{}',
  ip                   TEXT,
  created_at           BIGINT NOT NULL,
  PRIMARY KEY (id)
) PARTITION BY HASH (id);

CREATE TABLE IF NOT EXISTS universities (
  id                   TEXT NOT NULL,
  name                 TEXT NOT NULL,
  code                 TEXT,
  country              TEXT NOT NULL,
  region               TEXT,
  website              TEXT,
  created_at           BIGINT NOT NULL,
  PRIMARY KEY (id)
);

CREATE TABLE IF NOT EXISTS colleges (
  id                   TEXT NOT NULL,
  university_id        TEXT REFERENCES universities(id) ON DELETE SET NULL,
  name                 TEXT NOT NULL,
  city                 TEXT,
  country              TEXT NOT NULL,
  PRIMARY KEY (id)
);

CREATE TABLE IF NOT EXISTS branches (
  id                   TEXT NOT NULL,
  slug                 TEXT NOT NULL UNIQUE,
  name                 TEXT NOT NULL,
  category             TEXT NOT NULL,
  description          TEXT,
  icon                 TEXT,
  color                TEXT,
  order_index          BIGINT NOT NULL DEFAULT 0,
  parent_id            TEXT REFERENCES branches(id) ON DELETE SET NULL,
  is_active            BIGINT NOT NULL DEFAULT 1,
  PRIMARY KEY (id)
);

CREATE TABLE IF NOT EXISTS semesters (
  id                   BIGINT NOT NULL,
  label                TEXT NOT NULL,
  year                 BIGINT,
  PRIMARY KEY (id)
);

CREATE TABLE IF NOT EXISTS curricula (
  id                   TEXT NOT NULL,
  university_id        TEXT NOT NULL REFERENCES universities(id) ON DELETE CASCADE,
  branch_id            TEXT NOT NULL REFERENCES branches(id) ON DELETE CASCADE,
  name                 TEXT NOT NULL,
  effective_year       BIGINT NOT NULL DEFAULT 2024,
  is_active            BIGINT NOT NULL DEFAULT 1,
  UNIQUE (university_id, branch_id, effective_year),
  PRIMARY KEY (id)
);

CREATE TABLE IF NOT EXISTS curriculum_subjects (
  curriculum_id        TEXT NOT NULL REFERENCES curricula(id) ON DELETE CASCADE,
  subject_id           TEXT NOT NULL REFERENCES subjects(id) ON DELETE CASCADE,
  semester_id          BIGINT NOT NULL REFERENCES semesters(id) ON DELETE SET NULL,
  is_core              BIGINT NOT NULL DEFAULT 1,
  PRIMARY KEY (curriculum_id, subject_id)
);

CREATE TABLE IF NOT EXISTS subjects (
  id                   TEXT NOT NULL,
  slug                 TEXT NOT NULL UNIQUE,
  name                 TEXT NOT NULL,
  branch_id            TEXT REFERENCES branches(id) ON DELETE SET NULL,
  semester_id          BIGINT REFERENCES semesters(id) ON DELETE SET NULL,
  code                 TEXT,
  credits              BIGINT,
  difficulty           TEXT NOT NULL DEFAULT 'medium',
  description          TEXT,
  icon                 TEXT,
  color                TEXT,
  is_first_year        BIGINT NOT NULL DEFAULT 0,
  order_index          BIGINT NOT NULL DEFAULT 0,
  status               TEXT NOT NULL DEFAULT 'published',
  PRIMARY KEY (id)
);

CREATE TABLE IF NOT EXISTS modules (
  id                   TEXT NOT NULL,
  subject_id           TEXT NOT NULL REFERENCES subjects(id) ON DELETE CASCADE,
  slug                 TEXT NOT NULL,
  title                TEXT NOT NULL,
  summary              TEXT,
  order_index          BIGINT NOT NULL DEFAULT 0,
  UNIQUE (subject_id, slug),
  PRIMARY KEY (id)
);

CREATE TABLE IF NOT EXISTS topics (
  id                   TEXT NOT NULL,
  slug                 TEXT NOT NULL UNIQUE,
  subject_id           TEXT NOT NULL REFERENCES subjects(id) ON DELETE CASCADE,
  module_id            TEXT REFERENCES modules(id) ON DELETE SET NULL,
  title                TEXT NOT NULL,
  summary              TEXT,
  difficulty           TEXT NOT NULL DEFAULT 'medium',
  est_minutes          BIGINT NOT NULL DEFAULT 20,
  order_index          BIGINT NOT NULL DEFAULT 0,
  prerequisites        TEXT NOT NULL DEFAULT '[]',
  tags                 TEXT NOT NULL DEFAULT '[]',
  status               TEXT NOT NULL DEFAULT 'published',
  author_id            TEXT REFERENCES users(id) ON DELETE SET NULL,
  reviewer_id          TEXT REFERENCES users(id) ON DELETE SET NULL,
  accuracy_state       TEXT NOT NULL DEFAULT 'reviewed',
  source_ref           TEXT,
  version              BIGINT NOT NULL DEFAULT 1,
  view_count           BIGINT NOT NULL DEFAULT 0,
  created_at           BIGINT NOT NULL,
  updated_at           BIGINT NOT NULL,
  PRIMARY KEY (id)
);

CREATE TABLE IF NOT EXISTS notes (
  id                   TEXT NOT NULL,
  topic_id             TEXT NOT NULL REFERENCES topics(id) ON DELETE CASCADE,
  quality_level        TEXT NOT NULL DEFAULT 'standard',
  language             TEXT NOT NULL DEFAULT 'en',
  status               TEXT NOT NULL DEFAULT 'published',
  author_id            TEXT REFERENCES users(id) ON DELETE SET NULL,
  reviewer_id          TEXT REFERENCES users(id) ON DELETE SET NULL,
  version              BIGINT NOT NULL DEFAULT 1,
  created_at           BIGINT NOT NULL,
  updated_at           BIGINT NOT NULL,
  UNIQUE (topic_id, quality_level, language),
  PRIMARY KEY (id)
);

CREATE TABLE IF NOT EXISTS note_sections (
  id                   TEXT NOT NULL,
  note_id              TEXT NOT NULL REFERENCES notes(id) ON DELETE CASCADE,
  kind                 TEXT NOT NULL,
  title                TEXT NOT NULL,
  body                 TEXT NOT NULL,
  callout              TEXT,
  order_index          BIGINT NOT NULL DEFAULT 0,
  PRIMARY KEY (id)
);

CREATE TABLE IF NOT EXISTS diagrams (
  id                   TEXT NOT NULL,
  topic_id             TEXT NOT NULL REFERENCES topics(id) ON DELETE CASCADE,
  title                TEXT NOT NULL,
  kind                 TEXT NOT NULL DEFAULT 'svg',
  spec                 TEXT NOT NULL,
  caption              TEXT,
  hotspots             TEXT NOT NULL DEFAULT '[]',
  source_ref           TEXT,
  created_at           BIGINT NOT NULL,
  PRIMARY KEY (id)
);

CREATE TABLE IF NOT EXISTS models_3d (
  id                   TEXT NOT NULL,
  topic_id             TEXT NOT NULL REFERENCES topics(id) ON DELETE CASCADE,
  title                TEXT NOT NULL,
  caption              TEXT,
  scene                TEXT NOT NULL,
  source_ref           TEXT,
  order_index          BIGINT NOT NULL DEFAULT 0,
  created_at           BIGINT NOT NULL,
  PRIMARY KEY (id)
);

CREATE TABLE IF NOT EXISTS formulas (
  id                   TEXT NOT NULL,
  slug                 TEXT NOT NULL UNIQUE,
  subject_id           TEXT REFERENCES subjects(id) ON DELETE SET NULL,
  topic_id             TEXT REFERENCES topics(id) ON DELETE CASCADE,
  category             TEXT NOT NULL,
  name                 TEXT NOT NULL,
  latex                TEXT NOT NULL,
  variables            TEXT NOT NULL DEFAULT '[]',
  meaning              TEXT,
  application          TEXT,
  example_latex        TEXT,
  constraints          TEXT,
  order_index          BIGINT NOT NULL DEFAULT 0,
  PRIMARY KEY (id)
);

CREATE TABLE IF NOT EXISTS questions (
  id                   TEXT NOT NULL,
  slug                 TEXT NOT NULL UNIQUE,
  topic_id             TEXT REFERENCES topics(id) ON DELETE SET NULL,
  subject_id           TEXT REFERENCES subjects(id) ON DELETE SET NULL,
  kind                 TEXT NOT NULL,
  difficulty           TEXT NOT NULL DEFAULT 'medium',
  stem                 TEXT NOT NULL,
  context              TEXT,
  explanation          TEXT,
  answer_index         BIGINT,
  answer_text          TEXT,
  tolerance            DOUBLE PRECISION,
  code_language        TEXT,
  starter_code         TEXT,
  time_weight          BIGINT NOT NULL DEFAULT 1,
  tags                 TEXT NOT NULL DEFAULT '[]',
  author_id            TEXT REFERENCES users(id) ON DELETE SET NULL,
  is_active            BIGINT NOT NULL DEFAULT 1,
  created_at           BIGINT NOT NULL,
  PRIMARY KEY (id)
);

CREATE TABLE IF NOT EXISTS question_options (
  id                   TEXT NOT NULL,
  question_id          TEXT NOT NULL REFERENCES questions(id) ON DELETE CASCADE,
  label                TEXT NOT NULL,
  body                 TEXT NOT NULL,
  is_correct           BIGINT NOT NULL DEFAULT 0,
  rationale            TEXT,
  order_index          BIGINT NOT NULL DEFAULT 0,
  PRIMARY KEY (id)
);

CREATE TABLE IF NOT EXISTS dpp_sets (
  id                   TEXT NOT NULL,
  date                 TEXT NOT NULL UNIQUE,
  title                TEXT NOT NULL,
  subject_id           TEXT REFERENCES subjects(id) ON DELETE SET NULL,
  difficulty           TEXT NOT NULL DEFAULT 'mixed',
  duration_minutes     BIGINT NOT NULL DEFAULT 30,
  published            BIGINT NOT NULL DEFAULT 1,
  created_at           BIGINT NOT NULL,
  PRIMARY KEY (id)
);

CREATE TABLE IF NOT EXISTS dpp_questions (
  set_id               TEXT NOT NULL REFERENCES dpp_sets(id) ON DELETE CASCADE,
  question_id          TEXT NOT NULL REFERENCES questions(id) ON DELETE CASCADE,
  position             BIGINT NOT NULL,
  PRIMARY KEY (set_id, question_id)
);

CREATE TABLE IF NOT EXISTS submissions (
  id                   TEXT NOT NULL,
  user_id              TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  question_id          TEXT NOT NULL REFERENCES questions(id) ON DELETE CASCADE,
  dpp_set_id           TEXT REFERENCES dpp_sets(id) ON DELETE SET NULL,
  answer_index         BIGINT,
  answer_text          TEXT,
  is_correct           BIGINT NOT NULL,
  time_ms              BIGINT,
  created_at           BIGINT NOT NULL,
  PRIMARY KEY (id, user_id)
) PARTITION BY HASH (user_id);

CREATE TABLE IF NOT EXISTS mistakes (
  id                   TEXT NOT NULL,
  user_id              TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  question_id          TEXT NOT NULL REFERENCES questions(id) ON DELETE CASCADE,
  given                TEXT,
  correct              TEXT,
  resolved_at          BIGINT,
  created_at           BIGINT NOT NULL,
  UNIQUE (user_id, question_id),
  PRIMARY KEY (id, user_id)
) PARTITION BY HASH (user_id);

CREATE TABLE IF NOT EXISTS programming_languages (
  id                   TEXT NOT NULL,
  slug                 TEXT NOT NULL UNIQUE,
  name                 TEXT NOT NULL,
  icon                 TEXT,
  color                TEXT,
  blurb                TEXT,
  judge_slug           TEXT,
  runnable             BIGINT NOT NULL DEFAULT 1,
  order_index          BIGINT NOT NULL DEFAULT 0,
  PRIMARY KEY (id)
);

CREATE TABLE IF NOT EXISTS language_modules (
  id                   TEXT NOT NULL,
  language_id          TEXT NOT NULL REFERENCES programming_languages(id) ON DELETE CASCADE,
  slug                 TEXT NOT NULL,
  title                TEXT NOT NULL,
  summary              TEXT,
  body                 TEXT NOT NULL,
  example              TEXT,
  exercise             TEXT,
  order_index          BIGINT NOT NULL DEFAULT 0,
  UNIQUE (language_id, slug),
  PRIMARY KEY (id)
);

CREATE TABLE IF NOT EXISTS coding_problems (
  id                   TEXT NOT NULL,
  slug                 TEXT NOT NULL UNIQUE,
  title                TEXT NOT NULL,
  statement            TEXT NOT NULL,
  difficulty           TEXT NOT NULL DEFAULT 'medium',
  topics               TEXT NOT NULL DEFAULT '[]',
  hints                TEXT NOT NULL DEFAULT '[]',
  editorial            TEXT,
  solution_md          TEXT,
  tags                 TEXT NOT NULL DEFAULT '[]',
  expected_time        TEXT,
  expected_space       TEXT,
  wrapper              TEXT NOT NULL DEFAULT 'raw',
  solve_count          BIGINT NOT NULL DEFAULT 0,
  attempt_count        BIGINT NOT NULL DEFAULT 0,
  is_premium           BIGINT NOT NULL DEFAULT 0,
  created_at           BIGINT NOT NULL,
  PRIMARY KEY (id)
);

CREATE TABLE IF NOT EXISTS coding_problem_stubs (
  problem_id           TEXT NOT NULL REFERENCES coding_problems(id) ON DELETE CASCADE,
  language_id          TEXT NOT NULL REFERENCES programming_languages(id) ON DELETE CASCADE,
  stub                 TEXT NOT NULL,
  signature            TEXT,
  PRIMARY KEY (problem_id, language_id)
);

CREATE TABLE IF NOT EXISTS coding_testcases (
  id                   TEXT NOT NULL,
  problem_id           TEXT NOT NULL REFERENCES coding_problems(id) ON DELETE CASCADE,
  input                TEXT NOT NULL DEFAULT '',
  expected             TEXT NOT NULL,
  is_sample            BIGINT NOT NULL DEFAULT 0,
  explanation          TEXT,
  order_index          BIGINT NOT NULL DEFAULT 0,
  PRIMARY KEY (id)
);

CREATE TABLE IF NOT EXISTS coding_submissions (
  id                   TEXT NOT NULL,
  user_id              TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  problem_id           TEXT NOT NULL REFERENCES coding_problems(id) ON DELETE CASCADE,
  language             TEXT NOT NULL,
  code                 TEXT NOT NULL,
  status               TEXT NOT NULL,
  passed               BIGINT NOT NULL DEFAULT 0,
  total                BIGINT NOT NULL DEFAULT 0,
  runtime_ms           BIGINT,
  memory_kb            BIGINT,
  stderr               TEXT,
  is_accepted          BIGINT NOT NULL DEFAULT 0,
  created_at           BIGINT NOT NULL,
  PRIMARY KEY (id, user_id)
) PARTITION BY HASH (user_id);

CREATE TABLE IF NOT EXISTS projects (
  id                   TEXT NOT NULL,
  slug                 TEXT NOT NULL UNIQUE,
  title                TEXT NOT NULL,
  branch_id            TEXT REFERENCES branches(id) ON DELETE SET NULL,
  subject_id           TEXT REFERENCES subjects(id) ON DELETE SET NULL,
  difficulty           TEXT NOT NULL DEFAULT 'intermediate',
  category             TEXT NOT NULL DEFAULT 'software',
  est_hours            BIGINT NOT NULL DEFAULT 20,
  summary              TEXT,
  problem_statement    TEXT,
  objective            TEXT,
  prerequisites        TEXT NOT NULL DEFAULT '[]',
  hardware             TEXT,
  software             TEXT,
  architecture         TEXT,
  source_code          TEXT,
  database_design      TEXT,
  testing              TEXT,
  expected_output      TEXT,
  improvements         TEXT,
  resume_md            TEXT,
  interview_questions  TEXT NOT NULL DEFAULT '[]',
  tech                 TEXT NOT NULL DEFAULT '[]',
  skills               TEXT NOT NULL DEFAULT '[]',
  repo_url             TEXT,
  demo_url             TEXT,
  report_template_url  TEXT,
  build_count          BIGINT NOT NULL DEFAULT 0,
  status               TEXT NOT NULL DEFAULT 'published',
  order_index          BIGINT NOT NULL DEFAULT 0,
  created_at           BIGINT NOT NULL,
  PRIMARY KEY (id)
);

CREATE TABLE IF NOT EXISTS project_steps (
  id                   TEXT NOT NULL,
  project_id           TEXT NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
  phase                TEXT NOT NULL,
  title                TEXT NOT NULL,
  body                 TEXT NOT NULL,
  order_index          BIGINT NOT NULL DEFAULT 0,
  PRIMARY KEY (id)
);

CREATE TABLE IF NOT EXISTS project_resources (
  id                   TEXT NOT NULL,
  project_id           TEXT NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
  kind                 TEXT NOT NULL,
  title                TEXT NOT NULL,
  url                  TEXT,
  note                 TEXT,
  PRIMARY KEY (id)
);

CREATE TABLE IF NOT EXISTS videos (
  id                   TEXT NOT NULL,
  slug                 TEXT NOT NULL UNIQUE,
  title                TEXT NOT NULL,
  channel              TEXT NOT NULL,
  url                  TEXT NOT NULL,
  embed_id             TEXT,
  duration_s           BIGINT,
  language             TEXT NOT NULL DEFAULT 'en',
  level                TEXT NOT NULL DEFAULT 'beginner',
  category             TEXT NOT NULL DEFAULT 'concept',
  topic_id             TEXT REFERENCES topics(id) ON DELETE SET NULL,
  subject_id           TEXT REFERENCES subjects(id) ON DELETE SET NULL,
  rating               BIGINT NOT NULL DEFAULT 4,
  why_useful           TEXT,
  embeddable           BIGINT NOT NULL DEFAULT 1,
  created_at           BIGINT NOT NULL,
  PRIMARY KEY (id)
);

CREATE TABLE IF NOT EXISTS books (
  id                   TEXT NOT NULL,
  slug                 TEXT NOT NULL UNIQUE,
  title                TEXT NOT NULL,
  author               TEXT NOT NULL,
  subject_id           TEXT REFERENCES subjects(id) ON DELETE SET NULL,
  branch_id            TEXT REFERENCES branches(id) ON DELETE SET NULL,
  level                TEXT NOT NULL DEFAULT 'undergraduate',
  description          TEXT,
  why_read             TEXT,
  topics_covered       TEXT NOT NULL DEFAULT '[]',
  legal_url            TEXT NOT NULL,
  access_kind          TEXT NOT NULL DEFAULT 'official',
  publisher            TEXT,
  created_at           BIGINT NOT NULL,
  PRIMARY KEY (id)
);

CREATE TABLE IF NOT EXISTS resources (
  id                   TEXT NOT NULL,
  slug                 TEXT NOT NULL UNIQUE,
  title                TEXT NOT NULL,
  url                  TEXT NOT NULL,
  kind                 TEXT NOT NULL,
  category             TEXT NOT NULL DEFAULT 'documentation',
  branch_id            TEXT REFERENCES branches(id) ON DELETE SET NULL,
  subject_id           TEXT REFERENCES subjects(id) ON DELETE SET NULL,
  level                TEXT NOT NULL DEFAULT 'beginner',
  format               TEXT NOT NULL DEFAULT 'web',
  language             TEXT NOT NULL DEFAULT 'en',
  is_free              BIGINT NOT NULL DEFAULT 1,
  description          TEXT,
  created_at           BIGINT NOT NULL,
  PRIMARY KEY (id)
);

CREATE TABLE IF NOT EXISTS roadmaps (
  id                   TEXT NOT NULL,
  slug                 TEXT NOT NULL UNIQUE,
  title                TEXT NOT NULL,
  kind                 TEXT NOT NULL DEFAULT 'subject',
  branch_id            TEXT REFERENCES branches(id) ON DELETE SET NULL,
  target_role          TEXT,
  summary              TEXT,
  description          TEXT,
  order_index          BIGINT NOT NULL DEFAULT 0,
  PRIMARY KEY (id)
);

CREATE TABLE IF NOT EXISTS roadmap_nodes (
  id                   TEXT NOT NULL,
  roadmap_id           TEXT NOT NULL REFERENCES roadmaps(id) ON DELETE CASCADE,
  title                TEXT NOT NULL,
  summary              TEXT,
  ref_type             TEXT,
  ref_id               TEXT,
  is_required          BIGINT NOT NULL DEFAULT 1,
  order_index          BIGINT NOT NULL DEFAULT 0,
  PRIMARY KEY (id)
);

CREATE TABLE IF NOT EXISTS flashcards (
  id                   TEXT NOT NULL,
  topic_id             TEXT REFERENCES topics(id) ON DELETE CASCADE,
  subject_id           TEXT REFERENCES subjects(id) ON DELETE SET NULL,
  deck                 TEXT NOT NULL DEFAULT 'core',
  front                TEXT NOT NULL,
  back                 TEXT NOT NULL,
  hint                 TEXT,
  difficulty           TEXT NOT NULL DEFAULT 'medium',
  created_at           BIGINT NOT NULL,
  PRIMARY KEY (id)
);

CREATE TABLE IF NOT EXISTS user_flashcards (
  user_id              TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  flashcard_id         TEXT NOT NULL REFERENCES flashcards(id) ON DELETE CASCADE,
  ease_factor          DOUBLE PRECISION NOT NULL DEFAULT 2.5,
  interval_days        DOUBLE PRECISION NOT NULL DEFAULT 0,
  repetitions          BIGINT NOT NULL DEFAULT 0,
  due_at               BIGINT NOT NULL,
  last_reviewed_at     BIGINT,
  PRIMARY KEY (user_id, flashcard_id)
) PARTITION BY HASH (user_id);

CREATE TABLE IF NOT EXISTS user_progress (
  user_id              TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  topic_id             TEXT NOT NULL REFERENCES topics(id) ON DELETE CASCADE,
  status               TEXT NOT NULL DEFAULT 'started',
  mastery              BIGINT NOT NULL DEFAULT 0,
  time_spent_s         BIGINT NOT NULL DEFAULT 0,
  last_viewed_at       BIGINT NOT NULL,
  completed_at         BIGINT,
  PRIMARY KEY (user_id, topic_id)
) PARTITION BY HASH (user_id);

CREATE TABLE IF NOT EXISTS bookmarks (
  user_id              TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  entity_type          TEXT NOT NULL,
  entity_id            TEXT NOT NULL,
  note                 TEXT,
  created_at           BIGINT NOT NULL,
  PRIMARY KEY (user_id, entity_type, entity_id)
) PARTITION BY HASH (user_id);

CREATE TABLE IF NOT EXISTS personal_notes (
  id                   TEXT NOT NULL,
  user_id              TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  entity_type          TEXT NOT NULL DEFAULT 'topic',
  entity_id            TEXT NOT NULL,
  content              TEXT NOT NULL,
  is_private           BIGINT NOT NULL DEFAULT 1,
  created_at           BIGINT NOT NULL,
  updated_at           BIGINT NOT NULL,
  PRIMARY KEY (id, user_id)
) PARTITION BY HASH (user_id);

CREATE TABLE IF NOT EXISTS xp_events (
  id                   TEXT NOT NULL,
  user_id              TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  amount               BIGINT NOT NULL,
  reason               TEXT NOT NULL,
  entity_type          TEXT,
  entity_id            TEXT,
  created_at           BIGINT NOT NULL,
  PRIMARY KEY (id, user_id)
) PARTITION BY HASH (user_id);

CREATE TABLE IF NOT EXISTS streaks (
  user_id              TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  current_streak       BIGINT NOT NULL DEFAULT 0,
  longest_streak       BIGINT NOT NULL DEFAULT 0,
  last_active_day      TEXT,
  freeze_count         BIGINT NOT NULL DEFAULT 0,
  total_xp             BIGINT NOT NULL DEFAULT 0,
  level                BIGINT NOT NULL DEFAULT 1,
  PRIMARY KEY (user_id)
) PARTITION BY HASH (user_id);

CREATE TABLE IF NOT EXISTS activity (
  user_id              TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  day                  TEXT NOT NULL,
  notes_studied        BIGINT NOT NULL DEFAULT 0,
  questions_solved     BIGINT NOT NULL DEFAULT 0,
  coding_submissions   BIGINT NOT NULL DEFAULT 0,
  projects_touched     BIGINT NOT NULL DEFAULT 0,
  revisions            BIGINT NOT NULL DEFAULT 0,
  minutes              BIGINT NOT NULL DEFAULT 0,
  xp                   BIGINT NOT NULL DEFAULT 0,
  PRIMARY KEY (user_id, day)
) PARTITION BY HASH (user_id);

CREATE TABLE IF NOT EXISTS badges (
  id                   TEXT NOT NULL,
  slug                 TEXT NOT NULL UNIQUE,
  name                 TEXT NOT NULL,
  description          TEXT NOT NULL,
  icon                 TEXT NOT NULL DEFAULT 'award',
  tier                 TEXT NOT NULL DEFAULT 'bronze',
  criterion            TEXT NOT NULL,
  PRIMARY KEY (id)
);

CREATE TABLE IF NOT EXISTS user_badges (
  user_id              TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  badge_id             TEXT NOT NULL REFERENCES badges(id) ON DELETE CASCADE,
  earned_at            BIGINT NOT NULL,
  PRIMARY KEY (user_id, badge_id)
) PARTITION BY HASH (user_id);

CREATE TABLE IF NOT EXISTS discussions (
  id                   TEXT NOT NULL,
  user_id              TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  title                TEXT NOT NULL,
  body                 TEXT NOT NULL,
  kind                 TEXT NOT NULL DEFAULT 'question',
  tags                 TEXT NOT NULL DEFAULT '[]',
  entity_type          TEXT,
  entity_id            TEXT,
  upvotes              BIGINT NOT NULL DEFAULT 0,
  reply_count          BIGINT NOT NULL DEFAULT 0,
  is_resolved          BIGINT NOT NULL DEFAULT 0,
  is_locked            BIGINT NOT NULL DEFAULT 0,
  is_hidden            BIGINT NOT NULL DEFAULT 0,
  created_at           BIGINT NOT NULL,
  last_activity_at     BIGINT NOT NULL,
  PRIMARY KEY (id, user_id)
) PARTITION BY HASH (user_id);

CREATE TABLE IF NOT EXISTS comments (
  id                   TEXT NOT NULL,
  discussion_id        TEXT NOT NULL REFERENCES discussions(id) ON DELETE CASCADE,
  parent_id            TEXT REFERENCES comments(id) ON DELETE CASCADE,
  user_id              TEXT REFERENCES users(id) ON DELETE SET NULL,
  body                 TEXT NOT NULL,
  upvotes              BIGINT NOT NULL DEFAULT 0,
  is_ai                BIGINT NOT NULL DEFAULT 0,
  is_deleted           BIGINT NOT NULL DEFAULT 0,
  created_at           BIGINT NOT NULL,
  PRIMARY KEY (id, user_id)
) PARTITION BY HASH (user_id);

CREATE TABLE IF NOT EXISTS votes (
  user_id              TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  entity_type          TEXT NOT NULL,
  entity_id            TEXT NOT NULL,
  value                BIGINT NOT NULL,
  created_at           BIGINT NOT NULL,
  PRIMARY KEY (user_id, entity_type, entity_id)
) PARTITION BY HASH (user_id);

CREATE TABLE IF NOT EXISTS reports (
  id                   TEXT NOT NULL,
  reporter_id          TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  entity_type          TEXT NOT NULL,
  entity_id            TEXT NOT NULL,
  reason               TEXT NOT NULL,
  detail               TEXT,
  status               TEXT NOT NULL DEFAULT 'open',
  created_at           BIGINT NOT NULL,
  PRIMARY KEY (id)
);

CREATE TABLE IF NOT EXISTS notifications (
  id                   TEXT NOT NULL,
  user_id              TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  type                 TEXT NOT NULL,
  title                TEXT NOT NULL,
  body                 TEXT,
  url                  TEXT,
  read_at              BIGINT,
  created_at           BIGINT NOT NULL,
  PRIMARY KEY (id, user_id)
) PARTITION BY HASH (user_id);

CREATE TABLE IF NOT EXISTS certificates (
  id                   TEXT NOT NULL,
  user_id              TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  kind                 TEXT NOT NULL,
  entity_type          TEXT NOT NULL,
  entity_id            TEXT NOT NULL,
  title                TEXT NOT NULL,
  verify_id            TEXT NOT NULL UNIQUE,
  issued_at            BIGINT NOT NULL,
  meta                 TEXT NOT NULL DEFAULT '{}',
  tier                 TEXT NOT NULL DEFAULT 'bronze',
  PRIMARY KEY (id)
);

CREATE TABLE IF NOT EXISTS plans (
  id                   TEXT NOT NULL,
  slug                 TEXT NOT NULL UNIQUE,
  name                 TEXT NOT NULL,
  price_cents          BIGINT NOT NULL DEFAULT 0,
  currency             TEXT NOT NULL DEFAULT 'USD',
  interval             TEXT NOT NULL DEFAULT 'month',
  features             TEXT NOT NULL DEFAULT '[]',
  is_active            BIGINT NOT NULL DEFAULT 1,
  PRIMARY KEY (id)
);

CREATE TABLE IF NOT EXISTS subscriptions (
  id                   TEXT NOT NULL,
  user_id              TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  plan_id              TEXT NOT NULL REFERENCES plans(id) ON DELETE RESTRICT,
  status               TEXT NOT NULL DEFAULT 'active',
  started_at           BIGINT NOT NULL,
  expires_at           BIGINT,
  PRIMARY KEY (id)
);

CREATE TABLE IF NOT EXISTS payments (
  id                   TEXT NOT NULL,
  user_id              TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  subscription_id      TEXT REFERENCES subscriptions(id) ON DELETE SET NULL,
  amount_cents         BIGINT NOT NULL,
  currency             TEXT NOT NULL DEFAULT 'USD',
  provider             TEXT NOT NULL,
  provider_ref         TEXT,
  status               TEXT NOT NULL,
  created_at           BIGINT NOT NULL,
  PRIMARY KEY (id)
);

CREATE TABLE IF NOT EXISTS contests (
  id                   TEXT NOT NULL,
  slug                 TEXT NOT NULL UNIQUE,
  title                TEXT NOT NULL,
  kind                 TEXT NOT NULL DEFAULT 'weekly',
  starts_at            BIGINT NOT NULL,
  ends_at              BIGINT NOT NULL,
  description          TEXT,
  published            BIGINT NOT NULL DEFAULT 0,
  PRIMARY KEY (id)
);

CREATE TABLE IF NOT EXISTS contest_problems (
  contest_id           TEXT NOT NULL REFERENCES contests(id) ON DELETE CASCADE,
  question_id          TEXT REFERENCES questions(id) ON DELETE CASCADE,
  problem_id           TEXT REFERENCES coding_problems(id) ON DELETE CASCADE,
  points               BIGINT NOT NULL DEFAULT 10,
  order_index          BIGINT NOT NULL DEFAULT 0
);

CREATE TABLE IF NOT EXISTS contest_submissions (
  id                   TEXT NOT NULL,
  contest_id           TEXT NOT NULL REFERENCES contests(id) ON DELETE CASCADE,
  user_id              TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  question_id          TEXT REFERENCES questions(id) ON DELETE CASCADE,
  problem_id           TEXT REFERENCES coding_problems(id) ON DELETE CASCADE,
  score                BIGINT NOT NULL DEFAULT 0,
  created_at           BIGINT NOT NULL,
  PRIMARY KEY (id, user_id)
) PARTITION BY HASH (user_id);

CREATE TABLE IF NOT EXISTS site_config (
  key                  TEXT NOT NULL,
  value                TEXT NOT NULL,
  updated_at           BIGINT NOT NULL,
  PRIMARY KEY (key)
);

-- SQLite uses an FTS5 virtual table here. Postgres gets the same columns plus a
-- generated tsvector, which is what a GIN index can be built on.
--
-- NOTE: search.py currently issues FTS5-only SQL (MATCH, bm25()). A Postgres
-- deployment needs a tsquery branch in search(); the columns below are what
-- that branch will read.
CREATE TABLE IF NOT EXISTS search_index (
  entity_type  TEXT NOT NULL,
  entity_id    TEXT NOT NULL,
  title        TEXT NOT NULL DEFAULT '',
  body         TEXT NOT NULL DEFAULT '',
  branch       TEXT NOT NULL DEFAULT '',
  semester     TEXT NOT NULL DEFAULT '',
  difficulty   TEXT NOT NULL DEFAULT '',
  tags         TEXT NOT NULL DEFAULT '',
  tsv          tsvector GENERATED ALWAYS AS (
                 setweight(to_tsvector('simple', coalesce(title, '')), 'A') ||
                 setweight(to_tsvector('simple', coalesce(body, '')), 'B')
               ) STORED,
  PRIMARY KEY (entity_type, entity_id)
);
CREATE INDEX IF NOT EXISTS idx_search_tsv ON search_index USING GIN (tsv);
CREATE INDEX IF NOT EXISTS idx_search_branch ON search_index(branch, entity_type);

-- Helper: create the full set of hash partitions for a table. Idempotent, so the
-- schema script can be re-applied to a live database.
CREATE OR REPLACE FUNCTION engineverse_create_partitions(
  parent_table TEXT, partition_count INTEGER
) RETURNS VOID AS $body$
DECLARE
  n INTEGER;
  partition_name TEXT;
BEGIN
  FOR n IN 0..(partition_count - 1) LOOP
    partition_name := format('%s_p%s', parent_table, n);
    IF NOT EXISTS (SELECT 1 FROM pg_class WHERE relname = partition_name) THEN
      EXECUTE format(
        'CREATE TABLE %I PARTITION OF %I FOR VALUES WITH (MODULUS %s, REMAINDER %s)',
        partition_name, parent_table, partition_count, n);
    END IF;
  END LOOP;
END;
$body$ LANGUAGE plpgsql;

-- ---------------------------------------------------------------------------
-- Partitions. Fan-out chosen so the largest single partition of each table
-- stays in the low tens of millions of rows at ~1.5e9 users - small enough
-- for VACUUM, reindexing and a restore to stay tractable.
-- ---------------------------------------------------------------------------

SELECT engineverse_create_partitions('profiles', 64);
SELECT engineverse_create_partitions('streaks', 64);
SELECT engineverse_create_partitions('activity', 256);
SELECT engineverse_create_partitions('user_progress', 128);
SELECT engineverse_create_partitions('user_flashcards', 128);
SELECT engineverse_create_partitions('submissions', 256);
SELECT engineverse_create_partitions('xp_events', 128);
SELECT engineverse_create_partitions('notifications', 128);
SELECT engineverse_create_partitions('personal_notes', 64);
SELECT engineverse_create_partitions('comments', 128);
SELECT engineverse_create_partitions('discussions', 128);
SELECT engineverse_create_partitions('coding_submissions', 128);
SELECT engineverse_create_partitions('contest_submissions', 32);
SELECT engineverse_create_partitions('mistakes', 64);
SELECT engineverse_create_partitions('bookmarks', 64);
SELECT engineverse_create_partitions('votes', 64);
SELECT engineverse_create_partitions('user_badges', 64);
SELECT engineverse_create_partitions('audit_logs', 256);
SELECT engineverse_create_partitions('login_attempts', 32);
SELECT engineverse_create_partitions('api_rate_limits', 16);

-- ---------------------------------------------------------------------------
-- Indexes (translated from db/schema.sql).
-- ---------------------------------------------------------------------------
CREATE INDEX IF NOT EXISTS idx_users_status ON users(status);
CREATE INDEX IF NOT EXISTS idx_sessions_user ON sessions(user_id, expires_at);
CREATE INDEX IF NOT EXISTS idx_sessions_expiry ON sessions(expires_at);
CREATE INDEX IF NOT EXISTS idx_password_resets_user ON password_resets(user_id, created_at);
CREATE INDEX IF NOT EXISTS idx_password_resets_expiry ON password_resets(expires_at);
CREATE INDEX IF NOT EXISTS idx_login_ip ON login_attempts(ip, created_at);
CREATE INDEX IF NOT EXISTS idx_login_ident ON login_attempts(identifier, created_at);
CREATE INDEX IF NOT EXISTS idx_audit_actor ON audit_logs(actor_id, created_at);
CREATE INDEX IF NOT EXISTS idx_audit_action ON audit_logs(action, created_at);
CREATE INDEX IF NOT EXISTS idx_uni_country ON universities(country);
CREATE INDEX IF NOT EXISTS idx_branch_cat ON branches(category);
CREATE INDEX IF NOT EXISTS idx_subject_branch ON subjects(branch_id);
CREATE INDEX IF NOT EXISTS idx_subject_sem ON subjects(semester_id);
CREATE INDEX IF NOT EXISTS idx_topic_subject ON topics(subject_id, order_index);
CREATE INDEX IF NOT EXISTS idx_topic_module ON topics(module_id);
CREATE INDEX IF NOT EXISTS idx_section_note ON note_sections(note_id, order_index);
CREATE INDEX IF NOT EXISTS idx_diagram_topic ON diagrams(topic_id);
CREATE INDEX IF NOT EXISTS idx_model3d_topic ON models_3d(topic_id, order_index);
CREATE INDEX IF NOT EXISTS idx_formula_subject ON formulas(subject_id);
CREATE INDEX IF NOT EXISTS idx_formula_cat ON formulas(category);
CREATE INDEX IF NOT EXISTS idx_q_topic ON questions(topic_id, difficulty);
CREATE INDEX IF NOT EXISTS idx_q_subject ON questions(subject_id, kind);
CREATE INDEX IF NOT EXISTS idx_opt_q ON question_options(question_id, order_index);
CREATE INDEX IF NOT EXISTS idx_dppq_set ON dpp_questions(set_id, position);
CREATE INDEX IF NOT EXISTS idx_sub_user ON submissions(user_id, created_at);
CREATE INDEX IF NOT EXISTS idx_sub_question ON submissions(question_id, is_correct);
CREATE INDEX IF NOT EXISTS idx_sub_topic ON submissions(user_id, question_id);
CREATE INDEX IF NOT EXISTS idx_mistake_user ON mistakes(user_id, created_at);
CREATE INDEX IF NOT EXISTS idx_cp_difficulty ON coding_problems(difficulty);
CREATE INDEX IF NOT EXISTS idx_tc_problem ON coding_testcases(problem_id, order_index);
CREATE INDEX IF NOT EXISTS idx_csub_user ON coding_submissions(user_id, created_at);
CREATE INDEX IF NOT EXISTS idx_csub_problem ON coding_submissions(problem_id, is_accepted);
CREATE INDEX IF NOT EXISTS idx_project_difficulty ON projects(difficulty);
CREATE INDEX IF NOT EXISTS idx_project_branch ON projects(branch_id);
CREATE INDEX IF NOT EXISTS idx_pstep ON project_steps(project_id, order_index);
CREATE INDEX IF NOT EXISTS idx_video_topic ON videos(topic_id);
CREATE INDEX IF NOT EXISTS idx_res_kind ON resources(kind);
CREATE INDEX IF NOT EXISTS idx_rnode ON roadmap_nodes(roadmap_id, order_index);
CREATE INDEX IF NOT EXISTS idx_flash_topic ON flashcards(topic_id);
CREATE INDEX IF NOT EXISTS idx_uf_due ON user_flashcards(user_id, due_at);
CREATE INDEX IF NOT EXISTS idx_pnote ON personal_notes(user_id, entity_type, entity_id);
CREATE INDEX IF NOT EXISTS idx_xp_user ON xp_events(user_id, created_at);
CREATE INDEX IF NOT EXISTS idx_activity_day ON activity(day);
CREATE INDEX IF NOT EXISTS idx_disc_recent ON discussions(last_activity_at DESC);
CREATE INDEX IF NOT EXISTS idx_comment_disc ON comments(discussion_id, created_at);
CREATE INDEX IF NOT EXISTS idx_notif_user ON notifications(user_id, created_at DESC);

-- Append-only tables grow without bound. Prune in batches so VACUUM is never
-- asked to churn over the whole table at once.
CREATE OR REPLACE FUNCTION engineverse_prune_before(
  parent_table TEXT, cutoff_ms BIGINT
) RETURNS BIGINT AS $body$
DECLARE
  removed BIGINT := 0;
  batch BIGINT;
BEGIN
  LOOP
    EXECUTE format('DELETE FROM %I WHERE created_at < $1', parent_table)
      USING cutoff_ms;
    GET DIAGNOSTICS batch = ROW_COUNT;
    removed := removed + batch;
    EXIT WHEN batch < 100000;
    COMMIT;
  END LOOP;
  RETURN removed;
END;
$body$ LANGUAGE plpgsql;

ANALYZE;
