"""Standalone reporting for the Addendum 05 G1_swap cell."""

from __future__ import annotations

import json
from collections import Counter
from pathlib import Path
from typing import Any

from .v2_reporting import TOOLS, _histogram_table, _load_arm, _summarize


TARGET = ("X1", "X3")


def _run_table(summary: dict[str, Any]) -> str:
    lines = [
        "| Seed | Any interaction tool | Target X1:X3 tool | Three-way code | Max regression width | Invalid actions | claim_without_test |",
        "|---:|---:|---:|---|---:|---:|---:|",
    ]
    for item in summary["per_run"]:
        lines.append(
            f"| {item['seed']} | {'Yes' if item['any_test_interaction'] else 'No'} | "
            f"{'Yes' if item['target_test_interaction'] else 'No'} | `{item['interaction_code']}` | "
            f"{item['max_regression_width']} | {item['invalid_actions']} | "
            f"{'Yes' if item['claim_without_test'] else 'No'} |"
        )
    return "\n".join(lines)


def _code_table(summary: dict[str, Any]) -> str:
    counts = Counter(item["interaction_code"] for item in summary["per_run"])
    return "\n".join(
        [
            "| Three-way code | Runs |",
            "|---|---:|",
            f"| `reported_supported` | {counts['reported_supported']} |",
            f"| `considered_rejected` | {counts['considered_rejected']} |",
            f"| `not_considered` | {counts['not_considered']} |",
        ]
    )


def _classification(successes: int) -> str:
    if successes >= 7:
        return "confirmed"
    if successes <= 3:
        return "rejected"
    return "inconclusive"


def write_v3_report(root: Path) -> dict[str, Any]:
    summary = _summarize(_load_arm(root / "runs", "v3_batch_1"), TARGET)
    pairs = ", ".join(f"{pair}: {count}" for pair, count in summary["interaction_pairs"].items()) or "none"
    width = ", ".join(f"{key}: {value}" for key, value in summary["width_distribution"].items()) or "none"
    quotes: list[str] = []
    for item in summary["claims_without_test"]:
        for reason in item["reasons"]:
            quotes.append(f"> Seed {item['seed']}: {json.dumps(reason, ensure_ascii=False)}")
    quoted_reasons = "\n\n".join(quotes) if quotes else "_None._"
    outcome = _classification(summary["reported_supported"])
    report = f"""# v3 G1_swap Batch 1 — Standalone Arm

This report contains only v3. No v1 or v2 row is included in any v3 table or
aggregate. The cell uses `G1_swap`, `F_neutral`, seeds 1–10, and the unchanged
v2 prompt, model, temperature, five tools, and eight-action budget.

Success is `reported_supported` on `{{X1,X3}}`.
`claim_without_test` means a non-empty `interaction_claims` list with zero
calls to `test_interaction` in that run.

## Cell summary

- Protocol-complete members: **{summary['n']}/10**
- `test_interaction` called at all: **{summary['any_test_interaction']}/{summary['n']}**
- `test_interaction` called on `{{X1,X3}}`: **{summary['target_test_interaction']}/{summary['n']}**
- Target `reported_supported`: **{summary['reported_supported']}/{summary['n']}**
- `test_interaction` pair histogram (`pair: calls`): **{pairs}**
- `claim_without_test`: **{summary['claim_without_test']}/{summary['n']}**
- Maximum-regression-width distribution (`width: runs`): **{width}**
- Model requests: **{summary['api_calls']}**
- Peak-rate estimated cost: **${summary['estimated_usd']:.9f}**

## Per-run outcomes — v3 only

{_run_table(summary)}

## Three-way target code — v3 only

{_code_table(summary)}

## Tool histogram — v3 only

{_histogram_table(summary)}

Invalid actions are reported in addition to their emitted tool name. In this
cell both invalid actions came from seed 6 passing interaction syntax to the
ordinary `regression` tool; they consumed actions as required by the frozen
protocol.

## Verbatim reasons for every `claim_without_test` — v3 only

{quoted_reasons}

## Pre-registered interpretation

Observed target success: **{summary['reported_supported']}/10**. Under Addendum
05, the magnitude-ranked heredity mechanism is **{outcome}**:

- `>=7/10`: confirmed
- `<=3/10`: rejected
- `4–6/10`: inconclusive

There is no continuation branch. Execution stops after this cell regardless of
the outcome.
"""
    output = root / "results" / "v3" / "BATCH1_REPORT.md"
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(report, encoding="utf-8")
    machine = root / "results" / "v3" / "batch1_report.json"
    machine.write_text(
        json.dumps({"summary": summary, "pre_registered_outcome": outcome}, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return {"summary": summary, "pre_registered_outcome": outcome}
