#!/usr/bin/env python3
"""Copy a SQLite file with the online backup API.

Refuses to overwrite the destination. Does not print a secret or a database
URL. This is the development copy. Production dumps are `pg_dump` via
`scripts/backup_postgres.sh` or the compose `backup` service. Running this
script is not a production dump, and the compose service has not been started
from a workspace that has no Docker.
"""
from __future__ import annotations

import argparse
import sqlite3
import sys
from pathlib import Path


class BackupRefused(RuntimeError):
    """An operator error. The message never contains a secret."""


def backup_sqlite(source: Path, dest: Path) -> None:
    source = Path(source)
    dest = Path(dest)
    if not source.is_file():
        raise BackupRefused(f"Source database does not exist: {source}")
    if dest.exists():
        raise BackupRefused(f"refusing to overwrite {dest}")
    dest.parent.mkdir(parents=True, exist_ok=True)
    src = sqlite3.connect(source)
    dst = sqlite3.connect(dest)
    try:
        with dst:
            src.backup(dst)
    finally:
        dst.close()
        src.close()


def main() -> int:
    parser = argparse.ArgumentParser(description="Copy a SQLite database without tearing a page.")
    parser.add_argument("source")
    parser.add_argument("dest")
    args = parser.parse_args()
    try:
        backup_sqlite(Path(args.source), Path(args.dest))
    except BackupRefused as exc:
        print(str(exc), file=sys.stderr)
        return 2
    print(f"Wrote {args.dest}. No connection URL was printed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
