"""Accurate notes for subjects that previously had a title and no topic.

Each entry is ordinary textbook material: a definition, the formula with its
units, one worked example, and the mistake students actually make. Nothing
here is a generated syllabus and nothing claims a degree is covered.
"""
from __future__ import annotations

from engineverse.diagrams import box, arrow, hotspot, label
from engineverse.models3d import scene, box as solid, arrow as shaft, cylinder, label as tag, grid

INK = "#334155"
ACCENT = "#4f7cff"
WARM = "#f59e0b"
GOOD = "#16a34a"


def _flow(title: str, caption: str, steps: list[tuple[str, str]], footer: str) -> dict:
    objects: list = [label(360, 28, title, size=15, anchor="middle", weight=700)]
    hotspots = []
    x = 36
    for index, (name, explain) in enumerate(steps):
        objects += box(x, 70, 150, 64, name, fill="#eef3fb", size=13)
        hotspots.append(hotspot(x, 70, 150, 64, name, explain))
        if index < len(steps) - 1:
            objects.append(arrow(x + 150, 102, x + 188, 102))
        x += 188
    objects.append(label(360, 168, footer, size=12, anchor="middle"))
    return {
        "title": title,
        "caption": caption,
        "canvas": {"w": 720, "h": 200},
        "objects": objects,
        "hotspots": hotspots,
    }


def _model(title: str, caption: str, parts: list, labels: list) -> dict:
    return {
        "title": title,
        "caption": caption,
        "scene": scene(parts, labels=labels, distance=7.2, pitch=16, spin=0.15),
    }


