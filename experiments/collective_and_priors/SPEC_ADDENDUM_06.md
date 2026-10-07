# Spec Addendum 06 — Anthropic Cross-Family Replication

Supplements the base specification and Addenda 01–05. Where this document
conflicts with an earlier document, it controls only for the cross-family
replication. Authorized by the operator on 2026-10-05.

## 1. Purpose and design

Test whether the magnitude-ranked heredity behaviour observed with DeepSeek is
shared by another model family. Seeds within a model share its prior; a
different family is required to test prior identity. This is a cross-family
replication, not an extension by additional DeepSeek seeds.

The model is the only experimental change. All arms use `F_neutral`:

| Arm | Prompt | Dataset | Replicate labels |
|---|---|---|---|
| S-v1 | v1, without schema in system | `G1_strong` | 1–10 |
| S-v2 | v2, schema in system | `G1_strong` | 1–10 |
| S-v3 | v2, schema in system | `G1_swap` | 1–10 |

Assert by hash that every S-arm data file and system message is identical to
the corresponding DeepSeek arm. Never pool model families in a table; show
DeepSeek and Anthropic as separate columns.

## 2. Provider adapter

Add `src/providers/anthropic.py` using the official `anthropic` SDK. Map the
existing system message to the SDK `system` parameter and the existing user
message to one `user` message. Use no prefill, native tool calling,
`cache_control`, forced `tool_choice`, or structured-output schema.

- Set `max_tokens=2048` on every call.
- Treat `stop_reason == "max_tokens"` as a section 5.3 protocol failure.
- JSON compliance is instruction-only, followed by the existing section 5.3
  parse-and-retry behavior.
- Set `temperature=1.0`; do not send `top_p` or `top_k`.
- Thinking content must be absent from every response.
- Put the existing DeepSeek path behind the same interface without changing
  its behavior. All existing tests must continue to pass.

## 3. Empirical model selection

Try candidates in this pre-decided order and select the first that passes:

1. `claude-sonnet-5-5`
2. the Claude Sonnet 5 model identifier, only if confirmed from official
   Anthropic documentation; otherwise skip it
3. `claude-haiku-4-5-20251001`

For each candidate, run three smoke replicates on `G1_strong` with v2 prompts
and replicate labels 101–103. These labels never enter the main arms.

PASS requires both:

- zero thinking blocks across all responses; and
- at least 2/3 runs complete without `protocol_failure`.

Record every candidate tried, exact parameters, outcome, and reason. If all
three candidates fail, stop and report.

Thinking controls follow official documentation. For
`claude-sonnet-5-5`, first use the documented disabled setting; if rejected,
try `between_tools`. Because this experiment uses no native tools,
`between_tools` may yield no thinking content. For Haiku, do not enable
thinking. If an `effort` parameter exists, leave it at its default and record
that choice; only if the default yields thinking may the lowest value that
eliminates thinking be used, with the change recorded.

## 4. Pricing and budgets

Add these exact fields to `.env.example`:

```dotenv
ANTHROPIC_API_KEY=
PRICE_SONNET_5_5_INPUT_PER_M=2.00
PRICE_SONNET_5_5_OUTPUT_PER_M=10.00
PRICE_SONNET_5_INPUT_PER_M=2.00
PRICE_SONNET_5_OUTPUT_PER_M=10.00
PRICE_HAIKU_4_5_INPUT_PER_M=1.00
PRICE_HAIKU_4_5_OUTPUT_PER_M=5.00
```

Read token counts directly from response usage and never estimate them. Use an
enforcement factor of 1.0. The smoke cap is $0.60 across all candidates; each
S-arm cap is $1.20. The unchanged global hard stop is $9.00 cumulative,
including the approximately $0.19 already spent.

## 5. Gates and execution order

- Gate 0: all existing tests plus new adapter tests pass offline.
- Gate 1a for each S-arm: if fewer than 8/10 runs complete without
  `protocol_failure`, stop that arm and report.
