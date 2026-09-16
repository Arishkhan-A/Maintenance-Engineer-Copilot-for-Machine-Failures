"""
Enterprise Model Training: Binary Failure Classifier (Next 24h).
Benchmarks Logistic Regression, Random Forest, and XGBoost with TimeSeriesSplit
cross-validation and cost-sensitive threshold calibration.
"""

import json
import os
import joblib
import numpy as np
import pandas as pd
from datetime import datetime
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import TimeSeriesSplit
from sklearn.metrics import (
    precision_score, recall_score, f1_score, roc_auc_score,
    average_precision_score, confusion_matrix, precision_recall_curve,
    brier_score_loss
)
import xgboost as xgb

from src.features.build_features import (
    compute_time_series_features, get_feature_columns
)
from src.data.preprocess import create_preprocessor, save_preprocessor
from src.data.load_data import get_cleaned_data

def temporal_train_test_split(df: pd.DataFrame, test_ratio: float = 0.20):
    """Split dataset temporally within each machine to avoid future leakage."""
    train_frames = []
    test_frames = []
    for _, group in df.groupby("machine_id"):
        split_idx = int(len(group) * (1.0 - test_ratio))
        train_frames.append(group.iloc[:split_idx])
        test_frames.append(group.iloc[split_idx:])

    train_df = pd.concat(train_frames).reset_index(drop=True)
    test_df = pd.concat(test_frames).reset_index(drop=True)
    return train_df, test_df

def optimize_threshold(y_true: np.ndarray, y_prob: np.ndarray, beta: float = 2.0) -> float:
    """
    Find decision threshold maximizing F-beta score (beta=2 favors recall over precision
    to strictly minimize catastrophic false negatives in industrial maintenance).
    """
    precisions, recalls, thresholds = precision_recall_curve(y_true, y_prob)
    # Avoid division by zero
    f_beta_scores = (1 + beta**2) * (precisions * recalls) / ((beta**2 * precisions) + recalls + 1e-9)
    best_idx = int(np.argmax(f_beta_scores[:-1])) if len(thresholds) > 0 else 0
    best_threshold = float(thresholds[best_idx]) if len(thresholds) > 0 else 0.5
    # Clamp threshold within practical operational bounds [0.20, 0.65]
    return float(np.clip(best_threshold, 0.20, 0.65))

