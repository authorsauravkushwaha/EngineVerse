#!/usr/bin/env bash
# Opt-in encrypted off-site backup to a DIFFERENT, PRIVATE GitHub repository.
# This does not put a database in the public EngineVerse source repo, and it is
# never called from an HTTP request. Requires pg_dump, age and gh on the host.
# Supply libpq PG* variables so no DB password is put on a command line.
set -euo pipefail
set +x
umask 077

repo=${ENGINEVERSE_BACKUP_REPO:-}
recipient=${ENGINEVERSE_BACKUP_AGE_RECIPIENT:-}
if [[ ! "$repo" =~ ^[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+$ ]] ||
   [[ -z "$recipient" || -z "${GH_TOKEN:-}" || -z "${PGHOST:-}" ||
      -z "${PGUSER:-}" || -z "${PGDATABASE:-}" || -z "${PGPASSWORD:-}" ]]; then
  echo 'Backup needs a private owner/repo, age recipient, scoped GH_TOKEN and PG* connection variables.' >&2
  exit 2
fi
for executable in gh age pg_dump; do
  if ! command -v "$executable" >/dev/null 2>&1; then
    echo "Backup needs $executable." >&2
    exit 2
  fi
done

# This check is intentionally performed on EVERY run: if someone changes the
# repo's visibility, stop immediately rather than quietly publish new records.
if [[ "$(gh repo view "$repo" --json isPrivate --jq .isPrivate)" != true ]]; then
  echo 'Refusing off-site backup: the destination GitHub repository is not private.' >&2
  exit 2
fi

tmp=$(mktemp -d)
cleanup() { rm -rf -- "$tmp"; }
trap cleanup EXIT
trap 'exit 130' INT
trap 'exit 143' TERM
stamp=$(date -u +%Y%m%dT%H%M%SZ)
tag="engineverse-backup-$stamp"
archive="$tmp/$tag.dump.age"

# Pipefail is essential: an encryption of a *partial* failed dump is not a
# backup. Plaintext is never written to disk, including when upload fails.
pg_dump --format=custom --no-owner | age -r "$recipient" -o "$archive"
size=$(stat -c %s "$archive")
if (( size < 64 || size > 536870912 )); then
  echo 'Refusing empty or oversized encrypted dump (GitHub Releases are not a database).' >&2
  exit 1
fi
checksum=$(sha256sum "$archive" | cut -d' ' -f1)
# Releases are versioned snapshots, not a live database. The asset is already
# age-encrypted before gh can read it; only ciphertext and its hash leave here.
gh release create "$tag" "$archive" --repo "$repo" \
  --title "Encrypted EngineVerse backup $stamp" \
  --notes "age-encrypted PostgreSQL custom dump. Ciphertext SHA-256: $checksum. Restore on a disposable database first." \
  --prerelease
echo "Encrypted off-site backup created: $tag (ciphertext SHA-256: $checksum)."
