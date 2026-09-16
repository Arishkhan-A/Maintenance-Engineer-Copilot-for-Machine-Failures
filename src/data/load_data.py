"""
Enterprise Data Ingestion, Cleaning & Validation Pipeline.
Built for real-world industrial telemetry datasets with missing values,
sensor dropouts, and multi-format timestamps. Eliminates look-ahead data leakage.
"""

import os
import re
import pandas as pd
import numpy as np
from typing import Dict, Any, Tuple

DEFAULT_DATA_PATH = "predictive_maintenance_v3.csv"
FALLBACK_DATA_PATH = "data/raw/machine_predictive_maintenance.csv"
PROCESSED_DATA_PATH = "data/processed/cleaned_telemetry.csv"

# Nominal industrial baselines used for startup imputation (avoids look-ahead bfill)
SENSOR_NOMINAL_BASELINES = {
    "vibration_rms": 1.80,
    "temperature_motor": 58.0,
    "current_phase_avg": 36.0,
    "pressure_level": 12.0,
    "rpm": 2200.0,
    "ambient_temp": 25.0,
    "hours_since_maintenance": 250.0
}

def parse_industrial_timestamp(ts_series: pd.Series) -> pd.Series:
    """
    Robust timestamp parser supporting dot-separated and colon-separated 12h/24h timestamps.
    """
    cleaned = ts_series.astype(str).str.replace(r"(\d{1,2})\.(\d{2})", r"\1:\2", regex=True)
    try:
        parsed = pd.to_datetime(cleaned, format="%d-%m-%Y %I:%M %p", errors="coerce")
    except Exception:
        parsed = pd.to_datetime(cleaned, errors="coerce")
    if parsed.isna().any():
        fallback = pd.to_datetime(cleaned, errors="coerce")
        parsed = parsed.fillna(fallback)
    return parsed

def load_raw_data(filepath: str = None) -> pd.DataFrame:
    """
    Load raw telemetry dataset. Defaults to predictive_maintenance_v3.csv if present.
    """
    target_path = filepath
    if not target_path or not os.path.exists(target_path):
        if os.path.exists(DEFAULT_DATA_PATH):
            target_path = DEFAULT_DATA_PATH
        elif os.path.exists(FALLBACK_DATA_PATH):
            target_path = FALLBACK_DATA_PATH
        else:
            raise FileNotFoundError(f"Neither {DEFAULT_DATA_PATH} nor {FALLBACK_DATA_PATH} found.")

    print(f"Loading raw dataset from: {target_path}")
    df = pd.read_csv(target_path)
    return df

def clean_and_impute_dataset(df: pd.DataFrame) -> pd.DataFrame:
    """
    Professional ETL pipeline without look-ahead leakage:
    1. Removes corrupted records with missing timestamps or asset IDs.
    2. Standardizes machine IDs to clean industrial tags (e.g. M01 - M20).
    3. Parses timestamps and establishes strict chronological ordering per machine.
    4. Performs temporal forward-fill per machine (holding last valid physical reading).
       Initial missing values use fixed engineering baselines instead of backward-fill,
       strictly preventing future information leakage into past timestamps.
    5. Normalizes targets, operational modes, and failure categories.
    """
    df = df.copy()

    # Normalize column names if needed
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

    # 1. Drop records where vital keys are missing
    df = df.dropna(subset=["timestamp", "machine_id"]).reset_index(drop=True)

    # 2. Standardize machine_id e.g. 1.0 -> 'M01', 'M1' -> 'M01'
    def format_machine_id(val):
        try:
            num = int(float(val))
            return f"M{num:02d}"
        except Exception:
            val_str = str(val).strip().upper()
            if val_str.startswith("M") and val_str[1:].isdigit():
                return f"M{int(val_str[1:]):02d}"
            return val_str

    df["machine_id"] = df["machine_id"].apply(format_machine_id)

    # 3. Parse timestamp and sort chronologically per machine
    df["timestamp"] = parse_industrial_timestamp(df["timestamp"])
    df = df.dropna(subset=["timestamp"]).sort_values(["machine_id", "timestamp"]).reset_index(drop=True)

    # 4. Standardize machine types and operational modes
    if "machine_type" in df.columns:
        df["machine_type"] = df["machine_type"].fillna("CNC").astype(str).str.strip()
    else:
        df["machine_type"] = "CNC"

    if "operating_mode" in df.columns:
        df["operating_mode"] = df["operating_mode"].fillna("normal").astype(str).str.lower().str.strip()
    else:
        df["operating_mode"] = "normal"

    # Default ambient temperature if absent
    if "ambient_temp" not in df.columns:
        df["ambient_temp"] = 25.0

    # 5. Temporal per-machine forward-fill imputation (strict causality: NO bfill)
    sensor_cols = ["vibration_rms", "temperature_motor", "current_phase_avg", "pressure_level", "rpm", "ambient_temp"]
    for col in sensor_cols:
        if col in df.columns:
            # Per-machine forward fill (represents sensor holding last valid reading)
            df[col] = df.groupby("machine_id")[col].ffill()
            # For startup missing before first reading, use physical baseline default (zero future leakage)
            default_val = SENSOR_NOMINAL_BASELINES.get(col, 0.0)
            df[col] = df[col].fillna(default_val)

    # Hours since maintenance
    if "hours_since_maintenance" in df.columns:
        df["hours_since_maintenance"] = df.groupby("machine_id")["hours_since_maintenance"].ffill().fillna(250.0)
    else:
        df["hours_since_maintenance"] = 250.0

    # 6. Targets
    if "failure_within_24h" in df.columns:
        df["failure_within_24h"] = df["failure_within_24h"].fillna(0).astype(int)
    else:
        df["failure_within_24h"] = 0

    if "rul_hours" in df.columns:
        df["rul_hours"] = df["rul_hours"].fillna(100.0).clip(lower=0.0)
    else:
        df["rul_hours"] = 100.0

    if "failure_type" in df.columns:
        df["failure_type"] = df["failure_type"].fillna("none").astype(str).str.lower().str.strip()
    else:
        df["failure_type"] = "none"

    if "estimated_repair_cost" in df.columns:
        df["estimated_repair_cost"] = df["estimated_repair_cost"].fillna(0.0).clip(lower=0.0)
    else:
        df["estimated_repair_cost"] = 0.0

    return df

