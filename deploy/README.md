# Deployment

Four services: a one-shot release step, the web app, PostgreSQL, and a backup client.
The longer procedure, including Git Bash, is [docs/DEPLOYMENT.md](../docs/DEPLOYMENT.md).
This file is the topology. It is not a record of a deployment that has happened.

```bash
cp deploy/.env.example deploy/.env      # then set real values
docker compose -f deploy/docker-compose.yml up -d --build
```

`release` migrates with the bootstrap role and seeds the catalogue only when
it is empty. The web process does not migrate or seed, and it connects as
`engineverse_app`, which cannot `CREATE TABLE`. Init scripts in
`docker-entrypoint-initdb.d` run only on an empty data volume. `release`
repeats the grants so an existing volume still gets the runtime role.

Production refuses `ENGINEVERSE_JUDGE=auto`, `python` and `java`. The default
is `disabled`. Demo accounts are not created.

## Services

| Service | Image | Network | Notes |
|---|---|---|---|
| `release` | `deploy/Dockerfile.web` | `internal` | One shot (`restart: "no"`). Bootstrap database role. |
| `web` | same image | `internal` | Serves SSR HTML + the JSON API. Non-root, read-only root FS. Runtime database role. Bound to `127.0.0.1:8000`. |
| `db` | `postgres:16` | `internal` | Schema and runtime role on first boot. Not published to the host. |
| `backup` | `postgres:16` | `internal` | `pg_dump` once, then daily, into the `pg-backups` volume. Not published. Has not been started from this workspace. |

## Where learner code actually runs

Nowhere, in the production default. `ENGINEVERSE_JUDGE=disabled` refuses every
submission. The image still contains `gcc`, `g++`, a JDK and
`engineverse-sandbox.jar` because the same image can run the development judge.
That judge invokes `java -jar`, `gcc` and `python3` with `subprocess.run`. A
subprocess call cannot reach another container, so those toolchains are not a
second machine. Production startup refuses to use them.

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

This list applies only when a local judge is selected. Production compose does
not select one. If it did, containment inside the web container would be: rlimits set in the child (process count, address space,
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
