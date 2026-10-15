"""Curated problem sheets (spec §16-§18).

A sheet is a short, ordered list of problems that belong together: the ten that
teach hashing, the eight that teach the two-pointer and sliding-window family,
the set a mechanical or electronics learner should start with, and one curated
"interview core" that picks the thirty worth doing first.

Two rules keep the sheets honest.

*Membership is data.* The seeder writes these lists into ``coding_sheets`` and
``coding_sheet_problems``, and the pages read them from there. Adding a sheet is
a change to this file; nothing in the application hard-codes a sheet name.

*Every problem is in at least one sheet.* ``scripts/check_problems.py --sheets``
fails when a problem is unreachable, so a newly added problem cannot quietly
become invisible because nobody remembered to list it.

``audience`` is a comma-separated list of branch categories from
``branches.category`` (or ``all``). It is what points a stream at the sheets
that suit it; see ``engineverse.hub`` for the per-branch ordering on top of it.
"""
from __future__ import annotations

from . import coding_book, coding_core, coding_streams, practice_data

#: Every problem a sheet may name: the original 13 in ``practice_data`` plus the
#: bank in the three modules beside this one. Used by ``validate()`` below.
KNOWN_SLUGS: frozenset[str] = frozenset(
    [entry["slug"] for entry in practice_data.CODING_PROBLEMS]
    + [entry["slug"] for entry in coding_core.PROBLEMS]
    + [entry["slug"] for entry in coding_streams.PROBLEMS]
    + [entry["slug"] for entry in coding_book.PROBLEMS]
)

