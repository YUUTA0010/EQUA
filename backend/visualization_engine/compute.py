"""
Deterministic numeric computation for every visualization kind EquationLens
supports. Nothing here calls an LLM — everything is SymPy/NumPy/SciPy, per
spec section 13 ("never trust an LLM alone for mathematical calculations").
"""
from __future__ import annotations

import math
from typing import Any, Dict, List, Optional

import numpy as np
import sympy
from sympy import Symbol, lambdify, diff, solve

from equation_engine.parser import parse_equation, EquationParseError


def _safe_lambdify(expr: sympy.Expr, syms: List[Symbol]):
    return lambdify(syms, expr, modules=["numpy"])


def _eval_grid(f, xs: np.ndarray) -> np.ndarray:
    with np.errstate(all="ignore"):
        try:
            ys = f(xs)
            ys = np.asarray(ys, dtype=float)
            if ys.shape == ():
                ys = np.full_like(xs, float(ys))
        except Exception:  # noqa: BLE001
            ys = np.array([_safe_scalar(f, x) for x in xs])
    ys[np.iscomplex(ys) if np.iscomplexobj(ys) else np.zeros_like(ys, dtype=bool)] = np.nan
    return ys.astype(float) if not np.iscomplexobj(ys) else np.real(ys)


def _safe_scalar(f, x: float) -> float:
    try:
        v = f(x)
        v = complex(v)
        if abs(v.imag) > 1e-9:
            return float("nan")
        return float(v.real)
    except Exception:  # noqa: BLE001
        return float("nan")


# ---------------------------------------------------------------------------
# 2D Cartesian graph (also reused for velocity/energy/etc. line graphs)
# ---------------------------------------------------------------------------
def compute_graph2d(equation_text: str, parameters: Dict[str, float],
                     independent_symbol: str, dependent_symbol: str,
                     x_min: Optional[float] = None, x_max: Optional[float] = None,
                     n_points: int = 400) -> Dict[str, Any]:
    parsed = parse_equation(equation_text)
    expr = parsed.rhs_expr if parsed.rhs_expr is not None else parsed.lhs_expr
    if expr is None:
        raise ValueError("Could not build an expression to plot.")

    x = Symbol(independent_symbol)
    subs_map = {Symbol(k): v for k, v in parameters.items() if k != independent_symbol}
    expr_sub = expr.subs(subs_map)

    lo = x_min if x_min is not None else -10.0
    hi = x_max if x_max is not None else 10.0
    if hi <= lo:
        hi = lo + 1.0
    xs = np.linspace(lo, hi, n_points)

    try:
        f = _safe_lambdify(expr_sub, [x])
        ys = _eval_grid(f, xs)
    except Exception:  # noqa: BLE001
        ys = np.full_like(xs, np.nan)

    # key features: roots, extrema (numeric, best-effort)
    key_points: List[Dict[str, float]] = []
    try:
        deriv = diff(expr_sub, x)
        crit_points = solve(sympy.Eq(deriv, 0), x)
        for cp in crit_points:
            try:
                cp_val = float(cp)
                if lo <= cp_val <= hi:
                    y_val = float(expr_sub.subs(x, cp_val))
                    if not math.isnan(y_val):
                        key_points.append({"x": cp_val, "y": y_val, "label": "critical point"})
            except (TypeError, ValueError):
                continue
    except Exception:  # noqa: BLE001
        pass

    try:
        roots = solve(sympy.Eq(expr_sub, 0), x)
        for r in roots:
            try:
                r_val = float(r)
                if lo <= r_val <= hi:
                    key_points.append({"x": r_val, "y": 0.0, "label": "root"})
            except (TypeError, ValueError):
                continue
    except Exception:  # noqa: BLE001
        pass

    return {
        "x": xs.tolist(),
        "y": [None if (isinstance(v, float) and math.isnan(v)) else v for v in ys.tolist()],
        "x_label": independent_symbol,
        "y_label": dependent_symbol,
        "key_points": key_points,
    }


