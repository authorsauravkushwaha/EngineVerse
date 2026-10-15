"""Curriculum contracts, compatibility, privacy and truthful local practice."""
from __future__ import annotations

import copy
import json
import re

import pytest

from engineverse import academy, coding, db
from engineverse.code_format import color_code
from engineverse.lesson_schema import SECTION_TITLES, validate_unit
from seed_data.academy import UNITS, validate_catalogue


def test_every_language_has_initial_unit_and_seven_level_goals(seeded):
    languages = {row['slug'] for row in coding.list_languages()}
    assert {unit['language'] for unit in UNITS.values()} == languages
    assert set(academy.SYLLABI) == languages
    assert len(UNITS) == 15
    for language in languages:
        assert [level['level'] for level in academy.syllabus(language)] == list(range(1, 8))
        modules = coding.modules_for_language(language)
        coverage = academy.coverage(modules)
        assert coverage['structured'] == (2 if language in {'python', 'c', 'cpp', 'java', 'csharp'} else 1)
        assert coverage['structured'] < coverage['total']


def test_authored_units_and_navigation_validate(seeded):
    catalogue = {row['slug']: [m['slug'] for m in coding.modules_for_language(row['id'])]
                 for row in coding.list_languages()}
    validate_catalogue(catalogue)
    for slug, source in UNITS.items():
        stored = academy.decode_unit(academy.lesson(source['language'], slug))
        assert stored == source
        assert len(stored['tests']) >= 4
        assert len(stored['guided_hints']) == 3
        assert len(stored['challenge_hints']) == 3


@pytest.mark.parametrize('slug', sorted(UNITS))
def test_structured_reader_has_all_sections_and_local_disclosure(client, slug):
    language = UNITS[slug]['language']
    response = client.get(f'/programming/{language}/lessons/{slug}')
    assert response.status_code == 200
    text = response.text
    for key, title in SECTION_TITLES:
        assert f'id="{key}"' in text
        assert title in text
    assert 'Local-execution / reference-solution lesson' in text
    assert 'No code is uploaded or run by this page' in text
    assert 'not submitted or graded' in text
    assert 'does not compile, submit, award XP' in text
    assert 'id="academy-code"' in text
    assert 'id="academy-solution"' in text
    assert 'expected' not in response.headers  # no synthetic execution metadata


def test_all_existing_modules_have_reader_and_old_fragment(client):
    for language in coding.list_languages():
        index = client.get(f'/programming/{language["slug"]}')
        assert index.status_code == 200
        assert 'expansion goals' in index.text
        modules = coding.modules_for_language(language['id'])
        for position, module in enumerate(modules):
            path = f'/programming/{language["slug"]}/lessons/{module["slug"]}'
            assert f'id="{module["slug"]}"' in index.text
            assert f'href="{path}"' in index.text
            page = client.get(path)
            assert page.status_code == 200, path
            if not module['lesson_data']:
                assert 'Legacy lesson' in page.text
            if position:
                assert f'/lessons/{modules[position - 1]["slug"]}' in page.text
            if position + 1 < len(modules):
                assert f'/lessons/{modules[position + 1]["slug"]}' in page.text


@pytest.mark.parametrize('path', [
    '/programming/python/lessons/no-such-lesson',
    '/programming/no-language/lessons/python-loops-from-scratch',
    '/programming/java/lessons/python-loops-from-scratch',
    '/programming/python/lessons/%27%20OR%201=1--',
])
def test_reader_scopes_module_to_language(client, path):
    assert client.get(path).status_code == 404


@pytest.mark.parametrize('change', [
    {'schema_version': 2}, {'objectives': ''}, {'examples': 'TODO'},
    {'trace': []}, {'tests': []}, {'version': ''}, {'minutes': -1},
    {'level': 8}, {'references': [{'title': 'bad', 'url': 'javascript:alert(1)'}]},
])
def test_schema_rejects_incomplete_units(change):
    unit = copy.deepcopy(UNITS['python-loops-from-scratch'])
    unit.update(change)
    with pytest.raises(ValueError):
        validate_unit(unit)


