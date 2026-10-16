"""
VRP Solver service: Genetic Algorithm solver for the Vehicle Routing Problem
with time windows.  Given a depot node and a set of delivery nodes the solver
assigns stops to vehicles and sequences them to minimise total travel time or
distance.
"""

import logging
import math
import random
from typing import Any

import networkx as nx

from app.services.graph_service import get_graph

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Cost helpers
# ---------------------------------------------------------------------------

def compute_route_cost(
    G: nx.MultiDiGraph,
    node_list: list[int],
    metric: str = "time",
) -> float:
    """Sum the edge costs along a sequence of nodes.

    Parameters
    ----------
    G : nx.MultiDiGraph
    node_list : list[int]
        Ordered list of OSM node ids to traverse.
    metric : str
        'time'  → sum ``travel_time`` attributes.
        'distance' → sum ``length`` attributes.

    Returns
    -------
    float
        Total cost; ``float('inf')`` when any consecutive pair is not connected.
    """
    if len(node_list) < 2:
        return 0.0

    attr = "travel_time" if metric == "time" else "length"
    total = 0.0

    for u, v in zip(node_list[:-1], node_list[1:]):
        if not G.has_node(u) or not G.has_node(v):
            return float("inf")

        try:
            # Use Dijkstra for the inter-node leg so we get a realistic cost
            # even when nodes are not directly connected by a single edge.
            cost = nx.shortest_path_length(G, u, v, weight=attr)
            total += cost
        except (nx.NetworkXNoPath, nx.NodeNotFound):
            return float("inf")

    return total


def calculate_tour_cost(
    G: nx.MultiDiGraph,
    vehicle_routes: list[list[int]],
    metric: str = "time",
) -> float:
    """Return the total cost across all vehicle routes."""
    return sum(compute_route_cost(G, route, metric) for route in vehicle_routes)


# ---------------------------------------------------------------------------
# GA operators
# ---------------------------------------------------------------------------

def order_crossover(parent1: list, parent2: list) -> list:
    """Order crossover (OX) for permutation chromosomes.

    Copies a random slice from *parent1* into the child, then fills the
    remaining positions in the order they appear in *parent2*.
    """
    size = len(parent1)
    if size == 0:
        return []
    if size == 1:
        return parent1[:]

    start, end = sorted(random.sample(range(size), 2))
    child = [None] * size

    # Copy the slice from parent1
    child[start:end + 1] = parent1[start:end + 1]
    copied = set(parent1[start:end + 1])

    # Fill from parent2 in order
    fill_pos = (end + 1) % size
    for gene in parent2:
        if gene not in copied:
            child[fill_pos] = gene
            copied.add(gene)
            fill_pos = (fill_pos + 1) % size

    return child


def swap_mutation(route: list, mutation_rate: float = 0.02) -> list:
    """Randomly swap two elements in *route* with probability *mutation_rate*."""
    route = route[:]
    if len(route) < 2:
        return route
    if random.random() < mutation_rate:
        i, j = random.sample(range(len(route)), 2)
        route[i], route[j] = route[j], route[i]
    return route


# ---------------------------------------------------------------------------
# Population helpers
# ---------------------------------------------------------------------------

def create_individual(delivery_nodes: list[int]) -> list[int]:
    """Return a random permutation of delivery nodes (a candidate solution)."""
    individual = delivery_nodes[:]
    random.shuffle(individual)
    return individual


def split_route(
    individual: list[int],
    num_vehicles: int,
    depot_node: int,
) -> list[list[int]]:
    """Split the delivery permutation roughly evenly across vehicles.

    Each vehicle's sub-route is wrapped with the depot node at both ends:
    ``[depot, stop1, stop2, …, depot]``.
    """
    n = len(individual)
    if num_vehicles <= 0:
        num_vehicles = 1

    base_size = n // num_vehicles
    remainder = n % num_vehicles

    routes: list[list[int]] = []
    idx = 0
    for i in range(num_vehicles):
        chunk_size = base_size + (1 if i < remainder else 0)
        chunk = individual[idx: idx + chunk_size]
        idx += chunk_size
        # Wrap with depot
        route = [depot_node] + chunk + [depot_node]
        routes.append(route)

    return routes


# ---------------------------------------------------------------------------
# Tournament selection
# ---------------------------------------------------------------------------

def _tournament_select(
    population: list[list[int]],
    fitnesses: list[float],
    tournament_size: int,
) -> list[int]:
    """Select one individual via tournament selection (lower fitness = better)."""
    candidates = random.sample(range(len(population)), min(tournament_size, len(population)))
    best = min(candidates, key=lambda idx: fitnesses[idx])
    return population[best][:]


# ---------------------------------------------------------------------------
# Main solver
# ---------------------------------------------------------------------------

