"""
Tier-1 Enterprise Unified Inference Engine.
Serves:
1. Binary Failure Prediction (24h horizon)
2. Multi-Class Root-Cause Fault Diagnosis (Gradient Boosting)
3. Remaining Useful Life (RUL) Regression
4. Calibrated Isolation Forest Anomaly Detection
5. SHAP Quantitative Explainability
6. Composite Machine Health Index (0-100% MHI)
7. Financial Downtime Prevention & ROI Analytics
"""

import os
import joblib
import numpy as np
import pandas as pd
from typing import Dict, Any, List
from src.features.build_features import compute_time_series_features, get_feature_columns
from src.explainability.shap_explainer import ModelExplainer
from src.models.health_index import compute_machine_health_index, calculate_financial_roi

FAULT_LABELS_MAP = {
    "none": "Nominal Operation",
    "bearing": "Bearing Degradation",
    "motor_overheat": "Motor Overheating",
    "hydraulic": "Hydraulic Fault",
    "electrical": "Electrical Power Surge"
}

class MachineInferenceEngine:
    """Production inference engine serving all predictive maintenance layers."""

    def __init__(self, models_dir: str = "models"):
        self.models_dir = models_dir
        self.preprocessor = None
        self.failure_model = None
        self.multiclass_model = None
        self.fault_encoder = None
        self.rul_model = None
        self.anomaly_model = None
        self.optimal_threshold = 0.622
        self.model_version = "3.0.0-enterprise"
        self._load_artifacts()

    def _load_artifacts(self):
        prep_path = os.path.join(self.models_dir, "preprocessor.joblib")
        fail_path = os.path.join(self.models_dir, "failure_model.joblib")
        multi_path = os.path.join(self.models_dir, "multiclass_model.joblib")
        enc_path = os.path.join(self.models_dir, "fault_label_encoder.joblib")
        rul_path = os.path.join(self.models_dir, "rul_model.joblib")
        anom_path = os.path.join(self.models_dir, "anomaly_model.joblib")
        meta_path = os.path.join(self.models_dir, "model_metadata.json")

        if os.path.exists(meta_path):
            try:
                import json
                with open(meta_path, "r") as f:
                    meta = json.load(f)
                    self.optimal_threshold = float(meta.get("failure_model", {}).get("optimal_threshold", 0.622))
            except Exception:
                self.optimal_threshold = 0.622

        if os.path.exists(prep_path):
            self.preprocessor = joblib.load(prep_path)
        if os.path.exists(fail_path):
            self.failure_model = joblib.load(fail_path)
        if os.path.exists(multi_path):
            self.multiclass_model = joblib.load(multi_path)
        if os.path.exists(enc_path):
            self.fault_encoder = joblib.load(enc_path)
        if os.path.exists(rul_path):
            self.rul_model = joblib.load(rul_path)
        if os.path.exists(anom_path):
            loaded_anom = joblib.load(anom_path)
            if isinstance(loaded_anom, dict):
                self.anomaly_model = loaded_anom.get("model")
                self.anomaly_threshold = loaded_anom.get("threshold", 0.0)
                self.anom_feature_means = loaded_anom.get("feature_means")
                self.anom_feature_stds = loaded_anom.get("feature_stds")
                self.anom_feature_names = loaded_anom.get("feature_names", [])
            else:
                self.anomaly_model = getattr(loaded_anom, "model", loaded_anom)
                self.anomaly_threshold = getattr(loaded_anom, "threshold", 0.0)
                self.anom_feature_means = None
                self.anom_feature_stds = None
                self.anom_feature_names = []

        self.explainer = ModelExplainer(fail_path, prep_path)

    def is_ready(self) -> bool:
        return all([self.preprocessor, self.failure_model, self.rul_model, self.anomaly_model])

    def predict_window(self, df_window: pd.DataFrame) -> Dict[str, Any]:
        """
        Run full multi-layer inference pipeline on a telemetry window.
        """
        if not self.is_ready():
            self._load_artifacts()

        if df_window is None or df_window.empty:
            raise ValueError("Telemetry window is empty. Cannot perform inference without sensor data.")

        df_window = df_window.copy()
        if "machine_id" not in df_window.columns:
            df_window["machine_id"] = "M17"
        if "machine_type" not in df_window.columns:
            df_window["machine_type"] = "CNC"
        if "timestamp" not in df_window.columns:
            df_window["timestamp"] = pd.Timestamp.now().strftime("%Y-%m-%d %H:%M:%S")

        # Build feature set
        df_feats = compute_time_series_features(df_window)
        latest_row = df_feats.iloc[-1:]

        numeric_cols, cat_cols = get_feature_columns()
        all_cols = numeric_cols + cat_cols

        X_proc = self.preprocessor.transform(latest_row[all_cols])

        # 1. Failure Prediction (Binary Classifier with calibrated threshold)
        fail_prob = float(self.failure_model.predict_proba(X_proc)[0, 1])
        if fail_prob < 0.25:
            risk_level = "Normal"
        elif fail_prob < self.optimal_threshold:
            risk_level = "Medium"
        elif fail_prob < 0.85:
            risk_level = "High"
        else:
            risk_level = "Critical"

        # 2. Multi-Class Root-Cause Fault Diagnosis
        fault_diagnosis = "Nominal Operation"
        fault_confidence = 1.0 - fail_prob
        all_fault_probs = {}

        if self.multiclass_model is not None and self.fault_encoder is not None:
            mc_probs = self.multiclass_model.predict_proba(X_proc)[0]
            top_idx = int(np.argmax(mc_probs))
            raw_class = self.fault_encoder.inverse_transform([top_idx])[0]
            fault_diagnosis = FAULT_LABELS_MAP.get(raw_class, raw_class)
            fault_confidence = float(mc_probs[top_idx])

            for idx, c in enumerate(self.fault_encoder.classes_):
                c_name = FAULT_LABELS_MAP.get(c, c)
                all_fault_probs[c_name] = round(float(mc_probs[idx]), 3)

        # 3. Remaining Useful Life (RUL)
        rul_pred = float(self.rul_model.predict(X_proc)[0])
        rul_hours = max(0.0, round(rul_pred, 1))

        # 4. Anomaly Detection & Sensor Attribution
        anom_scores = self.anomaly_model.decision_function(X_proc)
        raw_pred = self.anomaly_model.predict(X_proc)
        is_anomaly = bool(raw_pred[0] == -1 or anom_scores[0] < self.anomaly_threshold)
        anomaly_score = round(float(anom_scores[0]), 4)

        # Sensor attribution for anomaly
        affected_sensors = []
        if self.anom_feature_means is not None and self.anom_feature_stds is not None:
            x_vec = X_proc[0]
            z_scores = np.abs((x_vec - self.anom_feature_means) / self.anom_feature_stds)
            top_z_idx = np.argsort(z_scores)[::-1][:3]
            for z_i in top_z_idx:
                s_name = self.anom_feature_names[z_i] if z_i < len(self.anom_feature_names) else f"feature_{z_i}"
                s_name = s_name.replace("num__", "").replace("cat__", "")
                affected_sensors.append({
                    "sensor": s_name,
                    "deviation_sigma": round(float(z_scores[z_i]), 2)
                })

        # 5. SHAP Feature Attribution
        explanations = self.explainer.explain_instance(X_proc, top_k=5)
        waterfall_data = self.explainer.get_waterfall_payload(X_proc, top_k=6)

        machine_id = str(latest_row["machine_id"].values[0])
        machine_type = str(latest_row["machine_type"].values[0])
        timestamp = str(latest_row["timestamp"].values[0])

        vib_val = float(latest_row.get("vibration_rms", latest_row.get("vibration", pd.Series([0.0]))).values[0])
        temp_val = float(latest_row.get("temperature_motor", latest_row.get("temperature", pd.Series([0.0]))).values[0])
        pres_val = float(latest_row.get("pressure_level", latest_row.get("pressure", pd.Series([0.0]))).values[0])
        curr_val = float(latest_row.get("current_phase_avg", latest_row.get("current", pd.Series([0.0]))).values[0])
        rpm_val = float(latest_row.get("rpm", pd.Series([0.0])).values[0])
        amb_val = float(latest_row.get("ambient_temp", pd.Series([25.0])).values[0])
        hours_val = float(latest_row.get("hours_since_maintenance", latest_row.get("operating_hours", pd.Series([0.0]))).values[0])

        # 6. Composite Machine Health Index (0-100%)
        health_meta = compute_machine_health_index(
            failure_prob=fail_prob,
            is_anomaly=is_anomaly,
            anomaly_score=anomaly_score,
            vibration_rms=vib_val,
            temperature_motor=temp_val,
            ambient_temp=amb_val,
            rul_hours=rul_hours
        )

        # 7. Financial ROI Analytics
        financial_meta = calculate_financial_roi(
            estimated_repair_cost=4200.0 if risk_level in ["High", "Critical"] else 0.0,
            estimated_downtime_hours=14.0 if risk_level == "Critical" else (8.0 if risk_level == "High" else 2.0),
            is_high_risk=(risk_level in ["High", "Critical"])
        )

        return {
            "machine_id": machine_id,
            "machine_type": machine_type,
            "timestamp": timestamp,
            "failure_probability": round(fail_prob, 4),
            "risk_level": risk_level,
            "calibrated_threshold": self.optimal_threshold,
            "fault_diagnosis": fault_diagnosis,
            "fault_confidence": round(fault_confidence, 3),
            "all_fault_probabilities": all_fault_probs,
            "rul_hours": rul_hours,
            "is_anomaly": is_anomaly,
            "anomaly_score": anomaly_score,
            "affected_sensors": affected_sensors,
            "health_index": health_meta,
            "financial_roi": financial_meta,
            "top_contributing_features": explanations,
            "waterfall_data": waterfall_data,
            "model_version": self.model_version,
            "current_telemetry": {
                "vibration_rms": round(vib_val, 3),
                "temperature_motor": round(temp_val, 2),
                "ambient_temp": round(amb_val, 2),
                "thermal_delta": round(temp_val - amb_val, 2),
                "pressure_level": round(pres_val, 2),
                "current_phase_avg": round(curr_val, 2),
                "rpm": round(rpm_val, 1),
                "hours_since_maintenance": round(hours_val, 1)
            }
        }

