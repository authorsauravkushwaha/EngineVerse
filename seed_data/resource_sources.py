"""The resource library: curated sources, expanded to cover every subject.

Before this module existed, 53 of the 73 seeded subjects had no video, book or
resource at all, and 55 had no flashcards. A learner who opened "Hydraulics" or
"Compiler Design" found an empty shelf.

The design constraint is honesty. A dead link is worse than no link, and a deep
link to one specific lecture rots within a semester — so the URLs here are kept
to host roots, official documentation indexes and search endpoints, all of
which are stable on a timescale of years rather than weeks. Where a subject
genuinely needs "find me a course on this", the resource *is* a search over a
trusted catalogue, and the description says so rather than pretending to be a
curated lecture.

That trade buys two things: the URL surface stays small enough to actually
check, and `scripts/check_links.py` can verify every one of them in a single
run. CI runs it, so a link that dies fails the build instead of quietly
becoming a dead button.

URLs are grouped so a reader can see at a glance what each entry is:

    OFFICIAL     language, database and standards documentation
    TOOLS        simulators, calculators, visualisers
    TEXTBOOKS    open-access textbooks and course material
    CATALOGUES   places to go looking for a course on a subject
"""

from __future__ import annotations

from urllib.parse import quote_plus

# ---------------------------------------------------------------------------
# Curated sources. Every URL is a host root or a long-lived index page.
# ---------------------------------------------------------------------------

