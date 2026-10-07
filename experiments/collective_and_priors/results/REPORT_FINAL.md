# Live Salmon — Integrated Final Report

![Experimental design](figures/experiment_design.svg)

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

This section is a post-result interpretation audit. It does not alter the
pre-registered rules or their accepted outcomes: P1 `DIFFERENT`, P2 supported,
and P3 Fisher two-sided p = 1.

**P1.** The `DIFFERENT` rule (`X4:X5` tested in at least 1/10 S-v2 runs)
fires when search **order** is identical but search **depth** is greater. It
therefore measured depth and labelled it prior. S-v2's top3 share was
30/38 = 0.789, above the pre-registered `SHARED` threshold of 0.75; the
verdict flipped solely on the `X4:X5` clause. Step-order evidence is examined
separately and exploratorily in E1.

**P2.** The pre-registered rule compared the cross-family oracle only with
the within-DeepSeek oracle. A diversity-benefit test must compare
cross-family success with `max(within-DeepSeek, within-Anthropic)`. Here the
corrected comparison is 1 versus `max(0, 1) = 1`, so there is no diversity
benefit. This does not change the recorded P2 verdict under its original rule.

**P3.** Anthropic tested all three top3 pairs in every S-v2 and S-v3 run, so
`P(select X1:X3) = 1` in both arms. The Fisher test had no power to distinguish
the selection mechanism within this family. Its pre-registered p = 1 remains
the recorded result.

### EXPLORATORY / NOT PRE-REGISTERED — E1–E7

These calculations use saved action logs only. They do not replace the accepted
P1 `DIFFERENT`, P2 supported, or P3 p = 1 verdicts.

#### E1. Ordering

`top3` is X1:X2, X1:X3, X2:X3. A run directly tests order only when it
contains both a top3 and a non-top3 interaction call; `ordered` means the
last top3 step precedes the first non-top3 step. A top3-only run is compatible
with that ordering but offers no observed contrast. Runs with no interaction
tests are not counted as order-compatible.

##### DeepSeek v2

| Seed | `test_interaction` calls in step order | Ordering status |
|---:|---|---|
| 1 | 7:X1:X2 | `top3_only_no_contrast` |
| 2 | 4:X1:X3 | `top3_only_no_contrast` |
| 3 | 8:X1:X3 | `top3_only_no_contrast` |
| 4 | 7:X1:X2 | `top3_only_no_contrast` |
| 5 | 6:X1:X2 | `top3_only_no_contrast` |
| 6 | 5:X1:X3 | `top3_only_no_contrast` |
| 7 | none | `no_tests` |
| 8 | 8:X1:X3 | `top3_only_no_contrast` |
| 9 | none | `no_tests` |
| 10 | 6:X1:X3 | `top3_only_no_contrast` |

Order-compatible runs (including top3-only runs): **8/10**. Directly informative ordered runs: **0/0**; top3-only without a non-top3 comparison: **8**; no interaction test: **2**.

##### DeepSeek v3

| Seed | `test_interaction` calls in step order | Ordering status |
|---:|---|---|
| 1 | none | `no_tests` |
| 2 | 5:X1:X2 | `top3_only_no_contrast` |
| 3 | none | `no_tests` |
| 4 | none | `no_tests` |
| 5 | 8:X1:X3 | `top3_only_no_contrast` |
| 6 | 3:X1:X3 | `top3_only_no_contrast` |
| 7 | 4:X1:X2 | `top3_only_no_contrast` |
| 8 | 7:X1:X3 | `top3_only_no_contrast` |
| 9 | 7:X1:X2 | `top3_only_no_contrast` |
| 10 | 6:X1:X3, 7:X2:X3, 8:X1:X2 | `top3_only_no_contrast` |

Order-compatible runs (including top3-only runs): **7/10**. Directly informative ordered runs: **0/0**; top3-only without a non-top3 comparison: **7**; no interaction test: **3**.

##### Anthropic S-v1

