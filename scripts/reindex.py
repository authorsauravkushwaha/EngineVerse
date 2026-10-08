#!/usr/bin/env python3
"""Rebuilds the search index from the content tables.

    python scripts/reindex.py            # rebuild
    python scripts/reindex.py --check    # report only, change nothing

The index is derived data. Nothing indexes a row when it is inserted, so content
added by SQL - which is how docs/CONTENT.md says to extend the catalogue - is
invisible to global search and to the AI tutor until this runs. The seeder calls
the same function, so `scripts/seed.py` also refreshes it; this exists for the
case where you added rows without reseeding.

The application also rebuilds on startup when the code indexes more than the
stored index holds (see search.INDEX_SCHEMA_VERSION), but that guard is for
schema changes, not for new rows, and it deliberately no-ops once the version
matches.
"""
from __future__ import annotations

import argparse
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "backend"))
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from engineverse import db, search  # noqa: E402
from engineverse.security.ids import now_ms  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--check", action="store_true",
                        help="report what would be indexed and exit without writing")
    args = parser.parse_args()

    db.migrate()

    if args.check:
        indexed = db.query(
            "SELECT entity_type, count(*) AS c FROM search_index GROUP BY entity_type ORDER BY c DESC"
        )
        print(f"search index currently holds {search.indexed_count()} entities:")
        for row in indexed:
            print(f"  {row['entity_type']:<12}{row['c']:>7}")
        print(f"\nrecorded index version: "
              f"{db.query_one('SELECT value FROM site_config WHERE key = ?', 'search_index_version') or '(none)'}"
              f"  (code expects {search.INDEX_SCHEMA_VERSION})")
        return 0

    count = search.reindex_all()
    db.execute(
        "INSERT INTO site_config (key, value, updated_at) VALUES ('search_index_version', ?, ?) "
        "ON CONFLICT(key) DO UPDATE SET value = excluded.value, updated_at = excluded.updated_at",
        str(search.INDEX_SCHEMA_VERSION), now_ms(),
    )
    print(f"Indexed {count} entities.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
