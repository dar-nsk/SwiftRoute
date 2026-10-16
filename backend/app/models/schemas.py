from pydantic import BaseModel, Field
from typing import List, Optional, Literal

class LatLon(BaseModel):
    lat: float = Field(..., ge=-90, le=90)
    lon: float = Field(..., ge=-180, le=180)

class RouteRequest(BaseModel):
    origin: LatLon
    destination: LatLon
    mode: Literal['fastest', 'eco', 'toll_free', 'balanced'] = 'balanced'
    hour: int = Field(default=12, ge=0, le=23)
    day_of_week: int = Field(default=1, ge=0, le=6)
    weather_code: int = Field(default=0, ge=0, le=2)

class RouteResponse(BaseModel):
    coordinates: List[List[float]]
    distance_m: float
    time_sec: float
    fuel_liters: float
    co2_kg: float
    mode: str
    waypoints: List[List[float]]

class VRPDelivery(BaseModel):
    lat: float = Field(..., ge=-90, le=90)
    lon: float = Field(..., ge=-180, le=180)
    label: Optional[str] = None

class VRPRequest(BaseModel):
    depot: LatLon
    deliveries: List[VRPDelivery] = Field(..., min_length=1, max_length=20)
    num_vehicles: int = Field(default=2, ge=1, le=10)
    optimize_for: Literal['time', 'distance'] = 'time'

class VehicleStat(BaseModel):
    vehicle_id: int
    stops: int
    distance_m: float
    time_sec: float

class VRPResponse(BaseModel):
    routes: List[List[List[float]]]
    vehicle_stats: List[VehicleStat]
    total_distance_m: float
    total_time_sec: float

class HealthResponse(BaseModel):
    status: str
    graph_loaded: bool
    model_loaded: bool
    city: str
    node_count: int
    edge_count: int
