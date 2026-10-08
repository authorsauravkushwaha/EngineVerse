"""Server-side 3D scenes for EngineVerse.

A scene is *data*, not markup. The browser renderer
(`backend/static/js/engine3d.js`) turns it into WebGL geometry; the server only
ever stores and serves numbers and allowlisted strings.

That split matters for security. The SVG diagrams are sanitised because SVG is
markup and markup can carry script. A scene cannot: `validate_scene()` rebuilds
the object from scratch, so anything that is not a finite number, a hex colour
or an allowlisted mesh name simply does not exist in the output. There is no
"escape the script" step because there is nothing to escape.

The validator also keeps the client honest in the other direction: every
numeric field is bounded, so a hand-edited row in the database cannot make a
phone build a 10-million-vertex mesh and hang the tab. The browser clamps the
same fields independently — see the `intParam`/`num` helpers in engine3d.js.

Keeping the vocabulary in the database (table `models_3d`) rather than in the
templates means a new model is an INSERT, not a deploy.
"""

from __future__ import annotations

import json
import math
from typing import Any

from .security.sanitize import safe_css_color

# ---------------------------------------------------------------------------
# The scene vocabulary. This must stay in step with the BUILDERS object in
# backend/static/js/engine3d.js; test_routes.py asserts that it does by
# reading the mesh names straight out of the JavaScript.
# ---------------------------------------------------------------------------

#: name -> ((param, low, high, default), ...). Values outside [low, high] are
#: clamped, missing values take the default, non-numbers are treated as missing.
MESH_PARAMS: dict[str, tuple[tuple[str, float, float, float], ...]] = {
    "box": (("width", 0.02, 200, 1.0), ("height", 0.02, 200, 1.0), ("depth", 0.02, 200, 1.0)),
    "sphere": (("radius", 0.005, 200, 0.5), ("segments", 3, 64, 24), ("rings", 2, 40, 14)),
    "cylinder": (("radius", 0.005, 200, 0.4), ("radiusTop", -1.0, 200, -1.0),
                 ("height", 0.005, 400, 1.0), ("segments", 3, 64, 24)),
    "cone": (("radius", 0.005, 200, 0.4), ("height", 0.005, 400, 1.0), ("segments", 3, 64, 24)),
    "torus": (("radius", 0.005, 200, 0.6), ("tube", 0.002, 100, 0.15), ("segments", 3, 96, 32), ("rings", 3, 48, 16)),
    "plane": (("size", 0.02, 400, 2.0),),
    "grid": (("size", 0.02, 400, 4.0), ("divisions", 2, 40, 10)),
    "axes": (("length", 0.02, 400, 1.0),),
    "wave": (
        ("width", 0.02, 400, 2.0), ("depth", 0.02, 400, 2.0),
        ("segmentsX", 2, 96, 32), ("segmentsZ", 2, 96, 32),
        ("amplitude", -200, 200, 0.25), ("frequency", 0, 200, 3.0),
    ),
    "helix": (
        ("radius", 0.005, 200, 0.5), ("height", 0.005, 400, 1.0),
        ("turns", 0.25, 60, 4.0), ("tube", 0.002, 20, 0.045), ("samples", 8, 400, 96),
    ),
    "arrow": (("shaft", 0.002, 10, 0.03), ("headLength", 0.01, 50, 0.22), ("headRadius", 0.005, 50, 0.09)),
    # line, points and tube carry a `points` list instead of scalar params.
    "line": (),
    "points": (),
    "tube": (("radius", 0.002, 50, 0.05),),
}

#: Meshes that take a polyline.
POLYLINE_MESHES = {"line", "points", "tube"}
#: Meshes that take an explicit start and end.
SPAN_MESHES = {"arrow"}

MESH_KINDS = frozenset(MESH_PARAMS)

MAX_OBJECTS = 220
MAX_LABELS = 40
MAX_POINTS = 400
MAX_SCENE_BYTES = 60_000
MAX_TEXT = 60

#: Colours are re-emitted as hex, so the palette below is only a convenience
#: for the scene builders — anything else goes through safe_css_color().
INK = "#e6ecff"
ACCENT = "#4f7cff"
WARM = "#ff9f43"
GOOD = "#35d39a"
BAD = "#ff6b6b"
NEUTRAL = "#8fa3c8"
DIM = "#3b4a6b"


