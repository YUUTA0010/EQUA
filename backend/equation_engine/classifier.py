"""
Classifies a ParsedEquation into a category (spec section 3).

Strategy:
  1. Known-equation library match (symbol-set based) — gives rich, accurate
     physical metadata for well-known laws.
  2. If no match, structural classification using SymPy (degree, presence of
     trig/exp/log terms, ODE detection already done in the parser).

This keeps the AI layer out of anything that can be determined
deterministically, per spec section 13.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Optional

import sympy
from sympy import Poly, degree, sin, cos, tan, exp, log, Symbol

from equation_engine.parser import ParsedEquation
from equation_engine.library import find_library_match, LIBRARY


@dataclass
class Classification:
    category_id: str
    category_label: str
    domain_area: str
    library_entry: Optional[Dict[str, Any]]
    confidence: float
    is_ambiguous: bool
    notes: List[str]


def _contains_func(expr: sympy.Expr, funcs) -> bool:
    try:
        return expr.has(*funcs)
    except Exception:  # noqa: BLE001
        return False


INDEPENDENT_VARIABLE_PRIORITY = ["t", "x", "s", "theta", "omega", "r"]


def choose_independent_variable(candidate_names: List[str]) -> str:
    """Pick a single canonical plotting/independent variable out of several
    free symbols, using common textbook conventions (t for time, x for
    generic position, etc.), falling back to alphabetical order. Shared
    between the classifier and the analyzer so both agree on which symbol
    is "the" independent variable."""
    names_sorted = sorted(candidate_names)
    for p in INDEPENDENT_VARIABLE_PRIORITY:
        if p in names_sorted:
            return p
    return names_sorted[0] if names_sorted else "x"


def _structural_classify(parsed: ParsedEquation) -> Classification:
    notes: List[str] = []
    expr = parsed.rhs_expr if parsed.rhs_expr is not None else parsed.lhs_expr
    if expr is None:
        return Classification("unrecognized", "Unrecognized Expression", "mathematics", None, 0.3, True,
                               ["Could not build a symbolic expression from this input."])

    if parsed.is_ode:
        order_label = "First-Order" if parsed.ode_order == 1 else f"{parsed.ode_order}th-Order"
        return Classification("first_order_ode" if parsed.ode_order == 1 else "higher_order_ode",
                               f"{order_label} Ordinary Differential Equation",
                               "engineering_mathematics", None, 0.85, False,
                               ["Detected derivative notation (dy/dx or y')."])

    free_syms = list(expr.free_symbols)
    indep_candidates = [s for s in free_syms if str(s) != (parsed.dependent_name or "")]

    if _contains_func(expr, (sin, cos, tan)):
        return Classification("trigonometric", "Trigonometric Equation", "mathematics", None, 0.75, False, notes)
    if _contains_func(expr, (exp,)):
        return Classification("exponential", "Exponential Equation", "mathematics", None, 0.75, False, notes)
    if _contains_func(expr, (log,)):
        return Classification("logarithmic", "Logarithmic Equation", "mathematics", None, 0.75, False, notes)

    # Genuine two-variable *surface* case: both candidates actually appear
    # nonlinearly/structurally as coordinates (heuristic: neither name looks
    # like a conventional "parameter letter" such as a, b, c, k, m — those
    # are almost always coefficients, not a second plotting axis).
    PARAMETER_LOOKING_NAMES = {"a", "b", "c", "k", "m", "n", "p", "q", "r", "s"}
    if len(indep_candidates) == 2:
        names = {str(s) for s in indep_candidates}
        if not names.issubset(PARAMETER_LOOKING_NAMES):
            return Classification("multivariable_function", "Function of Two Variables (Surface)",
                                   "mathematics", None, 0.7, False,
                                   ["Two independent variables detected — best shown as a 3D surface."])

    if len(indep_candidates) >= 1:
        # Pick a single canonical independent (plotting) variable; treat the
        # rest as parameters/coefficients.
        x_name = choose_independent_variable([str(s) for s in indep_candidates])
        x = next(s for s in indep_candidates if str(s) == x_name)
        try:
            if expr.is_polynomial(x):
                d = int(degree(sympy.Poly(expr, x)))
                label_map = {1: ("linear", "Linear Equation"), 2: ("quadratic", "Quadratic Equation"),
                             3: ("cubic", "Cubic Equation")}
                if d in label_map:
                    cid, label = label_map[d]
                    return Classification(cid, label, "mathematics", None, 0.9, False, notes)
                return Classification("polynomial", f"Polynomial Equation (degree {d})",
                                       "mathematics", None, 0.85, False, notes)
        except Exception:  # noqa: BLE001
            pass
        try:
            if expr.is_rational_function(x) and not expr.is_polynomial(x):
                return Classification("rational_function", "Rational Function", "mathematics", None, 0.7, False, notes)
        except Exception:  # noqa: BLE001
            pass
        return Classification("generic_function", "Generic Function of One Variable",
                               "mathematics", None, 0.6, True,
                               ["Could not identify a more specific category; showing a general-purpose graph."])

    if len(indep_candidates) == 0:
        return Classification("constant_relationship", "Constant / Algebraic Relationship",
                               "mathematics", None, 0.5, True,
                               ["No free independent variable was detected."])

    return Classification("multivariable_function", "Multivariable Equation", "mathematics", None, 0.5, True, notes)


def classify(parsed: ParsedEquation) -> Classification:
    if not parsed.is_ode:
        symbol_names_lower = {n.lower() for n in parsed.free_symbol_names}
        dep_lower = parsed.dependent_name.lower() if parsed.dependent_name else None
        entry = find_library_match(symbol_names_lower, dep_lower)
        if entry is not None:
            return Classification(
                category_id=entry["id"], category_label=entry["category_label"],
                domain_area=entry["domain_area"], library_entry=entry, confidence=0.97,
                is_ambiguous=False, notes=[],
            )
    result = _structural_classify(parsed)
    return result


def list_known_categories() -> List[Dict[str, str]]:
    out = [{"id": e["id"], "label": e["category_label"], "domain_area": e["domain_area"]} for e in LIBRARY]
    out += [
        {"id": "linear", "label": "Linear Equation", "domain_area": "mathematics"},
        {"id": "quadratic", "label": "Quadratic Equation", "domain_area": "mathematics"},
        {"id": "cubic", "label": "Cubic Equation", "domain_area": "mathematics"},
        {"id": "polynomial", "label": "Polynomial Equation", "domain_area": "mathematics"},
        {"id": "trigonometric", "label": "Trigonometric Equation", "domain_area": "mathematics"},
        {"id": "exponential", "label": "Exponential Equation", "domain_area": "mathematics"},
        {"id": "logarithmic", "label": "Logarithmic Equation", "domain_area": "mathematics"},
        {"id": "rational_function", "label": "Rational Function", "domain_area": "mathematics"},
        {"id": "multivariable_function", "label": "Function of Two Variables (Surface)", "domain_area": "mathematics"},
        {"id": "first_order_ode", "label": "First-Order Differential Equation", "domain_area": "engineering_mathematics"},
    ]
    return out
