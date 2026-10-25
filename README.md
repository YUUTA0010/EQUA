# EquationLens

> **Don't just solve the equation. Show what the equation means.**

EquationLens turns a typed, pasted, or scanned equation into a structured
understanding of what it *is* (classification, variables, units, physical
meaning) and an interactive visualization of what it *does* — with sliders
you can drag to see cause and effect in real time.

This is a working MVP built around the priority list in the product spec
(section 30): upload → OCR → equation editor → classification → 2D graph →
parameter sliders → AI explanation → "what changes what" → save. Several
higher-tier visualizations (3D surfaces, ODE slope fields, projectile
motion, a control-systems step-response demo) are also implemented on top
of that core. See **[Roadmap](#roadmap--whats-not-built-yet)** for what's
intentionally deferred.

---

## Architecture

```
equationlens/
├── backend/                     FastAPI + SymPy/NumPy/SciPy
│   ├── main.py                  App entrypoint, CORS, rate limiting
│   ├── api/                     HTTP routes
│   ├── equation_engine/         parse → classify → analyze (deterministic)
│   │   ├── parser.py            safe text → SymPy expression
│   │   ├── library.py           curated known-equation metadata (extensible)
│   │   ├── classifier.py        library match + structural fallback
│   │   └── analyzer.py          builds the full structured EquationAnalysis
│   ├── visualization_engine/    numeric computation for every chart/scene
│   │   ├── compute.py           graph2d, 3D surface, physics scenes, ODE, etc.
│   │   └── selector.py          routes equation+viz_id → compute function
│   ├── document_processor/      PDF/DOCX/image text extraction + OCR
│   ├── ai/                      OpenAI explanation service + template fallback
│   ├── storage/                 JSON-file persistence for saved items/projects
│   ├── models/                  Pydantic schemas (the AI/API JSON contract)
│   └── utils/security.py        safe expression parsing, upload validation, rate limiting
└── frontend/                    React + TypeScript + Vite + Tailwind
    └── src/
        ├── components/
        │   ├── equation/        equation display, variable list, parameter
        │   │                    explorer, what-if panel, change-one-thing,
        │   │                    compare view, the two big explain buttons
        │   ├── document/        upload dropzone, detected-equation list w/ correction
        │   ├── layout/          sidebar, top bar
        │   └── visualizations/  Graph2D, 3D surface, physics force-block,
        │                        circuit diagram, projectile, slope field,
        │                        control-systems step response + router
        ├── hooks/useEquationWorkspace.ts   core state: analyze → params → visualize
        ├── api/client.ts        typed API client
        └── pages/               Home, Upload, Library, Workspace, Saved, Projects, Settings
```

### The pipeline (spec section 13)

```
Document/Image/Text → OCR/Parser → Equation Detection → LaTeX
   → Classification → Symbolic Math Engine (SymPy) → Visualization Selection
   → Visualization Renderer (Plotly/SVG/Canvas) → AI Explanation (optional)
```

**Every number on screen comes from SymPy/NumPy/SciPy, never from the AI.**
The AI layer (`backend/ai/explain_service.py`) only ever rephrases facts
that were already computed deterministically — and if no `OPENAI_API_KEY`
is set, a template engine produces the explanation instead, so the whole
app works with zero external services (see **Demo Mode** below).

---

## Quick start

Requires **Python 3.10+** and **Node 18+**.

### 1. Backend

```bash
cd backend
python3 -m venv .venv && source .venv/bin/activate   # optional but recommended
pip install -r requirements.txt
cp ../.env.example .env      # all values are optional — see below
uvicorn main:app --reload --port 8000
```

OCR needs the **tesseract** binary on your system (not a pip package):

```bash
# Debian/Ubuntu
sudo apt-get install tesseract-ocr
# macOS
brew install tesseract
```

If it's not installed, the app still runs — image OCR requests return a
clear error message instead of crashing, and you can still use "Paste
Equation" or type equations directly.

### 2. Frontend

```bash
cd frontend
npm install
npm run dev
```

Open **http://localhost:5173**. Vite proxies `/api/*` to `http://localhost:8000`
(see `vite.config.ts`), so both servers just need to be running side by side.

### 3. Try it

- Home page → click any example card, or type `F = m*a` and hit "Visualize an Equation".
- Upload page → drop a PDF/image of a textbook page, or paste a block of text containing equations.
- Workspace → drag the parameter sliders and watch the visualization update live; try
  "WHAT DOES THIS EQUATION DO?", "CHANGE ONE THING", and "COMPARE".

---

## Demo Mode (no API keys required)

Everything above runs with an **empty `.env`**:

| Feature | With API key / service | Without (demo mode) |
|---|---|---|
| Equation classification, variables, units, math | — | Always deterministic (SymPy) — no key needed at all |
| Visualization data | — | Always deterministic (NumPy/SciPy) — no key needed at all |
| "What does this do?" / "Why does it look like that?" prose | OpenAI (`OPENAI_API_KEY`) | Built-in template engine (`ai/explain_service.py`) — factually grounded, just less varied in phrasing |
| Image/scanned-PDF OCR | `tesseract-ocr` installed | Clear error message; PDF text-layer extraction and "Paste Equation" still work |

The 12 demo equations in `GET /api/equations/library` (Newton's Second Law,
Ohm's Law, a quadratic, SHM, mass-energy equivalence, damped oscillation,
two kinematics equations, an RC circuit, a first-order ODE, a saddle
surface, and a generic linear equation) are always available and don't
require any upload.

---

## Security notes (spec section 15)

- **No `eval`/`exec` on user input, ever.** `utils/security.py::safe_parse_expr`
  parses equation text through SymPy's tokenizer with an explicit whitelist
  of function/constructor names — nothing else is reachable from the string.
- File uploads are validated by extension + content-type + size before
  touching disk; temp files are deleted immediately after extraction
  (`api/routes_documents.py`).
- A simple in-memory per-IP rate limiter guards every endpoint (`main.py`).
- All unhandled exceptions are caught by a global handler that returns a
  generic message — raw stack traces are never sent to the client.
- The OpenAI key lives only in `backend/.env` and is never sent to the
  frontend; the frontend never talks to OpenAI directly.

---

## Roadmap / what's not built yet

Per the spec's own MVP guidance (section 30: *"do not attempt to build
every possible visualization before the core experience works"*), this
build focuses on making the core loop excellent rather than covering all
25 visualization types shallowly. Implemented now:

2D graphs • 3D surfaces • physics force-block scenes • circuit (Ohm's Law)
diagrams • projectile motion (animated) • ODE slope fields + solution
curves • a 2nd-order control-system step response + pole plot (bonus
"Engineering Mode" preview).

Deferred, with the architecture already set up to add them (new entries in
`equation_engine/library.py` + a new function in `visualization_engine/compute.py`
+ a new component in `components/visualizations/` + a case in
`VisualizationRouter.tsx`):

- Bode / Nyquist / root-locus plots, vector fields, phasor diagrams, matrix/
  eigenvector transformations, mechanism/linkage animations, heatmaps.
- Automatic multi-equation "Equation Chain" detection across a document
  (section 10) — the data model supports it; the graph-building/traversal
  logic is not yet implemented.
- Higher-order and partial differential equations (only first-order ODEs
  are symbolically handled today).
- Math-aware OCR (Mathpix-style) for fractions/subscripts/integrals — the
  current OCR pipeline (Tesseract) handles printed single-line equations
  well but struggles with dense notation; the "Edit Equation" correction
  flow exists specifically to make this a non-blocker.
- User accounts/auth — projects and saved items are currently local to the
  machine running the backend (JSON-file storage), by design for a local
  MVP.

---

## Tech stack

**Frontend:** React 18, TypeScript, Vite, Tailwind CSS, Plotly.js (2D/3D),
KaTeX, React Router, Axios, lucide-react.

**Backend:** FastAPI, SymPy, NumPy, SciPy, PyMuPDF (PDF), python-docx,
pytesseract (OCR), OpenAI SDK (optional).
