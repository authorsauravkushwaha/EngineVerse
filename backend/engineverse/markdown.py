"""Markdown + LaTeX renderer for engineering notes.

Security model: this module builds **escaped HTML**. Nothing from content is
ever inserted raw. The maths renderer only emits a fixed set of tags/classes
with escaped operands, so a note cannot smuggle script into the page.

Supported syntax
    # .. ######  headings          **bold**  *italic*  ==highlight==
    `code`                          ```lang fenced code blocks
    - / * / +   bullet lists        1. ordered lists
    | a | b |   tables              > blockquotes
    ---         horizontal rule     [text](url) links (http/https/mailto only)
    $x^2$       inline maths        $$ ... $$ display maths
"""
from __future__ import annotations

import html
import re
from typing import Iterable

from .security.sanitize import is_safe_url

MAX_RENDER_LENGTH = 200_000

# ---------------------------------------------------------------------------
# LaTeX -> HTML (a focused, useful subset)
# ---------------------------------------------------------------------------

GREEK = {
    "alpha": "α", "beta": "β", "gamma": "γ", "delta": "δ", "epsilon": "ε",
    "varepsilon": "ε", "zeta": "ζ", "eta": "η", "theta": "θ", "vartheta": "ϑ",
    "iota": "ι", "kappa": "κ", "lambda": "λ", "mu": "μ", "nu": "ν", "xi": "ξ",
    "pi": "π", "rho": "ρ", "sigma": "σ", "tau": "τ", "upsilon": "υ", "phi": "φ",
    "varphi": "φ", "chi": "χ", "psi": "ψ", "omega": "ω",
    "Gamma": "Γ", "Delta": "Δ", "Theta": "Θ", "Lambda": "Λ", "Xi": "Ξ",
    "Pi": "Π", "Sigma": "Σ", "Upsilon": "Υ", "Phi": "Φ", "Psi": "Ψ", "Omega": "Ω",
    "infty": "∞", "partial": "∂", "nabla": "∇", "hbar": "ℏ", "ell": "ℓ",
    "angle": "∠", "degree": "°", "circ": "∘", "bullet": "•", "cdot": "·",
    "times": "×", "div": "÷", "pm": "±", "mp": "∓", "neq": "≠", "ne": "≠",
    "leq": "≤", "le": "≤", "geq": "≥", "ge": "≥", "approx": "≈", "equiv": "≡",
    "sim": "∼", "propto": "∝", "rightarrow": "→", "to": "→", "leftarrow": "←",
    "Rightarrow": "⇒", "Leftarrow": "⇐", "leftrightarrow": "↔", "mapsto": "↦",
    "in": "∈", "notin": "∉", "subset": "⊂", "subseteq": "⊆", "cup": "∪",
    "cap": "∩", "emptyset": "∅", "forall": "∀", "exists": "∃", "neg": "¬",
    "land": "∧", "lor": "∨", "implies": "⟹", "iff": "⟺", "perp": "⊥",
    "parallel": "∥", "therefore": "∴", "because": "∵", "sum": "∑", "prod": "∏",
    "int": "∫", "iint": "∬", "oint": "∮", "lim": "lim", "log": "log",
    "ln": "ln", "sin": "sin", "cos": "cos", "tan": "tan", "sec": "sec",
    "cosec": "cosec", "cot": "cot", "exp": "exp", "max": "max", "min": "min",
    "Re": "Re", "Im": "Im", "det": "det", "dim": "dim", "mod": "mod",
}

BIG_OPERATORS = {"sum", "prod", "int", "iint", "oint", "lim", "bigcup", "bigcap"}

FUNCTIONS = {"log", "ln", "sin", "cos", "tan", "sec", "cosec", "cot", "exp", "max", "min", "det", "dim", "mod", "lim"}


def _esc(value: str) -> str:
    return html.escape(value, quote=True)


