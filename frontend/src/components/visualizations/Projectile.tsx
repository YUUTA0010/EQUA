import { useEffect, useRef, useState } from "react";
import Plot from "./PlotlyBase";
import { Play, Pause, RotateCcw } from "lucide-react";

interface ProjectileProps {
  data: {
    x: number[]; y: number[]; t: number[];
    v0: number; theta_deg: number; g: number;
    time_of_flight: number; max_height: number; range: number;
    vx0: number; vy0: number;
  };
}

export default function Projectile({ data }: ProjectileProps) {
  const [frame, setFrame] = useState(0);
  const [playing, setPlaying] = useState(false);
  const rafRef = useRef<number | null>(null);
  const lastTsRef = useRef<number | null>(null);
  const n = data.x.length;

  useEffect(() => {
    setFrame(0);
    setPlaying(false);
  }, [data]);

  useEffect(() => {
    if (!playing) {
      if (rafRef.current) cancelAnimationFrame(rafRef.current);
      lastTsRef.current = null;
      return;
    }
    const duration = Math.max(data.time_of_flight, 0.3);
    const step = (ts: number) => {
      if (lastTsRef.current == null) lastTsRef.current = ts;
      const dt = (ts - lastTsRef.current) / 1000;
      lastTsRef.current = ts;
      setFrame((f) => {
        const next = f + (dt / duration) * n;
        if (next >= n - 1) {
          setPlaying(false);
          return n - 1;
        }
        return next;
      });
      rafRef.current = requestAnimationFrame(step);
    };
    rafRef.current = requestAnimationFrame(step);
    return () => {
      if (rafRef.current) cancelAnimationFrame(rafRef.current);
    };
  }, [playing, data, n]);

  const idx = Math.min(n - 1, Math.max(0, Math.round(frame)));
  const curX = data.x[idx] ?? 0;
  const curY = data.y[idx] ?? 0;
  const maxX = Math.max(...data.x, 1);
  const maxY = Math.max(...data.y, data.max_height, 1);

  const vScale = Math.min(maxX, maxY) * 0.18;
  const vxCur = data.vx0;
  const vyCur = data.vy0 - data.g * data.t[idx];
  const vMag = Math.sqrt(vxCur ** 2 + vyCur ** 2) || 1;

  return (
    <div className="space-y-4">
      <div className="rounded-xl border border-base-600/60 bg-base-900/60 p-3">
        <Plot
          data={[
            {
              x: data.x, y: data.y, type: "scatter", mode: "lines",
              line: { color: "#5fd4ff", width: 3 }, name: "Trajectory",
            },
            {
              x: [curX], y: [curY], type: "scatter", mode: "markers",
              marker: { color: "#f5a623", size: 14, symbol: "circle" }, name: "Projectile",
            },
            {
              x: [curX, curX + (vxCur / vMag) * vScale],
              y: [curY, curY + (vyCur / vMag) * vScale],
              type: "scatter", mode: "lines+markers",
              line: { color: "#3ddc97", width: 3 },
              marker: { size: [0, 6], color: "#3ddc97" },
              name: "Velocity",
            },
            {
              x: [curX, curX], y: [curY, curY - vScale * 0.6],
              type: "scatter", mode: "lines", line: { color: "#ff6b6b", width: 2, dash: "dot" },
              name: "Gravity",
            },
          ]}
          layout={{
            autosize: true, height: 380,
            margin: { l: 55, r: 20, t: 10, b: 45 },
            paper_bgcolor: "transparent", plot_bgcolor: "transparent",
            font: { color: "#94a3b8", family: "Inter, sans-serif", size: 12 },
            xaxis: { title: "Horizontal distance (m)", gridcolor: "#1c2440", range: [0, maxX * 1.1], scaleanchor: "y" },
            yaxis: { title: "Height (m)", gridcolor: "#1c2440", range: [0, maxY * 1.25] },
            showlegend: true,
            legend: { font: { color: "#94a3b8", size: 10 }, orientation: "h", y: -0.22 },
          }}
          config={{ displayModeBar: false, responsive: true }}
          style={{ width: "100%", height: "100%" }}
          useResizeHandler
        />
        <div className="flex items-center gap-3 mt-2 px-1">
          <button
            onClick={() => setPlaying((p) => !p)}
            className="inline-flex items-center gap-1.5 rounded-lg bg-accent-600/20 hover:bg-accent-600/30 text-accent-400 px-3 py-1.5 text-sm font-medium transition-colors"
          >
            {playing ? <Pause size={14} /> : <Play size={14} />}
            {playing ? "Pause" : "Launch"}
          </button>
          <button
            onClick={() => { setPlaying(false); setFrame(0); }}
            className="inline-flex items-center gap-1.5 rounded-lg bg-base-700/60 hover:bg-base-700 text-slate-300 px-3 py-1.5 text-sm font-medium transition-colors"
          >
            <RotateCcw size={14} /> Reset
          </button>
          <input
            type="range" min={0} max={n - 1} step={0.1} value={frame}
            onChange={(e) => { setPlaying(false); setFrame(Number(e.target.value)); }}
            className="flex-1"
          />
        </div>
      </div>

      <div className="grid grid-cols-3 gap-3">
        <StatCard label="Max height" value={`${data.max_height.toFixed(1)} m`} />
        <StatCard label="Range" value={`${data.range.toFixed(1)} m`} />
        <StatCard label="Time of flight" value={`${data.time_of_flight.toFixed(2)} s`} />
      </div>
    </div>
  );
}

function StatCard({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-xl border border-base-600/60 bg-base-900/60 px-4 py-3 text-center">
      <p className="text-[11px] uppercase tracking-wide text-slate-500">{label}</p>
      <p className="text-lg font-mono font-semibold text-slate-100 mt-0.5">{value}</p>
    </div>
  );
}
