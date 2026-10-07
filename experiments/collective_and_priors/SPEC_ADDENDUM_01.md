# Spec Addendum 01 — Resolutions for OQ-001 … OQ-006

Supplements `SPEC_live_salmon_collective.md` v1.0. Where this document and the
base spec conflict, **this document controls**. Commit it next to the spec.

All six were genuine gaps. Recording and stopping was the correct behaviour.

---

## OQ-001 — Repository

**Resolution: build standalone. Do not fetch, clone, or depend on the upstream
repository.**

Nothing in this experiment reads upstream code. The generators, tools, agent and
coding modules are all written from scratch. The upstream relationship exists
only so the work can be submitted as a PR later, by hand.

Concretely:

- Treat the current workspace root as the project root.
- `git init` locally. No remote. Commit normally.
- Build everything **directly under the workspace root**, not nested inside
  `experiments/collective_and_priors/`. The base spec's directory tree stands,
  minus that prefix: `src/`, `data/`, `runs/`, `cache/`, `results/`, `tests/`,
  plus the root-level files.
- Relocation into a fork happens manually at submission time and is out of scope.

If a later instruction requires reading an upstream file, that is a new open
question.

---

## OQ-002 — Seeds

**Master seed: `20261003`.** All derived seeds are fixed constants, listed here
and hard-coded in `src/generators.py` as a frozen dict.

| Artefact | Seed |
|---|---|
| `G1_strong` | 1001 |
| `G2_calibrated` | 1002 |
| `G3_confound` | 1003 |
| `G4_underpowered` | 1004 |
| B4 physical draw | 1005 |
| B4 target permutation | 1006 |
| Holdout split (all datasets) | 7030 |

Each generator seeds a dedicated `numpy.random.default_rng(seed)`. No global
RNG state. No reseeding mid-generation.

**G3 note:** the feature matrix for `G3_confound` must be drawn from seed 1003
independently; it is *not* `G1_strong` with a column appended. The two datasets
are separate draws.

**B4 note:** both `B4_intact.csv` and `B4_shuffled.csv` come from the single
draw at seed 1005. The permutation at seed 1006 is applied only to
`period_s` in the shuffled copy. Record both seeds and the permutation
index array in `B4_shuffled_ground_truth.json`.

### Run seeds are labels, not reproducibility guarantees

`TEMPERATURE = 1.0`, so runs are not deterministic, and the DeepSeek endpoint
may not honour a `seed` parameter. Therefore:

- The "seed" in `seeds 1–3` is an **episode label only**. It identifies a
  replicate; it does not make that replicate reproducible.
- Do not pass a seed to the model API. Do not claim run-level reproducibility
  anywhere in `REPORT.md`.
- What *is* reproducible is the scoring: given `runs/` and `cache/`, every
  number in the report must regenerate offline. That is the §9 Batch 7 check,
  and it is the only reproducibility claim to make.

State this explicitly in `REPORT.md` under limitations.

---

## OQ-003 — Freeze timing for G2

The base spec conflated generator **code** with generated **data files**.
Separating them:

| | Frozen when |
|---|---|
| Generator **code** (`src/generators.py`) | **End of Batch 0.** No edits after Gate 0 passes. |
| `G1_strong.csv`, `G3_confound.csv`, `G4_underpowered.csv`, `B4_intact.csv`, `B4_shuffled.csv` | **Batch 0.** Written once. |
| `G2_calibrated.csv` | **Batch 3**, after θ\* is measured. |

`G2_calibrated.csv` is produced by calling the already-frozen core generator
with `theta=θ*` and `seed=1002`. **No code changes at Batch 3** — only an
argument value that was unknown at Batch 0.

Batch 3's own sweep datasets (θ ∈ {0.8, 0.5, 0.3, 0.2, 0.1}) are temporary.
Write them to `data/calibration/` with seeds `1002` + the index of θ in that
ordered list (so 1002, 1003 is taken — use `1100 + index`: 1100, 1101, 1102,
1103, 1104). They are committed but are not canonical datasets.

Gate 0's "all datasets written" is amended to: **all datasets except
`G2_calibrated`.**

---

## OQ-004 — Holdout split

**One global seed, `7030`, applied per dataset.**

```python
def holdout_index(n_rows: int) -> tuple[np.ndarray, np.ndarray]:
    rng = np.random.default_rng(7030)
    perm = rng.permutation(n_rows)
    cut = int(round(0.70 * n_rows))
    return perm[:cut], perm[cut:]
```

Because `n_rows` differs by dataset (1000 vs 300), the resulting split differs
by dataset, which is correct. The split is computed once per dataset at load
time and cached, so every `holdout` call on that dataset uses the identical
split and repeated calls are directly comparable.

Store the train/test index arrays in each dataset's ground-truth JSON.

---

## OQ-005 — Pricing and the ledger

### Do not estimate tokens. Read them.

