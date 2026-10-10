"""Breadth-first course starters for subjects without authored topic notes.

The existing topic files remain the hand-authored deep curriculum. This module
fills the catalogue gaps with a clearly scoped first lesson for every subject
that otherwise had no notes, then supplies diagrams, questions, and models from
the same source of truth. It deliberately does not claim that one lesson is a
complete degree syllabus.

New lessons are published so a learner can read them, but are marked
``needs_review`` in the editorial metadata. In particular, the Cyber Security
notes are public while still being visibly available for expert review.
"""
from __future__ import annotations

import re
from typing import Any

from backend.engineverse.diagrams import arrow as svg_arrow, box as svg_box, hotspot, label as svg_label
from seed_data import foundations, topics_core, topics_cse
from seed_data.catalog import SUBJECTS


# Subject rows added to catalog.SUBJECTS for the twenty branches that previously
# had no subject path at all. The catalog owns the actual records; this tuple is
# a guard/documentation list so tests can prove every empty branch is covered.
NEW_BRANCH_SUBJECTS = {
    "site-reliability-engineering", "blockchain-systems", "iot-systems-design",
    "robotics-kinematics", "mechatronic-system-design", "production-planning-control",
    "operations-research", "industrial-automation", "aerodynamics-flight-mechanics",
    "physical-metallurgy", "polymer-processing", "reservoir-engineering",
    "mine-planning-operations", "bioprocess-engineering", "biomedical-instrumentation",
    "food-process-technology", "agricultural-machinery-systems", "marine-propulsion-systems",
    "textile-fiber-fabric-engineering", "renewable-energy-systems",
}


def _f(name: str, latex: str, variables: tuple[tuple[str, str, str], ...], conditions: str) -> dict:
    return {
        "name": name,
        "latex": latex,
        "variables": [{"s": symbol, "n": meaning, "u": unit} for symbol, meaning, unit in variables],
        "conditions": conditions,
    }


def _e(problem: str, approach: str, solution: str, answer: str) -> dict:
    return {"problem": problem, "approach": approach, "solution": solution, "answer": answer}


def _lesson(
    title: str,
    focus: str,
    formula: dict,
    derivation: str,
    example: dict,
    applications: tuple[str, ...],
    pitfall: str,
    industry: str,
    *,
    tags: tuple[str, ...] = (),
    difficulty: str = "medium",
    minutes: int = 30,
    quiz: dict | None = None,
    diagram_steps: tuple[tuple[str, str], ...] | None = None,
) -> dict:
    return {
        "title": title,
        "focus": focus,
        "formula": formula,
        "derivation": derivation,
        "example": example,
        "applications": list(applications),
        "pitfall": pitfall,
        "industry": industry,
        "tags": list(tags),
        "difficulty": difficulty,
        "minutes": minutes,
        "quiz": quiz,
        "diagram_steps": diagram_steps,
    }


