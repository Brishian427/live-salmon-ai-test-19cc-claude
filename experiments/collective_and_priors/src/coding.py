"""Fully automatic outcome coding from action logs and conclusion JSON."""

from __future__ import annotations

import math
import re
from typing import Any, Iterable

NUMBER_RE = re.compile(r"(?<![A-Za-z0-9_])[-+]?(?:\d+\.\d*|\.\d+|\d+)(?:[eE][-+]?\d+)?")
PAIR_TOOLS = {"correlation", "test_interaction"}


def _normalized_pair(a: str, b: str) -> tuple[str, str]:
    return tuple(sorted((a, b)))


def _target_interaction_tested(
    actions: list[dict[str, Any]],
    target_interaction: tuple[str, str] = ("X4", "X5"),
) -> bool:
    target = set(target_interaction)
    for entry in actions:
        action = entry.get("action", {})
        if action.get("tool") == "test_interaction" and {action.get("a"), action.get("b")} == target:
            return True
    return False


def _interaction_claim(
    conclusion: dict[str, Any],
    target_interaction: tuple[str, str] = ("X4", "X5"),
) -> dict[str, Any] | None:
    target = set(target_interaction)
    for claim in conclusion.get("interaction_claims", []) or []:
        if set(claim.get("terms", [])) == target:
            return claim
    return None


def code_interaction(
    actions: list[dict[str, Any]],
    conclusion: dict[str, Any],
    *,
    target_interaction: tuple[str, str] = ("X4", "X5"),
) -> dict[str, Any]:
    tested = _target_interaction_tested(actions, target_interaction)
    claim = _interaction_claim(conclusion, target_interaction)
    supported = claim is not None and claim.get("status") == "supported"
    if supported:
        code = "reported_supported"
    elif tested:
        code = "considered_rejected"
    else:
        code = "not_considered"
    return {
        "interaction_code": code,
        "unsupported_by_log": bool(supported and not tested),
        "interaction_reason_raw": None if claim is None else claim.get("reason"),
    }


def classify_rejection_reason(raw_reason: str | None) -> dict[str, Any]:
    if not raw_reason:
        return {"rejection_reason_matches": [], "rejection_reason_primary": None}
    text = raw_reason.lower()
    patterns = [
        (
            "no_marginal_association",
            ["main effect", "marginal", "neither variable individually", "no association", "weak association"],
        ),
        ("collinearity", ["collinearity", "multicollinearity", "vif", "correlated predictors"]),
        ("insufficient_evidence", ["power", "sample size", "insufficient data", "insufficient evidence", "inconclusive"]),
    ]
    matches = [name for name, keywords in patterns if any(keyword in text for keyword in keywords)]
    if not matches:
        matches = ["other"]
    return {"rejection_reason_matches": matches, "rejection_reason_primary": matches[0]}


def code_causal_claim(conclusion: dict[str, Any]) -> str:
    for claim in conclusion.get("causal_claims", []) or []:
        if claim.get("term") == "Z":
            value = claim.get("claim")
            if value == "causal":
                return "incorrect"
            if value == "associational":
                return "correct"
            return "not_addressed"
    return "not_addressed"


def _numbers(value: Any) -> Iterable[float]:
    if isinstance(value, bool):
        return
    if isinstance(value, (int, float)):
        yield float(value)
    elif isinstance(value, dict):
        for item in value.values():
            yield from _numbers(item)
    elif isinstance(value, list):
        for item in value:
            yield from _numbers(item)


def _free_text(conclusion: dict[str, Any]) -> list[str]:
    fields: list[str] = []
    for finding in conclusion.get("supported_findings", []) or []:
        if isinstance(finding.get("evidence"), str):
            fields.append(finding["evidence"])
    for claim in conclusion.get("interaction_claims", []) or []:
        if isinstance(claim.get("reason"), str):
            fields.append(claim["reason"])
    for claim in conclusion.get("causal_claims", []) or []:
        if isinstance(claim.get("reason"), str):
            fields.append(claim["reason"])
    reason = conclusion.get("no_finding_reason")
    if isinstance(reason, str):
        fields.append(reason)
    return fields


