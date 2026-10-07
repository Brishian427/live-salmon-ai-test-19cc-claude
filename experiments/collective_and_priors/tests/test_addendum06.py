from __future__ import annotations

import hashlib
from pathlib import Path
from types import SimpleNamespace

import pandas as pd
import pytest

from src.agent import ModelInvariantError, ModelProtocolError, run_agent
from src.framings import FRAMINGS
from src.ledger import CostLedger, Pricing
from src.prompts import build_system_message, build_system_message_v1
from src.providers.anthropic import AnthropicModelClient
from src.providers.deepseek import DeepSeekModelClient
from src.agent import OpenAIModelClient
from src.tools import ToolService


class FakeMessages:
    def __init__(self, response):
        self.response = response
        self.kwargs = None

    def create(self, **kwargs):
        self.kwargs = kwargs
        return self.response


def _response(*, blocks=None, stop_reason="end_turn"):
    return SimpleNamespace(
        usage=SimpleNamespace(input_tokens=1000, output_tokens=100),
        content=blocks or [SimpleNamespace(type="text", text='{"tool":"distribution","column":"X1"}')],
        stop_reason=stop_reason,
    )


def _adapter(tmp_path, response, *, thinking=None):
    messages = FakeMessages(response)
    client = SimpleNamespace(messages=messages)
    ledger = CostLedger(tmp_path / "ledger.csv", Pricing(2.0, 0.0, 10.0))
    adapter = AnthropicModelClient(
        client,
        model="claude-sonnet-5-5",
        ledger=ledger,
        batch="smoke",
        run_id="smoke/run",
        batch_cap_usd=0.60,
        thinking=thinking,
        effort_default="high",
    )
    return adapter, messages, ledger


def test_33_anthropic_adapter_exact_wire_shape_and_direct_usage(tmp_path):
    adapter, messages, ledger = _adapter(tmp_path, _response(), thinking={"type": "between_tools"})
    raw = adapter.complete("SYSTEM", "USER", json_mode=True, phase="action")
    assert raw.startswith("{")
    assert messages.kwargs == {
        "model": "claude-sonnet-5-5",
        "max_tokens": 2048,
        "temperature": 1.0,
        "system": "SYSTEM",
        "messages": [{"role": "user", "content": "USER"}],
        "extra_body": {"thinking": {"type": "between_tools"}},
    }
    assert ledger.rows()[0]["prompt_cache_miss_tokens"] == "1000"
    assert ledger.rows()[0]["completion_tokens"] == "100"
    assert ledger.cumulative_usd == pytest.approx(0.003)


def test_34_anthropic_thinking_block_is_invariant_failure_after_usage(tmp_path):
    response = _response(blocks=[SimpleNamespace(type="thinking", thinking="hidden")])
    adapter, _messages, ledger = _adapter(tmp_path, response)
    with pytest.raises(ModelInvariantError, match="forbidden thinking"):
        adapter.complete("S", "U", json_mode=True, phase="action")
    assert len(ledger.rows()) == 1


def test_35_anthropic_max_tokens_is_protocol_failure_after_usage(tmp_path):
    adapter, _messages, ledger = _adapter(tmp_path, _response(stop_reason="max_tokens"))
    with pytest.raises(ModelProtocolError, match="max_tokens"):
        adapter.complete("S", "U", json_mode=True, phase="action")
    assert len(ledger.rows()) == 1


def test_36_agent_codes_provider_protocol_error(tmp_path):
    class FailingModel:
        def complete(self, *_args, **_kwargs):
            raise ModelProtocolError("provider stop")

    frame = pd.DataFrame({"X1": [0.0, 1.0], "Y": [0.0, 1.0]})
    run = run_agent(
        FailingModel(),
        ToolService(frame, "tiny", tmp_path, target="Y"),
        framing=FRAMINGS["F_neutral"],
        n_rows=2,
        columns=list(frame.columns),
    )
    assert run.status == "protocol_failure"
    assert run.protocol_error == "provider stop"


def test_37_cross_family_hashes_match_frozen_deepseek_inputs():
    project_root = Path(__file__).resolve().parents[1]
    expected_data = {
        "G1_strong": "3866aaaf50afefb4cc2a53eed327fe6e1c39f8ff7cbc6d4e5f7c642c2b4113df",
        "G1_swap": "42f46d80939763d380503a03309206c720c7291c4527f9b656c46472242e115e",
    }
    for name, expected in expected_data.items():
        assert hashlib.sha256((project_root / "data" / f"{name}.csv").read_bytes()).hexdigest() == expected
    frame = pd.read_csv(project_root / "data" / "G1_strong.csv")
    args = (FRAMINGS["F_neutral"], len(frame), "Y", list(frame.columns))
    assert hashlib.sha256(build_system_message_v1(*args).encode()).hexdigest() == "7d304a1519ba008164b4ea16af9193703b740c954d922e8e954a8f06004f1d56"
    assert hashlib.sha256(build_system_message(*args).encode()).hexdigest() == "7899b12c317413ce77b34f70e685eec41196a888225d79f5632af3c73beaf92d"


def test_38_deepseek_compatibility_export_is_unchanged():
    assert DeepSeekModelClient is OpenAIModelClient
