"""Core interview problem bank (spec §16-§18): arrays through dynamic programming.

Grouped by the pattern each problem teaches, which is how the sheets in
``coding_sheets.py`` present them. Every problem here is language-independent
content - statement, examples, hints, editorial, one Python entry point and its
tests - built with the helper in ``coding_common.py``.

Only Python stubs are shipped for this bank. That is a deliberate choice rather
than an omission: the Python driver in ``engineverse/drivers.py`` is the one the
judge can compose and this repository can verify end to end (see
``scripts/check_problems.py``), and shipping a Java stub whose harness has never
been run would be offering a language that does not work.

The statements are written to be readable *inside* EngineVerse: no problem tells
the learner to go and look something up on another site, and each editorial
explains the pattern well enough to stand alone.
"""
from __future__ import annotations

from .coding_common import ex, problem, tc

PROBLEMS: list[dict] = []

# ---------------------------------------------------------------------------
# Arrays and hashing
# ---------------------------------------------------------------------------

PROBLEMS += [
    problem(
        "contains-duplicate", "Contains Duplicate", "easy",
        "Given a list of integers, return `True` if any value appears at least twice, and `False` if every "
        "element is distinct. The list may be empty, in which case the answer is `False`.",
        examples=[
            ex("[1, 2, 3, 1]", "True", "1 appears twice."),
            ex("[1, 2, 3, 4]", "False", "Every element is distinct."),
        ],
        topics=["array", "hash-table"],
        signature="def contains_duplicate(nums):",
        solution="""def contains_duplicate(nums):
    return len(set(nums)) != len(nums)
""",
        tests=[tc("1 2 3 1", "True"), tc("1 2 3 4", "False"), tc("", "False"),
               tc("7 7", "True"), tc("-1 -2 -3 -1", "True")],
        hints=["What is the fastest way to ask \"have I seen this value before?\"",
               "Trade memory for time: a set remembers what you have already read."],
        editorial="A set of what has been seen so far answers the question in one pass. Building the whole set "
                  "first and comparing sizes says the same thing with less code: if the distinct count is smaller "
                  "than the length, something repeated. Time O(n), space O(n). Sorting first also works and uses "
                  "O(1) extra space beyond the sort, but costs O(n log n).",
        wrapper="int-list", expected_time="O(n)", expected_space="O(n)",
    ),
    problem(
        "valid-anagram", "Valid Anagram", "easy",
        "Two words are anagrams if one can be rearranged into the other. Line 1 is the first word, line 2 the "
        "second. Return `True` when they are anagrams of each other, letter for letter, ignoring case and "
        "spaces.",
        examples=[
            ex("listen / silent", "True", "The same letters in a different order."),
            ex("hello / world", "False", "The letters do not match."),
        ],
        topics=["string", "hash-table", "sorting"],
        signature="def is_anagram(a, b):",
        solution="""def is_anagram(a, b):
    clean = lambda text: sorted(c for c in text.lower() if c.isalnum())
    return clean(a) == clean(b)
""",
        tests=[tc("listen\nsilent", "True"), tc("hello\nworld", "False"),
               tc("Dormitory\ndirty room", "True"), tc("a\nab", "False")],
        hints=["Two words are anagrams exactly when their sorted letters are equal.",
               "Counting letters with a dictionary gives the same answer in one pass."],
        editorial="Sorting both words and comparing is the shortest correct answer: O(n log n) time, O(n) space. "
                  "Counting letters into a dictionary is O(n) and is what an interviewer usually wants to see, "
                  "but both are accepted here. Remember to normalise case (and spaces) before comparing, which is "
                  "the part that trips people up.",
        wrapper="two-lines",
    ),
    problem(
        "group-anagrams", "Group Anagrams", "medium",
        "Given a line of words, group the ones that are anagrams of each other. Return the groups in the order "
        "each group's first word appears in the input, and sort the words inside each group alphabetically.",
        examples=[
            ex("eat tea tan ate nat bat",
               "[['ate', 'eat', 'tea'], ['nat', 'tan'], ['bat']]"),
        ],
        topics=["string", "hash-table", "sorting"],
        signature="def group_anagrams(words):",
        solution="""def group_anagrams(words):
    groups = {}
    order = []
    for word in words:
        key = "".join(sorted(word))
        if key not in groups:
            groups[key] = []
            order.append(key)
        groups[key].append(word)
    return [sorted(groups[key]) for key in order]
""",
        tests=[tc("eat tea tan ate nat bat", "[['ate', 'eat', 'tea'], ['nat', 'tan'], ['bat']]"),
               tc("abc cba bca", "[['abc', 'bca', 'cba']]"),
               tc("a", "[['a']]")],
        hints=["What single value is identical for every word in a group?",
               "Sorted letters make a perfect key. A 26-slot count works too and avoids the sort."],
        editorial="The key insight is that an anagram class has a canonical form: the word's letters in sorted "
                  "order. Map that key to the list of words that produced it, remembering insertion order so the "
                  "output is deterministic. Time O(n · k log k) for k-letter words, space O(n · k).",
        wrapper="string-list", expected_time="O(n·k log k)", expected_space="O(n·k)",
    ),
    problem(
        "top-k-frequent", "Top K Frequent Elements", "medium",
        "Line 1 is a list of integers, line 2 is an integer `k`. Return the `k` most frequent values, most "
        "frequent first. Break ties by taking the smaller value first so the answer is always the same for the "
        "same input.",
        examples=[
            ex("[1, 1, 1, 2, 2, 3], k = 2", "[1, 2]", "1 appears three times, 2 appears twice."),
            ex("[1], k = 1", "[1]"),
        ],
        topics=["array", "hash-table", "heap", "sorting"],
        signature="def top_k_frequent(nums, k):",
        solution="""def top_k_frequent(nums, k):
    counts = {}
    for value in nums:
        counts[value] = counts.get(value, 0) + 1
    ordered = sorted(counts, key=lambda value: (-counts[value], value))
    return ordered[:k]
""",
        tests=[tc("1 1 1 2 2 3\n2", "[1, 2]"), tc("1\n1", "[1]"),
               tc("4 4 4 4 3 3 2\n2", "[4, 3]"), tc("5 5 4 4 3\n3", "[4, 5, 3]")],
        hints=["Count first, decide ordering second.",
               "A heap of size k avoids sorting every distinct value."],
        editorial="Counting is a dictionary pass. Everything after that is ordering: sorting by (-count, value) "
                  "gives a deterministic answer and is O(d log d) for d distinct values. A min-heap of size k runs "
                  "in O(n log k), which matters when the value range is large. Bucket sort by frequency reaches "
                  "O(n) but cannot break ties by value as simply.",
        wrapper="int-list-int", expected_time="O(n log n)", expected_space="O(n)",
    ),
    problem(
        "product-except-self", "Product of Array Except Self", "medium",
        "Given a list of integers, return a list where position `i` holds the product of every element except "
        "the one at `i`. You may not use division, and the answer must run in linear time.",
        examples=[
            ex("[1, 2, 3, 4]", "[24, 12, 8, 6]", "2×3×4, 1×3×4, 1×2×4, 1×2×3."),
        ],
        topics=["array", "prefix-sum"],
        signature="def product_except_self(nums):",
        solution="""def product_except_self(nums):
    n = len(nums)
    out = [1] * n
    prefix = 1
    for i in range(n):
        out[i] = prefix
        prefix *= nums[i]
    suffix = 1
    for i in range(n - 1, -1, -1):
        out[i] *= suffix
        suffix *= nums[i]
    return out
""",
        tests=[tc("1 2 3 4", "[24, 12, 8, 6]"), tc("2 3 4", "[12, 8, 6]"),
               tc("-1 1 0 -3 3", "[0, 0, 9, 0, 0]"), tc("5", "[1]")],
        hints=["The answer for position i is (product of everything before i) × (product of everything after i).",
               "You can build both of those in two passes without extra arrays."],
        editorial="Write the prefix products into the output array first, then walk backwards multiplying by the "
                  "running suffix product. Each pass is O(n), and the only extra space is the output itself. The "
                  "division ban is the point of the problem: with zeros in the list, dividing would need special "
                  "cases anyway.",
        wrapper="int-list", expected_time="O(n)", expected_space="O(1) besides the output",
    ),
    problem(
        "longest-consecutive-sequence", "Longest Consecutive Sequence", "medium",
        "Given an unsorted list of integers, return the length of the longest run of consecutive values "
        "(`1, 2, 3, ...`). The list may contain duplicates, and the algorithm must run in linear time.",
        examples=[
            ex("[100, 4, 200, 1, 3, 2]", "4", "1, 2, 3, 4 form the longest run."),
            ex("[0, 3, 7, 2, 5, 8, 4, 6, 0, 1]", "9"),
        ],
        topics=["array", "hash-table", "union-find"],
        signature="def longest_consecutive(nums):",
        solution="""def longest_consecutive(nums):
    values = set(nums)
    best = 0
    for value in values:
        if value - 1 in values:
            continue
        length = 1
        while value + length in values:
            length += 1
        best = max(best, length)
    return best
""",
        tests=[tc("100 4 200 1 3 2", "4"), tc("0 3 7 2 5 8 4 6 0 1", "9"),
               tc("1 2 0 1", "3"), tc("", "0")],
        hints=["Sorting is O(n log n). The problem asks for better, so the work has to happen in a set.",
               "Only start counting a run from a value that has no predecessor in the set."],
        editorial="Put every value in a set. A value that has no predecessor begins a run; walk upward while the "
                  "set contains the next value. Each value is visited at most twice across all runs, so the total "
                  "work is O(n) even though the inner loop looks nested. Skip the check and every value would "
                  "start its own walk, which is the O(n²) trap this problem is testing for.",
        wrapper="int-list", expected_time="O(n)", expected_space="O(n)",
    ),
    problem(
        "move-zeroes", "Move Zeroes", "easy",
        "Move every zero in a list to the end while keeping the relative order of the non-zero values. Return "
        "the resulting list.",
        examples=[
            ex("[0, 1, 0, 3, 12]", "[1, 3, 12, 0, 0]"),
            ex("[0, 0, 1]", "[1, 0, 0]"),
        ],
        topics=["array", "two-pointers"],
        signature="def move_zeroes(nums):",
        solution="""def move_zeroes(nums):
    write = 0
    for value in nums:
        if value != 0:
            nums[write] = value
            write += 1
    for i in range(write, len(nums)):
        nums[i] = 0
    return nums
""",
        tests=[tc("0 1 0 3 12", "[1, 3, 12, 0, 0]"), tc("0 0 1", "[1, 0, 0]"),
               tc("1 2 3", "[1, 2, 3]"), tc("0", "[0]")],
        hints=["Keep one index for \"where the next non-zero belongs\".",
               "Every write position is behind or at the read position, so the pass is safe in place."],
        editorial="This is the write-index pattern: walk the list once, compact the non-zero values to the front "
                  "and remember where that front ended, then fill the remainder with zeros. It is O(n) time, O(1) "
                  "extra space, and stable - which is why swapping pairs is riskier than it looks.",
        wrapper="int-list", expected_time="O(n)",
    ),
    problem(
        "majority-element", "Majority Element", "easy",
        "Return the element that appears more than half the time in a list. The input is guaranteed to contain "
        "such an element.",
        examples=[
            ex("[3, 2, 3]", "3"),
            ex("[2, 2, 1, 1, 1, 2, 2]", "2"),
        ],
        topics=["array", "hash-table", "boyer-moore"],
        signature="def majority_element(nums):",
        solution="""def majority_element(nums):
    candidate = None
    count = 0
    for value in nums:
        if count == 0:
            candidate = value
        count += 1 if value == candidate else -1
    return candidate
""",
        tests=[tc("3 2 3", "3"), tc("2 2 1 1 1 2 2", "2"), tc("1", "1"), tc("5 5 5 1 2", "5")],
        hints=["A dictionary solves it, but a true majority can never be cancelled out by the minority.",
               "Pair up different values and throw both away. What is left must be the majority."],
        editorial="Boyer-Moore voting keeps one candidate and a counter. An equal value increments, a different "
                  "value decrements, and a zero counter adopts the next value. Because the majority element occurs "
                  "more than n/2 times it survives every cancellation. One pass, constant space. Counting with a "
                  "dictionary is easier to reason about but uses O(n) space, and sorting is O(n log n).",
        wrapper="int-list", expected_time="O(n)",
    ),
    problem(
        "subarray-sum-equals-k", "Subarray Sum Equals K", "medium",
        "Line 1 is a list of integers (some negative), line 2 is a target integer `k`. Return how many "
        "contiguous subarrays sum exactly to `k`.",
        examples=[
            ex("[1, 1, 1], k = 2", "2", "Two subarrays of length two."),
            ex("[1, 2, 3], k = 3", "2", "[3] and [1, 2]."),
        ],
        topics=["array", "prefix-sum", "hash-table"],
        signature="def subarray_sum(nums, k):",
        solution="""def subarray_sum(nums, k):
    seen = {0: 1}
    total = 0
    count = 0
    for value in nums:
        total += value
        count += seen.get(total - k, 0)
        seen[total] = seen.get(total, 0) + 1
    return count
""",
        tests=[tc("1 1 1\n2", "2"), tc("1 2 3\n3", "2"),
               tc("3 4 7 2 -3 1 4 2\n7", "4"), tc("1 -1 0\n0", "3")],
        hints=["The sum of a subarray is the difference of two prefix sums.",
               "Count how many earlier prefix sums equal current_prefix - k, and seed the map with 0 → 1."],
        editorial="Walk the list keeping a running prefix total. Any earlier prefix equal to `total - k` marks a "
                  "subarray that ends here and sums to k, so the running answer is the number of such prefixes "
                  "seen. The `{0: 1}` seed is what lets a subarray starting at index 0 be counted. Negative "
                  "numbers make a sliding window invalid, which is why the prefix map is the right tool: O(n) "
                  "time, O(n) space.",
        wrapper="int-list-int", expected_time="O(n)", expected_space="O(n)",
    ),
]

