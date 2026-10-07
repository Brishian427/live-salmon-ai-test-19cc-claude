# Cross-Family Replication Report

Selected Anthropic model: **`claude-sonnet-5-5`**. The only experimental change
from the matched DeepSeek arms is model family. DeepSeek and Anthropic are
never pooled in a family-level estimate or arm table.

## Empirical model selection

| Candidate | Exact parameters | Complete | Thinking-block runs | Outcome | Configuration basis | Result reason |
|---|---|---:|---:|---|---|---|
| `claude-sonnet-5-5` | `{"assistant_prefill_sent": false, "cache_control_sent": false, "effort_default": "high", "effort_sent": false, "max_tokens": 2048, "model": "claude-sonnet-5-5", "native_tools_sent": false, "structured_output_sent": false, "temperature": 1.0, "thinking": {"type": "between_tools"}, "top_k_sent": false, "top_p_sent": false}` | 3/3 | 0 | PASS | Official documentation says disabled is rejected; use the pre-registered between_tools fallback. | zero thinking blocks and >=2/3 complete |

## Prompt and data identity

Every S-arm passed its pre-execution SHA-256 assertion against the matching
DeepSeek system message and canonical data file. Exact hashes are preserved in
each run's `meta.json` and in `hash_assertions.json`.

## Budget audit

| Batch | Actual cost | Cap |
|---|---:|---:|
| Smoke (all candidates) | $0.176552 | $0.60 |
| S-v1 | $0.520458 | $1.20 |
| S-v2 | $0.589138 | $1.20 |
| S-v3 | $0.584724 | $1.20 |
| **Cross-family total** | **$1.870872** | — |

The complete ledger ended at **$2.061117528**, including all earlier
DeepSeek work, below the unchanged $9.00 global fuse.

## P1. Shared blind spot

- Random-choice top3 share: **3/190 = 0.0157895**
- DeepSeek v2 top3 share: **8/8 = 1.0**
- Anthropic S-v2 top3 share: **30/38 = 0.789474**
- S-v2 runs testing X4:X5: **5/10**
- Pre-registered verdict: **DIFFERENT**

## P2. Cross-family routing oracle on G1_strong

| Metric | DeepSeek v2 | Anthropic S-v2 | Cross-family oracle |
|---|---|---|---|
| Members | 10 | 10 | 20 |
| Tested-pair union | X1:X2, X1:X3 | X1:X2, X1:X3, X1:X4, X2:X3, X4:X5 | X1:X2, X1:X3, X1:X4, X2:X3, X4:X5 |
| Oracle success | 0 | 1 | 1 |

“Diversity of priors, not number of agents” is **supported** because
the cross-family oracle (1) is greater than the
within-DeepSeek oracle (0).

## P3. Data-independence of X1:X3 pair selection

| Metric | DeepSeek | Anthropic |
|---|---:|---:|
| Strong cell | 5/10 (v2) | 10/10 (S-v2) |
| Swap cell | 4/10 (v3) | 10/10 (S-v3) |
| Fisher exact, two-sided | descriptive reference only | p = 1 |

The Fisher comparison is descriptive only.

## S-v1 Anthropic arm

- Protocol-complete runs: **10/10**
- Any `test_interaction`: **10/10**
- Target `test_interaction` on `{X4,X5}`: **7/10**
- Target `reported_supported`: **7/10**
- Three-way code: **reported_supported 7; considered_rejected 0; not_considered 3**
- Pair histogram (`pair: calls`): **X1:X2: 10, X1:X3: 10, X2:X3: 10, X3:X4: 1, X4:X5: 7**
- Maximum-regression-width distribution (`width: runs`): **20: 10**
- `claim_without_test`: **0/10**
- Requests: **90**
- Cost: **$0.520458000**

### Per-run outcomes — S-v1 Anthropic arm

| Seed | Any interaction tool | Target X4:X5 tool | Three-way code | Max regression width | Invalid | claim_without_test |
|---:|---:|---:|---|---:|---:|---:|
| 1 | Yes | Yes | `reported_supported` | 20 | 0 | No |
| 2 | Yes | Yes | `reported_supported` | 20 | 0 | No |
| 3 | Yes | Yes | `reported_supported` | 20 | 0 | No |
| 4 | Yes | No | `not_considered` | 20 | 0 | No |
| 5 | Yes | Yes | `reported_supported` | 20 | 0 | No |
| 6 | Yes | Yes | `reported_supported` | 20 | 0 | No |
| 7 | Yes | Yes | `reported_supported` | 20 | 0 | No |
| 8 | Yes | No | `not_considered` | 20 | 0 | No |
| 9 | Yes | No | `not_considered` | 20 | 0 | No |
| 10 | Yes | Yes | `reported_supported` | 20 | 0 | No |

