# Deployment

Three services: the web app, PostgreSQL, and the judge sandbox.

```bash
cp deploy/.env.example deploy/.env      # then set real values
docker compose -f deploy/docker-compose.yml up -d --build
```

The web app migrates and seeds on first boot. `scripts/seed.py` is idempotent, so
re-running it against a database that already has learner data upserts rather
than duplicating.

## Services

| Service | Image | Network | Notes |
|---|---|---|---|
| `web` | `deploy/Dockerfile.web` | `internal` | Serves SSR HTML + the JSON API. Non-root, read-only root FS. |
| `db` | `postgres:16` | `internal` | `db/postgres/schema.pg.sql` is applied from `docker-entrypoint-initdb.d` on first boot. Not published to the host. |
| `sandbox` | `deploy/Dockerfile.sandbox` | **none** | Runs learner code. |

## Why the sandbox is cut off completely

Process isolation inside the JVM is not containment — it stops a submission from
crashing the sandbox, not from reading the host or dialling out. So the sandbox
container adds the OS-level layer:

- **`network_mode: "none"`** — no network interface at all. Note this is Docker's
  built-in null network; a custom network with `internal: true` would still allow
  container-to-container traffic, which is not isolation for a judge.
- **`read_only: true`** with a single `tmpfs` at `/work`, sized and mode `1777`,
  which is the only writable path.
- **`cap_drop: [ALL]`** and **`no-new-privileges:true`**.
- **`cpus: 1.0`, `mem_limit: 512m`, `pids_limit: 128`** — a fork bomb or an
  allocation loop is contained.
- Runs as **uid 10001**, non-root, with `/usr/sbin/nologin` and no home directory.

The web and sandbox images do not share a filesystem, a process or a network
namespace. The bridge invokes the sandbox as a subprocess and reads one JSON
verdict from stdout; there is no listening port to expose.

## Configuration

`ENGINEVERSE_SECRET` is the root of trust — it keys the session token digests, the
CSRF HMAC and the signed flash cookie. It must be at least 32 random bytes:

```bash
python -c "import secrets; print(secrets.token_urlsafe(48))"
```

Rotating it invalidates every session and signs everyone out. `deploy/.env` is
git-ignored.

In production set `ENGINEVERSE_DB_URL` to the Postgres DSN (the compose file does
this for you) and leave `ENGINEVERSE_DB_PATH` unused. `SITE_URL` should be the
public HTTPS origin; HSTS is only sent when the request arrives over HTTPS.

## Putting it behind TLS

The app terminates plain HTTP and expects a reverse proxy in front. It sets HSTS
when it sees HTTPS, and the session cookie is marked `Secure` when
`ENGINEVERSE_ENV=production` or the request is HTTPS. A minimal Caddy or nginx
front end is enough; the app does not need to terminate TLS itself.

## Scaling beyond one box

The compose file is a single-instance topology. To scale out:

1. Move to managed or replicated PostgreSQL. The schema is already partitioned —
   see `db/postgres/README.md`.
2. Put the rate limiter behind a shared store. It is currently in-process, so it
   under-counts across replicas.
3. Run the sandbox as a pool. It is stateless and already fully isolated, so N
   replicas need no coordination.
4. Shard by `user_id`. The ULID keys and the partitioning key are already aligned.

## Health

`/health` returns 200 with a JSON body. The web image healthchecks it; the sandbox
healthcheck runs a trivial submission and asserts an `accepted` verdict, which
proves the JVM starts *and* the compiler is present.