TOPICS = [
    {
        "subject": "digital-logic-design",
        "title": "Binary numbers and two's complement",
        "summary": "How unsigned binary counts, and how a fixed width represents a negative integer.",
        "difficulty": "easy",
        "minutes": 25,
        "tags": ["binary", "two's complement", "digital"],
        "simple": "An unsigned binary number is a sum of powers of two. Two's complement uses the same bits to store a negative value by inverting and adding one, so subtraction is addition of that pattern.",
        "definition": "For an n-bit pattern, the unsigned value is the sum of b_i 2^i. The two's complement value of the same pattern is -b_{n-1} 2^{n-1} plus the remaining unsigned bits. The range is -2^{n-1} to 2^{n-1}-1.",
        "intuition": "The top bit is a sign weight, not a decoration. 1000 in 4 bits is -8, not +8, because that bit contributes -8 and the lower bits contribute 0.",
        "points": [
            "Unsigned range for n bits is 0 to 2^n - 1.",
            "Two's complement range is -2^{n-1} to 2^{n-1} - 1.",
            "Negate by inverting every bit and adding 1.",
            "Adding one past the top bit discards the carry; that is overflow detection, not a wider result.",
        ],
        "formula": {
            "name": "Two's complement value",
            "latex": "V = -b_{n-1}2^{n-1} + \\sum_{i=0}^{n-2} b_i 2^i",
            "variables": [
                {"s": "V", "n": "signed value of the bit pattern", "u": "dimensionless"},
                {"s": "b_i", "n": "bit i, 0 or 1", "u": "dimensionless"},
                {"s": "n", "n": "width of the word", "u": "bit"},
            ],
            "conditions": "Fixed width. A carry out of bit n-1 is discarded, not stored.",
        },
        "derivation": (
            "Start from the unsigned sum and move the weight of the top bit from +2^{n-1} to -2^{n-1}. "
            "That single sign change is the definition. To negate a value x, compute (2^n - x) mod 2^n. "
            "Inverting the bits gives (2^n - 1 - x); adding one gives 2^n - x. The 2^n term falls off the "
            "end of an n-bit adder, which is why invert-and-add-one works."
        ),
        "example": {
            "problem": "Write -6 as a 4-bit two's complement pattern.",
            "approach": "Write +6, invert, add one.",
            "solution": "$$+6 = 0110$$\n\n$$\\text{invert} = 1001$$\n\n$$1001 + 1 = 1010$$\n\nCheck: top bit contributes -8, lower bits contribute 2, and -8 + 2 = -6.",
            "answer": "1010",
        },
        "applications": ["ALU subtraction", "sensor offsets stored in a byte", "assembly immediates"],
        "mistakes": [
            "Reading the top bit as +2^{n-1} after you have agreed the word is signed.",
            "Forgetting the add-one step and stopping at the one's complement.",
            "Calling 1000 in 4 bits positive eight.",
        ],
        "exam": [
            "Convert -13 to 8-bit two's complement.",
            "State the range of a 16-bit signed integer.",
            "Show why invert-and-add-one equals 2^n - x.",
        ],
        "interview": [
            "How do you detect signed overflow when adding two two's complement numbers?",
            "Why is there one more negative value than positive value?",
        ],
        "industry": (
            "Microcontrollers and CPUs add and subtract in two's complement because one adder does both. "
            "A firmware bug that treats a signed sensor word as unsigned will shift every negative reading "
            "by 2^n. Check the width in the datasheet before you scale the value."
        ),
    },
    {
        "subject": "discrete-mathematics",
        "title": "Sets, relations and functions",
        "summary": "Membership, ordered pairs, and the rule that a function gives each input one output.",
        "difficulty": "easy",
        "minutes": 25,
        "tags": ["sets", "functions", "discrete"],
        "simple": "A set is a collection of distinct elements. A relation is a set of ordered pairs. A function is a relation that pairs each element of the domain with exactly one element of the codomain.",
        "definition": "A function f: A -> B is a subset of A x B such that for every a in A there is exactly one b in B with (a, b) in f. A is the domain and B is the codomain.",
        "intuition": "If one input has two arrows leaving it, you do not have a function. If some input has no arrow, you also do not have a function from that domain.",
        "points": [
            "Sets ignore order and duplicates: {1, 2, 2} is {1, 2}.",
            "Ordered pairs do not: (1, 2) is not (2, 1).",
            "A function has exactly one output per domain element.",
            "Injective, surjective and bijective are extra properties, not part of the definition of a function.",
        ],
        "formula": {
            "name": "Function as a set of pairs",
            "latex": "f \\subseteq A \\times B,\\quad \\forall a \\in A\\ \\exists!\\ b \\in B:\\ (a,b) \\in f",
            "variables": [
                {"s": "A", "n": "domain", "u": "set"},
                {"s": "B", "n": "codomain", "u": "set"},
                {"s": "f", "n": "the function", "u": "set of pairs"},
            ],
            "conditions": "The unique-existence quantifier is the whole definition. Dropping it leaves a relation.",
        },
        "derivation": (
            "A x B is every ordered pair with the first element from A and the second from B. A relation is "
            "any subset of that product. Require that each first element appears once: that is existence and "
            "uniqueness. The graph of f is exactly that subset. Nothing else — no formula — is required for "
            "the object to be a function."
        ),
        "example": {
            "problem": "Is R = {(1, a), (1, b), (2, a)} a function from {1, 2} to {a, b}?",
            "approach": "Check each domain element for exactly one pair.",
            "solution": "1 appears in two pairs, with a and with b. The uniqueness condition fails, so R is a relation and not a function.",
            "answer": "No. 1 has two images.",
        },
        "applications": ["hash tables as functions from keys to buckets", "database foreign keys", "type signatures"],
        "mistakes": [
            "Calling a relation a function because every pair is valid.",
            "Confusing codomain with image. The image can be smaller.",
            "Writing {1, 2} = {2, 1} and then treating (1, 2) the same way.",
        ],
        "exam": [
            "Define a function using ordered pairs.",
            "Give a relation on {1, 2, 3} that is not a function, and say which condition fails.",
        ],
        "interview": [
            "What is the difference between injective and surjective?",
            "Why can a hash function map many keys to one bucket and still be a function?",
        ],
        "industry": (
            "An API that sometimes returns two different bodies for the same request id is not implementing "
            "a function of that id. Idempotent handlers and primary keys are the same uniqueness rule applied "
            "to stored data."
        ),
    },
    {
        "subject": "theory-of-computation",
        "title": "Deterministic finite automata",
        "summary": "A finite set of states, one start, a transition for every symbol, and a language of accepted strings.",
        "difficulty": "medium",
        "minutes": 30,
        "tags": ["automata", "DFA", "theory"],
        "simple": "A DFA reads a string one symbol at a time. From the current state and the next symbol there is exactly one next state. The string is accepted if the machine stops in an accept state.",
        "definition": "A DFA is (Q, Sigma, delta, q0, F). Q is finite, q0 is in Q, F is a subset of Q, and delta: Q x Sigma -> Q is a total function.",
        "intuition": "Deterministic means you never choose. If two arrows leave the same state on the same symbol, the machine is not a DFA.",
        "points": [
            "delta must be defined for every state and every symbol.",
            "There is one start state.",
            "Accept states may be empty; that DFA accepts nothing.",
            "The language is the set of strings that end in F.",
        ],
        "formula": {
            "name": "Extended transition",
            "latex": "\\hat{\\delta}(q, \\varepsilon) = q,\\quad \\hat{\\delta}(q, wa) = \\delta(\\hat{\\delta}(q, w), a)",
            "variables": [
                {"s": "q", "n": "a state", "u": "element of Q"},
                {"s": "w", "n": "the string read so far", "u": "string"},
                {"s": "a", "n": "the next symbol", "u": "element of Sigma"},
            ],
            "conditions": "delta is total. A missing arrow is not a DFA.",
        },
        "derivation": (
            "Define the run by induction on the length of the string. The empty string leaves the machine in "
            "q0. If the machine is in state p after w, the next symbol a moves it to delta(p, a). The string "
            "is in the language exactly when that final state is in F. Because delta returns one state, the "
            "run is unique."
        ),
        "example": {
            "problem": "A two-state DFA over {0, 1} stays in q0 on 0 and moves to q1 on 1. q1 is the only accept state, and both symbols keep it in q1. Which strings does it accept?",
            "approach": "The machine leaves q0 at the first 1 and never returns.",
            "solution": "Any string with no 1 stays in q0 and is rejected. The first 1 moves to q1, and every later symbol stays there. So the accepted strings are those with at least one 1.",
            "answer": "Every string that contains at least one 1.",
        },
        "applications": ["lexical token scanners", "protocol state machines", "simple input validators"],
        "mistakes": [
            "Leaving a symbol without an arrow and still calling the machine a DFA.",
            "Allowing two arrows on the same symbol.",
            "Forgetting that the empty string is accepted only when q0 is in F.",
        ],
        "exam": [
            "Draw a DFA for strings over {0, 1} that end in 01.",
            "Explain why a missing transition means the machine is not deterministic and total.",
        ],
        "interview": [
            "How is an NFA different from a DFA on one symbol?",
            "Why can every NFA be converted to a DFA, and what grows?",
        ],
        "industry": (
            "A lexer is a DFA in practice: each character moves a small state table, and an accept state emits "
            "a token. A missing case in that table is a missing transition. It should go to a dead state and "
            "report an error, not fall through."
        ),
    },
    {
        "subject": "compiler-design",
        "title": "Lexical analysis",
        "summary": "The front of a compiler turns characters into tokens before any grammar runs.",
        "difficulty": "medium",
        "minutes": 25,
        "tags": ["lexer", "tokens", "compiler"],
        "simple": "Lexical analysis reads the source as a stream of characters and groups them into tokens such as identifiers, numbers and operators. The parser never sees the raw characters.",
        "definition": "A token is a name plus the lexeme that produced it, and often an attribute such as the integer value. The lexer is a function from a character stream to a token stream.",
        "intuition": "Whitespace and comments are usually discarded here. If you leave them for the parser, every grammar rule has to mention them.",
        "points": [
            "The longest match wins when two token patterns both fit.",
            "Keywords are identifiers that the lexer classifies with a reserved-word table.",
            "A lexical error is a character sequence that matches no token.",
            "The parser receives tokens, not characters.",
        ],
        "formula": {
            "name": "Longest match",
            "latex": "\\mathrm{token}(s) = \\arg\\max_{p \\in P}\\{|m| : m \\text{ is a prefix of } s \\text{ and } m \\in L(p)\\}",
            "variables": [
                {"s": "s", "n": "remaining source", "u": "string"},
                {"s": "P", "n": "token patterns", "u": "set of languages"},
                {"s": "m", "n": "matched prefix", "u": "string"},
            ],
            "conditions": "If two patterns match the same longest prefix, a declared priority breaks the tie. Keywords beat identifiers.",
        },
        "derivation": (
            "Each token pattern is a regular language, so it has a DFA. The lexer runs the DFAs together, or "
            "one combined DFA, and remembers the last accept state it passed. When the next character would "
            "leave every pattern, it emits the token for that last accept state and rewinds to the character "
            "after the match. That rewind is why the longest match is well defined."
        ),
        "example": {
            "problem": "The source is `ifx = 3`. What tokens does a typical lexer emit?",
            "approach": "Apply longest match, then the keyword table.",
            "solution": "`if` is a keyword, but `ifx` is a longer identifier and the next character is a space, so the longest match is the identifier ifx. Then `=` is an operator and `3` is an integer literal.",
            "answer": "IDENTIFIER(ifx), EQUALS, INT(3).",
        },
        "applications": ["compiler front ends", "syntax highlighters", "search query parsers"],
        "mistakes": [
            "Emitting `if` and then `x` from `ifx`.",
            "Sending comments to the parser.",
            "Treating a lexical error as a parse error and blaming the grammar.",
        ],
        "exam": [
            "Define longest match and give a case where it matters.",
            "Why are keywords not a separate grammar of characters?",
        ],
        "interview": [
            "What is the difference between a lexeme and a token?",
            "How would you report the line of a lexical error?",
        ],
        "industry": (
            "A highlighter that splits `ifx` into a keyword is wrong in the same way a compiler lexer would be "
            "wrong. Ship the longest-match rule, and keep the keyword table separate so adding a keyword does "
            "not rewrite the identifier pattern."
        ),
    },
    {
        "subject": "engineering-mathematics-2",
        "title": "First-order linear differential equations",
        "summary": "The integrating factor that turns dy/dx + P(x)y = Q(x) into a derivative of a product.",
        "difficulty": "medium",
        "minutes": 30,
        "tags": ["ODE", "integrating factor", "calculus"],
        "simple": "A first-order linear equation has y and dy/dx to the first power. Multiply by the integrating factor and the left side becomes the derivative of (integrating factor times y).",
        "definition": "The standard form is dy/dx + P(x)y = Q(x), with P and Q functions of x only. The integrating factor is exp of the integral of P dx.",
        "intuition": "You are manufacturing a product rule. The extra term that the product rule would produce is exactly P times y times the integrating factor, which is the term already sitting in the equation.",
        "points": [
            "Write the equation in standard form before choosing P.",
            "The integrating factor depends on P, not on Q.",
            "An arbitrary constant appears when you integrate the right side.",
            "This method is for linear equations. A y-squared term needs a different method.",
        ],
        "formula": {
            "name": "Integrating factor",
            "latex": "\\mu(x) = e^{\\int P(x)\\,dx},\\quad \\frac{d}{dx}(\\mu y) = \\mu Q",
            "variables": [
                {"s": "\\mu", "n": "integrating factor", "u": "dimensionless if P is 1/x-like"},
                {"s": "P", "n": "coefficient of y in standard form", "u": "1 over the unit of x"},
                {"s": "Q", "n": "forcing term", "u": "unit of dy/dx"},
            ],
            "conditions": "The equation must already be in standard form. Do not include a constant of integration inside mu; it cancels.",
        },
        "derivation": (
            "Assume a multiplier mu(x). Then d/dx(mu y) = mu y' + mu' y. You want this to equal mu times "
            "(y' + P y), so mu' = mu P. Separate variables: d(mu)/mu = P dx. Integrate both sides and "
            "exponentiate. The constant factor in mu multiplies every term and cancels when you divide, so "
            "it is taken as 1."
        ),
        "example": {
            "problem": "Solve dy/dx + y = e^{-x}.",
            "approach": "P = 1, so the integrating factor is e^{x}.",
            "solution": "$$\\mu = e^{\\int 1\\,dx} = e^{x}$$\n\n$$\\frac{d}{dx}(e^{x} y) = e^{x} e^{-x} = 1$$\n\n$$e^{x} y = x + C$$\n\n$$y = (x + C)e^{-x}$$",
            "answer": "y = (x + C) e^{-x}",
        },
        "applications": ["RC circuit transients", "Newton's law of cooling", "mixing problems with a constant inflow"],
        "mistakes": [
            "Integrating P without putting the equation in standard form.",
            "Keeping a constant inside the integrating factor and then losing the real constant.",
            "Using this method on a nonlinear equation.",
        ],
        "exam": [
            "Solve dy/dx + 2y = 4 with y(0) = 1.",
            "Derive the integrating factor from the product rule.",
        ],
        "interview": [
            "Why does the constant inside the integrating factor not matter?",
            "What fails if P depends on y?",
        ],
        "industry": (
            "A first-order lag in a temperature or RC circuit is this equation. The time constant is 1/P when "
            "P is constant. Fitting a curve without writing the standard form first is how people report a "
            "time constant with the wrong sign."
        ),
    },
    {
        "subject": "engineering-chemistry",
        "title": "The ideal gas law",
        "summary": "PV = nRT, the units that make R true, and when a real gas stops obeying it.",
        "difficulty": "easy",
        "minutes": 20,
        "tags": ["gas law", "chemistry", "units"],
        "simple": "For a gas far from condensation, pressure times volume equals the amount of substance times R times the absolute temperature.",
        "definition": "The ideal gas law is PV = nRT. P is absolute pressure, V is volume, n is amount of substance, T is absolute temperature, and R is the gas constant.",
        "intuition": "Hold the amount and the temperature fixed and the pressure rises as you squeeze the volume. Heat the gas in a fixed volume and the pressure rises because the molecules hit harder and more often.",
        "points": [
            "T must be in kelvin. A Celsius value is not absolute.",
            "P must be absolute. Gauge pressure is short by about 1 atm.",
            "R is 8.314 J/(mol·K). Using 0.0821 requires pressure in atm and volume in litres.",
            "The law fails near the critical point and at high pressure.",
        ],
        "formula": {
            "name": "Ideal gas law",
            "latex": "PV = nRT",
            "variables": [
                {"s": "P", "n": "absolute pressure", "u": "Pa"},
                {"s": "V", "n": "volume", "u": "m^3"},
                {"s": "n", "n": "amount of substance", "u": "mol"},
                {"s": "R", "n": "gas constant, 8.314", "u": "J/(mol·K)"},
                {"s": "T", "n": "absolute temperature", "u": "K"},
            ],
            "conditions": "Ideal-gas behaviour: low pressure relative to the critical pressure, and temperature well above the point where the gas would liquefy.",
        },
        "derivation": (
            "Boyle's law says PV is constant at fixed n and T. Charles's law says V/T is constant at fixed n "
            "and P. Avogadro's law says V/n is constant at fixed P and T. The single equation that satisfies "
            "all three is PV = nRT, with R fixed by measuring one known gas. The kinetic theory arrives at "
            "the same relation by equating pressure to the momentum transferred by elastic collisions."
        ),
        "example": {
            "problem": "What is the volume of 1.00 mol of ideal gas at 100 kPa and 25 °C?",
            "approach": "Convert 25 °C to 298.15 K and use R = 8.314.",
            "solution": "$$V = \\frac{nRT}{P} = \\frac{(1.00)(8.314)(298.15)}{100 \\times 10^{3}}$$\n\n$$V = 0.0248\\ \\mathrm{m}^3 = 24.8\\ \\mathrm{L}$$",
            "answer": "0.0248 m^3",
        },
        "applications": ["reactor sizing at low pressure", "breathing-air cylinder estimates", "stoichiometry of gas feeds"],
        "mistakes": [
            "Using Celsius in PV = nRT.",
            "Mixing R = 8.314 with pressure in atmospheres.",
            "Applying the law to a vapour on the verge of condensing.",
        ],
        "exam": [
            "Calculate n for 2.0 L of gas at 1.0 atm and 300 K. State which R you used.",
            "Why does gauge pressure give the wrong amount?",
        ],
        "interview": [
            "When would you switch from the ideal gas law to a compressibility chart?",
            "What does R = 8.314 actually equal in base SI units?",
        ],
        "industry": (
            "A cylinder label gives gauge pressure. Add atmospheric pressure before you use PV = nRT, and "
            "check that the gas is not near its dew point. Oxygen and nitrogen at room temperature and a few "
            "bar are close to ideal; carbon dioxide near its vapour pressure is not."
        ),
    },
    {
        "subject": "heat-transfer",
        "title": "Fourier's law of conduction",
        "summary": "Heat flow through a solid is proportional to area and to the temperature gradient.",
        "difficulty": "medium",
        "minutes": 25,
        "tags": ["conduction", "Fourier", "heat"],
        "simple": "Heat conducts from hot to cold. The rate is the conductivity times the area times how steeply the temperature falls along the path.",
        "definition": "Fourier's law says the heat flux is minus k times the temperature gradient. The minus sign puts the flow in the direction of decreasing temperature.",
        "intuition": "A thicker wall of the same material moves less heat for the same temperature difference, because the gradient k sees is smaller.",
        "points": [
            "q is heat flow in watts. q'' is flux in watts per square metre.",
            "k is a material property. Metals are large; insulation is small.",
            "The minus sign is not optional. Dropping it reverses the direction.",
            "One-dimensional steady conduction through a slab gives q = k A (T_hot - T_cold) / L.",
        ],
        "formula": {
            "name": "Fourier's law, one-dimensional slab",
            "latex": "q = -kA\\frac{dT}{dx} = kA\\frac{T_{hot}-T_{cold}}{L}",
            "variables": [
                {"s": "q", "n": "heat transfer rate", "u": "W"},
                {"s": "k", "n": "thermal conductivity", "u": "W/(m·K)"},
                {"s": "A", "n": "area normal to the flow", "u": "m^2"},
                {"s": "L", "n": "thickness", "u": "m"},
                {"s": "T", "n": "temperature", "u": "K"},
            ],
            "conditions": "Steady state, constant k, heat flow only along x, no generation inside the slab.",
        },
        "derivation": (
            "The flux definition is q'' = -k dT/dx. Multiply by the area to get the rate. For steady state "
            "with constant k and no generation, dT/dx is constant, so the derivative is (T_cold - T_hot) / L "
            "if x increases toward the cold face. The two minus signs — the law, and the falling temperature "
            "— give a positive heat flow from hot to cold equal to k A (T_hot - T_cold) / L."
        ),
        "example": {
            "problem": "A 0.10 m brick wall, k = 0.70 W/(m·K), area 12 m^2, has faces at 30 °C and 10 °C. Find the steady heat flow.",
            "approach": "The temperature difference is 20 K. Thickness is 0.10 m.",
            "solution": "$$q = \\frac{(0.70)(12)(20)}{0.10} = 1680\\ \\mathrm{W}$$",
            "answer": "1680 W from the hot face to the cold face.",
        },
        "applications": ["furnace walls", "insulation thickness", "chip heat spreaders"],
        "mistakes": [
            "Using the outside air temperature as the wall-face temperature.",
            "Dropping the minus sign and then also swapping the temperatures.",
            "Using k of the fluid when the question is about the solid.",
        ],
        "exam": [
            "State Fourier's law and the meaning of the minus sign.",
            "A wall is doubled in thickness. What happens to steady conduction, all else fixed?",
        ],
        "interview": [
            "How is conduction different from convection at a surface?",
            "Why can you add wall resistances in series?",
        ],
        "industry": (
            "Insulation specs quote k and thickness because the slab formula is what the energy bill sees. "
            "A quoted U-value already includes the surface films. Do not put that U back into Fourier's law "
            "as if it were k."
        ),
    },
    {
        "subject": "surveying",
        "title": "Differential leveling",
        "summary": "Backsights and foresights turn staff readings into a height difference.",
        "difficulty": "easy",
        "minutes": 25,
        "tags": ["leveling", "survey", "reduced level"],
        "simple": "A level gives a horizontal line of sight. The difference of two staff readings from that line is the difference in height of the two points.",
        "definition": "A backsight is the reading on a point of known height. A foresight is the reading on the point whose height you want. The height of the instrument is the known height plus the backsight.",
        "intuition": "A larger staff reading means the ground is lower, because more of the staff sticks up into the horizontal line of sight.",
        "points": [
            "HI = RL of the known point + BS.",
            "RL of the next point = HI - FS.",
            "The arithmetic check is sum of backsights minus sum of foresights equals the last RL minus the first RL.",
            "A change point has a foresight from one setup and a backsight from the next.",
        ],
        "formula": {
            "name": "Height of collimation",
            "latex": "\\mathrm{HI} = \\mathrm{RL}_A + \\mathrm{BS},\\quad \\mathrm{RL}_B = \\mathrm{HI} - \\mathrm{FS}",
            "variables": [
                {"s": "\\mathrm{HI}", "n": "height of the line of sight", "u": "m"},
                {"s": "\\mathrm{RL}", "n": "reduced level", "u": "m"},
                {"s": "\\mathrm{BS}", "n": "backsight", "u": "m"},
                {"s": "\\mathrm{FS}", "n": "foresight", "u": "m"},
            ],
            "conditions": "The instrument is leveled, so the line of sight is horizontal. Staffs are vertical.",
        },
        "derivation": (
            "The line of sight is one horizontal plane for a given setup. The reduced level of that plane is "
            "the reduced level of the benchmark plus how far the staff at the benchmark rises to meet the "
            "plane. At the next point the staff rises a different distance to the same plane, so you subtract "
            "that reading. Moving the instrument starts a new plane, which is why a change point needs both "
            "a foresight and a new backsight."
        ),
        "example": {
            "problem": "Benchmark RL is 100.000 m. Backsight is 1.250 m. Foresight on B is 2.430 m. Find RL of B.",
            "approach": "Add the backsight, subtract the foresight.",
            "solution": "$$\\mathrm{HI} = 100.000 + 1.250 = 101.250\\ \\mathrm{m}$$\n\n$$\\mathrm{RL}_B = 101.250 - 2.430 = 98.820\\ \\mathrm{m}$$",
            "answer": "98.820 m",
        },
        "applications": ["setting out floor levels", "road profiles", "checking settlement"],
        "mistakes": [
            "Adding the foresight instead of subtracting it.",
            "Using a staff reading taken before the instrument was leveled.",
            "Forgetting the arithmetic check after a page of readings.",
        ],
        "exam": [
            "Compute a reduced level from one backsight and one foresight.",
            "State the arithmetic check for a leveling run.",
        ],
        "interview": [
            "Why does a larger staff reading mean a lower point?",
            "What is a change point for?",
        ],
        "industry": (
            "A floor poured to the wrong reduced level is expensive to break out. Close the run back on the "
            "benchmark and apply the arithmetic check before anyone sets formwork. A mis-closure larger than "
            "the specification is a reason to repeat the run, not to spread the error silently."
        ),
    },
]