# key: (title, url, kind, level, description)
SOURCES: dict[str, tuple[str, str, str, str, str]] = {
    # ---- official documentation -------------------------------------------
    "python-docs": ("Python documentation", "https://docs.python.org/3/", "documentation", "beginner",
                    "The authoritative reference. Read the tutorial end to end once, then keep the library "
                    "reference bookmarked rather than memorising it."),
    "java-learn": ("Official Java learning path", "https://dev.java/learn/", "documentation", "beginner",
                   "Oracle's own structured Java course, kept current with the language releases. The right "
                   "place to start before any third-party tutorial."),
    "cppreference": ("cppreference", "https://en.cppreference.com/w/", "documentation", "intermediate",
                     "The reference the compiler writers read. Precise, standards-accurate, and the fastest "
                     "way to settle a question about what C++ actually guarantees."),
    "mdn": ("MDN Web Docs", "https://developer.mozilla.org/", "documentation", "beginner",
            "The reference for the web platform, written and maintained by the people who build the browsers. "
            "Treat it as the specification you can actually read."),
    "postgres-docs": ("PostgreSQL documentation", "https://www.postgresql.org/docs/", "documentation", "intermediate",
                      "The manual every serious SQL user ends up living in. The chapters on indexes, query "
                      "planning and transactions are worth reading straight through."),
    "mysql-docs": ("MySQL reference manual", "https://dev.mysql.com/doc/", "documentation", "beginner",
                   "The reference for the database most production systems still run, including the InnoDB "
                   "storage-engine chapters that explain locking and isolation."),
    "git-book": ("Pro Git (free book)", "https://git-scm.com/book/en/v2", "documentation", "beginner",
                 "The canonical Git book, free online. Chapters 3, 5 and 7 turn Git from a thing you type at "
                 "into a thing you understand."),
    "docker-docs": ("Docker documentation", "https://docs.docker.com/", "documentation", "intermediate",
                    "Containers explained by the people who made them. The networking and volumes sections "
                    "are where most real-world confusion actually comes from."),
    "k8s-docs": ("Kubernetes documentation", "https://kubernetes.io/docs/", "documentation", "advanced",
                 "The official guide to the container orchestrator. Read the concepts section before touching "
                 "a YAML file."),

    # ---- tools and simulators ---------------------------------------------
    "falstad": ("Falstad circuit simulator", "https://www.falstad.com/circuit/", "simulator", "beginner",
                "Circuits you can build and watch in a browser, with current animated as moving dots. The "
                "fastest way to develop intuition for what a circuit is doing before solving it by hand."),
    "circuitverse": ("CircuitVerse digital logic simulator", "https://circuitverse.org/", "simulator", "beginner",
                     "Drag-and-drop digital logic in the browser, including flip-flops, counters and simple "
                     "processors. Ideal for testing a design before you commit it to an exam answer."),
    "phet": ("PhET interactive simulations", "https://phet.colorado.edu/", "simulator", "beginner",
             "Free physics, chemistry and mathematics simulations from the University of Colorado Boulder. "
             "Each one isolates a single phenomenon so you can vary one variable and watch the consequence."),
    "desmos": ("Desmos graphing calculator", "https://www.desmos.com/calculator", "tool", "beginner",
               "Graph anything in a keystroke. The habit worth building is plotting a function the moment you "
               "meet it — half of all 'surprising' calculus results stop being surprising once you see them."),
    "geogebra": ("GeoGebra", "https://www.geogebra.org/", "tool", "beginner",
                 "Dynamic geometry and algebra. Drag a point and watch the construction hold together, which "
                 "teaches invariants far better than a static figure."),
    "wolfram-alpha": ("Wolfram|Alpha", "https://www.wolframalpha.com/", "tool", "beginner",
                      "Computes integrals, solves equations and shows the steps. Use it to check your work, "
                      "never to do your work — the steps are the part you are being examined on."),
    "symbolab": ("Symbolab step-by-step solver", "https://www.symbolab.com/", "tool", "beginner",
                 "Another step-by-step solver, often clearer than Wolfram for limits and differential "
                 "equations. Cross-checking two solvers is a good way to catch a copied typo."),
    "python-tutor": ("Python Tutor visualiser", "https://pythontutor.com/", "tool", "beginner",
                     "Steps through your program frame by frame, drawing every reference. The single most "
                     "useful tool for understanding recursion, pointers and how the call stack actually works."),
    "visualgo": ("VisuAlgo algorithm visualiser", "https://visualgo.net/", "tool", "beginner",
                 "Data structures and algorithms animated step by step, built at the National University of "
                 "Singapore. Watch a rotation happen before you try to code one."),
    "engineering-toolbox": ("The Engineering ToolBox", "https://www.engineeringtoolbox.com/", "tool", "beginner",
                            "Tables of material properties, coefficients, standards and unit conversions. The "
                            "bookmarked reference behind most quick engineering estimates."),
    "nist-webbook": ("NIST Chemistry WebBook", "https://webbook.nist.gov/chemistry/", "dataset", "intermediate",
                     "Thermodynamic and phase data from the US National Institute of Standards and Technology. "
                     "Cite this rather than a textbook table when the number matters."),
    "pubchem": ("PubChem compound database", "https://pubchem.ncbi.nlm.nih.gov/", "dataset", "beginner",
                "Structures, properties and safety data for over 100 million chemical compounds, from the US "
                "National Institutes of Health."),

    # ---- open textbooks and course material -------------------------------
    "openstax-math": ("OpenStax mathematics textbooks", "https://openstax.org/subjects/math", "course", "beginner",
                      "Peer-reviewed, openly licensed university textbooks: Calculus I–III, statistics, "
                      "precalculus. Free forever, and the standard open alternative to a paid calculus text."),
    "openstax-science": ("OpenStax science textbooks", "https://openstax.org/subjects/science", "course", "beginner",
                         "Openly licensed University Physics, Chemistry and Biology at full university level. "
                         "Downloadable as PDF, so it works on a phone with no signal."),
    "libretexts-eng": ("Engineering LibreTexts", "https://eng.libretexts.org/", "course", "beginner",
                       "An open, editable engineering textbook library maintained by a consortium of "
                       "universities. Strong on mechanical, civil and chemical fundamentals."),
    "libretexts-chem": ("Chemistry LibreTexts", "https://chem.libretexts.org/", "course", "beginner",
                        "Open chemistry texts from general chemistry through reaction engineering, written and "
                        "reviewed by faculty."),
    "libretexts-math": ("Mathematics LibreTexts", "https://math.libretexts.org/", "course", "beginner",
                        "Open mathematics library covering the whole undergraduate sequence, including "
                        "differential equations and complex analysis."),
    "pauls-notes": ("Paul's Online Math Notes", "https://tutorial.math.lamar.edu/", "course", "beginner",
                    "Lamar University's free calculus and differential-equations notes. Famous for working "
                    "every example through in full rather than skipping the algebra."),
    "ostep": ("Operating Systems: Three Easy Pieces", "https://pages.cs.wisc.edu/~remzi/OSTEP/", "course", "intermediate",
              "The free, complete textbook used in real university operating-systems courses. Virtualisation, "
              "concurrency and persistence, explained with the actual code."),
    "osdev": ("OSDev wiki", "https://wiki.osdev.org/", "course", "advanced",
              "Community reference for writing an operating system from nothing. Dense, occasionally "
              "argumentative, and the best free resource on what happens below the abstraction."),
    "d2l": ("Dive into Deep Learning", "https://d2l.ai/", "course", "advanced",
            "An interactive deep-learning textbook with runnable code beside every equation, from the authors "
            "who built MXNet. Mathematics and implementation on the same page."),
    "neural-nets": ("Neural Networks and Deep Learning", "https://neuralnetworksanddeeplearning.com/", "course", "intermediate",
                    "Michael Nielsen's free book. Still the clearest derivation of backpropagation anywhere, "
                    "and short enough to finish in a weekend."),
    "crafting-interpreters": ("Crafting Interpreters", "https://craftinginterpreters.com/", "course", "advanced",
                              "Bob Nystrom's free book on building a programming language twice: a tree-walk "
                              "interpreter, then a bytecode VM. The best way to make compilers stop being magic."),
    "missing-semester": ("The Missing Semester of Your CS Education", "https://missing.csail.mit.edu/", "course", "beginner",
                         "MIT's course on the tools no curriculum teaches: the shell, Git, editors, debugging "
                         "and regular expressions. Six lectures that pay for themselves immediately."),
    "learnxiny": ("Learn X in Y minutes", "https://learnxinyminutes.com/", "course", "beginner",
                  "A single annotated page per language. The fastest way to read a language you half-know "
                  "before you have to use it."),
    "sqlbolt": ("SQLBolt interactive SQL lessons", "https://sqlbolt.com/", "course", "beginner",
                "SQL taught in the browser with a real database to query at every step. Finish it before you "
                "read anything about query optimisation."),
    "use-the-index-luke": ("Use The Index, Luke", "https://use-the-index-luke.com/", "course", "intermediate",
                           "How SQL indexing and performance actually work, written for developers rather than "
                           "database administrators. The section on anatomy of an index is the whole subject."),
    "caniuse": ("Can I use — browser support tables", "https://caniuse.com/", "tool", "intermediate",
                "Which browser supports which web feature, with the version numbers and the market share that "
                "makes it matter. Check it before you write a fallback you may not need."),
    "roadmap-sh": ("roadmap.sh developer roadmaps", "https://roadmap.sh/", "course", "beginner",
                   "Community-maintained skill maps for each engineering role, showing what to learn in what "
                   "order and why. Useful as a cross-check on your own plan."),
    "refactoring-guru": ("Refactoring Guru", "https://refactoring.guru/", "course", "intermediate",
                         "Every classic design pattern with structure diagrams, pseudo-code and an honest "
                         "account of when the pattern is the wrong choice."),
    "build-your-own-x": ("Build Your Own X", "https://github.com/codecrafters-io/build-your-own-x", "course", "advanced",
                         "Curated tutorials for building real systems from scratch: databases, compilers, "
                         "operating systems, blockchains, search engines. The best kind of project list."),
    "coding-interview-university": ("Coding Interview University", "https://github.com/jwasham/coding-interview-university",
                                    "course", "intermediate",
                                    "A complete self-study plan for a software-engineering interview, with the "
                                    "order and the time estimates worked out for you."),
    "system-design-primer": ("The System Design Primer", "https://github.com/donnemartin/system-design-primer",
                             "course", "advanced",
                             "How large systems are designed, with worked examples. The standard free "
                             "preparation for a system-design interview."),
    "ossu": ("Open Source Society University", "https://github.com/ossu/computer-science", "course", "beginner",
             "A complete computer-science degree assembled from free courses, sequenced with prerequisites. "
             "Useful as a structure even if you substitute your own materials."),
    "cs-video-courses": ("Computer science video courses", "https://github.com/Developer-Y/cs-video-courses",
                         "playlist", "beginner",
                         "A maintained index of university computer-science courses with free video, organised "
                         "by subject. A good way to find a full lecture series rather than one clip."),
    "the-algorithms": ("The Algorithms repository", "https://github.com/TheAlgorithms/Python", "course", "beginner",
                       "Every standard algorithm implemented and readable in one place. Read the implementation "
                       "after you have written your own — comparing the two is where the learning happens."),

    # ---- security ----------------------------------------------------------
    "owasp": ("OWASP", "https://owasp.org/", "documentation", "intermediate",
              "The Open Web Application Security Project. The Top Ten is the industry's shared vocabulary for "
              "what actually gets exploited, and the testing guide is genuinely practical."),
    "cryptopals": ("The Cryptopals crypto challenges", "https://cryptopals.com/", "course", "advanced",
                   "Cryptography learned by breaking it, one challenge at a time. Harder than any lecture and "
                   "worth considerably more."),

    # ---- networking standards ----------------------------------------------
    "rfc-http": ("RFC 9110 — HTTP Semantics", "https://datatracker.ietf.org/doc/html/rfc9110", "paper", "advanced",
                 "The current definition of HTTP: methods, status codes, headers and caching. Dense but "
                 "authoritative, and shorter than you would expect."),
    "rfc-tcp": ("RFC 9293 — Transmission Control Protocol", "https://datatracker.ietf.org/doc/html/rfc9293", "paper", "advanced",
                "TCP, consolidated. The state-transition diagram in section 3 is the whole protocol on one page."),
    "rfc-ip": ("RFC 791 — Internet Protocol", "https://datatracker.ietf.org/doc/html/rfc791", "paper", "intermediate",
               "IPv4 as originally specified. Forty-five years old and still the document that explains what "
               "an IP packet is."),
    "rfc-dns": ("RFC 1035 — Domain Names", "https://datatracker.ietf.org/doc/html/rfc1035", "paper", "advanced",
                "The DNS specification. Read it once and resolvers stop being mysterious."),
    "rfc-tls": ("RFC 8446 — TLS 1.3", "https://datatracker.ietf.org/doc/html/rfc8446", "paper", "advanced",
                "The transport security protocol, trimmed to a single round trip. Compare it with TLS 1.2 to "
                "see exactly which attacks the simplification removes."),
    "rfc-private": ("RFC 1918 — Private address space", "https://datatracker.ietf.org/doc/html/rfc1918", "paper", "beginner",
                    "One page that explains why your home network is 192.168.x.x and why that never collides "
                    "with the internet."),
    "beej-net": ("Beej's Guide to Network Programming", "https://beej.us/guide/bgnet/", "course", "intermediate",
                 "Sockets taught properly, in C, with working examples and a sense of humour. The classic "
                 "introduction and still free after two decades."),
}

