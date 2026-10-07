# v1 versus v2 Batch 1 — Separate Arms

The two arms are reported in separate tables and are never pooled. Both use
the byte-identical theta-0.8 `G1_strong` data, `F_neutral`, seeds 1–10, the
same model, temperature, five tools, and eight-action budget. The sole
experimental change is that v2 exposes the unchanged conclusion schema in the
system message from step 1.

`claim_without_test` is the pre-registered secondary outcome: a non-empty
`interaction_claims` list with zero calls to `test_interaction` in that run.

## v1 control arm

- `test_interaction` called at all: **0/10**
- `test_interaction` called on `{X4,X5}`: **0/10**
- Pairs supplied to `test_interaction` (`pair: calls`): **none**
- target coded `reported_supported`: **0/10**
- `claim_without_test`: **1/10**
- Maximum-regression-width distribution (`width: runs`): **1: 1, 2: 3, 3: 2, 6: 2, 20: 2**
- Model requests: **90**
- Peak-rate estimated cost: **$0.051389800**

### Per-run outcomes — v1 control arm

| Seed | Any interaction tool | Target X4:X5 tool | Target reported supported | Max regression width | Invalid actions | claim_without_test |
|---:|---:|---:|---:|---:|---:|---:|
| 1 | No | No | No | 3 | 0 | No |
| 2 | No | No | No | 2 | 0 | No |
| 3 | No | No | No | 2 | 0 | No |
| 4 | No | No | No | 20 | 0 | No |
| 5 | No | No | No | 6 | 0 | No |
| 6 | No | No | No | 3 | 0 | No |
| 7 | No | No | No | 2 | 0 | No |
| 8 | No | No | No | 1 | 0 | No |
| 9 | No | No | No | 20 | 0 | Yes |
| 10 | No | No | No | 6 | 0 | No |

### Tool histogram — v1 control arm

| Tool | All steps | Steps 1–4 | Steps 5–8 |
|---|---:|---:|---:|
| `distribution` | 14 | 14 | 0 |
| `correlation` | 42 | 21 | 21 |
| `regression` | 14 | 4 | 10 |
| `test_interaction` | 0 | 0 | 0 |
| `holdout` | 10 | 1 | 9 |
| `invalid` | 0 | 0 | 0 |

### Verbatim reasons for every `claim_without_test` — v1 control arm

> Seed 9: "Adding X1:X2 did not improve holdout R2 significantly (0.771772 vs 0.771869)."

> Seed 9: "Adding X1:X3 did not improve holdout R2 significantly (0.771772 vs 0.771869)."

> Seed 9: "Holdout R2 decreased (0.768603 vs 0.771772) and interaction not significant."

> Seed 9: "Holdout R2 decreased (0.768603 vs 0.771772) and interaction not significant."


## v2 treatment arm

- `test_interaction` called at all: **8/10**
- `test_interaction` called on `{X4,X5}`: **0/10**
- Pairs supplied to `test_interaction` (`pair: calls`): **X1:X2: 3, X1:X3: 5**
- target coded `reported_supported`: **0/10**
- `claim_without_test`: **0/10**
- Maximum-regression-width distribution (`width: runs`): **3: 1, 4: 1, 20: 8**
- Model requests: **90**
- Peak-rate estimated cost: **$0.069391344**

### Per-run outcomes — v2 treatment arm

| Seed | Any interaction tool | Target X4:X5 tool | Target reported supported | Max regression width | Invalid actions | claim_without_test |
|---:|---:|---:|---:|---:|---:|---:|
| 1 | Yes | No | No | 20 | 0 | No |
| 2 | Yes | No | No | 20 | 0 | No |
| 3 | Yes | No | No | 3 | 0 | No |
| 4 | Yes | No | No | 20 | 0 | No |
| 5 | Yes | No | No | 20 | 0 | No |
| 6 | Yes | No | No | 20 | 1 | No |
| 7 | No | No | No | 4 | 0 | No |
| 8 | Yes | No | No | 20 | 0 | No |
| 9 | No | No | No | 20 | 0 | No |
| 10 | Yes | No | No | 20 | 0 | No |