def compute_multi_series_graph2d(series_defs: List[Dict[str, Any]]) -> Dict[str, Any]:
    """series_defs: [{name, equation_text, parameters, independent_symbol, dependent_symbol, x_min, x_max}]"""
    series = []
    for sd in series_defs:
        result = compute_graph2d(
            sd["equation_text"], sd.get("parameters", {}), sd["independent_symbol"],
            sd["dependent_symbol"], sd.get("x_min"), sd.get("x_max"),
        )
        result["name"] = sd.get("name", sd["dependent_symbol"])
        series.append(result)
    return {"series": series}


# ---------------------------------------------------------------------------
# 3D surface z = f(x, y)
# ---------------------------------------------------------------------------
def compute_graph3d_surface(equation_text: str, x_range=(-5, 5), y_range=(-5, 5), n: int = 45) -> Dict[str, Any]:
    parsed = parse_equation(equation_text)
    expr = parsed.rhs_expr if parsed.rhs_expr is not None else parsed.lhs_expr
    free = sorted({str(s) for s in expr.free_symbols})
    dep_name = parsed.dependent_name
    indep = [s for s in free if s != dep_name][:2]
    if len(indep) < 2:
        raise ValueError("This equation does not have two independent variables to plot as a surface.")
    xs = np.linspace(x_range[0], x_range[1], n)
    ys = np.linspace(y_range[0], y_range[1], n)
    X, Y = np.meshgrid(xs, ys)
    f = _safe_lambdify(expr, [Symbol(indep[0]), Symbol(indep[1])])
    with np.errstate(all="ignore"):
        try:
            Z = f(X, Y)
            Z = np.asarray(Z, dtype=float)
            if Z.shape != X.shape:
                Z = np.full_like(X, float(Z))
        except Exception:  # noqa: BLE001
            Z = np.full_like(X, np.nan)
    Z = np.where(np.isfinite(Z), Z, None)
    return {
        "x": xs.tolist(), "y": ys.tolist(), "z": Z.tolist(),
        "x_label": indep[0], "y_label": indep[1], "z_label": dep_name or "z",
    }


# ---------------------------------------------------------------------------
# Physics: F = m * a block-and-arrows scene
# ---------------------------------------------------------------------------
def compute_physics_force_block(parameters: Dict[str, float]) -> Dict[str, Any]:
    F = float(parameters.get("F", parameters.get("f", 10.0)))
    m = float(parameters.get("m", 5.0))
    m = max(m, 0.01)
    a = F / m
    # sweep for the two relationship mini-graphs
    m_sweep = np.linspace(0.5, max(50.0, m * 2), 60)
    a_vs_m = (F / m_sweep).tolist()
    F_sweep = np.linspace(0.0, max(100.0, F * 2), 60)
    a_vs_F = (F_sweep / m).tolist()
    return {
        "F": F, "m": m, "a": a,
        "a_vs_m": {"x": m_sweep.tolist(), "y": a_vs_m, "x_label": "m (kg)", "y_label": "a (m/s²)", "current_x": m},
        "a_vs_F": {"x": F_sweep.tolist(), "y": a_vs_F, "x_label": "F (N)", "y_label": "a (m/s²)", "current_x": F},
    }


# ---------------------------------------------------------------------------
# Electrical: V = I * R circuit scene
# ---------------------------------------------------------------------------
def compute_circuit_ohm(parameters: Dict[str, float]) -> Dict[str, Any]:
    I = float(parameters.get("I", parameters.get("i", 0.5)))
    R = float(parameters.get("R", parameters.get("r", 10.0)))
    R = max(R, 0.01)
    V = I * R
    R_sweep = np.linspace(1.0, max(200.0, R * 2), 60)
    V_vs_R = (I * R_sweep).tolist()
    I_sweep = np.linspace(0.0, max(5.0, I * 2), 60)
    V_vs_I = (I_sweep * R).tolist()
    return {
        "V": V, "I": I, "R": R,
        "V_vs_R": {"x": R_sweep.tolist(), "y": V_vs_R, "x_label": "R (Ω)", "y_label": "V (V)", "current_x": R},
        "V_vs_I": {"x": I_sweep.tolist(), "y": V_vs_I, "x_label": "I (A)", "y_label": "V (V)", "current_x": I},
    }


