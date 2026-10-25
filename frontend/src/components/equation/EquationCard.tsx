import { InlineMath } from "react-katex";
import { Eye, BookOpen, Bookmark, AlertTriangle } from "lucide-react";

interface EquationCardProps {
  index?: number;
  equationText: string;
  label?: string;
  confidence?: number;
  onVisualize: () => void;
  onSave?: () => void;
}

function ErrSafeInlineMath({ math }: { math: string }) {
  try {
    return <InlineMath math={math} />;
  } catch {
    return <span>{math}</span>;
  }
}

export default function EquationCard({ index, equationText, label, confidence, onVisualize, onSave }: EquationCardProps) {
  const lowConfidence = confidence != null && confidence < 0.6;
  return (
    <div className="rounded-xl border border-base-600/60 bg-base-900/60 hover:border-accent-500/40 transition-colors p-4">
      <div className="flex items-start justify-between gap-2">
        <div className="min-w-0">
          {index != null && <p className="text-[11px] text-slate-500 mb-0.5">Equation {String(index).padStart(2, "0")}</p>}
          {label && <p className="text-xs text-accent-400 mb-1">{label}</p>}
          <div className="text-lg text-slate-100 font-mono overflow-x-auto">
            <ErrSafeInlineMath math={equationText.replace(/\*\*/g, "^").replace(/\*/g, "\\cdot ")} />
          </div>
        </div>
        {confidence != null && (
          <span className={`shrink-0 text-[10px] px-1.5 py-0.5 rounded-full font-mono ${
            lowConfidence ? "bg-signal-red/15 text-signal-red" : "bg-signal-green/15 text-signal-green"
          }`}>
            {Math.round(confidence * 100)}%
          </span>
        )}
      </div>
      {lowConfidence && (
        <p className="flex items-center gap-1 text-[11px] text-signal-red mt-1">
          <AlertTriangle size={11} /> Low confidence — please verify before visualizing.
        </p>
      )}
      <div className="flex items-center gap-2 mt-3">
        <button
          onClick={onVisualize}
          className="inline-flex items-center gap-1.5 rounded-lg bg-accent-600/20 hover:bg-accent-600/30 text-accent-400 px-3 py-1.5 text-xs font-medium transition-colors"
        >
          <Eye size={13} /> Visualize
        </button>
        <button
          onClick={onVisualize}
          className="inline-flex items-center gap-1.5 rounded-lg bg-base-700/60 hover:bg-base-700 text-slate-300 px-3 py-1.5 text-xs font-medium transition-colors"
        >
          <BookOpen size={13} /> Explain
        </button>
        {onSave && (
          <button
            onClick={onSave}
            className="inline-flex items-center gap-1.5 rounded-lg bg-base-700/60 hover:bg-base-700 text-slate-300 px-3 py-1.5 text-xs font-medium transition-colors ml-auto"
          >
            <Bookmark size={13} />
          </button>
        )}
      </div>
    </div>
  );
}
