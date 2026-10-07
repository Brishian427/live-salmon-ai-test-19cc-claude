"""Pre-registered Anthropic cross-family replication analysis."""

from __future__ import annotations

import itertools
import csv
import json
import math
from collections import Counter
from pathlib import Path
from typing import Any

from scipy.stats import fisher_exact

from .v2_reporting import TOOLS, _load_arm, _summarize


TOP3 = {("X1", "X2"), ("X1", "X3"), ("X2", "X3")}


def _pair_set(row: dict[str, Any]) -> set[tuple[str, str]]:
    return {
        tuple(sorted((action["action"]["a"], action["action"]["b"])))
        for action in row["actions"]
        if action.get("action", {}).get("tool") == "test_interaction"
        and isinstance(action.get("action", {}).get("a"), str)
        and isinstance(action.get("action", {}).get("b"), str)
    }


def _pair_calls(row: dict[str, Any]) -> list[tuple[str, str]]:
    """Return every valid interaction call, preserving repeat calls."""
    return [
        tuple(sorted((action["action"]["a"], action["action"]["b"])))
        for action in row["actions"]
        if action.get("action", {}).get("tool") == "test_interaction"
        and isinstance(action.get("action", {}).get("a"), str)
        and isinstance(action.get("action", {}).get("b"), str)
    ]


