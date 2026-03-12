from __future__ import annotations

import numpy as np
from sklearn.linear_model import ElasticNet

from .base import ModelResult, build_model_result


class ElasticNetModel:
    def __init__(self) -> None:
        self._model: ElasticNet | None = None

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
        self._model.fit(X_values, y_values)
        y_pred = np.asarray(self._model.predict(X_values), dtype=np.float64)
        coefficients = {
            ch: float(self._model.coef_[idx]) for idx, ch in enumerate(channel_names)
        }

        return build_model_result(
            model_name="ElasticNet",
            channel_names=channel_names,
            coefficients=coefficients,
            intercept=float(self._model.intercept_),
            raw_spend=raw_spend,
            X=X_values[:, :n_channels],
            y_pred=y_pred,
            r_squared=float(self._model.score(X_values, y_values)),
            rmse=float(np.sqrt(np.mean((y_values - y_pred) ** 2))),
        )

    def predict(self, X: np.ndarray) -> np.ndarray:
        if self._model is None:
            raise ValueError("Model has not been fitted")
        return np.asarray(self._model.predict(np.asarray(X, dtype=np.float64)), dtype=np.float64)
"""ElasticNet model. See docs/06_MODELS.md and 10_BUILD_MMM.md Step 3."""

# To be implemented: ElasticNetModel class with fit()
