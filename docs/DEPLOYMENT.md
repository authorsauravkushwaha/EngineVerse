# Deployment

This is how to run the application you already have. It is not a record of a
deployment. Nothing in this repository was published to a public host as part
of the production-readiness work, and a green test run is not that publication.

The brand name stays in site configuration. Do not hardcode a rename.

## What production refuses

With `ENGINEVERSE_ENV=production` the process will not start unless:

- `ENGINEVERSE_SECRET` is set, at least 32 characters, and not the development fallback
- `ENGINEVERSE_DB_URL` is a `postgresql://` URL
- `ENGINEVERSE_SITE_URL` is an `https://` origin
- `ENGINEVERSE_REVEAL_RESET_TOKEN` is off
- `ENGINEVERSE_JUDGE` is `disabled`, or `judge0` with `ENGINEVERSE_JUDGE0_URL`

`auto`, `python` and `java` run learner code on this server. Production refuses
them. A subprocess is not a separate container. `judge0` only means the
submission is sent to a URL you operate. This process does not verify that
host's isolation.

`SITE_URL`, `JUDGE` and `JAVA_SANDBOX_JAR` are accepted as aliases when the
`ENGINEVERSE_` names are unset. Compose sets the names the application reads.

## Git Bash on Windows

Use Git for Windows so the shell scripts and Compose files keep LF line
endings. In the repository:

```bash
git config core.autocrlf input
```

Create the virtualenv with the same Python you will run:

```bash
python -m venv .venv
source .venv/Scripts/activate
python -m pip install -r requirements.txt
cp .env.example .env
```

If `python` is not on `PATH`, use `py -3` instead. Git Bash paths look like
`/c/Users/you/EngineVerse`. Do not convert them to `C:\...` inside a bash
script. Docker Desktop must be running before `docker compose`.

Development seed, which creates the demo accounts and prints their passwords:

```bash
python scripts/seed.py --fresh
```

Do not point that command at a database that holds real accounts. `--fresh` is
refused when it finds users that are not the demo accounts, unless you pass
`--destroy-users`. Production refuses `--fresh` either way.

## Compose

```bash
cp deploy/.env.example deploy/.env
# edit deploy/.env. Generate values with:
#   python -c "import secrets; print(secrets.token_hex(32))"
docker compose -f deploy/docker-compose.yml up -d --build
```

Compose v2 is required. The `release` service must finish successfully before
`web` starts. `release` connects as the Postgres superuser created by the
image, applies migrations, and seeds the catalogue only when `subjects` is
empty. It does not create demo accounts. A later `docker compose up` does not
overwrite CMS edits. Refreshing seeded rows is explicit, and it does overwrite
those rows:

```bash
docker compose -f deploy/docker-compose.yml run --rm release python scripts/seed.py
```

Run that only when overwriting seeded content is what you want.

The web process connects as `engineverse_app`. That login can read and write
rows. It cannot `CREATE TABLE`. `db.migrate()` refuses that role by name as
well. The official Postgres image runs `docker-entrypoint-initdb.d` only when
the data volume is empty. `scripts/release.py` repeats the grants, which is
what repairs a volume created before the role existed. Do not expect the init
script to re-run on its own.

Postgres is not published to the host. The web port is bound to `127.0.0.1:8000`.
Put a TLS reverse proxy on the public interface and proxy to that port. Set
`ENGINEVERSE_SITE_URL` to the public `https://` origin. The session cookie is
`Secure` when that origin is HTTPS.

To listen on another interface, change the port mapping yourself and accept
that the app is then reachable without TLS unless the proxy is the only path.

Create the first administrator after release, with the bootstrap URL, not the
app URL. The password is an environment variable or a prompt, never an argument:

```bash
ENGINEVERSE_ADMIN_PASSWORD='...' python scripts/create_admin.py \
  --email ops@example.org --username ops --full-name 'Site operator'
```

A second run is refused. Replacing the password requires
`ENGINEVERSE_ALLOW_ADMIN_REPLACE=yes` and `--replace`. The password is not
printed. There is no second hidden administrator.

## Hosting choices

Any host that can run Docker Compose and a TLS proxy is enough. A single VPS,
a university VM, or a machine you already administer. This repository does not
depend on a hosted database, a hosted identity provider, or a CDN.

Do not put the Postgres port on the internet. Do not commit `deploy/.env`.
API rate limits are written to `api_rate_limits`, so a second web process on
this database shares them. Login lockout was already in the database. The
client address is still the TCP peer unless `ENGINEVERSE_TRUST_PROXY` is on.
This compose file does not set that flag and does not run a proxy. Behind a
proxy that you have not told the app to trust, every learner looks like the
proxy, and one shared bucket can throttle all of them. Turn the flag on only
when the process is reachable solely through a proxy that overwrites
`X-Forwarded-For`. A public peer is never allowed to pick its own address.

In production, a staff account cannot `POST` to `/admin` until an authenticator
is enrolled under Settings. `GET /admin` still works. Learners are not required
to enrol. Replacing the super administrator with `--replace` clears that
account's authenticator seal. The password and the seal are not printed.

## What is not done

- A production Postgres dump. `scripts/backup_sqlite.py` has copied the local
  development database; that file is gitignored and is not a production dump.
  Compose defines a `backup` service. Docker is not available here, so that
  service has not been started. See `docs/BACKUPS.md`.
- A Play submission. `android/listing/` is a listing pack generated from the
  configured site name. It has not been uploaded and it is not approved. See
  `docs/ANDROID_TWA.md`.
- A statement that Judge0 is isolated. `scripts/check_judge0.py` runs a canary.
  With no `ENGINEVERSE_JUDGE0_URL` the canary does not run, and a held canary
  is still not a certification. `GET /ops/judge` keeps `isolation_verified` false.
- A curriculum that covers a degree. The seeded snapshot is 56 topics. See
  `docs/CURRICULUM_COVERAGE.md`.

## GitHub Pages reading copy

GitHub Pages can serve files only. scripts/export_pages.py writes the public
catalogue, using the same neumorphic pages as the app.
.github/workflows/pages.yml publishes that folder. The address is
https://<github-user>.github.io/<repository>/.

That address is not the application. Sign-in, saved progress and code
execution are absent there. It is not a production deployment, not a Play
submission, and not a certificate.
