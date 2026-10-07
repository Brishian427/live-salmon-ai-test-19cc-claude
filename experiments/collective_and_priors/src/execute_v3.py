"""Resumable one-cell driver for Addendum 05."""

from __future__ import annotations

import json
from typing import Any

from .execute_experiment import CACHE, DATA, RESULTS, ROOT, BudgetAbort, Experiment, HaltBatch, write_gate_report
from .v3_reporting import write_v3_report


V3_STATE = RESULTS / "v3" / "execution_state.json"
V3_GATES = RESULTS / "v3" / "gates.md"


class V3Experiment(Experiment):
    def __init__(self) -> None:
        super().__init__()
        self.state = json.loads(V3_STATE.read_text(encoding="utf-8")) if V3_STATE.exists() else {}
        self.state.setdefault("completed_batches", [])
        self.state.setdefault("temperature", float(self.temperature))
        self.temperature = float(self.state["temperature"])
        self.cache_dir = CACHE / "v3"
        if not (DATA / "G1_swap.csv").exists() or not (DATA / "G1_swap_ground_truth.json").exists():
            raise RuntimeError("G1_swap canonical data is missing; generate and freeze it before v3 execution")

    def save_state(self, **updates: Any) -> None:
        self.state.update(updates)
        V3_STATE.parent.mkdir(parents=True, exist_ok=True)
        V3_STATE.write_text(json.dumps(self.state, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    def batch1(self) -> None:
        runs = [self._single("v3_batch_1", "G1_swap", "F_neutral", seed) for seed in range(1, 11)]
        complete = [run for run in runs if run.complete]
        if len(complete) != 10:
            raise HaltBatch(f"v3 protocol-complete runs: {len(complete)}/10")
        result = write_v3_report(ROOT)
        successes = int(result["summary"]["reported_supported"])
        outcome = str(result["pre_registered_outcome"])
        write_gate_report(
            V3_GATES,
            "v3 one-cell completion",
            True,
            [
                "protocol-complete runs: 10/10",
                f"X1:X3 reported_supported: {successes}/10",
                f"pre-registered heredity outcome: {outcome}",
                "mandatory unconditional stop after this cell",
            ],
        )
        self.mark_batch("v3_batch_1")
        self.save_state(
            target_reported_supported=successes,
            pre_registered_outcome=outcome,
            stopped_at="v3_batch_1",
            stop_reason="Addendum 05 unconditional one-cell stop",
            live_complete=True,
        )

    def run(self) -> None:
        if "v3_batch_1" in self.state["completed_batches"]:
            return
        try:
            self.batch1()
        except (BudgetAbort, HaltBatch) as exc:
            write_gate_report(V3_GATES, "v3 mandatory stop", False, [str(exc)])
            self.save_state(stop_reason=str(exc))
        except Exception as exc:
            message = f"{type(exc).__name__}: {exc}"
            write_gate_report(V3_GATES, "v3 external/runtime stop", False, [message])
            self.save_state(stop_reason=message)
            raise


def main() -> None:
    V3Experiment().run()


if __name__ == "__main__":
    main()
