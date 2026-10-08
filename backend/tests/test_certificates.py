"""Tiered certificates and the diagram corpus.

Two sets of guarantees that both come from the same failure mode: something
that looks present but is not. A certificate must never be issued without the
measured work behind it, and a topic must never render notes with no diagram
while the seed reports success.
"""

from __future__ import annotations

import json
import xml.etree.ElementTree as ET

import pytest

from engineverse import certificates as certs
from engineverse import db, diagrams as D, progress
from seed_data import diagrams_data

SUBJECT_SLUG = "data-structures-algorithms"


def _csrf(html: str) -> str:
    """The token the app embeds in every form; JSON POSTs send it as a header."""
    marker = 'name="csrf_token" value="'
    start = html.index(marker) + len(marker)
    return html[start : html.index('"', start)]


@pytest.fixture()
def subject(seeded):
    row = db.query_one("SELECT id, name FROM subjects WHERE slug = ?", SUBJECT_SLUG)
    assert row, f"seed has no subject {SUBJECT_SLUG}"
    return row


@pytest.fixture()
def learner(seeded, subject):
    """A learner with every topic in the subject completed and a clean slate."""
    user = db.query_one("SELECT id FROM users WHERE username = 'asha'")  # matches signed_in
    db.execute("DELETE FROM certificates WHERE user_id = ?", user["id"])
    topic_ids = [r["id"] for r in db.query("SELECT id FROM topics WHERE subject_id = ?", subject["id"])]
    db.execute("DELETE FROM user_progress WHERE user_id = ?", user["id"])
    # Reset the inputs the tiers read, or state from an earlier test decides the
    # tier this one asserts on.
    db.execute("DELETE FROM streaks WHERE user_id = ?", user["id"])
    db.execute("DELETE FROM submissions WHERE user_id = ?", user["id"])
    for topic_id in topic_ids:
        progress.complete_topic(user["id"], topic_id)
    return user


def _set_streak(user_id: str, days: int) -> None:
    db.execute(
        "INSERT INTO streaks (user_id,current_streak,longest_streak,total_xp,level) VALUES (?,?,?,?,1) "
        "ON CONFLICT(user_id) DO UPDATE SET longest_streak = excluded.longest_streak",
        user_id, min(days, 999), days, 0,
    )


def _set_accuracy(user_id: str, pct: int, total: int = 40) -> None:
    """Rewrites the learner's submissions so the reported accuracy is `pct`."""
    db.execute("DELETE FROM submissions WHERE user_id = ?", user_id)
    question = db.query_one("SELECT id FROM questions LIMIT 1")
    if not question:
        return
    correct = round(total * pct / 100)
    for index in range(total):
        db.execute(
            "INSERT INTO submissions (id,user_id,question_id,answer_index,is_correct,created_at) "
            "VALUES (?,?,?,?,?,?)",
            f"sub-test-{index}", user_id, question["id"], 0, 1 if index < correct else 0, index,
        )


# ---------------------------------------------------------------------------
# Tier logic
# ---------------------------------------------------------------------------

def test_tiers_are_ordered_and_unique():
    """The order is what makes the upgrade path a single comparison."""
    names = [tier["name"] for tier in certs.TIERS]
    assert names == ["bronze", "silver", "gold", "platinum"]
    assert len(set(names)) == len(names)
    for tier in certs.TIERS:
        assert tier["label"] and tier["summary"] and tier["requirements"]


def test_each_tier_demands_more_than_the_one_below():
    """If a higher tier were weaker, it could be reached while a lower one is not."""
    for lower, higher in zip(certs.TIERS, certs.TIERS[1:]):
        assert set(lower["requirements"]) <= set(higher["requirements"]), (
            f"{higher['name']} drops a requirement that {lower['name']} has"
        )
        for key, value in lower["requirements"].items():
            assert higher["requirements"][key] >= value, (
                f"{higher['name']} relaxes {key} below {lower['name']}"
            )


def test_no_certificate_without_full_completion(learner, subject):
    """The base requirement is finishing the subject, so partial work earns nothing."""
    db.execute(
        "DELETE FROM user_progress WHERE user_id = ? AND topic_id = (SELECT id FROM topics WHERE subject_id = ? LIMIT 1)",
        learner["id"], subject["id"],
    )
    assert certs.evaluate(learner["id"], subject["id"]) is None


def test_completion_alone_earns_bronze(learner, subject):
    _set_streak(learner["id"], 0)
    result = certs.evaluate(learner["id"], subject["id"])
    assert result is not None
    assert result[0]["name"] == "bronze"


def test_streak_upgrades_bronze_to_silver(learner, subject):
    _set_streak(learner["id"], 14)
    assert certs.evaluate(learner["id"], subject["id"])[0]["name"] == "silver"