# ---------------------------------------------------------------------------
# Which curated sources reach which discipline.
# ---------------------------------------------------------------------------

DISCIPLINE_SOURCES: dict[str, list[str]] = {
    "core": ["openstax-science", "phet", "wolfram-alpha"],
    "cse": ["missing-semester", "learnxiny", "python-tutor"],
    "electronics": ["falstad", "circuitverse", "phet"],
    "mechanical": ["engineering-toolbox", "libretexts-eng", "phet"],
    "civil": ["engineering-toolbox", "libretexts-eng"],
    "chemical": ["libretexts-chem", "nist-webbook", "pubchem"],
    "bio": ["libretexts-chem", "pubchem"],
    "other": ["libretexts-eng", "phet"],
}

# Subject-specific additions. Only where there is something genuinely better
# than the discipline default — a shared tool repeated 73 times is noise.
SUBJECT_SOURCES: dict[str, list[str]] = {
    # first-year core
    "engineering-mathematics-1": ["openstax-math", "pauls-notes", "desmos", "libretexts-math"],
    "engineering-mathematics-2": ["openstax-math", "pauls-notes", "libretexts-math"],
    "engineering-mathematics-3": ["pauls-notes", "libretexts-math", "desmos"],
    "discrete-mathematics": ["openstax-math", "libretexts-math"],
    "engineering-physics": ["openstax-science", "phet"],
    "engineering-chemistry": ["libretexts-chem", "nist-webbook", "pubchem"],
    "engineering-drawing": ["geogebra"],
    "engineering-graphics": ["geogebra"],
    "engineering-mechanics-fy": ["libretexts-eng", "phet"],
    "workshop-practice": ["engineering-toolbox"],
    "communication-skills": ["missing-semester"],
    "environmental-studies": ["nist-webbook"],
    "basic-electrical": ["falstad", "circuitverse"],
    "basic-electronics": ["falstad", "circuitverse"],
    "programming-fundamentals": ["python-docs", "java-learn", "python-tutor", "learnxiny"],

    # computer science
    "data-structures-algorithms": ["visualgo", "the-algorithms", "coding-interview-university"],
    "oops": ["refactoring-guru", "java-learn"],
    "operating-systems": ["ostep", "osdev"],
    "dbms": ["postgres-docs", "mysql-docs", "sqlbolt", "use-the-index-luke"],
    "computer-networks": ["beej-net", "rfc-ip", "rfc-tcp", "rfc-dns"],
    "web-technologies": ["mdn", "caniuse"],
    "software-engineering": ["refactoring-guru", "git-book"],
    "theory-of-computation": ["crafting-interpreters"],
    "compiler-design": ["crafting-interpreters"],
    "computer-architecture": ["osdev"],
    "cryptography-security": ["owasp", "cryptopals", "rfc-tls"],
    "cloud-computing-subject": ["docker-docs", "k8s-docs"],
    "machine-learning": ["d2l", "neural-nets"],
    "deep-learning": ["d2l", "neural-nets"],
    "data-science-foundations": ["openstax-math", "d2l"],
    "digital-logic-design": ["circuitverse"],

    # electronics and electrical
    "circuit-theory": ["falstad"],
    "analog-circuits": ["falstad"],
    "digital-electronics": ["circuitverse"],
    "electronic-devices": ["falstad"],
    "signals-systems": ["phet", "desmos"],
    "dsp": ["desmos"],
    "communication-systems": ["phet"],
    "control-systems-subject": ["desmos"],
    "electromagnetic-fields": ["phet", "desmos"],
    "measurements-instrumentation": ["engineering-toolbox"],
    "microprocessors": ["circuitverse", "osdev"],
    "power-electronics": ["falstad"],
    "power-systems": ["engineering-toolbox"],
    "electrical-machines-1": ["phet", "engineering-toolbox"],
    "electrical-machines-2": ["phet", "engineering-toolbox"],
    "vlsi-design-subject": ["circuitverse"],

    # mechanical
    "thermodynamics": ["nist-webbook", "engineering-toolbox"],
    "heat-transfer": ["engineering-toolbox"],
    "fluid-mechanics": ["engineering-toolbox", "phet"],
    "strength-of-materials": ["engineering-toolbox", "libretexts-eng"],
    "theory-of-machines": ["engineering-toolbox"],
    "machine-design": ["engineering-toolbox"],
    "manufacturing-processes": ["engineering-toolbox"],
    "ic-engines": ["engineering-toolbox"],
    "refrigeration-ac": ["nist-webbook", "engineering-toolbox"],
    "cad-cam": ["geogebra"],

    # civil
    "structural-analysis": ["libretexts-eng", "engineering-toolbox"],
    "rc-design": ["libretexts-eng"],
    "concrete-technology": ["libretexts-eng"],
    "soil-mechanics": ["libretexts-eng"],
    "hydraulics": ["engineering-toolbox", "phet"],
    "surveying": ["engineering-toolbox"],
    "transportation-engineering-subject": ["engineering-toolbox"],
    "estimating-costing": ["engineering-toolbox"],
    "environmental-engineering-subject": ["nist-webbook"],

    # chemical
    "chemical-thermodynamics": ["nist-webbook"],
    "reaction-engineering": ["libretexts-chem"],
    "mass-transfer": ["libretexts-chem"],
    "heat-transfer-operations": ["engineering-toolbox"],
    "fluid-flow-operations": ["engineering-toolbox"],
    "process-calculations": ["libretexts-chem", "nist-webbook"],
    "materials-science": ["libretexts-eng", "nist-webbook"],
}

