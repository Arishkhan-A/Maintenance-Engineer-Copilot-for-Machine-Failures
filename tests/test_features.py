"""Unit tests for feature engineering and enterprise data validation."""
import pytest
import pandas as pd
import numpy as np
from src.features.build_features import compute_time_series_features, get_feature_columns
from src.data.load_data import clean_and_impute_dataset, validate_data_quality

def test_feature_engineering_structure():
    # Sample synthetic test data conforming to enterprise schema
    data = {
        "timestamp": pd.date_range("2024-01-01", periods=15, freq="10min"),
        "machine_id": ["M01"] * 15,
        "machine_type": ["CNC"] * 15,
        "temperature_motor": np.linspace(50, 70, 15),
        "vibration_rms": np.linspace(1.5, 3.5, 15),
        "pressure_level": [6.0] * 15,
        "current_phase_avg": np.linspace(30, 45, 15),
        "rpm": [2400.0] * 15,
        "ambient_temp": [25.0] * 15,
        "operating_mode": ["normal"] * 15,
        "hours_since_maintenance": np.linspace(100, 102.5, 15),
        "failure_within_24h": [0] * 14 + [1]
    }
    df = pd.DataFrame(data)
    df_feat = compute_time_series_features(df)

    num_cols, cat_cols = get_feature_columns()
    
    # Assert all expected feature columns exist
    for col in num_cols:
        assert col in df_feat.columns, f"Missing numeric column: {col}"
    for col in cat_cols:
        assert col in df_feat.columns, f"Missing categorical column: {col}"

    # Assert no NaNs in rolling, lag, and differential features
    assert df_feat["vibration_rms_roll_mean_5"].isna().sum() == 0
    assert df_feat["temperature_motor_lag_1"].isna().sum() == 0
    assert df_feat["vibration_rms_delta"].isna().sum() == 0
    assert df_feat["temp_differential"].isna().sum() == 0

def test_data_validation_clean_check():
    data = {
        "timestamp": pd.date_range("2024-01-01", periods=10, freq="10min"),
        "machine_id": [1.0] * 10,
        "machine_type": ["Pump"] * 10,
        "temperature_motor": [60.0] * 10,
        "vibration_rms": [2.0] * 10,
        "pressure_level": [30.0] * 10,
        "current_phase_avg": [40.0] * 10,
        "rpm": [1500.0] * 10,
        "ambient_temp": [24.0] * 10,
        "operating_mode": ["normal"] * 10,
        "hours_since_maintenance": [500.0] * 10,
        "failure_within_24h": [0] * 10,
        "failure_type": ["none"] * 10,
        "rul_hours": [120.0] * 10,
        "estimated_repair_cost": [0.0] * 10
    }
    df = pd.DataFrame(data)
    df_clean = clean_and_impute_dataset(df)
    report = validate_data_quality(df_clean)
    assert report["is_production_clean"] is True
    assert report["missing_values_total"] == 0
    assert report["unique_machines"] == 1
    assert report["machine_list"][0] == "M01"
