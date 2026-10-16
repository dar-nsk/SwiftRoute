"""
FastAPI application entry-point for the AI Fleet Routing API.
"""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.routers import routing, vrp
from app.services import graph_service, ml_predictor

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(name)s  %(message)s",
)
logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Lifespan (startup / shutdown)
# ---------------------------------------------------------------------------

@asynccontextmanager
async def lifespan(app: FastAPI):
    # ---- Startup -----------------------------------------------------------
    logger.info("Starting AI Fleet Routing API …")
    try:
        await graph_service.initialize_graph()
        logger.info("Road-network graph ready.")
    except Exception as exc:
        logger.error("Graph initialisation failed: %s", exc)

    try:
        ml_predictor.load_model()
        if ml_predictor._model is not None:
            logger.info("ML travel-time model loaded.")
        else:
            logger.warning("ML model not found; falling back to congestion lookup tables.")
    except Exception as exc:
        logger.error("ML model loading failed: %s", exc)

    logger.info("Startup complete.  Serving at http://%s:%s", settings.host, settings.port)
    yield

    # ---- Shutdown ----------------------------------------------------------
    logger.info("Shutting down AI Fleet Routing API …")


# ---------------------------------------------------------------------------
# App instance
# ---------------------------------------------------------------------------

app = FastAPI(
    title="AI Fleet Routing API",
    description=(
        "AI-Powered Optimal Path & Fleet Routing System with ML-predicted "
        "travel times, multi-objective optimisation, and Genetic Algorithm VRP."
    ),
    version="1.0.0",
    lifespan=lifespan,
)

# ---------------------------------------------------------------------------
# CORS
# ---------------------------------------------------------------------------

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------------------------------------------------------
# Routers
# ---------------------------------------------------------------------------

app.include_router(routing.router)
app.include_router(vrp.router)


# ---------------------------------------------------------------------------
# Root
# ---------------------------------------------------------------------------

@app.get("/")
async def root():
    """Landing page — quick links for humans and machines."""
    return {
        "name": "AI Fleet Routing API",
        "version": "1.0.0",
        "docs": "/docs",
        "redoc": "/redoc",
        "health": "/api/health",
        "endpoints": {
            "single_route": "POST /api/route",
            "route_modes": "GET /api/route/modes",
            "fleet_vrp": "POST /api/vrp",
            "vrp_demo": "GET /api/vrp/demo",
        },
    }
