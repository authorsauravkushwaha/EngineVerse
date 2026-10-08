"""Server-side SVG diagrams for EngineVerse.

A diagram is *data*, not markup. `seed_data/diagrams_data.py` describes a scene
as a list of primitives with numbers and allowlisted strings, and this module
rebuilds the SVG from scratch. Nothing a caller puts in survives unless it is a
finite number inside bounds, a hex colour, or a string that has had its markup
removed — the same split as `models3d.py`, for the same reason: there is no
"escape the script" step because there is nothing to escape.

Two decisions worth knowing about before editing this file:

* **Arrowheads are drawn as geometry, not `<marker>` references.** A marker
  needs an `id`, and every diagram on a page shares one document, so the six
  hand-written diagrams that each declare `id="ar"` collide the moment two of
  them render together — the browser resolves `url(#ar)` to whichever came
  first. Drawing the head as a triangle keeps the output id-free.
* **Validation never drops an object silently.** An unknown kind raises rather
  than being skipped, because a skipped primitive looks identical to a diagram
  that was drawn correctly with one part missing.
"""

from __future__ import annotations

import json
import math
from typing import Any, Iterable, Sequence

from .security.sanitize import safe_css_color

# ---------------------------------------------------------------------------
# Limits. These bound what a hand-edited database row can make a browser do.
# ---------------------------------------------------------------------------

MAX_OBJECTS = 260
MAX_POINTS = 400
MAX_HOTSPOTS = 12
MAX_TEXT = 120
MAX_SVG_BYTES = 90_000
MIN_CANVAS = 120
MAX_CANVAS = 1600

#: name -> ((param, low, high, default), ...)
PRIMITIVES: dict[str, tuple[tuple[str, float, float, float], ...]] = {
    "box": (("x", 0, MAX_CANVAS, 0), ("y", 0, MAX_CANVAS, 0),
            ("w", 1, MAX_CANVAS, 80), ("h", 1, MAX_CANVAS, 40),
            ("rx", 0, 60, 6)),
    "circle": (("cx", 0, MAX_CANVAS, 0), ("cy", 0, MAX_CANVAS, 0), ("r", 1, 400, 12)),
    "line": (("x1", -MAX_CANVAS, MAX_CANVAS * 2, 0), ("y1", -MAX_CANVAS, MAX_CANVAS * 2, 0),
             ("x2", -MAX_CANVAS, MAX_CANVAS * 2, 0), ("y2", -MAX_CANVAS, MAX_CANVAS * 2, 0)),
    "arrow": (("x1", -MAX_CANVAS, MAX_CANVAS * 2, 0), ("y1", -MAX_CANVAS, MAX_CANVAS * 2, 0),
              ("x2", -MAX_CANVAS, MAX_CANVAS * 2, 0), ("y2", -MAX_CANVAS, MAX_CANVAS * 2, 0),
              ("head", 2, 40, 9)),
    "curve": (),      # carries `points`
    "poly": (),       # carries `points`
    "text": (("x", -MAX_CANVAS, MAX_CANVAS * 2, 0), ("y", -MAX_CANVAS, MAX_CANVAS * 2, 0),
             ("size", 6, 48, 13), ("weight", 100, 900, 400), ("opacity", 0.05, 1.0, 1.0),
             ("rotate", -180, 180, 0)),
    "axis": (("x", 0, MAX_CANVAS, 40), ("y", 0, MAX_CANVAS, 40),
             ("w", 20, MAX_CANVAS, 400), ("h", 20, MAX_CANVAS, 200), ("ticks", 0, 40, 5)),
    "grid": (("x", 0, MAX_CANVAS, 0), ("y", 0, MAX_CANVAS, 0),
             ("w", 10, MAX_CANVAS, 800), ("h", 10, MAX_CANVAS, 600), ("step", 8, 200, 40)),
    "brace": (("x", 0, MAX_CANVAS, 0), ("y", 0, MAX_CANVAS, 0), ("w", 10, MAX_CANVAS, 100),
              ("size", 4, 30, 8)),
    "arc": (("cx", 0, MAX_CANVAS, 0), ("cy", 0, MAX_CANVAS, 0), ("r", 2, 400, 30),
            ("a0", -720, 720, 0), ("a1", -720, 720, 90)),
}