# ---------------------------------------------------------------------------
# Two pointers and sliding window
# ---------------------------------------------------------------------------

PROBLEMS += [
    problem(
        "valid-palindrome", "Valid Palindrome", "easy",
        "Return `True` when a line of text reads the same forwards and backwards once you keep only letters and "
        "digits and ignore case. An empty line is a palindrome.",
        examples=[
            ex("A man, a plan, a canal: Panama", "True"),
            ex("race a car", "False"),
        ],
        topics=["string", "two-pointers"],
        signature="def is_palindrome(text):",
        solution="""def is_palindrome(text):
    cleaned = [c.lower() for c in text if c.isalnum()]
    return cleaned == cleaned[::-1]
""",
        tests=[tc("A man, a plan, a canal: Panama", "True"), tc("race a car", "False"),
               tc("", "True"), tc("0P", "False")],
        hints=["Filtering first is easier to get right than doing both jobs in one pointer walk.",
               "Moving two pointers inward skips the filtered list entirely and uses O(1) space."],
        editorial="The straightforward answer filters to alphanumeric lower-case characters and compares the "
                  "result with its reverse: O(n) time, O(n) space. The two-pointer version walks from both ends and "
                  "skips characters that are not alphanumeric, which uses constant space and is the version that "
                  "usually gets asked as a follow-up.",
        wrapper="string-bool",
    ),
    problem(
        "two-sum-sorted", "Two Sum II — Sorted Input", "easy",
        "Line 1 is a list sorted in ascending order, line 2 is a target. Return the 1-based positions of the two "
        "numbers that add up to the target, as `[i, j]` with `i < j`. Exactly one answer exists.",
        examples=[
            ex("[2, 7, 11, 15], target = 9", "[1, 2]"),
            ex("[2, 3, 4], target = 6", "[1, 3]"),
        ],
        topics=["array", "two-pointers", "binary-search"],
        signature="def two_sum_sorted(numbers, target):",
        solution="""def two_sum_sorted(numbers, target):
    left, right = 0, len(numbers) - 1
    while left < right:
        total = numbers[left] + numbers[right]
        if total == target:
            return [left + 1, right + 1]
        if total < target:
            left += 1
        else:
            right -= 1
    return []
""",
        tests=[tc("2 7 11 15\n9", "[1, 2]"), tc("2 3 4\n6", "[1, 3]"),
               tc("-1 0\n-1", "[1, 2]"), tc("1 2 3 4 5 6\n11", "[5, 6]")],
        hints=["The list is sorted, so a sum that is too small can only be fixed by moving the left pointer up.",
               "Every step eliminates a row or a column of the pair matrix."],
        editorial="Two pointers from the ends: if the sum is too small only a larger left value can help, and if "
                  "it is too large only a smaller right value can. Each iteration removes one candidate, so at "
                  "most n steps are needed: O(1) extra space, O(n) time. The hash-map solution from Two Sum also "
                  "works but ignores that the input is sorted, which is the whole point here.",
        wrapper="int-list-int",
    ),
    problem(
        "container-most-water", "Container With Most Water", "medium",
        "Given the heights of vertical lines, return the largest area of water that can be held between any two "
        "of them. The area is `min(h[i], h[j]) * (j - i)`.",
        examples=[
            ex("[1, 8, 6, 2, 5, 4, 8, 3, 7]", "49", "Lines 2 and 9 hold 7 × 7."),
            ex("[1, 1]", "1"),
        ],
        topics=["array", "two-pointers", "greedy"],
        signature="def max_area(height):",
        solution="""def max_area(height):
    left, right = 0, len(height) - 1
    best = 0
    while left < right:
        best = max(best, min(height[left], height[right]) * (right - left))
        if height[left] <= height[right]:
            left += 1
        else:
            right -= 1
    return best
""",
        tests=[tc("1 8 6 2 5 4 8 3 7", "49"), tc("1 1", "1"), tc("4 3 2 1 4", "16"),
               tc("1 2 1", "2")],
        hints=["Start with the widest pair and shrink inward.",
               "Moving the taller line inward cannot help, because the width shrinks and the shorter line still "
               "caps the height."],
        editorial="Begin with the widest container. Its height is limited by the shorter line, so moving the "
                  "taller side inward is pointless: the width strictly decreases and the height cannot increase. "
                  "Move the shorter side, record the best area seen, and continue until the pointers meet. "
                  "O(n) time, O(1) space - and the greedy argument is the part an interviewer is listening for.",
        wrapper="int-list",
    ),
    problem(
        "three-sum", "3Sum", "medium",
        "Given a list of integers, return every unique triple that sums to zero. Sort each triple ascending, "
        "return the triples in ascending order, and include no duplicate triple. Return `[]` when none exist.",
        examples=[
            ex("[-1, 0, 1, 2, -1, -4]", "[[-1, -1, 2], [-1, 0, 1]]"),
            ex("[0, 0, 0]", "[[0, 0, 0]]"),
        ],
        topics=["array", "two-pointers", "sorting"],
        signature="def three_sum(nums):",
        solution="""def three_sum(nums):
    nums = sorted(nums)
    out = []
    for i in range(len(nums) - 2):
        if i and nums[i] == nums[i - 1]:
            continue
        left, right = i + 1, len(nums) - 1
        while left < right:
            total = nums[i] + nums[left] + nums[right]
            if total == 0:
                out.append([nums[i], nums[left], nums[right]])
                left += 1
                right -= 1
                while left < right and nums[left] == nums[left - 1]:
                    left += 1
                while left < right and nums[right] == nums[right + 1]:
                    right -= 1
            elif total < 0:
                left += 1
            else:
                right -= 1
    return out
""",
        tests=[tc("-1 0 1 2 -1 -4", "[[-1, -1, 2], [-1, 0, 1]]"), tc("0 0 0", "[[0, 0, 0]]"),
               tc("1 2 3", "[]"), tc("-2 0 1 1 2", "[[-2, 0, 2], [-2, 1, 1]]")],
        hints=["Sort once, then fix one value and solve a two-sum on the rest with two pointers.",
               "Duplicates are the whole difficulty: skip repeated first values, and skip repeated pointer "
               "values after recording a triple."],
        editorial="Sort the list, then for each index i use two pointers on the suffix to find pairs summing to "
                  "-nums[i]. Sorting makes skipping duplicates easy and makes the output order deterministic. "
                  "Total time O(n²), space O(1) beyond the output. Missing the duplicate skips is the classic "
                  "wrong answer here, and it is usually visible in the test output as a repeated triple.",
        wrapper="int-list", expected_time="O(n²)", expected_space="O(1) besides the output",
    ),
    problem(
        "sorted-squares", "Squares of a Sorted Array", "easy",
        "Given a list sorted in ascending order (which may contain negatives), return a list of the squares of "
        "each value, also sorted in ascending order.",
        examples=[
            ex("[-4, -1, 0, 3, 10]", "[0, 1, 9, 16, 100]"),
            ex("[-7, -3, 2, 3, 11]", "[4, 9, 9, 49, 121]"),
        ],
        topics=["array", "two-pointers", "sorting"],
        signature="def sorted_squares(nums):",
        solution="""def sorted_squares(nums):
    return sorted(value * value for value in nums)
""",
        tests=[tc("-4 -1 0 3 10", "[0, 1, 9, 16, 100]"), tc("-7 -3 2 3 11", "[4, 9, 9, 49, 121]"),
               tc("1 2 3", "[1, 4, 9]"), tc("-1", "[1]")],
        hints=["Squaring destroys the order because negatives become positive.",
               "The largest square is always at one of the two ends, so the answer can be filled from the back."],
        editorial="Sorting the squares is O(n log n) and perfectly acceptable. The O(n) version compares the two "
                  "ends of the input and writes the larger square into the output from the right, because the "
                  "largest magnitude sits at one end. Both are correct; the second shows you noticed the input was "
                  "already sorted.",
        wrapper="int-list", expected_time="O(n log n)", expected_space="O(n)",
    ),
    problem(
        "minimum-window-substring", "Minimum Window Substring", "hard",
        "Line 1 is a string `s`, line 2 is a string `t`. Return the shortest substring of `s` that contains "
        "every character of `t` with at least the same multiplicity. Return an empty line when no such window "
        "exists.",
        examples=[
            ex("s = ADOBECODEBANC, t = ABC", "BANC"),
            ex("s = a, t = a", "a"),
            ex("s = a, t = b", "", "No window contains b."),
        ],
        topics=["string", "sliding-window", "hash-table"],
        signature="def min_window(source, target):",
        solution="""def min_window(source, target):
    if not source or not target:
        return ""
    need = {}
    for char in target:
        need[char] = need.get(char, 0) + 1
    required = len(need)
    formed = 0
    window = {}
    best = None
    left = 0
    for right, char in enumerate(source):
        window[char] = window.get(char, 0) + 1
        if char in need and window[char] == need[char]:
            formed += 1
        while formed == required:
            if best is None or right - left + 1 < best[1] - best[0] + 1:
                best = (left, right)
            window[source[left]] -= 1
            if source[left] in need and window[source[left]] < need[source[left]]:
                formed -= 1
            left += 1
    return "" if best is None else source[best[0]:best[1] + 1]
""",
        tests=[tc("ADOBECODEBANC\nABC", "BANC"), tc("a\na", "a"), tc("a\nb", ""),
               tc("aa\naa", "aa"), tc("bba\nab", "ba")],
        hints=["Grow the window to the right until it is valid, then shrink it from the left while it stays valid.",
               "Track how many distinct characters have reached their required count rather than comparing the "
               "whole window every step."],
        editorial="This is the expand/shrink template. Expand right, and whenever the window contains all of t, "
                  "record it if it is the shortest so far and then shrink from the left until it stops being "
                  "valid. Comparing full dictionaries at each step is O(26n) here but the counter-of-satisfied-"
                  "characters version is O(n) and is the one that generalises to larger alphabets.",
        wrapper="two-lines", expected_time="O(n)", expected_space="O(k)",
    ),
    problem(
        "sliding-window-maximum", "Sliding Window Maximum", "hard",
        "Line 1 is a list of integers, line 2 is a window size `k`. Return the maximum of every window of `k` "
        "consecutive values, in order from left to right.",
        examples=[
            ex("[1, 3, -1, -3, 5, 3, 6, 7], k = 3", "[3, 3, 5, 5, 6, 7]"),
        ],
        topics=["array", "sliding-window", "deque"],
        signature="def max_sliding_window(nums, k):",
        solution="""def max_sliding_window(nums, k):
    from collections import deque

    window = deque()
    out = []
    for index, value in enumerate(nums):
        while window and nums[window[-1]] <= value:
            window.pop()
        window.append(index)
        if window[0] <= index - k:
            window.popleft()
        if index >= k - 1:
            out.append(nums[window[0]])
    return out
""",
        tests=[tc("1 3 -1 -3 5 3 6 7\n3", "[3, 3, 5, 5, 6, 7]"), tc("1\n1", "[1]"),
               tc("9 8 7 6\n2", "[9, 8, 7]"), tc("-1 -2 -3\n2", "[-1, -2]")],
        hints=["Recomputing max() per window is O(n·k). Which values can never be the maximum again?",
               "Keep a deque of indices whose values are decreasing; drop the back when a bigger value arrives "
               "and drop the front when it leaves the window."],
        editorial="A monotonic deque holds indices with decreasing values. Before adding a new value, pop smaller "
                  "values from the back - they can never be the maximum while this one is in the window. Pop the "
                  "front when it falls out of the window, and the front is then the window maximum. Each index "
                  "enters and leaves once, so the total work is O(n).",
        wrapper="int-list-int", expected_time="O(n)", expected_space="O(k)",
    ),
    problem(
        "remove-duplicates-sorted", "Remove Duplicates from Sorted Array", "easy",
        "Given a sorted list, return how many values are unique - that is, the length of the list once every "
        "duplicate is removed in place, keeping the first occurrence of each value.",
        examples=[
            ex("[1, 1, 2]", "2", "The unique values are 1 and 2."),
            ex("[0, 0, 1, 1, 1, 2, 2, 3, 3, 4]", "5"),
        ],
        topics=["array", "two-pointers"],
        signature="def remove_duplicates(nums):",
        solution="""def remove_duplicates(nums):
    if not nums:
        return 0
    write = 1
    for read in range(1, len(nums)):
        if nums[read] != nums[write - 1]:
            nums[write] = nums[read]
            write += 1
    return write
""",
        tests=[tc("1 1 2", "2"), tc("0 0 1 1 1 2 2 3 3 4", "5"), tc("1", "1"), tc("1 1 1", "1")],
        hints=["The list is sorted, so duplicates are adjacent.",
               "Keep a slow write index and a fast read index."],
        editorial="Because the input is sorted, equal values sit next to each other. A write index marks where "
                  "the next new value belongs; a read index scans. The answer is the write index. O(n) time, "
                  "O(1) space. In an interview the follow-up is usually \"now allow each value at most twice\", "
                  "which is the same loop with a different comparison at the write pointer.",
        wrapper="int-list",
    ),
]

