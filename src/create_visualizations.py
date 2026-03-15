"""
Create visualizations for the Live Salmon Test results.
"""

import json
import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

plt.rcParams.update({
    "figure.figsize": (10, 6),
    "font.size": 12,
    "axes.titlesize": 14,
    "axes.labelsize": 12,
})

PLOTS_DIR = "results/plots"
os.makedirs(PLOTS_DIR, exist_ok=True)


def load_evaluations():
    with open("results/all_evaluations.json") as f:
        return json.load(f)


def plot_feature_detection_heatmap(evals):
    """Heatmap: which features each AI scientist identified (live salmon)."""
    live_evals = [e for e in evals if e["dataset"] == "live_salmon"]
    features = [f"X{i}" for i in range(1, 21)]

    # Ground truth categories
    true_feats = {"X1", "X2", "X3", "X4", "X5"}
    noise_feats = {f"X{i}" for i in range(6, 16)}
    corr_feats = {"X16", "X17", "X18", "X19", "X20"}

    rows = []
    labels = []
    for e in live_evals:
        claimed = set(e["claims"].get("features_claimed_significant", []))
        row = [1 if f in claimed else 0 for f in features]
        rows.append(row)
        labels.append(f"{e['model_name']}\nrun{e['run_id']}")

    data = np.array(rows)

    fig, ax = plt.subplots(figsize=(14, 6))
    im = ax.imshow(data, cmap="RdYlGn", aspect="auto", vmin=-0.2, vmax=1.2)

    ax.set_xticks(range(len(features)))
    ax.set_xticklabels(features, rotation=45, ha="right")
    ax.set_yticks(range(len(labels)))
    ax.set_yticklabels(labels, fontsize=9)

    # Color-code feature labels
    for i, f in enumerate(features):
        if f in true_feats:
            ax.get_xticklabels()[i].set_color("green")
            ax.get_xticklabels()[i].set_fontweight("bold")
        elif f in corr_feats:
            ax.get_xticklabels()[i].set_color("orange")
        elif f in noise_feats:
            ax.get_xticklabels()[i].set_color("red")

    # Add text annotations
    for i in range(len(labels)):
        for j in range(len(features)):
            color = "white" if data[i, j] == 1 else "gray"
            ax.text(j, i, "Y" if data[i, j] == 1 else "", ha="center", va="center",
                    color=color, fontsize=8, fontweight="bold")

    # Add dividers between feature groups
    ax.axvline(x=4.5, color="black", linewidth=2, linestyle="--")
    ax.axvline(x=14.5, color="black", linewidth=2, linestyle="--")

    ax.set_title("Live Salmon Test: Feature Detection by AI Scientists\n"
                 "(Green=true causal, Orange=correlated proxy, Red=noise)")
    plt.tight_layout()
    plt.savefig(f"{PLOTS_DIR}/feature_detection_heatmap.png", dpi=150)
    plt.close()
    print("Saved feature_detection_heatmap.png")


def plot_detection_rates_by_model(evals):
    """Bar chart: detection rates by model."""
    live_evals = [e for e in evals if e["dataset"] == "live_salmon"]
    models = sorted(set(e["model_name"] for e in live_evals))

    # Calculate per-feature detection rates
    true_feats = ["X1", "X2", "X3", "X4", "X5"]
    feat_rates = {f: [] for f in true_feats}

    for model in models:
        model_evals = [e for e in live_evals if e["model_name"] == model]
        for feat in true_feats:
            detected = sum(
                1 for e in model_evals
                if feat in e["claims"].get("features_claimed_significant", [])
            )
            feat_rates[feat].append(detected / len(model_evals))

    x = np.arange(len(models))
    width = 0.15
    fig, ax = plt.subplots(figsize=(12, 6))

    colors = ["#2ecc71", "#27ae60", "#16a085", "#e74c3c", "#c0392b"]
    for i, feat in enumerate(true_feats):
        offset = (i - 2) * width
        bars = ax.bar(x + offset, feat_rates[feat], width, label=feat, color=colors[i])
        for bar, val in zip(bars, feat_rates[feat]):
            if val > 0:
                ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.02,
                        f"{val:.0%}", ha="center", va="bottom", fontsize=8)

    ax.set_xlabel("Model")
    ax.set_ylabel("Detection Rate (across 3 runs)")
    ax.set_title("True Feature Detection Rates by Model\n(X1-X3: linear terms, X4-X5: interaction terms)")
    ax.set_xticks(x)
    ax.set_xticklabels(models)
    ax.set_ylim(0, 1.15)
    ax.legend(title="Feature", loc="upper right")
    ax.axhline(y=1.0, color="gray", linestyle=":", alpha=0.5)

    plt.tight_layout()
    plt.savefig(f"{PLOTS_DIR}/detection_rates_by_model.png", dpi=150)
    plt.close()
    print("Saved detection_rates_by_model.png")


