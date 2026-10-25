import { useEffect, useState } from "react";
import { useSearchParams } from "react-router-dom";
import { Loader2, AlertTriangle, Bookmark, Check } from "lucide-react";
import TopBar from "../components/layout/TopBar";
import EquationDisplay from "../components/equation/EquationDisplay";
import VariableList from "../components/equation/VariableList";
import ParameterExplorer from "../components/equation/ParameterExplorer";
import WhatIfPanel from "../components/equation/WhatIfPanel";
import ActionButtons from "../components/equation/ActionButtons";
import ChangeOneThing from "../components/equation/ChangeOneThing";
import CompareView from "../components/equation/CompareView";
import VisualizationRouter from "../components/visualizations/VisualizationRouter";
import { useEquationWorkspace } from "../hooks/useEquationWorkspace";
import { api } from "../api/client";

const DOMAIN_LABEL: Record<string, string> = {
  mathematics: "Mathematics", physics: "Physics", electrical: "Electrical",
  mechanical: "Mechanical", control: "Control Systems", signals: "Signals",
  engineering_mathematics: "Engineering Mathematics",
};

export default function WorkspacePage() {
  const [params] = useSearchParams();
  const eq = params.get("eq") || "F = m*a";
  const {
    equation, analysis, parameters, viz, visualizationId, lockedSymbol,
    analyzing, visualizing, error,
    loadEquation, updateParameter, resetParameters, setVisualizationId, setLockedSymbol,
  } = useEquationWorkspace(eq);

  const [saved, setSaved] = useState(false);

  useEffect(() => { loadEquation(eq); }, [eq]); // eslint-disable-line react-hooks/exhaustive-deps

  const dependentVar = analysis?.variables.find((v) => v.role === "dependent");
  const dependentValue = viz?.kind === "physics_force_block" ? viz.data.a
    : viz?.kind === "circuit_ohm" ? viz.data.V
    : viz?.kind === "graph2d" && dependentVar ? undefined
    : undefined;

  const handleSave = async () => {
    if (!analysis) return;
    try {
      await api.saveEquation({ equation: analysis.equation, category: analysis.category, parameters });
      setSaved(true);
      setTimeout(() => setSaved(false), 2000);
    } catch { /* non-critical */ }
  };

  return (
    <div className="min-h-screen">
      <TopBar title="Workspace" />
      <div className="p-4 md:p-6 max-w-[1500px] mx-auto space-y-5">
        {analyzing && (
          <div className="flex items-center gap-2 text-slate-400 text-sm">
            <Loader2 size={16} className="animate-spin" /> Analyzing equation…
          </div>
        )}

        {error && !analyzing && (
          <div className="rounded-xl border border-signal-red/30 bg-signal-red/10 text-signal-red text-sm px-4 py-3 flex items-center gap-2">
            <AlertTriangle size={16} /> {error}
          </div>
        )}

        {analysis && !analyzing && (
          <>
            {/* Header: equation + category */}
            <div className="rounded-2xl border border-base-600/60 bg-gradient-to-br from-base-900 to-base-800/60 shadow-panel p-5 md:p-6">
              <div className="flex flex-wrap items-start justify-between gap-3">
                <div>
                  <div className="flex items-center gap-2 mb-1">
                    <span className="text-[11px] uppercase tracking-wide text-accent-400 font-semibold">
                      {DOMAIN_LABEL[analysis.domain_area] || analysis.domain_area}
                    </span>
                    {analysis.is_ambiguous && (
                      <span className="text-[10px] px-1.5 py-0.5 rounded bg-signal-amber/15 text-signal-amber">
                        multiple interpretations possible
                      </span>
                    )}
                  </div>
                  <h2 className="text-xl font-semibold text-slate-100">{analysis.category_label}</h2>
                </div>
                <button
                  onClick={handleSave}
                  className="inline-flex items-center gap-1.5 rounded-lg bg-base-700/60 hover:bg-base-700 text-slate-300 px-3 py-2 text-xs font-medium transition-colors"
                >
                  {saved ? <Check size={13} className="text-signal-green" /> : <Bookmark size={13} />}
                  {saved ? "Saved" : "Save"}
                </button>
              </div>
              <EquationDisplay latex={analysis.latex} />
              <p className="text-sm text-slate-400 leading-relaxed mt-1">{analysis.physical_interpretation}</p>
              {analysis.warnings.length > 0 && (
                <div className="mt-2 flex items-start gap-1.5 text-xs text-signal-amber">
                  <AlertTriangle size={13} className="mt-0.5 shrink-0" />
                  <span>{analysis.warnings.join(" ")}</span>
                </div>
              )}
            </div>

            {/* Visualization option switcher */}
            {analysis.recommended_visualizations.length > 1 && (
              <div className="flex flex-wrap gap-2">
                {analysis.recommended_visualizations.map((opt) => (
                  <button
                    key={opt.id}
                    onClick={() => setVisualizationId(opt.id)}
                    title={opt.reason}
                    className={`text-xs px-3 py-1.5 rounded-full border transition-colors ${
                      visualizationId === opt.id
                        ? "bg-accent-500/15 border-accent-500/50 text-accent-400"
                        : "bg-base-800/60 border-base-600/60 text-slate-400 hover:border-base-500"
                    }`}
                  >
                    {opt.label}
                  </button>
                ))}
              </div>
            )}

            {/* Main grid: visualization dominant + side panels */}
            <div className="grid grid-cols-1 xl:grid-cols-[1fr_360px] gap-5">
              <div className="space-y-4 min-w-0">
                <div className="rounded-2xl border border-base-600/60 bg-base-900/40 shadow-panel p-4 md:p-5 relative">
                  {visualizing && (
                    <div className="absolute top-3 right-3 text-accent-400"><Loader2 size={16} className="animate-spin" /></div>
                  )}
                  {viz ? <VisualizationRouter viz={viz} /> : (
                    <div className="h-64 flex items-center justify-center text-slate-500 text-sm">
                      Building visualization…
                    </div>
                  )}
                  {viz?.caption && <p className="text-center text-xs text-slate-500 mt-2">{viz.caption}</p>}
                </div>

                <ActionButtons equation={analysis.equation} parameters={parameters} />

                <div className="flex flex-wrap items-center gap-3">
                  <ChangeOneThing analysis={analysis} lockedSymbol={lockedSymbol} onSelect={setLockedSymbol} />
                </div>
                <CompareView analysis={analysis} currentParameters={parameters} />
              </div>

              {/* Right rail: variables, parameters, what-if */}
              <div className="space-y-4 min-w-0">
                <Panel title="What Each Part Means">
                  <VariableList analysis={analysis} />
                </Panel>
                <Panel title="Parameter Explorer" action={
                  <button onClick={resetParameters} className="text-[11px] text-slate-500 hover:text-slate-300">Reset</button>
                }>
                  <ParameterExplorer
                    analysis={analysis} values={parameters} onChange={updateParameter}
                    dependentValue={dependentValue as number | undefined}
                    lockedSymbol={lockedSymbol}
                  />
                </Panel>
                <Panel title="What Happens If…">
                  <WhatIfPanel analysis={analysis} parameters={parameters} />
                </Panel>
              </div>
            </div>
          </>
        )}
      </div>
    </div>
  );
}

function Panel({ title, action, children }: { title: string; action?: React.ReactNode; children: React.ReactNode }) {
  return (
    <div className="rounded-2xl border border-base-600/60 bg-base-900/40 shadow-panel p-4">
      <div className="flex items-center justify-between mb-3">
        <p className="text-xs font-semibold uppercase tracking-wide text-slate-400">{title}</p>
        {action}
      </div>
      {children}
    </div>
  );
}
