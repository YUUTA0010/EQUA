"""
Finds equation-like substrings in raw extracted text (spec section 12, OCR
pipeline steps 1-3) and produces a confidence score + a best-effort LaTeX
guess for each. This is a lightweight, dependency-free heuristic detector —
good enough for typed/printed textbook equations and short OCR snippets.
It deliberately never executes anything; validation is just "can SymPy
parse this after normalization" (see parser.py / analyzer.py), which also
sandboxes against malicious input.
"""
from __future__ import annotations

import re
import uuid
from dataclasses import dataclass
from typing import List, Optional

from equation_engine.parser import normalize_ascii_math, parse_equation, EquationParseError

MATH_OPERATOR_CHARS = set("=+-*/^()[]{}<>ω√π∫∑ΔθφζΩμαβλσγτχψΣ")
GREEK_OR_MATH_WORDS = re.compile(r"\b(sin|cos|tan|exp|log|ln|sqrt|lim|sum|int)\b", re.IGNORECASE)


def _looks_mathy(line: str) -> float:
    """Heuristic score in [0,1] for 'does this line look like an equation'."""
    stripped = line.strip()
    if not stripped or len(stripped) > 200:
        return 0.0
    if "=" not in stripped and not GREEK_OR_MATH_WORDS.search(stripped):
        return 0.0

    letters = sum(ch.isalpha() for ch in stripped)
    digits = sum(ch.isdigit() for ch in stripped)
    operators = sum(ch in MATH_OPERATOR_CHARS for ch in stripped)
    spaces = sum(ch.isspace() for ch in stripped)
    total = max(len(stripped), 1)

    # Prose sentences have lots of letters and very few operators.
    word_count = len(re.findall(r"[A-Za-z]{4,}", stripped))
    score = 0.0
    if "=" in stripped:
        score += 0.4
    score += min(operators / total * 4, 0.3)
    score += min(digits / total * 2, 0.1)
    if word_count <= 2:
        score += 0.15
    if GREEK_OR_MATH_WORDS.search(stripped):
        score += 0.15
    if word_count > 6:
        score -= 0.4  # looks like a sentence, not an equation
    return max(0.0, min(1.0, score))


def _ascii_to_latex_guess(text: str) -> str:
    """Best-effort visual LaTeX guess used only for display before the user
    confirms/edits — the authoritative LaTeX comes from SymPy after parsing."""
    t = normalize_ascii_math(text)
    t = re.sub(r"\*\*(\w+)", r"^{\1}", t)
    t = re.sub(r"\*\*\(([^)]+)\)", r"^{\1}", t)
    t = t.replace("*", " \\cdot ")
    t = re.sub(r"sqrt\(([^)]+)\)", r"\\sqrt{\1}", t)
    for greek in ["omega", "theta", "phi", "zeta", "pi", "mu", "alpha", "beta",
                  "gamma", "delta", "Delta", "sigma", "tau", "lambda_"]:
        t = re.sub(rf"\b{greek}\b", "\\\\" + greek.rstrip("_"), t)
    return t


@dataclass
class DetectedCandidate:
    id: str
    raw_text: str
    latex_guess: str
    confidence: float
    page: Optional[int] = None


def detect_equations(text: str, page: Optional[int] = None, ocr_confidence: Optional[float] = None) -> List[DetectedCandidate]:
    candidates: List[DetectedCandidate] = []
    seen = set()
    # Split on newlines first, then also try to split long lines on '=' clusters
    raw_lines = re.split(r"[\n\r]+", text)
    for line in raw_lines:
        line = line.strip()
        if not line:
            continue
        score = _looks_mathy(line)
        if score < 0.35:
            continue
        key = re.sub(r"\s+", "", line).lower()
        if key in seen:
            continue
        seen.add(key)

        confidence = score
        try:
            parse_equation(line)
            confidence = min(1.0, confidence + 0.25)
        except EquationParseError:
            confidence = max(0.2, confidence - 0.15)
        except Exception:  # noqa: BLE001
            confidence = max(0.15, confidence - 0.2)

        if ocr_confidence is not None:
            confidence = (confidence + ocr_confidence) / 2

        candidates.append(DetectedCandidate(
            id=str(uuid.uuid4())[:8],
            raw_text=line,
            latex_guess=_ascii_to_latex_guess(line),
            confidence=round(confidence, 2),
            page=page,
        ))
    candidates.sort(key=lambda c: -c.confidence)
    return candidates
