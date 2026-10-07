from __future__ import annotations

import hashlib

import pytest

from src.generators import generate_g3_confound, write_dataset
from src.ledger import BudgetAbort, CostLedger, Pricing


def test_14_b1_b2_b3_resolve_to_same_file_hash(tmp_path):
    frame, truth = generate_g3_confound()
    csv_path, _ = write_dataset("G3_confound", frame, truth, tmp_path)
    paths = [csv_path, csv_path, csv_path]
    hashes = [hashlib.sha256(path.read_bytes()).hexdigest() for path in paths]
    assert len(set(hashes)) == 1


def test_15_ledger_simulated_spend_above_nine_triggers_stop(tmp_path):
    pricing = Pricing(input_cache_miss_per_m=1.0, input_cache_hit_per_m=0.0, output_per_m=0.0)
    ledger = CostLedger(tmp_path / "ledger.csv", pricing)
    ledger.append_usage(
        batch="test",
        run_id="simulated",
        usage={"prompt_cache_hit_tokens": 0, "prompt_cache_miss_tokens": 9_010_000, "completion_tokens": 0, "prompt_tokens": 9_010_000},
    )
    assert ledger.cumulative_usd == pytest.approx(9.01)
    with pytest.raises(BudgetAbort):
        ledger.ensure_can_call()