#: stroke/fill are validated as colours; `anchor` is allowlisted here.
ANCHORS = {"start", "middle", "end"}
DEFAULT_STROKE = "#334155"
DEFAULT_FILL = "none"
ACCENT = "#4f7cff"


# ---------------------------------------------------------------------------
# Small helpers
# ---------------------------------------------------------------------------

def _num(value: Any, low: float, high: float, default: float) -> float:
    """A number inside [low, high], or the default."""
    try:
        number = float(value)
    except (TypeError, ValueError):
        return default
    if not math.isfinite(number):
        return default
    return max(low, min(high, number))


def _int(value: Any, low: int, high: int, default: int) -> int:
    return int(round(_num(value, low, high, default)))


def _text(value: Any, limit: int = MAX_TEXT) -> str:
    """Label text with markup removed.

    Angle brackets and quotes are stripped rather than escaped: SVG is served
    inside an attribute *and* as element text depending on the field, and
    escaping correctly for both is how the original diagram helper ended up
    stripping `<` and `>` but leaving a quote that broke out of a
    single-quoted attribute. Removing the characters is correct for both.
    """
    if value is None:
        return ""
    cleaned = "".join(ch for ch in str(value) if ch not in "<>\"'\x00")
    cleaned = " ".join(cleaned.split())
    return cleaned[:limit]


def _points(raw: Any, limit: int = MAX_POINTS) -> list[tuple[float, float]]:
    out: list[tuple[float, float]] = []
    if not isinstance(raw, (list, tuple)):
        return out
    for pair in raw[:limit]:
        if isinstance(pair, (list, tuple)) and len(pair) >= 2:
            out.append((_num(pair[0], -MAX_CANVAS, MAX_CANVAS * 2, 0.0),
                        _num(pair[1], -MAX_CANVAS, MAX_CANVAS * 2, 0.0)))
    return out


def _fmt(value: float) -> str:
    """Shortest representation that does not lose a visible pixel."""
    return f"{value:.1f}".rstrip("0").rstrip(".")


# ---------------------------------------------------------------------------
# Primitive builders. Each returns a list of SVG element strings.
# ---------------------------------------------------------------------------

def _el_box(o: dict) -> list[str]:
    return [
        f'<rect x="{_fmt(o["x"])}" y="{_fmt(o["y"])}" width="{_fmt(o["w"])}" '
        f'height="{_fmt(o["h"])}" rx="{_fmt(o["rx"])}" fill="{o["fill"]}" '
        f'stroke="{o["stroke"]}" stroke-width="{_fmt(o["width"])}"/>'
    ]


def _el_circle(o: dict) -> list[str]:
    return [
        f'<circle cx="{_fmt(o["cx"])}" cy="{_fmt(o["cy"])}" r="{_fmt(o["r"])}" '
        f'fill="{o["fill"]}" stroke="{o["stroke"]}" stroke-width="{_fmt(o["width"])}"/>'
    ]


def _el_line(o: dict) -> list[str]:
    dash = f' stroke-dasharray="{o["dash"]}"' if o.get("dash") else ""
    return [
        f'<line x1="{_fmt(o["x1"])}" y1="{_fmt(o["y1"])}" x2="{_fmt(o["x2"])}" '
        f'y2="{_fmt(o["y2"])}" stroke="{o["stroke"]}" stroke-width="{_fmt(o["width"])}"'
        f' stroke-linecap="round"{dash}/>'
    ]


def _el_arrow(o: dict) -> list[str]:
    """A line plus a triangular head, so no marker id is needed."""
    x1, y1, x2, y2, head = o["x1"], o["y1"], o["x2"], o["y2"], o["head"]
    dx, dy = x2 - x1, y2 - y1
    length = math.hypot(dx, dy)
    parts = _el_line(o)
    if length < head:
        return parts          # too short for a head; the line alone is honest
    ux, uy = dx / length, dy / length
    px, py = -uy, ux                       # unit perpendicular
    base_x, base_y = x2 - ux * head, y2 - uy * head
    half = head * 0.42
    tip = f"{_fmt(x2)},{_fmt(y2)}"
    left = f"{_fmt(base_x + px * half)},{_fmt(base_y + py * half)}"
    right = f"{_fmt(base_x - px * half)},{_fmt(base_y - py * half)}"
    parts.append(f'<polygon points="{tip} {left} {right}" fill="{o["stroke"]}"/>')
    return parts


