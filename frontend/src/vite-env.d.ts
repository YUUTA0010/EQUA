/// <reference types="vite/client" />

declare module "react-plotly.js/factory" {
  import { Component } from "react";
  export default function createPlotlyComponent(plotly: any): typeof Component<any>;
}

declare module "plotly.js-dist-min";
