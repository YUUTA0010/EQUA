import Plot from "./PlotlyBase";

interface Graph3DSurfaceProps {
  x: number[];
  y: number[];
  z: (number | null)[][];
  xLabel: string;
  yLabel: string;
  zLabel: string;
  height?: number;
}

export default function Graph3DSurface({ x, y, z, xLabel, yLabel, zLabel, height = 480 }: Graph3DSurfaceProps) {
  return (
    <Plot
      data={[
        {
          x, y, z, type: "surface",
          colorscale: [
            [0, "#1a2a4a"], [0.5, "#2cb8f0"], [1, "#5fd4ff"],
          ],
          showscale: false,
          contours: { z: { show: true, usecolormap: true, project: { z: true } } },
        },
      ]}
      layout={{
        autosize: true,
        height,
        margin: { l: 0, r: 0, t: 10, b: 0 },
        paper_bgcolor: "transparent",
        font: { color: "#94a3b8", family: "Inter, sans-serif", size: 11 },
        scene: {
          xaxis: { title: xLabel, gridcolor: "#1c2440", backgroundcolor: "transparent" },
          yaxis: { title: yLabel, gridcolor: "#1c2440", backgroundcolor: "transparent" },
          zaxis: { title: zLabel, gridcolor: "#1c2440", backgroundcolor: "transparent" },
        },
      }}
      config={{ displayModeBar: true, displaylogo: false, responsive: true }}
      style={{ width: "100%", height: "100%" }}
      useResizeHandler
    />
  );
}
