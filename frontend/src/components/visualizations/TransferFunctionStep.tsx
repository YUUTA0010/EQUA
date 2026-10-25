import Plot from "./PlotlyBase";
import Graph2D from "./Graph2D";

interface TransferFunctionStepProps {
  data: {
    t: number[]; y: number[]; poles: { re: number; im: number }[];
    regime: string; zeta: number; wn: number;
  };
}

const REGIME_LABEL: Record<string, string> = {
  underdamped: "Underdamped — oscillates before settling",
  critically_damped: "Critically damped — fastest non-oscillating response",
  overdamped: "Overdamped — slow, no oscillation",
};

export default function TransferFunctionStep({ data }: TransferFunctionStepProps) {
  const maxIm = Math.max(1, ...data.poles.map((p) => Math.abs(p.im)));
  const maxRe = Math.max(1, ...data.poles.map((p) => Math.abs(p.re)));

  return (
    <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
      <div className="lg:col-span-2 rounded-xl border border-base-600/60 bg-base-900/60 p-3">
        <p className="text-xs font-semibold text-slate-400 mb-1 px-1">Step Response</p>
        <Graph2D x={data.t} y={data.y} xLabel="Time (s)" yLabel="Output" height={340} color="#5fd4ff" />
        <p className="text-center text-xs text-slate-500 mt-1 px-2">{REGIME_LABEL[data.regime] || data.regime}</p>
      </div>
      <div className="rounded-xl border border-base-600/60 bg-base-900/60 p-3">
        <p className="text-xs font-semibold text-slate-400 mb-1 px-1">Pole Locations (s-plane)</p>
        <Plot
          data={[
            {
              x: data.poles.map((p) => p.re), y: data.poles.map((p) => p.im),
              type: "scatter", mode: "markers",
              marker: { symbol: "x", size: 14, color: "#ff6b6b", line: { width: 2 } },
              name: "Poles",
            },
          ]}
          layout={{
            autosize: true, height: 300,
            margin: { l: 45, r: 15, t: 5, b: 40 },
            paper_bgcolor: "transparent", plot_bgcolor: "transparent",
            font: { color: "#94a3b8", family: "Inter, sans-serif", size: 11 },
            xaxis: { title: "Real", range: [-maxRe * 1.4 - 0.5, maxRe * 0.4 + 0.5], gridcolor: "#1c2440", zerolinecolor: "#3a4570" },
            yaxis: { title: "Imaginary", range: [-maxIm * 1.3 - 0.5, maxIm * 1.3 + 0.5], gridcolor: "#1c2440", zerolinecolor: "#3a4570" },
          }}
          config={{ displayModeBar: false, responsive: true }}
          style={{ width: "100%", height: "100%" }}
          useResizeHandler
        />
        <p className="text-center text-xs text-slate-500 mt-1">
          ζ = {data.zeta.toFixed(2)}, ωₙ = {data.wn.toFixed(2)} rad/s
        </p>
      </div>
    </div>
  );
}