### Tool histogram — S-v1 Anthropic arm

| Tool | All | Steps 1–4 | Steps 5–8 |
|---|---:|---:|---:|
| `distribution` | 0 | 0 | 0 |
| `correlation` | 0 | 0 | 0 |
| `regression` | 14 | 10 | 4 |
| `test_interaction` | 38 | 30 | 8 |
| `holdout` | 28 | 0 | 28 |
| `invalid` | 0 | 0 | 0 |

### X4/X5 in full-width regressions — S-v1 Anthropic arm

| Seed | Step | X4 p | X4 rank by |t| | X5 p | X5 rank by |t| |
|---:|---:|---:|---:|---:|---:|
| 1 | 1 | 1.5435e-05 | 4 | 0.000398853 | 5 |
| 2 | 1 | 1.5435e-05 | 4 | 0.000398853 | 5 |
| 3 | 1 | 1.5435e-05 | 4 | 0.000398853 | 5 |
| 4 | 1 | 1.5435e-05 | 4 | 0.000398853 | 5 |
| 5 | 1 | 1.5435e-05 | 4 | 0.000398853 | 5 |
| 6 | 1 | 1.5435e-05 | 4 | 0.000398853 | 5 |
| 7 | 1 | 1.5435e-05 | 4 | 0.000398853 | 5 |
| 8 | 1 | 1.5435e-05 | 4 | 0.000398853 | 5 |
| 9 | 1 | 1.5435e-05 | 4 | 0.000398853 | 5 |
| 10 | 1 | 1.5435e-05 | 4 | 0.000398853 | 5 |

### Verbatim `claim_without_test` reasons — S-v1 Anthropic arm

_None._

## S-v2 Anthropic arm

- Protocol-complete runs: **10/10**
- Any `test_interaction`: **10/10**
- Target `test_interaction` on `{X4,X5}`: **5/10**
- Target `reported_supported`: **5/10**
- Three-way code: **reported_supported 5; considered_rejected 0; not_considered 5**
- Pair histogram (`pair: calls`): **X1:X2: 10, X1:X3: 10, X1:X4: 3, X2:X3: 10, X4:X5: 5**
- Maximum-regression-width distribution (`width: runs`): **20: 10**
- `claim_without_test`: **0/10**
- Requests: **90**
- Cost: **$0.589138000**

### Per-run outcomes — S-v2 Anthropic arm

| Seed | Any interaction tool | Target X4:X5 tool | Three-way code | Max regression width | Invalid | claim_without_test |
|---:|---:|---:|---|---:|---:|---:|
| 1 | Yes | No | `not_considered` | 20 | 0 | No |
| 2 | Yes | Yes | `reported_supported` | 20 | 0 | No |
| 3 | Yes | Yes | `reported_supported` | 20 | 1 | No |
| 4 | Yes | No | `not_considered` | 20 | 0 | No |
| 5 | Yes | No | `not_considered` | 20 | 0 | No |
| 6 | Yes | Yes | `reported_supported` | 20 | 0 | No |
| 7 | Yes | Yes | `reported_supported` | 20 | 0 | No |
| 8 | Yes | No | `not_considered` | 20 | 0 | No |
| 9 | Yes | No | `not_considered` | 20 | 0 | No |
| 10 | Yes | Yes | `reported_supported` | 20 | 0 | No |

### Tool histogram — S-v2 Anthropic arm

| Tool | All | Steps 1–4 | Steps 5–8 |
|---|---:|---:|---:|
| `distribution` | 0 | 0 | 0 |
| `correlation` | 0 | 0 | 0 |
| `regression` | 11 | 10 | 1 |
| `test_interaction` | 38 | 30 | 8 |
| `holdout` | 31 | 0 | 31 |
| `invalid` | 1 | 0 | 1 |

### X4/X5 in full-width regressions — S-v2 Anthropic arm