# ---------------------------------------------------------------------------
# Stacks, queues and binary search
# ---------------------------------------------------------------------------

PROBLEMS += [
    problem(
        "evaluate-rpn", "Evaluate Reverse Polish Notation", "medium",
        "Given one line of space-separated tokens in reverse Polish notation, evaluate the expression and return "
        "the integer result. Operators are `+`, `-`, `*` and `/`, and division truncates toward zero.",
        examples=[
            ex("2 1 + 3 *", "9", "(2 + 1) × 3."),
            ex("4 13 5 / +", "6", "13 / 5 = 2, then 4 + 2."),
        ],
        topics=["stack", "math"],
        signature="def eval_rpn(tokens):",
        solution="""def eval_rpn(tokens):
    stack = []
    for token in tokens:
        if token in ("+", "-", "*", "/"):
            right = stack.pop()
            left = stack.pop()
            if token == "+":
                stack.append(left + right)
            elif token == "-":
                stack.append(left - right)
            elif token == "*":
                stack.append(left * right)
            else:
                stack.append(int(left / right))
        else:
            stack.append(int(token))
    return stack[-1]
""",
        tests=[tc("2 1 + 3 *", "9"), tc("4 13 5 / +", "6"), tc("7", "7"),
               tc("10 6 9 3 + -11 * / * 17 + 5 +", "22")],
        hints=["Push numbers, pop two for each operator.",
               "The order matters for subtraction and division: the first pop is the right operand."],
        editorial="Reverse Polish notation removes the need to know about precedence: every operator applies to "
                  "the two most recent values. Keep them on a stack, and note that integer division in Python is "
                  "not the same as truncation toward zero for negatives, which is why the reference uses "
                  "`int(left / right)`. O(n) time, O(n) space.",
        wrapper="string-list",
    ),
    problem(
        "daily-temperatures", "Daily Temperatures", "medium",
        "Given a list of daily temperatures, return a list where position `i` holds how many days you must wait "
        "after day `i` for a warmer temperature. Use `0` when no warmer day comes.",
        examples=[
            ex("[73, 74, 75, 71, 69, 72, 76, 73]", "[1, 1, 4, 2, 1, 1, 0, 0]"),
        ],
        topics=["array", "stack", "monotonic-stack"],
        signature="def daily_temperatures(temperatures):",
        solution="""def daily_temperatures(temperatures):
    waiting = [0] * len(temperatures)
    stack = []
    for day, temperature in enumerate(temperatures):
        while stack and temperatures[stack[-1]] < temperature:
            earlier = stack.pop()
            waiting[earlier] = day - earlier
        stack.append(day)
    return waiting
""",
        tests=[tc("73 74 75 71 69 72 76 73", "[1, 1, 4, 2, 1, 1, 0, 0]"),
               tc("30 40 50 60", "[1, 1, 1, 0]"), tc("30 60 90", "[1, 1, 0]")],
        hints=["A brute-force scan from each day is O(n²). What work is repeated?",
               "Keep a stack of days still waiting, with temperatures that never increase as you go down the "
               "stack."],
        editorial="Keep a stack of indices whose warmer day has not arrived. When today is warmer than the top of "
                  "the stack, that day's answer is the distance, and it can be popped - every index is pushed and "
                  "popped once, so the loop is O(n) overall. The stack values stay decreasing, which is what makes "
                  "the pop condition correct.",
        wrapper="int-list", expected_time="O(n)", expected_space="O(n)",
    ),
    problem(
        "next-greater-element", "Next Greater Element", "medium",
        "Given a list of integers, return a list where position `i` holds the first value to the right of `i` "
        "that is strictly greater, or `-1` if there is none.",
        examples=[
            ex("[2, 1, 2, 4, 3]", "[4, 2, 4, -1, -1]"),
        ],
        topics=["array", "stack", "monotonic-stack"],
        signature="def next_greater(nums):",
        solution="""def next_greater(nums):
    answer = [-1] * len(nums)
    stack = []
    for index, value in enumerate(nums):
        while stack and nums[stack[-1]] < value:
            answer[stack.pop()] = value
        stack.append(index)
    return answer
""",
        tests=[tc("2 1 2 4 3", "[4, 2, 4, -1, -1]"), tc("1 2 3 4", "[2, 3, 4, -1]"),
               tc("4 3 2 1", "[-1, -1, -1, -1]")],
        hints=["Same shape as Daily Temperatures, but you store the value rather than the distance.",
               "Values still waiting for an answer sit on the stack in decreasing order."],
        editorial="The monotonic stack records indices waiting for a greater value. When a bigger value arrives it "
                  "answers every smaller value below it on the stack, then takes their place. Each index is pushed "
                  "and popped at most once: O(n) time, O(n) space.",
        wrapper="int-list", expected_time="O(n)", expected_space="O(n)",
    ),
    problem(
        "search-rotated", "Search in Rotated Sorted Array", "medium",
        "A sorted list has been rotated at some unknown pivot. Line 1 is the rotated list, line 2 is a target "
        "value. Return the index of the target, or `-1` if it is absent. The algorithm must run in O(log n).",
        examples=[
            ex("[4, 5, 6, 7, 0, 1, 2], target = 0", "4"),
            ex("[4, 5, 6, 7, 0, 1, 2], target = 3", "-1"),
        ],
        topics=["array", "binary-search"],
        signature="def search_rotated(nums, target):",
        solution="""def search_rotated(nums, target):
    left, right = 0, len(nums) - 1
    while left <= right:
        middle = (left + right) // 2
        if nums[middle] == target:
            return middle
        if nums[left] <= nums[middle]:
            if nums[left] <= target < nums[middle]:
                right = middle - 1
            else:
                left = middle + 1
        else:
            if nums[middle] < target <= nums[right]:
                left = middle + 1
            else:
                right = middle - 1
    return -1
""",
        tests=[tc("4 5 6 7 0 1 2\n0", "4"), tc("4 5 6 7 0 1 2\n3", "-1"),
               tc("1\n0", "-1"), tc("1 3\n3", "1")],
        hints=["One half of a rotated sorted array is always properly sorted.",
               "Decide which half is sorted, then check whether the target falls inside it."],
        editorial="At every step one of the two halves is sorted in the ordinary sense. Compare its endpoints to "
                  "decide which one, then use a normal binary-search range test to keep the half that could "
                  "contain the target. Halving the range each step keeps it at O(log n) with O(1) space.",
        wrapper="int-list-int", expected_time="O(log n)",
    ),
    problem(
        "sqrt-integer", "Integer Square Root", "easy",
        "Given a non-negative integer `x`, return the integer part of its square root without using any library "
        "square-root function.",
        examples=[
            ex("4", "2"),
            ex("8", "2", "The true square root is 2.828…, so the integer part is 2."),
        ],
        topics=["math", "binary-search"],
        signature="def my_sqrt(x):",
        solution="""def my_sqrt(x):
    low, high = 0, x
    while low <= high:
        middle = (low + high) // 2
        if middle * middle <= x:
            low = middle + 1
        else:
            high = middle - 1
    return high
""",
        tests=[tc("4", "2"), tc("8", "2"), tc("0", "0"), tc("1", "1"), tc("2147395599", "46339")],
        hints=["The answer is between 0 and x.",
               "Binary search for the largest value whose square is at most x."],
        editorial="Binary search on the answer: keep the largest mid with mid² ≤ x. Beware the classic overflow "
                  "in languages with fixed-width integers - in Python the numbers just grow. O(log x) time, "
                  "O(1) space. Newton's method converges faster and is worth mentioning in an interview.",
        wrapper="int-n", expected_time="O(log x)",
    ),
    problem(
        "koko-eating-bananas", "Koko Eating Bananas", "medium",
        "Line 1 is a list of pile sizes, line 2 is the number of hours available. Koko eats at a constant speed "
        "of `k` bananas per hour from one pile at a time. Return the smallest `k` that clears every pile within "
        "the hours available.",
        examples=[
            ex("piles = [3, 6, 7, 11], hours = 8", "4"),
            ex("piles = [30, 11, 23, 4, 20], hours = 5", "30"),
        ],
        topics=["array", "binary-search"],
        signature="def min_eating_speed(piles, hours):",
        solution="""def min_eating_speed(piles, hours):
    def needed(speed):
        return sum((pile + speed - 1) // speed for pile in piles)

    low, high = 1, max(piles)
    while low < high:
        middle = (low + high) // 2
        if needed(middle) <= hours:
            high = middle
        else:
            low = middle + 1
    return low
""",
        tests=[tc("3 6 7 11\n8", "4"), tc("30 11 23 4 20\n5", "30"),
               tc("30 11 23 4 20\n6", "23"), tc("1\n1", "1")],
        hints=["If a speed works, every faster speed works. That monotonicity is what makes binary search valid.",
               "Hours needed for a pile is ceil(pile / speed)."],
        editorial="The predicate \"can finish within h hours\" is monotone in the speed, so binary search over "
                  "the speed range 1..max(piles). Each check is O(n), giving O(n log m) for the largest pile m. "
                  "The ceiling division `(pile + speed - 1) // speed` is the piece worth writing carefully: "
                  "integer division of a partial hour would under-count.",
        wrapper="int-list-int", expected_time="O(n log m)",
    ),
    problem(
        "median-two-sorted", "Median of Two Sorted Arrays", "hard",
        "Line 1 and line 2 are two sorted lists of integers. Return the median of the combined values as a "
        "number: the middle value when the total count is odd, or the mean of the two middle values when it is "
        "even.",
        examples=[
            ex("[1, 3] and [2]", "2.0"),
            ex("[1, 2] and [3, 4]", "2.5"),
        ],
        topics=["array", "binary-search", "divide-and-conquer"],
        signature="def find_median_sorted(a, b):",
        solution="""def find_median_sorted(a, b):
    merged = sorted(a + b)
    count = len(merged)
    if count == 0:
        return 0.0
    if count % 2:
        return float(merged[count // 2])
    return (merged[count // 2 - 1] + merged[count // 2]) / 2
""",
        tests=[tc("1 3\n2", "2.0"), tc("1 2\n3 4", "2.5"), tc("1 2 3 4 5\n", "3.0"),
               tc("\n7", "7.0"), tc("5\n6 7", "6.0")],
        hints=["Merging both lists and taking the middle is correct but O(m + n). The interesting version is "
               "O(log(min(m, n))) and partitions both lists instead of merging them.",
               "For the optimal version, binary search the split point of the shorter list so that every value "
               "on the left is at most every value on the right."],
        editorial="The straightforward answer merges and indexes, which is O(m + n) time and is what the "
                  "reference does here. The interview version binary searches the shorter list for a partition "
                  "where max(left half) ≤ min(right half); that runs in O(log(min(m, n))) and needs no merged "
                  "list at all. Both are accepted by this problem, and the follow-up question is usually \"do it "
                  "without merging\".",
        wrapper="list-pair", expected_time="O(m + n) here; O(log(min(m, n))) possible", expected_space="O(m + n)",
    ),
]

