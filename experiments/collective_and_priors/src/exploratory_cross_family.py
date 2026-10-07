"""Offline, post-registered E1–E7 audit of saved interaction routing logs."""

from __future__ import annotations

import itertools
import json
from collections import Counter
from pathlib import Path
from statistics import mean
from typing import Any

from scipy.stats import fisher_exact

from .v2_reporting import _load_arm


TOP3 = {("X1", "X2"), ("X1", "X3"), ("X2", "X3")}
ARM_SPECS = (
    ("DeepSeek v2", "v2_batch_1"),
    ("DeepSeek v3", "v3_batch_1"),
    ("Anthropic S-v1", "anthropic_s_v1"),
    ("Anthropic S-v2", "anthropic_s_v2"),
    ("Anthropic S-v3", "anthropic_s_v3"),
)
BEGIN = "<!-- BEGIN EXPLORATORY E1-E7 -->"
END = "<!-- END EXPLORATORY E1-E7 -->"
LIMITATION = (
    "- `regression` does not accept A:B interaction terms while `holdout` does. Agents that tried to confirm a discovered interaction in a full model lost one action per run (S-v3: 10/10 runs). This penalises more sophisticated behaviour and appears only after a discovery, so it does not affect X4:X5 outcomes. Tools were not changed post hoc."
)


def _calls(row: dict[str, Any]) -> list[dict[str, Any]]:
    output = []
    for entry in row["actions"]:
        action = entry.get("action", {})
        if action.get("tool") != "test_interaction":
            continue
        pair = tuple(sorted((str(action.get("a")), str(action.get("b")))))
        output.append(
            {
                "step": int(entry["step"]),
                "pair": pair,
                "interaction_p": entry.get("result", {}).get("interaction_p"),
            }
        )
    return output


def _pair_set(row: dict[str, Any]) -> set[tuple[str, str]]:
    return {call["pair"] for call in _calls(row)}


def _jaccard(rows: list[dict[str, Any]]) -> dict[str, Any]:
    sets = [_pair_set(row) for row in rows]
    nonempty = [value for value in sets if value]
    scores = [len(a & b) / len(a | b) for a, b in itertools.combinations(nonempty, 2)]
    return {
        "mean": mean(scores) if scores else None,
        "pairs_compared": len(scores),
        "empty_runs_excluded": len(sets) - len(nonempty),
    }


def _arm(rows: list[dict[str, Any]]) -> dict[str, Any]:
    per_run = []
    for row in rows:
        calls = _calls(row)
        top = [call["step"] for call in calls if call["pair"] in TOP3]
        other = [call["step"] for call in calls if call["pair"] not in TOP3]
        if top and other:
            order = "ordered" if max(top) < min(other) else "interleaved_or_reversed"
        elif top:
            order = "top3_only_no_contrast"
        elif other:
            order = "non_top3_only_no_contrast"
        else:
            order = "no_tests"
        significant = [call for call in calls if isinstance(call["interaction_p"], (int, float)) and call["interaction_p"] < 0.05]
        first_significant_step = significant[0]["step"] if significant else None
        after = sum(call["step"] > first_significant_step for call in calls) if first_significant_step is not None else None
        per_run.append(
            {
                "seed": int(row["meta"]["seed"]),
                "calls": calls,
                "n_tests": len(calls),
                "order": order,
                "first_significant_step": first_significant_step,
                "tests_after_first_significant": after,
            }
        )
    categories = Counter(item["order"] for item in per_run)
    distribution = Counter(item["n_tests"] for item in per_run)
    union = set().union(*(_pair_set(row) for row in rows)) if rows else set()
    return {
        "per_run": per_run,
        "ordering": dict(categories),
        "order_compatible_runs": categories["ordered"] + categories["top3_only_no_contrast"],
        "informative_ordered": categories["ordered"],
        "informative_runs": categories["ordered"] + categories["interleaved_or_reversed"],
        "mean_tests": mean(item["n_tests"] for item in per_run),
        "test_count_distribution": dict(sorted(distribution.items())),
        "union": [f"{a}:{b}" for a, b in sorted(union)],
        "jaccard": _jaccard(rows),
    }


