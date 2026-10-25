"""
Turns raw equation text (typed, pasted, or OCR'd) into a structured,
SymPy-backed representation.

Handles common textbook/OCR notation quirks:
  * unicode superscripts/subscripts (x², v₀)
  * unicode math operators (×, ÷, −, √)
  * Greek letters spelled with unicode glyphs (ω, θ, φ, ζ, π, μ, Ω, α, β, λ, Δ, σ)
  * simple first-order derivative notation: dy/dx, y', dx/dt
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple

import sympy
from sympy import Eq, Symbol, Function

from utils.security import safe_parse_expr, UnsafeExpressionError, CALLABLE_FUNCTION_NAMES

SUPERSCRIPT_MAP = {
    "⁰": "0", "¹": "1", "²": "2", "³": "3", "⁴": "4",
    "⁵": "5", "⁶": "6", "⁷": "7", "⁸": "8", "⁹": "9",
}
SUBSCRIPT_MAP = {
    "₀": "_0", "₁": "_1", "₂": "_2", "₃": "_3", "₄": "_4",
    "₅": "_5", "₆": "_6", "₇": "_7", "₈": "_8", "₉": "_9",
}
GREEK_MAP = {
    "ω": "omega", "Ω": "Omega", "θ": "theta", "φ": "phi", "ϕ": "phi",
    "ζ": "zeta", "π": "pi", "μ": "mu", "α": "alpha", "β": "beta",
    "λ": "lambda_", "Δ": "Delta", "δ": "delta", "σ": "sigma", "γ": "gamma",
    "τ": "tau", "Σ": "Sigma", "ρ": "rho", "χ": "chi", "ψ": "psi",
}


def _replace_superscripts(text: str) -> str:
    """Convert runs like x² into x**2 (only for simple trailing digit superscripts)."""
    def repl(match: "re.Match") -> str:
        base = match.group(1)
        exp_chars = match.group(2)
        exp = "".join(SUPERSCRIPT_MAP.get(ch, ch) for ch in exp_chars)
        return f"{base}**{exp}"

    pattern = re.compile(r"([A-Za-z0-9\)\]])([⁰¹²³⁴⁵⁶⁷⁸⁹]+)")
    return pattern.sub(repl, text)


def _replace_subscripts(text: str) -> str:
    for ch, repl in SUBSCRIPT_MAP.items():
        text = text.replace(ch, repl)
    return text


def normalize_ascii_math(raw: str) -> str:
    text = raw.strip()
    text = text.replace("−", "-").replace("×", "*").replace("·", "*").replace("÷", "/")
    text = text.replace("√", "sqrt")
    text = _replace_superscripts(text)
    text = _replace_subscripts(text)
    for ch, word in GREEK_MAP.items():
        text = text.replace(ch, word)
    # normalize common "^" already handled by convert_xor transform; leave as-is
    # collapse whitespace
    text = re.sub(r"\s+", " ", text).strip()
    return text


ODE_PATTERNS = [
    re.compile(r"d\s*([a-zA-Z_]\w*)\s*/\s*d\s*([a-zA-Z_]\w*)"),  # dy/dx
    re.compile(r"([a-zA-Z_]\w*)\s*'\s*\("),  # y'(x)
    re.compile(r"([a-zA-Z_]\w*)\s*'(?!\w)"),  # y'
]


@dataclass
class ParsedEquation:
    raw: str
    normalized: str
    is_equation: bool  # has "=" sign
    is_ode: bool
    ode_order: int
    lhs_text: Optional[str]
    rhs_text: Optional[str]
    lhs_expr: Optional[sympy.Expr]
    rhs_expr: Optional[sympy.Expr]
    free_symbol_names: List[str]
    dependent_name: Optional[str]
    independent_name: Optional[str]
    ode_func_name: Optional[str] = None
    ode_var_name: Optional[str] = None
    ode_rhs_of_derivative: Optional[str] = None  # e.g. "k*y" text for dy/dx = k*y


class EquationParseError(Exception):
    pass


def _detect_ode(normalized: str) -> Tuple[bool, int, Optional[str], Optional[str]]:
    """Very deliberately limited: detects first-order ODEs of the form
    dy/dx = f(x,y) or y' = f(x,y). Higher-order/PDE detection is flagged but
    not symbolically solved in this version (see README roadmap)."""
    m = ODE_PATTERNS[0].search(normalized)
    if m:
        return True, 1, m.group(1), m.group(2)
    m = ODE_PATTERNS[1].search(normalized) or ODE_PATTERNS[2].search(normalized)
    if m:
        return True, 1, m.group(1), None
    if "d2y" in normalized.replace(" ", "").lower() or "d^2y" in normalized.replace(" ", "").lower():
        return True, 2, "y", "x"
    return False, 0, None, None


def parse_equation(raw_text: str) -> ParsedEquation:
    normalized = normalize_ascii_math(raw_text)
    is_ode, ode_order, func_name, var_name = _detect_ode(normalized)

    if is_ode and ode_order == 1:
        # Expect pattern like "dy/dx = k*y" or "y' = k*y"
        if "=" not in normalized:
            raise EquationParseError("A differential equation must contain '='.")
        _, rhs_text = normalized.split("=", 1)
        rhs_text = rhs_text.strip()
        indep = var_name or "x"
        dep = func_name or "y"
        try:
            # Build symbols for everything except the function/derivative names themselves
            candidate_symbols = set(re.findall(r"[A-Za-z_]\w*", rhs_text))
            candidate_symbols -= CALLABLE_FUNCTION_NAMES
            candidate_symbols.discard(dep)
            candidate_symbols.discard(indep)
            local = {s: Symbol(s) for s in candidate_symbols}
            local[dep] = Symbol(dep)
            local[indep] = Symbol(indep)
            rhs_expr = safe_parse_expr(rhs_text, local)
        except UnsafeExpressionError as e:
            raise EquationParseError(str(e)) from e
        return ParsedEquation(
            raw=raw_text, normalized=normalized, is_equation=True, is_ode=True, ode_order=1,
            lhs_text=f"d{dep}/d{indep}", rhs_text=rhs_text, lhs_expr=None, rhs_expr=rhs_expr,
            free_symbol_names=sorted({str(s) for s in rhs_expr.free_symbols} | {dep, indep}),
            dependent_name=dep, independent_name=indep,
            ode_func_name=dep, ode_var_name=indep, ode_rhs_of_derivative=rhs_text,
        )

    if "=" in normalized:
        lhs_text, rhs_text = normalized.split("=", 1)
        lhs_text, rhs_text = lhs_text.strip(), rhs_text.strip()
        all_names = set(re.findall(r"[A-Za-z_]\w*", lhs_text + " " + rhs_text))
        all_names -= CALLABLE_FUNCTION_NAMES
        local = {n: Symbol(n) for n in all_names}
        try:
            lhs_expr = safe_parse_expr(lhs_text, local)
            rhs_expr = safe_parse_expr(rhs_text, local)
        except UnsafeExpressionError as e:
            raise EquationParseError(str(e)) from e
        free = sorted({str(s) for s in (lhs_expr.free_symbols | rhs_expr.free_symbols)})
        dependent_name = str(lhs_expr) if lhs_expr.is_symbol else None
        return ParsedEquation(
            raw=raw_text, normalized=normalized, is_equation=True, is_ode=False, ode_order=0,
            lhs_text=lhs_text, rhs_text=rhs_text, lhs_expr=lhs_expr, rhs_expr=rhs_expr,
            free_symbol_names=free, dependent_name=dependent_name, independent_name=None,
        )
    else:
        all_names = set(re.findall(r"[A-Za-z_]\w*", normalized))
        all_names -= CALLABLE_FUNCTION_NAMES
        local = {n: Symbol(n) for n in all_names}
        try:
            expr = safe_parse_expr(normalized, local)
        except UnsafeExpressionError as e:
            raise EquationParseError(str(e)) from e
        free = sorted({str(s) for s in expr.free_symbols})
        return ParsedEquation(
            raw=raw_text, normalized=normalized, is_equation=False, is_ode=False, ode_order=0,
            lhs_text=None, rhs_text=normalized, lhs_expr=None, rhs_expr=expr,
            free_symbol_names=free, dependent_name=None, independent_name=None,
        )


def to_latex(parsed: ParsedEquation) -> str:
    try:
        if parsed.is_ode:
            dep = parsed.ode_func_name or "y"
            indep = parsed.ode_var_name or "x"
            rhs_local = {s: Symbol(s) for s in parsed.free_symbol_names}
            rhs_expr = parsed.rhs_expr if parsed.rhs_expr is not None else safe_parse_expr(parsed.rhs_text or "0", rhs_local)
            return rf"\frac{{d{dep}}}{{d{indep}}} = {sympy.latex(rhs_expr)}"
        if parsed.is_equation and parsed.lhs_expr is not None and parsed.rhs_expr is not None:
            return sympy.latex(Eq(parsed.lhs_expr, parsed.rhs_expr))
        if parsed.rhs_expr is not None:
            return sympy.latex(parsed.rhs_expr)
    except Exception:  # noqa: BLE001
        pass
    return parsed.normalized


def to_plain_text(parsed: ParsedEquation) -> str:
    if parsed.is_ode:
        dep = parsed.ode_func_name or "y"
        indep = parsed.ode_var_name or "x"
        return f"d{dep}/d{indep} = {parsed.rhs_text}"
    if parsed.lhs_text and parsed.rhs_text:
        return f"{parsed.lhs_text} = {parsed.rhs_text}"
    return parsed.normalized
