# Spec Addendum 05 — G1_swap Magnitude-Ranked Heredity Cell

Supplements the base specification and Addenda 01–04. Where this document
conflicts with an earlier document, it controls only for the v3 arm. Authorized
by the operator on 2026-10-04 after accepting the pre-registered v2 stop.

## 1. Purpose and experimental scope

v3 consists of exactly one new dataset cell designed to test the
magnitude-ranked heredity mechanism suggested by the completed v2 logs. It
does not reopen v2 and has no continuation branch.

All prompts, tools, the eight-action budget, model, temperature, pricing,
framing, and the Addendum 04 schema-in-system-message change remain unchanged.

## 2. G1_swap dataset

Generate `G1_swap` with 1,000 rows, generator seed 1001, and the same feature
and noise draws as `G1_strong`. The only change is moving the theta-0.8 product
term from X4·X5 to X1·X3:

```text
Y = 2.0*X1 + 0.5*X2 - 1.5*X3 + 0.10*X4 + 0.10*X5
    + 0.8*(X1*X3) + eps
```

The feature distribution, main-effect coefficients, noise distribution,
sample size, holdout split, and every other generator property are unchanged.

## 3. Single v3 cell

Run ten independent single-agent runs on `G1_swap` under `F_neutral`, with
replicate labels 1–10. Store every v3 run, cache, state, report, and table in
paths separate from v1 and v2. Never merge arms in one table or aggregate.

Success is `reported_supported` on `{X1,X3}`. Report:

- the per-run three-way code: `reported_supported`, `considered_rejected`, or
  `not_considered`;
- the `test_interaction` pair histogram;
- `claim_without_test`, including every verbatim `reason` when present;
- the same per-run, regression-width, pooled-tool, half-by-half tool, invalid,
  request-count, and peak-cost fields used in the v1/v2 Batch 1 comparison.

## 4. Pre-registered interpretation and mandatory stop

- At least 7/10 target successes confirms the magnitude-ranked heredity
  mechanism.
- At most 3/10 target successes rejects the mechanism.
- 4–6/10 target successes is inconclusive.

Stop after this one cell regardless of outcome. Do not create any v3
continuation branch.
