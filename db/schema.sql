-- ===========================================================================
--  EngineVerse - core relational schema (SQLite dialect / development driver)
--  ---------------------------------------------------------------------------
--  This file is the single source of truth for the development database.
--  The production equivalent (PostgreSQL 16+, hash-partitioned for
--  10^9 scale) lives in db/postgres/schema.pg.sql and mirrors this model 1:1.
--
--  Conventions
--    * TEXT  ids are ULIDs (lexicographically sortable, 26 chars, no sequence
--      contention across shards - critical for horizontal scaling).
--    * timestamps are unix epoch milliseconds (INTEGER).
--    * every mutable content table carries status/version/author for the
--      content-quality workflow described in docs/CONTENT.md (draft ->
--      under_review -> approved -> published -> archived).
--    * JSON payloads are stored as TEXT and validated with Zod at the edge.
-- ===========================================================================

PRAGMA foreign_keys = ON;

-- ---------------------------------------------------------------------------
-- 1. IDENTITY, AUTHENTICATION, AUDIT
-- ---------------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS users (
  id                   TEXT PRIMARY KEY,
  email                TEXT NOT NULL UNIQUE,
  username             TEXT NOT NULL UNIQUE,
  password_hash        TEXT NOT NULL,            -- scrypt$N$r$p$saltB64$hashB64
  role                 TEXT NOT NULL DEFAULT 'student',
  status               TEXT NOT NULL DEFAULT 'active',
  email_verified       INTEGER NOT NULL DEFAULT 0,
  failed_login_count   INTEGER NOT NULL DEFAULT 0,
  locked_until         INTEGER,
  password_changed_at  INTEGER NOT NULL,
  totp_secret          TEXT,                     -- encrypted at rest; 2FA
  created_at           INTEGER NOT NULL,
  updated_at           INTEGER NOT NULL,
  deleted_at           INTEGER
);
CREATE INDEX IF NOT EXISTS idx_users_status ON users(status);

CREATE TABLE IF NOT EXISTS user_roles (
  user_id    TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  role       TEXT NOT NULL,
  granted_by TEXT,
  granted_at INTEGER NOT NULL,
  PRIMARY KEY (user_id, role)
);

CREATE TABLE IF NOT EXISTS profiles (
  user_id            TEXT PRIMARY KEY REFERENCES users(id) ON DELETE CASCADE,
  full_name          TEXT NOT NULL,
  avatar_seed        TEXT,
  headline           TEXT,
  bio                TEXT,
  country            TEXT,
  university_id      TEXT REFERENCES universities(id) ON DELETE SET NULL,
  college_id         TEXT REFERENCES colleges(id) ON DELETE SET NULL,
  branch_id          TEXT REFERENCES branches(id) ON DELETE SET NULL,
  semester_id        INTEGER REFERENCES semesters(id) ON DELETE SET NULL,
  skill_level        TEXT NOT NULL DEFAULT 'beginner',
  career_goal        TEXT,
  programming_xp     TEXT NOT NULL DEFAULT 'none',
  weekly_study_hours INTEGER NOT NULL DEFAULT 7,
  language_pref      TEXT NOT NULL DEFAULT 'en',
  note_quality       TEXT NOT NULL DEFAULT 'standard',
  github_url         TEXT,
  linkedin_url       TEXT,
  portfolio_url      TEXT,
  skills             TEXT NOT NULL DEFAULT '[]',
  privacy            TEXT NOT NULL DEFAULT '{}',
  notification_prefs TEXT NOT NULL DEFAULT '{}',
  onboarded_at       INTEGER,
  updated_at         INTEGER NOT NULL
);

-- Opaque bearer tokens; only the SHA-256 of the token is stored, so a database
-- leak alone cannot be replayed as a session.
CREATE TABLE IF NOT EXISTS sessions (
  id            TEXT PRIMARY KEY,
  token_hash    TEXT NOT NULL UNIQUE,
  user_id       TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  created_at    INTEGER NOT NULL,
  expires_at    INTEGER NOT NULL,
  last_seen_at  INTEGER NOT NULL,
  ip            TEXT,
  user_agent    TEXT,
  revoked_at    INTEGER
);
CREATE INDEX IF NOT EXISTS idx_sessions_user ON sessions(user_id, expires_at);
CREATE INDEX IF NOT EXISTS idx_sessions_expiry ON sessions(expires_at);

-- Password reset tokens. Stored hashed and matched exactly; they expire, are
-- single use, and a new request invalidates the previous one. Reset tokens used
-- to live in audit_logs and be looked up with `meta LIKE '%"<token>"%'`, which
-- let a submitted LIKE wildcard such as `%` match whoever had requested a reset
-- most recently - a full account takeover.
CREATE TABLE IF NOT EXISTS password_resets (
  token_hash    TEXT PRIMARY KEY,
  user_id       TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  created_at    INTEGER NOT NULL,
  expires_at    INTEGER NOT NULL,
  used_at       INTEGER,
  ip            TEXT
);
CREATE INDEX IF NOT EXISTS idx_password_resets_user ON password_resets(user_id, created_at);
CREATE INDEX IF NOT EXISTS idx_password_resets_expiry ON password_resets(expires_at);