# ---------------------------------------------------------------------------
# Linked lists, trees and heaps
# ---------------------------------------------------------------------------

PROBLEMS += [
    problem(
        "middle-of-linked-list", "Middle of the Linked List", "easy",
        "Given a linked list of values, return the node at the middle: the second middle node when the length "
        "is even. The list is built for you from one line of space-separated integers, and the answer is printed "
        "as the values from that node onwards.",
        examples=[
            ex("1 2 3 4 5", "3 4 5"),
            ex("1 2", "2", "Two nodes, so the second middle is chosen."),
        ],
        topics=["linked-list", "two-pointers"],
        signature="def middle_node(head):",
        solution="""def middle_node(head):
    slow = fast = head
    while fast and fast.next:
        slow = slow.next
        fast = fast.next.next
    return slow
""",
        tests=[tc("1 2 3 4 5", "3 4 5"), tc("1 2", "2"), tc("1", "1"), tc("1 2 3 4", "3 4")],
        hints=["Counting the length first takes two passes.",
               "A slow pointer moving one node per step and a fast one moving two land the slow pointer in the "
               "middle."],
        editorial="The fast/slow pointer pattern finds the middle in one pass with no extra memory: when the fast "
                  "pointer reaches the end, the slow pointer has covered half the list. It is also the first half "
                  "of cycle detection, palindrome checks and reordering problems.",
        wrapper="linked-list",
    ),
    problem(
        "max-depth-binary-tree", "Maximum Depth of a Binary Tree", "easy",
        "Given a binary tree in level order (`None` marks a missing child), return the number of nodes on the "
        "longest path from the root down to a leaf. An empty tree has depth 0.",
        examples=[
            ex("3 9 20 None None 15 7", "3"),
            ex("1 None 2", "2"),
        ],
        topics=["tree", "recursion", "depth-first-search"],
        signature="def max_depth(root):",
        solution="""def max_depth(root):
    if root is None:
        return 0
    return 1 + max(max_depth(root.left), max_depth(root.right))
""",
        tests=[tc("3 9 20 None None 15 7", "3"), tc("1 None 2", "2"), tc("", "0"), tc("1", "1")],
        hints=["The depth of a tree is one more than the depth of its deepest child.",
               "An iterative version uses a queue of (node, depth) pairs and avoids recursion limits."],
        editorial="Recursion states the definition directly: an empty tree has depth 0, anything else is one plus "
                  "the deeper of its subtrees. O(n) time, O(h) stack space for height h. The iterative breadth-"
                  "first version counts levels instead, which is the more useful shape when the question asks for "
                  "the tree's width as well.",
        wrapper="tree",
    ),
    problem(
        "symmetric-tree", "Symmetric Tree", "easy",
        "Given a binary tree in level order, return `True` when it is a mirror image of itself around its centre: "
        "the left subtree must be the right subtree reversed at every level.",
        examples=[
            ex("1 2 2 3 4 4 3", "True"),
            ex("1 2 2 None 3 None 3", "False"),
        ],
        topics=["tree", "recursion", "breadth-first-search"],
        signature="def is_symmetric(root):",
        solution="""def is_symmetric(root):
    def mirrored(left, right):
        if left is None or right is None:
            return left is right
        return (left.value == right.value
                and mirrored(left.left, right.right)
                and mirrored(left.right, right.left))

    return root is None or mirrored(root.left, root.right)
""",
        tests=[tc("1 2 2 3 4 4 3", "True"), tc("1 2 2 None 3 None 3", "False"),
               tc("1", "True"), tc("1 2 3", "False")],
        hints=["Comparing the tree with itself is not enough - the comparison has to cross the centre.",
               "Compare left.left with right.right, and left.right with right.left."],
        editorial="A symmetry check is a recursion over two nodes at once: their values must match and their "
                  "children must be mirrored. It is easy to write the wrong recursion that compares a node with "
                  "itself, which passes one example and fails the next. O(n) time, O(h) space.",
        wrapper="tree",
    ),
    problem(
        "diameter-binary-tree", "Diameter of a Binary Tree", "medium",
        "Given a binary tree in level order, return the length of the longest path between any two nodes, "
        "measured in edges. The path does not have to pass through the root.",
        examples=[
            ex("1 2 3 4 5", "3", "4 → 2 → 1 → 3 uses three edges."),
            ex("1 2", "1"),
        ],
        topics=["tree", "recursion", "depth-first-search"],
        signature="def diameter(root):",
        solution="""def diameter(root):
    best = 0

    def depth(node):
        nonlocal best
        if node is None:
            return 0
        left = depth(node.left)
        right = depth(node.right)
        best = max(best, left + right)
        return 1 + max(left, right)

    depth(root)
    return best
""",
        tests=[tc("1 2 3 4 5", "3"), tc("1 2", "1"), tc("1", "0"), tc("1 2 3", "2")],
        hints=["The longest path through a node is the sum of the heights of its two subtrees.",
               "Compute depths bottom-up and record the best candidate as you return."],
        editorial="One post-order traversal answers both questions: each call returns its subtree's height while "
                  "recording the best left-height + right-height seen at any node. That makes it O(n) rather than "
                  "the O(n²) result of measuring the height of every node separately. The two concepts - path "
                  "length and height - are different, and mixing them up is the usual mistake.",
        wrapper="tree", expected_time="O(n)", expected_space="O(h)",
    ),
    problem(
        "kth-largest", "Kth Largest Element", "medium",
        "Line 1 is a list of integers, line 2 is `k`. Return the `k`-th largest value, counting duplicates as "
        "separate positions.",
        examples=[
            ex("[3, 2, 1, 5, 6, 4], k = 2", "5"),
            ex("[3, 2, 3, 1, 2, 4, 5, 5, 6], k = 4", "4"),
        ],
        topics=["array", "heap", "quickselect"],
        signature="def find_kth_largest(nums, k):",
        solution="""def find_kth_largest(nums, k):
    ordered = sorted(nums, reverse=True)
    return ordered[k - 1]
""",
        tests=[tc("3 2 1 5 6 4\n2", "5"), tc("3 2 3 1 2 4 5 5 6\n4", "4"), tc("1\n1", "1"),
               tc("7 7 7\n2", "7")],
        hints=["Sorting is O(n log n) and acceptable. A min-heap of size k is O(n log k).",
               "Quickselect partitions like quicksort but only recurses into the side that contains the answer, "
               "which is O(n) on average."],
        editorial="Sorting gives the answer in one line. The heap version keeps the k largest values seen so far "
                  "in a min-heap, so the answer is the root at the end. Quickselect is the expected O(n) average "
                  "answer and shares its partition step with quicksort; its worst case is still O(n²) unless the "
                  "pivot is chosen randomly.",
        wrapper="int-list-int", expected_time="O(n log n)", expected_space="O(n)",
    ),
    problem(
        "last-stone-weight", "Last Stone Weight", "easy",
        "Given stone weights, repeatedly smash the two heaviest together: equal weights both vanish, otherwise "
        "the difference remains. Return the weight of the last stone, or 0 when none is left.",
        examples=[
            ex("[2, 7, 4, 1, 8, 1]", "1"),
            ex("[1]", "1"),
        ],
        topics=["array", "heap", "simulation"],
        signature="def last_stone_weight(stones):",
        solution="""def last_stone_weight(stones):
    import heapq

    heap = [-stone for stone in stones]
    heapq.heapify(heap)
    while len(heap) > 1:
        heaviest = -heapq.heappop(heap)
        second = -heapq.heappop(heap)
        if heaviest != second:
            heapq.heappush(heap, -(heaviest - second))
    return -heap.pop() if heap else 0
""",
        tests=[tc("2 7 4 1 8 1", "1"), tc("1", "1"), tc("2 2", "0"), tc("3 3 3 3", "0")],
        hints=["The two heaviest stones change after every smash, so re-sorting each round is wasteful.",
               "Python's heapq is a min-heap: negate the weights to use it as a max-heap."],
        editorial="A max-heap (implemented as a min-heap of negated weights) always exposes the two heaviest "
                  "stones. Each round pops two and pushes at most one, so the cost is O(n log n) overall. "
                  "Simulating with sort() each iteration is O(n² log n) and is the answer this problem is "
                  "designed to rule out.",
        wrapper="int-list", expected_time="O(n log n)", expected_space="O(n)",
    ),
]

