import type { DemoEquation } from "../types/equation";

export const DEMO_EQUATIONS: DemoEquation[] = [
  { equation: "F = m*a", label: "Newton's Second Law", domain_area: "physics" },
  { equation: "V = I*R", label: "Ohm's Law", domain_area: "electrical" },
  { equation: "y = x**2", label: "Quadratic Function", domain_area: "mathematics" },
  { equation: "y = A*sin(omega*t + phi)", label: "Sinusoidal Wave", domain_area: "signals" },
  { equation: "E = m*c**2", label: "Mass–Energy Equivalence", domain_area: "physics" },
  { equation: "y = A*exp(-zeta*wn*t)*sin(wd*t)", label: "Damped Oscillation", domain_area: "mechanical" },
  { equation: "v = u + a*t", label: "Kinematics — Velocity", domain_area: "mechanical" },
  { equation: "s = u*t + 0.5*a*t**2", label: "Kinematics — Position", domain_area: "mechanical" },
  { equation: "V = 5*(1 - exp(-t/(R*C)))", label: "RC Charging Circuit", domain_area: "electrical" },
  { equation: "dy/dx = k*y", label: "Exponential Growth/Decay ODE", domain_area: "engineering_mathematics" },
  { equation: "z = x**2 - y**2", label: "Saddle Surface", domain_area: "mathematics" },
  { equation: "y = m*x + c", label: "Linear Equation", domain_area: "mathematics" },
];

export const DOMAIN_LABELS: Record<string, string> = {
  mathematics: "Mathematics",
  physics: "Physics",
  electrical: "Electrical",
  mechanical: "Mechanical",
  aerospace: "Aerospace",
  control: "Control Systems",
  signals: "Signals",
  thermodynamics: "Thermodynamics",
  fluid_mechanics: "Fluid Mechanics",
  engineering_mathematics: "Engineering Mathematics",
};