def _el_curve(o: dict) -> list[str]:
    points = o["points"]
    if len(points) < 2:
        return []
    data = " ".join(f"{_fmt(x)},{_fmt(y)}" for x, y in points)
    dash = f' stroke-dasharray="{o["dash"]}"' if o.get("dash") else ""
    return [
        f'<polyline points="{data}" fill="{o["fill"]}" stroke="{o["stroke"]}" '
        f'stroke-width="{_fmt(o["width"])}" stroke-linejoin="round" '
        f'stroke-linecap="round"{dash}/>'
    ]


def _el_poly(o: dict) -> list[str]:
    points = o["points"]
    if len(points) < 3:
        return []
    data = " ".join(f"{_fmt(x)},{_fmt(y)}" for x, y in points)
    return [
        f'<polygon points="{data}" fill="{o["fill"]}" stroke="{o["stroke"]}" '
        f'stroke-width="{_fmt(o["width"])}" stroke-linejoin="round"/>'
    ]


def _el_text(o: dict) -> list[str]:
    body = o["text"]
    if not body:
        return []
    anchor = o["anchor"] if o["anchor"] in ANCHORS else "start"
    weight = f' font-weight="{o["weight"]}"' if o["weight"] != 400 else ""
    opacity = f' opacity="{_fmt(o["opacity"])}"' if o["opacity"] < 1 else ""
    rotate = f' transform="rotate({_fmt(o["rotate"])} {_fmt(o["x"])} {_fmt(o["y"])})"' if o["rotate"] else ""
    return [
        f'<text x="{_fmt(o["x"])}" y="{_fmt(o["y"])}" font-size="{_fmt(o["size"])}" '
        f'text-anchor="{anchor}" fill="{o["fill"]}"{weight}{opacity}{rotate}'
        f' font-family="ui-sans-serif,system-ui,sans-serif">{body}</text>'
    ]


def _el_axis(o: dict) -> list[str]:
    """An x/y axis pair with arrowed ends and optional ticks."""
    x, y, w, h, ticks = o["x"], o["y"], o["w"], o["h"], o["ticks"]
    parts = _el_arrow({"x1": x, "y1": y + h, "x2": x + w, "y2": y + h,
                       "stroke": o["stroke"], "width": o["width"], "head": 8, "dash": ""})
    parts += _el_arrow({"x1": x, "y1": y + h, "x2": x, "y2": y,
                        "stroke": o["stroke"], "width": o["width"], "head": 8, "dash": ""})
    if ticks > 1:
        for index in range(1, ticks):
            tx = x + w * index / ticks
            parts.append(f'<line x1="{_fmt(tx)}" y1="{_fmt(y + h - 3)}" x2="{_fmt(tx)}" '
                         f'y2="{_fmt(y + h + 3)}" stroke="{o["stroke"]}" stroke-width="1" opacity="0.5"/>')
    return parts


def _el_grid(o: dict) -> list[str]:
    x, y, w, h, step = o["x"], o["y"], o["w"], o["h"], o["step"]
    parts = []
    gx = x
    while gx <= x + w:
        parts.append(f'<line x1="{_fmt(gx)}" y1="{_fmt(y)}" x2="{_fmt(gx)}" y2="{_fmt(y + h)}" '
                     f'stroke="{o["stroke"]}" stroke-width="0.5" opacity="0.18"/>')
        gx += step
    gy = y
    while gy <= y + h:
        parts.append(f'<line x1="{_fmt(x)}" y1="{_fmt(gy)}" x2="{_fmt(x + w)}" y2="{_fmt(gy)}" '
                     f'stroke="{o["stroke"]}" stroke-width="0.5" opacity="0.18"/>')
        gy += step
    return parts


def _el_brace(o: dict) -> list[str]:
    """A dimension line with end ticks, for labelling a width or a length."""
    x, y, w, size = o["x"], o["y"], o["w"], o["size"]
    colour = o["stroke"]
    return [
        f'<line x1="{_fmt(x)}" y1="{_fmt(y)}" x2="{_fmt(x + w)}" y2="{_fmt(y)}" '
        f'stroke="{colour}" stroke-width="1.2"/>',
        f'<line x1="{_fmt(x)}" y1="{_fmt(y - size / 2)}" x2="{_fmt(x)}" '
        f'y2="{_fmt(y + size / 2)}" stroke="{colour}" stroke-width="1.2"/>',
        f'<line x1="{_fmt(x + w)}" y1="{_fmt(y - size / 2)}" x2="{_fmt(x + w)}" '
        f'y2="{_fmt(y + size / 2)}" stroke="{colour}" stroke-width="1.2"/>',
    ]


