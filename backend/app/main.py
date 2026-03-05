"""FastAPI application entry point."""
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app.api import health, scans
from app.config import get_settings


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Ensure upload directory exists on startup."""
    settings = get_settings()
    settings.upload_dir.mkdir(parents=True, exist_ok=True)
    yield
    # Optional: cleanup old uploads on shutdown


app = FastAPI(
    title="Security Scanning App",
    description="Scan code, Docker images, and infrastructure configs for security, cost, and performance issues.",
    version="0.1.0",
    lifespan=lifespan,
)

# CORS - allow all in production (Render, custom domains)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# API routes under /api prefix (for frontend fetch('/api/...'))
app.include_router(health.router, prefix="/api")
app.include_router(scans.router, prefix="/api")

# Static files and SPA fallback (must be after API routes)
STATIC_DIR = Path(__file__).resolve().parent.parent / "static"
if STATIC_DIR.exists():
    app.mount("/assets", StaticFiles(directory=STATIC_DIR / "assets"), name="assets")

    @app.get("/{full_path:path}")
    async def serve_spa(full_path: str):
        """Serve frontend SPA - static files or index.html for client-side routing."""
        if full_path.startswith("api/"):
            from fastapi import HTTPException
            raise HTTPException(404)
        file_path = STATIC_DIR / full_path
        if file_path.is_file():
            return FileResponse(file_path)
        return FileResponse(STATIC_DIR / "index.html")
