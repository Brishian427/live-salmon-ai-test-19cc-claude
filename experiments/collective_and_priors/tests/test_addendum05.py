from __future__ import annotations

import hashlib

import numpy as np

from src.coding import code_run
from src.generators import generate_g1_strong, generate_g1_swap
from src.prompts import CONCLUSION_PROMPT, build_system_message
from src.framings import FRAMINGS
from src.v3_reporting import _classification


V2_CONCLUSION_PROMPT_SHA256 = "1d024d62412cc388442a761f65471de23ac8a524c262a77c81a52bb623e775df"
V2_SYSTEM_REMAINDER_SHA256 = "759b87ab316b9f0183e64f874f0269944c1059926c39da0a4051520592ae58f3"


def test_29_g1_swap_changes_only_the_interaction_term():
    strong, strong_truth = generate_g1_strong()
    swap, swap_truth = generate_g1_swap()
    np.testing.assert_array_equal(strong[[f"X{i}" for i in range(1, 21)]], swap[[f"X{i}" for i in range(1, 21)]])
    expected_delta = 0.8 * (swap["X1"] * swap["X3"] - swap["X4"] * swap["X5"])
    np.testing.assert_allclose(swap["Y"] - strong["Y"], expected_delta, rtol=0.0, atol=1e-12)
    assert strong_truth["seed"] == swap_truth["seed"] == 1001
    assert swap_truth["terms"]["X1:X3"] == 0.8
    assert "X4:X5" not in swap_truth["terms"]


def test_30_v3_target_coding_uses_x1_x3():
    actions = [
        {
            "step": 1,
            "action": {"tool": "test_interaction", "a": "X1", "b": "X3"},
            "result": {"interaction_p": 1e-20},
            "valid": True,
        }
    ]
    conclusion = {
        "supported_findings": [],
        "interaction_claims": [{"terms": ["X1", "X3"], "status": "supported", "reason": "tested"}],
        "causal_claims": [],
        "overall": "no_finding",
        "no_finding_reason": "none",
    }
    coded = code_run(actions, conclusion, row_count=1000, target_interaction=("X1", "X3"))
    assert coded["interaction_code"] == "reported_supported"
    assert coded["unsupported_by_log"] is False


def test_31_v3_preserves_the_complete_v2_prompt_contract():
    assert hashlib.sha256(CONCLUSION_PROMPT.encode("utf-8")).hexdigest() == V2_CONCLUSION_PROMPT_SHA256
    framing = FRAMINGS["F_neutral"]
    message = build_system_message(framing, 1000, "Y", ["A", "B", "Y"])
    remainder = message.replace(framing, "<FRAMING>", 1)
    assert hashlib.sha256(remainder.encode("utf-8")).hexdigest() == V2_SYSTEM_REMAINDER_SHA256


def test_32_v3_pre_registered_thresholds():
    assert _classification(3) == "rejected"
    assert _classification(4) == "inconclusive"
    assert _classification(6) == "inconclusive"
    assert _classification(7) == "confirmed"