def _el_arc(o: dict) -> list[str]:
    cx, cy, r = o["cx"], o["cy"], o["r"]
    a0, a1 = math.radians(o["a0"]), math.radians(o["a1"])
    x0, y0 = cx + r * math.cos(a0), cy - r * math.sin(a0)
    x1, y1 = cx + r * math.cos(a1), cy - r * math.sin(a1)
    large = 1 if abs(a1 - a0) > math.pi else 0
    sweep = 0 if a1 > a0 else 1
    return [
        f'<path d="M {_fmt(x0)} {_fmt(y0)} A {_fmt(r)} {_fmt(r)} 0 {large} {sweep} '
        f'{_fmt(x1)} {_fmt(y1)}" fill="none" stroke="{o["stroke"]}" '
        f'stroke-width="{_fmt(o["width"])}" stroke-linecap="round"/>'
    ]


BUILDERS = {
    "box": _el_box, "circle": _el_circle, "line": _el_line, "arrow": _el_arrow,
    "curve": _el_curve, "poly": _el_poly, "text": _el_text, "axis": _el_axis,
    "grid": _el_grid, "brace": _el_brace, "arc": _el_arc,
}


# ---------------------------------------------------------------------------
# Validation
# ---------------------------------------------------------------------------

def _validate_object(raw: Any, index: int) -> dict:
    """Rebuild one primitive from scratch, or raise."""
    if not isinstance(raw, dict):
        raise TypeError(f"diagram object {index} is not a mapping")
    kind = raw.get("kind")
    if kind not in PRIMITIVES:
        raise ValueError(
            f"diagram object {index} has unknown kind {kind!r}; "
            f"expected one of {sorted(PRIMITIVES)}"
        )
    out: dict[str, Any] = {"kind": kind}
    for name, low, high, default in PRIMITIVES[kind]:
        out[name] = _int(raw.get(name), int(low), int(high), int(default)) if isinstance(default, int) \
            else _num(raw.get(name), low, high, default)
    out["stroke"] = safe_css_color(raw.get("stroke"), DEFAULT_STROKE)
    out["fill"] = safe_css_color(raw.get("fill"), DEFAULT_FILL) if raw.get("fill") is not None else "none"
    out["width"] = _num(raw.get("width"), 0.25, 24, 1.6)
    out["dash"] = _text(raw.get("dash"), 24)
    out["anchor"] = raw.get("anchor") if raw.get("anchor") in ANCHORS else "start"
    out["text"] = _text(raw.get("text"))
    out["points"] = _points(raw.get("points"))
    # Non-negative stroke width, and `none`/`transparent` stay as keywords.
    return out


def validate_scene(scene: Any) -> dict:
    """Return a rebuilt scene, or raise if it cannot be drawn safely.

    Raises rather than filtering: a diagram that silently loses a primitive
    looks exactly like one that was authored without it, and the two are only
    distinguishable at review time.
    """
    if not isinstance(scene, dict):
        raise TypeError("diagram scene must be a mapping")
    raw_objects = scene.get("objects")
    if not isinstance(raw_objects, (list, tuple)):
        raise TypeError("diagram scene needs an `objects` list")
    if len(raw_objects) > MAX_OBJECTS:
        raise ValueError(f"diagram has {len(raw_objects)} objects, limit is {MAX_OBJECTS}")
    if not raw_objects:
        raise ValueError("diagram has no objects")

    width = _int(scene.get("width"), MIN_CANVAS, MAX_CANVAS, 640)
    height = _int(scene.get("height"), MIN_CANVAS, MAX_CANVAS, 300)
    objects = [_validate_object(obj, i) for i, obj in enumerate(raw_objects)]

    raw_hotspots = scene.get("hotspots") or []
    if not isinstance(raw_hotspots, (list, tuple)):
        raise TypeError("diagram hotspots must be a list")
    if len(raw_hotspots) > MAX_HOTSPOTS:
        raise ValueError(f"diagram has {len(raw_hotspots)} hotspots, limit is {MAX_HOTSPOTS}")
    hotspots = []
    for spot in raw_hotspots:
        if not isinstance(spot, dict):
            raise TypeError("hotspot must be a mapping")
        label = _text(spot.get("label"), 60)
        explain = _text(spot.get("explain"), 400)
        if not label:
            continue                     # an unlabelled hotspot has nothing to say
        hotspots.append({
            "x": _int(spot.get("x"), 0, width, 0), "y": _int(spot.get("y"), 0, height, 0),
            "w": _int(spot.get("w"), 4, width, 40), "h": _int(spot.get("h"), 4, height, 40),
            "label": label, "explain": explain,
        })

    return {
        "title": _text(scene.get("title"), 120),
        "caption": _text(scene.get("caption"), 400),
        "label": _text(scene.get("label") or scene.get("title"), 200),
        "width": width, "height": height,
        "objects": objects, "hotspots": hotspots,
    }


