"""Addendum 06 Anthropic smoke selection and three matched S-arms."""

from __future__ import annotations

import hashlib
import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import anthropic
import pandas as pd
from dotenv import load_dotenv

from .agent import run_agent
from .coding import code_run
from .cross_family_reporting import generate_cross_family_report
from .execute_experiment import CACHE, DATA, LEDGER_PATH, RESULTS, ROOT, RUNS, SavedRun, _load_saved
from .framings import FRAMINGS
from .generators import FROZEN_SEEDS
from .ledger import BudgetAbort, CostLedger, Pricing
from .prompts import build_system_message, build_system_message_v1
from .providers.anthropic import AnthropicModelClient
from .run_batch import RunWriter, write_gate_report
from .tools import ToolService


STATE_PATH = RESULTS / "cross_family" / "execution_state.json"
GATES_PATH = RESULTS / "cross_family" / "gates.md"
SELECTION_PATH = RESULTS / "cross_family" / "model_selection.json"
HASH_PATH = RESULTS / "cross_family" / "hash_assertions.json"

EXPECTED_DATA_HASHES = {
    "G1_strong": "3866aaaf50afefb4cc2a53eed327fe6e1c39f8ff7cbc6d4e5f7c642c2b4113df",
    "G1_swap": "42f46d80939763d380503a03309206c720c7291c4527f9b656c46472242e115e",
}
EXPECTED_SYSTEM_HASHES = {
    "v1": "7d304a1519ba008164b4ea16af9193703b740c954d922e8e954a8f06004f1d56",
    "v2": "7899b12c317413ce77b34f70e685eec41196a888225d79f5632af3c73beaf92d",
}


@dataclass(frozen=True)
class Candidate:
    model: str
    thinking: dict[str, Any] | None
    effort_default: str | None
    input_price: float
    output_price: float
    configuration_reason: str

    @property
    def parameters(self) -> dict[str, Any]:
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


class StopReplication(RuntimeError):
    pass


def _write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


