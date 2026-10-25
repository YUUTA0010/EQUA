"""
EquationLens backend — FastAPI application entrypoint.

Run locally:
    cd backend
    pip install -r requirements.txt
    uvicorn main:app --reload --port 8000

The app is fully functional without any external API keys or services
(spec section 28, DEMO MODE): OCR gracefully degrades if tesseract isn't
installed, and AI explanations fall back to a deterministic template engine
if OPENAI_API_KEY is not set.
"""
from __future__ import annotations

import logging
import os
import sys
import time
from pathlib import Path

# Ensure backend directory is in sys.path so modules resolve correctly regardless of CWD
BACKEND_DIR = Path(__file__).resolve().parent
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from dotenv import load_dotenv

# Load .env from backend directory or project root
load_dotenv(BACKEND_DIR / ".env")
load_dotenv()

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from starlette.exceptions import HTTPException as StarletteHTTPException

from utils.security import RateLimiter
from api import routes_equations, routes_documents, routes_projects

HOST = os.environ.get("HOST", "127.0.0.1")
PORT = int(os.environ.get("PORT", "8000"))
MAX_UPLOAD_MB = float(os.environ.get("MAX_UPLOAD_MB", "15"))
RATE_LIMIT_PER_MINUTE = int(os.environ.get("RATE_LIMIT_PER_MINUTE", "120"))
CORS_ORIGINS = [o.strip() for o in os.environ.get(
    "CORS_ORIGINS", "http://localhost:5173,http://127.0.0.1:5173,http://localhost:8000,http://127.0.0.1:8000,http://localhost:8080,http://127.0.0.1:8080"
).split(",") if o.strip()]

app = FastAPI(
    title="EquationLens API",
    description="Turns equations into meaning: classification, symbolic analysis, "
                "and interactive visualization data.",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

_rate_limiter = RateLimiter(per_minute=RATE_LIMIT_PER_MINUTE)


@app.middleware("http")
async def rate_limit_middleware(request: Request, call_next):
    client_ip = request.client.host if request.client else "unknown"
    if request.url.path.startswith("/api/") and not _rate_limiter.allow(client_ip):
        return JSONResponse(status_code=429, content={
            "detail": "Too many requests. Please slow down and try again in a moment."
        })
    start = time.time()
    response = await call_next(request)
    response.headers["X-Process-Time-ms"] = str(round((time.time() - start) * 1000, 1))
    return response


@app.exception_handler(Exception)
async def catch_all_handler(request: Request, exc: Exception):
    if isinstance(exc, StarletteHTTPException):
        return JSONResponse(status_code=exc.status_code, content={"detail": exc.detail})
    if isinstance(exc, RequestValidationError):
        return JSONResponse(status_code=422, content={"detail": exc.errors()})
    logging.error("Unhandled error processing %s %s: %s", request.method, request.url.path, exc, exc_info=True)
    # Never leak raw stack traces / internals to the client (spec section 15 & 29).
    return JSONResponse(status_code=500, content={
        "detail": "Something went wrong while processing that request. Please try again, "
                  "or check whether the equation notation needs adjusting."
    })


@app.get("/api/health")
def health():
    openai_configured = bool(os.environ.get("OPENAI_API_KEY", "").strip())
    try:
        import pytesseract  # noqa: F401
        tesseract_available = True
    except Exception:  # noqa: BLE001
        tesseract_available = False
    return {
        "status": "ok",
        "ai_explanations": "openai" if openai_configured else "template_fallback",
        "ocr_available": tesseract_available,
        "max_upload_mb": MAX_UPLOAD_MB,
    }


app.include_router(routes_equations.router)
app.include_router(routes_documents.router)
app.include_router(routes_projects.router)

FRONTEND_DIST = BACKEND_DIR.parent / "frontend" / "dist"
if FRONTEND_DIST.exists() and (FRONTEND_DIST / "index.html").exists():
    if (FRONTEND_DIST / "assets").exists():
        app.mount("/assets", StaticFiles(directory=str(FRONTEND_DIST / "assets")), name="assets")

    @app.get("/")
    async def serve_index():
        return FileResponse(FRONTEND_DIST / "index.html")

    @app.get("/{full_path:path}")
    async def serve_spa(full_path: str):
        if full_path.startswith("api/"):
            return JSONResponse(status_code=404, content={"detail": "Not Found"})
        file_path = FRONTEND_DIST / full_path
        if file_path.is_file():
            return FileResponse(file_path)
        return FileResponse(FRONTEND_DIST / "index.html")
else:
    @app.get("/")
    async def index_fallback():
        return HTMLResponse("""
        <!DOCTYPE html>
        <html>
        <head><title>EquationLens API</title></head>
        <body style="font-family: sans-serif; padding: 2rem;">
            <h1>EquationLens API is running</h1>
            <p>API documentation is available at <a href="/docs">/docs</a>.</p>
            <p>To run the frontend UI: <code>cd frontend && npm run dev</code>, then open <a href="http://localhost:5173">http://localhost:5173</a>.</p>
        </body>
        </html>
        """)


if __name__ == "__main__":
    import uvicorn
    print("\n========================================================")
    print(" EquationLens Server Starting")
    print(f" -> Localhost: http://127.0.0.1:{PORT}")
    print(f" -> Alias:     http://localhost:{PORT}")
    print("========================================================\n")
    uvicorn.run("main:app", host=HOST, port=PORT, reload=True, app_dir=str(BACKEND_DIR))
