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


def build_stacked_period_share_chart(
    df: pd.DataFrame,
    title: str,
) -> alt.Chart:
    color_scale = alt.Scale(
        domain=["Media leads", "Baseline leads", "Unexplained gap", "Hidden + unexplained gap"],
        range=["#4C78A8", "#72B7B2", "#F58518", "#F58518"],
    )
    base = alt.Chart(df).encode(
        x=alt.X("Period:N", title=None),
        y=alt.Y(
            "Value:Q",
            stack="normalize",
            title="Share of leads",
            axis=alt.Axis(format="%"),
        ),
        color=alt.Color("Segment:N", title="Lead source", scale=color_scale),
        order=alt.Order("SegmentOrder:Q"),
        tooltip=[
            alt.Tooltip("Period:N", title="Period"),
            alt.Tooltip("Segment:N", title="Lead source"),
            alt.Tooltip("Value:Q", title="Leads", format=",.2f"),
            alt.Tooltip("SharePct:Q", title="Share (%)", format=".1f"),
            alt.Tooltip("TotalLeads:Q", title="Total leads", format=",.2f"),
        ],
    )
    bars = base.mark_bar(size=120)
    labels = base.mark_text(color="white", baseline="middle").encode(
        text=alt.Text("ShareLabel:N")
    )
    total_labels = (
        alt.Chart(df.drop_duplicates(subset=["Period"]))
        .mark_text(dy=-12, fontWeight="bold")
        .encode(
            x=alt.X("Period:N", title=None),
            y=alt.value(0),
            text=alt.Text("TotalLabel:N"),
        )
    )
    return (bars + labels + total_labels).properties(title=title, height=320, width="container")


def build_stacked_time_decomposition_chart(
    df: pd.DataFrame,
    title: str,
    share_mode: bool = False,
) -> alt.Chart:
    special_colors = {
        "baseline": "#72B7B2",
        "unexplained_gap": "#F58518",
        "other": "#B279A2",
    }
    palette = [
        "#4C78A8",
        "#54A24B",
        "#E45756",
        "#F58518",
        "#EECA3B",
        "#B279A2",
        "#FF9DA6",
        "#9D755D",
        "#BAB0AC",
    ]
    domain = list(pd.unique(df["variable"]))
    used_special = {name for name in domain if name in special_colors}
    non_special = [name for name in domain if name not in special_colors]
    range_values = []
    palette_idx = 0
    for name in domain:
        if name in special_colors:
            range_values.append(special_colors[name])
        else:
            range_values.append(palette[palette_idx % len(palette)])
            palette_idx += 1
    color_scale = alt.Scale(domain=domain, range=range_values)
    y_encoding = (
        alt.Y("leads:Q", stack="normalize", title="Share of leads", axis=alt.Axis(format="%"))
        if share_mode
        else alt.Y("sum(leads):Q", title="Leads")
    )
    base = alt.Chart(df).encode(
        x=alt.X("date:T", title="Date"),
        y=y_encoding,
        color=alt.Color("variable:N", title="Variable", scale=color_scale),
        order=alt.Order("SegmentOrder:Q"),
        tooltip=[
            alt.Tooltip("date:T", title="Date"),
            alt.Tooltip("variable:N", title="Variable"),
            alt.Tooltip("leads:Q", title="Leads", format=",.2f"),
            alt.Tooltip("share_pct:Q", title="Share (%)", format=".1f"),
            alt.Tooltip("total_leads:Q", title="Total leads", format=",.2f"),
        ],
    )
    bars = base.mark_bar()
    labels = base.mark_text(color="white", baseline="middle").encode(
        text=alt.Text("segment_label:N")
    )
    total_label_y = alt.value(0) if share_mode else alt.Y("total_leads:Q", title="Leads")
    total_label_dy = -12 if share_mode else -10
    total_labels = (
        alt.Chart(df.drop_duplicates(subset=["date"]))
        .mark_text(dy=total_label_dy, fontWeight="bold")
        .encode(
            x=alt.X("date:T", title="Date"),
            y=total_label_y,
            text=alt.Text("total_label:N"),
        )
    )
    return (bars + labels + total_labels).properties(title=title, height=320, width="container")


def build_actual_vs_predicted_chart(
    df: pd.DataFrame,
    title: str,
) -> alt.Chart:
    line = (
        alt.Chart(df)
        .mark_line(point=True)
        .encode(
            x=alt.X("date:T", title="Date"),
            y=alt.Y("leads:Q", title="Leads"),
            color=alt.Color("series:N", title="Series"),
            tooltip=[
                alt.Tooltip("date:T", title="Date"),
                alt.Tooltip("series:N", title="Series"),
                alt.Tooltip("leads:Q", title="Leads", format=",.2f"),
            ],
        )
    )
    labels = (
        alt.Chart(df)
        .mark_text(dy=-10)
        .encode(
            x=alt.X("date:T", title="Date"),
            y=alt.Y("leads:Q", title="Leads"),
            color=alt.Color("series:N", title="Series"),
            text=alt.Text("label:N"),
        )
    )
    return (line + labels).properties(title=title, height=320, width="container")


