from __future__ import annotations

import numpy as np
import statsmodels.api as sm
import streamlit as st

from .base import ModelResult, build_model_result


class OLSModel:
    def __init__(self) -> None:
        self._result = None

    def fit(
        self,
        X: np.ndarray,
        y: np.ndarray,
        raw_spend: dict[str, np.ndarray],
        **kwargs,
    ) -> ModelResult:
        channel_names: list[str] = kwargs["channel_names"]
        X_values = np.asarray(X, dtype=np.float64)
        y_values = np.asarray(y, dtype=np.float64)

        if X_values.ndim == 1:
            X_values = X_values.reshape(-1, 1)

        X_with_const = sm.add_constant(X_values, has_constant="add")
        if len(y_values) < 3 * X_with_const.shape[1]:
            st.warning(
                f"Only {len(y_values)} rows for {X_with_const.shape[1]} parameters — model may be overfit. Add more data for reliable results."
            )

        self._result = sm.OLS(y_values, X_with_const).fit()
        n_channels = len(channel_names)
        y_pred = np.asarray(self._result.predict(X_with_const), dtype=np.float64)
        coefficients = {
            ch: float(self._result.params[1 + idx]) for idx, ch in enumerate(channel_names)
        }

        return build_model_result(
            model_name="OLS",
            channel_names=channel_names,
            coefficients=coefficients,
            intercept=float(self._result.params[0]),
            raw_spend=raw_spend,
            X=X_values[:, :n_channels],
            y_pred=y_pred,
            r_squared=float(self._result.rsquared),
            rmse=float(np.sqrt(np.mean(self._result.resid**2))),
        )

    def predict(self, X: np.ndarray) -> np.ndarray:
        if self._result is None:
            raise ValueError("Model has not been fitted")

        X_values = np.asarray(X, dtype=np.float64)
        if X_values.ndim == 1:
            X_values = X_values.reshape(-1, 1)

        X_with_const = sm.add_constant(X_values, has_constant="add")
        return np.asarray(self._result.predict(X_with_const), dtype=np.float64)