# (lesson title, focus, governing relation, derivation basis, worked check,
#  applications, common failure, industry practice).  Equations are chosen as
# an entry point, not as a substitute for the subject's standards or syllabus.
STARTERS: dict[str, dict] = {
    # ----------------------------- first-year foundations -----------------
    "engineering-mathematics-3": _lesson(
        "Fourier Series and Orthogonal Components",
        "A periodic signal can be represented as a weighted sum of mutually orthogonal sine and cosine components.",
        _f("Fourier coefficients", r"f(t)=\frac{a_0}{2}+\sum_{n=1}^{\infty}(a_n\cos n\omega_0t+b_n\sin n\omega_0t)",
           (("f(t)", "periodic function being represented", "function units"), ("a_n,b_n", "harmonic coefficients", "function units"), ("\omega_0", "fundamental angular frequency", "rad/s")),
           "The function is periodic and piecewise integrable over one period; convergence at a jump is to the midpoint."),
        "Multiply the series by one basis function and integrate over a full period. Orthogonality makes every cross-term zero; only the matching harmonic survives. Divide by the integral of its squared basis function to obtain that coefficient.",
        _e("For f(t)=sin(2t), identify the non-zero sine coefficient in its Fourier series.", "The signal already is a single sine harmonic at angular frequency 2 rad/s.", "Compare with the series basis: b_1=1 and every other coefficient is zero.", "b₁ = 1; all other coefficients are 0."),
        ("Harmonic analysis of periodic vibration and electrical waveforms.", "Solving heat and wave equations with periodic boundary conditions."),
        "Confusing the angular frequency nω₀ with the harmonic index n, or forgetting the a₀/2 convention.",
        "Signal analysts inspect the spectrum as well as the reconstructed waveform; truncation and windowing can create leakage and ringing near discontinuities.",
        tags=("fourier-series", "orthogonality", "harmonics"), difficulty="hard"),
    "engineering-graphics": _lesson(
        "Orthographic Projection and Scale",
        "Orthographic views use parallel projectors to show true dimensions on faces parallel to the projection plane.",
        _f("Representative fraction", r"RF=\frac{L_d}{L_a}",
           (("RF", "representative fraction", "dimensionless"), ("L_d", "length on drawing", "mm"), ("L_a", "actual length", "mm")),
           "Use the same length unit in numerator and denominator; a reduced drawing has RF below one."),
        "The scale is the ratio of corresponding lengths. If a 2.5 m object is drawn as 25 mm, first convert both to millimetres; 25/2500 reduces to 1/100.",
        _e("A 2.5 m shaft is drawn 25 mm long. Find the representative fraction.", "Convert 2.5 m to 2500 mm before forming the ratio.", "RF=25/2500=1/100.", "Scale 1:100."),
        ("Manufacturing drawings and assembly layouts.", "Reading front, top, and side views without perspective distortion."),
        "Mixing units or confusing a projected view with a pictorial view; hidden edges and view alignment must be checked.",
        "Production drawings use a declared scale, projection convention, units, and revision block; critical dimensions are stated explicitly rather than measured from a print.",
        tags=("projection", "drawing-scale", "orthographic"), difficulty="easy"),
    "engineering-drawing": _lesson(
        "Limits, Fits, and Tolerance",
        "A tolerance is the allowed interval around a nominal dimension that lets parts function and assemble reliably.",
        _f("Tolerance width", r"T=D_{max}-D_{min}",
           (("T", "total tolerance width", "mm"), ("D_{max}", "maximum permitted size", "mm"), ("D_{min}", "minimum permitted size", "mm")),
           "The limit dimensions must use the same datum and unit; fit also depends on the mating feature."),
        "Tolerance is the size of the permissible interval, not the nominal dimension. Subtract the lower limit from the upper limit; a smaller interval demands tighter process control.",
        _e("A pin is specified from 19.95 mm to 20.05 mm. What is its tolerance width?", "Subtract the lower limit from the upper limit.", "T=20.05-19.95=0.10 mm.", "0.10 mm total tolerance."),
        ("Interchangeable shafts and holes.", "Datum-based inspection and geometric dimensioning and tolerancing."),
        "Treating a tolerance as a target value or measuring a dimension from a scaled screenshot instead of the stated limits.",
        "Designers allocate a tolerance budget across a stack, specify datums and inspection methods, and tighten only dimensions that control function.",
        tags=("tolerancing", "fits", "gd-and-t"), difficulty="medium"),
    "basic-electronics": _lesson(
        "Diode Bias and Series Current",
        "A forward-biased diode conducts while a resistor limits current; the source voltage is shared by both.",
        _f("Series current with a constant-drop diode", r"I=\frac{V_s-V_D}{R}",
           (("I", "series current", "A"), ("V_s", "supply voltage", "V"), ("V_D", "diode forward drop", "V"), ("R", "series resistance", "Ω")),
           "The constant-drop model is an approximation for a conducting diode; check current, power, and polarity against the datasheet."),
        "Apply Kirchhoff's voltage law around the loop: the source rise equals the diode drop plus the resistor drop. Substitute V_R=IR and solve for I.",
        _e("A 5 V source drives a silicon diode modelled as 0.7 V in series with 1 kΩ. Find the current.", "Use KVL and convert 1 kΩ to 1000 Ω.", "I=(5-0.7)/1000=0.0043 A.", "4.3 mA."),
        ("Rectifiers, indicator LEDs, and input protection.", "Biasing transistor junctions and reading basic sensor interfaces."),
        "Using the diode drop without checking polarity, current rating, resistor power, or temperature limits.",
        "Engineers use the piecewise model for hand estimates, then verify worst-case current and thermal margin against the selected component datasheet.",
        tags=("diodes", "bias", "kvl"), difficulty="easy"),
    "communication-skills": _lesson(
        "Writing a Decision-Ready Engineering Brief",
        "A useful technical brief states the decision, supports it with traceable evidence, and makes the next action explicit.",
        _f("Brief completeness checklist (a rubric, not a physical law)", r"B=P\land C\land E\land A",
           (("P", "purpose and decision stated", "criterion"), ("C", "claim is clear", "criterion"), ("E", "evidence is traceable", "criterion"), ("A", "action and owner are explicit", "criterion")),
           "This is a pass/fail checklist for communication quality, not a numerical performance equation."),
        "The checklist follows the reader's decision path: establish purpose, make one claim, show the evidence that would change the decision, then name the action and owner. Removing a required element leaves the reader unable to act or verify.",
        _e("A test report contains measurements but no conclusion or requested decision. Is it ready for sign-off?", "Check all four elements of the brief checklist, not only the evidence.", "Evidence is present, but purpose/claim/action are incomplete; add the conclusion and explicit requested decision.", "No. A decision-ready brief needs purpose, claim, evidence, and action."),
        ("Design reviews and incident summaries.", "Clear handover notes, test reports, and stakeholder presentations."),
        "Leading with background detail and hiding the decision, or presenting a claim without units, source, date, or uncertainty.",
        "Teams preserve the calculation and raw evidence, then put the decision and recommendation first; review comments are resolved against a versioned document.",
        tags=("technical-writing", "decision-brief", "evidence"), difficulty="easy"),
    "environmental-studies": _lesson(
        "The IPAT Model for Environmental Impact",
        "The IPAT identity separates environmental impact into population, consumption per person, and impact per unit of consumption.",
        _f("IPAT identity", r"I=P\,A\,T",
           (("I", "environmental impact", "impact units"), ("P", "population", "people"), ("A", "affluence or consumption per person", "resource units/person"), ("T", "impact per resource unit", "impact/resource unit")),
           "IPAT is a bookkeeping identity; it does not by itself establish causality or predict rebound and distribution effects."),
        "Multiplying people by consumption per person gives total consumption; multiplying by impact per unit converts that activity into an impact estimate. The factors help locate where an intervention acts.",
        _e("A community has 1000 residents, uses 1.2 resource units per resident, and produces 0.4 impact units per resource unit. Estimate I.", "Multiply the three factors with units carried through.", "I=1000×1.2×0.4=480 impact units.", "480 impact units for the stated boundary and period."),
        ("Comparing energy and material footprints.", "Scoping sustainability interventions before a life-cycle assessment."),
        "Treating IPAT as proof that one factor caused a trend; the boundary, time period, and impact indicator must be stated.",
        "Sustainability teams use a defined functional unit and system boundary, then replace coarse factors with measured lifecycle inventories for decisions.",
        tags=("sustainability", "ipat", "environment"), difficulty="easy"),
    "workshop-practice": _lesson(
        "Cutting Speed in Turning Operations",
        "Cutting speed is the tangential speed of the work surface at the cutting edge and sets the spindle-speed relationship.",
        _f("Turning cutting speed", r"V_c=\frac{\pi D N}{1000}",
           (("V_c", "cutting speed", "m/min"), ("D", "workpiece diameter", "mm"), ("N", "spindle speed", "rev/min")),
           "The factor 1000 converts millimetres to metres; the selected speed must respect tool and material limits."),
        "One revolution moves the surface by its circumference πD. At N revolutions per minute the surface travels πDN millimetres per minute; divide by 1000 for metres per minute.",
        _e("A 50 mm workpiece rotates at 600 rpm. Find cutting speed.", "Use the workpiece diameter at the cutting point.", "V_c=π×50×600/1000≈94.2 m/min.", "About 94.2 m/min."),
        ("Selecting a safe lathe spindle speed.", "Comparing tool materials and finish requirements."),
        "Entering diameter in metres while retaining the 1000 conversion, or choosing speed without checking the tool manufacturer's limit.",
        "Machinists start from the tooling supplier's speed/feed window, confirm rigidity and coolant, then inspect chip form, finish, and tool wear.",
        tags=("machining", "cutting-speed", "lathe")),

    # ----------------------------- computing and information --------------
    "machine-learning": _lesson(
        "Gradient Descent and Loss Minimization",
        "Gradient descent updates model parameters opposite the loss gradient so a small step locally reduces error.",
        _f("Gradient-descent update", r"\theta_{k+1}=\theta_k-\eta\nabla J(\theta_k)",
           (("θ", "model parameters", "parameter units"), ("η", "learning rate", "step scale"), ("J", "objective or loss", "loss units")),
           "The gradient is evaluated at the current parameters; the learning rate must be chosen for the scale and curvature of the objective."),
        "For a differentiable loss, the gradient points toward steepest local increase. Moving a short distance in the negative direction decreases the loss to first order; an oversized step can overshoot.",
        _e("For J(w)=(w-3)^2, take w=0 and η=0.1. Find one gradient-descent update.", "The derivative is dJ/dw=2(w-3)=-6.", "w_new=0-0.1(-6)=0.6.", "w₁ = 0.6."),
        ("Fitting regression and classification models.", "Tuning learned parameters while monitoring validation loss."),
        "Treating a lower training loss as proof of generalization, or changing the learning rate without monitoring stability and validation data.",
        "Practitioners track train/validation curves, fix data leakage before tuning, log seeds and configurations, and compare against a simple baseline.",
        tags=("optimization", "gradient-descent", "loss"), difficulty="hard"),
    "deep-learning": _lesson(
        "Backpropagation and the Chain Rule",
        "Backpropagation reuses local derivatives through a computation graph to obtain the loss gradient for each parameter.",
        _f("Chain rule through one layer", r"\frac{\partial L}{\partial w}=\frac{\partial L}{\partial a}\frac{\partial a}{\partial z}\frac{\partial z}{\partial w}",
           (("L", "loss", "loss units"), ("a", "layer activation", "activation units"), ("z", "pre-activation", "pre-activation units"), ("w", "weight parameter", "parameter units")),
           "Each derivative is evaluated at the same forward-pass values; gradients are accumulated for shared parameters."),
        "If z=wx+b and a=ReLU(z), the chain rule multiplies the loss sensitivity at a by the activation derivative and by ∂z/∂w=x. The same local factors are reused layer by layer in reverse order.",
        _e("Let z=wx with x=2 and a=z (identity activation). If ∂L/∂a=3, find ∂L/∂w.", "Use ∂a/∂z=1 and ∂z/∂w=x=2.", "∂L/∂w=3×1×2=6.", "Gradient with respect to w is 6."),
        ("Training neural networks with many layers.", "Diagnosing vanishing/exploding gradients and choosing normalization or residual paths."),
        "Mixing gradient values with parameter updates, or forgetting that ReLU has zero derivative for negative pre-activation.",
        "Training pipelines log gradient norms and checkpoints, validate preprocessing parity, and evaluate robustness and calibration in addition to loss.",
        tags=("backpropagation", "chain-rule", "neural-networks"), difficulty="hard"),
    "data-science-foundations": _lesson(
        "Standardization and the Z-Score",
        "A z-score expresses how many standard deviations an observation lies from a reference mean.",
        _f("Standard score", r"z=\frac{x-\mu}{\sigma}",
           (("z", "standardized score", "dimensionless"), ("x", "observation", "data units"), ("μ", "reference mean", "data units"), ("σ", "reference standard deviation", "data units")),
           "The reference population must be appropriate and σ must be non-zero; standardization does not make a distribution normal."),
        "Subtracting the mean centers the values at zero; dividing by standard deviation rescales their spread to one. Translation and positive scaling preserve ordering.",
        _e("A measurement is 74, with reference mean 62 and standard deviation 6. Find its z-score.", "Subtract the mean, then divide by the standard deviation.", "z=(74-62)/6=2.", "z = 2 standard deviations above the mean."),
        ("Comparing features measured in different units.", "Flagging unusual observations relative to a training baseline."),
        "Computing mean and standard deviation on the full dataset before a train/test split, which leaks test information.",
        "Analytics teams fit preprocessing only on the training partition, version the fitted parameters, and monitor distribution drift after deployment.",
        tags=("statistics", "standardization", "data-leakage")),
    "cloud-computing-subject": _lesson(
        "Service Availability and Error Budgets",
        "Availability is the fraction of observed service time that meets the agreed service condition.",
        _f("Availability from repair and failure times", r"A=\frac{MTBF}{MTBF+MTTR}",
           (("A", "availability fraction", "dimensionless"), ("MTBF", "mean time between failures", "h"), ("MTTR", "mean time to restore", "h")),
           "This steady-state approximation assumes repairable failures and comparable measurement boundaries."),
        "Over a long observation period, uptime and downtime alternate. The uptime share is MTBF divided by the full cycle MTBF+MTTR.",
        _e("A service averages 1000 hours between failures and 1 hour to restore. Estimate availability.", "Substitute the mean times in the same unit.", "A=1000/(1000+1)=0.9990.", "About 99.90% availability."),
        ("Setting service-level objectives and error budgets.", "Comparing redundancy, repair, and deployment-risk investments."),
        "Quoting component availability as end-to-end service availability; dependencies, user-visible latency, and maintenance windows matter.",
        "SRE teams define a user-facing SLI, set an SLO, spend the error budget deliberately, and test restoration rather than relying on uptime claims.",
        tags=("availability", "sre", "slo")),
    "web-technologies": _lesson(
        "HTTP Requests, Responses, and Safe State Changes",
        "HTTP separates a request's method, target, headers, and optional body from a response's status, headers, and representation.",
        _f("HTTP message model (structured fields)", r"Request=(method,target,headers,body)",
           (("method", "requested operation", "token"), ("target", "resource URI", "URI"), ("headers", "metadata and negotiation", "field map"), ("body", "optional representation", "bytes")),
           "HTTP is stateless at the protocol layer; applications must protect state changes with authentication, authorization, and CSRF defenses."),
        "A request describes what the client wants and the response reports the result. A safe API treats the method as intent, validates the body, and checks identity and permission on the server.",
        _e("A browser submits a payment by GET with the amount in the URL. Is that a safe state-changing design?", "Separate safe retrieval from mutation and enforce authorization server-side.", "No. Use an authorized state-changing method, CSRF protection where cookies authenticate, and server-side validation/idempotency.", "No: a state change should not be triggered by a safe GET request."),
        ("Designing accessible browser/API contracts.", "Debugging status codes, caching, authentication, and content negotiation."),
        "Assuming that hiding a button protects an endpoint, or treating every 2xx response as proof that the requested state is correct.",
        "Web teams validate inputs at the boundary, apply least privilege, use parameterized persistence, make mutations idempotent where possible, and test failure responses.",
        tags=("http", "web-security", "api"), difficulty="easy"),

    # ----------------------------- mechanical and manufacturing ----------
    "manufacturing-processes": _lesson(
        "Machining Parameters: Speed, Feed, and Material Removal",
        "A machining process is controlled by tool/work speed, feed per revolution, depth of cut, and the material-tool pair.",
        _f("Turning cutting speed", r"V_c=\frac{\pi D N}{1000}",
           (("V_c", "cutting speed", "m/min"), ("D", "work diameter", "mm"), ("N", "spindle speed", "rev/min")),
           "The conversion assumes D in millimetres and N in revolutions per minute; material and tool limits govern the chosen value."),
        "Surface travel per revolution is the circumference πD. Multiplying by revolutions per minute and converting millimetres to metres gives cutting speed.",
        _e("A 40 mm bar is turned at 800 rpm. Estimate the cutting speed.", "Use Vc=πDN/1000.", "Vc=π×40×800/1000≈100.5 m/min.", "About 100.5 m/min."),
        ("Selecting a machining route for a part feature.", "Estimating cycle time and managing chip formation."),
        "Optimizing a single parameter without considering tool material, rigidity, coolant, chip load, or surface-finish requirements.",
        "Process plans record tooling, approved cutting windows, inspection points, and traceability; first-article checks verify the setup before batch production.",
        tags=("machining", "process-planning", "cutting-speed")),
    "machine-design": _lesson(
        "Factor of Safety and Allowable Stress",
        "A factor of safety compares a material or component limit with the design demand under stated failure criteria.",
        _f("Factor of safety", r"n=\frac{S_{limit}}{\sigma_{working}}", (("n", "factor of safety", "dimensionless"), ("S_limit", "chosen strength limit", "MPa"), ("σ_working", "calculated working stress", "MPa")), "Strength and stress must refer to the same failure mode, load case, and unit system."),
        "If allowable stress is defined as limit strength divided by n, rearranging gives n=limit strength/working stress. The design is acceptable only when the chosen code and failure-mode checks also pass.",
        _e("A component has a 250 MPa yield strength and 100 MPa working stress. Find the yield-based factor of safety.", "Compare like-for-like tensile stresses.", "n=250/100=2.5.", "Yield-based factor of safety = 2.5."),
        ("Sizing shafts, fasteners, gears, and machine frames.", "Reviewing static, fatigue, wear, and overload cases."),
        "Treating one safety factor as universal or ignoring fatigue, stress concentration, buckling, corrosion, and uncertainty.",
        "Design reviews identify the governing failure modes, document load combinations and standards, then verify fatigue life and maintainability separately.",
        tags=("machine-design", "factor-of-safety", "failure"), difficulty="hard"),
    "theory-of-machines": _lesson(
        "Gear Ratio and Rotational Speed",
        "For an ideal external gear pair, tooth-count ratio sets the inverse speed ratio and reverses rotation direction.",
        _f("Ideal gear speed ratio", r"\frac{\omega_1}{\omega_2}=\frac{Z_2}{Z_1}", (("ω₁,ω₂", "input and output angular speeds", "rad/s"), ("Z₁,Z₂", "input and output tooth counts", "teeth")), "Neglects losses and compliance; for an external mesh the output rotates opposite to the input."),
        "Equal pitch-line velocities at the contact point require ω₁r₁=ω₂r₂. Since pitch radius is proportional to tooth count, the speed ratio follows from Z₂/Z₁.",
        _e("A 20-tooth pinion drives a 60-tooth gear at 900 rpm. Find output speed and direction.", "Use n₂=n₁ Z₁/Z₂.", "n₂=900×20/60=300 rpm; the external gear turns in the opposite direction.", "300 rpm, opposite rotation."),
        ("Selecting gear trains and speed reducers.", "Checking mechanism motion and torque-speed trade-offs."),
        "Using the tooth ratio in the wrong direction or forgetting that an external gear pair reverses rotation.",
        "Designers check contact stress, lubrication, backlash, alignment, duty cycle, and noise in addition to the ideal kinematic ratio.",
        tags=("gears", "kinematics", "speed-ratio")),
    "ic-engines": _lesson(
        "Brake Thermal Efficiency of an Engine",
        "Brake thermal efficiency compares useful shaft power with the chemical energy rate entering in the fuel.",
        _f("Brake thermal efficiency", r"\eta_{bth}=\frac{P_b}{\dot m_f\,LHV}", (("η_bth", "brake thermal efficiency", "dimensionless"), ("P_b", "brake power", "W"), ("ṁ_f", "fuel mass flow rate", "kg/s"), ("LHV", "fuel lower heating value", "J/kg")), "Use consistent power and energy units and specify whether the fuel heating value is LHV or HHV."),
        "Fuel energy entering per second is mass flow multiplied by heating value. Dividing measured brake power by that input rate gives the fraction delivered at the shaft.",
        _e("An engine delivers 20 kW, burns 0.001 kg/s, and fuel LHV is 43 MJ/kg. Estimate efficiency.", "Fuel energy rate is 0.001×43,000,000=43,000 W.", "η=20,000/43,000≈0.465.", "About 46.5% brake thermal efficiency."),
        ("Comparing engine load points and fuels.", "Assessing efficiency and emissions trade-offs over a duty cycle."),
        "Mixing indicated and brake power, or comparing LHV for one fuel with HHV for another.",
        "Test cells report corrected power, fuel flow, ambient conditions, uncertainty, and emissions; a single peak-efficiency point is not a vehicle-cycle result.",
        tags=("engine-performance", "efficiency", "fuel")),
    "cad-cam": _lesson(
        "CAD/CAM: From Parametric Model to Verified Toolpath",
        "A parametric CAD model expresses design intent; CAM transforms a checked part model and setup into a machine-specific toolpath.",
        _f("Tolerance stack-up for independent dimensions", r"T_{RSS}=\sqrt{\sum_i T_i^2}", (("T_RSS", "root-sum-square stack estimate", "mm"), ("T_i", "individual tolerance contribution", "mm"), ("i", "dimension index", "dimensionless")), "RSS assumes independent, suitably distributed contributions; worst-case stack-up instead sums absolute limits."),
        "For independent centered variations, variances add. If each tolerance is treated as a standard contribution, taking the square root of the sum of squares estimates the combined spread.",
        _e("Two independent contributors have 0.10 mm and 0.20 mm tolerance contributions. Find their RSS stack estimate.", "Square, add, and take the square root.", "T_RSS=√(0.10²+0.20²)=√0.05≈0.224 mm.", "About 0.224 mm (RSS estimate)."),
        ("Checking assembly clearances and tolerance budgets.", "Generating and simulating CNC operations from a design model."),
        "Using RSS where worst-case guarantees are required, or posting a toolpath without verifying workholding, cutter, offsets, and machine limits.",
        "A controlled workflow checks model revision, stock, fixtures, tool library, simulation, postprocessor, and a safe prove-out on the machine.",
        tags=("cad", "cam", "toolpath", "tolerance")),
    "refrigeration-ac": _lesson(
        "Vapour-Compression Refrigeration COP",
        "The coefficient of performance measures heat removed from the cold space per unit work supplied to the cycle.",
        _f("Refrigerator coefficient of performance", r"COP_R=\frac{Q_L}{W_{in}}", (("COP_R", "refrigerator coefficient of performance", "dimensionless"), ("Q_L", "heat removed from cold space", "kW"), ("W_in", "compressor work input", "kW")), "Use rates over the same interval; COP can exceed one because it is a heat-pump ratio, not an efficiency bounded by one."),
        "The energy balance for a cycle is Q_H=Q_L+W_in. COP_R asks how much desired cooling Q_L is delivered for each unit of work input.",
        _e("A unit removes 12 kW of heat while the compressor uses 3 kW. Find COP_R.", "Divide cooling capacity by work input.", "COP_R=12/3=4.", "COP_R = 4."),
        ("Comparing refrigeration cycles and equipment.", "Sizing cooling plant and evaluating seasonal performance."),
        "Calling COP a thermodynamic efficiency or comparing values without matching rating conditions and part-load behavior.",
        "HVAC engineers use certified ratings, refrigerant and ambient conditions, controls, defrost, and measured seasonal load when selecting equipment.",
        tags=("refrigeration", "cop", "heat-pump")),

    # ----------------------------- electronics and electrical -------------
    "electronic-devices": _lesson(
        "Diode I–V Behaviour and Load-Line Checks",
        "A diode's current changes nonlinearly with junction voltage; a series resistor and source establish the operating point.",
        _f("Series load-line approximation", r"I_D\approx\frac{V_S-V_D}{R}", (("I_D", "diode current", "A"), ("V_S", "supply voltage", "V"), ("V_D", "forward drop", "V"), ("R", "series resistance", "Ω")), "The constant-drop approximation is a hand-analysis model; temperature, dynamic resistance, and rated power still matter."),
        "Kirchhoff's voltage law gives V_S=V_D+IR. The resistor's I–V line intersects the diode's I–V curve at the operating point.",
        _e("A 5 V source, a 0.7 V diode model, and a 1 kΩ resistor are in series. Find the approximate current.", "Subtract the diode drop, then divide by resistance.", "I=(5-0.7)/1000=4.3 mA.", "4.3 mA."),
        ("Rectifiers, clamps, and transistor junction bias.", "Checking component operating points and dissipation."),
        "Assuming a fixed forward drop at every current and temperature, or omitting reverse-voltage and power checks.",
        "Designers compare the load-line estimate with the datasheet model and verify worst-case current, thermal rise, and transient stress.",
        tags=("diode", "iv-curve", "bias")),
    "communication-systems": _lesson(
        "Shannon Capacity and the SNR Limit",
        "Channel capacity bounds the error-free information rate for an ideal band-limited channel with additive white Gaussian noise.",
        _f("Shannon–Hartley capacity", r"C=B\log_2(1+S/N)", (("C", "capacity", "bit/s"), ("B", "bandwidth", "Hz"), ("S/N", "signal-to-noise power ratio", "dimensionless")), "S and N are powers measured over the same bandwidth; the result is an ideal limit, not a guaranteed application throughput."),
        "Increasing bandwidth creates more independent signal dimensions; improving SNR makes each dimension carry more information. The logarithm reflects diminishing returns from power alone.",
        _e("A 1 MHz channel has SNR 15 (linear). Find its Shannon capacity.", "Use log₂(1+15)=4 bits/s/Hz.", "C=10⁶×4=4×10⁶ bit/s.", "4 Mbit/s ideal capacity limit."),
        ("Comparing modulation and coding choices.", "Understanding why a noisy radio link needs coding and margin."),
        "Putting SNR in decibels directly into the logarithm instead of converting to a linear power ratio.",
        "Radio design budgets path loss, interference, fading, coding overhead, regulatory masks, and implementation margin; Shannon is an upper bound.",
        tags=("shannon-capacity", "snr", "information-theory"), difficulty="hard"),
    "microprocessors": _lesson(
        "Address Width and Memory-Mapped Peripherals",
        "An n-bit byte-addressed address field can name at most 2ⁿ distinct byte locations before reserved regions and mapping are considered.",
        _f("Address-space size", r"N_{bytes}=2^n", (("N_bytes", "number of byte addresses", "bytes"), ("n", "address width", "bits")), "This is the raw address space; implemented RAM, peripheral windows, and privilege mappings may be much smaller."),
        "Each of n independent bit positions has two states, so the number of bit patterns is 2×2×…×2=2ⁿ. A byte-addressed machine assigns one such pattern to each byte location.",
        _e("A microcontroller has a 16-bit byte address. What is the raw address-space size?", "Compute 2¹⁶.", "2¹⁶=65,536 bytes=64 KiB.", "64 KiB raw byte-address space."),
        ("Sizing pointers and linker regions.", "Mapping peripheral registers and memory protection windows."),
        "Equating raw address-space size with installed RAM, or accessing a peripheral without checking alignment and register semantics.",
        "Firmware teams use the reference manual and linker map, define register widths explicitly, and review interrupt and concurrency behavior.",
        tags=("microcontroller", "address-space", "memory-map")),
    "analog-circuits": _lesson(
        "Non-Inverting Op-Amp Gain",
        "With negative feedback and an ideal op amp, the non-inverting closed-loop gain is set by the resistor ratio.",
        _f("Non-inverting amplifier gain", r"A_v=1+\frac{R_f}{R_g}", (("A_v", "voltage gain", "V/V"), ("R_f", "feedback resistance", "Ω"), ("R_g", "resistance to reference", "Ω")), "The ideal relation requires negative feedback, linear operation, and adequate bandwidth and output swing."),
        "In linear negative feedback the input terminals are approximately at the same voltage. The divider at the inverting input is V−=Vout·Rg/(Rg+Rf); setting V−≈Vin and rearranging gives the gain.",
        _e("An op amp has Rf=9 kΩ and Rg=1 kΩ. Find the ideal non-inverting gain.", "Substitute the resistor ratio.", "A_v=1+9/1=10.", "Gain = 10 V/V."),
        ("Sensor conditioning and active filters.", "Building a high-input-impedance amplifier stage."),
        "Ignoring supply rails, input common-mode range, bandwidth, slew rate, or loading when using the ideal gain.",
        "Analog designers verify the actual op-amp datasheet over supply, temperature, gain-bandwidth, noise, and load before layout.",
        tags=("op-amp", "feedback", "gain")),
    "control-systems-subject": _lesson(
        "First-Order Step Response and Time Constant",
        "A stable first-order system reaches about 63.2% of a step change after one time constant.",
        _f("Unit-step response", r"y(t)=1-e^{-t/\tau}", (("y(t)", "normalized output response", "dimensionless"), ("t", "elapsed time", "s"), ("τ", "time constant", "s")), "For a unit-gain stable first-order system with zero initial condition and a unit step input."),
        "The differential equation τ dy/dt+y=1 has solution y=1−e^(−t/τ) after applying y(0)=0. At t=τ, the exponential is e⁻¹, leaving 1−e⁻¹≈0.632.",
        _e("A first-order sensor has τ=2 s. What fraction of its final step value has it reached at t=2 s?", "Set t/τ=1 in the normalized response.", "y=1-e⁻¹≈0.632.", "About 63.2%."),
        ("Interpreting sensor lag and process response.", "Choosing controller gains and settling-time targets."),
        "Calling 63.2% a settling value or applying the first-order model to a system with dominant oscillatory poles.",
        "Control engineers identify the plant, validate the model against measured transients, and check stability and actuator limits before tuning.",
        tags=("control", "step-response", "time-constant"), difficulty="hard"),
    "dsp": _lesson(
        "Sampling and the Nyquist Criterion",
        "A band-limited signal needs a sampling rate greater than twice its highest frequency to avoid ideal aliasing.",
        _f("Nyquist sampling condition", r"f_s>2f_{max}", (("f_s", "sampling frequency", "Hz"), ("f_max", "highest signal frequency", "Hz")), "The signal must be band-limited before sampling; a practical design includes anti-alias filtering and transition-band margin."),
        "Sampling creates spectral replicas separated by f_s. If f_s is not greater than twice the signal bandwidth, replicas overlap and distinct frequencies become indistinguishable.",
        _e("A signal contains useful content up to 8 kHz. What is the ideal minimum sampling rate, strictly above Nyquist?", "Twice 8 kHz is the boundary; choose a rate above it.", "f_s>16 kHz; a 20 kHz rate leaves practical margin before filter design.", "Greater than 16 kHz; 20 kHz is one possible choice."),
        ("Selecting audio and instrumentation ADC rates.", "Designing anti-alias filters before digital processing."),
        "Sampling at exactly twice the highest frequency without accounting for phase, bandwidth, or a realizable anti-alias filter.",
        "DSP chains specify the analog passband, stopband attenuation, ADC rate, clock jitter, and resampling stages as one system budget.",
        tags=("sampling", "nyquist", "aliasing"), difficulty="hard"),
    "vlsi-design-subject": _lesson(
        "Dynamic Power in CMOS Logic",
        "CMOS dynamic power grows with switched capacitance, the square of supply voltage, clock frequency, and activity.",
        _f("CMOS dynamic power", r"P_{dyn}=\alpha C V^2 f", (("P_dyn", "dynamic power", "W"), ("α", "switching activity factor", "dimensionless"), ("C", "effective switched capacitance", "F"), ("V", "supply voltage", "V"), ("f", "clock frequency", "Hz")), "This estimates capacitive switching power; leakage, short-circuit power, and data-dependent activity also contribute."),
        "Charging a capacitance costs energy proportional to CV². The number of transitions per second scales with αf, giving average switching power proportional to αCV²f.",
        _e("A block has α=0.25, C=20 pF, V=1 V, and f=100 MHz. Estimate dynamic power.", "Substitute SI units: 20 pF=20×10⁻¹² F and 100 MHz=10⁸ Hz.", "P=0.25×20×10⁻¹²×1²×10⁸=0.0005 W.", "0.5 mW dynamic power."),
        ("Comparing voltage/frequency operating points.", "Reasoning about clock gating, activity, and power budgets."),
        "Reducing frequency but not voltage and expecting a linear power reduction, or omitting leakage at low activity.",
        "Physical-design teams use activity-aware power analysis and measured workloads; clock gating and voltage scaling are checked against timing and reliability.",
        tags=("cmos", "dynamic-power", "low-power"), difficulty="hard"),
    "electrical-machines-2": _lesson(
        "Induction-Motor Slip and Rotor Speed",
        "Slip measures the fractional difference between synchronous field speed and rotor speed in an induction motor.",
        _f("Slip", r"s=\frac{N_s-N_r}{N_s}", (("s", "slip fraction", "dimensionless"), ("N_s", "synchronous speed", "rpm"), ("N_r", "rotor speed", "rpm")), "For motoring, rotor speed is below synchronous speed; frequency, pole count, and supply frequency set N_s."),
        "The relative speed between rotating field and rotor is N_s−N_r. Dividing by field speed normalizes it, so synchronous speed has zero slip and standstill has unit slip.",
        _e("A 4-pole motor on 50 Hz runs at 1440 rpm. Find slip.", "Synchronous speed is 120f/P=1500 rpm; compare to rotor speed.", "s=(1500-1440)/1500=0.04.", "4% slip."),
        ("Estimating induction-motor load and rotor frequency.", "Interpreting nameplate speed and torque behavior."),
        "Using line frequency without pole count to find synchronous speed, or reporting 4% as 4 instead of 0.04 in equations.",
        "Motor commissioning checks phase sequence, current balance, thermal class, overload settings, and actual loaded speed rather than relying on no-load values.",
        tags=("induction-motor", "slip", "synchronous-speed")),
    "power-electronics": _lesson(
        "Ideal Buck Converter Duty Ratio",
        "In continuous-conduction ideal operation, a buck converter's average output voltage is duty ratio times input voltage.",
        _f("Buck converter conversion ratio", r"V_o=D V_{in}", (("V_o", "average output voltage", "V"), ("D", "switch on-time fraction", "dimensionless"), ("V_in", "input voltage", "V")), "Assumes ideal switches, periodic steady state, continuous inductor current, and negligible ripple for the average relation."),
        "During on-time the inductor sees V_in−V_o; during off-time it sees −V_o. Volt-second balance over one period gives D(V_in−V_o)+(1−D)(−V_o)=0, hence V_o=DV_in.",
        _e("An ideal buck converter has V_in=24 V and D=0.25. Find average V_o.", "Multiply input by duty ratio.", "V_o=0.25×24=6 V.", "6 V ideal average output."),
        ("Point-of-load DC regulators.", "Selecting switch, inductor, and control ranges."),
        "Applying the ideal continuous-current ratio at light load or ignoring switch drops, ripple, current limits, and feedback stability.",
        "Power designers verify conduction mode across load, worst-case voltage/current/temperature, EMI, transient response, and protection behavior.",
        tags=("buck-converter", "duty-cycle", "dc-dc"), difficulty="hard"),
    "measurements-instrumentation": _lesson(
        "Calibration Error and Measurement Uncertainty",
        "Measurement error compares a reading with a reference; uncertainty describes the range of values reasonably attributable to the measurand.",
        _f("Relative error", r"e_r=\frac{x_m-x_r}{x_r}", (("e_r", "relative error", "dimensionless"), ("x_m", "measured value", "unit of measurand"), ("x_r", "reference value", "unit of measurand")), "The reference must be valid and non-zero; uncertainty and traceability should accompany a reported result."),
        "Subtracting the reference gives signed error. Dividing by the reference expresses the difference as a fraction, which can then be reported as a percentage.",
        _e("A meter reads 10.2 V for a 10.0 V reference. Find signed relative error.", "Use (measured−reference)/reference.", "e_r=(10.2-10.0)/10.0=0.02.", "+2% relative error."),
        ("Checking sensor chains and laboratory instruments.", "Reporting calibrated measurements with traceability."),
        "Calling the observed error the complete uncertainty, or ignoring resolution, repeatability, drift, and reference uncertainty.",
        "Metrology practice records calibration date, reference traceability, environment, range, and uncertainty; out-of-tolerance instruments trigger impact review.",
        tags=("calibration", "measurement-error", "uncertainty")),

    # ----------------------------- civil and infrastructure ---------------
    "structural-analysis": _lesson(
        "Equilibrium and Structural Determinacy",
        "A planar structure at rest must satisfy force and moment equilibrium; equilibrium alone does not guarantee stability or code adequacy.",
        _f("Planar rigid-body equilibrium", r"\sum F_x=0,\quad\sum F_y=0,\quad\sum M=0", (("F_x,F_y", "force components", "N"), ("M", "moment about a chosen point", "N·m")), "Apply to a clearly isolated free body with correct support reactions and sign convention."),
        "Newton's second law with zero translational and angular acceleration reduces to ΣF=0 and ΣM=0. The equations are independent only when the chosen reactions and geometry permit it.",
        _e("A simply supported beam carries a centered 10 kN point load. Find the two vertical reactions.", "By symmetry R_A=R_B; vertical equilibrium gives R_A+R_B=10 kN.", "Each reaction is 5 kN upward; moments about either support confirm the result.", "R_A=R_B=5 kN."),
        ("Finding support reactions before drawing shear and moment diagrams.", "Checking load paths and boundary conditions in structural models."),
        "Assuming symmetry without symmetric geometry/loading, or treating equilibrium as proof against buckling, deflection, or instability.",
        "Structural teams validate boundary conditions and load combinations, compare hand checks with analysis software, and document the governing code checks.",
        tags=("equilibrium", "reactions", "structures"), difficulty="medium"),
    "rc-design": _lesson(
        "Flexural Resistance of a Reinforced-Concrete Beam",
        "A singly reinforced beam resists bending through a compression block in concrete and tension carried mainly by steel reinforcement.",
        _f("Lever-arm moment resistance (simplified section check)", r"M_u=Tz\approx0.87 f_y A_s z", (("M_u", "ultimate moment resistance", "N·m"), ("f_y", "design yield strength of steel", "Pa"), ("A_s", "tension steel area", "m²"), ("z", "internal lever arm", "m")), "This is a simplified force-couple estimate; code stress blocks, neutral-axis limits, detailing, shear, and durability checks are also required."),
        "The internal compression and tension forces are approximately equal in a section without significant axial force. Their couple is T times lever arm z; the code design steel force is approximated here by 0.87 f_y A_s.",
        _e("Use f_y=415 MPa, A_s=1000 mm², and z=300 mm. Estimate the simplified moment resistance.", "Convert A_s=0.001 m² and f_y=415×10⁶ Pa.", "M≈0.87×415×10⁶×0.001×0.300=108,315 N·m.", "About 108.3 kN·m, before the remaining code checks."),
        ("Preliminary flexural checks for beams and slabs.", "Understanding reinforcement force and lever-arm behavior."),
        "Treating this force-couple estimate as a complete design; neutral-axis ductility, shear, anchorage, serviceability, and code detailing still govern.",
        "A licensed design workflow checks the applicable concrete code, drawings, reinforcement congestion, cover, durability exposure, and construction tolerances.",
        tags=("reinforced-concrete", "flexure", "design"), difficulty="hard"),
    "hydraulics": _lesson(
        "Pump Hydraulic Power and Head",
        "Hydraulic power is the rate of potential energy delivered to a fluid flow; shaft input is larger by the inverse of pump efficiency.",
        _f("Hydraulic power", r"P_h=\rho g Q H", (("P_h", "power delivered to fluid", "W"), ("ρ", "fluid density", "kg/m³"), ("g", "gravitational acceleration", "m/s²"), ("Q", "volume flow rate", "m³/s"), ("H", "total head", "m")), "Use total dynamic head and a consistent flow unit; actual shaft power is P_h/η."),
        "Each kilogram gains specific potential energy gH. Multiplying by density and volume flow gives mass flow per second times energy per mass: ρQgH.",
        _e("Water flows at 0.05 m³/s against 20 m head. Estimate hydraulic power.", "Use ρ=1000 kg/m³ and g=9.81 m/s².", "P_h=1000×9.81×0.05×20=9810 W.", "9.81 kW to the water; shaft input is higher."),
        ("Sizing pumps and estimating energy use.", "Checking irrigation, water-supply, and turbine systems."),
        "Using static elevation alone when pipe losses and pressure requirements add head, or confusing hydraulic with electrical input power.",
        "Pump selection uses system curves, efficiency maps, NPSH margin, operating range, and measured duty; throttling losses are reviewed against variable-speed control.",
        tags=("pump", "hydraulic-power", "head")),
    "transportation-engineering-subject": _lesson(
        "Stopping Sight Distance",
        "Stopping sight distance combines distance traveled during perception-reaction time with braking distance under a stated road condition.",
        _f("Level-road stopping distance approximation", r"SSD=0.278 V t+\frac{V^2}{254 f}", (("SSD", "stopping sight distance", "m"), ("V", "speed", "km/h"), ("t", "perception-reaction time", "s"), ("f", "longitudinal friction factor", "dimensionless")), "The constants use V in km/h on a level road; grade, wet surface, design standard, and adopted reaction time may change the calculation."),
        "Reaction distance is speed in metres per second multiplied by time. Braking distance follows from work-energy with friction as the resisting force; the formula constants perform the unit conversion.",
        _e("At 60 km/h, t=2.5 s, and f=0.35, estimate level-road SSD.", "Compute reaction distance 0.278×60×2.5 and braking distance 60²/(254×0.35).", "41.7+40.6≈82.3 m.", "About 82 m under the stated assumptions."),
        ("Checking highway sight lines at curves and intersections.", "Relating speed, friction, grade, and safety margins."),
        "Using a dry-road friction factor for all conditions or omitting grade, vehicle mix, and governing design-standard assumptions.",
        "Road designers apply the relevant jurisdictional standard, terrain and grade data, visibility envelope, and conservative operating speed.",
        tags=("sight-distance", "highway-design", "safety"), difficulty="hard"),
    "environmental-engineering-subject": _lesson(
        "Wastewater Treatment Removal Efficiency",
        "Removal efficiency compares influent and effluent concentration for one stated contaminant and treatment boundary.",
        _f("Concentration removal", r"\eta=\frac{C_{in}-C_{out}}{C_{in}}\times100\%", (("η", "removal efficiency", "%"), ("C_in", "influent concentration", "mg/L"), ("C_out", "effluent concentration", "mg/L")), "A concentration ratio is not a mass-removal rate when flow changes; compare samples and boundaries consistently."),
        "Removed concentration is C_in−C_out. Dividing by influent concentration normalizes the reduction, and multiplying by 100 expresses it as percent.",
        _e("Influent BOD is 200 mg/L and effluent is 30 mg/L. Find concentration removal efficiency.", "Use the same concentration units in both terms.", "η=(200-30)/200×100%=85%.", "85% concentration removal."),
        ("Comparing treatment stages and process stability.", "Checking permit targets and plant operation trends."),
        "Comparing one grab sample with an unpaired sample or reporting concentration removal as total pollutant mass removed.",
        "Operators trend flow-weighted samples, hydraulic loading, process conditions, and permit limits; a compliance result is not inferred from a single idealized example.",
        tags=("wastewater", "bod", "removal-efficiency")),
    "estimating-costing": _lesson(
        "Quantity Take-Off and Rate Analysis",
        "A measured work item is costed by multiplying its verified quantity by an applicable unit rate, then adding explicit indirect costs and taxes.",
        _f("Measured work-item cost", r"C=Q\,r", (("C", "direct item cost", "currency"), ("Q", "measured quantity", "item unit"), ("r", "unit rate", "currency/item unit")), "Quantities must follow the measurement standard and rate basis, date, location, scope, and exclusions must match."),
        "A unit rate is the cost per unit of work. Repeating that unit cost Q times gives Qr; summing across bill items gives the direct measured-work estimate.",
        _e("A bill contains 12 m³ of concrete at ₹2500/m³. Find the direct item cost.", "Multiply quantity by the quoted rate, keeping cubic metres consistent.", "C=12×2500=₹30,000.", "₹30,000 before separately stated overheads and taxes."),
        ("Preparing a bill of quantities.", "Comparing tender rates and tracking measured progress."),
        "Comparing rates with different inclusions or taking off a quantity without dimensions, units, location, and measurement rules.",
        "Estimators version drawings, retain take-off references, state price date and assumptions, and separate direct work, preliminaries, contingency, and tax.",
        tags=("quantity-takeoff", "rate-analysis", "cost-estimate")),

    # ----------------------------- chemical and materials -----------------
    "chemical-thermodynamics": _lesson(
        "Gibbs Free Energy and Reaction Direction",
        "At constant temperature and pressure, Gibbs free-energy change indicates the thermodynamic driving direction for a process.",
        _f("Gibbs relation", r"\Delta G=\Delta H-T\Delta S", (("ΔG", "Gibbs free-energy change", "kJ/mol"), ("ΔH", "enthalpy change", "kJ/mol"), ("T", "absolute temperature", "K"), ("ΔS", "entropy change", "kJ/(mol·K)")), "Use absolute temperature and consistent energy units; ΔG<0 indicates thermodynamic favorability, not a fast rate."),
        "The definition G=H−TS gives ΔG=ΔH−Δ(TS). At constant temperature, this becomes ΔG=ΔH−TΔS.",
        _e("At 298 K, ΔH=−20 kJ/mol and ΔS=−50 J/(mol·K). Find ΔG.", "Convert ΔS to −0.050 kJ/(mol·K) before multiplying.", "ΔG=−20−298(−0.050)=−5.1 kJ/mol.", "ΔG = −5.1 kJ/mol under the stated conditions."),
        ("Checking equilibrium direction and phase behavior.", "Assessing temperature effects on chemical processes."),
        "Mixing joules and kilojoules, or equating negative ΔG with a fast reaction or a safe operating condition.",
        "Process engineers combine thermodynamic feasibility with kinetics, phase equilibrium, heat removal, and validated property data before sizing equipment.",
        tags=("gibbs-free-energy", "equilibrium", "thermodynamics"), difficulty="hard"),
    "fluid-flow-operations": _lesson(
        "Reynolds Number and Flow Regime",
        "The Reynolds number compares inertial and viscous effects and helps identify the flow regime in a specified geometry.",
        _f("Pipe Reynolds number", r"Re=\frac{\rho v D}{\mu}", (("Re", "Reynolds number", "dimensionless"), ("ρ", "fluid density", "kg/m³"), ("v", "mean velocity", "m/s"), ("D", "pipe diameter", "m"), ("μ", "dynamic viscosity", "Pa·s")), "Use consistent SI units and a characteristic length appropriate to the geometry; transition is not a universal sharp boundary."),
        "Inertial force scales with ρv² while viscous force scales with μv/D. Their ratio reduces to ρvD/μ, a dimensionless similarity parameter.",
        _e("Water has ρ=1000 kg/m³, v=1 m/s, D=0.05 m, and μ=0.001 Pa·s. Find Re.", "Substitute SI values.", "Re=1000×1×0.05/0.001=50,000.", "Re = 50,000; pipe flow is turbulent under typical conditions."),
        ("Estimating pipe friction and pressure loss.", "Scaling flow tests and selecting pump operating points."),
        "Using kinematic viscosity in a formula that expects dynamic viscosity, or applying one transition threshold to every geometry and disturbance.",
        "Process teams pair Reynolds number with roughness, fittings, flow development, non-Newtonian behavior, and validated correlations.",
        tags=("reynolds-number", "pipe-flow", "fluid-mechanics")),
    "heat-transfer-operations": _lesson(
        "Heat Exchanger Duty and Log-Mean Temperature Difference",
        "For a steady exchanger with an approximately constant overall coefficient, duty is UA times the log-mean temperature difference.",
        _f("Exchanger heat duty", r"Q=U A\Delta T_{lm}", (("Q", "heat-transfer rate", "W"), ("U", "overall heat-transfer coefficient", "W/(m²·K)"), ("A", "heat-transfer area", "m²"), ("ΔT_lm", "log-mean temperature difference", "K")), "Use terminal temperature differences for the actual flow arrangement and a correction factor where the ideal counterflow relation does not apply."),
        "The local heat rate is dQ=UΔT dA. Integrating along the exchanger while both streams change temperature gives the logarithmic mean driving difference.",
        _e("An exchanger has U=500 W/(m²·K), A=10 m², and corrected ΔT_lm=20 K. Find duty.", "Multiply U, area, and corrected mean difference.", "Q=500×10×20=100,000 W.", "100 kW."),
        ("Preliminary heat-exchanger sizing.", "Checking fouling, duty, and utility loads."),
        "Using arithmetic mean temperature difference where the stream temperatures vary substantially, or forgetting flow-arrangement correction and fouling.",
        "Design teams check phase change, pressure drop, fouling factors, materials compatibility, cleanability, and operating turndown against measured process data.",
        tags=("heat-exchanger", "lmtd", "heat-duty"), difficulty="hard"),
    "mass-transfer": _lesson(
        "Fick's Law and Diffusive Flux",
        "For one-dimensional molecular diffusion in a simple medium, flux moves down the concentration gradient.",
        _f("Fick's first law", r"J_A=-D_{AB}\frac{dC_A}{dx}", (("J_A", "molar diffusive flux of A", "mol/(m²·s)"), ("D_AB", "diffusivity of A in B", "m²/s"), ("C_A", "concentration of A", "mol/m³"), ("x", "distance coordinate", "m")), "Applies to a defined diffusive frame and constant diffusivity; convection and multicomponent effects may also matter."),
        "A positive concentration gradient points toward increasing concentration, while diffusion goes the other way. The negative sign encodes that direction; D sets the flux magnitude.",
        _e("D=2×10⁻⁹ m²/s and concentration rises by 500 mol/m⁴ along +x. Find J_A.", "Assume the stated gradient is constant and apply the negative sign.", "J_A=−2×10⁻⁹×500=−1×10⁻⁶ mol/(m²·s).", "−1×10⁻⁶ mol/(m²·s), toward decreasing concentration."),
        ("Sizing absorption, extraction, and membrane transfer.", "Understanding boundary-layer resistance and drying."),
        "Dropping the negative sign or using a diffusivity from the wrong temperature, phase, or composition.",
        "Scale-up models distinguish film, interfacial, and bulk resistance and are checked against equilibrium data and operating measurements.",
        tags=("fick-law", "diffusion", "mass-transfer"), difficulty="hard"),
    "reaction-engineering": _lesson(
        "First-Order Batch-Reactor Conversion",
        "For a constant-volume first-order batch reaction, concentration decays exponentially with elapsed reaction time.",
        _f("First-order conversion", r"X=1-e^{-kt}", (("X", "fractional conversion", "dimensionless"), ("k", "first-order rate constant", "time⁻¹"), ("t", "reaction time", "time")), "Assumes a single irreversible first-order reaction, constant volume, and constant temperature so k is constant."),
        "The batch balance is dC/dt=−kC. Separating variables and integrating from C₀ at t=0 gives C/C₀=e^(−kt); conversion X=1−C/C₀.",
        _e("A first-order reaction has k=0.2 min⁻¹. Estimate conversion after 5 min.", "Compute kt=1 and use the exponential relation.", "X=1−e⁻¹≈0.632.", "About 63.2% conversion."),
        ("Estimating batch residence time.", "Comparing kinetic data and reactor operating conditions."),
        "Using k from a different temperature or treating conversion as a measure of selectivity when parallel reactions exist.",
        "Reaction engineers validate kinetic models over the operating window, account for heat/mass transfer limits, and check hazards before scale-up.",
        tags=("first-order", "batch-reactor", "conversion"), difficulty="hard"),
    "materials-science": _lesson(
        "Hall–Petch Strengthening and Grain Size",
        "For many polycrystalline metals over a useful grain-size range, smaller grains impede dislocation motion and raise yield strength.",
        _f("Hall–Petch relation", r"\sigma_y=\sigma_0+k_y d^{-1/2}", (("σ_y", "yield strength", "MPa"), ("σ_0", "friction stress", "MPa"), ("k_y", "material strengthening constant", "MPa·m^1/2"), ("d", "mean grain diameter", "m")), "Empirical relation over a material- and microstructure-dependent range; it can break down at very small grain sizes."),
        "Grain boundaries obstruct dislocation motion. Increasing boundary area per volume as grain size falls increases the stress needed for slip; experiments express that trend with d⁻¹/².",
        _e("If σ₀=100 MPa, k_y=0.5 MPa·m^1/2, and d=10⁻⁴ m, estimate σ_y.", "d⁻¹/²=100 m⁻¹/².", "σ_y=100+0.5×100=150 MPa.", "150 MPa by the stated Hall–Petch estimate."),
        ("Selecting heat treatments to control strength and ductility.", "Relating microscopy to mechanical test results."),
        "Applying a fitted Hall–Petch constant to another alloy, heat treatment, texture, or nanoscale grain regime.",
        "Materials teams tie processing history to microscopy and certified mechanical tests; the empirical fit is used only within its calibration range.",
        tags=("hall-petch", "grain-size", "materials"), difficulty="hard"),

    # ----------------------------- additional engineering branches --------
    "site-reliability-engineering": _lesson(
        "SLOs, SLIs, and Error Budgets",
        "A service-level indicator measures user-visible behavior; an objective sets the target and the error budget makes reliability trade-offs explicit.",
        _f("Error budget", r"B=1-SLO", (("B", "allowed bad-event fraction", "dimensionless"), ("SLO", "target good-event fraction", "dimensionless")), "The SLI event definition and time window must be explicit; this relation is a planning budget, not a promise of availability."),
        "If a target requires 99.9% good requests, the complement is 0.1% allowed bad requests over the same window. The complement is meaningful only when the SLI counts user-relevant events.",
        _e("An SLO is 99.9% successful requests over 30 days. What is the allowed error fraction?", "Take the complement of the SLO.", "1−0.999=0.001=0.1%.", "0.1% error budget for the stated window."),
        ("Prioritizing reliability work against feature delivery.", "Responding to incidents using service-level evidence."),
        "Using host uptime when users care about successful, timely requests, or treating an SLO as a guarantee without measuring it.",
        "SRE practice defines SLIs from user journeys, pages on actionable symptoms, rehearses rollback and restore, and reviews error-budget policy with product owners.",
        tags=("sre", "sli", "slo", "error-budget")),
    "blockchain-systems": _lesson(
        "Hash-Linked Blocks and Transaction Integrity",
        "A block header commits to its parent and transaction set; changing committed data changes the digest and breaks downstream links.",
        _f("Block commitment", r"h_i=H(h_{i-1}\parallel r_i\parallel n_i)", (("h_i", "current block digest", "fixed-length bits"), ("h_{i-1}", "parent digest", "fixed-length bits"), ("r_i", "transaction-root commitment", "fixed-length bits"), ("n_i", "other header fields/nonce", "encoded bytes")), "Collision resistance and consensus assumptions matter; a hash link alone does not establish truth or prevent all attacks."),
        "The block digest is computed from the previous digest and the current commitments. Editing an earlier transaction changes its root and digest, so later blocks no longer reference the expected history.",
        _e("If a transaction changes the Merkle root r_i, what must happen to h_i and the following parent links?", "Recompute the header hash, then note that the next block still points at the old digest.", "h_i changes; descendants must be rebuilt and accepted under the network's consensus rules.", "The current digest changes and downstream links no longer match."),
        ("Auditing append-only distributed records.", "Evaluating smart-contract and consensus design assumptions."),
        "Claiming that a hash makes a system immutable by itself; key theft, consensus capture, contract bugs, and governance still matter.",
        "Production teams review contract code, key custody, upgrade controls, oracle trust, chain finality, and incident response; use only authorized test networks for experiments.",
        tags=("blockchain", "hash-chain", "consensus"), difficulty="hard"),
    "iot-systems-design": _lesson(
        "Sensor Calibration and IoT Measurement Quality",
        "A calibrated sensor maps a physical input to a reported value with a documented scale, offset, uncertainty, and operating range.",
        _f("Linear sensor calibration model", r"y=ax+b", (("y", "reported measurement", "output units"), ("x", "reference measurand", "input units"), ("a", "scale factor", "output/input"), ("b", "zero offset", "output units")), "A linear fit is valid only over the calibrated range; temperature drift, hysteresis, and sensor aging may require additional terms."),
        "Two calibration points determine slope a=(y₂−y₁)/(x₂−x₁) and offset b=y₁−ax₁. Additional points test whether a linear model is justified.",
        _e("A 4–20 mA transmitter maps 0–100 °C linearly. What temperature corresponds to 12 mA?", "12 mA is halfway from 4 to 20 mA.", "x=(12−4)/(20−4)×100=50 °C.", "50 °C, assuming linear calibration."),
        ("Building trusted sensor-to-cloud telemetry.", "Monitoring battery-powered environmental and industrial devices."),
        "Treating an ADC count as a calibrated physical value or accepting data without range, timestamp, unit, and quality flags.",
        "IoT deployments version calibration coefficients, secure device identity, track firmware and battery status, and design store-and-forward behavior for outages.",
        tags=("iot", "sensor-calibration", "telemetry")),
    "robotics-kinematics": _lesson(
        "Forward Kinematics of a Two-Link Planar Arm",
        "Forward kinematics maps joint angles and link lengths to the end-effector position in a chosen coordinate frame.",
        _f("Planar two-link position", r"x=l_1\cos\theta_1+l_2\cos(\theta_1+\theta_2),\quad y=l_1\sin\theta_1+l_2\sin(\theta_1+\theta_2)", (("l₁,l₂", "link lengths", "m"), ("θ₁,θ₂", "joint angles", "rad"), ("x,y", "end-effector position", "m")), "Angles are measured using the stated joint convention; link flexibility, joint offsets, and tool frames are excluded."),
        "The first link contributes its vector at θ₁. The second link is rotated relative to the first, so its absolute angle is θ₁+θ₂. Add the two vectors component-wise.",
        _e("For l₁=l₂=1 m, θ₁=0, and θ₂=90°, find the end-effector coordinates.", "The first link contributes (1,0); the second contributes (0,1).", "x=1+0=1 m; y=0+1=1 m.", "(x,y)=(1 m,1 m)."),
        ("Workspace planning and robot motion visualization.", "Checking inverse-kinematic targets against reach and joint limits."),
        "Mixing degrees and radians or composing rotations in a different frame/order than the diagram defines.",
        "Robotics teams calibrate tool and base frames, check collision and singularity margins, and validate trajectories at constrained speed before production.",
        tags=("robotics", "forward-kinematics", "coordinate-frames"), difficulty="hard"),
    "mechatronic-system-design": _lesson(
        "Closed-Loop Sensor, Controller, and Actuator Design",
        "A mechatronic loop measures output, compares it with a reference, and drives an actuator to reduce the error.",
        _f("Proportional control law", r"e(t)=r(t)-y(t),\quad u(t)=K_p e(t)", (("r", "reference or setpoint", "output units"), ("y", "measured output", "output units"), ("e", "control error", "output units"), ("u", "controller output", "actuator units"), ("K_p", "proportional gain", "actuator/output")), "A proportional law is a baseline model; sensor noise, saturation, delay, and stability must be checked."),
        "The error is the desired value minus the measured value. Multiplying by gain produces a command whose sign drives the system toward the reference under the chosen actuator convention.",
        _e("A temperature setpoint is 60 °C, the measured value is 55 °C, and Kp=2 units/°C. Find u.", "Compute the error, then multiply by gain.", "e=5 °C; u=2×5=10 actuator units.", "u = 10 actuator units."),
        ("Motor speed, temperature, and positioning control.", "Integrating sensors, embedded logic, power electronics, and mechanical loads."),
        "Ignoring actuator saturation or sensor polarity; either can make the feedback positive instead of negative.",
        "Teams document signal ranges, interlocks, safe states, control limits, and fault behavior; hardware-in-loop tests precede commissioning.",
        tags=("mechatronics", "feedback", "control-loop")),
    "production-planning-control": _lesson(
        "Overall Equipment Effectiveness",
        "OEE combines availability, performance, and quality to describe productive output relative to planned production time.",
        _f("Overall equipment effectiveness", r"OEE=A\times P\times Q", (("A", "availability fraction", "dimensionless"), ("P", "performance fraction", "dimensionless"), ("Q", "quality fraction", "dimensionless")), "Use consistent definitions and a shared time boundary; OEE is a diagnostic, not a substitute for root-cause analysis."),
        "Productive good output is reduced successively by downtime, slower-than-ideal running, and defects. Multiplying the three fractions yields the combined good-production fraction.",
        _e("A line has A=0.90, P=0.80, and Q=0.95. Find OEE.", "Multiply the three dimensionless factors.", "OEE=0.90×0.80×0.95=0.684.", "68.4% OEE under the stated definitions."),
        ("Finding losses in a production shift.", "Prioritizing downtime, speed-loss, and defect-reduction work."),
        "Comparing OEE across plants with different planned-time or ideal-cycle definitions, or using the score to blame operators instead of finding system causes.",
        "Manufacturing teams agree the event taxonomy, validate ideal cycle times, and review loss categories with frontline staff before setting improvement actions.",
        tags=("production", "oee", "continuous-improvement")),
    "operations-research": _lesson(
        "Economic Order Quantity and Inventory Trade-Off",
        "The basic EOQ model balances fixed ordering cost against inventory holding cost under steady, deterministic demand.",
        _f("Economic order quantity", r"Q^*=\sqrt{\frac{2DS}{H}}", (("Q*", "economic order size", "units/order"), ("D", "annual demand", "units/year"), ("S", "fixed cost per order", "currency/order"), ("H", "holding cost per unit per year", "currency/(unit·year)")), "Assumes constant demand and lead time, no shortages, replenishment in lots, and no quantity discounts."),
        "Annual ordering cost is DS/Q; annual holding cost is HQ/2. Differentiating their sum with respect to Q and setting it to zero gives Q²=2DS/H.",
        _e("Demand is 10,000 units/year, order cost ₹200/order, and holding cost ₹5/unit/year. Find EOQ.", "Q*=√(2×10000×200/5).", "Q*=√800000≈894 units.", "About 894 units per order under the classical assumptions."),
        ("Choosing an initial replenishment lot size.", "Explaining the order-versus-carrying-cost trade-off."),
        "Treating EOQ as an automatic order policy when demand is variable, supply constrained, perishable, or subject to minimum order quantities.",
        "Planners validate lead-time variability, service level, shelf life, supplier constraints, and working-capital goals before using a deterministic baseline.",
        tags=("operations-research", "inventory", "eoq"), difficulty="hard"),
    "industrial-automation": _lesson(
        "PLC Sequence Logic and Safe Interlocks",
        "A PLC sequence advances machine states only when the required permissives are true and faults or unsafe conditions force a defined safe state.",
        _f("Sequence transition rule", r"S_{next}=S_i\land P_i\land\neg F", (("S_i", "current sequence state", "boolean"), ("P_i", "transition permissives", "boolean"), ("F", "fault/interlock condition", "boolean")), "This is a logical design pattern; safety functions require the applicable safety-rated architecture and validation."),
        "A transition is allowed only if the machine is in the expected state, every permissive is satisfied, and no blocking fault is active. Explicit state transitions prevent ambiguous combinations of outputs.",
        _e("A conveyor may start only in READY state when guard-closed is true and no fault is active. Which condition permits START?", "Conjoin the state and permissive, and exclude the fault condition.", "READY ∧ guard_closed ∧ ¬fault.", "Start only when READY, guard closed, and fault-free."),
        ("Automating packaging and material-handling cells.", "Making sequences diagnosable and recoverable after interruptions."),
        "Treating an ordinary PLC interlock as a certified safety function or allowing a reset to restart motion unexpectedly.",
        "Controls teams define safe states, hazard-rated devices, fault latching, reset behavior, and validated test cases with the machine risk assessment.",
        tags=("plc", "sequence-control", "interlocks")),
    "aerodynamics-flight-mechanics": _lesson(
        "Lift, Dynamic Pressure, and Wing Area",
        "For a specified flight condition, lift scales with dynamic pressure, reference area, and lift coefficient.",
        _f("Lift equation", r"L=\frac{1}{2}\rho V^2 S C_L", (("L", "lift force", "N"), ("ρ", "air density", "kg/m³"), ("V", "true airspeed", "m/s"), ("S", "reference wing area", "m²"), ("C_L", "lift coefficient", "dimensionless")), "C_L depends on geometry and flow condition; the relation is not a complete prediction near stall or in compressible/transonic regimes."),
        "Dynamic pressure is q=½ρV². Multiplying q by reference area and a dimensionless coefficient gives the aerodynamic force component defined as lift.",
        _e("At ρ=1.2 kg/m³, V=50 m/s, S=20 m², and C_L=0.5, estimate lift.", "Compute q=0.5×1.2×50²=1500 Pa, then L=qSC_L.", "L=1500×20×0.5=15,000 N.", "15 kN lift under the stated model."),
        ("Estimating aircraft trim and performance.", "Understanding lift changes with speed, density, and configuration."),
        "Using indicated airspeed in place of the defined true airspeed or extrapolating a lift coefficient through stall without data.",
        "Flight-performance work uses validated aerodynamic data, mass and center-of-gravity limits, atmosphere models, and approved flight-test or certification methods.",
        tags=("aerodynamics", "lift", "flight-mechanics"), difficulty="hard"),
    "physical-metallurgy": _lesson(
        "Lever Rule for Two-Phase Microstructures",
        "Within a two-phase region of an equilibrium phase diagram, tie-line distances determine phase fractions by mass balance.",
        _f("Lever rule for phase α", r"W_\alpha=\frac{C_\beta-C_0}{C_\beta-C_\alpha}", (("W_α", "mass fraction of phase α", "dimensionless"), ("C₀", "overall alloy composition", "composition units"), ("Cα,Cβ", "tie-line phase compositions", "composition units")), "Applies to the specified equilibrium two-phase field and a consistent composition basis; kinetics and segregation can alter the measured microstructure."),
        "The overall composition is the weighted average C₀=WαCα+WβCβ with Wα+Wβ=1. Solving those balances gives each fraction proportional to the opposite tie-line arm.",
        _e("A tie line has Cα=20%, Cβ=80%, and alloy C₀=50%. Find Wα.", "Use the opposite arm: (Cβ−C₀)/(Cβ−Cα).", "Wα=(80−50)/(80−20)=0.5.", "50% phase α by mass at equilibrium."),
        ("Estimating phase amounts during alloy heat treatment.", "Interpreting phase diagrams and microscopy."),
        "Using the wrong composition basis or applying an equilibrium phase fraction to a rapidly cooled, non-equilibrium structure.",
        "Metallurgists pair thermodynamic diagrams with actual process history, microscopy, and property tests; heat-treatment windows are validated on the component section size.",
        tags=("metallurgy", "phase-diagram", "lever-rule"), difficulty="hard"),
    "polymer-processing": _lesson(
        "Power-Law Rheology in Polymer Processing",
        "Many polymer melts are shear-thinning; a power-law model relates shear stress to shear rate over a limited processing range.",
        _f("Power-law fluid model", r"\tau=K\dot\gamma^n", (("τ", "shear stress", "Pa"), ("K", "consistency index", "Pa·sⁿ"), ("γ̇", "shear rate", "s⁻¹"), ("n", "flow-behavior index", "dimensionless")), "Empirical fit over a stated temperature and shear-rate range; polymer melts can be viscoelastic and need richer models."),
        "The exponent n sets how apparent viscosity changes with shear rate: n<1 means stress rises sublinearly and apparent viscosity falls as rate increases.",
        _e("A melt has K=5 Pa·s^0.5, n=0.5, and shear rate 4 s⁻¹. Estimate shear stress.", "Compute 4^0.5=2, then multiply by K.", "τ=5×2=10 Pa.", "10 Pa by the power-law approximation."),
        ("Estimating pressure and flow in extrusion dies.", "Comparing polymer grades and processing windows."),
        "Treating a fitted power law as a universal material constant or ignoring temperature, molecular weight, viscoelasticity, and degradation.",
        "Processors use rheometry at relevant temperature and shear rates, correlate die pressure with line data, and monitor residence time and thermal history.",
        tags=("polymer", "rheology", "shear-thinning"), difficulty="hard"),
    "reservoir-engineering": _lesson(
        "Darcy Flow Through a Porous Reservoir",
        "Darcy's law relates single-phase flow through a porous medium to permeability, area, pressure gradient, and viscosity.",
        _f("One-dimensional Darcy flux", r"q=-\frac{kA}{\mu}\frac{dp}{dx}", (("q", "volumetric flow rate", "m³/s"), ("k", "permeability", "m²"), ("A", "flow area", "m²"), ("μ", "dynamic viscosity", "Pa·s"), ("dp/dx", "pressure gradient", "Pa/m")), "Assumes laminar single-phase flow through a representative porous medium; field well flow needs geometry, relative permeability, and boundary conditions."),
        "The negative sign indicates flow from high to low pressure. Larger permeability and area increase flow; larger viscosity and pressure-gradient length reduce it.",
        _e("A core has k=1×10⁻¹² m², area=0.01 m², μ=0.001 Pa·s, and pressure gradient=10⁶ Pa/m. Estimate magnitude q.", "Use |q|=kA/μ times the gradient.", "|q|=10⁻¹²×0.01/0.001×10⁶=10⁻⁵ m³/s.", "1×10⁻⁵ m³/s toward lower pressure in this simplified core model."),
        ("Core-flow tests and reservoir deliverability estimates.", "Reasoning about permeability and pressure drawdown."),
        "Applying a core-scale single-phase equation directly to a field well without accounting for geometry, multiphase flow, skin, and pressure-dependent properties.",
        "Reservoir engineers state units and reference conditions, history-match pressure and production data, and bracket uncertainty in petrophysical properties.",
        tags=("reservoir", "darcy-law", "porous-media"), difficulty="hard"),
    "mine-planning-operations": _lesson(
        "Stripping Ratio and Open-Pit Mine Planning",
        "Stripping ratio compares waste removed with ore recovered and is one input to an economic open-pit limit.",
        _f("Mass stripping ratio", r"SR=\frac{M_{waste}}{M_{ore}}", (("SR", "stripping ratio", "t/t"), ("M_waste", "waste mass removed", "t"), ("M_ore", "ore mass recovered", "t")), "Use a consistent mass or volume basis and period; economic decisions also depend on grade, recovery, price, cost, slope, and closure."),
        "Divide waste movement by ore movement over the same mine phase. A higher ratio means more material must be moved for each unit of ore, but it is not an economic verdict on its own.",
        _e("A bench plan moves 900,000 t of waste and recovers 300,000 t of ore. Find the mass stripping ratio.", "Divide waste mass by ore mass.", "SR=900,000/300,000=3.", "3 t waste per tonne of ore."),
        ("Comparing pushback schedules.", "Testing mine economics and equipment fleet requirements."),
        "Treating stripping ratio alone as profitability or ignoring dilution, recovery, slope risk, water, tailings, and closure obligations.",
        "Mine plans combine a time-phased block model with geotechnical constraints, permits, water management, rehabilitation, and community engagement.",
        tags=("mining", "strip-ratio", "mine-planning"), difficulty="medium"),
    "bioprocess-engineering": _lesson(
        "Monod Growth Kinetics in a Bioreactor",
        "The Monod model describes specific microbial growth rate as substrate concentration rises toward a maximum.",
        _f("Monod relation", r"\mu=\mu_{max}\frac{S}{K_s+S}", (("μ", "specific growth rate", "h⁻¹"), ("μ_max", "maximum specific growth rate", "h⁻¹"), ("S", "limiting substrate concentration", "g/L"), ("K_s", "half-saturation constant", "g/L")), "Empirical single-limiting-substrate model; inhibition, maintenance, oxygen transfer, and multi-nutrient limits may require additional terms."),
        "At low substrate, growth is approximately proportional to S. At high substrate, the denominator is dominated by S and μ approaches μ_max; at S=K_s, it is half maximum.",
        _e("If μmax=0.8 h⁻¹, S=2 g/L, and Ks=2 g/L, find μ.", "At S=Ks the fraction S/(Ks+S) is one half.", "μ=0.8×2/(2+2)=0.4 h⁻¹.", "0.4 h⁻¹."),
        ("Estimating batch growth at a known substrate concentration.", "Choosing feed strategy and reactor operating range."),
        "Assuming substrate is the only limiting factor when oxygen transfer, pH, inhibition, or heat removal controls growth.",
        "Bioprocess scale-up tracks dissolved oxygen, mixing, sterility, pH, heat removal, and product quality; model parameters are measured for the actual strain and medium.",
        tags=("bioprocess", "monod", "cell-growth"), difficulty="hard"),
    "biomedical-instrumentation": _lesson(
        "Instrumentation Amplifier for a Differential Biopotential",
        "An instrumentation amplifier raises a small differential sensor signal while rejecting common-mode voltage, subject to range and safety constraints.",
        _f("Differential gain model", r"V_o=G(V_+-V_-)+V_{ref}", (("V_o", "amplifier output", "V"), ("G", "differential gain", "V/V"), ("V₊−V₋", "differential input", "V"), ("V_ref", "output reference", "V")), "Idealized linear model; input common-mode range, electrode offsets, noise, isolation, and patient-safety requirements must be verified."),
        "The wanted signal is the difference between two electrode voltages. A large common voltage should cancel in the differential stage, while gain scales the remaining small difference.",
        _e("An amplifier has G=1000 and a 1 mV differential input with Vref=0. Find ideal output.", "Convert 1 mV to 0.001 V.", "V_o=1000×0.001=1 V.", "1 V ideal output before range and safety checks."),
        ("ECG and biopotential acquisition.", "Conditioning bridge, pressure, and other low-level differential sensors."),
        "Increasing gain until the signal clips because electrode offset or common-mode voltage was not checked.",
        "Biomedical device engineering documents isolation, leakage-current limits, applied-part classification, calibration, EMC, and clinical validation under applicable standards.",
        tags=("biomedical", "instrumentation-amplifier", "ecg"), difficulty="hard"),
    "food-process-technology": _lesson(
        "Decimal Reduction Time in Thermal Preservation",
        "The decimal reduction time D is the exposure time at a specified temperature needed for a one-log reduction of a target organism.",
        _f("Log-linear survival model", r"\frac{N}{N_0}=10^{-t/D}", (("N/N₀", "surviving fraction", "dimensionless"), ("t", "exposure time", "min"), ("D", "decimal reduction time at reference temperature", "min")), "D depends strongly on organism, food matrix, and temperature; real process lethality must use validated time-temperature history."),
        "Each interval D multiplies survivors by 0.1. After t/D intervals, the surviving fraction is 10^(−t/D).",
        _e("At a validated temperature D=2 min. What reduction is predicted after 6 min?", "There are 6/2=3 decimal-reduction intervals.", "N/N₀=10⁻³=0.001, a three-log reduction.", "99.9% reduction in the idealized model."),
        ("Understanding thermal preservation targets.", "Comparing heating processes and cold-point lethality."),
        "Treating a D-value as fixed across temperatures or products, or using an illustrative reduction as a validated food-safety schedule.",
        "Food safety uses validated scheduled processes, cold-spot measurements, hygienic design, and hazard analysis; only qualified process authorities establish commercial thermal schedules.",
        tags=("food-safety", "thermal-processing", "d-value"), difficulty="hard"),
    "agricultural-machinery-systems": _lesson(
        "Field Capacity and Field Efficiency",
        "Field efficiency compares measured effective field capacity with theoretical capacity based on implement width and travel speed.",
        _f("Theoretical field capacity", r"C_t=\frac{Wv}{10}", (("C_t", "theoretical field capacity", "ha/h"), ("W", "working width", "m"), ("v", "travel speed", "km/h")), "The conversion assumes full width and no turns, overlap, stoppages, or field irregularity; effective capacity is lower."),
        "At speed v km/h, the machine travels 1000v metres per hour. Multiplying by width W gives square metres per hour; dividing by 10,000 converts to hectares per hour, yielding Wv/10.",
        _e("A 3 m implement travels at 6 km/h. Find theoretical field capacity.", "Use C_t=Wv/10.", "C_t=3×6/10=1.8 ha/h.", "1.8 ha/h theoretical capacity."),
        ("Sizing machinery for a field-operation window.", "Comparing actual capacity after turns, overlap, and downtime."),
        "Using theoretical capacity as a real daily output or ignoring field shape, soil condition, operator time, and implement adjustment.",
        "Machinery planning uses measured effective capacity, field conditions, safe operating limits, maintenance, and seasonal work windows.",
        tags=("agricultural-machinery", "field-capacity", "efficiency")),
    "marine-propulsion-systems": _lesson(
        "Shaft Power from Torque and Rotational Speed",
        "A rotating shaft transmits power equal to torque multiplied by angular speed; propulsive power delivered to the water is affected by losses.",
        _f("Rotational shaft power", r"P=T\omega=T\frac{2\pi N}{60}", (("P", "shaft power", "W"), ("T", "shaft torque", "N·m"), ("ω", "angular speed", "rad/s"), ("N", "rotational speed", "rpm")), "Use torque and speed measured at the same shaft; gear, bearing, propeller, and hull losses separate shaft power from useful thrust power."),
        "Work per revolution is torque times angular displacement 2π. Multiplying by revolutions per second N/60 gives power.",
        _e("A shaft transmits 20 kN·m at 300 rpm. Estimate power.", "Convert torque to 20,000 N·m and use ω=2π×300/60=31.42 rad/s.", "P≈20,000×31.42=628,400 W.", "About 628 kW shaft power."),
        ("Matching prime movers and propeller operating points.", "Checking engine load, shaft line, and propulsion trials."),
        "Using propeller rpm instead of the measured shaft speed across a gearbox or equating shaft power to useful thrust power.",
        "Marine engineers verify torsional vibration, alignment, cavitation margin, fuel/load curves, corrosion protection, and safety-critical shutdowns.",
        tags=("marine", "propulsion", "shaft-power"), difficulty="hard"),
    "textile-fiber-fabric-engineering": _lesson(
        "Yarn Linear Density and Tex",
        "Tex expresses yarn mass in grams per kilometre, allowing a direct comparison of linear density across yarns.",
        _f("Tex count", r"Tex=\frac{m_g}{L_{km}}", (("Tex", "linear density", "g/km"), ("m_g", "yarn mass", "g"), ("L_km", "yarn length", "km")), "State the count system; tex is direct, while cotton count and denier use different conventions."),
        "Linear density is mass divided by length. Expressing mass in grams and length in kilometres gives the defined tex unit without an additional scale factor.",
        _e("A 100 m yarn sample weighs 2 g. Find its tex value.", "Convert length to 0.1 km, then divide mass by length.", "Tex=2/0.1=20 g/km.", "20 tex."),
        ("Comparing yarn fineness and material consumption.", "Setting spinning, weaving, and fabric-weight process targets."),
        "Comparing tex directly with a reverse-count system without converting or checking whether the stated length is conditioned.",
        "Textile quality control records count method, conditioning atmosphere, twist, tensile behavior, and process stage; a yarn count alone does not determine fabric performance.",
        tags=("textile", "yarn-count", "tex")),
    "renewable-energy-systems": _lesson(
        "Capacity Factor for Renewable Generation",
        "Capacity factor compares energy actually generated over a period with the energy that would be produced at rated power continuously.",
        _f("Capacity factor", r"CF=\frac{E_{actual}}{P_{rated}t}", (("CF", "capacity factor", "dimensionless"), ("E_actual", "energy generated", "MWh"), ("P_rated", "rated power", "MW"), ("t", "period duration", "h")), "Use the same time window and define whether curtailment and outages are included; capacity factor is not conversion efficiency."),
        "Rated power times elapsed hours is the maximum nameplate energy for that period. Dividing actual energy by that baseline yields the utilization fraction.",
        _e("A 1 MW plant generates 2.4 MWh in one day. Find capacity factor.", "The 24-hour rated-energy baseline is 1×24=24 MWh.", "CF=2.4/24=0.10.", "10% for that day."),
        ("Comparing wind and solar resource utilization.", "Planning storage, grid connection, and annual energy yield."),
        "Calling capacity factor efficiency or comparing a short weather window with a multi-year annual value.",
        "Energy plans use long-term resource data, degradation, curtailment, availability, storage losses, and grid constraints alongside capacity factor.",
        tags=("renewable-energy", "capacity-factor", "generation")),
}


