"""
FastAPI Application Entry Point for Free Learning Path Builder
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .config import settings
from .database import engine, Base
from .routers import learning_paths, actions, calendar, test_runs

# Create database tables automatically
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Free Learning Path Builder API",
    description="Agentic workflow backend for generating verified, free, prerequisite-aware learning paths.",
    version="1.0.0"
)

# CORS configuration
cors_origins_raw = getattr(settings, "CORS_ORIGINS", "*")
cors_origins = [o.strip() for o in cors_origins_raw.split(",") if o.strip()] if cors_origins_raw != "*" else ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True if cors_origins != ["*"] else False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include Routers
app.include_router(learning_paths.router)
app.include_router(actions.router)
app.include_router(calendar.router)
app.include_router(test_runs.router)

@app.get("/api/health")
def health_check():
    return {
        "status": "healthy",
        "service": "Free Learning Path Builder API",
        "llm_provider": settings.LLM_PROVIDER,
        "database": settings.DATABASE_URL
    }

# Mount built frontend if available
import os
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pathlib import Path

frontend_dist = Path(__file__).resolve().parent.parent.parent / "frontend" / "dist"
if frontend_dist.exists():
    app.mount("/assets", StaticFiles(directory=str(frontend_dist / "assets")), name="assets")

    @app.get("/{full_path:path}")
    async def serve_spa(full_path: str):
        if full_path.startswith("api/"):
            return {"error": "API route not found"}
        target = frontend_dist / full_path
        if target.exists() and target.is_file():
            return FileResponse(target)
        return FileResponse(frontend_dist / "index.html")
else:
    @app.get("/")
    def root_health():
        return {
            "status": "healthy",
            "service": "Free Learning Path Builder API",
            "llm_provider": settings.LLM_PROVIDER,
            "database": settings.DATABASE_URL,
            "frontend": "Frontend dev server can be started with 'npm run dev' inside frontend/"
        }

