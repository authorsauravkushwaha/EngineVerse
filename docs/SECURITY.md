# Security

This document describes what the platform actually does, not what it intends to
do. Every mechanism below is implemented in `backend/engineverse/security/` and
covered by `backend/tests/test_security.py` (63 tests) and
`backend/tests/test_routes.py`.

## Threat model

The asset is learner data: identities, progress, and anything a learner writes.
The threats, in the order they are likely to arrive:

1. Credential theft — password guessing, credential stuffing, hash disclosure.
2. Session hijacking — cookie theft, fixation, cross-site request forgery.
3. Injection — SQL, XSS, open redirect, template injection.
4. Arbitrary code execution — via the coding judge.
5. Privilege escalation — a learner reaching staff capability.
6. Abuse — rate-limit evasion, content spam, enumeration.

## Passwords

`security/passwords.py`.

- **scrypt**, `N=16384, r=8, p=1`, 64-byte key, 16-byte random salt. Measured at
  **52 ms** per hash on the reference hardware — slow enough to make offline
  brute force expensive, fast enough not to be a denial-of-service lever.
- Stored as `scrypt$16384$8$1$<saltB64>$<hashB64>` (130 characters). The
  parameters travel with the hash, so the cost can be raised later without
  invalidating existing credentials. `needs_rehash()` reports any hash that is
  not current, and the login path transparently upgrades it.
- **NFKC normalisation** before hashing, so a password typed with combining
  characters verifies identically to the precomposed form. Without this, two
  visually identical passwords would be two different credentials.
- Constant-time comparison via `hmac.compare_digest`.
- Length capped at 256 characters, which bounds the scrypt input and prevents a
  CPU-exhaustion request.
- Policy is **length-first** per NIST SP 800-63B: minimum 10 characters, a
  character-mix requirement only in the 10–16 band (long passphrases are not
  penalised), a blocklist of 22 common passwords, detection of runs of a repeated
  character, and rejection of any password containing the account's own name,
  username or email.

## Sessions

`security/sessions.py`.

- The cookie holds `<ulid>.<random token>`. **Only the SHA-256 of the token is
  stored**, so a database disclosure does not yield usable sessions.
- Cookie `ev_session`: `HttpOnly`, `SameSite=Lax`, `Secure` when the deployment
  is HTTPS, `Path=/`, `Max-Age` from configuration.
- Every request touches `last_seen_at`; `prune_sessions()` removes expired rows.
- `revoke_session()` and `revoke_all_sessions()` support logout and
  "sign out everywhere", and changing a password revokes every other session.
- No session id appears in a URL, which removes the fixation and
  referrer-leakage vectors.

## Password reset

`auth.issue_password_reset()` / `auth.consume_password_reset()`, backed by the
`password_resets` table.

- The token is 32 bytes from `secrets.token_urlsafe`. **Only its SHA-256 is
  stored**, so reading the table does not yield a working link.
- The token is matched by **exact hash equality**, never by pattern.
- Tokens expire after 30 minutes and are single use; consuming one marks it used
  in the same step that returns the user id, so it cannot be replayed.
- Issuing a token deletes any outstanding one for that user, so there is never a
  choice of live links and an older emailed link stops working.
- A weak new password costs the user their token rather than being retryable, so
  the form cannot be used as a password-strength oracle.
- The page reports the same outcome whether or not the address exists.

### Why this is a table and not an audit row

Reset tokens were originally written into `audit_logs` and recovered with
`meta LIKE '%"<token>"%'`. Because the submitted token was interpolated straight
into the `LIKE` pattern, posting a single `%` matched the most recent row and
reset that account's password - a complete account takeover requiring no
credential and no access to anyone's email. The fix is not escaping the pattern;
a token is a secret and must be looked up by equality, so it now has a table of
its own with a hashed primary key. The old code also deleted from `audit_logs`,
which contradicts that table being append-only.

### Where the link goes

The link is only ever emailed, by `engineverse/notify.py` over the standard
library's `smtplib` — no third-party mail service. Configure it with
`ENGINEVERSE_SMTP_URL` and `ENGINEVERSE_MAIL_FROM`.

