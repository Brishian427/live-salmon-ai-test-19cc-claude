"""Batch driver primitives; live execution remains blocked by open questions."""

from __future__ import annotations

import json
from dataclasses import asdict
from pathlib import Path
from typing import Any

from .agent import AgentRun
from .prompts import prompts_sha256


class RunWriter:
    """Persist the frozen per-run output layout."""

    def __init__(self, runs_root: str | Path) -> None:
        self.runs_root = Path(runs_root)

    def write(
        self,
        *,
        batch: str,
        episode_id: str,
        agent_id: str,
        meta: dict[str, Any],
        run: AgentRun,
        coded: dict[str, Any] | None,
        cost: dict[str, Any],
    ) -> Path:
        directory = self.runs_root / batch / episode_id / agent_id
        directory.mkdir(parents=True, exist_ok=True)
        meta_with_prompt_hash = dict(meta)
        meta_with_prompt_hash["prompts_sha256"] = prompts_sha256()
        _write_json(directory / "meta.json", meta_with_prompt_hash)
        with (directory / "actions.jsonl").open("w", encoding="utf-8") as handle:
            for entry in run.actions:
                public_entry = {key: value for key, value in entry.items() if key != "raw"}
                handle.write(json.dumps(public_entry, sort_keys=True) + "\n")
        (directory / "conclusion.json").write_text(
            (run.conclusion_raw or "") + ("\n" if run.conclusion_raw else ""),
            encoding="utf-8",
        )
        _write_json(directory / "coded.json", coded or {"status": run.status})
        _write_json(directory / "cost.json", cost)
        return directory


def _write_json(path: Path, value: Any) -> None:
    if hasattr(value, "__dataclass_fields__"):
        value = asdict(value)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_gate_report(path: str | Path, gate: str, passed: bool, details: list[str]) -> None:
    """Append a deterministic Markdown gate section."""
    report_path = Path(path)
    report_path.parent.mkdir(parents=True, exist_ok=True)
    if not report_path.exists():
        report_path.write_text("# Gate Results\n", encoding="utf-8")
    with report_path.open("a", encoding="utf-8") as handle:
        handle.write(f"\n## {gate}: {'PASS' if passed else 'FAIL'}\n\n")
        for detail in details:
            handle.write(f"- {detail}\n")
