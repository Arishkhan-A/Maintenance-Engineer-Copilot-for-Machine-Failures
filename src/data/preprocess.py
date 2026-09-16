"""Data preprocessing pipeline using Scikit-Learn transformers."""
import os
import joblib
import pandas as pd
from typing import Tuple, List
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import StandardScaler, OneHotEncoder

def create_preprocessor(numeric_features: List[str], categorical_features: List[str]) -> ColumnTransformer:
    """Create reproducible preprocessing pipeline for numeric and categorical features."""
    numeric_pipe = Pipeline([
        ("imputer", SimpleImputer(strategy="median")),
        ("scaler", StandardScaler())
    ])

    categorical_pipe = Pipeline([
        ("imputer", SimpleImputer(strategy="most_frequent")),
        ("encoder", OneHotEncoder(handle_unknown="ignore", sparse_output=False))
    ])

    preprocessor = ColumnTransformer(
        transformers=[
            ("num", numeric_pipe, numeric_features),
            ("cat", categorical_pipe, categorical_features)
        ],
        remainder="drop"
    )
    return preprocessor

def save_preprocessor(preprocessor: ColumnTransformer, filepath: str = "models/preprocessor.joblib"):
    """Persist fitted preprocessor artifact to disk."""
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    joblib.dump(preprocessor, filepath)
    print(f"Saved preprocessor artifact to {filepath}")

def load_preprocessor(filepath: str = "models/preprocessor.joblib") -> ColumnTransformer:
    """Load fitted preprocessor artifact."""
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"Preprocessor artifact not found at {filepath}")
    return joblib.load(filepath)
