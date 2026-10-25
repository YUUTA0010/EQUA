import { useState } from "react";
import type { EquationAnalysis } from "../../types/equation";
import { api } from "../../api/client";
import { Loader2, Sparkles } from "lucide-react";

const EFFECT_ICON: Record<string, string> = {
  increases: "↑", decreases: "↓", non_monotonic: "↕", no_effect: "→",
  scales_amplitude: "↕", compresses_period: "⇄", shifts_phase: "⇄",
  faster_decay: "↓", faster_oscillation: "↑", increases_slope: "↗",
  shifts_up: "↑", increases_curvature: "⌢", slower_charging: "↓",
};

export default function WhatIfPanel({
  analysis, parameters,
}: { analysis: EquationAnalysis; parameters: Record<string, number> }) {
  const [expanded, setExpanded] = useState(false);
  const [aiText, setAiText] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  const fetchDeeper = async () => {
    setLoading(true);
    try {
      const res = await api.explain(analysis.equation, "what_if", parameters);
      setAiText(res.text);
      setExpanded(true);
    } catch {
      setAiText("Could not generate a deeper explanation right now.");
      setExpanded(true);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-3">
      {analysis.parameter_effects.length === 0 && analysis.relationships.length === 0 && (
        <p className="text-sm text-slate-500 italic">No sensitivity relationships were derived for this equation.</p>
      )}

      {analysis.parameter_effects.map((pe) => (
        <div key={pe.symbol} className="flex gap-3 rounded-lg border border-base-600/50 bg-base-900/50 px-3 py-2.5">
          <span className="text-xl text-accent-400 font-mono w-6 text-center shrink-0">
            {EFFECT_ICON[pe.effect] || "•"}
          </span>
          <p className="text-sm text-slate-300 leading-relaxed">{pe.explanation}</p>
        </div>
      ))}

      {analysis.parameter_effects.length === 0 && analysis.relationships.map((r, i) => (
        <div key={i} className="flex gap-3 rounded-lg border border-base-600/50 bg-base-900/50 px-3 py-2.5">
          <span className="text-xl text-accent-400 font-mono w-6 text-center shrink-0">•</span>
          <p className="text-sm text-slate-300 leading-relaxed">{r}</p>
        </div>
      ))}

      <button
        onClick={fetchDeeper}
        disabled={loading}
        className="inline-flex items-center gap-1.5 text-xs font-medium text-accent-400 hover:text-accent-300 transition-colors"
      >
        {loading ? <Loader2 size={13} className="animate-spin" /> : <Sparkles size={13} />}
        Explain this in more depth
      </button>

      {expanded && aiText && (
        <div className="rounded-lg border border-accent-500/20 bg-accent-500/5 px-3 py-2.5 text-sm text-slate-300 leading-relaxed animate-fade-in">
          {aiText}
        </div>
      )}
    </div>
  );
}
