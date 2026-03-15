"""
Prepare data summaries for AI scientists to analyze.

Instead of sending the full CSV (too large for context windows), we provide:
1. Dataset description and metadata
2. Summary statistics
3. Correlation matrix
4. A sample of rows
5. Pairwise correlations with Y
"""

import json
import numpy as np
import pandas as pd


def prepare_summary(csv_path: str, dataset_label: str) -> str:
    """Create a text summary of the dataset for an AI scientist to analyze."""
    df = pd.read_csv(csv_path)
    n, p = df.shape

    # Summary statistics
    desc = df.describe().round(4).to_string()

    # Correlations with Y
    corr_with_y = df.corr()["Y"].drop("Y").sort_values(ascending=False)
    corr_str = corr_with_y.round(4).to_string()

    # Full correlation matrix (upper triangle)
    full_corr = df.corr().round(3).to_string()

    # Sample rows
    sample = df.head(15).round(4).to_csv(index=False)

    # Additional: pairwise feature correlations (top non-trivial)
    corr_matrix = df.drop(columns=["Y"]).corr()
    pairs = []
    for i in range(len(corr_matrix.columns)):
        for j in range(i + 1, len(corr_matrix.columns)):
            c = corr_matrix.iloc[i, j]
            if abs(c) > 0.3:
                pairs.append((corr_matrix.columns[i], corr_matrix.columns[j], round(c, 3)))
    pairs.sort(key=lambda x: abs(x[2]), reverse=True)

    summary = f"""# Dataset: {dataset_label}

## Overview
- Number of samples: {n}
- Number of features: {p - 1} (X1 through X{p-1})
- Target variable: Y (continuous)
- All features and target are continuous numerical variables.

## Task
You are given a tabular dataset with {p-1} features (X1-X{p-1}) and a continuous target variable Y.
Your goal is to discover the relationship between the features and Y.

## Summary Statistics
{desc}

## Correlations of each feature with Y (sorted by value)
{corr_str}

## Notable inter-feature correlations (|r| > 0.3)
"""
    if pairs:
        for f1, f2, c in pairs:
            summary += f"  {f1} -- {f2}: r = {c}\n"
    else:
        summary += "  None found.\n"

    summary += f"""
## Full Correlation Matrix
{full_corr}

## Sample Data (first 15 rows)
{sample}

## Raw Data Access
The full dataset has {n} rows. The above sample and statistics represent the complete dataset.
"""
    return summary


if __name__ == "__main__":
    live = prepare_summary("datasets/live_salmon_data.csv", "Research Dataset A")
    dead = prepare_summary("datasets/dead_salmon_data.csv", "Research Dataset B")
    print("=== LIVE SALMON SUMMARY ===")
    print(live[:500])
    print("...")
    print("\n=== DEAD SALMON SUMMARY ===")
    print(dead[:500])
    print("...")
