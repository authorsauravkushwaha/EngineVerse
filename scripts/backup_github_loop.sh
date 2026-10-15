#!/usr/bin/env bash
# Optional daily encrypted backup worker. A failure exits non-zero; Docker
# restarts it instead of reporting an unverified backup as successful.
set -euo pipefail
interval=${BACKUP_INTERVAL_SECONDS:-86400}
if [[ ! "$interval" =~ ^[0-9]+$ ]] || (( interval < 3600 )); then
  echo 'BACKUP_INTERVAL_SECONDS must be at least one hour.' >&2
  exit 2
fi
while true; do
  /usr/local/bin/backup_github.sh
  if [[ ${BACKUP_ONCE:-} == 1 ]]; then
    exit 0
  fi
  sleep "$interval"
done