# Cyber Security is not a generic catalogue placeholder. These five original,
# defensive lessons are visible without a learner account and each has a real
# quiz item. The material is for authorized design, review, and lab work.
CYBER_SECURITY_LESSONS = [
    _lesson(
        "Threat Modeling and Security Objectives",
        "A threat model names assets, trust boundaries, adversaries, and abuse cases before controls are selected.",
        _f("Risk-ranking model (ordinal, not universal)", r"R=L\times I", (("R", "relative risk score", "ordinal score"), ("L", "likelihood rating", "ordinal scale"), ("I", "impact rating", "ordinal scale")), "Likelihood and impact scales must be defined locally; this product prioritizes review and is not a calibrated probability."),
        "Security requirements begin with what must be protected. A boundary and data-flow view exposes where trust changes; likelihood and impact then help rank review, but cannot replace judgment.",
        _e("A public endpoint exposes sensitive records and has high impact if abused. What should be documented before choosing a control?", "Start with the protected asset, boundary, abuse case, and the expected consequence.", "Record the asset and data flow, actor and abuse case, likelihood assumptions, impact, and existing controls.", "A scoped threat model, not a tool choice made in isolation."),
        ("Architecture reviews and abuse-case analysis.", "Prioritizing security requirements and control tests."),
        "Calling a risk score an objective probability or treating a checklist as proof that all threats have been found.",
        "Security reviews record assumptions, owners, mitigations, residual risk, and verification evidence; risk rankings are revisited after architecture changes.",
        tags=("cyber-security", "threat-modeling", "risk"), difficulty="medium",
        quiz={"stem": "A threat model is most useful when it is created at what point?", "options": ["During design, while assets and trust boundaries can still change", "Only after a breach, to explain the incident", "After choosing a security product, to justify the purchase", "Only when an application is exposed to the public internet"], "correct": 0, "explanation": "Threat modeling is most actionable during design and is repeated when trust boundaries, assets, or deployment assumptions change."},
        diagram_steps=(("Asset", "Name the data, service, and people whose confidentiality, integrity, or availability matter."), ("Boundary", "Map components and trust transitions so abuse cases can be stated."), ("Control", "Choose a mitigation and define a test or evidence that shows it works."))),
    _lesson(
        "Password Storage: Salts and Slow Password Hashing",
        "A server stores a salted, deliberately expensive password verifier rather than plaintext or a fast general-purpose hash.",
        _f("Password verifier", r"v=KDF(password,salt,cost)", (("v", "stored verifier", "fixed-length bytes"), ("password", "user secret", "secret input"), ("salt", "unique random per-account value", "bytes"), ("cost", "work factor parameters", "parameter set")), "Use a maintained password-hashing KDF such as Argon2id, scrypt, or PBKDF2 with parameters chosen for the deployment; never invent a KDF."),
        "A unique salt makes identical passwords produce different stored verifiers and prevents reusable precomputed tables. A memory- or CPU-expensive KDF raises the cost of each offline guess; the salt is stored alongside the verifier and is not secret.",
        _e("Two accounts choose the same password. Why should their stored verifiers still differ?", "Each account receives an independently generated random salt before the password KDF.", "Different salts make the KDF inputs different, so the resulting verifiers differ even when the password is the same.", "Use a unique random salt for each account and a slow password KDF."),
        ("Protecting account databases if a backup is exposed.", "Supporting secure password change and login verification."),
        "Encrypting passwords reversibly, reusing one salt globally, or applying a fast hash such as bare SHA-256 as a password verifier.",
        "Identity teams use a vetted library, benchmark cost parameters on production-class hardware, rate-limit online guesses, and plan algorithm upgrades.",
        tags=("cyber-security", "password-hashing", "salt", "kdf"), difficulty="medium",
        quiz={"stem": "Why does a password verifier use a unique salt and a password-specific KDF?", "options": ["To make offline guessing more expensive and prevent identical passwords from sharing the same verifier", "To make the password recoverable for support staff", "To replace account-level rate limits", "To make the salt act as a secret encryption key"], "correct": 0, "explanation": "A unique salt defeats precomputed reuse and a deliberately expensive KDF raises offline guess cost. The salt is not a secret and the original password is not recoverable."},
        diagram_steps=(("Password", "The user's secret is accepted only over a protected, authenticated channel."), ("Salt + KDF", "A per-account random salt and a vetted slow KDF produce the verifier."), ("Verify", "Login recomputes the verifier with stored parameters and compares it safely."))),
    _lesson(
        "Authenticated Encryption and Nonce Discipline",
        "Authenticated encryption with associated data (AEAD) protects ciphertext confidentiality and detects tampering in one construction.",
        _f("AEAD encryption interface", r"(C,T)=AEAD.Enc(K,N,P,A)", (("C", "ciphertext", "bytes"), ("T", "authentication tag", "bytes"), ("K", "secret key", "key bytes"), ("N", "nonce", "unique per key as required by the algorithm"), ("P", "plaintext", "bytes"), ("A", "associated authenticated data", "bytes")), "Nonce requirements are algorithm-specific; nonce reuse with the same key can be catastrophic. Authenticate context such as record identifiers when appropriate."),
        "Encryption transforms plaintext into ciphertext, while the tag binds the ciphertext and associated data to the key. Decryption must reject a tag mismatch before any plaintext is trusted.",
        _e("A receiver gets an AEAD ciphertext whose tag check fails. What should the application do?", "Treat failed authentication as corrupted or forged data and do not release plaintext to the caller.", "Reject the record, log a safe event, and follow the protocol's recovery path without using unauthenticated bytes.", "Reject it; authentication failure means the ciphertext or context is not trusted."),
        ("Protecting stored or transmitted application records.", "Binding encrypted payloads to version, tenant, or record context."),
        "Reusing a nonce when the algorithm forbids it, or exposing partially decrypted plaintext before tag verification succeeds.",
        "Cryptographic implementations use vetted AEAD libraries, unique nonce allocation, key rotation, authenticated context, and explicit failure handling.",
        tags=("cyber-security", "aead", "encryption", "integrity"), difficulty="hard",
        quiz={"stem": "What is the safe response when AEAD tag verification fails?", "options": ["Reject the message and never act on unauthenticated plaintext", "Continue with the decrypted bytes because encryption already hid them", "Retry decryption with a different nonce until the tag passes", "Ignore the tag for messages from a known client"], "correct": 0, "explanation": "AEAD authentication is part of the security guarantee. A failed tag means integrity and authenticity are not established, so the plaintext must not be trusted."},
        diagram_steps=(("Encrypt", "A vetted AEAD algorithm uses a key and nonce to produce ciphertext and a tag."), ("Bind context", "Associated data authenticates metadata without encrypting it."), ("Verify first", "The receiver verifies the tag before any application uses plaintext."))),
    _lesson(
        "TLS Certificates and Server Identity Validation",
        "TLS protects a channel only when the client validates the certificate chain and the requested hostname before trusting the peer.",
        _f("Certificate acceptance predicate", r"Accept=Chain\land Host\land Time\land Policy", (("Chain", "chain reaches a trusted issuer", "boolean"), ("Host", "certificate matches requested host", "boolean"), ("Time", "certificate is within validity period", "boolean"), ("Policy", "algorithm and usage constraints pass", "boolean")), "Exact validation follows the TLS implementation and trust policy; a valid certificate does not prove the server's business behavior is safe."),
        "Each check answers a different question: who issued the certificate, whether it names the destination, whether it is current, and whether its use is permitted. All required checks must pass before the channel is accepted.",
        _e("A trusted certificate is current but names api.example.test while the client requested payments.example.test. Should the client proceed?", "Hostname validation is independent of issuer-chain validation.", "No. The certificate name does not match the requested host, so the client must fail closed.", "No; a trusted chain does not excuse a hostname mismatch."),
        ("Securing service-to-service and browser connections.", "Investigating certificate rotation and trust-store failures."),
        "Disabling certificate checks to fix a deployment or assuming that encryption without hostname validation authenticates the intended server.",
        "Operations automate renewal, monitor expiry, preserve hostname verification, restrict trust roots, and rehearse key compromise and certificate rotation.",
        tags=("cyber-security", "tls", "certificates", "identity"), difficulty="medium",
        quiz={"stem": "A certificate chains to a trusted root but does not match the hostname requested by the client. What should the client do?", "options": ["Reject the connection because server identity validation failed", "Accept it because the issuer is trusted", "Disable hostname checks for this one request", "Continue if the response is encrypted"], "correct": 0, "explanation": "A trusted chain and a matching hostname are separate validation requirements. Encryption to the wrong peer is not authenticated communication with the intended server."},
        diagram_steps=(("Request host", "The client begins with the exact hostname it intends to reach."), ("Validate", "The chain, hostname, time, and certificate policy are checked."), ("Trust channel", "Application data is sent only after peer identity validation succeeds."))),
    _lesson(
        "Parameterized Queries and Injection Prevention",
        "Parameterized database calls keep SQL structure separate from untrusted values so input is interpreted as data, not executable syntax.",
        _f("Query construction rule", r"Q=Template\;\Vert\;BoundValues", (("Q", "database request", "query object"), ("Template", "fixed SQL structure", "trusted code"), ("BoundValues", "separately encoded parameters", "data values")), "Use the database driver's parameter binding; do not interpolate untrusted strings into SQL syntax."),
        "The database parses the fixed statement and binds each value in its own parameter slot. A quote or operator inside a value therefore remains a value instead of changing the parsed program.",
        _e("An account search accepts a user-supplied email. Which design keeps the value separate from SQL syntax?", "Use a fixed query with a bound placeholder for the email.", "Prepare `SELECT id FROM users WHERE email = ?` and bind the email as a value.", "A parameterized query with the input bound separately."),
        ("Protecting account, billing, and search queries.", "Keeping query plans stable and reviewable."),
        "Escaping a few characters by hand, concatenating untrusted values into SQL, or relying on client-side validation as a security boundary.",
        "Application reviews use parameter binding, least-privilege database roles, server-side validation, audit logging, and regression tests for authorization boundaries.",
        tags=("cyber-security", "sql-injection", "parameterized-queries", "defensive"), difficulty="easy",
        quiz={"stem": "Which approach prevents a user-supplied email from becoming SQL syntax?", "options": ["Use a fixed parameterized statement and bind the email as a value", "Concatenate the email after removing a single quote", "Validate the email only in browser JavaScript", "Give the endpoint a database administrator account"], "correct": 0, "explanation": "Parameter binding preserves the distinction between executable SQL structure and untrusted values; server-side authorization and least privilege remain necessary too."},
        diagram_steps=(("Input", "Treat the email as untrusted data at the server boundary."), ("Bind value", "Keep SQL structure fixed and pass the value through the database driver."), ("Authorize", "Validate the operation and database permissions independently."))),
]