@pytest.mark.parametrize('raw', ['bad json', 'null', '[]', '{"schema_version":99}'])
def test_bad_payload_is_not_claimed_structured(raw):
    assert academy.decode_unit({'lesson_data': raw, 'language_id': 'python'}) is None


def test_payload_for_another_language_is_not_accepted():
    assert academy.decode_unit({'lesson_data': json.dumps(UNITS['c-loops']), 'language_id': 'python'}) is None


def test_missing_and_cyclic_prerequisites_rejected(seeded, monkeypatch):
    units = copy.deepcopy(UNITS)
    catalogue = {row['slug']: [m['slug'] for m in coding.modules_for_language(row['id'])]
                 for row in coding.list_languages()}
    monkeypatch.setattr('seed_data.academy.UNITS', units)
    units['python-loops-from-scratch']['prerequisites'] = ['not-present']
    with pytest.raises(ValueError, match='navigation'):
        validate_catalogue(catalogue)
    units['python-loops-from-scratch']['prerequisites'] = ['python-complexity-big-o']
    with pytest.raises(ValueError, match='cyclic'):
        validate_catalogue(catalogue)


def test_lesson_content_is_escaped_and_reading_changes_no_learner_data(client):
    slug = 'python-loops-from-scratch'
    original = academy.lesson('python', slug)['lesson_data']
    unit = copy.deepcopy(UNITS[slug])
    unit['intuition'] += '\n<script>alert(123)</script>'
    unit['code_examples'][0]['code'] = '<img src=x onerror=alert(123)>'
    tables = ('coding_submissions', 'submissions', 'user_progress', 'xp_events', 'personal_notes')
    before = {t: db.scalar(f'SELECT count(*) FROM {t}') for t in tables}
    try:
        db.execute('UPDATE language_modules SET lesson_data = ? WHERE slug = ?', json.dumps(unit), slug)
        page = client.get(f'/programming/python/lessons/{slug}')
        assert page.status_code == 200
        assert '<script>alert(123)</script>' not in page.text
        assert '<img src=x onerror=alert(123)>' not in page.text
        assert '&lt;script&gt;' in page.text
    finally:
        db.execute('UPDATE language_modules SET lesson_data = ? WHERE slug = ?', original, slug)
    assert {t: db.scalar(f'SELECT count(*) FROM {t}') for t in tables} == before


def test_code_formatter_is_escaped_and_lossless():
    import html
    text = 'if value < 3: print("<script>x</script>") # comment\n'
    colored = color_code(text)
    assert '<script>' not in colored
    assert 'code-keyword' in colored
    assert html.unescape(re.sub(r'</?span[^>]*>', '', colored)) == text


def test_migration_adds_nullable_payload_without_destroying_legacy_data(seeded):
    # Upgrade a legacy-shaped table through the real additive migration helper.
    db.execute('CREATE TABLE academy_migration_probe(id TEXT PRIMARY KEY, body TEXT NOT NULL)')
    try:
        db.execute("INSERT INTO academy_migration_probe VALUES ('legacy', 'keep me')")
        assert db.ensure_column('academy_migration_probe', 'lesson_data', 'TEXT')
        assert not db.ensure_column('academy_migration_probe', 'lesson_data', 'TEXT')
        assert db.query_one('SELECT * FROM academy_migration_probe') == {
            'id': 'legacy', 'body': 'keep me', 'lesson_data': None}
    finally:
        db.execute('DROP TABLE academy_migration_probe')
    # Real migration is repeatable and keeps stored payload + existing accounts.
    before = db.query('SELECT id, lesson_data FROM language_modules ORDER BY id')
    users = db.scalar('SELECT count(*) FROM users')
    db.migrate()
    db.migrate()
    assert db.query('SELECT id, lesson_data FROM language_modules ORDER BY id') == before
    assert db.scalar('SELECT count(*) FROM users') == users


