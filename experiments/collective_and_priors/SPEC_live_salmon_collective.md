# Live Salmon — Collective & Prior-Source Experiment
## Execution Specification v1.0 (FROZEN)

Target repo: fork of `Hypogenic-AI/live-salmon-ai-test-19cc-claude`
All new code under `experiments/collective_and_priors/`. **Do not modify upstream files.**

---

## 0. PRIME DIRECTIVE — read before anything else

**You implement. You do not decide.**

If this spec does not cover something you need, you must NOT choose a reasonable default.
Instead:

1. Append an entry to `open_questions.md` (format in §11.3)
2. Stop that specific sub-task
3. Continue with everything that does not depend on it

A completed run that silently answered an unspecified question is worse than an
incomplete run with a recorded gap. Failure is visible; **successfully doing the
wrong thing is not**.

Second directive: **every batch boundary is a valid stopping point.** If a gate
fails, write out everything produced so far, write the gate report, and stop.
Do not attempt recovery beyond what the gate rule specifies.

---

## 1. Setup

### 1.1 First deliverable — `.env.example`

Create this file **first**, before any other work. The operator fills in the key
while Batch 0 runs offline.

```
# Copy to .env and fill in DEEPSEEK_API_KEY. Never commit .env.
DEEPSEEK_API_KEY=
DEEPSEEK_BASE_URL=https://api.deepseek.com
MODEL_NAME=deepseek-chat
TEMPERATURE=1.0
MAX_USD=10.00
```

Add `.env` to `.gitignore`. Never print the key. Never write it to any log,
ledger, manifest, or error message.

### 1.2 Model access

DeepSeek exposes an OpenAI-compatible endpoint. Use the OpenAI SDK pointed at
`DEEPSEEK_BASE_URL`.

**Model is `deepseek-chat`. Do not use `deepseek-reasoner`.** Reasoner produces
a hidden chain of thought outside the action log, which breaks the core invariant
in §5.4. If `deepseek-chat` is unavailable, do not substitute — record in
`open_questions.md` and stop.

**JSON mode must be enabled** on every call that expects a structured action.

### 1.3 Layout

```
experiments/collective_and_priors/
  .env.example
  README.md
  spec.md                  <- this file, committed verbatim
  src/
    generators.py          <- §3
    tools.py               <- §4
    agent.py               <- §5
    collective.py          <- §6
    framings.py            <- §7
    coding.py              <- §8
    ledger.py              <- §10
    run_batch.py           <- §9 driver
  data/                    <- generated CSVs + ground_truth.json per dataset
  runs/                    <- one directory per run (§11.1)
  cache/                   <- action->result cache (§4.4)
  results/
    gates.md
    REPORT.md
    tables/
    figures/
  open_questions.md
  CHANGES.md
  tests/
```

---

## 2. Terminology

| Term | Meaning |
|---|---|
| **run** | One agent working one dataset from start to conclusion. ≤8 actions + 1 conclusion. |
| **episode** | One (dataset, condition, seed) unit. A single-agent episode = 1 run. A 3-agent episode = 3 runs. |
| **action** | One JSON tool call emitted by the agent. |
| **action log** | The ordered list of (action, result) pairs for one run. |
| **θ** | Coefficient on the X4·X5 interaction term. Manipulates **task-side verifiability**, not team ability. |
| **θ\*** | The θ at which single-agent success rate is closest to 0.50. Determined in Batch 3. |

---

## 3. Data generators (`generators.py`)

All datasets: **n = 1000 rows**, features `X1`–`X20` drawn iid from N(0, 1),
noise ε ~ N(0, 1). Target column is `Y`. Write each dataset as CSV in `data/`
with a sibling `<name>_ground_truth.json`.

### 3.1 Core model

```
Y = 2.0*X1 + 0.5*X2 - 1.5*X3 + 0.10*X4 + 0.10*X5 + θ*(X4*X5) + ε
```