def _slugify(value: str) -> str:
    # Keep this aligned with engineverse.security.sanitize.slugify: apostrophes
    # are removed, not converted into word separators.
    cleaned = value.lower().replace("\u2019", "").replace("'", "")
    return re.sub(r"[^a-z0-9]+", "-", cleaned).strip("-")[:96].strip("-") or "item"


def _subject_map() -> dict[str, dict]:
    return {row[0]: {"slug": row[0], "name": row[1], "branch": row[2], "description": row[10], "category": row[2]}
            for row in SUBJECTS}


def _existing_topics() -> list[dict]:
    return list(topics_cse.TOPICS) + list(topics_core.TOPICS) + list(foundations.TOPICS)


def _build_topic(subject: dict, spec: dict) -> dict:
    name = subject["name"]
    formula = spec["formula"]
    conditions = formula["conditions"]
    focus = spec["focus"]
    app1, app2 = spec["applications"]
    mistake = spec["pitfall"]
    title = spec["title"]
    entry = {
        "subject": subject["slug"],
        "title": title,
        "summary": f"{title}: {focus}",
        "focus": focus,
        "difficulty": spec["difficulty"],
        "minutes": spec["minutes"],
        "tags": list(dict.fromkeys([*spec["tags"], subject["slug"], *_slugify(title).split("-")[:3]])),
        "simple": f"In {name}, {focus} In plain terms, start by naming the system and the question, then use the stated relationship to make a checkable engineering decision.",
        "definition": f"{title} is a core model in {name}: {focus} The model is used within these stated limits: {conditions}",
        "intuition": f"The useful intuition is that {focus.lower()} The relationship makes assumptions visible; a result is trustworthy only when its units, boundary, and operating conditions match the real problem.",
        "points": [
            focus,
            f"The governing relation is {formula['name']}; define every symbol before substituting values.",
            f"Model limits: {conditions}",
            "Check units, limiting cases, and an independent measurement or design constraint before acting on a calculated result.",
        ],
        "formula": formula,
        "derivation": spec["derivation"],
        "example": spec["example"],
        "applications": [app1, app2],
        "mistakes": [
            mistake,
            "Mixing units or changing the system boundary midway through a calculation.",
            "Reporting a precise-looking answer without checking assumptions, uncertainty, and safety constraints.",
        ],
        "exam": [
            f"State the assumptions behind {formula['name']} and explain when the relation should not be used.",
            f"Solve the worked {title} problem, showing units and a sanity check at each step.",
            f"Explain how changing one governing variable affects the result in {name}.",
        ],
        "interview": [
            f"How would you validate a {title.lower()} calculation against field or test data?",
            f"Which assumption in {formula['name']} would you challenge first for a real {name.lower()} system, and why?",
        ],
        "industry": spec["industry"],
        "diagram": _slugify(title),
        "accuracy_state": "needs_review",
    }
    if spec.get("quiz"):
        entry["quiz"] = spec["quiz"]
    if spec.get("diagram_steps"):
        entry["diagram_steps"] = spec["diagram_steps"]
    return entry


