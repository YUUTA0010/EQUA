"""
Extracts raw text from uploaded documents.

  * PDF  -> PyMuPDF (fitz) text layer; falls back to per-page OCR via
            PyMuPDF's rendering + pytesseract if the page has no text layer
            (i.e. it's a scan).
  * DOCX -> python-docx paragraphs + tables.
  * PNG/JPG -> pytesseract OCR directly.

If pytesseract/tesseract isn't installed on the host, image OCR degrades
gracefully with a clear error message rather than crashing the request
(see main.py demo-mode fallback).
"""
from __future__ import annotations

import io
import os
from dataclasses import dataclass
from typing import List, Optional

from PIL import Image

try:
    import pytesseract
    _TESSERACT_AVAILABLE = True
except Exception:  # noqa: BLE001
    _TESSERACT_AVAILABLE = False

try:
    import pymupdf as fitz
    _PYMUPDF_AVAILABLE = True
except Exception:  # noqa: BLE001
    try:
        import fitz
        _PYMUPDF_AVAILABLE = True
    except Exception:  # noqa: BLE001
        _PYMUPDF_AVAILABLE = False

try:
    import docx as _docx
    _DOCX_AVAILABLE = True
except Exception:  # noqa: BLE001
    _DOCX_AVAILABLE = False


@dataclass
class PageText:
    page: int
    text: str
    ocr_used: bool = False
    ocr_confidence: Optional[float] = None


class ExtractionError(Exception):
    pass


def extract_image(path: str) -> List[PageText]:
    if not _TESSERACT_AVAILABLE:
        raise ExtractionError(
            "OCR engine (tesseract) is not available on this server. "
            "Install tesseract-ocr, or paste the equation text directly."
        )
    img = Image.open(path).convert("RGB")
    data = pytesseract.image_to_data(img, config="--psm 6", output_type=pytesseract.Output.DICT)
    words = [w for w in data.get("text", []) if w.strip()]
    confs = [float(c) for c in data.get("conf", []) if str(c) not in ("-1", "")]
    text = " ".join(words)
    avg_conf = (sum(confs) / len(confs) / 100.0) if confs else 0.5
    return [PageText(page=1, text=text, ocr_used=True, ocr_confidence=avg_conf)]


def extract_pdf(path: str) -> List[PageText]:
    if not _PYMUPDF_AVAILABLE:
        raise ExtractionError("PDF engine (PyMuPDF) is not available on this server.")
    pages: List[PageText] = []
    doc = fitz.open(path)
    try:
        for i, page in enumerate(doc):
            text = page.get_text("text") or ""
            if text.strip():
                pages.append(PageText(page=i + 1, text=text, ocr_used=False))
            elif _TESSERACT_AVAILABLE:
                pix = page.get_pixmap(dpi=200)
                img = Image.open(io.BytesIO(pix.tobytes("png")))
                data = pytesseract.image_to_data(img, output_type=pytesseract.Output.DICT)
                words = [w for w in data.get("text", []) if w.strip()]
                confs = [float(c) for c in data.get("conf", []) if str(c) not in ("-1", "")]
                avg_conf = (sum(confs) / len(confs) / 100.0) if confs else 0.4
                pages.append(PageText(page=i + 1, text=" ".join(words), ocr_used=True, ocr_confidence=avg_conf))
            else:
                pages.append(PageText(page=i + 1, text="", ocr_used=False))
    finally:
        doc.close()
    return pages


def extract_docx(path: str) -> List[PageText]:
    if not _DOCX_AVAILABLE:
        raise ExtractionError("DOCX engine (python-docx) is not available on this server.")
    document = _docx.Document(path)
    parts: List[str] = [p.text for p in document.paragraphs if p.text.strip()]
    for table in document.tables:
        for row in table.rows:
            for cell in row.cells:
                if cell.text.strip():
                    parts.append(cell.text)
    return [PageText(page=1, text="\n".join(parts), ocr_used=False)]


def extract_document(path: str, filename: str) -> List[PageText]:
    ext = os.path.splitext(filename)[1].lower()
    if ext == ".pdf":
        return extract_pdf(path)
    if ext == ".docx":
        return extract_docx(path)
    if ext in (".png", ".jpg", ".jpeg", ".webp"):
        return extract_image(path)
    raise ExtractionError(f"Unsupported file extension: {ext}")
