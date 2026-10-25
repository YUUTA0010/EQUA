import Plot from "./PlotlyBase";

interface SlopeFieldProps {
  data: {
    segments: { x0: number; y0: number; x1: number; y1: number }[];
    curves: { y0: number; x: number[]; y: number[] }[];
    x_range: [number, number];
    y_range: [number, number];
  };
}

const CURVE_COLORS = ["#5fd4ff", "#f5a623", "#3ddc97", "#ff6b6b", "#b78bff"];

export default function SlopeField({ data }: SlopeFieldProps) {
  const shapes = data.segments.map((s) => ({
    type: "line" as const,
    x0: s.x0, y0: s.y0, x1: s.x1, y1: s.y1,
    line: { color: "#2a3355", width: 1.5 },
  }));

  const traces = data.curves.map((c, i) => ({
    x: c.x, y: c.y, type: "scatter" as const, mode: "lines" as const,
    line: { color: CURVE_COLORS[i % CURVE_COLORS.length], width: 3 },
    name: `y(0) = ${c.y0}`,
  }));

  return (
    <div className="rounded-xl border border-base-600/60 bg-base-900/60 p-3">
      <Plot
        data={traces}
        layout={{
          autosize: true, height: 460,
          margin: { l: 55, r: 20, t: 10, b: 45 },
          paper_bgcolor: "transparent", plot_bgcolor: "transparent",
          font: { color: "#94a3b8", family: "Inter, sans-serif", size: 12 },
          xaxis: { title: "x", range: data.x_range, gridcolor: "#1c2440", zerolinecolor: "#2a3355" },
          yaxis: { title: "y", range: data.y_range, gridcolor: "#1c2440", zerolinecolor: "#2a3355" },
          shapes,
          showlegend: true,
          legend: { font: { color: "#94a3b8" }, orientation: "h", y: -0.2 },
        }}
        config={{ displayModeBar: true, displaylogo: false, responsive: true }}
        style={{ width: "100%", height: "100%" }}
        useResizeHandler
      />
      <p className="text-center text-xs text-slate-500 mt-1 px-2">
        Each short gray segment shows the slope dy/dx at that point. The colored curves trace actual
        solutions starting from different initial values of y — notice how every curve follows the
        surrounding slope directions.
      </p>
    </div>
  );
}
