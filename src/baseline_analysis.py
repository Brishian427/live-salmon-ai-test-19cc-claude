"""
Baseline analysis: What a competent human data scientist would find.

Runs standard statistical methods (OLS, Lasso, Random Forest) on both
datasets to establish the "correct" analysis baseline.
"""

import json
import os
import warnings

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.linear_model import Lasso, LassoCV, LinearRegression
from sklearn.model_selection import cross_val_score
from sklearn.preprocessing import PolynomialFeatures
import scipy.stats as stats

warnings.filterwarnings("ignore")
np.random.seed(42)


def analyze_dataset(csv_path: str, label: str) -> dict:
    """Run standard analyses on a dataset."""
    df = pd.read_csv(csv_path)
    X = df.drop(columns=["Y"])
    y = df["Y"]
    features = X.columns.tolist()

    results = {"label": label, "n_samples": len(df), "n_features": len(features)}

    # 1. Univariate correlations with Y
    correlations = {}
    p_values = {}
    for col in features:
        r, p = stats.pearsonr(X[col], y)
        correlations[col] = round(r, 4)
        p_values[col] = round(p, 6)
    results["correlations"] = correlations
    results["correlation_p_values"] = p_values

    # Bonferroni correction
    n_tests = len(features)
    sig_uncorrected = [f for f, p in p_values.items() if p < 0.05]
    sig_bonferroni = [f for f, p in p_values.items() if p < 0.05 / n_tests]
    results["significant_uncorrected_p05"] = sig_uncorrected
    results["significant_bonferroni_p05"] = sig_bonferroni

    # 2. OLS Linear Regression
    ols = LinearRegression().fit(X, y)
    ols_r2 = ols.score(X, y)
    ols_cv = cross_val_score(ols, X, y, cv=5, scoring="r2").mean()
    ols_coefs = dict(zip(features, np.round(ols.coef_, 4)))
    results["ols"] = {
        "r2": round(ols_r2, 4),
        "cv_r2": round(ols_cv, 4),
        "coefficients": ols_coefs,
    }

    # 3. Lasso (for feature selection)
    lasso_cv = LassoCV(cv=5, random_state=42, max_iter=10000).fit(X, y)
    lasso_coefs = dict(zip(features, np.round(lasso_cv.coef_, 4)))
    lasso_selected = [f for f, c in lasso_coefs.items() if abs(c) > 0.01]
    results["lasso"] = {
        "alpha": round(lasso_cv.alpha_, 6),
        "coefficients": lasso_coefs,
        "selected_features": lasso_selected,
        "r2": round(lasso_cv.score(X, y), 4),
    }

    # 4. Random Forest (to detect nonlinearity)
    rf = RandomForestRegressor(n_estimators=100, random_state=42, n_jobs=-1)
    rf.fit(X, y)
    rf_r2 = rf.score(X, y)
    rf_cv = cross_val_score(rf, X, y, cv=5, scoring="r2", n_jobs=-1).mean()
    importances = dict(zip(features, np.round(rf.feature_importances_, 4)))
    results["random_forest"] = {
        "r2": round(rf_r2, 4),
        "cv_r2": round(rf_cv, 4),
        "importances": importances,
        "top_features": sorted(importances, key=importances.get, reverse=True)[:7],
    }

    # 5. Check for interaction: add X4*X5 to OLS
    X_inter = X.copy()
    X_inter["X4_X5"] = X["X4"] * X["X5"]
    ols_inter = LinearRegression().fit(X_inter, y)
    r2_gain = ols_inter.score(X_inter, y) - ols_r2
    results["interaction_test"] = {
        "r2_with_X4X5": round(ols_inter.score(X_inter, y), 4),
        "r2_gain": round(r2_gain, 4),
        "X4_X5_coefficient": round(ols_inter.coef_[-1], 4),
    }

    # 6. Nonlinearity gap: RF vs OLS
    results["nonlinearity_gap"] = round(rf_cv - ols_cv, 4)

    return results


def main():
    os.makedirs("results", exist_ok=True)

    print("=" * 60)
    print("BASELINE ANALYSIS")
    print("=" * 60)

    for label, path in [("live_salmon", "datasets/live_salmon_data.csv"),
                        ("dead_salmon", "datasets/dead_salmon_data.csv")]:
        print(f"\n--- {label.upper()} ---")
        results = analyze_dataset(path, label)

        # Save
        with open(f"results/baseline_{label}.json", "w") as f:
            json.dump(results, f, indent=2)

        # Print key findings
        print(f"  OLS R²: {results['ols']['r2']}, CV R²: {results['ols']['cv_r2']}")
        print(f"  Lasso selected: {results['lasso']['selected_features']}")
        print(f"  RF CV R²: {results['random_forest']['cv_r2']}")
        print(f"  RF top features: {results['random_forest']['top_features']}")
        print(f"  Sig (uncorrected): {results['significant_uncorrected_p05']}")
        print(f"  Sig (Bonferroni): {results['significant_bonferroni_p05']}")
        print(f"  Nonlinearity gap (RF-OLS): {results['nonlinearity_gap']}")
        print(f"  X4*X5 interaction coef: {results['interaction_test']['X4_X5_coefficient']}")
        print(f"  R² gain from X4*X5: {results['interaction_test']['r2_gain']}")

    print("\nBaseline analysis complete.")


if __name__ == "__main__":
    main()