With no relay configured, which is the default, self-service reset is reported as
**unavailable** and the token is consumed rather than left live in the table.
This was not always the case: the route used to render the token into
`forgot.html` because there was nowhere to send it, which made
`POST /forgot-password` a complete account-takeover endpoint — post a victim's
address, read the live reset link out of the response, set a new password.
Nothing gated it, and five tests depended on the behaviour, so it had been
working as designed.

`ENGINEVERSE_REVEAL_RESET_TOKEN=1` restores the old page for local development,
and is refused outright when `ENGINEVERSE_ENV=production`. It is also refused
when a relay is configured but unreachable: a form that starts revealing tokens
during an SMTP outage is a takeover endpoint that switches itself on at exactly
the wrong moment.

## CSRF

`security/csrf.py`.

- The token is `nonce.HMAC-SHA256(secret, "<session_id>:<nonce>")`. It is bound
  to the session, so a token minted for one session is worthless in another, and
  it cannot be forged without `ENGINEVERSE_SECRET`.
- Accepted from the `x-csrf-token` header (used by the JavaScript client) **or**
  the `csrf_token` form field (used by server-rendered forms, which cannot set a
  header). Reading only the header was a real defect: it 403'd every
  non-JavaScript form POST, including logout.
- Anonymous mutations — login and registration — are exempt because there is no
  session to bind a token to yet. They are covered by `SameSite=Lax`, the
  rate limiter, and account lockout instead.
- When the body must be read in middleware, `request.body()` is awaited before
  `request.form()`. Under Starlette's `BaseHTTPMiddleware` the request is a
  `_CachedRequest`, and caching the body is what lets the downstream handler read
  it again.

## Authorisation

`security/rbac.py`.

- 8 roles × 10 capabilities, expressed as an explicit allow-list. `can()` returns
  `False` for any role/capability pair that is not listed, and for any capability
  the module does not know about — the check **fails closed**.
- Roles: `student`, `mentor`, `moderator`, `subject_expert`, `project_reviewer`,
  `analytics_admin`, `content_admin`, `super_admin`. `student` holds no
  capabilities at all.
- `assert_can()` raises `Forbidden`, which the web layer turns into a 403.
  `/admin` is verified to return 403 for a student and 200 for a super admin.
- The seeder is tested against `rbac.ROLES`, because minting an undefined role
  silently produces an account with zero capabilities and a misleading label —
  a real defect this caught.

## Injection

- **SQL** — every query is parameterised through `db.query/execute/scalar`. No
  query in the codebase interpolates a value into SQL text. Foreign keys are
  enforced (verified by a test that an insert referencing a missing user fails).
- **XSS** — Jinja2 runs with `autoescape=True`. The two deliberate exceptions are
  rendered markdown, which passes through `markdown.py`'s own escaping and is
  never fed raw user HTML, and diagram SVG.
- **Stored SVG** — a diagram *is* markup, so `topic.html` emits `diagram.spec`
  with `| safe`. The spec is therefore run through `sanitize_svg()` where it is
  read, not in the template, so the clean version is the only one any caller can
  reach — including a future admin form. It allowlists elements and attributes
  rather than blocking known-bad ones, drops `on*` handlers and `javascript:`/
  `data:`/`vbscript:` URLs, and returns an empty string for input that is not SVG
  at all. A test asserts all six seeded diagrams survive with every element
  intact, because a sanitiser that mangles real diagrams is not a fix. CSP's
  nonce already stops an injected script; this is the layer that does not depend
  on a header being present.
- **Open redirect** — `is_safe_url()` allows only same-site paths and the
  `http`, `https` and `mailto` schemes. It explicitly rejects **protocol-relative
  URLs** (`//evil.com`, `/\evil.com`), which every browser resolves against the
  current scheme and which would otherwise turn any `next` parameter into an
  off-site redirect.
- **CSP** — a per-request nonce is generated for every response and the policy is
  `default-src 'self'` plus that nonce. A reused nonce would defeat the policy,
  so a test asserts two consecutive responses differ.

## Transport and headers

`SecurityHeadersMiddleware` sets, on every response:

