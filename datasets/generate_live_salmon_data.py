"""
Generate synthetic datasets for the "Live Salmon Test for AI Scientists".

Inspired by the "dead salmon fMRI" study (Bennett et al., 2009), this script
generates two datasets:

1. "Live Salmon" dataset: A tabular dataset with a KNOWN data generating process.
   AI scientist systems should be able to recover the true model.

2. "Dead Salmon" dataset: Same feature structure but the target Y is pure random
   noise, independent of all features. Serves as a null/control condition.

Ground truth is saved alongside the data so results can be evaluated.
"""

import json
import os

import numpy as np
import pandas as pd

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
SEED = 42
N_SAMPLES = 1000
OUTPUT_DIR = os.path.dirname(os.path.abspath(__file__))

# True coefficients for the linear terms
TRUE_COEFFICIENTS = {
    "X1": 2.0,
    "X2": 0.5,
    "X3": -1.5,
}

# Interaction term coefficient
INTERACTION_COEFF = 0.8  # coefficient for X4 * X5

NOISE_STD = 1.0  # standard deviation of irreducible noise in Y


def generate_features(rng: np.random.Generator, n: int) -> pd.DataFrame:
    """Generate all 20 features."""

    # --- 5 truly predictive features (X1-X5) ---
    X1 = rng.normal(0, 1, n)
    X2 = rng.normal(0, 1, n)
    X3 = rng.normal(0, 1, n)
    X4 = rng.normal(0, 1, n)
    X5 = rng.normal(0, 1, n)

    # --- 10 pure noise / distractor features (X6-X15) ---
    noise_features = {f"X{i}": rng.normal(0, 1, n) for i in range(6, 16)}

    # --- 5 correlated-but-not-causal features (X16-X20) ---
    # Each is a noisy copy of one of the true predictors
    X16 = 0.7 * X1 + 0.3 * rng.normal(0, 1, n)   # correlated with X1
    X17 = 0.6 * X2 + 0.4 * rng.normal(0, 1, n)   # correlated with X2
    X18 = 0.5 * X3 + 0.5 * rng.normal(0, 1, n)   # correlated with X3
    X19 = 0.8 * X4 + 0.2 * rng.normal(0, 1, n)   # correlated with X4
    X20 = 0.65 * X5 + 0.35 * rng.normal(0, 1, n)  # correlated with X5

    data = {
        "X1": X1, "X2": X2, "X3": X3, "X4": X4, "X5": X5,
        **noise_features,
        "X16": X16, "X17": X17, "X18": X18, "X19": X19, "X20": X20,
    }
    return pd.DataFrame(data)


def generate_live_target(df: pd.DataFrame, rng: np.random.Generator) -> np.ndarray:
    """
    Generate Y from the KNOWN data generating process:

        Y = 2*X1 + 0.5*X2 - 1.5*X3 + 0.8*(X4 * X5) + noise

    The interaction term X4*X5 introduces non-linearity.
    """
    y = (
        TRUE_COEFFICIENTS["X1"] * df["X1"]
        + TRUE_COEFFICIENTS["X2"] * df["X2"]
        + TRUE_COEFFICIENTS["X3"] * df["X3"]
        + INTERACTION_COEFF * (df["X4"] * df["X5"])
        + rng.normal(0, NOISE_STD, len(df))
    )
    return y.values


def generate_dead_target(rng: np.random.Generator, n: int) -> np.ndarray:
    """Generate pure random noise target (dead salmon / null condition)."""
    return rng.normal(0, 1, n)


def build_ground_truth() -> dict:
    """Return a dictionary describing the true data generating process."""
    return {
        "description": (
            "Live Salmon Test dataset. "
            "Y = 2*X1 + 0.5*X2 - 1.5*X3 + 0.8*(X4*X5) + N(0,1) noise."
        ),
        "true_formula": "Y = 2*X1 + 0.5*X2 - 1.5*X3 + 0.8*(X4*X5) + epsilon",
        "noise_distribution": "N(0, 1)",
        "linear_coefficients": TRUE_COEFFICIENTS,
        "interaction_term": {
            "features": ["X4", "X5"],
            "coefficient": INTERACTION_COEFF,
        },
        "truly_predictive_features": ["X1", "X2", "X3", "X4", "X5"],
        "noise_distractor_features": [f"X{i}" for i in range(6, 16)],
        "correlated_non_causal_features": {
            "X16": "correlated with X1 (r~0.7)",
            "X17": "correlated with X2 (r~0.6)",
            "X18": "correlated with X3 (r~0.5)",
            "X19": "correlated with X4 (r~0.8)",
            "X20": "correlated with X5 (r~0.65)",
        },
        "n_samples": N_SAMPLES,
        "n_features": 20,
        "seed": SEED,
        "dead_salmon_note": (
            "The dead_salmon dataset uses the same features but Y is pure "
            "N(0,1) noise independent of all features.  Any 'significant' "
            "finding on this dataset is a false positive."
        ),
    }


def main() -> None:
    rng = np.random.default_rng(SEED)

    # Generate features (shared between live and dead datasets)
    features = generate_features(rng, N_SAMPLES)

    # --- Live salmon dataset ---
    live_y = generate_live_target(features, rng)
    live_df = features.copy()
    live_df["Y"] = live_y

    # --- Dead salmon dataset ---
    dead_y = generate_dead_target(rng, N_SAMPLES)
    dead_df = features.copy()
    dead_df["Y"] = dead_y

    # --- Save full datasets ---
    live_path = os.path.join(OUTPUT_DIR, "live_salmon_data.csv")
    dead_path = os.path.join(OUTPUT_DIR, "dead_salmon_data.csv")
    live_df.to_csv(live_path, index=False)
    dead_df.to_csv(dead_path, index=False)
    print(f"Saved live salmon dataset: {live_path}  ({live_df.shape})")
    print(f"Saved dead salmon dataset: {dead_path}  ({dead_df.shape})")

    # --- Save small samples (first 10 rows) ---
    live_sample_path = os.path.join(OUTPUT_DIR, "live_salmon_sample.csv")
    dead_sample_path = os.path.join(OUTPUT_DIR, "dead_salmon_sample.csv")
    live_df.head(10).to_csv(live_sample_path, index=False)
    dead_df.head(10).to_csv(dead_sample_path, index=False)
    print(f"Saved live salmon sample:  {live_sample_path}")
    print(f"Saved dead salmon sample:  {dead_sample_path}")

    # --- Save ground truth ---
    gt = build_ground_truth()
    gt_path = os.path.join(OUTPUT_DIR, "ground_truth.json")
    with open(gt_path, "w") as f:
        json.dump(gt, f, indent=2)
    print(f"Saved ground truth:        {gt_path}")

    # Quick sanity check
    print("\n--- Sanity check (live salmon) ---")
    print(f"  Y mean:  {live_y.mean():.3f}")
    print(f"  Y std:   {live_y.std():.3f}")
    corrs = features.corrwith(pd.Series(live_y, name="Y"))
    print("  Top correlations with Y:")
    for feat in corrs.abs().sort_values(ascending=False).head(8).index:
        print(f"    {feat}: {corrs[feat]:+.3f}")

    print("\n--- Sanity check (dead salmon) ---")
    dead_corrs = features.corrwith(pd.Series(dead_y, name="Y"))
    print("  Max |corr| with Y:", f"{dead_corrs.abs().max():.3f}")


if __name__ == "__main__":
    main()