# ---------------------------------------------------------------------------
# Validation
# ---------------------------------------------------------------------------

def _finite(value: Any, default: float) -> float:
    """A float that is actually a number. Booleans, strings and NaN are not."""
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return float(default)
    result = float(value)
    if math.isnan(result) or math.isinf(result):
        return float(default)
    return result


def _bounded(value: Any, low: float, high: float, default: float) -> float:
    return max(low, min(high, _finite(value, default)))


def _vec(value: Any, default: float = 0.0, limit: float = 500.0) -> list[float]:
    """Three finite numbers. Anything shorter, longer or non-numeric is dropped."""
    if not isinstance(value, (list, tuple)) or len(value) != 3:
        return [default, default, default]
    return [max(-limit, min(limit, _finite(v, default))) for v in value]


def _text(value: Any, limit: int = MAX_TEXT) -> str:
    """Plain text only, and safe inside an HTML attribute of either quote style.

    Labels are drawn with ``textContent`` in the browser, so markup is removed
    rather than escaped — it must never *look* like markup. Quote characters
    are removed too: a scene is served as JSON inside an attribute, and while
    Jinja autoescapes the structural quotes, a stray ``'`` in the payload would
    still break out of a single-quoted attribute. Labels have no use for
    quotes, so dropping them costs nothing and removes the hazard entirely.
    """
    if not isinstance(value, str):
        return ""
    cleaned = value
    for ch in "<>\"'\x00":
        cleaned = cleaned.replace(ch, " ")
    return " ".join(cleaned.split())[:limit]


def _points(value: Any) -> list[list[float]]:
    if not isinstance(value, (list, tuple)):
        return []
    out: list[list[float]] = []
    for item in value:
        if isinstance(item, (list, tuple)) and len(item) == 3:
            out.append(_vec(item))
        if len(out) >= MAX_POINTS:
            break
    return out


def _object(raw: Any) -> dict | None:
    if not isinstance(raw, dict):
        return None
    kind = raw.get("mesh")
    if not isinstance(kind, str) or kind not in MESH_PARAMS:
        return None

    out: dict[str, Any] = {"mesh": kind}
    for name, low, high, default in MESH_PARAMS[kind]:
        # Always emitted: the stored scene states every value it depends on,
        # so a reader does not have to know the defaults to understand it.
        out[name] = round(_bounded(raw.get(name), low, high, default), 6)
    if kind == "cylinder" and out["radiusTop"] < 0:
        # A negative top radius means "not set" — a plain cylinder, not a cone.
        out["radiusTop"] = out["radius"]
    if kind in POLYLINE_MESHES:
        pts = _points(raw.get("points"))
        # A line or tube needs two points to exist; a point cloud needs one.
        if len(pts) < (1 if kind == "points" else 2):
            return None
        out["points"] = pts
    if kind in SPAN_MESHES:
        out["from"] = _vec(raw.get("from"))
        out["to"] = _vec(raw.get("to"))
    if "mode" in raw and raw.get("mode") == "lines" and kind == "sphere":
        out["mode"] = "lines"

    out["position"] = _vec(raw.get("position"))
    out["rotation"] = _vec(raw.get("rotation"))
    scale = raw.get("scale")
    if isinstance(scale, (int, float)) and not isinstance(scale, bool):
        s = max(0.01, min(200.0, _finite(scale, 1.0)))
        out["scale"] = [round(s, 6)] * 3
    elif isinstance(scale, (list, tuple)):
        out["scale"] = [round(max(0.01, min(200.0, _finite(v, 1.0))), 6) for v in _vec(scale, 1.0)]
    out["color"] = safe_css_color(raw.get("color"), NEUTRAL)
    out["opacity"] = round(_bounded(raw.get("opacity"), 0.05, 1.0, 1.0), 4)
    if raw.get("unlit") is True:
        out["unlit"] = True
    return out


