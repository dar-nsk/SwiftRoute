"""
Routing router: single-route calculation endpoints.
"""

import logging

from fastapi import APIRouter, HTTPException

from app.models.schemas import HealthResponse, RouteRequest, RouteResponse
from app.services import graph_service, ml_predictor, pathfinding

# Note: graph_service is used only for the health endpoint; routing now uses OSRM globally.

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["routing"])


# ---------------------------------------------------------------------------
# Health
# ---------------------------------------------------------------------------

@router.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint returning graph and model status."""
    try:
        G = graph_service.get_graph()
        graph_loaded = True
        node_count = G.number_of_nodes()
        edge_count = G.number_of_edges()
    except HTTPException:
        graph_loaded = False
        node_count = 0
        edge_count = 0

    model_loaded = ml_predictor._model is not None

    return HealthResponse(
        status="ok" if graph_loaded else "degraded",
        graph_loaded=graph_loaded,
        model_loaded=model_loaded,
        city=graph_service.settings.city_name,
        node_count=node_count,
        edge_count=edge_count,
    )


# ---------------------------------------------------------------------------
# Modes
# ---------------------------------------------------------------------------

@router.get("/route/modes")
async def get_modes():
    """Return available optimisation modes with descriptions."""
    return {
        "modes": [
            {
                "id": "fastest",
                "name": "Fastest Route",
                "icon": "fast",
                "description": "Minimises predicted travel time using ML model",
            },
            {
                "id": "eco",
                "name": "Eco / Fuel-Efficient",
                "icon": "eco",
                "description": "Minimises fuel consumption, avoids steep grades and congestion",
            },
            {
                "id": "toll_free",
                "name": "Toll-Free",
                "icon": "toll_free",
                "description": "Avoids toll roads, minimises financial cost",
            },
            {
                "id": "balanced",
                "name": "Balanced",
                "icon": "balanced",
                "description": "Balances time and distance for overall efficiency",
            },
        ]
    }


# ---------------------------------------------------------------------------
# Route calculation
# ---------------------------------------------------------------------------

@router.post("/route", response_model=RouteResponse)
async def calculate_route(request: RouteRequest):
    """Calculate the optimal route between two points using global OSRM routing.

    Works for any coordinates worldwide (India, USA, Europe, etc.).
    ML model adjusts travel time for congestion, weather, and time-of-day.
    """
    logger.info(
        "Route request: origin=(%s,%s) dest=(%s,%s) mode=%s hour=%d",
        request.origin.lat, request.origin.lon,
        request.destination.lat, request.destination.lon,
        request.mode, request.hour,
    )

    result = await pathfinding.astar_route(
        origin_lat=request.origin.lat,
        origin_lon=request.origin.lon,
        dest_lat=request.destination.lat,
        dest_lon=request.destination.lon,
        mode=request.mode,
        hour=request.hour,
        day_of_week=request.day_of_week,
        weather_code=request.weather_code,
    )

    return RouteResponse(**result)
