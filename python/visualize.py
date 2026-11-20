# ============================================================
# Stage 4 — EDA & Model Evaluation Charts  (visualize.py)
# ============================================================
# Run from the repo root:  python python/visualize.py
# Or all stages at once:   python main.py
# ============================================================

import sys
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
from joblib import load
from sklearn.metrics import ConfusionMatrixDisplay


def visualize():
    # ------------------------------------------------------------------
    # 0. Paths
    # ------------------------------------------------------------------
    BASE_DIR = Path(__file__).resolve().parent.parent
    CSV_PATH = BASE_DIR / "results" / "PYproperties.csv"
    ARTIFACT_PATH = BASE_DIR / "outputs" / "model_results.joblib"
    CHART_DIR = BASE_DIR / "outputs" / "charts"
    CHART_DIR.mkdir(parents=True, exist_ok=True)

    DPI = 300

    if not CSV_PATH.exists():
        sys.exit(f"ERROR: {CSV_PATH} not found. Run clean.py first.")
    if not ARTIFACT_PATH.exists():
        sys.exit(f"ERROR: {ARTIFACT_PATH} not found. Run analyze.py first.")

    # ------------------------------------------------------------------
    # 1. Load data
    # ------------------------------------------------------------------
    df = pd.read_csv(CSV_PATH, encoding="utf-8-sig")
    results = load(ARTIFACT_PATH)

    df["price_per_night"] = pd.to_numeric(df["price_per_night"], errors="coerce")
    df_price = df.dropna(subset=["price_per_night"])
    df_price = df_price[df_price["price_per_night"] > 0]

    sns.set_theme(style="whitegrid", palette="muted")

    # ------------------------------------------------------------------
    # Chart 1 — Price Distribution (histogram + boxplot side by side)
    # ------------------------------------------------------------------
    fig, axes = plt.subplots(1, 2, figsize=(14, 5))

    sns.histplot(df_price["price_per_night"], kde=True, bins=30, color="steelblue", ax=axes[0])
    axes[0].set_title("Price Per Night — Distribution", fontsize=12, fontweight="bold")
    axes[0].set_xlabel("Price (EUR)")
    axes[0].set_ylabel("Count")

    sns.boxplot(x=df_price["price_per_night"], color="steelblue", ax=axes[1])
    axes[1].set_title("Price Per Night — Boxplot", fontsize=12, fontweight="bold")
    axes[1].set_xlabel("Price (EUR)")

    fig.suptitle("Chart 1 — Price Distribution & Spread", fontsize=14, fontweight="bold", y=1.02)
    fig.tight_layout()
    fig.savefig(CHART_DIR / "1_price_distribution.png", dpi=DPI, bbox_inches="tight")
    print("Saved: 1_price_distribution.png")
    plt.close(fig)

    # ------------------------------------------------------------------
    # Chart 2 — Confusion Matrix (KNN)
    # ------------------------------------------------------------------
    class_names = results["class_names"]
    cm = results["confusion_matrix_knn"]
    best_k = results["best_k"]

    fig, ax = plt.subplots(figsize=(7, 6))
    disp = ConfusionMatrixDisplay(confusion_matrix=cm, display_labels=class_names)
    disp.plot(ax=ax, cmap="Blues", colorbar=True)
    ax.set_title(f"Chart 2 — KNN Confusion Matrix (K={best_k})", fontsize=13, fontweight="bold")
    fig.tight_layout()
    fig.savefig(CHART_DIR / "2_confusion_matrix_knn.png", dpi=DPI, bbox_inches="tight")
    print("Saved: 2_confusion_matrix_knn.png")
    plt.close(fig)

    # ------------------------------------------------------------------
    # Chart 3 — Model Comparison (KNN vs Random Forest)
    # ------------------------------------------------------------------
    metrics = {
        "Accuracy": [results["knn_accuracy"], results["rf_accuracy"]],
        "Macro F1": [results["knn_f1"], results["rf_f1"]],
    }
    models = ["KNN", "Random Forest"]
    x = np.arange(len(metrics))
    width = 0.30

    fig, ax = plt.subplots(figsize=(8, 5))
    for i, model in enumerate(models):
        vals = [metrics[m][i] for m in metrics]
        bars = ax.bar(x + i * width, vals, width, label=model)
        for bar, val in zip(bars, vals):
            ax.text(
                bar.get_x() + bar.get_width() / 2,
                bar.get_height() + 0.01,
                f"{val:.3f}",
                ha="center",
                va="bottom",
                fontsize=11,
                fontweight="bold",
            )

    ax.set_xticks(x + width / 2)
    ax.set_xticklabels(list(metrics.keys()), fontsize=12)
    ax.set_ylim(0, 1.15)
    ax.set_ylabel("Score")
    ax.set_title("Chart 3 — Model Comparison (KNN vs. Random Forest)", fontsize=13, fontweight="bold")
    ax.legend()
    ax.grid(axis="y", alpha=0.3)
    fig.tight_layout()
    fig.savefig(CHART_DIR / "3_model_comparison.png", dpi=DPI, bbox_inches="tight")
    print("Saved: 3_model_comparison.png")
    plt.close(fig)

    # ------------------------------------------------------------------
    print(f"\nSaved 3 essential charts to {CHART_DIR}")


if __name__ == "__main__":
    visualize()
