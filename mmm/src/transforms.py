from __future__ import annotations

import numpy as np
import pandas as pd


def geometric_adstock(x: np.ndarray, theta: float) -> np.ndarray:
    values = np.asarray(x, dtype=np.float64)
    output = np.zeros_like(values, dtype=np.float64)

    if values.size == 0:
        return output

    output[0] = values[0]
    for idx in range(1, len(values)):
        output[idx] = values[idx] + theta * output[idx - 1]

    return output


def hill_saturation(x: np.ndarray, alpha: float, k: float) -> np.ndarray:
    values = np.asarray(x, dtype=np.float64)
    if np.isclose(k, 0.0):
        return np.zeros_like(values, dtype=np.float64)

    numerator = np.power(values, alpha, dtype=np.float64)
    denominator = np.power(k, alpha, dtype=np.float64) + numerator
    with np.errstate(divide="ignore", invalid="ignore"):
        saturated = np.divide(
            numerator,
            denominator,
            out=np.zeros_like(values, dtype=np.float64),
            where=denominator != 0,
        )
    return saturated.astype(np.float64)


def log_saturation(x: np.ndarray) -> np.ndarray:
    values = np.asarray(x, dtype=np.float64)
    return np.log1p(values).astype(np.float64)


def transform_media(
    df: pd.DataFrame,
    channel_cols: list[str],
    adstock_params: dict[str, float],
    saturation_params: dict[str, dict[str, float]],
    adstock_type: dict[str, str] | None = None,
    saturation_type: dict[str, str] | None = None,
    control_cols: list[str] | None = None,
) -> np.ndarray:
    adstock_choice = adstock_type or {}
    saturation_choice = saturation_type or {}
    controls = control_cols or []
    columns: list[np.ndarray] = []

    for ch in channel_cols:
        series = df[ch].to_numpy(dtype=np.float64)

        if adstock_choice.get(ch, "geometric") == "geometric":
            series = geometric_adstock(series, float(adstock_params.get(ch, 0.0)))

        saturation_kind = saturation_choice.get(ch, "log")
        if saturation_kind == "hill":
            params = saturation_params.get(ch, {"alpha": 1.0, "k": 1.0})
            series = hill_saturation(
                series,
                float(params.get("alpha", 1.0)),
                float(params.get("k", 1.0)),
            )
        elif saturation_kind == "log":
            series = log_saturation(series)

        columns.append(series.astype(np.float64))

    for col in controls:
        columns.append(df[col].to_numpy(dtype=np.float64))

    if not columns:
        return np.empty((len(df), 0), dtype=np.float64)

    return np.column_stack(columns).astype(np.float64)