#: Two catalogue searches every subject gets. A search is not a curated
#: lecture, and the generated description says so — but a search over a trusted
#: catalogue is honest, it does not rot, and it always finds the current
#: course rather than the one that was popular when the seed was written.
CATALOGUES: list[tuple[str, str, str]] = [
    ("MIT OpenCourseWare search: {subject}", "https://ocw.mit.edu/search/?q={q}",
     "Free lecture notes, assignments and exams from MIT, searched for {subject}. Nothing here is curated "
     "by EngineVerse: it is the live MIT catalogue, which is why it finds courses that are current rather "
     "than courses that were popular when this page was written."),
    ("Wikipedia and Wikibooks: {subject}", "https://en.wikipedia.org/wiki/Special:Search?search={q}",
     "A starting point, not a substitute for the notes. Use it for the vocabulary and the history, then go "
     "to the textbook for the derivations."),
]


def build(subjects: list[dict]) -> list[tuple]:
    """Expand the registry into ``RESOURCES``-shaped rows for every subject.

    ``subjects`` is ``[{"slug": ..., "name": ..., "category": ...}]``. Returns
    rows in the same shape as ``library_data.RESOURCES`` so the seeder needs no
    special case.

    Titles carry the subject name, which is what keeps them unique: the same
    simulator legitimately serves ten subjects, and ``resources.slug`` is
    derived from the title and is unique in the schema. A repeated title would
    collide and ``ON CONFLICT DO NOTHING`` would drop the row silently — a
    subject would lose a resource with nothing anywhere to say so.
    """
    rows: list[tuple] = []
    for subject in subjects:
        slug, name = subject["slug"], subject["name"]
        discipline = subject.get("category") or "core"

        keys: list[str] = list(DISCIPLINE_SOURCES.get(discipline, []))
        for key in SUBJECT_SOURCES.get(slug, []):
            if key not in keys:
                keys.append(key)

        for key in keys:
            entry = SOURCES.get(key)
            if not entry:
                # Deliberately loud. A typo'd key skipped silently is a subject
                # that quietly loses a resource, which is the same failure
                # mode as the dropped 3D streamlines: nothing errors, and the
                # page just has less on it than it should.
                raise KeyError(f"subject {slug!r} references unknown source {key!r}")
            title, url, kind, level, description = entry
            rows.append((f"{title} — {name}", url, kind, kind, slug, level,
                         f"{description} Listed under {name}."))

        query = quote_plus(name)
        for title, url, description in CATALOGUES:
            rows.append((title.format(subject=name), url.format(q=query), "course", "course", slug,
                         "beginner", description.format(subject=name)))
    return rows


# ---------------------------------------------------------------------------
# Videos. `videos.url` is a course series or a channel, not a single clip: a
# deep link to one lecture is the fastest-rotting URL on the internet, and a
# dead video link is the most visible kind of dead button.
# ---------------------------------------------------------------------------

