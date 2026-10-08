"""Library, roadmap, flashcard, formula, diagram and project seed content.

Every external URL here points at content that is legally and freely available
(NPTEL, MIT OpenCourseWare, freeCodeCamp, official documentation, open-access
textbooks). Nothing pirated is hosted or embedded; paid books link to the
publisher.
"""

# =============================================================================
# VIDEOS  (link out to the source; nothing is re-hosted)
# =============================================================================

VIDEOS = [
    # (title, channel, url, minutes, level, category, subject, why)
    ("MIT 6.006 - Introduction to Algorithms, Lecture 1",
     "MIT OpenCourseWare", "https://ocw.mit.edu/courses/6-006-introduction-to-algorithms-spring-2020/",
     48, "intermediate", "concept", "data-structures-algorithms",
     "The canonical university treatment. Rigorous proofs alongside intuition - the right pace for a second-year student."),
    ("NPTEL - Design and Analysis of Algorithms",
     "NPTEL", "https://archive.nptel.ac.in/courses/106/102/106102140/",
     60, "advanced", "concept", "data-structures-algorithms",
     "Indian university syllabus aligned, free to audit, and the standard reference for GATE preparation."),
    ("3Blue1Brown - Essence of Linear Algebra",
     "3Blue1Brown", "https://www.3blue1brown.com/topics/linear-algebra",
     16, "beginner", "concept", "engineering-mathematics-3",
     "Builds genuine geometric intuition for matrices, determinants and eigenvalues before any symbol pushing."),
    ("Khan Academy - Differential Calculus",
     "Khan Academy", "https://www.khanacademy.org/math/differential-calculus",
     10, "beginner", "concept", "engineering-mathematics-1",
     "Short, tightly scoped lessons with immediate practice - ideal for closing a specific gap the night before an exam."),
    ("NPTEL - Fluid Mechanics, Bernoulli's Equation",
     "NPTEL", "https://archive.nptel.ac.in/courses/112/101/112101004/",
     55, "intermediate", "concept", "fluid-mechanics",
     "Full derivation from Euler's equation with worked numerical examples in the same style as university papers."),
    ("MIT 6.004 - Computation Structures",
     "MIT OpenCourseWare", "https://ocw.mit.edu/courses/6-004-computation-structures-spring-2017/",
     50, "intermediate", "concept", "computer-architecture",
     "From transistors to a working processor, which is exactly the arc of a Computer Organisation course."),
    ("NPTEL - Database Management Systems",
     "NPTEL", "https://archive.nptel.ac.in/courses/106/106/106106146/",
     60, "intermediate", "concept", "dbms",
     "Covers normalisation and transaction theory with the formal rigour that short tutorials skip."),
    ("freeCodeCamp - Relational Databases and SQL",
     "freeCodeCamp", "https://www.freecodecamp.org/learn/relational-database/",
     300, "beginner", "concept", "dbms",
     "Hands-on and completely free; you build a real database rather than only reading about one."),
    ("NPTEL - Operating Systems",
     "NPTEL", "https://archive.nptel.ac.in/courses/106/105/106105156/",
     60, "intermediate", "concept", "operating-systems",
     "Scheduling, paging and concurrency explained from first principles with the maths worked through."),
    ("MIT 6.033 - Computer System Engineering",
     "MIT OpenCourseWare", "https://ocw.mit.edu/courses/6-033-computer-system-engineering-spring-2018/",
     80, "advanced", "concept", "operating-systems",
     "Teaches how to reason about failure and modularity in large systems - the professional skill behind the syllabus."),
    ("NPTEL - Digital Electronics and Logic Design",
     "NPTEL", "https://archive.nptel.ac.in/courses/108/103/108103013/",
     55, "beginner", "concept", "digital-electronics",
     "Karnaugh maps, minimisation and sequential circuits with plenty of worked examples."),
    ("freeCodeCamp - Responsive Web Design",
     "freeCodeCamp", "https://www.freecodecamp.org/learn/2022/responsive-web-design/",
     300, "beginner", "concept", "web-technologies",
     "Project-based and free. Build five real sites instead of passively watching."),
    ("NPTEL - Strength of Materials",
     "NPTEL", "https://archive.nptel.ac.in/courses/112/105/112105252/",
     60, "intermediate", "concept", "strength-of-materials",
     "Stress-strain behaviour, bending and torsion derived carefully - the mechanics core for civil and mechanical."),
    ("NPTEL - Thermodynamics",
     "NPTEL", "https://archive.nptel.ac.in/courses/112/106/112106083/",
     60, "intermediate", "concept", "thermodynamics",
     "Entropy and availability explained with engineering examples rather than abstract argument."),
    ("freeCodeCamp - Python for Everybody",
     "freeCodeCamp", "https://www.freecodecamp.org/learn/scientific-computing-with-python/",
     240, "beginner", "concept", "programming-fundamentals",
     "Gentle on-ramp for students whose first language is not programming."),
    ("MIT 18.06 - Linear Algebra",
     "MIT OpenCourseWare", "https://ocw.mit.edu/courses/18-06-linear-algebra-spring-2010/",
     50, "intermediate", "concept", "engineering-mathematics-3",
     "Strang's course is the standard for good reason - the four fundamental subspaces become obvious here."),
    ("NPTEL - Signals and Systems",
     "NPTEL", "https://archive.nptel.ac.in/courses/108/102/108102044/",
     60, "advanced", "concept", "signals-systems",
     "Convolution and transforms developed properly, including the intuition most tutorials skip."),
    ("NPTEL - Machine Learning",
     "NPTEL", "https://archive.nptel.ac.in/courses/106/105/106105202/",
     60, "advanced", "concept", "machine-learning",
     "Mathematical foundations first, algorithms second - the right order for building real understanding."),
]

# =============================================================================
# BOOKS  (open access or publisher link - no pirated copies)
# =============================================================================

BOOKS = [
    ("Introduction to Algorithms", "Cormen, Leiserson, Rivest & Stein", "data-structures-algorithms",
     "undergraduate", "The standard reference for algorithms and data structures, covering correctness proofs and "
     "complexity analysis in depth.",
     "Read for the proof technique, not the encyclopaedic coverage. Chapters 2-4, 6-9, 15-17 and 22 carry an "
     "undergraduate DSA course.",
     ["sorting", "graphs", "dynamic-programming", "complexity"],
     "https://mitpress.mit.edu/9780262046305/introduction-to-algorithms/", "official", "MIT Press"),

    ("Think Python: How to Think Like a Computer Scientist", "Allen B. Downey", "programming-fundamentals",
     "beginner", "A free, concise introduction to programming through Python, written for people who have never "
     "coded before.",
     "Short chapters with immediate exercises. The best first book if you are starting from zero.",
     ["python", "fundamentals", "recursion"],
     "https://greenteapress.com/wp/think-python-2e/", "open_access", "Green Tea Press"),

    ("Automate the Boring Stuff with Python", "Al Sweigart", "programming-fundamentals",
     "beginner", "Project-driven Python for practical automation: files, spreadsheets, web scraping and email.",
     "Builds confidence fast because every chapter ends with something useful you can actually run.",
     ["python", "automation", "scripting"],
     "https://automatetheboringstuff.com/", "open_access", "No Starch Press"),

    ("Database System Concepts", "Silberschatz, Korth & Sudarshan", "dbms",
     "undergraduate", "Comprehensive treatment of relational models, SQL, transactions, concurrency control and "
     "query optimisation.",
     "The transaction and concurrency chapters (14-16) are the ones interviewers probe.",
     ["sql", "transactions", "indexing", "normalisation"],
     "https://www.db-book.com/", "official", "McGraw-Hill"),

    ("Operating System Concepts", "Silberschatz, Galvin & Gagne", "operating-systems",
     "undergraduate", "The classic OS text: processes, scheduling, memory management, file systems and security.",
     "The virtual memory and deadlock chapters map almost one-to-one onto university exam questions.",
     ["scheduling", "paging", "deadlock", "file-systems"],
     "https://www.os-book.com/", "official", "Wiley"),

    ("Computer Networks: A Systems Approach", "Peterson & Davie", "computer-networks",
     "undergraduate", "An open-access networking textbook that builds the protocol stack layer by layer with real "
     "implementation concerns.",
     "Free, well written and structured around systems rather than standards documents.",
     ["tcp", "routing", "protocols"],
     "https://book.systemsapproach.org/", "open_access", "Morgan Kaufmann"),

    ("Dive into Deep Learning", "Zhang, Lipton, Li & Smola", "deep-learning",
     "advanced", "An interactive deep learning book with runnable code for every concept, available free online.",
     "Read it with the notebook open. The mathematics and the implementation sit on the same page.",
     ["neural-networks", "cnn", "rnn", "attention"],
     "https://d2l.ai/", "open_access", "Cambridge University Press"),

    ("OpenIntro Statistics", "Diez, Cetinkaya-Rundel & Barr", "probability-statistics",
     "undergraduate", "A free, well-paced statistics textbook with a strong emphasis on real data and inference.",
     "Better than most paid texts at explaining what a p-value actually means.",
     ["probability", "inference", "regression"],
     "https://www.openintro.org/book/os/", "open_access", "OpenIntro"),

    ("Engineering Mechanics: Statics", "Russell C. Hibbeler", "engineering-mechanics-fy",
     "undergraduate", "The standard statics text, valued for its large set of carefully graded problems.",
     "Work the problems; the exposition is straightforward but the problem sets are the real value.",
     ["statics", "equilibrium", "trusses", "friction"],
     "https://www.pearson.com/en-us/subject-catalog/p/engineering-mechanics-statics/P200000003376",
     "official", "Pearson"),

    ("Fundamentals of Fluid Mechanics", "Munson, Young & Okiishi", "fluid-mechanics",
     "undergraduate", "A thorough introduction to fluid statics, kinematics, Bernoulli applications and dimensional "
     "analysis.",
     "Its worked examples are close to examination style, which makes it efficient revision material.",
     ["bernoulli", "fluid-statics", "dimensional-analysis"],
     "https://www.wiley.com/en-us/Fundamentals+of+Fluid+Mechanics-p-9781119578093", "official", "Wiley"),

    ("The C Programming Language", "Kernighan & Ritchie", "programming-fundamentals",
     "intermediate", "The original and still the clearest introduction to C, written by its creators.",
     "Short enough to finish in a week and it teaches you to think about memory, which no later language can.",
     ["c", "pointers", "memory"],
     "https://www.pearson.com/en-us/subject-catalog/p/c-programming-language/P200000003478", "official", "Pearson"),

    ("Clean Code", "Robert C. Martin", "software-engineering",
     "professional", "A handbook of agile software craftsmanship focused on naming, functions and refactoring.",
     "Read the first eight chapters; the later ones are more opinionated and worth arguing with.",
     ["clean-code", "refactoring", "naming"],
     "https://www.pearson.com/en-us/subject-catalog/p/clean-code-a-handbook-of-agile-software-craftsmanship/P200000009046",
     "official", "Pearson"),
]

# =============================================================================
# RESOURCES
# =============================================================================

RESOURCES = [
    ("Python Official Documentation", "https://docs.python.org/3/", "documentation", "documentation",
     "programming-fundamentals", "beginner", "The authoritative reference. Learn the tutorial section first, then "
     "keep the library reference bookmarked."),
    ("MDN Web Docs", "https://developer.mozilla.org/", "documentation", "documentation",
     "web-technologies", "beginner", "The definitive reference for HTML, CSS and JavaScript, maintained by the "
     "browser vendors themselves."),
    ("PostgreSQL Documentation", "https://www.postgresql.org/docs/", "documentation", "documentation",
     "dbms", "intermediate", "The SQL standard behaviour, indexing strategies and query planner internals."),
    ("NPTEL Course Catalogue", "https://nptel.ac.in/courses", "course", "course", None,
     "beginner", "Free, credit-eligible university courses across every Indian engineering discipline."),
    ("MIT OpenCourseWare", "https://ocw.mit.edu/", "course", "course", None,
     "intermediate", "Complete MIT course materials, free, including lecture notes, assignments and exams."),
    ("freeCodeCamp Curriculum", "https://www.freecodecamp.org/learn", "course", "course",
     "programming-fundamentals", "beginner", "Structured, project-based, free, with certifications on completion."),
    ("GeeksforGeeks - Engineering Notes", "https://www.geeksforgeeks.org/", "documentation", "documentation",
     "data-structures-algorithms", "beginner", "Quick lookup for algorithm summaries and interview questions. "
     "Verify anything you will be examined on against a textbook."),
    ("Desmos Graphing Calculator", "https://www.desmos.com/calculator", "tool", "simulator",
     "engineering-mathematics-1", "beginner", "Plot functions and see the effect of every parameter instantly."),
    ("Falstad Circuit Simulator", "https://www.falstad.com/circuit/", "tool", "simulator",
     "basic-electrical", "beginner", "Run circuits in the browser and watch current flow. Excellent for building "
     "intuition before solving network theorems by hand."),
    ("Wolfram Alpha", "https://www.wolframalpha.com/", "tool", "tool", "engineering-mathematics-1", "beginner",
     "Step-by-step calculus, algebra and differential equations. Use it to check work, never to replace the "
     "working."),
    ("Khan Academy", "https://www.khanacademy.org/", "course", "course", None, "beginner",
     "Free lessons across mathematics, physics and chemistry with mastery tracking."),
    ("LeetCode Problem Patterns", "https://leetcode.com/problemset/", "tool", "tool",
     "data-structures-algorithms", "intermediate", "The industry-standard interview practice set. EngineVerse "
     "covers the same patterns offline with full editorials."),
    ("GATE Previous Year Papers", "https://gate.iitm.ac.in/", "documentation", "exam", None, "advanced",
     "Official information and archives for the Graduate Aptitude Test in Engineering."),
    ("OASYS / FreeCAD", "https://www.freecad.org/", "tool", "tool", "cad-cam", "intermediate",
     "Open-source parametric CAD. A legitimate way to build a portfolio project without a paid licence."),
    ("Arduino Project Hub", "https://projecthub.arduino.cc/", "dataset", "project", None, "beginner",
     "Documented hardware builds with schematics and code you can reproduce on inexpensive parts."),
]

