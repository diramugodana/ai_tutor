# backend/main_optimized.py
"""
Optimized FastAPI backend with caching, parallel processing, and performance monitoring.
"""
import os
import sys
import time
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.gzip import GZipMiddleware

# Ensure project root on path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from backend.app.routes_optimized import router  # Use optimized routes

APP_ENV = os.getenv("APP_ENV", os.getenv("ENV", "development")).lower()

# CORS Configuration
if APP_ENV in ("production", "prod"):
    _raw = os.getenv("ALLOW_ORIGINS", "")
    ALLOW_ORIGINS = [o.strip() for o in _raw.split(",") if o.strip()]
    if not ALLOW_ORIGINS:
        ALLOW_ORIGINS = ["http://localhost:3000", "http://127.0.0.1:3000"]
else:
    ALLOW_ORIGINS = ["*"]

app = FastAPI(
    title="Tutor API (Optimized)",
    version="2.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    description="AI Tutor with caching, parallel processing, and performance optimizations",
)

# Add GZip compression middleware for faster responses
app.add_middleware(GZipMiddleware, minimum_size=1000)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOW_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# -------- Request/Response Timing Middleware --------
@app.middleware("http")
async def add_timing_header(request, call_next):
    """Add response time and cache status to response headers."""
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    response.headers["X-Process-Time"] = str(process_time)
    return response

# Include routes
app.include_router(router)


@app.on_event("startup")
def startup_info():
    redis_url = os.getenv("REDIS_URL") or os.getenv("REDIS_SERVER")
    if redis_url:
        print(f"Using Redis cache at: {redis_url}")
    else:
        print("Running without Redis; using in-memory cache (not shared across processes)")

# -------- Health & Status Endpoints --------
@app.get("/health", tags=["status"])
def health():
    """Health check endpoint."""
    return {"status": "ok", "env": APP_ENV, "version": "2.0.0"}

@app.get("/status", tags=["status"])
def status():
    """Detailed status including optimization info."""
    return {
        "status": "healthy",
        "optimizations_enabled": [
            "query_caching (10 min TTL)",
            "parallel_revision_processing",
            "reduced_token_budgets",
            "gzip_compression",
            "response_timing_monitoring",
        ],
        "model": "gpt-4o-mini (fast)",
        "cache_ttl_seconds": 600,
        "max_parallel_questions": 5,
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, workers=1)