# key: (title, channel, url, level, why)
VIDEO_SOURCES: dict[str, tuple[str, str, str, str, str]] = {
    "khan": ("Khan Academy", "Khan Academy", "https://www.youtube.com/@khanacademy", "beginner",
             "Short worked examples, one idea per video, with no step skipped. The best first pass at any "
             "quantitative subject."),
    "3b1b": ("3Blue1Brown", "3Blue1Brown", "https://www.youtube.com/@3blue1brown", "beginner",
             "Visual explanations of the ideas underneath the algebra. Watch one of these before you learn a "
             "topic formally and the notation lands much faster."),
    "mit-ocw": ("MIT OpenCourseWare lectures", "MIT OpenCourseWare", "https://www.youtube.com/@mitocw", "intermediate",
                "Full university lectures, unedited. Slower and harder than a tutorial channel, and that is the "
                "point: this is the real course."),
    "freecodecamp": ("freeCodeCamp full courses", "freeCodeCamp", "https://www.youtube.com/@freecodecamp", "beginner",
                     "Multi-hour, single-topic courses with no ads and no paywall. Depth that normally costs money."),
    "computerphile": ("Computerphile", "Computerphile", "https://www.youtube.com/@Computerphile", "beginner",
                      "University of Nottingham academics explaining computing ideas on a whiteboard. Good for "
                      "the 'why does this exist at all' question."),
    "organic": ("The Organic Chemistry Tutor", "The Organic Chemistry Tutor",
                "https://www.youtube.com/@TheOrganicChemistryTutor", "beginner",
                "Thousands of worked problems across chemistry, physics and mathematics. The reliable place to "
                "go when you need the same type of problem done five more times."),
    "efficient": ("The Efficient Engineer", "The Efficient Engineer",
                  "https://www.youtube.com/@TheEfficientEngineer", "intermediate",
                  "Mechanical and civil concepts animated properly. Unusually good at showing *why* a structure "
                  "or a mechanism behaves the way it does."),
    "practical": ("Practical Engineering", "Practical Engineering",
                  "https://www.youtube.com/@PracticalEngineeringChannel", "beginner",
                  "A working civil engineer on real infrastructure: why the drainage failed, what the retaining "
                  "wall is actually doing. The field context textbooks leave out."),
    "veritasium": ("Veritasium", "Veritasium", "https://www.youtube.com/@veritasium", "beginner",
                   "Physics explained through demonstration and experiment rather than derivation. Useful for "
                   "building the intuition a formula then compresses."),
    "numberphile": ("Numberphile", "Numberphile", "https://www.youtube.com/@numberphile", "beginner",
                    "Mathematicians talking about the problems they find interesting. Not a course, but the "
                    "best way to find out that mathematics has a culture."),
}

VIDEO_DISCIPLINE: dict[str, list[str]] = {
    # Four per category. Three was the target and four leaves room for a subject
    # that overrides one of them without dropping below the floor.
    "core": ["khan", "mit-ocw", "ilecture", "nptel"],
    "cse": ["freecodecamp", "computerphile", "ben-eater", "neso"],
    "electronics": ["mit-ocw", "khan", "eevblog", "neso"],
    "mechanical": ["efficient", "mit-ocw", "brunton", "real-engineering"],
    "civil": ["practical", "efficient", "structure-free", "ilecture"],
    "chemical": ["organic", "mit-ocw", "ilecture", "nptel"],
    "bio": ["organic", "khan", "ilecture", "nptel"],
    "other": ["khan", "mit-ocw", "ilecture", "nptel"],
}

VIDEO_SUBJECT: dict[str, list[str]] = {
    "engineering-mathematics-1": ["3b1b"],
    "engineering-mathematics-2": ["3b1b"],
    "engineering-mathematics-3": ["3b1b"],
    "discrete-mathematics": ["3b1b", "numberphile"],
    "engineering-physics": ["veritasium"],
    "engineering-chemistry": ["organic"],
    "chemical-thermodynamics": ["organic"],
    "process-calculations": ["organic"],
    "reaction-engineering": ["organic"],
    "machine-learning": ["3b1b"],
    "deep-learning": ["3b1b"],
    "data-science-foundations": ["3b1b"],
    "structural-analysis": ["efficient"],
    "strength-of-materials": ["efficient"],
    "theory-of-machines": ["efficient"],
    "fluid-mechanics": ["efficient"],
    "transportation-engineering-subject": ["practical"],
    "hydraulics": ["practical"],
    "environmental-engineering-subject": ["practical"],
    "surveying": ["practical"],
}


# Every generated video used to be filed under "concept", which left the
# category filter on /videos with a single option for all 320 rows. These are
# derived from what the source actually is: a lecture series is not a teardown.
VIDEO_CATEGORY: dict[str, str] = {
    "khan": "tutorial",
    "3b1b": "visualization",
    "mit-ocw": "lecture",
    "nptel": "lecture",
    "brunton": "lecture",
    "freecodecamp": "course",
    "computerphile": "explainer",
    "veritasium": "explainer",
    "numberphile": "explainer",
    "ben-eater": "build",
    "eevblog": "teardown",
    "neso": "tutorial",
    "organic": "tutorial",
    "ilecture": "worked-example",
    "structure-free": "worked-example",
    "efficient": "application",
    "real-engineering": "application",
    "practical": "application",
}


def build_videos(subjects: list[dict]) -> list[tuple]:
    """``VIDEOS``-shaped rows for every subject, from the video registry."""
    rows: list[tuple] = []
    for subject in subjects:
        slug, name = subject["slug"], subject["name"]
        discipline = subject.get("category") or "core"
        keys = list(VIDEO_DISCIPLINE.get(discipline, []))
        for key in VIDEO_SUBJECT.get(slug, []):
            if key not in keys:
                keys.append(key)
        for key in keys:
            entry = VIDEO_SOURCES.get(key)
            if not entry:
                raise KeyError(f"subject {slug!r} references unknown video source {key!r}")
            title, channel, url, level, why = entry
            category = VIDEO_CATEGORY.get(key, "concept")
            rows.append((f"{title} — {name}", channel, url, 0, level, category, slug,
                         f"{why} Filed under {name}."))
    return rows