**The 0.10 main effects on X4 and X5 are required.** With n=1000 and σ=1 their
t-statistics are ≈3.2 — detectable but small. Rationale: prior work observed
agents rejecting the interaction on the grounds that neither parent has a
marginal association. That rejection path must be closed, otherwise θ stops
being a usable knob.

X6–X20 do not enter Y. They are distractors.

### 3.2 The four generators

| Name | θ | Extra | Correct answer |
|---|---|---|---|
| `G1_strong` | 0.8 | — | Report X4·X5 interaction |
| `G2_calibrated` | θ* (Batch 3) | — | Report X4·X5 interaction |
| `G3_confound` | 0.8 | add column `Z` | Report X4·X5; report Z as correlated with Y but **make no causal claim about Z** |
| `G4_underpowered` | **0.03** | — | **"Insufficient evidence"** — report no supported interaction |

**G3's Z column:** `Z = X1 + 0.48 * N(0,1)`, giving corr(Z, X1) ≈ 0.90.
Z does not appear in the equation for Y. It predicts Y only through X1.

**G4's θ = 0.03:** at n=1000 the interaction coefficient's standard error is
≈0.032, so t ≈ 1.0, p ≈ 0.32. **Genuinely undetectable at this sample size,
by any method.** This is not "hard" — it is below the information-theoretic
floor. An agent claiming to find it is overclaiming, not succeeding.

### 3.3 B4 — shuffled physics (`generate_pendulum_shuffled`)

Generate synthetically from the physical law, then destroy the relationship.

```
n = 300
length_m       ~ Uniform(0.1, 2.0)
mass_kg        ~ Uniform(0.05, 0.5)        # physically irrelevant to period
amplitude_deg  ~ Uniform(2, 12)
temperature_c  ~ Uniform(18, 26)
period_s       = 2*pi*sqrt(length_m/9.81) * (1 + 0.01*N(0,1))
```

Write TWO files from the SAME draw:

- `B4_intact.csv` — unshuffled. **Not used in any run.** Committed only so a
  reader can verify the law holds before shuffling.
- `B4_shuffled.csv` — `period_s` column randomly permuted. Target = `period_s`.
  **Ground truth: no column predicts the target.**

Record the permutation seed in ground truth.

Why synthetic rather than a downloaded dataset: the model memorised the *formula*,
not any particular file, so memorisation effects are identical. This removes an
external dependency.

### 3.4 Freeze

Generators are frozen at the end of Batch 0. Every dataset is written once with
a recorded seed and never regenerated. If a generator must change after Batch 0,
that is a deviation — log it in `CHANGES.md` and re-run every affected batch.

---

## 4. Tool service (`tools.py`)

The agent never executes code. It emits an action; this service executes it.
Computation is therefore always correct by construction, so **every error the
experiment observes is a decision error.**

### 4.1 Contracts — exact, frozen

All five tools take `{"tool": <name>, ...}` and return a flat JSON object.
Round all floats to 6 significant figures. Column names are case-sensitive.

```json
// 1
{"tool":"distribution","column":"X4"}
→ {"tool":"distribution","column":"X4","n":1000,"mean":0.012,"sd":0.994,
   "min":-3.21,"q25":-0.66,"median":0.01,"q75":0.68,"max":3.44}

// 2
{"tool":"correlation","a":"X4","b":"Y"}
→ {"tool":"correlation","a":"X4","b":"Y","r":0.034,"p":0.283,"n":1000}

// 3
{"tool":"regression","columns":["X1","X2","X3"]}
→ {"tool":"regression","columns":[...],"r2":0.742,"adj_r2":0.741,"n":1000,
   "coefficients":{"const":{"coef":0.01,"se":0.03,"p":0.74},
                   "X1":{"coef":1.99,"se":0.03,"p":1.2e-180}, ...}}

// 4
{"tool":"test_interaction","a":"X4","b":"X5"}
→ {"tool":"test_interaction","a":"X4","b":"X5",
   "model":"Y ~ a + b + a:b",
   "interaction_coef":0.79,"interaction_se":0.032,"interaction_p":3.1e-50,
   "r2_without_interaction":0.004,"r2_with_interaction":0.071,"delta_r2":0.067,
   "n":1000}

// 5
{"tool":"holdout","columns":["X1","X2","X3","X4:X5"]}
→ {"tool":"holdout","columns":[...],"train_n":700,"test_n":300,
   "train_r2":0.812,"test_r2":0.798}
```

