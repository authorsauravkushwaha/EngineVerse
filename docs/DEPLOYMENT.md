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
- `ENGINEVERSE_LOGIN_OTP` is exactly `required`, `signup_only` or `disabled`
- when `ENGINEVERSE_LOGIN_OTP` is `required` or `signup_only`,
  `ENGINEVERSE_SMTP_URL` or `ENGINEVERSE_SMS_URL` is configured; otherwise
  startup refuses the deployment, because a new account (or every sign-in) would
  be asked for a code that nothing can deliver
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

**Recommended when a transport exists: `ENGINEVERSE_LOGIN_OTP=signup_only`.**
A six-digit code is then required in exactly three places and never on an
ordinary sign-in by an account that is already verified:

| Situation | What is asked for |
|---|---|
| Creating a **new account** | One 6-digit code to the Gmail/email address or to a mobile number with its country code, before the account is created |
| **Forgot password** | A 6-digit code by email or SMS, then the new password |
| **Change password** under Settings | A 6-digit code by email or SMS, then the new password |
| **Returning verified learner** | Password only - no code, no transport round trip |

Both the registration form and the recovery form let the learner choose Gmail or
SMS, and the SMS option always carries its country-code selector. An account that
registers with neither a mail nor an SMS transport configured degrades to
password-only signup rather than locking the new learner out.

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
docker compose --env-file deploy/.env -f deploy/docker-compose.yml up -d --build
```

Compose v2 is required. The `release` service must finish successfully before
`web` starts. `release` connects as the Postgres superuser created by the
image, applies migrations, and seeds the catalogue only when `subjects` is
empty. It does not create demo accounts. A later `docker compose up` does not
overwrite CMS edits. Refreshing seeded rows is explicit, and it does overwrite
those rows:

```bash
docker compose --env-file deploy/.env -f deploy/docker-compose.yml run --rm release python scripts/seed.py
```

Run that only when overwriting seeded content is what you want.

The web process connects as `engineverse_app`. That login can read and write
rows. It cannot `CREATE TABLE`. `db.migrate()` refuses that role by name as
well. The official Postgres image runs `docker-entrypoint-initdb.d` only when
the data volume is empty. `scripts/release.py` repeats the grants, which is
what repairs a volume created before the role existed. Do not expect the init
script to re-run on its own.

Postgres is not published to the host. By default the web port is bound only to
`127.0.0.1:8000`. Set `ENGINEVERSE_SITE_URL` to the public `https://` origin;
the session cookie is `Secure` for HTTPS. Do **not** publish the web or Postgres
container directly on `0.0.0.0`.

### Public HTTPS edge (one operator installation, not one per learner)

`deploy/public.yml` adds a Caddy TLS reverse proxy on 80/443. It is an *opt-in*
Compose overlay: this checkout cannot create your VPS, domain, DNS record or
certificates. On a server with Docker Compose v2, point your DNS A/AAAA record
to it, open 80/443 and fill in the ignored `deploy/.env` first. In particular,
set `ENGINEVERSE_SITE_URL=https://learn.example.org` to your real origin, with
unique strong secret and DB passwords. Then run:

```bash
docker compose --env-file deploy/.env -f deploy/docker-compose.yml -f deploy/public.yml up -d --build
curl --fail https://learn.example.org/health
python scripts/verify_hosted_app.py --url https://learn.example.org
```

Caddy overwrites incoming `X-Forwarded-For` with its TCP peer before the web
process (which now trusts only a private proxy) computes rate limits. The base
Compose file keeps loopback access for *on-host* health checks; only Caddy has
public ports. Never trust an unvetted upstream proxy's forwarded IP as a learner
address. Store the persistent Caddy TLS volumes alongside the Postgres volume;
re-deploys should not erase either.

`ENGINEVERSE_SIGNIN=optional` lets anyone browse the hosted catalogue without
an account. An account is still needed for saved learning progress, submissions,
community features and cross-device access. Opening a public website does not
magically provide an isolated judge: leave `ENGINEVERSE_JUDGE=disabled` until you
operate a separate, properly isolated Judge0 instance and test its controls.
Neither Caddy nor an Android wrapper runs learner code.

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

- A public HTTPS deployment, DNS change, Android release, or GitHub backup
  destination. The new overlays and workflows are instructions/automation for
  an operator who provides a real host, secrets and signing key; they have not
  run against a live production database in this checkout.
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

## GitHub Pages and the full app

GitHub Pages serves files only. It cannot host the Python process, accounts, a
shared database, community writes, or a code judge. **Never store actual learner
records in this public repository or in a Pages artifact.** A browser streak on
the reading copy stays in that browser; it is not synchronized or migrated into
the full app's account.

Until `ENGINEVERSE_APP_URL` is set, `.github/workflows/pages.yml` publishes the
public catalogue as a **reading copy**, including the four advanced capability
pages. The export renders a fresh no-demo seed as a signed-out visitor, checks
local links and heading outlines, refuses leaked demo passwords and disables
backend-only lab controls. SQL queries, workflow runs, swarm simulations and
new submissions require the live backend; the copy only shows labelled examples.

```bash
python scripts/export_pages.py --out site --reading-copy
```

After you have deployed the full app over HTTPS and checked registration, set the
**repository Actions variable** `ENGINEVERSE_APP_URL` in GitHub Settings →
Secrets and variables → Actions → Variables. Use exactly the origin, e.g.
`https://learn.example.org`, not `/login`, not the Pages URL, and no trailing
path. On the next `main` workflow run (usually after merging), the build calls
`scripts/verify_hosted_app.py` and **refuses to replace** the reading copy if the
app is down, is in development mode, lacks a working login/registration/install
page, or lacks its root PWA manifest. When verified, Pages changes to a small
gateway. It opens the *same* full website for everyone, and its 404 page forwards
old bookmarked paths and query strings to that origin. The app's normal auth
policy decides if they need to sign in. Cookies and records are never copied
between Pages and the app. You can test an export locally with:

```bash
python scripts/export_pages.py --out site --gateway --app-url https://learn.example.org
```

Set `ENGINEVERSE_SIGNIN=optional` **on the hosted app** to allow signed-out
visitors to browse notes there. The hosted app, not Pages or its code repository,
provides account-backed progress. The workflow publishes `deployment.json` with
the exact `main` commit and mode. `scripts/verify_pages.py` checks the actual
Pages HTTPS origin, links and assets after deployment; a green upload alone is
not enough. Once Pages is a gateway, availability of the full site depends on
your host, TLS and database; monitor and back it up.

A direct APK link appears only if an operator has published a signed Android
GitHub Release *and* sets `ENGINEVERSE_APK_URL` to its versioned asset in both
`deploy/.env` and the repository Actions variable. The Pages build verifies the
release has a nonempty, nondraft APK before showing the button. With no APK,
the full site still works in a phone browser/PWA. See [Android](ANDROID_TWA.md).
The public Pages URL is never the APK's TWA origin.

If you don't have a public HTTPS server yet, leave `ENGINEVERSE_APP_URL` and
`ENGINEVERSE_APK_URL` unset: Pages remains the useful public reading copy rather
than offering a fake sign-in or broken download. A code push or PR cannot by
itself deploy the backend, buy a host, provision a signing key, or turn GitHub
into a safe learner database.
