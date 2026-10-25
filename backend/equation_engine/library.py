"""
The equation library holds hand-curated metadata for well-known equations.

This is what lets EquationLens say something *meaningful* about `F = m*a`
instead of just plotting a generic function. When an uploaded/typed equation's
symbol set matches an entry here, we use this rich metadata. Otherwise we fall
back to generic structural classification (see classifier.py).

The registry is intentionally a plain list of dicts so new equations can be
added by anyone without touching the matching engine (spec: "architecture
must be extensible so new equation categories can be added later").
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional

# Each entry:
#   id: unique category id
#   category_label: human readable name
#   domain_area: mathematics | physics | electrical | mechanical | control | signals
#   dependent_candidates: symbol names that may appear alone on the LHS
#   required_symbols: symbol names (lowercased) that must ALL appear (order independent)
#   variables: dict symbol(lower) -> metadata
#   physical_interpretation: str
#   relationships: list[str]
#   visualization: primary visualization id
#   secondary_visualizations: list of {id,label,reason}
#   parameter_effect_templates: dict symbol(lower) -> {"effect": str, "explanation": str}

LIBRARY: List[Dict[str, Any]] = [
    {
        "id": "newtons_second_law",
        "category_label": "Newton's Second Law of Motion",
        "domain_area": "physics",
        "dependent_candidates": {"f", "a"},
        "required_symbols": {"f", "m", "a"},
        "variables": {
            "f": {"name": "Force", "unit": "N", "role": "parameter",
                  "description": "The net force applied to the object.",
                  "default": 10, "min": 0, "max": 100, "step": 1},
            "m": {"name": "Mass", "unit": "kg", "role": "parameter",
                  "description": "The mass of the object being accelerated.",
                  "default": 5, "min": 0.5, "max": 50, "step": 0.5},
            "a": {"name": "Acceleration", "unit": "m/s²", "role": "dependent",
                  "description": "The rate of change of velocity produced by the force (a = F/m).",
                  "default": 2, "min": 0, "max": 20, "step": 0.5},
        },
        "physical_interpretation": (
            "Newton's Second Law states that the net force acting on an object equals "
            "the product of its mass and its acceleration. It describes how an object's "
            "motion changes in response to an applied force."
        ),
        "relationships": [
            "Force is directly proportional to acceleration when mass is held constant.",
            "Force is directly proportional to mass when acceleration is held constant.",
            "For a fixed force, acceleration is inversely proportional to mass.",
        ],
        "visualization": "physics_force_block",
        "secondary_visualizations": [
            {"id": "graph2d", "label": "2D Graph", "reason": "Plot acceleration vs. force or vs. mass."},
        ],
        "parameter_effect_templates": {
            "f": {"effect": "increases", "explanation": "Increasing force while mass stays constant increases acceleration (a = F/m)."},
            "m": {"effect": "decreases", "explanation": "Increasing mass while force stays constant decreases acceleration (a = F/m)."},
        },
    },
    {
        "id": "ohms_law",
        "category_label": "Ohm's Law",
        "domain_area": "electrical",
        "dependent_candidates": {"v"},
        "required_symbols": {"v", "i", "r"},
        "variables": {
            "v": {"name": "Voltage", "unit": "V", "role": "dependent",
                  "description": "The electrical potential difference across the resistor.",
                  "default": 5, "min": 0, "max": 50, "step": 0.5},
            "i": {"name": "Current", "unit": "A", "role": "parameter",
                  "description": "The current flowing through the circuit.",
                  "default": 0.5, "min": 0, "max": 5, "step": 0.05},
            "r": {"name": "Resistance", "unit": "Ω", "role": "parameter",
                  "description": "The resistance of the component.",
                  "default": 10, "min": 1, "max": 200, "step": 1},
        },
        "physical_interpretation": (
            "Ohm's Law describes the linear relationship between voltage, current, and "
            "resistance in a simple resistive circuit: the voltage across a resistor is "
            "proportional to the current through it."
        ),
        "relationships": [
            "Voltage is directly proportional to current when resistance is fixed.",
            "Voltage is directly proportional to resistance when current is fixed.",
            "For a fixed voltage source, current decreases as resistance increases.",
        ],
        "visualization": "circuit_ohm",
        "secondary_visualizations": [
            {"id": "graph2d", "label": "V-I / I-R Graph", "reason": "Plot voltage vs current or current vs resistance."},
        ],
        "parameter_effect_templates": {
            "i": {"effect": "increases", "explanation": "Increasing current while resistance stays constant increases voltage (V = IR)."},
            "r": {"effect": "increases", "explanation": "Increasing resistance while current stays constant increases voltage (V = IR)."},
        },
    },
    {
        "id": "simple_harmonic_motion",
        "category_label": "Simple Harmonic Motion (Sinusoid)",
        "domain_area": "physics",
        "dependent_candidates": {"x", "y"},
        "required_symbols": {"a", "omega", "t", "phi"},
        "variables": {
            "x": {"name": "Displacement", "unit": "m", "role": "dependent", "description": "Position at time t."},
            "y": {"name": "Displacement", "unit": "m", "role": "dependent", "description": "Position at time t."},
            "a": {"name": "Amplitude", "unit": "m", "role": "parameter",
                  "description": "The maximum displacement from equilibrium.",
                  "default": 1, "min": 0.1, "max": 10, "step": 0.1},
            "omega": {"name": "Angular frequency (ω)", "unit": "rad/s", "role": "parameter",
                  "description": "How fast the oscillation repeats; ω = 2π/T.",
                  "default": 1, "min": 0.1, "max": 10, "step": 0.1},
            "phi": {"name": "Phase (φ)", "unit": "rad", "role": "parameter",
                    "description": "Horizontal shift of the waveform.",
                    "default": 0, "min": -3.14159, "max": 3.14159, "step": 0.05},
            "t": {"name": "Time", "unit": "s", "role": "independent", "description": "Independent time variable."},
        },
        "physical_interpretation": (
            "This equation describes simple harmonic motion — oscillation that repeats "
            "sinusoidally over time, such as a pendulum, a spring-mass system, or an AC "
            "voltage waveform."
        ),
        "relationships": [
            "Amplitude A scales the height of the wave without changing its timing.",
            "Angular frequency ω controls how many oscillations occur per unit time (period T = 2π/ω).",
            "Phase φ shifts the waveform left or right without changing its shape.",
        ],
        "visualization": "graph2d",
        "secondary_visualizations": [
            {"id": "phasor", "label": "Phasor Diagram", "reason": "Represent amplitude and phase as a rotating vector."},
        ],
        "parameter_effect_templates": {
            "a": {"effect": "scales_amplitude", "explanation": "Increasing amplitude A stretches the wave vertically — taller peaks and deeper troughs — without changing timing."},
            "omega": {"effect": "compresses_period", "explanation": "Increasing angular frequency ω compresses the wave horizontally, fitting more oscillations into the same time window (shorter period)."},
            "phi": {"effect": "shifts_phase", "explanation": "Changing phase φ slides the whole waveform left or right in time without altering its shape."},
        },
    },
    {
        "id": "damped_oscillation",
        "category_label": "Damped Harmonic Oscillation",
        "domain_area": "mechanical",
        "dependent_candidates": {"x", "y"},
        "required_symbols": {"a", "zeta", "wn", "wd", "t"},
        "variables": {
            "x": {"name": "Displacement", "unit": "m", "role": "dependent", "description": "Position at time t."},
            "y": {"name": "Displacement", "unit": "m", "role": "dependent", "description": "Position at time t."},
            "a": {"name": "Initial amplitude", "unit": "m", "role": "parameter", "default": 1, "min": 0.1, "max": 10, "step": 0.1},
            "zeta": {"name": "Damping ratio (ζ)", "unit": "-", "role": "parameter", "default": 0.15, "min": 0, "max": 1.5, "step": 0.01},
            "wn": {"name": "Natural frequency (ωₙ)", "unit": "rad/s", "role": "parameter", "default": 3, "min": 0.5, "max": 15, "step": 0.1},
            "wd": {"name": "Damped frequency (ω_d)", "unit": "rad/s", "role": "parameter", "default": 2.9, "min": 0.1, "max": 15, "step": 0.1},
            "t": {"name": "Time", "unit": "s", "role": "independent"},
        },
        "physical_interpretation": (
            "This equation models a damped oscillator: a system that oscillates while "
            "losing energy over time, such as a shock absorber, an RLC circuit, or a "
            "vibrating structure with friction."
        ),
        "relationships": [
            "The exponential term A·e^(-ζωₙt) forms an envelope that the oscillation decays within.",
            "Larger damping ratio ζ causes the oscillation to die out faster.",
            "If ζ ≥ 1 the system no longer oscillates (critically damped / overdamped).",
        ],
        "visualization": "graph2d",
        "secondary_visualizations": [],
        "parameter_effect_templates": {
            "zeta": {"effect": "faster_decay", "explanation": "Increasing damping ratio ζ makes the oscillation decay faster and, above ζ=1, removes oscillation entirely."},
            "wn": {"effect": "faster_oscillation", "explanation": "Increasing natural frequency ωₙ makes the system oscillate faster."},
        },
    },
    {
        "id": "mass_energy_equivalence",
        "category_label": "Mass–Energy Equivalence",
        "domain_area": "physics",
        "dependent_candidates": {"e"},
        "required_symbols": {"e", "m", "c"},
        "variables": {
            "e": {"name": "Energy", "unit": "J", "role": "dependent", "default": None},
            "m": {"name": "Mass", "unit": "kg", "role": "parameter", "default": 1, "min": 0, "max": 10, "step": 0.1},
            "c": {"name": "Speed of light", "unit": "m/s", "role": "constant", "default": 299792458},
        },
        "physical_interpretation": (
            "Einstein's mass–energy equivalence states that mass and energy are the same "
            "physical quantity and can be converted into each other; c² is an enormous "
            "conversion factor, so even a small mass corresponds to a huge amount of energy."
        ),
        "relationships": [
            "Energy is directly proportional to mass.",
            "Because c is squared, energy grows extremely quickly with even small increases in c — but c is a fixed constant of nature.",
        ],
        "visualization": "graph2d",
        "secondary_visualizations": [],
        "parameter_effect_templates": {
            "m": {"effect": "increases", "explanation": "Increasing mass increases energy linearly — doubling mass doubles energy."},
        },
    },
    {
        "id": "kinematics_velocity",
        "category_label": "Kinematics — Velocity under constant acceleration",
        "domain_area": "mechanical",
        "dependent_candidates": {"v"},
        "required_symbols": {"v", "u", "a", "t"},
        "variables": {
            "v": {"name": "Final velocity", "unit": "m/s", "role": "dependent"},
            "u": {"name": "Initial velocity", "unit": "m/s", "role": "parameter", "default": 0, "min": 0, "max": 50, "step": 1},
            "a": {"name": "Acceleration", "unit": "m/s²", "role": "parameter", "default": 2, "min": -20, "max": 20, "step": 0.5},
            "t": {"name": "Time", "unit": "s", "role": "independent", "default": 5, "min": 0, "max": 30, "step": 0.5},
        },
        "physical_interpretation": (
            "This is one of the SUVAT kinematics equations: it gives the velocity of an "
            "object undergoing constant acceleration after elapsed time t."
        ),
        "relationships": [
            "Velocity increases linearly with time when acceleration is constant.",
            "A larger initial velocity u shifts the whole velocity-time line upward.",
            "A larger acceleration a makes the velocity-time line steeper.",
        ],
        "visualization": "graph2d",
        "secondary_visualizations": [],
        "parameter_effect_templates": {
            "u": {"effect": "shifts_up", "explanation": "Increasing initial velocity u shifts the velocity-time graph upward (vertical offset)."},
            "a": {"effect": "increases_slope", "explanation": "Increasing acceleration a makes the velocity-time graph steeper."},
        },
    },
    {
        "id": "kinematics_position",
        "category_label": "Kinematics — Position under constant acceleration",
        "domain_area": "mechanical",
        "dependent_candidates": {"s"},
        "required_symbols": {"s", "u", "a", "t"},
        "variables": {
            "s": {"name": "Displacement", "unit": "m", "role": "dependent"},
            "u": {"name": "Initial velocity", "unit": "m/s", "role": "parameter", "default": 0, "min": 0, "max": 50, "step": 1},
            "a": {"name": "Acceleration", "unit": "m/s²", "role": "parameter", "default": 2, "min": -20, "max": 20, "step": 0.5},
            "t": {"name": "Time", "unit": "s", "role": "independent", "default": 5, "min": 0, "max": 30, "step": 0.5},
        },
        "physical_interpretation": (
            "This SUVAT equation gives the displacement of an object under constant "
            "acceleration as a function of time — a parabola in t because of the ½at² term."
        ),
        "relationships": [
            "Displacement grows quadratically with time due to the ½at² term.",
            "Larger acceleration makes displacement grow faster for the same time.",
        ],
        "visualization": "graph2d",
        "secondary_visualizations": [],
        "parameter_effect_templates": {
            "u": {"effect": "shifts", "explanation": "Increasing initial velocity u increases the initial slope of the displacement curve."},
            "a": {"effect": "increases_curvature", "explanation": "Increasing acceleration a makes the displacement curve bend upward more sharply."},
        },
    },
    {
        "id": "rc_charging",
        "category_label": "RC Circuit Charging",
        "domain_area": "electrical",
        "dependent_candidates": {"v", "vc"},
        "required_symbols": {"v", "r", "c", "t"},
        "variables": {
            "v": {"name": "Capacitor voltage", "unit": "V", "role": "dependent"},
            "r": {"name": "Resistance", "unit": "Ω", "role": "parameter", "default": 1000, "min": 100, "max": 10000, "step": 100},
            "c": {"name": "Capacitance", "unit": "F", "role": "parameter", "default": 0.001, "min": 0.0001, "max": 0.01, "step": 0.0001},
            "t": {"name": "Time", "unit": "s", "role": "independent"},
        },
        "physical_interpretation": (
            "This equation describes a capacitor charging through a resistor: voltage "
            "rises quickly at first, then approaches the supply voltage asymptotically. "
            "The time constant τ = RC controls how fast this happens."
        ),
        "relationships": [
            "Larger R or C increases the time constant τ = RC, slowing the charging process.",
            "The capacitor voltage never quite reaches the supply voltage in finite time — it asymptotically approaches it.",
        ],
        "visualization": "graph2d",
        "secondary_visualizations": [],
        "parameter_effect_templates": {
            "r": {"effect": "slower_charging", "explanation": "Increasing resistance R increases the time constant τ = RC, so the capacitor charges more slowly."},
            "c": {"effect": "slower_charging", "explanation": "Increasing capacitance C increases the time constant τ = RC, so the capacitor charges more slowly."},
        },
    },
]


def find_library_match(symbol_names_lower: set[str], dependent_name_lower: Optional[str]) -> Optional[Dict[str, Any]]:
    """Return the best-matching library entry, or None.

    Matching requires the equation's full symbol set to EXACTLY equal the
    entry's `required_symbols` (not just a superset) — this avoids, e.g., a
    plain "y = m*x" line matching Ohm's law just because 'm' is present.
    `dependent_candidates` is kept as documentation of the pedagogically
    expected dependent variable, but display roles come from each entry's
    `variables` metadata directly (see analyzer.py), so equations typed in
    either algebraic direction (F = ma or a = F/m) still match.
    Entries are tried largest-required-symbols-first so more specific
    matches win over more general ones.
    """
    candidates = sorted(LIBRARY, key=lambda e: -len(e["required_symbols"]))
    for entry in candidates:
        if entry["required_symbols"] == symbol_names_lower:
            return entry
    # fall back to subset match (equation may include extra descriptive symbols)
    for entry in candidates:
        if entry["required_symbols"].issubset(symbol_names_lower):
            return entry
    return None


def get_entry(category_id: str) -> Optional[Dict[str, Any]]:
    for e in LIBRARY:
        if e["id"] == category_id:
            return e
    return None