# ---------------------------------------------------------------------------
# Graphs
# ---------------------------------------------------------------------------

PROBLEMS += [
    problem(
        "number-of-islands", "Number of Islands", "medium",
        "Line 1 is a grid's row and column counts, then one line of characters per row where `1` is land and "
        "`0` is water. Return how many separate islands the grid contains, counting only horizontal and vertical "
        "connections.",
        examples=[
            ex("3 rows: 110 / 010 / 101", "3"),
        ],
        topics=["graph", "grid", "flood-fill"],
        signature="def num_islands(grid):",
        solution="""def num_islands(grid):
    if not grid:
        return 0
    rows = len(grid)
    cols = len(grid[0])
    count = 0

    def sink(r, c):
        if r < 0 or r >= rows or c < 0 or c >= cols or grid[r][c] != "1":
            return
        grid[r][c] = "0"
        sink(r + 1, c)
        sink(r - 1, c)
        sink(r, c + 1)
        sink(r, c - 1)

    for r in range(rows):
        for c in range(cols):
            if grid[r][c] == "1":
                count += 1
                sink(r, c)
    return count
""",
        tests=[tc("3 3\n110\n010\n101", "3"), tc("1 1\n0", "0"),
               tc("1 3\n111", "1"), tc("3 1\n1\n0\n1", "2")],
        hints=["Each piece of land you find that is not already part of a counted island starts a new one.",
               "Flood-fill the whole island when you find it, marking it visited, then continue the scan."],
        editorial="Scan every cell. When you find land that is still unvisited, that is a new island: increment "
                  "and flood-fill the connected land from there. Each cell is visited a constant number of times, "
                  "so it is O(rows × cols). A recursive flood fill is shortest; a queue-based one avoids recursion "
                  "limits on very large grids.",
        wrapper="grid", expected_time="O(rows × cols)", expected_space="O(rows × cols) worst case",
    ),
    problem(
        "bfs-grid-distance", "Shortest Path in a Binary Grid", "medium",
        "Line 1 gives the row and column counts, then one line of characters per row where `0` is open and `1` "
        "is blocked. Moving between open cells sharing an edge costs one step. Return the number of cells on the "
        "shortest path from the top-left to the bottom-right, or `-1` when no path exists.",
        examples=[
            ex("3 rows: 000 / 110 / 000", "5", "Path length in cells from corner to corner."),
            ex("2 rows: 01 / 10", "-1", "The start is blocked."),
        ],
        topics=["graph", "breadth-first-search", "grid"],
        signature="def shortest_path(grid):",
        solution="""def shortest_path(grid):
    from collections import deque

    size = len(grid)
    if not size or grid[0][0] != "0" or grid[size - 1][size - 1] != "0":
        return -1
    queue = deque([(0, 0, 1)])
    seen = {(0, 0)}
    while queue:
        row, col, distance = queue.popleft()
        if row == size - 1 and col == size - 1:
            return distance
        for d_row, d_col in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            next_row, next_col = row + d_row, col + d_col
            if (0 <= next_row < size and 0 <= next_col < size
                    and grid[next_row][next_col] == "0"
                    and (next_row, next_col) not in seen):
                seen.add((next_row, next_col))
                queue.append((next_row, next_col, distance + 1))
    return -1
""",
        tests=[tc("3 3\n000\n110\n000", "5"), tc("2 2\n01\n10", "-1"),
               tc("2 2\n00\n00", "3"), tc("1 1\n0", "1")],
        hints=["All edges cost the same, so breadth-first search gives the shortest path.",
               "Mark a cell visited when you enqueue it, not when you dequeue it, or the queue grows with "
               "duplicates."],
        editorial="Unweighted shortest paths are breadth-first search. Each queue entry carries its distance so "
                  "no separate distance table is needed. The visited set must be updated at enqueue time: marking "
                  "on dequeue is a subtle performance bug that turns a linear scan into one with repeated work.",
        wrapper="grid", expected_time="O(rows × cols)",
    ),
    problem(
        "rotting-oranges", "Rotting Oranges", "medium",
        "Line 1 gives grid dimensions, then one line of characters per row: `0` is empty, `1` is a fresh orange "
        "and `2` is rotten. Every minute, a rotten orange makes its fresh neighbours rot. Return how many minutes "
        "until no fresh orange remains, or `-1` if some can never rot.",
        examples=[
            ex("3 rows: 210 / 110 / 011", "4", "All oranges rot after four minutes."),
            ex("1 row: 1", "-1", "No rotten orange exists to start the spread."),
        ],
        topics=["graph", "breadth-first-search", "queue"],
        signature="def oranges_rotting(grid):",
        solution="""def oranges_rotting(grid):
    from collections import deque

    rows, cols = len(grid), len(grid[0])
    queue = deque()
    fresh = 0
    for row in range(rows):
        for col in range(cols):
            if grid[row][col] == "2":
                queue.append((row, col, 0))
            elif grid[row][col] == "1":
                fresh += 1
    minutes = 0
    while queue:
        row, col, minute = queue.popleft()
        minutes = max(minutes, minute)
        for d_row, d_col in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            next_row, next_col = row + d_row, col + d_col
            if (0 <= next_row < rows and 0 <= next_col < cols
                    and grid[next_row][next_col] == "1"):
                grid[next_row][next_col] = "2"
                fresh -= 1
                queue.append((next_row, next_col, minute + 1))
    return -1 if fresh else minutes
""",
        tests=[tc("3 3\n210\n110\n011", "4"), tc("1 1\n1", "-1"), tc("1 1\n0", "0")],
        hints=["This is a multi-source breadth-first search: every rotten orange starts in the queue at minute 0.",
               "Track the minute per orange instead of storing it in a separate structure - or process the queue "
               "level by level."],
        editorial="Seed the queue with every rotten orange and expand in rounds; the number of rounds needed to "
                  "exhaust the queue is the answer, and a leftover fresh count means some oranges are "
                  "unreachable. This is a breadcrumb-unfriendly problem to debug: write the level-by-level version "
                  "first, because it makes the minute count obvious. O(rows × cols) either way.",
        wrapper="grid", expected_time="O(rows × cols)",
    ),
    problem(
        "course-schedule", "Course Schedule", "medium",
        "Line 1 is the number of prerequisite pairs, then one `course prerequisite` pair per line. Return "
        "`True` when every course can be finished, and `False` when the requirements form a cycle.",
        examples=[
            ex("1 pair: 1 0", "True", "Course 1 needs course 0: fine."),
            ex("2 pairs: 1 0 and 0 1", "False", "The two courses need each other."),
        ],
        topics=["graph", "topological-sort", "depth-first-search"],
        signature="def can_finish(prerequisites):",
        solution="""def can_finish(prerequisites):
    graph = {}
    for course, requirement in prerequisites:
        graph.setdefault(requirement, []).append(course)

    colour = {}

    def visit(node):
        state = colour.get(node, 0)
        if state == 1:
            return False
        if state == 2:
            return True
        colour[node] = 1
        for following in graph.get(node, []):
            if not visit(following):
                return False
        colour[node] = 2
        return True

    nodes = {node for pair in prerequisites for node in pair}
    return all(visit(node) for node in nodes)
""",
        tests=[tc("1\n1 0", "True"), tc("2\n1 0\n0 1", "False"), tc("0\n", "True"),
               tc("3\n1 0\n2 1\n3 2", "True"), tc("3\n1 0\n2 1\n0 2", "False")],
        hints=["A course plan is impossible exactly when the requirement graph has a cycle.",
               "Three colours: unvisited, on the current path, and finished. A node reached again while it is on "
               "the path is the cycle."],
        editorial="Depth-first search with three states detects a cycle in one pass: white (unvisited), grey (on "
                  "the recursion path) and black (finished). Reaching a grey node proves a cycle. The alternative "
                  "is Kahn's algorithm, which repeatedly removes nodes with no prerequisites and reports failure "
                  "if any nodes remain. Both are O(courses + prerequisites).",
        wrapper="intervals", expected_time="O(V + E)",
    ),
    problem(
        "count-provinces", "Count Provinces", "medium",
        "Line 1 is the number of connections, then one `a b` pair per line indicating that node `a` is directly "
        "connected to node `b`. Return how many separate connected groups the nodes form.",
        examples=[
            ex("3 pairs: 0 1, 2 3, 4 5", "3"),
            ex("1 pair: 0 1", "1"),
        ],
        topics=["graph", "union-find", "depth-first-search"],
        signature="def count_provinces(connections):",
        solution="""def count_provinces(connections):
    parent = {}

    def find(node):
        parent.setdefault(node, node)
        while parent[node] != node:
            parent[node] = parent[parent[node]]
            node = parent[node]
        return node

    nodes = set()
    for left, right in connections:
        nodes.add(left)
        nodes.add(right)
        root_left, root_right = find(left), find(right)
        if root_left != root_right:
            parent[root_left] = root_right
    return len({find(node) for node in nodes})
""",
        tests=[tc("3\n0 1\n2 3\n4 5", "3"), tc("1\n0 1", "1"), tc("0\n", "0"),
               tc("4\n0 1\n1 2\n3 4\n4 5", "2")],
        hints=["Every new connection either merges two groups or joins two nodes already in the same one.",
               "Union-find with path compression answers this in almost constant time per connection."],
        editorial="Union-find is the natural fit: start with each node in its own group and union the endpoints of "
                  "every connection. The answer is the number of distinct roots. Path compression keeps the trees "
                  "flat, so each operation is effectively O(1). A depth-first traversal of an adjacency list gives "
                  "the same answer with the same complexity - the union-find version just reads more directly as "
                  "\"how many groups are left?\"",
        wrapper="intervals", expected_time="O(E α(V))", expected_space="O(V)",
    ),
]