| Seed | Step | X4 p | X4 rank by |t| | X5 p | X5 rank by |t| |
|---:|---:|---:|---:|---:|---:|
| 1 | 1 | 1.5435e-05 | 4 | 0.000398853 | 5 |
| 2 | 1 | 1.5435e-05 | 4 | 0.000398853 | 5 |
| 3 | 1 | 1.5435e-05 | 4 | 0.000398853 | 5 |
| 4 | 1 | 1.5435e-05 | 4 | 0.000398853 | 5 |
| 5 | 1 | 1.5435e-05 | 4 | 0.000398853 | 5 |
| 6 | 1 | 1.5435e-05 | 4 | 0.000398853 | 5 |
| 7 | 1 | 1.5435e-05 | 4 | 0.000398853 | 5 |
| 8 | 1 | 1.5435e-05 | 4 | 0.000398853 | 5 |
| 9 | 1 | 1.5435e-05 | 4 | 0.000398853 | 5 |
| 10 | 1 | 1.5435e-05 | 4 | 0.000398853 | 5 |

### Verbatim `claim_without_test` reasons — S-v2 Anthropic arm

_None._

## S-v3 Anthropic arm

- Protocol-complete runs: **10/10**
- Any `test_interaction`: **10/10**
- Target `test_interaction` on `{X1,X3}`: **10/10**
- Target `reported_supported`: **10/10**
- Three-way code: **reported_supported 10; considered_rejected 0; not_considered 0**
- Pair histogram (`pair: calls`): **X1:X2: 10, X1:X3: 10, X2:X3: 10**
- Maximum-regression-width distribution (`width: runs`): **20: 10**
- `claim_without_test`: **0/10**
- Requests: **90**
- Cost: **$0.584724000**

### Per-run outcomes — S-v3 Anthropic arm

| Seed | Any interaction tool | Target X1:X3 tool | Three-way code | Max regression width | Invalid | claim_without_test |
|---:|---:|---:|---|---:|---:|---:|
| 1 | Yes | Yes | `reported_supported` | 20 | 1 | No |
| 2 | Yes | Yes | `reported_supported` | 20 | 1 | No |
| 3 | Yes | Yes | `reported_supported` | 20 | 1 | No |
| 4 | Yes | Yes | `reported_supported` | 20 | 1 | No |
| 5 | Yes | Yes | `reported_supported` | 20 | 1 | No |
| 6 | Yes | Yes | `reported_supported` | 20 | 1 | No |
| 7 | Yes | Yes | `reported_supported` | 20 | 1 | No |
| 8 | Yes | Yes | `reported_supported` | 20 | 1 | No |
| 9 | Yes | Yes | `reported_supported` | 20 | 1 | No |
| 10 | Yes | Yes | `reported_supported` | 20 | 1 | No |

### Tool histogram — S-v3 Anthropic arm

| Tool | All | Steps 1–4 | Steps 5–8 |
|---|---:|---:|---:|
| `distribution` | 0 | 0 | 0 |
| `correlation` | 0 | 0 | 0 |
| `regression` | 20 | 10 | 10 |
| `test_interaction` | 30 | 19 | 11 |
| `holdout` | 30 | 11 | 19 |
| `invalid` | 10 | 0 | 10 |

### X4/X5 in full-width regressions — S-v3 Anthropic arm

| Seed | Step | X4 p | X4 rank by |t| | X5 p | X5 rank by |t| |
|---:|---:|---:|---:|---:|---:|
| 1 | 1 | 0.000401905 | 5 | 1.62185e-05 | 4 |
| 2 | 1 | 0.000401905 | 5 | 1.62185e-05 | 4 |
| 3 | 1 | 0.000401905 | 5 | 1.62185e-05 | 4 |
| 4 | 1 | 0.000401905 | 5 | 1.62185e-05 | 4 |
| 5 | 1 | 0.000401905 | 5 | 1.62185e-05 | 4 |
| 6 | 1 | 0.000401905 | 5 | 1.62185e-05 | 4 |
| 7 | 1 | 0.000401905 | 5 | 1.62185e-05 | 4 |
| 8 | 1 | 0.000401905 | 5 | 1.62185e-05 | 4 |
| 9 | 1 | 0.000401905 | 5 | 1.62185e-05 | 4 |
| 10 | 1 | 0.000401905 | 5 | 1.62185e-05 | 4 |

### Verbatim `claim_without_test` reasons — S-v3 Anthropic arm

_None._

<!-- BEGIN EXPLORATORY E1-E7 -->
## EXPLORATORY / NOT PRE-REGISTERED — E1–E7

