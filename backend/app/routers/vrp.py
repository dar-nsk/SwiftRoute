"""
VRP router: multi-vehicle fleet routing endpoints using OSRM for global routing.
"""

import logging

from fastapi import APIRouter, HTTPException
import httpx

from app.models.schemas import VehicleStat, VRPRequest, VRPResponse, VRPDelivery, LatLon
from app.services import graph_service, vrp_solver
from app.services.pathfinding import _osrm_route, _decode_polyline

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["vrp"])


async def _get_route_coords(lat1, lon1, lat2, lon2) -> list:
    """Get road-following coordinates between two points via OSRM."""
    try:
        result = await _osrm_route(lat1, lon1, lat2, lon2)
        return result["geometry"]
    except Exception:
        # Fallback: straight line
        return [[lat1, lon1], [lat2, lon2]]


@router.post("/vrp", response_model=VRPResponse)
async def solve_fleet_routing(request: VRPRequest):
    """Solve a multi-vehicle routing problem using OSRM for global road routing.

    Works for any city worldwide. Uses OSRM travel times for the GA cost function.
    """
    # Build list of all stops: depot + deliveries as (lat, lon) tuples
    all_points = [(request.depot.lat, request.depot.lon)] + [
        (d.lat, d.lon) for d in request.deliveries
    ]
    n = len(all_points)

    # Build a cost matrix (travel time in seconds) via OSRM for each pair
    logger.info("Building %dx%d cost matrix via OSRM …", n, n)
    cost_matrix = [[0.0] * n for _ in range(n)]
    for i in range(n):
        for j in range(n):
            if i != j:
                try:
                    result = await _osrm_route(
                        all_points[i][0], all_points[i][1],
                        all_points[j][0], all_points[j][1],
                    )
                    cost_matrix[i][j] = result["duration_sec"]
                except Exception:
                    # Use haversine fallback at 50kph
                    from app.services.pathfinding import haversine_distance
                    d = haversine_distance(
                        all_points[i][0], all_points[i][1],
                        all_points[j][0], all_points[j][1],
                    )
                    cost_matrix[i][j] = (d / 1000) / 50 * 3600

    # Run simple GA on the cost matrix (index-based, no graph needed)
    import random, math

    depot_idx = 0
    delivery_indices = list(range(1, n))
    num_vehicles = request.num_vehicles

    def route_cost(perm):
        routes = split(perm, num_vehicles)
        total = 0.0
        for r in routes:
            full = [depot_idx] + r + [depot_idx]
            for a, b in zip(full[:-1], full[1:]):
                total += cost_matrix[a][b]
        return total

    def split(perm, k):
        size = len(perm)
        base = size // k
        rem = size % k
        routes, idx = [], 0
        for i in range(k):
            chunk = base + (1 if i < rem else 0)
            routes.append(perm[idx:idx+chunk])
            idx += chunk
        return routes

    def ox(p1, p2):
        size = len(p1)
        if size < 2:
            return p1[:]
        s, e = sorted(random.sample(range(size), 2))
        child = [None] * size
        child[s:e+1] = p1[s:e+1]
        copied = set(child[s:e+1])
        fill = (e + 1) % size
        for g in p2:
            if g not in copied:
                child[fill] = g
                copied.add(g)
                fill = (fill + 1) % size
        return child

    POP, GEN, MUT = 80, 150, 0.05
    pop = [random.sample(delivery_indices, len(delivery_indices)) for _ in range(POP)]
    best = min(pop, key=route_cost)
    best_cost = route_cost(best)

    for _ in range(GEN):
        fits = [route_cost(ind) for ind in pop]
        ranked = sorted(range(POP), key=lambda i: fits[i])
        elites = [pop[i][:] for i in ranked[:max(1, POP//10)]]
        if fits[ranked[0]] < best_cost:
            best_cost = fits[ranked[0]]
            best = pop[ranked[0]][:]
        nxt = elites[:]
        while len(nxt) < POP:
            def tour():
                cands = random.sample(range(POP), 5)
                return pop[min(cands, key=lambda i: fits[i])][:]
            child = ox(tour(), tour())
            if random.random() < MUT and len(child) >= 2:
                i, j = random.sample(range(len(child)), 2)
                child[i], child[j] = child[j], child[i]
            nxt.append(child)
        pop = nxt

    best_split = split(best, num_vehicles)

    # Build coordinate routes using OSRM for each vehicle leg
    coordinate_routes = []
    vehicle_stats = []
    total_dist = 0.0
    total_time = 0.0

    for v_idx, stops in enumerate(best_split):
        full_stop_indices = [depot_idx] + stops + [depot_idx]
        vehicle_coords = []
        v_dist = 0.0
        v_time = 0.0

        for leg_a, leg_b in zip(full_stop_indices[:-1], full_stop_indices[1:]):
            lat1, lon1 = all_points[leg_a]
            lat2, lon2 = all_points[leg_b]
            leg_coords = await _get_route_coords(lat1, lon1, lat2, lon2)
            vehicle_coords.extend(leg_coords)
            v_dist += cost_matrix[leg_a][leg_b] * (50 / 3600)  # rough dist from time
            v_time += cost_matrix[leg_a][leg_b]

        # Get proper distance from OSRM for first leg as a better estimate
        try:
            check = await _osrm_route(
                all_points[full_stop_indices[0]][0], all_points[full_stop_indices[0]][1],
                all_points[full_stop_indices[-1]][0], all_points[full_stop_indices[-1]][1],
            )
        except Exception:
            pass

        coordinate_routes.append(vehicle_coords)
        vehicle_stats.append(VehicleStat(
            vehicle_id=v_idx,
            stops=len(stops),
            distance_m=round(v_time * (50000 / 3600), 2),
            time_sec=round(v_time, 2),
        ))
        total_dist += v_time * (50000 / 3600)
        total_time += v_time

    return VRPResponse(
        routes=coordinate_routes,
        vehicle_stats=vehicle_stats,
        total_distance_m=round(total_dist, 2),
        total_time_sec=round(total_time, 2),
    )


@router.get("/vrp/demo")
async def get_demo_vrp():
    """Demo VRP: 5 deliveries across Mumbai with 2 vehicles."""
    demo_request = VRPRequest(
        depot=LatLon(lat=19.0760, lon=72.8777),   # Mumbai central
        deliveries=[
            VRPDelivery(lat=19.0544, lon=72.8322, label="Bandra"),
            VRPDelivery(lat=18.9667, lon=72.8333, label="Colaba"),
            VRPDelivery(lat=19.1136, lon=72.8697, label="Andheri"),
            VRPDelivery(lat=19.0178, lon=72.8478, label="Worli"),
            VRPDelivery(lat=19.1543, lon=72.9897, label="Powai"),
        ],
        num_vehicles=2,
        optimize_for="time",
    )
    return await solve_fleet_routing(demo_request)