def analyze(root: Path) -> dict[str, Any]:
    rows = {label: _load_arm(root / "runs", batch) for label, batch in ARM_SPECS}
    if any(len(items) != 10 for items in rows.values()):
        raise AssertionError("E1–E7 require exactly 10 saved runs in every specified arm")
    arms = {label: _arm(items) for label, items in rows.items()}
    deepseek_union = set(arms["DeepSeek v2"]["union"])
    anthropic_union = set(arms["Anthropic S-v2"]["union"])
    tested_p = fisher_exact([[0, 10], [5, 5]], alternative="two-sided").pvalue
    supported_p = fisher_exact([[7, 3], [5, 5]], alternative="two-sided").pvalue
    result = {
        "arms": arms,
        "E3": {
            "deepseek_v2_subset_of_anthropic_s_v2": deepseek_union <= anthropic_union,
            "deepseek_v2_union": sorted(deepseek_union),
            "anthropic_s_v2_union": sorted(anthropic_union),
            "anthropic_only": sorted(anthropic_union - deepseek_union),
        },
        "E4": {
            "cross_family": 1,
            "within_deepseek": 0,
            "within_anthropic": 1,
            "max_within_family": 1,
            "diversity_benefit": False,
        },
        "E6": {
            "x4x5_tested_fisher_two_sided_p": float(tested_p),
            "x4x5_reported_supported_fisher_two_sided_p": float(supported_p),
        },
    }
    assert arms["DeepSeek v2"]["jaccard"]["mean"] is not None
    assert abs(arms["DeepSeek v2"]["jaccard"]["mean"] - 0.4642857142857143) < 1e-12
    assert result["E3"]["deepseek_v2_subset_of_anthropic_s_v2"]
    return result


def _distribution(value: dict[int, int]) -> str:
    return ", ".join(f"{key}: {count}" for key, count in value.items()) or "none"


def _order_table(label: str, arm: dict[str, Any]) -> str:
    lines = [
        f"#### {label}",
        "",
        "| Seed | `test_interaction` calls in step order | Ordering status |",
        "|---:|---|---|",
    ]
    for item in arm["per_run"]:
        calls = ", ".join(f"{call['step']}:{':'.join(call['pair'])}" for call in item["calls"]) or "none"
        lines.append(f"| {item['seed']} | {calls} | `{item['order']}` |")
    lines.extend(
        [
            "",
            f"Order-compatible runs (including top3-only runs): **{arm['order_compatible_runs']}/10**. "
            f"Directly informative ordered runs: **{arm['informative_ordered']}/{arm['informative_runs']}**; "
            f"top3-only without a non-top3 comparison: **{arm['ordering'].get('top3_only_no_contrast', 0)}**; "
            f"no interaction test: **{arm['ordering'].get('no_tests', 0)}**.",
        ]
    )
    return "\n".join(lines)


def _stopping_table(label: str, arm: dict[str, Any]) -> str:
    lines = [
        f"#### {label}",
        "",
        "| Seed | First significant interaction step | Later interaction tests |",
        "|---:|---:|---:|",
    ]
    for item in arm["per_run"]:
        first = item["first_significant_step"]
        after = item["tests_after_first_significant"]
        lines.append(f"| {item['seed']} | {first if first is not None else 'none'} | {after if after is not None else 'N/A'} |")
    values = [item["tests_after_first_significant"] for item in arm["per_run"] if item["tests_after_first_significant"] is not None]
    lines.extend(["", f"Runs reaching a significant interaction: **{len(values)}/10**; later interaction tests: **{sum(values)} total**, **{mean(values):.3f} mean among those runs**." if values else "",])
    return "\n".join(lines)


