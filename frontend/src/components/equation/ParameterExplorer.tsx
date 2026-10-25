import type { EquationAnalysis } from "../../types/equation";
import { InlineMath } from "react-katex";

interface ParameterExplorerProps {
  analysis: EquationAnalysis;
  values: Record<string, number>;
  onChange: (symbol: string, value: number) => void;
  dependentValue?: number | null;
  lockedSymbol?: string | null;
}

export default function ParameterExplorer({
  analysis, values, onChange, dependentValue, lockedSymbol,
}: ParameterExplorerProps) {
  const sliderVars = analysis.variables.filter((v) => v.role === "parameter" && v.min_value != null && v.max_value != null);
  const dependentVar = analysis.variables.find((v) => v.role === "dependent");
  const constants = analysis.variables.filter((v) => v.role === "constant");

  return (
    <div className="space-y-4">
      {sliderVars.map((v) => {
        const val = values[v.symbol] ?? v.default_value ?? 0;
        const min = v.min_value ?? 0;
        const max = v.max_value ?? 10;
        const step = v.step ?? 0.1;
        const fill = ((val - min) / (max - min || 1)) * 100;
        const isLocked = !!lockedSymbol && lockedSymbol !== v.symbol;
        return (
          <div key={v.symbol} className={`transition-opacity ${isLocked ? "opacity-35 pointer-events-none" : ""}`}>
            <div className="flex items-center justify-between mb-1.5">
              <label className="flex items-center gap-1.5 text-sm text-slate-300">
                <span className="font-mono text-accent-400"><InlineMath math={v.symbol} /></span>
                <span className="text-slate-400">{v.name}</span>
                {v.unit && v.unit !== "-" && <span className="text-xs text-slate-500">({v.unit})</span>}
              </label>
              <span className="font-mono text-sm text-slate-200 tabular-nums">{val.toFixed(2)}</span>
            </div>
            <input
              type="range" min={min} max={max} step={step} value={val}
              style={{ ["--fill" as any]: `${fill}%` }}
              onChange={(e) => onChange(v.symbol, Number(e.target.value))}
              className="w-full"
            />
          </div>
        );
      })}

      {dependentVar && (
        <div className="rounded-lg border border-accent-500/30 bg-accent-500/10 px-3 py-2.5 flex items-center justify-between">
          <span className="flex items-center gap-1.5 text-sm text-accent-300">
            <span className="font-mono"><InlineMath math={dependentVar.symbol} /></span>
            <span>{dependentVar.name}</span>
            <span className="text-[10px] uppercase tracking-wide bg-accent-500/20 px-1.5 py-0.5 rounded">auto-calculated</span>
          </span>
          <span className="font-mono text-sm text-accent-200 tabular-nums">
            {dependentValue != null ? dependentValue.toFixed(3) : "—"} {dependentVar.unit && dependentVar.unit !== "-" ? dependentVar.unit : ""}
          </span>
        </div>
      )}

      {constants.length > 0 && (
        <div className="space-y-1.5 pt-1">
          {constants.map((c) => (
            <div key={c.symbol} className="flex items-center justify-between text-xs text-slate-500 px-1">
              <span className="font-mono"><InlineMath math={c.symbol} /> — {c.name} <span className="italic">(fixed)</span></span>
              <span className="font-mono">{c.default_value?.toExponential(3)}</span>
            </div>
          ))}
        </div>
      )}

      {sliderVars.length === 0 && !dependentVar && (
        <p className="text-sm text-slate-500 italic">This equation has no adjustable parameters to explore.</p>
      )}
    </div>
  );
}