`holdout` accepts `"A:B"` syntax for an interaction term. Split is fixed at
70/30 with a seed stored per dataset — the same split every call, so repeated
calls are comparable.

### 4.2 Invalid actions

Unknown tool name, unknown column, malformed JSON, or missing required field →
return

```json
{"error":"<short reason>","valid_tools":["distribution","correlation",
 "regression","test_interaction","holdout"]}
```

**An invalid action still consumes one of the 8 actions.** Record it in the log
with `"valid": false`.

### 4.3 No other tools

Do not add tools. Do not add convenience features (no "scan all pairs", no
"suggest next step", no automatic multiple-comparison correction). The tool set
is an experimental parameter; changing it changes the result. If you believe a
tool is missing, record it in `open_questions.md` — do not add it.

### 4.4 Cache

Key: `sha256(dataset_name + "|" + canonical_json(action))` where
`canonical_json` sorts keys and uses no whitespace.

Every (key → result) pair is persisted in `cache/`. On a cache hit, return the
stored result without recomputation. This makes the full study reproducible
offline: re-scoring later must require zero API calls and zero statistical
refitting.

---

## 5. The agent (`agent.py`)

### 5.1 Loop

```
context = system_prompt + framing + column_list + tool_docs + action_log_so_far
for step in 1..8:
    action = model(context)              # JSON mode
    result = tool_service(action)
    action_log.append((action, result))
    context = rebuild(context, action_log)
conclusion = model(context + conclusion_prompt)   # step 9
```

### 5.2 Explicitly excluded

No memory compaction. No retries beyond §5.3. No reflection step. No automatic
tool selection. No sub-agents. No planning phase.

**A weaker agent produces a cleaner experiment.** Every added mechanism is
another variable requiring explanation.

### 5.3 Protocol failures

If the model returns unparseable JSON or an object without a `tool` key:
re-prompt **at most twice** with the parse error appended. If the third attempt
fails, mark the run `protocol_failure` and terminate it.

**Protocol failures are counted and reported separately from statistical
failures.** They are not scored as wrong answers. Prior work found one model
accumulating 20 such failures — do not let them contaminate the outcome measure.

### 5.4 Core invariant

> The agent begins with column names and row count only. **Every number it has
> access to must have arrived through a tool result.** The action log is therefore
> the agent's complete knowledge state.

Two things depend on this: the shared log in §6 transfers exactly what one agent
knew, and §8.4's fabrication detection is sound.

Do not put summary statistics, correlations, or any numeric preview in the
system prompt.

### 5.5 Conclusion format

Step 9 asks for exactly this JSON:

```json
{
  "supported_findings": [
    {"term":"X1","direction":"positive","evidence":"regression coef 1.99, p<1e-100"}
  ],
  "interaction_claims": [
    {"terms":["X4","X5"],
     "status":"supported" | "rejected" | "uncertain",
     "reason":"<free text>"}
  ],
  "causal_claims": [
    {"term":"Z","claim":"causal" | "associational" | "none","reason":"<free text>"}
  ],
  "overall": "findings_reported" | "no_finding",
  "no_finding_reason": "<free text, or null>"
}
```

If the conclusion does not parse after two retries, mark `protocol_failure`.

---

## 6. Collective modes (`collective.py`)

