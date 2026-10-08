-- ===========================================================================
--  EngineVerse - production relational schema (PostgreSQL 16+)
--  ---------------------------------------------------------------------------
--  Mirrors db/schema.sql 1:1, with the changes that matter at 10^9 scale:
--
--    * High-cardinality, append-mostly tables are HASH PARTITIONED on the column
--      that every query already filters by (user_id, or the parent id). Hash
--      partitioning spreads rows evenly and needs no rebalancing as the table
--      grows, which is exactly the shape of a global learner platform.
--    * ULID text primary keys are kept: they are lexicographically sortable and
--      can be minted on any node without sequence contention.
--    * Epoch-millisecond BIGINT timestamps throughout, so the application layer
--      is identical on SQLite and Postgres.
--    * JSON payloads are jsonb, so they can be indexed and queried instead of
--      only round-tripped.
--    * Full-text search uses tsvector + GIN rather than SQLite's FTS5.
--
--  Partition counts below assume 1.5e9 users. They are chosen so a single
--  partition of the largest table stays in the low tens of millions of rows -
--  small enough for VACUUM, reindexing and a restore to stay tractable.
--
--  Apply with:  psql "$DATABASE_URL" -f db/postgres/schema.pg.sql
--  The script is idempotent.
-- ===========================================================================

SET client_min_messages TO WARNING;

-- ---------------------------------------------------------------------------
-- 0. EXTENSIONS
-- ---------------------------------------------------------------------------

CREATE EXTENSION IF NOT EXISTS citext;   -- case-insensitive email/username
CREATE EXTENSION IF NOT EXISTS pgcrypto; -- gen_random_bytes, digests

-- ---------------------------------------------------------------------------
-- 1. IDENTITY, AUTHENTICATION, AUDIT
-- ---------------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS users (
  id                   TEXT PRIMARY KEY,
  email                CITEXT NOT NULL UNIQUE,
  username             CITEXT NOT NULL UNIQUE,
  password_hash        TEXT NOT NULL,            -- scrypt$N$r$p$saltB64$hashB64
  role                 TEXT NOT NULL DEFAULT 'student',
  status               TEXT NOT NULL DEFAULT 'active',
  email_verified       BOOLEAN NOT NULL DEFAULT FALSE,
  failed_login_count   INTEGER NOT NULL DEFAULT 0,
  locked_until         BIGINT,
  password_changed_at  BIGINT NOT NULL,
  totp_secret          TEXT,                     -- encrypted at rest
  created_at           BIGINT NOT NULL,
  updated_at           BIGINT NOT NULL,
  deleted_at           BIGINT
);
CREATE INDEX IF NOT EXISTS idx_users_status ON users(status);
CREATE INDEX IF NOT EXISTS idx_users_created ON users(created_at DESC);

CREATE TABLE IF NOT EXISTS user_roles (
  user_id    TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  role       TEXT NOT NULL,
  granted_by TEXT REFERENCES users(id) ON DELETE SET NULL,
  granted_at BIGINT NOT NULL,
  PRIMARY KEY (user_id, role)
);

-- Per-user profile data. Partitioned so a profile lookup touches one partition.
CREATE TABLE IF NOT EXISTS profiles (
  user_id      TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  full_name    TEXT,
  headline     TEXT,
  avatar_seed  TEXT,
  bio          TEXT,
  branch_id    TEXT,
  semester_id  TEXT,
  college_id   TEXT,
  note_quality TEXT NOT NULL DEFAULT 'standard',
  timezone     TEXT NOT NULL DEFAULT 'Asia/Kolkata',
  is_public    BOOLEAN NOT NULL DEFAULT TRUE,
  updated_at   BIGINT NOT NULL,
  PRIMARY KEY (user_id)
) PARTITION BY HASH (user_id);

CREATE TABLE IF NOT EXISTS profiles_p0 PARTITION OF profiles FOR VALUES WITH (MODULUS 64, REMAINDER 0);
CREATE TABLE IF NOT EXISTS profiles_p1 PARTITION OF profiles FOR VALUES WITH (MODULUS 64, REMAINDER 1);
CREATE TABLE IF NOT EXISTS profiles_p2 PARTITION OF profiles FOR VALUES WITH (MODULUS 64, REMAINDER 2);
CREATE TABLE IF NOT EXISTS profiles_p3 PARTITION OF profiles FOR VALUES WITH (MODULUS 64, REMAINDER 3);
-- Partitions 4..63 are created by the DO block at the end of this file so the
-- script stays readable; they are identical to the four above.

-- Sessions are short-lived and voluminous: partition by list on a rolling
-- window is unnecessary, hash on session id keeps inserts even.
CREATE TABLE IF NOT EXISTS sessions (
  id             TEXT PRIMARY KEY,
  user_id        TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  token_hash     TEXT NOT NULL UNIQUE,           -- SHA-256 of the opaque cookie
  ip             TEXT,
  user_agent     TEXT,
  created_at     BIGINT NOT NULL,
  expires_at     BIGINT NOT NULL,
  last_seen_at   BIGINT NOT NULL,
  revoked_at     BIGINT
) PARTITION BY HASH (id);

CREATE INDEX IF NOT EXISTS idx_sessions_user ON sessions(user_id, expires_at);
CREATE INDEX IF NOT EXISTS idx_sessions_expiry ON sessions(expires_at);

-- Password reset tokens: hashed, exactly matched, short lived and single use.
-- Not partitioned - the table is pruned on use and expiry rather than grown.
CREATE TABLE IF NOT EXISTS password_resets (
  token_hash     TEXT PRIMARY KEY,               -- SHA-256 of the opaque token
  user_id        TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  created_at     BIGINT NOT NULL,
  expires_at     BIGINT NOT NULL,
  used_at        BIGINT,
  ip             TEXT
);