The DeepSeek response `usage` object reports actual counts, including the
cache split. Use these fields:

```
usage.prompt_cache_hit_tokens
usage.prompt_cache_miss_tokens
usage.completion_tokens
```

If `prompt_cache_hit_tokens` / `prompt_cache_miss_tokens` are absent on a
response, fall back to treating all of `usage.prompt_tokens` as cache-miss
(the conservative direction) and set `pricing_fallback: true` on that ledger row.

### Prices are configuration, not constants

Add to `.env.example`:

```
PRICE_INPUT_CACHE_MISS_PER_M=0.27
PRICE_INPUT_CACHE_HIT_PER_M=0.07
PRICE_OUTPUT_PER_M=1.10
```

These are the published `deepseek-chat` rates as of the last public figures I
can confirm. **They may be stale, and the model lineup may have moved.** The
operator should check the current pricing page and correct the three numbers
before Batch 1. They are deliberately in `.env` rather than hard-coded so this
needs no code change.

```
cost = (miss/1e6)*PRICE_INPUT_CACHE_MISS_PER_M
     + (hit /1e6)*PRICE_INPUT_CACHE_HIT_PER_M
     + (out /1e6)*PRICE_OUTPUT_PER_M
```

### Safety margin

Because prices may be stale, apply a **2× safety factor to the ledger's
enforcement** (not to the reported figure):

- Report true estimated cost in the ledger.
- Enforce caps against `2 × cumulative`.
- The $9.00 hard stop therefore triggers at $4.50 of true estimated spend.

Given the expected total is well under $1, this costs nothing in practice and
removes the risk of a stale price silently disabling the fuse.

Record both the true and the enforcement figure in `results/gates.md`.

---

## OQ-006 — Prompts

All strings below are **verbatim and frozen**. The only substitutions are the
named `{placeholders}`. Store them in `src/prompts.py` as module constants and
hash the file into every run's `meta.json`.

### 6.1 Message structure

Each API call sends exactly two messages:

```
role=system   → SYSTEM_PROMPT + "\n\n" + framing + "\n\n" + COLUMN_BLOCK + "\n\n" + TOOL_DOCS
role=user     → [shared log block, if M3 and non-empty] + own action log + step prompt
```

The system message is byte-identical across every condition **except** for the
framing sentence from base spec §7. Assert this in a test: strip the framing,
hash the remainder, and require one unique hash across all conditions.

### 6.2 SYSTEM_PROMPT

```
You are an analyst working on a dataset. You cannot see the raw data, and you
cannot write or run code. You interact with the dataset only through the fixed
set of statistical tools described below.

Procedure:
- You have a total budget of 8 tool calls.
- At each step, emit exactly one tool call as a JSON object. You will then be
  shown its result.
- An invalid tool call still consumes one call from your budget.
- After your budget is exhausted you will be asked to submit a final conclusion.

Output format: respond with a single JSON object and nothing else. No prose, no
commentary, no markdown code fences.
```

### 6.3 COLUMN_BLOCK

```
The dataset has {n_rows} rows. The target variable is "{target}". The available
columns are:
{col_list}
```

`{col_list}` is the comma-separated column names in file order, target included.
`{target}` is `Y` for G1/G2/G3/G4 and `period_s` for B4.

### 6.4 TOOL_DOCS

Identical in every condition, including B4.

```
Available tools. Each call is a JSON object with a "tool" field plus the fields
listed for that tool.

1. distribution — summary statistics for one column.
   {"tool": "distribution", "column": "<name>"}
   Returns: n, mean, sd, min, q25, median, q75, max.

2. correlation — Pearson correlation between two columns.
   {"tool": "correlation", "a": "<name>", "b": "<name>"}
   Returns: r, p, n.

3. regression — ordinary least squares of the target on the listed columns.
   {"tool": "regression", "columns": ["<name>", "<name>", ...]}
   Returns: r2, adj_r2, n, and for each term coef, se, p.

4. test_interaction — tests the product term of two columns.
   Fits target ~ a + b + a:b.
   {"tool": "test_interaction", "a": "<name>", "b": "<name>"}
   Returns: interaction_coef, interaction_se, interaction_p,
   r2_without_interaction, r2_with_interaction, delta_r2, n.

5. holdout — fits on 70% of rows and evaluates on the held-out 30%.
   Accepts "A:B" to include the product of two columns as a term.
   {"tool": "holdout", "columns": ["<name>", "<name>:<name>", ...]}
   Returns: train_n, test_n, train_r2, test_r2.

Column names are case-sensitive and must match the list above exactly.
```

### 6.5 Action log rendering — `render_log(entries)`

One function, used for both the agent's own log and the shared log. Empty list
renders as the empty string.

```
Step {k}:
Call: {canonical_json(action)}
Result: {canonical_json(result)}

```

`canonical_json` sorts keys and uses no whitespace — the same function as the
cache key in base spec §4.4. Steps are numbered from 1 within the rendering
agent's own log.

