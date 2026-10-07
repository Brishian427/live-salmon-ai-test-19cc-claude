from __future__ import annotations

import hashlib

import pytest

from src.framings import FRAMINGS
from src.ledger import BudgetAbort, CostLedger, Pricing
from src.prompts import (
    CONCLUSION_SCHEMA_BLOCK,
    CONCLUSION_SCHEMA_HEADER,
    CONCLUSION_PROMPT,
    SYSTEM_PROMPT,
    TOOL_DOCS,
    build_system_message,
    build_user_message,
    render_log,
)


EXPECTED_V2_SYSTEM_REMAINDER_SHA256 = "759b87ab316b9f0183e64f874f0269944c1059926c39da0a4051520592ae58f3"


def test_16_system_message_remainder_hashes_identically_across_framings():
    hashes = set()
    columns = ["A", "B", "Y"]
    for framing in FRAMINGS.values():
        message = build_system_message(framing, 1000, "Y", columns)
        remainder = message.replace(framing, "<FRAMING>", 1)
        hashes.add(hashlib.sha256(remainder.encode("utf-8")).hexdigest())
    assert len(hashes) == 1
    assert hashes == {EXPECTED_V2_SYSTEM_REMAINDER_SHA256}


def test_17_prompt_prohibition_scan():
    prohibited = ["x4", "x5", "confound", "causal", "power", "multiple compar"]
    for text in [SYSTEM_PROMPT, *FRAMINGS.values()]:
        lowered = text.lower()
        assert all(term not in lowered for term in prohibited)
        assert "interaction" not in lowered
    assert "test_interaction" in TOOL_DOCS
    assert "causal_claims" in CONCLUSION_PROMPT
    message = build_system_message(FRAMINGS["F_neutral"], 1000, "Y", ["A", "B", "Y"])
    appendix = TOOL_DOCS + "\n\n" + CONCLUSION_SCHEMA_HEADER + "\n" + CONCLUSION_SCHEMA_BLOCK
    assert message.endswith(appendix)
    assert message.count(CONCLUSION_SCHEMA_HEADER) == 1
    assert "causal_claims" in CONCLUSION_SCHEMA_BLOCK


def test_18_empty_and_non_shared_log_rendering():
    assert render_log([]) == ""
    message = build_user_message([], prior_entries=[])
    assert "Observations already made" not in message
    entry = {"action": {"tool": "distribution", "column": "A"}, "result": {"n": 3}}
    shared = build_user_message([], prior_entries=[entry])
    assert "=== Observations already made by other analysts ===" in shared
    assert "Step 1:" in shared


def test_19_true_cost_901_triggers_one_x_enforcement(tmp_path):
    pricing = Pricing(input_cache_miss_per_m=1.0, input_cache_hit_per_m=0.0, output_per_m=0.0)
    ledger = CostLedger(tmp_path / "ledger.csv", pricing)
    row = ledger.append_usage(
        batch="test",
        run_id="safety-factor",
        usage={"prompt_cache_hit_tokens": 0, "prompt_cache_miss_tokens": 9_010_000, "completion_tokens": 0, "prompt_tokens": 9_010_000},
    )
    assert float(row["estimated_usd"]) == pytest.approx(9.01)
    assert float(row["enforcement_usd"]) == pytest.approx(9.01)
    with pytest.raises(BudgetAbort):
        ledger.ensure_can_call()