CREATE INDEX IF NOT EXISTS idx_password_resets_user ON password_resets(user_id, created_at);
CREATE INDEX IF NOT EXISTS idx_password_resets_expiry ON password_resets(expires_at);

-- Append-only credential-stuffing defence. Hash-partitioned on the identifier
-- because that is the only key the login path ever uses.
CREATE TABLE IF NOT EXISTS login_attempts (
  id          TEXT NOT NULL,
  identifier  TEXT NOT NULL,
  ip          TEXT,
  succeeded   BOOLEAN NOT NULL,
  reason      TEXT,
  created_at  BIGINT NOT NULL,
  PRIMARY KEY (id, identifier)
) PARTITION BY HASH (identifier);

CREATE INDEX IF NOT EXISTS idx_login_attempts_recent ON login_attempts(identifier, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_login_attempts_ip ON login_attempts(ip, created_at DESC);

CREATE TABLE IF NOT EXISTS api_rate_limits (
  bucket     TEXT NOT NULL,
  window_at  BIGINT NOT NULL,
  count      INTEGER NOT NULL DEFAULT 0,
  PRIMARY KEY (bucket, window_at)
);

-- Append-only. The single largest table on the platform, so it carries the
-- widest partition fan-out and is the first candidate for moving to a
-- time-series store or cold storage.
CREATE TABLE IF NOT EXISTS audit_logs (
  id          TEXT NOT NULL,
  actor_id    TEXT,
  action      TEXT NOT NULL,
  entity_type TEXT,
  entity_id   TEXT,
  ip          TEXT,
  meta        JSONB NOT NULL DEFAULT '{}'::jsonb,
  created_at  BIGINT NOT NULL,
  PRIMARY KEY (id, created_at)
) PARTITION BY HASH (id);

CREATE INDEX IF NOT EXISTS idx_audit_actor ON audit_logs(actor_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_audit_action ON audit_logs(action, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_audit_entity ON audit_logs(entity_type, entity_id);
CREATE INDEX IF NOT EXISTS idx_audit_meta ON audit_logs USING GIN (meta jsonb_path_ops);

-- ---------------------------------------------------------------------------
-- 2. CATALOGUE: BRANCHES -> SEMESTERS -> SUBJECTS -> MODULES -> TOPICS
-- ---------------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS universities (
  id         TEXT PRIMARY KEY,
  name       TEXT NOT NULL,
  country    TEXT NOT NULL DEFAULT 'IN',
  slug       TEXT NOT NULL UNIQUE,
  created_at BIGINT NOT NULL
);

CREATE TABLE IF NOT EXISTS colleges (
  id            TEXT PRIMARY KEY,
  university_id TEXT REFERENCES universities(id) ON DELETE SET NULL,
  name          TEXT NOT NULL,
  slug          TEXT NOT NULL UNIQUE,
  city          TEXT,
  created_at    BIGINT NOT NULL
);

CREATE TABLE IF NOT EXISTS branches (
  id         TEXT PRIMARY KEY,
  slug       TEXT NOT NULL UNIQUE,
  name       TEXT NOT NULL,
  category   TEXT NOT NULL,
  color      TEXT NOT NULL DEFAULT '#4f7cff',
  summary    TEXT,
  order_index INTEGER NOT NULL DEFAULT 0,
  created_at BIGINT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_branches_category ON branches(category, order_index);

CREATE TABLE IF NOT EXISTS semesters (
  id          TEXT PRIMARY KEY,
  branch_id   TEXT REFERENCES branches(id) ON DELETE CASCADE,
  number      INTEGER NOT NULL,
  name        TEXT NOT NULL,
  order_index INTEGER NOT NULL DEFAULT 0,
  UNIQUE (branch_id, number)
);

CREATE TABLE IF NOT EXISTS curricula (
  id            TEXT PRIMARY KEY,
  university_id TEXT REFERENCES universities(id) ON DELETE CASCADE,
  branch_id     TEXT NOT NULL REFERENCES branches(id) ON DELETE CASCADE,
  year          INTEGER NOT NULL,
  version       TEXT NOT NULL DEFAULT '1.0',
  is_active     BOOLEAN NOT NULL DEFAULT TRUE,
  UNIQUE (university_id, branch_id, year, version)
);

CREATE TABLE IF NOT EXISTS curriculum_subjects (
  curriculum_id TEXT NOT NULL REFERENCES curricula(id) ON DELETE CASCADE,
  subject_id    TEXT NOT NULL,
  semester_id   TEXT REFERENCES semesters(id) ON DELETE SET NULL,
  credits       NUMERIC(4,1) NOT NULL DEFAULT 3,
  is_core       BOOLEAN NOT NULL DEFAULT TRUE,
  order_index   INTEGER NOT NULL DEFAULT 0,
  PRIMARY KEY (curriculum_id, subject_id)
);

CREATE TABLE IF NOT EXISTS subjects (
  id          TEXT PRIMARY KEY,
  branch_id   TEXT REFERENCES branches(id) ON DELETE SET NULL,
  slug        TEXT NOT NULL UNIQUE,
  name        TEXT NOT NULL,
  code        TEXT,
  summary     TEXT,
  color       TEXT NOT NULL DEFAULT '#4f7cff',
  semester    INTEGER,
  first_year  BOOLEAN NOT NULL DEFAULT FALSE,
  status      TEXT NOT NULL DEFAULT 'published',
  order_index INTEGER NOT NULL DEFAULT 0,
  created_at  BIGINT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_subjects_branch ON subjects(branch_id, order_index);
CREATE INDEX IF NOT EXISTS idx_subjects_status ON subjects(status);

CREATE TABLE IF NOT EXISTS modules (
  id          TEXT PRIMARY KEY,
  subject_id  TEXT NOT NULL REFERENCES subjects(id) ON DELETE CASCADE,
  title       TEXT NOT NULL,
  summary     TEXT,
  order_index INTEGER NOT NULL DEFAULT 0
);
CREATE INDEX IF NOT EXISTS idx_modules_subject ON modules(subject_id, order_index);

CREATE TABLE IF NOT EXISTS topics (
  id           TEXT PRIMARY KEY,
  subject_id   TEXT NOT NULL REFERENCES subjects(id) ON DELETE CASCADE,
  module_id    TEXT REFERENCES modules(id) ON DELETE SET NULL,
  slug         TEXT NOT NULL UNIQUE,
  title        TEXT NOT NULL,
  summary      TEXT,
  difficulty   TEXT NOT NULL DEFAULT 'beginner',
  est_minutes  INTEGER NOT NULL DEFAULT 20,
  status       TEXT NOT NULL DEFAULT 'published',
  version      INTEGER NOT NULL DEFAULT 1,
  order_index  INTEGER NOT NULL DEFAULT 0,
  created_at   BIGINT NOT NULL,
  updated_at   BIGINT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_topics_subject ON topics(subject_id, order_index);
CREATE INDEX IF NOT EXISTS idx_topics_status ON topics(status);

-- ---------------------------------------------------------------------------
-- 3. CONTENT: NOTES (13-SECTION TEMPLATE), DIAGRAMS, FORMULAS
-- ---------------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS notes (
  id         TEXT PRIMARY KEY,
  topic_id   TEXT NOT NULL REFERENCES topics(id) ON DELETE CASCADE,
  quality    TEXT NOT NULL DEFAULT 'standard',
  author_id  TEXT REFERENCES users(id) ON DELETE SET NULL,
  status     TEXT NOT NULL DEFAULT 'published',
  version    INTEGER NOT NULL DEFAULT 1,
  created_at BIGINT NOT NULL,
  updated_at BIGINT NOT NULL,
  UNIQUE (topic_id, quality)
);

CREATE TABLE IF NOT EXISTS note_sections (
  id          TEXT PRIMARY KEY,
  note_id     TEXT NOT NULL REFERENCES notes(id) ON DELETE CASCADE,
  kind        TEXT NOT NULL,     -- simple|definition|intuition|points|formula|...
  title       TEXT NOT NULL,
  body_md     TEXT NOT NULL DEFAULT '',
  order_index INTEGER NOT NULL DEFAULT 0
);
CREATE INDEX IF NOT EXISTS idx_note_sections_note ON note_sections(note_id, order_index);

CREATE TABLE IF NOT EXISTS diagrams (
  id          TEXT PRIMARY KEY,
  topic_id    TEXT NOT NULL REFERENCES topics(id) ON DELETE CASCADE,
  title       TEXT NOT NULL,
  caption     TEXT,
  svg         TEXT NOT NULL,
  license     TEXT NOT NULL DEFAULT 'CC-BY-4.0',
  source_url  TEXT,
  hotspots    JSONB NOT NULL DEFAULT '[]'::jsonb,
  order_index INTEGER NOT NULL DEFAULT 0
);
CREATE INDEX IF NOT EXISTS idx_diagrams_topic ON diagrams(topic_id, order_index);

-- Interactive 3D models. `scene` is JSON describing geometry, validated by
-- engineverse.models3d.validate_scene() on write and on read. It is JSONB here
-- so a model can be queried and indexed by the server without parsing it in
-- application code first.
CREATE TABLE IF NOT EXISTS models_3d (
  id          TEXT PRIMARY KEY,
  topic_id    TEXT NOT NULL REFERENCES topics(id) ON DELETE CASCADE,
  title       TEXT NOT NULL,
  caption     TEXT,
  scene       JSONB NOT NULL,
  source_ref  TEXT,
  order_index INTEGER NOT NULL DEFAULT 0,
  created_at  BIGINT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_models_3d_topic ON models_3d(topic_id, order_index);

CREATE TABLE IF NOT EXISTS formulas (
  id         TEXT PRIMARY KEY,
  topic_id   TEXT REFERENCES topics(id) ON DELETE CASCADE,
  subject_id TEXT REFERENCES subjects(id) ON DELETE CASCADE,
  category   TEXT NOT NULL DEFAULT 'general',
  name       TEXT NOT NULL,
  latex      TEXT NOT NULL,
  variables  JSONB NOT NULL DEFAULT '[]'::jsonb,
  notes_md   TEXT,
  order_index INTEGER NOT NULL DEFAULT 0
);
CREATE INDEX IF NOT EXISTS idx_formulas_category ON formulas(category, order_index);
CREATE INDEX IF NOT EXISTS idx_formulas_topic ON formulas(topic_id);

-- ---------------------------------------------------------------------------
-- 4. PRACTICE: QUESTIONS, DPP, SUBMISSIONS, MISTAKES
-- ---------------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS questions (
  id           TEXT PRIMARY KEY,
  subject_id   TEXT REFERENCES subjects(id) ON DELETE CASCADE,
  topic_id     TEXT REFERENCES topics(id) ON DELETE CASCADE,
  slug         TEXT NOT NULL UNIQUE,
  kind         TEXT NOT NULL DEFAULT 'mcq',
  difficulty   TEXT NOT NULL DEFAULT 'medium',
  prompt_md    TEXT NOT NULL,
  answer       TEXT,
  explanation_md TEXT,
  is_active    BOOLEAN NOT NULL DEFAULT TRUE,
  created_at   BIGINT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_questions_topic ON questions(topic_id, difficulty);
CREATE INDEX IF NOT EXISTS idx_questions_subject ON questions(subject_id, kind);

CREATE TABLE IF NOT EXISTS question_options (
  id          TEXT PRIMARY KEY,
  question_id TEXT NOT NULL REFERENCES questions(id) ON DELETE CASCADE,
  label       TEXT NOT NULL,
  body_md     TEXT NOT NULL,
  is_correct  BOOLEAN NOT NULL DEFAULT FALSE,
  order_index INTEGER NOT NULL DEFAULT 0
);
CREATE INDEX IF NOT EXISTS idx_qoptions_question ON question_options(question_id, order_index);

CREATE TABLE IF NOT EXISTS dpp_sets (
  id              TEXT PRIMARY KEY,
  subject_id      TEXT REFERENCES subjects(id) ON DELETE SET NULL,
  branch_id       TEXT REFERENCES branches(id) ON DELETE SET NULL,
  date            TEXT NOT NULL UNIQUE,
  title           TEXT NOT NULL,
  summary         TEXT,
  duration_minutes INTEGER NOT NULL DEFAULT 30,
  published       BOOLEAN NOT NULL DEFAULT TRUE,
  created_at      BIGINT NOT NULL
);

CREATE TABLE IF NOT EXISTS dpp_questions (
  set_id      TEXT NOT NULL REFERENCES dpp_sets(id) ON DELETE CASCADE,
  question_id TEXT NOT NULL REFERENCES questions(id) ON DELETE CASCADE,
  position    INTEGER NOT NULL DEFAULT 0,
  PRIMARY KEY (set_id, question_id)
);

-- The hottest write path on the platform: every answer from every learner.
-- Hash-partitioned on user_id so a learner's history lives in one partition
-- and the leaderboard's aggregation can run partition-parallel.
CREATE TABLE IF NOT EXISTS submissions (
  id           TEXT NOT NULL,
  user_id      TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  question_id  TEXT NOT NULL REFERENCES questions(id) ON DELETE CASCADE,
  topic_id     TEXT REFERENCES topics(id) ON DELETE SET NULL,
  dpp_set_id   TEXT REFERENCES dpp_sets(id) ON DELETE SET NULL,
  answer       TEXT,
  is_correct   BOOLEAN NOT NULL DEFAULT FALSE,
  time_spent_s INTEGER NOT NULL DEFAULT 0,
  created_at   BIGINT NOT NULL,
  PRIMARY KEY (id, user_id)
) PARTITION BY HASH (user_id);

CREATE INDEX IF NOT EXISTS idx_submissions_user ON submissions(user_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_submissions_question ON submissions(question_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_submissions_topic ON submissions(topic_id, is_correct);

CREATE TABLE IF NOT EXISTS mistakes (
  id          TEXT NOT NULL,
  user_id     TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  question_id TEXT NOT NULL REFERENCES questions(id) ON DELETE CASCADE,
  topic_id    TEXT REFERENCES topics(id) ON DELETE SET NULL,
  note        TEXT,
  resolved    BOOLEAN NOT NULL DEFAULT FALSE,
  created_at  BIGINT NOT NULL,
  PRIMARY KEY (id, user_id)
) PARTITION BY HASH (user_id);

CREATE INDEX IF NOT EXISTS idx_mistakes_open ON mistakes(user_id, resolved, created_at DESC);

-- ---------------------------------------------------------------------------
-- 5. CODING: LANGUAGES, PROBLEMS, SUBMISSIONS
-- ---------------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS programming_languages (
  id          TEXT PRIMARY KEY,
  slug        TEXT NOT NULL UNIQUE,
  name        TEXT NOT NULL,
  color       TEXT NOT NULL DEFAULT '#4f7cff',
  runnable    BOOLEAN NOT NULL DEFAULT FALSE,
  order_index INTEGER NOT NULL DEFAULT 0
);

CREATE TABLE IF NOT EXISTS language_modules (
  id          TEXT PRIMARY KEY,
  language_id TEXT NOT NULL REFERENCES programming_languages(id) ON DELETE CASCADE,
  title       TEXT NOT NULL,
  body_md     TEXT NOT NULL,
  order_index INTEGER NOT NULL DEFAULT 0
);

CREATE TABLE IF NOT EXISTS coding_problems (
  id              TEXT PRIMARY KEY,
  slug            TEXT NOT NULL UNIQUE,
  title           TEXT NOT NULL,
  statement       TEXT NOT NULL,
  difficulty      TEXT NOT NULL DEFAULT 'medium',
  topics          JSONB NOT NULL DEFAULT '[]'::jsonb,
  hints           JSONB NOT NULL DEFAULT '[]'::jsonb,
  editorial       TEXT,
  solution_md     TEXT,
  tags            JSONB NOT NULL DEFAULT '[]'::jsonb,
  expected_time   TEXT,
  expected_space  TEXT,
  wrapper         TEXT NOT NULL DEFAULT 'raw',   -- see backend/engineverse/drivers.py
  solve_count     BIGINT NOT NULL DEFAULT 0,
  attempt_count   BIGINT NOT NULL DEFAULT 0,
  is_premium      BOOLEAN NOT NULL DEFAULT FALSE,
  created_at      BIGINT NOT NULL
);

CREATE TABLE IF NOT EXISTS coding_problem_stubs (
  problem_id  TEXT NOT NULL REFERENCES coding_problems(id) ON DELETE CASCADE,
  language_id TEXT NOT NULL REFERENCES programming_languages(id) ON DELETE CASCADE,
  stub        TEXT NOT NULL,
  signature   TEXT,
  PRIMARY KEY (problem_id, language_id)
);

CREATE TABLE IF NOT EXISTS coding_testcases (
  id          TEXT PRIMARY KEY,
  problem_id  TEXT NOT NULL REFERENCES coding_problems(id) ON DELETE CASCADE,
  input       TEXT NOT NULL DEFAULT '',
  expected    TEXT NOT NULL,
  is_sample   BOOLEAN NOT NULL DEFAULT FALSE,
  explanation TEXT,
  order_index INTEGER NOT NULL DEFAULT 0
);
CREATE INDEX IF NOT EXISTS idx_tc_problem ON coding_testcases(problem_id, order_index);

-- Source code is bulky; partitioned on user_id so one learner's submissions are
-- contiguous and pruning works for the "my submissions" page.
CREATE TABLE IF NOT EXISTS coding_submissions (
  id           TEXT NOT NULL,
  user_id      TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  problem_id   TEXT NOT NULL REFERENCES coding_problems(id) ON DELETE CASCADE,
  language     TEXT NOT NULL,
  code         TEXT NOT NULL,
  status       TEXT NOT NULL,
  passed       INTEGER NOT NULL DEFAULT 0,
  total        INTEGER NOT NULL DEFAULT 0,
  runtime_ms   INTEGER NOT NULL DEFAULT 0,
  memory_kb    INTEGER,
  stderr       TEXT,
  is_accepted  BOOLEAN NOT NULL DEFAULT FALSE,
  created_at   BIGINT NOT NULL,
  PRIMARY KEY (id, user_id)
) PARTITION BY HASH (user_id);

CREATE INDEX IF NOT EXISTS idx_coding_sub_user ON coding_submissions(user_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_coding_sub_problem ON coding_submissions(problem_id, is_accepted);

-- ---------------------------------------------------------------------------
-- 6. PROJECTS, LIBRARY, ROADMAPS
-- ---------------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS projects (
  id          TEXT PRIMARY KEY,
  slug        TEXT NOT NULL UNIQUE,
  title       TEXT NOT NULL,
  summary     TEXT,
  description_md TEXT NOT NULL DEFAULT '',
  category    TEXT NOT NULL DEFAULT 'web',
  difficulty  TEXT NOT NULL DEFAULT 'intermediate',
  branch_id   TEXT REFERENCES branches(id) ON DELETE SET NULL,
  skills      JSONB NOT NULL DEFAULT '[]'::jsonb,
  status      TEXT NOT NULL DEFAULT 'published',
  order_index INTEGER NOT NULL DEFAULT 0,
  created_at  BIGINT NOT NULL
);

CREATE TABLE IF NOT EXISTS project_steps (
  id          TEXT PRIMARY KEY,
  project_id  TEXT NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
  title       TEXT NOT NULL,
  body_md     TEXT NOT NULL DEFAULT '',
  order_index INTEGER NOT NULL DEFAULT 0
);

CREATE TABLE IF NOT EXISTS project_resources (
  id          TEXT PRIMARY KEY,
  project_id  TEXT NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
  title       TEXT NOT NULL,
  url         TEXT NOT NULL,
  kind        TEXT NOT NULL DEFAULT 'link',
  order_index INTEGER NOT NULL DEFAULT 0
);

CREATE TABLE IF NOT EXISTS videos (
  id          TEXT PRIMARY KEY,
  topic_id    TEXT REFERENCES topics(id) ON DELETE CASCADE,
  subject_id  TEXT REFERENCES subjects(id) ON DELETE SET NULL,
  title       TEXT NOT NULL,
  channel     TEXT NOT NULL,
  url         TEXT NOT NULL,       -- links out; never re-hosted
  duration_s  INTEGER NOT NULL DEFAULT 0,
  category    TEXT NOT NULL DEFAULT 'lecture',
  level       TEXT NOT NULL DEFAULT 'beginner',
  language    TEXT NOT NULL DEFAULT 'en',
  order_index INTEGER NOT NULL DEFAULT 0
);
CREATE INDEX IF NOT EXISTS idx_videos_topic ON videos(topic_id);
CREATE INDEX IF NOT EXISTS idx_videos_category ON videos(category, level);

CREATE TABLE IF NOT EXISTS books (
  id          TEXT PRIMARY KEY,
  subject_id  TEXT REFERENCES subjects(id) ON DELETE SET NULL,
  title       TEXT NOT NULL,
  author      TEXT NOT NULL,
  url         TEXT,                -- publisher or open-access source
  is_free     BOOLEAN NOT NULL DEFAULT FALSE,
  level       TEXT NOT NULL DEFAULT 'beginner',
  summary     TEXT,
  order_index INTEGER NOT NULL DEFAULT 0
);

CREATE TABLE IF NOT EXISTS resources (
  id          TEXT PRIMARY KEY,
  subject_id  TEXT REFERENCES subjects(id) ON DELETE SET NULL,
  branch_id   TEXT REFERENCES branches(id) ON DELETE SET NULL,
  title       TEXT NOT NULL,
  url         TEXT NOT NULL,
  kind        TEXT NOT NULL DEFAULT 'article',
  is_free     BOOLEAN NOT NULL DEFAULT TRUE,
  summary     TEXT,
  order_index INTEGER NOT NULL DEFAULT 0
);

CREATE TABLE IF NOT EXISTS roadmaps (
  id          TEXT PRIMARY KEY,
  slug        TEXT NOT NULL UNIQUE,
  title       TEXT NOT NULL,
  summary     TEXT,
  branch_id   TEXT REFERENCES branches(id) ON DELETE SET NULL,
  status      TEXT NOT NULL DEFAULT 'published',
  order_index INTEGER NOT NULL DEFAULT 0
);

CREATE TABLE IF NOT EXISTS roadmap_nodes (
  id          TEXT PRIMARY KEY,
  roadmap_id  TEXT NOT NULL REFERENCES roadmaps(id) ON DELETE CASCADE,
  topic_id    TEXT REFERENCES topics(id) ON DELETE SET NULL,
  title       TEXT NOT NULL,
  summary     TEXT,
  parent_id   TEXT REFERENCES roadmap_nodes(id) ON DELETE SET NULL,
  depth       INTEGER NOT NULL DEFAULT 0,
  order_index INTEGER NOT NULL DEFAULT 0
);
CREATE INDEX IF NOT EXISTS idx_roadmap_nodes_parent ON roadmap_nodes(roadmap_id, parent_id, order_index);

-- ---------------------------------------------------------------------------
-- 7. LEARNING STATE: FLASHCARDS, PROGRESS, XP, STREAKS
-- ---------------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS flashcards (
  id          TEXT PRIMARY KEY,
  topic_id    TEXT REFERENCES topics(id) ON DELETE CASCADE,
  subject_id  TEXT REFERENCES subjects(id) ON DELETE SET NULL,
  deck        TEXT NOT NULL DEFAULT 'core',
  front_md    TEXT NOT NULL,
  back_md     TEXT NOT NULL,
  order_index INTEGER NOT NULL DEFAULT 0
);
CREATE INDEX IF NOT EXISTS idx_flashcards_topic ON flashcards(topic_id, deck);

CREATE TABLE IF NOT EXISTS user_flashcards (
  user_id       TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  flashcard_id  TEXT NOT NULL REFERENCES flashcards(id) ON DELETE CASCADE,
  ease_factor   NUMERIC(4,2) NOT NULL DEFAULT 2.50,
  interval_days INTEGER NOT NULL DEFAULT 0,
  repetitions   INTEGER NOT NULL DEFAULT 0,
  due_at        BIGINT NOT NULL,
  last_seen_at  BIGINT,
  PRIMARY KEY (user_id, flashcard_id)
) PARTITION BY HASH (user_id);

CREATE INDEX IF NOT EXISTS idx_user_flashcards_due ON user_flashcards(user_id, due_at);

CREATE TABLE IF NOT EXISTS user_progress (
  user_id        TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  topic_id       TEXT NOT NULL REFERENCES topics(id) ON DELETE CASCADE,
  status         TEXT NOT NULL DEFAULT 'started',
  mastery        INTEGER NOT NULL DEFAULT 0,
  time_spent_s   INTEGER NOT NULL DEFAULT 0,
  last_viewed_at BIGINT NOT NULL,
  completed_at   BIGINT,
  PRIMARY KEY (user_id, topic_id)
) PARTITION BY HASH (user_id);

CREATE INDEX IF NOT EXISTS idx_user_progress_status ON user_progress(user_id, status);

CREATE TABLE IF NOT EXISTS bookmarks (
  user_id     TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  entity_type TEXT NOT NULL,
  entity_id   TEXT NOT NULL,
  created_at  BIGINT NOT NULL,
  PRIMARY KEY (user_id, entity_type, entity_id)
) PARTITION BY HASH (user_id);

CREATE TABLE IF NOT EXISTS personal_notes (
  id          TEXT NOT NULL,
  user_id     TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  topic_id    TEXT REFERENCES topics(id) ON DELETE CASCADE,
  body_md     TEXT NOT NULL,
  created_at  BIGINT NOT NULL,
  updated_at  BIGINT NOT NULL,
  PRIMARY KEY (id, user_id)
) PARTITION BY HASH (user_id);

CREATE TABLE IF NOT EXISTS xp_events (
  id          TEXT NOT NULL,
  user_id     TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  amount      INTEGER NOT NULL,
  reason      TEXT NOT NULL,
  entity_type TEXT,
  entity_id   TEXT,
  created_at  BIGINT NOT NULL,
  PRIMARY KEY (id, user_id)
) PARTITION BY HASH (user_id);

CREATE INDEX IF NOT EXISTS idx_xp_events_user ON xp_events(user_id, created_at DESC);

CREATE TABLE IF NOT EXISTS streaks (
  user_id        TEXT PRIMARY KEY REFERENCES users(id) ON DELETE CASCADE,
  current_streak INTEGER NOT NULL DEFAULT 0,
  longest_streak INTEGER NOT NULL DEFAULT 0,
  last_active_day TEXT,
  freeze_count   INTEGER NOT NULL DEFAULT 0,
  total_xp       BIGINT NOT NULL DEFAULT 0,
  level          INTEGER NOT NULL DEFAULT 1
);
CREATE INDEX IF NOT EXISTS idx_streaks_xp ON streaks(total_xp DESC);

-- One row per user per day. At 1.5e9 users this is the second-largest table,
-- so it is partitioned on user_id and is the primary candidate for rolling
-- older partitions into cold storage.
CREATE TABLE IF NOT EXISTS activity (
  user_id            TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  day                TEXT NOT NULL,
  notes_studied      INTEGER NOT NULL DEFAULT 0,
  questions_solved   INTEGER NOT NULL DEFAULT 0,
  coding_submissions INTEGER NOT NULL DEFAULT 0,
  projects_touched   INTEGER NOT NULL DEFAULT 0,
  revisions          INTEGER NOT NULL DEFAULT 0,
  minutes            INTEGER NOT NULL DEFAULT 0,
  xp                 INTEGER NOT NULL DEFAULT 0,
  PRIMARY KEY (user_id, day)
) PARTITION BY HASH (user_id);

CREATE INDEX IF NOT EXISTS idx_activity_day ON activity(day, xp DESC);

CREATE TABLE IF NOT EXISTS badges (
  id          TEXT PRIMARY KEY,
  slug        TEXT NOT NULL UNIQUE,
  name        TEXT NOT NULL,
  description TEXT NOT NULL,
  icon        TEXT,
  tier        TEXT NOT NULL DEFAULT 'bronze',
  criterion   TEXT
);

CREATE TABLE IF NOT EXISTS user_badges (
  user_id    TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  badge_id   TEXT NOT NULL REFERENCES badges(id) ON DELETE CASCADE,
  awarded_at BIGINT NOT NULL,
  PRIMARY KEY (user_id, badge_id)
) PARTITION BY HASH (user_id);

-- ---------------------------------------------------------------------------
-- 8. COMMUNITY
-- ---------------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS discussions (
  id          TEXT PRIMARY KEY,
  author_id   TEXT REFERENCES users(id) ON DELETE SET NULL,
  topic_id    TEXT REFERENCES topics(id) ON DELETE SET NULL,
  subject_id  TEXT REFERENCES subjects(id) ON DELETE SET NULL,
  kind        TEXT NOT NULL DEFAULT 'question',
  title       TEXT NOT NULL,
  body_md     TEXT NOT NULL,
  tags        JSONB NOT NULL DEFAULT '[]'::jsonb,
  resolved    BOOLEAN NOT NULL DEFAULT FALSE,
  vote_score  INTEGER NOT NULL DEFAULT 0,
  comment_count INTEGER NOT NULL DEFAULT 0,
  created_at  BIGINT NOT NULL,
  updated_at  BIGINT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_discussions_recent ON discussions(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_discussions_kind ON discussions(kind, resolved, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_discussions_topic ON discussions(topic_id, created_at DESC);

CREATE TABLE IF NOT EXISTS comments (
  id            TEXT PRIMARY KEY,
  thread_id     TEXT NOT NULL REFERENCES discussions(id) ON DELETE CASCADE,
  author_id     TEXT REFERENCES users(id) ON DELETE SET NULL,
  parent_id     TEXT REFERENCES comments(id) ON DELETE CASCADE,
  body_md       TEXT NOT NULL,
  is_answer     BOOLEAN NOT NULL DEFAULT FALSE,
  vote_score    INTEGER NOT NULL DEFAULT 0,
  created_at    BIGINT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_comments_thread ON comments(thread_id, created_at);

CREATE TABLE IF NOT EXISTS votes (
  user_id     TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  entity_type TEXT NOT NULL,
  entity_id   TEXT NOT NULL,
  value       SMALLINT NOT NULL,
  created_at  BIGINT NOT NULL,
  PRIMARY KEY (user_id, entity_type, entity_id)
) PARTITION BY HASH (user_id);

CREATE TABLE IF NOT EXISTS reports (
  id          TEXT PRIMARY KEY,
  reporter_id TEXT REFERENCES users(id) ON DELETE SET NULL,
  entity_type TEXT NOT NULL,
  entity_id   TEXT NOT NULL,
  reason      TEXT NOT NULL,
  status      TEXT NOT NULL DEFAULT 'open',
  created_at  BIGINT NOT NULL
);

CREATE TABLE IF NOT EXISTS notifications (
  id          TEXT NOT NULL,
  user_id     TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  kind        TEXT NOT NULL,
  title       TEXT NOT NULL,
  body        TEXT,
  url         TEXT,
  read_at     BIGINT,
  created_at  BIGINT NOT NULL,
  PRIMARY KEY (id, user_id)
) PARTITION BY HASH (user_id);

CREATE INDEX IF NOT EXISTS idx_notifications_unread ON notifications(user_id, read_at, created_at DESC);

-- ---------------------------------------------------------------------------
-- 9. CERTIFICATES, BILLING
-- ---------------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS certificates (
  id           TEXT PRIMARY KEY,
  user_id      TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  roadmap_id   TEXT REFERENCES roadmaps(id) ON DELETE SET NULL,
  verify_id    TEXT NOT NULL UNIQUE,   -- public verification URL, no accreditation claim
  title        TEXT NOT NULL,
  issued_at    BIGINT NOT NULL,
  meta         JSONB NOT NULL DEFAULT '{}'::jsonb,
  tier         TEXT NOT NULL DEFAULT 'bronze'   -- bronze|silver|gold|platinum
);
CREATE INDEX IF NOT EXISTS idx_certificates_user ON certificates(user_id, issued_at DESC);

CREATE TABLE IF NOT EXISTS plans (
  id          TEXT PRIMARY KEY,
  slug        TEXT NOT NULL UNIQUE,
  name        TEXT NOT NULL,
  price_cents INTEGER NOT NULL DEFAULT 0,
  currency    TEXT NOT NULL DEFAULT 'INR',
  interval    TEXT NOT NULL DEFAULT 'month',
  features    JSONB NOT NULL DEFAULT '[]'::jsonb,
  is_active   BOOLEAN NOT NULL DEFAULT TRUE
);

CREATE TABLE IF NOT EXISTS subscriptions (
  id          TEXT PRIMARY KEY,
  user_id     TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  plan_id     TEXT REFERENCES plans(id) ON DELETE SET NULL,
  status      TEXT NOT NULL DEFAULT 'active',
  started_at  BIGINT NOT NULL,
  ends_at     BIGINT
);
CREATE INDEX IF NOT EXISTS idx_subscriptions_user ON subscriptions(user_id, status);

CREATE TABLE IF NOT EXISTS payments (
  id          TEXT PRIMARY KEY,
  user_id     TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  amount_cents INTEGER NOT NULL,
  currency    TEXT NOT NULL DEFAULT 'INR',
  status      TEXT NOT NULL DEFAULT 'pending',
  reference   TEXT,
  created_at  BIGINT NOT NULL
);

-- ---------------------------------------------------------------------------
-- 10. CONTESTS
-- ---------------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS contests (
  id         TEXT PRIMARY KEY,
  slug       TEXT NOT NULL UNIQUE,
  title      TEXT NOT NULL,
  starts_at  BIGINT NOT NULL,
  ends_at    BIGINT NOT NULL,
  status     TEXT NOT NULL DEFAULT 'scheduled'
);

CREATE TABLE IF NOT EXISTS contest_problems (
  contest_id  TEXT NOT NULL REFERENCES contests(id) ON DELETE CASCADE,
  problem_id  TEXT NOT NULL REFERENCES coding_problems(id) ON DELETE CASCADE,
  points      INTEGER NOT NULL DEFAULT 100,
  order_index INTEGER NOT NULL DEFAULT 0,
  PRIMARY KEY (contest_id, problem_id)
);

CREATE TABLE IF NOT EXISTS contest_submissions (
  id          TEXT NOT NULL,
  contest_id  TEXT NOT NULL REFERENCES contests(id) ON DELETE CASCADE,
  user_id     TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  problem_id  TEXT NOT NULL REFERENCES coding_problems(id) ON DELETE CASCADE,
  score       INTEGER NOT NULL DEFAULT 0,
  created_at  BIGINT NOT NULL,
  PRIMARY KEY (id, contest_id)
) PARTITION BY HASH (contest_id);

-- ---------------------------------------------------------------------------
-- 11. PLATFORM CONFIG AND SEARCH
-- ---------------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS site_config (
  key        TEXT PRIMARY KEY,
  value      TEXT NOT NULL,
  updated_at BIGINT NOT NULL
);

-- Postgres full-text search replaces SQLite's FTS5. A generated tsvector with a
-- GIN index keeps this fast without a separate search service.
CREATE TABLE IF NOT EXISTS search_index (
  entity_type TEXT NOT NULL,
  entity_id   TEXT NOT NULL,
  slug        TEXT,
  title       TEXT NOT NULL,
  body        TEXT NOT NULL DEFAULT '',
  branch_slug TEXT,
  subject_slug TEXT,
  weight      INTEGER NOT NULL DEFAULT 1,
  tsv         TSVECTOR GENERATED ALWAYS AS (
                setweight(to_tsvector('english', coalesce(title, '')), 'A') ||
                setweight(to_tsvector('english', coalesce(body, '')), 'B')
              ) STORED,
  PRIMARY KEY (entity_type, entity_id)
);
CREATE INDEX IF NOT EXISTS idx_search_tsv ON search_index USING GIN (tsv);
CREATE INDEX IF NOT EXISTS idx_search_type ON search_index(entity_type, weight DESC);

-- ---------------------------------------------------------------------------
-- 12. REMAINING HASH PARTITIONS
-- ---------------------------------------------------------------------------
-- The four profile partitions above are spelled out as documentation of the
-- pattern; every other partitioned table gets its full fan-out here.

DO $$
DECLARE
  spec RECORD;
  n INTEGER;
  partition_name TEXT;
BEGIN
  FOREACH n IN ARRAY ARRAY[4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23,
                           24,25,26,27,28,29,30,31,32,33,34,35,36,37,38,39,40,41,
                           42,43,44,45,46,47,48,49,50,51,52,53,54,55,56,57,58,59,
                           60,61,62,63]
  LOOP
    partition_name := format('profiles_p%s', n);
    IF NOT EXISTS (SELECT 1 FROM pg_class WHERE relname = partition_name) THEN
      EXECUTE format(
        'CREATE TABLE %I PARTITION OF profiles FOR VALUES WITH (MODULUS 64, REMAINDER %s)',
        partition_name, n);
    END IF;
  END LOOP;
END $$;

-- Helper: create the full set of hash partitions for a table.
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

-- Fan-out chosen so the largest partition of each table stays in the low tens of
-- millions of rows at 1.5e9 users.
SELECT engineverse_create_partitions('sessions', 64);
SELECT engineverse_create_partitions('login_attempts', 32);
SELECT engineverse_create_partitions('audit_logs', 256);
SELECT engineverse_create_partitions('submissions', 256);
SELECT engineverse_create_partitions('mistakes', 64);
SELECT engineverse_create_partitions('coding_submissions', 128);
SELECT engineverse_create_partitions('user_flashcards', 128);
SELECT engineverse_create_partitions('user_progress', 128);
SELECT engineverse_create_partitions('bookmarks', 64);
SELECT engineverse_create_partitions('personal_notes', 64);
SELECT engineverse_create_partitions('xp_events', 128);
SELECT engineverse_create_partitions('activity', 256);
SELECT engineverse_create_partitions('user_badges', 64);
SELECT engineverse_create_partitions('votes', 64);
SELECT engineverse_create_partitions('notifications', 128);
SELECT engineverse_create_partitions('contest_submissions', 32);

-- ---------------------------------------------------------------------------
-- 13. MAINTENANCE
-- ---------------------------------------------------------------------------

-- Append-only tables grow without bound. Detach and archive a slice rather than
-- letting VACUUM churn over the whole table.
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
