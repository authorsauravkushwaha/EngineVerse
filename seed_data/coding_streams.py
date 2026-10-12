"""Stream problem bank: the problems that make the sheets fit a branch.

A mechanical learner and a cyber-security learner should not be handed the same
sheet list. The core bank in ``coding_core.py`` teaches patterns every software
interview asks about; this module is the other half - computation that arises
*inside* a discipline, written so that it is still real programming practice and
still judged the same way.

The mapping from branch to sheet lives in ``engineverse.hub.STREAM_SHEETS`` and
the sheets themselves in ``coding_sheets.py``; nothing here knows which branch
reads it, which keeps the content in one place and the routing in another.

Every problem here is still a Python function with test cases, so the judge, the
editor, XP and the mistake notebook all work exactly as they do for the core
bank. "Engineering computing" is not a lesser tier of the platform - it is a
different set of inputs.
"""
from __future__ import annotations

from .coding_common import ex, problem, tc

PROBLEMS: list[dict] = []

# ---------------------------------------------------------------------------
# Engineering computing - numerical methods and physical calculations
# ---------------------------------------------------------------------------

PROBLEMS += [
    problem(
        "bisection-iterations", "Bisection Method: Iterations to Converge", "medium",
        "The bisection method finds a root of `f(x) = x³ - 2x - 5` by halving an interval that brackets the "
        "root. Given the integer bounds `a` and `b` on one line, return how many halvings it takes before the "
        "interval is at most `1e-6` wide. That count is the number of function evaluations a real solver would "
        "perform, and knowing it is how you decide whether a tolerance is affordable.",
        examples=[
            ex("a = 2, b = 3", "20", "A width of 1 halved 20 times is below 1e-6."),
            ex("a = 2, b = 4", "21", "A width of 2 needs one more halving."),
        ],
        topics=["numerical-methods", "engineering-computing", "loops"],
        company="engineering computing",
        signature="def bisection_iterations(a, b):",
        solution="""def bisection_iterations(a, b):
    low, high = float(a), float(b)
    iterations = 0
    while high - low > 1e-6:
        middle = (low + high) / 2
        if f(low) * f(middle) <= 0:
            high = middle
        else:
            low = middle
        iterations += 1
    return iterations


def f(x):
    return x ** 3 - 2 * x - 5
""",
        tests=[tc("2 3", "20"), tc("2 4", "21"), tc("1 3", "21"), tc("2 2", "0")],
        hints=["Each step halves the interval, so the count depends only on its initial width.",
               "The number of evaluations is ceil(log2(width / tolerance)) - the loop is the honest way to "
               "check it."],
        editorial="The loop halves the bracket until its width is within tolerance, which is exactly what a "
                  "textbook bisection implementation does. The answer is a closed form - "
                  "`ceil(log2((b-a)/1e-6))` - but writing the loop shows why: bisection gains one bit of accuracy "
                  "per evaluation, so a tolerance of 1e-6 costs about 20 evaluations no matter how good the "
                  "bracket is. That is why Newton's method, which converges quadratically, exists.",
        wrapper="int-int", expected_time="O(log((b-a)/tolerance))",
    ),
    problem(
        "trapezoid-integral", "Trapezoid Rule for ∫x²", "easy",
        "Approximate the integral of `f(x) = x²` from `a` to `b` with the trapezoid rule using 100 strips, "
        "rounded to the nearest integer. The two integer bounds are on one line.",
        examples=[
            ex("0 3", "9", "The exact integral is 9, and 100 strips are plenty."),
            ex("1 4", "21", "4³/3 - 1³/3 = 21."),
        ],
        topics=["numerical-methods", "engineering-computing", "math"],
        company="engineering computing",
        signature="def trapezoid_integral(a, b):",
        solution="""def trapezoid_integral(a, b):
    strips = 100
    width = (b - a) / strips
    total = (f(a) + f(b)) / 2
    for step in range(1, strips):
        total += f(a + step * width)
    return round(total * width)


def f(x):
    return x * x
""",
        tests=[tc("0 3", "9"), tc("1 4", "21"), tc("2 5", "39"), tc("0 0", "0")],
        hints=["The trapezoid rule weights the two endpoints half and every interior point once.",
               "The composite version over n strips is exact for a straight line, which is why 100 strips gets "
               "a parabola to the nearest integer."],
        editorial="Composite trapezoid rule: sum the endpoints at half weight, add every interior point, and "
                  "multiply by the strip width. With 100 strips the error is below the rounding threshold for "
                  "these bounds, so the rounded result matches the exact integral. Simpson's rule with the same "
                  "number of points is more accurate, and worth mentioning as the follow-up.",
        wrapper="int-int",
    ),
    problem(
        "matrix-determinant-2x2", "Determinant of a 2×2 Matrix", "easy",
        "Line 1 gives the row and column counts, then one line of row entries each. Return the determinant "
        "`ad - bc` of the 2×2 matrix.",
        examples=[
            ex("[[1, 2], [3, 4]]", "-2"),
            ex("[[2, 0], [0, 5]]", "10"),
        ],
        topics=["matrix", "engineering-computing", "linear-algebra"],
        company="engineering computing",
        signature="def determinant(matrix):",
        solution="""def determinant(matrix):
    return matrix[0][0] * matrix[1][1] - matrix[0][1] * matrix[1][0]
""",
        tests=[tc("2 2\n1 2\n3 4", "-2"), tc("2 2\n2 0\n0 5", "10"),
               tc("2 2\n0 1\n1 0", "-1")],
        hints=["For a 2×2 matrix the determinant is the product of the main diagonal minus the product of the "
               "other one.",
               "A zero determinant means the rows are linearly dependent - the matrix has no inverse."],
        editorial="The 2×2 determinant is the signed area scaling factor of the matrix: it says how much the "
                  "transformation stretches area, and a negative sign means it also flips orientation. The 3×3 "
                  "rule of Sarrus is the same idea with more terms; beyond that the Laplace expansion or LU "
                  "decomposition is how it is actually computed.",
        wrapper="matrix",
    ),
    problem(
        "matrix-transpose", "Transpose a Matrix", "easy",
        "Line 1 gives the row and column counts, then one line of row entries each. Return the transposed "
        "matrix: rows become columns.",
        examples=[
            ex("[[1, 2, 3], [4, 5, 6]]", "1 4 / 2 5 / 3 6"),
            ex("[[1], [2]]", "1 2"),
        ],
        topics=["matrix", "engineering-computing", "arrays"],
        company="engineering computing",
        signature="def transpose(matrix):",
        solution="""def transpose(matrix):
    return [list(row) for row in zip(*matrix)]
""",
        tests=[tc("2 3\n1 2 3\n4 5 6", "1 4\n2 5\n3 6"), tc("2 1\n1\n2", "1 2"),
               tc("1 1\n7", "7")],
        hints=["Element (i, j) of the answer is element (j, i) of the input.",
               "`zip(*matrix)` pairs up the nth elements of every row."],
        editorial="Transposition is a reindexing: what was element (i, j) becomes (j, i), so the shape flips from "
                  "m×n to n×m. In NumPy this is `.T`, and in matrix algebra it is the operation that makes "
                  "`AᵀA` square - the first step of least squares. Time O(m·n), and the only care needed is "
                  "producing lists rather than tuples.",
        wrapper="matrix", expected_time="O(m × n)", expected_space="O(m × n)",
    ),
    problem(
        "dot-product", "Dot Product of Two Vectors", "easy",
        "Line 1 and line 2 are two vectors of the same length, space-separated. Return their dot product. "
        "Return `0` for two empty lines.",
        examples=[
            ex("[1, 2, 3] · [4, 5, 6]", "32", "4 + 10 + 18."),
            ex("[1, 0] · [0, 1]", "0", "Perpendicular vectors."),
        ],
        topics=["engineering-computing", "linear-algebra", "arrays"],
        company="engineering computing",
        signature="def dot_product(a, b):",
        solution="""def dot_product(a, b):
    return sum(left * right for left, right in zip(a, b))
""",
        tests=[tc("1 2 3\n4 5 6", "32"), tc("1 0\n0 1", "0"), tc("-1 2\n3 4", "5"),
               tc("\n", "0")],
        hints=["Multiply element-wise and add.",
               "`zip` stops at the shorter list, which is the behaviour the empty case needs."],
        editorial="The dot product projects one vector onto another: it is zero for perpendicular vectors, "
                  "negative when they point in opposite directions, and it is the work done by a force along a "
                  "displacement. In matrix terms it is a 1×n times an n×1 product, which is why the lengths must "
                  "agree.",
        wrapper="list-pair",
    ),
    problem(
        "resistors-parallel", "Equivalent Resistance in Parallel", "easy",
        "Given resistor values in ohms on one line, return the equivalent resistance of the parallel network, "
        "rounded to the nearest ohm.",
        examples=[
            ex("[2, 2]", "1"),
            ex("[10, 10, 10]", "3", "10/3 rounded to the nearest ohm."),
        ],
        topics=["engineering-computing", "electronics", "circuits"],
        company="engineering computing",
        signature="def parallel_resistance(values):",
        solution="""def parallel_resistance(values):
    if not values:
        return 0
    total = 1 / sum(1 / value for value in values)
    return round(total)
""",
        tests=[tc("2 2", "1"), tc("10 10 10", "3"), tc("4 12", "3"), tc("100", "100")],
        hints=["The conductances add: 1/R = 1/R₁ + 1/R₂ + …",
               "Invert at the very end, or every intermediate result is wrong."],
        editorial="Equivalent resistance in parallel is the reciprocal of the sum of conductances. Two immediate "
                  "consequences fall out of the formula: the equivalent resistance is always smaller than the "
                  "smallest branch, and adding a branch can only lower it. Rounding to the nearest ohm is a stand-"
                  "in for a tolerance check, which is how a real lab report would phrase the answer.",
        wrapper="int-list",
    ),
    problem(
        "reynolds-number", "Reynolds Number", "easy",
        "Water flowing in a pipe has velocity `v` in m/s and pipe diameter `d` in millimetres, given as two "
        "integers on one line. Using density 1000 kg/m³ and dynamic viscosity 0.001 Pa·s, return the Reynolds "
        "number `Re = ρvd/μ` as an integer.",
        examples=[
            ex("v = 1, d = 50", "50000"),
            ex("v = 3, d = 40", "120000"),
        ],
        topics=["engineering-computing", "fluid-mechanics", "math"],
        company="engineering computing",
        signature="def reynolds_number(v, d):",
        solution="""def reynolds_number(v, d):
    density = 1000.0
    viscosity = 0.001
    diameter_metres = d / 1000.0
    return int(round(density * v * diameter_metres / viscosity))
""",
        tests=[tc("1 50", "50000"), tc("3 40", "120000"), tc("2 25", "50000"),
               tc("1 10", "10000")],
        hints=["Convert millimetres to metres before substituting - the formula is in SI units.",
               "With water at 20 °C, Re above about 4000 means turbulent flow."],
        editorial="Reynolds number is the ratio of inertial to viscous forces, and it is dimensionless - which is "
                  "exactly why it predicts behaviour across different pipe sizes and fluids. Laminar flow below "
                  "roughly 2300, transitional in between and turbulent above about 4000 are the usual engineering "
                  "thresholds. Unit conversion is where the marks are lost in practice.",
        wrapper="int-int",
    ),
    problem(
        "gear-ratio", "Gear Ratio in Lowest Terms", "easy",
        "A driver gear with `t1` teeth meshes with a driven gear of `t2` teeth, given as two integers on one "
        "line. Return the ratio as a string in lowest terms, `t1:t2`.",
        examples=[
            ex("12, 36", "1:3", "One turn of the driver turns the driven gear a third of a turn."),
            ex("20, 15", "4:3"),
        ],
        topics=["engineering-computing", "mechanics", "number-theory"],
        company="engineering computing",
        signature="def gear_ratio(t1, t2):",
        solution="""def gear_ratio(t1, t2):
    from math import gcd

    divisor = gcd(t1, t2) or 1
    return f"{t1 // divisor}:{t2 // divisor}"
""",
        tests=[tc("12 36", "1:3"), tc("20 15", "4:3"), tc("7 7", "1:1"), tc("8 12", "2:3")],
        hints=["Divide both numbers by their greatest common divisor.",
               "The ratio is teeth-driven-to-teeth-driver, so keeping the order matters."],
        editorial="Reducing a ratio means dividing both terms by their greatest common divisor, which is Euclid's "
                  "algorithm. The engineering reason to reduce it is that only the reduced form tells you the "
                  "number of revolutions per tooth cycle - a 12:36 pair and a 1:3 pair behave identically on the "
                  "shaft but not in the gearbox drawing.",
        wrapper="int-int",
    ),
    problem(
        "prime-factorization", "Prime Factorisation", "medium",
        "Given an integer greater than 1 on its own line, return its prime factors in ascending order, with "
        "repeats: the factorisation `12` is `[2, 2, 3]`.",
        examples=[
            ex("12", "[2, 2, 3]"),
            ex("97", "[97]", "97 is prime, so the factorisation is itself."),
        ],
        topics=["engineering-computing", "number-theory", "math"],
        company="engineering computing",
        signature="def prime_factors(n):",
        solution="""def prime_factors(n):
    factors = []
    divisor = 2
    while divisor * divisor <= n:
        while n % divisor == 0:
            factors.append(divisor)
            n //= divisor
        divisor += 1
    if n > 1:
        factors.append(n)
    return factors
""",
        tests=[tc("12", "[2, 2, 3]"), tc("97", "[97]"), tc("2", "[2]"), tc("100", "[2, 2, 5, 5]"),
               tc("1024", "[2, 2, 2, 2, 2, 2, 2, 2, 2, 2]")],
        hints=["Trial division by every integer works, but the loop can stop at √n.",
               "Whatever remains after the loop is greater than 1 is prime."],
        editorial="Trial division finds the factors in ascending order. The subtle part is the final check: after "
                  "the loop stops, any remainder greater than 1 is a prime larger than √n. Stopping at √n makes "
                  "the worst case O(√n), which is why RSA uses numbers with hundreds of digits - factoring those "
                  "is exactly this hard problem at scale.",
        wrapper="int-n", expected_time="O(√n)",
    ),
]