def test_accuracy_is_required_for_gold(learner, subject):
    _set_streak(learner["id"], 20)
    _set_accuracy(learner["id"], 60)
    assert certs.evaluate(learner["id"], subject["id"])[0]["name"] == "silver"
    _set_accuracy(learner["id"], 90)
    assert certs.evaluate(learner["id"], subject["id"])[0]["name"] == "gold"


def test_platinum_needs_both_a_long_streak_and_mastery(learner, subject):
    _set_streak(learner["id"], 30)
    _set_accuracy(learner["id"], 95)
    # Mastery comes from the seed's completed topics; whatever it is, gold must
    # still be reachable, so assert the boundary rather than an exact tier.
    earned = certs.evaluate(learner["id"], subject["id"])[0]["name"]
    assert earned in ("gold", "platinum")
    numbers = certs.evidence(learner["id"], subject["id"])
    if numbers["mastery_pct"] >= 90:
        assert earned == "platinum"
    else:
        assert earned == "gold"


def test_completing_the_last_topic_issues_automatically(seeded, subject):
    """The hook lives in complete_topic, so earning is not a separate step."""
    user = db.query_one("SELECT id FROM users WHERE username = 'ravi'")
    db.execute("DELETE FROM certificates WHERE user_id = ?", user["id"])
    db.execute("DELETE FROM user_progress WHERE user_id = ?", user["id"])
    # This test is about the automatic hook, not about tiering, so pin the one
    # input that decides the tier. It used to pass on whatever streak the seed
    # happened to leave behind - and broke the moment the seeded history got
    # deep enough to earn silver on its own.
    _set_streak(user["id"], 0)
    topic_ids = [r["id"] for r in db.query("SELECT id FROM topics WHERE subject_id = ?", subject["id"])]
    for topic_id in topic_ids[:-1]:
        progress.complete_topic(user["id"], topic_id)
    assert db.query_one("SELECT id FROM certificates WHERE user_id = ?", user["id"]) is None
    progress.complete_topic(user["id"], topic_ids[-1])
    row = db.query_one("SELECT * FROM certificates WHERE user_id = ?", user["id"])
    assert row is not None, "completing the last topic did not issue a certificate"
    assert row["tier"] == "bronze"


def test_improving_upgrades_in_place_rather_than_duplicating(learner, subject):
    """One subject, one certificate. A second row would let one completion count twice."""
    first = certs.issue_for_subject(learner["id"], subject["id"])
    assert first["tier"] == "bronze"
    _set_streak(learner["id"], 20)
    second = certs.issue_for_subject(learner["id"], subject["id"])
    assert second["id"] == first["id"]
    assert second["tier"] == "silver"
    count = db.query_one(
        "SELECT count(*) AS n FROM certificates WHERE user_id = ? AND entity_type = 'subject'", learner["id"]
    )["n"]
    assert count == 1, f"{count} certificates for one subject"


def test_a_lower_tier_never_downgrades(learner, subject):
    first = certs.issue_for_subject(learner["id"], subject["id"])
    _set_streak(learner["id"], 20)
    certs.issue_for_subject(learner["id"], subject["id"])
    _set_streak(learner["id"], 0)          # streak lapsed
    again = certs.issue_for_subject(learner["id"], subject["id"])
    assert again["id"] == first["id"]
    assert again["tier"] == "silver", "an earned tier was taken away"


def test_verify_id_is_unguessable_and_unique(learner, subject):
    certs.issue_for_subject(learner["id"], subject["id"])
    row = db.query_one("SELECT verify_id FROM certificates WHERE user_id = ?", learner["id"])
    assert row["verify_id"].startswith("EV-")
    # A verify id is public, so it must not be derivable from the timestamp alone.
    suffix = row["verify_id"].rsplit("-", 1)[-1]
    assert len(suffix) >= 8
    others = db.query("SELECT verify_id FROM certificates")
    assert len({r["verify_id"] for r in others}) == len(others)


# ---------------------------------------------------------------------------
# The public page
# ---------------------------------------------------------------------------

def test_certificate_page_shows_tier_issuer_and_disclaimer(client, learner, subject):
    row = certs.issue_for_subject(learner["id"], subject["id"])
    page = client.get(f"/certificates/{row['verify_id']}")
    assert page.status_code == 200
    body = page.text
    assert "Bronze" in body
    assert certs.issuer_name() in body
    assert row["verify_id"] in body
    assert "cert-bronze" in body
    # The accreditation disclaimer must survive on the page itself, not only in
    # the stored meta, because the certificate gets screenshotted and shared.
    assert "not a university" in body.lower()


def test_unknown_verify_id_is_404(client, seeded):
    assert client.get("/certificates/EV-DOES-NOT-EXIST").status_code == 404