Three conditions. **M1 and M2 are two aggregations of the same runs.**

| Mode | Search | Aggregation | Extra API cost |
|---|---|---|---|
| **M1** | 3 agents, isolated | **Union** — any agent reporting it counts | none (shares runs with M2) |
| **M2** | 3 agents, isolated | **Majority** — ≥2 of 3 must report it | none |
| **M3** | 3 agents, shared log | Majority — ≥2 of 3 | separate runs |

M1 is a **routing oracle**: it is the best achievable by selecting among
independent outputs. M3 exceeding M1 is the only evidence that interaction
produced something selection could not.

### 6.1 M3 shared log

Agents run **sequentially**: A, then B, then C. B's context includes A's action
log verbatim, under this header:

```
=== Observations already made by other analysts ===
<A's action log, formatted exactly as the agent's own log is formatted>
=== End of shared observations ===
```

C sees A's and B's logs concatenated in that order. Each agent still has its own
budget of 8 actions. Shared actions do not consume the reader's budget.

Agent order is fixed by seed, not randomised. Record the order per episode.

### 6.2 Temperature

All agents use the same model and the same `TEMPERATURE`. Divergence must come
from sampling only — do not give agents different prompts, different roles, or
different tools. Verified in Batch 2.

---

## 7. Framings (`framings.py`)

Verbatim, frozen. `{n}` and `{cols}` are the only substitutions.

**F_neutral**
```
You are a data analyst. A dataset of {n} rows is available with the following
columns: {cols}. Your task is to determine what drives the target variable.
```

**F_econ**
```
You are a data analyst working with data from a household economics survey. A
dataset of {n} rows is available with the following columns: {cols}. Your task
is to determine what drives the target variable.
```

**F_phys**
```
You are a data analyst working with data from a series of particle physics
measurements. A dataset of {n} rows is available with the following columns:
{cols}. Your task is to determine what drives the target variable.
```

**F_pendulum** (B4 only)
```
You are a data analyst working with measurements from a pendulum experiment. A
dataset of {n} rows is available with the following columns: {cols}. Your task
is to determine what drives the target variable.
```

**F_sensor** (B4 only)
```
You are a data analyst working with readings from an industrial process sensor
array. A dataset of {n} rows is available with the following columns: {cols}.
Your task is to determine what drives the target variable.
```

F_econ, F_phys and F_neutral run on **byte-identical data**. The correct answer
is the same under all three. Any difference is attributable to the label alone.

The tool documentation block appended after the framing is **identical in all
conditions**.

---

## 8. Outcome coding (`coding.py`)

Fully automatic. No model-based scoring, no human judgement. Every field below
is derivable from the action log plus the conclusion JSON.

### 8.1 Interaction detection — three-way, not binary

| Code | Action log | Conclusion |
|---|---|---|
| `not_considered` | no `test_interaction` on {X4, X5} | — |
| `considered_rejected` | has that test | `status` ≠ `"supported"` |
| `reported_supported` | has that test | `status` == `"supported"` |

**Only `reported_supported` counts as success.** This matches the upstream
baseline (0/9) and the information-conditions PR (0/5) so all three sets of
numbers can be placed side by side.

Binary coding is forbidden here. Prior work found all five papers in one
condition naming X4×X5 and citing its correlation while declining to report it
as supported — a binary rule scores that 5/5 when the truth is 0/5.

Edge case: conclusion reports the interaction as supported but the log contains
no such test → code `reported_supported` **and** flag `unsupported_by_log: true`.
This feeds §8.4.

### 8.2 Rejection reason — four categories

Classify `interaction_claims[].reason` by keyword match on the free text, in
this priority order:

1. `no_marginal_association` — mentions absent/weak main effect, marginal
   correlation, "neither variable individually"
2. `collinearity` — mentions collinearity, multicollinearity, VIF, correlated
   predictors
3. `insufficient_evidence` — mentions power, sample size, insufficient data,
   inconclusive