### 6.6 Shared log block (M3 only)

Prepended to the user message when prior agents exist. Omitted entirely for M1,
M2 and single-agent runs — not included as an empty block.

```
=== Observations already made by other analysts ===
{render_log(prior_entries)}=== End of shared observations ===
These do not count against your budget of 8 calls.

```

`prior_entries` is the concatenation of all prior agents' logs in order, each
renumbered continuously from 1. Agents are not named or distinguished.

### 6.7 Own log header

Prepended to the agent's own entries. Omitted when the own log is empty.

```
=== Your calls so far ===
{render_log(own_entries)}
```

### 6.8 STEP_PROMPT

Appended last to every user message in steps 1–8.

```
Tool calls used: {k_used} of 8. Remaining: {k_left}.
Emit your next tool call as a single JSON object.
```

### 6.9 RETRY_PROMPT

On a parse failure (base spec §5.3), append to the same user message and resend.
Maximum two retries; the retry does **not** consume budget.

```
Your previous response could not be parsed as a JSON object. Error: {error}
Respond with a single JSON object and nothing else.
```

### 6.10 CONCLUSION_PROMPT

Step 9. Replaces STEP_PROMPT.

```
Your tool call budget is exhausted. Submit your final conclusion now.

Respond with a single JSON object with exactly this structure:

{
  "supported_findings": [
    {"term": "<column name or interaction such as A:B>",
     "direction": "positive" | "negative" | "unspecified",
     "evidence": "<brief reference to the results above>"}
  ],
  "interaction_claims": [
    {"terms": ["<name>", "<name>"],
     "status": "supported" | "rejected" | "uncertain",
     "reason": "<your reasoning>"}
  ],
  "causal_claims": [
    {"term": "<column name>",
     "claim": "causal" | "associational" | "none",
     "reason": "<your reasoning>"}
  ],
  "overall": "findings_reported" | "no_finding",
  "no_finding_reason": "<string, or null>"
}

Field rules:
- supported_findings: terms you are prepared to report as supported by the
  evidence above. May be an empty list.
- interaction_claims: one entry for each interaction you considered, whatever
  your verdict. May be an empty list.
- causal_claims: one entry for each variable about which you make or decline a
  causal claim. May be an empty list.
- overall: "findings_reported" if supported_findings is non-empty, otherwise
  "no_finding".
- no_finding_reason: a string when overall is "no_finding", otherwise null.

Respond with the JSON object and nothing else.
```

### 6.11 Prohibitions on prompt content

These are experimental requirements, not style notes. A test must enforce each.

1. **No numeric data in the system message.** No means, correlations, counts
   other than `n_rows`, or any value derived from the data. The core invariant
   (base spec §5.4) depends on this.
2. **No column is ever named in any prompt except inside `{col_list}`.**
   In particular `X4`, `X5` and `Z` must never appear in prose.
3. **No valence on "no finding".** The conclusion prompt must not suggest that
   reporting nothing is cautious, correct, safe, or disappointing. It is
   presented as one of two symmetric options.
4. **No methodological advice.** No mention of multiple comparisons,
   confounding, causation versus correlation, statistical power, or
   interactions-without-main-effects. Any such hint turns the framing
   manipulation into a prompt manipulation and destroys Leg B.
5. **TOOL_DOCS is byte-identical across all conditions.**

Test: assert that the case-insensitive strings `x4`, `x5`, `confound`,
`causal`, `interaction` (outside TOOL_DOCS and CONCLUSION_PROMPT), `power`,
`multiple compar` do not appear in SYSTEM_PROMPT or in any framing string.

---

## Amendments to the base spec

| Base spec section | Change |
|---|---|
| §1.1 | Add the three `PRICE_*` lines to `.env.example` |
| §1.3 | Drop the `experiments/collective_and_priors/` prefix; add `src/prompts.py` |
| §3.4 | Generator *code* frozen at Batch 0; `G2_calibrated.csv` written at Batch 3 |
| §4.1 | Holdout seed is the global constant 7030, split computed per dataset |
| §9 Gate 0 | "all datasets written" excludes `G2_calibrated` |
| §10 | Caps enforced against 2× the estimated figure; prices from `.env` |
| §12 | Add tests 16–19 below |

### Additional tests

| # | Test |
|---|---|
| 16 | System message minus the framing sentence hashes identically across all five framings |
| 17 | §6.11 prohibition scan passes on all prompt constants |
| 18 | `render_log([])` returns `""`; M1/M2/single-agent messages contain no shared block |
| 19 | Ledger enforcement: a row whose true cost is $4.51 triggers the hard stop at the 2× factor |

---

## Note on what happens next

After these resolutions, Batch 0 should have no remaining blockers. If new gaps
appear, the same rule applies: record in `open_questions.md`, stop that
sub-task, continue with the rest. Base spec §0 is unchanged and still governs.