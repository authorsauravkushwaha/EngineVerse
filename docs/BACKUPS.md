# Backups

A development SQLite copy has been taken with `scripts/backup_sqlite.py`. The
file lives under `backups/`, which is gitignored. It is not a production dump.
Docker is not available here, so the compose `backup` service has not been
started and no Postgres dump exists in this repository.

When you run `docker compose -f deploy/docker-compose.yml up`, that service
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
