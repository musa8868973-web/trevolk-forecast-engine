"""
app/main.py
===========
Trevolk Forecasting Engine — Application Entry Point

Responsibilities:
  - Create and configure the FastAPI application instance.
  - Register CORS middleware for the Next.js frontend.
  - Include API routers.
  - Run lifespan events (model warm-up on startup).

Run:
    uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
"""

import logging
from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.endpoints import router
from app.services.ml_service import MLService

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("trevolk.main")


# ---------------------------------------------------------------------------
# Lifespan — warm-up the ML singleton before the first request arrives
# ---------------------------------------------------------------------------
@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Startup: eagerly initialise the MLService singleton so the model is
    already in memory before any request hits the /api/predict endpoint.
    Shutdown: nothing to clean up (joblib models are stateless readers).
    """
    logger.info("=== Trevolk Forecasting Engine starting up ===")
    service = MLService.get_instance()
    service.load_model()          # idempotent — safe to call multiple times
    logger.info("=== Model warm-up complete. Ready to serve. ===")
    yield
    logger.info("=== Trevolk Forecasting Engine shut down. ===")


# ---------------------------------------------------------------------------
# FastAPI Application
# ---------------------------------------------------------------------------
app = FastAPI(
    title="Trevolk Forecasting Engine",
    description=(
        "Production-grade REST API that serves a trained XGBoost regression model "
        "for 7-day Rossmann store-sales forecasting."
    ),
    version="2.0.0",
    contact={
        "name": "Trevolk Engineering",
        "email": "engineering@trevolk.ai",
    },
    license_info={"name": "Proprietary"},
    lifespan=lifespan,
)

# ---------------------------------------------------------------------------
# CORS Middleware
# Allows the Next.js frontend (localhost:3000) to call this API.
# Add your production domain to `allow_origins` before deploying.
# ---------------------------------------------------------------------------
ALLOWED_ORIGINS = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    # "https://trevolk.example.com",  # <-- add production domain here
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------------------------------------------------------
# Routers
# ---------------------------------------------------------------------------
app.include_router(router, prefix="/api", tags=["Forecast"])


# ---------------------------------------------------------------------------
# Root / Health
# ---------------------------------------------------------------------------
@app.get("/", tags=["Health"], summary="Service root")
def root():
    return {"service": "Trevolk Forecasting Engine", "version": "2.0.0", "status": "ok"}


@app.get("/health", tags=["Health"], summary="Readiness probe")
def health():
    """Returns whether the ML model is loaded and the service is ready."""
    model_ready = MLService.get_instance().is_ready()
    return {
        "status": "healthy" if model_ready else "degraded",
        "model_loaded": model_ready,
    }


# ---------------------------------------------------------------------------
# Entry Point
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,       # Set reload=False in production
        log_level="info",
    )
