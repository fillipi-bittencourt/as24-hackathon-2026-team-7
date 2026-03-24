from __future__ import annotations

import math
from typing import Any

import altair as alt
import numpy as np
import pandas as pd

LOW_SPEND_QUANTILE = 0.2
MIN_BASELINE_SHARE = 0.1
MAX_BASELINE_SHARE = 0.6

CHART_TEXT = "#3D3120"
CHART_GRID = "#E8DEC3"
CHART_DOMAIN = "#D7C8A2"
CHART_RULE = "#B9A883"
CHART_BACKGROUND = "#FFFDF7"
CHART_PLOT_BACKGROUND = "#FFF8E6"
CHART_ACCENT = "#D4A017"
CHART_ACCENT_DARK = "#B7791F"
CHART_ACCENT_DEEP = "#8F5B13"
CHART_NEUTRAL = "#A88E5D"
CHART_NEUTRAL_LIGHT = "#CDB98C"
CHART_NEUTRAL_PALE = "#F3E2AE"
CHART_LABEL = "#4A3818"
CHART_SERIES_PALETTE = [
    "#D4A017",
    "#B7791F",
    "#8F5B13",
    "#CDB98C",
    "#A88E5D",
    "#F3E2AE",
    "#6A4700",
    "#E2C15B",
    "#BFA36A",
]


def apply_chart_theme(chart: alt.Chart) -> alt.Chart:
    return (
        chart.configure(background=CHART_BACKGROUND)
        .configure_view(
            stroke=CHART_DOMAIN,
            strokeOpacity=0.55,
            fill=CHART_PLOT_BACKGROUND,
            cornerRadius=14,
        )
        .configure_axis(
            gridColor=CHART_GRID,
            gridOpacity=0.75,
            domainColor=CHART_DOMAIN,
            tickColor=CHART_DOMAIN,
            labelColor=CHART_TEXT,
            titleColor=CHART_TEXT,
            labelFontSize=12,
            titleFontSize=12,
        )
        .configure_legend(
            orient="bottom",
            direction="horizontal",
            titleColor=CHART_TEXT,
            labelColor=CHART_TEXT,
            padding=10,
            symbolSize=110,
        )
        .configure_title(
            anchor="start",
            color=CHART_TEXT,
            fontSize=16,
            fontWeight=700,
            offset=12,
        )
    )


def style_chart(chart: alt.Chart, *, title: str, height: int) -> alt.Chart:
    return apply_chart_theme(
        chart.properties(title=title, height=height, width="container")
    )


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
    if 28 <= median_days <= 31:
        return "monthly"
    return None


def get_time_granularity_options(date_series: pd.Series) -> list[str]:
    grain = infer_grain(pd.to_datetime(date_series))
    if grain == "daily":
        return ["Daily", "Weekly", "Monthly"]
    if grain == "weekly":
        return ["Weekly", "Monthly"]
    return ["Monthly"]


def get_default_time_granularity(date_series: pd.Series) -> str:
    options = get_time_granularity_options(date_series)
    if "Weekly" in options:
        return "Weekly"
    return options[0]


def aggregate_time_series_df(
    df: pd.DataFrame,
    *,
    date_col: str,
    value_columns: list[str],
    granularity: str,
) -> pd.DataFrame:
    chart_df = df[[date_col, *value_columns]].copy()
    chart_df[date_col] = pd.to_datetime(chart_df[date_col])
    if granularity == "Daily":
        return chart_df.sort_values(date_col).reset_index(drop=True)
    if granularity == "Weekly":
        grouped = (
            chart_df.assign(period=chart_df[date_col].dt.to_period("W").dt.start_time)
            .groupby("period", as_index=False)[value_columns]
            .sum()
            .rename(columns={"period": date_col})
        )
        return grouped.sort_values(date_col).reset_index(drop=True)
    if granularity == "Monthly":
        grouped = (
            chart_df.assign(period=chart_df[date_col].dt.to_period("M").dt.to_timestamp())
            .groupby("period", as_index=False)[value_columns]
            .sum()
            .rename(columns={"period": date_col})
        )
        return grouped.sort_values(date_col).reset_index(drop=True)
    return chart_df.sort_values(date_col).reset_index(drop=True)


