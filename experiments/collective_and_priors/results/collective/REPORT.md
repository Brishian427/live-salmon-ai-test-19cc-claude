# Addendum 07 — collective shared-log arm

## Collective shared-log arm — Addendum 07

### Pre-registered verdicts and outcomes

- Gate 1a: **PASS**, 9/10 protocol-complete episodes.
- Gate 2: **WAIVED** by Addendum 07; S-v2 E7 within-family Jaccard = **0.777778**.
- A1 M3_majority versus M2: **8/10 (80.0%)** versus **60/120 (50.0%)**; two-sided descriptive Fisher p = **0.0995249**.
- A1 M3_union versus M1: **10/10 (100.0%)** versus **110/120 (91.7%)**; two-sided descriptive Fisher p = **1**.
- A2 duplication: **1/60 (1.7%)**; pre-registered verdict **DIVISION**.

M1 and M2 are computed from 10 independent single-agent runs by exhaustive triples; assumes exchangeability. The 120 triples overlap; Fisher p-values are descriptive and do not establish independent sampling.

| Source/outcome | Successes | Total | Rate |
|---|---:|---:|---:|
| Anthropic S-v2 single | 5 | 10 | 50.0% |
| M1 isolated union | 110 | 120 | 91.7% |
| M2 isolated majority | 60 | 120 | 50.0% |
| M3 shared-log union | 10 | 10 | 100.0% |
| M3 shared-log majority | 8 | 10 | 80.0% |

### A2–A6 details

- A2 top3 re-tests/opportunities: **1/60**.
- A3 episodes with position 1 not testing X4:X5: **8/10**. Position-2/3 agents self-testing it: **10/16 (62.5%)**; S-v2 single-agent baseline **5/10**.
- A4 `new_pairs_added` by position (own pair coverage, excluding previously touched pairs):
  - Position 1: mean **3.300**, distribution **[3, 3, 3, 3, 3, 3, 3, 3, 4, 5]**.
  - Position 2: mean **3.000**, distribution **[0, 1, 2, 2, 2, 3, 4, 5, 5, 6]**.
  - Position 3: mean **2.500**, distribution **[0, 0, 2, 2, 2, 3, 3, 4, 4, 5]**.
- A5 any top3 pair reported supported on G1_strong (true-null control): S-v2 **0/10 (0.0%)**; M3 position 1 **0/10 (0.0%)**, position 2 **0/10 (0.0%)**, position 3 **0/10 (0.0%)**.
- A6 fresh M3 position-1 X4:X5 `reported_supported`: **2/10 (20.0%)**, separate from S-v2.
- M3 `claim_without_test` (own plus shown shared entries): **0/30**.

Episode 10 position 2 had a protocol failure after four saved actions. It has no conclusion, so it contributes no reported support or false-positive report; its saved actions still count for the A2/A3 search-process denominators and A4 pair additions, and position 3 saw those four observations under the frozen shared-log rule. The episode fails Gate 1a's per-episode completeness criterion, while the arm passes at 9/10.

### Resumption and cost audit

- The episode-6 position-2 interrupted attempt is excluded from scoring and shared inputs. Its **6** charged responses cost **$0.0485160000** and remain in the ledger; the replacement uses a separate run ID.
- M3 arm ledger: **289** returned API responses, **$2.6973000000** including the discarded attempt (cap $3.50). Global cumulative cost: **$4.7584175280** (fuse $9.00).
- The non-generative pre-resume API probe succeeded. Transient retry notes are in `results/cost_ledger.notes.jsonl`.

### Per-agent M3 coding