class _TeX:
    """Recursive-descent renderer for the supported LaTeX subset."""

    def __init__(self, source: str) -> None:
        self.src = source
        self.pos = 0

    def peek(self) -> str:
        return self.src[self.pos] if self.pos < len(self.src) else ""

    def take(self) -> str:
        ch = self.peek()
        self.pos += 1
        return ch

    def group(self) -> str:
        """Consumes a `{...}` group or a single token."""
        self.skip_space()
        if self.peek() == "{":
            self.take()
            depth = 1
            start = self.pos
            while self.pos < len(self.src) and depth:
                ch = self.src[self.pos]
                if ch == "{":
                    depth += 1
                elif ch == "}":
                    depth -= 1
                    if depth == 0:
                        break
                self.pos += 1
            inner = self.src[start:self.pos]
            self.pos += 1  # consume '}'
            return inner
        if self.peek() == "\\":
            self.pos += 1
            name = ""
            while self.pos < len(self.src) and self.src[self.pos].isalpha():
                name += self.src[self.pos]
                self.pos += 1
            return "\\" + name if name else "\\" + self.take()
        return self.take()

    def skip_space(self) -> None:
        while self.pos < len(self.src) and self.src[self.pos] == " ":
            self.pos += 1

    def render(self) -> str:
        out: list[str] = []
        while self.pos < len(self.src):
            out.append(self.atom())
        return "".join(out)

    def atom(self) -> str:
        ch = self.peek()
        if ch == "":
            return ""
        if ch == "\\":
            return self.command()
        if ch == "{":
            return f'<span class="mrow">{_TeX(self.group()).render()}</span>'
        if ch == "}":
            self.take()
            return ""
        if ch == "^":
            self.take()
            return f'<sup class="msup">{_TeX(self.group()).render()}</sup>'
        if ch == "_":
            self.take()
            return f'<sub class="msub">{_TeX(self.group()).render()}</sub>'
        if ch == "&":
            self.take()
            return '<span class="mcol"></span>'
        self.take()
        if ch == " ":
            return " "
        if ch in "+-=<>()[]|,.:;!'":
            return f'<span class="mop">{_esc(ch)}</span>' if ch in "+-=<>|" else _esc(ch)
        if ch.isdigit() or ch == ".":
            number = ch
            while self.pos < len(self.src) and (self.src[self.pos].isdigit() or self.src[self.pos] == "."):
                number += self.take()
            return f'<span class="mnum">{_esc(number)}</span>'
        if ch.isalpha():
            run = ""
            while self.pos < len(self.src) and self.src[self.pos].isalpha():
                run += self.take()
            if run in FUNCTIONS:
                return f'<span class="mfn">{run}</span>'
            letters = "".join(f'<i class="mvar">{_esc(c)}</i>' for c in run)
            return letters
        return _esc(ch)

    def command(self) -> str:
        self.take()  # backslash
        name = ""
        while self.pos < len(self.src) and self.src[self.pos].isalpha():
            name += self.src[self.pos]
            self.pos += 1
        if not name:
            symbol = self.take()
            mapping = {",": "&thinsp;", ";": "&ensp;", ":": "&ensp;", " ": " ", "\\": "<br/>"}
            return mapping.get(symbol, _esc(symbol))

        if name in ("frac", "dfrac", "tfrac"):
            num = self.group()
            den = self.group()
            return (
                "<span class='mfrac'><span class='mnum-frac'>"
                + _TeX(num).render()
                + "</span><span class='mden-frac'>"
                + _TeX(den).render()
                + "</span></span>"
            )
        if name == "sqrt":
            body = self.group()
            return f'<span class="msqrt"><span class="msqrt-sign">√</span><span class="msqrt-body">{_TeX(body).render()}</span></span>'
        if name in ("text", "mathrm", "operatorname", "mbox"):
            return f'<span class="mtext">{_esc(self.group().strip())}</span>'
        if name in ("mathbf", "bm", "boldsymbol", "vec"):
            return f'<b class="mvec">{_TeX(self.group()).render()}</b>'
        if name in ("mathbb", "mathcal"):
            return f'<span class="mbb">{_TeX(self.group()).render()}</span>'
        if name in ("left", "right"):
            self.skip_space()
            bracket = self.take()
            return _esc(bracket) if bracket not in ".|" else ("" if bracket == "." else _esc(bracket))
        if name in ("overline", "bar"):
            return f'<span class="mover">{_TeX(self.group()).render()}</span>'
        if name in ("hat", "widehat"):
            return f'{_TeX(self.group()).render()}<span class="mhat">^</span>'
        if name in ("begin", "end"):
            env = self.group().strip()
            if name == "end":
                return ""
            return self.environment(env)
        if name in BIG_OPERATORS:
            glyph = GREEK.get(name, name)
            return f'<span class="mbig">{_esc(glyph)}</span>'
        if name in GREEK:
            glyph = GREEK[name]
            if name in FUNCTIONS:
                return f'<span class="mfn">{name}</span>'
            return f'<span class="msym">{_esc(glyph)}</span>'
        if name in ("quad", "qquad"):
            return "&emsp;" if name == "quad" else "&emsp;&emsp;"
        return f'<span class="mtext">{_esc(name)}</span>'

    def environment(self, name: str) -> str:
        """Handles matrix/pmatrix/bmatrix/cases/aligned."""
        end_token = f"\\end{{{name}}}"
        end_index = self.src.find(end_token, self.pos)
        body = self.src[self.pos: end_index if end_index != -1 else len(self.src)]
        self.pos = len(self.src) if end_index == -1 else end_index + len(end_token)
        rows = [row for row in re.split(r"\\\\", body) if row.strip()]
        cells_html: list[str] = []
        for row in rows:
            cells = re.split(r"&", row)
            cells_html.append(
                "<tr>" + "".join(f"<td>{_TeX(cell.strip()).render()}</td>" for cell in cells) + "</tr>"
            )
        delimiter = {"pmatrix": ("(", ")"), "bmatrix": ("[", "]"), "vmatrix": ("|", "|"), "Bmatrix": ("{", "}")}.get(name, ("", ""))
        klass = "mcases" if name == "cases" else "mmatrix"
        return (
            f'<span class="{klass}"><span class="mdelim">{_esc(delimiter[0])}</span>'
            f'<table class="mtable">{"".join(cells_html)}</table>'
            f'<span class="mdelim">{_esc(delimiter[1])}</span></span>'
        )


