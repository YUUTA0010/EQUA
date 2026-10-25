"""
Pydantic schemas for EquationLens.

These mirror the structured-JSON contract described in the product spec
(section 13 — AI SYSTEM). Every field the AI layer fills in is also
independently derivable from the deterministic SymPy analysis, so the
system never depends on the AI for anything numeric.
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class VariableInfo(BaseModel):
    symbol: str
    name: str = ""
    role: str = Field(description="independent | dependent | parameter | constant")
    unit: Optional[str] = None
    description: Optional[str] = None
    default_value: Optional[float] = None
    min_value: Optional[float] = None
    max_value: Optional[float] = None
    step: Optional[float] = None


class ConstantInfo(BaseModel):
    symbol: str
    value: float
    unit: Optional[str] = None
    description: Optional[str] = None


class ParameterEffect(BaseModel):
    symbol: str
    name: str = ""
    effect: str  # e.g. "increases", "decreases", "non_monotonic", "no_effect"
    explanation: str
    visual_effect: Optional[str] = None


class VisualizationOption(BaseModel):
    id: str
    label: str
    reason: str
    is_recommended: bool = False


class EquationAnalysis(BaseModel):
    equation: str
    latex: str
    plain_text: str
    category: str
    category_label: str
    domain_area: str  # mathematics | physics | electrical | mechanical | control | signals
    physical_interpretation: str
    variables: List[VariableInfo] = Field(default_factory=list)
    constants: List[ConstantInfo] = Field(default_factory=list)
    independent_variables: List[str] = Field(default_factory=list)
    dependent_variables: List[str] = Field(default_factory=list)
    relationships: List[str] = Field(default_factory=list)
    constraints: List[str] = Field(default_factory=list)
    recommended_visualizations: List[VisualizationOption] = Field(default_factory=list)
    parameter_effects: List[ParameterEffect] = Field(default_factory=list)
    confidence: float = 1.0
    is_ambiguous: bool = False
    warnings: List[str] = Field(default_factory=list)


class AnalyzeRequest(BaseModel):
    equation: str
    latex_hint: Optional[str] = None
    engineering_mode: bool = False


class VisualizeRequest(BaseModel):
    equation: str
    category: Optional[str] = None
    visualization_id: Optional[str] = None
    parameters: Dict[str, float] = Field(default_factory=dict)
    x_min: Optional[float] = None
    x_max: Optional[float] = None
    locked_symbol: Optional[str] = None  # used by "Change One Thing" mode


class VisualizationResponse(BaseModel):
    visualization_id: str
    kind: str  # "graph2d" | "physics_force_block" | "circuit_ohm" | "projectile" | "unsupported"
    data: Dict[str, Any]
    caption: str = ""


class ExplainRequest(BaseModel):
    equation: str
    category: Optional[str] = None
    mode: str = "what_it_does"  # what_it_does | why_looks_like_that | what_if | parameter_effects
    parameters: Dict[str, float] = Field(default_factory=dict)


class ExplainResponse(BaseModel):
    text: str
    source: str  # "ai" | "template"


class CompareRequest(BaseModel):
    equation: str
    category: Optional[str] = None
    config_a: Dict[str, float]
    config_b: Dict[str, float]
    x_min: Optional[float] = None
    x_max: Optional[float] = None


class CompareResponse(BaseModel):
    kind: str
    data_a: Dict[str, Any]
    data_b: Dict[str, Any]
    differences: List[str]


class DetectedEquation(BaseModel):
    id: str
    raw_text: str
    latex_guess: str
    confidence: float
    page: Optional[int] = None


class DocumentAnalysisResponse(BaseModel):
    document_id: str
    filename: str
    extracted_text_preview: str
    equations: List[DetectedEquation]
    figure_count: int = 0
    subjects_detected: List[str] = Field(default_factory=list)


class SaveEquationRequest(BaseModel):
    equation: str
    category: Optional[str] = None
    parameters: Dict[str, float] = Field(default_factory=dict)
    note: Optional[str] = None
    project_id: Optional[str] = None


class ProjectCreateRequest(BaseModel):
    name: str
    description: Optional[str] = None