# ---------------------------------------------------------------------------
# Projectile motion
# ---------------------------------------------------------------------------
def compute_projectile(parameters: Dict[str, float]) -> Dict[str, Any]:
    v0 = float(parameters.get("v0", 20.0))
    theta_deg = float(parameters.get("theta", 45.0))
    g = float(parameters.get("g", 9.81))
    g = max(g, 0.01)
    theta = math.radians(theta_deg)

    t_flight = (2 * v0 * math.sin(theta)) / g if v0 > 0 else 0.0
    n = 200
    ts = np.linspace(0, max(t_flight, 0.01), n)
    xs = v0 * np.cos(theta) * ts
    ys = v0 * np.sin(theta) * ts - 0.5 * g * ts ** 2
    ys = np.clip(ys, 0, None)

    max_height = (v0 ** 2) * (math.sin(theta) ** 2) / (2 * g)
    range_ = (v0 ** 2) * math.sin(2 * theta) / g

    return {
        "x": xs.tolist(), "y": ys.tolist(), "t": ts.tolist(),
        "v0": v0, "theta_deg": theta_deg, "g": g,
        "time_of_flight": t_flight, "max_height": max_height, "range": range_,
        "vx0": v0 * math.cos(theta), "vy0": v0 * math.sin(theta),
    }


# ---------------------------------------------------------------------------
# Slope field + solution curves for first-order ODEs: dy/dx = f(x, y)
# ---------------------------------------------------------------------------
def compute_slope_field(rhs_text: str, func_name: str = "y", var_name: str = "x",
                         x_range=(-5, 5), y_range=(-5, 5), grid_n: int = 18,
                         initial_conditions: Optional[List[float]] = None,
                         extra_params: Optional[Dict[str, float]] = None) -> Dict[str, Any]:
    x_sym, y_sym = Symbol(var_name), Symbol(func_name)
    param_syms = {}
    text = rhs_text
    all_names = set()
    import re as _re
    for tok in _re.findall(r"[A-Za-z_]\w*", text):
        all_names.add(tok)
    all_names.discard(var_name)
    all_names.discard(func_name)
    from utils.security import CALLABLE_FUNCTION_NAMES as _AFN
    all_names -= _AFN
    local = {var_name: x_sym, func_name: y_sym}
    for n_ in all_names:
        local[n_] = Symbol(n_)
    from utils.security import safe_parse_expr
    expr = safe_parse_expr(text, local)
    if extra_params:
        expr = expr.subs({Symbol(k): v for k, v in extra_params.items()})

    f = _safe_lambdify(expr, [x_sym, y_sym])

    xs = np.linspace(x_range[0], x_range[1], grid_n)
    ys = np.linspace(y_range[0], y_range[1], grid_n)
    segments = []
    with np.errstate(all="ignore"):
        for xv in xs:
            for yv in ys:
                try:
                    slope = float(f(xv, yv))
                    if not np.isfinite(slope):
                        continue
                except Exception:  # noqa: BLE001
                    continue
                norm = math.sqrt(1 + slope ** 2)
                dx = 0.35 * (x_range[1] - x_range[0]) / grid_n / norm
                dy = slope * dx
                segments.append({"x0": xv - dx, "y0": yv - dy, "x1": xv + dx, "y1": yv + dy})

    # solution curves via simple RK4 for each initial condition
    ics = initial_conditions if initial_conditions else [-2.0, 0.0, 2.0]
    curves = []
    for y0 in ics:
        curve_x, curve_y = [], []
        h = (x_range[1] - x_range[0]) / 400
        x_cur, y_cur = 0.0, float(y0)
        # integrate forward
        pts_fwd = []
        x_cur, y_cur = 0.0, float(y0)
        while x_cur <= x_range[1]:
            pts_fwd.append((x_cur, y_cur))
            try:
                k1 = float(f(x_cur, y_cur))
                k2 = float(f(x_cur + h / 2, y_cur + h / 2 * k1))
                k3 = float(f(x_cur + h / 2, y_cur + h / 2 * k2))
                k4 = float(f(x_cur + h, y_cur + h * k3))
                y_cur = y_cur + (h / 6) * (k1 + 2 * k2 + 2 * k3 + k4)
            except Exception:  # noqa: BLE001
                break
            x_cur += h
            if not np.isfinite(y_cur) or abs(y_cur) > 1e6:
                break
        # integrate backward
        pts_bwd = []
        x_cur, y_cur = 0.0, float(y0)
        while x_cur >= x_range[0]:
            pts_bwd.append((x_cur, y_cur))
            try:
                k1 = float(f(x_cur, y_cur))
                k2 = float(f(x_cur - h / 2, y_cur - h / 2 * k1))
                k3 = float(f(x_cur - h / 2, y_cur - h / 2 * k2))
                k4 = float(f(x_cur - h, y_cur - h * k3))
                y_cur = y_cur - (h / 6) * (k1 + 2 * k2 + 2 * k3 + k4)
            except Exception:  # noqa: BLE001
                break
            x_cur -= h
            if not np.isfinite(y_cur) or abs(y_cur) > 1e6:
                break
        pts = list(reversed(pts_bwd)) + pts_fwd[1:]
        curves.append({"y0": y0, "x": [p[0] for p in pts], "y": [p[1] for p in pts]})

    return {"segments": segments, "curves": curves, "x_range": list(x_range), "y_range": list(y_range)}