# ---------------------------------------------------------------------------
# Digital logic and signals
# ---------------------------------------------------------------------------

PROBLEMS += [
    problem(
        "count-set-bits", "Count Set Bits", "easy",
        "Given a non-negative integer on its own line, return how many bits are set to 1 in its binary "
        "representation - the Hamming weight.",
        examples=[
            ex("11", "3", "1011 has three set bits."),
            ex("128", "1"),
        ],
        topics=["bit-manipulation", "digital-logic", "electronics"],
        company="digital and embedded",
        signature="def count_set_bits(n):",
        solution="""def count_set_bits(n):
    count = 0
    while n:
        n &= n - 1
        count += 1
    return count
""",
        tests=[tc("11", "3"), tc("128", "1"), tc("0", "0"), tc("255", "8"), tc("1023", "10")],
        hints=["`bin(n).count('1')` is the one-liner; the interesting version clears the lowest set bit.",
               "`n & (n - 1)` removes the rightmost set bit, so the loop runs once per set bit."],
        editorial="The `n & (n - 1)` trick clears the lowest set bit, so the loop iterates exactly as many times "
                  "as there are ones rather than once per bit position. That matters in embedded code where the "
                  "loop budget is real. Python's `bin(n).count('1')` is faster in practice because the loop runs "
                  "in C, and modern CPUs have a POPCNT instruction for exactly this.",
        wrapper="int-n", expected_time="O(number of set bits)",
    ),
    problem(
        "single-number", "Single Number", "easy",
        "Every value in a list appears twice except one, which appears once. Return that value. The solution "
        "must use constant extra space.",
        examples=[
            ex("[4, 1, 2, 1, 2]", "4"),
            ex("[1, 1, 7]", "7"),
        ],
        topics=["bit-manipulation", "xor", "digital-logic"],
        company="digital and embedded",
        signature="def single_number(nums):",
        solution="""def single_number(nums):
    result = 0
    for value in nums:
        result ^= value
    return result
""",
        tests=[tc("4 1 2 1 2", "4"), tc("1 1 7", "7"), tc("5", "5"), tc("0 1 1", "0")],
        hints=["A dictionary works but uses O(n) space, which the problem forbids.",
               "XOR is its own inverse: x ^ x = 0, and x ^ 0 = x."],
        editorial="XOR every value. Pairs cancel to zero because XOR is associative and `x ^ x = 0`, leaving only "
                  "the unmatched value. This is the same property error-detecting codes rely on, and it is why a "
                  "parity bit works. One pass, one integer of extra space.",
        wrapper="int-list",
    ),
    problem(
        "gray-code-sequence", "Generate Gray Codes", "medium",
        "Given a bit width `n` on its own line, return the first `2ⁿ` Gray codes in sequence as integers. "
        "Consecutive codes may differ in exactly one bit.",
        examples=[
            ex("2", "[0, 1, 3, 2]"),
            ex("3", "[0, 1, 3, 2, 6, 7, 5, 4]"),
        ],
        topics=["bit-manipulation", "digital-logic", "vlsi"],
        company="digital and embedded",
        signature="def gray_codes(n):",
        solution="""def gray_codes(n):
    return [value ^ (value >> 1) for value in range(1 << n)]
""",
        tests=[tc("1", "[0, 1]"), tc("2", "[0, 1, 3, 2]"), tc("3", "[0, 1, 3, 2, 6, 7, 5, 4]"),
               tc("0", "[0]")],
        hints=["The k-th Gray code is `k ^ (k >> 1)`.",
               "Check the property on the sequence: each step flips exactly one bit."],
        editorial="Gray codes change one bit at a time, which is why rotary encoders and Karnaugh maps use them: "
                  "a one-bit change can only ever read as the old value or the new one, never as a third code. "
                  "The reflected binary formula `k ^ (k >> 1)` generates the whole sequence in order. The inverse "
                  "conversion folds bits back the other way.",
        wrapper="int-n", expected_time="O(2ⁿ)", expected_space="O(2ⁿ)",
    ),
    problem(
        "hamming-distance", "Hamming Distance", "easy",
        "Two non-negative integers are on one line. Return how many bit positions differ between their binary "
        "representations.",
        examples=[
            ex("1, 4", "2", "001 and 100 differ in two positions."),
            ex("7, 7", "0"),
        ],
        topics=["bit-manipulation", "digital-logic", "error-correction"],
        company="digital and embedded",
        signature="def hamming_distance(a, b):",
        solution="""def hamming_distance(a, b):
    difference = a ^ b
    return bin(difference).count("1")
""",
        tests=[tc("1 4", "2"), tc("7 7", "0"), tc("0 0", "0"), tc("255 0", "8"), tc("10 15", "2")],
        hints=["XOR marks exactly the positions that differ.",
               "Counting those set bits is the previous problem's job."],
        editorial="XOR the pair: every differing bit becomes 1 and every matching bit becomes 0, so the answer is "
                  "the Hamming weight of the result. Hamming distance measures how many single-bit errors a code "
                  "can detect, which is why a code with distance 3 can correct one error - the cornerstone of ECC "
                  "memory and RAID.",
        wrapper="int-int",
    ),
    problem(
        "even-parity", "Even Parity Bit", "easy",
        "A line of 0s and 1s is a data word sent over a link. Return the parity bit that must be appended so "
        "the total number of 1s is even: `0` when the word already has an even count, `1` otherwise.",
        examples=[
            ex("1 0 1 1", "1", "There are three ones, so one more is needed."),
            ex("1 0 1", "0"),
        ],
        topics=["bit-manipulation", "digital-logic", "error-detection"],
        company="digital and embedded",
        signature="def parity_bit(bits):",
        solution="""def parity_bit(bits):
    ones = sum(1 for bit in bits if bit == "1")
    return 1 if ones % 2 else 0
""",
        tests=[tc("1 0 1 1", "1"), tc("1 0 1", "0"), tc("0 0", "0"), tc("1 1 1 1 1", "1")],
        hints=["Count the ones and take it modulo 2.",
               "The parity bit is the XOR of every bit in the word."],
        editorial="A single parity bit detects any odd number of flipped bits and no even number of them. It is "
                  "the cheapest error detection there is, and its weakness - two errors cancel - is exactly why "
                  "CRC and Hamming codes exist. The XOR version generalises: CRC is a polynomial version of the "
                  "same idea.",
        wrapper="string-list",
    ),
    problem(
        "xor-checksum", "XOR Checksum", "easy",
        "Given a line of text on its own line, return the XOR of the ASCII codes of its characters as an "
        "integer. Return `0` for an empty line.",
        examples=[
            ex("AB", "3", "65 ^ 66 = 3."),
            ex("A", "65"),
        ],
        topics=["bit-manipulation", "networking", "error-detection"],
        company="digital and embedded",
        signature="def xor_checksum(text):",
        solution="""def xor_checksum(text):
    checksum = 0
    for character in text:
        checksum ^= ord(character)
    return checksum
""",
        tests=[tc("AB", "3"), tc("A", "65"), tc("hello", "98"), tc("", "0")],
        hints=["`ord()` gives a character's code point.",
               "Fold each code into a running XOR, starting from zero."],
        editorial="An XOR checksum is the simplest longitudinal check: byte order does not matter, a repeated "
                  "byte cancels, and the result fits in one byte. Protocols such as NMEA sentences use exactly "
                  "this. It catches every single-byte error and no two-byte error, which is why stronger "
                  "checksums replaced it wherever the cost is affordable.",
        wrapper="string-int",
    ),
    problem(
        "binary-gap", "Binary Gap", "medium",
        "Given a positive integer on its own line, return the length of its longest run of zeros that is "
        "bracketed on both sides by ones. Return `0` when there is no such run.",
        examples=[
            ex("9", "2", "1001 has a gap of two zeros."),
            ex("15", "0", "1111 has no zeros at all."),
        ],
        topics=["bit-manipulation", "digital-logic", "loops"],
        company="digital and embedded",
        signature="def binary_gap(n):",
        solution="""def binary_gap(n):
    best = 0
    current = None
    while n:
        if n & 1:
            if current is not None and current > best:
                best = current
            current = 0
        elif current is not None:
            current += 1
        n >>= 1
    return best
""",
        tests=[tc("9", "2"), tc("15", "0"), tc("20", "1"), tc("529", "4"),
               tc("1041", "5")],
        hints=["Scan the bits from the least significant end and keep a running count of zeros.",
               "Only start counting after the first one you see, or leading zeros are counted as a gap."],
        editorial="This is a state machine over the bit stream: before the first one, zeros are ignored; after it, "
                  "zeros accumulate until the next one closes the gap. The `current is None` guard is the whole "
                  "problem - the naive `bin(n).strip('0b0')` split counts leading zeros and gives a wrong answer "
                  "for powers of two. O(bits) time, O(1) space.",
        wrapper="int-n",
    ),
    problem(
        "decibels", "Power Ratio in Decibels", "easy",
        "Two integers on one line are a measured power `p1` and a reference power `p0`. Return the ratio in "
        "decibels, `10·log10(p1/p0)`, rounded to the nearest integer.",
        examples=[
            ex("100, 1", "20"),
            ex("2, 1", "3", "The doubling of power is about 3 dB."),
        ],
        topics=["signals", "electronics", "math"],
        company="digital and embedded",
        signature="def decibels(p1, p0):",
        solution="""def decibels(p1, p0):
    from math import log10

    return round(10 * log10(p1 / p0))
""",
        tests=[tc("100 1", "20"), tc("2 1", "3"), tc("1 1", "0"), tc("1000 1", "30"),
               tc("10 1", "10")],
        hints=["A decade of power is 10 dB; doubling is about 3 dB.",
               "For amplitudes rather than powers the factor is 20, not 10."],
        editorial="The decibel is a logarithmic ratio, so multiplication becomes addition: cascading two 3 dB "
                  "losses gives 6 dB. Rounding to the nearest integer makes the answer clean, but in a signal "
                  "chain the fractional part is what accumulates into a link budget - which is why the amplitude "
                  "form uses 20·log10 for the same scale.",
        wrapper="int-int",
    ),
    problem(
        "rms-value", "RMS of a Sampled Signal", "medium",
        "One line holds sampled amplitudes of a periodic signal. Return the root-mean-square value, rounded to "
        "the nearest integer.",
        examples=[
            ex("[3, 4]", "4", "√12.5 ≈ 3.54."),
            ex("[6, 8]", "7"),
        ],
        topics=["signals", "electronics", "statistics"],
        company="digital and embedded",
        signature="def rms(values):",
        solution="""def rms(values):
    if not values:
        return 0
    mean_square = sum(value * value for value in values) / len(values)
    return round(mean_square ** 0.5)
""",
        tests=[tc("3 4", "4"), tc("6 8", "7"), tc("0 0 0", "0"), tc("5 5 5 5", "5"),
               tc("1 2 3 4", "3")],
        hints=["Square first, then average, then take the square root - the order is the name.",
               "RMS is not the average of the absolute values; for a sine wave it is peak/√2."],
        editorial="RMS squares, averages and then roots, which is why it measures the equivalent steady value "
                  "that would deliver the same power as the alternating signal. For a pure sine the factor is "
                  "1/√2 ≈ 0.707 of the peak, a number worth knowing by heart in electronics. The square-then-root "
                  "order also means a few large samples dominate the result.",
        wrapper="int-list",
    ),
]

