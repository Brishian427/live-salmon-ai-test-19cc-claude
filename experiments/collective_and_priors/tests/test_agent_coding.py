from __future__ import annotations

import json

from src.agent import ScriptedMockModel, run_agent
from src.coding import add_new_pairs_added, code_run, fabricated_numbers, process_metrics
from src.generators import generate_g1_strong
from src.framings import F_NEUTRAL
from src.tools import ToolService


def _conclusion(status="supported", reason="interaction p=0.01"):
    return {
        "supported_findings": [],
        "interaction_claims": [{"terms": ["X4", "X5"], "status": status, "reason": reason}],
        "causal_claims": [],
        "overall": "findings_reported",
        "no_finding_reason": None,
    }


def test_09_agent_loop_uses_exactly_eight_actions_then_conclusion(tmp_path):
    frame, _ = generate_g1_strong()
    service = ToolService(frame, "G1_agent", tmp_path / "cache")
    action = json.dumps({"tool": "distribution", "column": "X4"})
    model = ScriptedMockModel([action] * 8, [json.dumps(_conclusion())])
    run = run_agent(
        model,
        service,
        framing=F_NEUTRAL,
        n_rows=len(frame),
        columns=list(frame.columns),
    )
    assert run.status == "complete"
    assert len(run.actions) == 8
    assert [call["phase"] for call in model.calls] == ["action"] * 8 + ["conclusion"]
    assert all(call["json_mode"] for call in model.calls)


def test_10_protocol_failure_is_separate_and_not_scored(tmp_path):
    frame, _ = generate_g1_strong()
    service = ToolService(frame, "G1_failure", tmp_path / "cache")
    model = ScriptedMockModel(["garbage"] * 3, [])
    run = run_agent(
        model,
        service,
        framing=F_NEUTRAL,
        n_rows=len(frame),
        columns=list(frame.columns),
    )
    assert run.status == "protocol_failure"
    assert run.conclusion is None
    assert run.actions == []
    assert len(model.calls) == 3


def test_11_named_but_unsupported_interaction_is_rejected():
    actions = [
        {
            "step": 1,
            "action": {"tool": "test_interaction", "a": "X4", "b": "X5"},
            "result": {"interaction_p": 0.3},
            "valid": True,
        }
    ]
    coded = code_run(actions, _conclusion(status="uncertain", reason="insufficient evidence"), row_count=1000)
    assert coded["interaction_code"] == "considered_rejected"
    assert coded["rejection_reason_primary"] == "insufficient_evidence"


def test_12_fabricated_number_detection():
    actions = [{"result": {"coef": 1.23456, "p": 0.0123456}}]
    clean = _conclusion(reason="coef 1.23 and p 0.0123")
    dirty = _conclusion(reason="coef 1.23 and score 7.77")
    assert fabricated_numbers(actions, clean, row_count=1000)["n_fabricated"] == 0
    result = fabricated_numbers(actions, dirty, row_count=1000)
    assert result["n_fabricated"] == 1
    assert result["fabricated_values"] == [7.77]


def test_13_nineteen_pairs_has_point_one_coverage():
    actions = [
        {
            "action": {"tool": "correlation", "a": "X1", "b": f"X{i}"},
            "result": {"r": 0.0, "p": 1.0},
            "valid": True,
        }
        for i in range(2, 21)
    ]
    assert process_metrics(actions)["coverage"] == 0.1


def test_21_b4_outcomes_are_distinct():
    conclusion = _conclusion()
    conclusion["supported_findings"] = [{"term": "mass_kg", "direction": "positive", "evidence": "p=0.01"}]
    coded = code_run([], conclusion, row_count=300)
    assert coded["any_supported"] is True
    assert coded["length_supported"] is False
    conclusion["supported_findings"].append(
        {"term": "length_m:mass_kg", "direction": "positive", "evidence": "p=0.01"}
    )
    assert code_run([], conclusion, row_count=300)["length_supported"] is True


def test_22_new_pairs_added_by_position():
    runs = [
        {"pairs_touched": [["X1", "X2"], ["X1", "X3"]]},
        {"pairs_touched": [["X1", "X2"], ["X2", "X3"]]},
        {"pairs_touched": [["X2", "X3"], ["X3", "X4"]]},
    ]
    shared = add_new_pairs_added(runs, shared_log=True)
    assert [run["position"] for run in shared] == [1, 2, 3]
    assert [run["new_pairs_added"] for run in shared] == [2, 1, 1]