def validate_scene(value: Any) -> dict | None:
    """Return a rebuilt, safe scene, or ``None`` if there is nothing to draw.

    Accepts a dict or a JSON string (that is what the database column holds).
    The result contains only finite numbers, hex colours and allowlisted mesh
    names — every other key in the input is discarded, which is what makes this
    safe to hand to a browser.
    """
    if isinstance(value, (bytes, bytearray)):
        try:
            value = value.decode("utf-8")
        except UnicodeDecodeError:
            return None
    if isinstance(value, str):
        if len(value) > MAX_SCENE_BYTES:
            return None
        try:
            value = json.loads(value)
        except (ValueError, TypeError):
            return None
    if not isinstance(value, dict):
        return None

    raw_objects = value.get("objects")
    if not isinstance(raw_objects, (list, tuple)):
        return None
    objects = [item for item in (_object(entry) for entry in raw_objects[:MAX_OBJECTS]) if item]
    if not objects:
        return None

    camera = value.get("camera") if isinstance(value.get("camera"), dict) else {}
    scene: dict[str, Any] = {
        "camera": {
            "distance": round(_bounded(camera.get("distance"), 0.8, 200, 6.0), 4),
            "yaw": round(_bounded(camera.get("yaw"), -360, 360, 35.0), 3),
            "pitch": round(_bounded(camera.get("pitch"), -85, 85, 18.0), 3),
            "fov": round(_bounded(camera.get("fov"), 15, 100, 45.0), 3),
        },
        "target": _vec(value.get("target")),
        "spin": round(_bounded(value.get("spin"), 0, 2, 0.22), 4),
        "ambient": round(_bounded(value.get("ambient"), 0, 1, 0.28), 4),
        "background": safe_css_color(value.get("background"), "#0b1224"),
        "objects": objects,
    }

    labels: list[dict] = []
    raw_labels = value.get("labels")
    if isinstance(raw_labels, (list, tuple)):
        for raw in raw_labels[:MAX_LABELS]:
            if not isinstance(raw, dict):
                continue
            text = _text(raw.get("text"))
            if not text:
                continue
            labels.append({"text": text, "at": _vec(raw.get("at"))})
    if labels:
        scene["labels"] = labels
    return scene


def scene_json(value: Any) -> str | None:
    """The attribute-ready form of a scene, or ``None`` when it is unusable."""
    scene = validate_scene(value)
    if not scene:
        return None
    return json.dumps(scene, separators=(",", ":"), ensure_ascii=True)


# ---------------------------------------------------------------------------
# Builders. Small helpers so a scene reads like a description of the model
# rather than a list of coordinates.
# ---------------------------------------------------------------------------

def _round6(v: float) -> float:
    return round(float(v), 6)


def _v(x: float, y: float, z: float) -> list[float]:
    return [_round6(x), _round6(y), _round6(z)]


def box(position, *, size=(1.0, 1.0, 1.0), color=ACCENT, opacity=1.0, rotation=None) -> dict:
    node: dict[str, Any] = {"mesh": "box", "width": _round6(size[0]), "height": _round6(size[1]),
                            "depth": _round6(size[2]), "position": _v(*position), "color": color}
    if opacity < 1.0:
        node["opacity"] = _round6(opacity)
    if rotation:
        node["rotation"] = _v(*rotation)
    return node


def sphere(position, radius=0.16, *, color=ACCENT, wire=False, opacity=1.0) -> dict:
    node: dict[str, Any] = {"mesh": "sphere", "radius": _round6(radius), "position": _v(*position), "color": color}
    if wire:
        node["mode"] = "lines"
    if opacity < 1.0:
        node["opacity"] = _round6(opacity)
    return node


def arrow(start, end, *, color=WARM, shaft=0.035, head=0.22, radius=0.085) -> dict:
    return {"mesh": "arrow", "from": _v(*start), "to": _v(*end), "color": color,
            "shaft": _round6(shaft), "headLength": _round6(head), "headRadius": _round6(radius)}


def edge(a, b, *, color=DIM) -> dict:
    return {"mesh": "line", "points": [_v(*a), _v(*b)], "color": color}


def chain(points, *, color=DIM) -> dict:
    return {"mesh": "line", "points": [_v(*p) for p in points], "color": color}


def pipe(points, *, color=ACCENT, radius=0.05) -> dict:
    return {"mesh": "tube", "points": [_v(*p) for p in points], "color": color, "radius": _round6(radius)}


