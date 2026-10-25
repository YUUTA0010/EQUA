"""
Generates natural-language explanations.

Per spec section 13: the AI is used ONLY for prose/semantic phrasing. Every
fact it's allowed to mention (variables, units, relationships, parameter
effects) was already computed deterministically by equation_engine/*. When
no OPENAI_API_KEY is configured (or the call fails for any reason), a
template engine produces equally factual — if less stylistically varied —
explanations, so the app is fully usable in demo mode (spec section 28).
"""
from __future__ import annotations

import os
from typing import Any, Dict

from models.schemas import EquationAnalysis

_OPENAI_CLIENT = None


def _get_client():
    global _OPENAI_CLIENT
    api_key = os.environ.get("OPENAI_API_KEY", "").strip()
    if not api_key:
        return None
    if _OPENAI_CLIENT is not None:
        return _OPENAI_CLIENT
    try:
        from openai import OpenAI
        _OPENAI_CLIENT = OpenAI(api_key=api_key)
        return _OPENAI_CLIENT
    except Exception:  # noqa: BLE001
        return None


def _analysis_context(analysis: EquationAnalysis) -> str:
    var_lines = "\n".join(
        f"- {v.symbol} ({v.role}): {v.name}" + (f", unit={v.unit}" if v.unit else "")
        for v in analysis.variables
    )
    rel_lines = "\n".join(f"- {r}" for r in analysis.relationships)
    return (
        f"Equation: {analysis.plain_text}\n"
        f"Category: {analysis.category_label}\n"
        f"Domain: {analysis.domain_area}\n"
        f"Physical interpretation (already established, do not contradict): {analysis.physical_interpretation}\n"
        f"Variables:\n{var_lines}\n"
        f"Known relationships (already established, do not contradict):\n{rel_lines}\n"
    )


def _call_openai(system: str, user: str) -> str | None:
    client = _get_client()
    if client is None:
        return None
    model = os.environ.get("OPENAI_MODEL", "gpt-4o-mini")
    try:
        resp = client.chat.completions.create(
            model=model,
            messages=[{"role": "system", "content": system}, {"role": "user", "content": user}],
            temperature=0.4,
            max_tokens=350,
        )
        return resp.choices[0].message.content.strip()
    except Exception:  # noqa: BLE001
        return None


SYSTEM_PROMPT = (
    "You are EquationLens's explanation engine. You are given the RESULT of a deterministic "
    "symbolic-math analysis of an equation (variables, units, relationships, category). "
    "Write a short, clear explanation for a student. Do NOT invent new variables, units, "
    "numeric results, or relationships beyond what is given — only rephrase and connect them "
    "in plain language. Keep it under 120 words. Do not use markdown headers."
)


def _template_what_it_does(analysis: EquationAnalysis) -> str:
    parts = [analysis.physical_interpretation.strip()] if analysis.physical_interpretation else []
    if analysis.variables:
        var_desc = ", ".join(
            f"{v.symbol} is {v.name.lower() if v.name else v.symbol}" for v in analysis.variables[:5]
        )
        parts.append(f"In this equation, {var_desc}.")
    if analysis.relationships:
        parts.append(analysis.relationships[0])
    return " ".join(parts) or f"This is a {analysis.category_label.lower()}."


def _template_why_looks_like_that(analysis: EquationAnalysis) -> str:
    cat = analysis.category
    if cat == "quadratic":
        return ("The squared term is what produces the curved, symmetric parabola shape: "
                "both a positive and a negative input of the same magnitude square to the same "
                "positive value, so the graph is a mirror image about its axis of symmetry. "
                "The sign and size of the squared term's coefficient control whether the curve "
                "opens upward or downward, and how narrow or wide it is.")
    if cat == "linear":
        return ("Because the independent variable only appears to the first power, equal steps "
                "in x always produce equal steps in y — that constant rate of change is exactly "
                "what makes the graph a straight line. The coefficient sets the steepness (slope) "
                "and the constant term sets where the line crosses the y-axis.")
    if cat == "trigonometric" or cat == "simple_harmonic_motion":
        return ("Sine and cosine repeat every 2π, which is why the graph shows a regular, "
                "repeating wave rather than settling to a single value. The coefficient in front "
                "stretches the wave vertically (amplitude), the coefficient multiplying the "
                "variable compresses or stretches it horizontally (frequency), and any constant "
                "added inside the function slides the wave left or right (phase).")
    if cat == "exponential":
        return ("Because the variable sits in the exponent, each equal step in x multiplies the "
                "output by the same factor rather than adding a fixed amount — that's what "
                "produces the rapidly curving growth or decay shape instead of a straight line.")
    if cat == "newtons_second_law":
        return ("The diagram shows two arrows because force and acceleration point in the same "
                "direction for a given mass — Newton's Second Law is a direct proportionality "
                "between them, scaled by mass. A bigger block (more mass) visibly needs a bigger "
                "force arrow to produce the same length acceleration arrow.")
    if cat == "ohms_law":
        return ("Voltage grows in a straight line as current increases because resistance is "
                "held constant in this view — Ohm's Law is a linear, proportional relationship, "
                "so doubling the current doubles the voltage across the same resistor.")
    if analysis.relationships:
        return " ".join(analysis.relationships)
    return "The equation's structure directly determines the visual shape: which terms dominate for large or small inputs shapes the curve you see."


def _template_what_if(analysis: EquationAnalysis) -> str:
    if analysis.parameter_effects:
        lines = [pe.explanation for pe in analysis.parameter_effects]
        return " ".join(lines)
    if analysis.relationships:
        return " ".join(analysis.relationships)
    return "Try changing a parameter with the sliders to see how the visualization responds."


def _template_parameter_effects(analysis: EquationAnalysis) -> str:
    if not analysis.parameter_effects:
        return "This equation's parameters map directly onto the shape and position of the visualization above."
    lines = [f"{pe.name or pe.symbol}: {pe.explanation}" for pe in analysis.parameter_effects]
    return "\n".join(lines)


def explain(analysis: EquationAnalysis, mode: str, parameters: Dict[str, float] | None = None) -> Dict[str, Any]:
    templates = {
        "what_it_does": _template_what_it_does,
        "why_looks_like_that": _template_why_looks_like_that,
        "what_if": _template_what_if,
        "parameter_effects": _template_parameter_effects,
    }
    template_fn = templates.get(mode, _template_what_it_does)
    fallback_text = template_fn(analysis)

    prompts = {
        "what_it_does": "Explain what this equation describes and what it does, in plain language.",
        "why_looks_like_that": "Explain WHY the visualization looks the way it does, connecting specific mathematical terms to specific visible features (shape, symmetry, direction, steepness, periodicity).",
        "what_if": "Explain, for each parameter, what happens to the visualization if that parameter increases, referencing the relationships given.",
        "parameter_effects": "For each parameter, give one crisp sentence describing its visual effect.",
    }
    user_prompt = _analysis_context(analysis) + "\n\nTask: " + prompts.get(mode, prompts["what_it_does"])
    if parameters:
        user_prompt += f"\n\nCurrent parameter values: {parameters}"

    ai_text = _call_openai(SYSTEM_PROMPT, user_prompt)
    if ai_text:
        return {"text": ai_text, "source": "ai"}
    return {"text": fallback_text, "source": "template"}