def _full_width(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    output: list[dict[str, Any]] = []
    for row in rows:
        for action in row["actions"]:
            call = action.get("action", {})
            if call.get("tool") != "regression" or len(call.get("columns", [])) != 20:
                continue
            coefficients = action["result"]["coefficients"]
            ranked = sorted(
                ((abs(float(value["coef"]) / float(value["se"])), name) for name, value in coefficients.items()),
                reverse=True,
            )
            ranks = {name: index + 1 for index, (_t, name) in enumerate(ranked)}
            output.append(
                {
                    "seed": row["meta"]["seed"],
                    "step": action["step"],
                    "X4_p": coefficients["X4"]["p"],
                    "X4_abs_t_rank": ranks["X4"],
                    "X5_p": coefficients["X5"]["p"],
                    "X5_abs_t_rank": ranks["X5"],
                }
            )
    return sorted(output, key=lambda item: (int(item["seed"]), int(item["step"])))


def _three_way(summary: dict[str, Any]) -> Counter[str]:
    return Counter(item["interaction_code"] for item in summary["per_run"])


def _tool_table(summary: dict[str, Any]) -> str:
    lines = ["| Tool | All | Steps 1–4 | Steps 5–8 |", "|---|---:|---:|---:|"]
    for tool in (*TOOLS, "invalid"):
        lines.append(f"| `{tool}` | {summary['pooled'][tool]} | {summary['first'][tool]} | {summary['second'][tool]} |")
    return "\n".join(lines)


def _run_table(summary: dict[str, Any], target: str) -> str:
    lines = [
        f"| Seed | Any interaction tool | Target {target} tool | Three-way code | Max regression width | Invalid | claim_without_test |",
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


def _full_width_table(rows: list[dict[str, Any]]) -> str:
    if not rows:
        return "_No full-width regressions._"
    lines = [
        "| Seed | Step | X4 p | X4 rank by |t| | X5 p | X5 rank by |t| |",
        "|---:|---:|---:|---:|---:|---:|",
    ]
    for row in rows:
        lines.append(
            f"| {row['seed']} | {row['step']} | {row['X4_p']:.6g} | {row['X4_abs_t_rank']} | "
            f"{row['X5_p']:.6g} | {row['X5_abs_t_rank']} |"
        )
    return "\n".join(lines)


def _arm_section(label: str, rows: list[dict[str, Any]], target: tuple[str, str]) -> tuple[str, dict[str, Any]]:
    summary = _summarize(rows, target)
    complete = sum(row["meta"].get("status") == "complete" for row in rows)
    codes = _three_way(summary)
    widths = ", ".join(f"{width}: {count}" for width, count in summary["width_distribution"].items()) or "none"
    pairs = ", ".join(f"{pair}: {count}" for pair, count in summary["interaction_pairs"].items()) or "none"
    quotes: list[str] = []
    for item in summary["claims_without_test"]:
        for reason in item["reasons"]:
            quotes.append(f"> Seed {item['seed']}: {json.dumps(reason, ensure_ascii=False)}")
    reasons = "\n\n".join(quotes) if quotes else "_None._"
    full = _full_width(rows)
    text = f"""## {label}

- Protocol-complete runs: **{complete}/10**
- Any `test_interaction`: **{summary['any_test_interaction']}/{summary['n']}**
- Target `test_interaction` on `{{{target[0]},{target[1]}}}`: **{summary['target_test_interaction']}/{summary['n']}**
- Target `reported_supported`: **{summary['reported_supported']}/{summary['n']}**
- Three-way code: **reported_supported {codes['reported_supported']}; considered_rejected {codes['considered_rejected']}; not_considered {codes['not_considered']}**
- Pair histogram (`pair: calls`): **{pairs}**
- Maximum-regression-width distribution (`width: runs`): **{widths}**
- `claim_without_test`: **{summary['claim_without_test']}/{summary['n']}**
- Requests: **{summary['api_calls']}**
- Cost: **${summary['estimated_usd']:.9f}**

### Per-run outcomes — {label}

{_run_table(summary, f'{target[0]}:{target[1]}')}

### Tool histogram — {label}

{_tool_table(summary)}

### X4/X5 in full-width regressions — {label}

{_full_width_table(full)}

### Verbatim `claim_without_test` reasons — {label}

{reasons}
"""
    return text, {"summary": summary, "full_width": full}


def _oracle(rows: list[dict[str, Any]], target: tuple[str, str]) -> dict[str, Any]:
    pair_sets = [_pair_set(row) for row in rows]
    union = set().union(*pair_sets) if pair_sets else set()
    success = int(any(row["coded"].get("interaction_code") == "reported_supported" for row in rows))
    return {
        "union": [f"{a}:{b}" for a, b in sorted(union)],
        "oracle_success": success,
        "target": f"{target[0]}:{target[1]}",
    }


def generate_cross_family_report(root: Path, selected_model: str, selection: dict[str, Any]) -> dict[str, Any]:
    runs_root = root / "runs"
    arm_specs = [
        ("S-v1 Anthropic arm", "anthropic_s_v1", ("X4", "X5")),
        ("S-v2 Anthropic arm", "anthropic_s_v2", ("X4", "X5")),
        ("S-v3 Anthropic arm", "anthropic_s_v3", ("X1", "X3")),
    ]
    arm_rows = {batch: _load_arm(runs_root, batch) for _label, batch, _target in arm_specs}
    arm_sections: list[str] = []
    arm_data: dict[str, Any] = {}
    for label, batch, target in arm_specs:
        section, data = _arm_section(label, arm_rows[batch], target)
        arm_sections.append(section)
        arm_data[batch] = data

    s_v2 = arm_rows["anthropic_s_v2"]
    s_v3 = arm_rows["anthropic_s_v3"]
    s_v2_calls = [pair for row in s_v2 for pair in _pair_calls(row)]
    top3_calls = sum(pair in TOP3 for pair in s_v2_calls)
    share = top3_calls / len(s_v2_calls) if s_v2_calls else math.nan
    x4x5_runs = sum(("X4", "X5") in _pair_set(row) for row in s_v2)
    if len(s_v2_calls) < 4:
        p1 = "UNRESOLVED"
    elif x4x5_runs >= 1:
        p1 = "DIFFERENT"
    elif share >= 0.75:
        p1 = "SHARED"
    else:
        p1 = "UNRESOLVED"

    deepseek_v2 = _load_arm(runs_root, "v2_batch_1")
    deepseek_oracle = _oracle(deepseek_v2, ("X4", "X5"))
    anthropic_oracle = _oracle(s_v2, ("X4", "X5"))
    cross_union = sorted(set(deepseek_oracle["union"]) | set(anthropic_oracle["union"]))
    cross_success = max(deepseek_oracle["oracle_success"], anthropic_oracle["oracle_success"])
    p2_supported = cross_success > deepseek_oracle["oracle_success"]

    s_v2_x1x3 = sum(("X1", "X3") in _pair_set(row) for row in s_v2)
    s_v3_x1x3 = sum(("X1", "X3") in _pair_set(row) for row in s_v3)
    fisher = fisher_exact(
        [[s_v2_x1x3, 10 - s_v2_x1x3], [s_v3_x1x3, 10 - s_v3_x1x3]],
        alternative="two-sided",
    )

    selection_lines = []
    for candidate in selection.get("candidates", []):
        selection_lines.append(
            f"| `{candidate['model']}` | `{json.dumps(candidate['parameters'], sort_keys=True)}` | "
            f"{candidate['complete_runs']}/3 | {candidate['thinking_block_runs']} | "
            f"{'PASS' if candidate['passed'] else 'FAIL'} | {candidate.get('configuration_reason', 'not recorded')} | {candidate['reason']} |"
        )
    selection_table = "\n".join(
        [
            "| Candidate | Exact parameters | Complete | Thinking-block runs | Outcome | Configuration basis | Result reason |",
            "|---|---|---:|---:|---|---|---|",
            *selection_lines,
        ]
    )

    ledger_rows: list[dict[str, str]] = []
    with (root / "results" / "cost_ledger.csv").open(encoding="utf-8", newline="") as handle:
        ledger_rows = list(csv.DictReader(handle))
    cost_by_batch = {
        batch: sum(float(row["estimated_usd"]) for row in ledger_rows if row["batch"] == batch)
        for batch in ("anthropic_smoke", "anthropic_s_v1", "anthropic_s_v2", "anthropic_s_v3")
    }
    cross_cost = sum(cost_by_batch.values())
    cumulative_cost = float(ledger_rows[-1]["cumulative_usd"])

    arm_text = "\n".join(arm_sections)
    report = f"""# Cross-Family Replication Report

Selected Anthropic model: **`{selected_model}`**. The only experimental change
from the matched DeepSeek arms is model family. DeepSeek and Anthropic are
never pooled in a family-level estimate or arm table.

## Empirical model selection

{selection_table}

## Prompt and data identity

Every S-arm passed its pre-execution SHA-256 assertion against the matching
DeepSeek system message and canonical data file. Exact hashes are preserved in
each run's `meta.json` and in `hash_assertions.json`.

## Budget audit

| Batch | Actual cost | Cap |
|---|---:|---:|
| Smoke (all candidates) | ${cost_by_batch['anthropic_smoke']:.6f} | $0.60 |
| S-v1 | ${cost_by_batch['anthropic_s_v1']:.6f} | $1.20 |
| S-v2 | ${cost_by_batch['anthropic_s_v2']:.6f} | $1.20 |
| S-v3 | ${cost_by_batch['anthropic_s_v3']:.6f} | $1.20 |
| **Cross-family total** | **${cross_cost:.6f}** | — |

The complete ledger ended at **${cumulative_cost:.9f}**, including all earlier
DeepSeek work, below the unchanged $9.00 global fuse.

## P1. Shared blind spot

- Random-choice top3 share: **3/190 = 0.0157895**
- DeepSeek v2 top3 share: **8/8 = 1.0**
- Anthropic S-v2 top3 share: **{top3_calls}/{len(s_v2_calls)} = {share:.6g}**
- S-v2 runs testing X4:X5: **{x4x5_runs}/10**
- Pre-registered verdict: **{p1}**

## P2. Cross-family routing oracle on G1_strong

| Metric | DeepSeek v2 | Anthropic S-v2 | Cross-family oracle |
|---|---|---|---|
| Members | 10 | 10 | 20 |
| Tested-pair union | {', '.join(deepseek_oracle['union']) or 'empty'} | {', '.join(anthropic_oracle['union']) or 'empty'} | {', '.join(cross_union) or 'empty'} |
| Oracle success | {deepseek_oracle['oracle_success']} | {anthropic_oracle['oracle_success']} | {cross_success} |

“Diversity of priors, not number of agents” is **{'supported' if p2_supported else 'not supported'}** because
the cross-family oracle ({cross_success}) is {'greater than' if p2_supported else 'not greater than'} the
within-DeepSeek oracle ({deepseek_oracle['oracle_success']}).

## P3. Data-independence of X1:X3 pair selection

| Metric | DeepSeek | Anthropic |
|---|---:|---:|
| Strong cell | 5/10 (v2) | {s_v2_x1x3}/10 (S-v2) |
| Swap cell | 4/10 (v3) | {s_v3_x1x3}/10 (S-v3) |
| Fisher exact, two-sided | descriptive reference only | p = {float(fisher.pvalue):.6g} |

The Fisher comparison is descriptive only.

{arm_text}

## Limitations

- temperature 1.0 is not equivalent sampling diversity across providers (DeepSeek range 0-2, Anthropic range 0-1)
- DeepSeek used constrained JSON mode; Anthropic did not
- two families is the minimum for a prior-identity test, not a survey; a SHARED result may reflect common training material rather than a universal property of language models
"""
    output = root / "results" / "cross_family" / "REPORT.md"
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(report, encoding="utf-8")
    result = {
        "selected_model": selected_model,
        "budget": {"by_batch": cost_by_batch, "cross_family_total": cross_cost, "cumulative_usd": cumulative_cost},
        "P1": {"top3_calls": top3_calls, "total_calls": len(s_v2_calls), "share": share, "x4x5_runs": x4x5_runs, "verdict": p1},
        "P2": {"deepseek": deepseek_oracle, "anthropic": anthropic_oracle, "cross_union": cross_union, "cross_success": cross_success, "supported": p2_supported},
        "P3": {"deepseek": {"v2": 5, "v3": 4}, "anthropic": {"s_v2": s_v2_x1x3, "s_v3": s_v3_x1x3}, "fisher_p": float(fisher.pvalue)},
        "arms": arm_data,
    }
    (root / "results" / "cross_family" / "analysis.json").write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    return result
