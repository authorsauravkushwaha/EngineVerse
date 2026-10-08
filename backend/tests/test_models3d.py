"""3D models: the scene vocabulary, the validator, and the seeded content.

These tests exist because of a specific bug. ``validate_scene()`` drops objects
it cannot understand rather than failing — which is the right behaviour for
untrusted data, but it also means a scene can silently lose content. A stray
``*`` in front of a helper that returns a dict (``*pipe(...)`` unpacks the
dict's *keys*) turned eight objects into junk strings, the validator dropped
them, and the Venturi model shipped with no streamlines. Every Python test
passed, because nothing asserted that a scene keeps everything it started with.

``test_validation_drops_nothing_from_a_seeded_scene`` is that assertion.
"""
from __future__ import annotations

import html
import json
import re
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "backend"))

from engineverse import catalog, db, models3d  # noqa: E402
from seed_data import models_3d as content  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
ENGINE = ROOT / "backend" / "static" / "js" / "engine3d.js"


def js_builder_kinds() -> set[str]:
    """The mesh names the browser actually knows how to draw."""
    source = ENGINE.read_text()
    block = re.search(r"const BUILDERS = \{(.*?)\n  \};", source, re.S)
    assert block, "could not locate the BUILDERS table in engine3d.js"
    return set(re.findall(r"^    (\w+):", block.group(1), re.M))


# ---------------------------------------------------------------------------
# The two vocabularies must not drift apart
# ---------------------------------------------------------------------------

class TestSceneVocabulary:
    def test_python_and_javascript_agree_on_the_mesh_vocabulary(self):
        assert models3d.MESH_KINDS == frozenset(js_builder_kinds())

    def test_every_mesh_kind_declares_its_parameters(self):
        assert set(models3d.MESH_PARAMS) == set(models3d.MESH_KINDS)

    def test_polylines_and_spans_are_covered(self):
        assert models3d.POLYLINE_MESHES <= models3d.MESH_KINDS
        assert models3d.SPAN_MESHES <= models3d.MESH_KINDS

    def test_the_renderer_clamps_the_same_fields_the_server_does(self):
        """A bound enforced on only one side is not a bound."""
        source = ENGINE.read_text()
        for param in ("segments", "rings", "segmentsX", "segmentsZ", "samples", "divisions", "radiusTop"):
            assert param in source, f"{param} is validated in Python but not clamped in the renderer"
        assert "MAX_VERTS" in source, "the renderer has no vertex ceiling of its own"


# ---------------------------------------------------------------------------
# The validator
# ---------------------------------------------------------------------------