- Gate 1b does not apply. Reachability is the measured replication outcome and
  zero target successes never stops an arm.
- Run S-v1, then S-v2, then S-v3.

## 6. Pre-registered analysis

Thresholds are derived from the existing DeepSeek data and are not chosen
freely after observing Anthropic.

### P1. Shared blind spot

Define `top3 = {X1:X2, X1:X3, X2:X3}`. Its random-choice share is
`3/190 = 0.016`; DeepSeek v2's observed share is `8/8 = 1.00`.

Compute the S-v2 share of `test_interaction` calls that target top3 and the
number of S-v2 runs testing `{X4,X5}`.

- `SHARED` if share is at least 0.75 and X4:X5 is tested in 0/10 runs.
- `DIFFERENT` if X4:X5 is tested in at least 1/10 runs.
- `UNRESOLVED` otherwise.
- If S-v2 makes fewer than four interaction tests in total, the verdict is
  `UNRESOLVED` regardless.

### P2. Cross-family routing oracle on G1_strong

Report pair unions and routing-oracle success separately for:

- within DeepSeek: ten v2 members, already measured as 0;
- within Anthropic: ten S-v2 members;
- cross-family: all twenty members.

“Diversity of priors, not number of agents” is supported if and only if the
cross-family oracle is greater than the within-DeepSeek oracle.

### P3. Data-independence of pair selection in the second family

Compare `P(select X1:X3)` for S-v2 versus S-v3 using Fisher's exact two-sided
test. Report it beside DeepSeek's descriptive 5/10 versus 4/10 comparison.
This analysis is descriptive only.

## 7. Required per-arm reporting

For every S-arm, report in the same format as the corresponding DeepSeek
reports:

- three-way interaction code;
- tool histogram pooled and split across steps 1–4 versus 5–8;
- maximum regression width;
- `claim_without_test`, with every reason quoted verbatim;
- X4 and X5 p-values and absolute-t ranks in every full-width regression.

## 8. Limitations

Include these statements verbatim in the final report:

- temperature 1.0 is not equivalent sampling diversity across providers (DeepSeek range 0-2, Anthropic range 0-1)
- DeepSeek used constrained JSON mode; Anthropic did not
- two families is the minimum for a prior-identity test, not a survey; a SHARED result may reflect common training material rather than a universal property of language models

## 9. Stop conditions

The only cross-family stop conditions are:

- all model candidates fail selection;
- Gate 1a fails on an arm;
- the budget fuse trips;
- the API is unavailable.

Otherwise execute all three arms, write `results/cross_family/REPORT.md`, and
stop.

## Criterion errors

This section is a post-result interpretation audit. It does not alter the
pre-registered rules or their accepted outcomes: P1 `DIFFERENT`, P2 supported,
and P3 Fisher two-sided p = 1.

**P1.** The `DIFFERENT` rule (`X4:X5` tested in at least 1/10 S-v2 runs)
fires when search **order** is identical but search **depth** is greater. It
therefore measured depth and labelled it prior. S-v2's top3 share was
30/38 = 0.789, above the pre-registered `SHARED` threshold of 0.75; the
verdict flipped solely on the `X4:X5` clause. Step-order evidence is examined
separately and exploratorily in E1.

**P2.** The pre-registered rule compared the cross-family oracle only with
the within-DeepSeek oracle. A diversity-benefit test must compare
cross-family success with `max(within-DeepSeek, within-Anthropic)`. Here the
corrected comparison is 1 versus `max(0, 1) = 1`, so there is no diversity
benefit. This does not change the recorded P2 verdict under its original rule.

**P3.** Anthropic tested all three top3 pairs in every S-v2 and S-v3 run, so
`P(select X1:X3) = 1` in both arms. The Fisher test had no power to distinguish
the selection mechanism within this family. Its pre-registered p = 1 remains
the recorded result.