CREATE TABLE IF NOT EXISTS login_attempts (
  id           TEXT PRIMARY KEY,
  identifier   TEXT NOT NULL,   -- normalised email or username
  ip           TEXT NOT NULL,
  success      INTEGER NOT NULL,
  reason       TEXT,
  created_at   INTEGER NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_login_ip ON login_attempts(ip, created_at);
CREATE INDEX IF NOT EXISTS idx_login_ident ON login_attempts(identifier, created_at);

CREATE TABLE IF NOT EXISTS api_rate_limits (
  bucket       TEXT PRIMARY KEY,
  count        INTEGER NOT NULL DEFAULT 0,
  window_start INTEGER NOT NULL
);

CREATE TABLE IF NOT EXISTS audit_logs (
  id          TEXT PRIMARY KEY,
  actor_id    TEXT,
  action      TEXT NOT NULL,
  entity_type TEXT,
  entity_id   TEXT,
  meta        TEXT NOT NULL DEFAULT '{}',
  ip          TEXT,
  created_at  INTEGER NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_audit_actor ON audit_logs(actor_id, created_at);
CREATE INDEX IF NOT EXISTS idx_audit_action ON audit_logs(action, created_at);

-- ---------------------------------------------------------------------------
-- 2. CATALOG: universities -> branches -> semesters -> subjects -> topics
-- ---------------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS universities (
  id         TEXT PRIMARY KEY,
  name       TEXT NOT NULL,
  code       TEXT,
  country    TEXT NOT NULL,
  region     TEXT,
  website    TEXT,
  created_at INTEGER NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_uni_country ON universities(country);

CREATE TABLE IF NOT EXISTS colleges (
  id            TEXT PRIMARY KEY,
  university_id TEXT REFERENCES universities(id) ON DELETE SET NULL,
  name          TEXT NOT NULL,
  city          TEXT,
  country       TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS branches (
  id          TEXT PRIMARY KEY,
  slug        TEXT NOT NULL UNIQUE,
  name        TEXT NOT NULL,
  category    TEXT NOT NULL,      -- cse | electronics | mechanical | civil | chemical | bio | other
  description TEXT,
  icon        TEXT,
  color       TEXT,
  order_index INTEGER NOT NULL DEFAULT 0,
  parent_id   TEXT REFERENCES branches(id) ON DELETE SET NULL,
  is_active   INTEGER NOT NULL DEFAULT 1
);
CREATE INDEX IF NOT EXISTS idx_branch_cat ON branches(category);

CREATE TABLE IF NOT EXISTS semesters (
  id     INTEGER PRIMARY KEY,
  label  TEXT NOT NULL,
  year   INTEGER
);

-- A curriculum binds (university, branch) to a concrete subject list so the
-- platform never hard-codes a syllabus in the frontend.
CREATE TABLE IF NOT EXISTS curricula (
  id            TEXT PRIMARY KEY,
  university_id TEXT NOT NULL REFERENCES universities(id) ON DELETE CASCADE,
  branch_id     TEXT NOT NULL REFERENCES branches(id) ON DELETE CASCADE,
  name          TEXT NOT NULL,
  effective_year INTEGER NOT NULL DEFAULT 2024,
  is_active     INTEGER NOT NULL DEFAULT 1,
  UNIQUE (university_id, branch_id, effective_year)
);

CREATE TABLE IF NOT EXISTS curriculum_subjects (
  curriculum_id TEXT NOT NULL REFERENCES curricula(id) ON DELETE CASCADE,
  subject_id    TEXT NOT NULL REFERENCES subjects(id) ON DELETE CASCADE,
  semester_id   INTEGER NOT NULL REFERENCES semesters(id) ON DELETE SET NULL,
  is_core       INTEGER NOT NULL DEFAULT 1,
  PRIMARY KEY (curriculum_id, subject_id)
);

CREATE TABLE IF NOT EXISTS subjects (
  id            TEXT PRIMARY KEY,
  slug          TEXT NOT NULL UNIQUE,
  name          TEXT NOT NULL,
  branch_id     TEXT REFERENCES branches(id) ON DELETE SET NULL,
  semester_id   INTEGER REFERENCES semesters(id) ON DELETE SET NULL,
  code          TEXT,
  credits       INTEGER,
  difficulty    TEXT NOT NULL DEFAULT 'medium',
  description   TEXT,
  icon          TEXT,
  color         TEXT,
  is_first_year INTEGER NOT NULL DEFAULT 0,
  order_index   INTEGER NOT NULL DEFAULT 0,
  status        TEXT NOT NULL DEFAULT 'published'
);
CREATE INDEX IF NOT EXISTS idx_subject_branch ON subjects(branch_id);
CREATE INDEX IF NOT EXISTS idx_subject_sem ON subjects(semester_id);

CREATE TABLE IF NOT EXISTS modules (
  id          TEXT PRIMARY KEY,
  subject_id  TEXT NOT NULL REFERENCES subjects(id) ON DELETE CASCADE,
  slug        TEXT NOT NULL,
  title       TEXT NOT NULL,
  summary     TEXT,
  order_index INTEGER NOT NULL DEFAULT 0,
  UNIQUE (subject_id, slug)
);

CREATE TABLE IF NOT EXISTS topics (
  id             TEXT PRIMARY KEY,
  slug           TEXT NOT NULL UNIQUE,
  subject_id     TEXT NOT NULL REFERENCES subjects(id) ON DELETE CASCADE,
  module_id      TEXT REFERENCES modules(id) ON DELETE SET NULL,
  title          TEXT NOT NULL,
  summary        TEXT,
  difficulty     TEXT NOT NULL DEFAULT 'medium',
  est_minutes    INTEGER NOT NULL DEFAULT 20,
  order_index    INTEGER NOT NULL DEFAULT 0,
  prerequisites  TEXT NOT NULL DEFAULT '[]',
  tags           TEXT NOT NULL DEFAULT '[]',
  status         TEXT NOT NULL DEFAULT 'published',
  author_id      TEXT REFERENCES users(id) ON DELETE SET NULL,
  reviewer_id    TEXT REFERENCES users(id) ON DELETE SET NULL,
  accuracy_state TEXT NOT NULL DEFAULT 'reviewed',
  source_ref     TEXT,
  version        INTEGER NOT NULL DEFAULT 1,
  view_count     INTEGER NOT NULL DEFAULT 0,
  created_at     INTEGER NOT NULL,
  updated_at     INTEGER NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_topic_subject ON topics(subject_id, order_index);
CREATE INDEX IF NOT EXISTS idx_topic_module ON topics(module_id);

-- ---------------------------------------------------------------------------
-- 3. LEARNING CONTENT: notes, sections, diagrams, formulas
-- ---------------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS notes (
  id            TEXT PRIMARY KEY,
  topic_id      TEXT NOT NULL REFERENCES topics(id) ON DELETE CASCADE,
  quality_level TEXT NOT NULL DEFAULT 'standard', -- beginner|standard|advanced|industry
  language      TEXT NOT NULL DEFAULT 'en',
  status        TEXT NOT NULL DEFAULT 'published',
  author_id     TEXT REFERENCES users(id) ON DELETE SET NULL,
  reviewer_id   TEXT REFERENCES users(id) ON DELETE SET NULL,
  version       INTEGER NOT NULL DEFAULT 1,
  created_at    INTEGER NOT NULL,
  updated_at    INTEGER NOT NULL,
  UNIQUE (topic_id, quality_level, language)
);

-- The 13-section engineering note template (see docs/NOTE_TEMPLATE.md)
CREATE TABLE IF NOT EXISTS note_sections (
  id          TEXT PRIMARY KEY,
  note_id     TEXT NOT NULL REFERENCES notes(id) ON DELETE CASCADE,
  kind        TEXT NOT NULL,
  title       TEXT NOT NULL,
  body        TEXT NOT NULL,
  callout     TEXT,          -- remember | warning | exam | interview | realworld
  order_index INTEGER NOT NULL DEFAULT 0
);
CREATE INDEX IF NOT EXISTS idx_section_note ON note_sections(note_id, order_index);

CREATE TABLE IF NOT EXISTS diagrams (
  id         TEXT PRIMARY KEY,
  topic_id   TEXT NOT NULL REFERENCES topics(id) ON DELETE CASCADE,
  title      TEXT NOT NULL,
  kind       TEXT NOT NULL DEFAULT 'svg',   -- svg | interactive | image | mermaid
  spec       TEXT NOT NULL,                 -- SVG markup or interactive node spec
  caption    TEXT,
  hotspots   TEXT NOT NULL DEFAULT '[]',    -- [{x,y,w,h,label,explain}]
  source_ref TEXT,
  created_at INTEGER NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_diagram_topic ON diagrams(topic_id);

CREATE TABLE IF NOT EXISTS formulas (
  id            TEXT PRIMARY KEY,
  slug          TEXT NOT NULL UNIQUE,
  subject_id    TEXT REFERENCES subjects(id) ON DELETE SET NULL,
  topic_id      TEXT REFERENCES topics(id) ON DELETE CASCADE,
  category      TEXT NOT NULL,
  name          TEXT NOT NULL,
  latex         TEXT NOT NULL,
  variables     TEXT NOT NULL DEFAULT '[]', -- [{symbol,name,unit}]
  meaning       TEXT,
  application   TEXT,
  example_latex TEXT,
  constraints   TEXT,
  order_index   INTEGER NOT NULL DEFAULT 0
);
CREATE INDEX IF NOT EXISTS idx_formula_subject ON formulas(subject_id);
CREATE INDEX IF NOT EXISTS idx_formula_cat ON formulas(category);

-- ---------------------------------------------------------------------------
-- 4. PRACTICE: questions, DPP sets, submissions, mistakes
-- ---------------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS questions (
  id            TEXT PRIMARY KEY,
  slug          TEXT NOT NULL UNIQUE,
  topic_id      TEXT REFERENCES topics(id) ON DELETE SET NULL,
  subject_id    TEXT REFERENCES subjects(id) ON DELETE SET NULL,
  kind          TEXT NOT NULL,             -- mcq|numerical|conceptual|debug|diagram|case|design|interview
  difficulty    TEXT NOT NULL DEFAULT 'medium',
  stem          TEXT NOT NULL,
  context       TEXT,
  explanation   TEXT,
  answer_index  INTEGER,
  answer_text   TEXT,
  tolerance     REAL,
  code_language TEXT,
  starter_code  TEXT,
  time_weight   INTEGER NOT NULL DEFAULT 1,
  tags          TEXT NOT NULL DEFAULT '[]',
  author_id     TEXT REFERENCES users(id) ON DELETE SET NULL,
  is_active     INTEGER NOT NULL DEFAULT 1,
  created_at    INTEGER NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_q_topic ON questions(topic_id, difficulty);
CREATE INDEX IF NOT EXISTS idx_q_subject ON questions(subject_id, kind);

CREATE TABLE IF NOT EXISTS question_options (
  id          TEXT PRIMARY KEY,
  question_id TEXT NOT NULL REFERENCES questions(id) ON DELETE CASCADE,
  label       TEXT NOT NULL,
  body        TEXT NOT NULL,
  is_correct  INTEGER NOT NULL DEFAULT 0,
  rationale   TEXT,
  order_index INTEGER NOT NULL DEFAULT 0
);
CREATE INDEX IF NOT EXISTS idx_opt_q ON question_options(question_id, order_index);

CREATE TABLE IF NOT EXISTS dpp_sets (
  id               TEXT PRIMARY KEY,
  date             TEXT NOT NULL UNIQUE,     -- YYYY-MM-DD
  title            TEXT NOT NULL,
  subject_id       TEXT REFERENCES subjects(id) ON DELETE SET NULL,
  difficulty       TEXT NOT NULL DEFAULT 'mixed',
  duration_minutes INTEGER NOT NULL DEFAULT 30,
  published        INTEGER NOT NULL DEFAULT 1,
  created_at       INTEGER NOT NULL
);

CREATE TABLE IF NOT EXISTS dpp_questions (
  set_id      TEXT NOT NULL REFERENCES dpp_sets(id) ON DELETE CASCADE,
  question_id TEXT NOT NULL REFERENCES questions(id) ON DELETE CASCADE,
  position    INTEGER NOT NULL,
  PRIMARY KEY (set_id, question_id)
);
CREATE INDEX IF NOT EXISTS idx_dppq_set ON dpp_questions(set_id, position);

-- Hot table. Partitioned by range(created_at) in Postgres.
CREATE TABLE IF NOT EXISTS submissions (
  id           TEXT PRIMARY KEY,
  user_id      TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  question_id  TEXT NOT NULL REFERENCES questions(id) ON DELETE CASCADE,
  dpp_set_id   TEXT REFERENCES dpp_sets(id) ON DELETE SET NULL,
  answer_index INTEGER,
  answer_text  TEXT,
  is_correct   INTEGER NOT NULL,
  time_ms      INTEGER,
  created_at   INTEGER NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_sub_user ON submissions(user_id, created_at);
CREATE INDEX IF NOT EXISTS idx_sub_question ON submissions(question_id, is_correct);
CREATE INDEX IF NOT EXISTS idx_sub_topic ON submissions(user_id, question_id);

CREATE TABLE IF NOT EXISTS mistakes (
  id          TEXT PRIMARY KEY,
  user_id     TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  question_id TEXT NOT NULL REFERENCES questions(id) ON DELETE CASCADE,
  given       TEXT,
  correct     TEXT,
  resolved_at INTEGER,
  created_at  INTEGER NOT NULL,
  UNIQUE (user_id, question_id)
);
CREATE INDEX IF NOT EXISTS idx_mistake_user ON mistakes(user_id, created_at);

-- ---------------------------------------------------------------------------
-- 5. CODING: languages, problems, test cases, submissions
-- ---------------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS programming_languages (
  id          TEXT PRIMARY KEY,
  slug        TEXT NOT NULL UNIQUE,
  name        TEXT NOT NULL,
  icon        TEXT,
  color       TEXT,
  blurb       TEXT,
  judge_slug  TEXT,                -- Judge0 language id / runner key
  runnable    INTEGER NOT NULL DEFAULT 1,
  order_index INTEGER NOT NULL DEFAULT 0
);

CREATE TABLE IF NOT EXISTS language_modules (
  id          TEXT PRIMARY KEY,
  language_id TEXT NOT NULL REFERENCES programming_languages(id) ON DELETE CASCADE,
  slug        TEXT NOT NULL,
  title       TEXT NOT NULL,
  summary     TEXT,
  body        TEXT NOT NULL,
  example     TEXT,
  exercise    TEXT,
  order_index INTEGER NOT NULL DEFAULT 0,
  UNIQUE (language_id, slug)
);

CREATE TABLE IF NOT EXISTS coding_problems (
  id              TEXT PRIMARY KEY,
  slug            TEXT NOT NULL UNIQUE,
  title           TEXT NOT NULL,
  statement       TEXT NOT NULL,
  difficulty      TEXT NOT NULL DEFAULT 'medium',
  topics          TEXT NOT NULL DEFAULT '[]',
  hints           TEXT NOT NULL DEFAULT '[]',
  editorial       TEXT,
  solution_md     TEXT,
  tags            TEXT NOT NULL DEFAULT '[]',
  expected_time   TEXT,
  expected_space  TEXT,
  -- Names the stdin/stdout harness appended to a submission before it runs.
  -- Wrappers live in backend/engineverse/drivers.py, so adding a new problem
  -- shape needs no change to the judge.
  wrapper         TEXT NOT NULL DEFAULT 'raw',
  solve_count     INTEGER NOT NULL DEFAULT 0,
  attempt_count   INTEGER NOT NULL DEFAULT 0,
  is_premium      INTEGER NOT NULL DEFAULT 0,
  created_at      INTEGER NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_cp_difficulty ON coding_problems(difficulty);

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
  is_sample   INTEGER NOT NULL DEFAULT 0,
  explanation TEXT,
  order_index INTEGER NOT NULL DEFAULT 0
);
CREATE INDEX IF NOT EXISTS idx_tc_problem ON coding_testcases(problem_id, order_index);

CREATE TABLE IF NOT EXISTS coding_submissions (
  id          TEXT PRIMARY KEY,
  user_id     TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  problem_id  TEXT NOT NULL REFERENCES coding_problems(id) ON DELETE CASCADE,
  language    TEXT NOT NULL,
  code        TEXT NOT NULL,
  status      TEXT NOT NULL,        -- accepted|wrong_answer|runtime_error|timeout|compile_error|internal_error
  passed      INTEGER NOT NULL DEFAULT 0,
  total       INTEGER NOT NULL DEFAULT 0,
  runtime_ms  INTEGER,
  memory_kb   INTEGER,
  stderr      TEXT,
  is_accepted INTEGER NOT NULL DEFAULT 0,
  created_at  INTEGER NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_csub_user ON coding_submissions(user_id, created_at);
CREATE INDEX IF NOT EXISTS idx_csub_problem ON coding_submissions(problem_id, is_accepted);

-- ---------------------------------------------------------------------------
-- 6. PROJECTS
-- ---------------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS projects (
  id                  TEXT PRIMARY KEY,
  slug                TEXT NOT NULL UNIQUE,
  title               TEXT NOT NULL,
  branch_id           TEXT REFERENCES branches(id) ON DELETE SET NULL,
  subject_id          TEXT REFERENCES subjects(id) ON DELETE SET NULL,
  difficulty          TEXT NOT NULL DEFAULT 'intermediate',
  category            TEXT NOT NULL DEFAULT 'software',
  est_hours           INTEGER NOT NULL DEFAULT 20,
  summary             TEXT,
  problem_statement   TEXT,
  objective           TEXT,
  prerequisites       TEXT NOT NULL DEFAULT '[]',
  hardware            TEXT,
  software            TEXT,
  architecture        TEXT,
  source_code         TEXT,
  database_design     TEXT,
  testing             TEXT,
  expected_output     TEXT,
  improvements        TEXT,
  resume_md           TEXT,
  interview_questions TEXT NOT NULL DEFAULT '[]',
  tech                TEXT NOT NULL DEFAULT '[]',
  skills              TEXT NOT NULL DEFAULT '[]',
  repo_url            TEXT,
  demo_url            TEXT,
  report_template_url TEXT,
  build_count         INTEGER NOT NULL DEFAULT 0,
  status              TEXT NOT NULL DEFAULT 'published',
  order_index         INTEGER NOT NULL DEFAULT 0,
  created_at          INTEGER NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_project_difficulty ON projects(difficulty);
CREATE INDEX IF NOT EXISTS idx_project_branch ON projects(branch_id);

CREATE TABLE IF NOT EXISTS project_steps (
  id          TEXT PRIMARY KEY,
  project_id  TEXT NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
  phase       TEXT NOT NULL,
  title       TEXT NOT NULL,
  body        TEXT NOT NULL,
  order_index INTEGER NOT NULL DEFAULT 0
);
CREATE INDEX IF NOT EXISTS idx_pstep ON project_steps(project_id, order_index);

CREATE TABLE IF NOT EXISTS project_resources (
  id         TEXT PRIMARY KEY,
  project_id TEXT NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
  kind       TEXT NOT NULL,
  title      TEXT NOT NULL,
  url        TEXT,
  note       TEXT
);

-- ---------------------------------------------------------------------------
-- 7. MEDIA & LIBRARY: videos, books, resources
-- ---------------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS videos (
  id          TEXT PRIMARY KEY,
  slug        TEXT NOT NULL UNIQUE,
  title       TEXT NOT NULL,
  channel     TEXT NOT NULL,
  url         TEXT NOT NULL,
  embed_id    TEXT,
  duration_s  INTEGER,
  language    TEXT NOT NULL DEFAULT 'en',
  level       TEXT NOT NULL DEFAULT 'beginner',
  category    TEXT NOT NULL DEFAULT 'concept',  -- beginner|concept|numerical|revision|exam
  topic_id    TEXT REFERENCES topics(id) ON DELETE SET NULL,
  subject_id  TEXT REFERENCES subjects(id) ON DELETE SET NULL,
  rating      INTEGER NOT NULL DEFAULT 4,
  why_useful  TEXT,
  embeddable  INTEGER NOT NULL DEFAULT 1,
  created_at  INTEGER NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_video_topic ON videos(topic_id);

CREATE TABLE IF NOT EXISTS books (
  id            TEXT PRIMARY KEY,
  slug          TEXT NOT NULL UNIQUE,
  title         TEXT NOT NULL,
  author        TEXT NOT NULL,
  subject_id    TEXT REFERENCES subjects(id) ON DELETE SET NULL,
  branch_id     TEXT REFERENCES branches(id) ON DELETE SET NULL,
  level         TEXT NOT NULL DEFAULT 'undergraduate',
  description   TEXT,
  why_read      TEXT,
  topics_covered TEXT NOT NULL DEFAULT '[]',
  legal_url     TEXT NOT NULL,
  access_kind   TEXT NOT NULL DEFAULT 'official',  -- official|open_access|library|archive
  publisher     TEXT,
  created_at    INTEGER NOT NULL
);

CREATE TABLE IF NOT EXISTS resources (
  id          TEXT PRIMARY KEY,
  slug        TEXT NOT NULL UNIQUE,
  title       TEXT NOT NULL,
  url         TEXT NOT NULL,
  kind        TEXT NOT NULL,       -- documentation|course|tool|dataset|simulator|paper|playlist
  category    TEXT NOT NULL DEFAULT 'documentation',
  branch_id   TEXT REFERENCES branches(id) ON DELETE SET NULL,
  subject_id  TEXT REFERENCES subjects(id) ON DELETE SET NULL,
  level       TEXT NOT NULL DEFAULT 'beginner',
  format      TEXT NOT NULL DEFAULT 'web',
  language    TEXT NOT NULL DEFAULT 'en',
  is_free     INTEGER NOT NULL DEFAULT 1,
  description TEXT,
  created_at  INTEGER NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_res_kind ON resources(kind);

-- ---------------------------------------------------------------------------
-- 8. ROADMAPS, SKILL TREES, FLASHCARDS, REVISION
-- ---------------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS roadmaps (
  id          TEXT PRIMARY KEY,
  slug        TEXT NOT NULL UNIQUE,
  title       TEXT NOT NULL,
  kind        TEXT NOT NULL DEFAULT 'subject',  -- subject|career|project|language
  branch_id   TEXT REFERENCES branches(id) ON DELETE SET NULL,
  target_role TEXT,
  summary     TEXT,
  description TEXT,
  order_index INTEGER NOT NULL DEFAULT 0
);

CREATE TABLE IF NOT EXISTS roadmap_nodes (
  id          TEXT PRIMARY KEY,
  roadmap_id  TEXT NOT NULL REFERENCES roadmaps(id) ON DELETE CASCADE,
  title       TEXT NOT NULL,
  summary     TEXT,
  ref_type    TEXT,               -- topic|subject|project|coding_problem|resource
  ref_id      TEXT,
  is_required INTEGER NOT NULL DEFAULT 1,
  order_index INTEGER NOT NULL DEFAULT 0
);
CREATE INDEX IF NOT EXISTS idx_rnode ON roadmap_nodes(roadmap_id, order_index);

CREATE TABLE IF NOT EXISTS flashcards (
  id         TEXT PRIMARY KEY,
  topic_id   TEXT REFERENCES topics(id) ON DELETE CASCADE,
  subject_id TEXT REFERENCES subjects(id) ON DELETE SET NULL,
  deck       TEXT NOT NULL DEFAULT 'core',
  front      TEXT NOT NULL,
  back       TEXT NOT NULL,
  hint       TEXT,
  difficulty TEXT NOT NULL DEFAULT 'medium',
  created_at INTEGER NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_flash_topic ON flashcards(topic_id);

-- SM-2 spaced repetition state per learner per card.
CREATE TABLE IF NOT EXISTS user_flashcards (
  user_id         TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  flashcard_id    TEXT NOT NULL REFERENCES flashcards(id) ON DELETE CASCADE,
  ease_factor     REAL NOT NULL DEFAULT 2.5,
  interval_days   REAL NOT NULL DEFAULT 0,
  repetitions     INTEGER NOT NULL DEFAULT 0,
  due_at          INTEGER NOT NULL,
  last_reviewed_at INTEGER,
  PRIMARY KEY (user_id, flashcard_id)
);
CREATE INDEX IF NOT EXISTS idx_uf_due ON user_flashcards(user_id, due_at);

-- ---------------------------------------------------------------------------
-- 9. PROGRESS, GAMIFICATION, BOOKMARKS, PERSONAL NOTES
-- ---------------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS user_progress (
  user_id       TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  topic_id      TEXT NOT NULL REFERENCES topics(id) ON DELETE CASCADE,
  status        TEXT NOT NULL DEFAULT 'started',  -- started|in_progress|completed|mastered
  mastery       INTEGER NOT NULL DEFAULT 0,       -- 0..100
  time_spent_s  INTEGER NOT NULL DEFAULT 0,
  last_viewed_at INTEGER NOT NULL,
  completed_at  INTEGER,
  PRIMARY KEY (user_id, topic_id)
);

CREATE TABLE IF NOT EXISTS bookmarks (
  user_id     TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  entity_type TEXT NOT NULL,
  entity_id   TEXT NOT NULL,
  note        TEXT,
  created_at  INTEGER NOT NULL,
  PRIMARY KEY (user_id, entity_type, entity_id)
);

CREATE TABLE IF NOT EXISTS personal_notes (
  id          TEXT PRIMARY KEY,
  user_id     TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  entity_type TEXT NOT NULL DEFAULT 'topic',
  entity_id   TEXT NOT NULL,
  content     TEXT NOT NULL,
  is_private  INTEGER NOT NULL DEFAULT 1,
  created_at  INTEGER NOT NULL,
  updated_at  INTEGER NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_pnote ON personal_notes(user_id, entity_type, entity_id);

CREATE TABLE IF NOT EXISTS xp_events (
  id          TEXT PRIMARY KEY,
  user_id     TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  amount      INTEGER NOT NULL,
  reason      TEXT NOT NULL,
  entity_type TEXT,
  entity_id   TEXT,
  created_at  INTEGER NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_xp_user ON xp_events(user_id, created_at);

CREATE TABLE IF NOT EXISTS streaks (
  user_id          TEXT PRIMARY KEY REFERENCES users(id) ON DELETE CASCADE,
  current_streak   INTEGER NOT NULL DEFAULT 0,
  longest_streak   INTEGER NOT NULL DEFAULT 0,
  last_active_day  TEXT,
  freeze_count     INTEGER NOT NULL DEFAULT 0,
  total_xp         INTEGER NOT NULL DEFAULT 0,
  level            INTEGER NOT NULL DEFAULT 1
);

-- GitHub-style contribution heatmap (one row per learner per day).
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
);
CREATE INDEX IF NOT EXISTS idx_activity_day ON activity(day);

CREATE TABLE IF NOT EXISTS badges (
  id          TEXT PRIMARY KEY,
  slug        TEXT NOT NULL UNIQUE,
  name        TEXT NOT NULL,
  description TEXT NOT NULL,
  icon        TEXT NOT NULL DEFAULT 'award',
  tier        TEXT NOT NULL DEFAULT 'bronze',
  criterion   TEXT NOT NULL   -- JSON rule evaluated by lib/gamification
);

CREATE TABLE IF NOT EXISTS user_badges (
  user_id   TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  badge_id  TEXT NOT NULL REFERENCES badges(id) ON DELETE CASCADE,
  earned_at INTEGER NOT NULL,
  PRIMARY KEY (user_id, badge_id)
);

-- ---------------------------------------------------------------------------
-- 10. COMMUNITY
-- ---------------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS discussions (
  id               TEXT PRIMARY KEY,
  user_id          TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  title            TEXT NOT NULL,
  body             TEXT NOT NULL,
  kind             TEXT NOT NULL DEFAULT 'question', -- question|discussion|project|doubt
  tags             TEXT NOT NULL DEFAULT '[]',
  entity_type      TEXT,
  entity_id        TEXT,
  upvotes          INTEGER NOT NULL DEFAULT 0,
  reply_count      INTEGER NOT NULL DEFAULT 0,
  is_resolved      INTEGER NOT NULL DEFAULT 0,
  is_locked        INTEGER NOT NULL DEFAULT 0,
  is_hidden        INTEGER NOT NULL DEFAULT 0,
  created_at       INTEGER NOT NULL,
  last_activity_at INTEGER NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_disc_recent ON discussions(last_activity_at DESC);

CREATE TABLE IF NOT EXISTS comments (
  id            TEXT PRIMARY KEY,
  discussion_id TEXT NOT NULL REFERENCES discussions(id) ON DELETE CASCADE,
  parent_id     TEXT REFERENCES comments(id) ON DELETE CASCADE,
  user_id       TEXT REFERENCES users(id) ON DELETE SET NULL,
  body          TEXT NOT NULL,
  upvotes       INTEGER NOT NULL DEFAULT 0,
  is_ai         INTEGER NOT NULL DEFAULT 0,
  is_deleted    INTEGER NOT NULL DEFAULT 0,
  created_at    INTEGER NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_comment_disc ON comments(discussion_id, created_at);

CREATE TABLE IF NOT EXISTS votes (
  user_id     TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  entity_type TEXT NOT NULL,
  entity_id   TEXT NOT NULL,
  value       INTEGER NOT NULL,
  created_at  INTEGER NOT NULL,
  PRIMARY KEY (user_id, entity_type, entity_id)
);

CREATE TABLE IF NOT EXISTS reports (
  id          TEXT PRIMARY KEY,
  reporter_id TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  entity_type TEXT NOT NULL,
  entity_id   TEXT NOT NULL,
  reason      TEXT NOT NULL,
  detail      TEXT,
  status      TEXT NOT NULL DEFAULT 'open',
  created_at  INTEGER NOT NULL
);

-- ---------------------------------------------------------------------------
-- 11. NOTIFICATIONS, CERTIFICATES, MONETISATION, CONTESTS, CONFIG
-- ---------------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS notifications (
  id         TEXT PRIMARY KEY,
  user_id    TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  type       TEXT NOT NULL,
  title      TEXT NOT NULL,
  body       TEXT,
  url        TEXT,
  read_at    INTEGER,
  created_at INTEGER NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_notif_user ON notifications(user_id, created_at DESC);

CREATE TABLE IF NOT EXISTS certificates (
  id          TEXT PRIMARY KEY,
  user_id     TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  kind        TEXT NOT NULL,      -- course|subject|path|project|challenge
  entity_type TEXT NOT NULL,
  entity_id   TEXT NOT NULL,
  title       TEXT NOT NULL,
  verify_id   TEXT NOT NULL UNIQUE,
  issued_at   INTEGER NOT NULL,
  meta        TEXT NOT NULL DEFAULT '{}'
);

CREATE TABLE IF NOT EXISTS plans (
  id          TEXT PRIMARY KEY,
  slug        TEXT NOT NULL UNIQUE,
  name        TEXT NOT NULL,
  price_cents INTEGER NOT NULL DEFAULT 0,
  currency    TEXT NOT NULL DEFAULT 'USD',
  interval    TEXT NOT NULL DEFAULT 'month',
  features    TEXT NOT NULL DEFAULT '[]',
  is_active   INTEGER NOT NULL DEFAULT 1
);

CREATE TABLE IF NOT EXISTS subscriptions (
  id          TEXT PRIMARY KEY,
  user_id     TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  plan_id     TEXT NOT NULL REFERENCES plans(id) ON DELETE RESTRICT,
  status      TEXT NOT NULL DEFAULT 'active',
  started_at  INTEGER NOT NULL,
  expires_at  INTEGER
);

CREATE TABLE IF NOT EXISTS payments (
  id             TEXT PRIMARY KEY,
  user_id        TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  subscription_id TEXT REFERENCES subscriptions(id) ON DELETE SET NULL,
  amount_cents   INTEGER NOT NULL,
  currency       TEXT NOT NULL DEFAULT 'USD',
  provider       TEXT NOT NULL,
  provider_ref   TEXT,
  status         TEXT NOT NULL,
  created_at     INTEGER NOT NULL
);

CREATE TABLE IF NOT EXISTS contests (
  id          TEXT PRIMARY KEY,
  slug        TEXT NOT NULL UNIQUE,
  title       TEXT NOT NULL,
  kind        TEXT NOT NULL DEFAULT 'weekly',
  starts_at   INTEGER NOT NULL,
  ends_at     INTEGER NOT NULL,
  description TEXT,
  published   INTEGER NOT NULL DEFAULT 0
);

CREATE TABLE IF NOT EXISTS contest_problems (
  contest_id  TEXT NOT NULL REFERENCES contests(id) ON DELETE CASCADE,
  question_id TEXT REFERENCES questions(id) ON DELETE CASCADE,
  problem_id  TEXT REFERENCES coding_problems(id) ON DELETE CASCADE,
  points      INTEGER NOT NULL DEFAULT 10,
  order_index INTEGER NOT NULL DEFAULT 0
);

CREATE TABLE IF NOT EXISTS contest_submissions (
  id          TEXT PRIMARY KEY,
  contest_id  TEXT NOT NULL REFERENCES contests(id) ON DELETE CASCADE,
  user_id     TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  question_id TEXT REFERENCES questions(id) ON DELETE CASCADE,
  problem_id  TEXT REFERENCES coding_problems(id) ON DELETE CASCADE,
  score       INTEGER NOT NULL DEFAULT 0,
  created_at  INTEGER NOT NULL
);

-- Brand + feature configuration. The product name is data, never code.
CREATE TABLE IF NOT EXISTS site_config (
  key        TEXT PRIMARY KEY,
  value      TEXT NOT NULL,
  updated_at INTEGER NOT NULL
);

-- ---------------------------------------------------------------------------
-- 12. FULL-TEXT SEARCH (PostgreSQL: tsvector + pg_trgm; see db/postgres)
-- ---------------------------------------------------------------------------

CREATE VIRTUAL TABLE IF NOT EXISTS search_index USING fts5(
  entity_type UNINDEXED,
  entity_id   UNINDEXED,
  title,
  body,
  branch      UNINDEXED,
  semester    UNINDEXED,
  difficulty  UNINDEXED,
  tags        UNINDEXED,
  tokenize = 'porter unicode61'
);
