from __future__ import annotations

import os
import tempfile
import uuid
from typing import Dict

from fastapi import APIRouter, UploadFile, File, HTTPException

from models.schemas import DocumentAnalysisResponse, DetectedEquation
from utils.security import validate_upload, UploadValidationError
from document_processor.extract import extract_document, ExtractionError
from document_processor.equation_detect import detect_equations

router = APIRouter(prefix="/api", tags=["documents"])

_MAX_UPLOAD_BYTES = int(float(os.environ.get("MAX_UPLOAD_MB", "15")) * 1024 * 1024)

# Small in-memory cache so the frontend can re-fetch a just-uploaded
# document's analysis without re-uploading. Not persisted across restarts —
# uploaded files themselves are deleted immediately after processing
# (spec section 15: "temporary file cleanup").
_DOCUMENT_CACHE: Dict[str, DocumentAnalysisResponse] = {}
_MAX_CACHE_ITEMS = 50


def _remember(doc_id: str, analysis: DocumentAnalysisResponse) -> None:
    if len(_DOCUMENT_CACHE) >= _MAX_CACHE_ITEMS:
        _DOCUMENT_CACHE.pop(next(iter(_DOCUMENT_CACHE)))
    _DOCUMENT_CACHE[doc_id] = analysis


SUBJECT_KEYWORDS = {
    "mechanics": ["force", "mass", "acceleration", "newton", "momentum", "velocity"],
    "electricity": ["voltage", "current", "resistance", "ohm", "circuit", "capacitor"],
    "waves & oscillation": ["amplitude", "frequency", "phase", "wave", "oscillat", "sin", "cos"],
    "thermodynamics": ["temperature", "heat", "entropy", "thermal"],
    "calculus": ["derivative", "integral", "d/dx", "dy/dx"],
}


def _detect_subjects(full_text: str) -> list[str]:
    lower = full_text.lower()
    found = []
    for subject, kws in SUBJECT_KEYWORDS.items():
        if any(kw in lower for kw in kws):
            found.append(subject)
    return found


@router.post("/upload", response_model=DocumentAnalysisResponse)
async def upload(file: UploadFile = File(...)):
    contents = await file.read()
    try:
        validate_upload(file.filename or "", file.content_type or "", len(contents), _MAX_UPLOAD_BYTES)
    except UploadValidationError as e:
        raise HTTPException(400, str(e)) from e

    suffix = os.path.splitext(file.filename or "")[1].lower()
    tmp_path = None
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
            tmp.write(contents)
            tmp_path = tmp.name

        try:
            pages = extract_document(tmp_path, file.filename or "upload")
        except ExtractionError as e:
            raise HTTPException(422, str(e)) from e
    finally:
        # Always clean up the temp file, even if extraction failed.
        if tmp_path and os.path.exists(tmp_path):
            os.remove(tmp_path)

    full_text = "\n".join(p.text for p in pages)
    if not full_text.strip():
        raise HTTPException(422, "No readable text or equations were found in this document. "
                                  "If it's a scanned image, try a clearer photo or higher-resolution scan.")

    all_candidates = []
    for p in pages:
        cands = detect_equations(p.text, page=p.page, ocr_confidence=p.ocr_confidence)
        all_candidates.extend(cands)

    doc_id = str(uuid.uuid4())[:12]
    response = DocumentAnalysisResponse(
        document_id=doc_id,
        filename=file.filename or "document",
        extracted_text_preview=full_text[:1200],
        equations=[DetectedEquation(id=c.id, raw_text=c.raw_text, latex_guess=c.latex_guess,
                                     confidence=c.confidence, page=c.page) for c in all_candidates],
        figure_count=0,
        subjects_detected=_detect_subjects(full_text),
    )
    _remember(doc_id, response)
    return response


@router.get("/documents/{document_id}", response_model=DocumentAnalysisResponse)
def get_document(document_id: str):
    cached = _DOCUMENT_CACHE.get(document_id)
    if not cached:
        raise HTTPException(404, "This document is no longer available. Please upload it again.")
    return cached


@router.post("/documents/analyze", response_model=DocumentAnalysisResponse)
def analyze_pasted_text(payload: dict):
    text = payload.get("text", "")
    if not text.strip():
        raise HTTPException(400, "Please provide document text to analyze.")
    candidates = detect_equations(text)
    doc_id = str(uuid.uuid4())[:12]
    response = DocumentAnalysisResponse(
        document_id=doc_id,
        filename="pasted-text",
        extracted_text_preview=text[:1200],
        equations=[DetectedEquation(id=c.id, raw_text=c.raw_text, latex_guess=c.latex_guess,
                                     confidence=c.confidence) for c in candidates],
        subjects_detected=_detect_subjects(text),
    )
    _remember(doc_id, response)
    return response
