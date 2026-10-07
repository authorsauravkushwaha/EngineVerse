"""Output- and input-sanitisation helpers.

The golden rule: **never** build HTML by string concatenation. Templates use
Jinja2 autoescaping, and every place that must emit markup (markdown, maths,
diagrams) goes through the escaping functions below.
"""
from __future__ import annotations

import html
import re
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