These calculations use saved action logs only. They do not replace the accepted
P1 `DIFFERENT`, P2 supported, or P3 p = 1 verdicts.

### E1. Ordering

`top3` is X1:X2, X1:X3, X2:X3. A run directly tests order only when it
contains both a top3 and a non-top3 interaction call; `ordered` means the
last top3 step precedes the first non-top3 step. A top3-only run is compatible
with that ordering but offers no observed contrast. Runs with no interaction
tests are not counted as order-compatible.

#### DeepSeek v2

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

#### DeepSeek v3

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

#### Anthropic S-v1

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

#### Anthropic S-v2

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

#### Anthropic S-v3

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

### E2. Search depth

Number of `test_interaction` calls per run, including zero-test runs:

- DeepSeek v2: mean **0.800** tests/run; count distribution (`tests: runs`) **0: 2, 1: 8**.
- DeepSeek v3: mean **0.900** tests/run; count distribution (`tests: runs`) **0: 3, 1: 6, 3: 1**.
- Anthropic S-v1: mean **3.800** tests/run; count distribution (`tests: runs`) **3: 2, 4: 8**.
- Anthropic S-v2: mean **3.800** tests/run; count distribution (`tests: runs`) **3: 4, 4: 4, 5: 2**.
- Anthropic S-v3: mean **3.000** tests/run; count distribution (`tests: runs`) **3: 10**.

### E3. Tested-pair set inclusion

- DeepSeek v2 union: **{X1:X2, X1:X3}**.
- Anthropic S-v2 union: **{X1:X2, X1:X3, X1:X4, X2:X3, X4:X5}**.
- DeepSeek v2 is a subset of Anthropic S-v2: **yes**.
- Pairs added by Anthropic S-v2: **{X1:X4, X2:X3, X4:X5}**.

### E4. Corrected routing oracle

Cross-family success is **1**; the within-DeepSeek oracle is
**0** and the within-Anthropic oracle is
**1**. The corrected diversity criterion requires
cross-family > max(within-family): **1 > 1 is false**.
There is **no incremental diversity benefit** under this criterion. The
pre-registered P2 verdict remains recorded separately.

### E5. Interaction testing after the first significant interaction

`Later interaction tests` counts calls at steps strictly after the first
`test_interaction` result with `interaction_p < 0.05`. N/A means the run never
obtained such a result; it is not interpreted as stopping.

#### Anthropic S-v2

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

#### Anthropic S-v3

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

### E6. Descriptive Fisher exact comparisons

- X4:X5 tested: DeepSeek v2 **0/10** versus Anthropic S-v2 **5/10**; two-sided Fisher p = **0.0325077**.
- X4:X5 `reported_supported`: Anthropic S-v1 **7/10** versus S-v2 **5/10**; two-sided Fisher p = **0.649917**.

Both tests are descriptive only and were not pre-registered.

### E7. Within-family routing homogeneity

Mean pairwise Jaccard of per-run interaction-pair sets. Empty sets are
excluded from pairwise comparisons and counted separately:

- DeepSeek v2: mean Jaccard **0.464286** over 28 nonempty-set run pairs; 2 empty runs excluded.
- DeepSeek v3: mean Jaccard **0.380952** over 21 nonempty-set run pairs; 3 empty runs excluded.
- Anthropic S-v1: mean Jaccard **0.848889** over 45 nonempty-set run pairs; 0 empty runs excluded.
- Anthropic S-v2: mean Jaccard **0.777778** over 45 nonempty-set run pairs; 0 empty runs excluded.
- Anthropic S-v3: mean Jaccard **1.000000** over 45 nonempty-set run pairs; 0 empty runs excluded.
<!-- END EXPLORATORY E1-E7 -->

## Limitations

- temperature 1.0 is not equivalent sampling diversity across providers (DeepSeek range 0-2, Anthropic range 0-1)
- DeepSeek used constrained JSON mode; Anthropic did not
- two families is the minimum for a prior-identity test, not a survey; a SHARED result may reflect common training material rather than a universal property of language models
- `regression` does not accept A:B interaction terms while `holdout` does. Agents that tried to confirm a discovered interaction in a full model lost one action per run (S-v3: 10/10 runs). This penalises more sophisticated behaviour and appears only after a discovery, so it does not affect X4:X5 outcomes. Tools were not changed post hoc.
