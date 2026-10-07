# Changes from the Frozen Specification

No deviations have been applied.

Specification gaps are recorded in `open_questions.md`; blocked work remains unimplemented rather than silently changed.

## 2026-10-03 — Spec Addendum 01

Applied `SPEC_ADDENDUM_01.md`, which controls where it conflicts with the base specification. This is an authorized amendment, not an implementation deviation.

## 2026-10-04 — Spec Addendum 02

Applied `SPEC_ADDENDUM_02.md`, which replaces `deepseek-chat` with the user-authorized `deepseek-v4-pro`. This is an authorized amendment, not an implementation deviation. Model-specific peak/off-peak pricing remains blocked by OQ-008.

## 2026-10-04 — Spec Addendum 03 (pre-execution)

Applied the operator's final pre-execution amendments from the 2026-10-04
instruction, recorded verbatim in substance in `SPEC_ADDENDUM_03.md`:

- Added six canonical G1/G2 single-agent reference runs to remove the Batch 3
  versus Batch 4 dataset-draw confound.
- Added `position` and `new_pairs_added` to measure anchoring versus search
  diversification directly.
- Split B4 outcomes into ordinary `any_supported` false positives and the
  `length_supported` memorisation signature.
- Added the true-null `G0_null` dataset and 21 Batch 5 runs required for valid
  d-prime and criterion estimates; G4 comparisons are now named detectability
  discrimination.
- Replaced the stale-price 2.0x enforcement factor with 1.0x after fixing all
  requests to verified peak prices; raised only Batch 5's cap to $1.80.

Thinking is explicitly disabled, theta-star ties select the smallest theta,
and the fixed agent-label order is defined in the same addendum.

## 2026-10-04 — Gate 1b terminal stop

Gate 1a passed with 3/3 protocol-complete runs. Gate 1b failed because 0/3
runs on `G1_strong` reported the X4·X5 interaction as supported. Per the frozen
gate rule, live execution stopped before Batch 2. No recovery, prompt change,
tool change, extra run, or gate override was attempted.

## 2026-10-04 — Batch 1 extended to n=10

After accepting the original Gate 1b stop and completing the no-API diagnosis,
the operator authorized seven additional Batch 1 replicates (episode labels
4–10). This is a replication-count extension of the existing Batch 1, not a
specification revision. Dataset, framing, model, temperature, prompts, tools,
eight-action budget, generator seed, and all other experimental parameters are
unchanged. The extension measures the frequency of interaction-tool non-use
and small-width regression behavior. Step C remains unapproved.

## 2026-10-04 — Spec Addendum 04 / v2 arm

Applied the operator-approved v2 revision in `SPEC_ADDENDUM_04.md`. Its only
substantive experimental change is exposing the unchanged conclusion JSON
schema and field rules in the system message from step 1. The complete step-9
conclusion prompt remains unchanged. v1 remains frozen as a separate n=10
control arm; v2 runs and tables use distinct paths and are never pooled with v1.

## 2026-10-04 — v2 Batch 1 terminal branch

Executed ten v2 single-agent runs on the original theta-0.8 `G1_strong` file.
The target interaction was `reported_supported` in 0/10 runs, so the
pre-registered branch stopped execution before Gate 2. No v2 Batch 2 request
was sent. A reporting-only correction counts seed 6's unknown `interaction`
tool name as one invalid action; no run was replaced or rerun.

## 2026-10-04 — v2 offline O1–O3 supplement

Appended full-width X4/X5 coefficient diagnostics and separate v1/v2
ten-member routing-oracle analyses to `results/v2/BATCH1_COMPARISON.md` using
only saved action logs. The cost ledger remained at 180 rows; no API request or
new experimental run was made for this supplement.

## 2026-10-04 — Spec Addendum 05 / isolated v3 cell

Added the one-cell `G1_swap` arm defined in `SPEC_ADDENDUM_05.md`. The data
retain seed 1001, all feature/noise draws, and every main-effect coefficient;
the sole generator change moves the theta-0.8 product from X4·X5 to X1·X3.
v3 retains the complete v2 prompt/tool/action configuration and uses separate
run, cache, state, result, and table paths. It stops after ten single-agent
runs under every outcome.

The completed v3 cell produced 4/10 `reported_supported` outcomes on X1·X3,
which is inconclusive under the pre-registered 4–6/10 interval. Execution
stopped unconditionally after the cell; no continuation run was created.

## 2026-10-05 — Spec Addendum 06 / Anthropic cross-family replication

