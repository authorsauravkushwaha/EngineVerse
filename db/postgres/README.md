# PostgreSQL schema

`schema.pg.sql` is the production data layer. It mirrors `db/schema.sql`
(SQLite, used for development) 1:1 in its *model* — same tables, same columns,
same relationships — and differs only where scale demands it.

```bash
createdb engineverse
psql "$DATABASE_URL" -f db/postgres/schema.pg.sql     # idempotent
```

The application picks this up with no code change: set `DB_URL` to a Postgres
DSN and `engineverse.db` routes through `PostgresConnection`, which rewrites `?`
placeholders to `%s`. Everything above the data layer is identical on both
backends.

## What changes for 1.5 billion users

### Hash partitioning on the hot tables

Sixteen tables are `PARTITION BY HASH` on the column every query already filters
by — usually `user_id`.

| Table | Partitions | Why |
|---|---|---|
| `submissions` | 256 | Every answer from every learner; the highest-volume write path |
| `activity` | 256 | One row per user per day — the second-largest table |
| `audit_logs` | 256 | Append-only, never updated, grows without bound |
| `coding_submissions` | 128 | Stores source code, so rows are bulky |
| `user_flashcards` | 128 | SRS state, read on every revision session |
| `user_progress` | 128 | Read on every dashboard render |
| `xp_events`, `notifications` | 128 | Per-user, high write rate |
| `sessions`, `profiles`, `mistakes`, `bookmarks`, `personal_notes`, `user_badges`, `votes` | 64 | |
| `login_attempts` | 32 | Only ever queried by identifier |
| `contest_submissions` | 32 | Bursty, bounded by contest size |

Hash partitioning is chosen over range or list because:

- **No rebalancing.** A range scheme on `created_at` needs new partitions minted
  on a schedule and hot rows all land in the newest one. Hash spreads writes
  evenly from the first insert to the billionth.
- **Partition pruning for free.** Every per-user query includes `user_id`, so
  Postgres reads one partition instead of scanning sixteen.
- **Tractable maintenance.** At these fan-outs the largest partition stays in the
  low tens of millions of rows, which keeps `VACUUM`, `REINDEX` and a single
  restore within reach.

`engineverse_create_partitions(parent, count)` builds the fan-out; the script
calls it for every partitioned table, and it is idempotent, so re-running the
schema is safe.

### Other production differences

- **`citext`** for `users.email` and `users.username` so uniqueness is
  case-insensitive without a separate lowercased column.
- **`jsonb`** instead of `TEXT` for JSON payloads, with a GIN index on
  `audit_logs.meta`, so operational data is queryable rather than opaque.
- **`tsvector` + GIN** for `search_index` in place of SQLite FTS5, with title
  weighted `A` and body `B`.
- **`BIGINT`** for epoch milliseconds and counters that a 32-bit int would
  overflow (`solve_count`, `attempt_count`, `total_xp`).
- **`engineverse_prune_before(table, cutoff_ms)`** deletes in batches and commits
  between them, so pruning an append-only table never holds one giant
  transaction open.

### Deliberately unchanged

- **ULID text primary keys.** Lexicographically sortable, so inserts append
  rather than scattering through the index, and they can be minted on any node
  with no sequence contention — which is what makes horizontal sharding
  possible later.
- **Epoch-millisecond integers for timestamps.** The application layer stays
  byte-identical across SQLite and Postgres.

## Scaling further

Partitioning buys headroom, not infinity. The next steps, in order:

1. **Read replicas** for the catalogue tables, which are read-heavy and rarely
   written.
2. **Detach-and-archive** old partitions of `audit_logs` and `activity` into cold
   storage rather than deleting them — the model already supports it because
   those tables are append-only.
3. **Shard by `user_id`** across nodes. The ULID keys and the `user_id`
   partitioning key are already aligned, so no rewrite is needed.

## Verification in this checkout

There is no PostgreSQL server in this workspace, so the schema has **not** been
applied to a live database here. It is parsed and checked for well-formedness
with `sqlglot` (141 statements, 68 `CREATE TABLE`, 0 unparsed) by
`backend/tests/test_postgres_schema.py`, and `.github/workflows/ci.yml` applies
it to a real PostgreSQL 16 service container on every push, which is the
authoritative check.