def generated_topics() -> list[dict]:
    """Return one published starter lesson for each previously empty subject."""
    subjects = _subject_map()
    covered = {row["subject"] for row in _existing_topics()}
    generated: list[dict] = []
    for subject_slug, subject in subjects.items():
        if subject_slug in covered:
            continue
        specs = CYBER_SECURITY_LESSONS if subject_slug == "cryptography-security" else [STARTERS.get(subject_slug)]
        if not specs or any(spec is None for spec in specs):
            raise KeyError(f"No starter lesson is authored for subject {subject_slug!r} ({subject['name']})")
        generated.extend(_build_topic(subject, spec) for spec in specs)

    topic_slugs = [_slugify(topic["title"]) for topic in _existing_topics() + generated]
    duplicates = sorted({slug for slug in topic_slugs if topic_slugs.count(slug) > 1})
    if duplicates:
        raise ValueError(f"duplicate topic slugs after subject expansion: {duplicates}")
    return generated


TOPICS = generated_topics()
TOPIC_BY_SLUG = {_slugify(entry["title"]): entry for entry in TOPICS}


def topics_for_subject(subject_slug: str) -> list[dict]:
    return [entry for entry in TOPICS if entry["subject"] == subject_slug]


def _short(text: str, limit: int = 26) -> str:
    text = " ".join(text.split())
    return text if len(text) <= limit else text[: limit - 1].rstrip() + "…"


