"""Addendum 07: sequential Anthropic shared-log episodes, resumable on disk."""

from __future__ import annotations

import hashlib
import itertools
import json
import os
import csv
from decimal import Decimal
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import anthropic
import pandas as pd
from dotenv import load_dotenv
from scipy.stats import fisher_exact

from .agent import run_agent
from .coding import add_new_pairs_added, code_run, process_metrics
from .collective import agent_order
from .execute_cross_family import EXPECTED_DATA_HASHES, EXPECTED_SYSTEM_HASHES
from .execute_experiment import CACHE, DATA, LEDGER_PATH, RESULTS, ROOT, RUNS, _load_saved
from .framings import FRAMINGS
from .ledger import BudgetAbort, CostLedger, Pricing
from .prompts import build_system_message
from .providers.anthropic import AnthropicModelClient
from .run_batch import RunWriter
from .tools import ToolService
from .transient_retry import RetryExhausted, append_ledger_note, call_with_transient_retries
from .v2_reporting import _load_arm

BATCH = "anthropic_m3"
OUT = RESULTS / "collective"
STATE = OUT / "execution_state.json"
NOTES = LEDGER_PATH.with_suffix(".notes.jsonl")
DISCARDED_RUN_ID = "anthropic_m3/G1_strong_shared_episode6/A"
RESTART_RUN_ID = "anthropic_m3/G1_strong_shared_episode6/A_restart1"
TARGET = ("X4", "X5")
TOP3 = {("X1", "X2"), ("X1", "X3"), ("X2", "X3")}
LABEL = "computed from 10 independent single-agent runs by exhaustive triples; assumes exchangeability."


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def read_entries(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line]


def pair(entry: dict[str, Any]) -> tuple[str, str] | None:
    call = entry.get("action", {})
    if call.get("tool") != "test_interaction":
        return None
    a, b = call.get("a"), call.get("b")
    return tuple(sorted((a, b))) if isinstance(a, str) and isinstance(b, str) else None


def test_pairs(entries: list[dict[str, Any]]) -> set[tuple[str, str]]:
    return {value for entry in entries if (value := pair(entry)) is not None}


def false_positive(conclusion: dict[str, Any] | None) -> bool:
    return any(
        tuple(sorted(claim.get("terms", []))) in TOP3 and claim.get("status") == "supported"
        for claim in (conclusion or {}).get("interaction_claims", []) or []
        if isinstance(claim, dict)
    )


def offline_baselines() -> dict[str, Any]:
    singles = _load_arm(RUNS, "anthropic_s_v2")
    if len(singles) != 10 or any(row["meta"].get("status") != "complete" for row in singles):
        raise RuntimeError("S-v2 baseline must contain exactly ten complete runs")
    triples = list(itertools.combinations(singles, 3))
    successes = [sum(row["coded"].get("interaction_code") == "reported_supported" for row in triple) for triple in triples]
    result = {
        "label": LABEL,
        "single_supported": sum(row["coded"].get("interaction_code") == "reported_supported" for row in singles),
        "single_false_positive": sum(false_positive(row["conclusion"]) for row in singles),
        "M1": sum(count >= 1 for count in successes),
        "M2": sum(count >= 2 for count in successes),
        "n_triples": len(triples),
    }
    assert result["n_triples"] == 120 and result["single_supported"] == 5
    return result