# =============================================================================
# FORMULAS  (formula centre)
# =============================================================================

FORMULAS = [
    # (slug, subject, category, name, latex, variables, meaning, application, example, constraints)
    ("bernoulli", "fluid-mechanics", "Fluid Mechanics", "Bernoulli's Equation",
     "p + \\frac{1}{2}\\rho v^{2} + \\rho g h = \\text{constant}",
     [("p", "static pressure", "Pa"), ("\\rho", "density", "kg/m^3"), ("v", "velocity", "m/s"),
      ("g", "gravity", "m/s^2"), ("h", "elevation", "m")],
     "Mechanical energy per unit volume is conserved along a streamline.",
     "Venturi meters, aerofoils, pump and pipe design, Pitot tubes.",
     "p_1 + \\tfrac{1}{2}\\rho v_1^2 = p_2 + \\tfrac{1}{2}\\rho v_2^2",
     "Steady, incompressible, inviscid, along one streamline."),

    ("reynolds-number", "fluid-mechanics", "Fluid Mechanics", "Reynolds Number",
     "Re = \\frac{\\rho v D}{\\mu}",
     [("D", "characteristic length", "m"), ("\\mu", "dynamic viscosity", "Pa.s")],
     "The ratio of inertial forces to viscous forces in a flow.",
     "Predicting laminar, transitional or turbulent flow.",
     "Re < 2300 \\Rightarrow \\text{laminar in a pipe}",
     "Newtonian fluid, well-defined characteristic length."),

    ("ohms-law", "basic-electrical", "Electrical", "Ohm's Law",
     "V = I R",
     [("V", "potential difference", "V"), ("I", "current", "A"), ("R", "resistance", "\\Omega")],
     "Current through a conductor is proportional to the applied voltage.",
     "Every resistive circuit analysis, from a sensor divider to a power feed.",
     "I = \\frac{12}{4} = 3\\ \\text{A}",
     "Ohmic materials only; semiconductors and lamps are non-linear."),

    ("ac-power-triangle", "basic-electrical", "Electrical", "AC Power Triangle",
     "S = \\sqrt{P^{2} + Q^{2}}, \\qquad \\text{pf} = \\frac{P}{S}",
     [("P", "real power", "W"), ("Q", "reactive power", "VAR"), ("S", "apparent power", "VA")],
     "Apparent power is the vector sum of real and reactive power.",
     "Power factor correction, generator and cable sizing.",
     "\\text{pf} = \\cos\\phi", "Sinusoidal steady state."),

    ("transformer-emf", "electrical-machines-1", "Electrical", "Transformer EMF Equation",
     "E = 4.44\\, f N \\phi_{max}",
     [("f", "frequency", "Hz"), ("N", "turns", "-"), ("\\phi_{max}", "peak flux", "Wb")],
     "The RMS voltage induced in a winding by a sinusoidally varying flux.",
     "Transformer design and rating verification.",
     "E = 4.44 \\times 50 \\times 500 \\times 0.01 = 1110\\ \\text{V}",
     "Sinusoidal excitation, negligible leakage reactance."),

    ("carnot-efficiency", "thermodynamics", "Thermodynamics", "Carnot Efficiency",
     "\\eta = 1 - \\frac{T_L}{T_H}",
     [("T_H", "source temperature", "K"), ("T_L", "sink temperature", "K")],
     "The maximum efficiency achievable by any heat engine between two reservoirs.",
     "Setting the theoretical ceiling for power plants and engines.",
     "\\eta = 1 - \\frac{300}{800} = 0.625",
     "Reversible cycle; temperatures must be absolute."),

    ("hookes-law", "strength-of-materials", "Mechanics of Solids", "Hooke's Law and Axial Deformation",
     "\\sigma = E\\epsilon, \\qquad \\delta = \\frac{PL}{AE}",
     [("\\sigma", "normal stress", "Pa"), ("E", "Young's modulus", "Pa"), ("\\epsilon", "strain", "-"),
      ("P", "axial load", "N"), ("A", "area", "m^2")],
     "Stress is proportional to strain within the elastic limit.",
     "Deflection checks on bars, bolts, columns and machine frames.",
     "\\delta = \\frac{50000 \\times 2}{3.14 \\times 10^{-4} \\times 200 \\times 10^9} = 1.59\\ \\text{mm}",
     "Linear elastic material, axial load, uniform section."),

    ("bending-stress", "strength-of-materials", "Mechanics of Solids", "Bending Stress",
     "\\frac{M}{I} = \\frac{\\sigma}{y} = \\frac{E}{R}",
     [("M", "bending moment", "N.m"), ("I", "second moment of area", "m^4"), ("y", "distance from neutral axis", "m"),
      ("R", "radius of curvature", "m")],
     "The flexure formula relating moment, geometry and stress in a beam.",
     "Beam design for buildings, bridges and machine frames.",
     "\\sigma_{max} = \\frac{M c}{I}", "Pure bending, plane sections remain plane."),

    ("newtons-second", "engineering-physics", "Physics", "Newton's Second Law",
     "\\mathbf{F} = m\\mathbf{a}",
     [("F", "net force", "N"), ("m", "mass", "kg"), ("a", "acceleration", "m/s^2")],
     "Net force equals the rate of change of momentum.",
     "Dynamics of every mechanical system.",
     "a = \\frac{20}{5} = 4\\ \\text{m/s}^2", "Inertial reference frame, constant mass."),

    ("quadratic-formula", "engineering-mathematics-1", "Mathematics", "Quadratic Formula",
     "x = \\frac{-b \\pm \\sqrt{b^{2} - 4ac}}{2a}",
     [("a", "leading coefficient", "-"), ("b", "linear coefficient", "-"), ("c", "constant term", "-")],
     "The roots of any quadratic equation.",
     "Control system poles, circuit transients, projectile motion.",
     "x = \\frac{-3 \\pm \\sqrt{9 + 16}}{2} = 2,\\ -2.5", "a must be non-zero."),

    ("euler-formula", "engineering-mathematics-3", "Mathematics", "Euler's Formula",
     "e^{i\\theta} = \\cos\\theta + i\\sin\\theta",
     [("\\theta", "angle", "rad")],
     "The bridge between the exponential and trigonometric functions in the complex plane.",
     "Phasor analysis, signal processing, AC circuit solution.",
     "e^{i\\pi} + 1 = 0", "Complex exponential definition."),

    ("fourier-transform", "signals-systems", "Mathematics", "Fourier Transform",
     "X(\\omega) = \\int_{-\\infty}^{\\infty} x(t)\\,e^{-j\\omega t}\\,dt",
     [("\\omega", "angular frequency", "rad/s")],
     "Decomposes a signal into its frequency components.",
     "Filter design, spectral analysis, communications, image processing.",
     "\\mathcal{F}\\{e^{-at}u(t)\\} = \\frac{1}{a + j\\omega}",
     "Absolutely integrable signal for the transform to exist."),

    ("bayes-theorem", "probability-statistics", "Mathematics", "Bayes' Theorem",
     "P(A \\mid B) = \\frac{P(B \\mid A)\\,P(A)}{P(B)}",
     [("P(A)", "prior probability", "-"), ("P(B \\mid A)", "likelihood", "-")],
     "How to update a belief when new evidence arrives.",
     "Medical testing, spam filtering, sensor fusion, machine learning.",
     "P(A \\mid B) = \\frac{0.99 \\times 0.01}{0.99 \\times 0.01 + 0.05 \\times 0.99} = 0.167",
     "P(B) must be non-zero."),

    ("darcy-weisbach", "fluid-mechanics", "Fluid Mechanics", "Darcy-Weisbach Equation",
     "h_f = f \\frac{L}{D} \\frac{v^{2}}{2g}",
     [("f", "friction factor", "-"), ("L", "pipe length", "m"), ("D", "pipe diameter", "m")],
     "Head loss due to friction in a pipe.",
     "Pumping power calculation and pipeline sizing.",
     "h_f = 0.02 \\times \\frac{100}{0.1} \\times \\frac{2^2}{2 \\times 9.81} = 4.08\\ \\text{m}",
     "Fully developed flow; f from the Moody chart."),

    ("big-o-sum", "data-structures-algorithms", "Computer Science", "Common Complexity Series",
     "\\sum_{i=1}^{n} i = \\frac{n(n+1)}{2} = O(n^{2}), \\qquad \\sum_{i=0}^{\\log n} 2^{i} = O(n)",
     [("n", "input size", "-")],
     "Arithmetic series give quadratic loops; geometric doubling gives linear totals.",
     "Analysing nested loops, dynamic arrays and amortised costs.",
     "1 + 2 + 4 + \\dots + n < 2n", "-"),
]

# =============================================================================
# ROADMAPS
# =============================================================================

ROADMAPS = [
    {
        "slug": "cse-placement-roadmap",
        "title": "CSE Placement Roadmap (6 months)",
        "kind": "career",
        "branch": "cse",
        "target_role": "Software Engineer",
        "summary": "From first-year fundamentals to a serviceable interview candidate in two semesters of focused work.",
        "description": (
            "This path assumes 8-10 focused hours per week. The order matters: data structures first because every "
            "later topic reuses them, then the three subjects interviewers actually test - operating systems, "
            "databases and networks - and finally projects and mock interviews. Do not skip the practice problems; "
            "reading about an algorithm and implementing it are different skills."
        ),
        "nodes": [
            ("Arrays and Strings", "Contiguous memory, indexing and the two-pointer technique.", "topic", "arrays", True),
            ("Linked Lists", "Pointer manipulation and the fast/slow pattern.", "topic", "linked-lists", True),
            ("Stacks and Queues", "LIFO/FIFO structures and their classic applications.", "topic", "stacks-queues", True),
            ("Trees and Binary Search Trees", "Recursive structure and balanced variants.", "topic", "trees-bst", True),
            ("Hash Tables", "Constant-time lookup and collision handling.", "topic", "hash-tables", True),
            ("Graph Traversal", "BFS, DFS and the standard graph patterns.", "topic", "graphs", True),
            ("Dynamic Programming", "Overlapping subproblems and table construction.", "topic", "dynamic-programming", True),
            ("Two Sum", "The canonical hash-map problem.", "coding", "two-sum", True),
            ("Valid Parentheses", "Stack applications.", "coding", "valid-parentheses", True),
            ("Maximum Subarray", "Kadane's algorithm.", "coding", "maximum-subarray", True),
            ("Longest Substring Without Repeats", "Sliding window.", "coding", "longest-substring", True),
            ("LRU Cache", "Design question combining two structures.", "coding", "lru-cache", False),
            ("Process Management", "Scheduling, context switching and concurrency.", "topic", "process-management", True),
            ("Deadlocks", "The four conditions and how to break them.", "topic", "deadlocks", True),
            ("Virtual Memory and Paging", "The mechanism behind modern multitasking.", "topic", "virtual-memory-paging", True),
            ("Normalisation", "Removing update anomalies.", "topic", "normalisation", True),
            ("Transactions and ACID", "Isolation levels and recovery.", "topic", "transactions-acid", True),
            ("Indexing", "B+ trees and query planning.", "topic", "indexing", True),
            ("TCP/IP Model", "Layering and encapsulation.", "topic", "tcp-ip-model", True),
            ("IP Addressing and Subnetting", "The arithmetic behind networks.", "topic", "ip-addressing-subnetting", True),
            ("Object Oriented Design", "Encapsulation, inheritance, polymorphism.", "topic", "oop-pillars", True),
            ("Build a Full Stack Project", "Apply everything end to end.", "project", "student-performance-dashboard", True),
            ("System Design Basics", "Scaling, caching and load balancing.", "topic", "design-patterns-intro", False),
        ],
    },
    {
        "slug": "first-year-foundation",
        "title": "First Year Engineering Foundation",
        "kind": "subject",
        "branch": None,
        "target_role": None,
        "summary": "The common first-year core, sequenced so each subject supports the next.",
        "description": (
            "Mathematics, physics, chemistry, mechanics, basic electrical and programming form the shared first "
            "year across almost every Indian university. This order front-loads the mathematics because calculus "
            "and linear algebra are prerequisites for nearly everything in semester three onward."
        ),
        "nodes": [
            ("Limits and Continuity", "The foundation of all calculus.", "subject", "engineering-mathematics-1", True),
            ("Matrices and Linear Algebra", "Systems of equations and vector spaces.", "subject", "engineering-mathematics-3", True),
            ("Engineering Physics", "Quantum, optics and semiconductors.", "subject", "engineering-physics", True),
            ("Engineering Chemistry", "Electrochemistry, polymers and water treatment.", "subject", "engineering-chemistry", True),
            ("Free Body Diagrams", "The core statics skill.", "topic", "equilibrium-of-forces-free-body-diagrams", True),
            ("Ohm's Law and DC Circuits", "Your first circuit analysis.", "topic", "kirchhoffs-laws", True),
            ("Programming Fundamentals", "Variables, control flow and functions.", "subject", "programming-fundamentals", True),
            ("FizzBuzz", "Your first coding problem.", "coding", "fizzbuzz", True),
            ("Engineering Graphics", "Projection and orthographic views.", "subject", "engineering-graphics", False),
            ("Communication Skills", "Technical writing and presentation.", "subject", "communication-skills", False),
        ],
    },
    {
        "slug": "machine-learning-path",
        "title": "Machine Learning Engineer Path",
        "kind": "career",
        "branch": "cse",
        "target_role": "Machine Learning Engineer",
        "summary": "Mathematics, classical machine learning, deep learning and deployment.",
        "description": (
            "Machine learning interviews test three things: whether you can derive the mathematics, whether you "
            "understand why a model fails, and whether you can put it into production. This path covers all three "
            "and ends with a deployed project."
        ),
        "nodes": [
            ("Linear Algebra", "Vectors, matrices and eigen-decomposition.", "subject", "engineering-mathematics-3", True),
            ("Probability and Statistics", "Distributions, inference and Bayes.", "subject", "probability-statistics", True),
            ("Python for Data Work", "NumPy, pandas and visualisation.", "subject", "data-science-foundations", True),
            ("Supervised Learning", "Regression, classification and evaluation.", "subject", "machine-learning", True),
            ("Neural Networks", "Forward and backward propagation.", "subject", "deep-learning", True),
            ("Convolutional Networks", "Image architecture fundamentals.", "topic", "convolutional-neural-networks", True),
            ("Transformers and Attention", "The architecture behind modern language models.", "topic", "transformers-attention", False),
            ("Model Deployment", "Serving, monitoring and drift.", "subject", "cloud-computing-subject", False),
        ],
    },
    {
        "slug": "gate-mechanical-path",
        "title": "GATE Mechanical Engineering Path",
        "kind": "career",
        "branch": "mechanical",
        "target_role": "GATE Aspirant / PSU Engineer",
        "summary": "The four pillars of the mechanical GATE syllabus in dependency order.",
        "description": (
            "Thermodynamics and fluid mechanics carry the largest weight, followed by strength of materials and "
            "theory of machines. Engineering mathematics underpins all of them and should be practised in parallel, "
            "not sequentially."
        ),
        "nodes": [
            ("Engineering Mathematics", "Calculus, linear algebra and probability.", "subject", "engineering-mathematics-2", True),
            ("Thermodynamics", "Laws, cycles and entropy.", "subject", "thermodynamics", True),
            ("Fluid Mechanics", "Statics, Bernoulli and boundary layers.", "subject", "fluid-mechanics", True),
            ("Strength of Materials", "Stress, strain and failure theories.", "subject", "strength-of-materials", True),
            ("Heat Transfer", "Conduction, convection and radiation.", "subject", "heat-transfer", True),
            ("Theory of Machines", "Kinematics and dynamics of mechanisms.", "subject", "theory-of-machines", True),
            ("Manufacturing", "Machining, casting and welding.", "subject", "manufacturing-processes", False),
        ],
    },
    {
        "slug": "python-language-path",
        "title": "Learn Python From Zero",
        "kind": "language",
        "branch": None,
        "target_role": None,
        "summary": "Eleven modules from variables to testing, each with runnable examples.",
        "description": "Work through the modules in order. Every module has an exercise - do not move on until yours runs.",
        "nodes": [
            ("Variables and Types", "Values, names and built-in types.", "resource", "python-variables", True),
            ("Control Flow", "Conditionals and loops.", "resource", "python-control-flow", True),
            ("Functions", "Parameters, scope and returns.", "resource", "python-functions", True),
            ("Collections", "Lists, tuples, sets and dictionaries.", "resource", "python-collections", True),
            ("Strings and Files", "Text processing and persistence.", "resource", "python-strings-files", True),
            ("Object Oriented Python", "Classes, inheritance and dunder methods.", "resource", "python-oop", True),
            ("Error Handling", "Exceptions and defensive programming.", "resource", "python-errors", True),
            ("Modules and Packages", "Organising larger programs.", "resource", "python-modules", True),
            ("Testing", "pytest and test-driven development.", "resource", "python-testing", False),
        ],
    },
]

