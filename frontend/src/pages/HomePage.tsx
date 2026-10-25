import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { ArrowRight, Upload, Sparkles } from "lucide-react";
import TopBar from "../components/layout/TopBar";
import { InlineMath } from "react-katex";
import { DEMO_EQUATIONS } from "../demo/demoEquations";

const FEATURE_CARDS = [
  { domain: "Mathematics", eq: "y = x**2", blurb: "See how changing coefficients changes the parabola." },
  { domain: "Physics", eq: "F = m*a", blurb: "See force, mass and acceleration interact." },
  { domain: "Electrical", eq: "V = I*R", blurb: "See voltage, current and resistance visually." },
  { domain: "Signals", eq: "y = A*sin(omega*t)", blurb: "See amplitude, frequency and phase in action." },
];

export default function HomePage() {
  const navigate = useNavigate();
  const [input, setInput] = useState("");

  const go = (eq: string) => navigate(`/workspace?eq=${encodeURIComponent(eq)}`);

  return (
    <div className="min-h-screen">
      <TopBar />
      <div className="max-w-5xl mx-auto px-4 md:px-6 py-14 md:py-20">
        <div className="text-center space-y-5">
          <span className="inline-flex items-center gap-1.5 text-xs font-medium text-accent-400 bg-accent-500/10 border border-accent-500/25 rounded-full px-3 py-1">
            <Sparkles size={12} /> Don't just solve the equation — see what it means
          </span>
          <h1 className="text-4xl md:text-6xl font-bold tracking-tight text-slate-50">
            See What Equations<br />Actually Do.
          </h1>
          <p className="text-slate-400 max-w-2xl mx-auto text-base md:text-lg leading-relaxed">
            Upload a textbook, equation, or engineering problem. EquationLens transforms mathematical
            formulas into interactive graphs, simulations, diagrams, and physical representations.
          </p>
        </div>

        <div className="mt-10 max-w-2xl mx-auto">
          <div className="flex flex-col sm:flex-row gap-3">
            <input
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && input.trim() && go(input.trim())}
              placeholder="Type an equation, e.g. F = m*a"
              className="flex-1 rounded-xl bg-base-900/70 border border-base-600/60 px-4 py-3.5 text-slate-100 font-mono text-sm focus:outline-none focus:border-accent-500/60"
            />
            <button
              onClick={() => input.trim() && go(input.trim())}
              className="inline-flex items-center justify-center gap-2 rounded-xl bg-accent-600 hover:bg-accent-500 text-base-950 font-semibold px-5 py-3.5 text-sm transition-colors"
            >
              Visualize an Equation <ArrowRight size={16} />
            </button>
          </div>
          <div className="flex justify-center mt-3">
            <button
              onClick={() => navigate("/upload")}
              className="inline-flex items-center gap-2 text-sm text-slate-400 hover:text-slate-200 transition-colors"
            >
              <Upload size={14} /> or Upload a Document
            </button>
          </div>
        </div>

        <div className="mt-16 grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          {FEATURE_CARDS.map((c) => (
            <button
              key={c.eq}
              onClick={() => go(c.eq)}
              className="text-left rounded-2xl border border-base-600/60 bg-base-900/50 hover:border-accent-500/40 hover:bg-base-900/80 transition-colors p-5 group"
            >
              <p className="text-[11px] uppercase tracking-wide text-accent-400 font-semibold mb-2">{c.domain}</p>
              <div className="text-xl text-slate-100 font-mono mb-2">
                <SafeMath eq={c.eq} />
              </div>
              <p className="text-sm text-slate-500 leading-relaxed">{c.blurb}</p>
              <span className="inline-flex items-center gap-1 text-xs text-accent-400 mt-3 opacity-0 group-hover:opacity-100 transition-opacity">
                Visualize <ArrowRight size={12} />
              </span>
            </button>
          ))}
        </div>

        <div className="mt-14">
          <p className="text-xs uppercase tracking-wide text-slate-500 mb-3 text-center">Or jump into the full example gallery</p>
          <div className="flex flex-wrap justify-center gap-2">
            {DEMO_EQUATIONS.map((d) => (
              <button
                key={d.equation}
                onClick={() => go(d.equation)}
                className="text-xs px-3 py-1.5 rounded-full bg-base-800/60 border border-base-600/60 text-slate-300 hover:border-accent-500/50 hover:text-accent-300 transition-colors"
              >
                {d.label}
              </button>
            ))}
          </div>
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
