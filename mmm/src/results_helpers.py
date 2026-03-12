from __future__ import annotations

import math
from typing import Any

import altair as alt
import numpy as np
import pandas as pd


def infer_grain(date_series: pd.Series) -> str | None:
    ordered = date_series.sort_values().dropna()
    if len(ordered) < 2:
        return None
    diffs = ordered.diff().dropna().dt.days
    if diffs.empty:
        return None
    median_days = float(diffs.median())
    if 1 <= median_days <= 2:
        return "daily"
    if 6 <= median_days <= 8:
        return "weekly"
    return None


def format_number(value: float) -> str:
    return f"{value:,.0f}"


def format_currency(value: float) -> str:
    return f"EUR {value:,.0f}"


def format_cpl(value: float | None) -> str:
    if value is None or math.isinf(value) or math.isnan(value):
        return "N/A"
    return f"EUR {value:,.2f} per lead"


def format_signed_number(value: float) -> str:
    return f"{value:,.0f}"


def pick_best_channel(cpl_map: dict[str, float]) -> tuple[str | None, float | None]:
    finite = {name: value for name, value in cpl_map.items() if not math.isinf(value)}
    if not finite:
        return None, None
    name, value = min(finite.items(), key=lambda item: item[1])
    return name, value


def pick_worst_channel(cpl_map: dict[str, float]) -> tuple[str | None, float | None]:
    finite = {name: value for name, value in cpl_map.items() if not math.isinf(value)}
    if not finite:
        return None, None
    name, value = max(finite.items(), key=lambda item: item[1])
    return name, value


def build_labeled_bar_chart(
    df: pd.DataFrame,
    category_col: str,
    value_col: str,
    label_col: str,
    title: str,
) -> alt.Chart:
    max_value = float(df[value_col].max()) if not df.empty else 0.0
    padded_max = max_value * 1.15 if max_value > 0 else 1.0
    base = alt.Chart(df).encode(
        x=alt.X(
            f"{value_col}:Q",
            title=None,
            scale=alt.Scale(domain=[0, padded_max]),
        ),
        y=alt.Y(f"{category_col}:N", sort="-x", title=None),
    )
    bars = base.mark_bar().encode(
        tooltip=[
            alt.Tooltip(f"{category_col}:N", title="Item"),
            alt.Tooltip(f"{value_col}:Q", title="Value", format=",.2f"),
        ]
    )
    labels = base.mark_text(align="left", baseline="middle", dx=4).encode(
        text=alt.Text(f"{label_col}:N")
    )
    return (bars + labels).properties(
        title=title,
        height=max(180, 36 * len(df)),
        width="container",
    )


def compute_display_attribution(
    result: Any,
    actual_total: float,
    row_mask: np.ndarray | None = None,
) -> tuple[dict[str, float], float, float]:
    if row_mask is None:
        row_mask = np.ones_like(result.baseline, dtype=bool)

    raw_channel_totals = {
        channel: max(float(result.contribution[channel][row_mask].sum()), 0.0)
        for channel in result.channel_names
    }
    raw_baseline_total = max(float(result.baseline[row_mask].sum()), 0.0)
    raw_explained_total = sum(raw_channel_totals.values()) + raw_baseline_total

    if math.isclose(actual_total, 0.0) or math.isclose(raw_explained_total, 0.0):
        return (
            {channel: 0.0 for channel in result.channel_names},
            0.0,
            max(actual_total, 0.0),
        )

    scale_factor = min(1.0, actual_total / raw_explained_total)
    display_channel_totals = {
        channel: value * scale_factor for channel, value in raw_channel_totals.items()
    }
    display_baseline_total = raw_baseline_total * scale_factor
    display_unexplained_total = max(
        actual_total - (sum(display_channel_totals.values()) + display_baseline_total),
        0.0,
    )

    if math.isclose(display_unexplained_total, 0.0, abs_tol=0.5):
        display_unexplained_total = 0.0

    return display_channel_totals, display_baseline_total, display_unexplained_total


def build_period_mask(
    date_series: pd.Series,
    period_label: str,
) -> np.ndarray:
    if period_label == "All data":
        return np.ones(len(date_series), dtype=bool)

    windows = {
        "Last 4 weeks": 4,
        "Last 8 weeks": 8,
        "Last 12 weeks": 12,
        "Last 26 weeks": 26,
    }
    window_size = windows.get(period_label)
    if window_size is None:
        return np.ones(len(date_series), dtype=bool)

    ordered_dates = pd.to_datetime(date_series).reset_index(drop=True)
    if ordered_dates.empty:
        return np.ones(len(date_series), dtype=bool)
    max_date = ordered_dates.max()
    threshold_date = max_date - pd.Timedelta(weeks=window_size)
    return (ordered_dates >= threshold_date).to_numpy(dtype=bool)


def compute_mape_non_zero(y_true: np.ndarray, y_pred: np.ndarray) -> tuple[float | None, str]:
    mask = y_true != 0
    used = int(np.sum(mask))
    total = int(len(y_true))
    if used == 0:
        return None, f"0/{total}"
    mape_value = float(np.mean(np.abs((y_true[mask] - y_pred[mask]) / y_true[mask])) * 100)
    return mape_value, f"{used}/{total}"


def compute_view_channel_metrics(
    df: pd.DataFrame,
    channel_names: list[str],
    period_mask: np.ndarray,
    display_channel_totals: dict[str, float],
) -> tuple[dict[str, float], dict[str, float]]:
    spend_totals: dict[str, float] = {}
    cpl_map: dict[str, float] = {}
    for channel in channel_names:
        spend_total = float(df.loc[period_mask, channel].sum())
        spend_totals[channel] = spend_total
        attributed = float(display_channel_totals.get(channel, 0.0))
        cpl_map[channel] = spend_total / attributed if attributed > 0 else float("inf")
    return spend_totals, cpl_map