def diagram_for_topic(slug: str) -> dict:
    """A safe three-stage SVG diagram for a generated course starter."""
    topic = TOPIC_BY_SLUG.get(slug)
    if not topic:
        raise KeyError(slug)
    steps = topic.get("diagram_steps") or (
        ("Define", "Name the system boundary, inputs, and the engineering question before selecting a model."),
        ("Model", f"Apply {topic['formula']['name']} with its symbols, units, and assumptions made explicit."),
        ("Verify", "Check the result against dimensions, operating limits, and independent evidence before use."),
    )
    xs = (34, 241, 448)
    objects = [svg_label(320, 30, topic["title"], size=15, anchor="middle", weight=700)]
    hot_spots = []
    fills = ("#eef2ff", "#ecfdf5", "#fffbeb")
    for index, ((title, explain), x) in enumerate(zip(steps, xs)):
        objects += svg_box(x, 72, 158, 62, _short(title, 22), fill=fills[index], size=13, rx=7)
        hot_spots.append(hotspot(x, 72, 158, 62, _short(title, 30), explain))
        if index < 2:
            objects.append(svg_arrow(x + 160, 103, x + 204, 103, stroke="#334155", width=1.8))
    formula_label = _short(topic["formula"]["latex"].replace("\\", ""), 110)
    objects.append(svg_label(320, 177, formula_label, size=12, anchor="middle", fill="#334155"))
    objects.append(svg_label(320, 205, "State assumptions → calculate → validate", size=12, anchor="middle", fill="#64748b"))
    return {
        "title": f"{topic['title']}: define, model, verify",
        "caption": f"{topic['summary']} The diagram highlights a repeatable path from stated assumptions to a checked result.",
        "label": f"Engineering workflow for {topic['title']}: define the problem, apply the model, and verify the result",
        "width": 640,
        "height": 225,
        "objects": objects,
        "hotspots": hot_spots,
    }