def render_tex(source: str, display: bool = False) -> str:
    """Renders a LaTeX fragment to escaped HTML."""
    if not source or not source.strip():
        return ""
    try:
        inner = _TeX(source).render()
    except RecursionError:  # pragma: no cover - pathological nesting
        return f'<code class="mtex">{_esc(source)}</code>'
    klass = "math math-display" if display else "math math-inline"
    return f'<span class="{klass}" role="math" aria-label="{_esc(source)}">{inner}</span>'


# ---------------------------------------------------------------------------
# Markdown
# ---------------------------------------------------------------------------

CODE_LANGUAGE_LABELS = {
    "python": "Python", "py": "Python", "java": "Java", "cpp": "C++", "c": "C",
    "javascript": "JavaScript", "js": "JavaScript", "typescript": "TypeScript",
    "ts": "TypeScript", "sql": "SQL", "bash": "Bash", "sh": "Shell", "html": "HTML",
    "css": "CSS", "json": "JSON", "yaml": "YAML", "kotlin": "Kotlin", "ruby": "Ruby",
    "go": "Go", "rust": "Rust", "matlab": "MATLAB", "text": "Text", "": "Code",
}

_INLINE_RE = re.compile(
    r"(`[^`]+`)"               # inline code
    r"|(\$\$[^$]+\$\$)"        # display maths
    r"|(\$[^$\n]+\$)"          # inline maths
    r"|(\*\*[^*]+\*\*)"        # bold
    r"|(==[^=]+==)"            # highlight
    r"|(\*[^*\n]+\*)"          # italic
    r"|(\[[^\]]+\]\([^)\s]+\))"  # link
)


def _inline(text: str) -> str:
    out: list[str] = []
    last = 0
    for match in _INLINE_RE.finditer(text):
        if match.start() > last:
            out.append(_esc(text[last:match.start()]))
        token = match.group(0)
        if token.startswith("`"):
            out.append(f"<code>{_esc(token[1:-1])}</code>")
        elif token.startswith("$$"):
            out.append(render_tex(token[2:-2], display=True))
        elif token.startswith("$"):
            out.append(render_tex(token[1:-1], display=False))
        elif token.startswith("**"):
            out.append(f"<strong>{_inline(token[2:-2])}</strong>")
        elif token.startswith("=="):
            out.append(f"<mark>{_inline(token[2:-2])}</mark>")
        elif token.startswith("*"):
            out.append(f"<em>{_inline(token[1:-1])}</em>")
        elif token.startswith("["):
            parsed = re.match(r"\[([^\]]+)\]\(([^)\s]+)\)", token)
            if parsed:
                label, href = parsed.group(1), parsed.group(2)
                if is_safe_url(href):
                    external = href.startswith("http")
                    attrs = ' target="_blank" rel="noopener noreferrer nofollow"' if external else ""
                    out.append(f'<a href="{_esc(href)}"{attrs}>{_inline(label)}</a>')
                else:
                    out.append(f"<span>{_inline(label)}</span>")
            else:
                out.append(_esc(token))
        else:
            out.append(_esc(token))
        last = match.end()
    if last < len(text):
        out.append(_esc(text[last:]))
    return "".join(out)


def _split_row(line: str) -> list[str]:
    return [cell.strip() for cell in line.strip().strip("|").split("|")]


