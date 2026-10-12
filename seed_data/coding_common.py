"""Shared helpers for the coding problem bank (spec §16).

The original 13 problems in ``practice_data.py`` spell every field out by hand,
including a stub and a reference solution for each of four languages. That does
not scale to a bank of ninety, and it is not where the value is: what a learner
reads is the statement, the worked examples, the hints and the editorial, and
what the judge runs is one entry point plus its tests.

So a problem here is declared once, in the language-independent way:

    problem("count-primes", "Count Primes", "easy",
            statement, examples=[ex("10", "4", "2, 3, 5 and 7 are prime...")],
            signature="def count_primes(n):", solution="def count_primes(n):\n    ...",
            tests=[tc("10", "4"), tc("2", "0")], wrapper="int-n")

and the module fills in the mechanical parts:

* the Python stub is generated from the signature, so the editor always opens on
  a declaration the harness can actually call - a stub that does not match
  ``drivers.entrypoint`` is a Run button that always fails;
* ``expected_time``/``expected_space`` default to the honest generic answer and
  are stated per problem where the real bound matters.

XP for a judged submission is awarded by outcome rather than by difficulty - see
``engineverse.coding.submit`` - so a problem does not carry an ``xp`` field here,
even though the older hand-written entries in ``practice_data`` still do.

Every reference solution in this bank is executed against its own test cases by
``scripts/check_problems.py``, which is the only reason it is safe to ship this
much content: a wrong expected output is a problem nobody can solve.
"""
from __future__ import annotations


def ex(prompt: str, output: str, explain: str | None = None) -> dict:
    """One worked example, as the problem statement renders it."""
    return {"input": prompt, "output": output, "explain": explain}


def tc(stdin: str, expected: str, explain: str | None = None) -> dict:
    """One judge test case: the exact stdin and the exact stdout."""
    return {"input": stdin, "expected": expected, "explain": explain}


def problem(
    slug: str,
    title: str,
    difficulty: str,
    statement: str,
    *,
    examples: list[dict],
    topics: list[str],
    signature: str,
    solution: str,
    tests: list[dict],
    wrapper: str,
    hints: list[str] | None = None,
    editorial: str = "",
    company: str = "",
    minutes: int = 20,
    expected_time: str = "O(n)",
    expected_space: str = "O(1)",
) -> dict:
    """Builds one problem in the shape ``scripts/seed.py`` inserts.

    ``solution`` is the reference implementation in Python, typed exactly as a
    learner would write it after the harness appends its driver. ``signature``
    is the same entry point written as a declaration; the generated stub is that
    declaration with a body that does nothing, which is what the editor opens on.
    """
    if difficulty not in {"easy", "medium", "hard"}:
        raise ValueError(f"{slug}: unknown difficulty {difficulty!r}")
    stubs = {
        "python": (
            f"{signature}\n"
            "    # Write your solution here\n"
            "    pass\n"
        )
    }
    return {
        "slug": slug,
        "title": title,
        "difficulty": difficulty,
        "statement": statement,
        "examples": examples,
        "topics": topics,
        "company": company,
        "signature": {"python": signature},
        "stub": stubs,
        "solution": {"python": solution},
        "tests": tests,
        "hints": hints or [],
        "editorial": editorial,
        "minutes": minutes,
        "wrapper": wrapper,
        "expected_time": expected_time,
        "expected_space": expected_space,
    }
