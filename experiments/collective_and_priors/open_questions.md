# Open Questions

## Resolution Status

- OQ-001 through OQ-006 were resolved by `SPEC_ADDENDUM_01.md` on 2026-10-03 and are retained below as historical records.
- OQ-007 was resolved by `SPEC_ADDENDUM_02.md` on 2026-10-04.
- OQ-008 was resolved by the user's peak-rate instruction on 2026-10-04.
- OQ-009 through OQ-014 were resolved by `SPEC_ADDENDUM_03.md` on 2026-10-04. No design question remains open.

## OQ-001
Where: repository root
Question: The specification targets a fork of `Hypogenic-AI/live-salmon-ai-test-19cc-claude`, but the current workspace has no `.git` metadata and does not contain that repository. Should this workspace be initialized as the target repository, or should the experiment files be moved into an existing fork?
Blocked: Repository-integrated implementation, version-control verification, and commits beyond the requested environment template.
Workaround applied: none — `.env.example` is staged at the specification's required workspace-relative path only.

## OQ-002
Where: `src/generators.py`, frozen dataset files
Question: The specification requires recorded seeds but does not provide the generation seed for G1, G3, G4, or the B4 draw and permutation.
Blocked: Writing and freezing the canonical dataset CSV and ground-truth files.
Workaround applied: none — generator functions require explicit seeds and canonical files are not generated.

## OQ-003
Where: Batch 0 and Batch 3, `G2_calibrated`
Question: Batch 0 says all datasets are written and generators frozen, while Batch 3 says to write `G2_calibrated.csv` only after theta-star is measured. Which instruction controls G2 creation and generator freeze timing?
Blocked: Creation of the canonical G2 dataset and the final generator freeze declaration.
Workaround applied: none — G2 creation remains deferred.

## OQ-004
Where: `src/tools.py`, holdout split
Question: The specification says the 70/30 holdout uses a fixed seed stored per dataset but does not give the seed values or say whether the seed is shared across datasets or unique per dataset.
Blocked: Canonical holdout results for frozen datasets.
Workaround applied: none — the tool service requires an explicit holdout seed.

## OQ-005
Where: `src/ledger.py`, live API cost estimation
Question: The specification requires estimated USD per call but does not freeze input, output, and cache token prices for `deepseek-chat`.
Blocked: Authoritative dollar estimates and budget enforcement for live API batches.
Workaround applied: none — the ledger requires explicit pricing before live calls.

## OQ-006
Where: `src/agent.py`, live model prompts
Question: The specification fixes the framing strings and conclusion JSON shape but does not provide the exact system prompt, tool-documentation text, action prompt, conclusion prompt, or shared action-log serialization.
Blocked: Live API agent runs and the claim that prompts are frozen and identical across conditions.
Workaround applied: none — the offline mock loop can be tested, but live prompts are not invented.

## OQ-007
Where: specification section 1.2, model access
Question: Authentication to the configured DeepSeek endpoint succeeds, but its model-list response contains `deepseek-flash` and `deepseek-v4-pro` and does not contain the required `deepseek-chat`. Should the endpoint/account configuration be changed so `deepseek-chat` is available, or should the frozen specification be revised explicitly?
Blocked: All live API runs beginning with Batch 1.
Workaround applied: none — no substitute model was selected and no completion request was sent.

Resolution: `SPEC_ADDENDUM_02.md` authorizes `deepseek-v4-pro` for every live model call.

## OQ-008
Where: `src/ledger.py`, `.env`, and live batch scheduling
Question: Official DeepSeek pricing checked on 2026-10-04 gives `deepseek-v4-pro` separate off-peak and peak prices: cache hit $0.022/$0.044, cache miss $0.66/$1.32, and output $1.98/$3.96 per million tokens. Spec Addendum 01 defines only one fixed value for each category. Should the ledger select rates dynamically from the documented UTC schedule, or should every call be reported and enforced at peak rates?
Blocked: Authoritative cost reporting, per-batch cap enforcement, and all live completion calls.
Workaround applied: none — the three stale `deepseek-chat` price fields are blank, and no completion call is sent.
Official source: https://api-docs.deepseek.com/quick_start/pricing/

Resolution: Apply the official peak rates to every request regardless of request time: cache-hit input $0.044/M tokens, cache-miss input $1.32/M tokens, and output $3.96/M tokens.

## OQ-009
Where: `src/agent.py`, every `deepseek-v4-pro` request
Question: `deepseek-v4-pro` enables thinking mode by default, and the provider documents that temperature has no effect in thinking mode. Should every request explicitly disable thinking so the frozen temperature-divergence design and complete-action-log invariant remain operative?
Blocked: Final live client configuration and all live calls.
Workaround applied: none.

Resolution: Explicitly disable thinking on every request; any non-empty reasoning/thinking response field fails the run and halts the batch.

