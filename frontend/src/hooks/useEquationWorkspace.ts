import { useCallback, useEffect, useRef, useState } from "react";
import { api, ApiError } from "../api/client";
import type { EquationAnalysis, VisualizationResponse } from "../types/equation";

export function useEquationWorkspace(initialEquation?: string) {
  const [equation, setEquation] = useState<string>(initialEquation || "");
  const [analysis, setAnalysis] = useState<EquationAnalysis | null>(null);
  const [parameters, setParameters] = useState<Record<string, number>>({});
  const [visualizationId, setVisualizationId] = useState<string | null>(null);
  const [viz, setViz] = useState<VisualizationResponse | null>(null);
  const [lockedSymbol, setLockedSymbol] = useState<string | null>(null);
  const [analyzing, setAnalyzing] = useState(false);
  const [visualizing, setVisualizing] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const debounceRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  const loadEquation = useCallback(async (eqText: string) => {
    setError(null);
    setAnalyzing(true);
    setEquation(eqText);
    try {
      const a = await api.analyze(eqText);
      if (a.category === "unrecognized") {
        setError(a.warnings[0] || "This does not look like a valid equation.");
        setAnalysis(null);
        return;
      }
      setAnalysis(a);
      const defaults: Record<string, number> = {};
      for (const v of a.variables) if (v.default_value != null) defaults[v.symbol] = v.default_value;
      for (const c of a.constants) defaults[c.symbol] = c.value;
      setParameters(defaults);
      setLockedSymbol(null);
      const recommended = a.recommended_visualizations[0]?.id || "graph2d";
      setVisualizationId(recommended);
    } catch (e) {
      setError(e instanceof ApiError ? e.message : "Could not analyze this equation.");
      setAnalysis(null);
    } finally {
      setAnalyzing(false);
    }
  }, []);

  const fetchVisualization = useCallback(async () => {
    if (!equation || !analysis) return;
    setVisualizing(true);
    try {
      const v = await api.visualize({
        equation, visualization_id: visualizationId, parameters, locked_symbol: lockedSymbol,
      });
      setViz(v);
      setError(null);
    } catch (e) {
      setError(e instanceof ApiError ? e.message : "Could not generate a visualization.");
    } finally {
      setVisualizing(false);
    }
  }, [equation, analysis, visualizationId, parameters, lockedSymbol]);

  // Debounced re-visualization whenever parameters/visualizationId/lockedSymbol change
  useEffect(() => {
    if (!analysis) return;
    if (debounceRef.current) clearTimeout(debounceRef.current);
    debounceRef.current = setTimeout(() => { fetchVisualization(); }, 120);
    return () => { if (debounceRef.current) clearTimeout(debounceRef.current); };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [analysis, parameters, visualizationId, lockedSymbol]);

  const updateParameter = useCallback((symbol: string, value: number) => {
    setParameters((p) => ({ ...p, [symbol]: value }));
  }, []);

  const resetParameters = useCallback(() => {
    if (!analysis) return;
    const defaults: Record<string, number> = {};
    for (const v of analysis.variables) if (v.default_value != null) defaults[v.symbol] = v.default_value;
    for (const c of analysis.constants) defaults[c.symbol] = c.value;
    setParameters(defaults);
  }, [analysis]);

  return {
    equation, analysis, parameters, viz, visualizationId, lockedSymbol,
    analyzing, visualizing, error,
    loadEquation, updateParameter, resetParameters,
    setVisualizationId, setLockedSymbol,
  };
}
