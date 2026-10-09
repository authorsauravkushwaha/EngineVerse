#!/bin/sh
# Creates the login the web process uses. The official image runs this only
# when the data directory is empty. An existing volume does not re-run it;
# scripts/release.py repeats the grants when APP_DB_PASSWORD is set.
#
# The password is passed to psql as a variable, not interpolated into the SQL
# text by this script. It must still be shell-safe because the process
# environment is expanded by the shell before psql sees it.
set -eu

if [ -z "${APP_DB_PASSWORD:-}" ]; then
  echo "APP_DB_PASSWORD is required to create the runtime role" >&2
  exit 1
fi

case "$APP_DB_PASSWORD" in
  *[!A-Za-z0-9_-]*)
    echo "APP_DB_PASSWORD must contain only A-Za-z0-9_-" >&2
    exit 1
    ;;
esac

if [ "${#APP_DB_PASSWORD}" -lt 16 ]; then
  echo "APP_DB_PASSWORD must be at least 16 characters" >&2
  exit 1
fi

case "${POSTGRES_DB:-}" in
  ""|*[!A-Za-z0-9_]*)
    echo "POSTGRES_DB must be a simple identifier" >&2
    exit 1
    ;;
esac

psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" \
  -v app_password="$APP_DB_PASSWORD" -v dbname="$POSTGRES_DB" <<'SQL'
SELECT CASE
  WHEN EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'engineverse_app')
  THEN format('ALTER ROLE engineverse_app WITH LOGIN NOSUPERUSER NOCREATEDB NOCREATEROLE PASSWORD %L', :'app_password')
  ELSE format('CREATE ROLE engineverse_app LOGIN NOSUPERUSER NOCREATEDB NOCREATEROLE PASSWORD %L', :'app_password')
END
\gexec
GRANT CONNECT ON DATABASE :"dbname" TO engineverse_app;
GRANT USAGE ON SCHEMA public TO engineverse_app;
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO engineverse_app;
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO engineverse_app;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO engineverse_app;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT USAGE, SELECT ON SEQUENCES TO engineverse_app;
REVOKE CREATE ON SCHEMA public FROM engineverse_app;
SQL

echo "Runtime role engineverse_app is configured. The password was not printed."
