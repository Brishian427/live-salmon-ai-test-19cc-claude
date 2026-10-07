# Batch 1 Extension to n=10

This report combines the original seeds 1–3 with the authorized extension
seeds 4–10. All ten runs use the same frozen `G1_strong` data,
`F_neutral`, model, temperature, messages, tools, and eight-action budget.
No specification or experimental parameter was changed.

## Primary result and Gate 1b

- Protocol-complete runs: **10/10**.
- Runs calling `test_interaction` at least once: **0/10**.
- Runs calling `test_interaction` on `{X4,X5}`: **0/10**.
- Runs coding `reported_supported` for `{X4,X5}`: **0/10**.
- Extended Gate 1b outcome: **FAIL**.

Every run remains `not_considered` for the target interaction under the frozen
coding rule. The n=10 extension strengthens the primary process finding: the
dedicated interaction tool was available in every step of every run and was
never selected across 80 total actions.

## Per-run summary

Tool histogram abbreviations: D = `distribution`, C = `correlation`,
R = `regression`, I = `test_interaction`, H = `holdout`.

| Seed | D | C | R | I | H | Invalid | Coverage | Max regression width | Interaction claims empty? | `claim_without_test` |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 1 | 2 | 3 | 2 | 0 | 1 | 0 | 0.015789473684210527 | 3 | Yes | No |
| 2 | 1 | 6 | 1 | 0 | 0 | 0 | 0.031578947368421054 | 2 | Yes | No |
| 3 | 1 | 6 | 1 | 0 | 0 | 0 | 0.031578947368421054 | 2 | Yes | No |
| 4 | 3 | 2 | 2 | 0 | 1 | 0 | 0.010526315789473684 | 20 | Yes | No |
| 5 | 0 | 7 | 1 | 0 | 0 | 0 | 0.03684210526315789 | 6 | Yes | No |
| 6 | 2 | 4 | 2 | 0 | 0 | 0 | 0.021052631578947368 | 3 | Yes | No |
| 7 | 2 | 3 | 2 | 0 | 1 | 0 | 0.015789473684210527 | 2 | Yes | No |
| 8 | 2 | 2 | 1 | 0 | 3 | 0 | 0.010526315789473684 | 1 | Yes | No |
| 9 | 1 | 2 | 1 | 0 | 4 | 0 | 0.010526315789473684 | 20 | **No** | **Yes** |
| 10 | 0 | 7 | 1 | 0 | 0 | 0 | 0.03684210526315789 | 6 | Yes | No |

Mean coverage was **0.02210526315789474**. No action was invalid.

## Aggregate tool histogram

| Tool | Calls | Share of 80 actions |
|---|---:|---:|
| `distribution` | 14 | 17.5% |
| `correlation` | 42 | 52.5% |
| `regression` | 14 | 17.5% |
| `test_interaction` | 0 | 0.0% |
| `holdout` | 10 | 12.5% |

## B6. Maximum regression width

Per-run maxima were:

| Seed | Maximum columns supplied to `regression` |
|---:|---:|
| 1 | 3 |
| 2 | 2 |
| 3 | 2 |
| 4 | 20 |
| 5 | 6 |
| 6 | 3 |
| 7 | 2 |
| 8 | 1 |
| 9 | 20 |
| 10 | 6 |

Distribution across runs:

| Maximum width | Runs |
|---:|---:|
| 1 | 1 |
| 2 | 3 |
| 3 | 2 |
| 6 | 2 |
| 20 | 2 |

- Runs ever passing more than five columns to `regression`: **4/10**.
- Runs ever passing all 20 feature columns to `regression`: **2/10**.

Thus the n=3 observation that no run exceeded three columns does not persist at
n=10. The stronger replicated result is specifically non-use of the dedicated
interaction test: **0/10**, even though two runs did perform the full
20-feature regression.

## B7. Tool position by half

Each cell is `D/C/R/I/H` for the indicated four-step half.

| Seed | Steps 1–4 | Steps 5–8 |
|---:|---|---|
| 1 | 2/1/1/0/0 | 0/2/1/0/1 |
| 2 | 1/3/0/0/0 | 0/3/1/0/0 |
| 3 | 1/3/0/0/0 | 0/3/1/0/0 |
| 4 | 3/1/0/0/0 | 0/1/2/0/1 |
| 5 | 0/4/0/0/0 | 0/3/1/0/0 |
| 6 | 2/2/0/0/0 | 0/2/2/0/0 |
| 7 | 2/1/1/0/0 | 0/2/1/0/1 |
| 8 | 2/1/1/0/0 | 0/1/0/0/3 |
| 9 | 1/1/1/0/1 | 0/1/0/0/3 |
| 10 | 0/4/0/0/0 | 0/3/1/0/0 |
| **All runs** | **14/21/4/0/1** | **0/21/10/0/9** |

There is a shift between halves: all 14 distribution calls occur in steps
1–4, while regression rises from 4 to 10 calls and holdout rises from 1 to 9
in steps 5–8. Correlation does **not** decline: it accounts for 21 calls in
each half. No run switches to `test_interaction` in either half. The observed
pattern is therefore early descriptive/pairwise screening followed by more
small-model or holdout confirmation, while pairwise correlation remains
equally common throughout.

## B8. Conclusion interaction claims

Nine runs submitted an empty `interaction_claims` list. Seed 9 submitted four
interaction claims while its log contained zero `test_interaction` calls and is
therefore explicitly flagged:

> **seed 9: `claim_without_test = true`**

Verbatim `reason` fields:

> "Adding X1:X2 did not improve holdout R2 significantly (0.771772 vs 0.771869)."

> "Adding X1:X3 did not improve holdout R2 significantly (0.771772 vs 0.771869)."

> "Holdout R2 decreased (0.768603 vs 0.771772) and interaction not significant."

> "Holdout R2 decreased (0.768603 vs 0.771772) and interaction not significant."

Important qualification: seed 9 did use `holdout` with the named interaction
terms, so these claims were not invented without any logged interaction-bearing
model. However, `holdout` returns R² values and no interaction p-value; the
words "significantly" and "not significant" are not supported by a significance
test in the log. All quoted numeric R² values themselves appear in its saved
tool results.

## Cost and stopping state

- Cost of all ten Batch 1 runs: **$0.0513898** at the frozen peak rates.
- Incremental cost of seeds 4–10: **$0.0389972**.
- Ledger rows after extension: **90** (nine model calls per complete run).
- Batch 1 cap was not breached.

Step C was not implemented. No prompt, specification, tool, action-budget,
dataset, generator, or model setting was changed.
