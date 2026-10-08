# Deployment

Two services: the web app and PostgreSQL.

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

## Where learner code actually runs

In the web container. `deploy/Dockerfile.web` installs `gcc`, `g++` and a headless
JRE and builds `engineverse-sandbox.jar` into `/app`, because the judge bridge
invokes `java -jar`, `gcc` and `python3` with `subprocess.run` — a subprocess
call cannot reach another container, so the toolchains have to sit next to the
application process.

This compose file used to define a third `sandbox` service, hardened with
`network_mode: "none"`, `cap_drop: [ALL]`, a read-only root filesystem and CPU,
memory and PID ceilings. It was removed because it could never have worked:

- The bridge calls the sandbox as a subprocess, which requires a shared process
  and filesystem. A separate container shares neither.
- The service had no network and no published port, so nothing could reach it by
  any other route either.
- Its `ENTRYPOINT` reads one JSON request from stdin. With no stdin attached the
  container exits at once, and `restart: unless-stopped` would have looped it
  forever.

Keeping it would have implied a boundary that does not exist, which is worse than
not having one.

### What does contain a submission

Inside the web container: rlimits set in the child (process count, address space,
CPU seconds, file size, open files), an empty tmpfs mounted over the application
user's home directory, a network namespace with no outbound access, a private
process group killed as a unit on timeout, and an unprivileged user. The
container adds `read_only: true` with `/tmp` as the only writable path — which is
where the judge creates its work directories — plus `cap_drop: [ALL]` and
`no-new-privileges:true`.

That is a real set of limits and the judge suite verifies each one. It is not
separation: a submission runs as the application user. See
`docs/SECURITY.md` for precisely what that does and does not stop.

### Making it a separate process

`deploy/Dockerfile.sandbox` still builds a standalone sandbox image — non-root
uid 10001, JDK only, `/work` as the single writable path — for anyone who wants
to run the judge on its own host. Wiring it into this topology needs a socket
protocol in `judge/java_bridge.py` (a unix socket on a shared volume is the usual
answer, since `network_mode: "none"` rules out TCP). Nothing implements that yet,
so it is future work rather than a configuration option.