# ---------------------------------------------------------------------------
# Dynamic programming
# ---------------------------------------------------------------------------

PROBLEMS += [
    problem(
        "climb-stairs", "Climbing Stairs", "easy",
        "You are climbing a staircase with `n` steps. Each move takes 1 or 2 steps. Return how many distinct "
        "ways there are to reach the top.",
        examples=[
            ex("2", "2", "1+1 or 2."),
            ex("3", "3", "1+1+1, 1+2, 2+1."),
        ],
        topics=["dynamic-programming", "recursion", "math"],
        signature="def climb_stairs(n):",
        solution="""def climb_stairs(n):
    previous, current = 1, 1
    for _ in range(n):
        previous, current = current, previous + current
    return previous
""",
        tests=[tc("0", "1"), tc("1", "1"), tc("2", "2"), tc("5", "8"), tc("10", "89")],
        hints=["The number of ways to reach step n is the number of ways to reach n-1 plus n-2.",
               "That recurrence is Fibonacci: only the last two values are ever needed."],
        editorial="Ways(n) = Ways(n-1) + Ways(n-2), because the last move was either one step or two. Naive "
                  "recursion recomputes the same values exponentially often; keeping the last two results makes it "
                  "O(n) time and O(1) space. Recognising that this is Fibonacci is half the point of the exercise.",
        wrapper="int-n",
    ),
    problem(
        "house-robber", "House Robber", "medium",
        "Given the amount of money in each house along a street, return the most you can rob without robbing two "
        "adjacent houses.",
        examples=[
            ex("[1, 2, 3, 1]", "4", "Rob houses 1 and 3."),
            ex("[2, 7, 9, 3, 1]", "12", "Rob houses 1, 3 and 5."),
        ],
        topics=["dynamic-programming", "array"],
        signature="def rob(nums):",
        solution="""def rob(nums):
    previous, current = 0, 0
    for amount in nums:
        previous, current = current, max(current, previous + amount)
    return current
""",
        tests=[tc("1 2 3 1", "4"), tc("2 7 9 3 1", "12"), tc("", "0"), tc("5", "5"),
               tc("2 1 1 2", "4")],
        hints=["At each house the decision is binary: rob it (and skip the previous) or skip it.",
               "Only the best totals for the previous two houses matter, so two variables are enough."],
        editorial="State: the best total up to house i. Transition: max(skip this house, rob it and add the best "
                  "total from two houses back). Rolling two variables keeps it O(n) time and O(1) space. The "
                  "recursive version with memoisation is easier to see the first time and is worth writing before "
                  "compressing it.",
        wrapper="int-list",
    ),
    problem(
        "longest-increasing-subsequence", "Longest Increasing Subsequence", "medium",
        "Given a list of integers, return the length of the longest strictly increasing subsequence. The values "
        "do not have to be adjacent in the original list.",
        examples=[
            ex("[10, 9, 2, 5, 3, 7, 101, 18]", "4", "2, 3, 7, 101."),
            ex("[7, 7, 7, 7]", "1"),
        ],
        topics=["dynamic-programming", "binary-search", "array"],
        signature="def length_of_lis(nums):",
        solution="""def length_of_lis(nums):
    import bisect

    tails = []
    for value in nums:
        position = bisect.bisect_left(tails, value)
        if position == len(tails):
            tails.append(value)
        else:
            tails[position] = value
    return len(tails)
""",
        tests=[tc("10 9 2 5 3 7 101 18", "4"), tc("7 7 7 7", "1"), tc("1 2 3 4", "4"),
               tc("4 3 2 1", "1"), tc("", "0")],
        hints=["The O(n²) dynamic programme is a good start: best length ending at each index.",
               "For O(n log n), keep the smallest possible tail value for each subsequence length."],
        editorial="The quadratic solution compares each element with every earlier one and records the best "
                  "length ending at that index. The faster version keeps an array where entry L is the smallest "
                  "value that can end an increasing subsequence of length L; that array is always sorted, so "
                  "binary search finds where each new value belongs. Note the array is a tool, not a real "
                  "subsequence, which is why only its length is returned.",
        wrapper="int-list", expected_time="O(n log n)", expected_space="O(n)",
    ),
    problem(
        "unique-paths", "Unique Paths", "medium",
        "A robot starts in the top-left corner of an `m × n` grid and can only move right or down. Line 1 holds "
        "`m` and line 2 holds `n` (as two integers on one line). Return how many distinct paths reach the "
        "bottom-right corner.",
        examples=[
            ex("m = 3, n = 7", "28"),
            ex("m = 3, n = 2", "3"),
        ],
        topics=["dynamic-programming", "math", "grid"],
        signature="def unique_paths(m, n):",
        solution="""def unique_paths(m, n):
    row = [1] * n
    for _ in range(m - 1):
        for column in range(1, n):
            row[column] += row[column - 1]
    return row[-1]
""",
        tests=[tc("3 7", "28"), tc("3 2", "3"), tc("1 1", "1"), tc("7 3", "28")],
        hints=["Every cell can only be reached from the cell above it or the cell to its left.",
               "One row of the table is enough: each row is built from the previous one in place."],
        editorial="Paths to a cell equal the sum of paths to the cell above and the cell to the left, with the "
                  "first row and first column fixed at 1. A single array updated left to right turns the O(m·n) "
                  "table into O(n) space. The closed form C(m+n-2, m-1) exists and is O(min(m, n)) work with big "
                  "integers, and is a nice thing to mention after the table works.",
        wrapper="int-int", expected_time="O(m × n)", expected_space="O(n)",
    ),
    problem(
        "partition-equal-subset", "Partition Equal Subset Sum", "medium",
        "Given a list of positive integers, return `True` when it can be split into two groups with equal sums.",
        examples=[
            ex("[1, 5, 11, 5]", "True", "1 + 5 + 5 = 11."),
            ex("[1, 2, 3, 5]", "False"),
        ],
        topics=["dynamic-programming", "subset-sum", "array"],
        signature="def can_partition(nums):",
        solution="""def can_partition(nums):
    total = sum(nums)
    if total % 2:
        return False
    target = total // 2
    reachable = {0}
    for value in nums:
        reachable |= {total_so_far + value for total_so_far in reachable
                      if total_so_far + value <= target}
    return target in reachable
""",
        tests=[tc("1 5 11 5", "True"), tc("1 2 3 5", "False"), tc("1 1", "True"),
               tc("2 2 3 5", "False"), tc("10 1 1 1 1 1 1 1 1 1 1", "True")],
        hints=["An odd total can never be split evenly.",
               "The question becomes: can some subset sum to half the total?",
               ],
        editorial="Reduce to subset sum: an odd total is impossible, otherwise ask whether any subset reaches "
                  "the half-total. A boolean set (or bitmask) of reachable sums is updated per value; the bitmask "
                  "version is O(n · total / 64) and is a good follow-up. The greedy \"always add to the smaller "
                  "side\" idea is wrong, and this problem exists to show why.",
        wrapper="int-list", expected_time="O(n × target)",
    ),
    problem(
        "max-product-subarray", "Maximum Product Subarray", "medium",
        "Given a list of integers, return the largest product that can be obtained from a contiguous subarray.",
        examples=[
            ex("[2, 3, -2, 4]", "6", "2 × 3."),
            ex("[-2, 0, -1]", "0"),
        ],
        topics=["dynamic-programming", "array"],
        signature="def max_product(nums):",
        solution="""def max_product(nums):
    best = current_max = current_min = nums[0]
    for value in nums[1:]:
        candidates = (value, value * current_max, value * current_min)
        current_max, current_min = max(candidates), min(candidates)
        best = max(best, current_max)
    return best
""",
        tests=[tc("2 3 -2 4", "6"), tc("-2 0 -1", "0"), tc("-2 3 -4", "24"), tc("2 -5 -2 -4 3", "24")],
        hints=["A negative multiplier turns the smallest product into the largest one.",
               "Track both the maximum and the minimum product ending at each position."],
        editorial="Unlike the sum version, the best answer at a position depends on both the largest and the "
                  "smallest product ending at the previous position, because multiplying by a negative swaps "
                  "them. Carrying two values keeps it O(n) with O(1) space. Forgetting the minimum is the exact "
                  "bug the negative test cases exist to catch.",
        wrapper="int-list",
    ),
    problem(
        "longest-palindromic-substring", "Longest Palindromic Substring", "medium",
        "Given a line of text, return the longest substring that reads the same forwards and backwards. Return "
        "the first such substring when several are equally long.",
        examples=[
            ex("babad", "bab", "aba is equally long but bab appears first."),
            ex("cbbd", "bb"),
        ],
        topics=["string", "dynamic-programming", "two-pointers"],
        signature="def longest_palindrome(text):",
        solution="""def longest_palindrome(text):
    if not text:
        return ""
    start, end = 0, 0

    def expand(left, right):
        while left >= 0 and right < len(text) and text[left] == text[right]:
            left -= 1
            right += 1
        return left + 1, right - 1

    for index in range(len(text)):
        for left, right in (expand(index, index), expand(index, index + 1)):
            if right - left > end - start:
                start, end = left, right
    return text[start:end + 1]
""",
        tests=[tc("babad", "bab"), tc("cbbd", "bb"), tc("a", "a"), tc("forgeeksskeegfor", "geeksskeeg")],
        hints=["Every palindrome has a centre: either one character or the gap between two.",
               "Expand outward from each of the 2n-1 centres and keep the longest.",
               ],
        editorial="Expanding around centres finds the answer in O(n²) time and O(1) space, and it is far easier "
                  "to get right than the O(n) Manacher's algorithm. Each of the 2n-1 centres expands until the "
                  "characters differ; that finds every palindrome because every palindrome has exactly one centre. "
                  "The dynamic-programming formulation (is substring i..j a palindrome?) is another O(n²) route "
                  "with O(n²) space.",
        wrapper="string-int", expected_time="O(n²)",
    ),
    problem(
        "edit-distance", "Edit Distance", "hard",
        "Line 1 is the source word, line 2 is the target word. Return the minimum number of single-character "
        "insertions, deletions or replacements needed to turn the source into the target.",
        examples=[
            ex("horse → ros", "3"),
            ex("intention → execution", "5"),
        ],
        topics=["dynamic-programming", "string"],
        signature="def edit_distance(source, target):",
        solution="""def edit_distance(source, target):
    previous = list(range(len(target) + 1))
    for i, source_char in enumerate(source, 1):
        current = [i]
        for j, target_char in enumerate(target, 1):
            current.append(min(
                previous[j] + 1,
                current[j - 1] + 1,
                previous[j - 1] + (source_char != target_char),
            ))
        previous = current
    return previous[-1]
""",
        tests=[tc("horse\nros", "3"), tc("intention\nexecution", "5"), tc("abc\nabc", "0"),
               tc("\nabc", "3"), tc("kitten\nsitting", "3")],
        hints=["Think of the table: rows are prefixes of the source, columns prefixes of the target.",
               "The three neighbours in the table are deletion, insertion and replacement; the diagonal is free "
               "when the characters match."],
        editorial="The classic tabulation: cell (i, j) is the cost of converting the first i source characters "
                  "into the first j target characters, taking the minimum of delete, insert and replace. Keeping "
                  "only the previous row makes it O(n·m) time with O(m) space. There is no faster general "
                  "algorithm, which is why the answer is always the table.",
        wrapper="two-lines", expected_time="O(n × m)", expected_space="O(m)",
    ),
    problem(
        "word-break", "Word Break", "hard",
        "Line 1 is the string to build, line 2 is a line of dictionary words separated by spaces. Return `True` "
        "when the string can be split entirely into dictionary words, reusing words as often as needed.",
        examples=[
            ex("leetcode / leet code", "True"),
            ex("catsandog / cats dog sand and cat", "False"),
        ],
        topics=["dynamic-programming", "string", "trie"],
        signature="def word_break(text, words):",
        solution="""def word_break(text, words):
    dictionary = set(words.split())
    reachable = [False] * (len(text) + 1)
    reachable[0] = True
    for end in range(1, len(text) + 1):
        for start in range(end):
            if reachable[start] and text[start:end] in dictionary:
                reachable[end] = True
                break
    return reachable[len(text)]
""",
        tests=[tc("leetcode\nleet code", "True"), tc("catsandog\ncats dog sand and cat", "False"),
               tc("applepenapple\napple pen", "True"), tc("a\nb", "False"), tc("a\na", "True")],
        hints=["Define reachable[i] as \"the first i characters can be built\".",
               "For each end position, look for any earlier reachable position where the slice between them is a "
               "dictionary word."],
        editorial="A one-dimensional dynamic programme over prefixes: reachable[0] is true, and reachable[end] is "
                  "true if some reachable[start] has text[start:end] in the dictionary. O(n²) time with a set of "
                  "words, or O(n·w) with a trie that walks forward instead of re-slicing. Greedy matching takes "
                  "the longest word first and is wrong - \"catsandog\" is the standard counter-example.",
        wrapper="two-lines", expected_time="O(n²)", expected_space="O(n)",
    ),
]