def plot_aggregate_metrics(evals):
    """Summary bar chart of aggregate metrics."""
    live_evals = [e for e in evals if e["dataset"] == "live_salmon"]
    dead_evals = [e for e in evals if e["dataset"] == "dead_salmon"]

    # Aggregate metrics
    metrics = {
        "X1 Detected\n(coef=2.0)": np.mean([
            "X1" in e["claims"].get("features_claimed_significant", [])
            for e in live_evals
        ]),
        "X2 Detected\n(coef=0.5)": np.mean([
            "X2" in e["claims"].get("features_claimed_significant", [])
            for e in live_evals
        ]),
        "X3 Detected\n(coef=-1.5)": np.mean([
            "X3" in e["claims"].get("features_claimed_significant", [])
            for e in live_evals
        ]),
        "X4 or X5\nDetected": np.mean([
            "X4" in e["claims"].get("features_claimed_significant", []) or
            "X5" in e["claims"].get("features_claimed_significant", [])
            for e in live_evals
        ]),
        "X4*X5 Interaction\nDetected": np.mean([
            e["scores"].get("interaction_detected", False)
            for e in live_evals
        ]),
        "Correlated Feature\nConfusion": np.mean([
            e["scores"].get("correlated_feature_confusion_rate", 0)
            for e in live_evals
        ]),
        "Dead Salmon\nFalse Positives": np.mean([
            e["scores"].get("false_positives_total", 0) > 0
            for e in dead_evals
        ]),
        "Dead Salmon\nNull Finding": np.mean([
            e["scores"].get("null_finding_reported", False)
            for e in dead_evals
        ]),
    }

    fig, ax = plt.subplots(figsize=(14, 6))
    colors = ["#2ecc71", "#f39c12", "#2ecc71", "#e74c3c", "#e74c3c",
              "#f39c12", "#2ecc71", "#2ecc71"]
    bars = ax.bar(range(len(metrics)), list(metrics.values()), color=colors, edgecolor="black", linewidth=0.5)

    for bar, val in zip(bars, metrics.values()):
        ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.02,
                f"{val:.0%}", ha="center", va="bottom", fontsize=11, fontweight="bold")

    ax.set_xticks(range(len(metrics)))
    ax.set_xticklabels(list(metrics.keys()), fontsize=9)
    ax.set_ylabel("Rate (across 9 live / 9 dead papers)")
    ax.set_title("Live Salmon Test: Aggregate Results Across All AI Scientists\n"
                 "(Green=good, Red=failure, Orange=partial)")
    ax.set_ylim(0, 1.2)
    ax.axhline(y=1.0, color="gray", linestyle=":", alpha=0.3)

    plt.tight_layout()
    plt.savefig(f"{PLOTS_DIR}/aggregate_metrics.png", dpi=150)
    plt.close()
    print("Saved aggregate_metrics.png")


def plot_coefficient_accuracy(evals):
    """Compare estimated vs true coefficients."""
    live_evals = [e for e in evals if e["dataset"] == "live_salmon"]
    true_coefs = {"X1": 2.0, "X2": 0.5, "X3": -1.5}

    fig, axes = plt.subplots(1, 3, figsize=(14, 5))

    for idx, (feat, true_val) in enumerate(true_coefs.items()):
        estimates = {}
        for e in live_evals:
            model = e["model_name"]
            est = e["claims"].get("estimated_coefficients", {}).get(feat)
            if est is not None and isinstance(est, (int, float)):
                estimates.setdefault(model, []).append(est)

        ax = axes[idx]
        ax.axhline(y=true_val, color="red", linewidth=2, linestyle="--", label=f"True ({true_val})")

        models = sorted(estimates.keys())
        for i, model in enumerate(models):
            vals = estimates[model]
            ax.scatter([i] * len(vals), vals, s=100, zorder=5, alpha=0.7,
                       label=model if idx == 0 else "")
            if vals:
                ax.plot([i - 0.1, i + 0.1], [np.mean(vals)] * 2, "k-", linewidth=2)

        ax.set_title(f"{feat} (true = {true_val})")
        ax.set_xticks(range(len(models)))
        ax.set_xticklabels(models, fontsize=8, rotation=15)
        ax.set_ylabel("Estimated Coefficient")
        ax.grid(axis="y", alpha=0.3)

    axes[0].legend(loc="upper right", fontsize=8)
    fig.suptitle("Coefficient Estimation Accuracy by AI Scientists", fontsize=14)
    plt.tight_layout()
    plt.savefig(f"{PLOTS_DIR}/coefficient_accuracy.png", dpi=150)
    plt.close()
    print("Saved coefficient_accuracy.png")


