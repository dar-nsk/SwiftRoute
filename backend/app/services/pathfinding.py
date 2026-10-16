"""
Pathfinding service: global routing via OSRM public API with ML-predicted
dynamic travel time adjustments layered on top.

OSRM covers the entire world, so any two coordinates on any road network work
(India, Europe, Americas, etc.).  The ML model then scales the raw OSRM travel
time by predicted congestion and weather factors.
"""

import logging
import math
import httpx

from fastapi import HTTPException

from app.services import ml_predictor

logger = logging.getLogger(__name__)

# Public OSRM demo server — covers the whole world, no API key needed.
OSRM_BASE = "http://router.project-osrm.org"

# Congestion lookup (hour → multiplier) — kept here for the eco/toll modes
CONGESTION_FACTORS: dict[int, float] = {
    0: 0.7, 1: 0.8, 2: 0.8, 3: 0.7, 4: 0.7, 5: 0.8, 6: 0.9,
    7: 1.8, 8: 1.9, 9: 1.7, 10: 1.3, 11: 1.2, 12: 1.2, 13: 1.1,
    14: 1.1, 15: 1.3, 16: 1.8, 17: 1.9, 18: 1.7, 19: 1.4,
    20: 1.2, 21: 1.0, 22: 0.9, 23: 0.8,
}

WEATHER_FACTORS: dict[int, float] = {
    0: 1.0,   # clear
    1: 1.25,  # rain
    2: 1.55,  # snow
}


# ---------------------------------------------------------------------------
# Geometry helpers
# ---------------------------------------------------------------------------

def haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Great-circle distance in metres."""
    R = 6_371_000.0
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2) ** 2
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


def compute_fuel(distance_m: float, grade: float = 0.0) -> float:
    """Fuel consumption in litres."""
    distance_km = distance_m / 1000.0
    base_rate = 0.08
    grade_penalty = max(0.0, grade) * 0.02
    return distance_km * (base_rate + grade_penalty)


# ---------------------------------------------------------------------------
# OSRM helpers
# ---------------------------------------------------------------------------

def _decode_polyline(encoded: str) -> list[list[float]]:
    """Decode a Google-style encoded polyline into [[lat, lon], ...] pairs."""
    coords = []
    index = 0
    lat = 0
    lon = 0
    while index < len(encoded):
        for is_lon in (False, True):
            result = 0
            shift = 0
            while True:
                b = ord(encoded[index]) - 63
                index += 1
                result |= (b & 0x1F) << shift
                shift += 5
                if b < 0x20:
                    break
            delta = ~(result >> 1) if result & 1 else result >> 1
            if is_lon:
                lon += delta
                coords.append([lat / 1e5, lon / 1e5])
            else:
                lat += delta
    return coords


async def _osrm_route(
    origin_lat: float, origin_lon: float,
    dest_lat: float, dest_lon: float,
    alternatives: bool = False,
) -> dict:
    """
    Call OSRM route API and return the best route dict with keys:
      distance_m, duration_sec, geometry ([[lat,lon], ...])
    """
    url = (
        f"{OSRM_BASE}/route/v1/driving/"
        f"{origin_lon},{origin_lat};{dest_lon},{dest_lat}"
        f"?overview=full&geometries=polyline&alternatives={'true' if alternatives else 'false'}"
    )
    async with httpx.AsyncClient(timeout=15.0) as client:
        try:
            resp = await client.get(url)
            resp.raise_for_status()
        except httpx.TimeoutException:
            raise HTTPException(status_code=503, detail="OSRM routing service timed out.")
        except httpx.HTTPStatusError as e:
            raise HTTPException(status_code=502, detail=f"OSRM error: {e.response.status_code}")
        except Exception as e:
            raise HTTPException(status_code=502, detail=f"OSRM unreachable: {e}")

    data = resp.json()
    if data.get("code") != "Ok" or not data.get("routes"):
        raise HTTPException(
            status_code=404,
            detail="No route found between the selected points. Try points on actual roads.",
        )
    route = data["routes"][0]
    geometry = _decode_polyline(route["geometry"])
    return {
        "distance_m": route["distance"],
        "duration_sec": route["duration"],
        "geometry": geometry,
    }


# ---------------------------------------------------------------------------
# ML adjustment
# ---------------------------------------------------------------------------

def _apply_ml_adjustment(
    base_duration_sec: float,
    distance_m: float,
    hour: int,
    day_of_week: int,
    weather_code: int,
    mode: str,
) -> float:
    """
    Adjust OSRM's base travel time using the ML model + congestion + weather.
    Returns the adjusted travel time in seconds.
    """
    congestion = CONGESTION_FACTORS.get(hour, 1.0)
    weather = WEATHER_FACTORS.get(weather_code, 1.0)

    if mode == "fastest":
        # Use ML model for fine-grained prediction
        speed_kph = (distance_m / 1000) / (base_duration_sec / 3600) if base_duration_sec > 0 else 50
        predicted = ml_predictor.predict_travel_time(
            base_duration_sec, distance_m, min(speed_kph, 130),
            hour, day_of_week, weather_code, 0.0,
        )
        return predicted

    elif mode == "eco":
        # Eco: penalise congested hours more, reward off-peak
        return base_duration_sec * congestion * weather * 0.95

    elif mode == "toll_free":
        # Toll-free: slightly longer path assumed by OSRM avoid=tolls not supported
        # on the demo server; we just adjust time by congestion only
        return base_duration_sec * congestion

    else:  # balanced
        return base_duration_sec * (0.6 * congestion + 0.4 * weather)


# ---------------------------------------------------------------------------
# Main routing function — works globally
# ---------------------------------------------------------------------------

async def astar_route(
    origin_lat: float,
    origin_lon: float,
    dest_lat: float,
    dest_lon: float,
    mode: str = "balanced",
    hour: int = 12,
    day_of_week: int = 1,
    weather_code: int = 0,
    # Legacy params kept for compatibility — ignored when using OSRM
    G=None,
    origin_node=None,
    dest_node=None,
) -> dict:
    """
    Compute an optimised route between two geographic coordinates.

    Uses OSRM for global road network routing (works anywhere in the world —
    India, USA, Europe, etc.) and applies the ML model on top to predict
    congestion-adjusted travel time.
    """
    osrm_result = await _osrm_route(origin_lat, origin_lon, dest_lat, dest_lon)

    distance_m = osrm_result["distance_m"]
    base_time = osrm_result["duration_sec"]
    coordinates = osrm_result["geometry"]

    # Apply ML-based adjustment
    adjusted_time = _apply_ml_adjustment(
        base_time, distance_m, hour, day_of_week, weather_code, mode
    )

    fuel_liters = compute_fuel(distance_m)
    co2_kg = fuel_liters * 2.31

    return {
        "coordinates": coordinates,
        "waypoints": coordinates,
        "distance_m": round(distance_m, 2),
        "time_sec": round(adjusted_time, 2),
        "fuel_liters": round(fuel_liters, 4),
        "co2_kg": round(co2_kg, 4),
        "mode": mode,
    }