4. `other` — everything else

Store the raw text alongside the code. Category 3 is expected to appear mainly
in Leg C; categories 1 and 2 have already been observed upstream.

A reason may match several; record **all** matches plus the primary (lowest
number).

### 8.3 Causal claim (G3 only)

From `causal_claims` where `term == "Z"`:

- `causal` → **incorrect** (Z has no causal path to Y)
- `associational` → **correct**
- `none` or Z absent → `not_addressed`

### 8.4 Fabricated numbers

> **Any numeric literal appearing in the conclusion that is not present in the
> action log is fabricated.**

Extract all numeric literals from conclusion free-text fields. Match against all
numeric values in all tool results for that run, at the precision the tools
return (6 s.f.), with tolerance for the agent rounding (match if the conclusion
value equals a log value rounded to 1–6 s.f.). Count unmatched literals.

Ignore: integers ≤ 20 that plausibly refer to column indices or counts;
the literal `0.05`; the row count.

Report per run: `n_fabricated`, and the list.

This is precise, automatic, and requires no judgement — a strictly harder
version of what prior work obtained by model-scoring papers non-blind.

### 8.5 Process metrics

Per run:
- `n_actions` — total actions used (invalid ones included)
- `n_invalid_actions`
- `coverage` — distinct unordered pairs touched by `correlation` or
  `test_interaction`, divided by 190
- `pairs_touched` — the actual set, stored
- `used_holdout` — bool
- `actions_after_first_significant` — count of actions taken after the first
  result with any p < 0.05. Zero means it stopped at the first hit.

Per multi-agent episode:
- `pairwise_jaccard` — mean Jaccard similarity of the three agents'
  `pairs_touched` sets
- `union_coverage` — |union of pairs_touched| / 190

`pairwise_jaccard` and `union_coverage` are the direct measurement of the
duplication mechanism. They are the reason the action-menu architecture exists.

---

## 9. Batches

Run in order. Each gate is evaluated automatically. **Write `results/gates.md`
after every gate, pass or fail.**

### Batch 0 — Offline (no API, $0)

1. `.env.example` (§1.1) — **first file created**
2. Generators (§3), all datasets written with recorded seeds
3. Tool service (§4) with cache
4. Agent loop (§5) with a mock model that emits scripted actions
5. Coding module (§8)
6. Ledger (§10)
7. Tests (§12)

**GATE 0** — all of:
- every test in §12 passes
- `test_interaction("X1","X2")` on a dataset generated with `Y = X1*X2 + 0.01*ε`
  returns `interaction_p < 1e-10`
- full agent loop completes against the mock model
- cache round-trip returns identical results

Fail → **STOP.** Write gate report. The tools are broken; nothing downstream is
interpretable.

---

### Batch 1 — Smoke (API, cap $0.20)

3 single-agent runs on `G1_strong`, `F_neutral`, seeds 1–3.

**GATE 1a (protocol):** ≥2 of 3 runs complete without `protocol_failure`.
Fail → STOP. Report the failure rate and example malformed outputs.

**GATE 1b (reachability):** ≥1 of 3 runs codes `reported_supported`.
Fail → STOP. Report: "five tools insufficient to reach the answer at θ=0.8" plus
each run's `pairs_touched`. This is an informative negative result, not a crash.

Record measured cost per run. Extrapolate to the full matrix and write it to
`results/gates.md`.

---

### Batch 2 — Temperature divergence (API, cap $0.20)

3 runs on `G1_strong`, `F_neutral`, same seed, `TEMPERATURE` from env.
Compute `pairwise_jaccard`.

**GATE 2:** `pairwise_jaccard < 0.80`.

- Fail → raise TEMPERATURE to 1.3, repeat once.
- Fail again → **skip Leg A entirely**, record in `results/gates.md` and
  `CHANGES.md`, and proceed to Batch 3. Legs B and C are unaffected.

