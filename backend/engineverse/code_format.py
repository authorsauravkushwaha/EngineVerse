"""Small escaped code formatter; token colors are a reading aid, not a parser."""
from __future__ import annotations

import html
import re

_TOKENS = re.compile(
    r'(?P<string>"(?:\\.|[^"\\])*"|\'(?:\\.|[^\'\\])*\')'
    r'|(?P<comment>//[^\n]*|\#[^\n]*|--[^\n]*)'
    r'|(?P<number>\b\d+(?:\.\d+)?\b)'
    r'|(?P<word>\b[A-Za-z_][A-Za-z_0-9]*\b)'
)
_KEYWORDS = set('if elif else for while in return def import from const let var int long '
                'double void public static class using namespace include fn mut use struct '
                'func package range readonly new null None True False true false '
                'SELECT FROM WHERE SUM COALESCE CREATE TABLE INSERT INTO VALUES NOT NULL '
                'PRIMARY KEY AS DISTINCT'.split())


def color_code(source: str) -> str:
    """Escape every byte from content; emit only fixed span classes."""
    output = []
    cursor = 0
    for match in _TOKENS.finditer(source):
        output.append(html.escape(source[cursor:match.start()]))
        text = match.group()
        kind = match.lastgroup
        if kind == 'word':
            kind = 'keyword' if text in _KEYWORDS else None
        escaped = html.escape(text)
        output.append(f'<span class="code-{kind}">{escaped}</span>' if kind else escaped)
        cursor = match.end()
    output.append(html.escape(source[cursor:]))
    return ''.join(output)
