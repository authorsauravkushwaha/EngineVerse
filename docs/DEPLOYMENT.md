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
- `ENGINEVERSE_LOGIN_OTP` is exactly `required` or `disabled`
- when `ENGINEVERSE_LOGIN_OTP=required`, `ENGINEVERSE_SMTP_URL` or
  `ENGINEVERSE_SMS_URL` is configured; otherwise startup refuses the deployment
- an `ENGINEVERSE_SMS_URL` used in production is HTTPS (the SMS gateway is
  operator-run, not a hosted EngineVerse service)
- `ENGINEVERSE_JUDGE` is `disabled`, or `judge0` with `ENGINEVERSE_JUDGE0_URL`

`auto`, `python` and `java` run learner code on this server. Production refuses
them. A subprocess is not a separate container. `judge0` only means the
submission is sent to a URL you operate. This process does not verify that
host's isolation.

## Sign-in factors and (optional) delivered codes

The default `ENGINEVERSE_LOGIN_OTP=disabled` is password-only sign-in. Passwords
are verified against a scrypt hash, sessions are opaque HttpOnly cookies, and
repeated failures lock the account temporarily. No transport is required, and
nothing about sign-in depends on a third party.

Two stronger options exist:

- **Per-account authenticator (recommended).** Any learner can enrol a TOTP
  authenticator under **Settings -> Security**. That account is then asked for a
  six-digit code from the app at every sign-in, with one-time recovery codes.
  This needs no mail or SMS at all.
- **Delivered code at every sign-in.** Set `ENGINEVERSE_LOGIN_OTP=required` to
  ask for a fresh six-digit code after every password check, for *every*
  account. The application does not use a hosted identity or SMS service, so
  production refuses to start in this mode until at least one first-party
  transport is configured:

- SMTP is suitable for email-only deployments. For Gmail, create a dedicated
  account and an app password with two-step verification; do not use the normal
  account password. The URL-encoded app password can be supplied to the
  standard-library SMTP client, for example:

  ```dotenv
  ENGINEVERSE_SMTP_URL=smtps://engineverse%40example.com:xxxx%2Dxxxx%2Dxxxx%2Dxxxx@smtp.gmail.com:465/?starttls=0
  ENGINEVERSE_MAIL_FROM=EngineVerse <engineverse@example.com>
  ```

  Keep the app password in the deployment secret store, not in Git or a ticket.
  Test delivery and the account's sending limits before opening registration.
- `ENGINEVERSE_SMS_URL` points to an HTTP endpoint operated by the deployment.
  It receives a POST with JSON `{"to":"+...","body":"..."}`. If the URL
  contains `userinfo` password, it becomes an `Authorization: Bearer` header
  and is stripped from the request URL. Production refuses a plain-HTTP SMS
  URL. The gateway must protect its own logs and rate limits; EngineVerse does
  not know carrier delivery status.

A local development instance with no transport may reveal a code once when demo
accounts are allowed. That fallback is never available in production or when a
transport is configured but fails.

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
- A curriculum that covers a degree. The expanded seed snapshot has 93 subjects
  across 45 branches and 121 published starter topics, but it is not a complete
  syllabus. Newly generated starter content, including Cyber Security, is marked
  `needs_review` in editorial metadata. See `docs/CURRICULUM_COVERAGE.md`.

## GitHub Pages sign-in gateway

GitHub Pages serves files only: it cannot run accounts, a database, live lab
operators or the code judge. The current `.github/workflows/pages.yml` explicitly
publishes the **public catalogue** with `--reading-copy`, including the four
[advanced capability pages](ADVANCED_CAPABILITIES.md). The export renders a fresh
no-demo seed as a signed-out visitor, checks all local links and heading outlines,
refuses leaked demo passwords, and disables backend-only lab controls in HTML.
This is separate from the real app's compulsory sign-in policy.

```bash
python scripts/export_pages.py --out site --reading-copy
```

Directory/schema filters, snippet copies and n8n JSON downloads work in the
reading copy. SQL queries, workflow runs and new swarm simulations do not; the
pages show labelled seeded examples and explain that execution needs a
self-hosted backend. Accounts, cross-device progress and the judge are likewise
not deployed to Pages.

The workflow uploads and deploys the files, then verifies the live HTTPS origin:
`deployment.json` must match the exact `main` commit, and the home page, all four
new capability pages, navigation/headings and shared CSS/JS assets must resolve.
The verifier retries briefly for CDN propagation. A green Pages workflow thus
includes a post-deployment check, not just an artifact upload.

### Optional gateway instead of a reading copy

An operator who wants no catalogue published can export a **sign-in gateway**:
one landing page whose buttons go to a self-hosted app's `/login` and `/register`,
with old deep links preserved as `next`. No catalogue or answers are published in
this mode. The workflow's explicit `--reading-copy` must be changed to `--gateway`
if choosing it, and its reading-copy-specific verification step must be adjusted.

```bash
python scripts/export_pages.py --out site --gateway --app-url https://learn.example.org
```

The exporter also accepts `ENGINEVERSE_APP_URL` as the gateway destination.
Without an app URL the gateway says the app is not hosted yet. Setting that
variable alone does not override the current workflow's `--reading-copy` flag.

The Pages address is not the Python application. It is not a production backend
deployment, a Play submission or an accredited certificate.
