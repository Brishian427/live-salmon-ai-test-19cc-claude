# Spec Addendum 07 — Anthropic shared-log collective arm and fork package

This addendum supplements the frozen base specification and Addenda 01–06. It authorizes only the work below. Prior pre-registered verdicts remain unchanged. Do not push or open a PR. Ask no questions except at the specified stops.

## Part 1 — Leg A (collective) on `claude-sonnet-5-5`

### Purpose and fixed conditions

The original Leg A never ran because DeepSeek failed Gate 1b. Anthropic S-v2 succeeds 5/10 on G1_strong, within the measurable range. Run the shared-log condition on that cell.

Use `claude-sonnet-5-5` with the exact Addendum 06 parameters: `thinking={"type":"between_tools"}`, temperature 1.0, `max_tokens=2048`, no effort override. Use v2 prompts (schema in the system message), F_neutral, and G1_strong. Assert by hash that the system message and data file match S-v2.

### M1 and M2 — offline routing baselines

Treat the 10 existing S-v2 runs as independent members. Enumerate all `C(10,3)=120` triples. M1 is the fraction of triples in which at least one member `reported_supported` on `{X4,X5}`. M2 is the fraction in which at least two members did. Label both: "computed from 10 independent single-agent runs by exhaustive triples; assumes exchangeability." No new runs for M1 or M2.

### M3 — new shared-log runs

Run 10 episodes, labels 1–10, with three sequential agents per episode (30 runs). The shared log follows base spec §6.1 and Addendum 01 §6.6 exactly. Each agent has its own eight-action budget; shared entries do not consume that budget. Rotate agent order as previously approved and record `position` in `{1,2,3}`.

An M3 agent's evidence base is the union of its own log and the shared entries shown to it. For the three-way code, `{X4,X5}` is considered if `test_interaction` on that pair occurs in either. Record `own_test_X4X5` when the agent itself tests it, and `seen_X4X5_only` when it does not but a shown shared entry does. The fabrication check treats numbers in the shared block as present. `claim_without_test` counts a test in either own or shared log.

M3_majority succeeds for an episode if at least two of its three agents `reported_supported` on `{X4,X5}`. M3_union succeeds if at least one does.

### Gates and caps

Gate 1a requires at least 8/10 protocol-complete episodes. A protocol failure by any agent marks the episode as failed. Gate 2 (temperature divergence) is waived because M3 agents receive different inputs by construction: divergence does not depend on sampling, and within-family homogeneity is part of the hypothesis. Report the E7 Jaccard value alongside. The Part 1 cap is $3.50; the unchanged global fuse is $9.00.

### Pre-registered analysis

- **A1 Primary:** Compare M3_majority with M2 and M3_union with M1 at the same aggregation level. Report rates and two-sided Fisher exact tests where sample sizes allow, descriptively.
- **A2 Duplication:** For every position-2 or position-3 agent, for each top-three pair `{X1:X2, X1:X3, X2:X3}` appearing in its shared log, record whether that agent re-tested the pair. `duplication_rate = re-tests / opportunities`. Verdict: DIVISION if `<=0.20`, IMITATION if `>=0.80`, otherwise MIXED. These bands are symmetric around the midpoint and fixed before data.
- **A3 Conditional depth:** Among episodes where position 1 did not test `{X4,X5}`, calculate the fraction of position-2/3 agents who tested it themselves. Compare with S-v2's single-agent baseline 5/10.
- **A4 New pairs:** Report `new_pairs_added` by M3 position, mean and distribution.
- **A5 Internal false-positive control:** The top-three pairs are true nulls on G1_strong. Report the rate of agents reporting any top-three pair as supported for S-v2 single agents and M3 by position.
- **A6 Fresh replicates:** Report position-1 agents' `{X4,X5}` `reported_supported` rate separately; never pool them with S-v2.

Stop after Part 1 only for Gate 1a failure, a budget fuse, or unavailable API. Otherwise write `results/collective/REPORT.md`, integrate it as a new section after cross-family in `results/REPORT_FINAL.md` with verdicts first and unqualified, and proceed to Part 2.