def _diagrams() -> dict:
    return {
        "binary-numbers-and-twos-complement": lambda: _flow(
            "Negate +6 in 4 bits",
            "Invert every bit, then add one. The pattern 1010 is -8 + 2 = -6.",
            [
                ("+6 = 0110", "Start from the positive value in the same width."),
                ("invert 1001", "One's complement flips every bit, including the leading zero."),
                ("+1 = 1010", "Adding one finishes two's complement. The top bit is -8."),
            ],
            "1010 means -8 + 2, not +10.",
        ),
        "sets-relations-and-functions": lambda: _flow(
            "One arrow per input",
            "A function pairs each domain element with exactly one codomain element.",
            [
                ("domain A", "Every element of A must appear exactly once as a first component."),
                ("exactly one", "Two arrows from the same element means the relation is not a function."),
                ("codomain B", "The image may be smaller than B. B is still the codomain."),
            ],
            "Uniqueness is the definition, not an extra property.",
        ),
        "deterministic-finite-automata": lambda: _flow(
            "One run, one symbol at a time",
            "A DFA has one next state for each state and each symbol. Accept if the run ends in F.",
            [
                ("start q0", "One start state. The empty string is accepted only if q0 is in F."),
                ("read a symbol", "delta is total: every symbol has an arrow."),
                ("end in F?", "The language is the set of strings whose unique run ends in an accept state."),
            ],
            "Two arrows on the same symbol means it is not a DFA.",
        ),
        "lexical-analysis": lambda: _flow(
            "Characters become tokens",
            "The lexer emits the longest match, then classifies keywords. The parser sees tokens.",
            [
                ("characters", "The source is a stream. Whitespace is usually discarded here."),
                ("longest match", "ifx is an identifier, not the keyword if followed by x."),
                ("token", "A token is a name, a lexeme, and any attribute the parser needs."),
            ],
            "A character that matches nothing is a lexical error.",
        ),
        "first-order-linear-differential-equations": lambda: _flow(
            "Make a product rule",
            "The integrating factor depends only on P. Multiplying turns the left side into d(mu y)/dx.",
            [
                ("standard form", "dy/dx + P(x)y = Q(x). Divide through before you choose P."),
                ("mu = exp ∫P", "Do not put a constant of integration inside mu."),
                ("integrate mu Q", "The constant of the solution appears on this step."),
            ],
            "A y-squared term is not this method.",
        ),
        "the-ideal-gas-law": lambda: _flow(
            "Absolute P and absolute T",
            "PV = nRT. Celsius and gauge pressure both give the wrong amount.",
            [
                ("P absolute", "Gauge pressure is short by about one atmosphere."),
                ("T in kelvin", "25 °C is 298 K, not 25."),
                ("n = PV/RT", "Use R that matches the units of P and V."),
            ],
            "R = 8.314 J/(mol·K) wants pascals and cubic metres.",
        ),
        "fouriers-law-of-conduction": lambda: _flow(
            "Hot to cold through the solid",
            "Steady slab flow is k A times the temperature drop divided by the thickness.",
            [
                ("hot face", "The driving difference is between the two faces, not the room air."),
                ("k and L", "Doubling L halves q when k, A and the temperatures stay fixed."),
                ("cold face", "The minus sign in Fourier's law points the flux downhill."),
            ],
            "q = k A (T_hot - T_cold) / L for a steady slab.",
        ),
        "differential-leveling": lambda: _flow(
            "One horizontal line of sight",
            "Add the backsight to the known level. Subtract the foresight.",
            [
                ("BS on BM", "HI = RL of the benchmark + backsight."),
                ("horizontal HI", "The instrument must be leveled before either reading."),
                ("FS on B", "RL of B = HI - foresight. A bigger reading is a lower point."),
            ],
            "Sum of BS minus sum of FS equals last RL minus first RL.",
        ),
    }


