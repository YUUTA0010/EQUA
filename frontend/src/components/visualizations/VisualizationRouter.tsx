import type { VisualizationResponse } from "../../types/equation";
import Graph2D from "./Graph2D";
import Graph3DSurface from "./Graph3DSurface";
import PhysicsForceBlock from "./PhysicsForceBlock";
import CircuitOhm from "./CircuitOhm";
import Projectile from "./Projectile";
import SlopeField from "./SlopeField";
import TransferFunctionStep from "./TransferFunctionStep";

export default function VisualizationRouter({ viz }: { viz: VisualizationResponse }) {
  switch (viz.kind) {
    case "graph2d":
      return (
        <Graph2D
          x={viz.data.x} y={viz.data.y}
          xLabel={viz.data.x_label} yLabel={viz.data.y_label}
          keyPoints={viz.data.key_points} height={440}
        />
      );
    case "graph3d_surface":
      return (
        <Graph3DSurface
          x={viz.data.x} y={viz.data.y} z={viz.data.z}
          xLabel={viz.data.x_label} yLabel={viz.data.y_label} zLabel={viz.data.z_label}
        />
      );
    case "physics_force_block":
      return <PhysicsForceBlock data={viz.data} />;
    case "circuit_ohm":
      return <CircuitOhm data={viz.data} />;
    case "projectile":
      return <Projectile data={viz.data} />;
    case "slope_field":
      return <SlopeField data={viz.data} />;
    case "transfer_function_step":
      return <TransferFunctionStep data={viz.data} />;
    default:
      return (
        <div className="rounded-xl border border-base-600/60 bg-base-900/60 p-8 text-center text-slate-400">
          No visualization renderer is available yet for "{viz.kind}".
        </div>
      );
  }
}