| Header | Value |
|---|---|
| `Content-Security-Policy` | `default-src 'self'` + per-request nonce |
| `X-Frame-Options` | `DENY` |
| `X-Content-Type-Options` | `nosniff` |
| `Referrer-Policy` | `strict-origin-when-cross-origin` |
| `Permissions-Policy` | camera, microphone and geolocation disabled |
| `Cross-Origin-Opener-Policy` / `Cross-Origin-Resource-Policy` | `same-origin` |
| `Strict-Transport-Security` | sent when the request arrives over HTTPS |
| `Cache-Control` | `private, no-store, max-age=0` on any page rendered for a signed-in user |

### Offline caching and shared devices

The service worker keeps a copy of fetched pages so the app works offline. Its
`cacheable()` check refuses non-GET requests, other origins, `/api/`, `/settings`
and `/admin` — but that is a denylist, and most pages render the viewer's own
data: `/today`, `/profile`, `/notifications`, `/mistakes`, `/streaks`. Cached on
a library machine or a sibling's phone, those would have been waiting for the
next person to open the app offline.

So `render()` marks every response built for a signed-in viewer as non-cacheable,
and the worker's `storable()` refuses to store anything carrying `no-store` or
`private`. The check lives in the response rather than in a path list because a
route added later is easy to forget, and the server already knows whether the
page it just built belongs to somebody.

## Rate limiting and lockout

- `security/ratelimit.py` keeps a sliding window per identifier: 30 requests/min
  for the judge, 300/min for the rest of `/api`. Exceeding it returns 429 with a
  `Retry-After`.
- `register_login_attempt()` records every credential check in `login_attempts`
  with the identifier, IP, outcome and reason. `auth_blocked()` consults it to
  lock an account after repeated failures, which is the defence against
  credential stuffing that a per-IP limit alone cannot provide.
- The failed-attempt counter and `locked_until` live on `users`, so lockout
  survives a process restart.

## The judge

Learner code is untrusted input that must execute. It never runs in the web
process.

- A child process with a scrubbed environment — a test asserts
  `os.environ.get('ENGINEVERSE_SECRET')` is `None` inside a submission.
- Resource ceilings applied with `setrlimit` **in the child**, not with `ulimit`
  in the generated script: process count, address space, CPU seconds, file size,
  open files and core dumps. A test reads each limit back from inside a
  submission and asserts it is bounded.
- A wall-clock deadline. The submission runs in its own session, so on timeout
  the **whole process group** is killed, not just the direct child. A test
  asserts a fork bomb is contained and leaves no processes behind.
- An empty `tmpfs` is mounted over the application user's home directory — and
  therefore over the checkout inside it — within the sandbox's mount namespace.
  A submission can neither read the source tree nor write anywhere that account
  can. Tests assert the checkout cannot be listed, that a source file cannot be
  opened, and that writes aimed at both the repository and the home directory
  leave nothing behind on the real filesystem. Whether the host permits an unprivileged mount namespace is
  **probed at startup** rather than assumed; when it is not available the run
  falls back to the rlimits alone and says so.
- Privileges are dropped to `nobody` where the parent is allowed to do so.
- Outbound network is blocked: a test opens a socket to `1.1.1.1:80` and asserts
  it does not connect.
- Output is truncated, so a submission cannot exhaust memory by printing.
- The Java path runs in a **second** JVM (see `sandbox-java/README.md`) so a
  `System.exit`, a thread that never stops, or an exhausted heap cannot reach the
  sandbox itself.

### Why the limits are set in Python

They were originally `ulimit` lines inside the generated shell script. `/bin/sh`
is dash on Debian-family images, and dash implements neither `ulimit -u` nor
`ulimit -t`. Both lines failed with `Illegal option`, the `2>/dev/null || true`
suffix swallowed the error, and every submission ran with an unbounded
`RLIMIT_NPROC` and `RLIMIT_CPU` of `0`. A submitted fork bomb then exhausted the
host and the application server was killed alongside it. `setrlimit` cannot fail
silently in the same way, and the tests read the limits back from inside the
sandbox rather than trusting that they were set.

### What the built-in provider does not contain

The mount namespace hides the checkout and the network namespace removes
outbound access, but this is still process isolation, not full OS containment:

