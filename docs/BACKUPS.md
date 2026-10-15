# Backups

A development SQLite copy has been taken with `scripts/backup_sqlite.py`. The
file lives under `backups/`, which is gitignored. It is not a production dump.
Docker is not available here, so the compose `backup` service has not been
started and no Postgres dump exists in this repository.

When you run `docker compose --env-file deploy/.env -f deploy/docker-compose.yml up`, that service
waits for `release`, then runs `pg_dump` into the `pg-backups` volume and
repeats daily. The volume is not published and is not mounted into `web`.
The client uses libpq environment variables. It does not print the password.
Keeping the service defined is not the same as having restored from it.

## Dump

`scripts/backup_postgres.sh` runs `pg_dump --format=custom`. It refuses to
overwrite an existing file. It does not print `ENGINEVERSE_DB_URL`, because
that URL contains the password.

```bash
mkdir -p backups
ENGINEVERSE_DB_URL='postgresql://engineverse:PASSWORD@127.0.0.1:5432/engineverse' \
  scripts/backup_postgres.sh backups/engineverse-$(date -u +%Y%m%dT%H%M%SZ).dump
```

Use the bootstrap role for the dump if the runtime role cannot read every
catalogue table you care about. `engineverse_app` has `SELECT` on tables that
existed when the grants were applied. A dump of learner data is personal data.
Keep it on encrypted storage the web server does not serve. `backups/` and
`*.dump` are git-ignored. Do not commit a dump. Do not paste a dump into an
issue.

Take a dump before a release that runs `scripts/seed.py`, because that command
upserts seeded rows and overwrites CMS edits to those ids. `scripts/release.py`
does not do that when subjects already exist.

The official Postgres image does not re-run init scripts on an existing
volume. A backup is the way back from a bad migration. The schema file in git
is not a backup of learner rows.

## Optional encrypted snapshots in a **private** GitHub repository

GitHub is **not** the live learner database. Never commit `.dump`, `.sqlite`,
account rows, password hashes, `.env` or the age private identity to the public
EngineVerse repository. If you want an off-site copy under your own GitHub
account, `deploy/github-backups.yml` opts into a *separate private repository*
containing only **age-encrypted** PostgreSQL snapshots as Release assets.
There is no plaintext dump file: `pg_dump | age` streams into an encrypted
archive on a temporary filesystem; `gh` uploads that archive after checking
`isPrivate` on every run. The worker has a scoped GitHub token and database
credentials, not an endpoint exposed to website visitors. No backup is
uploaded until you set the variables and start the overlay yourself.

1. **Offline**, generate an age X25519 identity on a machine you control:

   ```bash
   umask 077
   age-keygen -o /secure/offline/engineverse-age-key.txt
   grep '^# public key:' /secure/offline/engineverse-age-key.txt
   ```

   Keep the **private identity** securely outside the app server *and* outside
   GitHub; losing it makes all snapshots unreadable. Record the public `age1...`
   **recipient** for `ENGINEVERSE_BACKUP_AGE_RECIPIENT`.
2. Create a **different private repository with a default branch** (e.g.
   `your-owner/engineverse-private-backups`, initial README), and a fine-grained
   GitHub token with **Contents: read/write** restricted to *that repo only*.
   Verify `gh repo view your-owner/engineverse-private-backups --json isPrivate`
   reports `true`. Place the token in the ignored `deploy/.env` under
   `ENGINEVERSE_BACKUP_GH_TOKEN`, the private repo name under
   `ENGINEVERSE_BACKUP_REPO` and the **public** recipient under
   `ENGINEVERSE_BACKUP_AGE_RECIPIENT`. Never put the token in a workflow log,
   issue, public repo, or chat.
3. On the server, after a successful base Compose release, run:

   ```bash
   docker compose --env-file deploy/.env -f deploy/docker-compose.yml -f deploy/github-backups.yml up -d --build
   docker compose --env-file deploy/.env -f deploy/docker-compose.yml -f deploy/github-backups.yml logs --tail=30 github-backup
   ```

   The worker attempts an encrypted dump immediately, then daily. It exits
   nonzero on dump, encryption, visibility or upload failure so a failed job
   cannot masquerade as a completed backup. Set up failure monitoring. It
   enforces a 512 MiB ciphertext limit: for a larger database, use a proper
   encrypted object store rather than silently truncating a GitHub Release.
   The existing `pg-backups` local volume is separate and remains available.

**Rehearse restoring on a disposable database** while retaining the offline key:

```bash
mkdir -m 700 restore-test
gh release download engineverse-backup-TIMESTAMP \
  -R your-owner/engineverse-private-backups --pattern '*.dump.age' --dir restore-test
age -d -i /secure/offline/engineverse-age-key.txt \
  -o restore-test/engineverse.dump restore-test/engineverse-backup-TIMESTAMP.dump.age
createdb engineverse_restore
pg_restore --no-owner --dbname engineverse_restore restore-test/engineverse.dump
```

Authenticate `gh` privately and supply libpq connection settings (`PGHOST`,
`PGUSER`, `PGPASSWORD`) through a secret store, not command-line passwords or
shell history. Decrypted data is sensitive, so use encrypted temporary
storage and remove it securely after testing. A release exists ≠ a successful
restore. This repository cannot verify your private database, GitHub backup
repo or offline recovery key.

**Retention and deletion:** The local backup service prunes snapshots after 14
days by default. The private GitHub Releases are intentionally *not*
auto-deleted; set and enforce an operator retention policy, and delete expired
releases and tags yourself. Deleting a live learner account does not rewrite
old backups. The site's Privacy page discloses this; an operator must handle
delete requests and backup expiry appropriately. If the backup repo ever
becomes public or the age identity leaks, stop the worker, rotate the recipient,
review access and treat it as an incident.

## Restore

Restore replaces the target database. Do it on a copy first. This repository
does not ship a restore script that guesses the target, because that is how a
dump gets loaded onto the live server by mistake.

```bash
createdb engineverse_restore
pg_restore --no-owner --dbname 'postgresql://engineverse:PASSWORD@127.0.0.1:5432/engineverse_restore' \
  backups/engineverse-TIMESTAMP.dump
```

Point a disposable process at `engineverse_restore` and check that you can
sign in and that a learner row you expect is present. Only then, with the
live site stopped, restore onto the live database. There is no automatic
failover and no claim that this has been rehearsed.

SQLite development files under `data/` are not production backups. Copying
`engineverse.sqlite` while the process is writing it can produce a torn file.
Use the backup API instead:

```bash
python scripts/backup_sqlite.py data/engineverse.sqlite backups/engineverse-dev.sqlite
```

The script refuses to overwrite the destination. It does not print a connection
URL. A copy made this way was integrity-checked in the workspace that added
this note. That check is not a restore rehearsal of Postgres.

## What a backup does not fix

- A leaked `ENGINEVERSE_SECRET`. Rotating it signs everyone out. See
  `docs/INCIDENT_RESPONSE.md`.
- A judge that was left on `python` or `java`. Production startup now refuses
  those modes. A backup does not undo what a submission read.
- A lost keystore. Application backups do not contain it, and should not.
