"""Official-SDK Anthropic adapter for instruction-only JSON experiments."""

from __future__ import annotations

from typing import Any

from ..agent import ModelInvariantError, ModelProtocolError
from ..ledger import CostLedger
from ..transient_retry import call_with_transient_retries


class AnthropicModelClient:
    """Map the fixed system/user messages onto Anthropic's Messages API."""

    def __init__(
        self,
        client: Any,
        *,
        model: str,
        ledger: CostLedger,
        batch: str,
        run_id: str,
        batch_cap_usd: float,
        thinking: dict[str, Any] | None,
        effort_default: str | None,
        retry_notes_path: Any | None = None,
    ) -> None:
        self.client = client
        self.model = model
        self.ledger = ledger
        self.batch = batch
        self.run_id = run_id
        self.batch_cap_usd = batch_cap_usd
        self.thinking = thinking
        self.effort_default = effort_default
        self.retry_notes_path = retry_notes_path

    @property
    def sent_parameters(self) -> dict[str, Any]:
        return {
            "model": self.model,
            "max_tokens": 2048,
            "temperature": 1.0,
            "thinking": self.thinking,
            "effort_sent": False,
            "effort_default": self.effort_default,
            "top_p_sent": False,
            "top_k_sent": False,
            "native_tools_sent": False,
            "cache_control_sent": False,
            "structured_output_sent": False,
            "assistant_prefill_sent": False,
        }

    def complete(
        self,
        system_message: str,
        user_message: str,
        *,
        json_mode: bool,
        phase: str,
    ) -> str:
        del json_mode, phase
        self.ledger.ensure_can_call(batch=self.batch, batch_cap_usd=self.batch_cap_usd)
        kwargs: dict[str, Any] = {
            "model": self.model,
            "max_tokens": 2048,
            "temperature": 1.0,
            "system": system_message,
            "messages": [{"role": "user", "content": user_message}],
        }
        if self.thinking is not None:
            # SDK 0.46 predates current thinking literals, so use its official
            # extra_body escape hatch while retaining the official SDK client.
            kwargs["extra_body"] = {"thinking": self.thinking}
        response = (
            call_with_transient_retries(
                lambda: self.client.messages.create(**kwargs),
                notes_path=self.retry_notes_path,
                request_id=self.run_id,
            )
            if self.retry_notes_path is not None
            else self.client.messages.create(**kwargs)
        )
        usage = response.usage
        input_tokens = int(getattr(usage, "input_tokens"))
        output_tokens = int(getattr(usage, "output_tokens"))
        self.ledger.append_usage(
            batch=self.batch,
            run_id=self.run_id,
            usage={
                "prompt_cache_hit_tokens": 0,
                "prompt_cache_miss_tokens": input_tokens,
                "prompt_tokens": input_tokens,
                "completion_tokens": output_tokens,
            },
        )
        blocks = list(response.content)
        thinking_blocks = [block for block in blocks if "thinking" in str(getattr(block, "type", "")).lower()]
        if thinking_blocks:
            raise ModelInvariantError(
                f"Anthropic returned {len(thinking_blocks)} forbidden thinking block(s)"
            )
        if getattr(response, "stop_reason", None) == "max_tokens":
            raise ModelProtocolError('Anthropic stop_reason was "max_tokens"')
        unexpected = [str(getattr(block, "type", "")) for block in blocks if getattr(block, "type", None) != "text"]
        if unexpected:
            raise ModelProtocolError("Anthropic returned unexpected content block(s): " + ", ".join(unexpected))
        return "".join(str(getattr(block, "text", "")) for block in blocks)