def infer_granularity_scale_factor(date_series: pd.Series, granularity: str) -> float:
    dated = pd.to_datetime(date_series).dropna().sort_values()
    if dated.empty:
        return 1.0
    source_grain = infer_grain(dated) or "daily"
    if granularity == "Daily" or source_grain == granularity.lower():
        return 1.0
    grouped = aggregate_time_series_df(
        pd.DataFrame({"date": dated, "value": np.ones(len(dated), dtype=np.float64)}),
        date_col="date",
        value_columns=["value"],
        granularity=granularity,
    )
    if grouped.empty:
        return 1.0
    typical_bucket_size = float(grouped["value"].median())
    return max(1.0, typical_bucket_size)


def format_number(value: float) -> str:
    return f"{value:,.0f}"


def format_currency(value: float) -> str:
    return f"EUR {value:,.0f}"


def is_rankable_cpl(value: float | None) -> bool:
    if value is None:
        return False
    if math.isnan(value) or math.isinf(value):
        return False
    return value > 0


def format_cpl(value: float | None) -> str:
    if not is_rankable_cpl(value):
        return "N/A"
    return f"{value:,.2f}"


def format_signed_number(value: float) -> str:
    return f"{value:,.0f}"


def pick_best_channel(cpl_map: dict[str, float]) -> tuple[str | None, float | None]:
    finite = {
        name: value
        for name, value in cpl_map.items()
        if is_rankable_cpl(value)
    }
    if not finite:
        return None, None
    name, value = min(finite.items(), key=lambda item: item[1])
    return name, value


def pick_worst_channel(cpl_map: dict[str, float]) -> tuple[str | None, float | None]:
    finite = {
        name: value
        for name, value in cpl_map.items()
        if is_rankable_cpl(value)
    }
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
    bars = base.mark_bar(cornerRadiusEnd=8, color=CHART_ACCENT).encode(
        tooltip=[
            alt.Tooltip(f"{category_col}:N", title="Item"),
            alt.Tooltip(f"{value_col}:Q", title="Value", format=",.2f"),
        ]
    )
    labels = base.mark_text(align="left", baseline="middle", dx=4).encode(
        text=alt.Text(f"{label_col}:N")
    )
    return style_chart(
        bars + labels,
        title=title,
        height=max(180, 36 * len(df)),
    )


def build_signed_bar_chart(
    df: pd.DataFrame,
    category_col: str,
    value_col: str,
    label_col: str,
    title: str,
) -> alt.Chart:
    chart_df = df.copy()
    chart_df["Sign"] = np.where(chart_df[value_col] >= 0, "Positive", "Negative")
    min_value = float(chart_df[value_col].min()) if not chart_df.empty else 0.0
    max_value = float(chart_df[value_col].max()) if not chart_df.empty else 0.0
    domain_extent = max(abs(min_value), abs(max_value), 1.0) * 1.15
    base = alt.Chart(chart_df).encode(
        x=alt.X(
            f"{value_col}:Q",
            title=None,
            scale=alt.Scale(domain=[-domain_extent, domain_extent]),
        ),
        y=alt.Y(f"{category_col}:N", sort=None, title=None),
        color=alt.Color(
            "Sign:N",
            title=None,
            scale=alt.Scale(
                domain=["Positive", "Negative"],
                range=[CHART_ACCENT, CHART_ACCENT_DEEP],
            ),
        ),
        tooltip=[
            alt.Tooltip(f"{category_col}:N", title="Item"),
            alt.Tooltip(f"{value_col}:Q", title="Value", format=",.2f"),
        ],
    )
    bars = base.mark_bar(cornerRadiusEnd=8)
    positive_labels = (
        base.transform_filter(f"datum.{value_col} >= 0")
        .mark_text(align="left", baseline="middle", dx=4)
        .encode(text=alt.Text(f"{label_col}:N"))
    )
    negative_labels = (
        base.transform_filter(f"datum.{value_col} < 0")
        .mark_text(align="right", baseline="middle", dx=-4)
        .encode(text=alt.Text(f"{label_col}:N"))
    )
    zero_rule = alt.Chart(pd.DataFrame({value_col: [0.0]})).mark_rule(color=CHART_RULE).encode(
        x=alt.X(f"{value_col}:Q")
    )
    return style_chart(
        zero_rule + bars + positive_labels + negative_labels,
        title=title,
        height=max(180, 36 * len(chart_df)),
    )


