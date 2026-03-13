from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import numpy as np
from sklearn.preprocessing import StandardScaler


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


def fit_standardized_linear_model(
    model: Any,
    X: np.ndarray,
    y: np.ndarray,
) -> tuple[np.ndarray, float, np.ndarray, StandardScaler]:
    X_values = np.asarray(X, dtype=np.float64)
    y_values = np.asarray(y, dtype=np.float64)
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X_values)
    model.fit(X_scaled, y_values)
    y_pred = np.asarray(model.predict(X_scaled), dtype=np.float64)

    scale = np.where(np.isclose(scaler.scale_, 0.0), 1.0, scaler.scale_)
    coefficients = np.asarray(model.coef_, dtype=np.float64) / scale
    intercept = float(model.intercept_) - float(
        np.sum(np.asarray(model.coef_, dtype=np.float64) * scaler.mean_ / scale)
    )
    return coefficients.astype(np.float64), float(intercept), y_pred, scaler


def build_non_negative_media_prediction(
    *,
    X: np.ndarray,
    channel_names: list[str],
    intercept: float,
    channel_coefficients: np.ndarray,
    control_coefficients: np.ndarray | None = None,
) -> tuple[dict[str, float], np.ndarray]:
    X_values = np.asarray(X, dtype=np.float64)
    n_channels = len(channel_names)
    clipped_channel_coefficients = np.clip(
        np.asarray(channel_coefficients, dtype=np.float64),
        a_min=0.0,
        a_max=None,
    )
    y_pred = np.full(X_values.shape[0], float(intercept), dtype=np.float64)
    if n_channels > 0:
        y_pred += X_values[:, :n_channels] @ clipped_channel_coefficients
    if control_coefficients is not None and len(control_coefficients) > 0:
        y_pred += X_values[:, n_channels:] @ np.asarray(control_coefficients, dtype=np.float64)

    coefficients = {
        channel_names[idx]: float(clipped_channel_coefficients[idx])
        for idx in range(n_channels)
    }
    return coefficients, y_pred


def compute_r_squared_and_rmse(
    y_true: np.ndarray,
    y_pred: np.ndarray,
) -> tuple[float, float]:
    y_true_values = np.asarray(y_true, dtype=np.float64)
    y_pred_values = np.asarray(y_pred, dtype=np.float64)
    ss_res = float(np.sum((y_true_values - y_pred_values) ** 2))
    ss_tot = float(np.sum((y_true_values - np.mean(y_true_values)) ** 2)) or 1.0
    r_squared = 1.0 - (ss_res / ss_tot)
    rmse = float(np.sqrt(np.mean((y_true_values - y_pred_values) ** 2)))
    return float(r_squared), rmse


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
