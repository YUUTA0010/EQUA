"""
Security helpers.

Key principle (spec section 15): we NEVER execute arbitrary code extracted
from uploaded documents or typed by the user. All equation text goes through
`safe_parse_expr`, which:
  1. Rejects strings containing dangerous tokens outright.
  2. Parses with SymPy's tokenizer/transformer pipeline (not Python `eval`
     on a free-form namespace) restricted to an explicit whitelist of
     mathematical symbols/functions.
  3. Never imports or calls anything outside that whitelist.
"""
from __future__ import annotations

import re
import time
from collections import defaultdict, deque
from typing import Deque, Dict

import sympy
from sympy import symbols
from sympy.parsing.sympy_parser import (
    parse_expr,
    standard_transformations,
    implicit_multiplication_application,
    convert_xor,
)

# ---------------------------------------------------------------------------
# File upload validation
# ---------------------------------------------------------------------------
ALLOWED_EXTENSIONS = {".pdf", ".docx", ".png", ".jpg", ".jpeg", ".webp"}
ALLOWED_MIME_PREFIXES = ("image/", "application/pdf",
                          "application/vnd.openxmlformats-officedocument.wordprocessingml.document")
DEFAULT_MAX_UPLOAD_BYTES = 15 * 1024 * 1024  # 15MB default, overridden by env in main.py


class UploadValidationError(Exception):
    pass


def validate_upload(filename: str, content_type: str, size_bytes: int, max_bytes: int = DEFAULT_MAX_UPLOAD_BYTES) -> None:
    import os
    ext = os.path.splitext(filename or "")[1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise UploadValidationError(
            f"Unsupported file type '{ext or 'unknown'}'. Please upload PDF, DOCX, PNG, or JPG/JPEG."
        )
    if content_type and not any(content_type.startswith(p) for p in ALLOWED_MIME_PREFIXES):
        # Some browsers send generic octet-stream for docx; extension check above is primary guard.
        if content_type != "application/octet-stream":
            raise UploadValidationError(f"Unsupported content type '{content_type}'.")
    if size_bytes > max_bytes:
        mb = max_bytes / (1024 * 1024)
        raise UploadValidationError(f"File is too large. Maximum allowed size is {mb:.0f}MB.")
    if size_bytes <= 0:
        raise UploadValidationError("The uploaded file appears to be empty.")


# ---------------------------------------------------------------------------
# Safe symbolic expression parsing
# ---------------------------------------------------------------------------

DANGEROUS_TOKENS = [
    "__", "import", "exec", "eval(", "lambda", "open(", "os.", "sys.",
    "subprocess", "compile(", "globals(", "locals(", "input(", "getattr",
    "setattr", "delattr", "vars(", "\\x", "0x",
]

ALLOWED_FUNCTION_NAMES = {
    "sin", "cos", "tan", "cot", "sec", "csc",
    "asin", "acos", "atan", "atan2",
    "sinh", "cosh", "tanh",
    "exp", "log", "ln", "sqrt", "Abs", "abs",
    "Derivative", "diff", "Integral", "integrate",
    "Sum", "Product", "Matrix", "re", "im", "conjugate",
    "Max", "Min", "floor", "ceiling", "sign",
    "pi", "E", "I", "oo",
}

# Subset of the above that are strictly *callable functions* (always followed
# by parentheses in valid usage). Constants like pi/E/I/oo are excluded here
# because in physics/engineering equations those single letters overwhelmingly
# mean something else (I = current, E = energy or field strength) — so when
# building a per-equation local symbol table we only need to protect real
# function names from being shadowed, not these overloaded constant letters.
CALLABLE_FUNCTION_NAMES = {
    "sin", "cos", "tan", "cot", "sec", "csc",
    "asin", "acos", "atan", "atan2",
    "sinh", "cosh", "tanh",
    "exp", "log", "ln", "sqrt", "Abs", "abs",
    "Derivative", "diff", "Integral", "integrate",
    "Sum", "Product", "Matrix", "re", "im", "conjugate",
    "Max", "Min", "floor", "ceiling", "sign",
}

TRANSFORMATIONS = standard_transformations + (implicit_multiplication_application, convert_xor)



# SymPy's parser transformation pipeline (auto_number, auto_symbol, etc.)
# generates code that calls these core constructors directly — they must be
# present in the global namespace or parsing fails, even for simple
# expressions like "x**2". These are pure data constructors (no I/O, no
# filesystem, no process access), so they're safe to expose.
CORE_CONSTRUCTOR_NAMES = {"Integer", "Float", "Rational", "Symbol"}


def _build_safe_global_dict() -> dict:
    """Whitelist-only global dict passed to SymPy's parser — no builtins, no I/O."""
    g: Dict[str, object] = {}
    for name in ALLOWED_FUNCTION_NAMES | CORE_CONSTRUCTOR_NAMES:
        if hasattr(sympy, name):
            g[name] = getattr(sympy, name)
    g["ln"] = sympy.log
    return g


_SAFE_GLOBALS = _build_safe_global_dict()


class UnsafeExpressionError(Exception):
    pass


def assert_safe_text(text: str) -> None:
    lowered = text.lower()
    for tok in DANGEROUS_TOKENS:
        if tok in lowered:
            raise UnsafeExpressionError(
                "The input contains characters that are not allowed in a mathematical expression."
            )
    if len(text) > 2000:
        raise UnsafeExpressionError("Expression is too long to process.")


def safe_parse_expr(text: str, local_symbols: dict | None = None) -> sympy.Expr:
    """Parse a string into a SymPy expression using only whitelisted names.

    Never uses Python's built-in eval/exec with an unrestricted namespace.
    """
    assert_safe_text(text)
    local_dict = dict(local_symbols or {})
    try:
        expr = parse_expr(
            text,
            transformations=TRANSFORMATIONS,
            global_dict=_SAFE_GLOBALS,
            local_dict=local_dict,
            evaluate=True,
        )
    except Exception as e:  # noqa: BLE001
        raise UnsafeExpressionError(f"Could not parse expression: {e}") from e
    return expr


# ---------------------------------------------------------------------------
# Simple in-memory rate limiter (per-process; fine for local/demo deployment)
# ---------------------------------------------------------------------------
class RateLimiter:
    def __init__(self, per_minute: int = 120):
        self.per_minute = per_minute
        self._hits: Dict[str, Deque[float]] = defaultdict(deque)

    def allow(self, key: str) -> bool:
        now = time.time()
        window_start = now - 60
        dq = self._hits[key]
        while dq and dq[0] < window_start:
            dq.popleft()
        if len(dq) >= self.per_minute:
            return False
        dq.append(now)
        return True