def validate_data_quality(df: pd.DataFrame) -> Dict[str, Any]:
    """Comprehensive data quality audit report."""
    missing_report = df.isnull().sum().to_dict()
    total_missing = sum(missing_report.values())
    num_duplicates = int(df.duplicated(subset=["machine_id", "timestamp"]).sum())

    machines = df["machine_id"].unique().tolist()
    machine_types = df["machine_type"].value_counts().to_dict() if "machine_type" in df.columns else {}
    modes = df["operating_mode"].value_counts().to_dict() if "operating_mode" in df.columns else {}
    target_dist = df["failure_within_24h"].value_counts().to_dict() if "failure_within_24h" in df.columns else {}
    failure_types = df["failure_type"].value_counts().to_dict() if "failure_type" in df.columns else {}

    report = {
        "total_records": len(df),
        "unique_machines": len(machines),
        "machine_list": machines,
        "machine_types": machine_types,
        "operating_modes": modes,
        "missing_values_total": total_missing,
        "duplicate_timestamps": num_duplicates,
        "target_distribution": target_dist,
        "failure_types": failure_types,
        "is_production_clean": (total_missing == 0) and (num_duplicates == 0)
    }
    return report

def get_cleaned_data(save_cache: bool = True) -> pd.DataFrame:
    """Load, clean, validate, and optionally cache processed telemetry."""
    raw_df = load_raw_data()
    clean_df = clean_and_impute_dataset(raw_df)

    if save_cache:
        os.makedirs(os.path.dirname(PROCESSED_DATA_PATH), exist_ok=True)
        clean_df.to_csv(PROCESSED_DATA_PATH, index=False)
        # Also sync to data/raw/machine_predictive_maintenance.csv to keep canonical data aligned
        os.makedirs(os.path.dirname(FALLBACK_DATA_PATH), exist_ok=True)
        clean_df.to_csv(FALLBACK_DATA_PATH, index=False)
        print(f"Cleaned production dataset saved to: {PROCESSED_DATA_PATH} ({len(clean_df)} records)")

    return clean_df

if __name__ == "__main__":
    df_clean = get_cleaned_data()
    audit = validate_data_quality(df_clean)
    print("\n--- Data Quality Audit Report ---")
    print(f"Total Clean Records: {audit['total_records']}")
    print(f"Unique Machines ({audit['unique_machines']}): {audit['machine_list']}")
    print(f"Equipment Classes: {audit['machine_types']}")
    print(f"Operating Modes: {audit['operating_modes']}")
    print(f"Failure Distribution: {audit['target_distribution']}")
    print(f"Failure Types: {audit['failure_types']}")
    print(f"Production Clean Status: {audit['is_production_clean']}")