## Part 2 — package into the fork; no push

1. Read `FORK_URL` from `.env`. If absent, stop Part 2 and record the issue in `open_questions.md`.
2. Clone `FORK_URL` into a sibling directory outside this workspace and create branch `collective-and-priors`.
3. Copy the experiment into `experiments/collective_and_priors/` in the fork. Exclude `.env`, `Sextant/`, credentials, `__pycache__`, and local virtual environments. Include `src/`, `tests/`, `data/`, `runs/`, `cache/`, `results/`, all SPEC files and addenda, `CHANGES.md`, `open_questions.md`, `.env.example`, `README.md`, and the cost ledger. Modify no upstream file.
4. From inside the copied experiment, run all tests and offline replay. Only move-related path failures may be fixed; log every such fix in `CHANGES.md` and rerun. For any other failure, stop and report.
5. Scan the copied tree for strings matching an API-key pattern and literal values of `DEEPSEEK_API_KEY` or `ANTHROPIC_API_KEY`. On any hit, stop and report.
6. Commit on the branch with exact message: `Add tool-grounded agent harness: interaction search, routing oracle, cross-family replication and shared-log collective arm (refs #1)`.
7. Copy `PR_DESCRIPTION_DRAFT.md` to workspace `PR_DESCRIPTION.md` and make only these edits: add one Changes bullet for the shared-log collective arm on `claude-sonnet-5-5`; add a Findings subsection titled `Collective (shared-log) arm` containing a table of S-v2 single, M1, M2, M3_union, and M3_majority rates, A2 duplication rate and pre-registered verdict, A3 conditional rate, and A5 internal false-positive rates; remove `Run the shared-log condition...` from follow-ups; add follow-ups for framing and shuffled-physics conditions and the underpowered condition. Use numbers and pre-registered verdicts only, with no interpretive sentences.
8. Report branch name, commit hash, fork path, clean git status ahead of origin by one commit and not pushed, and test and replay results from inside the fork. Then stop.

## 2026-10-06 amendment — infrastructure retry and fixed resumption

The 2026-10-05 halt on `APIConnectionError` was correct under the then-current Addendum 07. It was infrastructure failure, not an experimental gate. This amendment is fixed before resuming and does not alter prompts, tools, model parameters, data, action budgets, coding thresholds, or the $3.50 arm/$9.00 global caps.

### No interim outcome look

Do not compute, print, or report M3 outcomes, including A1–A6, success rates, or duplication, until all ten episodes are complete. No decision to resume or interpret the experiment may depend on the first five episodes' results.

### Transient-error policy

On a connection error, timeout, HTTP 5xx, or HTTP 429, resend the **identical request** with exponential backoff of 2, 4, 8, 16, and 32 seconds, at most five resends after the initial failed attempt. This use of five resends follows the five explicitly specified delays. A failed request returned no content; retries do not change model state, do not consume the eight-action budget, and do not count as protocol failures. Log each retry's timestamp, error class, and attempt number in ledger notes. If the initial request and all five resends fail, stop under the existing API-unavailable condition. Do not retry any other failure class under this policy.

Before resumed completion calls, send one non-experimental reachability probe to the Anthropic API. Apply the same transient-error policy to that probe. If it exhausts, stop and report without restarting an agent.

### Fixed resumption rule

1. Keep episodes 1–5 exactly as saved; do not rerun or re-score them before episode 10.
2. In episode 6, keep the completed position-1 agent and its log. Discard the interrupted position-2 agent entirely from scoring, conclusions, and shared context. Its six billed responses remain in the cost ledger and are recorded in `CHANGES.md` as `discarded: incomplete due to API connection error; exogenous to outcome.` No unreturned or partial content enters another agent's input.
3. Restart episode 6 at position 2 as a fresh agent, with exactly the saved position-1 log as its shared input. Run position 3 normally, then episodes 7–10 under the unchanged design.
4. After episode 10, compute the full A1–A6 analysis; run all tests and offline replay, explicitly verifying exclusion of the discarded attempt. Continue to Part 2 only if the original gates and caps permit. Do not push or open a PR.
