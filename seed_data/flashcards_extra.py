"""Flashcards for the 55 subjects that had none.

The seeded library started with 34 cards covering 18 subjects, which meant a
learner who opened Revision from, say, "Power Electronics" or "Surveying" found
nothing to revise. These fill the gap so every subject has cards.

They are deliberately written as recall prompts rather than definitions to
copy. The `hint` field is the nudge that gets you to the answer without giving
it away, because a card you can only answer by reading it is not a card.

Difficulty follows the SM-2 schedule in `engineverse/srs.py`: `easy` cards are
meant to be answered in a couple of seconds, `hard` ones require reconstructing
a derivation or a chain of reasoning.
"""

from __future__ import annotations

# subject slug -> [(front, back, hint, difficulty)]
FLASHCARDS_EXTRA: dict[str, list[tuple[str, str, str, str]]] = {

    # ------------------------------------------------------------ electronics --
    "analog-circuits": [
        ("What four assumptions define an ideal op-amp?",
         "Infinite open-loop gain, infinite input impedance, zero output impedance and infinite bandwidth.",
         "Two about the inputs, two about the outputs.", "easy"),
        ("What does negative feedback trade away, and what does it buy?",
         "It trades open-loop gain for predictable closed-loop gain, wider bandwidth, lower distortion and "
         "controlled input/output impedance.",
         "The gain you give up was never usable anyway.", "medium"),
        ("Why can you assume the two op-amp inputs are at the same voltage?",
         "With negative feedback and enormous open-loop gain, any difference would drive the output to a rail, "
         "so the feedback forces the difference to near zero — the virtual short.",
         "What would the output do if they were not equal?", "hard"),
        ("What physically limits an op-amp's slew rate?",
         "The current available to charge the internal compensation capacitor: the output cannot change faster "
         "than I/C.",
         "It is a capacitor charging problem.", "hard"),
    ],
    "basic-electronics": [
        ("What is the typical forward voltage drop of a silicon diode, and of germanium?",
         "About 0.7 V for silicon and about 0.3 V for germanium.",
         "Germanium conducts sooner but leaks more.", "easy"),
        ("State the current relationship in a BJT.",
         "I_E = I_B + I_C, with I_C = β·I_B. The emitter current is the sum of the other two.",
         "Which terminal carries almost all of it?", "easy"),
        ("What is a Zener diode used for, and in which bias?",
         "Reverse bias, where it conducts at a controlled breakdown voltage — used as a voltage reference or "
         "regulator.",
         "Ordinary diodes avoid this region on purpose.", "medium"),
        ("Why is a full-wave rectifier easier to filter than a half-wave one?",
         "Its ripple frequency is twice the supply frequency, so the capacitor has less time to discharge and a "
         "smaller one suffices.",
         "Think about the gap between pulses.", "medium"),
    ],
    "digital-logic-design": [
        ("What separates a combinational circuit from a sequential one?",
         "A combinational output depends only on the present inputs; a sequential output also depends on stored "
         "state.",
         "Which one has memory?", "easy"),
        ("State De Morgan's first theorem.",
         "The complement of a product is the sum of the complements: (A·B)' = A' + B'.",
         "Break the line, change the sign.", "easy"),
        ("What are setup and hold time?",
         "The minimum time data must be stable before, and after, the active clock edge for the flip-flop to "
         "latch it correctly.",
         "One is about arriving early, one about leaving late.", "medium"),
        ("Why does a master-slave flip-flop avoid the race-around condition?",
         "The master is transparent only while the clock is high and the slave only after it falls, so the "
         "output cannot feed back and toggle repeatedly within one clock period.",
         "Think about when each half is open.", "hard"),
    ],
    "electronic-devices": [
        ("What is the depletion region of a PN junction?",
         "The zone either side of the junction with no free carriers, holding fixed ions and an electric field "
         "that opposes further diffusion.",
         "What is left behind when carriers recombine?", "medium"),
        ("Is a MOSFET voltage- or current-controlled, and how does a BJT differ?",
         "A MOSFET is voltage-controlled at the gate and draws almost no gate current; a BJT is current-"
         "controlled at the base.",
         "Which one needs a continuous input current to stay on?", "easy"),
        ("What is the threshold voltage of a MOSFET?",
         "The gate-source voltage at which a conducting channel first forms between source and drain.",
         "Below it, the device is off.", "easy"),
        ("What is the Early effect?",
         "Increasing the reverse bias on the collector-base junction narrows the base, so slightly more "
         "collector current flows — the output characteristics slope instead of being flat.",
         "It is why the curves are not perfectly horizontal.", "hard"),
    ],
    "measurements-instrumentation": [
        ("What is the difference between accuracy and precision?",
         "Accuracy is closeness to the true value; precision is how repeatable the reading is. An instrument "
         "can be precise and consistently wrong.",
         "A grouped cluster of shots far from the bullseye is which?", "easy"),
        ("What is instrument resolution?",
         "The smallest change in the measured quantity that the instrument can detect and display.",
         "It is the size of one step.", "easy"),
        ("What is a transducer?",
         "A device that converts one form of energy into another — in instrumentation, usually a physical "
         "quantity into an electrical signal.",
         "A thermocouple converts what into what?", "easy"),
        ("What does calibration actually establish?",
         "The relationship between the instrument's reading and a known standard, so the error can be corrected "
         "or at least quantified.",
         "It does not automatically make the instrument right.", "medium"),
    ],
    "microprocessors": [
        ("What is the difference between a microprocessor and a microcontroller?",
         "A microcontroller puts memory and peripherals on the same chip as the CPU, for embedded control; a "
         "microprocessor needs them externally and targets general computing.",
         "Which one would run a washing machine?", "easy"),
        ("What is an interrupt?",
         "A signal that makes the processor suspend the current program, run a service routine, and then resume "
         "where it left off.",
         "It is how hardware gets attention without being polled.", "easy"),
        ("Name the three stages of the instruction cycle.",
         "Fetch the instruction, decode what it means, execute it.",
         "Then the program counter moves on.", "easy"),
        ("Why does an interrupt service routine save the registers it uses?",
         "The interrupted program expects its state to be untouched when it resumes, and the ISR is not called "
         "by it, so nothing else will restore them.",
         "Who was using those registers before?", "medium"),
    ],
    "power-electronics": [
        ("What makes a thyristor different from a transistor as a switch?",
         "It latches: once triggered it stays on until the current falls below the holding value, so the gate "
         "loses control after turn-on.",
         "You can turn it on but not off.", "medium"),
        ("What is the difference between a rectifier and an inverter?",
         "A rectifier converts AC to DC; an inverter converts DC to AC.",
         "One is at the start of a power supply, one at the end.", "easy"),
        ("What does PWM control, and why switch at a constant frequency?",
         "It controls the average output voltage by varying pulse width. A fixed frequency keeps the filter "
         "design simple and the switching losses predictable.",
         "Vary width, not spacing.", "medium"),
        ("What is a chopper?",
         "A DC-to-DC converter, used to vary a DC voltage by switching it on and off.",
         "It is the DC equivalent of an AC transformer plus switch.", "easy"),
    ],
    "vlsi-design-subject": [
        ("What is CMOS's main advantage over older logic families?",
         "Almost no static power: in steady state only one transistor of each complementary pair conducts, so "
         "current flows mainly during switching.",
         "Think about what happens when the output is stable.", "medium"),
        ("What is a standard cell?",
         "A pre-characterised logic gate laid out to a fixed height, so place-and-route tools can tile them in "
         "rows automatically.",
         "Fixed height is what makes automation possible.", "medium"),
        ("What is clock skew and why does it matter?",
         "The difference in clock arrival time between registers. Too much of it eats into setup margin at the "
         "receiving register and can violate hold at another.",
         "It shortens the window you designed for.", "hard"),
        ("What is Moore's law, and what is it really an observation about?",
         "That transistor counts on a chip roughly double every two years. It is an empirical trend about "
         "manufacturing, not a physical law, and it has slowed.",
         "It says nothing about clock speed.", "easy"),
    ],

    # ------------------------------------------------------------- electrical --
    "circuit-theory": [
        ("State Kirchhoff's current law and what it rests on.",
         "The algebraic sum of currents at a node is zero, because charge cannot accumulate there.",
         "It is conservation of charge.", "easy"),
        ("State Kirchhoff's voltage law and what it rests on.",
         "The algebraic sum of voltages around any closed loop is zero, because the electric field is "
         "conservative.",
         "It is conservation of energy per unit charge.", "easy"),
        ("When is a Thevenin equivalent most useful?",
         "When one part of a circuit changes — usually the load — because you replace everything else with a "
         "single source and series resistance and only redo the easy part.",
         "What do you keep, and what do you throw away?", "medium"),
        ("What does the superposition theorem let you do, and what can it not give you?",
         "It lets you solve for voltages and currents one source at a time and add the results. It cannot be "
         "applied to power, because power depends on the square of current.",
         "Which quantity is non-linear in the sources?", "hard"),
    ],
    "electrical-machines-1": [
        ("What is the operating principle of a DC motor?",
         "A current-carrying conductor in a magnetic field experiences a force, F = BIL, which produces torque "
         "on the armature.",
         "It is the motor effect.", "easy"),
        ("What does the commutator do?",
         "It reverses the armature current every half turn so that the torque always acts in the same "
         "direction, converting the alternating induced voltage into unidirectional torque.",
         "Without it the motor would just oscillate.", "medium"),
        ("What is back EMF and how does it relate to the supply voltage?",
         "The voltage induced in the rotating armature, opposing the supply. V = E_b + I_a·R_a, so it sets how "
         "much current the motor draws.",
         "It is why a stalled motor burns out.", "hard"),
        ("Why must a DC series motor never be started without load?",
         "Its field flux comes from the armature current, so at no load the flux collapses and the speed rises "
         "until the machine destroys itself.",
         "Speed is inversely related to flux.", "hard"),
    ],
    "electrical-machines-2": [
        ("What do the turns ratios of an ideal transformer set?",
         "V2/V1 = N2/N1, and consequently I2/I1 = N1/N2, so power is conserved.",
         "Voltage goes up as current goes down.", "easy"),
        ("What is slip in an induction motor, and can it be zero under load?",
         "slip = (N_s − N)/N_s. It cannot be zero under load, because rotor current is induced by relative "
         "motion — at synchronous speed there would be no induced EMF and no torque.",
         "What induces the rotor current?", "hard"),
        ("State the formula for synchronous speed.",
         "N_s = 120·f / P, where f is the supply frequency and P the number of poles.",
         "More poles means slower.", "easy"),
        ("Why does an induction motor run at a poor power factor at light load?",
         "The magnetising current, which is largely reactive, dominates when the active component is small.",
         "Which part of the current does not do work?", "medium"),
    ],
    "electromagnetic-fields": [
        ("Summarise what each of Maxwell's four equations says.",
         "Gauss for E: charge is the source of electric flux. Gauss for B: there are no magnetic monopoles. "
         "Faraday: a changing magnetic field produces an electric field. Ampère–Maxwell: current and a "
         "changing electric field produce a magnetic field.",
         "Two about sources, two about induction.", "hard"),
        ("What do divergence and curl measure physically?",
         "Divergence is net outflow per unit volume — how much a point acts as a source. Curl is circulation "
         "per unit area — how much the field rotates about a point.",
         "One is about spreading, one about swirling.", "medium"),
        ("Why can an electromagnetic wave travel through a vacuum?",
         "A changing electric field produces a magnetic field and a changing magnetic field produces an "
         "electric field, so each sustains the other with no medium required.",
         "The two curl equations are a feedback loop.", "medium"),
        ("What is the physical meaning of electric potential?",
         "Work done per unit charge in bringing a test charge from infinity to that point.",
         "It is energy per coulomb.", "easy"),
    ],
    "signals-systems": [
        ("What makes a system linear, and what makes it time-invariant?",
         "Linear: superposition holds, so the response to a sum is the sum of the responses. Time-invariant: "
         "shifting the input shifts the output by the same amount.",
         "Two separate properties that happen to go together.", "medium"),
        ("What is an impulse response and why is it enough?",
         "The output when the input is a unit impulse. Because any signal can be written as a sum of scaled, "
         "shifted impulses, the impulse response fully characterises an LTI system.",
         "Decompose the input first.", "hard"),
        ("What does convolution compute?",
         "The output of an LTI system by sliding the impulse response over the input, multiplying and summing "
         "the overlap at each instant.",
         "Flip, slide, multiply, add.", "medium"),
        ("What does the Fourier transform tell you that the time-domain signal hides?",
         "Which frequencies are present and with what amplitude and phase.",
         "It changes the axis you look along.", "easy"),
    ],
    "dsp": [
        ("State the Nyquist–Shannon sampling theorem.",
         "A band-limited signal can be reconstructed exactly if it is sampled at more than twice its highest "
         "frequency component.",
         "Twice the top frequency, not the bandwidth.", "medium"),
        ("What is aliasing?",
         "High-frequency content appearing as a lower frequency because the sampling rate was too low, so the "
         "samples cannot distinguish the two.",
         "It is why wagon wheels look backwards on film.", "medium"),
        ("Why does an FIR filter always have linear phase?",
         "Its coefficients are symmetric, which gives a constant group delay across all frequencies, so the "
         "shape of the signal is preserved even as it is filtered.",
         "Symmetry is the key word.", "hard"),
        ("What does the FFT actually improve?",
         "It computes the same discrete Fourier transform in O(N log N) instead of O(N²). The result is "
         "identical; only the work changes.",
         "It is an algorithm, not a different transform.", "easy"),
    ],
    "communication-systems": [
        ("State Shannon's channel capacity theorem.",
         "C = B·log₂(1 + S/N): the maximum error-free data rate for a channel of bandwidth B and "
         "signal-to-noise ratio S/N.",
         "Bandwidth and SNR both help, but not equally.", "medium"),
        ("Why does FM use more bandwidth than AM?",
         "Its bandwidth grows with the modulation index, since sidebands spread over a wider range — the price "
         "of its better noise immunity.",
         "Trade bandwidth for immunity.", "medium"),
        ("What does a matched filter maximise?",
         "The signal-to-noise ratio at the sampling instant, which is what minimises the probability of a "
         "detection error.",
         "It is matched to the pulse shape.", "hard"),
        ("Why is a carrier wave used at all?",
         "To shift the signal to a frequency that radiates efficiently — an antenna needs to be comparable in "
         "size to a wavelength — and to allow many signals to share a medium on different carriers.",
         "Baseband audio would need an enormous antenna.", "medium"),
    ],

    # -------------------------------------------------------------------- CSE --
    "oops": [
        ("Name the four pillars of object-oriented programming.",
         "Encapsulation, inheritance, polymorphism and abstraction.",
         "Three of them start with a vowel.", "easy"),
        ("What is the difference between overloading and overriding?",
         "Overloading is several methods with the same name but different signatures in one class, resolved at "
         "compile time. Overriding is a subclass replacing a superclass method, resolved at run time.",
         "One is horizontal, one is vertical.", "medium"),
        ("What is the diamond problem?",
         "When a class inherits the same base through two different paths, the base's members are ambiguous — "
         "solved by virtual inheritance in C++ or a method resolution order in Python.",
         "Draw the inheritance graph.", "hard"),
        ("State the Liskov substitution principle.",
         "A subclass must be usable anywhere its base class is expected, without the caller having to know or "
         "change its behaviour.",
         "It is what inheritance is supposed to mean.", "medium"),
    ],
    "theory-of-computation": [
        ("What is the difference between a DFA and an NFA, and do they differ in power?",
         "A DFA has exactly one transition per symbol per state; an NFA may have several, or none. They accept "
         "exactly the same class of languages — the regular ones.",
         "Converting costs an exponential number of states.", "medium"),
        ("What is the pumping lemma used for?",
         "To prove that a language is *not* regular. It says any sufficiently long string in a regular language "
         "contains a pumpable substring, so a counterexample disproves regularity.",
         "It can never prove a language *is* regular.", "hard"),
        ("What is a Turing machine?",
         "An abstract machine with an unbounded tape, a head and a finite state table. It defines the boundary "
         "of what is mechanically computable.",
         "Unbounded tape is the important part.", "medium"),
        ("Why is the halting problem undecidable?",
         "Assume a decider exists and build a program that does the opposite of what the decider predicts "
         "about itself; feeding it to itself gives a contradiction.",
         "It is diagonalisation, like Russell's paradox.", "hard"),
    ],
    "compiler-design": [
        ("Name the phases of a compiler in order.",
         "Lexical analysis, syntax analysis, semantic analysis, intermediate code generation, optimisation and "
         "code generation.",
         "Three analyses, then three generations.", "medium"),
        ("What is a symbol table for?",
         "It maps each identifier to its declared attributes — type, scope and storage — so later phases can "
         "check uses against declarations.",
         "It is the compiler's memory of declarations.", "easy"),
        ("What distinguishes top-down from bottom-up parsing?",
         "Top-down predicts which production to expand from the start symbol (LL); bottom-up reduces the input "
         "back to the start symbol by recognising handles (LR).",
         "One predicts, one recognises.", "medium"),
        ("What is three-address code?",
         "An intermediate representation in which every instruction has at most one operator, so complex "
         "expressions become a sequence of simple ones with named temporaries.",
         "It makes optimisation tractable.", "medium"),
    ],
    "computer-architecture": [
        ("Name the three types of pipeline hazard.",
         "Structural (two instructions want the same hardware), data (an instruction needs a result not yet "
         "written) and control (the next instruction depends on a branch).",
         "Hardware, values, and the program counter.", "medium"),
        ("What limits a pipeline's speedup?",
         "The slowest stage sets the clock, and hazards plus pipeline fill and drain mean real speedup is well "
         "below the number of stages.",
         "Ideal speedup is never reached.", "medium"),
        ("State Amdahl's law and its consequence.",
         "Overall speedup is limited by the fraction that cannot be parallelised: as that fraction approaches "
         "zero improvement, total speedup approaches 1 over that fraction.",
         "The serial part is the ceiling.", "hard"),
        ("How do you compute average memory access time from the hit ratio?",
         "t_avg = hit_ratio × t_cache + (1 − hit_ratio) × t_memory, ignoring write-back effects.",
         "It is a weighted average.", "easy"),
    ],
    "cryptography-security": [
        ("What is the practical difference between symmetric and asymmetric cryptography?",
         "Symmetric uses one shared key and is fast, but the key must be distributed secretly. Asymmetric uses "
         "a public/private pair, solving distribution and enabling signatures, but is far slower.",
         "One is fast, one solves key exchange.", "medium"),
        ("What property of a hash function makes it useful for integrity?",
         "Collision resistance: you cannot find two different inputs with the same digest, so any change to "
         "the input changes the digest.",
         "Preimage resistance is the other one.", "medium"),
        ("Why is ECB mode considered unsafe for real data?",
         "Identical plaintext blocks encrypt to identical ciphertext blocks, so structure and repetition in "
         "the data remain visible.",
         "It encrypts each block in isolation.", "hard"),
        ("What does a TLS certificate actually protect against?",
         "It authenticates the server, so a man in the middle cannot impersonate it — encryption alone would "
         "still let an attacker sit between you and the real server.",
         "Encryption without authentication is not enough.", "hard"),
    ],
    "cloud-computing-subject": [
        ("Distinguish IaaS, PaaS and SaaS by who manages what.",
         "IaaS: you manage the OS, runtime and application. PaaS: you manage only the application. SaaS: you "
         "use the application.",
         "The stack shrinks as you go up.", "easy"),
        ("State the CAP theorem.",
         "A distributed system cannot simultaneously guarantee consistency, availability and partition "
         "tolerance. Since partitions do happen, the real choice is between consistency and availability during "
         "one.",
         "You only really choose when the network breaks.", "hard"),
        ("What is the purpose of a load balancer's health check?",
         "To stop routing traffic to instances that have stopped serving correctly, so a failed node degrades "
         "capacity rather than causing errors.",
         "It is how failures become invisible to users.", "medium"),
        ("What is autoscaling, and what can go wrong with it?",
         "Adding and removing instances in response to load metrics. Badly configured, it oscillates — scaling "
         "up on a spike, scaling down too eagerly, then repeating.",
         "Scale-down thresholds need hysteresis.", "medium"),
    ],
    "data-science-foundations": [
        ("What is the bias–variance trade-off?",
         "Bias is systematic error from assumptions too strong for the data; variance is sensitivity to the "
         "particular sample. Reducing one usually increases the other, and total error is their sum plus "
         "irreducible noise.",
         "Underfitting and overfitting are the two ends.", "hard"),
        ("How do you recognise overfitting?",
         "Training error is low and keeps falling while validation error stops improving and rises.",
         "It is the gap between the two curves.", "medium"),
        ("What is the difference between precision and recall?",
         "Precision: of the items you predicted positive, how many were right. Recall: of the items that were "
         "actually positive, how many did you find.",
         "One is about false positives, one about false negatives.", "medium"),
        ("Why hold out a test set instead of reporting training accuracy?",
         "Training accuracy measures memorisation. Only unseen data estimates generalisation, which is the "
         "thing you actually care about.",
         "The model has already seen the training set.", "easy"),
    ],
    "deep-learning": [
        ("What is the vanishing gradient problem?",
         "Gradients shrink multiplicatively as they propagate back through many layers with saturating "
         "activations, so early layers receive almost no learning signal.",
         "It is a chain rule product of small numbers.", "hard"),
        ("Why is ReLU widely used instead of a sigmoid?",
         "For positive inputs it does not saturate, so its gradient stays at 1 and does not vanish; it is also "
         "cheap to evaluate.",
         "Sigmoid derivatives are always below 0.25.", "medium"),
        ("What does batch normalisation do, and why does it help?",
         "It normalises a layer's inputs over each mini-batch, which keeps activations in a well-behaved range "
         "and allows a larger learning rate.",
         "It stops each layer chasing a moving target.", "medium"),
        ("What is dropout, and why does it act as a regulariser?",
         "Randomly zeroing a fraction of units during training, so no unit can rely on any particular partner "
         "— effectively training an ensemble that is averaged at test time.",
         "It prevents co-adaptation.", "hard"),
    ],
    "web-technologies": [
        ("What is the difference between HTTP and HTTPS?",
         "HTTPS is HTTP carried inside TLS, so the traffic is encrypted and the server's identity is "
         "authenticated by a certificate.",
         "It adds encryption *and* identity.", "easy"),
        ("What does a 3xx status code mean?",
         "A redirect: the resource is elsewhere and the response says where.",
         "1xx is informational, 2xx success, 4xx your fault, 5xx theirs.", "easy"),
        ("What is the difference between localStorage and sessionStorage?",
         "sessionStorage is cleared when the tab closes; localStorage persists until explicitly deleted.",
         "One of them dies with the tab.", "easy"),
        ("What problem does CORS solve, and for whom?",
         "It lets a server declare which other origins may read its responses. It protects users from a "
         "malicious page reading data on their behalf, not the server from being contacted.",
         "The browser enforces it, not the server.", "hard"),
    ],
    "discrete-mathematics": [
        ("State the pigeonhole principle.",
         "If n + 1 items are placed into n boxes, at least one box holds two or more.",
         "More items than places.", "easy"),
        ("What is a bijection, and why does it matter?",
         "A function that is both one-to-one and onto. It proves two sets have the same cardinality, even "
         "infinite ones.",
         "It is how you count without counting.", "medium"),
        ("State the handshaking lemma.",
         "The sum of the degrees of all vertices equals twice the number of edges, so the number of "
         "odd-degree vertices is always even.",
         "Every edge is counted twice.", "medium"),
        ("What are the two parts of a proof by induction?",
         "The base case, and the inductive step showing that if the statement holds for k it holds for k + 1. "
         "Both are needed: either alone proves nothing.",
         "A ladder with no first rung, or no way up.", "medium"),
    ],
    "engineering-mathematics-3": [
        ("What is the Laplace transform for?",
         "Converting a differential equation into an algebraic one in the s-domain, where it can be solved and "
         "then inverted.",
         "Derivatives become multiplication by s.", "medium"),
        ("What does a Fourier series represent?",
         "A periodic function as a sum of sines and cosines of integer multiples of the fundamental frequency.",
         "Any periodic signal, given mild conditions.", "easy"),
        ("What is the Jacobian used for in multiple integrals?",
         "It scales the volume element when you change variables, so the integral keeps its value in the new "
         "coordinates.",
         "It is the local stretch factor.", "hard"),
        ("What determines the order of a partial differential equation?",
         "The order of the highest partial derivative appearing in it.",
         "Same rule as for ODEs.", "easy"),
    ],

    # ------------------------------------------------------------- mechanical --
    "engineering-mechanics-fy": [
        ("What are the two conditions for static equilibrium?",
         "The vector sum of all forces is zero, and the sum of moments about any point is zero.",
         "No translation and no rotation.", "easy"),
        ("What is a free body diagram?",
         "The body isolated from its surroundings with every external force and moment drawn on it, including "
         "the reaction forces the supports provide.",
         "You cannot solve for what you have not drawn.", "easy"),
        ("How do static and kinetic friction differ?",
         "Static friction matches the applied force up to a maximum of μ_s·N; kinetic friction is a constant "
         "μ_k·N, and μ_k is smaller than μ_s.",
         "It is harder to start something moving than to keep it moving.", "medium"),
        ("What is a couple?",
         "Two equal, opposite, parallel forces separated by a distance. It produces a pure moment with no net "
         "force, so it cannot be balanced by a single force.",
         "Pure rotation, no translation.", "medium"),
    ],
    "heat-transfer": [
        ("Name the three modes of heat transfer.",
         "Conduction through a material, convection by fluid motion, and radiation as electromagnetic waves — "
         "which alone needs no medium.",
         "One of them works in a vacuum.", "easy"),
        ("State Fourier's law of conduction.",
         "q = −k·A·dT/dx: heat flow is proportional to the area and the temperature gradient, and the negative "
         "sign says it goes downhill.",
         "k is the material property.", "easy"),
        ("What is the overall heat transfer coefficient U?",
         "The reciprocal of the total thermal resistance across a composite wall, letting you write Q = U·A·ΔT "
         "as if it were a single layer.",
         "Resistances in series add; U inverts the sum.", "medium"),
        ("Why are fins used, and when do they stop helping?",
         "They increase surface area so convection removes more heat. They stop helping when the fin's own "
         "conduction resistance is high enough that its tip is near ambient — adding length then adds little.",
         "Effectiveness falls as the fin gets longer.", "hard"),
    ],
    "theory-of-machines": [
        ("What is the difference between a mechanism and a machine?",
         "A mechanism transmits or transforms motion; a machine also transmits or transforms force and does "
         "useful work.",
         "Every machine contains mechanisms.", "easy"),
        ("State Grashof's condition for a four-bar linkage.",
         "The sum of the shortest and longest links must be less than or equal to the sum of the other two; "
         "only then can at least one link rotate through a full revolution.",
         "It decides whether you get a crank or a rocker.", "hard"),
        ("What is the degree of freedom of a mechanism?",
         "The number of independent inputs required to fix the position of every link.",
         "Count what you would have to drive.", "medium"),
        ("Why does a large pressure angle on a cam cause trouble?",
         "The force on the follower has a large component perpendicular to its motion, so friction rises and "
         "the follower can jam in its guide.",
         "Decompose the force along and across the motion.", "hard"),
    ],
    "machine-design": [
        ("What is a factor of safety, and what does it cover?",
         "The ratio of failure stress to working stress. It covers uncertainty in loads, material properties, "
         "manufacturing defects and the analysis itself.",
         "It is a budget for being wrong.", "easy"),
        ("What does an S-N curve show?",
         "Stress amplitude against the number of cycles to failure. For steels it flattens to an endurance "
         "limit below which fatigue failure does not occur.",
         "It is the fatigue picture.", "medium"),
        ("What is stress concentration, and what quantifies it?",
         "The local rise in stress at a geometric discontinuity such as a hole or a sharp fillet, quantified "
         "by the factor K_t. It matters most under fatigue loading.",
         "Sharp corners are where parts start to crack.", "medium"),
        ("What is the difference between yield strength and ultimate strength?",
         "Yield is where permanent deformation begins; ultimate is the maximum stress the material reaches "
         "before it fractures.",
         "Design against yield, not against fracture.", "medium"),
    ],
    "manufacturing-processes": [
        ("Compare casting and forging.",
         "Casting pours molten metal into a mould, allowing complex shapes but leaving a cast structure. "
         "Forging deforms solid metal, which aligns the grain flow and gives higher strength.",
         "One is liquid, one is solid.", "medium"),
        ("What separates hot working from cold working?",
         "Hot working is above the recrystallisation temperature, so strain hardening is continuously removed "
         "and large deformations are possible. Cold working hardens the metal and gives better surface finish.",
         "Recrystallisation is the boundary.", "hard"),
        ("What is the difference between a jig and a fixture?",
         "A jig guides the cutting tool as well as holding the workpiece; a fixture only locates and holds it.",
         "Only one of them touches the tool path.", "medium"),
        ("Why does a cutting fluid matter beyond cooling?",
         "It also lubricates the tool-chip interface, reducing built-up edge and tool wear, and flushes chips "
         "out of the cut.",
         "Cooling is only half of it.", "medium"),
    ],
    "ic-engines": [
        ("How do the Otto and Diesel cycles differ in heat addition?",
         "Otto adds heat at constant volume with spark ignition; Diesel adds it at constant pressure with "
         "compression ignition and no spark plug.",
         "One is a bang, one is a burn.", "hard"),
        ("What is knocking in a petrol engine?",
         "Autoignition of the unburnt end gas before the flame front reaches it, causing a sudden pressure "
         "spike and the characteristic metallic sound.",
         "It is combustion happening too early in the wrong place.", "hard"),
        ("What is the stoichiometric air-fuel ratio for petrol?",
         "About 14.7 parts air to 1 part fuel by mass.",
         "Richer than that is under 14.7.", "easy"),
        ("Name the four strokes of a four-stroke cycle.",
         "Intake, compression, power and exhaust — two crankshaft revolutions per cycle.",
         "Two revolutions, one power stroke.", "easy"),
    ],
    "refrigeration-ac": [
        ("Name the four processes of a vapour-compression cycle.",
         "Compression, condensation, expansion and evaporation.",
         "Two heat exchangers and two pressure-changing devices.", "easy"),
        ("What does the expansion valve do?",
         "It drops the refrigerant's pressure so it can evaporate at a low temperature, absorbing heat from "
         "the space being cooled.",
         "Low pressure means low boiling point.", "medium"),
        ("What is the coefficient of performance, and can it exceed 1?",
         "The desired heat effect divided by the work input. It routinely exceeds 1, because the machine moves "
         "heat rather than creating it.",
         "It is not an efficiency.", "medium"),
        ("What is the difference between sensible cooling and dehumidification?",
         "Sensible cooling lowers the air temperature. Dehumidification removes moisture, which happens when "
         "the coil surface is below the dew point so water condenses out.",
         "One changes temperature, one changes moisture content.", "hard"),
    ],
    "cad-cam": [
        ("What does parametric modelling mean?",
         "The geometry is driven by dimensions and constraints rather than fixed coordinates, so changing a "
         "dimension rebuilds the whole model consistently.",
         "Change one number and everything updates.", "easy"),
        ("What is the difference between G00 and G01?",
         "G00 is a rapid traverse with the tool clear of the work; G01 is linear interpolation at the "
         "programmed feed rate, used for cutting.",
         "Only one of them is allowed to touch the part.", "medium"),
        ("What does a CNC post-processor do?",
         "It converts the neutral toolpath into the specific G-code dialect and syntax of the target machine "
         "and controller.",
         "The same toolpath, different machines.", "medium"),
        ("What is tolerance stack-up?",
         "The accumulation of individual part tolerances through an assembly, which can make a set of "
         "in-specification parts fail to fit together.",
         "Every part being legal does not make the assembly legal.", "hard"),
    ],

    "basic-electrical": [
        ("What does Kirchhoff's voltage law state?",
         "The algebraic sum of the voltages around any closed loop is zero — energy supplied equals energy "
         "dissipated, so you cannot gain potential by going round a loop.",
         "It is conservation of energy applied to a loop.", "easy"),
        ("How do you read a resistor's colour bands?",
         "The first two bands give the significant digits, the third the multiplier and the fourth the "
         "tolerance. Brown-black-red is 1, 0 and ×100, so 1 kΩ.",
         "Digits, then multiplier, then tolerance.", "medium"),
    ],
    "engineering-mathematics-1": [
        ("When may you apply L'Hôpital's rule?",
         "Only when the limit takes the indeterminate form 0/0 or ∞/∞, and the derivative of the denominator "
         "is not itself zero at that point.",
         "Check the form before differentiating.", "medium"),
        ("What does the nth derivative of e^x equal?",
         "e^x itself. The exponential is its own derivative at every order, which is why it solves y' = y.",
         "Differentiating it changes nothing.", "easy"),
    ],
    "engineering-mathematics-2": [
        ("What is the Laplace transform of e^(at)?",
         "1/(s − a), valid for Re(s) > a. The transform converges only where the exponential decay of e^(−st) "
         "outruns the growth of e^(at).",
         "Region of convergence matters.", "hard"),
        ("Why convert an ODE with the Laplace transform?",
         "Differentiation becomes multiplication by s, turning a differential equation into an algebraic one "
         "that handles initial conditions directly.",
         "It moves you from calculus to algebra.", "medium"),
    ],
    "engineering-physics": [
        ("What does the photoelectric effect show that classical wave theory cannot explain?",
         "That emission depends on frequency, not intensity. Below the threshold frequency no electron is "
         "emitted however bright the light, which only a quantised photon explains.",
         "Intensity changes the count, not the energy.", "hard"),
        ("What is the difference between an intrinsic and an extrinsic semiconductor?",
         "An intrinsic one is pure, with equal electron and hole concentrations. Doping makes it extrinsic and "
         "deliberately unbalances them to raise conductivity.",
         "Doping is the difference.", "medium"),
    ],
    "programming-fundamentals": [
        ("What is the difference between a shallow and a deep copy?",
         "A shallow copy shares nested objects with the original, so mutating a list inside it affects both. "
         "A deep copy recurses and shares nothing.",
         "It is about nested objects.", "hard"),
        ("When should you reach for a set instead of a list?",
         "When you need membership testing or uniqueness. A set hashes its elements so lookup is O(1), "
         "where a list scans in O(n).",
         "Hashing beats scanning.", "medium"),
    ],
    "software-engineering": [
        ("What is technical debt?",
         "The accumulated cost of shortcuts taken to ship sooner. It is not a mistake in itself — it becomes "
         "a problem when the interest, in slowdown and defects, exceeds what the shortcut bought.",
         "Shortcuts have interest.", "medium"),
        ("What distinguishes verification from validation?",
         "Verification asks whether the product was built to specification; validation asks whether it is the "
         "right product for the user. You can pass one and fail the other.",
         "Built right versus the right thing.", "hard"),
    ],
    "soil-mechanics": [
        ("What is the void ratio?",
         "The volume of voids divided by the volume of solids, e = V_v / V_s. Unlike porosity it can exceed "
         "one, because it is a ratio to solids rather than to the whole.",
         "Compare it with porosity.", "medium"),
        ("What does Darcy's law describe?",
         "Laminar flow through soil, where discharge velocity is proportional to the hydraulic gradient. The "
         "constant of proportionality is the coefficient of permeability.",
         "It applies only to laminar flow.", "medium"),
    ],
    "digital-electronics": [
        ("Why is a NAND gate called universal?",
         "Any Boolean function can be built from NAND gates alone, because NOT, AND and OR are each expressible "
         "with them — which is why chips are manufactured that way.",
         "You can make every other gate from it.", "medium"),
    ],
    "fluid-mechanics": [
        ("When does the Reynolds number say flow is turbulent?",
         "Above roughly 4000 in a pipe. It compares inertial to viscous forces, Re = ρvD/μ, so fast, large or "
         "thin flows tip over.",
         "Inertia versus viscosity.", "hard"),
    ],
    "machine-learning": [
        ("What is the bias-variance trade-off?",
         "A simple model underfits with high bias; a complex one overfits with high variance. Total error is "
         "the sum of both plus irreducible noise, so reducing one raises the other.",
         "Underfitting versus overfitting.", "hard"),
    ],
    "strength-of-materials": [
        ("What is the difference between stress and strain?",
         "Stress is internal force per unit area, in pascals. Strain is the resulting deformation per unit "
         "length, and is dimensionless.",
         "One has units, the other does not.", "easy"),
    ],
    "thermodynamics": [
        ("What does the Carnot efficiency depend on?",
         "Only the two reservoir temperatures, η = 1 − T_cold/T_hot. No real engine between the same reservoirs "
         "can beat it, whatever its working fluid.",
         "Nothing but the temperatures.", "hard"),
    ],

    "control-systems-subject": [
        ("What does each term of a PID controller act on?",
         "P acts on the present error, I on its accumulated value and D on its rate of change. Only the "
         "integral term removes steady-state offset; only the derivative term adds damping.",
         "Present, past and future of the error.", "medium"),
        ("What does adding a pole to a transfer function do?",
         "It slows the response and pulls the root locus toward the right half-plane, reducing the stability "
         "margin. Adding a zero does the opposite.",
         "Poles attract the locus, zeros repel it.", "hard"),
        ("What is gain margin?",
         "How much the loop gain can increase before the closed-loop system becomes unstable, measured at the "
         "frequency where the phase reaches −180°.",
         "It is read off the Bode plot at one specific frequency.", "hard"),
        ("What does the Routh–Hurwitz criterion tell you without solving anything?",
         "How many closed-loop roots lie in the right half-plane, from the characteristic polynomial's "
         "coefficients alone — so you can judge stability without finding the roots.",
         "Sign changes in the first column.", "hard"),
    ],
    "power-systems": [
        ("What is the per-unit system for?",
         "It expresses quantities as ratios to a chosen base, so transformer turns ratios stop changing the "
         "numbers and equipment on different voltage levels can be compared directly.",
         "It removes the transformer from the arithmetic.", "medium"),
        ("What separates a symmetrical from an unsymmetrical fault?",
         "A symmetrical fault affects all three phases equally. An unsymmetrical one does not, so it must be "
         "analysed with positive, negative and zero sequence components.",
         "Only one of them needs sequence networks.", "hard"),
        ("What does a load flow study compute?",
         "The bus voltages and the real and reactive power flows throughout the network under steady-state "
         "conditions, which is the basis for planning and for checking line loadings.",
         "It solves the network for a given set of injections.", "medium"),
        ("Why is power transmitted at high voltage?",
         "For the same power, higher voltage means lower current, and losses are I²R — so they fall with the "
         "square of the current.",
         "Losses depend on current, not on power.", "medium"),
    ],

    # ------------------------------------------------------------------ civil --
    "structural-analysis": [
        ("What distinguishes a statically determinate structure from an indeterminate one?",
         "A determinate structure can be solved from the equilibrium equations alone. An indeterminate one has "
         "more unknowns than equations, so compatibility of deformations is needed too.",
         "Count unknowns against equations.", "medium"),
        ("What is the degree of static indeterminacy?",
         "The number of redundant unknowns: total unknown reactions and internal forces minus the number of "
         "independent equilibrium equations available.",
         "How many extra equations must you find?", "hard"),
        ("What does a bending moment diagram show?",
         "How the internal resisting moment varies along a member, which is where you find the maximum moment "
         "the section must carry.",
         "Its slope is the shear force.", "medium"),
        ("When may the principle of superposition be applied?",
         "Only when the material is linear elastic and the deformations are small enough not to change the "
         "geometry the loads act on.",
         "Two conditions, both required.", "hard"),
    ],
    "rc-design": [
        ("Why is steel placed in concrete at all?",
         "Concrete is strong in compression and very weak in tension; the steel carries the tension that "
         "concrete cannot.",
         "Each material does what it is good at.", "easy"),
        ("What is the difference between a singly and a doubly reinforced beam?",
         "A singly reinforced beam has only tension steel. A doubly reinforced one adds compression steel, "
         "used where the section is restricted or where reversal of moment is possible.",
         "Where does the extra steel go, and why?", "medium"),
        ("What are stirrups for?",
         "To resist shear, which concrete alone handles poorly near supports, and to hold the longitudinal "
         "bars in position during pouring.",
         "They do two jobs, not one.", "medium"),
        ("Why is concrete cover specified?",
         "It protects the steel from corrosion and gives fire resistance; too little and the reinforcement "
         "rusts, too much and the cover cracks away from the bar.",
         "It is a durability requirement, not a structural one.", "medium"),
    ],
    "concrete-technology": [
        ("What does the water-cement ratio control?",
         "Strength and durability primarily: a lower w/c gives a denser, stronger paste, but too little water "
         "makes the mix unworkable and impossible to compact.",
         "It is the single most important number in a mix.", "medium"),
        ("What is segregation, and what causes it?",
         "The separation of coarse aggregate from the mortar, caused by a harsh mix, excessive free water, "
         "over-vibration or dropping concrete too far.",
         "The big stones end up at the bottom.", "medium"),
        ("Why must concrete be cured?",
         "Hydration needs water. If the surface dries out, the reaction stops there and the surface stays "
         "weak, dusty and permeable.",
         "It is not about drying — it is the opposite.", "easy"),
        ("Why is 28 days the standard age for testing strength?",
         "Ordinary Portland cement has hydrated substantially by then, so the result is stable and comparable "
         "— though hydration continues, slowly, for years.",
         "It is a convention, not an end point.", "medium"),
    ],
    "hydraulics": [
        ("What is the difference between a pump and a turbine?",
         "A pump adds energy to a fluid, converting shaft work into pressure and velocity. A turbine extracts "
         "energy from a fluid, converting it into shaft work.",
         "They are the same machine run backwards.", "easy"),
        ("What is specific speed, and why is it useful?",
         "A dimensionless index combining head, flow and rotational speed. It classifies machines by shape and "
         "duty independently of size, so you can select a type from the duty alone.",
         "It lets you compare a small pump with a large one.", "hard"),
        ("What is water hammer?",
         "A pressure surge caused when flow is stopped suddenly: the fluid's momentum has to go somewhere, so "
         "a pressure wave travels back up the pipe and can burst it.",
         "It is why valves are closed slowly.", "medium"),
        ("What separates an impulse turbine from a reaction turbine?",
         "An impulse turbine uses only the kinetic energy of a jet at atmospheric pressure, as in a Pelton "
         "wheel. A reaction turbine develops torque from a pressure drop across the runner, as in Francis and "
         "Kaplan.",
         "Pressure constant, or pressure falling?", "hard"),
    ],
    "surveying": [
        ("What is the difference between a level line and a horizontal line?",
         "A level line follows the curvature of the earth and is everywhere perpendicular to the plumb line; a "
         "horizontal line is tangential and diverges from it over distance.",
         "They coincide only over short distances.", "hard"),
        ("What is a benchmark?",
         "A point of known elevation, used as the reference from which levels are taken.",
         "Everything else is measured relative to it.", "easy"),
        ("What does a total station add to a theodolite?",
         "Electronic distance measurement and onboard recording, so angles and distances are captured and "
         "stored together without separate taping.",
         "It measures angles *and* distances.", "easy"),
        ("Why is a traverse closed?",
         "So the angular and linear misclosure can be computed. A closed traverse reveals its own errors; an "
         "open one hides them.",
         "You cannot correct what you cannot detect.", "medium"),
    ],
    "estimating-costing": [
        ("What is the difference between an approximate and a detailed estimate?",
         "An approximate estimate uses unit rates per area or volume for an early figure. A detailed estimate "
         "measures every item from the drawings and prices them individually.",
         "One is for feasibility, one for tendering.", "easy"),
        ("What is a rate analysis?",
         "Breaking a composite rate into its components — materials, labour, plant and overheads — so it can "
         "be checked, updated or defended.",
         "It shows where a rate actually comes from.", "medium"),
        ("What is a contingency in an estimate?",
         "An allowance for unforeseen items, expressed as a percentage of the estimated cost. It is not a "
         "buffer for poor estimating.",
         "Known unknowns, not mistakes.", "medium"),
        ("What is a work charge establishment?",
         "Temporary staff engaged specifically for a large work and charged to it, rather than to the "
         "department's regular establishment.",
         "Hired for the job, paid from the job.", "medium"),
    ],
    "transportation-engineering-subject": [
        ("What is the difference between flexible and rigid pavement?",
         "Flexible (bituminous) pavement transfers load by grain-to-grain contact through its layers. Rigid "
         "(concrete) pavement spreads load over a wide area by slab action.",
         "One distributes, one bridges.", "hard"),
        ("What is stopping sight distance?",
         "The distance a driver needs to perceive a hazard, react, and brake to a stop — the sum of the "
         "distance covered during perception-reaction time and the braking distance.",
         "Two components, both needed.", "medium"),
        ("What is super-elevation for?",
         "Banking a horizontal curve so that a component of the vehicle's weight helps resist the centrifugal "
         "force, reducing reliance on friction.",
         "It tilts the road to do some of the work.", "medium"),
        ("What does the California Bearing Ratio measure?",
         "The strength of a subgrade or base material relative to a standard crushed stone, used to decide "
         "how thick the pavement layers must be.",
         "Higher CBR means a thinner pavement.", "medium"),
    ],
    "environmental-engineering-subject": [
        ("What is BOD and why does it matter?",
         "Biochemical oxygen demand: the oxygen micro-organisms consume while decomposing organic matter. High "
         "BOD means the receiving water will lose its dissolved oxygen and aquatic life will die.",
         "It measures the oxygen the water will owe.", "hard"),
        ("What does primary treatment remove, and how?",
         "Settleable solids by sedimentation and floating matter by screening and skimming — physical "
         "processes, not biological ones.",
         "No microbes are involved yet.", "easy"),
        ("What is the activated sludge process?",
         "Aerobic micro-organisms digest dissolved organic matter in an aerated tank; part of the settled "
         "biomass is returned to keep the population active.",
         "It is biological, and it recycles its own workers.", "medium"),
        ("What is eutrophication?",
         "Nutrient overload, usually nitrogen and phosphorus, causing algal blooms whose decomposition then "
         "depletes the water's oxygen.",
         "Too much fertiliser, then no oxygen.", "medium"),
    ],

    # --------------------------------------------------------------- chemical --
    "chemical-thermodynamics": [
        ("What does fugacity correct for?",
         "Non-ideality. It is an effective pressure that lets real-gas equilibria be written with ideal "
         "expressions, with the fugacity coefficient φ = f/P approaching 1 as pressure falls.",
         "It is the pressure a real gas wishes it had.", "hard"),
        ("State the Gibbs–Duhem equation.",
         "At constant temperature and pressure, the sum over all components of x_i·dμ_i equals zero — the "
         "chemical potentials cannot change independently.",
         "It constrains the mixture.", "hard"),
        ("What is the maximum efficiency of a heat engine operating between two temperatures?",
         "The Carnot efficiency, 1 − T_C/T_H, using absolute temperatures. No real engine can exceed it.",
         "Absolute temperatures, not Celsius.", "medium"),
        ("What does the third law of thermodynamics establish?",
         "That the entropy of a perfect crystal approaches zero as the temperature approaches absolute zero, "
         "which gives entropies an absolute reference.",
         "It is why absolute entropies exist.", "medium"),
    ],
    "reaction-engineering": [
        ("What is the essential difference between a PFR and a CSTR?",
         "A plug flow reactor has no axial mixing, so concentration falls along its length. A CSTR is "
         "perfectly mixed, so everything inside is at the outlet concentration — the lowest, and slowest, "
         "value.",
         "That is why a PFR is usually smaller for the same conversion.", "hard"),
        ("What is conversion?",
         "The fraction of the limiting reactant that has reacted, X = (moles in − moles out) / moles in.",
         "It is a fraction, so it is between 0 and 1.", "easy"),
        ("What does the Arrhenius equation say about temperature?",
         "k = A·exp(−Ea/RT), so the rate constant rises steeply and non-linearly with temperature; a high "
         "activation energy means a steeper rise.",
         "It is exponential, not linear.", "medium"),
        ("What is space time?",
         "Reactor volume divided by the volumetric feed rate — the time a fluid element would take to pass "
         "through at inlet conditions.",
         "It has units of time but is a ratio of volumes.", "hard"),
    ],
    "mass-transfer": [
        ("State Fick's first law of diffusion.",
         "Diffusive flux is proportional to the negative concentration gradient, with the diffusion "
         "coefficient as the constant.",
         "Matter flows downhill in concentration, like heat.", "medium"),
        ("What is the difference between absorption and stripping?",
         "Absorption transfers a solute from a gas into a liquid; stripping transfers it from a liquid into a "
         "gas. Same equipment, opposite direction.",
         "It depends which way you want the solute to go.", "medium"),
        ("What is HETP?",
         "Height equivalent to a theoretical plate: the height of packing that achieves the same separation as "
         "one ideal equilibrium stage.",
         "It converts stages into metres.", "hard"),
        ("What property makes distillation possible?",
         "A difference in volatility between the components, so the vapour is richer in the more volatile one "
         "than the liquid it came from.",
         "No volatility difference, no separation.", "medium"),
    ],
    "fluid-flow-operations": [
        ("What does the Reynolds number compare, and what is its significance?",
         "Inertial to viscous forces, Re = ρvD/μ. Below about 2100 pipe flow is laminar; above about 4000 it is "
         "turbulent.",
         "It predicts the flow regime, not the pressure drop.", "medium"),
        ("What does the Darcy–Weisbach equation calculate?",
         "Frictional head loss in a pipe: h_f = f·(L/D)·(v²/2g).",
         "Length, diameter, velocity and a friction factor.", "medium"),
        ("What causes cavitation in a pump?",
         "Local pressure falling below the liquid's vapour pressure, forming bubbles that collapse violently "
         "when they reach higher pressure, eroding the impeller.",
         "It happens at the suction side.", "hard"),
        ("What distinguishes a Newtonian from a non-Newtonian fluid?",
         "In a Newtonian fluid the viscosity is constant regardless of shear rate. In a non-Newtonian one it "
         "changes — ketchup thins when shaken, cornflour paste thickens.",
         "Is viscosity a constant, or a function?", "medium"),
    ],
    "heat-transfer-operations": [
        ("What is the LMTD and why is it needed?",
         "The log-mean temperature difference. Because the driving force varies along an exchanger, the "
         "arithmetic mean is wrong; LMTD is the correct average for Q = U·A·ΔT_lm.",
         "The temperature difference is not constant along the length.", "hard"),
        ("Why is counter-current usually better than parallel flow?",
         "It maintains a larger mean temperature difference along the whole length, so less area is needed for "
         "the same duty, and the outlet can approach the inlet temperature of the other stream.",
         "Look at the two temperature profiles.", "hard"),
        ("What is a fouling factor?",
         "The extra thermal resistance caused by deposits on a heat-transfer surface. It reduces U and is why "
         "exchangers are specified larger than the clean calculation requires.",
         "It is why real exchangers are oversized.", "medium"),
        ("What is heat exchanger effectiveness?",
         "The actual heat transfer divided by the maximum thermodynamically possible, which would occur if one "
         "stream reached the other's inlet temperature.",
         "It is a ratio to an ideal, not an efficiency.", "medium"),
    ],
    "materials-science": [
        ("Compare BCC, FCC and HCP crystal structures.",
         "FCC is close-packed with many slip systems, so it is ductile. BCC is less densely packed and "
         "stronger but less ductile. HCP has few slip systems, so it is brittle.",
         "Slip systems decide ductility.", "hard"),
        ("What is the iron–carbon eutectoid reaction?",
         "At about 0.8% carbon and 727 °C, austenite transforms on slow cooling into pearlite, a lamellar "
         "mixture of ferrite and cementite.",
         "It is the reaction that gives steel its structure.", "hard"),
        ("What does quenching do to steel?",
         "It cools fast enough to suppress diffusion, trapping carbon and producing hard, brittle martensite — "
         "which is then tempered to recover some toughness.",
         "Fast cooling prevents equilibrium.", "medium"),
        ("What is the difference between elastic and plastic deformation?",
         "Elastic deformation is recoverable — remove the load and the shape returns. Plastic deformation is "
         "permanent, from dislocation movement.",
         "Yield is the boundary between them.", "easy"),
    ],
    "process-calculations": [
        ("State the general material balance equation.",
         "Accumulation = input − output + generation − consumption. At steady state with no reaction, it "
         "reduces to input = output.",
         "Four terms, and two usually vanish.", "medium"),
        ("What is a basis, and why must you choose one?",
         "The quantity you fix to start a calculation, such as 100 kg of feed. Every other quantity is "
         "expressed relative to it, so the arithmetic stays consistent.",
         "Without it you have ratios with no anchor.", "easy"),
        ("What is the difference between a recycle and a purge stream?",
         "Recycle returns unconverted material to the reactor. A purge removes a small bleed so that inert or "
         "accumulating components do not build up indefinitely.",
         "One saves material, one prevents accumulation.", "hard"),
        ("How do you convert between mole fraction and mass fraction?",
         "Multiply each mole fraction by its molecular weight, then divide by the sum over all components.",
         "You need the molecular weights to move between them.", "medium"),
    ],
    "engineering-chemistry": [
        ("What makes water hard, and why is that a problem?",
         "Dissolved calcium and magnesium salts. They form insulating scale in boilers and heat exchangers, "
         "and they react with soap to form scum instead of lather.",
         "Scale is an insulator where you need conduction.", "medium"),
        ("What is the difference between a primary and a secondary cell?",
         "A primary cell is used once and discarded; a secondary cell is rechargeable because its reactions "
         "are reversible.",
         "One of them can be run backwards.", "easy"),
        ("What does a catalyst do, and what does it not do?",
         "It lowers the activation energy, so the reaction reaches equilibrium faster. It does not change the "
         "equilibrium position or get consumed.",
         "It changes the path, not the destination.", "medium"),
        ("What is the octane number of a fuel?",
         "A measure of its resistance to knocking, by comparison with a reference blend of iso-octane and "
         "heptane. Higher is better for a petrol engine.",
         "It is the opposite of cetane number.", "medium"),
    ],

    # ------------------------------------------------------- first-year / other --
    "engineering-drawing": [
        ("What is the difference between first-angle and third-angle projection?",
         "In first angle the object sits between the observer and the projection plane, so views are placed "
         "opposite the direction you looked. In third angle the plane is between, so views go on the same "
         "side. India and Europe use first angle; the US uses third.",
         "It is about which side of the glass the object is on.", "hard"),
        ("What is a section view?",
         "A cutaway that exposes internal features, with the cut surfaces hatched and the material behind "
         "drawn normally.",
         "It shows what you cannot see from outside.", "easy"),
        ("What is the difference between a title block and a revision table?",
         "The title block carries the drawing's identity — number, title, scale, material, who drew and "
         "checked it. The revision table records each change, with a date and reason.",
         "One says what it is, one says what changed.", "medium"),
        ("What is an isometric projection?",
         "A pictorial in which the three axes are 120° apart and dimensions along them are drawn to a common "
         "scale, with no perspective foreshortening.",
         "No vanishing points.", "medium"),
    ],
    "engineering-graphics": [
        ("How do you choose which view is the front view?",
         "The one that shows the most features and the natural orientation in which the part is used.",
         "Most information, most natural.", "easy"),
        ("What does a hidden line represent?",
         "An edge or contour that exists but is behind a visible surface, drawn dashed.",
         "Dashed means not directly visible.", "easy"),
        ("What is a centre line for?",
         "It marks axes of symmetry and the centres of holes and arcs, drawn as a long-short-long dash.",
         "It is a construction reference, not an edge.", "easy"),
        ("What does the scale on a drawing mean?",
         "The ratio of the drawn size to the actual size, such as 1:2 for half size or 2:1 for double.",
         "Drawn first, real second.", "easy"),
    ],
    "environmental-studies": [
        ("What is the greenhouse effect?",
         "Atmospheric gases are transparent to incoming solar radiation but absorb the outgoing infrared the "
         "earth emits, then re-radiate part of it back, warming the surface.",
         "In passes through, out does not.", "medium"),
        ("What is biodiversity?",
         "The variety of life at genetic, species and ecosystem levels. It matters because diverse systems are "
         "more resilient to disturbance.",
         "Three levels, not just a species count.", "easy"),
        ("What distinguishes a renewable from a non-renewable resource?",
         "Whether it replenishes on a human timescale. Solar and wind do; coal and oil take geological time.",
         "It is about the rate of renewal, not the amount.", "easy"),
        ("What is an ecological footprint?",
         "The biologically productive area needed to supply a population's consumption and absorb its waste. "
         "Comparing it with available area shows overshoot.",
         "It converts consumption into land.", "medium"),
    ],
    "communication-skills": [
        ("What makes technical writing clear?",
         "One idea per sentence, the actor named as the subject, terms defined before use, and the conclusion "
         "stated before the reasoning.",
         "Short sentences, named actors, conclusion first.", "medium"),
        ("When is the passive voice the right choice in a report?",
         "When the actor is unknown, irrelevant, or deliberately not being assigned — the method matters more "
         "than who performed it.",
         "Not a mistake, but not the default either.", "medium"),
        ("What is an executive summary for?",
         "To give a decision-maker the finding and the recommendation first, so they can act without reading "
         "the analysis — which must still be there for those who check.",
         "Conclusion first, evidence after.", "easy"),
        ("What is the difference between hearing and listening?",
         "Hearing is the passive reception of sound; listening is the active process of interpreting and "
         "responding to it.",
         "One is physical, one is attentional.", "easy"),
    ],
    "workshop-practice": [
        ("What is a centre punch used for?",
         "To make a small dent at the intended hole position so the drill bit cannot wander when it starts.",
         "It gives the drill tip somewhere to sit.", "easy"),
        ("What is the difference between a file's cut and its shape?",
         "Cut is the coarseness and pattern of the teeth; shape is the cross-section, chosen to suit the "
         "surface being worked.",
         "One is about the teeth, one about the profile.", "medium"),
        ("What is tapping?",
         "Cutting internal threads inside a drilled hole, using a tap sized to match the intended bolt.",
         "Drill first, then cut the thread.", "easy"),
        ("What is a try square used for?",
         "Checking that two surfaces are perpendicular and marking lines at right angles to an edge.",
         "It tests squareness; it does not make it.", "easy"),
    ],
}

