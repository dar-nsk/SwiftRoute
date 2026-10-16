# AI-Powered Optimal Path & Fleet Routing System

A full-stack, production-ready routing platform that goes beyond shortest-path geometry. It optimizes routes across multiple business constraints — travel time, fuel cost, traffic density, and delivery windows — using real road network data, machine learning, and combinatorial optimization.

---

## Features

- **A\* Pathfinding on real OSM road networks (Manhattan)** — downloads and caches the actual street graph via OSMnx; every edge weight reflects real road geometry.
- **XGBoost ML model for dynamic travel time prediction** — predicts congestion-adjusted traversal time from time-of-day, day-of-week, road class, and simulated weather features.
- **Multi-objective cost functions (fastest / eco / toll-free / balanced)** — a slider in the UI lets users shift priority between speed, fuel efficiency, and financial cost.
- **Genetic Algorithm Vehicle Routing Problem (VRP) solver** — assigns N delivery stops across K vehicles, respects time windows, and minimizes total fleet cost.
- **Interactive React + Leaflet.js frontend** — click any two points on the map to compute a route; supports multi-stop VRP mode.
- **Real-time route visualization with cost breakdowns** — animated polyline, per-segment cost table, and summary panel (distance, ETA, fuel, toll estimate).
- **Docker Compose one-command deployment** — the entire stack (backend + frontend + nginx reverse proxy) starts with a single command.

---

## Architecture

```
Browser (React + Leaflet)
        |
        | HTTP / REST
        v
  nginx reverse proxy (:80)
        |
        v
  FastAPI Backend (:8000)
  ┌─────────────────────────────┐
  │  A* Pathfinding Engine      │
  │  XGBoost ML Predictor       │
  │  Genetic Algorithm VRP      │
  │  OSMnx Graph Service        │
  └─────────────────────────────┘
        |
        | OSM Data (cached GraphML)
        v
  Road Network Graph (GraphML)
```

- The **Graph Service** downloads the OSM road network for the configured city on first run and persists it as a GraphML file so subsequent starts are instant.
- The **ML Predictor** loads a pre-trained XGBoost model (trained via `scripts/train_model.py`) and augments each edge weight at query time.
- The **VRP Solver** uses a Genetic Algorithm with tournament selection, order-crossover, and 2-opt local search to find near-optimal multi-vehicle routes.

---

## Prerequisites

