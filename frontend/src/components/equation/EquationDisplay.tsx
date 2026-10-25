import React from "react";
import { BlockMath } from "react-katex";

export default function EquationDisplay({ latex, size = "lg" }: { latex: string; size?: "lg" | "md" }) {
  return (
    <div className={`w-full overflow-x-auto py-2 text-slate-50 ${size === "lg" ? "text-2xl" : "text-lg"}`}>
      <ErrorBoundaryKatex latex={latex} />
    </div>
  );
}

class ErrorBoundaryKatex extends React.Component<{ latex: string }, { hasError: boolean }> {
  state = { hasError: false };

  static getDerivedStateFromError() {
    return { hasError: true };
  }

  componentDidUpdate(prevProps: { latex: string }) {
    if (prevProps.latex !== this.props.latex && this.state.hasError) {
      this.setState({ hasError: false });
    }
  }

  render() {
    if (this.state.hasError) {
      return <span className="font-mono text-slate-300">{this.props.latex}</span>;
    }
    return (
      <BlockMath
        math={this.props.latex}
        errorColor="#ff6b6b"
        renderError={() => <span className="font-mono text-slate-300">{this.props.latex}</span>}
      />
    );
  }
}