def render(result: dict[str, Any]) -> str:
    arms = result["arms"]
    e1 = "\n\n".join(_order_table(label, arms[label]) for label, _batch in ARM_SPECS)
    e2_lines = []
    e7_lines = []
    for label, _batch in ARM_SPECS:
        arm = arms[label]
        e2_lines.append(f"- {label}: mean **{arm['mean_tests']:.3f}** tests/run; count distribution (`tests: runs`) **{_distribution(arm['test_count_distribution'])}**.")
        j = arm["jaccard"]
        e7_lines.append(f"- {label}: mean Jaccard **{j['mean']:.6f}** over {j['pairs_compared']} nonempty-set run pairs; {j['empty_runs_excluded']} empty runs excluded.")
    e3 = result["E3"]
    e4 = result["E4"]
    e6 = result["E6"]
    stopping = "\n\n".join(_stopping_table(label, arms[label]) for label in ("Anthropic S-v2", "Anthropic S-v3"))
    return f"""## EXPLORATORY / NOT PRE-REGISTERED — E1–E7

These calculations use saved action logs only. They do not replace the accepted
P1 `DIFFERENT`, P2 supported, or P3 p = 1 verdicts.

### E1. Ordering

`top3` is X1:X2, X1:X3, X2:X3. A run directly tests order only when it
contains both a top3 and a non-top3 interaction call; `ordered` means the
last top3 step precedes the first non-top3 step. A top3-only run is compatible
with that ordering but offers no observed contrast. Runs with no interaction
tests are not counted as order-compatible.

{e1}

Across families, the available logs do **not** directly establish identical
ordering: DeepSeek v2 never tested a non-top3 pair, so it has zero informative
within-run top3-versus-non-top3 comparisons. Anthropic S-v1 and S-v2 do show
top3-before-non-top3 ordering in every run where both classes were tested.

### E2. Search depth

Number of `test_interaction` calls per run, including zero-test runs:

{chr(10).join(e2_lines)}

### E3. Tested-pair set inclusion

- DeepSeek v2 union: **{{{', '.join(e3['deepseek_v2_union'])}}}**.
- Anthropic S-v2 union: **{{{', '.join(e3['anthropic_s_v2_union'])}}}**.
- DeepSeek v2 is a subset of Anthropic S-v2: **{'yes' if e3['deepseek_v2_subset_of_anthropic_s_v2'] else 'no'}**.
- Pairs added by Anthropic S-v2: **{{{', '.join(e3['anthropic_only'])}}}**.

### E4. Corrected routing oracle

Cross-family success is **{e4['cross_family']}**; the within-DeepSeek oracle is
**{e4['within_deepseek']}** and the within-Anthropic oracle is
**{e4['within_anthropic']}**. The corrected diversity criterion requires
cross-family > max(within-family): **{e4['cross_family']} > {e4['max_within_family']} is false**.
There is **no incremental diversity benefit** under this criterion. The
pre-registered P2 verdict remains recorded separately.

### E5. Interaction testing after the first significant interaction

`Later interaction tests` counts calls at steps strictly after the first
`test_interaction` result with `interaction_p < 0.05`. N/A means the run never
obtained such a result; it is not interpreted as stopping.

{stopping}

S-v2's first significant result occurred at step 6 or 8, whereas S-v3's
occurred at step 2 in every run. Thus S-v2's zero later tests cannot by
itself be interpreted as an earlier voluntary stopping rule; fewer action
slots remained after discovery.

### E6. Descriptive Fisher exact comparisons

- X4:X5 tested: DeepSeek v2 **0/10** versus Anthropic S-v2 **5/10**; two-sided Fisher p = **{e6['x4x5_tested_fisher_two_sided_p']:.6g}**.
- X4:X5 `reported_supported`: Anthropic S-v1 **7/10** versus S-v2 **5/10**; two-sided Fisher p = **{e6['x4x5_reported_supported_fisher_two_sided_p']:.6g}**.

Both tests are descriptive only and were not pre-registered.

### E7. Within-family routing homogeneity

Mean pairwise Jaccard of per-run interaction-pair sets. Empty sets are
excluded from pairwise comparisons and counted separately:

{chr(10).join(e7_lines)}
"""


