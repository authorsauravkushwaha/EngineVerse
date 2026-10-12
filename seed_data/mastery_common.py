"""Shared shape for the mastery lesson pass.

The catalogue already carries a breadth pass (``subject_paths.STARTERS``, one
starter lesson wherever a subject had nothing) and a depth pass
(``deeper_lessons``, two further lessons per subject). This module defines the
shape used by the *mastery* pass: one more authored lesson for every subject in
the catalogue, assembled from domain modules and validated before any seeder
reads it.

What makes a mastery lesson different from the earlier passes:

* every lesson names a second, independent worked check (``second_example``),
  so the worked-example section carries two fully worked problems rather than
  one problem restated;
* exam and interview prompts are authored per lesson (``exam``/``interview``)
  instead of being templated from the formula name alone;
* pitfalls are a list - a single pitfall reads as an afterthought.

The honesty rules of the existing passes still apply: a formula is a canonical
relation of the field with its validity conditions stated, a non-quantitative
subject uses a rubric in place of a physical law and says so, and every lesson
is published with ``accuracy_state="needs_review"`` because publication is not
expert sign-off.
"""
from __future__ import annotations


def _f(
    name: str,
    latex: str,
    variables: tuple[tuple[str, str, str], ...],
    conditions: str,
) -> dict:
    """A governing relation with its symbol table and validity conditions."""
    return {
        "name": name,
        "latex": latex,
        "variables": [{"s": symbol, "n": meaning, "u": unit} for symbol, meaning, unit in variables],
        "conditions": conditions,
    }


def _e(problem: str, approach: str, solution: str, answer: str) -> dict:
    """A worked problem: statement, method, shown steps, stated result."""
    return {"problem": problem, "approach": approach, "solution": solution, "answer": answer}


def _lesson(
    title: str,
    focus: str,
    formula: dict,
    derivation: str,
    example: dict,
    applications: tuple[str, ...],
    pitfalls: tuple[str, ...],
    industry: str,
    *,
    second_example: dict | None = None,
    exam: tuple[str, ...] = (),
    interview: tuple[str, ...] = (),
    tags: tuple[str, ...] = (),
    difficulty: str = "medium",
    minutes: int = 30,
    quiz: dict | None = None,
    diagram_steps: tuple[tuple[str, str], ...] | None = None,
) -> dict:
    return {
        "title": title,
        "focus": focus,
        "formula": formula,
        "derivation": derivation,
        "example": example,
        "second_example": second_example,
        "applications": list(applications),
        "pitfalls": list(pitfalls),
        "industry": industry,
        "exam": list(exam),
        "interview": list(interview),
        "tags": list(tags),
        "difficulty": difficulty,
        "minutes": minutes,
        "quiz": quiz,
        "diagram_steps": diagram_steps,
    }


#: Every subject must gain at least this many mastery lessons. Enforced by
#: ``mastery_lessons.validate`` so "every field" is a checked claim.
MIN_LESSONS_PER_SUBJECT = 1

#: Fields every mastery lesson must carry, checked before the seed runs.
REQUIRED_FIELDS = ("title", "focus", "formula", "derivation", "example", "applications",
                   "pitfalls", "industry")


def merge_modules(modules) -> dict[str, tuple[dict, ...]]:
    """Combine domain modules into one subject -> lessons mapping.

    Later modules may add lessons to a subject an earlier module started; the
    subject must never appear twice with the same lesson title, which is what
    the duplicate check in :func:`problems_in` is for.
    """
    merged: dict[str, list[dict]] = {}
    for module in modules:
        for subject, specs in module.LESSONS.items():
            merged.setdefault(subject, []).extend(specs)
    return {subject: tuple(specs) for subject, specs in merged.items()}


def problems_in(lessons: dict[str, tuple[dict, ...]], subject_slugs: set[str]) -> list[str]:
    """Every problem with the corpus, collected rather than raised one at a time."""
    problems: list[str] = []
    unknown = sorted(set(lessons) - subject_slugs)
    if unknown:
        problems.append(f"mastery lessons reference unknown subjects: {unknown}")
    missing = sorted(subject_slugs - set(lessons))
    if missing:
        problems.append(f"subjects with no mastery lesson: {missing}")
    for slug, specs in sorted(lessons.items()):
        if len(specs) < MIN_LESSONS_PER_SUBJECT:
            problems.append(f"{slug}: {len(specs)} mastery lessons, at least {MIN_LESSONS_PER_SUBJECT} required")
        for spec in specs:
            title = spec.get("title", "")
            for field in REQUIRED_FIELDS:
                if not spec.get(field):
                    problems.append(f"{slug} / {title!r}: missing field {field!r}")
            if len(spec.get("applications", [])) < 2:
                problems.append(f"{slug} / {title!r}: needs at least two applications")
            if len(spec.get("pitfalls", [])) < 2:
                problems.append(f"{slug} / {title!r}: needs at least two pitfalls")
            if spec.get("difficulty") not in ("easy", "medium", "hard"):
                problems.append(f"{slug} / {title!r}: difficulty must be easy/medium/hard")
            formula = spec.get("formula") or {}
            if not formula.get("name") or not formula.get("latex") or not formula.get("variables"):
                problems.append(f"{slug} / {title!r}: formula needs name, latex and variables")
            elif not formula.get("conditions"):
                problems.append(f"{slug} / {title!r}: formula needs its validity conditions")
            for label in ("example", "second_example"):
                example = spec.get(label)
                if label == "second_example" and example is None:
                    continue
                if not example:
                    problems.append(f"{slug} / {title!r}: {label} missing")
                    continue
                for field in ("problem", "approach", "solution", "answer"):
                    if not example.get(field):
                        problems.append(f"{slug} / {title!r}: {label} missing {field!r}")
            if len(spec.get("exam", [])) < 2:
                problems.append(f"{slug} / {title!r}: needs at least two authored exam prompts")
            if len(spec.get("interview", [])) < 2:
                problems.append(f"{slug} / {title!r}: needs at least two authored interview prompts")
    titles = [spec["title"] for specs in lessons.values() for spec in specs]
    duplicates = sorted({title for title in titles if titles.count(title) > 1})
    if duplicates:
        problems.append(f"duplicate mastery lesson titles: {duplicates}")
    return problems
