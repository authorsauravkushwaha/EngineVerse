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
- **XSS** — Jinja2 runs with `autoescape=True`. The one deliberate exception is
  rendered markdown, which passes through `markdown.py`'s own escaping and is
  never fed raw user HTML.
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

For a hard boundary, do not use the built-in provider: run the judge as a
non-root user in a container with its own filesystem, which is what
`deploy/docker-compose.yml` does for the Java sandbox (`network_mode: none`,
`cap_drop: [ALL]`, `no-new-privileges`, CPU, memory and PID ceilings).

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
- **The Java sandbox is not compiled in this workspace** — no JDK is installed
  here. `.github/workflows/java.yml` compiles it and runs its tests on every push.