def build_spend_vs_contribution_chart(
    df: pd.DataFrame,
    title: str,
) -> alt.Chart:
    rule = (
        alt.Chart(df)
        .mark_rule(color="#B0B0B0")
        .encode(
            y=alt.Y("Channel:N", title=None),
            x=alt.X("MinShare:Q", title="Share (%)"),
            x2="MaxShare:Q",
        )
    )
    points = (
        alt.Chart(df)
        .mark_point(filled=True, size=110)
        .encode(
            y=alt.Y("Channel:N", title=None, sort="-x"),
            x=alt.X("SharePct:Q", title="Share (%)"),
            color=alt.Color("Metric:N", title="Metric"),
            tooltip=[
                alt.Tooltip("Channel:N", title="Channel"),
                alt.Tooltip("Metric:N", title="Metric"),
                alt.Tooltip("SharePct:Q", title="Share (%)", format=".1f"),
                alt.Tooltip("Total:Q", title="Total", format=",.2f"),
            ],
        )
    )
    labels = (
        alt.Chart(df)
        .mark_text(dx=8, baseline="middle")
        .encode(
            y=alt.Y("Channel:N", title=None, sort="-x"),
            x=alt.X("SharePct:Q", title="Share (%)"),
            color=alt.Color("Metric:N", title="Metric"),
            text=alt.Text("Label:N"),
        )
    )
    return (rule + points + labels).properties(title=title, height=max(220, 42 * len(df["Channel"].unique())), width="container")


def compute_display_attribution(
    result: Any,
    actual_values: np.ndarray,
    row_mask: np.ndarray | None = None,
) -> tuple[dict[str, float], float, float]:
    channel_vectors, baseline_vector, unexplained_vector = compute_display_attribution_vectors(
        result,
        actual_values,
        row_mask=row_mask,
    )
    display_channel_totals = {
        channel: float(np.sum(values))
        for channel, values in channel_vectors.items()
    }
    display_baseline_total = float(np.sum(baseline_vector))
    display_unexplained_total = float(np.sum(unexplained_vector))

    if math.isclose(display_unexplained_total, 0.0, abs_tol=0.5):
        display_unexplained_total = 0.0

    return display_channel_totals, display_baseline_total, display_unexplained_total


def compute_display_attribution_vectors(
    result: Any,
    actual_values: np.ndarray,
    row_mask: np.ndarray | None = None,
) -> tuple[dict[str, np.ndarray], np.ndarray, np.ndarray]:
    actual_array = np.asarray(actual_values, dtype=np.float64)
    if row_mask is None:
        row_mask = np.ones_like(result.baseline, dtype=bool)

    selected_actuals = np.asarray(actual_array[row_mask], dtype=np.float64)
    if selected_actuals.size == 0:
        return (
            {channel: np.zeros(0, dtype=np.float64) for channel in result.channel_names},
            np.zeros(0, dtype=np.float64),
            np.zeros(0, dtype=np.float64),
        )

    channel_vectors = {
        channel: np.zeros_like(selected_actuals, dtype=np.float64)
        for channel in result.channel_names
    }
    baseline_vector = np.zeros_like(selected_actuals, dtype=np.float64)
    unexplained_vector = np.zeros_like(selected_actuals, dtype=np.float64)

    selected_indices = np.flatnonzero(row_mask)
    for pos, idx in enumerate(selected_indices):
        actual_value = max(float(selected_actuals[pos]), 0.0)
        raw_channel_values = {
            channel: max(float(result.contribution[channel][idx]), 0.0)
            for channel in result.channel_names
        }
        raw_baseline_value = max(float(result.baseline[idx]), 0.0)
        raw_explained_value = sum(raw_channel_values.values()) + raw_baseline_value

        if math.isclose(raw_explained_value, 0.0):
            unexplained_vector[pos] = actual_value
            continue

        scale_factor = min(1.0, actual_value / raw_explained_value)
        explained_total = 0.0
        for channel, value in raw_channel_values.items():
            scaled_value = value * scale_factor
            channel_vectors[channel][pos] = scaled_value
            explained_total += scaled_value
        baseline_vector[pos] = raw_baseline_value * scale_factor
        explained_total += baseline_vector[pos]
        unexplained_vector[pos] = max(actual_value - explained_total, 0.0)

    return channel_vectors, baseline_vector, unexplained_vector


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
    grain = infer_grain(ordered_dates)
    max_date = ordered_dates.max()
    if grain == "weekly":
        threshold_date = max_date - pd.Timedelta(weeks=max(window_size - 1, 0))
        return (ordered_dates >= threshold_date).to_numpy(dtype=bool)
    if grain == "daily":
        threshold_date = max_date - pd.Timedelta(days=max((window_size * 7) - 1, 0))
        return (ordered_dates >= threshold_date).to_numpy(dtype=bool)

    keep_count = min(window_size, len(ordered_dates))
    row_mask = np.zeros(len(ordered_dates), dtype=bool)
    row_mask[-keep_count:] = True
    return row_mask


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
