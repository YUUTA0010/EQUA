export interface VariableInfo {
  symbol: string;
  name: string;
  role: "independent" | "dependent" | "parameter" | "constant";
  unit?: string | null;
  description?: string | null;
  default_value?: number | null;
  min_value?: number | null;
  max_value?: number | null;
  step?: number | null;
}

export interface ConstantInfo {
  symbol: string;
  value: number;
  unit?: string | null;
  description?: string | null;
}

export interface ParameterEffect {
  symbol: string;
  name: string;
  effect: string;
  explanation: string;
  visual_effect?: string | null;
}

export interface VisualizationOption {
  id: string;
  label: string;
  reason: string;
  is_recommended: boolean;
}

export interface EquationAnalysis {
  equation: string;
  latex: string;
  plain_text: string;
  category: string;
  category_label: string;
  domain_area: string;
  physical_interpretation: string;
  variables: VariableInfo[];
  constants: ConstantInfo[];
  independent_variables: string[];
  dependent_variables: string[];
  relationships: string[];
  constraints: string[];
  recommended_visualizations: VisualizationOption[];
  parameter_effects: ParameterEffect[];
  confidence: number;
  is_ambiguous: boolean;
  warnings: string[];
}

export interface VisualizationResponse {
  visualization_id: string;
  kind: string;
  data: any;
  caption: string;
}

export interface ExplainResponse {
  text: string;
  source: "ai" | "template";
}

export interface DetectedEquation {
  id: string;
  raw_text: string;
  latex_guess: string;
  confidence: number;
  page?: number | null;
}

export interface DocumentAnalysisResponse {
  document_id: string;
  filename: string;
  extracted_text_preview: string;
  equations: DetectedEquation[];
  figure_count: number;
  subjects_detected: string[];
}

export interface CompareResponse {
  kind: string;
  data_a: any;
  data_b: any;
  differences: string[];
}

export interface DemoEquation {
  equation: string;
  label: string;
  domain_area: string;
}