# ---------------------------------------------------------------------------
# Data analysis and machine learning
# ---------------------------------------------------------------------------

PROBLEMS += [
    problem(
        "mean-median-mode", "Mean, Median and Mode", "easy",
        "Given a line of integers, return `[mean, median, mode]`. The mean is the integer part of the average, "
        "the median is the middle value (the smaller of the two middle values when the count is even), and the "
        "mode is the most frequent value, breaking ties by taking the smallest.",
        examples=[
            ex("[1, 2, 2, 3, 5]", "[2, 2, 2]"),
        ],
        topics=["statistics", "data-analysis", "arrays"],
        company="data and AI",
        signature="def summarise(values):",
        solution="""def summarise(values):
    ordered = sorted(values)
    count = len(ordered)
    mean = sum(ordered) // count
    if count % 2:
        median = ordered[count // 2]
    else:
        median = min(ordered[count // 2 - 1], ordered[count // 2])
    counts = {}
    for value in ordered:
        counts[value] = counts.get(value, 0) + 1
    mode = max(sorted(counts), key=lambda value: counts[value])
    return [mean, median, mode]
""",
        tests=[tc("1 2 2 3 5", "[2, 2, 2]"), tc("1 2 3 4", "[2, 2, 1]"),
               tc("7", "[7, 7, 7]"), tc("5 5 6 6 6", "[5, 6, 6]")],
        hints=["Sorting once answers the median and makes the mode count straightforward.",
               "The mean is integer division on purpose, so the output stays deterministic."],
        editorial="Mean, median and mode answer different questions about the same data: the mean is sensitive to "
                  "every value, the median is not, and the mode is the only one that works for categorical data. "
                  "That difference is why a salary report usually quotes the median - one outlier moves the mean "
                  "and leaves the median alone.",
        wrapper="int-list",
    ),
    problem(
        "standard-deviation", "Population Standard Deviation", "medium",
        "Given a line of integers, return the population standard deviation (divide by n, not n−1), rounded to "
        "the nearest integer.",
        examples=[
            ex("[2, 4, 4, 4, 5, 5, 7, 9]", "2", "The classic textbook data set."),
            ex("[5, 5, 5]", "0"),
        ],
        topics=["statistics", "data-analysis", "math"],
        company="data and AI",
        signature="def standard_deviation(values):",
        solution="""def standard_deviation(values):
    count = len(values)
    mean = sum(values) / count
    variance = sum((value - mean) ** 2 for value in values) / count
    return round(variance ** 0.5)
""",
        tests=[tc("2 4 4 4 5 5 7 9", "2"), tc("5 5 5", "0"), tc("1 3", "1"), tc("10 20 30", "8")],
        hints=["Compute the mean first, then the average squared deviation from it.",
               "Dividing by n gives the population figure; dividing by n−1 gives the sample estimate."],
        editorial="Standard deviation is the square root of the mean squared deviation, which makes it the typical "
                  "distance from the mean in the same units as the data. The n versus n−1 distinction is real: "
                  "dividing by n−1 (Bessel's correction) removes the bias when the data is a sample rather than "
                  "the whole population. Mixing them up is the most common statistics mistake in student reports.",
        wrapper="int-list",
    ),
    problem(
        "moving-average", "Simple Moving Average", "easy",
        "Given a line of integers, return the simple moving average with a window of three, rounded to the "
        "nearest integer. A series shorter than three values returns no averages.",
        examples=[
            ex("[1, 2, 3, 4]", "[2, 3]"),
            ex("[1, 2]", "[]"),
        ],
        topics=["data-analysis", "sliding-window", "time-series"],
        company="data and AI",
        signature="def moving_average(values):",
        solution="""def moving_average(values):
    window = 3
    if len(values) < window:
        return []
    return [round(sum(values[i:i + window]) / window) for i in range(len(values) - window + 1)]
""",
        tests=[tc("1 2 3 4", "[2, 3]"), tc("1 2", "[]"), tc("3 3 3 3", "[3, 3]"),
               tc("1 2 3 4 5 6", "[2, 3, 4, 5]")],
        hints=["Each output needs the sum of three consecutive values.",
               "A running sum avoids re-adding the window from scratch each time."],
        editorial="A moving average smooths a noisy series by averaging a fixed window. The efficient "
                  "implementation keeps a running sum and adds one value while subtracting the one that left the "
                  "window, making the whole series O(n) instead of O(n·k). It is the simplest filter in signal "
                  "processing and the ancestor of every exponential-smoothing method.",
        wrapper="int-list",
    ),
    problem(
        "euclidean-distance", "Euclidean Distance", "easy",
        "Line 1 and line 2 are two points with the same number of integer coordinates. Return the Euclidean "
        "distance between them, rounded to the nearest integer.",
        examples=[
            ex("[0, 0] and [3, 4]", "5"),
            ex("[1, 2] and [4, 6]", "5"),
        ],
        topics=["data-analysis", "knn", "math"],
        company="data and AI",
        signature="def distance(a, b):",
        solution="""def distance(a, b):
    total = sum((left - right) ** 2 for left, right in zip(a, b))
    return round(total ** 0.5)
""",
        tests=[tc("0 0\n3 4", "5"), tc("1 2\n4 6", "5"), tc("2 2\n2 2", "0"),
               tc("0 0 0\n1 2 2", "3")],
        hints=["Sum the squared differences, then take the square root.",
               "This is the metric every k-nearest-neighbour lookup uses."],
        editorial="Euclidean distance is the L2 norm of the difference vector. In high dimensions it becomes "
                  "surprisingly unhelpful - distances concentrate and the nearest neighbour is barely nearer than "
                  "the farthest - which is why text search often prefers cosine similarity. Knowing when it "
                  "misbehaves is the interesting part.",
        wrapper="list-pair",
    ),
    problem(
        "least-squares-slope", "Least Squares Slope", "medium",
        "Line 1 holds the x values, line 2 the matching y values, both space-separated integers. Return the "
        "slope of the least squares line through the points, rounded to the nearest integer.",
        examples=[
            ex("x = [1, 2, 3], y = [2, 4, 6]", "2"),
            ex("x = [0, 1, 2, 3], y = [1, 3, 5, 7]", "2"),
        ],
        topics=["statistics", "regression", "data-analysis"],
        company="data and AI",
        signature="def slope(xs, ys):",
        solution="""def slope(xs, ys):
    count = len(xs)
    mean_x = sum(xs) / count
    mean_y = sum(ys) / count
    numerator = sum((x - mean_x) * (y - mean_y) for x, y in zip(xs, ys))
    denominator = sum((x - mean_x) ** 2 for x in xs)
    if denominator == 0:
        return 0
    return round(numerator / denominator)
""",
        tests=[tc("1 2 3\n2 4 6", "2"), tc("0 1 2 3\n1 3 5 7", "2"),
               tc("1 1 1\n2 4 6", "0"), tc("1 2 3 4\n1 2 3 4", "1")],
        hints=["Slope = covariance(x, y) / variance(x).",
               "Centre the data first: subtracting the means makes both sums simpler and more accurate."],
        editorial="The least squares slope is the covariance of x and y divided by the variance of x. Centring "
                  "the data before summing is not cosmetic - the raw formula subtracts two large nearly equal "
                  "numbers and loses precision. When the x values are all identical the variance is zero and the "
                  "slope is undefined; returning 0 is a deliberate stand-in for that case.",
        wrapper="list-pair",
    ),
    problem(
        "correlation-sign", "Sign of the Correlation", "medium",
        "Line 1 holds the x values, line 2 the matching y values. Return `1` when x and y move together, `-1` "
        "when they move in opposite directions, and `0` when there is no linear relationship at all.",
        examples=[
            ex("x = [1, 2, 3], y = [2, 4, 6]", "1"),
            ex("x = [1, 2, 3], y = [6, 4, 2]", "-1"),
            ex("x = [1, 2, 3], y = [2, 2, 2]", "0"),
        ],
        topics=["statistics", "correlation", "data-analysis"],
        company="data and AI",
        signature="def correlation_sign(xs, ys):",
        solution="""def correlation_sign(xs, ys):
    count = len(xs)
    mean_x = sum(xs) / count
    mean_y = sum(ys) / count
    covariance = sum((x - mean_x) * (y - mean_y) for x, y in zip(xs, ys))
    variance_x = sum((x - mean_x) ** 2 for x in xs)
    variance_y = sum((y - mean_y) ** 2 for y in ys)
    if variance_x == 0 or variance_y == 0:
        return 0
    coefficient = covariance / (variance_x ** 0.5 * variance_y ** 0.5)
    if abs(coefficient) < 1e-9:
        return 0
    return 1 if coefficient > 0 else -1
""",
        tests=[tc("1 2 3\n2 4 6", "1"), tc("1 2 3\n6 4 2", "-1"), tc("1 2 3\n2 2 2", "0"),
               tc("1 2 3 4\n3 5 7 9", "1")],
        hints=["The Pearson coefficient is covariance divided by the product of the standard deviations.",
               "If either variable has zero variance the coefficient is undefined; report no relationship."],
        editorial="The Pearson coefficient normalises the covariance so it lands between -1 and 1. The sign is "
                  "the direction of the linear relationship and the magnitude is its strength, which is why "
                  "returning only the sign here loses most of the information on purpose. The classic warning "
                  "applies: correlation is not causation, and a correlation of 0.9 can still be produced by a "
                  "single outlier.",
        wrapper="list-pair",
    ),
    problem(
        "one-hot-encode", "One-Hot Encode Labels", "easy",
        "Line 1 holds integer class labels, line 2 the number of classes `k`. Return the one-hot matrix as a "
        "list of rows: row `i` has a `1` in the column of label `i` and zeros elsewhere.",
        examples=[
            ex("labels = [0, 2, 1], k = 3", "[[1, 0, 0], [0, 0, 1], [0, 1, 0]]"),
        ],
        topics=["machine-learning", "feature-engineering", "data-analysis"],
        company="data and AI",
        signature="def one_hot(labels, k):",
        solution="""def one_hot(labels, k):
    matrix = []
    for label in labels:
        row = [0] * k
        row[label] = 1
        matrix.append(row)
    return matrix
""",
        tests=[tc("0 2 1\n3", "[[1, 0, 0], [0, 0, 1], [0, 1, 0]]"),
               tc("1\n2", "[[0, 1]]"),
               tc("0 0\n2", "[[1, 0], [1, 0]]")],
        hints=["Every row is zeros with one 1 at the label's index.",
               "`k` decides the row length, so it has to be given even when the labels do not use every class."],
        editorial="One-hot encoding turns a categorical value into a vector with a single 1, which stops a model "
                  "from reading class 2 as \"twice class 1\" the way a raw integer would. The trade-off is "
                  "dimensionality: a feature with a million categories becomes a million columns, which is why "
                  "hashing tricks and embeddings exist.",
        wrapper="int-list-int",
    ),
    problem(
        "histogram-bins", "Histogram Bin Counts", "medium",
        "A line of integers is the data and the second line is the number of equal-width bins. Return the count "
        "of values in each bin, covering the range from the smallest to the largest value inclusive. Return an "
        "empty list for empty data.",
        examples=[
            ex("[0, 1, 2, 3, 4, 5], bins = 2", "[3, 3]"),
            ex("[1, 1, 2], bins = 1", "[3]"),
        ],
        topics=["data-analysis", "statistics", "bucketing"],
        company="data and AI",
        signature="def histogram(values, bins):",
        solution="""def histogram(values, bins):
    if not values or bins <= 0:
        return []
    low, high = min(values), max(values)
    counts = [0] * bins
    if high == low:
        counts[0] = len(values)
        return counts
    width = (high - low) / bins
    for value in values:
        index = int((value - low) / width)
        if index >= bins:
            index = bins - 1
        counts[index] += 1
    return counts
""",
        tests=[tc("0 1 2 3 4 5\n2", "[3, 3]"), tc("1 1 2\n1", "[3]"),
               tc("0 0 0\n3", "[3, 0, 0]"), tc("1 2 3 4\n2", "[2, 2]")],
        hints=["Width = (max − min) / bins, then each value's bin is `int((value − min) / width)`.",
               "The largest value lands exactly at the right edge, so clamp the index into range."],
        editorial="Binning is how a continuous distribution becomes a bar chart. The two bugs to avoid are the "
                  "max value falling one bin past the end and a data range of zero width - both are handled "
                  "explicitly here. Equal-width bins are the default; equal-frequency (quantile) bins show a "
                  "skewed distribution far better.",
        wrapper="int-list-int",
    ),
]

