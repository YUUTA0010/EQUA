import { useState } from "react";
import type { EquationAnalysis } from "../../types/equation";
import { Target, X } from "lucide-react";
import { InlineMath } from "react-katex";

interface ChangeOneThingProps {
  analysis: EquationAnalysis;
  lockedSymbol: string | null;
  onSelect: (symbol: string | null) => void;
}

export default function ChangeOneThing({ analysis, lockedSymbol, onSelect }: ChangeOneThingProps) {
  const [open, setOpen] = useState(false);
  const params = analysis.variables.filter((v) => v.role === "parameter");

  if (params.length < 2) return null;

  const active = lockedSymbol != null;

  return (
    <div className="rounded-xl border border-base-600/60 bg-base-900/60 p-3">
      <button
        onClick={() => {
          if (active) { onSelect(null); setOpen(false); }
          else setOpen((o) => !o);
        }}
        className={`w-full flex items-center justify-center gap-2 rounded-lg py-2.5 px-4 font-semibold text-sm transition-colors ${
          active ? "bg-signal-green/15 text-signal-green border border-signal-green/40"
                 : "bg-base-700/60 hover:bg-base-700 text-slate-300 border border-base-600/60"
        }`}
      >
        {active ? <X size={15} /> : <Target size={15} />}
        {active ? `Exploring "${analysis.variables.find(v => v.symbol === lockedSymbol)?.name}" — click to exit` : "CHANGE ONE THING"}
      </button>

      {open && !active && (
        <div className="mt-2 grid grid-cols-2 gap-2 animate-fade-in">
          {params.map((p) => (
            <button
              key={p.symbol}
              onClick={() => { onSelect(p.symbol); setOpen(false); }}
              className="text-left rounded-lg border border-base-600/50 bg-base-800/60 hover:border-accent-500/50 hover:bg-accent-500/10 px-3 py-2 transition-colors"
            >
              <span className="text-xs text-slate-500">Explore</span>
              <p className="text-sm font-medium text-slate-200 flex items-center gap-1">
                <InlineMath math={p.symbol} /> — {p.name}
              </p>
            </button>
          ))}
        </div>
      )}
      {active && (
        <p className="text-xs text-slate-500 mt-2 text-center">
          Every other parameter is frozen at its default. Move only this slider to see its effect in isolation.
        </p>
      )}
    </div>
  );
}
