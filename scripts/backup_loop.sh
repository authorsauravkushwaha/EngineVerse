#!/bin/sh
# Periodic pg_dump for the compose backup service.
#
# Uses libpq environment variables (PGHOST, PGUSER, PGDATABASE, PGPASSWORD).
# It does not read ENGINEVERSE_DB_URL and it does not print a connection URL
# or a password. A failed dump removes the partial file and exits non-zero so
# the container restarts. This script does not restore anything.
set -eu

dest=${BACKUP_DIR:-/backups}
keep_days=${BACKUP_KEEP_DAYS:-14}
interval=${BACKUP_INTERVAL_SECONDS:-86400}

mkdir -p "$dest"

dump_once() {
  stamp=$(date -u +%Y%m%dT%H%M%SZ)
  out="$dest/engineverse-${stamp}.dump"
  if [ -e "$out" ]; then
    echo "refusing to overwrite $out" >&2
    return 2
  fi
  if pg_dump --format=custom --no-owner --file="$out"; then
    echo "Wrote $out. The connection URL was not printed."
    find "$dest" -name 'engineverse-*.dump' -type f -mtime +"$keep_days" -delete
    return 0
  fi
  rm -f "$out"
  echo "Dump failed. The connection URL was not printed." >&2
  return 1
}

dump_once
if [ "${BACKUP_ONCE:-}" = "1" ]; then
  exit 0
fi
while true; do
  sleep "$interval"
  dump_once
done