def plot_methods_used(evals):
    """Bar chart of methods mentioned across all papers."""
    all_methods = {}
    for e in evals:
        if e["dataset"] == "live_salmon":
            for method in e["claims"].get("methods_used", []):
                method_lower = method.lower()
                all_methods[method_lower] = all_methods.get(method_lower, 0) + 1

    # Group similar methods
    grouped = {}
    for m, count in all_methods.items():
        if "correlation" in m:
            grouped["Correlation analysis"] = grouped.get("Correlation analysis", 0) + count
        elif "regression" in m or "ols" in m:
            grouped["Linear regression"] = grouped.get("Linear regression", 0) + count
        elif "collinearity" in m or "vif" in m:
            grouped["Multicollinearity check"] = grouped.get("Multicollinearity check", 0) + count
        elif "multiple" in m or "bonferroni" in m or "fdr" in m:
            grouped["Multiple comparisons\ncorrection"] = grouped.get("Multiple comparisons\ncorrection", 0) + count
        elif "interaction" in m:
            grouped["Interaction testing"] = grouped.get("Interaction testing", 0) + count
        elif "nonlinear" in m:
            grouped["Nonlinearity check"] = grouped.get("Nonlinearity check", 0) + count
        elif "effect size" in m:
            grouped["Effect size estimation"] = grouped.get("Effect size estimation", 0) + count
        elif "forward" in m or "stepwise" in m or "selection" in m:
            grouped["Feature selection"] = grouped.get("Feature selection", 0) + count
        else:
            grouped[m[:30]] = grouped.get(m[:30], 0) + count

    sorted_methods = sorted(grouped.items(), key=lambda x: x[1], reverse=True)[:10]

    fig, ax = plt.subplots(figsize=(10, 6))
    methods, counts = zip(*sorted_methods)
    ax.barh(range(len(methods)), counts, color="#3498db", edgecolor="black", linewidth=0.5)
    ax.set_yticks(range(len(methods)))
    ax.set_yticklabels(methods, fontsize=10)
    ax.set_xlabel("Number of papers mentioning method (out of 9)")
    ax.set_title("Statistical Methods Used by AI Scientists (Live Salmon)")
    ax.invert_yaxis()
    plt.tight_layout()
    plt.savefig(f"{PLOTS_DIR}/methods_used.png", dpi=150)
    plt.close()
    print("Saved methods_used.png")


def create_summary_table(evals):
    """Create a summary table of all results."""
    rows = []
    for e in evals:
        s = e["scores"]
        row = {
            "Model": e["model_name"],
            "Run": e["run_id"],
            "Dataset": e["dataset"],
        }
        if e["dataset"] == "live_salmon":
            row["TPR"] = s.get("true_positive_rate", None)
            row["FPR_noise"] = s.get("false_positive_rate_noise", None)
            row["Corr_confusion"] = s.get("correlated_feature_confusion_rate", None)
            row["Interaction"] = s.get("interaction_detected", None)
            row["Coef_error"] = s.get("mean_coefficient_error", None)
            row["MC_mentioned"] = s.get("multiple_comparisons_mentioned", None)
        else:
            row["FP_total"] = s.get("false_positives_total", None)
            row["Null_finding"] = s.get("null_finding_reported", None)
            row["MC_mentioned"] = s.get("multiple_comparisons_mentioned", None)
        rows.append(row)

    df = pd.DataFrame(rows)
    df.to_csv("results/summary_table.csv", index=False)
    print("Saved summary_table.csv")
    return df


if __name__ == "__main__":
    evals = load_evaluations()
    plot_feature_detection_heatmap(evals)
    plot_detection_rates_by_model(evals)
    plot_aggregate_metrics(evals)
    plot_coefficient_accuracy(evals)
    plot_methods_used(evals)
    df = create_summary_table(evals)
    print("\nSummary table:")
    print(df.to_string(index=False))
