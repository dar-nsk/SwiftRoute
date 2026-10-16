"""
Download (or verify) the OSM road-network graph for the configured city and
save it to the path specified in app.config.settings.

Usage
-----
    python scripts/download_graph.py
"""

import os
import sys

import osmnx as ox

# Make the app package importable from the scripts directory
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from app.config import settings  # noqa: E402


def main() -> None:
    graph_path = settings.graph_file

    # Ensure the data directory exists
    graph_dir = os.path.dirname(graph_path)
    if graph_dir:
        os.makedirs(graph_dir, exist_ok=True)

    if os.path.exists(graph_path):
        print(f"Graph file already exists at '{graph_path}'.  Loading to verify …")
        G = ox.load_graphml(graph_path)
        print(
            f"Graph OK: {G.number_of_nodes():,} nodes, "
            f"{G.number_of_edges():,} edges."
        )
        return

    print(f"Downloading road network for: {settings.city_name!r} …")
    G = ox.graph_from_place(settings.city_name, network_type="drive")
    G = ox.add_edge_speeds(G)
    G = ox.add_edge_travel_times(G)

    # Inject default grade / toll attributes so the graph is immediately
    # compatible with the pathfinding service.
    for _u, _v, _key, data in G.edges(keys=True, data=True):
        data.setdefault("grade", 0.0)
        data.setdefault("is_toll", False)

    ox.save_graphml(G, graph_path)
    print(
        f"Graph saved to '{graph_path}': "
        f"{G.number_of_nodes():,} nodes, {G.number_of_edges():,} edges."
    )


if __name__ == "__main__":
    main()
