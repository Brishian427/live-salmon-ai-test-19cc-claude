"""Separate-arm Batch 1 diagnostics for Addendum 04."""

from __future__ import annotations

import json
from collections import Counter
from pathlib import Path
from typing import Any


TOOLS = ("distribution", "correlation", "regression", "test_interaction", "holdout")


def _load_arm(runs_root: Path, batch: str) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for meta_path in sorted((runs_root / batch).glob("*/*/meta.json")):
        directory = meta_path.parent
        meta = json.loads(meta_path.read_text(encoding="utf-8"))
        actions = [
            json.loads(line)
            for line in (directory / "actions.jsonl").read_text(encoding="utf-8").splitlines()
            if line
        ]
        coded = json.loads((directory / "coded.json").read_text(encoding="utf-8"))
        conclusion_raw = (directory / "conclusion.json").read_text(encoding="utf-8").strip()
        try:
            conclusion = json.loads(conclusion_raw) if conclusion_raw else {}
        except json.JSONDecodeError:
            conclusion = {}
        cost = json.loads((directory / "cost.json").read_text(encoding="utf-8"))
        rows.append({"meta": meta, "actions": actions, "coded": coded, "conclusion": conclusion, "cost": cost})
    return sorted(rows, key=lambda row: int(row["meta"]["seed"]))


def _summarize(
    rows: list[dict[str, Any]],
    target_interaction: tuple[str, str] = ("X4", "X5"),
) -> dict[str, Any]:
    pooled: Counter[str] = Counter()
    first: Counter[str] = Counter()
    second: Counter[str] = Counter()
    per_run: list[dict[str, Any]] = []
    claims_without_test: list[dict[str, Any]] = []
    interaction_pairs: Counter[tuple[str, str]] = Counter()
    for row in rows:
        actions = row["actions"]
        names = [entry.get("action", {}).get("tool", "invalid") for entry in actions]
        for counter, entries in ((pooled, actions), (first, actions[:4]), (second, actions[4:8])):
            for entry in entries:
                name = entry.get("action", {}).get("tool")
                if name in TOOLS:
                    counter[name] += 1
                if not entry.get("valid", "error" not in entry.get("result", {})):
                    counter["invalid"] += 1
        interaction_actions = [entry for entry in actions if entry.get("action", {}).get("tool") == "test_interaction"]
        target_actions = [
            entry
            for entry in interaction_actions
            if {entry.get("action", {}).get("a"), entry.get("action", {}).get("b")} == set(target_interaction)
        ]
        interaction_pairs.update(
            tuple(sorted((entry["action"]["a"], entry["action"]["b"])))
            for entry in interaction_actions
            if isinstance(entry.get("action", {}).get("a"), str)
            and isinstance(entry.get("action", {}).get("b"), str)
        )
        widths = [
            len(entry.get("action", {}).get("columns", []))
            for entry in actions
            if entry.get("action", {}).get("tool") == "regression"
            and isinstance(entry.get("action", {}).get("columns"), list)
        ]
        claims = row["conclusion"].get("interaction_claims", []) or []
        flag = bool(claims and not interaction_actions)
        if flag:
            claims_without_test.append(
                {
                    "seed": row["meta"]["seed"],
                    "reasons": [claim.get("reason") for claim in claims],
                }
            )
        per_run.append(
            {
                "seed": row["meta"]["seed"],
                "any_test_interaction": bool(interaction_actions),
                "target_test_interaction": bool(target_actions),
                "reported_supported": row["coded"].get("interaction_code") == "reported_supported",
                "interaction_code": row["coded"].get("interaction_code"),
                "max_regression_width": max(widths, default=0),
                "invalid_actions": sum(
                    not entry.get("valid", "error" not in entry.get("result", {})) for entry in actions
                ),
                "claim_without_test": flag,
            }
        )
    width_distribution = Counter(item["max_regression_width"] for item in per_run)
    return {
        "n": len(rows),
        "per_run": per_run,
        "any_test_interaction": sum(item["any_test_interaction"] for item in per_run),
        "target_test_interaction": sum(item["target_test_interaction"] for item in per_run),
        "reported_supported": sum(item["reported_supported"] for item in per_run),
        "claim_without_test": sum(item["claim_without_test"] for item in per_run),
        "width_distribution": dict(sorted(width_distribution.items())),
        "pooled": {name: pooled[name] for name in (*TOOLS, "invalid")},
        "first": {name: first[name] for name in (*TOOLS, "invalid")},
        "second": {name: second[name] for name in (*TOOLS, "invalid")},
        "claims_without_test": claims_without_test,
        "interaction_pairs": {f"{a}:{b}": count for (a, b), count in sorted(interaction_pairs.items())},
        "api_calls": sum(int(row["cost"]["api_calls"]) for row in rows),
        "estimated_usd": sum(float(row["cost"]["estimated_usd"]) for row in rows),
    }