def build_stacked_period_share_chart(
    df: pd.DataFrame,
    title: str,
) -> alt.Chart:
    color_scale = alt.Scale(
        domain=["Media leads", "Baseline leads", "Unexplained gap", "Hidden + unexplained gap"],
        range=[CHART_ACCENT, CHART_NEUTRAL_LIGHT, CHART_ACCENT_DARK, CHART_ACCENT_DARK],
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
    labels = base.mark_text(color=CHART_LABEL, baseline="middle").encode(
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
    return style_chart(bars + labels + total_labels, title=title, height=320)


def build_stacked_time_decomposition_chart(
    df: pd.DataFrame,
    title: str,
    share_mode: bool = False,
) -> alt.Chart:
    special_colors = {
        "baseline": CHART_NEUTRAL_LIGHT,
        "unexplained_gap": CHART_ACCENT_DARK,
        "residual_gap": CHART_ACCENT_DARK,
        "other": CHART_NEUTRAL,
    }
    palette = CHART_SERIES_PALETTE
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
    labels = base.mark_text(color=CHART_LABEL, baseline="middle").encode(
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
    return style_chart(bars + labels + total_labels, title=title, height=320)


def build_actual_vs_predicted_chart(
    df: pd.DataFrame,
    title: str,
) -> alt.Chart:
    final_points = (
        df.sort_values(["series", "date"])
        .groupby("series", as_index=False)
        .tail(1)
        .assign(end_label=lambda frame: frame["series"] + ": " + frame["leads"].round(0).astype(int).astype(str))
    )
    line = (
        alt.Chart(df)
        .mark_line(point=True, strokeWidth=3)
        .encode(
            x=alt.X("date:T", title="Date"),
            y=alt.Y("leads:Q", title="Leads"),
            color=alt.Color(
                "series:N",
                title="Series",
                scale=alt.Scale(
                    domain=["Actual leads", "Predicted leads"],
                    range=[CHART_ACCENT_DEEP, CHART_ACCENT],
                ),
            ),
            tooltip=[
                alt.Tooltip("date:T", title="Date"),
                alt.Tooltip("series:N", title="Series"),
                alt.Tooltip("leads:Q", title="Leads", format=",.2f"),
            ],
        )
    )
    labels = (
        alt.Chart(final_points)
        .mark_text(align="left", dx=8, dy=-8, fontWeight="bold")
        .encode(
            x=alt.X("date:T", title="Date"),
            y=alt.Y("leads:Q", title="Leads"),
            color=alt.Color("series:N", title="Series"),
            text=alt.Text("end_label:N"),
        )
    )
    return style_chart(line + labels, title=title, height=320)


def build_single_series_line_chart(
    df: pd.DataFrame,
    *,
    date_col: str,
    value_col: str,
    title: str,
    series_name: str,
    height: int = 320,
) -> alt.Chart:
    chart_df = df.copy()
    final_point = chart_df.sort_values(date_col).tail(1).copy()
    final_point["end_label"] = (
        series_name + ": " + final_point[value_col].round(0).astype(int).astype(str)
    )
    line = (
        alt.Chart(chart_df)
        .mark_line(point=True, strokeWidth=3, color=CHART_ACCENT_DARK)
        .encode(
            x=alt.X(f"{date_col}:T", title="Date"),
            y=alt.Y(f"{value_col}:Q", title=series_name),
            tooltip=[
                alt.Tooltip(f"{date_col}:T", title="Date"),
                alt.Tooltip(f"{value_col}:Q", title=series_name, format=",.2f"),
            ],
        )
    )
    label = (
        alt.Chart(final_point)
        .mark_text(align="left", dx=8, dy=-8, fontWeight="bold", color=CHART_LABEL)
        .encode(
            x=alt.X(f"{date_col}:T", title="Date"),
            y=alt.Y(f"{value_col}:Q", title=series_name),
            text=alt.Text("end_label:N"),
        )
    )
    return style_chart(line + label, title=title, height=height)


def build_spend_vs_contribution_chart(
    df: pd.DataFrame,
    title: str,
) -> alt.Chart:
    rule = (
        alt.Chart(df)
        .mark_rule(color=CHART_RULE)
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
            color=alt.Color(
                "Metric:N",
                title="Metric",
                scale=alt.Scale(
                    domain=["Spend share", "Contribution share"],
                    range=[CHART_NEUTRAL_LIGHT, CHART_ACCENT],
                ),
            ),
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
    return style_chart(
        rule + points + labels,
        title=title,
        height=max(220, 42 * len(df["Channel"].unique())),
    )


def compute_faithful_attribution(
    result: Any,
    actual_values: np.ndarray,
    row_mask: np.ndarray | None = None,
) -> tuple[dict[str, float], float, float]:
    channel_vectors, baseline_vector, residual_vector = compute_faithful_attribution_vectors(
        result,
        actual_values,
        row_mask=row_mask,
    )
    channel_totals = {
        channel: float(np.sum(values))
        for channel, values in channel_vectors.items()
    }
    baseline_total = float(np.sum(baseline_vector))
    residual_total = float(np.sum(residual_vector))
    return channel_totals, baseline_total, residual_total


def compute_faithful_attribution_vectors(
    result: Any,
    actual_values: np.ndarray,
    row_mask: np.ndarray | None = None,
) -> tuple[dict[str, np.ndarray], np.ndarray, np.ndarray]:
    actual_array = np.asarray(actual_values, dtype=np.float64)
    y_pred_array = np.asarray(result.y_pred, dtype=np.float64)
    if row_mask is None:
        row_mask = np.ones_like(y_pred_array, dtype=bool)

    channel_vectors = {
        channel: np.asarray(result.contribution[channel][row_mask], dtype=np.float64)
        for channel in result.channel_names
    }
    baseline_vector = np.asarray(result.baseline[row_mask], dtype=np.float64)
    residual_vector = np.asarray(actual_array[row_mask] - y_pred_array[row_mask], dtype=np.float64)
    return channel_vectors, baseline_vector, residual_vector


def compute_display_attribution(
    result: Any,
    actual_values: np.ndarray,
    row_mask: np.ndarray | None = None,
    total_spend_series: np.ndarray | None = None,
) -> tuple[dict[str, float], float, float]:
    channel_vectors, baseline_vector, unexplained_vector = compute_display_attribution_vectors(
        result,
        actual_values,
        row_mask=row_mask,
        total_spend_series=total_spend_series,
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
    total_spend_series: np.ndarray | None = None,
) -> tuple[dict[str, np.ndarray], np.ndarray, np.ndarray]:
    actual_array = np.asarray(actual_values, dtype=np.float64)
    if row_mask is None:
        row_mask = np.ones_like(result.baseline, dtype=bool)
    structural_baseline_share = estimate_structural_baseline_share(
        actual_array,
        total_spend_series,
    )

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
        baseline_floor = actual_value * structural_baseline_share
        bounded_baseline_value = min(
            actual_value,
            max(raw_baseline_value, baseline_floor),
        )
        remaining_actual = max(actual_value - bounded_baseline_value, 0.0)
        raw_media_total = sum(raw_channel_values.values())

        explained_media_total = 0.0
        if not math.isclose(raw_media_total, 0.0):
            media_scale_factor = min(1.0, remaining_actual / raw_media_total)
            for channel, value in raw_channel_values.items():
                scaled_value = value * media_scale_factor
                channel_vectors[channel][pos] = scaled_value
                explained_media_total += scaled_value
        baseline_vector[pos] = bounded_baseline_value
        unexplained_vector[pos] = max(actual_value - baseline_vector[pos] - explained_media_total, 0.0)

    return channel_vectors, baseline_vector, unexplained_vector


def estimate_structural_baseline_share(
    actual_values: np.ndarray,
    total_spend_series: np.ndarray | None,
) -> float:
    actual_array = np.asarray(actual_values, dtype=np.float64)
    if total_spend_series is None:
        return MIN_BASELINE_SHARE

    spend_array = np.asarray(total_spend_series, dtype=np.float64)
    valid_mask = np.isfinite(actual_array) & np.isfinite(spend_array) & (actual_array >= 0)
    if not np.any(valid_mask):
        return MIN_BASELINE_SHARE

    valid_actual = actual_array[valid_mask]
    valid_spend = spend_array[valid_mask]
    if valid_actual.size == 0:
        return MIN_BASELINE_SHARE

    overall_median_actual = float(np.median(valid_actual))
    if math.isclose(overall_median_actual, 0.0):
        return MIN_BASELINE_SHARE

    spend_threshold = float(np.quantile(valid_spend, LOW_SPEND_QUANTILE))
    low_spend_mask = valid_spend <= spend_threshold
    if not np.any(low_spend_mask):
        return MIN_BASELINE_SHARE

    low_spend_actual = valid_actual[low_spend_mask]
    anchor_share = float(np.median(low_spend_actual)) / overall_median_actual
    return float(np.clip(anchor_share, MIN_BASELINE_SHARE, MAX_BASELINE_SHARE))


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
