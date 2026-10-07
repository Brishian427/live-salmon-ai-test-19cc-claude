from __future__ import annotations

import hashlib

from src.agent import ScriptedMockModel, run_agent
from src.framings import FRAMINGS
from src.generators import CALIBRATION_SEEDS
from src.prompts import (
    CONCLUSION_PROMPT,
    CONCLUSION_SCHEMA_BLOCK,
    CONCLUSION_SCHEMA_HEADER,
    TOOL_DOCS,
    build_system_message,
)
from src.tools import ToolService
from src.v2_reporting import _summarize


V1_CONCLUSION_PROMPT_SHA256 = "1d024d62412cc388442a761f65471de23ac8a524c262a77c81a52bb623e775df"


def test_26_schema_visible_from_step_one_and_step_nine_prompt_unchanged(tmp_path):
    assert hashlib.sha256(CONCLUSION_PROMPT.encode("utf-8")).hexdigest() == V1_CONCLUSION_PROMPT_SHA256
    system = build_system_message(FRAMINGS["F_neutral"], 3, "Y", ["A", "B", "Y"])
    assert system.index(CONCLUSION_SCHEMA_HEADER) > system.index(TOOL_DOCS)
    assert system.endswith(CONCLUSION_SCHEMA_HEADER + "\n" + CONCLUSION_SCHEMA_BLOCK)

    import pandas as pd

    frame = pd.DataFrame({"A": [1.0, 2.0, 3.0], "B": [2.0, 3.0, 5.0], "Y": [1.0, 3.0, 4.0]})
    actions = ['{"tool":"distribution","column":"A"}'] * 8
    conclusion = '{"supported_findings":[],"interaction_claims":[],"causal_claims":[],"overall":"no_finding","no_finding_reason":"none"}'
    model = ScriptedMockModel(actions, [conclusion])
    run_agent(
        model,
        ToolService(frame, "addendum04", tmp_path),
        framing=FRAMINGS["F_neutral"],
        n_rows=3,
        columns=list(frame.columns),
    )
    assert CONCLUSION_SCHEMA_HEADER in model.calls[0]["system_message"]
    assert CONCLUSION_PROMPT not in model.calls[0]["user_message"]
    assert CONCLUSION_PROMPT in model.calls[-1]["user_message"]


def test_27_v2_calibration_doubling_grid_and_seed_map():
    assert CALIBRATION_SEEDS == {0.2: 1200, 0.4: 1201, 0.8: 1202, 1.6: 1203, 3.2: 1204}


def test_28_v2_histogram_counts_unknown_tool_as_invalid():
    row = {
        "meta": {"seed": 1},
        "actions": [
            {
                "action": {"tool": "interaction", "a": "X4", "b": "X5"},
                "result": {"error": "unknown tool"},
                "valid": False,
            }
        ],
        "coded": {"interaction_code": "not_considered"},
        "conclusion": {"interaction_claims": []},
        "cost": {"api_calls": 1, "estimated_usd": 0.001},
    }
    summary = _summarize([row])
    assert summary["pooled"]["invalid"] == 1
    assert summary["first"]["invalid"] == 1
    assert summary["per_run"][0]["invalid_actions"] == 1
    assert summary["interaction_pairs"] == {}
