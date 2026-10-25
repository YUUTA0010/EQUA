import Graph2D from "./Graph2D";

interface PhysicsForceBlockProps {
  data: {
    F: number; m: number; a: number;
    a_vs_m: { x: number[]; y: number[]; x_label: string; y_label: string; current_x: number };
    a_vs_F: { x: number[]; y: number[]; x_label: string; y_label: string; current_x: number };
  };
}

export default function PhysicsForceBlock({ data }: PhysicsForceBlockProps) {
  const { F, m, a } = data;
  // Block size scales gently with mass (visual metaphor, clamped for sanity)
  const blockSize = 60 + Math.min(60, Math.sqrt(m) * 12);
  const forceArrowLen = 40 + Math.min(160, F * 3);
  const accelArrowLen = 40 + Math.min(160, a * 12);
  const cx = 260;
  const cy = 130;

  return (
    <div className="space-y-6">
      <div className="rounded-xl border border-base-600/60 bg-base-900/60 p-4">
        <svg viewBox="0 0 520 260" className="w-full h-64">
          {/* ground line */}
          <line x1="20" y1={cy + blockSize / 2 + 30} x2="500" y2={cy + blockSize / 2 + 30} stroke="#2a3355" strokeWidth="2" />
          {/* Force arrow (incoming, from the left) */}
          <g>
            <line
              x1={cx - blockSize / 2 - forceArrowLen} y1={cy}
              x2={cx - blockSize / 2 - 6} y2={cy}
              stroke="#f5a623" strokeWidth="4" markerEnd="url(#arrow-force)"
            />
            <text x={cx - blockSize / 2 - forceArrowLen} y={cy - 14} fill="#f5a623" fontSize="15" fontFamily="JetBrains Mono, monospace" fontWeight="600">
              F = {F.toFixed(1)} N
            </text>
          </g>
          {/* Block */}
          <rect
            x={cx - blockSize / 2} y={cy - blockSize / 2} width={blockSize} height={blockSize}
            rx="8" fill="#1c2440" stroke="#5fd4ff" strokeWidth="2.5"
          />
          <text x={cx} y={cy + 5} textAnchor="middle" fill="#e2e8f0" fontSize="14" fontFamily="JetBrains Mono, monospace" fontWeight="700">
            m = {m.toFixed(1)} kg
          </text>
          {/* Acceleration arrow (outgoing, to the right) */}
          <g>
            <line
              x1={cx + blockSize / 2 + 6} y1={cy}
              x2={cx + blockSize / 2 + accelArrowLen} y2={cy}
              stroke="#3ddc97" strokeWidth="4" markerEnd="url(#arrow-accel)"
            />
            <text x={cx + blockSize / 2 + 10} y={cy - 14} fill="#3ddc97" fontSize="15" fontFamily="JetBrains Mono, monospace" fontWeight="600">
              a = {a.toFixed(2)} m/s²
            </text>
          </g>
          <defs>
            <marker id="arrow-force" markerWidth="10" markerHeight="10" refX="8" refY="5" orient="auto">
              <path d="M0,0 L10,5 L0,10 Z" fill="#f5a623" />
            </marker>
            <marker id="arrow-accel" markerWidth="10" markerHeight="10" refX="8" refY="5" orient="auto">
              <path d="M0,0 L10,5 L0,10 Z" fill="#3ddc97" />
            </marker>
          </defs>
        </svg>
        <p className="text-center text-xs text-slate-500 mt-1">
          Force in (amber) drives the block; the resulting acceleration (green) is what you'd observe.
        </p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div className="rounded-xl border border-base-600/60 bg-base-900/60 p-3">
          <p className="text-xs font-semibold text-slate-400 mb-1 px-1">Acceleration vs. Mass (F fixed at {F.toFixed(1)} N)</p>
          <Graph2D
            x={data.a_vs_m.x} y={data.a_vs_m.y}
            xLabel={data.a_vs_m.x_label} yLabel={data.a_vs_m.y_label}
            height={220} color="#5fd4ff"
            keyPoints={[{ x: m, y: a, label: "current" }]}
          />
        </div>
        <div className="rounded-xl border border-base-600/60 bg-base-900/60 p-3">
          <p className="text-xs font-semibold text-slate-400 mb-1 px-1">Acceleration vs. Force (m fixed at {m.toFixed(1)} kg)</p>
          <Graph2D
            x={data.a_vs_F.x} y={data.a_vs_F.y}
            xLabel={data.a_vs_F.x_label} yLabel={data.a_vs_F.y_label}
            height={220} color="#f5a623"
            keyPoints={[{ x: F, y: a, label: "current" }]}
          />
        </div>
      </div>
    </div>
  );
}
