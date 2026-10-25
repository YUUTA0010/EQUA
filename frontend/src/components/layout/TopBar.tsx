import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { Menu, Waves, CircuitBoard } from "lucide-react";
import { api } from "../../api/client";

interface TopBarProps {
  title?: string;
  engineeringMode?: boolean;
  onToggleEngineeringMode?: () => void;
}

export default function TopBar({ title, engineeringMode, onToggleEngineeringMode }: TopBarProps) {
  const [backendOk, setBackendOk] = useState<boolean | null>(null);

  useEffect(() => {
    api.health().then(() => setBackendOk(true)).catch(() => setBackendOk(false));
  }, []);

  return (
    <header className="sticky top-0 z-20 flex items-center justify-between gap-4 border-b border-base-700/60 bg-base-950/80 backdrop-blur px-4 md:px-6 py-3">
      <div className="flex items-center gap-3 min-w-0">
        <Link to="/" className="md:hidden flex items-center gap-1.5 shrink-0">
          <Waves size={18} className="text-accent-400" />
        </Link>
        <button className="md:hidden text-slate-400"><Menu size={20} /></button>
        {title && <h1 className="text-sm md:text-base font-semibold text-slate-200 truncate">{title}</h1>}
      </div>
      <div className="flex items-center gap-3 shrink-0">
        {onToggleEngineeringMode && (
          <button
            onClick={onToggleEngineeringMode}
            className={`hidden sm:inline-flex items-center gap-1.5 rounded-lg px-3 py-1.5 text-xs font-medium transition-colors ${
              engineeringMode ? "bg-signal-green/15 text-signal-green border border-signal-green/30"
                               : "bg-base-800 text-slate-400 border border-base-700"
            }`}
          >
            <CircuitBoard size={13} /> Engineering Mode
          </button>
        )}
        {backendOk === false && (
          <span className="text-[11px] text-signal-red px-2 py-1 rounded bg-signal-red/10">Backend offline</span>
        )}
      </div>
    </header>
  );
}