### Tool histogram — v2 treatment arm

| Tool | All steps | Steps 1–4 | Steps 5–8 |
|---|---:|---:|---:|
| `distribution` | 14 | 10 | 4 |
| `correlation` | 25 | 15 | 10 |
| `regression` | 16 | 7 | 9 |
| `test_interaction` | 8 | 1 | 7 |
| `holdout` | 16 | 6 | 10 |
| `invalid` | 1 | 1 | 0 |

### Verbatim reasons for every `claim_without_test` — v2 treatment arm

_None._


## Pre-registered branch

v2 target `reported_supported` is **0/10**.
The 0/10 branch applies: stop after this comparison; Gate 2 is not started.

## O1. Full-width regression diagnostics — v2 only

Eight v2 runs passed all 20 feature columns to `regression`. Rank 1 denotes
the largest absolute t statistic among the 20 feature coefficients; the
intercept is excluded. Because every run queried the same frozen dataset with
the same 20-column model, the returned statistics are identical, but every
run and action step is reported separately.

| Seed | Step | X4 coef | X4 se | X4 p | X4 rank by \|t\| | X5 coef | X5 se | X5 p | X5 rank by \|t\| |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 1 | 2 | 0.180924 | 0.0416471 | 1.5435e-05 | 4 | 0.14717 | 0.0414199 | 0.000398853 | 5 |
| 2 | 2 | 0.180924 | 0.0416471 | 1.5435e-05 | 4 | 0.14717 | 0.0414199 | 0.000398853 | 5 |
| 4 | 1 | 0.180924 | 0.0416471 | 1.5435e-05 | 4 | 0.14717 | 0.0414199 | 0.000398853 | 5 |
| 5 | 1 | 0.180924 | 0.0416471 | 1.5435e-05 | 4 | 0.14717 | 0.0414199 | 0.000398853 | 5 |
| 6 | 3 | 0.180924 | 0.0416471 | 1.5435e-05 | 4 | 0.14717 | 0.0414199 | 0.000398853 | 5 |
| 8 | 3 | 0.180924 | 0.0416471 | 1.5435e-05 | 4 | 0.14717 | 0.0414199 | 0.000398853 | 5 |
| 9 | 8 | 0.180924 | 0.0416471 | 1.5435e-05 | 4 | 0.14717 | 0.0414199 | 0.000398853 | 5 |
| 10 | 1 | 0.180924 | 0.0416471 | 1.5435e-05 | 4 | 0.14717 | 0.0414199 | 0.000398853 | 5 |

Runs in which both X4 and X5 had `p < 0.05`: **8/8 full-width runs**
(and 8/10 v2 runs overall). Despite ranking fourth and fifth by absolute t,
neither variable was routed into `test_interaction` with the other.

## O2. M1 routing oracle, n=10 members, computed from existing independent runs — v2

No new run was made. Each member's set contains only the normalized pairs it
passed to `test_interaction` in its existing v2 action log.

- Union across ten members: **{X1:X2, X1:X3}**
- Is `{X4,X5}` in the union? **No**
- Routing-oracle success for reported-supported `{X4,X5}`: **0**
- Members with non-empty interaction-test sets: **8**
- Members excluded from pairwise Jaccard because their sets were empty: **2**
- Mean pairwise Jaccard among the eight non-empty member sets: **0.464286**
  (`13/28`; each member had one pair, with three X1:X2 members and five
  X1:X3 members)

The routing oracle cannot recover the target because no independent member
ever routed X4:X5 to the dedicated interaction tool or reported it supported.

## O3. M1 routing oracle, n=10 members, computed from existing independent runs — v1

No new run was made. All ten v1 interaction-test pair sets are empty.

- Union across ten members: **empty set**
- Is `{X4,X5}` in the union? **No**
- Routing-oracle success for reported-supported `{X4,X5}`: **0**
- Members with non-empty interaction-test sets: **0**
- Members excluded from pairwise Jaccard because their sets were empty: **10**
- Mean pairwise Jaccard among non-empty member sets: **not estimable** (fewer
  than two eligible members)
