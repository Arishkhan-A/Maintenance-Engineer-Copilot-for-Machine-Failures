"""
Enterprise Remaining Useful Life (RUL) Regressor.
Estimates remaining machine operating hours before scheduled or forced downtime.
Benchmarks XGBoost, HistGradientBoosting, and Random Forest regressors.
"""

import json
import os
import joblib
import numpy as np
import pandas as pd
from datetime import datetime
from sklearn.ensemble import RandomForestRegressor, HistGradientBoostingRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
import xgboost as xgb

from src.features.build_features import compute_time_series_features, get_feature_columns
from src.data.preprocess import load_preprocessor
from src.models.train_failure import temporal_train_test_split
from src.data.load_data import get_cleaned_data

def train_rul_model(cleaned_csv: str = "data/processed/cleaned_telemetry.csv",
                    models_dir: str = "models") -> dict:
    """Train regression model to estimate machine Remaining Useful Life (RUL)."""
    os.makedirs(models_dir, exist_ok=True)
    if not os.path.exists(cleaned_csv):
        df_clean = get_cleaned_data(save_cache=True)
    else:
        df_clean = pd.read_csv(cleaned_csv)

    print(f"Loaded {len(df_clean)} records for RUL regression training...")
    df_feats = compute_time_series_features(df_clean)

    train_df, test_df = temporal_train_test_split(df_feats, test_ratio=0.20)
    numeric_cols, cat_cols = get_feature_columns()
    all_feature_cols = numeric_cols + cat_cols

    preprocessor = load_preprocessor(os.path.join(models_dir, "preprocessor.joblib"))

    X_train_proc = preprocessor.transform(train_df[all_feature_cols])
    y_train = train_df["rul_hours"].values.astype(float)

    X_test_proc = preprocessor.transform(test_df[all_feature_cols])
    y_test = test_df["rul_hours"].values.astype(float)

    # 1. XGBoost Regressor
    xgb_reg = xgb.XGBRegressor(
        n_estimators=200,
        max_depth=6,
        learning_rate=0.05,
        subsample=0.85,
        colsample_bytree=0.85,
        reg_alpha=0.1,
        reg_lambda=1.0,
        random_state=42,
        n_jobs=-1
    )
    xgb_reg.fit(X_train_proc, y_train)
    xgb_preds = np.clip(xgb_reg.predict(X_test_proc), 0.0, None)
    xgb_r2 = float(r2_score(y_test, xgb_preds))
    xgb_mae = float(mean_absolute_error(y_test, xgb_preds))
    xgb_rmse = float(np.sqrt(mean_squared_error(y_test, xgb_preds)))

    # 2. HistGradientBoosting Regressor
    hgb_reg = HistGradientBoostingRegressor(
        max_iter=150,
        max_depth=8,
        learning_rate=0.06,
        l2_regularization=0.5,
        random_state=42
    )
    hgb_reg.fit(X_train_proc, y_train)
    hgb_preds = np.clip(hgb_reg.predict(X_test_proc), 0.0, None)
    hgb_r2 = float(r2_score(y_test, hgb_preds))
    hgb_mae = float(mean_absolute_error(y_test, hgb_preds))
    hgb_rmse = float(np.sqrt(mean_squared_error(y_test, hgb_preds)))

    # 3. Random Forest Regressor
    rf_reg = RandomForestRegressor(
        n_estimators=120,
        max_depth=12,
        min_samples_leaf=3,
        random_state=42,
        n_jobs=-1
    )
    rf_reg.fit(X_train_proc, y_train)
    rf_preds = np.clip(rf_reg.predict(X_test_proc), 0.0, None)
    rf_r2 = float(r2_score(y_test, rf_preds))
    rf_mae = float(mean_absolute_error(y_test, rf_preds))
    rf_rmse = float(np.sqrt(mean_squared_error(y_test, rf_preds)))

    # Select champion by lowest RMSE / highest R2
    candidates = [
        ("XGBRegressor", xgb_reg, xgb_r2, xgb_mae, xgb_rmse),
        ("HistGradientBoostingRegressor", hgb_reg, hgb_r2, hgb_mae, hgb_rmse),
        ("RandomForestRegressor", rf_reg, rf_r2, rf_mae, rf_rmse)
    ]
    candidates.sort(key=lambda x: x[4]) # sort by RMSE ascending
    best_name, best_model, best_r2, best_mae, best_rmse = candidates[0]

    model_path = os.path.join(models_dir, "rul_model.joblib")
    joblib.dump(best_model, model_path)

    metadata_path = os.path.join(models_dir, "model_metadata.json")
    metadata = {}
    if os.path.exists(metadata_path):
        try:
            with open(metadata_path, "r") as f:
                metadata = json.load(f)
        except Exception:
            metadata = {}

    metadata["rul_model"] = {
        "model_type": best_name,
        "dataset_source": "predictive_maintenance_v3.csv",
        "trained_date": datetime.now().isoformat(),
        "train_samples": len(train_df),
        "test_samples": len(test_df),
        "metrics": {
            "mae_hours": round(best_mae, 2),
            "rmse_hours": round(best_rmse, 2),
            "r2_score": round(best_r2, 4)
        },
        "benchmarks": {
            "xgboost": {"mae": round(xgb_mae, 2), "rmse": round(xgb_rmse, 2), "r2": round(xgb_r2, 4)},
            "hist_gradient_boosting": {"mae": round(hgb_mae, 2), "rmse": round(hgb_rmse, 2), "r2": round(hgb_r2, 4)},
            "random_forest": {"mae": round(rf_mae, 2), "rmse": round(rf_rmse, 2), "r2": round(rf_r2, 4)}
        }
    }

    with open(metadata_path, "w") as f:
        json.dump(metadata, f, indent=2)

    print(f"\n--- RUL Regressor Champion ({best_name}) ---")
    print(f"MAE: {best_mae:.2f} hrs | RMSE: {best_rmse:.2f} hrs | R²: {best_r2:.4f}")
    return metadata["rul_model"]

if __name__ == "__main__":
    train_rul_model()

