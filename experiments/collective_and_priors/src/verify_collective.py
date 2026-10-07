"""Read-only tool, shared-log, and coding replay for Addendum 07."""

from __future__ import annotations

import hashlib
import json
import tempfile
import csv
from decimal import Decimal
from pathlib import Path
from typing import Any

import pandas as pd

from .coding import add_new_pairs_added, code_run
from .execute_collective import DISCARDED_RUN_ID, RESTART_RUN_ID, TARGET, collect_episodes, false_positive, test_pairs
from .execute_experiment import DATA, LEDGER_PATH, ROOT, RUNS
from .tools import ToolService


def verify() -> dict[str, Any]:
    frame_path = DATA / "G1_strong.csv"
    frame = pd.read_csv(frame_path)
    data_hash = hashlib.sha256(frame_path.read_bytes()).hexdigest()
    runs = actions_checked = 0
    failures: list[str] = []
    discarded = json.loads((ROOT / "results" / "collective" / "discarded_attempt.json").read_text(encoding="utf-8"))
    with LEDGER_PATH.open("r", encoding="utf-8", newline="") as handle:
        rows_ledger = list(csv.DictReader(handle))
    discarded_rows = [row for row in rows_ledger if row["run_id"] == DISCARDED_RUN_ID]
    if len(discarded_rows) != 6 or discarded["response_count"] != 6:
        failures.append("discarded attempt response count")
    if sum((Decimal(row["enforcement_usd"]) for row in discarded_rows), Decimal("0")) != Decimal(discarded["enforcement_usd"]):
        failures.append("discarded attempt ledger cost")
    if discarded["scored"] or discarded["shown_to_other_agents"]:
        failures.append("discarded attempt disposition")
    if (RUNS / "anthropic_m3" / "G1_strong_shared_episode6" / "A" / "meta.json").exists():
        replacement_meta = json.loads((RUNS / "anthropic_m3" / "G1_strong_shared_episode6" / "A" / "meta.json").read_text(encoding="utf-8"))
        if replacement_meta.get("ledger_run_id") != RESTART_RUN_ID:
            failures.append("replacement run ledger identity")
    with tempfile.TemporaryDirectory(prefix="live-salmon-collective-replay-") as temp:
        service = ToolService(frame, "G1_strong", Path(temp), target="Y")
        for episode_number, rows in enumerate(collect_episodes(), 1):
            prior: list[dict[str, Any]] = []
            expected_codings = []
            for row in rows:
                directory = row["directory"]
                if row["shared"] != prior:
                    failures.append(f"episode {episode_number} position {row['meta']['position']}: shared snapshot")
                if row["meta"]["data_sha256"] != data_hash:
                    failures.append(f"{directory}: data hash")
                for entry in row["actions"]:
                    if service.execute(entry["action"]) != entry["result"]:
                        failures.append(f"{directory}: tool step {entry['step']}")
                    actions_checked += 1
                if row["meta"]["status"] == "complete":
                    expected = code_run(row["actions"], row["conclusion"], row_count=len(frame), shared_entries=prior)
                    own_pairs, shared_pairs = test_pairs(row["actions"]), test_pairs(prior)
                    expected.update({
                        "position": row["meta"]["position"],
                        "own_test_X4X5": TARGET in own_pairs,
                        "seen_X4X5_only": TARGET not in own_pairs and TARGET in shared_pairs,
                        "claim_without_test": bool(row["conclusion"].get("interaction_claims") and not (own_pairs | shared_pairs)),
                        "top3_false_positive": false_positive(row["conclusion"]),
                    })
                else:
                    expected = {
                        "status": row["meta"]["status"],
                        "protocol_error": row["coded"].get("protocol_error"),
                        "position": row["meta"]["position"],
                        "own_test_X4X5": TARGET in test_pairs(row["actions"]),
                        "seen_X4X5_only": TARGET not in test_pairs(row["actions"]) and TARGET in test_pairs(prior),
                        "claim_without_test": False,
                        "top3_false_positive": False,
                    }
                expected_codings.append(expected)
                prior.extend(row["actions"])
                runs += 1
            if len(rows) == 3 and all(row["meta"]["status"] == "complete" for row in rows):
                add_new_pairs_added(expected_codings, shared_log=True)
            for row, expected in zip(rows, expected_codings):
                if row["coded"] != expected:
                    failures.append(f"{row['directory']}: coding")
    result = {"runs_replayed": runs, "tool_actions_replayed": actions_checked, "discarded_responses_excluded": len(discarded_rows), "mismatches": len(failures), "failures": failures}
    output = ROOT / "results" / "collective" / "replay_verification.json"
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    if failures:
        raise AssertionError("collective replay mismatch: " + ", ".join(failures[:10]))
    return result


def main() -> None:
    print(json.dumps(verify(), sort_keys=True))


if __name__ == "__main__":
    main()
