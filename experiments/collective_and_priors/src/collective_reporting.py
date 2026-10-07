"""Frozen Addendum 07 report layout for the shared-log arm."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .execute_experiment import RESULTS


def _rate(n: int, denominator: int) -> str:
    return f"{n}/{denominator} ({n/denominator:.1%})" if denominator else "undefined (0/0)"


def write_reports(result: dict[str, Any]) -> None:
    baseline = result["baseline"]
    majority, union = result["M3_majority"], result["M3_union"]
    conditional = _rate(result["conditional_hits"], result["conditional_agents"])
    duplication = _rate(result["duplication_hits"], result["duplication_opportunities"])
    fp = result["false_positive_by_position"]
    new_pairs = result["new_pairs_by_position"]
    run_lines = [
        "| Episode | Agent | Position | Status | Three-way code | Own X4:X5 | Seen only | New pairs | Top3 false positive | Claim without test |",
        "|---:|---|---:|---|---|---|---|---:|---|---|",
    ]
    for item in result["per_run"]:
        run_lines.append(
            f"| {item['episode']} | {item['agent']} | {item['position']} | {item['status']} | "
            f"{item['interaction_code']} | {item['own_test_X4X5']} | {item['seen_X4X5_only']} | "
            f"{item['new_pairs_added']} | {item['top3_false_positive']} | {item['claim_without_test']} |"
        )
    summary = f"""## Collective shared-log arm — Addendum 07

### Pre-registered verdicts and outcomes

- Gate 1a: **PASS**, {result['complete_episodes']}/10 protocol-complete episodes.
- Gate 2: **WAIVED** by Addendum 07; S-v2 E7 within-family Jaccard = **{result['E7_S_v2_jaccard']:.6f}**.
- A1 M3_majority versus M2: **{_rate(majority, 10)}** versus **{_rate(baseline['M2'], 120)}**; two-sided descriptive Fisher p = **{result['fisher_majority_vs_M2']:.6g}**.
- A1 M3_union versus M1: **{_rate(union, 10)}** versus **{_rate(baseline['M1'], 120)}**; two-sided descriptive Fisher p = **{result['fisher_union_vs_M1']:.6g}**.
- A2 duplication: **{duplication}**; pre-registered verdict **{result['duplication_verdict']}**.

M1 and M2 are {baseline['label']} The 120 triples overlap; Fisher p-values are descriptive and do not establish independent sampling.

| Source/outcome | Successes | Total | Rate |
|---|---:|---:|---:|
| Anthropic S-v2 single | {baseline['single_supported']} | 10 | {baseline['single_supported']/10:.1%} |
| M1 isolated union | {baseline['M1']} | 120 | {baseline['M1']/120:.1%} |
| M2 isolated majority | {baseline['M2']} | 120 | {baseline['M2']/120:.1%} |
| M3 shared-log union | {union} | 10 | {union/10:.1%} |
| M3 shared-log majority | {majority} | 10 | {majority/10:.1%} |

### A2–A6 details

- A2 top3 re-tests/opportunities: **{result['duplication_hits']}/{result['duplication_opportunities']}**.
- A3 episodes with position 1 not testing X4:X5: **{result['conditional_episodes']}/10**. Position-2/3 agents self-testing it: **{conditional}**; S-v2 single-agent baseline **5/10**.
- A4 `new_pairs_added` by position (own pair coverage, excluding previously touched pairs):
  - Position 1: mean **{new_pairs['1']['mean']:.3f}**, distribution **{new_pairs['1']['distribution']}**.
  - Position 2: mean **{new_pairs['2']['mean']:.3f}**, distribution **{new_pairs['2']['distribution']}**.
  - Position 3: mean **{new_pairs['3']['mean']:.3f}**, distribution **{new_pairs['3']['distribution']}**.
- A5 any top3 pair reported supported on G1_strong (true-null control): S-v2 **{_rate(baseline['single_false_positive'], 10)}**; M3 position 1 **{_rate(fp['1'], 10)}**, position 2 **{_rate(fp['2'], 10)}**, position 3 **{_rate(fp['3'], 10)}**.
- A6 fresh M3 position-1 X4:X5 `reported_supported`: **{_rate(result['position1_supported'], 10)}**, separate from S-v2.
- M3 `claim_without_test` (own plus shown shared entries): **{sum(item['claim_without_test'] for item in result['per_run'])}/30**.

Episode 10 position 2 had a protocol failure after four saved actions. It has no conclusion, so it contributes no reported support or false-positive report; its saved actions still count for the A2/A3 search-process denominators and A4 pair additions, and position 3 saw those four observations under the frozen shared-log rule. The episode fails Gate 1a's per-episode completeness criterion, while the arm passes at 9/10.

### Resumption and cost audit

- The episode-6 position-2 interrupted attempt is excluded from scoring and shared inputs. Its **{result['discarded_attempt']['response_count']}** charged responses cost **${result['discarded_attempt']['enforcement_usd']}** and remain in the ledger; the replacement uses a separate run ID.
- M3 arm ledger: **{result['cost']['arm_response_count']}** returned API responses, **${result['cost']['arm_enforcement_usd']}** including the discarded attempt (cap $3.50). Global cumulative cost: **${result['cost']['global_enforcement_usd']}** (fuse $9.00).
- The non-generative pre-resume API probe succeeded. Transient retry notes are in `results/cost_ledger.notes.jsonl`.

### Per-agent M3 coding

{chr(10).join(run_lines)}
"""
    out = RESULTS / "collective" / "REPORT.md"
    out.write_text("# Addendum 07 — collective shared-log arm\n\n" + summary, encoding="utf-8")
    final = RESULTS / "REPORT_FINAL.md"
    content = final.read_text(encoding="utf-8")
    marker = "## Collective shared-log arm — Addendum 07"
    if marker in content:
        content = content[:content.index(marker)].rstrip() + "\n\n"
    final.write_text(content.rstrip() + "\n\n" + summary, encoding="utf-8")
