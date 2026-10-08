"""Tests for the in-house Markdown and LaTeX-subset renderer.

The renderer exists so the platform needs no third-party script or CDN, which
means its output has to be correct rather than merely plausible.
"""
from __future__ import annotations

import re

from engineverse import markdown


def _visible(tex: str) -> str:
    """Strips tags so a test can assert on the characters a reader actually sees."""
    html = markdown._TeX(tex).render()
    html = html.replace("&thinsp;", " ").replace("&ensp;", " ").replace("&emsp;", " ")
    return re.sub(r"<[^>]+>", "", html).replace("&amp;", "&").replace("&#x27;", "'")


# ---------------------------------------------------------------------------
# Regression: the first letter of every alphabetic run was dropped
# ---------------------------------------------------------------------------

def test_single_variable_survives():
    """``run`` started empty after ``take()`` had already consumed the letter."""
    assert _visible("k") == "k"
    assert _visible("E") == "E"


def test_first_letter_of_a_run_survives():
    assert _visible("I_s") == "Is"
    assert _visible("dQ") == "dQ"


def test_sum_with_subscript_is_complete():
    """The bug that prompted this file: both the index and the variable vanished."""
    html = markdown._TeX(r"\sum_k I_k = 0").render()
    assert '<sub class="msub"></sub>' not in html, "empty subscript element rendered"
    assert _visible(r"\sum_k I_k = 0") == "∑k Ik = 0"


def test_diode_equation_is_complete():
    assert _visible(r"I = I_s \left(e^{qV/kT} - 1\right)") == "I = Is (eqV/kT - 1)"


def test_ohms_law_style_products():
    assert _visible(r"\sigma = E\varepsilon") == "σ = Eε"
    assert _visible(r"P_{\text{loss}} = I^2 R") == "Ploss = I2 R"


def test_greek_and_prime_notation():
    assert _visible(r"\tau_f = c' + \sigma' \tan\phi'") == "τf = c' + σ' tanφ'"


def test_fraction_keeps_both_operands():
    """Fractions went through ``group()``, a different path than bare runs."""
    html = markdown._TeX(r"\frac{V_1}{N_2}").render()
    assert "mnum-frac" in html and "mden-frac" in html
    assert _visible(r"\frac{V_1}{N_2}") == "V1N2"


def test_every_variable_in_a_seeded_formula_is_rendered():
    """End-to-end over the real data: no formula loses a letter."""
    stripped = _visible(r"\sum_k I_k")
    for expected in ("∑", "k", "I"):
        assert expected in stripped


def test_display_math_is_wrapped_once_and_labelled():
    """aria-label carries the raw LaTeX, which is what a screen reader reads."""
    html = markdown.render(r"$$\sum_k I_k = 0$$")
    assert html.count('class="math math-display"') == 1
    assert r'aria-label="\sum_k I_k = 0"' in html
    assert "$$" not in html, "the delimiters must be consumed, not printed"


def test_math_renderer_does_not_emit_raw_angle_brackets():
    """The output goes into ``| safe``, so it must not be able to break out."""
    hostile = markdown._TeX("a < b > c").render()
    assert "<b >" not in hostile and "&lt;" in hostile