def model_for_topic(slug: str) -> dict:
    """A safe, small 3D process model for generated course starters."""
    topic = TOPIC_BY_SLUG.get(slug)
    if not topic:
        raise KeyError(slug)
    from engineverse.models3d import arrow, box, grid, label, scene

    entry = _subject_map()[topic["subject"]]
    caption = (
        f"This 3D learning model separates the problem definition, the {topic['formula']['name']} model, and a verification step. "
        f"For {entry['name']}, {topic['focus']} A real design still requires the stated assumptions, validated inputs, and applicable safety checks."
    )
    return {
        "title": topic["title"],
        "caption": caption,
        "scene": scene([
            grid(6, 6, position=(0, -1.25, 0)),
            box((-2.0, 0.0, 0), size=(1.15, 0.75, 0.75), color="#4f7cff"),
            box((0.0, 0.0, 0), size=(1.35, 1.0, 0.9), color="#35d39a"),
            box((2.0, 0.0, 0), size=(1.15, 0.75, 0.75), color="#ff9f43"),
            arrow((-1.34, 0.0, 0), (-0.76, 0.0, 0), color="#e6ecff", shaft=0.03, head=0.16, radius=0.05),
            arrow((0.76, 0.0, 0), (1.34, 0.0, 0), color="#e6ecff", shaft=0.03, head=0.16, radius=0.05),
        ], labels=[
            label("define", (-2.0, 0.62, 0)),
            label("apply model", (0.0, 0.72, 0)),
            label("verify", (2.0, 0.62, 0)),
            label("assumptions matter", (0.0, -0.88, 0)),
        ], distance=7.2, pitch=17, yaw=25, spin=0.0),
    }


