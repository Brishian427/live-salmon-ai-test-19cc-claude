# Spec Addendum 02 — Resolution for OQ-007

Supplements `SPEC_live_salmon_collective.md` v1.0 and
`SPEC_ADDENDUM_01.md`. Where this document conflicts with either earlier
document, this document controls.

## OQ-007 — Model access

**Resolution: use `deepseek-v4-pro` for every live model call.**

The configured endpoint has retired `deepseek-chat` and exposes
`deepseek-v4-pro`. The user explicitly selected `deepseek-v4-pro` on
2026-10-04.

Concretely:

- Set `MODEL_NAME=deepseek-v4-pro` in `.env` and `.env.example`.
- Use the same model in every condition and batch.
- Do not pass a seed to the model API; run seed values remain episode labels.
- Do not substitute `deepseek-flash` if `deepseek-v4-pro` is unavailable.
- No generator, tool, prompt, coding, or aggregation contract changes.

## Pricing boundary

This addendum does not silently reuse the retired `deepseek-chat` prices.
Official DeepSeek documentation checked on 2026-10-04 lists separate peak and
off-peak prices for `deepseek-v4-pro`, which cannot be represented faithfully
by Spec Addendum 01's three fixed price fields. OQ-008 records that remaining
decision. Live completion calls remain blocked until it is resolved.
