"""Synthetic data generators defined by frozen specification section 3."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

N_CORE = 1000
N_FEATURES = 20
N_PENDULUM = 300

MASTER_SEED = 20261003
FROZEN_SEEDS = {
    "G0_null": 1000,
    "G1_strong": 1001,
    "G1_swap": 1001,
    "G2_calibrated": 1002,
    "G3_confound": 1003,
    "G4_underpowered": 1004,
    "B4_draw": 1005,
    "B4_permutation": 1006,
    "holdout": 7030,
}
CALIBRATION_SEEDS = {
    0.2: 1200,
    0.4: 1201,
    0.8: 1202,
    1.6: 1203,
    3.2: 1204,
}


def generate_core(theta: float, seed: int, *, include_confound: bool = False) -> tuple[pd.DataFrame, dict[str, Any]]:
    """Generate one core-model dataset from an explicit seed."""
    rng = np.random.default_rng(seed)
    x = rng.normal(0.0, 1.0, size=(N_CORE, N_FEATURES))
    epsilon = rng.normal(0.0, 1.0, size=N_CORE)
    columns = [f"X{i}" for i in range(1, N_FEATURES + 1)]
    frame = pd.DataFrame(x, columns=columns)
    frame["Y"] = (
        2.0 * frame["X1"]
        + 0.5 * frame["X2"]
        - 1.5 * frame["X3"]
        + 0.10 * frame["X4"]
        + 0.10 * frame["X5"]
        + theta * (frame["X4"] * frame["X5"])
        + epsilon
    )
    if include_confound:
        frame["Z"] = frame["X1"] + 0.48 * rng.normal(0.0, 1.0, size=N_CORE)

    truth: dict[str, Any] = {
        "generator": "core",
        "n": N_CORE,
        "seed": seed,
        "theta": theta,
        "noise_sd": 1.0,
        "target": "Y",
        "terms": {
            "X1": 2.0,
            "X2": 0.5,
            "X3": -1.5,
            "X4": 0.10,
            "X5": 0.10,
            "X4:X5": theta,
        },
        "distractors": [f"X{i}" for i in range(6, 21)],
        "confound_Z": include_confound,
    }
    return frame, truth


def generate_g1_strong(seed: int = FROZEN_SEEDS["G1_strong"]) -> tuple[pd.DataFrame, dict[str, Any]]:
    return generate_core(theta=0.8, seed=seed)


def generate_g1_swap(seed: int = FROZEN_SEEDS["G1_swap"]) -> tuple[pd.DataFrame, dict[str, Any]]:
    """Generate the Addendum 05 cell with the product moved to X1:X3."""
    rng = np.random.default_rng(seed)
    x = rng.normal(0.0, 1.0, size=(N_CORE, N_FEATURES))
    epsilon = rng.normal(0.0, 1.0, size=N_CORE)
    columns = [f"X{i}" for i in range(1, N_FEATURES + 1)]
    frame = pd.DataFrame(x, columns=columns)
    frame["Y"] = (
        2.0 * frame["X1"]
        + 0.5 * frame["X2"]
        - 1.5 * frame["X3"]
        + 0.10 * frame["X4"]
        + 0.10 * frame["X5"]
        + 0.8 * (frame["X1"] * frame["X3"])
        + epsilon
    )
    truth: dict[str, Any] = {
        "generator": "G1_swap",
        "n": N_CORE,
        "seed": seed,
        "theta": 0.8,
        "noise_sd": 1.0,
        "target": "Y",
        "terms": {
            "X1": 2.0,
            "X2": 0.5,
            "X3": -1.5,
            "X4": 0.10,
            "X5": 0.10,
            "X1:X3": 0.8,
        },
        "distractors": [f"X{i}" for i in range(6, 21)],
        "confound_Z": False,
        "source_cell": "G1_strong",
        "sole_change": "interaction pair moved from X4:X5 to X1:X3",
    }
    return frame, truth


def generate_g0_null(seed: int = FROZEN_SEEDS["G0_null"]) -> tuple[pd.DataFrame, dict[str, Any]]:
    """Generate the true-zero interaction reference added by Addendum 03."""
    frame, truth = generate_core(theta=0.0, seed=seed)
    truth["ground_truth"] = "no interaction exists"
    return frame, truth


def generate_g2_calibrated(
    theta_star: float,
    seed: int = FROZEN_SEEDS["G2_calibrated"],
) -> tuple[pd.DataFrame, dict[str, Any]]:
    return generate_core(theta=theta_star, seed=seed)


def generate_g3_confound(seed: int = FROZEN_SEEDS["G3_confound"]) -> tuple[pd.DataFrame, dict[str, Any]]:
    return generate_core(theta=0.8, seed=seed, include_confound=True)


def generate_g4_underpowered(seed: int = FROZEN_SEEDS["G4_underpowered"]) -> tuple[pd.DataFrame, dict[str, Any]]:
    return generate_core(theta=0.03, seed=seed)


def generate_pendulum_shuffled(
    draw_seed: int = FROZEN_SEEDS["B4_draw"],
    permutation_seed: int = FROZEN_SEEDS["B4_permutation"],
) -> tuple[pd.DataFrame, pd.DataFrame, dict[str, Any]]:
    """Generate intact and shuffled pendulum frames from the same draw."""
    rng = np.random.default_rng(draw_seed)
    length = rng.uniform(0.1, 2.0, size=N_PENDULUM)
    frame = pd.DataFrame(
        {
            "length_m": length,
            "mass_kg": rng.uniform(0.05, 0.5, size=N_PENDULUM),
            "amplitude_deg": rng.uniform(2.0, 12.0, size=N_PENDULUM),
            "temperature_c": rng.uniform(18.0, 26.0, size=N_PENDULUM),
            "period_s": 2.0
            * np.pi
            * np.sqrt(length / 9.81)
            * (1.0 + 0.01 * rng.normal(0.0, 1.0, size=N_PENDULUM)),
        }
    )
    intact = frame.copy()
    permutation_rng = np.random.default_rng(permutation_seed)
    shuffled = frame.copy()
    permutation_index = permutation_rng.permutation(N_PENDULUM)
    shuffled["period_s"] = shuffled["period_s"].to_numpy()[permutation_index]
    truth = {
        "generator": "pendulum_shuffled",
        "n": N_PENDULUM,
        "draw_seed": draw_seed,
        "permutation_seed": permutation_seed,
        "permutation_index": permutation_index.tolist(),
        "target": "period_s",
        "intact_used_in_runs": False,
        "shuffled_ground_truth": "no column predicts the target",
    }
    return intact, shuffled, truth


def holdout_index(n_rows: int) -> tuple[np.ndarray, np.ndarray]:
    """Return the frozen 70/30 split for a dataset row count."""
    rng = np.random.default_rng(FROZEN_SEEDS["holdout"])
    permutation = rng.permutation(n_rows)
    cut = int(round(0.70 * n_rows))
    return permutation[:cut], permutation[cut:]


def write_dataset(
    name: str,
    frame: pd.DataFrame,
    ground_truth: dict[str, Any],
    data_dir: str | Path,
) -> tuple[Path, Path]:
    """Write a dataset and sibling ground truth with the frozen split."""
    output_dir = Path(data_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    csv_path = output_dir / f"{name}.csv"
    truth_path = output_dir / f"{name}_ground_truth.json"
    truth = dict(ground_truth)
    truth["dataset_name"] = name
    train_index, test_index = holdout_index(len(frame))
    truth["holdout_seed"] = FROZEN_SEEDS["holdout"]
    truth["holdout_train_index"] = train_index.tolist()
    truth["holdout_test_index"] = test_index.tolist()
    frame.to_csv(csv_path, index=False)
    truth_path.write_text(json.dumps(truth, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return csv_path, truth_path


def write_pendulum_pair(
    intact: pd.DataFrame,
    shuffled: pd.DataFrame,
    ground_truth: dict[str, Any],
    data_dir: str | Path,
) -> tuple[Path, Path, Path]:
    output_dir = Path(data_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    intact_path = output_dir / "B4_intact.csv"
    shuffled_path = output_dir / "B4_shuffled.csv"
    truth_path = output_dir / "B4_shuffled_ground_truth.json"
    truth = dict(ground_truth)
    train_index, test_index = holdout_index(len(shuffled))
    truth["holdout_seed"] = FROZEN_SEEDS["holdout"]
    truth["holdout_train_index"] = train_index.tolist()
    truth["holdout_test_index"] = test_index.tolist()
    intact.to_csv(intact_path, index=False)
    shuffled.to_csv(shuffled_path, index=False)
    truth_path.write_text(json.dumps(truth, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return intact_path, shuffled_path, truth_path


def write_batch0_canonical_datasets(data_dir: str | Path) -> dict[str, Path]:
    """Write every Batch 0 canonical dataset except G2, exactly once."""
    output_dir = Path(data_dir)
    outputs: dict[str, Path] = {}
    for name, generator in (
        ("G0_null", generate_g0_null),
        ("G1_strong", generate_g1_strong),
        ("G3_confound", generate_g3_confound),
        ("G4_underpowered", generate_g4_underpowered),
    ):
        frame, truth = generator()
        csv_path, truth_path = write_dataset(name, frame, truth, output_dir)
        outputs[name] = csv_path
        outputs[f"{name}_ground_truth"] = truth_path
    intact, shuffled, truth = generate_pendulum_shuffled()
    intact_path, shuffled_path, truth_path = write_pendulum_pair(intact, shuffled, truth, output_dir)
    outputs["B4_intact"] = intact_path
    outputs["B4_shuffled"] = shuffled_path
    outputs["B4_shuffled_ground_truth"] = truth_path
    return outputs
