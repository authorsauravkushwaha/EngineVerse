"""Problems for the book-depth language paths: raw drills plus pattern gaps.

The language books in ``language_book_*.py`` end every module with a judged
problem to code. Most of those already exist in ``coding_core``,
``coding_streams`` and ``practice_data``; this module holds the ones that did
not:

* six ``drill-*`` problems: raw basics (loops, conditions, scans, string
  validation) that the C# foundations modules - and any true beginner - solve
  before touching patterns;
* ``merge-intervals`` and ``trapping-rain-water``: two pattern staples the
  stage plans reference that the bank was missing;
* ``word-ladder`` and ``serialize-tree``: hard favourites named across the
  mastery modules, now actually solvable instead of merely mentioned.

Same contract as the other banks: one Python entry point per problem, built
with the helper in ``coding_common.py``, verified by
``scripts/check_problems.py``.
"""
from __future__ import annotations

from .coding_common import ex, problem, tc

PROBLEMS: list[dict] = []

# ---------------------------------------------------------------------------
# Raw drills: the first six programs a beginner should be able to write
# ---------------------------------------------------------------------------

PROBLEMS += [
    problem(
        "drill-times-table", "Times Table", "easy",
        "Given an integer `n`, return the first 10 multiples of `n` as a list: "
        "`[n*1, n*2, ..., n*10]`. This is the loop drill: one counter, one "
        "rule, ten outputs. It works for zero and negative `n` too.",
        examples=[
            ex("3", "3 6 9 12 15 18 21 24 27 30", "3 times 1 through 10."),
            ex("0", "0 0 0 0 0 0 0 0 0 0", "Zero times anything is zero."),
        ],
        topics=["loop", "arithmetic"],
        signature="def times_table(n):",
        solution="def times_table(n):\n    return [n * i for i in range(1, 11)]\n",
        tests=[tc("3", "3 6 9 12 15 18 21 24 27 30"), tc("7", "7 14 21 28 35 42 49 56 63 70"),
               tc("1", "1 2 3 4 5 6 7 8 9 10"), tc("0", "0 0 0 0 0 0 0 0 0 0"),
               tc("-2", "-2 -4 -6 -8 -10 -12 -14 -16 -18 -20")],
        hints=["range(1, 11) counts from 1 to 10 inclusive.",
               "Build the list one multiple at a time, or with a list comprehension."],
        editorial="A loop from 1 to 10 appending `n * i` is the whole program. The drill is the "
                  "shape - counter, rule, collect - which every later loop reuses. Time O(1) "
                  "(ten steps regardless of input), space O(1).",
        wrapper="lines", minutes=10, expected_time="O(1)", expected_space="O(1)",
    ),
    problem(
        "drill-min-max-scan", "Min-Max Scan", "easy",
        "Given a list of integers, return `[minimum, maximum]` found in a single "
        "left-to-right scan. An empty list returns `[]`. Do not sort: the point "
        "of the drill is tracking two running answers while reading once.",
        examples=[
            ex("3 1 2", "[1, 3]", "Minimum 1, maximum 3."),
            ex("5", "[5, 5]", "One element is both the min and the max."),
        ],
        topics=["array", "loop"],
        signature="def min_max(nums):",
        solution="def min_max(nums):\n"
                 "    if not nums:\n"
                 "        return []\n"
                 "    lo = hi = nums[0]\n"
                 "    for x in nums[1:]:\n"
                 "        if x < lo:\n"
                 "            lo = x\n"
                 "        elif x > hi:\n"
                 "            hi = x\n"
                 "    return [lo, hi]\n",
        tests=[tc("3 1 2", "[1, 3]"), tc("5", "[5, 5]"), tc("-4 -1 -9", "[-9, -1]"),
               tc("", "[]"), tc("8 8 8", "[8, 8]")],
        hints=["Start both answers at the first element, then compare each new value against both.",
               "elif is enough for the maximum: a value smaller than lo cannot also exceed hi unless all are equal."],
        editorial="Initialise `lo` and `hi` to the first element and update both per value: one "
                  "pass, two comparisons each. Sorting would cost O(n log n); the scan is O(n) "
                  "time and O(1) space, and the empty-list guard keeps the first-element access safe.",
        wrapper="int-list", minutes=10, expected_time="O(n)", expected_space="O(1)",
    ),
    problem(
        "drill-grade-bands", "Grade Bands", "easy",
        "Given a score from 0 to 100, return the letter grade: `A` for 90 and "
        "above, `B` for 80 and above, `C` for 70 and above, `D` for 60 and "
        "above, otherwise `F`. This is the conditionals drill: ordered bands "
        "checked from the top down.",
        examples=[
            ex("95", "A", "95 clears the 90 bar."),
            ex("82", "B", "82 clears 80 but not 90."),
            ex("59", "F", "Below every bar."),
        ],
        topics=["conditionals"],
        signature="def grade(score):",
        solution="def grade(score):\n"
                 "    if score >= 90:\n"
                 "        return 'A'\n"
                 "    if score >= 80:\n"
                 "        return 'B'\n"
                 "    if score >= 70:\n"
                 "        return 'C'\n"
                 "    if score >= 60:\n"
                 "        return 'D'\n"
                 "    return 'F'\n",
        tests=[tc("95", "A"), tc("82", "B"), tc("70", "C"), tc("60", "D"), tc("59", "F"),
               tc("100", "A"), tc("0", "F"), tc("90", "A")],
        hints=["Check the highest band first and return immediately when one matches.",
               "Test the boundaries: 90, 80, 70, 60 - off-by-one lives exactly there."],
        editorial="Ordered early returns from the top band down: the first true condition is the "
                  "answer, and anything falling through every check is F. Boundary tests (90 "
                  "versus 89) are the whole test plan. Time and space O(1).",
        wrapper="int-n", minutes=10, expected_time="O(1)", expected_space="O(1)",
    ),
    problem(
        "drill-sum-until-zero", "Sum Until Zero", "easy",
        "Given a list of integers, add them up from the left but stop at the "
        "first zero (the zero itself adds nothing, and everything after it is "
        "ignored). An empty list, or a list starting with zero, sums to 0. "
        "This is the early-exit drill: `break` the moment the sentinel appears.",
        examples=[
            ex("1 2 3 0 99", "6", "1 + 2 + 3, then the zero stops the scan; 99 is never read."),
            ex("0 5", "0", "The very first value is the sentinel."),
        ],
        topics=["loop", "array"],
        signature="def sum_until_zero(nums):",
        solution="def sum_until_zero(nums):\n"
                 "    total = 0\n"
                 "    for x in nums:\n"
                 "        if x == 0:\n"
                 "            break\n"
                 "        total += x\n"
                 "    return total\n",
        tests=[tc("1 2 3 0 99", "6"), tc("0 5", "0"), tc("5 5", "10"), tc("", "0"),
               tc("-3 3 0", "0")],
        hints=["Accumulate into a running total, and break - not continue - on zero.",
               "No zero in the list means the loop simply adds everything."],
        editorial="A running total plus `break` on the sentinel: the loop's two exits (sentinel "
                  "found, list exhausted) are both correct by construction. Time O(n), space O(1).",
        wrapper="int-list", minutes=10, expected_time="O(n)", expected_space="O(1)",
    ),
    problem(
        "drill-count-vowels", "Count Vowels", "easy",
        "Given a line of text, count how many of its characters are vowels "
        "(`a, e, i, o, u`, in either case). Spaces, digits and punctuation "
        "count for nothing. This is the string-scan drill: look at every "
        "character once and keep one counter.",
        examples=[
            ex("hello", "2", "e and o."),
            ex("AEIOU", "5", "Uppercase counts too."),
            ex("rhythm", "0", "Sometimes y is not a vowel, and here it is not."),
        ],
        topics=["string", "loop"],
        signature="def count_vowels(text):",
        solution="def count_vowels(text):\n"
                 "    vowels = set('aeiouAEIOU')\n"
                 "    count = 0\n"
                 "    for ch in text:\n"
                 "        if ch in vowels:\n"
                 "            count += 1\n"
                 "    return count\n",
        tests=[tc("hello", "2"), tc("AEIOU", "5"), tc("rhythm", "0"), tc("Hello World", "3"),
               tc("", "0"), tc("12345!?", "0")],
        hints=["A set of the ten vowel characters makes each check O(1).",
               "Lowercasing the character first is the alternative to listing both cases."],
        editorial="One pass, one counter, membership in a ten-character set: O(n) time, O(1) "
                  "space. The only decisions are case handling (list both cases, or lower each "
                  "character) and remembering that the input line can be empty.",
        wrapper="string-int", minutes=10, expected_time="O(n)", expected_space="O(1)",
    ),
    problem(
        "drill-valid-identifier", "Valid Identifier", "easy",
        "Given a line of text, decide whether it is a valid identifier in the "
        "C/Java/Python style: non-empty, the first character a letter or "
        "underscore, and every remaining character a letter, digit or "
        "underscore. Return `True` or `False`. This is the validation drill: a "
        "short list of refusals, each checked in order.",
        examples=[
            ex("_count1", "True", "Underscore start, then letters and a digit."),
            ex("9lives", "False", "An identifier cannot start with a digit."),
            ex("total$", "False", "$ is not an identifier character."),
        ],
        topics=["string", "validation"],
        signature="def is_valid_identifier(text):",
        solution="def is_valid_identifier(text):\n"
                 "    if not text:\n"
                 "        return False\n"
                 "    if not (text[0].isalpha() or text[0] == '_'):\n"
                 "        return False\n"
                 "    for ch in text[1:]:\n"
                 "        if not (ch.isalnum() or ch == '_'):\n"
                 "            return False\n"
                 "    return True\n",
        tests=[tc("_count1", "True"), tc("9lives", "False"), tc("total$", "False"),
               tc("_", "True"), tc("", "False"), tc("a", "True"), tc("with space", "False")],
        hints=["Refuse the empty string first, then check the first character on its own rule.",
               "str.isalnum() covers letters and digits in one call."],
        editorial="Three refusals in order: empty, bad first character, bad later character. "
                  "Anything surviving all three is valid. Validation as a list of explicit "
                  "refusals - rather than one clever condition - is the professional shape. "
                  "Time O(n), space O(1).",
        wrapper="string-bool", minutes=10, expected_time="O(n)", expected_space="O(1)",
    ),
]

