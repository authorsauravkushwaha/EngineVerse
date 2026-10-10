"""3D models, keyed by topic slug.

Each entry is a *model*, not a picture: geometry that carries the idea the
notes are making, plus a caption that says what to look at. They are stored in
the `models_3d` table and rendered by `backend/static/js/engine3d.js`, so a new
one is an INSERT rather than a deploy.

Everything here is built from the helpers in `engineverse.models3d`, which
means every scene passes through `validate_scene()` on its way in and on its
way out — there is no markup in a scene, only numbers and hex colours.

Conventions used throughout:
  * +X is "along", +Y is "up", +Z is "toward the reader".
  * `arrow(a, b)` puts the tip at `b`, so a force arrow is drawn start → tip.
  * Wireframe boxes (`wire_box`) mark a *volume*; solid boxes mark a *thing*.
"""

from __future__ import annotations

import math

from engineverse.models3d import (
    ACCENT, BAD, DIM, GOOD, INK, NEUTRAL, WARM,
    arrow, box, chain, cylinder, edge, grid, helix, label, lattice_points,
    pipe, scene, sphere, tree_edges, binary_tree_layout, wire_box,
)

# ---------------------------------------------------------------------------
# Small helpers shared by several models
# ---------------------------------------------------------------------------


def ring(position, radius, *, color=ACCENT, tube=0.03, axis="y", opacity=1.0) -> dict:
    """A circular field line / pipe cross-section lying in the XZ plane."""
    node = {"mesh": "torus", "radius": round(radius, 6), "tube": round(tube, 6),
            "position": [round(v, 6) for v in position], "color": color}
    if axis == "x":
        node["rotation"] = [0.0, 0.0, 90.0]
    if opacity < 1.0:
        node["opacity"] = round(opacity, 6)
    return node


def arc_points(radius, start_deg, end_deg, steps=24, *, plane="xy") -> list[list[float]]:
    pts = []
    for i in range(steps + 1):
        a = math.radians(start_deg + (end_deg - start_deg) * i / steps)
        if plane == "xy":
            pts.append([radius * math.cos(a), radius * math.sin(a), 0.0])
        else:
            pts.append([radius * math.cos(a), 0.0, radius * math.sin(a)])
    return pts


def profile_duct(radius_at, *, x0=-2.7, x1=2.7, step=0.6, color=ACCENT, opacity=0.28) -> list[dict]:
    """A duct of varying radius, built from short cylinders laid along +X."""
    out = []
    n = int(round((x1 - x0) / step))
    for i in range(n):
        centre = x0 + step * (i + 0.5)
        out.append(cylinder((centre, 0, 0), radius=radius_at(centre), height=step,
                            color=color, rotation=(0, 0, 90), opacity=opacity))
    return out


def slabs(count, *, size=(2.6, 0.22, 1.5), gap=0.34, colour_at=None, start=0.0) -> list[dict]:
    """A stack of horizontal slabs — protocol layers, soil strata, memory tiers."""
    out = []
    for i in range(count):
        y = start + i * (size[1] + gap)
        out.append(box((0, y, 0), size=size, color=(colour_at(i) if colour_at else ACCENT)))
    return out


# ---------------------------------------------------------------------------
# The models
# ---------------------------------------------------------------------------