Rationale: at zero effective divergence M1 ≈ M2 ≈ single agent and the three
curves coincide. Leg A would produce a null that reflects the harness, not the
world.

---

### Batch 3 — θ calibration (API, cap $1.00)

Single agent, `F_neutral`, θ ∈ {0.8, 0.5, 0.3, 0.2, 0.1}, 5 seeds each = 25 runs.
Success rate = fraction coded `reported_supported`.

**θ\* := the θ whose success rate is closest to 0.50.**

**GATE 3:** some θ in the sweep has success rate in [0.25, 0.75].
Fail → use the closest value anyway, set `calibration_deviation: true`, record
the full curve, and continue. **Do not extend the sweep.**

Write `data/G2_calibrated.csv` using θ\*. Record θ\* and the curve in
`results/tables/calibration.csv`.

The curve itself is a deliverable: it is the single-agent detection profile and
serves as the denominator for Leg A's slope.

---

### Batch 4 — Leg A: collective × verifiability (API, cap $3.00)

`F_neutral` throughout. Two datasets: `G1_strong` (θ=0.8), `G2_calibrated` (θ\*).

| Sub-batch | Runs |
|---|---|
| 4a — isolated | 2 datasets × 3 seeds × 3 agents = **18 runs** → yields M1 and M2 |
| 4b — shared log | 2 datasets × 3 seeds × 3 agents = **18 runs** → yields M3 |

Plus single-agent reference: reuse Batch 3's runs at θ=0.8 and θ\*.

**No gate.** Cap breach → reduce seeds from 3 to 2 and continue; record.

Primary outputs:
- success rate per {single, M1, M2, M3} × {0.8, θ\*}
- **slope**: change in collective gain from θ=0.8 to θ\*, per mode
- `pairwise_jaccard` and `union_coverage`, isolated vs shared

Interpretation note for the report — do not compute a verdict, just lay out
both: the level at each θ is a property of the task; the **slope across θ** is
the property of the team. The two must not be conflated.

---

### Batch 5 — Leg C: underpowered (API, cap $1.00)

`G4_underpowered`, `F_neutral`.

| Condition | Runs |
|---|---|
| Single agent, 3 seeds | 3 |
| M3, 3 seeds × 3 agents | 9 |

Correct answer is `no_finding` with reason `insufficient_evidence`.
Report the full three-way code distribution and the §8.2 reason distribution.
Any `reported_supported` here is overclaiming.

---

### Batch 6 — Leg B: prior source (API, cap $1.50)

Single agent throughout.

| Cell | Dataset | Framing | Runs |
|---|---|---|---|
| B1 | `G3_confound` | F_neutral | 3 |
| B2 | `G3_confound` | F_econ | 3 |
| B3 | `G3_confound` | F_phys | 3 |
| B4a | `B4_shuffled` | F_pendulum | 3 |
| B4b | `B4_shuffled` | F_sensor | 3 |

B1–B3 use the **same CSV file**. Verify by hash and assert equality at runtime.

Primary outputs: §8.3 causal-claim distribution across B1/B2/B3; for B4,
whether any run reports a supported relationship, and the B4a − B4b difference.

Cap breach → drop B3 first, then B4b.

---

### Batch 7 — Analysis (no API, $0)

1. All tables in `results/tables/`
2. `d'` and `c` per condition where both signal and null cells exist:
   `d' = z(hit) - z(FA)`, `c = -0.5*(z(hit) + z(FA))`, with the standard
   0.5-count correction for rates of 0 or 1
3. Figures: (a) calibration curve; (b) Leg A — x = θ, four lines, with
   `union_coverage` on a second panel; (c) rejection-reason distribution across
   all legs; (d) fabricated-number counts by condition
4. `REPORT.md`: method, every table, every gate outcome, all limitations, the
   full cost ledger
