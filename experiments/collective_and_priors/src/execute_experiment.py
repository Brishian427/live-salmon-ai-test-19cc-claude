"""Resumable live driver for the fully amended Live Salmon experiment."""

from __future__ import annotations

import csv
import hashlib
import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pandas as pd
from dotenv import load_dotenv
from openai import OpenAI

from .agent import AgentRun, OpenAIModelClient, run_agent
from .coding import add_new_pairs_added, code_run
from .collective import agent_order, aggregate_m1, aggregate_majority, collective_process_metrics
from .framings import FRAMINGS
from .generators import (
    CALIBRATION_SEEDS,
    FROZEN_SEEDS,
    generate_core,
    generate_g0_null,
    generate_g2_calibrated,
    write_dataset,
)
from .ledger import BudgetAbort, CostLedger, Pricing
from .run_batch import RunWriter, write_gate_report
from .tools import ToolService

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
RUNS = ROOT / "runs"
RESULTS = ROOT / "results"
CACHE = ROOT / "cache"
LEDGER_PATH = RESULTS / "cost_ledger.csv"
STATE_PATH = RESULTS / "execution_state.json"
GATES_PATH = RESULTS / "gates.md"

BATCH_CAPS = {
    "batch_1": 0.20,
    "batch_2": 0.20,
    "batch_2_retry": 0.20,
    "batch_3": 1.00,
    "batch_4": 3.00,
    "batch_5": 1.80,
    "batch_6": 1.50,
    "v2_batch_1": 0.20,
    "v2_batch_2": 0.20,
    "v2_batch_2_retry": 0.20,
    "v2_batch_3": 1.00,
    "v2_batch_4": 3.00,
    "v2_batch_5": 1.80,
    "v2_batch_6": 1.50,
    "v3_batch_1": 0.20,
}


class HaltBatch(RuntimeError):
    pass


@dataclass
class SavedRun:
    directory: Path
    meta: dict[str, Any]
    actions: list[dict[str, Any]]
    conclusion: dict[str, Any] | None
    coded: dict[str, Any]

    @property
    def complete(self) -> bool:
        return self.meta.get("status") == "complete"