SHEETS: list[dict] = [
    {
        "slug": "first-drills",
        "title": "First Drills: Loops, Conditions, Strings",
        "blurb": "Before the pattern sheets: six raw basics every programmer writes in their sleep. One loop, "
                 "one rule, one counter - the shapes every harder problem is built from.",
        "level": "core",
        "audience": "all",
        "est_hours": 3,
        "topic_focus": ["loop", "conditionals", "string", "validation"],
        "order_index": 0,
        "problems": [
            "drill-times-table", "drill-min-max-scan", "drill-grade-bands", "drill-sum-until-zero",
            "drill-count-vowels", "drill-valid-identifier",
        ],
    },
    {
        "slug": "arrays-hashing",
        "title": "Arrays & Hashing",
        "blurb": "The first pattern sheet to finish. A hash map turns a nested loop into a single pass, and these ten "
                 "problems are where that idea clicks.",
        "level": "core",
        "audience": "all",
        "est_hours": 6,
        "topic_focus": ["array", "hash-table", "prefix-sum"],
        "order_index": 1,
        "problems": [
            "two-sum", "contains-duplicate", "valid-anagram", "group-anagrams", "top-k-frequent",
            "product-except-self", "longest-consecutive-sequence", "move-zeroes", "majority-element",
            "subarray-sum-equals-k",
        ],
    },
    {
        "slug": "two-pointers-window",
        "title": "Two Pointers & Sliding Window",
        "blurb": "Two indices moving with a purpose. Once you can see when a window can only grow or only "
                 "shrink, a whole family of O(n²) problems collapses to O(n).",
        "level": "core",
        "audience": "all",
        "est_hours": 7,
        "topic_focus": ["two-pointers", "sliding-window", "string"],
        "order_index": 2,
        "problems": [
            "valid-palindrome", "two-sum-sorted", "container-most-water", "sorted-squares",
            "remove-duplicates-sorted", "three-sum", "longest-substring", "minimum-window-substring",
            "sliding-window-maximum",
        ],
    },
    {
        "slug": "stacks-search",
        "title": "Stacks & Binary Search",
        "blurb": "Monotonic stacks answer \"the next value bigger than this one\" in one pass, and binary search "
                 "answers \"the smallest value that works\" without testing every candidate.",
        "level": "core",
        "audience": "all",
        "est_hours": 7,
        "topic_focus": ["stack", "binary-search", "monotonic-stack"],
        "order_index": 3,
        "problems": [
            "valid-parentheses", "evaluate-rpn", "daily-temperatures", "next-greater-element",
            "binary-search", "search-rotated", "sqrt-integer", "koko-eating-bananas", "median-two-sorted",
        ],
    },
    {
        "slug": "linked-trees-heaps",
        "title": "Linked Lists, Trees & Heaps",
        "blurb": "Pointer manipulation and recursion over recursive structures. The fast/slow pointer and the "
                 "post-order traversal recur in interview after interview.",
        "level": "core",
        "audience": "all",
        "est_hours": 8,
        "topic_focus": ["linked-list", "tree", "heap", "recursion"],
        "order_index": 4,
        "problems": [
            "reverse-linked-list", "merge-sorted-arrays", "middle-of-linked-list", "max-depth-binary-tree",
            "symmetric-tree", "diameter-binary-tree", "level-order-traversal", "kth-largest",
            "last-stone-weight", "lru-cache",
        ],
    },
    {
        "slug": "graphs-traversal",
        "title": "Graphs & Grid Traversal",
        "blurb": "Breadth-first search for shortest paths, depth-first search for connectivity, and the "
                 "three-colour trick that detects a cycle. Grids are graphs wearing a costume.",
        "level": "core",
        "audience": "all",
        "est_hours": 8,
        "topic_focus": ["graph", "breadth-first-search", "union-find", "grid"],
        "order_index": 5,
        "problems": [
            "detect-cycle", "number-of-islands", "rotting-oranges", "bfs-grid-distance",
            "course-schedule", "count-provinces", "dijkstra-shortest-path",
        ],
    },
    {
        "slug": "dynamic-programming",
        "title": "Dynamic Programming",
        "blurb": "State, transition, base case. Eleven problems that move from one rolling variable to a full "
                 "table and back down again when only one row is needed.",
        "level": "core",
        "audience": "all",
        "est_hours": 10,
        "topic_focus": ["dynamic-programming", "string", "grid"],
        "order_index": 6,
        "problems": [
            "climb-stairs", "coin-change", "house-robber", "maximum-subarray",
            "longest-increasing-subsequence", "unique-paths", "partition-equal-subset",
            "max-product-subarray", "longest-palindromic-substring", "edit-distance", "word-break",
        ],
    },
    {
        "slug": "advanced-patterns",
        "title": "Advanced Patterns: Sweeps, Water, Ladders, Codecs",
        "blurb": "Four hard patterns that recur in senior interviews: the sort-and-sweep over intervals, the "
                 "two-pointer extreme, BFS over word graphs, and the tree codec. Do these after the core sheets.",
        "level": "interview",
        "audience": "all",
        "est_hours": 8,
        "topic_focus": ["intervals", "two-pointers", "breadth-first-search", "tree"],
        "order_index": 7,
        "problems": [
            "merge-intervals", "trapping-rain-water", "word-ladder", "serialize-tree",
        ],
    },
    {
        "slug": "engineering-computing",
        "title": "Engineering Computing",
        "blurb": "The programming every engineering discipline actually does: bisection and the trapezoid rule, "
                 "matrix work, unit conversions and the formulas behind them. Mechanical, civil, chemical and "
                 "electronics learners all start here.",
        "level": "stream",
        "audience": "mechanical,civil,chemical,bio,other,electronics",
        "est_hours": 6,
        "topic_focus": ["numerical-methods", "matrix", "mechanics", "fluid-mechanics"],
        "order_index": 10,
        "problems": [
            "bisection-iterations", "trapezoid-integral", "matrix-determinant-2x2", "matrix-transpose",
            "dot-product", "resistors-parallel", "reynolds-number", "gear-ratio", "prime-factorization",
        ],
    },
    {
        "slug": "digital-signals",
        "title": "Digital Logic & Signals",
        "blurb": "Bits as a first-class tool: parity, Hamming distance, Gray codes, checksums and RMS. Written "
                 "for electronics, electrical, VLSI and embedded learners, and worth doing by anyone who has "
                 "never used XOR deliberately.",
        "level": "stream",
        "audience": "electronics,mechanical",
        "est_hours": 6,
        "topic_focus": ["bit-manipulation", "digital-logic", "signals", "error-detection"],
        "order_index": 11,
        "problems": [
            "count-set-bits", "single-number", "gray-code-sequence", "hamming-distance", "even-parity",
            "xor-checksum", "binary-gap", "decibels", "rms-value",
        ],
    },
    {
        "slug": "data-analysis",
        "title": "Data, Statistics & ML Plumbing",
        "blurb": "Means and standard deviations, regression and correlation, one-hot encoding and binning. The "
                 "arithmetic behind every model and every lab report.",
        "level": "stream",
        "audience": "cse,chemical,bio,other",
        "est_hours": 6,
        "topic_focus": ["statistics", "data-analysis", "machine-learning", "regression"],
        "order_index": 12,
        "problems": [
            "mean-median-mode", "standard-deviation", "moving-average", "euclidean-distance",
            "least-squares-slope", "correlation-sign", "one-hot-encode", "histogram-bins",
        ],
    },
    {
        "slug": "security-systems",
        "title": "Security, Networks & Systems",
        "blurb": "Encoding is not encryption, validation is a list of refusals, and entropy has a formula. For "
                 "cyber-security, IT, DevOps and cloud learners - and anyone shipping code that reads input.",
        "level": "stream",
        "audience": "cse,electronics",
        "est_hours": 5,
        "topic_focus": ["security", "cryptography", "networking", "validation"],
        "order_index": 13,
        "problems": [
            "caesar-cipher", "base64-encode", "validate-ipv4", "cidr-usable-hosts", "password-entropy",
            "verify-sha256",
        ],
    },
    {
        "slug": "software-web",
        "title": "Software & Web Engineering",
        "blurb": "The string and parsing work that fills a working week: slugs, versions, encodings, Roman "
                 "numerals and the whitespace bug in every first attempt.",
        "level": "stream",
        "audience": "cse,chemical,other",
        "est_hours": 5,
        "topic_focus": ["string", "parsing", "web", "compression"],
        "order_index": 14,
        "problems": [
            "fizzbuzz", "reverse-words", "longest-common-prefix", "slugify", "run-length-encoding",
            "version-compare", "int-to-roman",
        ],
    },
    {
        "slug": "interview-core",
        "title": "Interview Core: 30 Problems",
        "blurb": "If you only have a fortnight, do these. Thirty problems across the patterns that come up "
                 "most, chosen so that finishing them means you have seen each idea at least twice.",
        "level": "interview",
        "audience": "all",
        "est_hours": 20,
        "topic_focus": ["interview", "patterns"],
        "order_index": 20,
        "problems": [
            "two-sum", "contains-duplicate", "valid-anagram", "group-anagrams", "top-k-frequent",
            "product-except-self", "longest-consecutive-sequence", "subarray-sum-equals-k",
            "valid-palindrome", "container-most-water", "three-sum", "sliding-window-maximum",
            "valid-parentheses", "daily-temperatures", "search-rotated", "koko-eating-bananas",
            "merge-sorted-arrays", "max-depth-binary-tree", "diameter-binary-tree", "level-order-traversal",
            "kth-largest", "number-of-islands", "course-schedule", "climb-stairs", "coin-change",
            "house-robber", "longest-increasing-subsequence", "partition-equal-subset", "edit-distance",
            "longest-palindromic-substring",
        ],
    },
]


def validate() -> None:
    """Fails loudly when a sheet names a problem that does not exist.

    Called by the seeder, so a typo in a slug stops the seed instead of
    producing a sheet that silently renders short.
    """
    for sheet in SHEETS:
        for slug in sheet["problems"]:
            if slug not in KNOWN_SLUGS:
                raise ValueError(f"sheet {sheet['slug']} names unknown problem {slug!r}")
        if len(set(sheet["problems"])) != len(sheet["problems"]):
            raise ValueError(f"sheet {sheet['slug']} lists a problem twice")
    placed = {slug for sheet in SHEETS for slug in sheet["problems"]}
    missing = sorted(KNOWN_SLUGS - placed)
    if missing:
        raise ValueError(f"problems in no sheet: {missing}")