| Seed | `test_interaction` calls in step order | Ordering status |
|---:|---|---|
| 1 | 2:X1:X3, 3:X1:X2, 4:X2:X3, 8:X4:X5 | `ordered` |
| 2 | 2:X1:X3, 3:X1:X2, 4:X2:X3, 8:X4:X5 | `ordered` |
| 3 | 2:X1:X3, 3:X1:X2, 4:X2:X3, 8:X4:X5 | `ordered` |
| 4 | 2:X1:X3, 3:X1:X2, 4:X2:X3, 8:X3:X4 | `ordered` |
| 5 | 2:X1:X3, 3:X1:X2, 4:X2:X3, 8:X4:X5 | `ordered` |
| 6 | 2:X1:X3, 3:X1:X2, 4:X2:X3, 8:X4:X5 | `ordered` |
| 7 | 2:X1:X3, 3:X1:X2, 4:X2:X3, 8:X4:X5 | `ordered` |
| 8 | 2:X1:X3, 3:X1:X2, 4:X2:X3 | `top3_only_no_contrast` |
| 9 | 2:X1:X3, 3:X1:X2, 4:X2:X3 | `top3_only_no_contrast` |
| 10 | 2:X1:X3, 3:X1:X2, 4:X2:X3, 6:X4:X5 | `ordered` |

Order-compatible runs (including top3-only runs): **10/10**. Directly informative ordered runs: **8/8**; top3-only without a non-top3 comparison: **2**; no interaction test: **0**.

##### Anthropic S-v2

| Seed | `test_interaction` calls in step order | Ordering status |
|---:|---|---|
| 1 | 2:X1:X3, 3:X1:X2, 4:X2:X3, 6:X1:X4 | `ordered` |
| 2 | 2:X1:X3, 3:X1:X2, 4:X2:X3, 8:X4:X5 | `ordered` |
| 3 | 2:X1:X3, 3:X1:X2, 4:X2:X3, 6:X4:X5 | `ordered` |
| 4 | 2:X1:X3, 3:X1:X2, 4:X2:X3 | `top3_only_no_contrast` |
| 5 | 2:X1:X3, 3:X1:X2, 4:X2:X3 | `top3_only_no_contrast` |
| 6 | 2:X1:X3, 3:X1:X2, 4:X2:X3, 6:X1:X4, 8:X4:X5 | `ordered` |
| 7 | 2:X1:X3, 3:X1:X2, 4:X2:X3, 6:X1:X4, 8:X4:X5 | `ordered` |
| 8 | 2:X1:X3, 3:X1:X2, 4:X2:X3 | `top3_only_no_contrast` |
| 9 | 2:X1:X3, 3:X1:X2, 4:X2:X3 | `top3_only_no_contrast` |
| 10 | 2:X1:X3, 3:X1:X2, 4:X2:X3, 8:X4:X5 | `ordered` |

Order-compatible runs (including top3-only runs): **10/10**. Directly informative ordered runs: **6/6**; top3-only without a non-top3 comparison: **4**; no interaction test: **0**.

##### Anthropic S-v3

| Seed | `test_interaction` calls in step order | Ordering status |
|---:|---|---|
| 1 | 2:X1:X3, 4:X2:X3, 5:X1:X2 | `top3_only_no_contrast` |
| 2 | 2:X1:X3, 4:X2:X3, 5:X1:X2 | `top3_only_no_contrast` |
| 3 | 2:X1:X3, 4:X1:X2, 5:X2:X3 | `top3_only_no_contrast` |
| 4 | 2:X1:X3, 4:X2:X3, 5:X1:X2 | `top3_only_no_contrast` |
| 5 | 2:X1:X3, 4:X2:X3, 5:X1:X2 | `top3_only_no_contrast` |
| 6 | 2:X1:X3, 4:X2:X3, 5:X1:X2 | `top3_only_no_contrast` |
| 7 | 2:X1:X3, 5:X1:X2, 6:X2:X3 | `top3_only_no_contrast` |
| 8 | 2:X1:X3, 4:X2:X3, 5:X1:X2 | `top3_only_no_contrast` |
| 9 | 2:X1:X3, 4:X2:X3, 5:X1:X2 | `top3_only_no_contrast` |
| 10 | 2:X1:X3, 4:X2:X3, 5:X1:X2 | `top3_only_no_contrast` |

Order-compatible runs (including top3-only runs): **10/10**. Directly informative ordered runs: **0/0**; top3-only without a non-top3 comparison: **10**; no interaction test: **0**.

Across families, the available logs do **not** directly establish identical
ordering: DeepSeek v2 never tested a non-top3 pair, so it has zero informative
within-run top3-versus-non-top3 comparisons. Anthropic S-v1 and S-v2 do show
top3-before-non-top3 ordering in every run where both classes were tested.

#### E2. Search depth

Number of `test_interaction` calls per run, including zero-test runs:

- DeepSeek v2: mean **0.800** tests/run; count distribution (`tests: runs`) **0: 2, 1: 8**.
- DeepSeek v3: mean **0.900** tests/run; count distribution (`tests: runs`) **0: 3, 1: 6, 3: 1**.
- Anthropic S-v1: mean **3.800** tests/run; count distribution (`tests: runs`) **3: 2, 4: 8**.
- Anthropic S-v2: mean **3.800** tests/run; count distribution (`tests: runs`) **3: 4, 4: 4, 5: 2**.
- Anthropic S-v3: mean **3.000** tests/run; count distribution (`tests: runs`) **3: 10**.

#### E3. Tested-pair set inclusion

- DeepSeek v2 union: **{X1:X2, X1:X3}**.
- Anthropic S-v2 union: **{X1:X2, X1:X3, X1:X4, X2:X3, X4:X5}**.
- DeepSeek v2 is a subset of Anthropic S-v2: **yes**.
- Pairs added by Anthropic S-v2: **{X1:X4, X2:X3, X4:X5}**.

#### E4. Corrected routing oracle

Cross-family success is **1**; the within-DeepSeek oracle is
**0** and the within-Anthropic oracle is
**1**. The corrected diversity criterion requires
cross-family > max(within-family): **1 > 1 is false**.
There is **no incremental diversity benefit** under this criterion. The
pre-registered P2 verdict remains recorded separately.

#### E5. Interaction testing after the first significant interaction

`Later interaction tests` counts calls at steps strictly after the first
`test_interaction` result with `interaction_p < 0.05`. N/A means the run never
obtained such a result; it is not interpreted as stopping.

##### Anthropic S-v2

| Seed | First significant interaction step | Later interaction tests |
|---:|---:|---:|
| 1 | none | N/A |
| 2 | 8 | 0 |
| 3 | 6 | 0 |
| 4 | none | N/A |
| 5 | none | N/A |
| 6 | 8 | 0 |
| 7 | 8 | 0 |
| 8 | none | N/A |
| 9 | none | N/A |
| 10 | 8 | 0 |

Runs reaching a significant interaction: **5/10**; later interaction tests: **0 total**, **0.000 mean among those runs**.

##### Anthropic S-v3

| Seed | First significant interaction step | Later interaction tests |
|---:|---:|---:|
| 1 | 2 | 2 |
| 2 | 2 | 2 |
| 3 | 2 | 2 |
| 4 | 2 | 2 |
| 5 | 2 | 2 |
| 6 | 2 | 2 |
| 7 | 2 | 2 |
| 8 | 2 | 2 |
| 9 | 2 | 2 |
| 10 | 2 | 2 |

Runs reaching a significant interaction: **10/10**; later interaction tests: **20 total**, **2.000 mean among those runs**.

S-v2's first significant result occurred at step 6 or 8, whereas S-v3's
occurred at step 2 in every run. Thus S-v2's zero later tests cannot by
itself be interpreted as an earlier voluntary stopping rule; fewer action
slots remained after discovery.

#### E6. Descriptive Fisher exact comparisons

- X4:X5 tested: DeepSeek v2 **0/10** versus Anthropic S-v2 **5/10**; two-sided Fisher p = **0.0325077**.
- X4:X5 `reported_supported`: Anthropic S-v1 **7/10** versus S-v2 **5/10**; two-sided Fisher p = **0.649917**.

Both tests are descriptive only and were not pre-registered.

#### E7. Within-family routing homogeneity

Mean pairwise Jaccard of per-run interaction-pair sets. Empty sets are
excluded from pairwise comparisons and counted separately:

- DeepSeek v2: mean Jaccard **0.464286** over 28 nonempty-set run pairs; 2 empty runs excluded.
- DeepSeek v3: mean Jaccard **0.380952** over 21 nonempty-set run pairs; 3 empty runs excluded.
- Anthropic S-v1: mean Jaccard **0.848889** over 45 nonempty-set run pairs; 0 empty runs excluded.
- Anthropic S-v2: mean Jaccard **0.777778** over 45 nonempty-set run pairs; 0 empty runs excluded.
- Anthropic S-v3: mean Jaccard **1.000000** over 45 nonempty-set run pairs; 0 empty runs excluded.


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

- temperature 1.0 is not equivalent sampling diversity across providers (DeepSeek range 0-2, Anthropic range 0-1)
- DeepSeek used constrained JSON mode; Anthropic did not
- two families is the minimum for a prior-identity test, not a survey; a SHARED result may reflect common training material rather than a universal property of language models
- `regression` does not accept A:B interaction terms while `holdout` does. Agents that tried to confirm a discovered interaction in a full model lost one action per run (S-v3: 10/10 runs). This penalises more sophisticated behaviour and appears only after a discovery, so it does not affect X4:X5 outcomes. Tools were not changed post hoc.

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
