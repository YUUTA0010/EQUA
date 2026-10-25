from __future__ import annotations

from typing import List

from fastapi import APIRouter, HTTPException

from models.schemas import (
    AnalyzeRequest, EquationAnalysis, VisualizeRequest, VisualizationResponse,
    ExplainRequest, ExplainResponse, CompareRequest, CompareResponse,
    SaveEquationRequest,
)
from equation_engine.analyzer import analyze_equation
from equation_engine.classifier import list_known_categories
from equation_engine.library import LIBRARY
from visualization_engine.selector import build_visualization, VisualizationError
from visualization_engine import compute as C
from ai.explain_service import explain as ai_explain
from storage import store
from document_processor.equation_detect import detect_equations, DetectedCandidate

router = APIRouter(prefix="/api/equations", tags=["equations"])


@router.post("/detect")
def detect(payload: dict):
    text = payload.get("text", "")
    if not text or not text.strip():
        raise HTTPException(400, "Please provide some text or an equation to detect.")
    candidates = detect_equations(text)
    return {"equations": [c.__dict__ for c in candidates]}


@router.post("/analyze", response_model=EquationAnalysis)
def analyze(req: AnalyzeRequest):
    if not req.equation or not req.equation.strip():
        raise HTTPException(400, "Please provide an equation to analyze.")
    analysis = analyze_equation(req.equation, engineering_mode=req.engineering_mode)
    return analysis


@router.post("/visualize", response_model=VisualizationResponse)
def visualize(req: VisualizeRequest):
    try:
        result = build_visualization(
            req.equation, req.visualization_id, req.parameters, req.x_min, req.x_max, req.locked_symbol,
        )
    except VisualizationError as e:
        raise HTTPException(422, str(e)) from e
    except Exception as e:  # noqa: BLE001
        raise HTTPException(500, "Could not generate a visualization for this equation. "
                                  "Its notation may be ambiguous — try editing it.") from e
    return VisualizationResponse(visualization_id=result["visualization_id"], kind=result["kind"],
                                  data=result["data"], caption=result["caption"])


@router.post("/explain", response_model=ExplainResponse)
def explain_endpoint(req: ExplainRequest):
    analysis = analyze_equation(req.equation)
    if analysis.category == "unrecognized":
        raise HTTPException(422, "This equation could not be understood well enough to explain yet.")
    result = ai_explain(analysis, req.mode, req.parameters)
    return ExplainResponse(**result)


@router.post("/compare", response_model=CompareResponse)
def compare(req: CompareRequest):
    analysis = analyze_equation(req.equation)
    if analysis.category == "unrecognized":
        raise HTTPException(422, "This equation could not be understood well enough to compare.")
    indep = analysis.independent_variables[0] if analysis.independent_variables else None
    dep = analysis.dependent_variables[0] if analysis.dependent_variables else "y"
    if indep is None:
        raise HTTPException(422, "Comparison currently supports single-independent-variable graphs.")

    defaults = {v.symbol: v.default_value for v in analysis.variables if v.default_value is not None}
    params_a = {**defaults, **req.config_a}
    params_b = {**defaults, **req.config_b}
    params_a.pop(indep, None)
    params_b.pop(indep, None)

    data_a = C.compute_graph2d(req.equation, params_a, indep, dep, req.x_min, req.x_max)
    data_b = C.compute_graph2d(req.equation, params_b, indep, dep, req.x_min, req.x_max)

    differences = []
    for key in set(list(req.config_a.keys()) + list(req.config_b.keys())):
        va, vb = req.config_a.get(key), req.config_b.get(key)
        if va is not None and vb is not None and va != vb:
            var_meta = next((v for v in analysis.variables if v.symbol == key), None)
            name = var_meta.name if var_meta else key
            differences.append(f"{name} ({key}): {va} → {vb}")

    return CompareResponse(kind="graph2d", data_a=data_a, data_b=data_b, differences=differences)


@router.get("/library")
def get_library():
    demo_equations = [
        {"equation": "F = m*a", "label": "Newton's Second Law", "domain_area": "physics"},
        {"equation": "V = I*R", "label": "Ohm's Law", "domain_area": "electrical"},
        {"equation": "y = x**2", "label": "Quadratic Function", "domain_area": "mathematics"},
        {"equation": "y = A*sin(omega*t + phi)", "label": "Sinusoidal Wave", "domain_area": "signals"},
        {"equation": "E = m*c**2", "label": "Mass–Energy Equivalence", "domain_area": "physics"},
        {"equation": "y = A*exp(-zeta*wn*t)*sin(wd*t)", "label": "Damped Oscillation", "domain_area": "mechanical"},
        {"equation": "v = u + a*t", "label": "Kinematics — Velocity", "domain_area": "mechanical"},
        {"equation": "s = u*t + 0.5*a*t**2", "label": "Kinematics — Position", "domain_area": "mechanical"},
        {"equation": "V = 5*(1 - exp(-t/(R*C)))", "label": "RC Charging Circuit", "domain_area": "electrical"},
        {"equation": "dy/dx = k*y", "label": "Exponential Growth/Decay ODE", "domain_area": "engineering_mathematics"},
        {"equation": "z = x**2 - y**2", "label": "Saddle Surface", "domain_area": "mathematics"},
        {"equation": "y = m*x + c", "label": "Linear Equation", "domain_area": "mathematics"},
    ]
    return {"demo_equations": demo_equations, "categories": list_known_categories()}


@router.post("/save")
def save(req: SaveEquationRequest):
    record = store.save_equation(req.model_dump())
    return record


@router.get("/saved")
def saved(project_id: str | None = None):
    return {"items": store.list_saved_equations(project_id)}


@router.delete("/saved/{equation_id}")
def delete_saved(equation_id: str):
    ok = store.delete_equation(equation_id)
    if not ok:
        raise HTTPException(404, "Saved equation not found.")
    return {"deleted": True}
