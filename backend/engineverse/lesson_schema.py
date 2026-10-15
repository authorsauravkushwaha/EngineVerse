"""Shared validation contract for optional structured language lessons."""
from __future__ import annotations

SECTION_TITLES = (
    ("objectives", "A · Learning objectives"),
    ("intuition", "B · Intuitive explanation"),
    ("technical", "C · Technical explanation"),
    ("visual", "D · Visual understanding"),
    ("syntax", "E · Syntax and language rules"),
    ("examples", "F · Working examples"),
    ("walkthrough", "G · Execution walkthrough"),
    ("applications", "H · Real-world applications"),
    ("mistakes", "I · Mistakes and debugging"),
    ("alternatives", "J · Compare alternatives"),
    ("check", "K · Knowledge check"),
    ("guided", "L · Guided coding practice"),
    ("challenge", "M · Independent challenge"),
    ("mastery", "N · Mastery checkpoint"),
    ("further", "O · Further learning"),
)

def validate_unit(unit: dict) -> None:
    """Fail authoring/seed checks rather than silently publish an incomplete unit."""
    from urllib.parse import urlparse
    if unit.get('schema_version') != 1:
        raise ValueError('unsupported academy schema_version')
    for key, _ in SECTION_TITLES:
        if not isinstance(unit.get(key), str) or len(unit[key].strip()) < 40:
            raise ValueError(f'empty or superficial academy section: {key}')
    for key in ('language', 'version', 'setup', 'review', 'prerequisite_text', 'reference', 'solution_explanation', 'check_answer', 'test_strategy'):
        if not isinstance(unit.get(key), str) or not unit[key].strip():
            raise ValueError(f'missing academy field: {key}')
    if not isinstance(unit.get('minutes'), int) or not 5 <= unit['minutes'] <= 180:
        raise ValueError('invalid reading/practice estimate')
    if unit.get('level') not in range(1, 8):
        raise ValueError('invalid learning level')
    if not isinstance(unit.get('prerequisites'), list):
        raise ValueError('prerequisites must be a list')
    for key in ('trace', 'code_examples', 'tests', 'guided_hints', 'challenge_hints', 'references'):
        if not isinstance(unit.get(key), list) or not unit[key]:
            raise ValueError(f'missing academy collection: {key}')
    for example in unit['code_examples']:
        if not example.get('label') or not example.get('code'):
            raise ValueError('example requires label and code')
    if not any(e.get('expected') is not None for e in unit['code_examples']):
        raise ValueError('at least one example needs deterministic expected output')
    for row in unit['trace']:
        if not all(isinstance(row.get(k), str) and row[k] for k in ('step', 'value', 'state')):
            raise ValueError('invalid trace row')
    for test in unit['tests']:
        if not all(isinstance(test.get(k), str) and test[k] for k in ('input', 'expected', 'reason')):
            raise ValueError('test requires input, expected and reason')
    for ref in unit['references']:
        parsed = urlparse(ref.get('url', ''))
        if not ref.get('title') or parsed.scheme != 'https' or not parsed.hostname or parsed.username or parsed.password:
            raise ValueError('reference needs a title and public HTTPS URL')
