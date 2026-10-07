"""Deterministic Batch 7 analysis and offline replay verification."""

from __future__ import annotations

import hashlib
import json
import math
import os
import shutil
import tempfile
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Iterable

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd
from scipy.stats import norm

from .coding import code_run
from .collective import aggregate_m1, aggregate_majority, collective_process_metrics


def _load_runs(root: Path) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for meta_path in sorted((root / "runs").glob("*/*/*/meta.json")):
        directory = meta_path.parent
        meta = json.loads(meta_path.read_text(encoding="utf-8"))
        actions_path = directory / "actions.jsonl"
        actions = [json.loads(line) for line in actions_path.read_text(encoding="utf-8").splitlines() if line]
        coded = json.loads((directory / "coded.json").read_text(encoding="utf-8"))
        raw = (directory / "conclusion.json").read_text(encoding="utf-8").strip()
        try:
            conclusion = json.loads(raw) if raw else None
        except json.JSONDecodeError:
            conclusion = None
        records.append(
            {
                "batch": directory.parents[1].name,
                "episode": directory.parent.name,
                "agent": directory.name,
                "directory": directory,
                "meta": meta,
                "actions": actions,
                "coded": coded,
                "conclusion": conclusion,
            }
        )
    return records


def _episodes(records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    groups: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    for record in records:
        groups[(record["batch"], record["episode"])].append(record)
    episodes: list[dict[str, Any]] = []
    for (batch, episode), runs in sorted(groups.items()):
        runs.sort(key=lambda item: item["meta"].get("position", 1))
        meta = runs[0]["meta"]
        complete = [run for run in runs if run["meta"].get("status") == "complete"]
        if meta["mode"] == "single":
            success = bool(complete and complete[0]["coded"].get("interaction_code") == "reported_supported")
            episodes.append({"batch": batch, "episode": episode, "dataset": meta["dataset"], "framing": meta["framing"], "mode": "single", "seed": meta["seed"], "success": success, "runs": runs})
        elif len(complete) == 3:
            coded = [run["coded"] for run in runs]
            if meta["mode"] == "isolated":
                episodes.append({"batch": batch, "episode": episode, "dataset": meta["dataset"], "framing": meta["framing"], "mode": "M1", "seed": meta["seed"], "success": aggregate_m1(coded), "runs": runs})
                episodes.append({"batch": batch, "episode": episode, "dataset": meta["dataset"], "framing": meta["framing"], "mode": "M2", "seed": meta["seed"], "success": aggregate_majority(coded), "runs": runs})
            else:
                episodes.append({"batch": batch, "episode": episode, "dataset": meta["dataset"], "framing": meta["framing"], "mode": "M3", "seed": meta["seed"], "success": aggregate_majority(coded), "runs": runs})
    return episodes


def _rate(rows: list[dict[str, Any]]) -> tuple[int, int, float]:
    n = len(rows)
    hits = sum(bool(row["success"]) for row in rows)
    return hits, n, hits / n if n else math.nan


def _adjust_rate(count: int, n: int) -> float:
    if n == 0:
        return math.nan
    if count == 0:
        return 0.5 / n
    if count == n:
        return (n - 0.5) / n
    return count / n


def _signal_metrics(hit_count: int, hit_n: int, fa_count: int, fa_n: int) -> tuple[float, float]:
    hit = _adjust_rate(hit_count, hit_n)
    fa = _adjust_rate(fa_count, fa_n)
    z_hit, z_fa = norm.ppf(hit), norm.ppf(fa)
    return float(z_hit - z_fa), float(-0.5 * (z_hit + z_fa))


def _write_csv(frame: pd.DataFrame, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    frame.to_csv(path, index=False, lineterminator="\n")


def _markdown(frame: pd.DataFrame) -> str:
    if frame.empty:
        return "_No rows._"
    columns = list(frame.columns)
    lines = ["| " + " | ".join(columns) + " |", "| " + " | ".join(["---"] * len(columns)) + " |"]
    for _, row in frame.iterrows():
        values = []
        for column in columns:
            value = row[column]
            if isinstance(value, float):
                values.append("" if math.isnan(value) else f"{value:.6g}")
            else:
                values.append(str(value).replace("|", "\\|"))
        lines.append("| " + " | ".join(values) + " |")
    return "\n".join(lines)


def _verify_coding(records: list[dict[str, Any]]) -> dict[str, Any]:
    checked = 0
    failures: list[str] = []
    keys = {
        "interaction_code", "unsupported_by_log", "interaction_reason_raw",
        "rejection_reason_matches", "rejection_reason_primary", "n_fabricated",
        "fabricated_values", "n_actions", "n_invalid_actions", "coverage",
        "pairs_touched", "used_holdout", "actions_after_first_significant",
        "causal_claim_Z", "any_supported", "length_supported",
    }
    for record in records:
        if record["meta"].get("status") != "complete" or record["conclusion"] is None:
            continue
        expected = code_run(
            record["actions"],
            record["conclusion"],
            row_count=300 if record["meta"]["dataset"] == "B4_shuffled" else 1000,
            is_g3=record["meta"]["dataset"] == "G3_confound",
            target_interaction=("X1", "X3") if record["meta"]["dataset"] == "G1_swap" else ("X4", "X5"),
            shared_entries=(
                [json.loads(line) for line in (record["directory"] / "shared_entries.jsonl").read_text(encoding="utf-8").splitlines() if line]
                if (record["directory"] / "shared_entries.jsonl").exists() else None
            ),
        )
        checked += 1
        for key in keys & expected.keys():
            if record["coded"].get(key) != expected[key]:
                failures.append(f"{record['directory']}:{key}")
    if failures:
        raise AssertionError("offline coding replay mismatch: " + ", ".join(failures[:10]))
    return {"runs_replayed": checked, "coding_mismatches": 0}


def generate_analysis(root: Path, output: Path) -> dict[str, Any]:
    records = _load_runs(root)
    episodes = _episodes(records)
    tables = output / "tables"
    figures = output / "figures"
    tables.mkdir(parents=True, exist_ok=True)
    figures.mkdir(parents=True, exist_ok=True)

    # Calibration table is already a live-batch artifact; reproduce it from runs if available.
    cal_rows = []
    for theta in (0.8, 0.5, 0.3, 0.2, 0.1):
        dataset = f"calibration_theta_{str(theta).replace('.', 'p')}"
        subset = [ep for ep in episodes if ep["batch"] == "batch_3" and ep["dataset"] == dataset]
        hits, n, rate = _rate(subset)
        if n:
            cal_rows.append({"theta": theta, "successes": hits, "n": n, "success_rate": rate})
    calibration = pd.DataFrame(cal_rows)
    _write_csv(calibration, tables / "calibration.csv")

    leg_a_rows = []
    for dataset in ("G1_strong", "G2_calibrated"):
        for mode in ("single", "M1", "M2", "M3"):
            subset = [ep for ep in episodes if ep["batch"] == "batch_4" and ep["dataset"] == dataset and ep["mode"] == mode]
            hits, n, rate = _rate(subset)
            if n:
                leg_a_rows.append({"dataset": dataset, "mode": mode, "successes": hits, "n": n, "success_rate": rate})
    leg_a = pd.DataFrame(leg_a_rows)
    _write_csv(leg_a, tables / "leg_a_success.csv")

    process_rows = []
    for record in records:
        if record["batch"] == "batch_4" and record["meta"].get("mode") in {"isolated", "shared"} and record["meta"].get("status") == "complete":
            process_rows.append({"dataset": record["meta"]["dataset"], "condition": record["meta"]["mode"], "position": record["coded"].get("position"), "new_pairs_added": record["coded"].get("new_pairs_added")})
    process = pd.DataFrame(process_rows)
    position_summary = process.groupby(["dataset", "condition", "position"], as_index=False)["new_pairs_added"].mean() if not process.empty else process
    _write_csv(position_summary, tables / "leg_a_new_pairs_by_position.csv")
    coverage_rows = []
    grouped = defaultdict(list)
    for record in records:
        if record["batch"] == "batch_4" and record["meta"].get("mode") in {"isolated", "shared"} and record["meta"].get("status") == "complete":
            grouped[(record["episode"], record["meta"]["dataset"], record["meta"]["mode"])].append(record)
    for (episode, dataset, mode), runs in grouped.items():
        if len(runs) == 3:
            metrics = collective_process_metrics([run["coded"] for run in runs])
            coverage_rows.append({"episode": episode, "dataset": dataset, "condition": mode, **metrics})
    coverage = pd.DataFrame(coverage_rows)
    _write_csv(coverage, tables / "leg_a_process.csv")

    g4_rows = []
    for record in records:
        if record["batch"] == "batch_5" and record["meta"]["dataset"] == "G4_underpowered" and record["meta"].get("status") == "complete":
            g4_rows.append({"condition": "single" if record["meta"]["mode"] == "single" else "M3_agent", "interaction_code": record["coded"]["interaction_code"], "reason": record["coded"].get("rejection_reason_primary")})
    leg_c = pd.DataFrame(g4_rows)
    _write_csv(leg_c, tables / "leg_c_underpowered.csv")

    causal_rows = []
    b4_rows = []
    for record in records:
        if record["batch"] != "batch_6" or record["meta"].get("status") != "complete":
            continue
        if record["meta"]["dataset"] == "G3_confound":
            causal_rows.append({"framing": record["meta"]["framing"], "seed": record["meta"]["seed"], "causal_claim_Z": record["coded"].get("causal_claim_Z")})
        else:
            b4_rows.append({"framing": record["meta"]["framing"], "seed": record["meta"]["seed"], "any_supported": record["coded"].get("any_supported"), "length_supported": record["coded"].get("length_supported")})
    causal = pd.DataFrame(causal_rows)
    _write_csv(causal, tables / "leg_b_causal_claims.csv")
    b4 = pd.DataFrame(b4_rows)
    b4_summary_rows = []
    if not b4.empty:
        for metric in ("any_supported", "length_supported"):
            rates = b4.groupby("framing")[metric].mean().to_dict()
            b4_summary_rows.append({"metric": metric, "pendulum_rate": rates.get("F_pendulum", math.nan), "sensor_rate": rates.get("F_sensor", math.nan), "pendulum_minus_sensor": rates.get("F_pendulum", math.nan) - rates.get("F_sensor", math.nan)})
    b4_summary = pd.DataFrame(b4_summary_rows)
    _write_csv(b4, tables / "b4_run_outcomes.csv")
    _write_csv(b4_summary, tables / "b4_summary.csv")

    sd_rows = []
    for mode in ("single", "M1", "M2", "M3"):
        null = [ep for ep in episodes if ep["dataset"] == "G0_null" and ep["mode"] == mode]
        fa_count, fa_n, fa_rate = _rate(null)
        for signal in ("G1_strong", "G2_calibrated"):
            hits = [ep for ep in episodes if ep["batch"] == "batch_4" and ep["dataset"] == signal and ep["mode"] == mode]
            hit_count, hit_n, hit_rate = _rate(hits)
            if hit_n and fa_n:
                dprime, criterion = _signal_metrics(hit_count, hit_n, fa_count, fa_n)
                sd_rows.append({"metric": "d_prime", "mode": mode, "signal": signal, "reference": "G0_null", "hit_count": hit_count, "hit_n": hit_n, "hit_rate": hit_rate, "fa_count": fa_count, "fa_n": fa_n, "fa_rate": fa_rate, "value": dprime, "criterion": criterion})
    for mode in ("single", "M3"):
        null = [ep for ep in episodes if ep["dataset"] == "G4_underpowered" and ep["mode"] == mode]
        fa_count, fa_n, fa_rate = _rate(null)
        for signal in ("G1_strong", "G2_calibrated"):
            hits = [ep for ep in episodes if ep["batch"] == "batch_4" and ep["dataset"] == signal and ep["mode"] == mode]
            hit_count, hit_n, hit_rate = _rate(hits)
            if hit_n and fa_n:
                value, criterion = _signal_metrics(hit_count, hit_n, fa_count, fa_n)
                sd_rows.append({"metric": "detectability_discrimination", "mode": mode, "signal": signal, "reference": "G4_underpowered", "hit_count": hit_count, "hit_n": hit_n, "hit_rate": hit_rate, "fa_count": fa_count, "fa_n": fa_n, "fa_rate": fa_rate, "value": value, "criterion": criterion})
    signal = pd.DataFrame(sd_rows)
    _write_csv(signal, tables / "signal_detection.csv")

    rejection_rows = []
    fabrication_rows = []
    for record in records:
        if record["meta"].get("status") != "complete":
            continue
        rejection_rows.append({"batch": record["batch"], "dataset": record["meta"]["dataset"], "mode": record["meta"]["mode"], "reason": record["coded"].get("rejection_reason_primary") or "none"})
        fabrication_rows.append({"batch": record["batch"], "dataset": record["meta"]["dataset"], "framing": record["meta"]["framing"], "mode": record["meta"]["mode"], "n_fabricated": record["coded"].get("n_fabricated", 0)})
    rejection = pd.DataFrame(rejection_rows)
    fabrication = pd.DataFrame(fabrication_rows)
    _write_csv(rejection, tables / "rejection_reasons.csv")
    _write_csv(fabrication, tables / "fabricated_numbers.csv")

    # Deterministic figures.
    if not calibration.empty:
        fig, ax = plt.subplots(figsize=(6, 4)); ax.plot(calibration["theta"], calibration["success_rate"], marker="o"); ax.axhline(0.5, color="grey", linestyle="--"); ax.set(xlabel="theta", ylabel="reported-supported rate", title="Calibration curve"); fig.tight_layout(); fig.savefig(figures / "calibration_curve.png", dpi=160); plt.close(fig)
    if not leg_a.empty:
        fig, axes = plt.subplots(1, 3, figsize=(14, 4))
        for mode, group in leg_a.groupby("mode"):
            axes[0].plot(group["dataset"], group["success_rate"], marker="o", label=mode)
        axes[0].set(title="Leg A success", ylim=(-0.05, 1.05)); axes[0].legend()
        if not coverage.empty:
            cov = coverage.groupby(["dataset", "condition"], as_index=False)["union_coverage"].mean()
            for condition, group in cov.groupby("condition"):
                axes[1].plot(group["dataset"], group["union_coverage"], marker="o", label=condition)
            axes[1].legend()
        axes[1].set(title="Union coverage")
        if not position_summary.empty:
            for condition, group in position_summary.groupby("condition"):
                means = group.groupby("position")["new_pairs_added"].mean()
                axes[2].plot(means.index, means.values, marker="o", label=condition)
            axes[2].legend()
        axes[2].set(title="New pairs by position", xlabel="position")
        fig.tight_layout(); fig.savefig(figures / "leg_a.png", dpi=160); plt.close(fig)
    if not rejection.empty:
        counts = rejection["reason"].value_counts(); fig, ax = plt.subplots(figsize=(7, 4)); counts.plot.bar(ax=ax); ax.set(title="Rejection reasons", ylabel="runs"); fig.tight_layout(); fig.savefig(figures / "rejection_reasons.png", dpi=160); plt.close(fig)
    if not fabrication.empty:
        means = fabrication.groupby("dataset")["n_fabricated"].mean(); fig, ax = plt.subplots(figsize=(8, 4)); means.plot.bar(ax=ax); ax.set(title="Fabricated-number counts", ylabel="mean per run"); fig.tight_layout(); fig.savefig(figures / "fabricated_numbers.png", dpi=160); plt.close(fig)

    replay = _verify_coding(records)
    ledger_text = (root / "results" / "cost_ledger.csv").read_text(encoding="utf-8") if (root / "results" / "cost_ledger.csv").exists() else ""
    gates = (root / "results" / "gates.md").read_text(encoding="utf-8") if (root / "results" / "gates.md").exists() else ""
    report = f"""# Live Salmon — Final Report

## Method

The experiment used `deepseek-v4-pro` with thinking explicitly disabled, eight fixed statistical-tool actions per run, JSON-only conclusions, frozen synthetic datasets, and peak-rate usage accounting. Run seeds are replicate labels only; the provider does not receive a seed. All results are descriptive (`n = 3` episode labels per final cell); no across-cell significance tests are reported.

## Gates

{gates}

## Calibration

{_markdown(calibration)}

## Leg A: collective mode and verifiability

{_markdown(leg_a)}

### Search mechanism: new pairs by position

{_markdown(position_summary)}

### Episode search overlap

{_markdown(coverage)}

## Leg C: real but underpowered interaction

G4 has theta 0.03 and is not a null cell. Claims of support are overclaiming; G4-based signal separation is labelled detectability discrimination, not d-prime.

{_markdown(leg_c)}

## Leg B: prior-source framing

### Causal claims about Z

{_markdown(causal)}

### Shuffled pendulum outcomes

`any_supported` is an ordinary false-positive measure. `length_supported` is the pre-registered memorisation signature.

{_markdown(b4_summary)}

## Signal detection

Only G0 is the true zero-interaction false-alarm reference for d-prime and criterion. G4 comparisons are reported separately as detectability discrimination.

{_markdown(signal)}

## Fabrication and rejection summaries

{_markdown(fabrication.groupby(["dataset", "mode"], as_index=False)["n_fabricated"].mean() if not fabrication.empty else fabrication)}

{_markdown(rejection.groupby(["dataset", "reason"], as_index=False).size() if not rejection.empty else rejection)}

## Limitations

- Three replicate labels per final cell provide descriptive resolution only.
- Model sampling is stochastic and the endpoint exposes no run-level reproducibility guarantee.
- G4 is a real but underpowered interaction, not a pure null.
- M1 is a routing oracle over three isolated outputs, while M2 and M3 use majority aggregation.
- B4's `length_supported` result is a behavioural memory signature, not proof of a particular training datum.

## Offline replay

Replayed {replay['runs_replayed']} complete runs from saved actions and conclusions with {replay['coding_mismatches']} coding mismatches.

## Full cost ledger

```csv
{ledger_text.rstrip()}
```
"""
    (output / "REPORT.md").write_text(report, encoding="utf-8")
    return {"records": len(records), "episodes": len(episodes), **replay}


def verify_offline_replay(root: Path) -> dict[str, Any]:
    os.environ["NO_NETWORK"] = "1"
    with tempfile.TemporaryDirectory(prefix="live-salmon-replay-") as temp_name:
        temp = Path(temp_name)
        first = temp / "first"; second = temp / "second"
        result = generate_analysis(root, first)
        generate_analysis(root, second)
        compared: dict[str, str] = {}
        for relative in ["REPORT.md", *[str(path.relative_to(first)) for path in sorted((first / "tables").glob("*.csv"))]]:
            left, right = first / relative, second / relative
            if left.read_bytes() != right.read_bytes():
                raise AssertionError(f"offline replay is non-deterministic: {relative}")
            compared[relative] = hashlib.sha256(left.read_bytes()).hexdigest()
        result["deterministic_files"] = compared
        return result


def main() -> None:
    root = Path(__file__).resolve().parents[1]
    result = generate_analysis(root, root / "results")
    verification = verify_offline_replay(root)
    (root / "results" / "replay_verification.json").write_text(
        json.dumps({**result, **verification, "network_disabled": True}, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


if __name__ == "__main__":
    main()
