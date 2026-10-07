# Anthropic Official-Documentation Verification

Verified on 2026-10-05 before any Anthropic completion request.

## Candidate identifiers and controls

- Claude Sonnet 5.5: Claude API ID `claude-sonnet-5-5`. Official guidance
  states that `disabled` is rejected and `thinking: {"type":"between_tools"}`
  is the lowest setting; with no native tools the response contains text only.
  API default effort is `high`, so the experiment omits `output_config` and
  records the untouched default.
- Claude Sonnet 5: Claude API ID `claude-sonnet-5`. Official guidance states
  that thinking is on by default and is fully disabled with
  `thinking: {"type":"disabled"}`. API default effort is `high`, so the
  experiment omits `output_config` and records the untouched default.
- Claude Haiku 4.5: Claude API ID `claude-haiku-4-5-20251001`. Thinking is off
  unless legacy extended thinking is explicitly enabled; the experiment sends
  no thinking parameter. Effort is not supported.

The official documentation therefore confirms candidate 2 and it remains in
the pre-registered order.

## Prices

- Sonnet 5.5: $2.00 per million input tokens and $10.00 per million output
  tokens.
- Sonnet 5: $2.00 per million input tokens and $10.00 per million output
  tokens.
- Haiku 4.5: $1.00 per million input tokens and $5.00 per million output
  tokens.

These match the operator-supplied `.env.example` values.

## Official sources

- https://platform.claude.com/docs/en/models/overview
- https://platform.claude.com/docs/en/models/sonnet-5/overview
- https://platform.claude.com/docs/en/models/sonnet-5-5/whats-new-sonnet-5-5
- https://platform.claude.com/docs/en/build-with-claude/thinking
- https://platform.claude.com/docs/en/build-with-claude/effort
- https://www.anthropic.com/claude-sonnet-5-5