def _histogram_table(summary: dict[str, Any]) -> str:
    lines = ["| Tool | All steps | Steps 1–4 | Steps 5–8 |", "|---|---:|---:|---:|"]
    for name in (*TOOLS, "invalid"):
        lines.append(f"| `{name}` | {summary['pooled'][name]} | {summary['first'][name]} | {summary['second'][name]} |")
    return "\n".join(lines)


def _run_table(summary: dict[str, Any]) -> str:
    lines = [
        "| Seed | Any interaction tool | Target X4:X5 tool | Target reported supported | Max regression width | Invalid actions | claim_without_test |",
        "|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for item in summary["per_run"]:
        lines.append(
            f"| {item['seed']} | {'Yes' if item['any_test_interaction'] else 'No'} | "
            f"{'Yes' if item['target_test_interaction'] else 'No'} | "
            f"{'Yes' if item['reported_supported'] else 'No'} | {item['max_regression_width']} | {item['invalid_actions']} | "
            f"{'Yes' if item['claim_without_test'] else 'No'} |"
        )
    return "\n".join(lines)


def _arm_section(label: str, summary: dict[str, Any]) -> str:
    width = ", ".join(f"{key}: {value}" for key, value in summary["width_distribution"].items())
    pairs = ", ".join(f"{key}: {value}" for key, value in summary["interaction_pairs"].items()) or "none"
    quoted: list[str] = []
    for item in summary["claims_without_test"]:
        for reason in item["reasons"]:
            quoted.append(f"> Seed {item['seed']}: {json.dumps(reason, ensure_ascii=False)}")
    quotes = "\n\n".join(quoted) if quoted else "_None._"
    n = summary["n"]
    return f"""## {label}

- `test_interaction` called at all: **{summary['any_test_interaction']}/{n}**
- `test_interaction` called on `{{X4,X5}}`: **{summary['target_test_interaction']}/{n}**
- Pairs supplied to `test_interaction` (`pair: calls`): **{pairs}**
- target coded `reported_supported`: **{summary['reported_supported']}/{n}**
- `claim_without_test`: **{summary['claim_without_test']}/{n}**
- Maximum-regression-width distribution (`width: runs`): **{width}**
- Model requests: **{summary['api_calls']}**
- Peak-rate estimated cost: **${summary['estimated_usd']:.9f}**

### Per-run outcomes — {label}

{_run_table(summary)}

### Tool histogram — {label}

{_histogram_table(summary)}

### Verbatim reasons for every `claim_without_test` — {label}

{quotes}
"""


def write_batch1_comparison(root: Path) -> dict[str, Any]:
    v1 = _summarize(_load_arm(root / "runs", "batch_1"))
    v2 = _summarize(_load_arm(root / "runs", "v2_batch_1"))
    report = f"""# v1 versus v2 Batch 1 — Separate Arms

The two arms are reported in separate tables and are never pooled. Both use
the byte-identical theta-0.8 `G1_strong` data, `F_neutral`, seeds 1–10, the
same model, temperature, five tools, and eight-action budget. The sole
experimental change is that v2 exposes the unchanged conclusion schema in the
system message from step 1.

`claim_without_test` is the pre-registered secondary outcome: a non-empty
`interaction_claims` list with zero calls to `test_interaction` in that run.

{_arm_section('v1 control arm', v1)}

{_arm_section('v2 treatment arm', v2)}

## Pre-registered branch

v2 target `reported_supported` is **{v2['reported_supported']}/{v2['n']}**.
"""
    if v2["n"] == 10:
        if v2["reported_supported"] == 0:
            report += "The 0/10 branch applies: stop after this comparison; Gate 2 is not started.\n"
        else:
            report += "The >=1/10 branch applies: continue to Gate 2 and the remaining amended experiment.\n"
    else:
        report += "The arm is incomplete, so no continuation branch is evaluated.\n"
    output = root / "results" / "v2" / "BATCH1_COMPARISON.md"
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(report, encoding="utf-8")
    machine = root / "results" / "v2" / "batch1_comparison.json"
    machine.write_text(json.dumps({"v1": v1, "v2": v2}, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return {"v1": v1, "v2": v2}