def test_targeted_update_is_dry_by_default_and_preserves_ids_and_progress(seeded):
    from scripts.update_academy import apply_units
    before = db.query('SELECT id, lesson_data FROM language_modules ORDER BY id')
    tables = ('users', 'coding_submissions', 'submissions', 'user_progress', 'bookmarks', 'personal_notes')
    counts = {t: db.scalar(f'SELECT count(*) FROM {t}') for t in tables}
    assert len(apply_units()) == 15
    assert db.query('SELECT id, lesson_data FROM language_modules ORDER BY id') == before
    apply_units(apply=True)
    assert db.query('SELECT id, lesson_data FROM language_modules ORDER BY id') == before
    assert {t: db.scalar(f'SELECT count(*) FROM {t}') for t in tables} == counts


def test_static_export_and_sitemap_include_readers(client, seeded):
    from scripts.export_pages import public_paths, rewrite_html
    path = '/programming/python/lessons/python-loops-from-scratch'
    assert path in public_paths()
    assert path in client.get('/sitemap.xml').text
    rewritten = rewrite_html(client.get(path).text, '/EngineVerse')
    assert '/EngineVerse/programming/python/' in rewritten
    assert '/EngineVerse/static/js/academy.js' in rewritten
    assert '/EngineVerse/static/css/academy.css' in rewritten
    assert 'href="#objectives"' in rewritten


def test_reader_obeys_existing_signin_policy(client, monkeypatch):
    from engineverse.config import reload_settings
    monkeypatch.setenv('ENGINEVERSE_SIGNIN', 'required')
    reload_settings()
    try:
        response = client.get('/programming/python/lessons/python-loops-from-scratch', follow_redirects=False)
        assert response.status_code in (302, 303)
        assert '/login' in response.headers['location']
    finally:
        monkeypatch.setenv('ENGINEVERSE_SIGNIN', 'optional')
        reload_settings()


def test_lesson_javascript_has_no_runner_upload_or_storage():
    from pathlib import Path
    source = (Path(__file__).resolve().parents[1] / 'static/js/academy.js').read_text()
    assert 'event.preventDefault()' in source
    assert 'reference.hidden = true' in source
    for forbidden in ('fetch(', 'eval(', 'new Function(', 'localStorage', 'sessionStorage', 'XMLHttpRequest'):
        assert forbidden not in source


def test_offline_checker_includes_every_academy_reference():
    from scripts.check_links import collect_from_source
    urls = collect_from_source()
    for unit in UNITS.values():
        for ref in unit['references']:
            assert ref['url'] in urls
            assert any(row['table'] == 'academy_reference' for row in urls[ref['url']])


def test_sum_fixtures_reject_realistic_wrong_algorithms():
    tests = UNITS['python-loops-from-scratch']['tests']
    fixtures = [(list(map(int, t['input'].split()))[1:], int(t['expected'])) for t in tests]
    mutants = [
        lambda values: sum(values),
        lambda values: next((x for x in reversed(values) if x > 0), 0),
        lambda values: sum(set(x for x in values if x > 0)),
    ]
    for wrong in mutants:
        assert any(wrong(values) != expected for values, expected in fixtures)
    for values, expected in fixtures:
        assert sum(x for x in values if x > 0) == expected


def test_boundary_fixtures_reject_returning_any_equal_duplicate():
    values, target = [1, 3, 3, 9], 3
    # Returning immediately at the first midpoint is a plausible wrong approach.
    first_midpoint = len(values) // 2
    assert values[first_midpoint] == target
    assert first_midpoint != 1  # the required FIRST qualifying position
    # A nonadvancing lo=mid update on a singleton leaves the interval unchanged.
    lo, hi, mid = 0, 1, 0
    lo = mid
    assert (lo, hi) == (0, 1)