# =============================================================================
# FLASHCARDS
# =============================================================================

FLASHCARDS = [
    # (subject, deck, front, back, hint, difficulty)
    ("data-structures-algorithms", "Complexity", "Worst-case time complexity of binary search?", "O(log n) - the search space halves every comparison.", "Each step discards half.", "easy"),
    ("data-structures-algorithms", "Complexity", "Amortised cost of appending to a dynamic array?", "O(1). Copies form a geometric series totalling under 2n for n appends.", "1 + 2 + 4 + ...", "medium"),
    ("data-structures-algorithms", "Structures", "Which structure gives FIFO ordering?", "A queue. Enqueue at the rear, dequeue from the front.", "First in, first out.", "easy"),
    ("data-structures-algorithms", "Structures", "Why is a B+ tree preferred over a binary tree for disk indexes?", "A high fan-out keeps the tree shallow, so a lookup costs only 3-4 disk reads, and the linked leaves support range scans.", "Disk reads dominate.", "hard"),
    ("data-structures-algorithms", "Graphs", "Complexity of BFS with an adjacency list?", "O(V + E). Each vertex is enqueued once and each edge examined once.", "Visit each edge once.", "medium"),
    ("operating-systems", "Core", "What is a context switch?", "Saving one process's state and restoring another's: registers, program counter, stack pointer and page tables.", "Thousands of cycles.", "medium"),
    ("operating-systems", "Core", "Name the four Coffman conditions for deadlock.", "Mutual exclusion, hold and wait, no preemption, circular wait.", "All four must hold simultaneously.", "easy"),
    ("operating-systems", "Memory", "What causes thrashing?", "Too many processes competing for too few page frames, so the CPU spends its time servicing page faults.", "Degree of multiprogramming.", "medium"),
    ("dbms", "Core", "What does the D in ACID stand for?", "Durability - committed changes survive a crash, enforced by write-ahead logging.", "Write-ahead log.", "easy"),
    ("dbms", "Core", "Which isolation level prevents phantom reads?", "Serializable. Repeatable read locks read rows but not the gaps between them.", "Predicate locking.", "hard"),
    ("dbms", "Design", "What does 3NF remove?", "Transitive dependencies of non-prime attributes on the key.", "A -> B -> C.", "medium"),
    ("computer-networks", "Core", "Minimum sampling rate for a 4 kHz signal?", "8 kHz - the Nyquist rate, twice the highest frequency component.", "Nyquist-Shannon.", "easy"),
    ("computer-networks", "Core", "Why is UDP preferred for live voice?", "Retransmitted packets arrive after their playout deadline and are useless, so reliability machinery only adds latency.", "Delay-bounded.", "medium"),
    ("computer-networks", "Addressing", "How many usable hosts in a /28?", "14. Sixteen addresses minus network and broadcast.", "2^4 - 2.", "easy"),
    ("fluid-mechanics", "Core", "State Bernoulli's equation.", "p + (1/2)rho*v^2 + rho*g*h = constant along a streamline for steady, incompressible, inviscid flow.", "Energy per unit volume.", "medium"),
    ("fluid-mechanics", "Core", "Four assumptions behind Bernoulli's equation?", "Steady, incompressible, inviscid, along a single streamline.", "No friction, no work.", "medium"),
    ("thermodynamics", "Core", "Carnot efficiency formula?", "eta = 1 - T_L / T_H, with both temperatures in kelvin.", "Absolute temperatures only.", "easy"),
    ("thermodynamics", "Core", "What does the second law say about entropy in an isolated system?", "It never decreases; it is constant only for reversible processes.", "Arrow of time.", "medium"),
    ("strength-of-materials", "Core", "Hooke's law?", "sigma = E * epsilon within the elastic limit.", "Linear region.", "easy"),
    ("strength-of-materials", "Core", "Effect of doubling beam depth on section modulus?", "Quadruples it, because Z = b*d^2/6.", "Proportional to d squared.", "medium"),
    ("digital-electronics", "Core", "Which gates are functionally complete on their own?", "NAND and NOR - each can build AND, OR and NOT.", "Universal gates.", "easy"),
    ("digital-electronics", "Core", "Why do Karnaugh maps use Gray code?", "So adjacent cells differ in exactly one variable, letting that variable cancel when grouped.", "One variable changes.", "medium"),
    ("circuit-theory", "Core", "Kirchhoff's Current Law expresses conservation of what?", "Charge. Current entering a node equals current leaving it.", "Charge cannot accumulate.", "easy"),
    ("basic-electrical", "Core", "Why are transformers rated in kVA?", "Heating depends on voltage and current, not on the load's power factor, which the manufacturer cannot know.", "Apparent power.", "medium"),
    ("programming-fundamentals", "Core", "What happens to a recursion with no reachable base case?", "Stack overflow - frames accumulate until the limit is hit.", "Each call needs a frame.", "easy"),
    ("engineering-mathematics-1", "Core", "Limit of sin(3x)/x as x approaches 0?", "3. Factor out the 3 and use the standard sin(u)/u limit.", "sin(u)/u tends to 1.", "medium"),
    ("engineering-mathematics-2", "Core", "Laplace transform of t^2?", "2/s^3. In general L{t^n} = n!/s^(n+1).", "n factorial over s to the n+1.", "medium"),
    ("probability-statistics", "Core", "State Bayes' theorem.", "P(A|B) = P(B|A) P(A) / P(B).", "Posterior from prior and likelihood.", "medium"),
    ("machine-learning", "Core", "What is overfitting and how do you detect it?", "The model memorises noise, so training error stays low while validation error rises. Detect it with a held-out set or cross-validation.", "Train versus validation gap.", "medium"),
    ("machine-learning", "Core", "When do you prefer precision over recall?", "When false positives are costly, such as flagging a transaction as fraud or a tumour as malignant for invasive follow-up.", "Cost of a false alarm.", "hard"),
    ("software-engineering", "Core", "What does the Single Responsibility Principle state?", "A module should have one, and only one, reason to change.", "One axis of change.", "medium"),
    ("process-calculations", "Core", "What is a tie component?", "A species that passes through the process unchanged, so its mass links two streams directly.", "Dry solids in a dryer.", "medium"),
    ("soil-mechanics", "Core", "Effective stress formula?", "sigma' = sigma - u: total stress minus pore water pressure.", "Grains carry the load.", "easy"),
    ("engineering-physics", "Core", "Why does light intensity below threshold frequency eject no electrons?", "Emission depends on photon energy h*nu exceeding the work function; intensity only raises the photon count.", "One photon, one electron.", "medium"),
]

# =============================================================================
# DIAGRAMS (declarative SVG built by the frontend renderer)
# =============================================================================

