from __future__ import annotations

import json

import numpy as np
import pandas as pd

from src.generators import generate_g1_strong
from src.tools import ToolService, cache_key, canonical_json


def _service(tmp_path):
    frame, _ = generate_g1_strong()
    return ToolService(frame, "G1_test", tmp_path / "cache")


def test_06_tool_sanity_interaction_p_below_threshold(tmp_path):
    rng = np.random.default_rng(12345)
    x1 = rng.normal(size=1000)
    x2 = rng.normal(size=1000)
    frame = pd.DataFrame({"X1": x1, "X2": x2})
    frame["Y"] = x1 * x2 + 0.01 * rng.normal(size=1000)
    service = ToolService(frame, "sanity", tmp_path / "cache")
    result = service.execute({"tool": "test_interaction", "a": "X1", "b": "X2"})
    assert result["interaction_p"] < 1e-10


def test_07_each_tool_rejects_unknown_columns_with_error_shape(tmp_path):
    service = _service(tmp_path)
    actions = [
        {"tool": "distribution", "column": "NOPE"},
        {"tool": "correlation", "a": "X1", "b": "NOPE"},
        {"tool": "regression", "columns": ["X1", "NOPE"]},
        {"tool": "test_interaction", "a": "X1", "b": "NOPE"},
        {"tool": "holdout", "columns": ["X1", "NOPE"]},
    ]
    for action in actions:
        result = service.execute(action)
        assert set(result) == {"error", "valid_tools"}
        assert result["valid_tools"] == [
            "distribution",
            "correlation",
            "regression",
            "test_interaction",
            "holdout",
        ]


def test_08_cache_round_trip_is_identical_without_recompute(tmp_path):
    service = _service(tmp_path)
    action = {"tool": "distribution", "column": "X4"}
    first = service.execute(action)
    count = service.computation_count
    second = service.execute(action)
    assert second == first
    assert service.computation_count == count
    expected_path = tmp_path / "cache" / f"{cache_key('G1_test', action)}.json"
    assert json.loads(expected_path.read_text(encoding="utf-8")) == first
    assert canonical_json(action) == '{"column":"X4","tool":"distribution"}'
