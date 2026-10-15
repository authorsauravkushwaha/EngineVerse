#!/usr/bin/env python3
"""Narrow update of authored academy units; dry run unless --apply is supplied.

Back up first. This intentionally replaces body/example/exercise/lesson_data
on the listed module ids, but never deletes/recreates modules or learner rows.
Unlike a fresh seed, it is appropriate for an existing catalogue after review.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
for path in (ROOT, ROOT / 'backend'):
    sys.path.insert(0, str(path))

from engineverse import db, search
from seed_data import academy


def apply_units(*, apply: bool = False) -> list[str]:
    modules = db.query('SELECT language_id, slug FROM language_modules')
    catalogue = {}
    for row in modules:
        catalogue.setdefault(row['language_id'], []).append(row['slug'])
    academy.validate_catalogue(catalogue)
    slugs = sorted(academy.UNITS)
    if not apply:
        return slugs
    with db.transaction():
        for slug in slugs:
            unit = academy.UNITS[slug]
            db.execute(
                'UPDATE language_modules SET lesson_data = ?, body = ?, example = ?, exercise = ? '
                'WHERE slug = ? AND language_id = ?',
                json.dumps(unit, ensure_ascii=False), academy.searchable_body(unit),
                unit['code_examples'][0]['code'], unit['challenge'], slug, unit['language'],
            )
    search.reindex_all()
    return slugs


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--apply', action='store_true', help='replace only the listed authored module fields')
    args = parser.parse_args()
    # Migration is an explicit separate release operation, not a dry-run side effect.
    slugs = apply_units(apply=args.apply)
    print(('Updated' if args.apply else 'Would update') + f' {len(slugs)} existing modules:')
    print('\n'.join(slugs))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