| Episode | Agent | Position | Status | Three-way code | Own X4:X5 | Seen only | New pairs | Top3 false positive | Claim without test |
|---:|---|---:|---|---|---|---|---:|---|---|
| 1 | A | 1 | complete | not_considered | False | False | 3 | False | False |
| 1 | B | 2 | complete | reported_supported | True | False | 5 | False | False |
| 1 | C | 3 | complete | reported_supported | False | True | 2 | False | False |
| 2 | B | 1 | complete | reported_supported | True | False | 5 | False | False |
| 2 | C | 2 | complete | reported_supported | False | True | 1 | False | False |
| 2 | A | 3 | complete | reported_supported | False | True | 4 | False | False |
| 3 | C | 1 | complete | not_considered | False | False | 3 | False | False |
| 3 | A | 2 | complete | reported_supported | True | False | 2 | False | False |
| 3 | B | 3 | complete | reported_supported | False | True | 5 | False | False |
| 4 | A | 1 | complete | not_considered | False | False | 3 | False | False |
| 4 | B | 2 | complete | not_considered | False | False | 2 | False | False |
| 4 | C | 3 | complete | reported_supported | True | False | 3 | False | False |
| 5 | B | 1 | complete | not_considered | False | False | 3 | False | False |
| 5 | C | 2 | complete | reported_supported | True | False | 3 | False | False |
| 5 | A | 3 | complete | reported_supported | False | True | 2 | False | False |
| 6 | C | 1 | complete | not_considered | False | False | 3 | False | False |
| 6 | A | 2 | complete | reported_supported | True | False | 4 | False | False |
| 6 | B | 3 | complete | reported_supported | True | False | 0 | False | False |
| 7 | A | 1 | complete | reported_supported | True | False | 4 | False | False |
| 7 | B | 2 | complete | reported_supported | False | True | 0 | False | False |
| 7 | C | 3 | complete | reported_supported | False | True | 4 | False | False |
| 8 | B | 1 | complete | not_considered | False | False | 3 | False | False |
| 8 | C | 2 | complete | reported_supported | True | False | 6 | False | False |
| 8 | A | 3 | complete | reported_supported | False | True | 3 | False | False |
| 9 | C | 1 | complete | not_considered | False | False | 3 | False | False |
| 9 | A | 2 | complete | reported_supported | True | False | 5 | False | False |
| 9 | B | 3 | complete | reported_supported | True | False | 0 | False | False |
| 10 | A | 1 | complete | not_considered | False | False | 3 | False | False |
| 10 | B | 2 | protocol_failure | None | False | False | 2 | False | False |
| 10 | C | 3 | complete | reported_supported | True | False | 2 | False | False |

## Supplementary readouts

- **R1 — Conditional target testing.** In the 8 M3 episodes where the position-1 agent did not run `test_interaction` on `{X4,X5}`, position-2 and position-3 agents ran that test themselves in **10/16 (62.5%)** cases.
- **R2 — Source of supported target reports.** Among the 20 M3 agents coded `reported_supported` on `{X4,X5}`, **12** were `own_test` and **8** were `seen_only`. By position: position 1 = **2 own_test, 0 seen_only** (2 supported); position 2 = **6 own_test, 2 seen_only** (8 supported); position 3 = **4 own_test, 6 seen_only** (10 supported).
- **R3 — New pairs added.** Position 1: mean **3.30**, distribution **[3, 3, 3, 3, 3, 3, 3, 3, 4, 5]**. Position 2: mean **3.00**, distribution **[0, 1, 2, 2, 2, 3, 4, 5, 5, 6]**. Position 3: mean **2.50**, distribution **[0, 0, 2, 2, 2, 3, 3, 4, 4, 5]**.
- **R4 — Any top3 pair reported supported.** S-v2 single agents: **0/10 (0.0%)**. M3 overall: **0/30 (0.0%)**. M3 by position: position 1 **0/10 (0.0%)**, position 2 **0/10 (0.0%)**, position 3 **0/10 (0.0%)**. The protocol-failed episode-10 position-2 agent produced no support report and remains in the stated M3 denominator.
- **R5 — Fresh position-1 target support.** M3 position-1 agents reported `{X4,X5}` supported in **2/10 (20.0%)** runs. This rate is not pooled with S-v2.
- **R6 — Episode-10 sensitivity.** If episode 10 is excluded, M3 majority is **8/9** and M3 union is **9/9**. If episode 10 is included and its failed agent is counted as not supporting, M3 majority is **8/10** and M3 union is **10/10**. The existing published **8/10 majority** and **10/10 union** figures used the second treatment. Both treatments are reported because the episode-level aggregation rule for a protocol-failed agent was not pre-specified; no treatment is selected as preferred.
- **R7 — Isolated-copy `new_pairs_added` baseline.** Across all **720** ordered triples of distinct S-v2 runs, where pairs are those touched by `correlation` or `test_interaction`, mean `new_pairs_added` by position was **3.80 / 0.51 / 0.31** for positions 1 / 2 / 3, respectively.
