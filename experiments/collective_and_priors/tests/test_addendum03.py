from __future__ import annotations

from types import SimpleNamespace

import pytest

from src.agent import ModelInvariantError, OpenAIModelClient
from src.collective import agent_order
from src.ledger import CostLedger, Pricing


class _Message:
    content = '{"tool":"distribution","column":"X1"}'

    def model_dump(self):
        return {"content": self.content, "reasoning_content": "forbidden"}


class _Completions:
    def __init__(self):
        self.kwargs = None

    def create(self, **kwargs):
        self.kwargs = kwargs
        usage = SimpleNamespace(
            prompt_cache_hit_tokens=0,
            prompt_cache_miss_tokens=10,
            completion_tokens=5,
            prompt_tokens=10,
        )
        return SimpleNamespace(choices=[SimpleNamespace(message=_Message())], usage=usage)


def test_23_reasoning_field_halts_and_thinking_is_disabled(tmp_path):
    completions = _Completions()
    client = SimpleNamespace(chat=SimpleNamespace(completions=completions))
    ledger = CostLedger(tmp_path / "ledger.csv", Pricing(1.32, 0.044, 3.96))
    model = OpenAIModelClient(
        client,
        model="deepseek-v4-pro",
        temperature=1.0,
        ledger=ledger,
        batch="batch_test",
        run_id="run",
    )
    with pytest.raises(ModelInvariantError):
        model.complete("system", "user", json_mode=True, phase="action")
    assert completions.kwargs["extra_body"] == {"thinking": {"type": "disabled"}}
    assert len(ledger.rows()) == 1


def test_24_frozen_agent_orders():
    assert agent_order(1) == ["A", "B", "C"]
    assert agent_order(2) == ["B", "C", "A"]
    assert agent_order(3) == ["C", "A", "B"]


def test_25_batch_cap_uses_true_cost(tmp_path):
    ledger = CostLedger(tmp_path / "ledger.csv", Pricing(1.0, 0.0, 0.0))
    ledger.append_usage(
        batch="batch_1",
        run_id="run",
        usage={"prompt_cache_hit_tokens": 0, "prompt_cache_miss_tokens": 210_000, "completion_tokens": 0, "prompt_tokens": 210_000},
    )
    with pytest.raises(Exception, match="batch cap"):
        ledger.ensure_can_call(batch="batch_1", batch_cap_usd=0.20)
