import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import TopBar from "../components/layout/TopBar";
import { InlineMath } from "react-katex";
import { api } from "../api/client";
import { DEMO_EQUATIONS, DOMAIN_LABELS } from "../demo/demoEquations";
import type { DemoEquation } from "../types/equation";
import { ArrowRight } from "lucide-react";

export default function LibraryPage() {
  const navigate = useNavigate();
  const [items, setItems] = useState<DemoEquation[]>(DEMO_EQUATIONS);
  const [filter, setFilter] = useState<string>("all");

  useEffect(() => {
    api.library().then((res) => setItems(res.demo_equations)).catch(() => {});
  }, []);

  const domains = ["all", ...Array.from(new Set(items.map((i) => i.domain_area)))];
  const filtered = filter === "all" ? items : items.filter((i) => i.domain_area === filter);

  return (
    <div className="min-h-screen">
      <TopBar title="Equation Library" />
      <div className="max-w-6xl mx-auto px-4 md:px-6 py-8 space-y-6">
        <div>
          <h2 className="text-2xl font-semibold text-slate-100">Equation Library</h2>
          <p className="text-slate-500 text-sm mt-1">A gallery of ready-to-explore equations across math, physics, and engineering.</p>
        </div>

        <div className="flex flex-wrap gap-2">
          {domains.map((d) => (
            <button
              key={d}
              onClick={() => setFilter(d)}
              className={`text-xs px-3 py-1.5 rounded-full border transition-colors capitalize ${
                filter === d ? "bg-accent-500/15 border-accent-500/50 text-accent-400" : "bg-base-800/60 border-base-600/60 text-slate-400 hover:border-base-500"
              }`}
            >
              {d === "all" ? "All" : DOMAIN_LABELS[d] || d}
            </button>
          ))}
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
          {filtered.map((item) => (
            <button
              key={item.equation}
              onClick={() => navigate(`/workspace?eq=${encodeURIComponent(item.equation)}`)}
              className="text-left rounded-2xl border border-base-600/60 bg-base-900/50 hover:border-accent-500/40 hover:bg-base-900/80 transition-colors p-5 group"
            >
              <p className="text-[11px] uppercase tracking-wide text-accent-400 font-semibold mb-2">
                {DOMAIN_LABELS[item.domain_area] || item.domain_area}
              </p>
              <div className="text-xl text-slate-100 font-mono mb-2">
                <SafeMath eq={item.equation} />
              </div>
              <p className="text-sm text-slate-500">{item.label}</p>
              <span className="inline-flex items-center gap-1 text-xs text-accent-400 mt-3 opacity-0 group-hover:opacity-100 transition-opacity">
                Visualize <ArrowRight size={12} />
              </span>
            </button>
          ))}
        </div>
      </div>
    </div>
  );
}

function SafeMath({ eq }: { eq: string }) {
  try {
    return <InlineMath math={eq.replace(/\*\*/g, "^").replace(/\*/g, "\\cdot ")} />;
  } catch {
    return <span>{eq}</span>;
  }
}