def test_issuer_is_configurable(seeded):
    """The name is branding, so it must be changeable without editing code."""
    before = certs.issuer_name()
    try:
        from engineverse import brand

        brand.set_many({"certificate_issuer": "Test Issuer"})
        assert certs.issuer_name() == "Test Issuer"
    finally:
        brand.set_many({"certificate_issuer": before})
        assert certs.issuer_name() == before


def test_refresh_endpoint_returns_the_current_set(signed_in, learner, subject):
    token = _csrf(signed_in.get("/dashboard").text)
    response = signed_in.post(
        "/api/certificates/refresh", json={}, headers={"x-csrf-token": token}
    )
    assert response.status_code == 200, response.text
    assert "certificates" in response.json()


def test_certificate_list_exposes_the_tier(signed_in, learner, subject):
    certs.issue_for_subject(learner["id"], subject["id"])
    response = signed_in.get("/api/certificates")
    assert response.status_code == 200
    rows = response.json()["certificates"]
    assert rows and all("tier" in r and "tier_label" in r for r in rows)


# ---------------------------------------------------------------------------
# Diagrams
# ---------------------------------------------------------------------------

def test_every_topic_has_a_diagram(seeded):
    """The regression test: 6 of 48 topics had one, and the rest rendered none."""
    missing = db.query(
        "SELECT t.slug FROM topics t WHERE NOT EXISTS "
        "(SELECT 1 FROM diagrams d WHERE d.topic_id = t.id) ORDER BY t.slug"
    )
    assert [r["slug"] for r in missing] == [], "topics with no diagram"


def test_every_diagram_is_authored_for_a_real_topic(seeded):
    orphans = db.query(
        "SELECT count(*) AS n FROM diagrams d WHERE NOT EXISTS "
        "(SELECT 1 FROM topics t WHERE t.id = d.topic_id)"
    )[0]["n"]
    assert orphans == 0


def test_every_stored_diagram_is_well_formed_and_inert(seeded):
    """Each stored spec must parse as XML and carry nothing executable."""
    rows = db.query("SELECT id, spec, hotspots FROM diagrams")
    assert len(rows) >= 48
    for row in rows:
        root = ET.fromstring(row["spec"])          # raises if malformed
        for element in root.iter():
            tag = element.tag.split("}")[-1]
            assert "script" not in tag.lower(), f"{row['id']} contains a script element"
            for attr in element.attrib:
                assert not attr.lower().startswith("on"), f"{row['id']} has an on* attribute"
            assert "javascript:" not in (element.text or "").lower()
        spots = json.loads(row["hotspots"])
        assert spots, f"{row['id']} has no hotspots, so nothing on it is explorable"
        for spot in spots:
            assert spot["label"] and spot["explain"], f"{row['id']} has an empty hotspot"


def test_no_diagram_declares_an_id(seeded):
    """Two SVGs on one page sharing an id resolve to whichever came first.

    The arrowheads are drawn as geometry for exactly this reason.
    """
    for row in db.query("SELECT id, spec FROM diagrams"):
        assert "id=" not in row["spec"], f"{row['id']} declares an id attribute"
        assert "<marker" not in row["spec"], f"{row['id']} uses a marker reference"


def test_diagram_module_and_seeder_agree(seeded):
    """If the seeder dropped a diagram the counts would diverge."""
    stored = db.query_one("SELECT count(*) AS n FROM diagrams")["n"]
    assert stored == len(diagrams_data.all_slugs())


@pytest.mark.parametrize("slug", sorted(diagrams_data.all_slugs()))
def test_each_scene_validates_and_keeps_every_primitive(slug):
    """A validator that silently drops a primitive is worse than no validator."""
    scene = diagrams_data.build(slug)
    validated = D.validate_scene(scene)
    assert len(validated["objects"]) == len(scene["objects"]), f"{slug} lost objects"
    assert validated["title"] and validated["caption"] and validated["label"]
    svg = D.render_svg(validated)
    assert svg.startswith("<svg") and svg.endswith("</svg>")
    assert len(svg) < D.MAX_SVG_BYTES


def test_unknown_diagram_kind_raises():
    with pytest.raises(ValueError):
        D.validate_scene({"objects": [{"kind": "not-a-shape"}]})


def test_diagram_text_cannot_carry_markup():
    svg = D.render_svg(D.validate_scene({
        "objects": [{"kind": "text", "x": 1, "y": 1, "text": "</text><script>alert(1)</script>"}],
    }))
    root = ET.fromstring(svg)
    assert "<script" not in svg.lower()
    assert all("script" not in el.tag.lower() for el in root.iter())


def test_build_names_the_missing_topic(seeded):
    """The seeder relies on this raising, not returning None."""
    with pytest.raises(KeyError) as error:
        diagrams_data.build("this-topic-does-not-exist")
    assert "this-topic-does-not-exist" in str(error.value)