def cylinder(position, radius=0.4, height=1.0, *, color=ACCENT, rotation=None, opacity=1.0,
             radius_top=None) -> dict:
    node: dict[str, Any] = {"mesh": "cylinder", "radius": _round6(radius), "height": _round6(height),
                            "position": _v(*position), "color": color}
    if radius_top is not None:
        node["radiusTop"] = _round6(radius_top)
    if rotation:
        node["rotation"] = _v(*rotation)
    if opacity < 1.0:
        node["opacity"] = _round6(opacity)
    return node


def helix(position, radius=0.5, height=1.0, turns=4, *, color=WARM, tube=0.045, rotation=None) -> dict:
    node: dict[str, Any] = {"mesh": "helix", "radius": _round6(radius), "height": _round6(height),
                            "turns": _round6(turns), "tube": _round6(tube),
                            "position": _v(*position), "color": color}
    if rotation:
        node["rotation"] = _v(*rotation)
    return node


def grid(size=4.0, divisions=8, *, color=DIM, position=(0.0, 0.0, 0.0)) -> dict:
    return {"mesh": "grid", "size": _round6(size), "divisions": int(divisions), "color": color,
            "position": _v(*position)}


def label(text, at) -> dict:
    return {"text": text, "at": _v(*at)}


def scene(objects, *, labels=None, distance=6.0, yaw=35.0, pitch=18.0, spin=0.22,
          target=(0.0, 0.0, 0.0), background="#0b1224", ambient=0.3) -> dict:
    data: dict[str, Any] = {
        "camera": {"distance": _round6(distance), "yaw": _round6(yaw), "pitch": _round6(pitch)},
        "target": _v(*target),
        "spin": _round6(spin),
        "ambient": _round6(ambient),
        "background": background,
        "objects": objects,
    }
    if labels:
        data["labels"] = labels
    return data


def lattice_points(spacing=1.0, n=2, *, color=INK, radius=0.07, offset=(0.0, 0.0, 0.0)) -> list[dict]:
    """A small cubic lattice — atoms, grid cells, memory blocks, buckets."""
    out = []
    half = (n - 1) * spacing / 2
    for i in range(n):
        for j in range(n):
            for k in range(n):
                out.append(sphere((offset[0] - half + i * spacing, offset[1] - half + j * spacing,
                                   offset[2] - half + k * spacing), radius, color=color))
    return out


def wire_box(position, size, *, color=DIM) -> list[dict]:
    """The twelve edges of a box, drawn as lines. Cheaper and clearer than a
    translucent cube when the cube only marks a volume."""
    x, y, z = position
    w, h, d = size
    corners = [
        (x - w / 2, y - h / 2, z - d / 2), (x + w / 2, y - h / 2, z - d / 2),
        (x + w / 2, y + h / 2, z - d / 2), (x - w / 2, y + h / 2, z - d / 2),
        (x - w / 2, y - h / 2, z + d / 2), (x + w / 2, y - h / 2, z + d / 2),
        (x + w / 2, y + h / 2, z + d / 2), (x - w / 2, y + h / 2, z + d / 2),
    ]
    pairs = [(0, 1), (1, 2), (2, 3), (3, 0), (4, 5), (5, 6), (6, 7), (7, 4), (0, 4), (1, 5), (2, 6), (3, 7)]
    return [edge(corners[a], corners[b], color=color) for a, b in pairs]


def binary_tree_layout(values, *, x_spread=1.35, z_spread=0.9, y_drop=0.75):
    """Positions for a complete binary tree, spread in X and Z so the depth of
    the tree is visible as depth in space rather than as flatness."""
    positions: list[tuple[float, float, float]] = []
    for index in range(len(values)):
        level = int(math.floor(math.log2(index + 1)))
        slot = index - (2 ** level - 1)
        width = 2 ** level
        x = (slot - (width - 1) / 2) * x_spread * (1.6 ** -level) * 2
        positions.append((_round6(x), _round6(-level * y_drop + 1.2), _round6(level * z_spread)))
    return positions


def tree_edges(positions) -> list[dict]:
    out = []
    for index in range(1, len(positions)):
        parent = (index - 1) // 2
        out.append(edge(positions[parent], positions[index], color=DIM))
    return out
