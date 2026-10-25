import { useState } from "react";
import type { EquationAnalysis } from "../../types/equation";
import { api } from "../../api/client";
import Graph2D from "../visualizations/Graph2D";
import { GitCompare, Loader2, X } from "lucide-react";

interface CompareViewProps {
  analysis: EquationAnalysis;
  currentParameters: Record<string, number>;
}

export default function CompareView({ analysis, currentParameters }: CompareViewProps) {
  const [open, setOpen] = useState(false);
  const sliderVars = analysis.variables.filter((v) => v.role === "parameter" && v.min_value != null);
  const [configA, setConfigA] = useState<Record<string, number>>(currentParameters);
  const [configB, setConfigB] = useState<Record<string, number>>(() => {
    const b = { ...currentParameters };
    // Nudge config B so the two start visibly different.
    const first = sliderVars[0];
    if (first) {
      const mid = ((first.min_value ?? 0) + (first.max_value ?? 10)) / 2;
      b[first.symbol] = mid;
    }
    return b;
  });
  const [result, setResult] = useState<{ dataA: any; dataB: any; diffs: string[] } | null>(null);
  const [loading, setLoading] = useState(false);

  const indep = analysis.independent_variables[0] || sliderVars[0]?.symbol;

  const runCompare = async () => {
    setLoading(true);
    try {
      const res = await api.compare({ equation: analysis.equation, config_a: configA, config_b: configB });
      setResult({ dataA: res.data_a, dataB: res.data_b, diffs: res.differences });
    } catch (e) {
      // surfaced via lack of result
    } finally {
      setLoading(false);
    }
  };

  if (!open) {
    return (
      <button
        onClick={() => setOpen(true)}
        className="inline-flex items-center gap-2 rounded-lg bg-base-700/60 hover:bg-base-700 text-slate-300 px-4 py-2 text-sm font-medium transition-colors"
      >
        <GitCompare size={15} /> COMPARE
      </button>
    );
  }

  return (
    <div className="rounded-xl border border-base-600/60 bg-base-900/70 p-4 animate-fade-in space-y-4">
      <div className="flex items-center justify-between">
        <p className="text-sm font-semibold text-slate-200 flex items-center gap-1.5"><GitCompare size={15} /> Before / After Comparison</p>
        <button onClick={() => setOpen(false)} className="text-slate-500 hover:text-slate-300"><X size={16} /></button>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <ConfigEditor label="Configuration A" vars={sliderVars} values={configA} onChange={setConfigA} color="text-accent-400" />
        <ConfigEditor label="Configuration B" vars={sliderVars} values={configB} onChange={setConfigB} color="text-signal-amber" />
      </div>

      <button
        onClick={runCompare}
        disabled={loading}
        className="w-full rounded-lg bg-accent-600/20 hover:bg-accent-600/30 text-accent-400 font-medium py-2 text-sm transition-colors flex items-center justify-center gap-2"
      >
        {loading && <Loader2 size={14} className="animate-spin" />}
        Compare
      </button>

      {result && (
        <div className="space-y-3">
          <Graph2D
            x={result.dataA.x} y={result.dataA.y}
            xLabel={indep || "x"} yLabel={analysis.dependent_variables[0] || "y"}
            height={320}
            extraTraces={[{ x: result.dataB.x, y: result.dataB.y, name: "Configuration B", color: "#f5a623" }]}
          />
          {result.diffs.length > 0 && (
            <div className="rounded-lg border border-base-600/50 bg-base-800/50 p-3">
              <p className="text-xs font-semibold text-slate-400 uppercase tracking-wide mb-1.5">What changed</p>
              <ul className="text-sm text-slate-300 space-y-1">
                {result.diffs.map((d, i) => <li key={i}>• {d}</li>)}
              </ul>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

function ConfigEditor({ label, vars, values, onChange, color }: {
  label: string; vars: any[]; values: Record<string, number>;
  onChange: (v: Record<string, number>) => void; color: string;
}) {
  return (
    <div className="rounded-lg border border-base-600/50 bg-base-800/40 p-3 space-y-2.5">
      <p className={`text-xs font-semibold uppercase tracking-wide ${color}`}>{label}</p>
      {vars.map((v) => (
        <div key={v.symbol}>
          <div className="flex justify-between text-xs text-slate-400 mb-1">
            <span>{v.symbol} — {v.name}</span>
            <span className="font-mono">{(values[v.symbol] ?? v.default_value ?? 0).toFixed(2)}</span>
          </div>
          <input
            type="range" min={v.min_value} max={v.max_value} step={v.step || 0.1}
            value={values[v.symbol] ?? v.default_value ?? 0}
            onChange={(e) => onChange({ ...values, [v.symbol]: Number(e.target.value) })}
            className="w-full"
          />
        </div>
      ))}
    </div>
  );
}