def build(subjects: list[dict], existing_counts: dict[str, int] | None = None,
          target: int = 3) -> list[tuple]:
    """``FLASHCARDS``-shaped rows: (subject_slug, deck, front, back, hint, difficulty).

    ``existing_counts`` maps a subject slug to the number of cards it already
    has from the hand-written deck in ``library_data.FLASHCARDS``. Cards are
    emitted only to reach ``target``, so a subject that already has a full deck
    gets nothing and a subject with a single token card gets topped up.

    Passing a plain set of "covered" slugs is not enough: twelve subjects had
    exactly one hand-written card, and skipping them left a Revision page with
    nothing worth reviewing.

    A subject that cannot reach ``target`` raises rather than shipping thin.
    The deck is named after the subject so the revision page can group cards by
    what the learner is actually revising, rather than one undifferentiated pile.
    """
    counts = existing_counts or {}
    rows: list[tuple] = []
    for subject in subjects:
        slug, name = subject["slug"], subject["name"]
        need = target - counts.get(slug, 0)
        if need <= 0:
            continue
        cards = FLASHCARDS_EXTRA.get(slug) or []
        if len(cards) < need:
            raise KeyError(
                f"subject {slug!r} needs {need} flashcards to reach {target} but only "
                f"{len(cards)} are authored"
            )
        for front, back, hint, difficulty in cards[:need]:
            rows.append((slug, name, front, back, hint, difficulty))
    return rows
