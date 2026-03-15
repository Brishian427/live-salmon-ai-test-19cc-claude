# Live Salmon Test -- Datasets

## Overview

This directory contains synthetic datasets for the **Live Salmon Test for AI Scientists**, inspired by the "dead salmon fMRI" study (Bennett et al., 2009).

Two datasets are provided:

| Dataset | File | Description |
|---------|------|-------------|
| **Live Salmon** | `live_salmon_data.csv` | Target Y is generated from a **known formula** involving 5 of the 20 features. An AI scientist should be able to recover the true model. |
| **Dead Salmon** | `dead_salmon_data.csv` | Target Y is **pure random noise**, independent of all features. Any "significant" finding is a false positive. |

Both datasets share the same 20 features and 1000 rows.

## Feature structure (20 features)

| Features | Role |
|----------|------|
| X1 -- X5 | Truly predictive (used in the generating formula) |
| X6 -- X15 | Pure noise / distractors (independent of Y) |
| X16 -- X20 | Correlated with X1--X5 but **not** directly causal |

## Ground truth

The true data generating process for the **live salmon** dataset is:

```
Y = 2*X1 + 0.5*X2 - 1.5*X3 + 0.8*(X4 * X5) + epsilon
```

where `epsilon ~ N(0, 1)`.

Full details (coefficients, correlation structure, etc.) are saved in `ground_truth.json`.

## Files in this directory

| File | Tracked in git? | Description |
|------|-----------------|-------------|
| `generate_live_salmon_data.py` | Yes | Script that generates all datasets |
| `ground_truth.json` | Yes | True model specification |
| `live_salmon_sample.csv` | Yes | First 10 rows of live dataset |
| `dead_salmon_sample.csv` | Yes | First 10 rows of dead dataset |
| `live_salmon_data.csv` | No (gitignored) | Full live dataset (1000 rows) |
| `dead_salmon_data.csv` | No (gitignored) | Full dead dataset (1000 rows) |

## Regenerating the data

The full CSV files are gitignored because they can be regenerated deterministically (fixed seed = 42).

```bash
source .venv/bin/activate
python datasets/generate_live_salmon_data.py
```

Dependencies: `numpy`, `pandas` (install with `uv pip install numpy pandas`).
