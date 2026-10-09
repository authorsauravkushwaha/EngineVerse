# Incident response

This is a checklist for the person who administers the deployment. It is not
a staffed response team, and it has not been drilled. Do not put passwords,
session tokens, dumps, or learner data in the ticket you open.

## Credential leak

1. Treat the value as public. Do not paste it into chat to confirm it leaked.
2. If `ENGINEVERSE_SECRET` leaked, generate a new one and restart the web
   process. Every session cookie becomes invalid. That is the intended effect.
3. If `POSTGRES_PASSWORD` or `APP_DB_PASSWORD` leaked, change them from the
   bootstrap role, update `deploy/.env`, and restart. `scripts/release.py`
   applies `APP_DB_PASSWORD` to `engineverse_app` when it is set. It does not
   print the password.
4. If an administrator password leaked, set a new one with
   `scripts/create_admin.py --replace` and `ENGINEVERSE_ALLOW_ADMIN_REPLACE=yes`.
   Sessions for that account are revoked. The authenticator seal on that
   account is cleared, because rotating `ENGINEVERSE_SECRET` in step 2 makes
   every existing seal unreadable. The new password and the old seal are not
   printed. Enrol an authenticator again after signing in. In production, staff
   cannot change anything under `/admin` until that is done. `GET /admin` still
   works.
5. Read `audit_logs` for `auth.login` and `admin.user_updated` around the
   time of the leak. Record what you saw, not the secrets you rotated.

A stolen password is not enough for an account that has enrolled an
authenticator. It is enough for every account that has not. Learners are not
required to enrol. If someone loses the authenticator and the recovery codes,
a super administrator uses **Clear authenticator** on the admin page. That
clears the seal, revokes that account's sessions, and does not show the seal.
It refuses to clear the signed-in account. The only super administrator still
uses `scripts/create_admin.py --replace`, which also clears that seal. Do not
paste the seal into the ticket.

## Submitted code

Production must be running with `ENGINEVERSE_JUDGE=disabled` or with a Judge0
URL you operate. If a process was started with `python`, `java` or `auto`,
learner code ran as a subprocess on that host. That is not a container
boundary. The child is supposed to have a scrubbed environment, rlimits, and
a namespace when the kernel allows it. Assume a submission could read what
the application user could read if those probes failed open.

1. Set `ENGINEVERSE_JUDGE=disabled` and restart. Startup refuses the local modes.
2. Take the web container out of rotation if you have more than one. API rate
   limits are shared through `api_rate_limits` on this database. They still
   collapse to one address when a proxy is in front and `ENGINEVERSE_TRUST_PROXY`
   is off.
3. Preserve logs from the host. Do not copy `ENGINEVERSE_SECRET` into the
   preservation notes.
4. If you believe the host was written to, rebuild the image and rotate the
   secret and the database passwords. A backup from before the window is the
   restore source. See `docs/BACKUPS.md`.

`GET /api/ops/judge` is staff-only and reports the provider name and an
isolation sentence. The sentence for the local runner says the code runs on
this host and is not a separate container. Believe that sentence.

## Learner data

A dump, a log line with an email, or a screenshot of an admin page is personal
data. Delete the copy you do not need. Do not commit it. The health check in
production does not include the user count. Development and test still do.

## What this checklist does not include

- A public status page.
- A legal notification timeline. That depends on the institution and the
  jurisdiction, which this repository does not decide.
- A claim that the audit log is complete. `record()` is best-effort and will
  not fail the request it is recording.
