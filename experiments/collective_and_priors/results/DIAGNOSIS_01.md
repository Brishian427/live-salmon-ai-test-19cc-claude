# Diagnosis 01 — Batch 1 Gate 1b Failure

Scope: the three existing Batch 1 action logs only, plus one direct offline
`ToolService` call on the frozen `G1_strong.csv`. No model API call, replacement
run, prompt change, tool change, or experimental revision was made.

## D1. Full 20-feature regression

| Run | Called `regression` with X1–X20 together? | Step |
|---|---:|---:|
| seed 1 | No | — |
| seed 2 | No | — |
| seed 3 | No | — |

The regressions that were called were:

- seed 1: `regression([X1])` at step 4 and `regression([X1,X2,X3])` at step 7;
- seed 2: `regression([X1,X3])` at step 8;
- seed 3: `regression([X1,X3])` at step 8.

## D2. X4/X5 estimates and ranks from a full regression

Not applicable. None of the three runs requested a regression containing all
20 feature columns, so the action logs contain no corresponding X4/X5
coefficient, standard-error, p-value, or absolute-t rank.

## D3. Pairs touched

These are all unordered pairs touched by either `correlation` or
`test_interaction`. No run called `test_interaction` at all.

### Seed 1

- `{X1, Y}` — `correlation`, step 3
- `{X2, Y}` — `correlation`, step 5
- `{X3, Y}` — `correlation`, step 6

### Seed 2

- `{X1, Y}` — `correlation`, step 2
- `{X2, Y}` — `correlation`, step 3
- `{X3, Y}` — `correlation`, step 4
- `{X4, Y}` — `correlation`, step 5
- `{X5, Y}` — `correlation`, step 6
- `{X6, Y}` — `correlation`, step 7

### Seed 3

- `{X1, Y}` — `correlation`, step 2
- `{X2, Y}` — `correlation`, step 3
- `{X3, Y}` — `correlation`, step 4
- `{X4, Y}` — `correlation`, step 5
- `{X5, Y}` — `correlation`, step 6
- `{X6, Y}` — `correlation`, step 7

## D4. Actions, coverage, and tool histograms

Coverage is distinct correlation/interaction pairs divided by 190.

| Run | `n_actions` | Distinct pairs | Coverage | Tool-name histogram |
|---|---:|---:|---:|---|
| seed 1 | 8 | 3 | 3/190 = 0.015789473684210527 | `distribution`: 2; `correlation`: 3; `regression`: 2; `holdout`: 1; `test_interaction`: 0 |
| seed 2 | 8 | 6 | 6/190 = 0.031578947368421054 | `distribution`: 1; `correlation`: 6; `regression`: 1; `holdout`: 0; `test_interaction`: 0 |
| seed 3 | 8 | 6 | 6/190 = 0.031578947368421054 | `distribution`: 1; `correlation`: 6; `regression`: 1; `holdout`: 0; `test_interaction`: 0 |

## D5. Direct offline X4·X5 check

Directly calling

```json
{"tool":"test_interaction","a":"X4","b":"X5"}
```

on the frozen `data/G1_strong.csv` through the existing `ToolService`, using a
temporary cache, returned:

| Field | Value |
|---|---:|
| interaction coefficient | 0.748512 |
| interaction SE | 0.0835222 |
| interaction p-value | **1.54339e-18** |
| R² without interaction | 0.0147968 |
| R² with interaction | 0.0883126 |
| delta R² | 0.0735158 |
| n | 1000 |

Therefore `interaction_p < 1e-10` is confirmed (`1.54339e-18 < 1e-10`).

## Diagnostic conclusion

The dataset and interaction tool expose the target signal decisively when it is
queried. Gate 1b failed because none of the three agents selected the X4·X5
interaction test within its eight actions. The observed failure is therefore a
search/decision failure under the frozen harness, not absence of the signal or
failure of `test_interaction`.

## No-API verification

The cost ledger remained byte-identical during this diagnosis and retained the
same 27 rows before and after the offline check. No API call was made.

## Step A supplement — explicit tool counts and regression widths

The histogram below counts all eight saved actions in each run. `Invalid`
counts actions whose saved `valid` field is `false`.

| Run | `distribution` | `correlation` | `regression` | `test_interaction` | `holdout` | Invalid |
|---|---:|---:|---:|---:|---:|---:|
| seed 1 | 2 | 3 | 2 | 0 | 1 | 0 |
| seed 2 | 1 | 6 | 1 | 0 | 0 | 0 |
| seed 3 | 1 | 6 | 1 | 0 | 0 | 0 |

Every saved `regression` call and its input width:

| Run | Step | Columns supplied | Number of columns |
|---|---:|---|---:|
| seed 1 | 4 | `X1` | 1 |
| seed 1 | 7 | `X1`, `X2`, `X3` | 3 |
| seed 2 | 8 | `X1`, `X3` | 2 |
| seed 3 | 8 | `X1`, `X3` | 2 |

No action was invalid, and no regression call contained more than three
features. This supplement was computed solely from the existing JSONL action
logs; no API call was made.
