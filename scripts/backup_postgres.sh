#!/bin/sh
# Dump a PostgreSQL database. This script does not delete anything and does not
# print the connection URL, because that URL contains the password.
#
#   ENGINEVERSE_DB_URL='postgresql://...' scripts/backup_postgres.sh backups/engineverse.dump
#
# Restore is documented in docs/BACKUPS.md. It is a separate, destructive step
# and is not performed here.
set -eu

output=${1:-}
if [ -z "$output" ]; then
  echo "usage: scripts/backup_postgres.sh backups/engineverse.dump" >&2
  exit 2
fi

url=${ENGINEVERSE_DB_URL:-}
if [ -z "$url" ]; then
  echo "ENGINEVERSE_DB_URL is not set. It was not printed because it would contain a password." >&2
  exit 2
fi

case "$url" in
  postgresql://*|postgres://*) ;;
  *)
    echo "ENGINEVERSE_DB_URL is not a postgresql URL." >&2
    exit 2
    ;;
esac

mkdir -p "$(dirname "$output")"
if [ -e "$output" ]; then
  echo "refusing to overwrite $output" >&2
  exit 2
fi

pg_dump --format=custom --no-owner --file="$output" "$url"
echo "Wrote $output. The connection URL was not printed."