class TestValidator:
    def _good(self):
        return {"objects": [{"mesh": "sphere", "radius": 0.4, "position": [0, 0, 0], "color": "#4f7cff"}]}

    def test_a_plain_scene_survives(self):
        scene = models3d.validate_scene(self._good())
        assert scene and scene["objects"][0]["mesh"] == "sphere"
        assert scene["objects"][0]["color"] == "#4f7cff"

    def test_it_accepts_the_json_string_form_the_database_holds(self):
        scene = models3d.validate_scene(json.dumps(self._good()))
        assert scene and len(scene["objects"]) == 1

    @pytest.mark.parametrize("junk", [
        None, "", "not json", "[]", '"a string"', "42", b"\xff\xfe",
        {"objects": []}, {"objects": "not a list"}, {"objects": {}},
        {}, {"labels": []}, {"objects": [{"mesh": "nope"}]}, {"objects": [None, 1, "x"]},
    ])
    def test_it_refuses_anything_that_is_not_a_drawable_scene(self, junk):
        assert models3d.validate_scene(junk) is None

    def test_an_oversized_payload_is_refused_without_being_parsed(self):
        huge = json.dumps({"objects": [{"mesh": "sphere"}] * 5000})
        assert len(huge) > models3d.MAX_SCENE_BYTES
        assert models3d.validate_scene(huge) is None

    def test_unknown_keys_are_discarded_rather_than_passed_through(self):
        raw = self._good()
        raw["objects"][0].update({"onload": "steal()", "style": "url(x)", "extra": 1})
        raw["evil"] = "<script>"
        scene = models3d.validate_scene(raw)
        keys = set(scene["objects"][0])
        assert not {"onload", "style", "extra", "evil"} & keys
        assert not {"evil"} & set(scene)

    @pytest.mark.parametrize("payload", [
        "<script>alert(1)</script>",
        "' onmouseover='x",
        '"><img src=x>',
        "quote \" and ' together",
    ])
    def test_label_text_cannot_carry_markup(self, payload):
        scene = models3d.validate_scene({"objects": [{"mesh": "box"}], "labels": [{"text": payload, "at": [0, 0, 0]}]})
        text = scene["labels"][0]["text"]
        for ch in "<>'\"":
            assert ch not in text

    def test_the_emitted_json_cannot_break_out_of_an_attribute(self):
        """JSON must contain structural quotes, so safety here is two-part:
        the payload carries no ``'``, ``<`` or ``>`` (so it is safe even inside
        a single-quoted attribute emitted with ``| safe``), and the template
        environment autoescapes the structural ``"``."""
        raw = self._good()
        raw["labels"] = [{"text": "V'\"<>", "at": [0, 0, 0]}]
        encoded = models3d.scene_json(raw)
        for ch in "'<>":
            assert ch not in encoded, f"{ch!r} in the payload would break the attribute"
        from web.deps import templates
        assert templates.env.autoescape is True, "the structural quotes rely on autoescaping"

    def test_absurd_numbers_are_clamped_not_honoured(self):
        scene = models3d.validate_scene({
            "objects": [{"mesh": "sphere", "radius": 1e9, "segments": 1e9, "rings": 1e9,
                         "opacity": 99, "scale": 1e9, "position": [1e9, 0, 0]}],
            "camera": {"distance": 1e9, "fov": 1e9, "pitch": 1e9},
            "spin": 1e9, "ambient": -5,
        })
        obj = scene["objects"][0]
        assert obj["radius"] <= 200 and obj["segments"] <= 64 and obj["rings"] <= 40
        assert obj["opacity"] == 1.0
        assert max(obj["scale"]) <= 200
        assert max(abs(v) for v in obj["position"]) <= 500
        assert scene["camera"]["distance"] <= 200
        assert 15 <= scene["camera"]["fov"] <= 100
        assert scene["camera"]["pitch"] <= 85
        assert scene["spin"] <= 2 and scene["ambient"] == 0

    def test_nan_and_infinity_never_reach_the_renderer(self):
        scene = models3d.validate_scene({
            "objects": [{"mesh": "box", "width": float("nan"), "height": float("inf"),
                         "depth": float("-inf"), "position": [float("nan"), 0, 0]}],
        })
        obj = scene["objects"][0]
        assert obj["width"] == 1.0 and obj["height"] == 1.0 and obj["depth"] == 1.0
        assert obj["position"][0] == 0.0
        json.loads(json.dumps(scene))  # would raise on a non-finite value

    def test_a_cylinder_without_a_top_radius_stays_a_cylinder(self):
        obj = models3d.validate_scene({"objects": [{"mesh": "cylinder", "radius": 0.5}]})["objects"][0]
        assert obj["radiusTop"] == obj["radius"]

    def test_a_cylinder_with_a_top_radius_is_a_truncated_cone(self):
        obj = models3d.validate_scene({"objects": [{"mesh": "cylinder", "radius": 0.5, "radiusTop": 0.15}]})["objects"][0]
        assert obj["radiusTop"] == 0.15

    def test_object_and_label_counts_are_capped(self):
        scene = models3d.validate_scene({
            "objects": [{"mesh": "box"}] * (models3d.MAX_OBJECTS + 50),
            "labels": [{"text": "x", "at": [0, 0, 0]}] * (models3d.MAX_LABELS + 50),
        })
        assert len(scene["objects"]) == models3d.MAX_OBJECTS
        assert len(scene["labels"]) == models3d.MAX_LABELS

    def test_a_polyline_needs_at_least_two_points_to_be_a_line(self):
        assert models3d.validate_scene({"objects": [{"mesh": "line", "points": [[0, 0, 0]]}]}) is None
        assert models3d.validate_scene({"objects": [{"mesh": "tube", "points": [[0, 0, 0]]}]}) is None
        assert models3d.validate_scene({"objects": [{"mesh": "line", "points": [[0, 0, 0], [1, 1, 1]]}]})

    def test_scene_json_returns_none_for_garbage(self):
        assert models3d.scene_json("nope") is None
        assert models3d.scene_json({"objects": []}) is None


# ---------------------------------------------------------------------------
# The shipped content
# ---------------------------------------------------------------------------