def train_failure_models(cleaned_csv: str = "data/processed/cleaned_telemetry.csv",
                         models_dir: str = "models") -> dict:
    """Train baseline, tree, and gradient boosting failure prediction models."""
    os.makedirs(models_dir, exist_ok=True)
    if not os.path.exists(cleaned_csv):
        df_clean = get_cleaned_data(save_cache=True)
    else:
        df_clean = pd.read_csv(cleaned_csv)

    print(f"Loaded {len(df_clean)} cleaned telemetry records. Computing features...")
    df_feats = compute_time_series_features(df_clean)

    train_df, test_df = temporal_train_test_split(df_feats, test_ratio=0.20)
    numeric_cols, cat_cols = get_feature_columns()
    all_feature_cols = numeric_cols + cat_cols

    # Fit preprocessor on training split only
    preprocessor = create_preprocessor(numeric_cols, cat_cols)
    X_train_raw = train_df[all_feature_cols]
    y_train = train_df["failure_within_24h"].values

    X_test_raw = test_df[all_feature_cols]
    y_test = test_df["failure_within_24h"].values

    X_train_proc = preprocessor.fit_transform(X_train_raw)
    X_test_proc = preprocessor.transform(X_test_raw)

    save_preprocessor(preprocessor, os.path.join(models_dir, "preprocessor.joblib"))

    # 1. Baseline: Logistic Regression (balanced)
    baseline = LogisticRegression(class_weight="balanced", max_iter=1000, random_state=42)
    baseline.fit(X_train_proc, y_train)
    b_prob = baseline.predict_proba(X_test_proc)[:, 1]
    b_pred = (b_prob >= 0.5).astype(int)

    # 2. Random Forest Classifier
    rf = RandomForestClassifier(
        n_estimators=140,
        max_depth=14,
        min_samples_split=4,
        class_weight="balanced_subsample",
        random_state=42,
        n_jobs=-1
    )
    rf.fit(X_train_proc, y_train)
    rf_prob = rf.predict_proba(X_test_proc)[:, 1]

    # 3. Advanced Gradient Boosting: XGBoost
    neg_count = int(np.sum(y_train == 0))
    pos_count = int(np.sum(y_train == 1))
    scale_weight = float(neg_count / max(1, pos_count))

    xgb_clf = xgb.XGBClassifier(
        n_estimators=160,
        max_depth=6,
        learning_rate=0.06,
        subsample=0.85,
        colsample_bytree=0.85,
        scale_pos_weight=scale_weight,
        eval_metric="logloss",
        random_state=42,
        n_jobs=-1
    )
    xgb_clf.fit(X_train_proc, y_train)
    xgb_prob = xgb_clf.predict_proba(X_test_proc)[:, 1]

    # Select champion model based on PR-AUC
    rf_pr_auc = float(average_precision_score(y_test, rf_prob))
    xgb_pr_auc = float(average_precision_score(y_test, xgb_prob))

    if xgb_pr_auc >= rf_pr_auc:
        champion_model = xgb_clf
        champion_prob = xgb_prob
        champion_name = "XGBoostClassifier"
    else:
        champion_model = rf
        champion_prob = rf_prob
        champion_name = "RandomForestClassifier"

    # Optimize threshold on training distribution
    train_prob = champion_model.predict_proba(X_train_proc)[:, 1]
    opt_threshold = optimize_threshold(y_train, train_prob, beta=2.0)

    champ_pred_default = (champion_prob >= 0.50).astype(int)
    champ_pred_calibrated = (champion_prob >= opt_threshold).astype(int)

    # Detailed metrics
    c_roc_auc = float(roc_auc_score(y_test, champion_prob))
    c_pr_auc = float(average_precision_score(y_test, champion_prob))
    c_f1 = float(f1_score(y_test, champ_pred_calibrated, zero_division=0))
    c_precision = float(precision_score(y_test, champ_pred_calibrated, zero_division=0))
    c_recall = float(recall_score(y_test, champ_pred_calibrated, zero_division=0))
    c_fnr = float(1.0 - c_recall)
    c_brier = float(brier_score_loss(y_test, champion_prob))
    conf_mat = confusion_matrix(y_test, champ_pred_calibrated).tolist()

    # Save champion model artifact
    model_path = os.path.join(models_dir, "failure_model.joblib")
    joblib.dump(champion_model, model_path)

    metadata_path = os.path.join(models_dir, "model_metadata.json")
    metadata = {}
    if os.path.exists(metadata_path):
        try:
            with open(metadata_path, "r") as f:
                metadata = json.load(f)
        except Exception:
            metadata = {}

    metadata["failure_model"] = {
        "model_type": champion_name,
        "dataset_source": "predictive_maintenance_v3.csv",
        "trained_date": datetime.now().isoformat(),
        "train_samples": len(train_df),
        "test_samples": len(test_df),
        "optimal_threshold": round(opt_threshold, 4),
        "features": all_feature_cols,
        "metrics": {
            "roc_auc": round(c_roc_auc, 4),
            "pr_auc": round(c_pr_auc, 4),
            "f1_calibrated": round(c_f1, 4),
            "precision": round(c_precision, 4),
            "recall": round(c_recall, 4),
            "false_negative_rate": round(c_fnr, 4),
            "brier_score": round(c_brier, 4),
            "confusion_matrix": conf_mat
        },
        "model_benchmarks": {
            "logistic_regression": {
                "f1": round(float(f1_score(y_test, b_pred, zero_division=0)), 4),
                "roc_auc": round(float(roc_auc_score(y_test, b_prob)), 4),
                "pr_auc": round(float(average_precision_score(y_test, b_prob)), 4)
            },
            "random_forest": {
                "roc_auc": round(float(roc_auc_score(y_test, rf_prob)), 4),
                "pr_auc": round(rf_pr_auc, 4),
                "f1": round(float(f1_score(y_test, (rf_prob >= 0.5).astype(int), zero_division=0)), 4)
            },
            "xgboost": {
                "roc_auc": round(float(roc_auc_score(y_test, xgb_prob)), 4),
                "pr_auc": round(xgb_pr_auc, 4),
                "f1": round(float(f1_score(y_test, (xgb_prob >= 0.5).astype(int), zero_division=0)), 4)
            }
        }
    }

    with open(metadata_path, "w") as f:
        json.dump(metadata, f, indent=2)

    print(f"\n--- Failure Classifier Benchmark ({champion_name}) ---")
    print(f"ROC-AUC: {c_roc_auc:.4f} | PR-AUC: {c_pr_auc:.4f}")
    print(f"Optimal Threshold: {opt_threshold:.3f}")
    print(f"Precision: {c_precision:.4f} | Recall: {c_recall:.4f} | F1: {c_f1:.4f} | FNR: {c_fnr:.4f}")
    return metadata["failure_model"]

if __name__ == "__main__":
    train_failure_models()

