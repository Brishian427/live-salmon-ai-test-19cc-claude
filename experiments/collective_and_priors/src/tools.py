"""Frozen five-tool statistical service with persistent action-result cache."""

from __future__ import annotations

import hashlib
import json
import math
from pathlib import Path
from typing import Any, Callable

import numpy as np
import pandas as pd
import statsmodels.api as sm
from scipy import stats

from .generators import holdout_index

VALID_TOOLS = ["distribution", "correlation", "regression", "test_interaction", "holdout"]


def canonical_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def cache_key(dataset_name: str, action: dict[str, Any]) -> str:
    payload = dataset_name + "|" + canonical_json(action)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _six_significant(value: float) -> float:
    if not math.isfinite(value) or value == 0:
        return float(value)
    return float(f"{value:.6g}")


def _round_value(value: Any) -> Any:
    if isinstance(value, (float, np.floating)):
        return _six_significant(float(value))
    if isinstance(value, (int, np.integer)):
        return int(value)
    if isinstance(value, dict):
        return {str(key): _round_value(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_round_value(item) for item in value]
    return value


def _error(reason: str) -> dict[str, Any]:
    return {"error": reason, "valid_tools": VALID_TOOLS.copy()}


class ToolService:
    """Execute only the five frozen statistical actions against one dataset."""

    def __init__(
        self,
        frame: pd.DataFrame,
        dataset_name: str,
        cache_dir: str | Path,
        *,
        target: str = "Y",
    ) -> None:
        self.frame = frame.copy()
        self.dataset_name = dataset_name
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.target = target
        self.train_index, self.test_index = holdout_index(len(self.frame))
        self.computation_count = 0

    def execute(self, action: Any) -> dict[str, Any]:
        validation_error = self._validate(action)
        if validation_error is not None:
            return _error(validation_error)

        assert isinstance(action, dict)
        key = cache_key(self.dataset_name, action)
        path = self.cache_dir / f"{key}.json"
        if path.exists():
            return json.loads(path.read_text(encoding="utf-8"))

        handlers: dict[str, Callable[[dict[str, Any]], dict[str, Any]]] = {
            "distribution": self._distribution,
            "correlation": self._correlation,
            "regression": self._regression,
            "test_interaction": self._test_interaction,
            "holdout": self._holdout,
        }
        self.computation_count += 1
        result = _round_value(handlers[action["tool"]](action))
        path.write_text(canonical_json(result) + "\n", encoding="utf-8")
        return result

    def _validate(self, action: Any) -> str | None:
        if not isinstance(action, dict):
            return "action must be a JSON object"
        tool = action.get("tool")
        if tool not in VALID_TOOLS:
            return "unknown tool"
        required = {
            "distribution": ["column"],
            "correlation": ["a", "b"],
            "regression": ["columns"],
            "test_interaction": ["a", "b"],
            "holdout": ["columns"],
        }[tool]
        missing = [field for field in required if field not in action]
        if missing:
            return f"missing required field: {missing[0]}"
        if tool in {"regression", "holdout"}:
            columns = action.get("columns")
            if not isinstance(columns, list) or not columns:
                return "columns must be a non-empty list"
            for term in columns:
                if not isinstance(term, str):
                    return "column names must be strings"
                parts = term.split(":")
                if tool == "regression" and len(parts) != 1:
                    return "regression columns cannot contain interaction syntax"
                if len(parts) > 2 or any(part not in self.frame.columns for part in parts):
                    return f"unknown column: {term}"
        else:
            for field in required:
                column = action.get(field)
                if not isinstance(column, str) or column not in self.frame.columns:
                    return f"unknown column: {column}"
        if self.target not in self.frame.columns:
            return f"unknown target column: {self.target}"
        return None

    def _distribution(self, action: dict[str, Any]) -> dict[str, Any]:
        column = action["column"]
        values = self.frame[column]
        return {
            "tool": "distribution",
            "column": column,
            "n": len(values),
            "mean": values.mean(),
            "sd": values.std(ddof=1),
            "min": values.min(),
            "q25": values.quantile(0.25),
            "median": values.median(),
            "q75": values.quantile(0.75),
            "max": values.max(),
        }

    def _correlation(self, action: dict[str, Any]) -> dict[str, Any]:
        a, b = action["a"], action["b"]
        result = stats.pearsonr(self.frame[a], self.frame[b])
        return {"tool": "correlation", "a": a, "b": b, "r": result.statistic, "p": result.pvalue, "n": len(self.frame)}

    def _regression(self, action: dict[str, Any]) -> dict[str, Any]:
        columns = action["columns"]
        design = sm.add_constant(self.frame[columns], has_constant="add")
        fit = sm.OLS(self.frame[self.target], design).fit()
        coefficients = {
            name: {"coef": fit.params[name], "se": fit.bse[name], "p": fit.pvalues[name]}
            for name in design.columns
        }
        return {
            "tool": "regression",
            "columns": columns,
            "r2": fit.rsquared,
            "adj_r2": fit.rsquared_adj,
            "n": len(self.frame),
            "coefficients": coefficients,
        }

    def _test_interaction(self, action: dict[str, Any]) -> dict[str, Any]:
        a, b = action["a"], action["b"]
        base = self.frame[[a, b]].copy()
        without = sm.OLS(self.frame[self.target], sm.add_constant(base, has_constant="add")).fit()
        interaction_name = f"{a}:{b}"
        with_interaction = base.copy()
        with_interaction[interaction_name] = self.frame[a] * self.frame[b]
        fitted = sm.OLS(
            self.frame[self.target],
            sm.add_constant(with_interaction, has_constant="add"),
        ).fit()
        return {
            "tool": "test_interaction",
            "a": a,
            "b": b,
            "model": "Y ~ a + b + a:b",
            "interaction_coef": fitted.params[interaction_name],
            "interaction_se": fitted.bse[interaction_name],
            "interaction_p": fitted.pvalues[interaction_name],
            "r2_without_interaction": without.rsquared,
            "r2_with_interaction": fitted.rsquared,
            "delta_r2": fitted.rsquared - without.rsquared,
            "n": len(self.frame),
        }

    def _design_matrix(self, terms: list[str], frame: pd.DataFrame) -> pd.DataFrame:
        design: dict[str, pd.Series] = {}
        for term in terms:
            parts = term.split(":")
            design[term] = frame[parts[0]] if len(parts) == 1 else frame[parts[0]] * frame[parts[1]]
        return pd.DataFrame(design, index=frame.index)

    def _holdout(self, action: dict[str, Any]) -> dict[str, Any]:
        columns = action["columns"]
        train_idx, test_idx = self.train_index, self.test_index
        design = self._design_matrix(columns, self.frame)
        train_x = sm.add_constant(design.iloc[train_idx], has_constant="add")
        test_x = sm.add_constant(design.iloc[test_idx], has_constant="add")
        train_y = self.frame[self.target].iloc[train_idx]
        test_y = self.frame[self.target].iloc[test_idx]
        fit = sm.OLS(train_y, train_x).fit()
        train_pred = fit.predict(train_x)
        test_pred = fit.predict(test_x)

        def r2_score(actual: pd.Series, predicted: pd.Series) -> float:
            residual = float(np.square(actual.to_numpy() - predicted.to_numpy()).sum())
            total = float(np.square(actual.to_numpy() - actual.mean()).sum())
            return 1.0 - residual / total

        return {
            "tool": "holdout",
            "columns": columns,
            "train_n": len(train_idx),
            "test_n": len(test_idx),
            "train_r2": r2_score(train_y, train_pred),
            "test_r2": r2_score(test_y, test_pred),
        }