# ---------------------------------------------------------------------------
# Security and systems
# ---------------------------------------------------------------------------

PROBLEMS += [
    problem(
        "caesar-cipher", "Caesar Cipher", "easy",
        "Line 1 is the text, line 2 is the shift. Rotate every letter forward by the shift, wrapping around "
        "the alphabet, and leave every other character untouched. The shift may be larger than 26 or negative.",
        examples=[
            ex("Attack at dawn! / 3", "Dwwdfn dw gdzq!"),
            ex("xyz / 3", "abc", "Wrapping past z returns to a."),
        ],
        topics=["strings", "cryptography", "security"],
        company="security and systems",
        signature="def caesar(text, shift):",
        solution="""def caesar(text, shift):
    step = int(shift) % 26
    out = []
    for character in text:
        if character.isalpha() and character.isascii():
            base = ord("A") if character.isupper() else ord("a")
            out.append(chr((ord(character) - base + step) % 26 + base))
        else:
            out.append(character)
    return "".join(out)
""",
        tests=[tc("Attack at dawn!\n3", "Dwwdfn dw gdzq!"), tc("xyz\n3", "abc"),
               tc("abc\n-3", "xyz"), tc("Hello, World!\n0", "Hello, World!"),
               tc("abc\n29", "def")],
        hints=["Only letters move. Digits, spaces and punctuation stay where they are.",
               "Modulo handles wrapping, and taking the shift modulo 26 first handles negative and large shifts."],
        editorial="The Caesar cipher is a rotation of the alphabet, so the whole implementation is one modulo "
                  "operation per letter. It is broken by brute force in 25 attempts, which is why it is only "
                  "useful as a teaching device - but the letter-only rotation and the wrap-around are exactly the "
                  "mechanics ROT13 and the substitution ciphers used before computers worked on.",
        wrapper="two-lines",
    ),
    problem(
        "base64-encode", "Base64 Encode", "easy",
        "Given a line of text, return its standard Base64 encoding with padding, on one line.",
        examples=[
            ex("Hello", "SGVsbG8="),
            ex("Hi", "SGk="),
        ],
        topics=["strings", "encoding", "security"],
        company="security and systems",
        signature="def to_base64(text):",
        solution="""def to_base64(text):
    import base64

    return base64.b64encode(text.encode("utf-8")).decode("ascii")
""",
        tests=[tc("Hello", "SGVsbG8="), tc("Hi", "SGk="), tc("", ""),
               tc("The quick brown fox", "VGhlIHF1aWNrIGJyb3duIGZveA==")],
        hints=["Base64 takes three bytes and produces four characters.",
               "The `=` padding restores the length when the input is not a multiple of three bytes."],
        editorial="Base64 maps 6 bits to each of 64 printable characters so binary data survives a text-only "
                  "channel. It is encoding, not encryption - anything base64-encoded is trivially decoded - and "
                  "imagining otherwise is the mistake behind a long history of credential leaks. The padding "
                  "characters exist so the original byte length is recoverable.",
        wrapper="string-int",
    ),
    problem(
        "validate-ipv4", "Validate an IPv4 Address", "medium",
        "Given a line of text, return `True` when it is a valid dotted-decimal IPv4 address: exactly four parts, "
        "each an integer from 0 to 255, with no leading zeros and no extra characters.",
        examples=[
            ex("192.168.0.1", "True"),
            ex("256.1.1.1", "False", "256 is out of range."),
            ex("01.2.3.4", "False", "Leading zeros are not allowed."),
        ],
        topics=["strings", "networking", "validation"],
        company="security and systems",
        signature="def is_ipv4(text):",
        solution="""def is_ipv4(text):
    parts = text.split(".")
    if len(parts) != 4:
        return False
    for part in parts:
        if not part.isdigit():
            return False
        if len(part) > 1 and part[0] == "0":
            return False
        if int(part) > 255:
            return False
    return True
""",
        tests=[tc("192.168.0.1", "True"), tc("256.1.1.1", "False"), tc("01.2.3.4", "False"),
               tc("1.2.3", "False"), tc("1.2.3.4.5", "False"), tc("1.2.3.4", "True"),
               tc("1.2.3.a", "False")],
        hints=["Split on dots and check the count first.",
               "`isdigit()` rejects negative signs and spaces, but \"01\" still needs its own rule."],
        editorial="Validation is a sequence of small refusals: wrong number of parts, non-digits, leading zeros, "
                  "out of range. The leading-zero rule is not pedantry - many parsers treat 010 as octal, so "
                  "accepting it creates an ambiguity attackers use to smuggle a different address past a filter. "
                  "That class of bug is why `ipaddress` in the standard library exists and should be preferred in "
                  "production code.",
        wrapper="string-bool",
    ),
    problem(
        "cidr-usable-hosts", "Usable Hosts in a CIDR Block", "medium",
        "Given a CIDR block such as `192.168.1.0/24` on its own line, return how many addresses can be assigned "
        "to hosts: the block size minus the network and broadcast addresses.",
        examples=[
            ex("192.168.1.0/24", "254"),
            ex("10.0.0.0/8", "16777214"),
        ],
        topics=["networking", "security", "bit-manipulation"],
        company="security and systems",
        signature="def usable_hosts(cidr):",
        solution="""def usable_hosts(cidr):
    prefix = int(cidr.split("/")[1])
    hosts = (1 << (32 - prefix)) - 2
    return hosts if hosts > 0 else 0
""",
        tests=[tc("192.168.1.0/24", "254"), tc("10.0.0.0/8", "16777214"),
               tc("192.168.1.0/31", "0"), tc("0.0.0.0/32", "0"), tc("172.16.0.0/16", "65534")],
        hints=["A /24 leaves 8 host bits, which is 256 addresses.",
               "The network and broadcast addresses are not assignable, so subtract two - but a /31 or /32 has "
               "none to spare."],
        editorial="A CIDR suffix says how many leading bits are network, leaving 32 − prefix bits for hosts. "
                  "Subtracting two accounts for the network and broadcast addresses, and the clamp to zero covers "
                  "the point-to-point /31 and single-address /32 cases where that arithmetic would go negative. "
                  "Knowing this by heart is what makes a subnet plan readable at a glance.",
        wrapper="string-int",
    ),
    problem(
        "password-entropy", "Password Entropy", "medium",
        "Given a password on the first line and its character-set size on the second, return the entropy in "
        "bits - `length × log2(pool)` - rounded to the nearest integer. Repeats count, because the estimate is "
        "about the search space rather than the password's wisdom.",
        examples=[
            ex("abcdef / 26", "28", "Six lower-case letters."),
            ex("Tr0ub4dor&3 / 94", "72", "Eleven characters from a 94-symbol set."),
        ],
        topics=["security", "math", "cryptography"],
        company="security and systems",
        signature="def entropy(password, pool):",
        solution="""def entropy(password, pool):
    from math import log2

    alphabet = int(pool)
    if not password or alphabet <= 1:
        return 0
    return round(len(password) * log2(alphabet))
""",
        tests=[tc("abcdef\n26", "28"), tc("Tr0ub4dor&3\n94", "72"),
               tc("\n94", "0"), tc("a\n1", "0"), tc("aaaaaaaa\n26", "38")],
        hints=["log2(pool) is the bits per character; multiply by the length.",
               "A pool of size 1 or an empty password carries no entropy at all."],
        editorial="Entropy counts the bits an attacker must guess: length × log2(alphabet size). The model is "
                  "deliberately naive - \"aaaaaaaa\" scores the same as any other eight-letter password, and it "
                  "knows nothing about dictionary words - which is why a length estimate is a floor and not a "
                  "promise. It does show the trade clearly: adding one character is worth more than switching "
                  "from lower-case to mixed case.",
        wrapper="two-lines",
    ),
    problem(
        "verify-sha256", "Verify a SHA-256 Digest", "easy",
        "Line 1 is a message and line 2 is a claimed lowercase hex digest. Return `True` when the digest is the "
        "SHA-256 of the message, and `False` otherwise.",
        examples=[
            ex("abc / ba7816bf...", "True", "The well-known SHA-256 test vector for \u201cabc\u201d."),
            ex("abc / 0000...", "False"),
        ],
        topics=["security", "hashing", "integrity"],
        company="security and systems",
        signature="def verify_digest(message, digest):",
        solution="""def verify_digest(message, digest):
    import hashlib

    actual = hashlib.sha256(message.encode("utf-8")).hexdigest()
    return actual == digest.strip().lower()
""",
        tests=[tc("abc\nba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad", "True"),
               tc("abc\n" + "0" * 64, "False"),
               tc("\ne3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855", "True"),
               tc("abc\nBA7816BF8F01CFEA414140DE5DAE2223B00361A396177A9CB410FF61F20015AD", "True")],
        hints=["Hash the message and compare with the claim.",
               "Normalise case before comparing: hex digests are often written in upper case."],
        editorial="Hashing gives a fixed-length fingerprint that changes completely if one bit of the message "
                  "changes. Comparing digests is how downloads, package managers and Git verify integrity - and "
                  "it is also how passwords should be stored, with a salt and a slow KDF rather than one SHA-256 "
                  "pass, because a fast hash is exactly what an attacker wants.",
        wrapper="two-lines",
    ),
]