# ---------------------------------------------------------------------------
# Rendering
# ---------------------------------------------------------------------------

def render_svg(scene: dict) -> str:
    """Build the SVG for a validated scene.

    `role="img"` plus `aria-label` is what makes the diagram reachable by a
    screen reader; the text primitives inside are then announced rather than
    leaving the figure silent.
    """
    parts: list[str] = [
        f'<svg viewBox="0 0 {scene["width"]} {scene["height"]}" '
        f'xmlns="http://www.w3.org/2000/svg" role="img" '
        f'aria-label="{scene["label"]}" preserveAspectRatio="xMidYMid meet">'
    ]
    emitted = 0
    for obj in scene["objects"]:
        builder = BUILDERS[obj["kind"]]
        for element in builder(obj):
            parts.append(element)
            emitted += 1
    parts.append("</svg>")
    svg = "".join(parts)
    if emitted == 0:
        raise ValueError("diagram rendered no elements")
    if len(svg.encode("utf-8")) > MAX_SVG_BYTES:
        raise ValueError(f"diagram svg is {len(svg.encode('utf-8'))} bytes, limit is {MAX_SVG_BYTES}")
    return svg


def render(scene: Any) -> tuple[str, str]:
    """Validate and render, returning ``(svg, hotspots_json)``.

    The pair is what the `diagrams` table stores, so this is the single entry
    point the seeder should use.
    """
    validated = validate_scene(scene)
    return render_svg(validated), json.dumps(validated["hotspots"], ensure_ascii=False)


# ---------------------------------------------------------------------------
# Composers. These are conveniences for authoring, not part of the vocabulary.
# ---------------------------------------------------------------------------

def box(x: float, y: float, w: float, h: float, label: str = "", *,
        fill: str = "none", stroke: str = DEFAULT_STROKE, size: int = 13,
        anchor: str = "middle", rx: int = 6, width: float = 1.6) -> list[dict]:
    """A rectangle, optionally with a centred label. Returns one or two objects."""
    out = [{"kind": "box", "x": x, "y": y, "w": w, "h": h, "rx": rx,
            "fill": fill, "stroke": stroke, "width": width}]
    if label:
        out.append({"kind": "text", "x": x + w / 2, "y": y + h / 2 + size * 0.35,
                    "text": label, "size": size, "anchor": anchor,
                    "fill": stroke if fill == "none" else DEFAULT_STROKE})
    return out


def arrow(x1: float, y1: float, x2: float, y2: float, *, stroke: str = ACCENT,
          width: float = 1.8, head: int = 9) -> dict:
    return {"kind": "arrow", "x1": x1, "y1": y1, "x2": x2, "y2": y2,
            "stroke": stroke, "width": width, "head": head}


def label(x: float, y: float, text: str, *, size: int = 13, anchor: str = "start",
          fill: str = "#334155", weight: int = 400, opacity: float = 1.0,
          rotate: float = 0) -> dict:
    return {"kind": "text", "x": x, "y": y, "text": text, "size": size,
            "anchor": anchor, "fill": fill, "weight": weight,
            "opacity": opacity, "rotate": rotate}


def polyline(points: Iterable[Sequence[float]], *, stroke: str = ACCENT,
             width: float = 2.2, dash: str = "", fill: str = "none") -> dict:
    return {"kind": "curve", "points": [list(p) for p in points],
            "stroke": stroke, "width": width, "dash": dash, "fill": fill}


def hotspot(x: float, y: float, w: float, h: float, label_text: str, explain: str) -> dict:
    return {"x": x, "y": y, "w": w, "h": h, "label": label_text, "explain": explain}
