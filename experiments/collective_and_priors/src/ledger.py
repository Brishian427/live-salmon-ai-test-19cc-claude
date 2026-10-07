"""Append-only usage ledger with configurable pricing and 2x enforcement."""

from __future__ import annotations

import csv
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping

HARD_STOP_ENFORCEMENT_USD = 9.00
ENFORCEMENT_FACTOR = 1.0


class BudgetAbort(RuntimeError):
    pass


@dataclass(frozen=True)
class Pricing:
    input_cache_miss_per_m: float
    input_cache_hit_per_m: float
    output_per_m: float

    @classmethod
    def from_mapping(cls, values: Mapping[str, str]) -> "Pricing":
        return cls(
            input_cache_miss_per_m=float(values["PRICE_INPUT_CACHE_MISS_PER_M"]),
            input_cache_hit_per_m=float(values["PRICE_INPUT_CACHE_HIT_PER_M"]),
            output_per_m=float(values["PRICE_OUTPUT_PER_M"]),
        )

    def estimate(self, cache_miss_tokens: int, cache_hit_tokens: int, completion_tokens: int) -> float:
        return (
            cache_miss_tokens * self.input_cache_miss_per_m
            + cache_hit_tokens * self.input_cache_hit_per_m
            + completion_tokens * self.output_per_m
        ) / 1_000_000.0


def _usage_value(usage: Any, name: str) -> int | None:
    if isinstance(usage, Mapping):
        value = usage.get(name)
    else:
        value = getattr(usage, name, None)
    return None if value is None else int(value)


class CostLedger:
    FIELDNAMES = [
        "timestamp",
        "batch",
        "run_id",
        "prompt_cache_hit_tokens",
        "prompt_cache_miss_tokens",
        "completion_tokens",
        "prompt_tokens",
        "pricing_fallback",
        "estimated_usd",
        "enforcement_usd",
        "cumulative_usd",
        "cumulative_enforcement_usd",
    ]

    def __init__(self, path: str | Path, pricing: Pricing) -> None:
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.pricing = pricing

    def rows(self) -> list[dict[str, str]]:
        if not self.path.exists():
            return []
        with self.path.open("r", encoding="utf-8", newline="") as handle:
            return list(csv.DictReader(handle))

    @property
    def cumulative_usd(self) -> float:
        rows = self.rows()
        return 0.0 if not rows else float(rows[-1]["cumulative_usd"])

    @property
    def cumulative_enforcement_usd(self) -> float:
        rows = self.rows()
        return 0.0 if not rows else float(rows[-1]["cumulative_enforcement_usd"])

    def batch_enforcement_usd(self, batch: str) -> float:
        return sum(float(row["enforcement_usd"]) for row in self.rows() if row["batch"] == batch)

    def ensure_can_call(
        self,
        *,
        estimated_next_true_usd: float = 0.0,
        batch: str | None = None,
        batch_cap_usd: float | None = None,
    ) -> None:
        projected = self.cumulative_enforcement_usd + ENFORCEMENT_FACTOR * estimated_next_true_usd
        if projected >= HARD_STOP_ENFORCEMENT_USD:
            raise BudgetAbort(
                f"hard stop: projected enforcement spend ${projected:.6f} reaches the ${HARD_STOP_ENFORCEMENT_USD:.2f} fuse"
            )
        if batch is not None and batch_cap_usd is not None:
            batch_projected = self.batch_enforcement_usd(batch) + ENFORCEMENT_FACTOR * estimated_next_true_usd
            if batch_projected >= batch_cap_usd:
                raise BudgetAbort(
                    f"batch cap: {batch} projected spend ${batch_projected:.6f} reaches ${batch_cap_usd:.2f}"
                )

    def append_usage(
        self,
        *,
        batch: str,
        run_id: str,
        usage: Any,
        timestamp: str | None = None,
    ) -> dict[str, str]:
        hit = _usage_value(usage, "prompt_cache_hit_tokens")
        miss = _usage_value(usage, "prompt_cache_miss_tokens")
        prompt = _usage_value(usage, "prompt_tokens") or 0
        completion = _usage_value(usage, "completion_tokens") or 0
        fallback = hit is None or miss is None
        if fallback:
            hit = 0
            miss = prompt
        assert hit is not None and miss is not None
        amount = self.pricing.estimate(miss, hit, completion)
        enforcement = ENFORCEMENT_FACTOR * amount
        cumulative = self.cumulative_usd + amount
        cumulative_enforcement = self.cumulative_enforcement_usd + enforcement
        row = {
            "timestamp": timestamp or datetime.now(timezone.utc).isoformat(),
            "batch": batch,
            "run_id": run_id,
            "prompt_cache_hit_tokens": str(hit),
            "prompt_cache_miss_tokens": str(miss),
            "completion_tokens": str(completion),
            "prompt_tokens": str(prompt),
            "pricing_fallback": str(fallback).lower(),
            "estimated_usd": f"{amount:.10f}",
            "enforcement_usd": f"{enforcement:.10f}",
            "cumulative_usd": f"{cumulative:.10f}",
            "cumulative_enforcement_usd": f"{cumulative_enforcement:.10f}",
        }
        exists = self.path.exists()
        with self.path.open("a", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=self.FIELDNAMES)
            if not exists:
                writer.writeheader()
            writer.writerow(row)
        return row
