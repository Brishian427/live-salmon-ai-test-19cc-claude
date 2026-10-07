"""Resumable Addendum 04 v2 driver with fully separate run paths."""

from __future__ import annotations

import csv
import json
import shutil
from pathlib import Path
from typing import Any

from .collective import collective_process_metrics
from .execute_experiment import (
    CACHE,
    DATA,
    RESULTS,
    ROOT,
    BudgetAbort,
    Experiment,
    HaltBatch,
    write_gate_report,
)
from .generators import CALIBRATION_SEEDS, generate_core, generate_g2_calibrated, write_dataset
from .v2_reporting import write_batch1_comparison


V2_STATE = RESULTS / "v2" / "execution_state.json"
V2_GATES = RESULTS / "v2" / "gates.md"
V2_CALIBRATION = DATA / "calibration_v2"


class V2Experiment(Experiment):
    def __init__(self) -> None:
        super().__init__()
        self.state = json.loads(V2_STATE.read_text(encoding="utf-8")) if V2_STATE.exists() else {}
        self.state.setdefault("completed_batches", [])
        self.state.setdefault("leg_a_enabled", True)
        self.state.setdefault("temperature", float(self.temperature))
        self.temperature = float(self.state["temperature"])
        self.cache_dir = CACHE / ("v2_postcal" if self.state.get("calibration_complete") else "v2_precal")

    def save_state(self, **updates: Any) -> None:
        self.state.update(updates)
        V2_STATE.parent.mkdir(parents=True, exist_ok=True)
        V2_STATE.write_text(json.dumps(self.state, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    def dataset(self, name: str):
        if name.startswith("v2_calibration_theta_"):
            import pandas as pd

            return pd.read_csv(V2_CALIBRATION / f"{name}.csv"), "Y"
        return super().dataset(name)

    def batch1(self) -> bool:
        runs = [self._single("v2_batch_1", "G1_strong", "F_neutral", seed) for seed in range(1, 11)]
        complete = [run for run in runs if run.complete]
        supported = [run for run in complete if run.coded.get("interaction_code") == "reported_supported"]
        write_gate_report(
            V2_GATES,
            "v2 Batch 1 protocol and pre-registered branch",
            len(complete) == 10,
            [f"complete runs: {len(complete)}/10", f"reported_supported: {len(supported)}/10"],
        )
        summary = write_batch1_comparison(ROOT)
        if len(complete) != 10:
            raise HaltBatch(f"v2 Batch 1 protocol-complete runs: {len(complete)}/10")
        self.mark_batch("v2_batch_1")
        self.save_state(batch1_reported_supported=len(supported))
        return bool(summary["v2"]["reported_supported"])

    def batch2(self) -> bool:
        def attempt(batch: str) -> float:
            records = [self._single(batch, "G1_strong", "F_neutral", 1, tag=f"rep{i}") for i in (1, 2, 3)]
            return collective_process_metrics([record.coded for record in records])["pairwise_jaccard"]

        jaccard = attempt("v2_batch_2")
        passed = jaccard < 0.80
        write_gate_report(V2_GATES, "v2 Gate 2 initial", passed, [f"pairwise_jaccard: {jaccard:.6f}", f"temperature: {self.temperature}"])
        if not passed:
            self.temperature = 1.3
            self.save_state(temperature=1.3, gate2_escalated=True)
            jaccard = attempt("v2_batch_2_retry")
            passed = jaccard < 0.80
            write_gate_report(V2_GATES, "v2 Gate 2 retry", passed, [f"pairwise_jaccard: {jaccard:.6f}", "temperature: 1.3"])
        if not passed:
            self.save_state(leg_a_enabled=False, gate2_failed=True)
        self.mark_batch("v2_batch_2")
        return passed

    def batch3(self) -> None:
        rates: dict[float, float] = {}
        rows: list[dict[str, Any]] = []
        for theta in (0.2, 0.4, 0.8, 1.6, 3.2):
            name = f"v2_calibration_theta_{str(theta).replace('.', 'p')}"
            csv_path = V2_CALIBRATION / f"{name}.csv"
            if not csv_path.exists():
                frame, truth = generate_core(theta, CALIBRATION_SEEDS[theta])
                write_dataset(name, frame, truth, V2_CALIBRATION)
            runs = [self._single("v2_batch_3", name, "F_neutral", seed) for seed in (1, 2, 3, 4, 5)]
            success = sum(run.complete and run.coded.get("interaction_code") == "reported_supported" for run in runs)
            rates[theta] = success / 5
            rows.append({"theta": theta, "successes": success, "n": 5, "success_rate": rates[theta]})
        table = RESULTS / "v2" / "tables" / "calibration.csv"
        table.parent.mkdir(parents=True, exist_ok=True)
        with table.open("w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
            writer.writeheader()
            writer.writerows(rows)
        theta_star = min(rates, key=lambda theta: (abs(rates[theta] - 0.5), theta))
        qualifying = [theta for theta, rate in rates.items() if rate >= 0.8]
        theta_strong = min(qualifying) if qualifying else 3.2
        gate = any(0.25 <= rate <= 0.75 for rate in rates.values())
        details = [f"theta={theta}: rate={rate:.3f}" for theta, rate in rates.items()]
        details.extend(
            [
                f"theta_star: {theta_star}",
                f"theta_strong: {theta_strong}",
                f"theta_strong_equals_theta_star: {str(theta_strong == theta_star).lower()}",
                f"calibration_deviation: {str(not gate).lower()}",
            ]
        )
        write_gate_report(V2_GATES, "v2 Gate 3", gate, details)

        frame, truth = generate_g2_calibrated(theta_star)
        write_dataset("G2_calibrated", frame, truth, DATA)
        regenerated = theta_strong != 0.8
        if regenerated:
            archive = DATA / "archive"
            archive.mkdir(parents=True, exist_ok=True)
            original_csv = archive / "G1_strong_theta_0p8_seed1001.csv"
            original_truth = archive / "G1_strong_theta_0p8_seed1001_ground_truth.json"
            if not original_csv.exists():
                shutil.copy2(DATA / "G1_strong.csv", original_csv)
                shutil.copy2(DATA / "G1_strong_ground_truth.json", original_truth)
            frame, truth = generate_core(theta_strong, 1001)
            write_dataset("G1_strong", frame, truth, DATA)
            self.cache_dir = CACHE / "v2_postcal"
        self.save_state(
            theta_star=theta_star,
            theta_strong=theta_strong,
            theta_strong_equals_theta_star=theta_strong == theta_star,
            calibration_rates={str(key): value for key, value in rates.items()},
            calibration_deviation=not gate,
            g1_regenerated=regenerated,
            calibration_complete=True,
        )
        self.mark_batch("v2_batch_3")

    def batch4(self) -> None:
        if not self.state.get("leg_a_enabled", True):
            self.mark_batch("v2_batch_4_skipped")
            return
        datasets = ("G1_strong",) if self.state.get("theta_strong_equals_theta_star") else ("G1_strong", "G2_calibrated")
        for dataset in datasets:
            for seed in (1, 2, 3):
                self._single("v2_batch_4", dataset, "F_neutral", seed, tag="canonical")
                self.run_episode(batch="v2_batch_4", episode_id=f"{dataset}_isolated_seed{seed}", dataset_name=dataset, framing_name="F_neutral", mode="isolated", seed=seed)
                self.run_episode(batch="v2_batch_4", episode_id=f"{dataset}_shared_seed{seed}", dataset_name=dataset, framing_name="F_neutral", mode="shared", seed=seed)
        self.mark_batch("v2_batch_4")

    def batch5(self) -> None:
        for seed in (1, 2, 3):
            self._single("v2_batch_5", "G4_underpowered", "F_neutral", seed)
            self.run_episode(batch="v2_batch_5", episode_id=f"G4_underpowered_shared_seed{seed}", dataset_name="G4_underpowered", framing_name="F_neutral", mode="shared", seed=seed)
            self._single("v2_batch_5", "G0_null", "F_neutral", seed)
            self.run_episode(batch="v2_batch_5", episode_id=f"G0_null_isolated_seed{seed}", dataset_name="G0_null", framing_name="F_neutral", mode="isolated", seed=seed)
            self.run_episode(batch="v2_batch_5", episode_id=f"G0_null_shared_seed{seed}", dataset_name="G0_null", framing_name="F_neutral", mode="shared", seed=seed)
        self.mark_batch("v2_batch_5")

    def batch6(self) -> None:
        cells = [
            ("B1", "G3_confound", "F_neutral"),
            ("B2", "G3_confound", "F_econ"),
            ("B4a", "B4_shuffled", "F_pendulum"),
            ("B4b", "B4_shuffled", "F_sensor"),
            ("B3", "G3_confound", "F_phys"),
        ]
        for cell, dataset, framing in cells:
            for seed in (1, 2, 3):
                self._single("v2_batch_6", dataset, framing, seed, tag=cell)
        self.mark_batch("v2_batch_6")

    def run(self) -> None:
        try:
            if "v2_batch_1" not in self.state["completed_batches"]:
                if not self.batch1():
                    self.save_state(stopped_at="v2_batch_1", stop_reason="pre-registered 0/10 branch")
                    return
            if "v2_batch_2" not in self.state["completed_batches"]:
                self.batch2()
            if "v2_batch_3" not in self.state["completed_batches"]:
                self.batch3()
            if "v2_batch_4" not in self.state["completed_batches"] and "v2_batch_4_skipped" not in self.state["completed_batches"]:
                self.batch4()
            if "v2_batch_5" not in self.state["completed_batches"]:
                self.batch5()
            if "v2_batch_6" not in self.state["completed_batches"]:
                self.batch6()
            self.save_state(live_complete=True)
        except (BudgetAbort, HaltBatch) as exc:
            write_gate_report(V2_GATES, "v2 mandatory stop", False, [str(exc)])
            self.save_state(stop_reason=str(exc))
        except Exception as exc:
            message = f"{type(exc).__name__}: {exc}"
            write_gate_report(V2_GATES, "v2 external/runtime stop", False, [message])
            self.save_state(stop_reason=message)
            raise


def main() -> None:
    V2Experiment().run()


if __name__ == "__main__":
    main()
