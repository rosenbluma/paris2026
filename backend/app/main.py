"""Paris 2026 Marathon Training Tracker - FastAPI Backend."""
import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.database import init_db
from app.routers import (
    plans_router,
    workouts_router,
    runs_router,
    notes_router,
    sync_router,
    stats_router,
)

# Initialize FastAPI app
app = FastAPI(
    title="Paris 2026 Marathon Tracker",
    description="Track your journey to the Paris Marathon 2026",
    version="1.0.0",
)

# CORS middleware for frontend
# Use CORS_ORIGINS env var in production, fall back to localhost for development
cors_origins = os.environ.get("CORS_ORIGINS", "http://localhost:5173,http://127.0.0.1:5173")
origins = [origin.strip() for origin in cors_origins.split(",")]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routers
app.include_router(plans_router)
app.include_router(workouts_router)
app.include_router(runs_router)
app.include_router(notes_router)
app.include_router(sync_router)
app.include_router(stats_router)


@app.on_event("startup")
async def startup():
    """Initialize database on startup."""
    init_db()


@app.get("/api/health")
async def health():
    """API health check."""
    return {"status": "healthy"}


# Serve static frontend files in production
static_dir = os.path.join(os.path.dirname(__file__), "static")
if os.path.exists(static_dir):
    from fastapi.responses import FileResponse

    # Serve static assets
    app.mount("/assets", StaticFiles(directory=os.path.join(static_dir, "assets")), name="assets")

    # Serve index.html at root
    @app.get("/")
    async def serve_root():
        """Serve frontend at root."""
        return FileResponse(os.path.join(static_dir, "index.html"))

    # Catch-all route for SPA client-side routing
    @app.get("/{full_path:path}")
    async def serve_spa(full_path: str):
        """Serve the SPA for any non-API route."""
        if full_path.startswith("api/"):
            return {"error": "Not found"}
        return FileResponse(os.path.join(static_dir, "index.html"))
else:
    # No static files - show API info
    @app.get("/")
    async def root():
        return {"status": "running", "app": "Paris 2026 Marathon Tracker", "message": "Frontend not deployed"}