DIAGRAMS = _diagrams()


def _models() -> dict:
    return {
        "binary-numbers-and-twos-complement": _model(
            "Four bits, the top one weighted negative",
            "The tall box is the sign bit. In a 4-bit two's complement word its weight is -8, not +8. The three short boxes are the lower bits, weighted +1, +2 and +4.",
            [
                solid((-1.8, 0.2, 0), size=(0.7, 0.5, 0.5), color=INK),
                solid((-0.6, 0.2, 0), size=(0.7, 0.5, 0.5), color=INK),
                solid((0.6, 0.2, 0), size=(0.7, 0.5, 0.5), color=INK),
                solid((1.8, 0.7, 0), size=(0.7, 1.5, 0.5), color=WARM),
            ],
            [tag("bit 0", (-1.8, -0.5, 0)), tag("bit 3 = -8", (1.8, 1.7, 0))],
        ),
        "sets-relations-and-functions": _model(
            "Two arrows that should not both exist",
            "Two arrows leave the same input and land on two different images. A function may have only one of those arrows. This picture is a relation that fails the definition.",
            [
                cylinder((-1.6, 0, 0), radius=0.35, height=0.8, color=ACCENT),
                cylinder((1.6, 0.6, 0), radius=0.3, height=0.6, color=GOOD),
                cylinder((1.6, -0.6, 0), radius=0.3, height=0.6, color=WARM),
                shaft((-1.2, 0.1, 0), (1.2, 0.6, 0), radius=0.04, color=INK),
                shaft((-1.2, -0.1, 0), (1.2, -0.6, 0), radius=0.04, color=INK),
            ],
            [tag("one input", (-1.6, 0.8, 0)), tag("two images", (1.6, 1.3, 0))],
        ),
        "deterministic-finite-automata": _model(
            "States, and one arrow per symbol",
            "Each cylinder is a state. The arrow is the only transition on that symbol. A second arrow on the same symbol would mean the machine is not a DFA.",
            [
                cylinder((-1.4, 0, 0), radius=0.4, height=0.5, color=ACCENT),
                cylinder((1.4, 0, 0), radius=0.4, height=0.5, color=GOOD),
                shaft((-0.9, 0, 0), (0.9, 0, 0), radius=0.05, color=INK),
            ],
            [tag("q0", (-1.4, 0.7, 0)), tag("q1 accept", (1.4, 0.7, 0)), tag("symbol", (0, 0.45, 0))],
        ),
        "lexical-analysis": _model(
            "A stream cut into tokens",
            "The long bar is the character stream. The three boxes are the tokens the lexer emits after the longest match. The parser never sees the bar, only the boxes.",
            [
                solid((0, -0.8, 0), size=(4.2, 0.25, 0.4), color=INK),
                solid((-1.4, 0.4, 0), size=(1.1, 0.45, 0.45), color=ACCENT),
                solid((0, 0.4, 0), size=(0.8, 0.45, 0.45), color=WARM),
                solid((1.4, 0.4, 0), size=(1.0, 0.45, 0.45), color=GOOD),
            ],
            [tag("characters", (0, -1.3, 0)), tag("tokens", (0, 1.0, 0))],
        ),
        "first-order-linear-differential-equations": _model(
            "The product whose derivative you can see",
            "The vertical bar is mu times y after the integrating factor has turned the left side into a derivative. The grid is the x axis the product is plotted against.",
            [
                grid(size=4, divisions=4, position=(0.0, -1.2, 0.0)),
                cylinder((0, 0.2, 0), radius=0.08, height=2.2, color=ACCENT),
            ],
            [tag("x", (1.6, -1.0, 0)), tag("mu y", (0.4, 1.4, 0))],
        ),
        "the-ideal-gas-law": _model(
            "A piston, pressure on the face",
            "The arrow is the absolute pressure on the piston face, not the gauge reading. The cylinder under the piston is the volume in PV = nRT.",
            [
                cylinder((0, -0.4, 0), radius=0.8, height=1.2, color=ACCENT),
                solid((0, 0.5, 0), size=(1.8, 0.15, 1.8), color=INK),
                shaft((0, 0.7, 0), (0, 1.5, 0), radius=0.06, color=WARM),
            ],
            [tag("V", (1.2, -0.4, 0)), tag("P", (0.35, 1.3, 0))],
        ),
        "fouriers-law-of-conduction": _model(
            "Heat through a wall",
            "The slab is the wall of thickness L. The arrow is the heat flow from the hot face toward the cold face. Steady conduction is k A times the temperature drop divided by L.",
            [
                solid((0, 0, 0), size=(0.6, 2.2, 2.2), color=WARM),
                shaft((-1.2, 0, 0), (-0.4, 0, 0), radius=0.06, color=INK),
            ],
            [tag("hot", (-1.3, 0.4, 0)), tag("L", (0, -1.4, 0))],
        ),
        "differential-leveling": _model(
            "A horizontal line over two staffs",
            "The bar is the horizontal line of sight. The taller staff reaches farther up to that line, so the ground under it is lower. Reduced level is the line height minus the staff reading.",
            [
                solid((0, 0.8, 0), size=(3.6, 0.08, 0.08), color=ACCENT),
                cylinder((-1.2, 0, 0), radius=0.08, height=1.4, color=GOOD),
                cylinder((1.2, -0.3, 0), radius=0.08, height=2.0, color=WARM),
            ],
            [tag("BS", (-1.2, 1.2, 0)), tag("FS larger", (1.2, 1.2, 0))],
        ),
    }


MODELS = _models()