# ---------------------------------------------------------------------------
# Books. Only open-access or officially free titles: nothing here is a pirated
# copy, and every `legal_url` is the publisher's or the author's own page.
# ---------------------------------------------------------------------------

# key: (title, author, level, description, why_read, topics, url, access, publisher)
BOOK_SOURCES: dict[str, tuple] = {
    "openstax-calc1": ("OpenStax Calculus, Volume 1", "Gilbert Strang & Edwin Jedrysik (OpenStax)", "undergraduate",
                       "Limits, derivatives and integrals of a single variable, peer-reviewed and openly "
                       "licensed by Rice University.",
                       "The standard free replacement for a paid calculus text, and complete enough to be the "
                       "only book you use.", ["limits", "derivatives", "integrals"],
                       "https://openstax.org/details/books/calculus-volume-1", "open_access", "OpenStax"),
    "openstax-physics1": ("OpenStax University Physics, Volume 1", "Samuel Ling & Jeff Sanny (OpenStax)", "undergraduate",
                          "Mechanics, waves and thermodynamics at full university level, with worked examples.",
                          "Covers the first-year physics syllabus end to end and downloads as a PDF, so it "
                          "works with no signal.", ["mechanics", "thermodynamics", "waves"],
                          "https://openstax.org/details/books/university-physics-volume-1", "open_access", "OpenStax"),
    "openstax-chem": ("OpenStax Chemistry 2e", "Paul Flowers & Klaus Theopold (OpenStax)", "undergraduate",
                      "General chemistry from atomic structure through equilibrium and electrochemistry.",
                      "The openly licensed alternative to a first-year chemistry textbook, with the problem "
                      "sets included.", ["equilibrium", "thermochemistry", "electrochemistry"],
                      "https://openstax.org/details/books/chemistry-2e", "open_access", "OpenStax"),
    "ostep-book": ("Operating Systems: Three Easy Pieces", "Remzi & Andrea Arpaci-Dusseau", "undergraduate",
                   "Virtualisation, concurrency and persistence, taught around real code.",
                   "The free textbook used in actual university OS courses. Read the concurrency part twice.",
                   ["processes", "threads", "paging", "deadlocks"],
                   "https://pages.cs.wisc.edu/~remzi/OSTEP/", "open_access", "Arpaci-Dusseau Books"),
    "d2l-book": ("Dive into Deep Learning", "Aston Zhang, Zachary Lipton, Mu Li & Alexander Smola", "postgraduate",
                 "An interactive deep-learning textbook with runnable code beside every derivation.",
                 "The rare book where the mathematics and the implementation are on the same page.",
                 ["gradient-descent", "convolution", "attention"], "https://d2l.ai/", "open_access", "Cambridge University Press"),
    "nielsen-book": ("Neural Networks and Deep Learning", "Michael Nielsen", "undergraduate",
                     "A short, complete derivation of backpropagation and what it is actually computing.",
                     "Finish it in a weekend and backpropagation stops being a black box.",
                     ["backpropagation", "regularisation"], "https://neuralnetworksanddeeplearning.com/",
                     "open_access", "Determination Press"),
    "nystrom-book": ("Crafting Interpreters", "Robert Nystrom", "undergraduate",
                     "Building a programming language twice: a tree-walk interpreter, then a bytecode VM.",
                     "The best way to make compilers stop being magic, and free in full online.",
                     ["parsing", "bytecode", "garbage-collection"], "https://craftinginterpreters.com/",
                     "open_access", "Genever Benning"),
    "pro-git-book": ("Pro Git", "Scott Chacon & Ben Straub", "undergraduate",
                     "The complete Git book, free online and kept current with Git itself.",
                     "Chapters 3, 5 and 7 are the difference between typing Git and understanding it.",
                     ["branching", "rebasing", "history"], "https://git-scm.com/book/en/v2", "open_access", "Apress"),
    "libretexts-eng-book": ("Engineering LibreTexts library", "LibreTexts consortium", "undergraduate",
                            "An open, faculty-maintained engineering textbook library spanning statics, "
                            "materials, thermodynamics and process engineering.",
                            "Where to look when there is no single famous open textbook for your subject — "
                            "and there usually is not.", ["statics", "materials", "process"],
                            "https://eng.libretexts.org/", "open_access", "LibreTexts"),
    "libretexts-chem-book": ("Chemistry LibreTexts library", "LibreTexts consortium", "undergraduate",
                             "Open chemistry texts from general chemistry through reaction and process "
                             "engineering, written and reviewed by faculty.",
                             "Covers the chemical-engineering sequence that commercial publishers serve with "
                             "four separate expensive books.", ["reaction-engineering", "mass-transfer"],
                             "https://chem.libretexts.org/", "open_access", "LibreTexts"),
    "libretexts-math-book": ("Mathematics LibreTexts library", "LibreTexts consortium", "undergraduate",
                             "Open mathematics covering the whole undergraduate sequence including "
                             "differential equations and complex analysis.",
                             "The open alternative for the third-year mathematics that OpenStax does not yet "
                             "cover.", ["differential-equations", "complex-analysis"],
                             "https://math.libretexts.org/", "open_access", "LibreTexts"),
    "pauls-book": ("Paul's Online Math Notes", "Paul Dawkins, Lamar University", "undergraduate",
                   "Calculus and differential-equations notes that work every example through in full.",
                   "The book to read when a textbook skips the algebra you actually got stuck on.",
                   ["limits", "series", "differential-equations"], "https://tutorial.math.lamar.edu/",
                   "open_access", "Lamar University"),
}

