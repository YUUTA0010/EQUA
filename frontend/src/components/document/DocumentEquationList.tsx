import { useState } from "react";
import type { DocumentAnalysisResponse } from "../../types/equation";
import { InlineMath } from "react-katex";
import { AlertTriangle, Check, Edit3, Eye } from "lucide-react";

interface DocumentEquationListProps {
  document: DocumentAnalysisResponse;
  onVisualize: (equationText: string) => void;
}

export default function DocumentEquationList({ document, onVisualize }: DocumentEquationListProps) {
  const [corrections, setCorrections] = useState<Record<string, string>>({});
  const [editingId, setEditingId] = useState<string | null>(null);

  if (document.equations.length === 0) {
    return (
      <div className="rounded-xl border border-base-600/60 bg-base-900/60 p-6 text-center text-slate-400 text-sm">
        No equations were confidently detected in this document. Try "Paste Equation" instead, or upload a
        clearer image.
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="grid grid-cols-3 gap-3">
        <Stat label="Equations found" value={document.equations.length} />
        <Stat label="Subjects detected" value={document.subjects_detected.length || "—"} />
        <Stat label="Avg. confidence" value={`${Math.round(
          (document.equations.reduce((s, e) => s + e.confidence, 0) / document.equations.length) * 100
        )}%`} />
      </div>

      {document.subjects_detected.length > 0 && (
        <div className="flex flex-wrap gap-2">
          {document.subjects_detected.map((s) => (
            <span key={s} className="text-xs px-2.5 py-1 rounded-full bg-base-700/60 text-slate-300 capitalize">{s}</span>
          ))}
        </div>
      )}

      <div className="space-y-3">
        {document.equations.map((eq, i) => {
          const isLow = eq.confidence < 0.6;
          const currentText = corrections[eq.id] ?? eq.raw_text;
          const isEditing = editingId === eq.id;
          return (
            <div key={eq.id} className="rounded-xl border border-base-600/60 bg-base-900/60 p-4">
              <div className="flex items-start justify-between gap-3">
                <div className="min-w-0 flex-1">
                  <p className="text-[11px] text-slate-500 mb-1">Equation {String(i + 1).padStart(2, "0")}{eq.page ? ` · page ${eq.page}` : ""}</p>
                  {isEditing ? (
                    <input
                      autoFocus
                      value={currentText}
                      onChange={(e) => setCorrections((c) => ({ ...c, [eq.id]: e.target.value }))}
                      className="w-full rounded-lg bg-base-800/70 border border-accent-500/50 px-3 py-2 text-sm font-mono text-slate-100 focus:outline-none"
                    />
                  ) : (
                    <div className="text-lg font-mono text-slate-100 overflow-x-auto">
                      <SafeMath text={currentText} />
                    </div>
                  )}
                </div>
                <span className={`shrink-0 text-[10px] px-1.5 py-0.5 rounded-full font-mono ${
                  isLow ? "bg-signal-red/15 text-signal-red" : "bg-signal-green/15 text-signal-green"
                }`}>
                  {Math.round(eq.confidence * 100)}%
                </span>
              </div>

              {isLow && !isEditing && (
                <p className="flex items-center gap-1 text-[11px] text-signal-red mt-2">
                  <AlertTriangle size={11} /> Equation recognition confidence: {Math.round(eq.confidence * 100)}%. Please verify.
                </p>
              )}

              <div className="flex items-center gap-2 mt-3">
                {isEditing ? (
                  <button
                    onClick={() => setEditingId(null)}
                    className="inline-flex items-center gap-1.5 rounded-lg bg-signal-green/15 hover:bg-signal-green/25 text-signal-green px-3 py-1.5 text-xs font-medium transition-colors"
                  >
                    <Check size={13} /> Apply Correction
                  </button>
                ) : (
                  <button
                    onClick={() => setEditingId(eq.id)}
                    className="inline-flex items-center gap-1.5 rounded-lg bg-base-700/60 hover:bg-base-700 text-slate-300 px-3 py-1.5 text-xs font-medium transition-colors"
                  >
                    <Edit3 size={13} /> Edit Equation
                  </button>
                )}
                <button
                  onClick={() => onVisualize(currentText)}
                  className="inline-flex items-center gap-1.5 rounded-lg bg-accent-600/20 hover:bg-accent-600/30 text-accent-400 px-3 py-1.5 text-xs font-medium transition-colors ml-auto"
                >
                  <Eye size={13} /> Visualize
                </button>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}

function SafeMath({ text }: { text: string }) {
  try {
    return <InlineMath math={text.replace(/\*\*/g, "^").replace(/\*/g, "\\cdot ")} />;
  } catch {
    return <span>{text}</span>;
  }
}

function Stat({ label, value }: { label: string; value: string | number }) {
  return (
    <div className="rounded-xl border border-base-600/60 bg-base-900/60 px-3 py-2.5 text-center">
      <p className="text-[10px] uppercase tracking-wide text-slate-500">{label}</p>
      <p className="text-base font-mono font-semibold text-slate-100">{value}</p>
    </div>
  );
}
