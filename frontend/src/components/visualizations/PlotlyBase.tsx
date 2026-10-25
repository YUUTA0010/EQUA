import Plotly from "plotly.js-dist-min";
import createPlotlyComponent from "react-plotly.js/factory";

const factory: any = (createPlotlyComponent as any).default || createPlotlyComponent;
const PlotlyLib: any = (Plotly as any).default || Plotly;
const Plot = typeof factory === "function" ? factory(PlotlyLib) : (() => null);

export default Plot;