class CrossFamilyExperiment:
    def __init__(self) -> None:
        load_dotenv(ROOT / ".env")
        if not os.getenv("ANTHROPIC_API_KEY"):
            raise RuntimeError("ANTHROPIC_API_KEY is missing")
        self.client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"], timeout=120.0, max_retries=0)
        self.writer = RunWriter(RUNS)
        self.state = json.loads(STATE_PATH.read_text(encoding="utf-8")) if STATE_PATH.exists() else {}
        self.state.setdefault("completed_arms", [])
        self.state.setdefault("candidate_results", [])
        self.candidates = [
            Candidate("claude-sonnet-5-5", {"type": "between_tools"}, "high", float(os.environ["PRICE_SONNET_5_5_INPUT_PER_M"]), float(os.environ["PRICE_SONNET_5_5_OUTPUT_PER_M"]), "Official documentation says disabled is rejected; use the pre-registered between_tools fallback."),
            Candidate("claude-sonnet-5", {"type": "disabled"}, "high", float(os.environ["PRICE_SONNET_5_INPUT_PER_M"]), float(os.environ["PRICE_SONNET_5_OUTPUT_PER_M"]), "Official documentation confirmed the model ID and disabled thinking control."),
            Candidate("claude-haiku-4-5-20251001", None, None, float(os.environ["PRICE_HAIKU_4_5_INPUT_PER_M"]), float(os.environ["PRICE_HAIKU_4_5_OUTPUT_PER_M"]), "Official documentation says thinking is off unless explicitly enabled; no thinking or effort parameter is sent."),
        ]
        reasons = {candidate.model: candidate.configuration_reason for candidate in self.candidates}
        for result in self.state["candidate_results"]:
            result.setdefault("configuration_reason", reasons[result["model"]])
        self.hash_assertions = self._assert_hashes()

    def save_state(self, **updates: Any) -> None:
        self.state.update(updates)
        _write_json(STATE_PATH, self.state)

    def _assert_hashes(self) -> dict[str, Any]:
        result: dict[str, Any] = {"data": {}, "system": {}}
        for dataset, expected in EXPECTED_DATA_HASHES.items():
            actual = hashlib.sha256((DATA / f"{dataset}.csv").read_bytes()).hexdigest()
            if actual != expected:
                raise RuntimeError(f"data hash mismatch for {dataset}: {actual} != {expected}")
            result["data"][dataset] = {"deepseek_hash": expected, "anthropic_hash": actual, "match": True}
        frame = pd.read_csv(DATA / "G1_strong.csv")
        for variant, builder in (("v1", build_system_message_v1), ("v2", build_system_message)):
            message = builder(FRAMINGS["F_neutral"], len(frame), "Y", list(frame.columns))
            actual = hashlib.sha256(message.encode("utf-8")).hexdigest()
            expected = EXPECTED_SYSTEM_HASHES[variant]
            if actual != expected:
                raise RuntimeError(f"system hash mismatch for {variant}: {actual} != {expected}")
            result["system"][variant] = {"deepseek_hash": expected, "anthropic_hash": actual, "match": True}
        _write_json(HASH_PATH, result)
        return result

    @staticmethod
    def _pricing(candidate: Candidate) -> Pricing:
        return Pricing(candidate.input_price, 0.0, candidate.output_price)

    @staticmethod
    def _system_message(dataset: str, prompt_variant: str) -> str:
        frame = pd.read_csv(DATA / f"{dataset}.csv")
        builder = build_system_message_v1 if prompt_variant == "v1" else build_system_message
        return builder(FRAMINGS["F_neutral"], len(frame), "Y", list(frame.columns))

    def _run_cost(self, ledger: CostLedger, run_id: str) -> dict[str, Any]:
        rows = [row for row in ledger.rows() if row["run_id"] == run_id]
        return {
            "api_calls": len(rows),
            "prompt_cache_hit_tokens": sum(int(row["prompt_cache_hit_tokens"]) for row in rows),
            "prompt_cache_miss_tokens": sum(int(row["prompt_cache_miss_tokens"]) for row in rows),
            "completion_tokens": sum(int(row["completion_tokens"]) for row in rows),
            "estimated_usd": sum(float(row["estimated_usd"]) for row in rows),
            "enforcement_usd": sum(float(row["enforcement_usd"]) for row in rows),
        }

    def run_one(
        self,
        *,
        candidate: Candidate,
        batch: str,
        episode_id: str,
        dataset: str,
        prompt_variant: str,
        seed: int,
        batch_cap: float,
    ) -> SavedRun:
        directory = RUNS / batch / episode_id / "single"
        saved = _load_saved(directory)
        if saved is not None:
            return saved
        frame = pd.read_csv(DATA / f"{dataset}.csv")
        system_message = self._system_message(dataset, prompt_variant)
        data_hash = hashlib.sha256((DATA / f"{dataset}.csv").read_bytes()).hexdigest()
        system_hash = hashlib.sha256(system_message.encode("utf-8")).hexdigest()
        ledger = CostLedger(LEDGER_PATH, self._pricing(candidate))
        run_id = f"{batch}/{episode_id}/single"
        model = AnthropicModelClient(
            self.client,
            model=candidate.model,
            ledger=ledger,
            batch=batch,
            run_id=run_id,
            batch_cap_usd=batch_cap,
            thinking=candidate.thinking,
            effort_default=candidate.effort_default,
        )
        service = ToolService(frame, dataset, CACHE / "cross_family" / batch, target="Y")
        run = run_agent(
            model,
            service,
            framing=FRAMINGS["F_neutral"],
            n_rows=len(frame),
            columns=list(frame.columns),
            target="Y",
            system_message_override=system_message,
        )
        target_interaction = ("X1", "X3") if dataset == "G1_swap" else ("X4", "X5")
        coded = (
            code_run(run.actions, run.conclusion, row_count=len(frame), target_interaction=target_interaction)
            if run.status == "complete" and run.conclusion is not None
            else {"status": run.status, "protocol_error": run.protocol_error}
        )
        meta = {
            "provider": "anthropic",
            "model": candidate.model,
            "parameters": candidate.parameters,
            "dataset": dataset,
            "framing": "F_neutral",
            "prompt_variant": prompt_variant,
            "mode": "single",
            "seed": seed,
            "agent_order": ["single"],
            "agent_id": "single",
            "position": 1,
            "temperature": 1.0,
            "status": run.status,
            "generator_seed": FROZEN_SEEDS.get(dataset),
            "data_sha256": data_hash,
            "system_message_sha256": system_hash,
        }
        self.writer.write(
            batch=batch,
            episode_id=episode_id,
            agent_id="single",
            meta=meta,
            run=run,
            coded=coded,
            cost=self._run_cost(ledger, run_id),
        )
        saved = _load_saved(directory)
        assert saved is not None
        if run.status == "budget_abort":
            raise BudgetAbort(run.protocol_error or "Anthropic budget abort")
        return saved

    @staticmethod
    def _api_unavailable(exc: Exception) -> bool:
        return isinstance(
            exc,
            (
                anthropic.APIConnectionError,
                anthropic.AuthenticationError,
                anthropic.PermissionDeniedError,
                anthropic.RateLimitError,
                anthropic.InternalServerError,
            ),
        )

    def _write_selection(self) -> None:
        payload = {"candidates": self.state["candidate_results"], "selected_model": self.state.get("selected_model")}
        _write_json(SELECTION_PATH, payload)

    def select_model(self) -> Candidate:
        selected = self.state.get("selected_model")
        if selected:
            return next(candidate for candidate in self.candidates if candidate.model == selected)
        attempted = {item["model"] for item in self.state["candidate_results"]}
        for candidate in self.candidates:
            if candidate.model in attempted:
                prior = next(item for item in self.state["candidate_results"] if item["model"] == candidate.model)
                if prior["passed"]:
                    return candidate
                continue
            runs: list[SavedRun] = []
            errors: list[str] = []
            for seed in (101, 102, 103):
                try:
                    runs.append(
                        self.run_one(
                            candidate=candidate,
                            batch="anthropic_smoke",
                            episode_id=f"{candidate.model}_G1_strong_v2_seed{seed}",
                            dataset="G1_strong",
                            prompt_variant="v2",
                            seed=seed,
                            batch_cap=0.60,
                        )
                    )
                except BudgetAbort:
                    raise
                except Exception as exc:
                    if self._api_unavailable(exc):
                        raise StopReplication(f"API unavailable during {candidate.model}: {type(exc).__name__}: {exc}") from exc
                    errors.append(f"seed {seed}: {type(exc).__name__}: {exc}")
            complete = sum(run.complete for run in runs)
            thinking_failures = sum(run.meta.get("status") == "reasoning_field_failure" for run in runs)
            passed = thinking_failures == 0 and complete >= 2
            reason = "zero thinking blocks and >=2/3 complete" if passed else "; ".join(errors) or f"complete={complete}/3, thinking_block_runs={thinking_failures}"
            result = {
                "model": candidate.model,
                "parameters": candidate.parameters,
                "configuration_reason": candidate.configuration_reason,
                "complete_runs": complete,
                "attempted_runs": len(runs) + len(errors),
                "thinking_block_runs": thinking_failures,
                "passed": passed,
                "reason": reason,
            }
            self.state["candidate_results"].append(result)
            if passed:
                self.save_state(selected_model=candidate.model)
                self._write_selection()
                return candidate
            self.save_state()
            self._write_selection()
        raise StopReplication("all model candidates failed selection")

    def run_arm(self, candidate: Candidate, arm: str, dataset: str, prompt_variant: str) -> None:
        records = [
            self.run_one(
                candidate=candidate,
                batch=arm,
                episode_id=f"{dataset}_{prompt_variant}_seed{seed}",
                dataset=dataset,
                prompt_variant=prompt_variant,
                seed=seed,
                batch_cap=1.20,
            )
            for seed in range(1, 11)
        ]
        complete = sum(record.complete for record in records)
        passed = complete >= 8
        write_gate_report(GATES_PATH, f"Gate 1a {arm}", passed, [f"complete without protocol_failure: {complete}/10"])
        if not passed:
            raise StopReplication(f"Gate 1a failed for {arm}: {complete}/10 complete")
        self.state["completed_arms"].append(arm)
        self.save_state()

    def run(self) -> None:
        try:
            candidate = self.select_model()
            arms = [
                ("anthropic_s_v1", "G1_strong", "v1"),
                ("anthropic_s_v2", "G1_strong", "v2"),
                ("anthropic_s_v3", "G1_swap", "v2"),
            ]
            for arm, dataset, prompt_variant in arms:
                if arm not in self.state["completed_arms"]:
                    self.run_arm(candidate, arm, dataset, prompt_variant)
            analysis = generate_cross_family_report(
                ROOT,
                candidate.model,
                {"candidates": self.state["candidate_results"]},
            )
            self.save_state(live_complete=True, analysis=analysis, stop_reason="completed all three S-arms")
        except BudgetAbort as exc:
            write_gate_report(GATES_PATH, "cross-family budget stop", False, [str(exc)])
            self.save_state(stop_reason=str(exc))
        except StopReplication as exc:
            write_gate_report(GATES_PATH, "cross-family mandatory stop", False, [str(exc)])
            self.save_state(stop_reason=str(exc))
        except Exception as exc:
            if self._api_unavailable(exc):
                message = f"API unavailable: {type(exc).__name__}: {exc}"
                write_gate_report(GATES_PATH, "cross-family API stop", False, [message])
                self.save_state(stop_reason=message)
                return
            raise


def main() -> None:
    CrossFamilyExperiment().run()


if __name__ == "__main__":
    main()