- Everything outside the mounted-over checkout is visible to a submission.
  `/etc/passwd`, the interpreter and the standard library are all readable, as
  they must be for the code to run.
- Privilege dropping to `nobody` only happens when the parent is privileged
  enough to do it. Running the application as an unprivileged user — which is
  the recommended deployment — means the drop is refused and the rlimits plus
  the tmpfs are what contain the submission.
- The mount namespace itself depends on unprivileged user namespaces being
  enabled. That is why support is **probed at startup** rather than assumed;
  `provider_info()` reports it, so an operator can see what they actually have.

### The container in `deploy/` is not a boundary either

An earlier revision of this document said the hardening lived in
`deploy/docker-compose.yml`, which ran a separate `sandbox` container with
`network_mode: none`, `cap_drop: [ALL]` and a read-only root filesystem. That was
wrong, and the service has been removed. The judge bridge invokes the sandbox
with `subprocess.run`, which cannot cross a container boundary, and the service
had no network and no published port, so nothing could reach it by any other
route either. Its `ENTRYPOINT` reads one JSON request from stdin, so with no
stdin attached it exited immediately and `restart: unless-stopped` looped it.

So in the shipped topology **learner code runs inside the web container**, where
the toolchains have to be for a subprocess call to work. What contains a
submission there is the list above — rlimits, the tmpfs over the home directory,
the network namespace, a private process group killed as a unit, and an
unprivileged user — plus the container's own `read_only` root, `cap_drop: [ALL]`
and `no-new-privileges`.

That is a real set of limits and it is what the tests verify. It is not
separation. Turning it into separation means giving the bridge a socket protocol
and running the judge as its own process on its own filesystem, which
`deploy/Dockerfile.sandbox` can build but nothing yet talks to. Until that
exists, treat a determined attacker who can submit code as able to read what the
application user can read.

## Audit

`audit_logs` is append-only and records the action, actor, entity, IP and a JSON
detail blob. Security-relevant events — rejected CSRF, failed logins, role
changes, application errors — are written there. It is the largest table on the
platform, so in Postgres it is hash-partitioned 256 ways.

## Secrets

`ENGINEVERSE_SECRET` is the root of trust: it keys the session token hashing, the
CSRF HMAC and the signed flash cookie. It is read only from the environment, never
from the database or a request, and is stripped from the judge's child
environment. `.env` is git-ignored; `.env.example` documents the variables and
holds no real value.

## Honest limitations

- **No second factor is enforced yet.** The schema carries `totp_secret` and the
  login path will accept a code, but enrolment is not built. Do not describe this
  deployment as MFA-protected.
- **The password blocklist is small** (22 entries). It catches `password` and
  `123456`; it is not a substitute for a corpus such as HaveIBeenPwned's.
- **Rate limits are in-process.** They are correct for a single instance and will
  under-count across replicas. A multi-instance deployment needs a shared store.
- **Email verification is not wired to a mail transport.** `email_verified`
  exists and the flow is present, but no mail is sent.
- **The Java sandbox cannot be built in this workspace** — no JDK is installed
  here, and none can be fetched. It is not unverified, though:
  `.github/workflows/java.yml` compiles it, runs its unit tests, and smoke-tests
  the built jar on JDK 21 and JDK 25 on every change to `sandbox-java/`.
- **The Java sandbox's policy file does nothing on JDK 24 or later.** JEP 486
  permanently disabled the Security Manager, so `-Djava.security.policy` is
  inert and the file is never read. The policy is opt-in
  (`ENGINEVERSE_SANDBOX_POLICY=1`) and off by default, and `Runner` now prints a
  warning and omits the flags rather than implying the control is active. What
  actually contains a submission is the separate child JVM, the heap and stack
  ceilings and the hard deadline — those hold on every JDK. Consequence: on a
  modern JDK a Java submission is not blocked from opening a socket, so the
  network egress control must come from the container or host, not from the
  sandbox. Whether the JVM warns or errors on `-Djava.security.manager=allow`
  under JDK 25 is unverified here (no JVM to run), which is exactly why the
  flags are no longer passed at all.
