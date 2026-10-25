import { useEffect, useState } from "react";
import TopBar from "../components/layout/TopBar";
import { api } from "../api/client";
import { CheckCircle2, XCircle } from "lucide-react";

export default function SettingsPage() {
  const [health, setHealth] = useState<any>(null);
  const [err, setErr] = useState(false);

  useEffect(() => {
    api.health().then(setHealth).catch(() => setErr(true));
  }, []);

  return (
    <div className="min-h-screen">
      <TopBar title="Settings" />
      <div className="max-w-2xl mx-auto px-4 md:px-6 py-8 space-y-6">
        <h2 className="text-2xl font-semibold text-slate-100">Settings</h2>

        <div className="rounded-2xl border border-base-600/60 bg-base-900/50 p-5 space-y-3">
          <p className="text-sm font-semibold text-slate-300 uppercase tracking-wide text-xs">Backend status</p>
          {err && <p className="text-signal-red text-sm">Could not reach the backend at /api. Is it running?</p>}
          {health && (
            <div className="space-y-2 text-sm">
              <Row label="API" ok value="Reachable" />
              <Row label="AI Explanations" ok={health.ai_explanations === "openai"} value={
                health.ai_explanations === "openai" ? "OpenAI configured" : "Template fallback (no API key set)"
              } />
              <Row label="OCR (Tesseract)" ok={health.ocr_available} value={health.ocr_available ? "Available" : "Not installed"} />
              <Row label="Max upload size" ok value={`${health.max_upload_mb} MB`} />
            </div>
          )}
        </div>

        <div className="rounded-2xl border border-base-600/60 bg-base-900/50 p-5 space-y-2 text-sm text-slate-400">
          <p className="font-semibold text-slate-300">About EquationLens</p>
          <p>Version 0.1.0 — MVP build. Equation classification, symbolic analysis, and all numeric computation
             run deterministically via SymPy/NumPy/SciPy. AI is used only for optional prose explanations.</p>
        </div>
      </div>
    </div>
  );
}

function Row({ label, ok, value }: { label: string; ok: boolean; value: string }) {
  return (
    <div className="flex items-center justify-between border-b border-base-700/50 pb-2 last:border-0 last:pb-0">
      <span className="text-slate-400">{label}</span>
      <span className={`flex items-center gap-1.5 font-medium ${ok ? "text-signal-green" : "text-signal-amber"}`}>
        {ok ? <CheckCircle2 size={14} /> : <XCircle size={14} />} {value}
      </span>
    </div>
  );
}
