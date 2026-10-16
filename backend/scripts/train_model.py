"""
Generate synthetic training data and train an XGBoost travel-time regression
model.  The trained model is saved to the path defined in app.config.settings.

Usage
-----
    python scripts/train_model.py
"""

import math
import os
import sys

import joblib
import numpy as np
import pandas as pd
from sklearn.metrics import mean_squared_error
from sklearn.model_selection import train_test_split
from xgboost import XGBRegressor

# Make the app package importable from the scripts directory
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from app.config import settings  # noqa: E402

# ---------------------------------------------------------------------------
# Congestion / weather lookup tables (mirror ml_predictor.py)
# ---------------------------------------------------------------------------

CONGESTION_FACTORS: dict[int, float] = {
    0: 0.7,  1: 0.8,  2: 0.8,  3: 0.7,  4: 0.7,  5: 0.8,  6: 0.9,
    7: 1.8,  8: 1.9,  9: 1.7, 10: 1.3, 11: 1.2, 12: 1.2, 13: 1.1,
    14: 1.1, 15: 1.3, 16: 1.8, 17: 1.9, 18: 1.7, 19: 1.4, 20: 1.2,
    21: 1.0, 22: 0.9, 23: 0.8,
}

WEATHER_FACTORS: dict[int, float] = {
    0: 1.0,   # clear
    1: 1.3,   # rain
    2: 1.7,   # snow
}


# ---------------------------------------------------------------------------
# Data generation
# ---------------------------------------------------------------------------

def generate_synthetic_data(n_samples: int = 50_000):
    """Create a synthetic dataset that mimics real traffic patterns.

    Features
    --------
    base_travel_time : OSM-derived travel time in seconds
    length           : road segment length in metres
    speed_kph        : posted speed limit in km/h
    hour_sin / cos   : cyclic encoding of the hour of day
    day_of_week      : 0 = Monday … 6 = Sunday
    is_weekend       : binary flag
    weather_code     : 0 = clear, 1 = rain, 2 = snow
    grade            : road gradient (rise / run)

    Target
    ------
    Actual travel time in seconds, derived by applying congestion / weather
    multipliers to the base travel time plus Gaussian noise.
    """
    np.random.seed(42)

    base_travel_time = np.random.uniform(10, 600, n_samples)
    length = np.random.uniform(20, 5000, n_samples)
    speed_kph = np.random.uniform(20, 80, n_samples)
    hour = np.random.randint(0, 24, n_samples)
    day_of_week = np.random.randint(0, 7, n_samples)
    weather_code = np.random.choice([0, 1, 2], n_samples, p=[0.7, 0.2, 0.1])
    grade = np.random.uniform(-0.1, 0.1, n_samples)

    congestion_factor = np.array([CONGESTION_FACTORS[h] for h in hour])
    weather_factor = np.array([WEATHER_FACTORS[w] for w in weather_code])
    grade_penalty = np.maximum(0.0, grade) * 2.0
    noise = np.random.normal(0, base_travel_time * 0.05)

    target = (
        base_travel_time * congestion_factor * weather_factor * (1.0 + grade_penalty)
        + noise
    )
    target = np.maximum(target, 5.0)  # minimum 5 seconds

    # Cyclic hour encoding
    hour_sin = np.sin(2 * math.pi * hour / 24)
    hour_cos = np.cos(2 * math.pi * hour / 24)
    is_weekend = (day_of_week >= 5).astype(int)

    X = np.column_stack([
        base_travel_time, length, speed_kph,
        hour_sin, hour_cos, day_of_week, is_weekend,
        weather_code, grade,
    ])
    return X, target


# ---------------------------------------------------------------------------
# Training
# ---------------------------------------------------------------------------

def main() -> None:
    print("Generating synthetic training data …")
    X, y = generate_synthetic_data(50_000)

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42
    )
    print(f"  Train samples : {len(X_train):,}")
    print(f"  Test  samples : {len(X_test):,}")

    print("\nTraining XGBoost model …")
    model = XGBRegressor(
        n_estimators=200,
        max_depth=6,
        learning_rate=0.1,
        subsample=0.8,
        colsample_bytree=0.8,
        random_state=42,
        n_jobs=-1,
    )
    model.fit(X_train, y_train)

    y_pred = model.predict(X_test)
    rmse = math.sqrt(mean_squared_error(y_test, y_pred))
    print(f"\nTest RMSE : {rmse:.2f} seconds")

    feature_names = [
        "base_travel_time", "length", "speed_kph",
        "hour_sin", "hour_cos", "day_of_week", "is_weekend",
        "weather_code", "grade",
    ]
    importances = dict(zip(feature_names, model.feature_importances_))
    sorted_imp = sorted(importances.items(), key=lambda kv: -kv[1])
    print("\nFeature importances:")
    for name, imp in sorted_imp:
        print(f"  {name:<22} {imp:.4f}")

    # Ensure the output directory exists
    model_dir = os.path.dirname(settings.model_file)
    if model_dir:
        os.makedirs(model_dir, exist_ok=True)

    joblib.dump(model, settings.model_file)
    print(f"\nModel saved → {settings.model_file}")


if __name__ == "__main__":
    main()
