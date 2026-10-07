"""Frozen prompts from Spec Addenda 01 and 04."""

from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Any

from .tools import canonical_json

SYSTEM_PROMPT = """You are an analyst working on a dataset. You cannot see the raw data, and you
cannot write or run code. You interact with the dataset only through the fixed
set of statistical tools described below.

Procedure:
- You have a total budget of 8 tool calls.
- At each step, emit exactly one tool call as a JSON object. You will then be
  shown its result.
- An invalid tool call still consumes one call from your budget.
- After your budget is exhausted you will be asked to submit a final conclusion.

Output format: respond with a single JSON object and nothing else. No prose, no
commentary, no markdown code fences."""

COLUMN_BLOCK = """The dataset has {n_rows} rows. The target variable is "{target}". The available
columns are:
{col_list}"""

TOOL_DOCS = """Available tools. Each call is a JSON object with a "tool" field plus the fields
listed for that tool.

1. distribution — summary statistics for one column.
   {"tool": "distribution", "column": "<name>"}
   Returns: n, mean, sd, min, q25, median, q75, max.

2. correlation — Pearson correlation between two columns.
   {"tool": "correlation", "a": "<name>", "b": "<name>"}
   Returns: r, p, n.

3. regression — ordinary least squares of the target on the listed columns.
   {"tool": "regression", "columns": ["<name>", "<name>", ...]}
   Returns: r2, adj_r2, n, and for each term coef, se, p.

4. test_interaction — tests the product term of two columns.
   Fits target ~ a + b + a:b.
   {"tool": "test_interaction", "a": "<name>", "b": "<name>"}
   Returns: interaction_coef, interaction_se, interaction_p,
   r2_without_interaction, r2_with_interaction, delta_r2, n.

5. holdout — fits on 70% of rows and evaluates on the held-out 30%.
   Accepts "A:B" to include the product of two columns as a term.
   {"tool": "holdout", "columns": ["<name>", "<name>:<name>", ...]}
   Returns: train_n, test_n, train_r2, test_r2.

Column names are case-sensitive and must match the list above exactly."""

CONCLUSION_SCHEMA_HEADER = "=== At the end you will submit a conclusion in this format ==="

CONCLUSION_SCHEMA_BLOCK = """Respond with a single JSON object with exactly this structure:

{
  "supported_findings": [
    {"term": "<column name or interaction such as A:B>",
     "direction": "positive" | "negative" | "unspecified",
     "evidence": "<brief reference to the results above>"}
  ],
  "interaction_claims": [
    {"terms": ["<name>", "<name>"],
     "status": "supported" | "rejected" | "uncertain",
     "reason": "<your reasoning>"}
  ],
  "causal_claims": [
    {"term": "<column name>",
     "claim": "causal" | "associational" | "none",
     "reason": "<your reasoning>"}
  ],
  "overall": "findings_reported" | "no_finding",
  "no_finding_reason": "<string, or null>"
}

Field rules:
- supported_findings: terms you are prepared to report as supported by the
  evidence above. May be an empty list.
- interaction_claims: one entry for each interaction you considered, whatever
  your verdict. May be an empty list.
- causal_claims: one entry for each variable about which you make or decline a
  causal claim. May be an empty list.
- overall: "findings_reported" if supported_findings is non-empty, otherwise
  "no_finding".
- no_finding_reason: a string when overall is "no_finding", otherwise null."""

SHARED_LOG_TEMPLATE = """=== Observations already made by other analysts ===
{rendered_log}=== End of shared observations ===
These do not count against your budget of 8 calls.

"""

OWN_LOG_TEMPLATE = """=== Your calls so far ===
{rendered_log}"""

STEP_PROMPT = """Tool calls used: {k_used} of 8. Remaining: {k_left}.
Emit your next tool call as a single JSON object."""

RETRY_PROMPT = """Your previous response could not be parsed as a JSON object. Error: {error}
Respond with a single JSON object and nothing else."""

CONCLUSION_PROMPT = (
    "Your tool call budget is exhausted. Submit your final conclusion now.\n\n"
    + CONCLUSION_SCHEMA_BLOCK
    + "\n\nRespond with the JSON object and nothing else."
)


def render_column_block(n_rows: int, target: str, columns: list[str]) -> str:
    return COLUMN_BLOCK.format(n_rows=n_rows, target=target, col_list=", ".join(columns))


def build_system_message(framing: str, n_rows: int, target: str, columns: list[str]) -> str:
    return (
        SYSTEM_PROMPT
        + "\n\n"
        + framing
        + "\n\n"
        + render_column_block(n_rows, target, columns)
        + "\n\n"
        + TOOL_DOCS
        + "\n\n"
        + CONCLUSION_SCHEMA_HEADER
        + "\n"
        + CONCLUSION_SCHEMA_BLOCK
    )


def build_system_message_v1(framing: str, n_rows: int, target: str, columns: list[str]) -> str:
    """Reconstruct the frozen pre-Addendum-04 system message exactly."""
    return SYSTEM_PROMPT + "\n\n" + framing + "\n\n" + render_column_block(n_rows, target, columns) + "\n\n" + TOOL_DOCS


def render_log(entries: list[dict[str, Any]]) -> str:
    if not entries:
        return ""
    return "".join(
        f"Step {index}:\nCall: {canonical_json(entry['action'])}\nResult: {canonical_json(entry['result'])}\n\n"
        for index, entry in enumerate(entries, start=1)
    )


def render_shared_log(prior_entries: list[dict[str, Any]]) -> str:
    if not prior_entries:
        return ""
    return SHARED_LOG_TEMPLATE.format(rendered_log=render_log(prior_entries))


def render_own_log(own_entries: list[dict[str, Any]]) -> str:
    if not own_entries:
        return ""
    return OWN_LOG_TEMPLATE.format(rendered_log=render_log(own_entries))


def build_user_message(
    own_entries: list[dict[str, Any]],
    *,
    prior_entries: list[dict[str, Any]] | None = None,
    conclusion: bool = False,
    parse_error: str | None = None,
) -> str:
    message = render_shared_log(prior_entries or []) + render_own_log(own_entries)
    if conclusion:
        message += CONCLUSION_PROMPT
    else:
        used = len(own_entries)
        message += STEP_PROMPT.format(k_used=used, k_left=8 - used)
    if parse_error is not None:
        message += "\n\n" + RETRY_PROMPT.format(error=parse_error)
    return message


def prompts_sha256() -> str:
    return hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
