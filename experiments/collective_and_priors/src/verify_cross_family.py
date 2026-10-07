"""Deterministically replay Addendum 06 tools and coding from saved logs."""

from __future__ import annotations

import hashlib
import json
import tempfile
from pathlib import Path
from typing import Any

import pandas as pd

from .coding import code_run
from .execute_experiment import DATA, ROOT, RUNS
from .tools import ToolService


BATCHES = ("anthropic_smoke", "anthropic_s_v1", "anthropic_s_v2", "anthropic_s_v3")


def verify() -> dict[str, Any]:
    tool_actions = 0
    coding_runs = 0
    runs = 0
    failures: list[str] = []
    with tempfile.TemporaryDirectory(prefix="live-salmon-cross-family-replay-") as temporary:
        cache_root = Path(temporary)
        for batch in BATCHES:
            for meta_path in sorted((RUNS / batch).glob("*/*/meta.json")):
                directory = meta_path.parent
                relative = directory.relative_to(ROOT).as_posix()
                meta = json.loads(meta_path.read_text(encoding="utf-8"))
                actions = [
                    json.loads(line)
                    for line in (directory / "actions.jsonl").read_text(encoding="utf-8").splitlines()
                    if line
                ]
                coded = json.loads((directory / "coded.json").read_text(encoding="utf-8"))
                conclusion = json.loads((directory / "conclusion.json").read_text(encoding="utf-8"))
                frame_path = DATA / f"{meta['dataset']}.csv"
                frame = pd.read_csv(frame_path)
                service = ToolService(frame, meta["dataset"], cache_root / batch, target="Y")
                runs += 1
                if meta.get("status") != "complete":
                    failures.append(f"{relative}:status={meta.get('status')}")
                data_hash = hashlib.sha256(frame_path.read_bytes()).hexdigest()
                if meta.get("data_sha256") != data_hash:
                    failures.append(f"{relative}:data_sha256")
                for entry in actions:
                    actual = service.execute(entry["action"])
                    tool_actions += 1
                    if actual != entry["result"]:
                        failures.append(f"{relative}:tool_step_{entry['step']}")
                target = ("X1", "X3") if meta["dataset"] == "G1_swap" else ("X4", "X5")
                replayed = code_run(actions, conclusion, row_count=len(frame), target_interaction=target)
                coding_runs += 1
                if replayed != coded:
                    failures.append(f"{relative}:coding")
    result = {
        "runs_replayed": runs,
        "tool_actions_replayed": tool_actions,
        "coding_runs_replayed": coding_runs,
        "mismatches": len(failures),
        "failures": failures,
    }
    output = ROOT / "results" / "cross_family" / "replay_verification.json"
    output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    if failures:
        raise AssertionError("cross-family replay mismatch: " + ", ".join(failures[:10]))
    return result


def main() -> None:
    print(json.dumps(verify(), sort_keys=True))


if __name__ == "__main__":
    main()
