from __future__ import annotations

from dataclasses import dataclass

import numpy as np


@dataclass
class ModelResult:
    model_name: str
    channel_names: list[str]
    coefficients: dict[str, float]
    intercept: float
    cpl: dict[str, float]
    contribution: dict[str, np.ndarray]
    contribution_pct: dict[str, float]
    y_pred: np.ndarray
    baseline: np.ndarray
    baseline_pct: float
    r_squared: float
    rmse: float
    coefficient_lower: dict[str, float] | None = None
    coefficient_upper: dict[str, float] | None = None
    cpl_lower: dict[str, float] | None = None
    cpl_upper: dict[str, float] | None = None


def build_model_result(
    *,
    model_name: str,
    channel_names: list[str],
    coefficients: dict[str, float],
    intercept: float,
    raw_spend: dict[str, np.ndarray],
    X: np.ndarray,
    y_pred: np.ndarray,
    r_squared: float,
    rmse: float,
) -> ModelResult:
    contribution: dict[str, np.ndarray] = {}
    for idx, ch in enumerate(channel_names):
        contribution[ch] = coefficients[ch] * X[:, idx]

    cpl: dict[str, float] = {}
    for ch in channel_names:
        attr_leads = float(contribution[ch].sum())
        raw_total = float(np.asarray(raw_spend[ch], dtype=np.float64).sum())
        cpl[ch] = raw_total / attr_leads if attr_leads > 0 else float("inf")

    y_pred_total = float(y_pred.sum()) if float(y_pred.sum()) != 0 else 1.0

    contribution_pct: dict[str, float] = {}
    for ch in channel_names:
        contribution_pct[ch] = float(contribution[ch].sum()) / y_pred_total

    baseline = y_pred.copy()
    for ch in channel_names:
        baseline = baseline - contribution[ch]
    baseline = np.clip(baseline, 0, None)
    baseline_pct = float(baseline.sum()) / y_pred_total

    return ModelResult(
        model_name=model_name,
        channel_names=channel_names,
        coefficients=coefficients,
        intercept=float(intercept),
        cpl=cpl,
        contribution=contribution,
        contribution_pct=contribution_pct,
        y_pred=y_pred.astype(np.float64),
        baseline=baseline.astype(np.float64),
        baseline_pct=baseline_pct,
        r_squared=float(r_squared),
        rmse=float(rmse),
    )
