"""Unit tests for Multi-Class Fault Diagnosis Classifier."""
import pytest
import os
import joblib
import numpy as np
import pandas as pd
from src.models.predict import MachineInferenceEngine

def test_multiclass_artifacts_exist():
    assert os.path.exists("models/multiclass_model.joblib"), "multiclass_model.joblib is missing"
    assert os.path.exists("models/fault_label_encoder.joblib"), "fault_label_encoder.joblib is missing"

def test_multiclass_prediction_in_engine():
    engine = MachineInferenceEngine()
    rows = []
    # Create window with high vibration indicating bearing wear
    for i in range(12):
        rows.append({
            "timestamp": f"2024-01-01 10:{i:02d}:00",
            "machine_id": "M17",
            "machine_type": "CNC",
            "temperature_motor": 65.0 + i,
            "vibration_rms": 3.5 + (i * 0.3),
            "pressure_level": 6.0,
            "current_phase_avg": 38.0,
            "rpm": 2400.0,
            "ambient_temp": 25.0,
            "operating_mode": "normal",
            "hours_since_maintenance": 1200.0
        })
    df_win = pd.DataFrame(rows)
    pred = engine.predict_window(df_win)

    assert "fault_diagnosis" in pred
    assert pred["fault_diagnosis"] in [
        "Nominal Operation",
        "Bearing Degradation",
        "Motor Overheating",
        "Hydraulic Fault",
        "Electrical Power Surge"
    ]
    assert "fault_confidence" in pred
    assert 0.0 <= pred["fault_confidence"] <= 1.0
    assert "all_fault_probabilities" in pred
    assert len(pred["all_fault_probabilities"]) > 0
    assert "health_index" in pred
    assert 0.0 <= pred["health_index"]["health_score"] <= 100.0
    assert "financial_roi" in pred