DIAGRAMS = {
    "bernoulli": {
        "title": "Bernoulli's principle in a Venturi tube",
        "caption": "As the pipe narrows, velocity rises and static pressure falls. The manometer columns show the "
                   "pressure difference directly.",
        "kind": "svg",
        "spec": (
            '<svg viewBox="0 0 640 260" xmlns="http://www.w3.org/2000/svg" role="img" '
            'aria-label="Venturi tube showing velocity and pressure change">'
            '<defs><marker id="ar" markerWidth="10" markerHeight="10" refX="8" refY="3" orient="auto">'
            '<path d="M0,0 L0,6 L9,3 z" fill="#4f7cff"/></marker></defs>'
            '<path d="M40,80 L200,80 L260,110 L380,110 L440,80 L600,80 L600,180 L440,180 L380,150 L260,150 '
            'L200,180 L40,180 Z" fill="#1b2440" stroke="#4f7cff" stroke-width="2"/>'
            '<rect x="150" y="20" width="14" height="60" fill="#2b3b66" stroke="#4f7cff"/>'
            '<rect x="152" y="44" width="10" height="36" fill="#38bdf8"/>'
            '<rect x="310" y="20" width="14" height="60" fill="#2b3b66" stroke="#4f7cff"/>'
            '<rect x="312" y="26" width="10" height="54" fill="#38bdf8"/>'
            '<rect x="470" y="20" width="14" height="60" fill="#2b3b66" stroke="#4f7cff"/>'
            '<rect x="472" y="44" width="10" height="36" fill="#38bdf8"/>'
            '<line x1="60" y1="130" x2="140" y2="130" stroke="#4f7cff" stroke-width="3" marker-end="url(#ar)"/>'
            '<line x1="270" y1="130" x2="370" y2="130" stroke="#4f7cff" stroke-width="3" marker-end="url(#ar)"/>'
            '<line x1="480" y1="130" x2="590" y2="130" stroke="#4f7cff" stroke-width="3" marker-end="url(#ar)"/>'
            '<text x="70" y="212" fill="#9fb0d0" font-size="14">v low, p high</text>'
            '<text x="280" y="212" fill="#9fb0d0" font-size="14">v high, p low</text>'
            '<text x="480" y="212" fill="#9fb0d0" font-size="14">v low, p high</text>'
            '<text x="250" y="245" fill="#6f80a4" font-size="13">Continuity: A1 v1 = A2 v2</text>'
            "</svg>"
        ),
        "hotspots": [
            {"x": 260, "y": 100, "w": 130, "h": 60, "label": "Throat",
             "explain": "Smallest area, so by continuity the velocity is highest here. Bernoulli then forces the "
                        "static pressure to its minimum - this is the region a carburettor uses to draw in fuel."},
            {"x": 140, "y": 70, "w": 40, "h": 60, "label": "Inlet manometer",
             "explain": "The higher liquid column marks the higher static pressure upstream."},
        ],
    },
    "stress-strain": {
        "title": "Stress-strain curve for mild steel",
        "caption": "Proportional limit, elastic limit, yield plateau, strain hardening, necking and fracture.",
        "kind": "svg",
        "spec": (
            '<svg viewBox="0 0 640 320" xmlns="http://www.w3.org/2000/svg" role="img" '
            'aria-label="Stress strain curve for mild steel">'
            '<line x1="60" y1="270" x2="600" y2="270" stroke="#6f80a4" stroke-width="2"/>'
            '<line x1="60" y1="270" x2="60" y2="30" stroke="#6f80a4" stroke-width="2"/>'
            '<text x="300" y="300" fill="#9fb0d0" font-size="14">Strain</text>'
            '<text x="18" y="150" fill="#9fb0d0" font-size="14" transform="rotate(-90 30 150)">Stress</text>'
            '<polyline points="60,270 170,150 200,140 300,146 330,120 430,70 470,60 520,110 560,180" '
            'fill="none" stroke="#4f7cff" stroke-width="3"/>'
            '<circle cx="170" cy="150" r="5" fill="#38bdf8"/><text x="178" y="146" fill="#9fb0d0" font-size="12">'
            'Proportional limit</text>'
            '<circle cx="200" cy="140" r="5" fill="#38bdf8"/><text x="208" y="132" fill="#9fb0d0" font-size="12">'
            'Elastic limit</text>'
            '<circle cx="300" cy="146" r="5" fill="#38bdf8"/><text x="240" y="176" fill="#9fb0d0" font-size="12">'
            'Yield plateau</text>'
            '<circle cx="470" cy="60" r="5" fill="#f59e0b"/><text x="410" y="46" fill="#f59e0b" font-size="12">'
            'Ultimate strength</text>'
            '<circle cx="560" cy="180" r="5" fill="#ef4444"/><text x="470" y="200" fill="#ef4444" font-size="12">'
            'Fracture (necking)</text>'
            "</svg>"
        ),
        "hotspots": [
            {"x": 60, "y": 140, "w": 140, "h": 130, "label": "Elastic region",
             "explain": "Unload here and the material returns to its original length. Hooke's law holds up to the "
                        "proportional limit; between the proportional and elastic limits the material is still "
                        "elastic but no longer linear."},
            {"x": 400, "y": 40, "w": 180, "h": 100, "label": "Necking",
             "explain": "After the ultimate point the cross-section locally reduces, so engineering stress falls "
                        "even though true stress keeps rising."},
        ],
    },
    "kirchhoff": {
        "title": "Kirchhoff's Current Law at a node",
        "caption": "Charge cannot accumulate at a junction, so the currents entering equal the currents leaving.",
        "kind": "svg",
        "spec": (
            '<svg viewBox="0 0 480 240" xmlns="http://www.w3.org/2000/svg" role="img" '
            'aria-label="Currents entering and leaving a node">'
            '<defs><marker id="ar2" markerWidth="10" markerHeight="10" refX="8" refY="3" orient="auto">'
            '<path d="M0,0 L0,6 L9,3 z" fill="#38bdf8"/></marker></defs>'
            '<circle cx="240" cy="120" r="9" fill="#4f7cff"/>'
            '<line x1="60" y1="80" x2="232" y2="116" stroke="#38bdf8" stroke-width="3" marker-end="url(#ar2)"/>'
            '<line x1="60" y1="160" x2="232" y2="124" stroke="#38bdf8" stroke-width="3" marker-end="url(#ar2)"/>'
            '<line x1="248" y1="120" x2="420" y2="120" stroke="#38bdf8" stroke-width="3" marker-end="url(#ar2)"/>'
            '<text x="90" y="70" fill="#9fb0d0" font-size="14">I1 = 2 A</text>'
            '<text x="90" y="182" fill="#9fb0d0" font-size="14">I2 = 4 A</text>'
            '<text x="330" y="110" fill="#9fb0d0" font-size="14">I3 = 6 A</text>'
            '<text x="140" y="222" fill="#6f80a4" font-size="13">I1 + I2 = I3</text>'
            "</svg>"
        ),
        "hotspots": [
            {"x": 210, "y": 90, "w": 60, "h": 60, "label": "Node",
             "explain": "Sum of currents entering equals sum leaving. This is conservation of charge, and it holds "
                        "for any closed surface, not just a point."},
        ],
    },
    "carnot-cycle": {
        "title": "Carnot cycle on a pressure-volume diagram",
        "caption": "Two isothermals and two adiabatics enclose the maximum work obtainable between two temperatures.",
        "kind": "svg",
        "spec": (
            '<svg viewBox="0 0 520 340" xmlns="http://www.w3.org/2000/svg" role="img" '
            'aria-label="Carnot cycle on a PV diagram">'
            '<line x1="60" y1="290" x2="480" y2="290" stroke="#6f80a4" stroke-width="2"/>'
            '<line x1="60" y1="290" x2="60" y2="30" stroke="#6f80a4" stroke-width="2"/>'
            '<text x="250" y="320" fill="#9fb0d0" font-size="14">Volume V</text>'
            '<text x="20" y="160" fill="#9fb0d0" font-size="14" transform="rotate(-90 32 160)">Pressure P</text>'
            '<path d="M150,90 Q250,120 330,150 Q300,210 260,250 Q170,210 150,90 Z" '
            'fill="rgba(79,124,255,0.15)" stroke="#4f7cff" stroke-width="2.5"/>'
            '<text x="180" y="80" fill="#f59e0b" font-size="13">Isothermal at T_H</text>'
            '<text x="300" y="270" fill="#38bdf8" font-size="13">Isothermal at T_L</text>'
            '<text x="330" y="180" fill="#9fb0d0" font-size="13">Adiabatic</text>'
            '<text x="170" y="180" fill="#9fb0d0" font-size="13">Enclosed area = net work</text>'
            "</svg>"
        ),
        "hotspots": [
            {"x": 150, "y": 90, "w": 200, "h": 180, "label": "Cycle area",
             "explain": "The area enclosed on a P-V diagram is the net work per cycle. The Carnot cycle encloses "
                        "the most work for the given temperature limits, which is why its efficiency is the "
                        "theoretical ceiling."},
        ],
    },
    "kmap": {
        "title": "Three variable Karnaugh map",
        "caption": "Gray-code ordering makes adjacent cells differ in exactly one variable.",
        "kind": "svg",
        "spec": (
            '<svg viewBox="0 0 460 260" xmlns="http://www.w3.org/2000/svg" role="img" '
            'aria-label="Three variable Karnaugh map">'
            '<text x="30" y="90" fill="#9fb0d0" font-size="15">A</text>'
            '<text x="150" y="40" fill="#9fb0d0" font-size="15">BC</text>'
            '<text x="120" y="66" fill="#6f80a4" font-size="12">00</text>'
            '<text x="190" y="66" fill="#6f80a4" font-size="12">01</text>'
            '<text x="260" y="66" fill="#6f80a4" font-size="12">11</text>'
            '<text x="330" y="66" fill="#6f80a4" font-size="12">10</text>'
            '<text x="60" y="110" fill="#6f80a4" font-size="12">0</text>'
            '<text x="60" y="180" fill="#6f80a4" font-size="12">1</text>'
            '<g stroke="#4f7cff" stroke-width="1.5" fill="none">'
            '<rect x="100" y="80" width="70" height="60"/><rect x="170" y="80" width="70" height="60"/>'
            '<rect x="240" y="80" width="70" height="60"/><rect x="310" y="80" width="70" height="60"/>'
            '<rect x="100" y="140" width="70" height="60"/><rect x="170" y="140" width="70" height="60"/>'
            '<rect x="240" y="140" width="70" height="60"/><rect x="310" y="140" width="70" height="60"/></g>'
            '<text x="130" y="116" fill="#38bdf8" font-size="16">1</text>'
            '<text x="270" y="116" fill="#38bdf8" font-size="16">1</text>'
            '<text x="200" y="176" fill="#38bdf8" font-size="16">1</text>'
            '<text x="340" y="176" fill="#38bdf8" font-size="16">1</text>'
            '<rect x="96" y="76" width="148" height="68" rx="10" fill="none" stroke="#f59e0b" stroke-width="2.5"/>'
            '<rect x="236" y="136" width="148" height="68" rx="10" fill="none" stroke="#22c55e" stroke-width="2.5"/>'
            '<text x="100" y="238" fill="#f59e0b" font-size="13">group 1 -> A\'C\'</text>'
            '<text x="240" y="238" fill="#22c55e" font-size="13">group 2 -> AC</text>'
            "</svg>"
        ),
        "hotspots": [
            {"x": 96, "y": 76, "w": 148, "h": 68, "label": "Group of two",
             "explain": "Minterms 0 and 2 differ only in B, so B cancels and the group reduces to A'C'."},
            {"x": 310, "y": 80, "w": 70, "h": 60, "label": "Wrap-around column",
             "explain": "The leftmost and rightmost columns are adjacent because 00 and 10 differ in only one "
                        "variable. Missing this is the most common K-map error."},
        ],
    },
    "fbd": {
        "title": "Free body diagram of a simply supported beam",
        "caption": "Isolate the body, draw every external force, then write the equilibrium equations.",
        "kind": "svg",
        "spec": (
            '<svg viewBox="0 0 560 250" xmlns="http://www.w3.org/2000/svg" role="img" '
            'aria-label="Free body diagram of a beam">'
            '<defs><marker id="ar3" markerWidth="10" markerHeight="10" refX="8" refY="3" orient="auto">'
            '<path d="M0,0 L0,6 L9,3 z" fill="#4f7cff"/></marker></defs>'
            '<rect x="80" y="110" width="400" height="22" fill="#2b3b66" stroke="#4f7cff"/>'
            '<polygon points="80,132 100,168 60,168" fill="none" stroke="#9fb0d0" stroke-width="2"/>'
            '<line x1="460" y1="132" x2="500" y2="132" stroke="#9fb0d0" stroke-width="2"/>'
            '<circle cx="480" cy="140" r="8" fill="none" stroke="#9fb0d0" stroke-width="2"/>'
            '<line x1="280" y1="40" x2="280" y2="102" stroke="#ef4444" stroke-width="3" marker-end="url(#ar3)"/>'
            '<text x="292" y="60" fill="#ef4444" font-size="14">200 N</text>'
            '<line x1="80" y1="200" x2="80" y2="140" stroke="#22c55e" stroke-width="3" marker-end="url(#ar3)"/>'
            '<text x="30" y="215" fill="#22c55e" font-size="14">R_A</text>'
            '<line x1="480" y1="200" x2="480" y2="150" stroke="#22c55e" stroke-width="3" marker-end="url(#ar3)"/>'
            '<text x="492" y="215" fill="#22c55e" font-size="14">R_B</text>'
            '<text x="180" y="240" fill="#6f80a4" font-size="13">Sum of moments about A gives R_B directly</text>'
            "</svg>"
        ),
        "hotspots": [
            {"x": 60, "y": 132, "w": 50, "h": 40, "label": "Pin support",
             "explain": "A pin provides two reaction components: vertical and horizontal."},
            {"x": 455, "y": 132, "w": 55, "h": 20, "label": "Roller support",
             "explain": "A roller provides only a vertical reaction - it cannot resist horizontal movement."},
        ],
    },
}

# =============================================================================
# PROJECTS
# =============================================================================