5. Verify offline replay: re-run all coding from `cache/` and `runs/` with the
   network disabled; assert every number in `REPORT.md` reproduces

Report `n = 3` seeds honestly. Do not compute significance tests across cells —
the design does not support them. Descriptive only.

---

### Total

~100 API runs. At `deepseek-chat` pricing this is expected to land well under
$1.00 total. The $10 cap is a fuse, not a budget.

---

## 10. Cost ledger (`ledger.py`)

Every API call appends a row: timestamp, batch, run id, prompt tokens,
completion tokens, estimated USD, cumulative USD.

- Check cumulative total **before** each call.
- At **$9.00** cumulative: hard stop. Abort all remaining calls, flush
  everything, write `results/gates.md` with a budget-abort notice, and run
  Batch 7 on whatever exists.
- Per-batch caps as listed. On breach, apply that batch's documented reduction
  and continue; if no reduction is documented, stop that batch and continue to
  the next.

The ledger is committed. It is part of the result.

---

## 11. Outputs

### 11.1 Per run — `runs/<batch>/<episode_id>/<agent_id>/`

```
meta.json        dataset, framing, mode, seed, agent order, model, temperature
actions.jsonl    one {action, result, valid, step} per line
conclusion.json  raw model output
coded.json       every field from §8
cost.json        tokens and USD for this run
```

### 11.2 `CHANGES.md`

Every deviation from this spec, with reason and timestamp. Includes: gate
failures and the action taken, caps breached, temperature changes,
`calibration_deviation`.

### 11.3 `open_questions.md`

One entry per unspecified decision:

```
## OQ-001
Where: src/tools.py, holdout split
Question: Spec says 70/30 with a fixed seed but does not say whether the split
is shared across datasets or per-dataset.
Blocked: holdout tool
Workaround applied: none — tool raises NotImplementedError
```

**"Workaround applied" must be `none` unless this spec authorised one.**

---

## 12. Tests

Offline, no network. All must pass at Gate 0.

| # | Test |
|---|---|
| 1 | Each generator produces the recorded shape and column set |
| 2 | In `G1_strong`, true interaction recovers to within 2 SE via OLS |
| 3 | In `G4_underpowered`, interaction p > 0.10 (confirming it is genuinely undetectable) |
| 4 | In `G3_confound`, corr(Z, X1) ∈ [0.88, 0.92]; Z absent from the Y equation |
| 5 | `B4_intact` recovers the pendulum law (R² > 0.95 on log-log); `B4_shuffled` does not (R² < 0.05) |
| 6 | **Tool sanity:** on `Y = X1*X2 + 0.01ε`, `test_interaction("X1","X2")` gives p < 1e-10 |
| 7 | Each tool rejects unknown columns with the §4.2 error shape |
| 8 | Cache: same action twice → identical result, second call does no computation |
| 9 | Agent loop terminates at exactly 8 actions, then emits a conclusion |
| 10 | Protocol failure path: mock model emitting garbage three times → run marked `protocol_failure`, not scored |
| 11 | Coding: a synthetic (log, conclusion) pair naming X4×X5 without `status:"supported"` codes `considered_rejected`, **not** success |
| 12 | Fabrication: a conclusion containing a number absent from the log is flagged; one containing only log numbers is not |
| 13 | Coverage: a log touching 19 distinct pairs yields `coverage == 0.1` |
| 14 | B1/B2/B3 resolve to the same file hash |
| 15 | Ledger: simulated spend of $9.01 triggers the hard stop |

---

## 13. Scope statement — include verbatim in `README.md`

> This experiment measures analytical decision-making, not programming ability.
> The tool set is fixed and the agent never executes code; we observe what it
> chooses to examine, when it stops, and how it interprets what it finds.
> The tool set is itself an uncalibrated design choice: a different set could
> change the results. It is frozen and published so others can vary it.

---

## 14. Reminder

Re-read §0 before making any judgement call. Record and skip. Do not decide.