| Tool | Version |
|------|---------|
| [Docker](https://docs.docker.com/get-docker/) | 20.10+ |
| [Docker Compose](https://docs.docker.com/compose/install/) | 2.0+ (V2 plugin or standalone) |

No Python or Node.js installation is required on the host — everything runs inside containers.

---

## Quick Start

```bash
git clone <repo-url>
cd Smart_Ai
docker-compose up --build
```

- **Frontend:** http://localhost:3000
- **API docs (Swagger UI):** http://localhost:8000/docs
- **API docs (ReDoc):** http://localhost:8000/redoc

The first build downloads the Manhattan road network and trains the ML model inside the backend container; this takes 3–8 minutes depending on your connection and CPU. Subsequent starts use the cached graph and model and are ready in under 30 seconds.

---

## Development Setup

### Backend

```bash
cd backend
pip install -r requirements.txt

# Download the OSM road network (saves to data/graph.graphml)
python scripts/download_graph.py

# Train the XGBoost travel-time predictor (saves to data/model.json)
python scripts/train_model.py

# Start the API server with auto-reload
uvicorn app.main:app --reload --port 8000
```

### Frontend

```bash
cd frontend
npm install
npm start
# Opens http://localhost:3000 with hot-reload
```

Make sure the backend is running on port 8000 before starting the frontend in development mode.

---

## API Documentation

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/health` | Health check — returns service status and graph/model load state |
| `GET` | `/api/route/modes` | List all available optimization modes with descriptions |
| `POST` | `/api/route` | Calculate the optimal single route between two coordinates |
| `POST` | `/api/vrp` | Solve multi-vehicle routing for a set of delivery locations |
| `GET` | `/api/vrp/demo` | Return a pre-computed demo VRP solution (no body required) |

### `POST /api/route` — Calculate Optimal Route

**Request body:**

```json
{
  "start_lat": 40.7128,
  "start_lng": -74.0060,
  "end_lat": 40.7580,
  "end_lng": -73.9855,
  "mode": "fastest",
  "hour": 8,
  "day_of_week": 1
}
```

**`mode` values:** `fastest` | `eco` | `toll_free` | `balanced`

**Response:**

```json
{
  "path": [
    [40.7128, -74.0060],
    [40.7145, -74.0032],
    "..."
  ],
  "total_distance_km": 5.42,
  "total_time_min": 18.3,
  "total_cost": 124.7,
  "fuel_cost_estimate": 0.87,
  "optimization_mode": "fastest",
  "segments": [
    {
      "from": [40.7128, -74.0060],
      "to": [40.7145, -74.0032],
      "distance_m": 320,
      "predicted_time_s": 42,
      "edge_cost": 12.1
    }
  ]
}
```

---

### `POST /api/vrp` — Multi-Vehicle Routing

**Request body:**

```json
{
  "depot": [40.7128, -74.0060],
  "deliveries": [
    [40.7580, -73.9855],
    [40.7489, -73.9680],
    [40.7282, -74.0776]
  ],
  "num_vehicles": 2,
  "mode": "balanced"
}
```

**Response:**

```json
{
  "vehicles": [
    {
      "vehicle_id": 0,
      "stops": [
        [40.7128, -74.0060],
        [40.7580, -73.9855],
        [40.7128, -74.0060]
      ],
      "total_distance_km": 8.1,
      "total_time_min": 31.4
    },
    {
      "vehicle_id": 1,
      "stops": [
        [40.7128, -74.0060],
        [40.7489, -73.9680],
        [40.7282, -74.0776],
        [40.7128, -74.0060]
      ],
      "total_distance_km": 11.6,
      "total_time_min": 44.2
    }
  ],
  "total_fleet_distance_km": 19.7,
  "total_fleet_time_min": 75.6,
  "optimization_mode": "balanced"
}
```

---

## How to Change the City

The default city is **Manhattan, New York City, USA**. To use a different city:

```bash
# Option 1: environment variable override at runtime
docker-compose up --build -e CITY_NAME="Chicago, Illinois, USA"

# Option 2: edit .env or docker-compose.yml
# In docker-compose.yml, under backend > environment:
#   CITY_NAME: "Chicago, Illinois, USA"
```

After changing the city, the graph and model files in `backend/data/` must be regenerated. Delete them and let the container rebuild on next start, or run the scripts manually:

```bash
cd backend
python scripts/download_graph.py
python scripts/train_model.py
```

---

## Optimization Modes

| Mode | Priority | Cost Function |
|------|----------|---------------|
| **fastest** | Minimize travel time | ML-predicted traversal time dominates edge weight |
| **eco** | Minimize fuel consumption | Penalizes high-speed roads, elevation changes, and congested segments |
| **toll_free** | Minimize financial cost | Heavily penalizes roads flagged as toll roads in OSM |
| **balanced** | Equal weight | Weighted sum of time, fuel, and toll components |

The mode is passed per-request, so a user can compare all four routes for the same origin/destination without restarting anything.

---

## Project Structure

```
Smart_Ai/
├── backend/
│   ├── app/
│   │   ├── main.py              # FastAPI application entry point
│   │   ├── config.py            # Environment config (city name, model paths)
│   │   ├── models/
│   │   │   └── schemas.py       # Pydantic request/response models
│   │   ├── routers/
│   │   │   ├── routing.py       # /api/route endpoints
│   │   │   └── vrp.py           # /api/vrp endpoints
│   │   └── services/
│   │       ├── graph_service.py # OSMnx graph download & caching
│   │       ├── ml_predictor.py  # XGBoost travel-time predictor
│   │       ├── pathfinding.py   # A* algorithm with dynamic edge weights
│   │       └── vrp_solver.py    # Genetic Algorithm VRP solver
│   ├── scripts/
│   │   ├── download_graph.py    # One-time graph download script
│   │   └── train_model.py       # ML model training script
│   ├── data/                    # Auto-created; holds graph.graphml & model.json
│   ├── requirements.txt
│   └── Dockerfile
├── frontend/
│   ├── src/
│   │   ├── App.jsx              # Root component
│   │   ├── index.js             # React entry point
│   │   ├── components/
│   │   │   ├── MapView.jsx      # Leaflet map canvas
│   │   │   ├── ControlPanel.jsx # Mode slider + coordinate inputs
│   │   │   ├── RouteInfo.jsx    # Cost breakdown panel
│   │   │   └── VRPPanel.jsx     # Multi-stop VRP UI
│   │   └── services/
│   │       └── api.js           # Axios API client
│   ├── public/
│   │   └── index.html
│   ├── package.json
│   └── Dockerfile
├── docker-compose.yml
├── nginx.conf
└── README.md
```

---

## Screenshots

> **Route Calculation View** — user clicks origin and destination on the Manhattan map; the optimal route polyline renders with a cost breakdown sidebar.
>
> *(Add a screenshot here after first run: `frontend/public/screenshots/route-view.png`)*

> **VRP Fleet View** — two vehicles shown in different colors completing their assigned delivery circuits from the depot.
>
> *(Add a screenshot here after first run: `frontend/public/screenshots/vrp-view.png`)*

---

## Troubleshooting

**Backend takes too long to start**
The first run downloads ~50 MB of OSM data and trains the XGBoost model. This is normal. Check logs with `docker-compose logs -f backend`.

**"Graph not loaded" error**
The graph download failed (network issue or invalid city name). Check the backend logs and verify the `CITY_NAME` environment variable matches an OSM-recognized location string.

**Frontend shows blank map**
Ensure the backend container is healthy (`docker-compose ps`) and CORS is not blocked. In development mode, verify the proxy setting in `frontend/package.json` points to `http://localhost:8000`.

**Port conflicts**
If ports 3000 or 8000 are in use, edit the `ports` section in `docker-compose.yml`:
```yaml
ports:
  - "3001:80"   # change 3000 to 3001 for frontend
```

---

## License

MIT
