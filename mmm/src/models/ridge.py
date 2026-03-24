from __future__ import annotations

import numpy as np

from .base import (
    ModelResult,
    build_model_result,
    compute_r_squared_and_rmse,
    fit_constrained_standardized_linear_model,
)


class RidgeModel:
    def __init__(self) -> None:
        self._intercept: float | None = None
        self._coefficients: np.ndarray | None = None

    def fit(
        self,
        X: np.ndarray,
        y: np.ndarray,
        raw_spend: dict[str, np.ndarray],
        **kwargs,
    ) -> ModelResult:
        channel_names: list[str] = kwargs["channel_names"]
        alpha = float(kwargs.get("alpha", kwargs.get("reg_alpha", 1.0)))
        X_values = np.asarray(X, dtype=np.float64)
        y_values = np.asarray(y, dtype=np.float64)
        n_channels = len(channel_names)

        constrained_fit = fit_constrained_standardized_linear_model(
            X_values,
            y_values,
            n_channels=n_channels,
            alpha=alpha,
            l1_ratio=0.0,
        )
        self._intercept = constrained_fit.intercept
        self._coefficients = constrained_fit.coefficients
        coefficients_array = self._coefficients
        intercept = self._intercept
        y_pred = constrained_fit.y_pred
        coefficients = {
            ch: float(coefficients_array[idx]) for idx, ch in enumerate(channel_names)
        }
        r_squared, rmse = compute_r_squared_and_rmse(y_values, y_pred)

        return build_model_result(
            model_name="Ridge",
            channel_names=channel_names,
            coefficients=coefficients,
            intercept=intercept,
            raw_spend=raw_spend,
            X=X_values[:, :n_channels],
            y_pred=y_pred,
            r_squared=r_squared,
            rmse=rmse,
        )

    def predict(self, X: np.ndarray) -> np.ndarray:
        if self._intercept is None or self._coefficients is None:
            raise ValueError("Model has not been fitted")
        X_values = np.asarray(X, dtype=np.float64)
        return np.asarray(
            float(self._intercept) + (X_values @ np.asarray(self._coefficients, dtype=np.float64)),
            dtype=np.float64,
        )
