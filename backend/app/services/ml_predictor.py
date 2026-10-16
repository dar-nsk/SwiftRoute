"""
ML Predictor service: loads a pre-trained travel-time regression model and
provides a prediction function used by the pathfinding engine.

When no trained model is available the service falls back to simple
hour-of-day / weather congestion lookup tables.
"""

import logging
import math

import joblib
import numpy as np

from app.config import settings

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Module-level singleton
# ---------------------------------------------------------------------------
_model = None

# ---------------------------------------------------------------------------
# Lookup tables
# ---------------------------------------------------------------------------

# Congestion multiplier by hour-of-day (0 = midnight … 23 = 11 pm)
CONGESTION_FACTORS: dict[int, float] = {
    0: 0.7,
    1: 0.8,
    2: 0.8,
    3: 0.7,
    4: 0.7,
    5: 0.8,
    6: 0.9,
    7: 1.8,
    8: 1.9,
    9: 1.7,
    10: 1.3,
    11: 1.2,
    12: 1.2,
    13: 1.1,
    14: 1.1,
    15: 1.3,
    16: 1.8,
    17: 1.9,
    18: 1.7,
    19: 1.4,
    20: 1.2,
    21: 1.0,
    22: 0.9,
    23: 0.8,
}

# Weather multiplier: 0 = clear, 1 = rain, 2 = snow
WEATHER_FACTORS: dict[int, float] = {
    0: 1.0,
    1: 1.3,
    2: 1.7,
}


# ---------------------------------------------------------------------------
# Model management
# ---------------------------------------------------------------------------

def load_model() -> None:
    """Try to load the joblib model from the path specified in settings."""
    global _model

    model_path = settings.model_file
    try:
        _model = joblib.load(model_path)
        logger.info("Travel-time model loaded from %s.", model_path)
    except FileNotFoundError:
        logger.warning(
            "Model file not found at '%s'. Falling back to congestion lookup tables.",
            model_path,
        )
        _model = None
    except Exception as exc:
        logger.exception(
            "Failed to load model from '%s': %s. Falling back to lookup tables.",
            model_path, exc,
        )
        _model = None


# ---------------------------------------------------------------------------
# Prediction
# ---------------------------------------------------------------------------

def predict_travel_time(
    base_travel_time: float,
    length: float,
    speed_kph: float,
    hour: int,
    day_of_week: int,
    weather_code: int,
    grade: float = 0.0,
) -> float:
    """Predict the actual travel time (seconds) for a road segment.

    Parameters
    ----------
    base_travel_time : float
        OSM-derived travel time in seconds.
    length : float
        Edge length in metres.
    speed_kph : float
        Posted / estimated speed in km/h.
    hour : int
        Hour of day (0–23).
    day_of_week : int
        Day of week (0 = Monday … 6 = Sunday).
    weather_code : int
        0 = clear, 1 = rain, 2 = snow.
    grade : float
        Road gradient (rise / run).  Positive = uphill.

    Returns
    -------
    float
        Predicted travel time in seconds, always ≥ 50 % of the base value.
    """
    if _model is not None:
        # Build feature vector matching the training schema
        hour_sin = math.sin(2 * math.pi * hour / 24)
        hour_cos = math.cos(2 * math.pi * hour / 24)
        is_weekend = 1 if day_of_week >= 5 else 0

        features = np.array([[
            base_travel_time,
            length,
            speed_kph,
            hour_sin,
            hour_cos,
            day_of_week,
            is_weekend,
            weather_code,
            grade,
        ]], dtype=float)

        try:
            predicted = float(_model.predict(features)[0])
        except Exception as exc:
            logger.warning("Model prediction failed (%s); using fallback.", exc)
            predicted = (
                base_travel_time
                * CONGESTION_FACTORS.get(hour, 1.0)
                * WEATHER_FACTORS.get(weather_code, 1.0)
            )
    else:
        congestion = CONGESTION_FACTORS.get(hour, 1.0)
        weather = WEATHER_FACTORS.get(weather_code, 1.0)
        predicted = base_travel_time * congestion * weather

    # Guard against unrealistically short predictions
    return max(base_travel_time * 0.5, predicted)
