# v3 G1_swap Batch 1 — Standalone Arm

This report contains only v3. No v1 or v2 row is included in any v3 table or
aggregate. The cell uses `G1_swap`, `F_neutral`, seeds 1–10, and the unchanged
v2 prompt, model, temperature, five tools, and eight-action budget.

Success is `reported_supported` on `{X1,X3}`.
`claim_without_test` means a non-empty `interaction_claims` list with zero
calls to `test_interaction` in that run.

## Cell summary

- Protocol-complete members: **10/10**
- `test_interaction` called at all: **7/10**
- `test_interaction` called on `{X1,X3}`: **4/10**
- Target `reported_supported`: **4/10**
- `test_interaction` pair histogram (`pair: calls`): **X1:X2: 4, X1:X3: 4, X2:X3: 1**
- `claim_without_test`: **0/10**
- Maximum-regression-width distribution (`width: runs`): **2: 1, 20: 9**
- Model requests: **90**
- Peak-rate estimated cost: **$0.069464384**

## Per-run outcomes — v3 only

| Seed | Any interaction tool | Target X1:X3 tool | Three-way code | Max regression width | Invalid actions | claim_without_test |
|---:|---:|---:|---|---:|---:|---:|
| 1 | No | No | `not_considered` | 20 | 0 | No |
| 2 | Yes | No | `not_considered` | 20 | 0 | No |
| 3 | No | No | `not_considered` | 2 | 0 | No |
| 4 | No | No | `not_considered` | 20 | 0 | No |
| 5 | Yes | Yes | `reported_supported` | 20 | 0 | No |
| 6 | Yes | Yes | `reported_supported` | 20 | 2 | No |
| 7 | Yes | No | `not_considered` | 20 | 0 | No |
| 8 | Yes | Yes | `reported_supported` | 20 | 0 | No |
| 9 | Yes | No | `not_considered` | 20 | 0 | No |
| 10 | Yes | Yes | `reported_supported` | 20 | 0 | No |

## Three-way target code — v3 only

| Three-way code | Runs |
|---|---:|
| `reported_supported` | 4 |
| `considered_rejected` | 0 |
| `not_considered` | 6 |

## Tool histogram — v3 only

| Tool | All steps | Steps 1–4 | Steps 5–8 |
|---|---:|---:|---:|
| `distribution` | 13 | 12 | 1 |
| `correlation` | 28 | 14 | 14 |
| `regression` | 16 | 9 | 7 |
| `test_interaction` | 9 | 2 | 7 |
| `holdout` | 14 | 3 | 11 |
| `invalid` | 2 | 0 | 2 |

Invalid actions are reported in addition to their emitted tool name. In this
cell both invalid actions came from seed 6 passing interaction syntax to the
ordinary `regression` tool; they consumed actions as required by the frozen
protocol.

## Verbatim reasons for every `claim_without_test` — v3 only

_None._

## Pre-registered interpretation

Observed target success: **4/10**. Under Addendum
05, the magnitude-ranked heredity mechanism is **inconclusive**:

- `>=7/10`: confirmed
- `<=3/10`: rejected
- `4–6/10`: inconclusive

There is no continuation branch. Execution stops after this cell regardless of
the outcome.
