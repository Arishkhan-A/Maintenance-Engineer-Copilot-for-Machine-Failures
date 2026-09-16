"""
Enterprise Feature Engineering Pipeline for Industrial Machine Telemetry.
Calculates time-series lags, rolling statistics, thermodynamics, kinematics,
and operating mode features without target leakage.
"""

import os
import numpy as np
import pandas as pd
from typing import Tuple, List

def compute_time_series_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    Construct multi-scale time-series, rate-of-change, rolling statistics,
    thermodynamic differentials, and kinematic interaction features grouped per machine.
    Zero future leakage: initial lags fill forward or fallback to current reading without bfill.
    """
    df = df.copy()

    # Normalize column names in case legacy names are passed
    col_mapping = {
        "vibration": "vibration_rms",
        "temperature": "temperature_motor",
        "current": "current_phase_avg",
        "pressure": "pressure_level",
        "load": "operating_mode",
        "operating_hours": "hours_since_maintenance",
        "rul": "rul_hours"
    }
    for old_col, new_col in col_mapping.items():
        if old_col in df.columns and new_col not in df.columns:
            df.rename(columns={old_col: new_col}, inplace=True)

    if "ambient_temp" not in df.columns:
        df["ambient_temp"] = 25.0
    if "operating_mode" not in df.columns:
        df["operating_mode"] = "normal"
    if "hours_since_maintenance" not in df.columns:
        df["hours_since_maintenance"] = 250.0
    if "machine_id" not in df.columns:
        df["machine_id"] = "M01"
    if "timestamp" not in df.columns:
        df["timestamp"] = pd.Timestamp.now().strftime("%Y-%m-%d %H:%M:%S")

    df = df.sort_values(["machine_id", "timestamp"]).reset_index(drop=True)

    sensor_cols = ["vibration_rms", "temperature_motor", "current_phase_avg", "pressure_level", "rpm"]

    # 1. Rolling statistics, Lags & Trends per machine
    for col in sensor_cols:
        if col in df.columns:
            # Rolling 5-step mean and std
            df[f"{col}_roll_mean_5"] = (
                df.groupby("machine_id")[col]
                .transform(lambda s: s.rolling(5, min_periods=1).mean())
            )
            df[f"{col}_roll_std_5"] = (
                df.groupby("machine_id")[col]
                .transform(lambda s: s.rolling(5, min_periods=1).std().fillna(0.0))
            )
            # Rolling 10-step mean, min, max
            df[f"{col}_roll_mean_10"] = (
                df.groupby("machine_id")[col]
                .transform(lambda s: s.rolling(10, min_periods=1).mean())
            )
            df[f"{col}_roll_max_10"] = (
                df.groupby("machine_id")[col]
                .transform(lambda s: s.rolling(10, min_periods=1).max())
            )
            df[f"{col}_roll_min_10"] = (
                df.groupby("machine_id")[col]
                .transform(lambda s: s.rolling(10, min_periods=1).min())
            )

            # Lags (1, 3, 5 periods) - NO bfill to prevent future look-ahead leakage
            df[f"{col}_lag_1"] = df.groupby("machine_id")[col].shift(1).fillna(df[col])
            df[f"{col}_lag_3"] = df.groupby("machine_id")[col].shift(3).fillna(df[col])
            df[f"{col}_lag_5"] = df.groupby("machine_id")[col].shift(5).fillna(df[col])

            # First difference (rate of change)
            df[f"{col}_delta"] = (df[col] - df[f"{col}_lag_1"]).fillna(0.0)

            # Trend / slope proxies
            df[f"{col}_trend_5"] = ((df[col] - df[f"{col}_lag_5"]) / 5.0).fillna(0.0)

            # Local deviation / Z-score from rolling mean
            df[f"{col}_deviation"] = (
                (df[col] - df[f"{col}_roll_mean_5"]) / (df[f"{col}_roll_std_5"] + 1e-4)
            ).clip(-4.0, 4.0).fillna(0.0)

    # 2. Thermodynamics & Physics Features
    # Motor differential over ambient temperature (thermal gradient)
    df["temp_differential"] = df["temperature_motor"] - df["ambient_temp"]
    # Kinematic vibration-to-rpm ratio
    df["vib_to_rpm"] = df["vibration_rms"] / (df["rpm"] + 1e-5)
    # Power factor proxy (Current * RPM / 1000)
    df["power_est"] = (df["current_phase_avg"] * df["rpm"]) / 1000.0
    # Pressure stability index (instantaneous pressure relative to rolling mean)
    pres_mean = df.get("pressure_level_roll_mean_5", df["pressure_level"])
    df["pressure_stability"] = df["pressure_level"] / (pres_mean + 1e-5)
    # Cumulative machine stress accumulator (hours * vibration)
    df["maintenance_stress"] = df["hours_since_maintenance"] * (df["vibration_rms"] + 0.1)

    # 3. Industrial Degradation & Operating Cycle Features
    df["vib_severity"] = np.maximum(0.0, df["vibration_rms"] - 1.8)
    df["temp_severity"] = np.maximum(0.0, df["temperature_motor"] - 55.0)
    df["degradation_energy"] = df["vib_severity"] * df["temp_severity"]
    hours_diff = df.groupby("machine_id")["hours_since_maintenance"].diff().fillna(0)
    df["cycle_id"] = (hours_diff < -1.0).cumsum()
    df["cycle_elapsed"] = df.groupby(["machine_id", "cycle_id"])["hours_since_maintenance"].transform(lambda s: s - s.min())

    return df

def get_feature_columns() -> Tuple[List[str], List[str]]:
    """Return numeric and categorical feature lists for model training."""
    numeric_cols = [
        "vibration_rms", "temperature_motor", "current_phase_avg", "pressure_level", "rpm",
        "ambient_temp", "hours_since_maintenance", "temp_differential", "vib_to_rpm", "power_est",
        "pressure_stability", "maintenance_stress", "vib_severity", "temp_severity", "degradation_energy", "cycle_elapsed",
        "vibration_rms_roll_mean_5", "vibration_rms_roll_std_5", "vibration_rms_roll_mean_10", "vibration_rms_roll_max_10", "vibration_rms_roll_min_10",
        "vibration_rms_lag_1", "vibration_rms_lag_3", "vibration_rms_lag_5", "vibration_rms_delta", "vibration_rms_trend_5", "vibration_rms_deviation",
        "temperature_motor_roll_mean_5", "temperature_motor_roll_std_5", "temperature_motor_roll_mean_10", "temperature_motor_roll_max_10", "temperature_motor_roll_min_10",
        "temperature_motor_lag_1", "temperature_motor_lag_3", "temperature_motor_lag_5", "temperature_motor_delta", "temperature_motor_trend_5", "temperature_motor_deviation",
        "current_phase_avg_roll_mean_5", "current_phase_avg_roll_std_5", "current_phase_avg_roll_mean_10", "current_phase_avg_roll_max_10", "current_phase_avg_roll_min_10",
        "current_phase_avg_lag_1", "current_phase_avg_lag_3", "current_phase_avg_lag_5", "current_phase_avg_delta", "current_phase_avg_trend_5", "current_phase_avg_deviation",
        "pressure_level_roll_mean_5", "pressure_level_roll_std_5", "pressure_level_roll_mean_10", "pressure_level_roll_max_10", "pressure_level_roll_min_10",
        "pressure_level_lag_1", "pressure_level_lag_3", "pressure_level_lag_5", "pressure_level_delta", "pressure_level_trend_5", "pressure_level_deviation",
        "rpm_roll_mean_5", "rpm_roll_std_5", "rpm_roll_mean_10", "rpm_roll_max_10", "rpm_roll_min_10",
        "rpm_lag_1", "rpm_lag_3", "rpm_lag_5", "rpm_delta", "rpm_trend_5", "rpm_deviation"
    ]
    categorical_cols = ["machine_type", "operating_mode"]
    return numeric_cols, categorical_cols


def generate_and_save_features(input_cleaned_csv: str = "data/processed/cleaned_telemetry.csv",
                                output_feature_csv: str = "data/processed/engineered_features.csv") -> pd.DataFrame:
    """Build features from cleaned dataset and persist engineered feature table."""
    if not os.path.exists(input_cleaned_csv):
        from src.data.load_data import get_cleaned_data
        df_clean = get_cleaned_data(save_cache=True)
    else:
        df_clean = pd.read_csv(input_cleaned_csv)

    df_feats = compute_time_series_features(df_clean)
    os.makedirs(os.path.dirname(output_feature_csv), exist_ok=True)
    df_feats.to_csv(output_feature_csv, index=False)
    print(f"Engineered {df_feats.shape[1]} features across {len(df_feats)} records -> {output_feature_csv}")
    return df_feats

if __name__ == "__main__":
    generate_and_save_features()