BOOK_DISCIPLINE: dict[str, list[str]] = {
    "core": ["libretexts-eng-book", "openstax-calc1", "openstax-calc2", "hefferon-la"],
    "cse": ["libretexts-math-book", "sicp", "crafting-interpreters", "automate"],
    "electronics": ["openstax-physics1", "openstax-physics2", "allaboutcircuits", "openstax-physics3"],
    "mechanical": ["libretexts-eng-book", "libretexts-engineering", "openstax-physics1", "openstax-calc3"],
    "civil": ["libretexts-eng-book", "libretexts-engineering", "openstax-calc2", "openstax-physics1"],
    "chemical": ["libretexts-chem-book", "openstax-chem", "libretexts-engineering", "openstax-physics1"],
    "bio": ["libretexts-chem-book", "openstax-biology2", "openstax-chem", "openstax-stats"],
    "other": ["libretexts-eng-book", "openstax-calc1", "openstax-stats", "immersive-la"],
}

BOOK_SUBJECT: dict[str, list[str]] = {
    "engineering-mathematics-1": ["openstax-calc1", "pauls-book"],
    "engineering-mathematics-2": ["openstax-calc1"],
    "engineering-mathematics-3": ["pauls-book", "libretexts-math-book"],
    "engineering-physics": ["openstax-physics1"],
    "engineering-chemistry": ["openstax-chem"],
    "operating-systems": ["ostep-book"],
    "compiler-design": ["nystrom-book"],
    "theory-of-computation": ["nystrom-book"],
    "machine-learning": ["d2l-book"],
    "deep-learning": ["d2l-book", "nielsen-book"],
    "data-science-foundations": ["nielsen-book"],
    "software-engineering": ["pro-git-book"],
    "thermodynamics": ["openstax-physics1"],
    "chemical-thermodynamics": ["openstax-chem"],
}


def build_books(subjects: list[dict]) -> list[tuple]:
    """``BOOKS``-shaped rows for every subject, from the book registry."""
    rows: list[tuple] = []
    for subject in subjects:
        slug, name = subject["slug"], subject["name"]
        discipline = subject.get("category") or "core"
        keys = list(BOOK_DISCIPLINE.get(discipline, []))
        for key in BOOK_SUBJECT.get(slug, []):
            if key not in keys:
                keys.append(key)
        for key in keys:
            entry = BOOK_SOURCES.get(key)
            if not entry:
                raise KeyError(f"subject {slug!r} references unknown book source {key!r}")
            title, author, level, description, why, topics, url, access, publisher = entry
            rows.append((f"{title} — {name}", author, slug, level,
                         f"{description} Filed under {name}.", why, topics, url, access, publisher))
    return rows


def all_urls() -> list[str]:
    """Every URL this module can emit, for the link checker."""
    urls = [entry[1] for entry in SOURCES.values()]
    urls += [url.format(q="example") for _, url, _ in CATALOGUES]
    urls += [entry[2] for entry in VIDEO_SOURCES.values()]
    urls += [entry[6] for entry in BOOK_SOURCES.values()]
    return urls


# ---------------------------------------------------------------------------
# Additional sources.
#
# Added because most subjects were reaching only one book and two videos: the
# discipline maps below had one entry per category, so 67 of 73 subjects had
# fewer than three books and 53 had fewer than three videos. Every subject now
# gets at least three of each.
#
# Everything here is legally free to read or embed. Open-access textbooks
# (OpenStax, LibreTexts, and author-hosted texts released for free) and public
# lecture channels - no pirated copies of commercial books.
# ---------------------------------------------------------------------------

VIDEO_SOURCES.update({
    "nptel": ("NPTEL lecture series", "NPTEL Human Resource Development",
              "https://www.youtube.com/@nptelhrd", "intermediate",
              "Full IIT and IISc lecture courses across every engineering branch. The closest thing to "
              "attending an institute of technology for free, and aligned to the Indian syllabus."),
    "brunton": ("Steve Brunton engineering lectures", "Eigensteve",
                "https://www.youtube.com/@Eigensteve", "advanced",
                "Fluid dynamics, control theory and machine learning taught from the governing equations "
                "up. The bridge between a textbook and research."),
    "real-engineering": ("Real Engineering", "Real Engineering",
                         "https://www.youtube.com/@RealEngineering", "beginner",
                         "How structures, aircraft and power systems are actually engineered, with the "
                         "numbers shown rather than hand-waved."),
    "eevblog": ("EEVblog", "EEVblog", "https://www.youtube.com/@EEVblog", "intermediate",
                "Bench work, teardowns and measurement. The practical complement to a circuits course, "
                "and where you learn what an instrument actually does."),
    "ben-eater": ("Ben Eater", "Ben Eater", "https://www.youtube.com/@BenEater", "intermediate",
                  "A computer and a VGA driver built from discrete gates on a breadboard, one signal at a "
                  "time. Nothing about how a CPU works survives this series unexplained."),
    "neso": ("Neso Academy", "Neso Academy", "https://www.youtube.com/@nesoacademy", "beginner",
             "Short syllabus-aligned lectures for digital logic, signals and systems, networks and theory "
             "of computation."),
    "ilecture": ("Michel van Biezen worked problems", "ilectureonline",
                 "https://www.youtube.com/@ilectureonline", "beginner",
                 "Thousands of short worked problems across mathematics, physics, chemistry and "
                 "engineering. Useful when the method is clear but the algebra is not."),
    "structure-free": ("Structure Free", "Structure Free",
                       "https://www.youtube.com/@structurefree", "intermediate",
                       "Statics, mechanics of materials and structural analysis solved on paper step by "
                       "step, at the pace of a tutorial rather than a lecture."),
})

