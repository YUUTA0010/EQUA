import Plot from "./PlotlyBase";

interface KeyPoint { x: number; y: number; label: string }

interface Graph2DProps {
  x: number[];
  y: (number | null)[];
  xLabel: string;
  yLabel: string;
  keyPoints?: KeyPoint[];
  color?: string;
  title?: string;
  height?: number;
  extraTraces?: { x: number[]; y: (number | null)[]; name: string; color?: string; dash?: string }[];
}

export default function Graph2D({
  x, y, xLabel, yLabel, keyPoints = [], color = "#5fd4ff", title, height = 420, extraTraces = [],
}: Graph2DProps) {
  const traces: any[] = [
    {
      x, y, type: "scatter", mode: "lines",
      line: { color, width: 3 },
      name: yLabel,
      hovertemplate: `${xLabel}=%{x:.3f}<br>${yLabel}=%{y:.3f}<extra></extra>`,
    },
    ...extraTraces.map((t) => ({
      x: t.x, y: t.y, type: "scatter", mode: "lines",
      line: { color: t.color || "#f5a623", width: 2, dash: t.dash || "solid" },
      name: t.name,
    })),
  ];

  if (keyPoints.length > 0) {
    traces.push({
      x: keyPoints.map((k) => k.x),
      y: keyPoints.map((k) => k.y),
      type: "scatter", mode: "markers",
      marker: { color: "#ff6b6b", size: 9, symbol: "circle-open", line: { width: 2 } },
      name: "Key points",
      text: keyPoints.map((k) => k.label),
      hovertemplate: "%{text}<br>(%{x:.3f}, %{y:.3f})<extra></extra>",
    });
  }

  return (
    <Plot
      data={traces}
      layout={{
        title: title ? { text: title, font: { size: 14, color: "#cbd5e1" } } : undefined,
        autosize: true,
        height,
        margin: { l: 55, r: 20, t: title ? 36 : 10, b: 45 },
        paper_bgcolor: "transparent",
        plot_bgcolor: "transparent",
        font: { color: "#94a3b8", family: "Inter, sans-serif", size: 12 },
        xaxis: { title: xLabel, gridcolor: "#1c2440", zerolinecolor: "#2a3355", zerolinewidth: 1 },
        yaxis: { title: yLabel, gridcolor: "#1c2440", zerolinecolor: "#2a3355", zerolinewidth: 1 },
        showlegend: extraTraces.length > 0,
        legend: { font: { color: "#94a3b8" }, orientation: "h", y: -0.2 },
      }}
      config={{ displayModeBar: true, displaylogo: false, responsive: true, modeBarButtonsToRemove: ["lasso2d", "select2d"] }}
      style={{ width: "100%", height: "100%" }}
      useResizeHandler
    />
  );
}