MODELS_3D: dict[str, dict] = {

    # ---------------------------------------------------------------- core --

    "stress-strain-hookes-law": {
        "title": "A tensile specimen under load",
        "caption": (
            "Equal and opposite forces F pull on the grips. Inside the gauge length L₀ the "
            "stress is σ = F/A and the strain is ε = ΔL/L₀; Hooke's law says σ = Eε, so while "
            "the material stays elastic, doubling F doubles the stretch and removing the load "
            "returns the specimen to its original length. The green cage is the original "
            "length — everything outside it is permanent once the yield point is passed."
        ),
        "scene": scene([
            grid(7, 7, position=(0, -1.05, 0)),
            cylinder((0, 0, 0), radius=0.22, height=1.5, color=ACCENT, rotation=(0, 0, 90)),
            box((-1.15, 0, 0), size=(0.55, 0.62, 0.62), color=DIM),
            box((1.15, 0, 0), size=(0.55, 0.62, 0.62), color=DIM),
            arrow((-1.5, 0, 0), (-2.4, 0, 0), color=WARM, shaft=0.05, head=0.3, radius=0.11),
            arrow((1.5, 0, 0), (2.4, 0, 0), color=WARM, shaft=0.05, head=0.3, radius=0.11),
            *wire_box((0, 0, 0), (1.5, 0.52, 0.52), color=GOOD),
        ], labels=[label("F", (-2.8, 0.3, 0)), label("F", (2.8, 0.3, 0)),
                   label("gauge length L₀", (0, 0.62, 0))],
            distance=6.8, pitch=13, yaw=28),
    },

    "equilibrium-of-forces-free-body-diagrams": {
        "title": "A body in three-dimensional equilibrium",
        "caption": (
            "Three forces act through one point. F₁ + F₂ + W = 0, so ΣF = 0 in x, y *and* z "
            "at once and the body does not accelerate — this is the condition a free body "
            "diagram exists to check. On the right the same three vectors are placed head to "
            "tail: they close into a triangle, and a closed polygon is the geometric statement "
            "of equilibrium."
        ),
        "scene": scene([
            grid(6, 6, position=(0, -1.7, 0)),
            box((0, 0, 0), size=(0.8, 0.8, 0.8), color=NEUTRAL, opacity=0.9),
            arrow((0, 0, 0), (2.0, 0.8, 0.0), color=ACCENT),
            arrow((0, 0, 0), (-1.4, 1.2, 0.6), color=GOOD),
            arrow((0, 0, 0), (-0.6, -2.0, -0.6), color=BAD),
            chain([(3.4, 1.6, 0.0), (5.4, 2.4, 0.0), (4.0, 3.6, 0.6), (3.4, 1.6, 0.0)], color=WARM),
        ], labels=[label("F₁", (2.35, 1.05, 0)), label("F₂", (-1.75, 1.45, 0.6)),
                   label("W", (-0.75, -2.35, -0.6)), label("closed ⇒ ΣF = 0", (4.4, 4.0, 0.3))],
            distance=9.5, yaw=30, pitch=12, target=(1.2, 0.7, 0)),
    },

    "bernoullis-equation": {
        "title": "A Venturi: faster in the throat, lower pressure",
        "caption": (
            "The same mass flow has to squeeze through the narrow throat, so continuity forces "
            "the fluid to speed up there (the long blue arrow). Bernoulli then trades that "
            "kinetic energy for pressure: the orange arrows show the pressure is *lower* in "
            "the throat than at the inlet. Measuring that pressure difference is exactly how a "
            "Venturi meter reads flow rate."
        ),
        "scene": scene([
            *profile_duct(lambda x: 0.28 + 0.52 * min(1.0, abs(x) / 1.5)),
            pipe([(-2.7, 0.42 * 0.55, 0.0), (-1.5, 0.30, 0.0), (-0.6, 0.15, 0.0), (0.0, 0.12, 0.0),
                  (0.6, 0.15, 0.0), (1.5, 0.30, 0.0), (2.7, 0.42 * 0.55, 0.0)], color=ACCENT, radius=0.02),
            pipe([(-2.7, -0.42 * 0.55, 0.0), (-1.5, -0.30, 0.0), (-0.6, -0.15, 0.0), (0.0, -0.12, 0.0),
                  (0.6, -0.15, 0.0), (1.5, -0.30, 0.0), (2.7, -0.42 * 0.55, 0.0)], color=ACCENT, radius=0.02),
            arrow((-2.4, 1.0, 0.0), (-1.7, 1.0, 0.0), color=INK, shaft=0.03, head=0.2, radius=0.07),
            arrow((0.0, 0.85, 0.0), (1.25, 0.85, 0.0), color=INK, shaft=0.035, head=0.24, radius=0.08),
            arrow((-2.4, -0.95, 0.0), (-2.4, -1.55, 0.0), color=WARM, shaft=0.03, head=0.2, radius=0.07),
            arrow((0.0, -0.75, 0.0), (0.0, -1.05, 0.0), color=WARM, shaft=0.03, head=0.2, radius=0.07),
        ], labels=[label("inlet: v₁ low, p₁ high", (-2.3, 1.35, 0)),
                   label("throat: v₂ high, p₂ low", (0.35, 1.2, 0))],
            distance=7.5, pitch=12, yaw=22),
    },

    "fluid-statics-manometry": {
        "title": "A U-tube manometer",
        "caption": (
            "The two legs hold the same liquid, so at any level the pressure must be equal. "
            "Apply that at the dashed datum and the unknown pressure on the left balances the "
            "atmosphere plus the extra column ρgh on the right. A manometer measures pressure "
            "with nothing but a height difference and a density."
        ),
        "scene": scene([
            grid(6, 6, position=(0, -1.6, 0)),
            cylinder((-1.1, 0.0, 0), radius=0.28, height=2.6, color=INK, opacity=0.22),
            cylinder((1.1, 0.0, 0), radius=0.28, height=2.6, color=INK, opacity=0.22),
            cylinder((0, -1.25, 0), radius=0.26, height=2.2, color=INK, opacity=0.22, rotation=(0, 0, 90)),
            cylinder((-1.1, -0.55, 0), radius=0.24, height=1.9, color=ACCENT, opacity=0.85),
            cylinder((1.1, -0.15, 0), radius=0.24, height=1.1, color=ACCENT, opacity=0.85),
            cylinder((0, -1.25, 0), radius=0.23, height=2.2, color=ACCENT, opacity=0.85, rotation=(0, 0, 90)),
            chain([(-1.8, 0.4, 0), (1.8, 0.4, 0)], color=GOOD),
            arrow((-1.1, 1.5, 0), (-1.1, 0.75, 0), color=WARM, shaft=0.035, head=0.24, radius=0.09),
            arrow((1.1, 1.9, 0), (1.1, 1.15, 0), color=NEUTRAL, shaft=0.03, head=0.2, radius=0.07),
        ], labels=[label("p (unknown)", (-1.1, 1.75, 0)), label("p_atm", (1.1, 2.15, 0)),
                   label("datum — equal pressure both sides", (0, 0.62, 0)),
                   label("h", (1.75, 0.05, 0))],
            distance=6.8, pitch=12),
    },

    "first-law-energy-balance": {
        "title": "A closed system: Q in, W out, ΔU stored",
        "caption": (
            "Heat Q crosses the boundary into the gas; the gas pushes the piston up and does "
            "work W on the surroundings. The first law, ΔU = Q − W, is a balance sheet: what "
            "comes in either leaves as work or stays behind as internal energy (which for an "
            "ideal gas shows up as temperature). Nothing is created or destroyed."
        ),
        "scene": scene([
            grid(5, 5, position=(0, -1.5, 0)),
            cylinder((0, -0.15, 0), radius=0.75, height=2.0, color=INK, opacity=0.2),
            cylinder((0, -0.55, 0), radius=0.68, height=1.2, color=WARM, opacity=0.4),
            cylinder((0, 0.62, 0), radius=0.7, height=0.22, color=NEUTRAL),
            arrow((-1.9, -0.55, 0), (-0.95, -0.55, 0), color=BAD, shaft=0.05, head=0.28, radius=0.1),
            arrow((0, 0.85, 0), (0, 1.75, 0), color=GOOD, shaft=0.05, head=0.28, radius=0.1),
            arrow((0.95, -0.55, 0), (1.55, -0.55, 0), color=ACCENT, shaft=0.03, head=0.2, radius=0.07),
        ], labels=[label("Q in", (-2.15, -0.3, 0)), label("W out (piston rises)", (0.1, 1.95, 0)),
                   label("ΔU stays in the gas", (1.7, -0.3, 0))],
            distance=6.2, pitch=14),
    },

    "material-energy-balances": {
        "title": "A process unit: mass in, mass out, nothing created",
        "caption": (
            "Two feed streams enter, two product streams leave, and at steady state the total "
            "mass in must equal the total mass out — that single sentence is the material "
            "balance, and per species it becomes one equation each. Heat and shaft work cross "
            "the boundary without carrying mass, so they appear in the energy balance only. "
            "Draw the boundary first; everything else follows from what crosses it."
        ),
        "scene": scene([
            grid(7, 7, position=(0, -1.4, 0)),
            box((0, 0, 0), size=(1.9, 1.6, 1.4), color=DIM, opacity=0.35),
            *wire_box((0, 0, 0), (1.9, 1.6, 1.4), color=INK),
            pipe([(-2.6, 0.5, 0.4), (-0.95, 0.5, 0.4)], color=ACCENT, radius=0.07),
            pipe([(-2.6, -0.4, -0.4), (-0.95, -0.4, -0.4)], color=GOOD, radius=0.07),
            pipe([(0.95, 0.5, 0.0), (2.6, 0.5, 0.0)], color=WARM, radius=0.07),
            pipe([(0.95, -0.5, 0.0), (2.6, -0.5, 0.0)], color=BAD, radius=0.07),
            arrow((0, 1.0, 0), (0, 1.8, 0), color=NEUTRAL, shaft=0.04, head=0.24, radius=0.09),
            arrow((0, -1.0, 0), (0, -1.7, 0), color=NEUTRAL, shaft=0.04, head=0.24, radius=0.09),
        ], labels=[label("F₁", (-2.85, 0.75, 0.4)), label("F₂", (-2.85, -0.15, -0.4)),
                   label("P₁", (2.85, 0.75, 0.0)), label("P₂", (2.85, -0.25, 0.0)),
                   label("Q out", (0, 2.0, 0)), label("W in", (0, -1.95, 0)),
                   label("Σm_in = Σm_out", (0, -0.45, 1.1))],
            distance=7.6, pitch=15, yaw=30, spin=0.15),
    },

    "entropy-the-second-law": {
        "title": "Heat only flows downhill — and that is the second law",
        "caption": (
            "Q_H leaves the hot reservoir, part of it becomes work W, and the rest Q_C must be "
            "rejected to the cold reservoir. The thin red arrow shows the one thing the second "
            "law forbids: heat moving by itself from cold to hot. Every real engine pays that "
            "tax, which is why no engine can be 100% efficient and why entropy always rises."
        ),
        "scene": scene([
            grid(7, 7, position=(0, -1.9, 0)),
            box((-1.9, 0.7, 0), size=(1.25, 1.25, 1.25), color=BAD, opacity=0.55),
            box((1.9, -0.7, 0), size=(1.25, 1.25, 1.25), color=ACCENT, opacity=0.55),
            cylinder((0, 0.0, 0), radius=0.55, height=0.9, color=NEUTRAL),
            arrow((-1.2, 0.7, 0), (-0.6, 0.35, 0), color=WARM, shaft=0.05, head=0.26, radius=0.1),
            arrow((0.6, -0.35, 0), (1.25, -0.7, 0), color=INK, shaft=0.05, head=0.26, radius=0.1),
            arrow((0, -0.5, 0), (0, -1.4, 0), color=GOOD, shaft=0.05, head=0.26, radius=0.1),
            arrow((1.4, -1.35, 0.0), (-1.4, 1.35, 0.0), color=BAD, shaft=0.012, head=0.16, radius=0.05),
        ], labels=[label("hot reservoir T_H", (-1.9, 1.55, 0)), label("cold reservoir T_C", (1.9, 0.15, 0)),
                   label("engine", (0, 0.75, 0)), label("W out", (0, -1.65, 0)),
                   label("forbidden by the 2nd law", (0, 0.0, 0.9))],
            distance=7.6, pitch=13),
    },

    "concrete-mix-design-workability": {
        "title": "The slump cone — workability measured in millimetres",
        "caption": (
            "Fresh concrete is packed into a truncated mould 300 mm high, 200 mm across the "
            "bottom and 100 mm across the top. Lift the mould and the concrete slumps. The "
            "drop in height is the slump: near zero means harsh and unworkable, 200 mm means "
            "segregating. Most structural work sits between 50 and 100 mm."
        ),
        "scene": scene([
            grid(6, 6, position=(0, -0.02, 0)),
            cylinder((0, 0.375, 0), radius=0.5, radius_top=0.25, height=0.75, color=DIM, opacity=0.22),
            cylinder((0, 0.22, 0), radius=0.72, radius_top=0.24, height=0.44, color=NEUTRAL, opacity=0.95),
            arrow((0.9, 0.75, 0), (0.9, 0.44, 0), color=WARM, shaft=0.02, head=0.12, radius=0.05),
            chain([(0.9, 0.75, 0), (0.9, 0.44, 0)], color=WARM),
        ], labels=[label("mould (300 mm)", (-0.95, 0.85, 0)),
                   label("slump = drop in height", (1.05, 0.62, 0)),
                   label("slumped concrete", (0, -0.28, 0))],
            distance=4.6, pitch=14, yaw=32),
    },

    "effective-stress-bearing-capacity": {
        "title": "A footing on layered soil",
        "caption": (
            "The column load spreads through the footing into the strata. Total stress σ grows "
            "with depth as γz, but pore water carries part of it, so the stress the soil "
            "skeleton actually feels is the effective stress σ′ = σ − u — and only σ′ gives "
            "strength and settlement. The red lines are the failure surface Terzaghi's bearing "
            "capacity equations are built on."
        ),
        "scene": scene([
            box((0, 0.05, 0), size=(4.4, 0.7, 4.4), color="#8a6a3f", opacity=0.55),
            box((0, -0.65, 0), size=(4.4, 0.7, 4.4), color="#6d5330", opacity=0.55),
            box((0, -1.35, 0), size=(4.4, 0.7, 4.4), color="#4f3d24", opacity=0.55),
            box((0, 0.58, 0), size=(1.7, 0.32, 1.7), color=NEUTRAL),
            box((0, 1.35, 0), size=(0.55, 1.2, 0.55), color=DIM),
            arrow((-0.5, 2.35, 0), (-0.5, 1.7, 0), color=WARM, shaft=0.04, head=0.22, radius=0.09),
            arrow((0.5, 2.35, 0), (0.5, 1.7, 0), color=WARM, shaft=0.04, head=0.22, radius=0.09),
            chain([(-0.85, 0.42, 0.0), (-1.75, -0.95, 0.0), (-0.3, -1.55, 0.0)], color=BAD),
            chain([(0.85, 0.42, 0.0), (1.75, -0.95, 0.0), (0.3, -1.55, 0.0)], color=BAD),
        ], labels=[label("q (applied pressure)", (0, 2.6, 0)), label("footing", (1.15, 0.6, 0)),
                   label("σ′ = σ − u", (-2.2, -0.6, 0.6)), label("failure surface", (1.9, -1.5, 0))],
            distance=8.2, pitch=16, yaw=34),
    },

    # ------------------------------------------------------------ electrical --

    "transformers": {
        "title": "Two windings, one core, one flux",
        "caption": (
            "The primary N₁ carries alternating current and drives a flux Φ around the core. "
            "That same changing flux cuts the secondary N₂, so the voltages are in the turns "
            "ratio: V₂/V₁ = N₂/N₁. Here N₁ = 8 and N₂ = 5, a step-down. With no load the "
            "power in equals the power out, so the secondary current steps *up* by the same "
            "ratio the voltage stepped down."
        ),
        "scene": scene([
            box((0, 0, 0), size=(0.55, 2.2, 0.55), color=DIM),
            box((-1.15, 0, 0), size=(0.45, 2.2, 0.45), color=DIM),
            box((1.15, 0, 0), size=(0.45, 2.2, 0.45), color=DIM),
            box((0, 1.2, 0), size=(2.75, 0.45, 0.45), color=DIM),
            box((0, -1.2, 0), size=(2.75, 0.45, 0.45), color=DIM),
            helix((-1.15, 0, 0), radius=0.45, height=1.7, turns=8, color=WARM, tube=0.05),
            helix((1.15, 0, 0), radius=0.45, height=1.7, turns=5, color=GOOD, tube=0.05),
            arrow((-0.7, 1.2, 0.5), (0.7, 1.2, 0.5), color=ACCENT, shaft=0.03, head=0.22, radius=0.07),
            arrow((0.7, -1.2, 0.5), (-0.7, -1.2, 0.5), color=ACCENT, shaft=0.03, head=0.22, radius=0.07),
            arrow((1.15, 0.55, 0.5), (1.15, -0.55, 0.5), color=ACCENT, shaft=0.03, head=0.22, radius=0.07),
            arrow((-1.15, -0.55, 0.5), (-1.15, 0.55, 0.5), color=ACCENT, shaft=0.03, head=0.22, radius=0.07),
        ], labels=[label("N₁ = 8 (primary)", (-1.15, 1.75, 0)), label("N₂ = 5 (secondary)", (1.15, 1.75, 0)),
                   label("Φ around the core", (0, -1.75, 0.5))],
            distance=6.4, pitch=12, yaw=32),
    },

    "ac-circuits-power-factor": {
        "title": "Phasors and the angle that costs you money",
        "caption": (
            "V and I rotate together at ω; the diagram is a freeze-frame. Only the component "
            "of I in phase with V does real work: P = VI cos φ. The green projection is that "
            "component; the rest sloshes back and forth as reactive power. cos φ = 1 means all "
            "the current is useful — which is why utilities charge for a poor power factor."
        ),
        "scene": scene([
            {"mesh": "plane", "size": 4.6, "rotation": [90.0, 0.0, 0.0], "position": [0.6, 0.6, 0.0],
             "color": DIM, "opacity": 0.18},
            arrow((0, 0, 0), (2.8, 0, 0), color=ACCENT, shaft=0.045, head=0.28, radius=0.1),
            arrow((0, 0, 0), (2.25, 1.5, 0), color=WARM, shaft=0.045, head=0.28, radius=0.1),
            chain([(2.25, 1.5, 0), (2.25, 0.0, 0)], color=GOOD),
            pipe(arc_points(0.85, 0, 33.7, 28), color=NEUTRAL, radius=0.02),
            helix((0, 0, 0), radius=0.85, height=0.7, turns=1, color=DIM, tube=0.015, rotation=(90, 0, 0)),
            arrow((0, 0, 0), (0, -1.1, 0), color=DIM, shaft=0.02, head=0.16, radius=0.05),
            arrow((0, 0, 0), (-1.1, 0, 0), color=DIM, shaft=0.02, head=0.16, radius=0.05),
        ], labels=[label("V", (2.95, 0.2, 0)), label("I (leads)", (2.4, 1.7, 0)),
                   label("I·cos φ → real power", (1.6, -0.35, 0)), label("φ", (1.0, 0.3, 0)),
                   label("rotating at ω", (0, 0, 0.9))],
            distance=6.6, pitch=16, yaw=38, spin=0.0),
    },

    "kirchhoffs-laws": {
        "title": "A circuit as a loop and a node",
        "caption": (
            "KCL: at every node, current in equals current out — the three arrows at the "
            "central node add to zero, because charge cannot pile up. KVL: around any closed "
            "loop the rises and drops cancel — the green loop through the source and both "
            "resistors sums to zero, because the electric field is conservative. Together they "
            "are enough to solve any linear network."
        ),
        "scene": scene([
            grid(6, 6, position=(0, -1.5, 0)),
            pipe([(-1.6, 0.9, 0), (1.6, 0.9, 0), (1.6, -0.9, 0), (-1.6, -0.9, 0), (-1.6, 0.9, 0)],
                 color=DIM, radius=0.04),
            pipe([(0, 0.9, 0), (0, -0.9, 0)], color=DIM, radius=0.04),
            sphere((0, 0.9, 0), 0.12, color=INK),
            box((-1.6, 0.0, 0), size=(0.35, 0.7, 0.35), color=WARM),
            box((0.75, 0.9, 0), size=(0.8, 0.32, 0.32), color=ACCENT),
            box((0.0, -0.9, 0), size=(0.8, 0.32, 0.32), color=GOOD),
            arrow((-1.6, -0.15, 0.35), (-1.6, 0.15, 0.35), color=WARM, shaft=0.03, head=0.18, radius=0.07),
            arrow((0.2, 1.2, 0), (0.6, 1.2, 0), color=INK, shaft=0.03, head=0.18, radius=0.07),
            arrow((0.0, -0.35, 0), (0.0, -0.7, 0), color=INK, shaft=0.03, head=0.18, radius=0.07),
            arrow((-0.15, 0.9, 0.35), (-0.6, 0.9, 0.35), color=BAD, shaft=0.03, head=0.18, radius=0.07),
            chain([(-1.6, 0.9, 0.55), (1.6, 0.9, 0.55), (1.6, -0.9, 0.55), (-1.6, -0.9, 0.55), (-1.6, 0.9, 0.55)],
                  color=GOOD),
        ], labels=[label("node: I₁ = I₂ + I₃", (0, 1.55, 0)), label("source", (-2.05, 0, 0)),
                   label("R₁", (1.25, 1.05, 0)), label("R₂", (0, -1.3, 0)),
                   label("KVL loop: ΣV = 0", (0, -0.9, 0.9))],
            distance=6.6, pitch=14),
    },

    "maxwells-equations": {
        "title": "A current and the field it wraps around it",
        "caption": (
            "Ampère's law: a current along the wire produces a magnetic field that circles it. "
            "The rings are field lines — reverse the current and every ring reverses with it. "
            "Faraday's law is the mirror image, a changing B curling an E. Those two "
            "statements, plus Gauss's laws for E and B, are the whole of classical "
            "electromagnetism."
        ),
        "scene": scene([
            cylinder((0, 0, 0), radius=0.14, height=4.0, color=WARM),
            ring((0, 1.2, 0), 0.62, color=ACCENT, tube=0.025),
            ring((0, 0.4, 0), 0.85, color=ACCENT, tube=0.025),
            ring((0, -0.4, 0), 0.85, color=ACCENT, tube=0.025),
            ring((0, -1.2, 0), 0.62, color=ACCENT, tube=0.025),
            arrow((0, 1.9, 0), (0, 2.6, 0), color=WARM, shaft=0.04, head=0.26, radius=0.1),
            arrow((0.62, 1.2, 0.0), (0.0, 1.2, 0.62), color=GOOD, shaft=0.025, head=0.18, radius=0.06),
            arrow((0.0, -0.4, -0.85), (0.85, -0.4, 0.0), color=GOOD, shaft=0.025, head=0.18, radius=0.06),
        ], labels=[label("I", (0.2, 2.7, 0)), label("B circles the wire", (1.35, 0.4, 0)),
                   label("right-hand rule", (0, -1.7, 0))],
            distance=6.4, pitch=12, spin=0.3),
    },

    "semiconductors-pn-junctions": {
        "title": "The depletion region",
        "caption": (
            "Holes from the p-side and electrons from the n-side recombine at the junction, "
            "leaving behind fixed ions and a region with no free carriers — the depletion "
            "region outlined in white. Those ions set up an electric field E pointing from n "
            "to p, which opposes further diffusion. Equilibrium is a balance between that "
            "field and the concentration gradient, and it is what makes a diode conduct one "
            "way only."
        ),
        "scene": scene([
            grid(6, 6, position=(0, -1.1, 0)),
            box((-1.35, 0, 0), size=(2.0, 1.0, 0.9), color=BAD, opacity=0.3),
            box((1.35, 0, 0), size=(2.0, 1.0, 0.9), color=ACCENT, opacity=0.3),
            *lattice_points(0.5, 3, color=BAD, radius=0.075, offset=(-1.5, 0, 0)),
            *lattice_points(0.5, 3, color=ACCENT, radius=0.075, offset=(1.5, 0, 0)),
            *wire_box((0, 0, 0), (1.1, 1.05, 0.95), color=INK),
            arrow((0.5, 0, 0.6), (-0.5, 0, 0.6), color=WARM, shaft=0.04, head=0.24, radius=0.09),
            arrow((-0.9, 0, -0.6), (-0.35, 0, -0.6), color=GOOD, shaft=0.03, head=0.2, radius=0.07),
            arrow((0.35, 0, -0.6), (0.9, 0, -0.6), color=GOOD, shaft=0.03, head=0.2, radius=0.07),
        ], labels=[label("p-type (holes)", (-1.5, 0.85, 0)), label("n-type (electrons)", (1.5, 0.85, 0)),
                   label("depletion region", (0, -0.85, 0)), label("E: n → p", (0, 0.4, 0.9)),
                   label("diffusion", (0, 0.35, -0.9))],
            distance=7.2, pitch=14),
    },

    "per-unit-system-fault-analysis": {
        "title": "A balanced three-phase set, 120° apart",
        "caption": (
            "Three identical sinusoids, each a third of a cycle behind the last. At every "
            "instant they sum to zero, which is why a balanced load needs no neutral current. "
            "A fault breaks that symmetry: the per-unit system lets you compare a 400 kV "
            "transmission line and a 415 V feeder on the same base, because every quantity is "
            "a ratio to its own rating."
        ),
        "scene": scene([
            *[pipe([(-2.6 + 0.13 * i,
                     0.85 * math.sin(i * 0.35 + phase),
                     0.9 * (k - 1))
                    for i in range(41)],
                   color=colour, radius=0.045)
              for k, (phase, colour) in enumerate([(0.0, ACCENT), (2.094, WARM), (4.189, GOOD)])],
            chain([(-2.7, 0, -0.9), (-2.7, 0, 0.9)], color=DIM),
            chain([(2.7, 0, -0.9), (2.7, 0, 0.9)], color=DIM),
            chain([(-2.7, 0, 0), (2.7, 0, 0)], color=DIM, ),
        ], labels=[label("phase a", (2.9, 0.9, -0.9)), label("phase b", (2.9, 0.9, 0)),
                   label("phase c", (2.9, 0.9, 0.9)), label("time →", (0, -1.3, 0))],
            distance=8.0, pitch=18, yaw=30, spin=0.0),
    },

    # ------------------------------------------------------- data structures --

    "binary-trees-traversals": {
        "title": "A binary tree, with depth as depth",
        "caption": (
            "Each level sits one step further back and one step lower, so the depth of a node "
            "is literally how far away it is. In-order (left, root, right) visits 1 2 3 4 5 6 "
            "7; pre-order (root, left, right) visits 4 2 1 3 6 5 7. Traversal cost is O(n) "
            "because every node is visited exactly once, but stack depth is O(h) — which is "
            "why a balanced tree matters."
        ),
        "scene": scene([
            *tree_edges(binary_tree_layout(list(range(1, 8)))),
            *[sphere(p, 0.2, color=ACCENT if i else WARM) for i, p in enumerate(binary_tree_layout(list(range(1, 8))))],
        ], labels=[label(str(v), (p[0], p[1] + 0.32, p[2])) for v, p in zip(range(1, 8), binary_tree_layout(list(range(1, 8))))]
            + [label("root", (binary_tree_layout([1])[0][0], 1.9, 0))],
            distance=8.5, pitch=20, yaw=25, spin=0.12),
    },

    "binary-search-trees": {
        "title": "Searching a BST: half the tree dies at every step",
        "caption": (
            "Every left subtree holds smaller keys, every right subtree larger. To find 50 the "
            "search compares once at 40, goes right, compares at 60, goes left — two "
            "comparisons, and each one discards an entire subtree. That is O(log n) in a "
            "balanced tree and O(n) in a degenerate one, which is the whole reason self-"
            "balancing trees exist."
        ),
        "scene": scene([
            *tree_edges(binary_tree_layout([40, 20, 60, 10, 30, 50, 70])),
            *[sphere(p, 0.2, color=(BAD if v in (40, 60, 50) else ACCENT))
              for v, p in zip([40, 20, 60, 10, 30, 50, 70], binary_tree_layout([40, 20, 60, 10, 30, 50, 70]))],
            pipe([binary_tree_layout([40, 20, 60, 10, 30, 50, 70])[0],
                  binary_tree_layout([40, 20, 60, 10, 30, 50, 70])[2],
                  binary_tree_layout([40, 20, 60, 10, 30, 50, 70])[5]], color=WARM, radius=0.03),
        ], labels=[label(str(v), (p[0], p[1] + 0.32, p[2]))
                   for v, p in zip([40, 20, 60, 10, 30, 50, 70], binary_tree_layout([40, 20, 60, 10, 30, 50, 70]))]
            + [label("search for 50 → 3 comparisons", (0, -1.9, 1.8))],
            distance=8.5, pitch=20, yaw=25, spin=0.12),
    },

    "hash-tables": {
        "title": "Buckets, collisions and chains",
        "caption": (
            "h(key) picks a bucket, so a lookup touches one slot and costs O(1) on average. "
            "Two keys can hash to the same bucket — a collision — and then the bucket holds a "
            "chain, and the chain must be walked. Average cost is therefore 1 + α where α is "
            "the load factor: keep the table under roughly 75% full and chains stay short."
        ),
        "scene": scene([
            grid(9, 9, position=(0, -1.6, 0)),
            *[box((i * 0.85 - 2.975, -0.8, 0), size=(0.5, 0.5, 0.5), color=(NEUTRAL if i != 3 else WARM))
              for i in range(8)],
            *[arrow((x, -0.15, 0), (x, -0.5, 0), color=ACCENT, shaft=0.025, head=0.16, radius=0.06)
              for x in (-2.975, -1.275, 0.425, 2.125)],
            sphere((-2.975, -0.15, 0), 0.11, color=ACCENT),
            sphere((-1.275, -0.15, 0), 0.11, color=ACCENT),
            sphere((2.125, -0.15, 0), 0.11, color=ACCENT),
            sphere((-1.275, 0.3, 0), 0.14, color=BAD),
            sphere((0.425, 0.35, 0), 0.14, color=BAD),
            sphere((0.425, 0.35, -0.55), 0.14, color=BAD),
            sphere((0.425, 0.35, -1.1), 0.14, color=BAD),
            edge((0.425, -0.55, 0), (0.425, 0.2, 0), color=DIM),
            edge((0.425, 0.35, -0.14), (0.425, 0.35, -0.41), color=DIM),
            edge((0.425, 0.35, -0.69), (0.425, 0.35, -0.96), color=DIM),
        ], labels=[label("bucket 0", (-2.975, -1.2, 0)), label("bucket 3", (0.425, -1.2, 0)),
                   label("bucket 7", (2.975, -1.2, 0)),
                   label("collision chain — walked in order", (0.425, 0.85, -0.6))],
            distance=7.6, pitch=18, yaw=32),
    },

    "linked-lists": {
        "title": "A singly linked list",
        "caption": (
            "Each node stores a value and a pointer to the next node, and nothing else — so "
            "insertion at a known position is O(1) because only two pointers change, while "
            "finding that position is O(n) because the only way forward is through the links. "
            "The nodes need not be adjacent in memory, which is exactly why an array beats it "
            "for cache locality."
        ),
        "scene": scene([
            grid(9, 9, position=(0, -0.9, 0)),
            *[box((i * 1.5 - 2.25, 0, 0), size=(0.95, 0.6, 0.6), color=ACCENT if i else WARM)
              for i in range(4)],
            box((3.75, 0, 0), size=(0.75, 0.6, 0.6), color=DIM, opacity=0.6),
            *[arrow((i * 1.5 - 1.65, 0, 0), (i * 1.5 - 0.6, 0, 0), color=GOOD, shaft=0.03, head=0.18, radius=0.07)
              for i in range(1, 4)],
            arrow((-3.6, 0, 0), (-2.85, 0, 0), color=BAD, shaft=0.03, head=0.18, radius=0.07),
        ], labels=[label("head", (-3.9, 0.35, 0)), label("next", (0, 0.45, 0)),
                   label("NULL", (3.75, -0.45, 0)), label("O(1) insert, O(n) search", (0, -0.75, 0))],
            distance=8.2, pitch=15, yaw=26, spin=0.0),
    },

    "stacks-queues": {
        "title": "LIFO against FIFO",
        "caption": (
            "The stack on the left only exposes its top: the last thing pushed is the first "
            "thing popped, which is what makes it the natural home for call frames and undo "
            "histories. The queue on the right exposes two ends: everything leaves in the "
            "order it arrived, which is what a scheduler or a printer spool needs. Same "
            "building blocks, opposite disciplines."
        ),
        "scene": scene([
            grid(9, 9, position=(0, -1.4, 0)),
            *[box((-1.9, -0.9 + i * 0.5, 0), size=(1.5, 0.4, 0.9), color=ACCENT if i == 3 else NEUTRAL)
              for i in range(4)],
            arrow((-1.9, 1.5, 0), (-1.9, 0.95, 0), color=GOOD, shaft=0.035, head=0.2, radius=0.08),
            arrow((-1.9, 0.95, 0.7), (-1.9, 1.5, 0.7), color=WARM, shaft=0.035, head=0.2, radius=0.08),
            *[box((i * 0.85 - 0.2, -1.0, 1.6), size=(0.6, 0.55, 0.6), color=ACCENT if i == 0 else NEUTRAL)
              for i in range(4)],
            arrow((-1.6, -1.0, 1.6), (-1.0, -1.0, 1.6), color=WARM, shaft=0.035, head=0.2, radius=0.08),
            arrow((3.3, -1.0, 1.6), (3.9, -1.0, 1.6), color=GOOD, shaft=0.035, head=0.2, radius=0.08),
        ], labels=[label("push", (-1.9, 1.75, 0)), label("pop", (-1.9, 1.75, 0.7)),
                   label("LIFO — last in, first out", (-1.9, -1.6, 0)),
                   label("enqueue", (-1.9, -0.5, 1.6)), label("dequeue", (3.9, -0.5, 1.6)),
                   label("FIFO — first in, first out", (1.2, -1.6, 1.6))],
            distance=9.5, pitch=20, yaw=32),
    },

    "graphs-traversals": {
        "title": "A graph, and a breadth-first sweep through it",
        "caption": (
            "Six vertices, seven edges, no coordinates implied — a graph is relationships, not "
            "geometry. BFS from A reaches B and C first, then D and E, then F, because it "
            "explores in rings of distance. That is why BFS finds the shortest unweighted path "
            "and DFS does not: DFS would dive straight down one branch instead."
        ),
        "scene": scene([
            *[edge(a, b, color=DIM) for a, b in [
                ((0, 1.2, 0), (-1.6, 0.2, 0.5)), ((0, 1.2, 0), (1.6, 0.2, -0.5)),
                ((-1.6, 0.2, 0.5), (-2.4, -1.0, 1.2)), ((-1.6, 0.2, 0.5), (0.2, -1.0, 1.4)),
                ((1.6, 0.2, -0.5), (2.4, -1.0, -1.2)), ((0.2, -1.0, 1.4), (2.4, -1.0, -1.2)),
                ((-2.4, -1.0, 1.2), (0.2, -1.0, 1.4)),
            ]],
            sphere((0, 1.2, 0), 0.24, color=WARM),
            sphere((-1.6, 0.2, 0.5), 0.22, color=BAD),
            sphere((1.6, 0.2, -0.5), 0.22, color=BAD),
            sphere((-2.4, -1.0, 1.2), 0.22, color=GOOD),
            sphere((0.2, -1.0, 1.4), 0.22, color=GOOD),
            sphere((2.4, -1.0, -1.2), 0.22, color=ACCENT),
        ], labels=[label("A (0)", (0, 1.6, 0)), label("B (1)", (-1.6, 0.6, 0.5)),
                   label("C (1)", (1.6, 0.6, -0.5)), label("D (2)", (-2.4, -0.6, 1.2)),
                   label("E (2)", (0.2, -0.6, 1.4)), label("F (3)", (2.4, -0.6, -1.2))],
            distance=8.0, pitch=18, spin=0.15),
    },

    "heaps-priority-queues": {
        "title": "A binary heap, level by level",
        "caption": (
            "A heap is a complete binary tree stored in an array, and its only rule is that "
            "every parent beats its children. The maximum is therefore always at the root, so "
            "extract-max is O(log n): swap the root with the last leaf, then sift down. This "
            "is a max-heap — 90 on top, and each level strictly below its parent."
        ),
        "scene": scene([
            *tree_edges(binary_tree_layout([90, 70, 80, 40, 50, 60, 30])),
            *[sphere(p, 0.2, color=WARM if i == 0 else ACCENT)
              for i, p in enumerate(binary_tree_layout([90, 70, 80, 40, 50, 60, 30]))],
        ], labels=[label(str(v), (p[0], p[1] + 0.32, p[2]))
                   for v, p in zip([90, 70, 80, 40, 50, 60, 30],
                                   binary_tree_layout([90, 70, 80, 40, 50, 60, 30]))]
            + [label("root = max, always", (0, 1.95, 0))],
            distance=8.5, pitch=20, yaw=25, spin=0.12),
    },

    "recursion-backtracking": {
        "title": "A recursion tree, and the path that backs out",
        "caption": (
            "Each level is one recursive call and sits further back in space, so the call "
            "stack has a visible depth. Backtracking tries a branch, hits a dead end, returns, "
            "and tries the next one — the orange path is that walk. Depth costs stack frames, "
            "and branching costs time: a tree that doubles at every level reaches 2^d leaves, "
            "which is why pruning matters more than anything else."
        ),
        "scene": scene([
            *tree_edges(binary_tree_layout(list(range(1, 16)))),
            *[sphere(p, 0.13, color=BAD if i in (7, 8) else ACCENT)
              for i, p in enumerate(binary_tree_layout(list(range(1, 16))))],
            pipe([binary_tree_layout(list(range(1, 16)))[0],
                  binary_tree_layout(list(range(1, 16)))[1],
                  binary_tree_layout(list(range(1, 16)))[3],
                  binary_tree_layout(list(range(1, 16)))[7]], color=WARM, radius=0.03),
        ], labels=[label("dead end — backtrack", (binary_tree_layout(list(range(1, 16)))[7][0], -1.6, 3.0)),
                   label("depth = stack frames", (3.2, 0.6, 1.5))],
            distance=10.5, pitch=18, yaw=22, spin=0.1),
    },

    "arrays": {
        "title": "A two-dimensional array in row-major order",
        "caption": (
            "A 4×3 array is 12 contiguous cells, and a[i][j] sits at offset i·3 + j — that "
            "arithmetic is the entire implementation, with no pointers anywhere. Because the "
            "cells are contiguous, walking a row strides through memory one element at a "
            "time and the cache stays warm; walking a column strides by 3 and thrashes it. "
            "That single fact explains most array performance."
        ),
        "scene": scene([
            grid(8, 8, position=(0, -0.7, 0)),
            *[box((j * 0.85 - 1.275, 0, i * 0.85 - 0.85), size=(0.7, 0.3, 0.7),
                  color=WARM if i == 1 else ACCENT)
              for i in range(3) for j in range(4)],
            arrow((-2.6, 0, -0.85), (-1.9, 0, -0.85), color=GOOD, shaft=0.03, head=0.18, radius=0.07),
            arrow((1.9, 0, -0.85), (2.5, 0, -0.85), color=GOOD, shaft=0.03, head=0.18, radius=0.07),
            arrow((-1.275, 0, -2.1), (-1.275, 0, -1.5), color=BAD, shaft=0.03, head=0.18, radius=0.07),
        ], labels=[label("row 1 — highlighted", (0, 0.45, 0)),
                   label("a[i][j] at offset i·3 + j", (0, -0.6, 1.9)),
                   label("walking a row: stride 1 (fast)", (2.9, 0.2, -0.85)),
                   label("walking a column: stride 4 (slow)", (-1.275, 0.2, -2.4))],
            distance=8.4, pitch=26, yaw=35, spin=0.1),
    },

    "sorting-complexity": {
        "title": "What O(n), O(n log n) and O(n²) actually cost",
        "caption": (
            "Three curves over the same input sizes. Linear and linearithmic growth look "
            "almost identical here and stay usable at a million items. The quadratic curve "
            "looks harmless at n = 10 and is four orders of magnitude worse at n = 1000 — "
            "which is the entire reason a bubble sort is a teaching tool and a merge sort is "
            "what ships."
        ),
        "scene": scene([
            grid(8, 8, position=(0, -0.1, 0)),
            *[pipe([(-3.0 + 0.15 * i, 0.05 + 0.9 * (i / 20.0), 0.0) for i in range(21)],
                   color=GOOD, radius=0.045),
              pipe([(-3.0 + 0.15 * i, 0.05 + 1.5 * (i / 20.0) * math.log2(i + 2) / math.log2(22), 0.0)
                    for i in range(21)], color=WARM, radius=0.045),
              pipe([(-3.0 + 0.15 * i, 0.05 + 3.2 * (i / 20.0) ** 2, 0.0) for i in range(21)],
                   color=BAD, radius=0.045)],
            arrow((-3.0, 0, 0), (3.3, 0, 0), color=DIM, shaft=0.02, head=0.18, radius=0.05),
            arrow((-3.0, 0, 0), (-3.0, 3.4, 0), color=DIM, shaft=0.02, head=0.18, radius=0.05),
        ], labels=[label("O(n)", (3.35, 1.0, 0)), label("O(n log n)", (3.35, 1.7, 0)),
                   label("O(n²)", (3.35, 3.1, 0)), label("input size n →", (0, -0.45, 0)),
                   label("operations", (-3.6, 3.5, 0))],
            distance=9.0, pitch=10, yaw=18, spin=0.0),
    },

    "dynamic-programming": {
        "title": "A DP table, with the answer in the last cell",
        "caption": (
            "The height of each cell is the value stored there, and each cell is computed only "
            "from cells already behind it. That is the whole technique: define a subproblem, "
            "fill a table in an order where every dependency is ready, and read the answer "
            "off the far corner. Storing the table turns an exponential recursion into "
            "O(rows × cols)."
        ),
        "scene": scene([
            grid(8, 8, position=(0, -0.15, 0)),
            *[box((j * 0.72 - 1.44, 0.06 + 0.09 * v, i * 0.72 - 1.44),
                  size=(0.62, 0.12 + 0.18 * v, 0.62),
                  color=BAD if (i, j) == (4, 4) else (WARM if (i + j) == 7 else ACCENT))
              for i, row in enumerate([[0, 1, 2, 3, 4], [1, 1, 2, 3, 4], [2, 2, 2, 3, 4],
                                       [3, 3, 3, 3, 4], [4, 4, 4, 4, 4]])
              for j, v in enumerate(row)],
            arrow((-2.6, 1.1, -2.6), (-1.9, 1.1, -1.9), color=GOOD, shaft=0.03, head=0.2, radius=0.07),
        ], labels=[label("base cases (row and column 0)", (0, 1.35, -1.9)),
                   label("each cell reads its neighbours", (0, 1.35, 0.4)),
                   label("answer", (1.44, 1.6, 1.44))],
            distance=9.0, pitch=30, yaw=35, spin=0.1),
    },

    # ------------------------------------------------------------- systems --

    "memory-management-paging": {
        "title": "Paging: indirection between what you see and what exists",
        "caption": (
            "The process believes it has four contiguous pages. The page table maps them onto "
            "physical frames in any order at all — here page 2 lands in frame 0 and page 0 in "
            "frame 3. Nothing has to be physically adjacent, so external fragmentation "
            "disappears, and an unmapped page simply faults instead of corrupting its "
            "neighbour. The cost is one extra lookup per access, which is what a TLB caches."
        ),
        "scene": scene([
            grid(8, 8, position=(0, -1.4, 0)),
            *[box((-1.6, 0.9 - i * 0.75, 0), size=(1.0, 0.55, 0.7), color=ACCENT) for i in range(4)],
            *[box((1.6, 0.9 - i * 0.75, 0), size=(1.0, 0.55, 0.7),
                  color=NEUTRAL if i != 2 else DIM) for i in range(4)],
            pipe([(-1.05, 0.9, 0), (1.05, 0.9 - 3 * 0.75, 0)], color=WARM, radius=0.035),
            pipe([(-1.05, 0.9 - 0.75, 0), (1.05, 0.9 - 1 * 0.75, 0)], color=WARM, radius=0.035),
            pipe([(-1.05, 0.9 - 1.5, 0), (1.05, 0.9 - 0 * 0.75, 0)], color=BAD, radius=0.035),
            pipe([(-1.05, 0.9 - 2.25, 0), (1.05, 0.9 - 1.5 * 0.75, 0)], color=WARM, radius=0.035),
        ], labels=[label("virtual pages", (-1.6, 1.55, 0)), label("physical frames", (1.6, 1.55, 0)),
                   label("page 0", (-2.35, 0.9, 0)), label("page 2", (-2.35, -0.6, 0)),
                   label("frame 0", (2.35, 0.9, 0)), label("frame 3", (2.35, -1.35, 0)),
                   label("page table = the arrows", (0, -1.75, 0))],
            distance=8.4, pitch=16, spin=0.0),
    },

    "cpu-scheduling": {
        "title": "A Gantt chart: the same jobs, two schedules",
        "caption": (
            "The top row runs the jobs in submission order (FCFS); the bottom runs the "
            "shortest job first. Same work, same total, but the short job at the back of the "
            "first row waits through everything ahead of it. SJF minimises average waiting "
            "time — and starves long jobs, which is why real schedulers age them."
        ),
        "scene": scene([
            grid(10, 10, position=(0, -0.6, 0)),
            box((-2.2, 0.55, 0), size=(2.6, 0.4, 0.6), color=ACCENT),
            box((0.6, 0.55, 0), size=(1.4, 0.4, 0.6), color=WARM),
            box((2.3, 0.55, 0), size=(2.0, 0.4, 0.6), color=GOOD),
            box((-2.9, -0.55, 0), size=(1.4, 0.4, 0.6), color=WARM),
            box((-0.9, -0.55, 0), size=(2.0, 0.4, 0.6), color=GOOD),
            box((1.6, -0.55, 0), size=(2.6, 0.4, 0.6), color=ACCENT),
            chain([(-3.5, 0, 0), (3.5, 0, 0)], color=DIM),
            *[chain([(x, 0, 0), (x, 0.95, 0)], color=DIM) for x in (-3.5, -2.2, -0.9, 0.6, 1.6, 3.5)],
        ], labels=[label("FCFS", (-4.0, 0.55, 0)), label("SJF", (-4.0, -0.55, 0)),
                   label("A (long)", (-2.2, 0.95, 0)), label("B", (0.6, 0.95, 0)),
                   label("C", (2.3, 0.95, 0)), label("time →", (0, -0.35, 0))],
            distance=9.5, pitch=22, yaw=24, spin=0.0),
    },

    "deadlocks": {
        "title": "Circular wait — the fourth Coffman condition",
        "caption": (
            "P0 holds R0 and waits for R1; P1 holds R1 and waits for R2; P2 holds R2 and waits "
            "for R0. Nobody can proceed and nobody will let go, so the system is stuck "
            "forever. Break any one of the four conditions — mutual exclusion, hold and wait, "
            "no preemption, circular wait — and deadlock becomes impossible. Ordering lock "
            "acquisition breaks the cycle and is the cheapest fix in practice."
        ),
        "scene": scene([
            grid(7, 7, position=(0, -1.0, 0)),
            sphere((-1.5, 0.9, 0), 0.3, color=ACCENT),
            sphere((1.5, 0.9, 0), 0.3, color=ACCENT),
            sphere((0.0, -1.0, 0), 0.3, color=ACCENT),
            box((-2.2, -0.4, 0), size=(0.55, 0.55, 0.55), color=WARM),
            box((2.2, -0.4, 0), size=(0.55, 0.55, 0.55), color=WARM),
            box((0.0, 1.5, 0), size=(0.55, 0.55, 0.55), color=WARM),
            arrow((-1.2, 0.75, 0), (1.2, 0.75, 0), color=BAD, shaft=0.035, head=0.2, radius=0.08),
            arrow((1.3, 0.6, 0), (0.3, -0.7, 0), color=BAD, shaft=0.035, head=0.2, radius=0.08),
            arrow((-0.3, -0.7, 0), (-1.3, 0.6, 0), color=BAD, shaft=0.035, head=0.2, radius=0.08),
            edge((-1.9, 0.7, 0), (-2.2, -0.1, 0), color=GOOD),
            edge((1.9, 0.7, 0), (2.2, -0.1, 0), color=GOOD),
            edge((-0.15, -1.3, 0), (0.0, 1.2, 0), color=GOOD),
        ], labels=[label("P0", (-1.5, 1.35, 0)), label("P1", (1.5, 1.35, 0)), label("P2", (0, -1.45, 0)),
                   label("R0", (-2.6, -0.4, 0)), label("R1", (2.6, -0.4, 0)), label("R2", (0, 1.95, 0)),
                   label("holds", (-1.4, 0.2, 0)), label("waits for", (0.4, 0.0, 0))],
            distance=7.6, pitch=18, spin=0.15),
    },

    "processes-threads": {
        "title": "One process, several threads, one shared heap",
        "caption": (
            "The outer box is the process: it owns the address space, the file handles and the "
            "memory. The cylinders inside are threads. They share the heap and the open files "
            "but each keeps its own stack and registers — which is exactly why a thread can be "
            "created far more cheaply than a process, and exactly why two threads writing the "
            "same heap object need synchronisation."
        ),
        "scene": scene([
            grid(8, 8, position=(0, -1.5, 0)),
            box((0, 0, 0), size=(3.2, 2.4, 1.8), color=DIM, opacity=0.22),
            *[cylinder((x, 0.45, 0), radius=0.24, height=1.5, color=ACCENT) for x in (-0.95, 0.0, 0.95)],
            box((0, -0.85, 0), size=(2.6, 0.5, 1.2), color=WARM, opacity=0.8),
            *[box((x, 1.4, 0), size=(0.5, 0.3, 0.5), color=NEUTRAL) for x in (-0.95, 0.0, 0.95)],
        ], labels=[label("process: own address space, open files", (0, 1.85, 0)),
                   label("thread 1", (-0.95, -0.4, 0)), label("thread 2", (0.0, -0.4, 0)),
                   label("thread 3", (0.95, -0.4, 0)),
                   label("shared heap — needs locking", (0, -1.35, 0)),
                   label("private stacks", (0, 1.75, 0.6))],
            distance=8.0, pitch=16, spin=0.12),
    },

    "synchronisation-semaphores": {
        "title": "A bounded buffer guarded by two semaphores",
        "caption": (
            "The producer waits on `empty` before writing, the consumer waits on `full` before "
            "reading, and both take `mutex` while touching the ring. `empty` and `full` count "
            "the free and filled slots, so neither side can overtake the other; `mutex` makes "
            "each individual update atomic. Remove `mutex` and two threads can claim the same "
            "slot — which is a race, not a deadlock."
        ),
        "scene": scene([
            grid(8, 8, position=(0, -1.2, 0)),
            ring((0, 0, 0), 1.35, color=DIM, tube=0.14),
            *[box((1.35 * math.cos(a), 0, 1.35 * math.sin(a)), size=(0.5, 0.32, 0.5),
                  color=WARM if i < 3 else NEUTRAL, rotation=(0, -math.degrees(a), 0))
              for i, a in enumerate([i * math.pi / 4 for i in range(8)])],
            arrow((-2.6, 0, 0), (-1.75, 0, 0), color=GOOD, shaft=0.04, head=0.22, radius=0.09),
            arrow((1.75, 0, 0), (2.6, 0, 0), color=ACCENT, shaft=0.04, head=0.22, radius=0.09),
        ], labels=[label("producer", (-2.9, 0.35, 0)), label("consumer", (2.9, 0.35, 0)),
                   label("filled slots", (0, 0.4, 1.35)), label("free slots", (0, 0.4, -1.35)),
                   label("wait(empty) / wait(full) / mutex", (0, -0.6, 0))],
            distance=7.6, pitch=32, spin=0.15),
    },

    "cache-memory-locality": {
        "title": "Sets, ways and the line that gets evicted",
        "caption": (
            "Main memory is addressed by (tag, set index, offset). The set index picks a row "
            "here; the ways are the slots in that row; the tag decides which one actually "
            "holds your line. Two addresses with the same set index compete for the same few "
            "ways, so a loop that strides by the cache size thrashes while a loop that walks "
            "consecutively never misses. Locality is not an optimisation — it is the model."
        ),
        "scene": scene([
            grid(9, 9, position=(0, -0.6, 0)),
            *[box((w * 0.8 - 1.2, 0, s * 0.75 - 1.125), size=(0.68, 0.24, 0.62),
                  color=WARM if (s == 1 and w == 0) else (ACCENT if (s + w) % 2 == 0 else NEUTRAL))
              for s in range(4) for w in range(4)],
            box((3.2, 0.9, 0), size=(0.7, 0.7, 0.7), color=BAD),
            pipe([(3.2, 0.5, 0), (-1.2, 0.3, -0.375)], color=BAD, radius=0.03),
        ], labels=[label("set index →", (0, -0.45, 1.9)), label("ways →", (-2.6, 0.3, 0)),
                   label("memory line", (3.2, 1.5, 0)), label("hit", (-1.2, 0.45, -0.375)),
                   label("tag check picks the way", (0, 0.7, 0))],
            distance=8.6, pitch=32, yaw=32, spin=0.1),
    },

    "file-systems": {
        "title": "A directory tree and the inodes behind it",
        "caption": (
            "A path is a walk down a tree: each directory holds names pointing at inode "
            "numbers, and each inode holds the metadata and the block pointers — never the "
            "name. That separation is why a hard link works (two names, one inode) and why "
            "deleting a file only removes a name until the last one is gone."
        ),
        "scene": scene([
            *[edge((0, 1.6, 0), p, color=DIM) for p in [(-1.8, 0.5, 0), (0, 0.5, 0.9), (1.8, 0.5, -0.4)]],
            *[edge((-1.8, 0.5, 0), p, color=DIM) for p in [(-2.6, -0.6, 0.4), (-1.0, -0.6, -0.4)]],
            *[edge((1.8, 0.5, -0.4), p, color=DIM) for p in [(1.2, -0.6, -1.0), (2.6, -0.6, 0.2)]],
            box((0, 1.6, 0), size=(0.9, 0.45, 0.5), color=WARM),
            *[box(p, size=(0.85, 0.42, 0.5), color=ACCENT)
              for p in [(-1.8, 0.5, 0), (0, 0.5, 0.9), (1.8, 0.5, -0.4)]],
            *[box(p, size=(0.8, 0.36, 0.45), color=GOOD)
              for p in [(-2.6, -0.6, 0.4), (-1.0, -0.6, -0.4), (1.2, -0.6, -1.0), (2.6, -0.6, 0.2)]],
        ], labels=[label("/", (0, 2.0, 0)), label("etc", (-1.8, 0.9, 0)), label("home", (0, 0.9, 0.9)),
                   label("var", (1.8, 0.9, -0.4)), label("passwd", (-2.6, -0.25, 0.4)),
                   label("log", (2.6, -0.25, 0.2))],
            distance=8.0, pitch=20, spin=0.12),
    },

    "transactions-acid": {
        "title": "Two transactions racing on one row",
        "caption": (
            "T1 and T2 both read the same balance and both write it back. Interleaved like "
            "this, one update is silently lost — the classic lost update. Isolation exists to "
            "prevent exactly that, and the price is concurrency: serialisable ordering is safe "
            "and slow, read committed is fast and permits anomalies. Every isolation level is "
            "a point on that trade."
        ),
        "scene": scene([
            grid(10, 10, position=(0, -0.7, 0)),
            box((-1.4, 0.6, 0.9), size=(2.2, 0.3, 0.5), color=ACCENT),
            box((1.0, 0.6, 0.0), size=(2.2, 0.3, 0.5), color=WARM),
            box((-0.4, 0.6, -0.9), size=(2.2, 0.3, 0.5), color=GOOD),
            chain([(-3.2, 0.6, 1.4), (3.2, 0.6, 1.4)], color=DIM),
            box((0.0, -0.2, 0.0), size=(0.9, 0.5, 0.9), color=BAD),
            arrow((-1.0, 0.35, 0.9), (-0.4, 0.05, 0.45), color=ACCENT, shaft=0.02, head=0.14, radius=0.05),
            arrow((1.4, 0.35, 0.0), (0.4, 0.05, 0.0), color=WARM, shaft=0.02, head=0.14, radius=0.05),
            arrow((-0.2, 0.35, -0.9), (0.0, 0.05, -0.45), color=GOOD, shaft=0.02, head=0.14, radius=0.05),
        ], labels=[label("T1", (-2.7, 0.6, 0.9)), label("T2", (-0.2, 0.6, 0.0)),
                   label("T3", (-1.7, 0.6, -0.9)), label("shared row", (0, -0.65, 0)),
                   label("time →", (3.4, 0.6, 1.4))],
            distance=9.0, pitch=26, yaw=30, spin=0.0),
    },

    # ---------------------------------------------------- databases / web ----

    "osi-tcp-ip-models": {
        "title": "The stack, and what encapsulation adds at each floor",
        "caption": (
            "Data descends the stack and each layer wraps what it was given: the application "
            "message becomes a segment, then a packet, then a frame, then bits. The arrow on "
            "the right is that descent. Each header is only meaningful to the matching layer "
            "on the far end, which is what lets you replace Ethernet with Wi-Fi without the "
            "application noticing."
        ),
        "scene": scene([
            *slabs(7, size=(2.8, 0.26, 1.5), gap=0.3, start=-1.3,
                   colour_at=lambda i: ["#7f5af0", "#4f7cff", "#3aa0ff", "#35d39a", "#8fd14f",
                                        "#ffce54", "#ff9f43"][i]),
            arrow((2.2, 1.4, 0), (2.2, -1.3, 0), color=INK, shaft=0.04, head=0.26, radius=0.1),
            arrow((-2.2, -1.3, 0), (-2.2, 1.4, 0), color=DIM, shaft=0.04, head=0.26, radius=0.1),
            box((0, 2.0, 0), size=(1.2, 0.3, 0.8), color=NEUTRAL),
        ], labels=[label("7 application", (0, 1.05, 0.95)), label("6 presentation", (0, 0.75, 0.95)),
                   label("5 session", (0, 0.45, 0.95)), label("4 transport — segments", (0, 0.15, 0.95)),
                   label("3 network — packets", (0, -0.15, 0.95)), label("2 data link — frames", (0, -0.45, 0.95)),
                   label("1 physical — bits", (0, -0.75, 0.95)), label("your data", (0, 2.35, 0)),
                   label("down", (2.55, 0, 0)), label("up", (-2.55, 0, 0))],
            distance=8.4, pitch=14, yaw=28, spin=0.08),
    },

    "ip-addressing-subnetting": {
        "title": "One address block, carved into subnets",
        "caption": (
            "The big cube is a /24: 256 addresses. Moving one bit from the host part to the "
            "network part halves it into two /25s, again into four /26s. Every cut costs two "
            "addresses per subnet — the network and the broadcast address — so a /30 leaves "
            "exactly two usable hosts, which is why point-to-point links use them."
        ),
        "scene": scene([
            *wire_box((0, 0.9, 0), (3.0, 1.5, 2.0), color=DIM),
            box((-0.75, 0.9, 0), size=(1.4, 1.35, 1.85), color=ACCENT, opacity=0.55),
            box((0.75, 0.9, 0), size=(1.4, 1.35, 1.85), color=GOOD, opacity=0.55),
            box((-1.125, -0.9, 0), size=(0.65, 1.0, 1.6), color=WARM, opacity=0.75),
            box((-0.375, -0.9, 0), size=(0.65, 1.0, 1.6), color=BAD, opacity=0.75),
            box((0.375, -0.9, 0), size=(0.65, 1.0, 1.6), color=NEUTRAL, opacity=0.75),
            box((1.125, -0.9, 0), size=(0.65, 1.0, 1.6), color=INK, opacity=0.55),
            arrow((0, 0.05, 0), (0, -0.3, 0), color=INK, shaft=0.03, head=0.18, radius=0.07),
        ], labels=[label("/24 — 256 addresses", (0, 1.85, 0)), label("/25", (-0.75, 0.9, 1.1)),
                   label("/25", (0.75, 0.9, 1.1)), label("/26 each — 62 usable", (0, -1.6, 0))],
            distance=7.6, pitch=16, spin=0.12),
    },

    "tcp-flow-control": {
        "title": "The sliding window",
        "caption": (
            "The strip is the byte stream. The sender may have everything inside the bracket "
            "in flight and nothing outside it. As acknowledgements arrive the bracket slides "
            "right; the receiver advertises how much room it has, so the bracket can also "
            "shrink. That single mechanism is what stops a fast sender from drowning a slow "
            "receiver — flow control, distinct from congestion control."
        ),
        "scene": scene([
            grid(11, 11, position=(0, -0.5, 0)),
            *[box((i * 0.62 - 3.1, 0, 0), size=(0.5, 0.45, 0.9),
                  color=DIM if i < 3 else (GOOD if i < 5 else (WARM if i < 9 else NEUTRAL)))
              for i in range(11)],
            *wire_box((0.94, 0, 0), (2.7, 0.75, 1.25), color=BAD),
            arrow((0.94, 0.75, 0), (2.2, 0.75, 0), color=BAD, shaft=0.02, head=0.16, radius=0.05),
        ], labels=[label("acked", (-2.6, 0.55, 0)), label("in flight", (0.6, 0.55, 0)),
                   label("not yet allowed", (2.9, 0.55, 0)),
                   label("window = receiver's advertised space", (0.94, 1.0, 0)),
                   label("slides right as ACKs arrive", (2.0, 1.0, 0.7))],
            distance=10.0, pitch=26, yaw=26, spin=0.0),
    },

    "sql-joins-aggregation": {
        "title": "An inner join as an intersection",
        "caption": (
            "Two tables, each a block of rows. An inner join keeps only the rows whose key "
            "appears in both — geometrically the overlap in the middle. A LEFT join keeps the "
            "whole left block and fills the unmatched part with NULL. Aggregation then "
            "collapses groups of rows into one row per key, which is why GROUP BY must name "
            "every column it does not aggregate."
        ),
        "scene": scene([
            grid(9, 9, position=(0, -0.9, 0)),
            *[box((x, 0, z), size=(0.55, 0.5, 0.55), color=ACCENT, opacity=0.75)
              for x in (-1.6, -0.9, -0.2) for z in (-0.7, 0.0, 0.7)],
            *[box((x, 0, z), size=(0.55, 0.5, 0.55), color=GOOD, opacity=0.75)
              for x in (0.2, 0.9, 1.6) for z in (-0.7, 0.0, 0.7)],
            *[box((x, 0.6, z), size=(0.55, 0.5, 0.55), color=WARM)
              for x in (-0.2, 0.2) for z in (-0.7, 0.0, 0.7)],
        ], labels=[label("orders", (-1.6, 0.6, 0)), label("customers", (1.6, 0.6, 0)),
                   label("matching keys", (0, 1.3, 0)), label("INNER JOIN keeps only this", (0, -0.75, 1.3))],
            distance=8.4, pitch=30, yaw=30, spin=0.1),
    },

    "normalization": {
        "title": "One wide table, decomposed",
        "caption": (
            "The wide table on the left repeats the department name and its manager for every "
            "employee, so one fact is stored many times and an update can leave the copies "
            "disagreeing. Splitting it into two tables joined by a key stores each fact once. "
            "That is 3NF: every non-key column depends on the key, the whole key and nothing "
            "but the key."
        ),
        "scene": scene([
            grid(9, 9, position=(0, -1.0, 0)),
            box((-2.4, 0, 0), size=(2.0, 1.8, 0.5), color=BAD, opacity=0.55),
            box((1.6, 0.45, 0), size=(1.6, 0.8, 0.5), color=ACCENT, opacity=0.8),
            box((1.6, -0.55, 0), size=(1.6, 1.0, 0.5), color=GOOD, opacity=0.8),
            pipe([(-1.35, 0, 0), (0.7, -0.55, 0)], color=WARM, radius=0.035),
            pipe([(-1.35, 0.45, 0), (0.7, 0.45, 0)], color=WARM, radius=0.035),
            *wire_box((-2.4, 0, 0), (2.0, 1.8, 0.5), color=BAD),
        ], labels=[label("employee(id, name, dept, manager)", (-2.4, 1.2, 0)),
                   label("department(id, name, manager)", (1.6, 1.15, 0)),
                   label("employee(id, name, dept_id)", (1.6, -1.25, 0)),
                   label("foreign key", (0.0, -0.9, 0))],
            distance=8.6, pitch=18, spin=0.0),
    },

    "indexes-query-performance": {
        "title": "A B-tree: the reason an index beats a scan",
        "caption": (
            "A sequential scan reads every row. A B-tree descent reads one node per level — "
            "three levels here, so three page reads instead of thousands of rows. Each node "
            "splits the keyspace, so one comparison discards most of the table. The trade is "
            "that every insert and update must also maintain the tree, which is why an index "
            "speeds up reads and slows down writes."
        ),
        "scene": scene([
            *[edge((0, 1.5, 0), p, color=DIM) for p in [(-1.8, 0.4, 0.8), (0, 0.4, 0), (1.8, 0.4, -0.8)]],
            *[edge((x, 0.4, z), (x + dx, -0.7, z + dz), color=(WARM if x == 0 and dx == 0 else DIM))
              for (x, z) in [(-1.8, 0.8), (0, 0), (1.8, -0.8)]
              for dx, dz in zip((-0.75, 0, 0.75), (0.75, 0, -0.75))],
            box((0, 1.5, 0), size=(1.1, 0.4, 0.5), color=ACCENT),
            *[box(p, size=(1.0, 0.38, 0.45), color=NEUTRAL) for p in [(-1.8, 0.4, 0.8), (0, 0.4, 0), (1.8, 0.4, -0.8)]],
            *[box((x, -0.7, z), size=(0.62, 0.3, 0.38), color=GOOD)
              for (x, z) in [(-2.55, 1.55), (-1.8, 0.8), (-1.05, 0.05), (-0.75, 0.75), (0, 0),
                             (0.75, -0.75), (1.05, -0.05), (1.8, -0.8), (2.55, -1.55)]],
        ], labels=[label("root", (0, 1.9, 0)), label("internal node", (0, 0.8, 0)),
                   label("leaf pages", (0, -1.15, 0)), label("3 reads, not 3000", (0, -1.5, 1.2))],
            distance=8.6, pitch=22, yaw=26, spin=0.1),
    },

    # --------------------------------------------- programming fundamentals --

    "variables-data-types-operators": {
        "title": "How many bytes, and what they mean",
        "caption": (
            "A type is a promise about how many bytes a variable occupies and how to read "
            "them. The same 32 bits mean 42 as an int, a very small number as a float and "
            "four characters as a char array. An int32 wraps at 2³¹ − 1; an int64 does not "
            "reach its limit in any real program. Choosing the type is choosing the range, "
            "the precision and the memory."
        ),
        "scene": scene([
            grid(9, 9, position=(0, -0.8, 0)),
            *[box((i * 0.55 - 1.925, 0.8, 0), size=(0.48, 0.42, 0.48), color=ACCENT) for i in range(8)],
            *[box((i * 0.55 - 0.825, 0.0, 0), size=(0.48, 0.42, 0.48), color=WARM) for i in range(4)],
            *[box((i * 0.55 - 0.55, -0.8, 0), size=(0.48, 0.42, 0.48), color=GOOD) for i in range(2)],
        ], labels=[label("int64 — 8 bytes", (0, 1.35, 0)), label("int32 / float — 4 bytes", (0, 0.55, 0)),
                   label("int16 — 2 bytes", (0, -0.25, 0)),
                   label("same bits, different meaning", (0, -1.2, 0))],
            distance=8.0, pitch=22, yaw=26, spin=0.0),
    },

    "control-flow-conditionals-loops": {
        "title": "Control flow as a graph you can walk",
        "caption": (
            "Every program is this shape: nodes that do work, branches that pick a path, and "
            "one edge that goes back. The backward edge is the loop, and it is drawn going "
            "away from you so the repetition is visible. Cyclomatic complexity is simply "
            "edges − nodes + 2, and it counts the independent paths through this graph — "
            "which is how many tests you need to cover it."
        ),
        "scene": scene([
            grid(8, 8, position=(0, -1.9, 0)),
            *[edge(a, b, color=DIM) for a, b in [
                ((0, 1.5, 0), (0, 0.6, 0)), ((0, 0.6, 0), (-1.3, -0.3, 0)), ((0, 0.6, 0), (1.3, -0.3, 0)),
                ((-1.3, -0.3, 0), (-1.3, -1.2, 0)), ((1.3, -0.3, 0), (1.3, -1.2, 0)),
                ((-1.3, -1.2, 0), (0, -1.8, 0)), ((1.3, -1.2, 0), (0, -1.8, 0)),
            ]],
            pipe([(1.3, -1.2, 0), (2.2, -0.6, 0.9), (1.6, 0.4, 1.2), (0.2, 0.6, 0.4)], color=WARM, radius=0.035),
            box((0, 1.5, 0), size=(0.9, 0.4, 0.4), color=ACCENT),
            box((0, 0.6, 0), size=(0.9, 0.5, 0.4), color=WARM, rotation=(0, 0, 45)),
            box((-1.3, -0.3, 0), size=(0.85, 0.4, 0.4), color=GOOD),
            box((1.3, -0.3, 0), size=(0.85, 0.4, 0.4), color=GOOD),
            box((-1.3, -1.2, 0), size=(0.85, 0.4, 0.4), color=NEUTRAL),
            box((1.3, -1.2, 0), size=(0.85, 0.4, 0.4), color=NEUTRAL),
            box((0, -1.8, 0), size=(0.9, 0.4, 0.4), color=BAD),
        ], labels=[label("start", (0, 1.9, 0)), label("if?", (0.75, 0.85, 0)),
                   label("then", (-1.9, -0.3, 0)), label("else", (1.9, -0.3, 0)),
                   label("loop back", (2.35, 0.0, 1.1)), label("join", (0, -2.2, 0))],
            distance=8.0, pitch=16, spin=0.12),
    },

    "boolean-algebra-karnaugh-maps": {
        "title": "A 4-variable Karnaugh map",
        "caption": (
            "The map is a truth table folded so that neighbours differ in exactly one "
            "variable. Any group of 1s whose size is a power of two drops the variables that "
            "change inside it, and what is left is the simplified term. Grey code ordering is "
            "the whole trick — it is why the columns read 00, 01, 11, 10 and not 00, 01, 10, "
            "11. Wrapping counts: the edges are adjacent."
        ),
        "scene": scene([
            grid(8, 8, position=(0, -0.4, 0)),
            *[box((c * 0.85 - 1.275, 0.06 + 0.05 * v, r * 0.85 - 1.275),
                  size=(0.72, 0.12 + 0.1 * v, 0.72),
                  color=WARM if v else NEUTRAL, opacity=1.0 if v else 0.6)
              for r, row in enumerate([[1, 1, 0, 1], [1, 1, 0, 0], [0, 0, 1, 1], [0, 0, 1, 0]])
              for c, v in enumerate(row)],
            *wire_box((-0.85, 0.35, -0.85), (1.75, 0.5, 1.75), color=GOOD),
        ], labels=[label("CD →", (0, -0.3, 1.9)), label("AB ↓", (-1.95, 0.3, 0)),
                   label("group of 4 ⇒ two variables drop out", (0, 1.0, -0.85)),
                   label("wraps at the edges", (1.9, 0.6, 1.6))],
            distance=7.4, pitch=40, yaw=35, spin=0.08),
    },

    # ---------------------------------------------------------------- math --

    "limits-continuity": {
        "title": "A surface, and what continuity means on it",
        "caption": (
            "A function of two variables is a surface. It is continuous at a point when the "
            "limit is the same along *every* path into that point, and equals the value there. "
            "A smooth sheet like this one is continuous everywhere; a surface with a tear or a "
            "spike is not. Checking two paths and agreeing is never a proof — the paths that "
            "break a limit are the ones you did not try."
        ),
        "scene": scene([
            {"mesh": "wave", "width": 4.0, "depth": 4.0, "segmentsX": 48, "segmentsZ": 48,
             "amplitude": 0.55, "frequency": 1.7, "color": ACCENT, "opacity": 0.92},
            grid(6, 6, position=(0, -1.0, 0)),
            sphere((0, 0.55, 0), 0.09, color=WARM),
            arrow((0, -1.0, 0), (0, 0.45, 0), color=DIM, shaft=0.02, head=0.16, radius=0.05),
            pipe([(-2.0, -0.9, -2.0), (0.0, 0.55, 0.0)], color=GOOD, radius=0.025),
            pipe([(2.0, -0.9, 2.0), (0.0, 0.55, 0.0)], color=GOOD, radius=0.025),
        ], labels=[label("z = f(x, y)", (1.9, 0.9, 0)), label("same limit along every path", (0, 1.0, 0)),
                   label("two paths shown — not a proof", (0, -0.8, 1.6))],
            distance=7.4, pitch=24, yaw=32, spin=0.12),
    },

    "convolution-lti-systems": {
        "title": "Convolution: flip, slide, multiply, add",
        "caption": (
            "The back surface is the input x(t); the front is the impulse response h(t), "
            "already flipped. Convolution slides one across the other, multiplies the overlap "
            "point by point and integrates — the output at time τ is the area of that overlap. "
            "Because an LTI system's response to anything is the sum of its responses to "
            "impulses, knowing h(t) tells you the response to every possible input."
        ),
        "scene": scene([
            grid(8, 8, position=(0, -0.6, 0)),
            {"mesh": "wave", "width": 4.0, "depth": 1.6, "segmentsX": 48, "segmentsZ": 12,
             "amplitude": 0.6, "frequency": 2.2, "color": ACCENT, "position": [0.0, 0.0, -1.1]},
            {"mesh": "wave", "width": 4.0, "depth": 1.6, "segmentsX": 48, "segmentsZ": 12,
             "amplitude": -0.6, "frequency": 2.2, "color": WARM, "position": [0.0, 0.0, 1.1]},
            arrow((-2.3, 0, 0), (2.3, 0, 0), color=DIM, shaft=0.02, head=0.18, radius=0.05),
        ], labels=[label("x(t) — the input", (0, 1.0, -1.1)), label("h(−t) — flipped", (0, 1.0, 1.1)),
                   label("slide → overlap → integrate", (0, -0.45, 0)), label("τ", (2.6, 0.2, 0))],
            distance=8.2, pitch=22, yaw=26, spin=0.1),
    },

    # -------------------------------------------------- software engineering --

    "software-process-models-testing": {
        "title": "The spiral model: each loop is a round of risk",
        "caption": (
            "Waterfall runs once and hopes. The spiral revisits the same four activities — "
            "plan, risk analysis, build, evaluate — once per revolution, and every revolution "
            "produces something you can show and a risk you have retired. The radius grows "
            "because each loop costs money, which is also its weakness: on a small project "
            "the risk analysis costs more than the code."
        ),
        "scene": scene([
            helix((0, 0, 0), radius=1.5, height=2.6, turns=3, color=ACCENT, tube=0.07),
            grid(7, 7, position=(0, -1.6, 0)),
            sphere((1.5, -1.3, 0), 0.16, color=WARM),
            sphere((-1.06, 0.0, 1.06), 0.16, color=GOOD),
            sphere((-0.6, 1.3, -1.33), 0.16, color=BAD),
            arrow((0, -1.6, 0), (0, 1.8, 0), color=DIM, shaft=0.02, head=0.18, radius=0.05),
        ], labels=[label("plan", (1.9, -1.3, 0)), label("risk analysis", (-1.4, 0.25, 1.4)),
                   label("build & evaluate", (-0.9, 1.55, -1.6)), label("cost / time →", (0, 2.1, 0)),
                   label("each loop retires one risk", (0, -1.95, 0))],
            distance=7.6, pitch=16, spin=0.25),
    },

    "encapsulation-inheritance-polymorphism": {
        "title": "An inheritance hierarchy, with the override visible",
        "caption": (
            "The arrows point from subclass to superclass: an `is-a` relationship. Each box "
            "hides its fields and exposes only methods — encapsulation. `Payment` declares "
            "`charge()`; the three subclasses each implement it differently, and the caller "
            "does not need to know which one it holds. That is polymorphism: one call site, "
            "three behaviours, chosen at run time."
        ),
        "scene": scene([
            *[edge((0, 1.3, 0), p, color=DIM) for p in [(-1.6, 0.0, 0.7), (0, 0.0, 0), (1.6, 0.0, -0.7)]],
            box((0, 1.3, 0), size=(1.5, 0.5, 0.6), color=WARM),
            *[box(p, size=(1.4, 0.45, 0.55), color=ACCENT)
              for p in [(-1.6, 0.0, 0.7), (0, 0.0, 0), (1.6, 0.0, -0.7)]],
            *[box((p[0], -0.85, p[2]), size=(1.4, 0.35, 0.55), color=GOOD, opacity=0.85)
              for p in [(-1.6, 0.0, 0.7), (0, 0.0, 0), (1.6, 0.0, -0.7)]],
        ], labels=[label("Payment  (abstract)", (0, 1.75, 0)), label("Card", (-1.6, 0.45, 0.7)),
                   label("UPI", (0, 0.45, 0)), label("Wallet", (1.6, 0.45, -0.7)),
                   label("charge() — overridden three ways", (0, -1.35, 0))],
            distance=8.0, pitch=18, spin=0.12),
    },

    "design-patterns": {
        "title": "Strategy: swapping the algorithm without touching the caller",
        "caption": (
            "The context on the left holds a reference to an interface, never to a concrete "
            "class. The three boxes on the right all satisfy it. At run time you hand the "
            "context whichever strategy fits, and the calling code is unchanged — that is the "
            "pattern in one sentence. Compare it with a chain of `if` statements: same "
            "behaviour, but every new algorithm edits the caller."
        ),
        "scene": scene([
            *[edge((-1.4, 0, 0), p, color=DIM) for p in [(1.4, 0.9, 0.8), (1.4, 0, 0), (1.4, -0.9, -0.8)]],
            box((-1.4, 0, 0), size=(1.5, 0.7, 0.8), color=WARM),
            box((1.4, 0, 0), size=(1.5, 0.4, 0.7), color=ACCENT, opacity=0.9),
            *[box((1.4, y, z), size=(1.5, 0.4, 0.7), color=GOOD)
              for y, z in [(0.9, 0.8), (-0.9, -0.8)]],
            arrow((1.4, 0.62, 0.8), (1.4, 0.32, 0.4), color=DIM, shaft=0.02, head=0.14, radius=0.05),
            arrow((1.4, -0.62, -0.8), (1.4, -0.32, -0.4), color=DIM, shaft=0.02, head=0.14, radius=0.05),
        ], labels=[label("Context", (-1.4, 0.55, 0)), label("«interface» Strategy", (1.4, 0.4, 0)),
                   label("ConcreteStrategyA", (1.4, 1.3, 0.8)), label("ConcreteStrategyB", (1.4, -1.3, -0.8)),
                   label("injected at run time", (0, -1.35, 0))],
            distance=8.0, pitch=18, spin=0.12),
    },
}

from seed_data.foundations import MODELS as _FOUNDATION_MODELS  # noqa: E402

MODELS_3D.update(_FOUNDATION_MODELS)

# Generate compact workflow models for the all-subject starter lessons. They
# share the same allowlisted scene constructors and validation as hand-authored
# scenes, while the caption remains specific to the topic and governing model.
from seed_data.subject_paths import generated_models as _generated_starter_models  # noqa: E402

MODELS_3D.update(_generated_starter_models())
