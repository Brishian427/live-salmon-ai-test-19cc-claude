# Spec Addendum 04 — v2 Early Conclusion-Schema Visibility

Supplements the base specification and Addenda 01–03. Where this document
conflicts with an earlier document, this document controls for the v2 arm.
Authorized by the operator on 2026-10-04 after the frozen v1 Batch 1 control
arm completed 10 runs.

## 1. The only substantive experimental change

Move `CONCLUSION_PROMPT`'s JSON schema block and its field rules into the
system message, appended after `TOOL_DOCS`, under this exact header:

```
=== At the end you will submit a conclusion in this format ===
```

The schema is therefore visible from step 1. At step 9, continue sending the
complete, unchanged `CONCLUSION_PROMPT` in the user message exactly as before.
No other text in any prompt changes.

## 2. Required companion amendments

These are implementation and analysis amendments, not additional experimental
changes.

### A1. Prompt-prohibition scan

The Test 17 exemption that covered `CONCLUSION_PROMPT` now covers the schema
block wherever it appears. The framing sentence and every other part of
`SYSTEM_PROMPT` remain fully subject to the original prohibition scan.

### A2. Framing-independent system hash

Recompute and pin Test 16's expected hash. The invariant is unchanged: after
replacing the framing sentence, the complete system message must hash
identically across every framing.

### A3. Batch 3 doubling grid

Replace the calibration grid with:

| theta | temporary dataset seed |
|---:|---:|
| 0.2 | 1200 |
| 0.4 | 1201 |
| 0.8 | 1202 |
| 1.6 | 1203 |
| 3.2 | 1204 |

Run five v2 single-agent replicates per theta.

- `theta_star`: theta whose success rate is closest to 0.5; ties select the
  smaller theta.
- `theta_strong`: smallest theta with success rate at least 0.8; if no grid
  value qualifies, use 3.2.
- Leg A uses `theta_strong` and `theta_star`.
- If `theta_strong != 0.8`, regenerate canonical `G1_strong` at
  `theta_strong` with generator seed 1001 and log the regeneration.
- If `theta_strong == theta_star`, record the equality, run Leg A at that
  single theta only, and report the slope as not estimable.

## 3. v2 Batch 1 and separate control arm

Run ten v2 single-agent replicates on the existing byte-identical
theta-0.8 `G1_strong`, `F_neutral`, with episode labels 1–10. Compare them to
the frozen v1 Batch 1 n=10 arm, but never merge v1 and v2 rows in any table.

Report separately by arm:

- any `test_interaction` call;
- `test_interaction` on `{X4,X5}`;
- `reported_supported` on `{X4,X5}`;
- maximum regression-width distribution;
- pooled tool histogram and tool histograms for steps 1–4 versus 5–8;
- `claim_without_test` rate as a pre-registered secondary outcome;
- every `claim_without_test` reason verbatim.

## 4. Pre-registered continuation branch

- If v2 Batch 1 has 0/10 `reported_supported`, stop and report the v1-versus-v2
  comparison.
- If v2 Batch 1 has at least 1/10 `reported_supported`, continue to Gate 2,
  then Batch 3 on the doubling grid, then Batches 4–7 under all previously
  approved amendments plus this addendum.

No further question is required unless a gate fails, the budget fuse trips, or
the API becomes unavailable.
