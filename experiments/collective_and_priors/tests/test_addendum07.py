from src.coding import code_run
from src.collective import agent_order
from src.execute_collective import LABEL, offline_baselines
from src.transient_retry import RetryExhausted, call_with_transient_retries
import anthropic
import httpx
import json
import pytest


def test_rotation_ten_episodes() -> None:
    assert [agent_order(seed) for seed in range(1, 11)] == [
        ["A", "B", "C"], ["B", "C", "A"], ["C", "A", "B"],
    ] * 3 + [["A", "B", "C"]]


def test_shared_evidence_affects_coding_not_own_process() -> None:
    shared = [{"step": 1, "action": {"tool": "test_interaction", "a": "X4", "b": "X5"},
               "result": {"interaction_p": 0.001}, "valid": True}]
    conclusion = {"interaction_claims": [{"terms": ["X4", "X5"], "status": "supported", "reason": "p=0.001"}]}
    coded = code_run([], conclusion, row_count=1000, shared_entries=shared)
    assert coded["interaction_code"] == "reported_supported"
    assert coded["unsupported_by_log"] is False
    assert coded["n_fabricated"] == 0
    assert coded["n_actions"] == 0
    assert coded["coverage"] == 0


def test_offline_m1_m2_exact_triples() -> None:
    result = offline_baselines()
    assert result["n_triples"] == 120
    assert result["single_supported"] == 5
    assert result["M1"] == 110
    assert result["M2"] == 60
    assert result["label"] == LABEL


def _connection_error() -> anthropic.APIConnectionError:
    return anthropic.APIConnectionError(request=httpx.Request("POST", "https://example.invalid/messages"))


def test_transient_retry_reuses_request_and_logs_fixed_backoff(tmp_path) -> None:
    calls = []
    sleeps = []
    request = object()

    def send():
        calls.append(request)
        if len(calls) < 3:
            raise _connection_error()
        return "ok"

    path = tmp_path / "cost_ledger.notes.jsonl"
    assert call_with_transient_retries(send, notes_path=path, request_id="run", sleep=sleeps.append) == "ok"
    assert calls == [request, request, request]
    assert sleeps == [2, 4]
    notes = [json.loads(line) for line in path.read_text().splitlines()]
    assert [note["attempt_number"] for note in notes] == [2, 3]
    assert [note["error_class"] for note in notes] == ["APIConnectionError"] * 2


def test_transient_retry_exhausts_after_five_resends(tmp_path) -> None:
    calls = []
    sleeps = []

    def send():
        calls.append(1)
        raise _connection_error()

    path = tmp_path / "notes.jsonl"
    with pytest.raises(RetryExhausted):
        call_with_transient_retries(send, notes_path=path, request_id="run", sleep=sleeps.append)
    assert len(calls) == 6
    assert sleeps == [2, 4, 8, 16, 32]
    notes = [json.loads(line) for line in path.read_text().splitlines()]
    assert [note["event"] for note in notes] == ["retry"] * 5 + ["retry_exhausted"]


def test_nontransient_error_is_not_retried(tmp_path) -> None:
    path = tmp_path / "notes.jsonl"
    with pytest.raises(ValueError):
        call_with_transient_retries(lambda: (_ for _ in ()).throw(ValueError("bad")), notes_path=path, request_id="run", sleep=lambda _: None)
    assert not path.exists()
