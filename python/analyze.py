# ============================================================
# Stage 3 — Data Analysis & KNN Modeling  (analyze.py)
# ============================================================
# Run from the repo root:  python python/analyze.py
# Or all stages at once:   python main.py
# ============================================================

import sys
from pathlib import Path

import numpy as np
import pandas as pd
from joblib import dump
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import (
    accuracy_score,
    classification_report,
    confusion_matrix,
    f1_score,
)
from sklearn.model_selection import cross_val_score, StratifiedKFold, train_test_split
from sklearn.neighbors import KNeighborsClassifier
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler


def analyze():
    # ------------------------------------------------------------------
    # 1. Load cleaned CSV
    # ------------------------------------------------------------------
    CSV_PATH = Path(__file__).resolve().parent.parent / "results" / "PYproperties.csv"
    if not CSV_PATH.exists():
        sys.exit(f"ERROR: Cleaned CSV not found at {CSV_PATH}. Run clean.py first.")

    df = pd.read_csv(CSV_PATH, encoding="utf-8-sig")
    print(f"Loaded {CSV_PATH.name}: {df.shape[0]} rows × {df.shape[1]} columns\n")
    print(df.describe(include="all").to_string())
    print()

    # ------------------------------------------------------------------
    # 2. Create balanced classification target (price_tier)
    # ------------------------------------------------------------------
    df = df.dropna(subset=["price_per_night"]).copy()
    df = df[df["price_per_night"] > 0].copy()

    df["price_tier"] = pd.qcut(
        df["price_per_night"],
        q=3,
        labels=["Budget", "Mid-range", "Luxury"],
    )
    print(f"Price tiers distribution:\n{df['price_tier'].value_counts().sort_index()}\n")

    # ------------------------------------------------------------------
    # 3. Select features (drop target, identifiers, raw price, URL, etc.)
    # ------------------------------------------------------------------
    NUMERIC_FEATURES = ["star_rating", "review_score", "review_count", "latitude", "longitude"]
    CATEGORICAL_FEATURES = ["search_city", "members", "property_type", "area"]

    NUMERIC_FEATURES = [c for c in NUMERIC_FEATURES if c in df.columns]
    CATEGORICAL_FEATURES = [c for c in CATEGORICAL_FEATURES if c in df.columns]

    feature_cols = NUMERIC_FEATURES + CATEGORICAL_FEATURES
    df_model = df[feature_cols + ["price_tier"]].dropna(subset=["price_tier"]).copy()

    for col in NUMERIC_FEATURES:
        df_model[col] = pd.to_numeric(df_model[col], errors="coerce")
        df_model[col] = df_model[col].fillna(df_model[col].median())

    for col in CATEGORICAL_FEATURES:
        df_model[col] = df_model[col].fillna("Unknown").astype(str)

    X = df_model[feature_cols]
    y = df_model["price_tier"]
    class_names = list(y.cat.categories) if hasattr(y, "cat") else sorted(y.unique())

    print(f"Features: {feature_cols}")
    print(f"Modeling dataset: {X.shape[0]} rows × {X.shape[1]} features")
    print(f"Target classes: {class_names}\n")

    # ------------------------------------------------------------------
    # 4. Stratified 80/20 train-test split
    # ------------------------------------------------------------------
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.20, random_state=42, stratify=y,
    )
    print(f"Train: {X_train.shape[0]}  |  Test: {X_test.shape[0]}\n")

    # ------------------------------------------------------------------
    # 5. Preprocessing pipeline (fit on train only)
    # ------------------------------------------------------------------
    preprocessor = ColumnTransformer(
        transformers=[
            ("num", StandardScaler(), NUMERIC_FEATURES),
            ("cat", OneHotEncoder(handle_unknown="ignore", sparse_output=False), CATEGORICAL_FEATURES),
        ]
    )

    # ------------------------------------------------------------------
    # 6. KNN hyperparameter tuning (K = 3, 5, 7 … 21)
    # ------------------------------------------------------------------
    k_values = list(range(3, 22, 2))
    k_scores = []

    cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)

    print("KNN tuning (5-fold CV):")
    for k in k_values:
        pipe = Pipeline([
            ("pre", preprocessor),
            ("knn", KNeighborsClassifier(n_neighbors=k)),
        ])
        scores = cross_val_score(pipe, X_train, y_train, cv=cv, scoring="accuracy")
        mean_score = scores.mean()
        k_scores.append(mean_score)
        print(f"  K={k:2d}  →  CV accuracy = {mean_score:.4f} (±{scores.std():.4f})")

    best_idx = int(np.argmax(k_scores))
    best_k = k_values[best_idx]
    print(f"\n  ★ Best K = {best_k}  (CV accuracy = {k_scores[best_idx]:.4f})\n")

    # ------------------------------------------------------------------
    # 7. Train final KNN + benchmark Random Forest
    # ------------------------------------------------------------------
    knn_pipe = Pipeline([
        ("pre", preprocessor),
        ("knn", KNeighborsClassifier(n_neighbors=best_k)),
    ])
    knn_pipe.fit(X_train, y_train)
    y_pred_knn = knn_pipe.predict(X_test)

    rf_pipe = Pipeline([
        ("pre", preprocessor),
        ("rf", RandomForestClassifier(n_estimators=200, random_state=42)),
    ])
    rf_pipe.fit(X_train, y_train)
    y_pred_rf = rf_pipe.predict(X_test)

    # ------------------------------------------------------------------
    # 8. Print classification reports
    # ------------------------------------------------------------------
    print("=" * 60)
    print(f"  KNN  (K={best_k})  — Test Set Results")
    print("=" * 60)
    print(classification_report(y_test, y_pred_knn, target_names=class_names))

    knn_acc = accuracy_score(y_test, y_pred_knn)
    knn_f1 = f1_score(y_test, y_pred_knn, average="macro")

    print("=" * 60)
    print("  Random Forest  — Test Set Results")
    print("=" * 60)
    print(classification_report(y_test, y_pred_rf, target_names=class_names))

    rf_acc = accuracy_score(y_test, y_pred_rf)
    rf_f1 = f1_score(y_test, y_pred_rf, average="macro")

    print(f"Summary:  KNN acc={knn_acc:.4f} F1={knn_f1:.4f}  |  RF acc={rf_acc:.4f} F1={rf_f1:.4f}\n")

    # ------------------------------------------------------------------
    # 9. Save artifacts for Stage 4 (visualize.py)
    # ------------------------------------------------------------------
    OUTPUT_DIR = Path(__file__).resolve().parent.parent / "outputs"
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    artifact_path = OUTPUT_DIR / "model_results.joblib"

    artifacts = {
        "y_test": np.array(y_test),
        "y_pred_knn": np.array(y_pred_knn),
        "y_pred_rf": np.array(y_pred_rf),
        "class_names": class_names,
        "k_values": k_values,
        "k_scores": k_scores,
        "best_k": best_k,
        "knn_accuracy": knn_acc,
        "knn_f1": knn_f1,
        "rf_accuracy": rf_acc,
        "rf_f1": rf_f1,
        "confusion_matrix_knn": confusion_matrix(y_test, y_pred_knn, labels=class_names),
    }

    dump(artifacts, artifact_path)
    print(f"Saved model artifacts → {artifact_path}")


if __name__ == "__main__":
    analyze()
