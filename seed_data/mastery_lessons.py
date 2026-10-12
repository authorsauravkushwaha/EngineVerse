"""A mastery lesson for every subject in the catalogue.

Three passes now build the generated curriculum:

* the breadth pass (``subject_paths.STARTERS``) - one starter lesson wherever a
  subject had no notes at all;
* the depth pass (``deeper_lessons``) - two further lessons for every subject;
* this mastery pass - one more lesson per subject, assembled from the domain
  modules below and validated before the seed reads it.

A mastery lesson is deliberately the most detailed of the three: the focus is a
sentence rather than a phrase, the derivation explains why the relation holds,
there are two independent worked checks with checkable arithmetic, several
applications and pitfalls, and the exam and interview prompts are written for
the specific relation instead of being templated from its name. The extra
material is rendered into the standard 13-section note by
``subject_paths._build_topic``, which also deepens the sections of every other
generated topic.

Publication rules are unchanged: every lesson is seeded as ``published`` with
``accuracy_state="needs_review"``, because reachable-and-readable is not the
same claim as expert-signed-off.
"""
from __future__ import annotations

from seed_data import (
    mastery_civil_chemical,
    mastery_computing,
    mastery_electronics,
    mastery_foundations,
    mastery_mechanical,
)
from seed_data.mastery_common import MIN_LESSONS_PER_SUBJECT, merge_modules, problems_in

#: Domain modules merged into one subject -> lessons mapping.
DOMAIN_MODULES = (
    mastery_foundations,
    mastery_computing,
    mastery_electronics,
    mastery_mechanical,
    mastery_civil_chemical,
)

LESSONS: dict[str, tuple[dict, ...]] = merge_modules(DOMAIN_MODULES)


def validate(subject_slugs: set[str]) -> None:
    """Fail the seed if the mastery pass does not cover every subject.

    Every problem with the corpus is collected and raised together, so one run
    names every gap rather than one gap per reseed.
    """
    problems = problems_in(LESSONS, subject_slugs)
    if problems:
        raise ValueError("mastery_lessons.py does not satisfy the coverage contract:\n  "
                         + "\n  ".join(problems))
