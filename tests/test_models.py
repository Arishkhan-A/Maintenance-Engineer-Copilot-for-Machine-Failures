"""Unit tests for ML models, RUL regression, Anomaly detector and SHAP."""
import pytest
import numpy as np
import pandas as pd
from src.models.predict import MachineInferenceEngine

@pytest.fixture
def sample_telemetry_window():
    rows = []
    for i in range(12):
        rows.append({
            "timestamp": f"2024-01-01 10:{i:02d}:00",
            "machine_id": "M17",
            "machine_type": "CNC",
            "temperature_motor": 55.0 + (i * 1.5),
            "vibration_rms": 2.0 + (i * 0.25),
            "pressure_level": 6.0,
            "current_phase_avg": 35.0 + (i * 0.8),
            "rpm": 2400.0,
            "ambient_temp": 24.5,
            "operating_mode": "normal",
            "hours_since_maintenance": 1200.0 + (i * 0.1)
        })
    return pd.DataFrame(rows)

def test_inference_engine_prediction(sample_telemetry_window):
    engine = MachineInferenceEngine()
    assert engine.is_ready(), "Model artifacts are not loaded properly."

    result = engine.predict_window(sample_telemetry_window)

    assert "machine_id" in result
    assert result["machine_id"] == "M17"
    assert "failure_probability" in result
    assert 0.0 <= result["failure_probability"] <= 1.0
    assert result["risk_level"] in ["Normal", "Medium", "High", "Critical"]
    assert "rul_hours" in result
    assert result["rul_hours"] >= 0.0
    assert "is_anomaly" in result
    assert isinstance(result["is_anomaly"], bool)
    assert "top_contributing_features" in result
    assert len(result["top_contributing_features"]) > 0

def test_shap_contribution_bounds(sample_telemetry_window):
    engine = MachineInferenceEngine()
    result = engine.predict_window(sample_telemetry_window)
    shap_list = result["top_contributing_features"]
    
    for item in shap_list:
        assert "feature" in item
        assert "contribution_percent" in item
        assert 0.0 <= item["contribution_percent"] <= 100.0