class CollectiveExperiment:
    def __init__(self) -> None:
        load_dotenv(ROOT / ".env")
        key = os.getenv("ANTHROPIC_API_KEY")
        if not key:
            raise RuntimeError("ANTHROPIC_API_KEY is missing")
        self.client = anthropic.Anthropic(api_key=key, timeout=120.0, max_retries=0)
        self.frame = pd.read_csv(DATA / "G1_strong.csv")
        self.system = build_system_message(FRAMINGS["F_neutral"], len(self.frame), "Y", list(self.frame.columns))
        self.data_hash = hashlib.sha256((DATA / "G1_strong.csv").read_bytes()).hexdigest()
        self.system_hash = hashlib.sha256(self.system.encode("utf-8")).hexdigest()
        reference = json.loads(next((RUNS / "anthropic_s_v2").glob("*/*/meta.json")).read_text(encoding="utf-8"))
        if self.data_hash != reference["data_sha256"] or self.data_hash != EXPECTED_DATA_HASHES["G1_strong"]:
            raise RuntimeError("G1_strong hash does not match S-v2")
        if self.system_hash != reference["system_message_sha256"] or self.system_hash != EXPECTED_SYSTEM_HASHES["v2"]:
            raise RuntimeError("system-message hash does not match S-v2")
        self.ledger = CostLedger(LEDGER_PATH, Pricing(float(os.environ["PRICE_SONNET_5_5_INPUT_PER_M"]), 0.0, float(os.environ["PRICE_SONNET_5_5_OUTPUT_PER_M"])))
        self.writer = RunWriter(RUNS)
        OUT.mkdir(parents=True, exist_ok=True)
        write_json(OUT / "hash_assertions.json", {"data_sha256": self.data_hash, "system_message_sha256": self.system_hash, "match_S_v2": True})
        write_json(OUT / "offline_baselines.json", offline_baselines())

    def assert_resume_snapshot(self) -> None:
        for episode in range(1, 6):
            for agent_id in agent_order(episode):
                saved = _load_saved(RUNS / BATCH / f"G1_strong_shared_episode{episode}" / agent_id)
                if saved is None or not saved.complete:
                    raise RuntimeError(f"missing completed pre-interruption agent: episode {episode}, {agent_id}")
        episode6 = RUNS / BATCH / "G1_strong_shared_episode6"
        first = _load_saved(episode6 / agent_order(6)[0])
        if first is None or not first.complete:
            raise RuntimeError("episode 6 position 1 is not a completed saved run")
        for agent_id in agent_order(6)[1:]:
            saved = _load_saved(episode6 / agent_id)
            if saved is not None and (not saved.complete or saved.meta.get("ledger_run_id") != (RESTART_RUN_ID if agent_id == agent_order(6)[1] else f"{BATCH}/G1_strong_shared_episode6/{agent_id}")):
                raise RuntimeError("episode 6 has a saved run outside the fixed resumption rule")
        discarded = [row for row in self.ledger.rows() if row["run_id"] == DISCARDED_RUN_ID]
        if len(discarded) != 6:
            raise RuntimeError("discarded episode 6 position-2 attempt must have exactly six billed responses")
        cost = sum((Decimal(row["enforcement_usd"]) for row in discarded), Decimal("0"))
        record = {
            "run_id": DISCARDED_RUN_ID,
            "response_count": len(discarded),
            "enforcement_usd": str(cost),
            "disposition": "discarded: incomplete due to API connection error; exogenous to outcome.",
            "scored": False,
            "shown_to_other_agents": False,
            "replacement_run_id": RESTART_RUN_ID,
        }
        path = OUT / "discarded_attempt.json"
        if path.exists() and json.loads(path.read_text(encoding="utf-8")) != record:
            raise RuntimeError("discarded-attempt record changed")
        if not path.exists():
            write_json(path, record)
            append_ledger_note(NOTES, {
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "request_id": DISCARDED_RUN_ID,
                "event": "discarded_incomplete_attempt",
                "response_count": len(discarded),
                "enforcement_usd": str(cost),
            })

    def probe(self) -> None:
        call_with_transient_retries(
            lambda: self.client.models.list(limit=1),
            notes_path=NOTES,
            request_id="anthropic_m3/pre_resume_probe",
        )
        write_json(OUT / "probe.json", {"model": "claude-sonnet-5-5", "reachable": True})

    def run_cost(self, run_id: str) -> dict[str, Any]:
        rows = [row for row in self.ledger.rows() if row["run_id"] == run_id]
        return {
            "api_calls": len(rows),
            "prompt_cache_hit_tokens": sum(int(row["prompt_cache_hit_tokens"]) for row in rows),
            "prompt_cache_miss_tokens": sum(int(row["prompt_cache_miss_tokens"]) for row in rows),
            "completion_tokens": sum(int(row["completion_tokens"]) for row in rows),
            "estimated_usd": sum(float(row["estimated_usd"]) for row in rows),
            "enforcement_usd": sum(float(row["enforcement_usd"]) for row in rows),
        }

    def run_one(self, episode: int, agent_id: str, position: int, order: list[str], prior: list[dict[str, Any]]) -> Any:
        episode_id = f"G1_strong_shared_episode{episode}"
        directory = RUNS / BATCH / episode_id / agent_id
        saved = _load_saved(directory)
        if saved is not None:
            existing_prior = read_entries(directory / "shared_entries.jsonl")
            if existing_prior != prior:
                raise RuntimeError(f"saved shared log differs in {directory}")
            return saved
        run_id = RESTART_RUN_ID if episode == 6 and position == 2 else f"{BATCH}/{episode_id}/{agent_id}"
        model = AnthropicModelClient(
            self.client, model="claude-sonnet-5-5", ledger=self.ledger, batch=BATCH,
            run_id=run_id, batch_cap_usd=3.50,
            thinking={"type": "between_tools"}, effort_default="high",
            retry_notes_path=NOTES,
        )
        run = run_agent(
            model, ToolService(self.frame, "G1_strong", CACHE / BATCH, target="Y"),
            framing=FRAMINGS["F_neutral"], n_rows=len(self.frame), columns=list(self.frame.columns),
            prior_entries=prior, system_message_override=self.system,
        )
        own_pairs, seen_pairs = test_pairs(run.actions), test_pairs(prior)
        coded = (
            code_run(run.actions, run.conclusion, row_count=len(self.frame), shared_entries=prior)
            if run.status == "complete" and run.conclusion is not None
            else {"status": run.status, "protocol_error": run.protocol_error}
        )
        coded.update({
            "position": position,
            "own_test_X4X5": TARGET in own_pairs,
            "seen_X4X5_only": TARGET not in own_pairs and TARGET in seen_pairs,
            "claim_without_test": bool(
                run.conclusion and run.conclusion.get("interaction_claims") and not (own_pairs | seen_pairs)
            ),
            "top3_false_positive": false_positive(run.conclusion),
        })
        meta = {
            "provider": "anthropic", "model": "claude-sonnet-5-5", "parameters": model.sent_parameters,
            "dataset": "G1_strong", "framing": "F_neutral", "prompt_variant": "v2",
            "mode": "shared", "seed": episode, "episode": episode,
            "agent_order": order, "agent_id": agent_id, "position": position,
            "temperature": 1.0, "status": run.status, "generator_seed": 1001,
            "data_sha256": self.data_hash, "system_message_sha256": self.system_hash,
            "ledger_run_id": run_id,
        }
        self.writer.write(batch=BATCH, episode_id=episode_id, agent_id=agent_id, meta=meta, run=run, coded=coded, cost=self.run_cost(run_id))
        with (directory / "shared_entries.jsonl").open("w", encoding="utf-8") as handle:
            for entry in prior:
                handle.write(json.dumps({k: v for k, v in entry.items() if k != "raw"}, sort_keys=True) + "\n")
        saved = _load_saved(directory)
        assert saved is not None
        if run.status == "budget_abort":
            raise BudgetAbort(run.protocol_error or "budget abort")
        return saved

    def run(self) -> dict[str, Any]:
        for episode in range(1, 11):
            order = agent_order(episode)
            prior: list[dict[str, Any]] = []
            records = []
            for position, agent_id in enumerate(order, 1):
                saved = self.run_one(episode, agent_id, position, order, prior)
                records.append(saved)
                prior.extend(saved.actions)
                write_json(STATE, {"last_episode": episode, "last_position": position, "batch_spend_usd": self.ledger.batch_enforcement_usd(BATCH), "global_spend_usd": self.ledger.cumulative_enforcement_usd})
            if all(record.complete for record in records):
                codings = add_new_pairs_added([record.coded for record in records], shared_log=True)
                for record, coded in zip(records, codings):
                    write_json(record.directory / "coded.json", coded)
            print(f"episode {episode}/10 complete: {[record.meta['status'] for record in records]}", flush=True)
        return generate_report()


