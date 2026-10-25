"""
Orchestrates: parse -> classify -> enrich -> produce EquationAnalysis.

This is the deterministic core described in spec section 13. The AI layer
(ai/explain_service.py) only ever consumes the *output* of this module to
write prose — it never invents variables, units, or relationships.
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional

import numpy as np
import sympy
from sympy import diff, lambdify, Symbol

from equation_engine.parser import parse_equation, to_latex, to_plain_text, EquationParseError
from equation_engine.classifier import classify, choose_independent_variable
from models.schemas import EquationAnalysis, VariableInfo, ConstantInfo, ParameterEffect, VisualizationOption

KNOWN_CONSTANTS = {
    "c": (299792458.0, "m/s", "Speed of light in vacuum"),
    "g": (9.80665, "m/s²", "Standard gravitational acceleration"),
    "pi": (float(np.pi), "-", "Pi"),
    "e": (float(np.e), "-", "Euler's number"),
    "h": (6.62607015e-34, "J·s", "Planck constant"),
    "k_b": (1.380649e-23, "J/K", "Boltzmann constant"),
}


def _default_range_for(name: str) -> Dict[str, float]:
    return {"default": 1.0, "min": -10.0, "max": 10.0, "step": 0.1}


def _generic_variable_info(name: str, role: str) -> VariableInfo:
    lname = name.lower()
    if lname in KNOWN_CONSTANTS:
        val, unit, desc = KNOWN_CONSTANTS[lname]
        return VariableInfo(symbol=name, name=name, role="constant", unit=unit,
                             description=desc, default_value=val)
    rng = _default_range_for(name)
    return VariableInfo(symbol=name, name=name, role=role,
                         description=f"Variable '{name}' appearing in the equation.",
                         default_value=rng["default"] if role != "independent" else None,
                         min_value=rng["min"], max_value=rng["max"], step=rng["step"])


def _sign_over_range(f, values: np.ndarray) -> str:
    """Classify how a scalar function behaves over sampled values: increases /
    decreases / non_monotonic / no_effect / undefined."""
    ys = []
    for v in values:
        try:
            y = float(f(v))
            if np.isnan(y) or np.isinf(y):
                continue
            ys.append(y)
        except Exception:  # noqa: BLE001
            continue
    if len(ys) < 2:
        return "undefined"
    diffs = np.diff(ys)
    diffs = diffs[np.abs(diffs) > 1e-9]
    if len(diffs) == 0:
        return "no_effect"
    if np.all(diffs > 0):
        return "increases"
    if np.all(diffs < 0):
        return "decreases"
    return "non_monotonic"


def _compute_parameter_effects(parsed, dependent_expr: Optional[sympy.Expr],
                                variables: List[VariableInfo]) -> List[ParameterEffect]:
    effects: List[ParameterEffect] = []
    if dependent_expr is None:
        return effects
    param_vars = [v for v in variables if v.role == "parameter"]
    base_point = {}
    for v in variables:
        if v.role in ("parameter", "independent") and v.default_value is not None:
            base_point[Symbol(v.symbol)] = v.default_value
        elif v.role == "independent":
            base_point[Symbol(v.symbol)] = 1.0
        elif v.role == "constant" and v.default_value is not None:
            base_point[Symbol(v.symbol)] = v.default_value

    for pv in param_vars:
        sym = Symbol(pv.symbol)
        if sym not in dependent_expr.free_symbols:
            continue
        try:
            other_syms = [s for s in dependent_expr.free_symbols if s != sym]
            fixed = {s: base_point.get(s, 1.0) for s in other_syms}
            partial_expr = dependent_expr.subs(fixed)
            f = lambdify(sym, partial_expr, modules=["numpy"])
            lo = pv.min_value if pv.min_value is not None else 0.1
            hi = pv.max_value if pv.max_value is not None else 10.0
            if lo <= 0 and hi > 0:
                lo = 0.01
            xs = np.linspace(lo, hi, 25)
            behavior = _sign_over_range(f, xs)
        except Exception:  # noqa: BLE001
            behavior = "undefined"

        verb = {
            "increases": f"increases the value",
            "decreases": f"decreases the value",
            "non_monotonic": "has a non-monotonic (mixed) effect on the value",
            "no_effect": "has no effect on the value",
            "undefined": "has an effect that depends on the other parameters",
        }.get(behavior, "affects the value")

        dep_name = variables[0].name if variables else "the dependent variable"
        explanation = f"Increasing {pv.name or pv.symbol} {verb} of {dep_name}."
        effects.append(ParameterEffect(symbol=pv.symbol, name=pv.name or pv.symbol,
                                        effect=behavior, explanation=explanation))
    return effects


def analyze_equation(raw_text: str, engineering_mode: bool = False) -> EquationAnalysis:
    try:
        parsed = parse_equation(raw_text)
    except EquationParseError as e:
        return EquationAnalysis(
            equation=raw_text, latex=raw_text, plain_text=raw_text,
            category="unrecognized", category_label="Could Not Parse",
            domain_area="mathematics",
            physical_interpretation="",
            confidence=0.0, is_ambiguous=True,
            warnings=[f"This does not look like a valid equation. Please check the notation. ({e})"],
        )

    classification = classify(parsed)
    latex = to_latex(parsed)
    plain_text = to_plain_text(parsed)

    variables: List[VariableInfo] = []
    constants: List[ConstantInfo] = []
    dependent_expr: Optional[sympy.Expr] = None
    warnings: List[str] = []

    entry = classification.library_entry
    if entry is not None:
        dependent_expr = parsed.rhs_expr
        for sym_name in parsed.free_symbol_names:
            meta = entry["variables"].get(sym_name.lower())
            if meta is None:
                variables.append(_generic_variable_info(sym_name, "parameter"))
                continue
            role = meta.get("role", "parameter")
            if role == "constant":
                constants.append(ConstantInfo(symbol=sym_name, value=float(meta.get("default", 0) or 0),
                                               unit=meta.get("unit"), description=meta.get("description")))
            variables.append(VariableInfo(
                symbol=sym_name, name=meta.get("name", sym_name), role=role,
                unit=meta.get("unit"), description=meta.get("description"),
                default_value=meta.get("default"), min_value=meta.get("min"),
                max_value=meta.get("max"), step=meta.get("step"),
            ))
        # Dependent variable (for display ordering) comes straight from the
        # library's own role metadata — not from which symbol happened to be
        # typed on the left-hand side, so "F = m*a" and "a = F/m" both work.
        dep_name = next((v.symbol for v in variables if v.role == "dependent"), parsed.dependent_name)
        variables.sort(key=lambda v: 0 if v.role == "dependent" else (1 if v.role == "parameter" else 2))

        relationships = entry["relationships"]
        physical_interpretation = entry["physical_interpretation"]
        recs = [VisualizationOption(id=entry["visualization"],
                                     label=_viz_label(entry["visualization"]),
                                     reason="Best represents the physical meaning of this equation.",
                                     is_recommended=True)]
        for sv in entry.get("secondary_visualizations", []):
            recs.append(VisualizationOption(id=sv["id"], label=sv["label"], reason=sv["reason"], is_recommended=False))

        param_effects: List[ParameterEffect] = []
        for sym_name, tmpl in entry.get("parameter_effect_templates", {}).items():
            var = next((v for v in variables if v.symbol.lower() == sym_name), None)
            param_effects.append(ParameterEffect(
                symbol=var.symbol if var else sym_name, name=var.name if var else sym_name,
                effect=tmpl["effect"], explanation=tmpl["explanation"],
            ))
        independent_vars = [v.symbol for v in variables if v.role == "independent"]
        dependent_vars = [v.symbol for v in variables if v.role == "dependent"]
        domain_area = classification.domain_area
        category_label = classification.category_label
        category_id = classification.category_id
        confidence = classification.confidence
        constraints = []

    else:
        # Generic / structural path
        if parsed.is_ode:
            dependent_expr = None
            variables.append(_generic_variable_info(parsed.ode_func_name or "y", "dependent"))
            variables.append(_generic_variable_info(parsed.ode_var_name or "x", "independent"))
            for name in parsed.free_symbol_names:
                if name in (parsed.ode_func_name, parsed.ode_var_name):
                    continue
                variables.append(_generic_variable_info(name, "parameter"))
            relationships = [
                f"The rate of change of {parsed.ode_func_name} with respect to {parsed.ode_var_name} "
                f"depends on: {parsed.rhs_text}.",
            ]
            physical_interpretation = (
                "This is a differential equation: rather than describing a value directly, it "
                "describes how that value changes. Solving it (or tracing its slope field) reveals "
                "the family of possible behaviors, such as growth or decay curves."
            )
            recs = [
                VisualizationOption(id="slope_field", label="Slope Field + Solution Curves",
                                     reason="Shows the direction of change everywhere and traces solutions from different starting points.",
                                     is_recommended=True),
            ]
            independent_vars = [parsed.ode_var_name or "x"]
            dependent_vars = [parsed.ode_func_name or "y"]
            domain_area = classification.domain_area
            category_label = classification.category_label
            category_id = classification.category_id
            confidence = classification.confidence
            constraints = []
            param_effects = []
        else:
            expr = parsed.rhs_expr if parsed.rhs_expr is not None else parsed.lhs_expr
            dependent_expr = expr
            free_syms = sorted({str(s) for s in (expr.free_symbols if expr is not None else [])})
            dep_name = parsed.dependent_name

            if classification.category_id == "multivariable_function":
                indep = [s for s in free_syms if s != dep_name][:2]
                for s in indep:
                    variables.append(_generic_variable_info(s, "independent"))
                if dep_name:
                    variables.append(_generic_variable_info(dep_name, "dependent"))
                else:
                    variables.append(VariableInfo(symbol="z", name="z", role="dependent"))
                independent_vars = indep
                dependent_vars = [dep_name or "z"]
                recs = [VisualizationOption(id="graph3d_surface", label="3D Surface",
                                             reason="Two independent variables map naturally to a surface z = f(x, y).",
                                             is_recommended=True),
                        VisualizationOption(id="contour", label="Contour Plot",
                                             reason="A top-down view of the same surface, useful for spotting level curves.",
                                             is_recommended=False)]
            else:
                indep = [s for s in free_syms if s != dep_name]
                x_name = choose_independent_variable(indep) if indep else "x"
                variables.append(_generic_variable_info(x_name, "independent"))
                if dep_name:
                    variables.append(_generic_variable_info(dep_name, "dependent"))
                else:
                    variables.append(VariableInfo(symbol="y", name="y", role="dependent"))
                for s in indep:
                    if s != x_name:
                        variables.append(_generic_variable_info(s, "parameter"))
                independent_vars = [x_name]
                dependent_vars = [dep_name or "y"]
                recs = [VisualizationOption(id="graph2d", label="2D Graph",
                                             reason="A single independent variable maps naturally to a line/curve graph.",
                                             is_recommended=True)]

            relationships = [f"{dependent_vars[0]} is determined by evaluating: {parsed.rhs_text or parsed.normalized}."]
            physical_interpretation = _generic_interpretation(classification.category_id)
            domain_area = classification.domain_area
            category_label = classification.category_label
            category_id = classification.category_id
            confidence = classification.confidence
            constraints = _domain_constraints(expr, free_syms)
            param_effects = _compute_parameter_effects(parsed, dependent_expr, variables)

    if classification.notes:
        warnings.extend(classification.notes)

    return EquationAnalysis(
        equation=raw_text,
        latex=latex,
        plain_text=plain_text,
        category=category_id,
        category_label=category_label,
        domain_area=domain_area,
        physical_interpretation=physical_interpretation,
        variables=variables,
        constants=constants,
        independent_variables=independent_vars,
        dependent_variables=dependent_vars,
        relationships=relationships,
        constraints=constraints,
        recommended_visualizations=recs,
        parameter_effects=param_effects,
        confidence=confidence,
        is_ambiguous=classification.is_ambiguous,
        warnings=warnings,
    )


def _viz_label(viz_id: str) -> str:
    return {
        "physics_force_block": "Force/Mass/Acceleration Diagram",
        "circuit_ohm": "Circuit Diagram",
        "graph2d": "2D Graph",
        "graph3d_surface": "3D Surface",
        "slope_field": "Slope Field",
        "projectile": "Projectile Motion Simulation",
        "phasor": "Phasor Diagram",
    }.get(viz_id, viz_id.replace("_", " ").title())


def _generic_interpretation(category_id: str) -> str:
    return {
        "linear": "This equation describes a straight-line relationship: the dependent variable changes at a constant rate as the independent variable changes.",
        "quadratic": "This equation describes a parabola: the dependent variable changes at a rate that itself increases, producing curved, symmetric behavior.",
        "cubic": "This equation describes a cubic curve, which can have inflection points and asymmetric behavior compared to a parabola.",
        "polynomial": "This equation is a polynomial relationship — a sum of power terms of the independent variable.",
        "trigonometric": "This equation is periodic — its value repeats in a regular cycle as the independent variable increases.",
        "exponential": "This equation describes exponential behavior — the rate of change is proportional to the current value, producing rapid growth or decay.",
        "logarithmic": "This equation describes logarithmic behavior — rapid change at small values that slows dramatically as the input grows.",
        "rational_function": "This equation is a ratio of two expressions and may have asymptotes where the denominator approaches zero.",
        "generic_function": "This is a general mathematical relationship between the detected variables.",
    }.get(category_id, "This is a mathematical relationship between the detected variables.")


def _domain_constraints(expr, free_syms: List[str]) -> List[str]:
    constraints: List[str] = []
    try:
        text = str(expr)
        if "log(" in text:
            constraints.append("Defined only where the argument of the logarithm is positive.")
        if "sqrt(" in text:
            constraints.append("Defined only where the expression under the square root is non-negative.")
        if "/" in text:
            constraints.append("Undefined where the denominator equals zero.")
    except Exception:  # noqa: BLE001
        pass
    return constraints
