"""Output- and input-sanitisation helpers.

The golden rule: **never** build HTML by string concatenation. Templates use
Jinja2 autoescaping, and every place that must emit markup (markdown, maths,
diagrams) goes through the escaping functions below.
"""
from __future__ import annotations

import html
import re
from html import escape as html_escape
from html.parser import HTMLParser
from urllib.parse import urlparse

CONTROL_CHARS = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]")
SAFE_URL_SCHEMES = {"http", "https", "mailto"}


def sanitize_text(value: str, max_length: int = 2000) -> str:
    """Strips control characters, normalises newlines and caps length."""
    if value is None:
        return ""
    text = CONTROL_CHARS.sub("", str(value)).replace("\r\n", "\n").replace("\r", "\n")
    return text.strip()[:max_length]


def escape(value: str | None) -> str:
    return html.escape("" if value is None else str(value), quote=True)


def is_safe_url(url: str | None) -> bool:
    """Blocks javascript:, data:, file: and other script-executing schemes."""
    if not url:
        return False
    url = url.strip()
    if url.startswith(("/", "#")):
        # Protocol-relative URLs ("//evil.com", "/\\evil.com") are treated as
        # absolute by every browser, so accepting them would turn any `next`
        # parameter into an open redirect. Only a single leading slash is a
        # genuine same-site path.
        if url.startswith("//") or url.startswith("/\\"):
            return False
        return True
    try:
        parsed = urlparse(url)
    except ValueError:
        return False
    if not parsed.scheme:
        return False
    return parsed.scheme.lower() in SAFE_URL_SCHEMES


def safe_link(url: str | None, fallback: str = "#") -> str:
    return url.strip() if is_safe_url(url) else fallback


def slugify(value: str, max_length: int = 96) -> str:
    # Apostrophes are dropped rather than becoming a separator, so
    # "Bernoulli's Equation" -> "bernoullis-equation" (not "bernoulli-s-equation").
    cleaned = value.lower().replace("\u2019", "").replace("'", "")
    slug = re.sub(r"[^a-z0-9]+", "-", cleaned).strip("-")
    return slug[:max_length].strip("-") or "item"


def strip_html(value: str) -> str:
    return re.sub(r"<[^>]+>", "", value or "")


def truncate(value: str, limit: int = 200) -> str:
    text = (value or "").strip()
    return text if len(text) <= limit else text[: limit - 1].rstrip() + "…"


# ---------------------------------------------------------------------------
# SVG sanitising
# ---------------------------------------------------------------------------

#: Diagram specs are stored markup rendered with `| safe`. CSP with a nonce stops
#: an injected script from running, but a sanitiser is the layer that should not
#: depend on a header being present, and the admin CMS is meant to grow a
#: diagram editor. Allowlist, not blocklist: new SVG gains a feature far more
#: often than anyone remembers to block it.
SVG_ELEMENTS = frozenset("""
svg g defs marker path rect line polyline polygon circle ellipse text tspan
title desc linearGradient radialGradient stop clipPath
""".split())

SVG_ATTRIBUTES = frozenset("""
viewbox xmlns role aria-label aria-hidden id class
d x y x1 y1 x2 y2 cx cy r rx ry width height points
fill fill-opacity fill-rule stroke stroke-width stroke-opacity stroke-dasharray
stroke-linecap stroke-linejoin font-size font-family font-weight text-anchor
transform marker-end marker-start orient refx refy markerwidth markerheight
opacity dominant-baseline letter-spacing
""".split())

#: Attribute values that can execute script. `href` and `xlink:href` are left
#: out of the allowlist above for the same reason.
_DANGEROUS_VALUE = re.compile(r"\s*(javascript|data|vbscript)\s*:", re.I)


class _SvgSanitiser(HTMLParser):
    """Rebuilds SVG keeping only allowlisted elements and attributes."""

    def __init__(self) -> None:
        super().__init__(convert_charrefs=False)
        self.out: list[str] = []
        self.skipping = 0

    def handle_starttag(self, tag, attrs):
        tag = tag.lower()
        if tag not in SVG_ELEMENTS:
            self.skipping += 1
            return
        kept = []
        for name, value in attrs:
            name = name.lower()
            if name not in SVG_ATTRIBUTES:
                continue
            if name.startswith("on"):
                continue
            if value and _DANGEROUS_VALUE.match(value):
                continue
            kept.append(f' {name}="{html_escape(value or "", quote=True)}"')
        self.out.append(f"<{tag}{''.join(kept)}>")

    def handle_startendtag(self, tag, attrs):
        before = len(self.out)
        self.handle_starttag(tag, attrs)
        if len(self.out) > before:
            self.out[-1] = self.out[-1][:-1] + " />"

    def handle_endtag(self, tag):
        if tag.lower() not in SVG_ELEMENTS:
            self.skipping = max(0, self.skipping - 1)
            return
        self.out.append(f"</{tag.lower()}>")

    def handle_data(self, data):
        if not self.skipping:
            self.out.append(html_escape(data, quote=False))


def sanitize_svg(spec: str) -> str:
    """Strips anything from an SVG diagram that could execute.

    Returns an empty string if the input contains no SVG at all, so a caller
    cannot be tricked into rendering arbitrary HTML as a diagram.
    """
    if not spec or "<svg" not in spec.lower():
        return ""
    sanitiser = _SvgSanitiser()
    sanitiser.feed(spec)
    sanitiser.close()
    return "".join(sanitiser.out)
