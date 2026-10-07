"""Aggregation and coverage metrics for the three frozen collective modes."""

from __future__ import annotations

from itertools import combinations
from typing import Any


def _success(coded: dict[str, Any]) -> bool:
    return coded.get("interaction_code") == "reported_supported"


def aggregate_m1(coded_runs: list[dict[str, Any]]) -> bool:
    if len(coded_runs) != 3:
        raise ValueError("M1 requires exactly three runs")
    return any(_success(run) for run in coded_runs)


def aggregate_majority(coded_runs: list[dict[str, Any]]) -> bool:
    if len(coded_runs) != 3:
        raise ValueError("majority aggregation requires exactly three runs")
    return sum(_success(run) for run in coded_runs) >= 2


def collective_process_metrics(coded_runs: list[dict[str, Any]]) -> dict[str, float]:
    if len(coded_runs) != 3:
        raise ValueError("collective metrics require exactly three runs")
    sets = [set(tuple(pair) for pair in run.get("pairs_touched", [])) for run in coded_runs]
    similarities: list[float] = []
    for left, right in combinations(sets, 2):
        union = left | right
        similarities.append(1.0 if not union else len(left & right) / len(union))
    return {
        "pairwise_jaccard": sum(similarities) / len(similarities),
        "union_coverage": len(set().union(*sets)) / 190.0,
    }


AGENT_ORDER_BY_SEED = {
    1: ["A", "B", "C"],
    2: ["B", "C", "A"],
    3: ["C", "A", "B"],
}


def agent_order(seed: int) -> list[str]:
    if seed < 1:
        raise ValueError(f"no frozen agent order for seed label {seed}")
    return AGENT_ORDER_BY_SEED[(seed - 1) % 3 + 1].copy()