# ---------------------------------------------------------------------------
# Bonus: 2nd-order control system step response + poles (engineering mode)
# ---------------------------------------------------------------------------
def compute_second_order_step_response(zeta: float, wn: float, t_max: Optional[float] = None) -> Dict[str, Any]:
    zeta = max(zeta, 0.0)
    wn = max(wn, 0.01)
    if t_max is None:
        t_max = 8.0 / (zeta * wn) if zeta > 0.02 else 20.0 / wn
    t_max = min(max(t_max, 1.0), 60.0)
    ts = np.linspace(0, t_max, 500)

    if zeta < 1:
        wd = wn * math.sqrt(1 - zeta ** 2)
        phi = math.acos(zeta) if zeta <= 1 else 0.0
        y = 1 - (np.exp(-zeta * wn * ts) / math.sqrt(1 - zeta ** 2)) * np.sin(wd * ts + phi)
        poles = [{"re": -zeta * wn, "im": wd}, {"re": -zeta * wn, "im": -wd}]
        regime = "underdamped"
    elif abs(zeta - 1) < 1e-6:
        y = 1 - np.exp(-wn * ts) * (1 + wn * ts)
        poles = [{"re": -wn, "im": 0.0}, {"re": -wn, "im": 0.0}]
        regime = "critically_damped"
    else:
        r1 = -wn * (zeta - math.sqrt(zeta ** 2 - 1))
        r2 = -wn * (zeta + math.sqrt(zeta ** 2 - 1))
        y = 1 + (r2 * np.exp(r1 * ts) - r1 * np.exp(r2 * ts)) / (r1 - r2)
        poles = [{"re": r1, "im": 0.0}, {"re": r2, "im": 0.0}]
        regime = "overdamped"

    return {
        "t": ts.tolist(), "y": y.tolist(), "poles": poles, "regime": regime,
        "zeta": zeta, "wn": wn,
    }