# ---------------------------------------------------------------------------
# Software and web engineering
# ---------------------------------------------------------------------------

PROBLEMS += [
    problem(
        "reverse-words", "Reverse the Words in a Sentence", "easy",
        "Given a line of text, return it with the words in reverse order and single spaces between them. "
        "Leading, trailing and repeated spaces in the input must not appear in the output.",
        examples=[
            ex("the sky is blue", "blue is sky the"),
            ex("  hello   world  ", "world hello"),
        ],
        topics=["strings", "arrays"],
        company="software and web",
        signature="def reverse_words(text):",
        solution="""def reverse_words(text):
    return " ".join(text.split()[::-1])
""",
        tests=[tc("the sky is blue", "blue is sky the"), tc("  hello   world  ", "world hello"),
               tc("single", "single"), tc("", "")],
        hints=["`split()` with no argument already collapses runs of whitespace and trims the ends.",
               "Reversing the list and joining with a single space gives the required spacing."],
        editorial="Two details carry the whole problem: `split()` without arguments splits on any whitespace and "
                  "drops empty pieces, and `join` with one space rebuilds the string. Writing a manual split "
                  "usually produces the double-space bug the tests here are looking for. O(n) time and space.",
        wrapper="string-int",
    ),
    problem(
        "longest-common-prefix", "Longest Common Prefix", "easy",
        "Given one line of words, return the longest prefix shared by every word. Return an empty line when "
        "they share none.",
        examples=[
            ex("flower flow flight", "fl"),
            ex("dog racecar car", ""),
        ],
        topics=["strings", "arrays"],
        company="software and web",
        signature="def longest_common_prefix(words):",
        solution="""def longest_common_prefix(words):
    if not words:
        return ""
    prefix = words[0]
    for word in words[1:]:
        while not word.startswith(prefix):
            prefix = prefix[:-1]
            if not prefix:
                return ""
    return prefix
""",
        tests=[tc("flower flow flight", "fl"), tc("dog racecar car", ""),
               tc("interview", "interview"), tc("a ab abc", "a")],
        hints=["Start with the first word as the candidate prefix and shrink it against each other word.",
               "Sorting the words makes the answer the common prefix of the first and last."],
        editorial="Shrinking a candidate prefix against each word is the clearest O(total characters) solution. "
                  "The sorting shortcut works because after sorting, the two most different words are at the ends, "
                  "so their common prefix is the answer for the whole list. Both are worth knowing, and neither "
                  "needs the words to be the same length.",
        wrapper="string-list",
    ),
    problem(
        "slugify", "Slugify a Title", "easy",
        "Turn a title into a URL slug: lower case, letters and digits kept, every run of other characters "
        "replaced by a single hyphen, and no leading or trailing hyphen.",
        examples=[
            ex("Hello, World!", "hello-world"),
            ex("  Fast   API Design  ", "fast-api-design"),
        ],
        topics=["strings", "web"],
        company="software and web",
        signature="def slugify(title):",
        solution="""def slugify(title):
    import re

    cleaned = re.sub(r"[^a-z0-9]+", "-", title.lower())
    return cleaned.strip("-")
""",
        tests=[tc("Hello, World!", "hello-world"), tc("  Fast   API Design  ", "fast-api-design"),
               tc("Python 3.12 is out", "python-3-12-is-out"), tc("!!!", ""),
               tc("already-a-slug", "already-a-slug")],
        hints=["Lower-case first, then replace every run of non-alphanumerics with one hyphen.",
               "The `+` in the regular expression is what collapses repeated separators."],
        editorial="A slug is a URL-safe identifier, so the transformation is: normalise case, collapse everything "
                  "that is not a letter or digit into one separator, and trim the ends. Writing `re.sub` with `+` "
                  "instead of a per-character replace is the difference between \"fast-api-design\" and a row of "
                  "repeated hyphens. In production, strip accents first - `café` should not become `caf`.",
        wrapper="string-int",
    ),
    problem(
        "run-length-encoding", "Run-Length Encoding", "medium",
        "Given a line of text, encode it as each character followed by its run length, for example `aaabbc` "
        "becomes `a3b2c1`. A character that appears once still gets the count 1.",
        examples=[
            ex("aaabbc", "a3b2c1"),
            ex("abc", "a1b1c1"),
        ],
        topics=["strings", "compression"],
        company="software and web",
        signature="def run_length_encode(text):",
        solution="""def run_length_encode(text):
    if not text:
        return ""
    out = []
    current = text[0]
    count = 0
    for character in text:
        if character == current:
            count += 1
        else:
            out.append(f"{current}{count}")
            current = character
            count = 1
    out.append(f"{current}{count}")
    return "".join(out)
""",
        tests=[tc("aaabbc", "a3b2c1"), tc("abc", "a1b1c1"), tc("", ""), tc("a", "a1"),
               tc("aaaAAAaa", "a3A3a2")],
        hints=["Walk the string once, tracking the current character and how many times you have seen it.",
               "The last run has to be emitted after the loop - that is the classic off-by-one here."],
        editorial="Run-length encoding is only a compression scheme for data with long runs: `abc` expands from "
                  "three characters to six. That is why formats that use it - fax transmission, TIFF, and the "
                  "packed bits in old bitmap fonts - also specify a marker or fall back to a literal when runs are "
                  "short. The implementation is a state machine, and the final emit after the loop is the part "
                  "people forget.",
        wrapper="string-int",
    ),
    problem(
        "version-compare", "Compare Version Numbers", "medium",
        "Line 1 and line 2 are two dot-separated version strings. Return `-1` when the first is older, `1` when "
        "it is newer, and `0` when they are equal. Missing parts count as zero, so `1.0` and `1.0.0` are equal.",
        examples=[
            ex("1.2.3 vs 1.2.4", "-1"),
            ex("1.0 vs 1.0.0", "0"),
            ex("2.0 vs 1.9.9", "1"),
        ],
        topics=["strings", "web", "parsing"],
        company="software and web",
        signature="def compare_versions(left, right):",
        solution="""def compare_versions(left, right):
    parts_left = [int(part) for part in left.split(".")]
    parts_right = [int(part) for part in right.split(".")]
    size = max(len(parts_left), len(parts_right))
    for index in range(size):
        first = parts_left[index] if index < len(parts_left) else 0
        second = parts_right[index] if index < len(parts_right) else 0
        if first != second:
            return 1 if first > second else -1
    return 0
""",
        tests=[tc("1.2.3\n1.2.4", "-1"), tc("1.0\n1.0.0", "0"), tc("2.0\n1.9.9", "1"),
               tc("1.0.0\n1", "0"), tc("0.9\n1.0", "-1")],
        hints=["Compare part by part, treating a missing part as zero.",
               "Do not compare the strings numerically - \"10\" is less than \"9\" as text."],
        editorial="Version comparison is a numeric comparison per component, padded with zeros. It looks trivial "
                  "and is a reliable source of production incidents: comparing \"1.10\" with \"1.9\" as strings "
                  "gets it backwards, and forgetting the zero padding makes 1.0 and 1.0.0 unequal. Real "
                  "implementations also handle pre-release suffixes, which is where the rules stop being obvious.",
        wrapper="two-lines",
    ),
    problem(
        "int-to-roman", "Integer to Roman", "medium",
        "Given an integer from 1 to 3999 on its own line, return its Roman numeral. Use the standard subtractive "
        "forms: 4 is `IV`, 9 is `IX`, 40 is `XL`, 90 is `XC`, 400 is `CD` and 900 is `CM`.",
        examples=[
            ex("1994", "MCMXCIV", "1000 + 900 + 90 + 4."),
            ex("58", "LVIII"),
        ],
        topics=["strings", "greedy", "math"],
        company="software and web",
        signature="def int_to_roman(number):",
        solution="""def int_to_roman(number):
    values = (
        (1000, "M"), (900, "CM"), (500, "D"), (400, "CD"),
        (100, "C"), (90, "XC"), (50, "L"), (40, "XL"),
        (10, "X"), (9, "IX"), (5, "V"), (4, "IV"), (1, "I"),
    )
    out = []
    for value, symbol in values:
        while number >= value:
            out.append(symbol)
            number -= value
    return "".join(out)
""",
        tests=[tc("1994", "MCMXCIV"), tc("58", "LVIII"), tc("4", "IV"), tc("9", "IX"),
               tc("3999", "MMMCMXCIX"), tc("1", "I")],
        hints=["Greedy works because the symbol table includes the subtractive pairs.",
               "Taking the largest symbol that fits and repeating it is the whole algorithm."],
        editorial="Greedy subtraction works only because the table includes the six subtractive pairs (CM, CD, "
                  "XC, XL, IX, IV) as first-class symbols; without them, greedy would emit IIII for 4. That is "
                  "the insight the problem is really testing. O(1) space and time for the constrained range, and "
                  "the reverse direction - parsing a Roman numeral - is the mirror image with a check for "
                  "out-of-order pairs.",
        wrapper="int-n",
    ),
]
