"""Topic content for Mechanical, ECE, EEE, Civil, Chemical and remaining first-year subjects."""

from .topics_cse import t

TOPICS = [
    # =====================================================================
    # FLUID MECHANICS  (flagship topic - spec §75)
    # =====================================================================
    t(
        "fluid-mechanics", "Bernoulli's Equation",
        summary="Energy conservation for a flowing fluid: pressure, velocity and elevation trade against each other along a streamline.",
        difficulty="medium", minutes=35,
        tags=["bernoulli", "fluid", "energy", "pressure", "venturi", "aerodynamics"],
        simple=(
            "When a fluid speeds up, its pressure drops. Blow across a strip of paper and it lifts - the fast air "
            "above it has lower pressure than the still air below. Bernoulli's equation is the exact bookkeeping "
            "behind that observation."
        ),
        definition=(
            "For steady, incompressible, inviscid flow along a streamline, the sum of pressure energy, kinetic "
            "energy and potential energy per unit volume is constant: p + (1/2)rho*v^2 + rho*g*h = constant."
        ),
        intuition=(
            "Bernoulli's equation is simply the work-energy theorem applied to a fluid element. No energy is "
            "created or destroyed, so if the fluid gains speed it must pay for it out of pressure or height. "
            "Every surprising fluid effect - lift, carburettor suction, a shower curtain pulling inward - is "
            "this trade being made visible."
        ),
        points=[
            "Pressure head p/(rho*g), velocity head v^2/(2g) and elevation head h all have units of length.",
            "The equation applies along a single streamline; comparing across streamlines needs additional care.",
            "Real fluids lose energy to friction, so engineers add a head-loss term h_f between two sections.",
            "Compressible flow (Mach > 0.3) and unsteady flow both invalidate the incompressible form.",
        ],
        formula={
            "name": "Bernoulli's equation (per unit volume)",
            "latex": "p + \\frac{1}{2}\\rho v^{2} + \\rho g h = \\text{constant}",
            "variables": [
                {"s": "p", "n": "static pressure", "u": "Pa"},
                {"s": "\\rho", "n": "fluid density", "u": "kg/m^3"},
                {"s": "v", "n": "flow velocity", "u": "m/s"},
                {"s": "g", "n": "gravitational acceleration, 9.81", "u": "m/s^2"},
                {"s": "h", "n": "elevation above the datum", "u": "m"},
            ],
            "conditions": "Steady, incompressible, inviscid, along a streamline, no shaft work or heat transfer.",
        },
        derivation=(
            "Start with Euler's equation for inviscid flow along a streamline:\n\n"
            "$$\\frac{dp}{\\rho} + v\\,dv + g\\,dh = 0$$\n\n"
            "For an incompressible fluid the density is constant, so every term is an exact differential and can "
            "be integrated directly between two points on the same streamline:\n\n"
            "$$\\int_1^2 \\frac{dp}{\\rho} + \\int_1^2 v\\,dv + g\\int_1^2 dh = 0$$\n\n"
            "$$\\frac{p_2 - p_1}{\\rho} + \\frac{v_2^2 - v_1^2}{2} + g(h_2 - h_1) = 0$$\n\n"
            "Rearranging gives the familiar form:\n\n"
            "$$p_1 + \\frac{1}{2}\\rho v_1^2 + \\rho g h_1 = p_2 + \\frac{1}{2}\\rho v_2^2 + \\rho g h_2$$\n\n"
            "Dividing throughout by rho*g expresses the same statement in metres of head, which is how it is "
            "used in hydraulic engineering."
        ),
        example={
            "problem": (
                "Water flows through a horizontal pipe that narrows from 100 mm to 50 mm diameter. The pressure "
                "in the wide section is 200 kPa and the velocity is 2 m/s. Find the pressure in the narrow section."
            ),
            "approach": (
                "Use continuity to find the velocity in the narrow section, then apply Bernoulli between the two "
                "sections (horizontal, so the elevation terms cancel)."
            ),
            "solution": (
                "**Step 1 - continuity.**\n"
                "$$A_1 v_1 = A_2 v_2 \\Rightarrow v_2 = v_1 \\left(\\frac{d_1}{d_2}\\right)^2 "
                "= 2 \\times \\left(\\frac{100}{50}\\right)^2 = 8\\ \\text{m/s}$$\n\n"
                "**Step 2 - Bernoulli.**\n"
                "$$p_2 = p_1 + \\frac{1}{2}\\rho(v_1^2 - v_2^2) "
                "= 200{,}000 + \\frac{1}{2}(1000)(2^2 - 8^2)$$\n"
                "$$p_2 = 200{,}000 - 30{,}000 = 170{,}000\\ \\text{Pa}$$"
            ),
            "answer": "170 kPa. The pressure fell by 30 kPa as the fluid quadrupled its speed.",
        },
        applications=[
            "Aircraft wings and aerofoils: the pressure difference across the surface produces lift.",
            "Venturi meters and orifice plates measure flow rate from a pressure difference.",
            "Carburettors, spray guns and aspirators use the low pressure at a throat to draw in fuel or liquid.",
            "Pitot tubes on aircraft measure airspeed from stagnation and static pressure.",
            "Pump and pipeline design, chimney draught and blood-flow analysis in arteries.",
        ],
        mistakes=[
            "Applying Bernoulli across two different streamlines, or through a pump or turbine, without adding the work term.",
            "Ignoring friction in a long pipe and getting an optimistic answer - add the head loss.",
            "Forgetting that the equation needs absolute or gauge pressure used consistently at both sections.",
            "Using it for gases at high speed where compressibility matters.",
        ],
        exam=[
            "State Bernoulli's equation with all assumptions and derive it from Euler's equation.",
            "A venturi meter has inlet diameter 200 mm and throat diameter 100 mm. Derive the discharge formula.",
            "Water flows from a large tank through a 25 mm nozzle located 4 m below the free surface. Find the exit velocity.",
            "Explain the terms pressure head, velocity head and elevation head with units.",
        ],
        interview=[
            "Why does an aeroplane wing generate lift - and is Bernoulli the whole story?",
            "How does a Venturi meter measure flow, and what is its discharge coefficient?",
            "Where does Bernoulli's equation break down in real engineering practice?",
        ],
        diagram="bernoulli",
        industry=(
            "In practice engineers rarely use raw Bernoulli. They use the extended energy equation with a pump "
            "head, turbine head and a friction loss term from the Darcy-Weisbach equation, and they apply "
            "correction factors (kinetic energy correction factor alpha) for non-uniform velocity profiles. "
            "CFD tools solve the full Navier-Stokes equations, but Bernoulli remains the sanity check every "
            "engineer runs first."
        ),
    ),
    t(
        "fluid-mechanics", "Fluid Statics & Manometry",
        summary="Pressure in a fluid at rest, and how a simple column of liquid measures it.",
        difficulty="easy", minutes=25, tags=["fluid-statics", "manometer", "pressure", "buoyancy"],
        simple="Water pushes harder the deeper you go, because there is more water above you. A manometer just lets a liquid column show you that push.",
        definition="Fluid statics studies fluids at rest, where shear stress is zero and pressure acts equally in all directions at a point. Pressure varies with depth as dp/dh = rho*g.",
        intuition="A fluid at rest cannot resist shear, so the only stress is normal pressure. That single fact leads directly to Pascal's law, manometers and buoyancy.",
        points=[
            "Pressure at depth h in a liquid is p = p_surface + rho*g*h.",
            "Pascal's law: pressure applied to a confined fluid transmits undiminished in all directions - the basis of hydraulics.",
            "A manometer balances an unknown pressure against a known liquid column.",
            "Buoyant force equals the weight of displaced fluid (Archimedes), acting through the centre of buoyancy.",
        ],
        formula={
            "name": "Hydrostatic pressure and buoyancy",
            "latex": "p = p_0 + \\rho g h, \\qquad F_b = \\rho g V_{displaced}",
            "variables": [
                {"s": "p_0", "n": "surface pressure", "u": "Pa"},
                {"s": "h", "n": "depth below the surface", "u": "m"},
                {"s": "V_{displaced}", "n": "volume of fluid displaced", "u": "m^3"},
            ],
            "conditions": "Incompressible fluid, uniform gravity, at rest.",
        },
        example={
            "problem": "A U-tube manometer containing mercury (specific gravity 13.6) shows a 150 mm difference. Find the gauge pressure.",
            "approach": "Convert the mercury column to an equivalent pressure using rho = SG x 1000.",
            "solution": "p = 13.6 x 1000 x 9.81 x 0.150 = 20,012 Pa.",
            "answer": "About 20.0 kPa gauge.",
        },
        applications=[
            "Hydraulic presses, brakes and jacks.",
            "Dam and retaining wall design, where pressure grows linearly with depth.",
            "Ship and submarine stability, hydrometers and barometers.",
        ],
        mistakes=[
            "Using gauge pressure in one term and absolute in another.",
            "Forgetting that pressure acts on the projected area when computing forces on curved surfaces.",
            "Confusing the centre of pressure with the centroid - the centre of pressure is always deeper.",
        ],
        exam=[
            "Derive the total pressure and centre of pressure on a vertically immersed plane surface.",
            "Explain Pascal's law and its application in a hydraulic press.",
            "State and prove Archimedes' principle.",
        ],
        interview=[
            "Why are dams thicker at the bottom?",
            "How does a submarine control its depth?",
            "What is the difference between the centre of pressure and the centre of gravity?",
        ],
    ),
    # =====================================================================
    # THERMODYNAMICS
    # =====================================================================
    t(
        "thermodynamics", "Entropy & the Second Law",
        summary="Why some processes never happen in reverse, and the quantity that measures the direction of time.",
        difficulty="hard", minutes=35, tags=["entropy", "second-law", "carnot", "irreversibility"],
        simple=(
            "Heat flows from hot to cold on its own, never the other way. Entropy is the number that always goes "
            "up when that happens - it counts how spread out the energy has become."
        ),
        definition=(
            "Entropy is a state property defined for a reversible process as dS = deltaQ_rev / T. The second law "
            "states that the entropy of an isolated system never decreases; it is constant only for reversible "
            "processes and increases for all real (irreversible) ones."
        ),
        intuition=(
            "There are vastly more disordered arrangements than ordered ones, so a system left alone drifts toward "
            "disorder simply because that is overwhelmingly more likely. Entropy quantifies that drift, and the "
            "second law is why you cannot build a perpetual motion machine."
        ),
        points=[
            "Entropy is a property; entropy generation is not - it is created by irreversibility and can never be destroyed.",
            "The Carnot efficiency is the ceiling for any heat engine operating between two temperatures.",
            "Friction, unrestrained expansion, mixing and finite temperature differences all generate entropy.",
            "Isentropic means both adiabatic and reversible - a useful idealisation, never achieved exactly.",
        ],
        formula={
            "name": "Entropy change and Carnot efficiency",
            "latex": "dS = \\frac{\\delta Q_{rev}}{T}, \\qquad \\eta_{Carnot} = 1 - \\frac{T_L}{T_H}",
            "variables": [
                {"s": "T", "n": "absolute temperature", "u": "K"},
                {"s": "\\delta Q_{rev}", "n": "reversible heat transfer", "u": "J"},
                {"s": "T_H, T_L", "n": "source and sink temperatures", "u": "K"},
            ],
            "conditions": "Temperatures must be absolute (kelvin). Carnot applies to reversible cycles only.",
        },
        derivation=(
            "Clausius observed that for any reversible cyclic process the cyclic integral of deltaQ/T vanishes:\n\n"
            "$$\\oint \\frac{\\delta Q_{rev}}{T} = 0$$\n\n"
            "A quantity whose cyclic integral is zero must be a state function, so we define entropy S such that "
            "dS = deltaQ_rev / T. For an irreversible process between the same two states, the Clausius "
            "inequality gives a smaller integral, so:\n\n"
            "$$\\Delta S \\geq \\int \\frac{\\delta Q}{T}$$\n\n"
            "For an isolated system deltaQ = 0, therefore Delta S >= 0 - the principle of entropy increase."
        ),
        example={
            "problem": "A heat engine receives 500 kJ from a source at 800 K and rejects heat to a sink at 300 K. What is the maximum possible work output?",
            "approach": "The maximum work comes from a reversible (Carnot) engine operating between those temperatures.",
            "solution": "eta_max = 1 - 300/800 = 0.625. W_max = 0.625 x 500 = 312.5 kJ.",
            "answer": "312.5 kJ. Any real engine delivers less, and the difference is the work lost to irreversibility.",
        },
        applications=[
            "Power plants, refrigeration and heat pumps - all bounded by the second law.",
            "Exergy analysis identifies where a plant actually wastes potential, not just energy.",
            "Chemical equilibrium, phase change and reaction spontaneity.",
            "Information theory: Shannon entropy is formally the same construct.",
        ],
        mistakes=[
            "Using Celsius instead of kelvin in the Carnot formula - a very common exam error.",
            "Treating entropy as 'disorder' in a loose sense and losing the quantitative meaning.",
            "Assuming an adiabatic process is isentropic; it must also be reversible.",
        ],
        exam=[
            "State the Kelvin-Planck and Clausius statements and show they are equivalent.",
            "Prove that no engine operating between two reservoirs can exceed Carnot efficiency.",
            "Calculate the entropy change when an ideal gas expands isothermally and when it mixes adiabatically.",
        ],
        interview=[
            "Explain entropy to a first-year student, then to a design engineer.",
            "What is exergy and why is it more useful than energy in an audit?",
            "Why can a heat pump have a COP greater than 1 while an engine cannot have efficiency greater than 1?",
        ],
        diagram="carnot-cycle",
        industry=(
            "Real plants are designed against isentropic efficiencies: turbines around 85-90%, compressors 70-85%. "
            "The gap between the ideal isentropic exit state and the real one is the design target, and it shows up "
            "directly as fuel cost. Exergy destruction per component is the standard way to rank where to spend "
            "the next capital budget."
        ),
    ),
    t(
        "thermodynamics", "First Law & Energy Balance",
        summary="Energy accounting for a system: what goes in, what comes out, and what is stored.",
        difficulty="medium", minutes=25, tags=["first-law", "energy", "enthalpy", "control-volume"],
        simple="Energy cannot be created or destroyed. Whatever enters a system either leaves or stays inside - and the first law is just that sentence written as an equation.",
        definition="The first law states that energy is conserved. For a closed system, Q - W = dU. For an open (control volume) system in steady state, the rate of energy entering equals the rate leaving, with enthalpy carrying the flow work.",
        intuition="Enthalpy exists because pushing fluid into a system costs work (pV). Bundling that flow work with internal energy makes open-system balances far simpler.",
        points=[
            "Closed system: Q - W = Delta U. Open steady system: sum(m_dot * h + ke + pe) in = out.",
            "Enthalpy h = u + pv; it is the natural property for flowing fluids.",
            "Perpetual motion machines of the first kind violate this law.",
            "Steady flow energy equation underpins turbines, compressors, nozzles and heat exchangers.",
        ],
        formula={
            "name": "Steady flow energy equation",
            "latex": "\\dot{Q} - \\dot{W} = \\dot{m}\\left[(h_2 - h_1) + \\frac{v_2^2 - v_1^2}{2} + g(z_2 - z_1)\\right]",
            "variables": [
                {"s": "\\dot{Q}", "n": "heat transfer rate", "u": "W"},
                {"s": "\\dot{W}", "n": "shaft work rate", "u": "W"},
                {"s": "\\dot{m}", "n": "mass flow rate", "u": "kg/s"},
                {"s": "h", "n": "specific enthalpy", "u": "J/kg"},
            ],
            "conditions": "Steady state, one inlet and one outlet, uniform properties at each section.",
        },
        example={
            "problem": "Steam enters an adiabatic turbine at h1 = 3400 kJ/kg and leaves at h2 = 2700 kJ/kg with a mass flow of 10 kg/s. Neglect kinetic and potential changes. Find the power output.",
            "approach": "Adiabatic means Q = 0, so the SFEE reduces to W = m_dot (h1 - h2).",
            "solution": "W = 10 x (3400 - 2700) = 7000 kW.",
            "answer": "7 MW.",
        },
        applications=[
            "Turbine, compressor, pump and heat exchanger sizing.",
            "Engine performance testing and fuel consumption calculation.",
            "HVAC load calculation and refrigeration cycle analysis.",
        ],
        mistakes=[
            "Forgetting flow work and using internal energy instead of enthalpy for open systems.",
            "Sign convention errors on work done by versus on the system.",
            "Ignoring kinetic energy in nozzles, where it is the dominant term.",
        ],
        exam=[
            "Derive the steady flow energy equation from the first law for a control volume.",
            "Apply the SFEE to a nozzle, a throttle and a compressor, simplifying each.",
            "Explain why enthalpy rather than internal energy appears in open-system analysis.",
        ],
        interview=[
            "Why does temperature stay constant across an ideal throttle valve?",
            "How do you measure turbine efficiency in the field?",
            "What is the difference between a closed and an open system?",
        ],
    ),
    # =====================================================================
    # STRENGTH OF MATERIALS
    # =====================================================================
    t(
        "strength-of-materials", "Stress, Strain & Hooke's Law",
        summary="How materials respond to load, and the linear region every design lives inside.",
        difficulty="medium", minutes=30, tags=["stress", "strain", "youngs-modulus", "elasticity"],
        simple="Pull a rubber band a little and it springs back. Pull too hard and it stays stretched. Stress is the internal push or pull per unit area; strain is how much it stretched.",
        definition="Stress is the internal resisting force per unit area (sigma = P/A). Strain is the deformation per unit original length (epsilon = delta/L). Within the elastic limit they are proportional: sigma = E * epsilon (Hooke's law).",
        intuition="Designers do not limit force; they limit stress, because stress is what a material actually feels. Normalising by area is what lets one material property apply to any component size.",
        points=[
            "Normal stress acts perpendicular to the section; shear stress acts parallel.",
            "The stress-strain curve has proportional limit, elastic limit, yield point, ultimate strength and fracture.",
            "Ductile materials neck before fracture; brittle materials fracture with little warning.",
            "Poisson's ratio links lateral contraction to axial extension.",
        ],
        formula={
            "name": "Axial deformation",
            "latex": "\\sigma = \\frac{P}{A}, \\qquad \\epsilon = \\frac{\\delta}{L}, \\qquad \\delta = \\frac{PL}{AE}",
            "variables": [
                {"s": "P", "n": "axial load", "u": "N"},
                {"s": "A", "n": "cross-sectional area", "u": "m^2"},
                {"s": "E", "n": "Young's modulus", "u": "Pa"},
                {"s": "\\delta", "n": "elongation", "u": "m"},
            ],
            "conditions": "Uniform bar, axial load through the centroid, linear elastic material.",
        },
        example={
            "problem": "A 20 mm diameter steel bar 2 m long carries a 50 kN tensile load. E = 200 GPa. Find the stress and elongation.",
            "approach": "Compute the area, then stress, then elongation from Hooke's law.",
            "solution": "A = pi x (0.020)^2 / 4 = 3.1416e-4 m^2. sigma = 50,000 / 3.1416e-4 = 159.2 MPa. delta = PL/(AE) = (50,000 x 2)/(3.1416e-4 x 200e9) = 1.59 mm.",
            "answer": "Stress 159 MPa, elongation 1.59 mm. Both are well inside the elastic range for structural steel.",
        },
        applications=[
            "Structural steel design, machine elements, fasteners and pressure vessels.",
            "Finite element analysis begins from exactly these relations.",
            "Failure analysis and fatigue life estimation.",
        ],
        mistakes=[
            "Using engineering stress past the ultimate point where the area has changed dramatically.",
            "Confusing yield strength with ultimate tensile strength in a design check.",
            "Ignoring stress concentration at holes and fillets.",
        ],
        exam=[
            "Draw the stress-strain diagram for mild steel and label every significant point.",
            "Derive the expression for elongation of a tapered bar under axial load.",
            "Define Poisson's ratio and relate E, G and K.",
        ],
        interview=[
            "What is the difference between stress and pressure?",
            "Why do brittle materials fail suddenly?",
            "What is a stress concentration factor and how do you reduce it?",
        ],
        diagram="stress-strain",
    ),
    # =====================================================================
    # ECE
    # =====================================================================
    t(
        "digital-electronics", "Boolean Algebra & Karnaugh Maps",
        summary="Simplifying logic expressions so circuits need fewer gates - the manual version of what synthesis tools automate.",
        difficulty="medium", minutes=30, tags=["boolean", "kmap", "logic", "minimization"],
        simple="A Karnaugh map lays a truth table out as a grid so that adjacent cells differ by only one variable. Grouping neighbours cancels the variable that changes.",
        definition="Boolean algebra manipulates binary variables with AND, OR and NOT under a set of identities. A Karnaugh map is a graphical arrangement of minterms in Gray-code order that allows adjacency-based minimisation of sum-of-products or product-of-sums expressions.",
        intuition="Two adjacent cells differ in exactly one variable, and that variable appears both complemented and uncomplemented across the pair - so it cancels. Larger groups cancel more variables, which is why bigger groups mean fewer gates.",
        points=[
            "Group sizes must be powers of two: 1, 2, 4, 8.",
            "The map wraps around - the leftmost and rightmost columns are adjacent.",
            "Every 1 must be covered; overlapping groups are allowed and often necessary.",
            "Beyond four or five variables K-maps become impractical and the Quine-McCluskey method or a synthesis tool takes over.",
        ],
        example={
            "problem": "Minimise F(A,B,C) = sum of minterms 0, 2, 5, 7.",
            "approach": "Plot the minterms on a three-variable K-map, then form the largest legal groups.",
            "solution": "Minterms 0 and 2 are adjacent, giving A'C'. Minterms 5 and 7 are adjacent, giving AC. So F = A'C' + AC.",
            "answer": "F = A'C' + AC - an XNOR of A and C, independent of B.",
        },
        applications=[
            "Combinational circuit design, decoder and multiplexer logic.",
            "FPGA synthesis and ASIC standard-cell optimisation.",
            "Test generation and hazard elimination.",
        ],
        mistakes=[
            "Forming groups that are not powers of two.",
            "Forgetting the wrap-around adjacency.",
            "Leaving a minterm uncovered, or adding a redundant group.",
        ],
        exam=[
            "Minimise a four-variable function using a K-map and implement it with NAND gates only.",
            "State and prove De Morgan's theorems.",
            "Distinguish between SOP and POS forms and convert between them.",
        ],
        interview=[
            "Why do K-maps use Gray code ordering?",
            "What is a static hazard and how do you remove it?",
            "Why are NAND and NOR called universal gates?",
        ],
        diagram="kmap",
    ),
    t(
        "signals-systems", "Convolution & LTI Systems",
        summary="The single operation that completely characterises any linear time-invariant system.",
        difficulty="hard", minutes=35, tags=["convolution", "lti", "impulse-response", "signals"],
        simple="Feed a system a single sharp pulse and record what comes out. That recording - the impulse response - lets you predict the output for any input at all.",
        definition="For a linear time-invariant system with impulse response h(t), the output to any input x(t) is the convolution integral y(t) = integral of x(tau) h(t - tau) d tau. In discrete time this becomes a summation.",
        intuition="Any signal can be built from shifted, scaled impulses. Linearity lets you add the responses, and time invariance lets you shift them - so the impulse response is a complete description of the system.",
        points=[
            "Convolution is commutative, associative and distributive.",
            "In the frequency domain convolution becomes multiplication: Y(w) = X(w) H(w).",
            "A system is stable if the impulse response is absolutely integrable, and causal if h(t) = 0 for t < 0.",
            "The length of a discrete convolution of sequences of length N and M is N + M - 1.",
        ],
        formula={
            "name": "Convolution integral and sum",
            "latex": "y(t) = \\int_{-\\infty}^{\\infty} x(\\tau)\\,h(t-\\tau)\\,d\\tau, \\qquad y[n] = \\sum_{k=-\\infty}^{\\infty} x[k]\\,h[n-k]",
            "variables": [
                {"s": "x", "n": "input signal", "u": "-"},
                {"s": "h", "n": "impulse response", "u": "-"},
                {"s": "\\tau, k", "n": "dummy variable of summation", "u": "-"},
            ],
            "conditions": "System must be linear and time invariant.",
        },
        example={
            "problem": "An LTI system has h[n] = {1, 2, 1}. Find the output for x[n] = {1, 1}.",
            "approach": "Perform discrete convolution; the result has length 2 + 3 - 1 = 4.",
            "solution": "y[0] = 1x1 = 1; y[1] = 1x2 + 1x1 = 3; y[2] = 1x1 + 1x2 = 3; y[3] = 1x1 = 1.",
            "answer": "y[n] = {1, 3, 3, 1}.",
        },
        applications=[
            "Audio reverberation and equalisation, image blur and sharpening.",
            "Channel modelling in communications and equaliser design.",
            "Neural network convolutional layers are literally this operation.",
        ],
        mistakes=[
            "Reversing the wrong sequence, or forgetting to flip h at all.",
            "Getting the output length wrong.",
            "Applying convolution to a time-varying or non-linear system.",
        ],
        exam=[
            "Compute the convolution of two given discrete sequences, showing every step.",
            "State and prove the convolution property of the Fourier transform.",
            "Determine causality and stability from a given impulse response.",
        ],
        interview=[
            "Why is convolution multiplication in the frequency domain?",
            "What is the difference between convolution and cross-correlation?",
            "How is convolution used in a CNN?",
        ],
    ),
    t(
        "electromagnetic-fields", "Maxwell's Equations",
        summary="Four equations that unify electricity, magnetism and light - the foundation of all electromagnetics.",
        difficulty="hard", minutes=35, tags=["maxwell", "electromagnetics", "waves"],
        simple="Changing electric fields make magnetic fields, and changing magnetic fields make electric fields. Together they can sustain each other and travel through empty space - that is light.",
        definition="Maxwell's equations are Gauss's law for electricity, Gauss's law for magnetism, Faraday's law of induction and the Ampere-Maxwell law. Together with the Lorentz force they completely describe classical electromagnetism.",
        intuition="The displacement current term is Maxwell's great addition: without it the equations are inconsistent for a charging capacitor, and with it they predict electromagnetic waves travelling at the speed of light.",
        points=[
            "Gauss (E): electric flux out of a closed surface equals enclosed charge over epsilon_0.",
            "Gauss (B): magnetic monopoles do not exist; magnetic field lines always close.",
            "Faraday: a changing magnetic flux induces an electric field.",
            "Ampere-Maxwell: currents and changing electric fields both produce magnetic fields.",
        ],
        formula={
            "name": "Maxwell's equations in differential form",
            "latex": "\\nabla \\cdot \\mathbf{E} = \\frac{\\rho}{\\varepsilon_0}, \\quad \\nabla \\cdot \\mathbf{B} = 0, \\quad \\nabla \\times \\mathbf{E} = -\\frac{\\partial \\mathbf{B}}{\\partial t}, \\quad \\nabla \\times \\mathbf{B} = \\mu_0 \\mathbf{J} + \\mu_0 \\varepsilon_0 \\frac{\\partial \\mathbf{E}}{\\partial t}",
            "variables": [
                {"s": "\\rho", "n": "charge density", "u": "C/m^3"},
                {"s": "\\mathbf{J}", "n": "current density", "u": "A/m^2"},
                {"s": "\\varepsilon_0", "n": "permittivity of free space", "u": "F/m"},
                {"s": "\\mu_0", "n": "permeability of free space", "u": "H/m"},
            ],
            "conditions": "Classical regime; quantum effects require QED.",
        },
        derivation=(
            "Take the curl of Faraday's law and substitute the Ampere-Maxwell law:\n\n"
            "$$\\nabla \\times (\\nabla \\times \\mathbf{E}) = -\\frac{\\partial}{\\partial t}(\\nabla \\times \\mathbf{B})$$\n\n"
            "Using the vector identity and the source-free condition:\n\n"
            "$$\\nabla^2 \\mathbf{E} = \\mu_0 \\varepsilon_0 \\frac{\\partial^2 \\mathbf{E}}{\\partial t^2}$$\n\n"
            "This is a wave equation with speed $c = 1/\\sqrt{\\mu_0 \\varepsilon_0} = 3 \\times 10^8$ m/s - "
            "the speed of light, which is how light was shown to be an electromagnetic wave."
        ),
        applications=[
            "Antenna design, radar, wireless communication and microwave engineering.",
            "Optical fibres, photonics and laser design.",
            "Motor and transformer design, electromagnetic compatibility testing.",
        ],
        mistakes=[
            "Omitting the displacement current term in a time-varying problem.",
            "Applying integral forms without checking the symmetry assumptions.",
            "Forgetting boundary conditions at material interfaces.",
        ],
        exam=[
            "Write Maxwell's equations in both differential and integral form and explain each physically.",
            "Derive the electromagnetic wave equation and the expression for the speed of light.",
            "State the boundary conditions for E and B at a dielectric interface.",
        ],
        interview=[
            "Why was the displacement current term necessary?",
            "How does an antenna radiate, in one paragraph?",
            "What is the physical meaning of the Poynting vector?",
        ],
    ),
    # =====================================================================
    # EEE
    # =====================================================================
    t(
        "circuit-theory", "Kirchhoff's Laws",
        summary="The two conservation rules - charge and energy - that let you solve any circuit.",
        difficulty="medium", minutes=30, tags=["kcl", "kvl", "circuit", "nodal", "mesh"],
        simple="KCL says current flowing into a junction must flow out - charge cannot pile up. KVL says the voltages around any loop add to zero - you cannot get energy for free by going in a circle.",
        definition="Kirchhoff's Current Law: the algebraic sum of currents at any node is zero (conservation of charge). Kirchhoff's Voltage Law: the algebraic sum of voltages around any closed loop is zero (conservation of energy).",
        intuition="These are not circuit-specific tricks; they are conservation laws applied to a lumped network. Every circuit analysis method - nodal, mesh, Thevenin - is built on them.",
        points=[
            "KCL applies at nodes and gives (n-1) independent equations for n nodes.",
            "KVL applies to independent loops; there are b - n + 1 of them for b branches.",
            "Sign convention must be chosen once and applied consistently.",
            "Nodal analysis uses KCL with node voltages; mesh analysis uses KVL with loop currents.",
        ],
        example={
            "problem": "A 12 V battery feeds two resistors in parallel, 6 ohm and 3 ohm. Find the total current.",
            "approach": "Apply KVL to each branch to get branch currents, then KCL at the node for the total.",
            "solution": "I1 = 12/6 = 2 A, I2 = 12/3 = 4 A. By KCL, I_total = 2 + 4 = 6 A.",
            "answer": "6 A. Equivalently, R_eq = 2 ohm and I = 12/2 = 6 A.",
        },
        applications=[
            "Every circuit from a phone charger to a power grid.",
            "PCB design verification and fault diagnosis.",
            "Power system load flow, which is Kirchhoff's laws at scale.",
        ],
        mistakes=[
            "Inconsistent sign conventions leading to equations that look wrong but are actually fine.",
            "Writing KVL around a loop that is not independent, giving a redundant equation.",
            "Forgetting that KCL applies to a closed surface, not just a point.",
        ],
        exam=[
            "State Kirchhoff's laws and solve a two-loop network by mesh analysis.",
            "Solve a three-node circuit by nodal analysis.",
            "Derive the relationship between branch, node and independent loop counts.",
        ],
        interview=[
            "What physical principle does each of Kirchhoff's laws express?",
            "When is nodal analysis preferable to mesh analysis?",
            "Do Kirchhoff's laws hold at high frequency? Why or why not?",
        ],
        diagram="kirchhoff",
    ),
    t(
        "electrical-machines-1", "Transformers",
        summary="Transferring electrical power between circuits at different voltages using a shared magnetic field.",
        difficulty="medium", minutes=30, tags=["transformer", "emf", "efficiency", "testing"],
        simple="Two coils wound on the same iron core. A changing current in the first induces a voltage in the second - and the ratio of turns sets the ratio of voltages.",
        definition="A transformer is a static device that transfers electrical energy between two or more circuits through electromagnetic induction, changing voltage and current while keeping frequency and (ideally) power constant.",
        intuition="Power is the product of voltage and current, so stepping voltage up necessarily steps current down. That is why transmission lines run at hundreds of kilovolts - losses scale with the square of current.",
        points=[
            "EMF equation: E = 4.44 f N phi_max for a sinusoidal supply.",
            "Turns ratio equals the voltage ratio; the current ratio is its inverse.",
            "Open-circuit test gives core losses; short-circuit test gives copper losses and equivalent impedance.",
            "Maximum efficiency occurs when copper loss equals core loss.",
        ],
        formula={
            "name": "Transformer EMF and efficiency",
            "latex": "E = 4.44\\, f N \\phi_{max}, \\qquad \\eta = \\frac{\\text{output}}{\\text{output} + P_{core} + P_{cu}}",
            "variables": [
                {"s": "f", "n": "supply frequency", "u": "Hz"},
                {"s": "N", "n": "number of turns", "u": "-"},
                {"s": "\\phi_{max}", "n": "maximum flux", "u": "Wb"},
            ],
            "conditions": "Sinusoidal excitation, negligible leakage for the EMF equation.",
        },
        example={
            "problem": "A 2300/230 V transformer draws 2 A at 0.2 power factor on open circuit. Find the core loss.",
            "approach": "Open-circuit input power equals core loss, since copper loss is negligible at no load.",
            "solution": "P_core = V x I x cos(phi) = 2300 x 2 x 0.2 = 920 W.",
            "answer": "920 W of core loss.",
        },
        applications=[
            "Power transmission and distribution networks.",
            "Isolation and impedance matching in electronics and audio.",
            "Instrument transformers for metering and protection.",
        ],
        mistakes=[
            "Assuming a transformer can change frequency or DC voltage - it cannot.",
            "Confusing rated kVA with rated kW.",
            "Neglecting regulation when sizing for a load at the end of a long feeder.",
        ],
        exam=[
            "Derive the EMF equation of a transformer from first principles.",
            "Describe the open-circuit and short-circuit tests and what each determines.",
            "Derive the condition for maximum efficiency.",
        ],
        interview=[
            "Why are transformers rated in kVA rather than kW?",
            "Why is the transformer core laminated?",
            "What is all-day efficiency and why does it matter for distribution transformers?",
        ],
    ),
    t(
        "power-systems", "Per-Unit System & Fault Analysis",
        summary="Normalising power system quantities so machines of different ratings can be compared directly.",
        difficulty="hard", minutes=30, tags=["per-unit", "fault", "symmetrical-components", "power"],
        simple="Instead of working with millions of volts and thousands of amps, engineers divide everything by a chosen base. All values become numbers near 1, and mistakes become obvious.",
        definition="The per-unit system expresses quantities as fractions of chosen base values. With base MVA and base kV fixed, base impedance is Z_base = kV^2 / MVA, and any quantity's per-unit value is its actual value divided by its base.",
        intuition="Per-unit removes the turns ratio from transformer calculations entirely, which is why fault studies across an entire network become tractable. A per-unit value far from 1 immediately signals an error.",
        points=[
            "Choose one base MVA for the whole system; voltage bases change with transformer ratios.",
            "Per-unit impedance is unchanged when referred across an ideal transformer.",
            "Symmetrical components resolve unbalanced faults into positive, negative and zero sequence networks.",
            "Three-phase faults are the most severe; line-to-ground faults are the most common.",
        ],
        formula={
            "name": "Base impedance and per-unit conversion",
            "latex": "Z_{base} = \\frac{(kV_{base})^2}{MVA_{base}}, \\qquad Z_{pu} = \\frac{Z_{actual}}{Z_{base}}",
            "variables": [
                {"s": "kV_{base}", "n": "base line-to-line voltage", "u": "kV"},
                {"s": "MVA_{base}", "n": "base apparent power", "u": "MVA"},
            ],
            "conditions": "Three-phase system, consistent line-to-line voltage base.",
        },
        applications=[
            "Fault studies and protective relay setting.",
            "Load flow and stability studies.",
            "Equipment specification and comparison across manufacturers.",
        ],
        mistakes=[
            "Mixing line-to-line and phase voltage bases.",
            "Forgetting to convert impedances when changing the MVA base.",
            "Applying single-phase formulas to three-phase quantities.",
        ],
        exam=[
            "Convert a given impedance to per-unit on a new base.",
            "Explain symmetrical components and their use in unbalanced fault analysis.",
            "Derive the fault current for a three-phase symmetrical fault at a generator terminal.",
        ],
        interview=[
            "Why do protection engineers work in per-unit?",
            "Which fault type is most common, and which is most severe?",
            "How does a differential relay distinguish an internal from an external fault?",
        ],
    ),
    # =====================================================================
    # CIVIL
    # =====================================================================
    t(
        "soil-mechanics", "Effective Stress & Bearing Capacity",
        summary="Why water in soil controls whether a foundation stands or sinks.",
        difficulty="hard", minutes=30, tags=["effective-stress", "bearing-capacity", "consolidation", "foundation"],
        simple="Soil particles carry the load; water in the pores does not. Take the total pressure and subtract the water pressure, and you have the pressure the grains actually feel.",
        definition="Effective stress is the intergranular stress carried by the soil skeleton: sigma' = sigma - u, where sigma is total stress and u is pore water pressure. Terzaghi's bearing capacity equation gives the ultimate load a shallow foundation can carry before shear failure.",
        intuition="Strength and stiffness come from friction between grains, and friction needs normal force between grains. Water pressure pushes grains apart, so it reduces strength - which is exactly why a rising water table can destabilise a slope that was previously safe.",
        points=[
            "A rising water table reduces effective stress and therefore bearing capacity.",
            "Terzaghi's equation combines cohesion, surcharge and unit-weight terms with shape factors.",
            "Consolidation is the slow squeeze of water out of clay, causing settlement over years.",
            "Safe bearing capacity is the ultimate capacity divided by a factor of safety, usually 3.",
        ],
        formula={
            "name": "Terzaghi's bearing capacity (strip footing)",
            "latex": "q_u = c N_c + \\gamma D_f N_q + 0.5 \\gamma B N_\\gamma",
            "variables": [
                {"s": "c", "n": "cohesion", "u": "kPa"},
                {"s": "\\gamma", "n": "unit weight of soil", "u": "kN/m^3"},
                {"s": "D_f", "n": "foundation depth", "u": "m"},
                {"s": "B", "n": "footing width", "u": "m"},
                {"s": "N_c, N_q, N_\\gamma", "n": "bearing capacity factors", "u": "-"},
            ],
            "conditions": "Shallow foundation, general shear failure, homogeneous soil.",
        },
        applications=[
            "Foundation design for buildings, bridges and towers.",
            "Slope stability and retaining wall design.",
            "Earthquake liquefaction assessment.",
        ],
        mistakes=[
            "Using total stress where effective stress governs strength.",
            "Ignoring the water table position in the bearing capacity calculation.",
            "Confusing immediate settlement with long-term consolidation settlement.",
        ],
        exam=[
            "State the principle of effective stress and derive it from a saturated soil element.",
            "Write Terzaghi's bearing capacity equation and explain each term.",
            "Explain one-dimensional consolidation and derive Terzaghi's consolidation equation outline.",
        ],
        interview=[
            "Why does a rising water table reduce bearing capacity?",
            "What is liquefaction and when does it occur?",
            "How do you decide between a shallow and a pile foundation?",
        ],
    ),
    t(
        "concrete-technology", "Concrete Mix Design & Workability",
        summary="Choosing proportions so fresh concrete can be placed and hardened concrete reaches its design strength.",
        difficulty="medium", minutes=25, tags=["concrete", "mix-design", "slump", "strength"],
        simple="Concrete is a recipe: cement, water, sand and aggregate. Too much water makes it easy to pour but weak; too little makes it strong but impossible to place.",
        definition="Mix design determines the proportions of cement, water, fine and coarse aggregate to achieve target strength, durability and workability. The water-cement ratio is the dominant factor controlling strength and permeability.",
        intuition="Abrams' law captures the whole trade-off: strength falls as the water-cement ratio rises, because surplus water leaves voids when it evaporates. Workability is solved with admixtures rather than extra water.",
        points=[
            "Lower w/c ratio means higher strength and lower permeability - but poorer workability.",
            "Slump test measures workability; typical values range 25 mm for pavements to 100+ mm for pumped concrete.",
            "Superplasticisers give workability without extra water - the single most important modern admixture.",
            "Curing keeps moisture available so hydration completes; uncured concrete can lose half its strength.",
        ],
        example={
            "problem": "An M25 grade mix requires a w/c ratio of 0.5 and 400 kg/m^3 of cement. Find the water content per cubic metre.",
            "approach": "Multiply the cement content by the water-cement ratio.",
            "solution": "Water = 0.5 x 400 = 200 kg, i.e. 200 litres per cubic metre.",
            "answer": "200 litres. Check this against the maximum permitted for the exposure condition.",
        },
        applications=[
            "Structural concrete for buildings, bridges, dams and pavements.",
            "Precast and prestressed production where early strength matters.",
            "Marine and aggressive-environment structures requiring low permeability.",
        ],
        mistakes=[
            "Adding water on site to improve workability, silently reducing strength.",
            "Ignoring aggregate moisture content, which changes the effective w/c ratio.",
            "Skipping curing, especially in hot or windy weather.",
        ],
        exam=[
            "Describe the IS method of concrete mix design with all steps.",
            "Explain Abrams' water-cement ratio law.",
            "List the tests for workability and the range of values each suits.",
        ],
        interview=[
            "Why does adding water on site damage concrete?",
            "What does a superplasticiser actually do at the particle level?",
            "How do you ensure durability in a marine structure?",
        ],
    ),
    # =====================================================================
    # CHEMICAL
    # =====================================================================
    t(
        "process-calculations", "Material & Energy Balances",
        summary="The accountant's discipline of chemical engineering: what goes in must come out or accumulate.",
        difficulty="medium", minutes=30, tags=["mass-balance", "energy-balance", "process"],
        simple="Every kilogram that enters a process must leave it or stay inside. Writing that down for each unit and each species is the basis of all process design.",
        definition="A material balance applies conservation of mass to a defined system boundary: input - output + generation - consumption = accumulation. An energy balance does the same for energy, including enthalpy flows, heat and work.",
        intuition="Balances are the sanity check on every design. If the numbers do not close, the flowsheet is wrong - no amount of clever equipment fixes a mass balance that does not balance.",
        points=[
            "Choose the system boundary first; it determines which streams appear in the balance.",
            "Total mass balances always close; species balances close only if there is no reaction.",
            "A tie component (one that does not react) is the fastest way to link two streams.",
            "Recycle and purge streams make balances iterative - solve with a converging assumption.",
        ],
        example={
            "problem": "A dryer removes water from 1000 kg/h of wet solids containing 40% water to produce a product with 5% water. Find the water removed and the product rate.",
            "approach": "Use dry solids as the tie component, then a total balance.",
            "solution": "Dry solids = 600 kg/h and stay constant. Product = 600 / 0.95 = 631.6 kg/h. Water removed = 1000 - 631.6 = 368.4 kg/h.",
            "answer": "631.6 kg/h of product, 368.4 kg/h of water evaporated.",
        },
        applications=[
            "Plant design and scale-up from laboratory to production.",
            "Troubleshooting: a balance that stops closing locates the leak or the bad meter.",
            "Sustainability reporting and yield optimisation.",
        ],
        mistakes=[
            "Balancing total mass across a reacting system and calling it a species balance.",
            "Forgetting the accumulation term in an unsteady process.",
            "Not closing the recycle loop, so the answer depends on an arbitrary first guess.",
        ],
        exam=[
            "Solve a two-unit flowsheet with a recycle stream.",
            "Write the general balance equation and simplify it for a steady-state non-reacting system.",
            "Perform a combustion balance to find the flue gas composition.",
        ],
        interview=[
            "How do you find a leak in a process using only flow meters?",
            "What is a tie component and why is it useful?",
            "How does an energy balance differ for an exothermic reactor?",
        ],
    ),
    # =====================================================================
    # FIRST YEAR (remaining)
    # =====================================================================
    t(
        "engineering-mechanics-fy", "Equilibrium of Forces & Free Body Diagrams",
        summary="The single most important skill in mechanics: isolating a body and drawing every force on it.",
        difficulty="medium", minutes=30, tags=["statics", "equilibrium", "fbd", "moments"],
        simple="A free body diagram is a sketch of the object alone, with every push and pull on it drawn as an arrow. If the arrows balance, the object does not move.",
        definition="A body is in static equilibrium when the vector sum of forces and the sum of moments about any point are both zero. A free body diagram isolates the body and shows all external forces and reactions acting on it.",
        intuition="Most mechanics errors are not calculation errors - they are missing forces. The FBD is the discipline that makes the force list complete before any algebra begins.",
        points=[
            "Three equilibrium equations in 2-D: sum Fx = 0, sum Fy = 0, sum M = 0.",
            "Reaction types: roller (one), pin (two), fixed (two plus a moment).",
            "Choose the moment point to eliminate unknowns and reduce the algebra.",
            "Two-force members carry load only along their axis - a huge simplification in trusses.",
        ],
        example={
            "problem": "A 10 kg beam 4 m long is simply supported and carries a 200 N point load at its centre. Find the reactions.",
            "approach": "Draw the FBD, take moments about one support to eliminate the other reaction.",
            "solution": "Weight = 98.1 N at 2 m, load 200 N at 2 m. Moments about A: R_B x 4 = (98.1 + 200) x 2, so R_B = 149.05 N. By vertical equilibrium R_A = 298.1 - 149.05 = 149.05 N.",
            "answer": "Both reactions are 149.05 N, as symmetry requires.",
        },
        applications=[
            "Structural analysis, machine design and mechanism synthesis.",
            "Crane, rigging and lifting plans.",
            "Vehicle loading and stability assessment.",
        ],
        mistakes=[
            "Forgetting a reaction at a support, or adding one that the support cannot provide.",
            "Mixing up clockwise and anticlockwise moment signs.",
            "Drawing the FBD of the whole structure when only one member is needed.",
        ],
        exam=[
            "Determine the reactions of a beam with an overhang under a uniformly distributed load.",
            "Analyse a pin-jointed truss by the method of joints.",
            "State and apply Lami's theorem for three concurrent forces.",
        ],
        interview=[
            "Why is a free body diagram drawn before any calculation?",
            "What is a two-force member and why does it matter in trusses?",
            "How do you check whether a structure is statically determinate?",
        ],
        diagram="fbd",
    ),
    t(
        "basic-electrical", "AC Circuits & Power Factor",
        summary="Why voltage and current can be out of step in AC systems, and what that costs you.",
        difficulty="medium", minutes=30, tags=["ac", "power-factor", "reactance", "rms"],
        simple="In AC circuits, coils and capacitors make the current arrive late or early compared with the voltage. That mismatch does no useful work but still fills the wires.",
        definition="In an AC circuit, inductive and capacitive elements cause a phase difference phi between voltage and current. Power factor is cos(phi), the ratio of real power to apparent power, and reactive power circulates between source and load without doing work.",
        intuition="Reactive power does not perform work, but it still occupies conductor capacity and causes I^2R losses. That is why utilities charge industrial customers for a poor power factor.",
        points=[
            "Real power P = VI cos phi (W), reactive Q = VI sin phi (VAR), apparent S = VI (VA).",
            "In a purely resistive load voltage and current are in phase and power factor is 1.",
            "Inductive loads lag; capacitive loads lead - so capacitors correct an inductive power factor.",
            "RMS values are used because they give the same heating effect as an equivalent DC value.",
        ],
        formula={
            "name": "AC power triangle",
            "latex": "S = \\sqrt{P^2 + Q^2}, \\qquad \\text{pf} = \\cos\\phi = \\frac{P}{S}",
            "variables": [
                {"s": "P", "n": "real power", "u": "W"},
                {"s": "Q", "n": "reactive power", "u": "VAR"},
                {"s": "S", "n": "apparent power", "u": "VA"},
            ],
            "conditions": "Sinusoidal steady state.",
        },
        example={
            "problem": "A motor draws 10 kW at a power factor of 0.7 lagging from a 400 V supply. Find the apparent power and the current.",
            "approach": "S = P / pf, then I = S / V.",
            "solution": "S = 10,000 / 0.7 = 14,286 VA. I = 14,286 / 400 = 35.7 A.",
            "answer": "14.3 kVA and 35.7 A. Correcting the power factor to 0.95 would cut the current to 26.3 A - a 26% reduction in conductor losses.",
        },
        applications=[
            "Industrial power factor correction with capacitor banks.",
            "Sizing cables, transformers and generators.",
            "Motor drives, UPS systems and grid stability management.",
        ],
        mistakes=[
            "Using peak values where RMS is required.",
            "Confusing kVA rating with kW output when sizing a generator.",
            "Over-correcting the power factor into a leading condition, which can cause resonance.",
        ],
        exam=[
            "Draw the power triangle and derive the relationships between P, Q and S.",
            "Explain series resonance and derive the resonant frequency of an RLC circuit.",
            "Calculate the capacitance needed to improve a given load to a target power factor.",
        ],
        interview=[
            "Why do utilities penalise low power factor?",
            "What happens at resonance in a series RLC circuit?",
            "Why is RMS used instead of average value for AC power?",
        ],
    ),
]