def generated_models() -> dict[str, dict]:
    return {slug: model_for_topic(slug) for slug in TOPIC_BY_SLUG}


def _topic_tokens(text: str) -> set[str]:
    return {word for word in re.findall(r"[a-z0-9]+", text.lower()) if len(word) > 2}


def resolve_question_topic(question: dict, topics: list[dict]) -> str | None:
    """Attach a hand-written subject question to the closest topic by tag overlap."""
    candidates = [topic for topic in topics if topic["subject"] == question.get("subject")]
    if not candidates:
        return None
    wanted = _topic_tokens(" ".join([question.get("title", ""), question.get("statement", ""), *question.get("tags", [])]))
    ranked = []
    for index, topic in enumerate(candidates):
        terms = _topic_tokens(" ".join([topic["title"], topic["summary"], *topic.get("tags", [])]))
        ranked.append((len(wanted & terms), -index, topic))
    return _slugify(max(ranked, key=lambda row: (row[0], row[1]))[2]["title"]) if ranked else _slugify(candidates[0]["title"])


def questions_for_topics(topics: list[dict]) -> list[dict]:
    """One concept-check question per topic, plus authored Cyber Security MCQs."""
    from seed_data import notes_extra

    questions: list[dict] = []
    topic_slugs = [_slugify(topic["title"]) for topic in topics]
    for index, topic in enumerate(topics):
        slug = topic_slugs[index]
        formula = topic.get("formula") or notes_extra.formula(slug) or {"name": "the topic's governing model"}
        custom = topic.get("quiz")
        if custom:
            stem = custom["stem"]
            options = list(custom["options"])
            correct = int(custom["correct"])
            explanation = custom["explanation"]
            difficulty = topic["difficulty"]
        else:
            same_subject = [i for i, other in enumerate(topics) if i != index and other["subject"] == topic["subject"]]
            same_branch = [i for i, other in enumerate(topics) if i != index and other.get("branch") == topic.get("branch")]
            alternatives = same_subject + [i for i in same_branch if i not in same_subject]
            alternatives += [i for i in range(len(topics)) if i != index and i not in alternatives]
            distractors = [topics[i]["summary"] for i in alternatives[:3]]
            while len(distractors) < 3:
                distractors.append("It is a different model; the stated assumptions and variables do not describe this topic.")
            stem = f"Which statement best captures the central idea of {topic['title']}?"
            options = [topic["summary"], *distractors]
            correct = 0
            explanation = f"{topic.get('definition') or topic['summary']} The key relation is {formula['name']}; check its assumptions before applying it."
            difficulty = topic["difficulty"]
        # Keep the answer from occupying the first slot on every generated
        # question. Rotate deterministically so reseeds remain stable while the
        # answer key is not a visible position pattern.
        if options:
            shift = index % len(options)
            options = options[shift:] + options[:shift]
            correct = (correct - shift) % len(options)
        questions.append({
            "subject": topic["subject"],
            "topic": slug,
            "title": f"Concept check: {topic['title']}",
            "difficulty": difficulty,
            "statement": stem,
            "options": options,
            "correct": correct,
            "explanation": explanation,
            "tags": list(dict.fromkeys([*topic.get("tags", []), "concept-check"])),
            "source": "EngineVerse authored learning check",
        })
    return questions


# Fail immediately if a catalogue edit introduces an uncovered subject. This is
# intentionally independent of DB lookup so a missing lesson cannot disappear
# silently through dict.get() in the seed path.
SUBJECT_SLUGS = {row[0] for row in SUBJECTS}
_existing_subjects = {topic["subject"] for topic in _existing_topics()}
_missing_subjects = SUBJECT_SLUGS - _existing_subjects
_unmapped = _missing_subjects - set(STARTERS) - {"cryptography-security"}
if _unmapped:
    raise KeyError(f"Subjects have no starter lesson: {sorted(_unmapped)}")
_unknown_starters = set(STARTERS) - SUBJECT_SLUGS
if _unknown_starters:
    raise KeyError(f"Starter lesson points to unknown subject: {sorted(_unknown_starters)}")
