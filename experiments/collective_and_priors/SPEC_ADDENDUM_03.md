# Spec Addendum 03 — Final Pre-Execution Resolutions

Supplements `SPEC_live_salmon_collective.md`, `SPEC_ADDENDUM_01.md`, and
`SPEC_ADDENDUM_02.md`. Where this document conflicts with an earlier document,
this document controls. Authorized by the operator on 2026-10-04 before the
first live completion call.

## 1. Model mode and response invariant

Use `deepseek-v4-pro` with thinking explicitly disabled on every request.
Inspect the complete response message. If any reasoning/thinking field is
present and non-empty, mark the run failed and halt the current batch. The
temperature and complete-action-log invariants remain mandatory.

## 2. Canonical single-agent references for Leg A

Batch 4 adds six single-agent reference runs: three episode labels each on the
canonical `G1_strong` (generator seed 1001) and `G2_calibrated` (generator seed
1002) files. Batch 3 runs are calibration-only and are never used as the
single-agent comparison for Batch 4.

## 3. Calibration tie-break

If multiple theta values have success rates equally close to 0.50, choose the
smallest tied theta as theta-star.

## 4. Agent order, position, and mechanism metric

Use the following fixed label order: episode label 1 = A/B/C, 2 = B/C/A, and
3 = C/A/B. Batch 2 uses episode label 1. Labels carry no analyst identity.

Record `position` in `{1,2,3}` in each multi-agent run's `meta.json`. Define:

```
new_pairs_added = |pairs_touched \
                    union(pairs_touched of all prior-position agents)|
```

For single-agent and isolated M1/M2 runs, `new_pairs_added` equals
`|pairs_touched|`. Report mean `new_pairs_added` by position separately for
isolated and shared-log episodes and include it as a Leg A figure panel.

## 5. B4 outcomes

Record two automatic outcomes:

- `any_supported`: `supported_findings` is non-empty.
- `length_supported`: a `supported_findings[].term` contains `length_m`,
  including interaction terms.

For each outcome report the pendulum-minus-sensor rate difference.
`length_supported` is the memorisation signature; `any_supported` is an
ordinary false-positive rate.

## 6. G0 null and Batch 7 pairings

Add `G0_null`, identical to the core G1 generator except theta = 0.0, with
generator seed 1000. It retains the 0.10 X4 and X5 main effects. Ground truth:
no interaction exists.

Append these cells to Batch 5, all with `F_neutral` and episode labels 1–3:

- single agent: 3 runs;
- isolated three-agent episodes: 9 runs, yielding M1 and M2 null cells;
- shared-log three-agent episodes: 9 runs, yielding M3 null cells.

Using `reported_supported` on `{X4,X5}`, compute d-prime and criterion
separately for single, M1, M2, and M3, pairing the G1 and G2 hit rates with the
corresponding G0 false-alarm rate. G3 is excluded.

Compute the same formulas with G4 instead of G0 for single and M3 only, but
label the result `detectability discrimination`, never d-prime. B4 reports
rates only and cites G0 single as the synthetic false-positive reference; no
d-prime is computed for B4.

## 7. Budget enforcement

Use official `deepseek-v4-pro` peak rates for every request:

- cache-hit input: $0.044 per million tokens;
- cache-miss input: $1.32 per million tokens;
- output: $3.96 per million tokens.

Set the enforcement factor to 1.0. The $9.00 hard stop is evaluated against
the true estimated cumulative cost. All original per-batch caps remain except
Batch 5, whose cap is raised from $1.00 to $1.80.

## 8. Execution authorization

After implementing and testing this addendum, proceed through Batches 1–7
without further design questions. Base specification section 0 still governs
gate failures, budget stops, artifact flushing, and visible failure reporting.