class TestSeededScenes:
    def test_there_is_a_model_for_every_topic(self, seeded):
        slugs = {row["slug"] for row in db.query("SELECT slug FROM topics")}
        assert slugs, "no topics were seeded"
        assert not slugs - set(content.MODELS_3D), "topics with no 3D model"
        assert not set(content.MODELS_3D) - slugs, "models pointing at no topic"

    def test_every_scene_validates(self):
        for slug, entry in content.MODELS_3D.items():
            assert models3d.validate_scene(entry["scene"]), f"{slug} did not validate"

    def test_validation_drops_nothing_from_a_seeded_scene(self):
        """The regression test for the silently-dropped streamlines.

        Nothing here re-implements the validator: it compares the object count
        that went in with the object count that came out, and names the first
        object that vanished if they differ.
        """
        for slug, entry in content.MODELS_3D.items():
            raw = entry["scene"]["objects"]
            kept = models3d.validate_scene(entry["scene"])["objects"]
            assert len(kept) == len(raw), (
                f"{slug}: {len(raw) - len(kept)} object(s) were silently dropped by "
                f"validate_scene; the first offender is {raw[len(kept)]!r}"
            )

    def test_every_object_uses_a_mesh_the_renderer_can_draw(self):
        js_kinds = js_builder_kinds()
        for slug, entry in content.MODELS_3D.items():
            for obj in entry["scene"]["objects"]:
                assert isinstance(obj, dict), f"{slug}: {obj!r} is not an object"
                assert obj.get("mesh") in js_kinds, f"{slug}: unknown mesh {obj.get('mesh')!r}"

    def test_no_scene_exceeds_the_renderer_or_wire_limits(self):
        for slug, entry in content.MODELS_3D.items():
            encoded = models3d.scene_json(entry["scene"])
            assert len(encoded) <= models3d.MAX_SCENE_BYTES, f"{slug} is too large to serve"
            assert len(entry["scene"]["objects"]) <= models3d.MAX_OBJECTS, f"{slug} has too many objects"

    def test_every_model_has_a_title_and_a_caption_that_teaches_something(self):
        for slug, entry in content.MODELS_3D.items():
            assert len(entry["title"]) >= 8, f"{slug} has no real title"
            # A caption that does not mention the mechanism is decoration.
            assert len(entry["caption"]) >= 120, f"{slug} caption is too thin to explain the model"

    def test_no_scene_depends_on_the_auto_spin_to_be_legible(self):
        for slug, entry in content.MODELS_3D.items():
            camera = entry["scene"]["camera"]
            assert 0.8 <= camera["distance"] <= 200, f"{slug} camera distance is out of range"


# ---------------------------------------------------------------------------
# Serving it
# ---------------------------------------------------------------------------

class TestCatalogAndPage:
    def test_models_for_topic_returns_a_renderable_scene(self, seeded):
        topic = db.query_one("SELECT id FROM topics WHERE slug = 'transformers'")
        rows = catalog.models_for_topic(topic["id"])
        assert rows, "the transformers topic has no 3D model"
        scene = json.loads(rows[0]["scene_json"])
        assert any(o["mesh"] == "helix" for o in scene["objects"]), "the windings are missing"

    def test_an_unknown_topic_has_no_models(self, seeded):
        assert catalog.models_for_topic("no-such-topic") == []

    def test_a_corrupted_row_is_dropped_rather_than_rendered(self, seeded):
        topic = db.query_one("SELECT id FROM topics WHERE slug = 'arrays'")
        model_id = db.query_one("SELECT id FROM models_3d WHERE topic_id = ?", topic["id"])["id"]
        original = db.query_one("SELECT scene FROM models_3d WHERE id = ?", model_id)["scene"]
        try:
            db.execute("UPDATE models_3d SET scene = ? WHERE id = ?", '{"objects":[{"mesh":"nope"}]}', model_id)
            assert catalog.models_for_topic(topic["id"]) == []
            db.execute("UPDATE models_3d SET scene = ? WHERE id = ?", "not json at all", model_id)
            assert catalog.models_for_topic(topic["id"]) == []
        finally:
            db.execute("UPDATE models_3d SET scene = ? WHERE id = ?", original, model_id)
        assert len(catalog.models_for_topic(topic["id"])) == 1

    def test_the_topic_page_carries_the_model_and_the_renderer(self, client):
        page = client.get("/topics/hash-tables")
        assert page.status_code == 200
        assert "data-model3d" in page.text
        assert "/static/js/engine3d.js" in page.text

        match = re.search(r'data-scene="([^"]*)"', page.text)
        assert match, "the scene attribute is missing"
        scene = json.loads(html.unescape(match.group(1)))
        assert scene["objects"], "an empty scene reached the page"
        assert scene["labels"], "an unlabelled model is hard to read"

    def test_the_canvas_is_reachable_without_javascript_too(self, client):
        """The caption carries the lesson; the canvas is an addition."""
        page = client.get("/topics/hash-tables")
        assert "collision" in page.text.lower()
        assert "<canvas" in page.text
        assert 'role="img"' in page.text

    def test_the_renderer_script_is_served(self, client):
        res = client.get("/static/js/engine3d.js")
        assert res.status_code == 200
        assert res.headers["content-type"].startswith("text/javascript")
        assert "EngineVerse3D" in res.text

    def test_the_service_worker_precaches_the_renderer(self):
        sw = (ROOT / "backend" / "static" / "sw.js").read_text()
        assert '"/static/js/engine3d.js"' in sw, "an offline visit would get a blank model"