PROJECTS = [
    {
        "slug": "student-performance-dashboard",
        "title": "Student Performance Dashboard (Full Stack)",
        "branch": "cse", "subject": "software-engineering",
        "difficulty": "intermediate", "category": "software", "est_hours": 45,
        "summary": "A server-rendered web application with a relational database, authentication, charts and an "
                   "exportable report - the single best project for a first software engineering interview.",
        "problem_statement": (
            "A department needs a way to record marks for every subject across semesters, show a student's trend "
            "over time, flag at-risk students automatically, and let a faculty member export a printable report. "
            "Right now this lives in disconnected spreadsheets that disagree with each other."
        ),
        "objective": (
            "Design a normalised relational schema, build a secure server-rendered application on top of it, and "
            "add three analytical features: a per-student trend chart, an at-risk detector and a PDF/CSV export."
        ),
        "prerequisites": ["SQL and normalisation", "One backend language", "Basic HTML and CSS", "Git"],
        "hardware": "Any laptop. No special hardware required.",
        "software": "Python 3.11+ or Java 17+, PostgreSQL or SQLite, Git, any code editor.",
        "architecture": (
            "A three-tier design. The presentation tier is server-rendered HTML with progressive enhancement, so "
            "the application works without JavaScript. The application tier holds the routing, validation and "
            "business rules. The data tier is a relational database with a normalised schema and foreign key "
            "constraints enforced. Sessions are stored server side with only an opaque token in the cookie.\n\n"
            "```\n"
            "Browser --HTTPS--> [App Server: routes, validation, templates]\n"
            "                              |\n"
            "                              +--> [Relational DB: students, subjects, marks]\n"
            "                              +--> [Session store]\n"
            "```"
        ),
        "source_code": (
            "Suggested module layout:\n\n"
            "```\n"
            "app/\n"
            "  main.py           # application entry point and route table\n"
            "  db.py             # connection handling and query helpers\n"
            "  models.py         # data access for students, subjects, marks\n"
            "  services.py       # business rules: at-risk detection, GPA calculation\n"
            "  templates/        # server rendered HTML\n"
            "  static/           # CSS and small progressive-enhancement JS\n"
            "migrations/\n"
            "tests/\n"
            "```"
        ),
        "database_design": (
            "Core tables:\n\n"
            "- `students(id, roll_no UNIQUE, name, email UNIQUE, branch_id, admitted_year)`\n"
            "- `subjects(id, code UNIQUE, name, credits, semester_id)`\n"
            "- `enrolments(id, student_id, subject_id, UNIQUE(student_id, subject_id))`\n"
            "- `assessments(id, subject_id, name, max_marks, weight)`\n"
            "- `marks(id, enrolment_id, assessment_id, score, UNIQUE(enrolment_id, assessment_id))`\n\n"
            "The UNIQUE constraints do real work: they make it impossible to record the same assessment twice for "
            "one student, which is the bug that plagues spreadsheet-based systems. Add an index on "
            "`marks(enrolment_id)` because every report query filters on it."
        ),
        "testing": (
            "Write tests at three levels. Unit tests for the GPA and at-risk calculations, using boundary cases "
            "(exactly 40%, zero marks, a student with no assessments). Integration tests that exercise a full "
            "request against a temporary database. One end-to-end test that registers, logs in, records marks and "
            "reads the report back."
        ),
        "expected_output": (
            "A running web application where a faculty member logs in, records marks, sees a per-student trend "
            "chart, sees a highlighted list of at-risk students, and downloads a report. Include a screenshot in "
            "your README."
        ),
        "improvements": [
            "Add role-based access so students can only see their own marks.",
            "Cache the at-risk computation and invalidate it on mark entry.",
            "Add CSV import with row-level error reporting.",
            "Deploy behind a reverse proxy with HTTPS and rate limiting.",
        ],
        "resume_md": (
            "**Student Performance Dashboard** | Python, SQL, HTML/CSS\n"
            "- Designed a normalised 6-table schema with unique constraints that eliminate duplicate mark entry\n"
            "- Built a server-rendered application with hashed-password authentication and server-side sessions\n"
            "- Implemented automatic at-risk detection and per-student trend visualisation\n"
            "- Covered business logic with 40+ unit and integration tests"
        ),
        "interview_questions": [
            "Why did you normalise the schema this way? What would break if you stored marks in one wide table?",
            "How does your at-risk rule work, and how would you change it if the threshold varied by branch?",
            "What happens if two faculty members record marks for the same student at the same moment?",
            "How would this design change to support 50,000 students?",
        ],
        "tech": ["Python", "SQL", "HTML", "CSS"],
        "skills": ["database design", "backend development", "testing", "data visualisation"],
        "steps": [
            ("1. Requirements", "Write down every actor and every action",
             "List the actors: student, faculty, administrator. For each, write the actions they need as plain "
             "sentences - 'a faculty member records marks for an assessment', 'a student views their trend'. "
             "Turn each sentence into a screen later. Resist the urge to start coding; two hours here saves two "
             "weeks later."),
            ("2. Schema", "Design and create the tables",
             "Draw the entity relationships first. Identify the entities (student, subject, assessment, mark), "
             "then the relationships. Write the CREATE TABLE statements with explicit foreign keys, NOT NULL "
             "constraints and UNIQUE constraints. Insert ten rows by hand and query them before writing any "
             "application code."),
            ("3. Data access", "Write the query layer",
             "Build a small module that owns every SQL statement. Never let a SQL string appear in a route "
             "handler. Use parameterised queries throughout - this is both the security requirement and the "
             "readability requirement."),
            ("4. Core screens", "Build the read paths first",
             "Implement the student list, the student detail page and the marks entry form. Get the read paths "
             "working before the write paths; they are simpler and they prove the schema is right."),
            ("5. Analytics", "Add GPA, trend and at-risk detection",
             "Compute weighted GPA from credits. Plot marks over semesters. Define at-risk explicitly - for "
             "example, two consecutive semesters below a threshold, or a current semester average more than one "
             "standard deviation below the cohort - and write it as a single testable function."),
            ("6. Security", "Authentication, sessions and validation",
             "Hash passwords with a memory-hard algorithm and a per-user salt. Store only a hash of the session "
             "token. Validate and escape every input at the boundary. Add CSRF protection to every state-changing "
             "form."),
            ("7. Tests and polish", "Cover the logic and write the README",
             "Write the tests described in the testing section. Then write a README with setup instructions, a "
             "screenshot and a short paragraph on the hardest decision you made. Interviewers read the README "
             "before they read the code."),
        ],
        "resources": [
            ("documentation", "PostgreSQL Tutorial", "https://www.postgresql.org/docs/current/tutorial.html",
             "The official tutorial covers exactly the SQL you need."),
            ("course", "freeCodeCamp Relational Databases", "https://www.freecodecamp.org/learn/relational-database/",
             "Free, hands-on, project-based."),
        ],
    },
    {
        "slug": "arduino-weather-station",
        "title": "IoT Weather Station with Live Dashboard",
        "branch": "electronics", "subject": "microprocessors",
        "difficulty": "beginner", "category": "hardware", "est_hours": 25,
        "summary": "Read temperature, humidity and pressure from sensors, publish readings over a network and "
                   "chart them on a self-hosted dashboard.",
        "problem_statement": (
            "You want continuous environmental data for a room, greenhouse or lab bench, with history you can "
            "query and chart, without depending on a cloud service that may disappear."
        ),
        "objective": (
            "Interface digital sensors over I2C, publish readings on a schedule, store them in a database and "
            "render a live chart. Handle sensor failure and network outage gracefully."
        ),
        "prerequisites": ["Basic C or Python", "Ohm's law and voltage dividers", "What HTTP and JSON are"],
        "hardware": "Microcontroller board (ESP32 or Arduino with an Ethernet/Wi-Fi shield), BME280 or DHT22 "
                   "sensor, breadboard, jumper wires, 10 kOhm pull-up resistors, USB cable. Total cost under "
                   "1500 INR.",
        "software": "PlatformIO or the Arduino IDE, Python 3 for the collector, SQLite.",
        "architecture": (
            "```\n"
            "[Sensor]--I2C-->[Microcontroller]--HTTP POST-->[Collector]-->[SQLite]-->[Dashboard]\n"
            "```\n\n"
            "The microcontroller reads the sensor every 60 seconds, buffers up to 100 readings in flash so a "
            "network outage does not lose data, and posts them as a JSON array. The collector validates and "
            "inserts. The dashboard reads the database and renders a chart."
        ),
        "source_code": (
            "Microcontroller loop outline:\n\n"
            "```\n"
            "read sensor -> if failed, increment error counter and retry with backoff\n"
            "            -> append reading to ring buffer\n"
            "            -> if buffer has data and Wi-Fi is up: POST /api/readings\n"
            "            -> if POST succeeds: clear buffer; else keep for next cycle\n"
            "```\n\n"
            "The buffer is the whole design. A device that only sends when the network is up is a toy; one that "
            "survives an outage is a product."
        ),
        "database_design": (
            "`readings(id, device_id, ts, temperature_c, humidity_pct, pressure_hpa, created_at)` with an index on "
            "`(device_id, ts)`. Every dashboard query filters by device and time range, so that composite index is "
            "the one that matters. Consider rounding timestamps to the minute - it halves the row count for no "
            "practical loss."
        ),
        "testing": (
            "Test the collector with malformed JSON, out-of-range values (humidity above 100%, temperature below "
            "-50 C) and duplicate timestamps. On the device side, unplug the network for ten minutes and confirm "
            "the readings arrive afterwards with their original timestamps, not the upload time."
        ),
        "expected_output": "A dashboard showing temperature, humidity and pressure over the last 24 hours, backed "
                           "by a database you can query directly.",
        "improvements": [
            "Add MQTT so several devices can share one collector.",
            "Calibrate the sensor against a reference thermometer and store the offset.",
            "Add alerting when a threshold is crossed.",
            "Make the device sleep between readings to run on a battery for weeks.",
        ],
        "resume_md": (
            "**IoT Weather Station** | C++, Python, SQLite\n"
            "- Interfaced a BME280 over I2C and published readings on a 60-second schedule\n"
            "- Implemented a 100-reading flash buffer so network outages cause no data loss\n"
            "- Built a Python collector with input validation and a live charting dashboard"
        ),
        "interview_questions": [
            "Why I2C rather than SPI or UART for this sensor?",
            "What happens to your data if the network is down for an hour?",
            "How do you detect that a sensor has failed rather than reporting a stuck value?",
            "How would you secure the HTTP endpoint?",
        ],
        "tech": ["C++", "Python", "SQLite", "HTTP"],
        "skills": ["embedded systems", "sensor interfacing", "IoT", "data collection"],
        "steps": [
            ("1. Breadboard", "Wire the sensor and read it over I2C",
             "Connect VCC, GND, SDA and SCL. Add pull-up resistors if the module does not have them. Scan the I2C "
             "bus to find the sensor address, then read the chip ID register to confirm communication before "
             "trying to read measurements."),
            ("2. Reliable reads", "Read all three measurements with error handling",
             "BME280 requires a specific start-up delay and a forced or normal measurement mode. Read the raw "
             "registers and apply the calibration coefficients from the datasheet - the library does this for "
             "you, but read the datasheet section once so you understand what it is doing."),
            ("3. Buffering", "Survive a network outage",
             "Implement a ring buffer of 100 readings. Each entry carries its own timestamp taken at read time. "
             "This is the difference between a demo and a working system."),
            ("4. Collector", "Accept and validate readings",
             "A single POST endpoint taking a JSON array. Validate ranges, reject duplicates, insert in one "
             "transaction. Return how many rows were accepted so the device can trim its buffer correctly."),
            ("5. Dashboard", "Chart the last 24 hours",
             "Query the database for the time range, downsample to one point per minute if there are more than "
             "500 points, and render a chart. Add a table of the latest ten readings."),
            ("6. Harden", "Handle real-world failure",
             "Add a watchdog so a hung device restarts. Log sensor failures with a counter. Set a sensible "
             "timeout on every network call."),
        ],
        "resources": [
            ("documentation", "BME280 datasheet", "https://www.bosch-sensortec.com/media/boschsensortec/downloads/datasheets/bst-bme280-ds002.pdf",
             "The calibration section is the part most people skip and later regret."),
            ("tool", "PlatformIO", "https://platformio.org/", "Cross-platform embedded development environment."),
        ],
    },
    {
        "slug": "solar-pump-controller",
        "title": "Solar Water Pump Controller",
        "branch": "electrical", "subject": "power-electronics",
        "difficulty": "advanced", "category": "hardware", "est_hours": 60,
        "summary": "Design the power electronics and control logic that runs a DC pump from a solar panel array at "
                   "its maximum power point.",
        "problem_statement": (
            "A solar panel's output voltage varies widely with irradiance. A pump connected directly either stalls "
            "in low light or is damaged by over-voltage in bright sun. Something must match the panel to the pump "
            "continuously."
        ),
        "objective": (
            "Build a DC-DC converter stage with maximum power point tracking, protect the panel and pump from "
            "faults, and log energy produced against energy consumed."
        ),
        "prerequisites": ["Power electronics", "DC machines", "Microcontroller programming", "Basic control theory"],
        "hardware": "Solar panel (100 W class), DC pump rated to match, MOSFETs and driver, inductor and "
                   "capacitor for the converter, current and voltage sensors, microcontroller, fuses and "
                   "heat sinks.",
        "software": "Simulation tool (LTspuce or any SPICE), embedded toolchain, oscilloscope for measurement.",
        "architecture": (
            "```\n"
            "[Solar Panel]-->[DC-DC Buck]-->[Pump]\n"
            "      |              ^\n"
            "      +--[V,I sense]--+-->[MPPT controller]\n"
            "```\n\n"
            "The controller measures panel voltage and current, computes power, and adjusts the converter duty "
            "cycle to climb toward the maximum power point using perturb-and-observe."
        ),
        "source_code": (
            "Perturb-and-observe outline:\n\n"
            "```\n"
            "every 100 ms:\n"
            "  p = v * i\n"
            "  if p > p_prev: keep the direction of the last duty change\n"
            "  else: reverse it\n"
            "  duty += step * direction   (clamped to safe limits)\n"
            "```\n\n"
            "Add a deadband so the controller stops hunting once power stops changing measurably."
        ),
        "database_design": (
            "`telemetry(ts, panel_v, panel_a, duty, pump_current, state)`. Sample at 1 Hz and keep raw data for 7 "
            "days plus hourly averages indefinitely - that is what turns a project into a dataset you can analyse "
            "and talk about."
        ),
        "testing": (
            "Test in simulation before touching hardware. Verify the converter efficiency at several duty cycles, "
            "confirm the MPPT converges within a second of an irradiance step, and prove the protection trips on "
            "over-current and on pump stall."
        ),
        "expected_output": "A working rig that starts the pump in morning light, tracks the maximum power point "
                           "through the day, and produces an energy log you can plot.",
        "improvements": [
            "Replace perturb-and-observe with incremental conductance for better tracking in changing light.",
            "Add soft start to limit inrush current into the pump.",
            "Add remote monitoring over a network link.",
        ],
        "resume_md": (
            "**Solar Water Pump Controller** | Power Electronics, Embedded C\n"
            "- Designed a buck converter stage with maximum power point tracking using perturb-and-observe\n"
            "- Implemented over-current, over-voltage and stall protection with tested trip thresholds\n"
            "- Logged irradiance against delivered energy to quantify tracking efficiency"
        ),
        "interview_questions": [
            "Why does a solar panel need MPPT rather than direct connection?",
            "What is the weakness of perturb-and-observe under rapidly changing irradiance?",
            "How did you size the inductor and capacitor?",
            "What protection did you include and how did you test it?",
        ],
        "tech": ["Power Electronics", "Embedded C", "SPICE"],
        "skills": ["power electronics", "control", "embedded systems", "measurement"],
        "steps": [
            ("1. Characterise the panel", "Measure the I-V curve",
             "Plot current against voltage under load at several irradiances. The knee of the curve is the "
             "maximum power point. Knowing where it actually sits is what makes the rest of the design "
             "quantitative rather than hopeful."),
            ("2. Size the converter", "Choose the topology and components",
             "A buck converter steps the panel voltage down to the pump rating. Size the inductor for acceptable "
             "current ripple at your switching frequency, and the capacitor for acceptable voltage ripple. "
             "Simulate before building."),
            ("3. Control loop", "Implement MPPT",
             "Start with perturb-and-observe because it is simple and demonstrably works. Measure convergence "
             "time and steady-state oscillation, then improve it."),
            ("4. Protection", "Never let a fault reach the hardware",
             "Over-current limit, over-voltage clamp, reverse polarity protection, fuses rated to interrupt the "
             "available fault current, and thermal shutdown. Test each one deliberately."),
            ("5. Log and analyse", "Prove it works with data",
             "Log at 1 Hz, then plot delivered energy against the theoretical maximum from your measured I-V "
             "curve. That percentage is your headline number."),
        ],
        "resources": [
            ("documentation", "LTspice", "https://www.analog.com/en/resources/design-tools-and-calculators/ltspice-simulator.html",
             "Free SPICE simulator for the converter design."),
        ],
    },
    {
        "slug": "structural-load-analyser",
        "title": "Beam Load Analyser with Shear and Moment Diagrams",
        "branch": "civil", "subject": "structural-analysis",
        "difficulty": "intermediate", "category": "software", "est_hours": 35,
        "summary": "Compute reactions, shear force and bending moment for a simply supported beam under arbitrary "
                   "loads, and plot the diagrams.",
        "problem_statement": (
            "Students and junior engineers hand-calculate shear and moment diagrams for standard cases but have no "
            "tool for a beam with several mixed loads at arbitrary positions."
        ),
        "objective": (
            "Build a numerical solver that accepts point loads, uniformly distributed loads and moments at "
            "arbitrary positions, then computes and plots the reaction forces, shear force diagram and bending "
            "moment diagram."
        ),
        "prerequisites": ["Statics and equilibrium", "Basic numerical methods", "One programming language"],
        "hardware": "Any laptop.",
        "software": "Python with NumPy and Matplotlib, or Java with any charting library.",
        "architecture": (
            "A pure computational core with no user interface, wrapped by a thin interface layer. The core takes a "
            "beam definition and returns arrays of shear and moment values. Keeping the core free of any UI code "
            "makes it unit-testable against textbook answers, which is the only way to trust the output."
        ),
        "source_code": (
            "Core algorithm:\n\n"
            "```\n"
            "1. Sum moments about the left support to find the right reaction.\n"
            "2. Sum vertical forces to find the left reaction.\n"
            "3. Walk along the beam in small steps. At each station, sum every load to the left.\n"
            "4. Shear at a station = reaction - sum of downward loads to the left.\n"
            "5. Moment at a station = integral of shear (cumulative trapezoidal sum).\n"
            "```\n\n"
            "The integral relationship between shear and moment is what makes the numerical approach work."
        ),
        "database_design": (
            "Optional persistence: `beams(id, name, length, support_type, created_at)` and `loads(id, beam_id, "
            "kind, position, magnitude)`. Storing load cases lets you compare designs and build a library of "
            "standard cases."
        ),
        "testing": (
            "Validate against closed-form textbook cases: a central point load (maximum moment PL/4), a uniformly "
            "distributed load (maximum moment wL^2/8), and a point load at a third span. If your numerical answer "
            "is not within 0.5% of the closed form, your step size or your load application is wrong."
        ),
        "expected_output": "A tool that takes a beam and its loads and produces labelled shear and moment diagrams "
                           "plus the maximum values and their positions.",
        "improvements": [
            "Add overhangs and cantilever supports.",
            "Add a cross-section library and report maximum bending stress.",
            "Export results to a PDF report.",
        ],
        "resume_md": (
            "**Beam Load Analyser** | Python, NumPy, Matplotlib\n"
            "- Implemented a numerical solver for reactions, shear and moment under arbitrary mixed loading\n"
            "- Validated output against closed-form textbook solutions to within 0.5%\n"
            "- Produced labelled engineering diagrams suitable for design reports"
        ),
        "interview_questions": [
            "What is the relationship between load, shear and bending moment?",
            "Where does the maximum bending moment occur in a simply supported beam with a central point load?",
            "How did you verify your numerical solution?",
        ],
        "tech": ["Python", "NumPy", "Matplotlib"],
        "skills": ["numerical methods", "structural analysis", "data visualisation"],
        "steps": [
            ("1. Reactions", "Solve the statics",
             "Two equations, two unknowns for a simply supported beam. Implement this first and test it against "
             "hand calculations before going any further."),
            ("2. Shear", "Walk the beam and accumulate",
             "Discretise the beam into 500 stations. At each station sum the reaction and every load to the left. "
             "Handle point loads as step changes and distributed loads as ramps."),
            ("3. Moment", "Integrate the shear",
             "Use the trapezoidal rule on the shear array. The moment should be zero at both supports - that is "
             "your built-in check."),
            ("4. Plot", "Draw proper engineering diagrams",
             "Plot shear and moment against position with the baseline at zero, label the maximum values and their "
             "positions, and use the conventional sign convention."),
            ("5. Validate", "Compare with closed-form solutions",
             "Run the three standard textbook cases and print the percentage error. This is the step that turns a "
             "program into an engineering tool."),
        ],
        "resources": [],
    },
    {
        "slug": "distillation-column-simulator",
        "title": "Binary Distillation Column Simulator",
        "branch": "chemical", "subject": "mass-transfer",
        "difficulty": "advanced", "category": "software", "est_hours": 40,
        "summary": "Apply the McCabe-Thiele method numerically to find the number of theoretical stages for a binary "
                   "separation.",
        "problem_statement": (
            "Designing a distillation column by hand-drawing the McCabe-Thiele diagram is accurate enough for a "
            "tutorial but useless for exploring how reflux ratio, feed quality and product purity trade against "
            "each other."
        ),
        "objective": (
            "Implement the operating lines and equilibrium curve numerically, step off stages automatically, and "
            "let the user vary reflux ratio and feed condition to see the effect on stage count and energy demand."
        ),
        "prerequisites": ["Vapour-liquid equilibrium", "Mass transfer", "Numerical methods"],
        "hardware": "Any laptop.",
        "software": "Python with NumPy and Matplotlib.",
        "architecture": (
            "A thermodynamic module that produces the equilibrium curve, a column module that builds the operating "
            "lines, a stepping module that walks from the distillate composition to the feed composition and then "
            "to the bottoms, and a plotting module. Keeping the thermodynamics separate means you can swap in a "
            "different system without touching the column logic."
        ),
        "source_code": (
            "```\n"
            "rectifying line:  y = (R/(R+1)) x + xD/(R+1)\n"
            "stripping line:   from (xB, xB) through the q-line intersection\n"
            "q line:           y = (q/(q-1)) x - xF/(q-1)\n"
            "step off stages between the equilibrium curve and the operating lines\n"
            "```\n\n"
            "Use a root finder to intersect the stepping line with the equilibrium curve rather than a fixed grid "
            "- it is barely more code and much more accurate."
        ),
        "database_design": "Not required. If you want to save cases, store the input parameters and the resulting "
                           "stage count so you can plot stage count against reflux ratio.",
        "testing": (
            "Validate against the standard benzene-toluene textbook example. Confirm that as reflux ratio "
            "increases the stage count falls toward the minimum, and that at total reflux the stage count equals "
            "the Fenske minimum. If either limit is wrong, the operating lines are wrong."
        ),
        "expected_output": "An interactive McCabe-Thiele plot with the stages drawn, and a chart showing stage "
                           "count against reflux ratio.",
        "improvements": [
            "Add stage efficiency so the output is real trays rather than theoretical stages.",
            "Add an energy estimate from the reboiler duty.",
            "Support a second binary system.",
        ],
        "resume_md": (
            "**Distillation Column Simulator** | Python, NumPy\n"
            "- Implemented the McCabe-Thiele method numerically with automatic stage stepping\n"
            "- Validated against textbook benzene-toluene results and both analytical limits\n"
            "- Produced an interactive reflux-ratio versus stage-count trade-off chart"
        ),
        "interview_questions": [
            "What happens to the number of stages as the reflux ratio approaches the minimum?",
            "What does the q parameter represent physically?",
            "Why does your simulator need a root finder rather than a fixed grid?",
        ],
        "tech": ["Python", "NumPy", "Matplotlib"],
        "skills": ["process simulation", "thermodynamics", "numerical methods"],
        "steps": [
            ("1. Equilibrium data", "Build the x-y curve",
             "Use Raoult's law with Antoine vapour pressure correlations for benzene and toluene. Generate the "
             "equilibrium curve and plot it - if it does not look like the textbook curve, stop and fix it."),
            ("2. Operating lines", "Draw the rectifying and stripping lines",
             "Implement both lines and the q-line. Plot all three with the equilibrium curve and the 45-degree "
             "reference line."),
            ("3. Step off stages", "Automate the graphical method",
             "Start at the distillate composition on the 45-degree line, move horizontally to the equilibrium "
             "curve, then vertically to the operating line. Switch to the stripping line below the feed stage. "
             "Stop at the bottoms composition."),
            ("4. Sensitivity", "Explore the trade-offs",
             "Sweep the reflux ratio from just above minimum to total reflux and plot stage count. Add reboiler "
             "duty as a second axis so the economic trade-off is visible."),
        ],
        "resources": [],
    },
    {
        "slug": "portfolio-website",
        "title": "Personal Portfolio Website",
        "branch": "cse", "subject": "web-technologies",
        "difficulty": "beginner", "category": "software", "est_hours": 15,
        "summary": "A fast, accessible, self-hosted personal site that a recruiter can read in thirty seconds.",
        "problem_statement": (
            "Recruiters spend under a minute on a portfolio. Most student sites are slow, break on a phone, and "
            "bury the interesting work under animation."
        ),
        "objective": (
            "Build a site that loads in under a second, works without JavaScript, is readable on a phone, and puts "
            "your three best projects above the fold."
        ),
        "prerequisites": ["HTML and CSS basics", "Git"],
        "hardware": "Any laptop.",
        "software": "A text editor and Git.",
        "architecture": (
            "Static HTML and CSS, no framework, no build step, no tracking scripts. Host it on a free static "
            "host or a GitHub Pages branch. The constraint of no JavaScript is deliberate: it forces the content "
            "to be good on its own."
        ),
        "source_code": (
            "```\n"
            "index.html        # one page, semantic elements\n"
            "style.css         # custom properties, mobile-first\n"
            "projects/*.html   # one page per project with the problem, the decision, the result\n"
            "```\n\n"
            "Use semantic elements (header, main, article, footer). A screen reader navigating your portfolio is "
            "a real use case, and semantic HTML is what makes it work."
        ),
        "database_design": "None. This is deliberately a static site.",
        "testing": (
            "Test with JavaScript disabled. Test on a narrow viewport. Test with the browser text size at 200%. "
            "Run the page through an accessibility checker and fix the contrast failures - they are almost always "
            "trivial and they are the most commonly reported issue."
        ),
        "expected_output": "A live URL that loads fast and presents three projects clearly, each with the problem, "
                           "the key technical decision and a measurable result.",
        "improvements": [
            "Add a print stylesheet so a recruiter can print it.",
            "Add an RSS feed for a blog.",
            "Add dark mode using prefers-color-scheme.",
        ],
        "resume_md": (
            "**Personal Portfolio** | HTML, CSS\n"
            "- Built a dependency-free static site loading in under one second with no JavaScript required\n"
            "- Achieved full keyboard navigation and WCAG AA contrast compliance\n"
            "- Documented three projects with problem, decision and measured outcome"
        ),
        "interview_questions": [
            "Why did you avoid a framework?",
            "How did you verify the accessibility of your site?",
            "What is the largest asset on your page and how did you optimise it?",
        ],
        "tech": ["HTML", "CSS"],
        "skills": ["web fundamentals", "accessibility", "performance"],
        "steps": [
            ("1. Content first", "Write the text before any styling",
             "Write your headline, a two-sentence summary and three project descriptions in a plain text file. "
             "Each project description should state the problem, the key decision you made and the result. If you "
             "cannot write that, you do not understand the project well enough yet."),
            ("2. Structure", "Semantic HTML",
             "Build the page with header, main, article and footer. Add proper heading hierarchy - one h1, then "
             "h2 and h3 in order. Add alt text to every image."),
            ("3. Style", "Mobile-first CSS",
             "Use custom properties for colours so dark mode is a one-line change. Set a readable line length "
             "(around 65 characters) and a base font size of at least 16 pixels."),
            ("4. Projects", "One page per project",
             "Include the problem, a diagram or screenshot, the hardest decision and what you would do "
             "differently. That last section is what impresses interviewers."),
            ("5. Ship", "Deploy and measure",
             "Deploy it, then measure the load time and fix the largest asset. Add the URL to your resume and "
             "your GitHub profile."),
        ],
        "resources": [
            ("documentation", "MDN Accessibility Guide", "https://developer.mozilla.org/en-US/docs/Learn/Accessibility",
             "Practical, free and directly applicable."),
        ],
    },
]