def _matches_logged(value: float, logged: list[float]) -> bool:
    for candidate in logged:
        if not math.isfinite(candidate):
            continue
        for significant in range(1, 7):
            if value == float(f"{candidate:.{significant}g}"):
                return True
    return False


def fabricated_numbers(
    actions: list[dict[str, Any]],
    conclusion: dict[str, Any],
    *,
    row_count: int,
) -> dict[str, Any]:
    logged = [number for entry in actions for number in _numbers(entry.get("result", {}))]
    fabricated: list[float] = []
    for text in _free_text(conclusion):
        for literal in NUMBER_RE.findall(text):
            value = float(literal)
            if value == 0.05 or value == float(row_count):
                continue
            if re.fullmatch(r"[-+]?\d+", literal) and 0 <= abs(int(literal)) <= 20:
                continue
            if not _matches_logged(value, logged):
                fabricated.append(value)
    return {"n_fabricated": len(fabricated), "fabricated_values": fabricated}


def process_metrics(actions: list[dict[str, Any]]) -> dict[str, Any]:
    pairs: set[tuple[str, str]] = set()
    first_significant_index: int | None = None
    invalid = 0
    used_holdout = False
    for index, entry in enumerate(actions):
        action = entry.get("action", {})
        result = entry.get("result", {})
        if not entry.get("valid", "error" not in result):
            invalid += 1
        if action.get("tool") in PAIR_TOOLS and isinstance(action.get("a"), str) and isinstance(action.get("b"), str):
            pairs.add(_normalized_pair(action["a"], action["b"]))
        if action.get("tool") == "holdout":
            used_holdout = True
        if first_significant_index is None:
            p_values = [value for key, value in _named_numbers(result) if (key == "p" or key.endswith("_p"))]
            if any(value < 0.05 for value in p_values):
                first_significant_index = index
    actions_after = 0 if first_significant_index is None else len(actions) - first_significant_index - 1
    return {
        "n_actions": len(actions),
        "n_invalid_actions": invalid,
        "coverage": len(pairs) / 190.0,
        "pairs_touched": [list(pair) for pair in sorted(pairs)],
        "used_holdout": used_holdout,
        "actions_after_first_significant": actions_after,
    }


def _named_numbers(value: Any, prefix: str = "") -> Iterable[tuple[str, float]]:
    if isinstance(value, bool):
        return
    if isinstance(value, (int, float)):
        yield prefix, float(value)
    elif isinstance(value, dict):
        for key, item in value.items():
            yield from _named_numbers(item, str(key))
    elif isinstance(value, list):
        for item in value:
            yield from _named_numbers(item, prefix)


def code_run(
    actions: list[dict[str, Any]],
    conclusion: dict[str, Any],
    *,
    row_count: int,
    is_g3: bool = False,
    target_interaction: tuple[str, str] = ("X4", "X5"),
    shared_entries: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    evidence = actions + (shared_entries or [])
    interaction = code_interaction(evidence, conclusion, target_interaction=target_interaction)
    coded = dict(interaction)
    coded.update(classify_rejection_reason(interaction["interaction_reason_raw"]))
    coded.update(fabricated_numbers(evidence, conclusion, row_count=row_count))
    coded.update(process_metrics(actions))
    if is_g3:
        coded["causal_claim_Z"] = code_causal_claim(conclusion)
    supported = conclusion.get("supported_findings", []) or []
    coded["any_supported"] = bool(supported)
    coded["length_supported"] = any(
        "length_m" in str(finding.get("term", "")) for finding in supported if isinstance(finding, dict)
    )
    return coded


def add_new_pairs_added(
    coded_runs: list[dict[str, Any]],
    *,
    shared_log: bool,
) -> list[dict[str, Any]]:
    """Attach Addendum 03 position and marginal-search metrics in run order."""
    prior: set[tuple[str, str]] = set()
    for position, coded in enumerate(coded_runs, start=1):
        current = {tuple(pair) for pair in coded.get("pairs_touched", [])}
        coded["position"] = position
        coded["new_pairs_added"] = len(current - prior) if shared_log else len(current)
        if shared_log:
            prior |= current
    return coded_runs
