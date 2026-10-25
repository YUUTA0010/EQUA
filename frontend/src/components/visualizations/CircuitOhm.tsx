import Graph2D from "./Graph2D";

interface CircuitOhmProps {
  data: {
    V: number; I: number; R: number;
    V_vs_R: { x: number[]; y: number[]; x_label: string; y_label: string; current_x: number };
    V_vs_I: { x: number[]; y: number[]; x_label: string; y_label: string; current_x: number };
  };
}

export default function CircuitOhm({ data }: CircuitOhmProps) {
  const { V, I, R } = data;
  const zigzags = Math.max(4, Math.min(10, Math.round(3 + R / 20)));

  const zigzagPath = (x0: number, x1: number, y: number, n: number) => {
    const w = (x1 - x0) / n;
    let d = `M ${x0} ${y}`;
    for (let i = 0; i < n; i++) {
      const xa = x0 + w * i + w * 0.25;
      const xb = x0 + w * i + w * 0.75;
      const dy = i % 2 === 0 ? -14 : 14;
      d += ` L ${xa} ${y + dy} L ${xb} ${y - dy}`;
    }
    d += ` L ${x1} ${y}`;
    return d;
  };

  return (
    <div className="space-y-6">
      <div className="rounded-xl border border-base-600/60 bg-base-900/60 p-4">
        <svg viewBox="0 0 520 220" className="w-full h-56">
          {/* Loop wires */}
          <line x1="80" y1="60" x2="80" y2="160" stroke="#5fd4ff" strokeWidth="3" />
          <line x1="80" y1="60" x2="200" y2="60" stroke="#5fd4ff" strokeWidth="3" />
          <line x1="340" y1="60" x2="440" y2="60" stroke="#5fd4ff" strokeWidth="3" />
          <line x1="440" y1="60" x2="440" y2="160" stroke="#5fd4ff" strokeWidth="3" />
          <line x1="80" y1="160" x2="440" y2="160" stroke="#5fd4ff" strokeWidth="3" />

          {/* Battery symbol at left */}
          <g transform="translate(80,110)">
            <line x1="0" y1="-30" x2="0" y2="-14" stroke="#5fd4ff" strokeWidth="3" />
            <line x1="-14" y1="-14" x2="14" y2="-14" stroke="#f5a623" strokeWidth="5" />
            <line x1="-7" y1="-4" x2="7" y2="-4" stroke="#f5a623" strokeWidth="2" />
            <line x1="0" y1="6" x2="0" y2="50" stroke="#5fd4ff" strokeWidth="3" />
            <text x="26" y="4" fill="#f5a623" fontSize="14" fontFamily="JetBrains Mono, monospace" fontWeight="600">
              V = {V.toFixed(2)} V
            </text>
          </g>

          {/* Resistor zig-zag at top */}
          <path d={zigzagPath(200, 340, 60, zigzags)} fill="none" stroke="#3ddc97" strokeWidth="3" strokeLinejoin="round" />
          <text x="210" y="34" fill="#3ddc97" fontSize="14" fontFamily="JetBrains Mono, monospace" fontWeight="600">
            R = {R.toFixed(1)} Ω
          </text>

          {/* Current direction arrows along the bottom wire */}
          {[140, 230, 320, 400].map((x, i) => (
            <g key={i} transform={`translate(${x},160)`}>
              <path d="M0,0 L-10,-6 L-10,6 Z" fill="#ff6b6b" transform="rotate(180)" />
            </g>
          ))}
          <text x="230" y="185" fill="#ff6b6b" fontSize="14" fontFamily="JetBrains Mono, monospace" fontWeight="600" textAnchor="middle">
            I = {I.toFixed(2)} A
          </text>
        </svg>
        <p className="text-center text-xs text-slate-500 mt-1">
          Current I flows around the loop; the resistor R converts that flow into a voltage drop V = IR.
        </p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div className="rounded-xl border border-base-600/60 bg-base-900/60 p-3">
          <p className="text-xs font-semibold text-slate-400 mb-1 px-1">Voltage vs. Resistance (I fixed at {I.toFixed(2)} A)</p>
          <Graph2D
            x={data.V_vs_R.x} y={data.V_vs_R.y}
            xLabel={data.V_vs_R.x_label} yLabel={data.V_vs_R.y_label}
            height={220} color="#3ddc97"
            keyPoints={[{ x: R, y: V, label: "current" }]}
          />
        </div>
        <div className="rounded-xl border border-base-600/60 bg-base-900/60 p-3">
          <p className="text-xs font-semibold text-slate-400 mb-1 px-1">Voltage vs. Current (R fixed at {R.toFixed(1)} Ω)</p>
          <Graph2D
            x={data.V_vs_I.x} y={data.V_vs_I.y}
            xLabel={data.V_vs_I.x_label} yLabel={data.V_vs_I.y_label}
            height={220} color="#ff6b6b"
            keyPoints={[{ x: I, y: V, label: "current" }]}
          />
        </div>
      </div>
    </div>
  );
}