# =============================================================================
# PROGRAMMING LANGUAGES + LEARNING MODULES
# =============================================================================

LANGUAGES = [
    ("python", "Python", "py", "#3776ab",
     "The best first language and the language of data, automation and machine learning. Readable syntax, a "
     "massive standard library, and it is what EngineVerse itself is built with.", "python"),
    ("java", "Java", "java", "#f89820",
     "Statically typed, strongly object oriented and the backbone of enterprise systems, Android and large "
     "codebases. Learning Java teaches you types and design properly.", "java"),
    ("javascript", "JavaScript", "js", "#f7df1e",
     "The language of the browser and, through Node.js, of many backends. Essential for anything user-facing on "
     "the web.", "javascript"),
    ("cpp", "C++", "cpp", "#00599c",
     "Direct memory control with modern abstractions. Used in competitive programming, game engines, embedded "
     "systems and anything where performance is non-negotiable.", "cpp"),
    ("c", "C", "c", "#a8b9cc",
     "The language every other language is measured against. Learning C teaches you what a pointer, a stack frame "
     "and a memory allocation actually are.", "c"),
    ("sql", "SQL", "sql", "#e38c00",
     "Not a general-purpose language, but the one every engineer uses daily. Data lives in relational databases "
     "and SQL is how you talk to them.", None),
]

