#!/usr/bin/env python3
"""Runs every seeded problem's reference solution against its own tests.

    python scripts/check_problems.py            # every problem in the bank
    python scripts/check_problems.py --problems two-sum count-primes
    python scripts/check_problems.py --sheets   # also validate sheet membership

Why this exists
---------------
The bank is content, and content is where the mistakes are. A test case whose
expected output does not match what the reference solution prints is a problem
that *nobody* can solve, including the person who wrote it, and the failure is
invisible until a learner hits it. Tests that only check a problem's rows exist
cannot see that.

This walks the same path the judge does - the same wrapper composition, the same
program text, the same output comparison - so a green run here means the editor
would accept the reference solution and, more importantly, that the expected
outputs are reachable at all.

It runs the solutions in this process's own interpreter, without the sandbox.
That is deliberate: it is a content check, not a security check, and it has to
work on a laptop with no namespaces. Nothing here is a substitute for
``backend/tests/test_judge.py``, which exercises the real sandbox.
"""
from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
BACKEND = REPO_ROOT / "backend"
for entry in (str(BACKEND), str(REPO_ROOT)):
    if entry not in sys.path:
        sys.path.insert(0, entry)

from engineverse.drivers import WRAPPERS, compose  # noqa: E402
from engineverse.judge import outputs_match  # noqa: E402


def load_problems() -> list[dict]:
    from seed_data import coding_book, coding_core, coding_streams

    problems = list(coding_core.PROBLEMS) + list(coding_streams.PROBLEMS) + list(coding_book.PROBLEMS)
    seen: dict[str, int] = {}
    for problem in problems:
        slug = problem["slug"]
        if slug in seen:
            raise SystemExit(f"duplicate problem slug: {slug}")
        seen[slug] = 1
    return problems


def run_case(program: str, stdin: str, timeout: float = 20.0) -> tuple[str, str]:
    try:
        result = subprocess.run(
            [sys.executable, "-c", program],
            input=stdin,
            capture_output=True,
            text=True,
            timeout=timeout,
        )
    except subprocess.TimeoutExpired:
        return "", "TIMEOUT"
    if result.returncode != 0:
        return result.stdout, (result.stderr.strip().splitlines() or ["EXIT %d" % result.returncode])[-1]
    return result.stdout, ""


def check(problems: list[dict]) -> int:
    failures = 0
    for problem in problems:
        slug = problem["slug"]
        wrapper = problem.get("wrapper", "raw")
        if wrapper not in WRAPPERS:
            print(f"FAIL {slug}: unknown wrapper {wrapper!r}")
            failures += 1
            continue
        signature = (problem.get("signature") or {}).get("python")
        solution = (problem.get("solution") or {}).get("python")
        if not solution:
            print(f"FAIL {slug}: no Python reference solution")
            failures += 1
            continue
        if not problem.get("tests"):
            print(f"FAIL {slug}: no test cases")
            failures += 1
            continue
        program = compose("python", solution, wrapper, signature)
        bad: list[str] = []
        for index, case in enumerate(problem["tests"]):
            stdout, error = run_case(program, case["input"])
            if error:
                bad.append(f"case {index}: {error}")
                continue
            if not outputs_match(stdout, case["expected"]):
                bad.append(
                    f"case {index}: input {case['input']!r} expected {case['expected']!r} got {stdout.strip()!r}"
                )
        if bad:
            failures += 1
            print(f"FAIL {slug} ({wrapper}, {len(problem['tests'])} cases)")
            for line in bad[:4]:
                print(f"     {line}")
        else:
            print(f"ok   {slug}  {len(problem['tests'])} cases")
    return failures


def check_sheets(problems: list[dict]) -> int:
    """Sheet membership must name real problems, and every problem must be in one."""
    from seed_data import coding_sheets, practice_data

    slugs = {problem["slug"] for problem in problems}
    # The original 13 problems live in practice_data and are seeded as well, so
    # membership is checked against the union of both banks.
    slugs |= {problem["slug"] for problem in practice_data.CODING_PROBLEMS}
    failures = 0
    placed: set[str] = set()
    for sheet in coding_sheets.SHEETS:
        unknown = [slug for slug in sheet["problems"] if slug not in slugs]
        if unknown:
            print(f"FAIL sheet {sheet['slug']}: unknown problems {unknown[:5]}")
            failures += 1
        if not sheet["problems"]:
            print(f"FAIL sheet {sheet['slug']}: empty")
            failures += 1
        placed.update(sheet["problems"])
    unplaced = sorted(slugs - placed)
    if unplaced:
        print(f"FAIL {len(unplaced)} problems are in no sheet: {unplaced[:8]}")
        failures += 1
    print(f"ok   {len(coding_sheets.SHEETS)} sheets cover {len(placed)} problems")
    return failures


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--problems", nargs="*", default=None,
                        help="check only these slugs")
    parser.add_argument("--sheets", action="store_true",
                        help="also validate sheet membership")
    args = parser.parse_args()

    problems = load_problems()
    if args.problems:
        wanted = set(args.problems)
        problems = [problem for problem in problems if problem["slug"] in wanted]
        missing = wanted - {problem["slug"] for problem in problems}
        if missing:
            raise SystemExit(f"unknown problem slug(s): {sorted(missing)}")

    print(f"Checking {len(problems)} problems\n")
    failures = check(problems)
    if args.sheets:
        print()
        failures += check_sheets(load_problems())

    print()
    if failures:
        print(f"{failures} problem(s) failed")
        return 1
    print("All reference solutions match their expected output.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