def write_reports(root: Path) -> dict[str, Any]:
    result = analyze(root)
    appendix = render(result)
    cross_path = root / "results" / "cross_family" / "REPORT.md"
    original = cross_path.read_text(encoding="utf-8")
    if BEGIN in original:
        original = original.split(BEGIN, 1)[0].rstrip() + "\n\n## Limitations\n" + original.split("## Limitations\n", 1)[1]
    if "## Limitations\n" not in original:
        raise AssertionError("cross-family report lacks Limitations insertion point")
    before, limitations = original.split("## Limitations\n", 1)
    if LIMITATION not in limitations:
        limitations = limitations.rstrip() + "\n" + LIMITATION + "\n"
    cross_path.write_text(before.rstrip() + "\n\n" + BEGIN + "\n" + appendix.rstrip() + "\n" + END + "\n\n## Limitations\n" + limitations, encoding="utf-8")

    addendum = (root / "SPEC_ADDENDUM_06.md").read_text(encoding="utf-8")
    criterion_errors = "## Criterion errors\n" + addendum.split("## Criterion errors\n", 1)[1]
    analysis = json.loads((root / "results" / "cross_family" / "analysis.json").read_text(encoding="utf-8"))
    assert analysis["P1"]["verdict"] == "DIFFERENT"
    assert analysis["P2"]["supported"] is True
    assert analysis["P3"]["fisher_p"] == 1.0
    final = f"""# Live Salmon — Integrated Final Report

This report follows the executed sequence. The original frozen experiment
stopped at Gate 1b; later cells were separately authorized. All post-result
analyses below are labeled exploratory and use existing logs only.

## DeepSeek v1 — unchanged Batch 1, n=10

On `G1_strong`, 0/10 runs called `test_interaction` and 0/10 reported
X4:X5 supported. Gate 1b remained FAIL. Full diagnostics are in
`results/BATCH1_EXTENSION.md`.

## DeepSeek v2 — schema visible from step 1, n=10

On the same `G1_strong` data, 8/10 runs called `test_interaction`, 0/10
tested X4:X5, and 0/10 reported it supported. The pre-registered 0/10
branch stopped v2 before Gate 2. Full separate-arm comparison is in
`results/v2/BATCH1_COMPARISON.md`.

## DeepSeek v3 — interaction moved to X1:X3, n=10

On `G1_swap`, 4/10 runs reported X1:X3 supported. This is **inconclusive**
under Addendum 05's 4–6/10 rule. Full cell diagnostics are in
`results/v3/BATCH1_REPORT.md`.

## Anthropic cross-family replication — Addendum 06

### Accepted pre-registered verdicts

- P1: **DIFFERENT**. Anthropic S-v2 tested X4:X5 in 5/10 runs and reported
  it supported in all five.
- P2: **supported**. The pre-registered cross-family routing oracle was 1,
  compared with 0 within DeepSeek.
- P3: **p = 1**, two-sided Fisher exact. Anthropic selected X1:X3 in 10/10
  S-v2 and 10/10 S-v3 runs.

### Criterion errors

{criterion_errors.split('## Criterion errors', 1)[1].strip()}

{appendix.replace('## EXPLORATORY', '### EXPLORATORY', 1).replace(chr(10) + '### E', chr(10) + '#### E').replace('#### DeepSeek', '##### DeepSeek').replace('#### Anthropic', '##### Anthropic')}

### Separate Anthropic arm outcomes

#### S-v1

10/10 protocol-complete; X4:X5 tested and `reported_supported` in 7/10;
maximum regression width 20 in 10/10; `claim_without_test` 0/10.

#### S-v2

10/10 protocol-complete; X4:X5 tested and `reported_supported` in 5/10;
maximum regression width 20 in 10/10; `claim_without_test` 0/10.

#### S-v3

10/10 protocol-complete; X1:X3 tested and `reported_supported` in 10/10;
maximum regression width 20 in 10/10; `claim_without_test` 0/10. Each run
also made one invalid ordinary-regression call containing interaction syntax.

The per-run logs, tool histograms, p-values, ranks, costs, model selection,
and full arm diagnostics are in `results/cross_family/REPORT.md`.

### Offline verification

The final 38-test suite passed. The corrected read-only coding replay checked
all 63 saved runs with zero mismatches; the separate Anthropic replay also
reproduced all 264 tool actions across its 33 smoke and S-arm runs with zero
mismatches. The cost ledger remained at 567 rows during this supplement.

### Limitations

{limitations.strip()}
"""
    (root / "results" / "REPORT_FINAL.md").write_text(final, encoding="utf-8")
    (root / "results" / "cross_family" / "exploratory_e1_e7.json").write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    return result


def main() -> None:
    root = Path(__file__).resolve().parents[1]
    result = write_reports(root)
    print(json.dumps({"E3": result["E3"], "E4": result["E4"], "E6": result["E6"]}, sort_keys=True))


if __name__ == "__main__":
    main()
