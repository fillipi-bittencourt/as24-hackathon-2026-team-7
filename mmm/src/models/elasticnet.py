from __future__ import annotations

import numpy as np
from sklearn.linear_model import ElasticNet
from sklearn.preprocessing import StandardScaler

from .base import (
    ModelResult,
    build_model_result,
    compute_r_squared_and_rmse,
    fit_standardized_linear_model,
)


class ElasticNetModel:
    def __init__(self) -> None:
        self._model: ElasticNet | None = None
        self._scaler: StandardScaler | None = None

    def fit(
        self,
        X: np.ndarray,
        y: np.ndarray,
        raw_spend: dict[str, np.ndarray],
        **kwargs,
    ) -> ModelResult:
        channel_names: list[str] = kwargs["channel_names"]
        alpha = float(kwargs.get("alpha", kwargs.get("reg_alpha", 1.0)))
        l1_ratio = float(kwargs.get("l1_ratio", 0.5))
        X_values = np.asarray(X, dtype=np.float64)
        y_values = np.asarray(y, dtype=np.float64)
        n_channels = len(channel_names)

        self._model = ElasticNet(
            alpha=alpha,
            l1_ratio=l1_ratio,
            fit_intercept=True,
            random_state=42,
            max_iter=10000,
        )
        coefficients_array, intercept, y_pred, self._scaler = fit_standardized_linear_model(
            self._model,
            X_values,
            y_values,
        )
        coefficients = {
            ch: float(coefficients_array[idx]) for idx, ch in enumerate(channel_names)
        }
        r_squared, rmse = compute_r_squared_and_rmse(y_values, y_pred)

        return build_model_result(
            model_name="ElasticNet",
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
        if self._model is None or self._scaler is None:
            raise ValueError("Model has not been fitted")
        X_values = np.asarray(X, dtype=np.float64)
        return np.asarray(self._model.predict(self._scaler.transform(X_values)), dtype=np.float64)
