"""Eight-action agent loop and deterministic offline mock support."""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any

from .ledger import BudgetAbort, CostLedger
from .prompts import RETRY_PROMPT, build_system_message, build_user_message
from .providers.base import CompletionClient
from .tools import ToolService

ModelClient = CompletionClient


class ModelInvariantError(RuntimeError):
    """A provider response violated a pre-registered experiment invariant."""


class ModelProtocolError(RuntimeError):
    """A provider response is an explicit section 5.3 protocol failure."""


@dataclass
class AgentRun:
    status: str
    actions: list[dict[str, Any]]
    conclusion_raw: str | None
    conclusion: dict[str, Any] | None
    protocol_error: str | None = None


def _parse_action(raw: str) -> tuple[dict[str, Any] | None, str | None]:
    try:
        parsed = json.loads(raw)
    except json.JSONDecodeError as exc:
        return None, f"invalid JSON: {exc.msg}"
    if not isinstance(parsed, dict):
        return None, "action must be a JSON object"
    if "tool" not in parsed:
        return None, "action object is missing tool"
    return parsed, None


def _parse_object(raw: str) -> tuple[dict[str, Any] | None, str | None]:
    try:
        parsed = json.loads(raw)
    except json.JSONDecodeError as exc:
        return None, f"invalid JSON: {exc.msg}"
    if not isinstance(parsed, dict):
        return None, "conclusion must be a JSON object"
    return parsed, None


def _request_with_two_retries(
    model: ModelClient,
    system_message: str,
    user_message: str,
    *,
    phase: str,
    require_tool: bool,
) -> tuple[str, dict[str, Any] | None, str | None]:
    request_user_message = user_message
    raw = ""
    error: str | None = None
    for _attempt in range(3):
        raw = model.complete(
            system_message,
            request_user_message,
            json_mode=True,
            phase=phase,
        )
        parsed, error = _parse_action(raw) if require_tool else _parse_object(raw)
        if error is None:
            return raw, parsed, None
        request_user_message = user_message + "\n\n" + RETRY_PROMPT.format(error=error)
    return raw, None, error


def run_agent(
    model: ModelClient,
    tool_service: ToolService,
    *,
    framing: str,
    n_rows: int,
    columns: list[str],
    target: str = "Y",
    prior_entries: list[dict[str, Any]] | None = None,
    system_message_override: str | None = None,
) -> AgentRun:
    """Run exactly eight validly parsed action emissions, then one conclusion."""
    action_log: list[dict[str, Any]] = []
    system_message = system_message_override or build_system_message(framing, n_rows, target, columns)
    for step in range(1, 9):
        user_message = build_user_message(action_log, prior_entries=prior_entries)
        try:
            raw, action, error = _request_with_two_retries(
                model,
                system_message,
                user_message,
                phase="action",
                require_tool=True,
            )
        except ModelInvariantError as exc:
            return AgentRun(
                status="reasoning_field_failure",
                actions=action_log,
                conclusion_raw=None,
                conclusion=None,
                protocol_error=str(exc),
            )
        except ModelProtocolError as exc:
            return AgentRun(
                status="protocol_failure",
                actions=action_log,
                conclusion_raw=None,
                conclusion=None,
                protocol_error=str(exc),
            )
        except BudgetAbort as exc:
            return AgentRun(
                status="budget_abort",
                actions=action_log,
                conclusion_raw=None,
                conclusion=None,
                protocol_error=str(exc),
            )
        if error is not None or action is None:
            return AgentRun(
                status="protocol_failure",
                actions=action_log,
                conclusion_raw=None,
                conclusion=None,
                protocol_error=error,
            )
        result = tool_service.execute(action)
        action_log.append(
            {
                "step": step,
                "action": action,
                "result": result,
                "valid": "error" not in result,
                "raw": raw,
            }
        )

    conclusion_user_message = build_user_message(
        action_log,
        prior_entries=prior_entries,
        conclusion=True,
    )
    try:
        raw, conclusion, error = _request_with_two_retries(
            model,
            system_message,
            conclusion_user_message,
            phase="conclusion",
            require_tool=False,
        )
    except ModelInvariantError as exc:
        return AgentRun(
            status="reasoning_field_failure",
            actions=action_log,
            conclusion_raw=None,
            conclusion=None,
            protocol_error=str(exc),
        )
    except ModelProtocolError as exc:
        return AgentRun(
            status="protocol_failure",
            actions=action_log,
            conclusion_raw=raw if "raw" in locals() else None,
            conclusion=None,
            protocol_error=str(exc),
        )
    except BudgetAbort as exc:
        return AgentRun(
            status="budget_abort",
            actions=action_log,
            conclusion_raw=None,
            conclusion=None,
            protocol_error=str(exc),
        )
    if error is not None or conclusion is None:
        return AgentRun(
            status="protocol_failure",
            actions=action_log,
            conclusion_raw=raw,
            conclusion=None,
            protocol_error=error,
        )
    return AgentRun(
        status="complete",
        actions=action_log,
        conclusion_raw=raw,
        conclusion=conclusion,
    )


class ScriptedMockModel:
    """Offline model that returns caller-supplied outputs in order."""

    def __init__(self, action_outputs: list[str], conclusion_outputs: list[str]) -> None:
        self.action_outputs = iter(action_outputs)
        self.conclusion_outputs = iter(conclusion_outputs)
        self.calls: list[dict[str, Any]] = []

    def complete(
        self,
        system_message: str,
        user_message: str,
        *,
        json_mode: bool,
        phase: str,
    ) -> str:
        self.calls.append(
            {
                "system_message": system_message,
                "user_message": user_message,
                "json_mode": json_mode,
                "phase": phase,
            }
        )
        if phase == "action":
            return next(self.action_outputs)
        return next(self.conclusion_outputs)


class OpenAIModelClient:
    """OpenAI-compatible client that records actual response usage per call."""

    def __init__(
        self,
        client: Any,
        *,
        model: str,
        temperature: float,
        ledger: CostLedger,
        batch: str,
        run_id: str,
        batch_cap_usd: float | None = None,
    ) -> None:
        self.client = client
        self.model = model
        self.temperature = temperature
        self.ledger = ledger
        self.batch = batch
        self.run_id = run_id
        self.batch_cap_usd = batch_cap_usd

    def complete(
        self,
        system_message: str,
        user_message: str,
        *,
        json_mode: bool,
        phase: str,
    ) -> str:
        self.ledger.ensure_can_call(batch=self.batch, batch_cap_usd=self.batch_cap_usd)
        response = self.client.chat.completions.create(
            model=self.model,
            temperature=self.temperature,
            response_format={"type": "json_object"} if json_mode else None,
            extra_body={"thinking": {"type": "disabled"}},
            messages=[
                {"role": "system", "content": system_message},
                {"role": "user", "content": user_message},
            ],
        )
        self.ledger.append_usage(
            batch=self.batch,
            run_id=self.run_id,
            usage=response.usage,
        )
        message = response.choices[0].message
        payload = message.model_dump() if hasattr(message, "model_dump") else vars(message)
        offending = [
            str(key)
            for key, value in payload.items()
            if ("reasoning" in str(key).lower() or "thinking" in str(key).lower())
            and value not in (None, "", [], {})
        ]
        if offending:
            raise ModelInvariantError(
                "provider returned forbidden reasoning/thinking field(s): " + ", ".join(sorted(offending))
            )
        content = message.content
        return "" if content is None else content