Applied the operator-approved cross-family replication in
`SPEC_ADDENDUM_06.md`. The model family is the sole experimental change: the
three Anthropic S-arms hash-match the corresponding DeepSeek prompt and data
inputs, retain the fixed tools and eight-action budget, and are reported as
separate arms. The official Anthropic SDK adapter uses instruction-only JSON,
direct response usage, provider-specific thinking controls, and the frozen
peak-price budget caps. Gate 0 passed all 38 offline tests before any new API
request.

All three S-arms then passed Gate 1a at 10/10 protocol-complete runs using
`claude-sonnet-5-5`. Anthropic S-v2 tested X4·X5 in 5/10 runs and reported it
supported in all five, producing the pre-registered P1 verdict `DIFFERENT`.
The cross-family routing oracle succeeded where the DeepSeek-only oracle did
not. S-v2 and S-v3 each selected X1·X3 in 10/10 runs (two-sided Fisher p=1).
The cross-family requests cost $1.870872; the full ledger ended at $2.061117528.
Offline replay reproduced all 264 saved tool actions and all 33 coded runs
with zero mismatches.

## 2026-10-05 — Offline criterion audit and exploratory E1–E7

The operator accepted the pre-registered P1 `DIFFERENT`, P2 supported, and P3
p=1 verdicts, then authorized a post-result audit of what those criteria
actually measure. `SPEC_ADDENDUM_06.md` now records the P1 depth/order,
P2 comparator, and P3 saturation errors without changing any original rule
or outcome. `results/cross_family/REPORT.md` appends clearly labeled
exploratory E1–E7 calculations from the existing logs and the exact
regression/holdout limitation. `results/REPORT_FINAL.md` presents the
historical v1/v2/v3 sequence followed by the cross-family result. No API
request, run, tool, or ledger row was added or changed.
The legacy read-only replay checker was corrected to use X1·X3 for
`G1_swap`; it previously assumed X4·X5 for every dataset. The correction
changes no saved coding or experimental tool. All 63 saved runs now replay
with zero coding mismatches, all 33 Anthropic runs reproduce 264/264 tool
actions, and the complete 38-test suite passes.

## 2026-10-05 — Addendum 07 pre-execution registration

Created `SPEC_ADDENDUM_07.md` before new API calls. Implemented the sequential
Anthropic M3 shared-log arm, rotating agent order across ten episodes, with
per-agent shared-evidence coding and a separate read-only replay. The existing
prompt, tools, data, eight-action budget, model parameters, and previous arm
records remain unchanged. Hash assertions match Anthropic S-v2's system
message and G1_strong data file. The offline 120-triple M1/M2 baselines are
110/120 and 60/120 respectively; the 41-test pre-execution suite passes.

The live M3 sequence hit the authorized `APIConnectionError` stop during
episode 6, position 2. Episodes 1–5 and episode 6 position 1 are complete;
16 saved runs and 128 actions replay with zero mismatches. The interrupted
agent had six billed responses without a persisted run log. The M3 ledger
spent $1.424748, with $3.485865528 global cumulative spend. Gate 1a and
A1–A6 remain unevaluated; `results/collective/STOP.md` records the partial
state. No Part 2 fork action, push, or PR was attempted.

## 2026-10-06 — Fixed infrastructure resumption rule

Before inspecting any interim M3 outcome or resuming requests, appended the
operator's fixed retry, exclusion, and restart policy to Addendum 07. Episode
6 position 2's original six billed responses ($0.0485160000) are
`discarded: incomplete due to API connection error; exogenous to outcome.`
They remain in the original cost ledger, are excluded from scoring and shared
context, and are separated from the replacement attempt by a new ledger run
ID. Episodes 1–5 and episode 6 position 1 remain unchanged. No interim M3
success, duplication, or A1–A6 statistic was computed for this decision.

The non-generative pre-resume API probe succeeded. The fixed restart completed
episodes 6–10 without a transient retry; episode 10 position 2 failed the
JSON protocol after four saved actions. Gate 1a passed at 9/10 complete
episodes. After all ten episodes, M3_majority was 8/10 versus M2 60/120,
M3_union was 10/10 versus M1 110/120, and A2 was 1/60 (`DIVISION`).
`results/collective/REPORT.md` and `results/REPORT_FINAL.md` contain A1–A6,
the protocol-failure treatment, and the cost audit. The M3 ledger totals
$2.6973000000 including the discarded $0.0485160000; global cumulative
spend is $4.7584175280. Full M3 replay reproduced 30 saved agent records
and 236 tool actions, explicitly excluding the six discarded responses,
with zero mismatches. The 44-test suite, 92-run read-only coding replay, and
33-run Anthropic cross-family replay pass.

Addendum 07 Part 2 stopped at step 1: `FORK_URL` is absent from `.env`.
Recorded OQ-015. No fork clone, branch, commit, push, or PR was attempted.