## OQ-010
Where: Batch 4 single-agent reference
Question: The base spec says to reuse Batch 3 runs at theta 0.8 and theta-star, but Addendum 01 requires those calibration runs to use temporary datasets generated with seeds 1100–1104 while Batch 4 uses canonical G1/G2 generated with seeds 1001/1002. Should Batch 4 add six single-agent runs on the canonical G1/G2 files so collective gain is compared on byte-identical data, rather than use the non-identical calibration datasets as its primary single-agent reference?
Blocked: Valid Leg A collective-gain and slope calculation.
Workaround applied: none.

Resolution: Add six canonical Batch 4 single-agent baselines; Batch 3 runs are calibration-only.

## OQ-011
Where: Batch 3 theta-star selection
Question: If two or more theta values have success rates equally close to 0.50, which tied value wins?
Blocked: Deterministic creation of canonical `G2_calibrated.csv` in the event of a tie.
Workaround applied: none.

Resolution: Select the smallest theta among tied candidates.

## OQ-012
Where: Batch 2 and M3 agent order metadata/execution
Question: The spec says agent order is fixed by seed but supplies no seed-to-order mapping, and Batch 2 says only “same seed.” What exact mapping and Batch 2 label should be used?
Blocked: M3 execution ordering and required metadata.
Workaround applied: none.

Resolution: Use seed-label orders 1=A/B/C, 2=B/C/A, 3=C/A/B; Batch 2 uses label 1. Record position and the new-pairs mechanism metric.

## OQ-013
Where: Batch 6 B4 outcome coding
Question: What exact automatic predicate constitutes “reports a supported relationship” for B4, and what direction should be used for the B4a minus B4b difference?
Blocked: B4 primary outcome table.
Workaround applied: none.

Resolution: Report `any_supported` and `length_supported`; each difference is pendulum minus sensor.

## OQ-014
Where: Batch 7 signal-detection analysis
Question: Which exact signal/null cells feed each d-prime and criterion calculation? The spec gives formulas but does not identify the cell pairings.
Blocked: Batch 7 d-prime and criterion table.
Workaround applied: none.

Resolution: Add G0 and use its matching single/M1/M2/M3 cells for d-prime and criterion. G4 comparisons are detectability discrimination only; G3 and B4 are excluded from d-prime.

## OQ-015 — Part 2 fork destination

Where: Addendum 07 Part 2, ignored workspace `.env`
Question: What is the fork clone URL to set as `FORK_URL`? The field is absent on 2026-10-06.
Blocked: Cloning the sibling fork, creating `collective-and-priors`, copying the experiment, fork-side verification and secret scan, committing, and preparing the final fork status handoff.
Workaround applied: none. Part 1 is complete; Part 2 stopped at its explicitly specified first step. No clone, push, or PR was attempted. `PR_DESCRIPTION_DRAFT.md` is also not present in the workspace; its availability in the intended fork cannot be checked until a destination is supplied.

2026-10-06 final-preparation recheck: `FORK_URL` is still absent or empty. The self-contained instruction also requires the PR draft at workspace root before any packaging step, and that file is independently absent. Steps 2–4 were skipped exactly as directed.

2026-10-06 update: the operator supplied the complete PR description inline and explicitly removed the draft-file prerequisite. Only `FORK_URL` remains blocked under this question.

Resolution: On 2026-10-07 the operator supplied `https://github.com/Brishian427/live-salmon-ai-test-19cc-claude.git`; it was written to the ignored `.env` and verified with `git ls-remote` at fork `main` commit `c88a910fc9eef390b8020645639a556fb7e393e4`.

## OQ-016 — Supplementary readout definitions

Where: Final PR preparation Step 1 and `results/collective/REPORT.md`
Question: What are the exact definitions of supplementary readouts R1–R6? The referenced previous instruction is not present in this thread's retained user messages, attached text, project specifications, reports, CHANGES, or Sextant state.
Blocked: Computing and writing the required `Supplementary readouts` section without inventing metrics or denominators.
Workaround applied: none. No API call was made and no R1–R6 value was inferred from its label alone.

Resolution: The user's self-contained final-preparation attachment supplied exact definitions for R1–R6 on 2026-10-06. Compute them strictly offline from existing M3 and S-v2 artifacts, including both required R6 treatments, and append them to `results/collective/REPORT.md`.

## OQ-017 — PR-description draft input

Where: Final preparation Step 2, workspace root
Question: Where is the required `PR_DESCRIPTION_DRAFT.md`? It is absent from the workspace root on 2026-10-06.
Blocked: Steps 2–4, including fork packaging, placeholder replacement, the local fork commit, and pre-push verification.
Workaround applied: none. The instruction explicitly requires both this file and `FORK_URL`; because both are absent, Steps 2–4 were skipped and no clone, commit, push, or PR was attempted.

Resolution: The operator supplied the full PR description inline in the diagram/final-packaging instruction and explicitly stated that no draft file is needed. Future packaging should use that inline text and must not wait for `PR_DESCRIPTION_DRAFT.md`.
