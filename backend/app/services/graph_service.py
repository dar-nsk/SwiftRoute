"""
Graph service: loads (or downloads) the OSM road-network graph and exposes
helper functions used by the rest of the backend.
"""

import asyncio
import logging
import os

import networkx as nx
import osmnx as ox
from fastapi import HTTPException

from app.config import settings

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Module-level singletons
# ---------------------------------------------------------------------------
_graph: nx.MultiDiGraph | None = None
_graph_lock: asyncio.Lock | None = None


# ---------------------------------------------------------------------------
# Initialisation
# ---------------------------------------------------------------------------

async def initialize_graph() -> None:
    """Download or load the road-network graph and enrich its edges."""
    global _graph, _graph_lock

    if _graph_lock is None:
        _graph_lock = asyncio.Lock()

    async with _graph_lock:
        if _graph is not None:
            # Another coroutine already loaded it while we were waiting.
            return

        graph_path = settings.graph_file

        try:
            if os.path.exists(graph_path):
                logger.info("Loading graph from %s …", graph_path)
                G = ox.load_graphml(graph_path)
                logger.info("Graph loaded from file (%d nodes, %d edges).",
                            G.number_of_nodes(), G.number_of_edges())
            else:
                logger.info(
                    "Graph file not found. Downloading graph for '%s' …",
                    settings.city_name,
                )
                G = ox.graph_from_place(settings.city_name, network_type="drive")
                # Persist for future runs
                os.makedirs(os.path.dirname(graph_path) or ".", exist_ok=True)
                ox.save_graphml(G, graph_path)
                logger.info(
                    "Graph downloaded and saved to %s (%d nodes, %d edges).",
                    graph_path, G.number_of_nodes(), G.number_of_edges(),
                )

            # Enrich edges ------------------------------------------------
            G = ox.add_edge_speeds(G)
            G = ox.add_edge_travel_times(G)

            # Add grade (elevation-based slope) and toll flag defaults
            for u, v, key, data in G.edges(keys=True, data=True):
                if "grade" not in data:
                    data["grade"] = 0.0
                if "is_toll" not in data:
                    data["is_toll"] = False

            _graph = G
            logger.info("Graph initialisation complete.")

        except Exception as exc:
            logger.exception("Failed to initialise graph: %s", exc)
            raise


# ---------------------------------------------------------------------------
# Public accessors
# ---------------------------------------------------------------------------

def get_graph() -> nx.MultiDiGraph:
    """Return the loaded graph or raise 503 if it is not ready."""
    if _graph is None:
        raise HTTPException(
            status_code=503,
            detail="Road-network graph is not loaded yet. Please retry shortly.",
        )
    return _graph


def get_nearest_node(lat: float, lon: float) -> int:
    """Return the OSM node id nearest to the given coordinates.

    OSMnx expects (longitude, latitude) order — we handle the swap here.
    """
    try:
        G = get_graph()
        node_id = ox.nearest_nodes(G, lon, lat)
        return node_id
    except HTTPException:
        raise
    except Exception as exc:
        logger.exception("get_nearest_node failed for (%s, %s): %s", lat, lon, exc)
        raise HTTPException(
            status_code=500,
            detail=f"Could not find nearest node: {exc}",
        )


def get_node_coords(node_id: int) -> tuple[float, float]:
    """Return (lat, lon) for a given graph node id."""
    try:
        G = get_graph()
        node_data = G.nodes[node_id]
        # OSMnx stores latitude as 'y' and longitude as 'x'
        return float(node_data["y"]), float(node_data["x"])
    except HTTPException:
        raise
    except KeyError:
        logger.error("Node %s not found in graph.", node_id)
        raise HTTPException(
            status_code=404,
            detail=f"Node {node_id} not found in graph.",
        )
    except Exception as exc:
        logger.exception("get_node_coords failed for node %s: %s", node_id, exc)
        raise HTTPException(
            status_code=500,
            detail=f"Could not retrieve node coordinates: {exc}",
        )
