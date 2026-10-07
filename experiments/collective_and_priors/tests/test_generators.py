from __future__ import annotations

import numpy as np
import statsmodels.api as sm

from src.generators import (
    FROZEN_SEEDS,
    generate_g0_null,
    generate_g1_strong,
    generate_g2_calibrated,
    generate_g3_confound,
    generate_g4_underpowered,
    generate_pendulum_shuffled,
)
from src.tools import ToolService

def _interaction_fit(frame):
    design = frame[["X1", "X2", "X3", "X4", "X5"]].copy()
    design["X4:X5"] = frame["X4"] * frame["X5"]
    return sm.OLS(frame["Y"], sm.add_constant(design, has_constant="add")).fit()


def test_01_each_generator_shape_and_columns():
    expected = {*(f"X{i}" for i in range(1, 21)), "Y"}
    for generator in (generate_g0_null, generate_g1_strong, generate_g4_underpowered):
        frame, truth = generator()
        assert frame.shape == (1000, 21)
        assert set(frame.columns) == expected
        assert truth["seed"] in FROZEN_SEEDS.values()
    calibrated, truth = generate_g2_calibrated(0.2)
    assert calibrated.shape == (1000, 21)
    assert truth["theta"] == 0.2
    confound, truth = generate_g3_confound()
    assert confound.shape == (1000, 22)
    assert set(confound.columns) == expected | {"Z"}
    intact, shuffled, truth = generate_pendulum_shuffled()
    expected_b4 = {"length_m", "mass_kg", "amplitude_deg", "temperature_c", "period_s"}
    assert intact.shape == shuffled.shape == (300, 5)
    assert set(intact.columns) == set(shuffled.columns) == expected_b4
    assert truth["permutation_seed"] == FROZEN_SEEDS["B4_permutation"]
    assert sorted(truth["permutation_index"]) == list(range(300))


def test_02_g1_interaction_recovers_within_two_se():
    frame, _ = generate_g1_strong()
    fit = _interaction_fit(frame)
    estimate = fit.params["X4:X5"]
    se = fit.bse["X4:X5"]
    assert abs(estimate - 0.8) <= 2 * se


def test_03_g4_interaction_is_underpowered(tmp_path):
    frame, _ = generate_g4_underpowered()
    service = ToolService(frame, "G4_underpowered", tmp_path / "cache")
    result = service.execute({"tool": "test_interaction", "a": "X4", "b": "X5"})
    assert result["interaction_p"] > 0.10


def test_04_g3_confound_contract():
    frame, truth = generate_g3_confound()
    correlation = frame[["Z", "X1"]].corr().loc["Z", "X1"]
    assert 0.88 <= correlation <= 0.92
    assert "Z" not in truth["terms"]


def test_05_pendulum_law_before_and_after_shuffle():
    intact, shuffled, _ = generate_pendulum_shuffled()

    def log_log_r2(frame):
        x = sm.add_constant(np.log(frame[["length_m"]]), has_constant="add")
        return sm.OLS(np.log(frame["period_s"]), x).fit().rsquared

    assert log_log_r2(intact) > 0.95
    assert log_log_r2(shuffled) < 0.05


def test_20_g0_is_true_zero_interaction(tmp_path):
    frame, truth = generate_g0_null()
    service = ToolService(frame, "G0_null", tmp_path / "cache")
    result = service.execute({"tool": "test_interaction", "a": "X4", "b": "X5"})
    assert truth["theta"] == 0.0
    assert truth["seed"] == 1000
    assert result["interaction_p"] > 0.05
