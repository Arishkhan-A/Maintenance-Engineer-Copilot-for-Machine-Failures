"""
Enterprise Monitoring & Data/Feature Drift Detection Engine.
Tracks API latency, model inference latency, prediction distributions,
and calculates Kolmogorov-Smirnov (KS) drift statistics on sensor features.
"""

import time
import numpy as np
import pandas as pd
from typing import Dict, Any, List
from scipy.stats import ks_2samp

class ProductionDriftMonitor:
    """Production monitor tracking system latency, prediction distributions, and sensor drift."""

    def __init__(self, baseline_csv: str = "data/processed/cleaned_telemetry.csv"):
        self.baseline_csv = baseline_csv
        self.baseline_data: Dict[str, np.ndarray] = {}
        self.recent_predictions: List[Dict[str, Any]] = []
        self.latency_records: List[float] = []
        self.error_count: int = 0
        self.request_count: int = 0
        self.start_time = time.time()
        self._load_baseline()

    def _load_baseline(self):
        try:
            df = pd.read_csv(self.baseline_csv)
            sensor_cols = ["vibration_rms", "temperature_motor", "current_phase_avg", "pressure_level", "rpm"]
            for col in sensor_cols:
                if col in df.columns:
                    self.baseline_data[col] = df[col].dropna().values
        except Exception as e:
            print(f"Warning: Could not load baseline data for drift detection: {e}")

    def record_request(self, latency_ms: float, is_error: bool = False):
        """Record request metrics."""
        self.request_count += 1
        if is_error:
            self.error_count += 1
        self.latency_records.append(latency_ms)
        if len(self.latency_records) > 500:
            self.latency_records.pop(0)

    def record_prediction(self, prediction_result: Dict[str, Any]):
        """Record model inference results for distribution drift monitoring."""
        self.recent_predictions.append({
            "timestamp": prediction_result.get("timestamp"),
            "machine_id": prediction_result.get("machine_id"),
            "risk_level": prediction_result.get("risk_level"),
            "failure_probability": prediction_result.get("failure_probability", 0.0),
            "is_anomaly": prediction_result.get("is_anomaly", False),
            "rul_hours": prediction_result.get("rul_hours", 0.0)
        })
        if len(self.recent_predictions) > 300:
            self.recent_predictions.pop(0)

    def calculate_feature_drift(self, recent_df: pd.DataFrame) -> Dict[str, Any]:
        """
        Run two-sample Kolmogorov-Smirnov test on streaming telemetry vs baseline.
        Returns p-value and drift alert status (p < 0.05 indicates significant distribution drift).
        """
        drift_report = {}
        if not self.baseline_data or recent_df is None or len(recent_df) < 5:
            return {col: {"drift_detected": False, "p_value": 1.0, "statistic": 0.0} for col in ["vibration_rms", "temperature_motor", "pressure_level", "current_phase_avg"]}

        sensor_cols = ["vibration_rms", "temperature_motor", "current_phase_avg", "pressure_level"]
        for col in sensor_cols:
            sensor_series = recent_df.get(col, recent_df.get(col.replace("_rms", "").replace("_motor", "").replace("_phase_avg", "").replace("_level", "")))
            if sensor_series is not None and col in self.baseline_data:
                sample = sensor_series.dropna().values
                if len(sample) >= 5:
                    ks_stat, p_val = ks_2samp(self.baseline_data[col], sample)
                    drift_report[col] = {
                        "drift_detected": bool(p_val < 0.05),
                        "p_value": round(float(p_val), 4),
                        "ks_statistic": round(float(ks_stat), 4),
                        "status": "DRIFT_ALERT" if p_val < 0.05 else "STABLE"
                    }
                else:
                    drift_report[col] = {"drift_detected": False, "p_value": 1.0, "ks_statistic": 0.0, "status": "INSUFFICIENT_SAMPLE"}
        return drift_report

    def get_monitoring_summary(self) -> Dict[str, Any]:
        """Aggregate real-time performance and system health indicators."""
        lats = self.latency_records if self.latency_records else [0.0]
        p50 = float(np.percentile(lats, 50))
        p95 = float(np.percentile(lats, 95))
        p99 = float(np.percentile(lats, 99))

        risk_counts = {"Normal": 0, "Medium": 0, "High": 0, "Critical": 0}
        anomaly_count = 0
        for p in self.recent_predictions:
            lvl = p.get("risk_level", "Normal")
            risk_counts[lvl] = risk_counts.get(lvl, 0) + 1
            if p.get("is_anomaly"):
                anomaly_count += 1

        total_preds = len(self.recent_predictions)
        uptime_sec = round(time.time() - self.start_time, 1)

        return {
            "uptime_seconds": uptime_sec,
            "total_requests": self.request_count,
            "total_errors": self.error_count,
            "error_rate_percent": round((self.error_count / max(1, self.request_count)) * 100.0, 2),
            "latency_ms": {
                "p50": round(p50, 2),
                "p95": round(p95, 2),
                "p99": round(p99, 2),
                "mean": round(float(np.mean(lats)), 2)
            },
            "prediction_distribution": {
                "total_logged": total_preds,
                "risk_breakdown": risk_counts,
                "active_anomalies": anomaly_count,
                "anomaly_rate_percent": round((anomaly_count / max(1, total_preds)) * 100.0, 1) if total_preds > 0 else 0.0
            }
        }

# Global singleton monitor
global_drift_monitor = ProductionDriftMonitor()