def collect_episodes() -> list[list[dict[str, Any]]]:
    episodes = []
    for episode in range(1, 11):
        rows = []
        for meta_path in (RUNS / BATCH / f"G1_strong_shared_episode{episode}").glob("*/meta.json"):
            directory = meta_path.parent
            saved = _load_saved(directory)
            assert saved is not None
            rows.append({
                "meta": saved.meta, "actions": saved.actions, "coded": saved.coded,
                "conclusion": saved.conclusion,
                "shared": read_entries(directory / "shared_entries.jsonl"),
                "directory": directory,
            })
        episodes.append(sorted(rows, key=lambda row: row["meta"]["position"]))
    return episodes


def generate_report() -> dict[str, Any]:
    baseline = offline_baselines()
    episodes = collect_episodes()
    complete = sum(len(rows) == 3 and all(row["meta"]["status"] == "complete" for row in rows) for rows in episodes)
    if complete < 8:
        result = {"gate_1a": "FAIL", "complete_episodes": complete}
        write_json(OUT / "analysis.json", result)
        return result
    majority = sum(sum(row["coded"].get("interaction_code") == "reported_supported" for row in rows) >= 2 for rows in episodes)
    union = sum(any(row["coded"].get("interaction_code") == "reported_supported" for row in rows) for rows in episodes)
    duplication_hits = duplication_n = 0
    conditional_hits = conditional_n = 0
    new_pairs: dict[int, list[int]] = {1: [], 2: [], 3: []}
    false_pos: dict[int, int] = {1: 0, 2: 0, 3: 0}
    position1_supported = 0
    per_run = []
    for episode_id, rows in enumerate(episodes, 1):
        assert len(rows) == 3
        first_own_target = TARGET in test_pairs(rows[0]["actions"])
        position1_supported += rows[0]["coded"].get("interaction_code") == "reported_supported"
        prior_touched: set[tuple[str, str]] = set()
        for row in rows:
            position = row["meta"]["position"]
            own, shared = test_pairs(row["actions"]), test_pairs(row["shared"])
            own_touched = {tuple(pair) for pair in process_metrics(row["actions"])["pairs_touched"]}
            marginal_pairs = len(own_touched - prior_touched)
            prior_touched |= own_touched
            if row["coded"].get("new_pairs_added") is not None and row["coded"]["new_pairs_added"] != marginal_pairs:
                raise RuntimeError(f"new_pairs_added coding mismatch in episode {episode_id} position {position}")
            new_pairs[position].append(marginal_pairs)
            false_pos[position] += false_positive(row["conclusion"])
            if position > 1:
                opportunities = TOP3 & shared
                duplication_n += len(opportunities)
                duplication_hits += len(opportunities & own)
                if not first_own_target:
                    conditional_n += 1
                    conditional_hits += TARGET in own
            per_run.append({
                "episode": episode_id, "agent": row["meta"]["agent_id"], "position": position,
                "status": row["meta"]["status"], "interaction_code": row["coded"].get("interaction_code"),
                "own_test_X4X5": TARGET in own, "seen_X4X5_only": TARGET not in own and TARGET in shared,
                "claim_without_test": row["coded"].get("claim_without_test", False),
                "new_pairs_added": marginal_pairs,
                "top3_false_positive": false_positive(row["conclusion"]),
            })
    duplication_rate = duplication_hits / duplication_n if duplication_n else None
    verdict = "DIVISION" if duplication_rate is not None and duplication_rate <= .20 else "IMITATION" if duplication_rate is not None and duplication_rate >= .80 else "MIXED"
    fisher_majority = fisher_exact([[majority, 10-majority], [baseline["M2"], 120-baseline["M2"]]], alternative="two-sided").pvalue
    fisher_union = fisher_exact([[union, 10-union], [baseline["M1"], 120-baseline["M1"]]], alternative="two-sided").pvalue
    result = {
        "gate_1a": "PASS", "complete_episodes": complete,
        "baseline": baseline, "M3_majority": majority, "M3_union": union,
        "fisher_majority_vs_M2": float(fisher_majority), "fisher_union_vs_M1": float(fisher_union),
        "duplication_hits": duplication_hits, "duplication_opportunities": duplication_n,
        "duplication_rate": duplication_rate, "duplication_verdict": verdict,
        "conditional_hits": conditional_hits, "conditional_agents": conditional_n,
        "conditional_episodes": sum(TARGET not in test_pairs(rows[0]["actions"]) for rows in episodes),
        "new_pairs_by_position": {str(k): {"mean": sum(v)/len(v), "distribution": sorted(v)} for k, v in new_pairs.items()},
        "false_positive_by_position": {str(k): v for k, v in false_pos.items()},
        "position1_supported": position1_supported, "per_run": per_run,
        "E7_S_v2_jaccard": 0.777778,
    }
    with LEDGER_PATH.open("r", encoding="utf-8", newline="") as handle:
        ledger_rows = list(csv.DictReader(handle))
    result["cost"] = {
        "arm_enforcement_usd": str(sum((Decimal(row["enforcement_usd"]) for row in ledger_rows if row["batch"] == BATCH), Decimal("0"))),
        "global_enforcement_usd": ledger_rows[-1]["cumulative_enforcement_usd"],
        "arm_response_count": sum(row["batch"] == BATCH for row in ledger_rows),
    }
    result["discarded_attempt"] = json.loads((OUT / "discarded_attempt.json").read_text(encoding="utf-8"))
    write_json(OUT / "analysis.json", result)
    from .collective_reporting import write_reports
    write_reports(result)
    return result


def main() -> None:
    experiment = CollectiveExperiment()
    try:
        experiment.assert_resume_snapshot()
        experiment.probe()
        print(json.dumps(experiment.run(), sort_keys=True), flush=True)
    except BudgetAbort as exc:
        write_json(STATE, {"stop_reason": "budget fuse", "detail": str(exc)})
        print(f"STOP: budget fuse: {exc}", flush=True)
    except (RetryExhausted, anthropic.APIConnectionError, anthropic.APIStatusError) as exc:
        write_json(STATE, {"stop_reason": "API unavailable", "error_type": type(exc).__name__})
        print(f"STOP: API unavailable: {type(exc).__name__}", flush=True)


if __name__ == "__main__":
    main()