def _json_write(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _load_saved(directory: Path) -> SavedRun | None:
    required = [directory / name for name in ("meta.json", "actions.jsonl", "coded.json")]
    if not all(path.exists() for path in required):
        return None
    meta = json.loads((directory / "meta.json").read_text(encoding="utf-8"))
    actions = [json.loads(line) for line in (directory / "actions.jsonl").read_text(encoding="utf-8").splitlines() if line]
    coded = json.loads((directory / "coded.json").read_text(encoding="utf-8"))
    conclusion_path = directory / "conclusion.json"
    raw = conclusion_path.read_text(encoding="utf-8").strip() if conclusion_path.exists() else ""
    try:
        conclusion = json.loads(raw) if raw else None
    except json.JSONDecodeError:
        conclusion = None
    return SavedRun(directory, meta, actions, conclusion, coded)


class Experiment:
    def __init__(self) -> None:
        load_dotenv(ROOT / ".env")
        required = [
            "DEEPSEEK_API_KEY",
            "DEEPSEEK_BASE_URL",
            "MODEL_NAME",
            "TEMPERATURE",
            "PRICE_INPUT_CACHE_MISS_PER_M",
            "PRICE_INPUT_CACHE_HIT_PER_M",
            "PRICE_OUTPUT_PER_M",
        ]
        missing = [name for name in required if not os.getenv(name)]
        if missing:
            raise RuntimeError("missing required environment fields: " + ", ".join(missing))
        if os.environ["MODEL_NAME"] != "deepseek-v4-pro":
            raise RuntimeError("MODEL_NAME must be deepseek-v4-pro")
        self.model = os.environ["MODEL_NAME"]
        self.temperature = float(os.environ["TEMPERATURE"])
        self.pricing = Pricing.from_mapping(os.environ)
        if self.pricing != Pricing(1.32, 0.044, 3.96):
            raise RuntimeError("pricing must equal the frozen peak-rate schedule")
        max_usd = float(os.getenv("MAX_USD", "10.00"))
        if max_usd < 9.0:
            raise RuntimeError("MAX_USD must be at least the frozen $9 hard-stop threshold")
        self.client = OpenAI(
            api_key=os.environ["DEEPSEEK_API_KEY"],
            base_url=os.environ["DEEPSEEK_BASE_URL"],
            timeout=120.0,
            max_retries=0,
        )
        self.ledger = CostLedger(LEDGER_PATH, self.pricing)
        self.writer = RunWriter(RUNS)
        self.state = json.loads(STATE_PATH.read_text(encoding="utf-8")) if STATE_PATH.exists() else {}
        self.state.setdefault("completed_batches", [])
        self.state.setdefault("leg_a_enabled", True)
        self.state.setdefault("temperature", self.temperature)
        self.temperature = float(self.state["temperature"])

    def save_state(self, **updates: Any) -> None:
        self.state.update(updates)
        _json_write(STATE_PATH, self.state)

    def dataset(self, name: str) -> tuple[pd.DataFrame, str]:
        path = DATA / f"{name}.csv"
        if name.startswith("calibration_theta_"):
            path = DATA / "calibration" / f"{name}.csv"
        frame = pd.read_csv(path)
        return frame, "period_s" if name == "B4_shuffled" else "Y"

    def _run_cost(self, run_id: str) -> dict[str, Any]:
        rows = [row for row in self.ledger.rows() if row["run_id"] == run_id]
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
        batch: str,
        episode_id: str,
        agent_id: str,
        dataset_name: str,
        framing_name: str,
        mode: str,
        seed: int,
        order: list[str] | None = None,
        position: int = 1,
        prior_entries: list[dict[str, Any]] | None = None,
    ) -> SavedRun:
        directory = RUNS / batch / episode_id / agent_id
        saved = _load_saved(directory)
        if saved is not None:
            if saved.meta.get("status") == "reasoning_field_failure":
                raise HaltBatch(f"forbidden reasoning field in saved run {batch}/{episode_id}/{agent_id}")
            return saved

        frame, target = self.dataset(dataset_name)
        run_id = f"{batch}/{episode_id}/{agent_id}"
        model_client = OpenAIModelClient(
            self.client,
            model=self.model,
            temperature=self.temperature,
            ledger=self.ledger,
            batch=batch,
            run_id=run_id,
            batch_cap_usd=BATCH_CAPS[batch],
        )
        service = ToolService(frame, dataset_name, getattr(self, "cache_dir", CACHE), target=target)
        run = run_agent(
            model_client,
            service,
            framing=FRAMINGS[framing_name],
            n_rows=len(frame),
            columns=list(frame.columns),
            target=target,
            prior_entries=prior_entries,
        )
        coded = (
            code_run(
                run.actions,
                run.conclusion,
                row_count=len(frame),
                is_g3=dataset_name == "G3_confound",
                target_interaction=("X1", "X3") if dataset_name == "G1_swap" else ("X4", "X5"),
            )
            if run.status == "complete" and run.conclusion is not None
            else {"status": run.status, "protocol_error": run.protocol_error}
        )
        if run.status == "complete":
            coded["position"] = position
            coded["new_pairs_added"] = len(coded.get("pairs_touched", []))
        meta = {
            "dataset": dataset_name,
            "framing": framing_name,
            "mode": mode,
            "seed": seed,
            "agent_order": order or [agent_id],
            "agent_id": agent_id,
            "position": position,
            "model": self.model,
            "temperature": self.temperature,
            "status": run.status,
            "generator_seed": FROZEN_SEEDS.get(dataset_name),
        }
        self.writer.write(
            batch=batch,
            episode_id=episode_id,
            agent_id=agent_id,
            meta=meta,
            run=run,
            coded=coded,
            cost=self._run_cost(run_id),
        )
        saved = _load_saved(directory)
        assert saved is not None
        if run.status == "reasoning_field_failure":
            raise HaltBatch(f"forbidden reasoning field in {run_id}")
        if run.status == "budget_abort":
            raise BudgetAbort(run.protocol_error or f"budget abort in {run_id}")
        return saved

    def run_episode(
        self,
        *,
        batch: str,
        episode_id: str,
        dataset_name: str,
        framing_name: str,
        mode: str,
        seed: int,
    ) -> list[SavedRun]:
        order = agent_order(seed)
        prior: list[dict[str, Any]] = []
        records: list[SavedRun] = []
        for position, agent_id in enumerate(order, start=1):
            record = self.run_one(
                batch=batch,
                episode_id=episode_id,
                agent_id=agent_id,
                dataset_name=dataset_name,
                framing_name=framing_name,
                mode=mode,
                seed=seed,
                order=order,
                position=position,
                prior_entries=prior if mode == "shared" else None,
            )
            records.append(record)
            if mode == "shared":
                prior.extend(record.actions)
        complete = [record for record in records if record.complete]
        if len(complete) == 3:
            coded = [record.coded for record in records]
            add_new_pairs_added(coded, shared_log=mode == "shared")
            for record, updated in zip(records, coded):
                _json_write(record.directory / "coded.json", updated)
                record.coded = updated
        return records

    def _single(self, batch: str, dataset: str, framing: str, seed: int, *, tag: str = "") -> SavedRun:
        suffix = f"_{tag}" if tag else ""
        return self.run_one(
            batch=batch,
            episode_id=f"{dataset}_{framing}_seed{seed}{suffix}",
            agent_id="single",
            dataset_name=dataset,
            framing_name=framing,
            mode="single",
            seed=seed,
        )

    def mark_batch(self, batch: str) -> None:
        if batch not in self.state["completed_batches"]:
            self.state["completed_batches"].append(batch)
        self.save_state()

    def batch1(self) -> bool:
        runs = [self._single("batch_1", "G1_strong", "F_neutral", seed) for seed in (1, 2, 3)]
        complete = [run for run in runs if run.complete]
        gate1a = len(complete) >= 2
        successes = [run for run in complete if run.coded.get("interaction_code") == "reported_supported"]
        write_gate_report(GATES_PATH, "Gate 1a", gate1a, [f"complete runs: {len(complete)}/3"])
        if not gate1a:
            return False
        gate1b = bool(successes)
        details = [f"reported_supported: {len(successes)}/3"]
        details.extend(f"seed {run.meta['seed']} pairs: {run.coded.get('pairs_touched', [])}" for run in runs)
        mean_cost = sum(json.loads((run.directory / "cost.json").read_text())["estimated_usd"] for run in runs) / 3
        details.append(f"measured mean cost/run: ${mean_cost:.6f}; 127-run extrapolation: ${127 * mean_cost:.4f}")
        write_gate_report(GATES_PATH, "Gate 1b", gate1b, details)
        if gate1b:
            self.mark_batch("batch_1")
        return gate1b

    def batch2(self) -> None:
        def attempt(batch: str) -> float:
            records = [self._single(batch, "G1_strong", "F_neutral", 1, tag=f"rep{i}") for i in (1, 2, 3)]
            return collective_process_metrics([record.coded for record in records])["pairwise_jaccard"]

        jaccard = attempt("batch_2")
        passed = jaccard < 0.80
        write_gate_report(GATES_PATH, "Gate 2 initial", passed, [f"pairwise_jaccard: {jaccard:.6f}", f"temperature: {self.temperature}"])
        if not passed:
            self.temperature = 1.3
            self.save_state(temperature=1.3)
            with (ROOT / "CHANGES.md").open("a", encoding="utf-8") as handle:
                handle.write("\n## Batch 2 temperature escalation\n\nGate 2 failed at the configured temperature; the authorized one-time retry uses temperature 1.3.\n")
            jaccard = attempt("batch_2_retry")
            passed = jaccard < 0.80
            write_gate_report(GATES_PATH, "Gate 2 retry", passed, [f"pairwise_jaccard: {jaccard:.6f}", "temperature: 1.3"])
        if not passed:
            self.save_state(leg_a_enabled=False)
            with (ROOT / "CHANGES.md").open("a", encoding="utf-8") as handle:
                handle.write("\nLeg A is skipped because both authorized Gate 2 attempts failed.\n")
        self.mark_batch("batch_2")

    def batch3(self) -> None:
        calibration_dir = DATA / "calibration"
        rates: dict[float, float] = {}
        rows: list[dict[str, Any]] = []
        for theta in (0.8, 0.5, 0.3, 0.2, 0.1):
            name = f"calibration_theta_{str(theta).replace('.', 'p')}"
            csv_path = calibration_dir / f"{name}.csv"
            if not csv_path.exists():
                frame, truth = generate_core(theta, CALIBRATION_SEEDS[theta])
                write_dataset(name, frame, truth, calibration_dir)
            runs = [self._single("batch_3", name, "F_neutral", seed) for seed in (1, 2, 3, 4, 5)]
            success = sum(run.complete and run.coded.get("interaction_code") == "reported_supported" for run in runs)
            rates[theta] = success / 5
            rows.append({"theta": theta, "successes": success, "n": 5, "success_rate": rates[theta]})
        table = RESULTS / "tables" / "calibration.csv"
        table.parent.mkdir(parents=True, exist_ok=True)
        with table.open("w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
            writer.writeheader(); writer.writerows(rows)
        theta_star = min(rates, key=lambda theta: (abs(rates[theta] - 0.5), theta))
        gate = any(0.25 <= rate <= 0.75 for rate in rates.values())
        write_gate_report(GATES_PATH, "Gate 3", gate, [f"theta={theta}: rate={rate:.3f}" for theta, rate in rates.items()] + [f"theta_star: {theta_star}", f"calibration_deviation: {str(not gate).lower()}"])
        if not gate:
            with (ROOT / "CHANGES.md").open("a", encoding="utf-8") as handle:
                handle.write("\n## Batch 3 calibration deviation\n\nNo theta had success rate in [0.25, 0.75]; the closest value was used without extending the sweep.\n")
        g2_path = DATA / "G2_calibrated.csv"
        if not g2_path.exists():
            frame, truth = generate_g2_calibrated(theta_star)
            write_dataset("G2_calibrated", frame, truth, DATA)
        self.save_state(theta_star=theta_star, calibration_rates={str(k): v for k, v in rates.items()}, calibration_deviation=not gate)
        self.mark_batch("batch_3")

    def batch4(self) -> None:
        if not self.state.get("leg_a_enabled", True):
            self.mark_batch("batch_4_skipped")
            return
        for dataset in ("G1_strong", "G2_calibrated"):
            for seed in (1, 2, 3):
                self._single("batch_4", dataset, "F_neutral", seed, tag="canonical")
                self.run_episode(batch="batch_4", episode_id=f"{dataset}_isolated_seed{seed}", dataset_name=dataset, framing_name="F_neutral", mode="isolated", seed=seed)
                self.run_episode(batch="batch_4", episode_id=f"{dataset}_shared_seed{seed}", dataset_name=dataset, framing_name="F_neutral", mode="shared", seed=seed)
        self.mark_batch("batch_4")

    def batch5(self) -> None:
        for seed in (1, 2, 3):
            self._single("batch_5", "G4_underpowered", "F_neutral", seed)
            self.run_episode(batch="batch_5", episode_id=f"G4_underpowered_shared_seed{seed}", dataset_name="G4_underpowered", framing_name="F_neutral", mode="shared", seed=seed)
            self._single("batch_5", "G0_null", "F_neutral", seed)
            self.run_episode(batch="batch_5", episode_id=f"G0_null_isolated_seed{seed}", dataset_name="G0_null", framing_name="F_neutral", mode="isolated", seed=seed)
            self.run_episode(batch="batch_5", episode_id=f"G0_null_shared_seed{seed}", dataset_name="G0_null", framing_name="F_neutral", mode="shared", seed=seed)
        self.mark_batch("batch_5")

    def batch6(self) -> None:
        cells = [
            ("B1", "G3_confound", "F_neutral"),
            ("B2", "G3_confound", "F_econ"),
            ("B4a", "B4_shuffled", "F_pendulum"),
            ("B4b", "B4_shuffled", "F_sensor"),
            ("B3", "G3_confound", "F_phys"),
        ]
        hashes = [hashlib.sha256((DATA / "G3_confound.csv").read_bytes()).hexdigest() for _ in range(3)]
        if len(set(hashes)) != 1:
            raise RuntimeError("B1/B2/B3 dataset hash assertion failed")
        for cell, dataset, framing in cells:
            for seed in (1, 2, 3):
                self._single("batch_6", dataset, framing, seed, tag=cell)
        self.mark_batch("batch_6")

    def run(self) -> None:
        stages = [
            ("batch_1", self.batch1),
            ("batch_2", self.batch2),
            ("batch_3", self.batch3),
            ("batch_4", self.batch4),
            ("batch_5", self.batch5),
            ("batch_6", self.batch6),
        ]
        for name, action in stages:
            if name in self.state["completed_batches"]:
                continue
            try:
                outcome = action()
                if outcome is False:
                    self.save_state(stopped_at=name, stop_reason="gate failure")
                    return
            except (BudgetAbort, HaltBatch) as exc:
                write_gate_report(GATES_PATH, f"{name} mandatory stop", False, [str(exc)])
                self.save_state(stopped_at=name, stop_reason=str(exc))
                return
            except Exception as exc:
                message = f"{type(exc).__name__}: {exc}"
                write_gate_report(GATES_PATH, f"{name} external/runtime stop", False, [message])
                self.save_state(stopped_at=name, stop_reason=message)
                return
        self.save_state(live_complete=True)


def main() -> None:
    Experiment().run()


if __name__ == "__main__":
    main()
