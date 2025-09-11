# backend/app/main.py
import os
import sys

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Ensure project root on path (adjust if your structure differs)
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from backend.app.routes import router  # noqa: E402

APP_ENV = os.getenv("APP_ENV", os.getenv("ENV", "development")).lower()

# In prod, read comma-separated origins from ALLOW_ORIGINS
# e.g. ALLOW_ORIGINS="https://yourapp.com,https://admin.yourapp.com"
if APP_ENV in ("production", "prod"):
    _raw = os.getenv("ALLOW_ORIGINS", "")
    ALLOW_ORIGINS = [o.strip() for o in _raw.split(",") if o.strip()]
    # Sensible fallback to local dev frontend if not provided
    if not ALLOW_ORIGINS:
        ALLOW_ORIGINS = ["http://localhost:3000", "http://127.0.0.1:3000"]
else:
    # Development: be permissive to avoid CORS pain
    ALLOW_ORIGINS = ["*"]

app = FastAPI(
    title="Tutor API",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOW_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],   # GET, POST, PUT, PATCH, DELETE, OPTIONS
    allow_headers=["*"],   # Authorization, Content-Type, etc.
)

# Mount application routes
app.include_router(router)

# Optional: lightweight health check
@app.get("/health", tags=["health"])
def health():
    return {"status": "ok", "env": APP_ENV}

if __name__ == "__main__":
    # Run with: python -m backend.app.main
    import uvicorn

    # Bind to all interfaces so LAN/IP access works (and CORS origin matching can succeed)
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", "8000"))
    reload_flag = os.getenv("RELOAD", "true").lower() == "true" and APP_ENV != "production"

    uvicorn.run("backend.app.main:app", host=host, port=port, reload=reload_flag)