LANGUAGE_MODULES = {
    "python": [
        ("python-variables", "Variables and Types", "Names bound to values, and the built-in types.",
         "Python is dynamically typed: a name is bound to a value and can be rebound to a value of another type. "
         "The built-in scalar types are `int` (arbitrary precision), `float` (IEEE 754 double), `bool`, `str` and "
         "`NoneType`. Strings are immutable sequences of Unicode code points.\n\n"
         "Type conversion is explicit: `int('42')`, `str(42)`, `float('3.14')`. Python will not silently convert "
         "for you, which prevents an entire category of bugs.\n\n"
         "Use `type(x)` to inspect and `isinstance(x, int)` to test. Prefer `isinstance` in conditionals because "
         "it respects inheritance.",
         "name = 'EngineVerse'\nyear = 2026\nratio = 3.14\nactive = True\n\nprint(type(name), type(year), type(ratio))\nprint(name.upper(), year + 1, round(ratio, 1))\nprint(int('42') * 2)",
         "Bind a variable to your name and another to your graduation year. Print a sentence that uses both, with "
         "the year converted to a string."),
        ("python-control-flow", "Control Flow", "Conditionals, loops and the statements that control them.",
         "`if / elif / else` branches on truthiness. Empty containers, zero, `None` and `''` are falsy - a "
         "convenience that also causes bugs when zero is a meaningful value.\n\n"
         "`for` iterates over a sequence; `while` repeats while a condition holds. `range(n)` produces 0 to n-1. "
         "`enumerate` gives index and value; `zip` pairs two sequences.\n\n"
         "`break` exits a loop, `continue` skips to the next iteration, and `else` on a loop runs only if the loop "
         "was never broken - a genuinely useful and often unknown feature.",
         "for i, letter in enumerate('engine'):\n    if letter == 'n':\n        continue\n    print(i, letter)\n\ntotal = 0\nfor n in range(1, 11):\n    if total > 20:\n        break\n    total += n\nprint('total', total)",
         "Print the multiplication table of 7 from 1 to 10 using a loop, then rewrite it with a list "
         "comprehension."),
        ("python-functions", "Functions", "Parameters, return values, scope and defaults.",
         "Functions are defined with `def` and are first-class objects - you can pass them, store them and return "
         "them. Arguments are passed by object reference, so mutating a mutable argument is visible to the caller.\n\n"
         "Default parameter values are evaluated once at definition time. Never use a mutable default like "
         "`def f(items=[])` - use `None` and create the list inside.\n\n"
         "`*args` collects extra positional arguments into a tuple; `**kwargs` collects keyword arguments into a "
         "dict. Type hints do not enforce anything at runtime but they document intent and let tools check your "
         "code.",
         "def describe(name: str, marks: list[int] | None = None) -> str:\n    marks = marks or []\n    if not marks:\n        return f'{name} has no marks recorded'\n    average = sum(marks) / len(marks)\n    return f'{name}: average {average:.1f} from {len(marks)} assessments'\n\nprint(describe('Asha', [72, 85, 91]))\nprint(describe('Ravi'))",
         "Write a function `grade(score)` that returns 'A' for 90 and above, 'B' for 75 and above, 'C' for 50 and "
         "above, otherwise 'F'. Test it on the boundaries."),
        ("python-collections", "Collections", "Lists, tuples, sets and dictionaries.",
         "Four built-in collections cover almost everything.\n\n"
         "- **list** - ordered, mutable, allows duplicates. Append is amortised O(1); insert and remove in the "
         "middle are O(n).\n"
         "- **tuple** - ordered, immutable. Usable as a dictionary key, and the idiomatic way to return multiple "
         "values.\n"
         "- **set** - unordered, unique. Membership testing is O(1) average, which makes it the right tool for "
         "'have I seen this'.\n"
         "- **dict** - key to value mapping, insertion ordered since Python 3.7, O(1) lookup.\n\n"
         "Comprehensions build all four concisely: `[x*x for x in nums if x > 0]`, `{k: v for k, v in pairs}`.",
         "nums = [3, 1, 4, 1, 5, 9, 2, 6, 5]\nprint('unique:', sorted(set(nums)))\nprint('squares:', [n * n for n in nums if n % 2 == 1])\n\ncounts = {}\nfor n in nums:\n    counts[n] = counts.get(n, 0) + 1\nprint('counts:', counts)\n\nfirst, *rest = nums\nprint(first, rest)",
         "Count the frequency of each word in a sentence and print the three most common."),
        ("python-strings-files", "Strings and Files", "Text processing and persistence.",
         "Strings are immutable, so every 'modification' creates a new string. Building a long string with `+=` in "
         "a loop is O(n^2) - collect parts in a list and use `''.join(parts)`.\n\n"
         "f-strings format values inline: `f'{value:.2f}'`, `f'{name:>10}'`, `f'{count:,}'`.\n\n"
         "Use `with open(...)` for files. It closes the file even if an exception is raised. Always specify "
         "`encoding='utf-8'` explicitly; the default varies by platform and is a classic source of bugs.",
         "words = ['engineer', 'reads', 'and', 'applies']\nsentence = ' '.join(w.capitalize() for w in words)\nprint(sentence)\n\nwith open('/tmp/ev_demo.txt', 'w', encoding='utf-8') as handle:\n    handle.write(f'{sentence}\\n')\n\nwith open('/tmp/ev_demo.txt', encoding='utf-8') as handle:\n    for line in handle:\n        print(repr(line))",
         "Read a text file and print the number of lines, words and characters."),
        ("python-oop", "Object Oriented Python", "Classes, inheritance and special methods.",
         "A class bundles data with the functions that operate on it. `__init__` initialises an instance; `self` "
         "is the instance, passed explicitly.\n\n"
         "Special (dunder) methods make your objects work with Python syntax: `__str__` for printing, `__eq__` "
         "for comparison, `__len__` for `len()`, `__getitem__` for indexing, `__repr__` for debugging.\n\n"
         "`@dataclass` removes the boilerplate for classes that mostly hold data. Prefer composition over "
         "inheritance; inherit only when the subclass genuinely *is a* superclass.",
         "from dataclasses import dataclass, field\n\n\n@dataclass\nclass Student:\n    name: str\n    marks: list[int] = field(default_factory=list)\n\n    def add(self, score: int) -> None:\n        if not 0 <= score <= 100:\n            raise ValueError('score must be between 0 and 100')\n        self.marks.append(score)\n\n    @property\n    def average(self) -> float:\n        return sum(self.marks) / len(self.marks) if self.marks else 0.0\n\n\nasha = Student('Asha')\nfor score in (72, 85, 91):\n    asha.add(score)\nprint(asha)\nprint(f'average {asha.average:.1f}')",
         "Write a `BankAccount` class with deposit, withdraw and balance. Withdraw must refuse to overdraw."),
        ("python-errors", "Error Handling", "Exceptions and defensive programming.",
         "Exceptions signal that something went wrong. Let them propagate unless you can genuinely recover - "
         "catching everything with a bare `except:` hides bugs.\n\n"
         "Catch the specific exception you expect. `except Exception` at a top-level boundary is acceptable; "
         "elsewhere it is usually a mistake.\n\n"
         "Raise your own exception types for domain errors so callers can distinguish them. Use `finally` or "
         "`with` for cleanup rather than relying on the happy path.",
         "class InvalidMarkError(Exception):\n    pass\n\n\ndef record(score):\n    if not isinstance(score, (int, float)):\n        raise TypeError('score must be numeric')\n    if not 0 <= score <= 100:\n        raise InvalidMarkError(f'{score} is out of range')\n    return score\n\n\nfor candidate in (85, 150, 'abc'):\n    try:\n        print('ok', record(candidate))\n    except InvalidMarkError as error:\n        print('rejected:', error)\n    except TypeError as error:\n        print('type error:', error)",
         "Write a `safe_divide(a, b)` that returns None instead of raising, and logs what went wrong."),
        ("python-modules", "Modules and Packages", "Organising programs into files.",
         "A module is a `.py` file; a package is a directory of modules. `import module` binds the module object, "
         "`from module import name` binds just the name.\n\n"
         "`if __name__ == '__main__':` guards code that should only run when the file is executed directly, not "
         "when it is imported - essential for testable modules.\n\n"
         "Avoid circular imports. If two modules import each other, the design is wrong: extract the shared part "
         "into a third module.",
         "# maths_tools.py\n\n\ndef clamp(value, low, high):\n    return max(low, min(high, value))\n\n\ndef average(values):\n    values = list(values)\n    return sum(values) / len(values) if values else 0.0\n\n\nif __name__ == '__main__':\n    print(clamp(150, 0, 100))\n    print(average([1, 2, 3]))",
         "Split a program you have already written into two modules and import one from the other."),
        ("python-testing", "Testing", "pytest and test-driven development.",
         "A test is a function that asserts something. pytest discovers functions named `test_*` and reports "
         "failures with the values involved.\n\n"
         "Test behaviour, not implementation. Name tests after what they verify: "
         "`test_average_of_empty_list_is_zero`.\n\n"
         "Cover the boundaries: empty input, single element, zero, negative numbers, and the exact threshold. "
         "Boundary bugs are where real defects live.",
         "def average(values):\n    values = list(values)\n    return sum(values) / len(values) if values else 0.0\n\n\ndef test_average_of_empty_list_is_zero():\n    assert average([]) == 0.0\n\n\ndef test_average_of_single_element():\n    assert average([7]) == 7.0\n\n\ndef test_average_of_several():\n    assert average([1, 2, 3, 4]) == 2.5\n\n\n# run with: python -m pytest",
         "Write three tests for your `grade(score)` function covering each boundary."),
    ],
    "java": [
        ("java-basics", "Java Basics", "Types, variables and the entry point.",
         "Java is statically typed: every variable's type is fixed at compile time and checked before the program "
         "runs. This catches a large class of errors early at the cost of more writing.\n\n"
         "Primitives (`int`, `long`, `double`, `boolean`, `char`) are values; everything else is an object accessed "
         "by reference. `int` is 32-bit and wraps on overflow - use `Math.addExact` or `long` when that matters.\n\n"
         "Execution starts at `public static void main(String[] args)`. Everything else is reachable from there.",
         "public class Main {\n    public static void main(String[] args) {\n        String name = \"EngineVerse\";\n        int year = 2026;\n        double ratio = 3.14159;\n        boolean active = true;\n\n        System.out.printf(\"%s in %d, ratio %.2f, active %b%n\", name, year, ratio, active);\n        System.out.println(\"max int: \" + Integer.MAX_VALUE);\n    }\n}",
         "Declare variables for your name, marks and grade, then print them in one formatted line."),
        ("java-control-flow", "Control Flow and Arrays", "Conditionals, loops and fixed-size arrays.",
         "Java has `if/else`, `switch` (with the modern arrow syntax and exhaustiveness checking on enums), "
         "`for`, enhanced `for` and `while`.\n\n"
         "Arrays are fixed size and zero-indexed. Out-of-bounds access throws `ArrayIndexOutOfBoundsException` "
         "rather than corrupting memory - a safety guarantee C does not give you.\n\n"
         "`ArrayList<T>` is the resizable list you will actually use. Generics make it type-safe at compile time.",
         "import java.util.ArrayList;\nimport java.util.List;\n\npublic class Main {\n    public static void main(String[] args) {\n        List<Integer> marks = new ArrayList<>(List.of(72, 85, 91, 68));\n        int total = 0;\n        for (int mark : marks) {\n            total += mark;\n        }\n        double average = (double) total / marks.size();\n        System.out.printf(\"Average: %.2f over %d assessments%n\", average, marks.size());\n\n        String grade = average >= 75 ? \"First class\" : \"Pass\";\n        System.out.println(grade);\n    }\n}",
         "Print the multiplication table of 7, then store it in a list and print the sum."),
        ("java-oop", "Classes and Objects", "Encapsulation, constructors and methods.",
         "A class declares fields and methods. Constructors initialise instances; `this` refers to the current "
         "instance.\n\n"
         "Encapsulation means fields are `private` and accessed through methods. That gives you a place to "
         "validate, log or change the internal representation later without breaking callers.\n\n"
         "Records (Java 16+) generate the boilerplate for immutable data carriers automatically.",
         "public class Student {\n    private final String name;\n    private final java.util.List<Integer> marks = new java.util.ArrayList<>();\n\n    public Student(String name) {\n        this.name = name;\n    }\n\n    public void addMark(int score) {\n        if (score < 0 || score > 100) {\n            throw new IllegalArgumentException(\"score must be 0-100, got \" + score);\n        }\n        marks.add(score);\n    }\n\n    public double average() {\n        if (marks.isEmpty()) return 0.0;\n        int total = 0;\n        for (int m : marks) total += m;\n        return (double) total / marks.size();\n    }\n\n    @Override\n    public String toString() {\n        return String.format(\"%s: %.1f\", name, average());\n    }\n\n    public static void main(String[] args) {\n        Student asha = new Student(\"Asha\");\n        asha.addMark(72);\n        asha.addMark(85);\n        asha.addMark(91);\n        System.out.println(asha);\n    }\n}",
         "Write a `BankAccount` class with private balance, deposit and withdraw that refuses to overdraw."),
        ("java-interfaces", "Interfaces and Collections", "Polymorphism and the standard collections.",
         "An interface declares behaviour without implementation. Coding to an interface rather than a class is "
         "what lets you swap implementations later - the single most important design habit in Java.\n\n"
         "`List`, `Set` and `Map` are interfaces; `ArrayList`, `HashSet` and `HashMap` are implementations. "
         "Declare variables as the interface, construct the implementation.\n\n"
         "The Streams API expresses filter-map-reduce pipelines declaratively.",
         "import java.util.*;\nimport java.util.stream.*;\n\npublic class Main {\n    public static void main(String[] args) {\n        List<String> subjects = List.of(\"DBMS\", \"OS\", \"Networks\", \"DSA\");\n\n        List<String> short_names = subjects.stream()\n            .filter(s -> s.length() <= 4)\n            .map(String::toUpperCase)\n            .sorted()\n            .collect(Collectors.toList());\n\n        Map<String, Integer> lengths = subjects.stream()\n            .collect(Collectors.toMap(s -> s, String::length));\n\n        System.out.println(short_names);\n        System.out.println(lengths);\n    }\n}",
         "Use streams to find the longest word in a list of strings."),
        ("java-exceptions", "Exceptions and Generics", "Error handling and type parameters.",
         "Checked exceptions must be caught or declared with `throws`. Unchecked exceptions (subclasses of "
         "`RuntimeException`) need not be. Use unchecked for programming errors and checked for recoverable "
         "conditions the caller can act on.\n\n"
         "`try-with-resources` closes anything implementing `AutoCloseable` automatically.\n\n"
         "Generics parameterise types: `List<Integer>`, `Map<String, List<Integer>>`. Wildcards (`? extends T`) "
         "let you write methods that accept a family of types.",
         "import java.util.*;\n\npublic class Main {\n    static <T extends Comparable<T>> T max(List<T> items) {\n        if (items.isEmpty()) throw new IllegalArgumentException(\"empty list\");\n        T best = items.get(0);\n        for (T item : items) {\n            if (item.compareTo(best) > 0) best = item;\n        }\n        return best;\n    }\n\n    public static void main(String[] args) {\n        System.out.println(max(List.of(3, 9, 4)));\n        System.out.println(max(List.of(\"beta\", \"alpha\", \"gamma\")));\n        try {\n            max(List.<Integer>of());\n        } catch (IllegalArgumentException e) {\n            System.out.println(\"caught: \" + e.getMessage());\n        }\n    }\n}",
         "Write a generic `Pair<A, B>` class with getters and a toString."),
    ],
    "javascript": [
        ("js-basics", "JavaScript Basics", "Variables, types and functions.",
         "JavaScript is dynamically typed. Declare with `let` (reassignable) or `const` (not reassignable); never "
         "use `var`, which has confusing function scoping.\n\n"
         "Use `===` for comparison. `==` performs type coercion and produces results nobody wants: "
         "`0 == ''` is true.\n\n"
         "Functions are values. Arrow functions are concise and do not rebind `this`.",
         "const name = 'EngineVerse';\nlet year = 2026;\n\nconst greet = (who) => `Hello, ${who}!`;\nconst add = (a, b) => a + b;\n\nconsole.log(greet(name), year, add(2, 3));\nconsole.log(0 === '', 0 == '');  // false, true - always use ===\n\nconst marks = [72, 85, 91];\nconsole.log(marks.map(m => m * 2).filter(m => m > 150));",
         "Write an arrow function `grade(score)` returning A/B/C/F and test it in the console."),
        ("js-dom", "The DOM and Events", "Making pages interactive.",
         "The DOM is the browser's object model of your HTML. `document.querySelector` finds elements; you change "
         "them through `textContent`, `classList` and `style`.\n\n"
         "`addEventListener` attaches a handler. Never build HTML by concatenating user input into a string - "
         "that is how cross-site scripting happens. Set `textContent`, or create elements explicitly.\n\n"
         "`fetch` performs network requests and returns promises.",
         "// Assume this HTML exists:\n// <input id=\"score\"><button id=\"go\">Add</button><ul id=\"list\"></ul>\n\nconst marks = [];\n\ndocument.querySelector('#go').addEventListener('click', () => {\n  const value = Number(document.querySelector('#score').value);\n  if (Number.isNaN(value)) return;\n  marks.push(value);\n  const item = document.createElement('li');\n  item.textContent = `${value} (running average ${(marks.reduce((a, b) => a + b, 0) / marks.length).toFixed(1)})`;\n  document.querySelector('#list').append(item);\n});",
         "Build a counter page with increment and decrement buttons, without using innerHTML."),
        ("js-async", "Asynchronous JavaScript", "Promises, async/await and fetch.",
         "JavaScript runs on a single thread with an event loop. Asynchronous work returns a Promise that settles "
         "later.\n\n"
         "`async` marks a function that returns a promise; `await` pauses it until a promise settles. This reads "
         "like synchronous code but does not block the thread.\n\n"
         "Always wrap `await` in `try/catch`, or the rejection becomes an unhandled promise rejection. Use "
         "`Promise.all` for independent concurrent work.",
         "async function loadUser(id) {\n  try {\n    const response = await fetch(`/api/users/${id}`);\n    if (!response.ok) throw new Error(`HTTP ${response.status}`);\n    return await response.json();\n  } catch (error) {\n    console.error('failed to load', id, error.message);\n    return null;\n  }\n}\n\nasync function loadAll(ids) {\n  return Promise.all(ids.map(loadUser));\n}",
         "Fetch a public JSON API and render three fields from the response, with error handling."),
    ],
    "cpp": [
        ("cpp-basics", "C++ Basics", "Types, streams and functions.",
         "C++ is statically typed with manual memory management and zero-cost abstractions. `int` is typically "
         "32-bit; use `<cstdint>` types like `int64_t` when the exact width matters.\n\n"
         "`std::cout` with `<<` writes to standard output; `std::cin` with `>>` reads. Prefer `std::string` over "
         "`char*` in modern code.\n\n"
         "Compile with warnings on: `g++ -Wall -Wextra -std=c++20 main.cpp`.",
         "#include <iostream>\n#include <string>\n#include <vector>\n#include <numeric>\n\nint main() {\n    std::string name = \"EngineVerse\";\n    std::vector<int> marks = {72, 85, 91, 68};\n\n    int total = std::accumulate(marks.begin(), marks.end(), 0);\n    double average = static_cast<double>(total) / marks.size();\n\n    std::cout << name << \": average \" << average\n              << \" over \" << marks.size() << \" assessments\" << std::endl;\n    return 0;\n}",
         "Read five integers from standard input and print their sum and average."),
        ("cpp-memory", "Pointers and Memory", "References, pointers and RAII.",
         "A pointer holds an address; a reference is an alias that cannot be reseated or null. Prefer references "
         "unless you genuinely need nullability or reseating.\n\n"
         "Manual `new`/`delete` is the source of most C++ bugs. RAII - acquiring a resource in a constructor and "
         "releasing it in a destructor - makes cleanup automatic and exception safe.\n\n"
         "Use `std::vector` instead of raw arrays, `std::unique_ptr` for exclusive ownership and "
         "`std::shared_ptr` only when ownership is genuinely shared.",
         "#include <iostream>\n#include <memory>\n#include <vector>\n\nclass Buffer {\npublic:\n    explicit Buffer(size_t n) : data_(n, 0) {\n        std::cout << \"allocated \" << n << std::endl;\n    }\n    ~Buffer() { std::cout << \"released\" << std::endl; }\n    size_t size() const { return data_.size(); }\nprivate:\n    std::vector<int> data_;\n};\n\nint main() {\n    int value = 42;\n    int& ref = value;          // reference: cannot be null\n    int* ptr = &value;         // pointer: holds the address\n    std::cout << ref << \" \" << *ptr << std::endl;\n\n    auto buffer = std::make_unique<Buffer>(10);\n    std::cout << \"size \" << buffer->size() << std::endl;\n    // buffer is released automatically at end of scope\n    return 0;\n}",
         "Write a function that swaps two integers using references, then one using pointers."),
        ("cpp-classes", "Classes and Templates", "Encapsulation and generic programming.",
         "Classes bundle data with methods. Mark methods that do not modify state `const` - it documents intent "
         "and lets you call them on const objects.\n\n"
         "The Rule of Five: if you need a custom destructor, copy constructor, copy assignment, move constructor "
         "or move assignment, you probably need all five. Most classes need none because the defaults are correct.\n\n"
         "Templates provide compile-time generic programming with zero runtime cost.",
         "#include <iostream>\n#include <string>\n#include <vector>\n\ntemplate <typename T>\nclass Stack {\npublic:\n    void push(const T& value) { items_.push_back(value); }\n    T pop() {\n        T top = items_.back();\n        items_.pop_back();\n        return top;\n    }\n    bool empty() const { return items_.empty(); }\n    size_t size() const { return items_.size(); }\nprivate:\n    std::vector<T> items_;\n};\n\nint main() {\n    Stack<int> numbers;\n    numbers.push(1);\n    numbers.push(2);\n    numbers.push(3);\n    while (!numbers.empty()) std::cout << numbers.pop() << \" \";\n    std::cout << std::endl;\n\n    Stack<std::string> words;\n    words.push(\"alpha\");\n    std::cout << words.pop() << std::endl;\n    return 0;\n}",
         "Write a templated `max_of` function that works for any comparable type."),
    ],
    "c": [
        ("c-basics", "C Basics", "Types, I/O and control flow.",
         "C is small, close to the machine and the language in which operating systems and interpreters are "
         "written. Every C programmer must manage memory explicitly.\n\n"
         "`printf` and `scanf` use format specifiers: `%d` int, `%f` double, `%s` string, `%c` char. A mismatch "
         "between specifier and argument is undefined behaviour, not an error message.\n\n"
         "Compile with `gcc -Wall -Wextra -std=c11 main.c` and treat every warning as an error.",
         "#include <stdio.h>\n\nint main(void) {\n    int marks[5] = {72, 85, 91, 68, 79};\n    int total = 0;\n\n    for (int i = 0; i < 5; i++) {\n        total += marks[i];\n    }\n\n    double average = (double) total / 5;\n    printf(\"Total: %d\\n\", total);\n    printf(\"Average: %.2f\\n\", average);\n    return 0;\n}",
         "Read five integers and print the largest, without using an array."),
        ("c-pointers", "Pointers and Arrays", "Addresses, dereferencing and pointer arithmetic.",
         "A pointer holds the address of a value. `&x` takes an address; `*p` dereferences it.\n\n"
         "An array name decays to a pointer to its first element, so `a[i]` is defined as `*(a + i)`. This is why "
         "C cannot detect array bounds - it is only doing address arithmetic.\n\n"
         "`malloc` allocates on the heap and returns `void*`; `free` releases it. Every `malloc` needs exactly one "
         "`free`, and using memory after freeing it is undefined behaviour.",
         "#include <stdio.h>\n#include <stdlib.h>\n\nvoid swap(int* a, int* b) {\n    int temp = *a;\n    *a = *b;\n    *b = temp;\n}\n\nint main(void) {\n    int x = 3, y = 7;\n    printf(\"before: %d %d\\n\", x, y);\n    swap(&x, &y);\n    printf(\"after:  %d %d\\n\", x, y);\n\n    int n = 5;\n    int* buffer = malloc(n * sizeof(int));\n    if (buffer == NULL) return 1;\n\n    for (int i = 0; i < n; i++) buffer[i] = i * i;\n    for (int i = 0; i < n; i++) printf(\"%d \", buffer[i]);\n    printf(\"\\n\");\n\n    free(buffer);\n    return 0;\n}",
         "Write `int string_length(const char* s)` using pointer arithmetic, not the subscript operator."),
        ("c-structs", "Structures and Dynamic Memory", "Grouping data and building real structures.",
         "A `struct` groups named fields. Pass large structs by pointer to avoid copying; mark the parameter "
         "`const` if the function does not modify it.\n\n"
         "A singly linked list is the classic exercise that teaches pointers properly: you must handle the empty "
         "list, single node, head insertion and tail deletion as separate cases.\n\n"
         "Run your program under Valgrind or with `-fsanitize=address` to catch leaks and invalid accesses.",
         "#include <stdio.h>\n#include <stdlib.h>\n\ntypedef struct Node {\n    int value;\n    struct Node* next;\n} Node;\n\nNode* push_front(Node* head, int value) {\n    Node* node = malloc(sizeof(Node));\n    if (node == NULL) return head;\n    node->value = value;\n    node->next = head;\n    return node;\n}\n\nvoid print_list(const Node* head) {\n    while (head != NULL) {\n        printf(\"%d -> \", head->value);\n        head = head->next;\n    }\n    printf(\"NULL\\n\");\n}\n\nvoid free_list(Node* head) {\n    while (head != NULL) {\n        Node* next = head->next;\n        free(head);\n        head = next;\n    }\n}\n\nint main(void) {\n    Node* list = NULL;\n    for (int i = 1; i <= 5; i++) list = push_front(list, i);\n    print_list(list);\n    free_list(list);\n    return 0;\n}",
         "Add an `append` function that adds to the end, and a `reverse` function that reverses in place."),
    ],
}

