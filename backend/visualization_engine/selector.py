"""
Given an EquationAnalysis-like context and a requested (or default)
visualization id, computes the actual numeric data to render.

This module intentionally knows nothing about HTTP — it's called by the
API layer in api/routes_equations.py.
"""
from __future__ import annotations

from typing import Any, Dict, Optional

from equation_engine.analyzer import analyze_equation
from equation_engine.parser import parse_equation
from visualization_engine import compute as C


class VisualizationError(Exception):
    pass


def _param_defaults(analysis) -> Dict[str, float]:
    out = {}
    for v in analysis.variables:
        if v.default_value is not None:
            out[v.symbol] = v.default_value
    for c in analysis.constants:
        out[c.symbol] = c.value
    return out


def build_visualization(equation_text: str, visualization_id: Optional[str],
                         parameters: Dict[str, float], x_min: Optional[float],
                         x_max: Optional[float], locked_symbol: Optional[str] = None) -> Dict[str, Any]:
    analysis = analyze_equation(equation_text)
    if analysis.category == "unrecognized":
        raise VisualizationError("This does not look like a valid equation yet — please check the notation.")

    defaults = _param_defaults(analysis)
    merged_params = {**defaults, **parameters}

    viz_id = visualization_id or (analysis.recommended_visualizations[0].id if analysis.recommended_visualizations else "graph2d")

    if viz_id == "physics_force_block":
        data = C.compute_physics_force_block(merged_params)
        caption = f"F = {data['F']:.2f} N, m = {data['m']:.2f} kg → a = {data['a']:.2f} m/s²"
        return {"visualization_id": viz_id, "kind": "physics_force_block", "data": data, "caption": caption,
                "analysis": analysis}

    if viz_id == "circuit_ohm":
        data = C.compute_circuit_ohm(merged_params)
        caption = f"I = {data['I']:.2f} A, R = {data['R']:.2f} Ω → V = {data['V']:.2f} V"
        return {"visualization_id": viz_id, "kind": "circuit_ohm", "data": data, "caption": caption,
                "analysis": analysis}

    if viz_id == "projectile":
        data = C.compute_projectile(merged_params)
        caption = (f"Range = {data['range']:.1f} m, Max height = {data['max_height']:.1f} m, "
                   f"Time of flight = {data['time_of_flight']:.2f} s")
        return {"visualization_id": viz_id, "kind": "projectile", "data": data, "caption": caption,
                "analysis": analysis}

    if viz_id == "slope_field":
        parsed = parse_equation(equation_text)
        if not parsed.is_ode:
            raise VisualizationError("Slope fields require a differential equation (e.g. dy/dx = k*y).")
        extra = {k: v for k, v in merged_params.items() if k not in (parsed.ode_func_name, parsed.ode_var_name)}
        data = C.compute_slope_field(parsed.rhs_text, parsed.ode_func_name or "y", parsed.ode_var_name or "x",
                                      extra_params=extra)
        caption = f"Slope field for d{parsed.ode_func_name}/d{parsed.ode_var_name} = {parsed.rhs_text}"
        return {"visualization_id": viz_id, "kind": "slope_field", "data": data, "caption": caption,
                "analysis": analysis}

    if viz_id == "graph3d_surface":
        data = C.compute_graph3d_surface(equation_text)
        caption = f"Surface {data['z_label']} = f({data['x_label']}, {data['y_label']})"
        return {"visualization_id": viz_id, "kind": "graph3d_surface", "data": data, "caption": caption,
                "analysis": analysis}

    if viz_id == "transfer_function_step":
        zeta = float(merged_params.get("zeta", 0.3))
        wn = float(merged_params.get("wn", 3.0))
        data = C.compute_second_order_step_response(zeta, wn)
        caption = f"Step response — {data['regime'].replace('_', ' ')} (ζ={zeta:.2f}, ωₙ={wn:.2f})"
        return {"visualization_id": viz_id, "kind": "transfer_function_step", "data": data, "caption": caption,
                "analysis": analysis}

    # default: graph2d
    indep = analysis.independent_variables[0] if analysis.independent_variables else None
    dep = analysis.dependent_variables[0] if analysis.dependent_variables else "y"
    if indep is None:
        # Some equations (e.g. E = m*c^2) have no explicit "independent"
        # variable — they're a direct relationship rather than a function of
        # time/position. In that case, plot the dependent variable against
        # its first non-constant parameter instead (e.g. E vs. m).
        param_syms = [v.symbol for v in analysis.variables if v.role == "parameter"]
        indep = param_syms[0] if param_syms else None
    if indep is None:
        raise VisualizationError("Could not determine an independent variable to plot against.")

    plot_params = {k: v for k, v in merged_params.items() if k != indep}
    if locked_symbol:
        # In "Change One Thing" mode, only the locked symbol is allowed to vary;
        # everything else is frozen at its default.
        plot_params = {k: (v if k == locked_symbol else defaults.get(k, v)) for k, v in plot_params.items()}

    indep_var_meta = next((v for v in analysis.variables if v.symbol == indep), None)
    effective_x_min = x_min if x_min is not None else (indep_var_meta.min_value if indep_var_meta else None)
    effective_x_max = x_max if x_max is not None else (indep_var_meta.max_value if indep_var_meta else None)

    data = C.compute_graph2d(equation_text, plot_params, indep, dep, effective_x_min, effective_x_max)
    caption = f"{dep} as a function of {indep}"
    return {"visualization_id": "graph2d", "kind": "graph2d", "data": data, "caption": caption, "analysis": analysis}