# ---------------------------------------------------------------------------
# Pattern staples the stage plans reference
# ---------------------------------------------------------------------------

PROBLEMS += [
    problem(
        "merge-intervals", "Merge Intervals", "medium",
        "Given a list of `[start, end]` intervals, merge every group that "
        "overlaps and return the merged intervals in order. Two intervals "
        "overlap when the second starts at or before the first ends (so "
        "`[1, 4]` and `[4, 5]` merge into `[1, 5]`). An empty list returns an "
        "empty list.",
        examples=[
            ex("4\n1 3\n2 6\n8 10\n15 18", "1 6\n8 10\n15 18",
               "[1,3] and [2,6] overlap into [1,6]; the rest stand alone."),
            ex("2\n1 4\n4 5", "1 5", "Touching at 4 still counts as overlapping."),
        ],
        topics=["array", "sorting", "intervals"],
        signature="def merge_intervals(intervals):",
        solution="def merge_intervals(intervals):\n"
                 "    if not intervals:\n"
                 "        return []\n"
                 "    ordered = sorted(intervals, key=lambda iv: iv[0])\n"
                 "    merged = [list(ordered[0])]\n"
                 "    for start, end in ordered[1:]:\n"
                 "        if start <= merged[-1][1]:\n"
                 "            merged[-1][1] = max(merged[-1][1], end)\n"
                 "        else:\n"
                 "            merged.append([start, end])\n"
                 "    return merged\n",
        tests=[tc("4\n1 3\n2 6\n8 10\n15 18", "1 6\n8 10\n15 18"),
               tc("2\n1 4\n4 5", "1 5"), tc("1\n7 7", "7 7"),
               tc("3\n1 2\n3 4\n5 6", "1 2\n3 4\n5 6"),
               tc("3\n5 9\n1 3\n2 4", "1 4\n5 9"), tc("0", "[]")],
        hints=["Sort by start first: after sorting, each interval only needs comparing with the last merged one.",
               "Touching counts as overlapping here - use <=, not <."],
        editorial="Sorting by start turns a two-dimensional overlap question into a one-pass "
                  "sweep: keep the last merged interval, extend it when the next starts at or "
                  "before its end, otherwise start a new one. The sort dominates at O(n log n) "
                  "time; the sweep is O(n) time and O(n) space for the output.",
        wrapper="intervals", minutes=25, expected_time="O(n log n)", expected_space="O(n)",
    ),
    problem(
        "trapping-rain-water", "Trapping Rain Water", "hard",
        "Given a list of bar heights, compute how much rain water is trapped "
        "after raining. Water trapped above bar `i` equals `max(0, min(tallest "
        "bar to its left, tallest bar to its right) - height[i])`; the answer "
        "is the sum over all bars. The two-pointer solution does this in one "
        "pass with O(1) extra space.",
        examples=[
            ex("0 1 0 2 1 0 1 3 2 1 2 1", "6", "The classic skyline traps 6 units."),
            ex("4 2 0 3 2 5", "9", "The deep valley between 4 and 5 holds most of it."),
        ],
        topics=["array", "two-pointers"],
        signature="def trap(height):",
        solution="def trap(height):\n"
                 "    left, right = 0, len(height) - 1\n"
                 "    left_max = right_max = water = 0\n"
                 "    while left < right:\n"
                 "        if height[left] < height[right]:\n"
                 "            if height[left] >= left_max:\n"
                 "                left_max = height[left]\n"
                 "            else:\n"
                 "                water += left_max - height[left]\n"
                 "            left += 1\n"
                 "        else:\n"
                 "            if height[right] >= right_max:\n"
                 "                right_max = height[right]\n"
                 "            else:\n"
                 "                water += right_max - height[right]\n"
                 "            right -= 1\n"
                 "    return water\n",
        tests=[tc("0 1 0 2 1 0 1 3 2 1 2 1", "6"), tc("4 2 0 3 2 5", "9"),
               tc("1 2 3", "0"), tc("", "0"), tc("5", "0"), tc("3 0 3", "3")],
        hints=["The water above bar i is bounded by the shorter of the tallest bars on each side.",
               "Move the pointer on the shorter side: its bound is already decided by the taller side."],
        editorial="For each bar, the trapping level is min(left max, right max). The two-pointer "
                  "method always advances the shorter side, because the taller side guarantees "
                  "the min is the shorter side's max - so that side can be settled without "
                  "knowing the rest. One pass, O(n) time, O(1) space. The easier O(n)-space "
                  "version precomputes both max arrays first.",
        wrapper="int-list", minutes=35, expected_time="O(n)", expected_space="O(1)",
    ),
    problem(
        "word-ladder", "Word Ladder", "hard",
        "Given a begin word, an end word and a word list, return the length of "
        "the shortest transformation sequence from begin to end where each "
        "step changes exactly one letter and every intermediate word is in the "
        "list. The length counts both ends (so `hit` to `cog` via `hot, dot, "
        "dog` is 5). Return 0 when no sequence exists.",
        examples=[
            ex("hit\ncog\nhot dot dog lot log cog", "5", "hit -> hot -> dot -> dog -> cog."),
            ex("hit\ncog\nhot dot dog lot log", "0", "cog is unreachable without cog in the list."),
        ],
        topics=["string", "breadth-first-search", "graph"],
        signature="def ladder_length(begin_word, end_word, word_list):",
        solution="def ladder_length(begin_word, end_word, word_list):\n"
                 "    words = set(word_list)\n"
                 "    if begin_word == end_word:\n"
                 "        return 1\n"
                 "    if end_word not in words:\n"
                 "        return 0\n"
                 "    from collections import deque\n"
                 "    patterns: dict[str, list[str]] = {}\n"
                 "    for word in list(words) + [begin_word]:\n"
                 "        for i in range(len(word)):\n"
                 "            key = word[:i] + '*' + word[i + 1:]\n"
                 "            patterns.setdefault(key, []).append(word)\n"
                 "    queue = deque([(begin_word, 1)])\n"
                 "    seen = {begin_word}\n"
                 "    while queue:\n"
                 "        word, depth = queue.popleft()\n"
                 "        for i in range(len(word)):\n"
                 "            key = word[:i] + '*' + word[i + 1:]\n"
                 "            for nxt in patterns.get(key, []):\n"
                 "                if nxt == end_word:\n"
                 "                    return depth + 1\n"
                 "                if nxt not in seen:\n"
                 "                    seen.add(nxt)\n"
                 "                    queue.append((nxt, depth + 1))\n"
                 "            patterns[key] = []\n"
                 "    return 0\n",
        tests=[tc("hit\ncog\nhot dot dog lot log cog", "5"),
               tc("hit\ncog\nhot dot dog lot log", "0"),
               tc("a\nc\na b c", "2"),
               tc("red\ntax\nted tex red tax tad den rex pee", "4"),
               tc("hot\nhot\nhot", "1")],
        hints=["BFS from the begin word finds the shortest sequence first - depth-first cannot promise that.",
               "Index words by wildcard patterns (h*t) so neighbours are a dictionary lookup, not a scan."],
        editorial="Words are graph nodes, one-letter changes are edges, and BFS from the begin "
                  "word reaches the end at the shortest depth. Wildcard-pattern buckets make "
                  "neighbour lookup O(1) per pattern instead of comparing every pair of words. "
                  "Time O(M^2 * N) for N words of length M, space O(M^2 * N) for the buckets.",
        wrapper="word-ladder", minutes=40, expected_time="O(M^2 N)", expected_space="O(M^2 N)",
    ),
    problem(
        "serialize-tree", "Serialize a Binary Tree", "medium",
        "Given a binary tree, serialize it to a string with a preorder walk "
        "that writes `#` for every null child and joins values with commas: a "
        "single node `1` becomes `1,#,#`. The `#` markers make the encoding "
        "unambiguous - the same preorder without them could describe several "
        "trees. An empty tree serializes to `#`.",
        examples=[
            ex("1 2 3 None None 4 5", "1,2,#,#,3,4,#,#,5,#,#",
               "Preorder 1, 2, 3 with null markers under each leaf."),
            ex("1", "1,#,#", "The root plus its two null children."),
        ],
        topics=["tree", "depth-first-search"],
        signature="def serialize(root):",
        solution="def serialize(root):\n"
                 "    parts: list[str] = []\n"
                 "    def walk(node):\n"
                 "        if node is None:\n"
                 "            parts.append('#')\n"
                 "            return\n"
                 "        parts.append(str(node.value))\n"
                 "        walk(node.left)\n"
                 "        walk(node.right)\n"
                 "    walk(root)\n"
                 "    return ','.join(parts)\n",
        tests=[tc("1 2 3 None None 4 5", "1,2,#,#,3,4,#,#,5,#,#"),
               tc("1", "1,#,#"), tc("", "#"), tc("1 None 2", "1,#,2,#,#"),
               tc("3 1 None None 2", "3,1,#,2,#,#,#")],
        hints=["Preorder means: the node first, then the left subtree, then the right.",
               "Write a marker for null children too - without them the shape is lost."],
        editorial="Preorder with null markers is a complete description: deserializing reads "
                  "tokens back in the same order, rebuilding nodes and nulls one token at a "
                  "time. Every node produces one token plus markers, so time and space are O(n). "
                  "Level-order with trailing-null trimming is the common alternative format.",
        wrapper="tree", minutes=25, expected_time="O(n)", expected_space="O(n)",
    ),
]
