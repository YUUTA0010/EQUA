import type { EquationAnalysis } from "../../types/equation";
import { InlineMath } from "react-katex";

const ROLE_STYLES: Record<string, string> = {
  dependent: "bg-accent-500/15 text-accent-400 border-accent-500/30",
  independent: "bg-signal-green/15 text-signal-green border-signal-green/30",
  parameter: "bg-signal-amber/15 text-signal-amber border-signal-amber/30",
  constant: "bg-slate-500/15 text-slate-400 border-slate-500/30",
};

const ROLE_LABEL: Record<string, string> = {
  dependent: "Calculated",
  independent: "Independent",
  parameter: "Parameter",
  constant: "Constant",
};

export default function VariableList({ analysis }: { analysis: EquationAnalysis }) {
  return (
    <div className="space-y-2">
      {analysis.variables.map((v) => (
        <div
          key={v.symbol}
          className="flex items-start gap-3 rounded-lg border border-base-600/50 bg-base-900/50 px-3 py-2.5"
        >
          <div className="w-9 h-9 shrink-0 rounded-md bg-base-700/70 flex items-center justify-center font-mono text-sm text-slate-100">
            <InlineMath math={v.symbol} />
          </div>
          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-2 flex-wrap">
              <span className="font-medium text-slate-100 text-sm">{v.name || v.symbol}</span>
              <span className={`text-[10px] px-1.5 py-0.5 rounded border ${ROLE_STYLES[v.role] || ROLE_STYLES.constant}`}>
                {ROLE_LABEL[v.role] || v.role}
              </span>
              {v.unit && v.unit !== "-" && (
                <span className="text-[11px] font-mono text-slate-500">[{v.unit}]</span>
              )}
            </div>
            {v.description && <p className="text-xs text-slate-500 mt-0.5">{v.description}</p>}
          </div>
        </div>
      ))}
      {analysis.constraints.length > 0 && (
        <div className="mt-3 rounded-lg border border-signal-amber/20 bg-signal-amber/5 px-3 py-2">
          <p className="text-[11px] font-semibold text-signal-amber uppercase tracking-wide mb-1">Constraints</p>
          <ul className="text-xs text-slate-400 space-y-0.5 list-disc list-inside">
            {analysis.constraints.map((c, i) => <li key={i}>{c}</li>)}
          </ul>
        </div>
      )}
    </div>
  );
}
