"""
Tier-1 Multi-Class Fault Diagnosis Classifier.
Benchmarks HistGradientBoosting and XGBoost multi-class classifiers with
balanced loss weighting to diagnose root-cause failure mechanisms:
- Bearing Degradation
- Motor Overheating & Thermal Runaway
- Hydraulic Pressure Loss & Seal Rupture
- Electrical Power Inverter Breakdown
- Nominal Operational State
"""

import json
import os
import joblib
import numpy as np
import pandas as pd
from datetime import datetime
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.preprocessing import LabelEncoder
from sklearn.metrics import classification_report, f1_score, precision_score, recall_score, accuracy_score
import xgboost as xgb

from src.features.build_features import compute_time_series_features, get_feature_columns
from src.data.preprocess import load_preprocessor
from src.models.train_failure import temporal_train_test_split
from src.data.load_data import get_cleaned_data

FAULT_LABELS_MAP = {
    "none": "Nominal Operation",
    "bearing": "Bearing Degradation",
    "motor_overheat": "Motor Overheating",
    "hydraulic": "Hydraulic Fault",
    "electrical": "Electrical Power Surge"
}

def train_multiclass_fault_model(cleaned_csv: str = "data/processed/cleaned_telemetry.csv",
                                 models_dir: str = "models") -> dict:
    """Train multi-class model benchmarking XGBoost and HistGradientBoosting."""
    os.makedirs(models_dir, exist_ok=True)
    if not os.path.exists(cleaned_csv):
        df_clean = get_cleaned_data(save_cache=True)
    else:
        df_clean = pd.read_csv(cleaned_csv)

    print(f"Loaded {len(df_clean)} records for multi-class fault training...")
    df_feats = compute_time_series_features(df_clean)

    train_df, test_df = temporal_train_test_split(df_feats, test_ratio=0.20)
    numeric_cols, cat_cols = get_feature_columns()
    all_feature_cols = numeric_cols + cat_cols

    preprocessor = load_preprocessor(os.path.join(models_dir, "preprocessor.joblib"))

    X_train_proc = preprocessor.transform(train_df[all_feature_cols])
    X_test_proc = preprocessor.transform(test_df[all_feature_cols])

    # Encode target fault types
    label_encoder = LabelEncoder()
    y_train = label_encoder.fit_transform(train_df["failure_type"].astype(str))
    y_test = label_encoder.transform(test_df["failure_type"].astype(str))

    # Calculate smoothed class weights for balanced learning
    classes, counts = np.unique(y_train, return_counts=True)
    total_samples = len(y_train)
    weights = {c: (total_samples / (len(classes) * count)) ** 0.85 for c, count in zip(classes, counts)}
    sample_weights = np.array([weights[y] for y in y_train])

    # 1. HistGradientBoosting Classifier
    hgb_clf = HistGradientBoostingClassifier(
        max_iter=160,
        max_depth=9,
        learning_rate=0.07,
        l2_regularization=0.2,
        random_state=42
    )
    hgb_clf.fit(X_train_proc, y_train, sample_weight=sample_weights)
    hgb_pred = hgb_clf.predict(X_test_proc)
    hgb_macro_f1 = float(f1_score(y_test, hgb_pred, average="macro", zero_division=0))

    # 2. XGBoost Multi-Class Classifier
    xgb_mc = xgb.XGBClassifier(
        objective="multi:softprob",
        num_class=len(classes),
        n_estimators=180,
        max_depth=6,
        learning_rate=0.06,
        subsample=0.85,
        colsample_bytree=0.85,
        random_state=42,
        n_jobs=-1
    )
    xgb_mc.fit(X_train_proc, y_train, sample_weight=sample_weights)
    xgb_pred = xgb_mc.predict(X_test_proc)
    xgb_macro_f1 = float(f1_score(y_test, xgb_pred, average="macro", zero_division=0))

    # Select champion by Macro F1 (gives equal weight to minority fault classes like hydraulic)
    if xgb_macro_f1 >= hgb_macro_f1:
        champion_clf = xgb_mc
        champion_pred = xgb_pred
        champion_name = "XGBClassifier"
        champion_macro_f1 = xgb_macro_f1
    else:
        champion_clf = hgb_clf
        champion_pred = hgb_pred
        champion_name = "HistGradientBoostingClassifier"
        champion_macro_f1 = hgb_macro_f1

    weighted_f1 = float(f1_score(y_test, champion_pred, average="weighted", zero_division=0))
    accuracy = float(accuracy_score(y_test, champion_pred))

    # Save models
    model_path = os.path.join(models_dir, "multiclass_model.joblib")
    encoder_path = os.path.join(models_dir, "fault_label_encoder.joblib")
    joblib.dump(champion_clf, model_path)
    joblib.dump(label_encoder, encoder_path)

    # Class-wise report
    class_names = [FAULT_LABELS_MAP.get(c, c) for c in label_encoder.classes_]
    report = classification_report(y_test, champion_pred, target_names=class_names, output_dict=True, zero_division=0)

    metadata_path = os.path.join(models_dir, "model_metadata.json")
    metadata = {}
    if os.path.exists(metadata_path):
        try:
            with open(metadata_path, "r") as f:
                metadata = json.load(f)
        except Exception:
            metadata = {}

    metadata["multiclass_fault_model"] = {
        "model_type": champion_name,
        "dataset_source": "predictive_maintenance_v3.csv",
        "trained_date": datetime.now().isoformat(),
        "train_samples": len(train_df),
        "test_samples": len(test_df),
        "classes": class_names,
        "metrics": {
            "accuracy": round(accuracy, 4),
            "macro_f1": round(champion_macro_f1, 4),
            "weighted_f1": round(weighted_f1, 4),
            "per_class": {
                name: {
                    "precision": round(report[name]["precision"], 4),
                    "recall": round(report[name]["recall"], 4),
                    "f1": round(report[name]["f1-score"], 4)
                }
                for name in class_names if name in report
            }
        },
        "benchmarks": {
            "xgboost_macro_f1": round(xgb_macro_f1, 4),
            "hist_gradient_boosting_macro_f1": round(hgb_macro_f1, 4)
        }
    }

    with open(metadata_path, "w") as f:
        json.dump(metadata, f, indent=2)

    print(f"\n--- Multi-Class Fault Diagnosis Champion ({champion_name}) ---")
    print(f"Accuracy: {accuracy:.4f} | Macro F1: {champion_macro_f1:.4f} | Weighted F1: {weighted_f1:.4f}")
    for name in class_names:
        if name in report:
            print(f"  [{name}]: F1={report[name]['f1-score']:.4f}, Recall={report[name]['recall']:.4f}, Precision={report[name]['precision']:.4f}")

    return metadata["multiclass_fault_model"]

if __name__ == "__main__":
    train_multiclass_fault_model()