def render(source: str | None) -> str:
    """Renders markdown to safe HTML."""
    if not source:
        return ""
    text = source.replace("\r\n", "\n").replace("\r", "\n")[:MAX_RENDER_LENGTH]
    lines = text.split("\n")
    out: list[str] = []
    index = 0
    total = len(lines)

    while index < total:
        line = lines[index]
        stripped = line.strip()

        if not stripped:
            index += 1
            continue

        fence = re.match(r"^```(\w*)\s*$", stripped)
        if fence:
            language = fence.group(1).lower()
            index += 1
            buffer: list[str] = []
            while index < total and not lines[index].strip().startswith("```"):
                buffer.append(lines[index])
                index += 1
            index += 1
            label = CODE_LANGUAGE_LABELS.get(language, language.upper() or "Code")
            code = _esc("\n".join(buffer))
            out.append(
                f'<div class="codeblock"><div class="codeblock-bar"><span>{_esc(label)}</span>'
                f'<span class="codeblock-lines">{len(buffer)} lines</span></div>'
                f"<pre><code>{code}</code></pre></div>"
            )
            continue

        if stripped.startswith("$$"):
            rest = stripped[2:]
            # Single-line display maths: $$ ... $$ all on one line.
            if len(rest) >= 2 and rest.endswith("$$"):
                out.append(render_tex(rest[:-2], display=True))
                index += 1
                continue
            index += 1
            buffer = []
            if rest.strip():
                buffer.append(rest)
            while index < total and not lines[index].strip().startswith("$$"):
                buffer.append(lines[index])
                index += 1
            index += 1
            body = "\n".join(buffer)
            if body.rstrip().endswith("$$"):
                body = body.rstrip()[:-2]
            out.append(render_tex(body, display=True))
            continue

        heading = re.match(r"^(#{1,6})\s+(.*)$", stripped)
        if heading:
            level = min(len(heading.group(1)) + 2, 6)
            out.append(f"<h{level} class='md-h'>{_inline(heading.group(2))}</h{level}>")
            index += 1
            continue

        if re.match(r"^(-{3,}|\*{3,}|_{3,})$", stripped):
            out.append("<hr class='md-hr'/>")
            index += 1
            continue

        # Table: a header row followed by a |---|---| separator row.
        if "|" in line and index + 1 < total and re.match(r"^\s*\|?[\s:|-]+\|[\s:|-]*$", lines[index +1]):
            head = _split_row(line)
            index += 2
            rows: list[list[str]] = []
            while index < total and "|" in lines[index] and lines[index].strip():
                rows.append(_split_row(lines[index]))
                index += 1
            out.append(
                "<div class='table-wrap'><table class='md-table'><thead><tr>"
                + "".join(f"<th>{_inline(cell)}</th>" for cell in head)
                + "</tr></thead><tbody>"
                + "".join(
                    "<tr>" + "".join(f"<td>{_inline(cell)}</td>" for cell in row) + "</tr>" for row in rows
                )
                + "</tbody></table></div>"
            )
            continue

        if re.match(r"^\s*>\s?", line):
            buffer = []
            while index < total and re.match(r"^\s*>\s?", lines[index]):
                buffer.append(re.sub(r"^\s*>\s?", "", lines[index]))
                index += 1
            out.append(f"<blockquote class='md-quote'>{_inline(' '.join(buffer))}</blockquote>")
            continue

        if re.match(r"^\s*[-*+]\s+", line):
            items = _collect_list(lines, index, r"^\s*[-*+]\s+")
            index += len(items)
            out.append(
                "<ul class='md-ul'>" + "".join(f"<li>{_inline(item)}</li>" for item in items) + "</ul>"
            )
            continue

        if re.match(r"^\s*\d+[.)]\s+", line):
            items = _collect_list(lines, index, r"^\s*\d+[.)]\s+")
            index += len(items)
            out.append(
                "<ol class='md-ol'>" + "".join(f"<li>{_inline(item)}</li>" for item in items) + "</ol>"
            )
            continue

        buffer = []
        while (
            index < total
            and lines[index].strip()
            and not re.match(r"^(#{1,6}\s|```|\$\$|\s*>\s?|\s*[-*+]\s|\s*\d+[.)]\s)", lines[index])
        ):
            buffer.append(lines[index])
            index += 1
        if buffer:
            out.append(f"<p class='md-p'>{_inline(' '.join(buffer))}</p>")
        else:
            index += 1

    return "".join(out)


def _collect_list(lines: list[str], start: int, pattern: str) -> list[str]:
    items: list[str] = []
    index = start
    while index < len(lines) and re.match(pattern, lines[index]):
        items.append(re.sub(pattern, "", lines[index], count=1))
        index += 1
    return items


def plain_text(source: str | None, limit: int = 240) -> str:
    """Strips markdown/LaTeX for snippets and search indexes."""
    if not source:
        return ""
    text = re.sub(r"```.*?```", " ", source, flags=re.S)
    text = re.sub(r"\$\$?.*?\$\$?", " ", text)
    text = re.sub(r"`([^`]+)`", r"\1", text)
    text = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", text)
    text = re.sub(r"[*_=#>|]", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text[:limit]


def excerpt(source: str | None, limit: int = 180) -> str:
    text = plain_text(source, limit + 1)
    return text if len(text) <= limit else text[: limit - 1].rstrip() + "…"


def render_many(chunks: Iterable[str]) -> str:
    return "".join(render(chunk) for chunk in chunks)
