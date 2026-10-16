from pydantic_settings import BaseSettings
from typing import List
import os

class Settings(BaseSettings):
    city_name: str = "Manhattan, New York, USA"
    graph_file: str = "data/city_graph.graphml"
    model_file: str = "data/travel_time_model.joblib"
    host: str = "0.0.0.0"
    port: int = 8000
    cors_origins: List[str] = ["*"]

    class Config:
        env_prefix = ""
        env_file = ".env"
        env_file_encoding = "utf-8"

settings = Settings()