def solve_vrp(
    depot_node: int,
    delivery_nodes: list[int],
    num_vehicles: int,
    optimize_for: str = "time",
    G: nx.MultiDiGraph | None = None,
) -> dict:
    """Solve the VRP using a Genetic Algorithm.

    Parameters
    ----------
    depot_node : int
        OSM node id of the depot (start/end for every vehicle).
    delivery_nodes : list[int]
        OSM node ids that must be visited (one visit each).
    num_vehicles : int
        Number of vehicles available.
    optimize_for : str
        'time' or 'distance'.
    G : nx.MultiDiGraph, optional
        Road-network graph; fetched from the graph service if not supplied.

    Returns
    -------
    dict
        ``routes``        – list of lists of node ids (one per vehicle)
        ``vehicle_stats`` – per-vehicle summary dicts
        ``total_distance_m`` – total fleet distance in metres
        ``total_time_sec``   – total fleet time in seconds
    """
    if G is None:
        G = get_graph()

    metric = "time" if optimize_for == "time" else "distance"

    # GA hyper-parameters
    POPULATION_SIZE = 100
    GENERATIONS = 200
    MUTATION_RATE = 0.02
    TOURNAMENT_SIZE = 5
    ELITE_FRACTION = 0.10

    n_deliveries = len(delivery_nodes)
    if n_deliveries == 0:
        return {
            "routes": [[depot_node]] * num_vehicles,
            "vehicle_stats": [
                {"vehicle_id": i, "stops": 0, "distance_m": 0.0, "time_sec": 0.0}
                for i in range(num_vehicles)
            ],
            "total_distance_m": 0.0,
            "total_time_sec": 0.0,
        }

    # ---- Initialise population ------------------------------------------
    population: list[list[int]] = [
        create_individual(delivery_nodes) for _ in range(POPULATION_SIZE)
    ]

    def fitness(individual: list[int]) -> float:
        routes = split_route(individual, num_vehicles, depot_node)
        return calculate_tour_cost(G, routes, metric)

    best_individual: list[int] = min(population, key=fitness)
    best_cost: float = fitness(best_individual)

    n_elites = max(1, int(POPULATION_SIZE * ELITE_FRACTION))

    # ---- Evolve ------------------------------------------------------------
    for generation in range(GENERATIONS):
        fitnesses = [fitness(ind) for ind in population]

        # Sort by fitness (ascending = better)
        ranked = sorted(range(len(population)), key=lambda i: fitnesses[i])
        elites = [population[i][:] for i in ranked[:n_elites]]

        # Update global best
        if fitnesses[ranked[0]] < best_cost:
            best_cost = fitnesses[ranked[0]]
            best_individual = population[ranked[0]][:]

        # Build next generation
        next_gen = elites[:]
        while len(next_gen) < POPULATION_SIZE:
            p1 = _tournament_select(population, fitnesses, TOURNAMENT_SIZE)
            p2 = _tournament_select(population, fitnesses, TOURNAMENT_SIZE)
            child = order_crossover(p1, p2)
            child = swap_mutation(child, MUTATION_RATE)
            next_gen.append(child)

        population = next_gen

    # ---- Build output from best solution -----------------------------------
    best_routes = split_route(best_individual, num_vehicles, depot_node)

    vehicle_stats: list[dict] = []
    total_distance_m = 0.0
    total_time_sec = 0.0

    for i, route in enumerate(best_routes):
        dist = compute_route_cost(G, route, "distance")
        time = compute_route_cost(G, route, "time")
        # Clamp infinities (disconnected routes) to 0 for reporting
        dist = dist if math.isfinite(dist) else 0.0
        time = time if math.isfinite(time) else 0.0
        vehicle_stats.append({
            "vehicle_id": i,
            "stops": len(route) - 2,  # exclude depot at both ends
            "distance_m": round(dist, 2),
            "time_sec": round(time, 2),
        })
        total_distance_m += dist
        total_time_sec += time

    return {
        "routes": best_routes,
        "vehicle_stats": vehicle_stats,
        "total_distance_m": round(total_distance_m, 2),
        "total_time_sec": round(total_time_sec, 2),
    }


# ---------------------------------------------------------------------------
# Coordinate converter
# ---------------------------------------------------------------------------

def nodes_to_coordinates(
    G: nx.MultiDiGraph,
    routes: list[list[int]],
) -> list[list[list[float]]]:
    """Convert a list of node-id routes to lat/lon coordinate routes.

    Parameters
    ----------
    G : nx.MultiDiGraph
    routes : list[list[int]]
        Each inner list is an ordered sequence of OSM node ids.

    Returns
    -------
    list[list[list[float]]]
        ``[[[lat, lon], …], …]`` — one coordinate list per vehicle route.
    """
    coordinate_routes: list[list[list[float]]] = []
    for route in routes:
        coords: list[list[float]] = []
        for node_id in route:
            try:
                node_data = G.nodes[node_id]
                coords.append([float(node_data["y"]), float(node_data["x"])])
            except KeyError:
                logger.warning("Node %s not found in graph; skipping.", node_id)
        coordinate_routes.append(coords)
    return coordinate_routes
