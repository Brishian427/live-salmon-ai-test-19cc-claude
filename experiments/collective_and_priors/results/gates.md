# Gate Results

## Gate 0: PASS (superseded by amended Gate 0 below)

- All 15 required offline tests passed: `15 passed in 12.38s`.
- Tool sanity passed: synthetic `Y = X1*X2 + 0.01*epsilon` produced `interaction_p < 1e-10`.
- The full mock agent loop emitted exactly 8 actions and then a conclusion.
- The cache round trip returned an identical result without a second computation.
- Protocol-failure, three-way interaction coding, fabrication detection, coverage, identical G3 file resolution, and the $9.00 ledger fuse all passed.
- No network or model API call was made.
- Canonical dataset files were not frozen because OQ-002 through OQ-004 require seed and G2-timing decisions. Tests used explicit test-local seeds and did not create canonical experimental data.

## Gate 0 (Spec Addendum 01): PASS

- All 19 required offline tests passed: `19 passed in 4.17s`.
- Tests 16–19 passed: framing-independent system-message remainder, prompt prohibition scan, empty/shared log rendering, and the 2× ledger safety-factor fuse.
- Canonical Batch 0 datasets were written once with frozen seeds: `G1_strong`, `G3_confound`, `G4_underpowered`, `B4_intact`, and `B4_shuffled`.
- `G2_calibrated` was correctly not written and remains deferred until Batch 3.
- Ground-truth files contain global holdout seed `7030` and the exact train/test index arrays; B4 ground truth also contains the complete permutation index array.
- Generator code is frozen at this gate. Future generator edits require a deviation entry and affected-batch reruns.
- True cumulative completion cost: `$0.00`.
- 2× enforcement cumulative cost: `$0.00`.
- The credential/model-list preflight was non-generative and did not send a completion request.
- OQ-007 remains open because the authenticated endpoint does not list `deepseek-chat`; Batch 1 is not started.

## Model Preflight after Spec Addendum 02: PASS WITH PRICING BLOCK

- Authentication and endpoint connectivity succeeded.
- The configured model `deepseek-v4-pro` is present in the endpoint's model list.
- No completion request was sent and no completion tokens were consumed.
- All 19 offline tests passed again: `19 passed in 12.74s`.
- OQ-007 is resolved by the user-authorized model amendment.
- OQ-008 remains open because official `deepseek-v4-pro` pricing has separate peak and off-peak rates, while the current ledger contract has only one rate per token category.
- The three price fields are intentionally blank, so live completion calls remain blocked rather than being mispriced.

## Gate 0 (Spec Addendum 03): PASS

- All 25 amended offline tests passed: `25 passed in 4.03s`.
- `G0_null` was generated with theta `0.0`, seed `1000`, the frozen main effects, and the global holdout split.
- Thinking is explicitly disabled on every request; a non-empty reasoning/thinking response field is tested to fail the run.
- Peak prices are frozen at `$0.044/M` cache-hit input, `$1.32/M` cache-miss input, and `$3.96/M` output tokens.
- Budget enforcement is tested at `1.0x`; the global hard stop remains `$9.00` and Batch 5's amended cap is `$1.80`.
- Canonical baseline, theta tie-break, agent order/position, `new_pairs_added`, and B4 dual-outcome contracts are implemented.
- Batch 7 analysis generation and offline coding replay completed against an empty pre-live artifact set without error.
- No completion request was sent during the amendment or Gate 0 verification.

## Gate 1a: PASS

- complete runs: 3/3

## Gate 1b: FAIL

- Five tools insufficient to reach the answer at theta=0.8.
- reported_supported: 0/3
- seed 1 pairs: [['X1', 'Y'], ['X2', 'Y'], ['X3', 'Y']]
- seed 2 pairs: [['X1', 'Y'], ['X2', 'Y'], ['X3', 'Y'], ['X4', 'Y'], ['X5', 'Y'], ['X6', 'Y']]
- seed 3 pairs: [['X1', 'Y'], ['X2', 'Y'], ['X3', 'Y'], ['X4', 'Y'], ['X5', 'Y'], ['X6', 'Y']]
- measured mean cost/run: $0.004131; 127-run extrapolation: $0.5246

Mandatory action: stopped before Batch 2. No recovery or prompt/tool change was attempted.

## Gate 1b (authorized Batch 1 extension to n=10): FAIL

- Protocol-complete runs: 10/10.
- Runs calling `test_interaction` at least once: 0/10.
- Runs calling `test_interaction` on `{X4,X5}`: 0/10.
- Runs coding `reported_supported` for `{X4,X5}`: 0/10.
- Total Batch 1 cost: `$0.0513898`; the `$0.20` cap was not breached.
- This extension changed only replicate count. The frozen prompts, tools, eight-action budget, data, model, temperature, and all other parameters were unchanged.
- Step C remains unapproved; execution stops here.