# =============================================================================
# SITE CONFIG
# =============================================================================

SITE_CONFIG = {
    "site_name": "EngineVerse",
    "tagline": "Learn every engineering branch. Build real projects. Get placed.",
    "description": (
        "EngineVerse is a structured learning platform for engineering students and working professionals. "
        "Interactive notes with derivations, daily practice problems, a coding judge, guided real-world projects, "
        "spaced-repetition revision and a placement preparation path - across every engineering branch."
    ),
    "support_email": "support@engineverse.local",
    "theme": "dark",
    "free_tier_note": (
        "All core learning content - notes, practice problems, coding problems, projects, flashcards and formulas "
        "- is free and always will be. Premium covers optional extras such as certificates and unlimited AI tutor "
        "conversations, never the education itself."
    ),
    "accent_color": "#4f7cff",
    "accent_color_2": "#38bdf8",
    "accent_color_3": "#a78bfa",
    "announcement": "",
    "maintenance_mode": "0",
    "registration_open": "1",
}

# =============================================================================
# BADGES
# =============================================================================

BADGES = [
    ("first-step", "First Step", "Read your first topic", "spark", "#4f7cff", "topics_read", 1),
    ("ten-topics", "Getting Started", "Read ten topics", "book", "#38bdf8", "topics_read", 10),
    ("fifty-topics", "Scholar", "Read fifty topics", "graduation", "#a78bfa", "topics_read", 50),
    ("first-solve", "First Blood", "Solve your first coding problem", "code", "#22c55e", "problems_solved", 1),
    ("ten-solves", "Problem Solver", "Solve ten coding problems", "code", "#22c55e", "problems_solved", 10),
    ("fifty-solves", "Algorithmist", "Solve fifty coding problems", "trophy", "#f59e0b", "problems_solved", 50),
    ("streak-7", "Week Warrior", "Maintain a seven day streak", "flame", "#ef4444", "streak", 7),
    ("streak-30", "Consistent", "Maintain a thirty day streak", "flame", "#ef4444", "streak", 30),
    ("streak-100", "Century Club", "Maintain a hundred day streak", "crown", "#f59e0b", "streak", 100),
    ("first-project", "Builder", "Complete your first project", "wrench", "#0ea5e9", "projects_done", 1),
    ("quiz-master", "Quiz Master", "Answer fifty practice questions correctly", "target", "#8b5cf6", "questions_correct", 50),
    ("night-owl", "Night Owl", "Study after midnight", "moon", "#6366f1", "night_sessions", 1),
]

# =============================================================================
# PLANS
# =============================================================================

PLANS = [
    ("free", "Free", 0, "Everything a student needs to learn and practise.",
     ["All notes and topics across every branch", "Daily practice problems", "All coding problems and the judge",
      "All projects and roadmaps", "Flashcards and formula centre", "Community discussions", "Portfolio page"],
     1),
    ("pro", "Pro", 299, "For students preparing for placements, with unlimited AI assistance.",
     ["Everything in Free", "Unlimited AI tutor conversations", "Verified certificates of completion",
      "Mock interview question banks", "Advanced system design track", "Ad-free experience", "Priority support"],
     0),
    ("team", "Institution", 0, "For colleges and training teams. Contact us for pricing.",
     ["Everything in Pro for every member", "Faculty dashboard with cohort analytics",
      "Custom curriculum mapping to your university", "Bulk student onboarding", "Progress reporting and exports"],
     0),
]