BOOK_SOURCES.update({
    "openstax-calc2": ("OpenStax Calculus, Volume 2", "Gilbert Strang & Edwin Jedrysik (OpenStax)", "undergraduate",
                       "Integration techniques, sequences, series and multivariable calculus, peer-reviewed "
                       "and openly licensed.",
                       "The second half of the standard free calculus sequence, so nothing has to be "
                       "bought to finish the course.", ["integrals", "series", "multivariable"],
                       "https://openstax.org/details/books/calculus-volume-2", "open_access", "OpenStax"),
    "openstax-calc3": ("OpenStax Calculus, Volume 3", "Gilbert Strang & Edwin Jedrysik (OpenStax)", "undergraduate",
                       "Vectors, partial derivatives, multiple integrals and vector calculus.",
                       "Covers the third-year mathematics every branch needs, including the gradient, "
                       "divergence and curl theorems.", ["vectors", "partial-derivatives", "vector-calculus"],
                       "https://openstax.org/details/books/calculus-volume-3", "open_access", "OpenStax"),
    "openstax-physics2": ("OpenStax University Physics, Volume 2", "Samuel Ling & Jeff Sanny (OpenStax)", "undergraduate",
                          "Electricity, magnetism and thermodynamics with full derivations.",
                          "The electricity and magnetism half of first-year physics, which is where most "
                          "of the electrical syllabus begins.", ["electrostatics", "circuits", "magnetism"],
                          "https://openstax.org/details/books/university-physics-volume-2", "open_access", "OpenStax"),
    "openstax-physics3": ("OpenStax University Physics, Volume 3", "Samuel Ling & Jeff Sanny (OpenStax)", "undergraduate",
                          "Optics, relativity and quantum mechanics.",
                          "Completes the physics sequence and gives electronics students the semiconductor "
                          "background their devices assume.", ["optics", "quantum", "relativity"],
                          "https://openstax.org/details/books/university-physics-volume-3", "open_access", "OpenStax"),
    "openstax-stats": ("OpenStax Introductory Statistics", "Barbara Illowsky & Susan Dean (OpenStax)", "undergraduate",
                       "Descriptive statistics, probability, distributions, inference and regression.",
                       "Statistics is assumed by machine learning, quality control and every experimental "
                       "report; this covers it without a licence fee.", ["probability", "distributions", "regression"],
                       "https://openstax.org/details/books/introductory-statistics", "open_access", "OpenStax"),
    "openstax-biology2": ("OpenStax Biology 2e", "Matthew Douglas & Jung Choi (OpenStax)", "undergraduate",
                          "Cell biology, genetics, evolution and physiology at university level.",
                          "The reference for biomedical and biochemical branches, and the background "
                          "chemistry students need before metabolism.", ["cells", "genetics", "metabolism"],
                          "https://openstax.org/details/books/biology-2e", "open_access", "OpenStax"),
    "hefferon-la": ("Linear Algebra", "Jim Hefferon", "undergraduate",
                    "A complete proof-based linear algebra text, freely hosted by the author.",
                    "Goes further than a service course needs, which matters because eigenvalues and "
                    "vector spaces carry into control, signals and machine learning.",
                    ["vectors", "eigenvalues", "linear-transformations"],
                    "https://joshua.smcvt.edu/linearalgebra/", "open_access", "Author-hosted"),
    "immersive-la": ("Immersive Linear Algebra", "J. Ström, K. Åström & T. Akenine-Möller", "undergraduate",
                     "An interactive textbook where every figure can be dragged and the algebra follows.",
                     "The one linear algebra book where changing a vector immediately shows what the "
                     "transformation does to it.", ["vectors", "transforms", "projections"],
                     "http://immersivemath.com/ila/", "open_access", "Author-hosted"),
    "think-python": ("Think Python, 2nd edition", "Allen B. Downey", "beginner",
                     "Programming concepts taught through Python, released free by the author.",
                     "The gentlest correct introduction to programming that still covers recursion, "
                     "data structures and testing properly.", ["python", "recursion", "data-structures"],
                     "https://greenteapress.com/wp/think-python-2e/", "open_access", "Green Tea Press"),
    "automate": ("Automate the Boring Stuff with Python", "Al Sweigart", "beginner",
                 "Practical Python for spreadsheets, files, scraping and automation, free online from the author.",
                 "Gets to useful programs fast, which is what keeps a first-year student going through "
                 "the theory.", ["python", "automation", "files"],
                 "https://automatetheboringstuff.com/", "open_access", "Author-hosted"),
    "crafting-interpreters": ("Crafting Interpreters", "Robert Nystrom", "advanced",
                              "Two complete programming languages built from scratch, free online.",
                              "The clearest available explanation of how a language actually runs, and "
                              "directly relevant to compilers and language design.",
                              ["parsing", "interpreters", "bytecode"],
                              "https://craftinginterpreters.com/", "open_access", "Author-hosted"),
    "beej-net": ("Beej's Guide to Network Programming", "Brian Hall", "intermediate",
                 "Sockets programming in C, free and maintained by the author.",
                 "Networking is taught as protocol layers everywhere else; this shows the actual calls "
                 "that make two machines talk.", ["sockets", "tcp", "networking"],
                 "https://beej.us/guide/bgnet/", "open_access", "Author-hosted"),
    "allaboutcircuits": ("All About Circuits textbook", "Tony Kuphaldt and contributors", "beginner",
                         "A full DC/AC circuits and semiconductors textbook, openly licensed.",
                         "Explains circuits from charge carriers upward, which is what makes the later "
                         "shorthand make sense.", ["dc-circuits", "ac-circuits", "semiconductors"],
                         "https://www.allaboutcircuits.com/textbook/", "open_access", "All About Circuits"),
    "libretexts-engineering": ("LibreTexts Engineering", "LibreTexts contributors", "undergraduate",
                               "A collaborative open library spanning statics, dynamics, materials and "
                               "process engineering.",
                               "The broadest open collection for the mechanical, civil and chemical "
                               "core, written by faculty rather than aggregated.",
                               ["statics", "materials", "process-engineering"],
                               "https://eng.libretexts.org/", "open_access", "LibreTexts"),
    "sicp": ("Structure and Interpretation of Computer Programs", "Abelson, Sussman & Sussman", "advanced",
             "The MIT text on abstraction, recursion and metalinguistic abstraction, free from MIT Press.",
             "Hard, and worth it: it is the book that made 'abstraction' a word programmers use.",
             ["abstraction", "recursion", "interpreters"],
             "https://mitpress.mit.edu/sites/default/files/sicp/index.html", "open_access", "MIT Press"),
})
