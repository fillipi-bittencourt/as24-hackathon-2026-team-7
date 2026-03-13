from __future__ import annotations

import math
from typing import Any

import numpy as np
import pandas as pd
import streamlit as st
from statsmodels.stats.outliers_influence import variance_inflation_factor

from src.results_helpers import (
    aggregate_time_series_df,
    get_default_time_granularity,
    get_time_granularity_options,
    infer_grain,
)

MAX_VIF_INPUTS = 12


def render_data_overview_tab() -> None:
    if not st.session_state.get("valid") or st.session_state.get("df") is None:
        st.warning("Load and validate data in the Data tab first.")
        return

    df = st.session_state["df"]
    date_col = st.session_state["date_col"]
    target_col = st.session_state["target_col"]
    channel_cols = st.session_state.get("channel_cols", [])
    control_cols = st.session_state.get("control_cols", [])
    input_cols = [*channel_cols, *control_cols]
    target_values = df[target_col].astype(float)
    grain = infer_grain(df[date_col]) or "unknown"

    st.caption(
        "Use this step to inspect the validated dataset before choosing transforms or fitting models. Focus on coverage, target behavior, input quality, and overlap across selected inputs."
    )
    st.info(
        "Recommended reading order: check the top metrics first, then review the health tags, then inspect target behavior, spend aggregations, input diagnostics, and multicollinearity."
    )

    row_count = len(df)
    rows_per_parameter = row_count / max(1, 1 + len(input_cols))
    zero_target_pct = float((target_values == 0).mean() * 100)
    max_abs_corr = compute_max_abs_correlation(df, input_cols)
    coverage_risk = classify_input_coverage_risk(df, input_cols)

    top_col1, top_col2, top_col3, top_col4 = st.columns(4)
    top_col1.metric("Rows", f"{row_count:,}")
    top_col2.metric("Date grain", grain.title())
    top_col3.metric("Channels", str(len(channel_cols)))
    top_col4.metric("Controls", str(len(control_cols)))

    top_col5, top_col6, top_col7, top_col8 = st.columns(4)
    top_col5.metric(
        "Date range",
        f"{df[date_col].min().date()} to {df[date_col].max().date()}",
    )
    top_col6.metric("Rows per parameter", f"{rows_per_parameter:.1f}")
    top_col7.metric("Target total", f"{float(target_values.sum()):,.0f}")
    top_col8.metric("Zero-target rows", f"{zero_target_pct:.1f}%")

    st.subheader("Health tags")
    tag_col1, tag_col2, tag_col3, tag_col4 = st.columns(4)
    tag_col1.markdown(
        f"**Dataset health**  \n`{classify_dataset_health(rows_per_parameter, zero_target_pct)}`"
    )
    tag_col2.markdown(
        f"**Signal volatility**  \n`{classify_target_volatility(target_values)}`"
    )
    tag_col3.markdown(
        f"**Correlation risk**  \n`{classify_correlation_risk(max_abs_corr)}`"
    )
    tag_col4.markdown(
        f"**Input coverage**  \n`{coverage_risk}`"
    )

    st.subheader("Selected modeling scope")
    st.markdown(
        f"""
        **Target**: `{target_col}`

        **Channels**: {", ".join(f"`{name}`" for name in channel_cols) if channel_cols else "None"}

        **Controls**: {", ".join(f"`{name}`" for name in control_cols) if control_cols else "None"}
        """
    )

    st.subheader("Target behavior")
    st.caption(
        "This shows the validated target trend. Large spikes, long flat periods, or many zero rows can make model interpretation harder."
    )
    time_granularity_options = get_time_granularity_options(df[date_col])
    default_granularity = get_default_time_granularity(df[date_col])
    previous_granularity = st.session_state.get("overview_target_granularity", default_granularity)
    time_granularity = st.selectbox(
        "Target time-series granularity",
        options=time_granularity_options,
        index=time_granularity_options.index(previous_granularity)
        if previous_granularity in time_granularity_options
        else time_granularity_options.index(default_granularity),
        help="Choose how the target trend should be aggregated in the chart.",
        key="overview_target_granularity",
    )
    target_chart_df = build_overview_target_timeseries(
        df=df,
        date_col=date_col,
        target_col=target_col,
        granularity=time_granularity,
    )
    st.line_chart(target_chart_df, height=280)
    st.dataframe(build_overview_target_summary(target_values), width="stretch")

    st.subheader("Channel spend aggregations")
    if channel_cols:
        st.caption(
            "These are broad spend and coverage summaries for the selected channel inputs before transformations are applied."
        )
        st.dataframe(
            build_channel_aggregation_df(df, channel_cols),
            width="stretch",
        )
    else:
        st.info("No channels selected yet, so there is no spend aggregation table to show.")

    st.subheader("Input diagnostics")
    st.caption(
        "These are validated raw selected inputs before adstock or saturation. Use them as pre-model setup diagnostics, not as the final transformed model matrix."
    )
    diagnostics_df = build_overview_input_diagnostics(
        df=df,
        target_col=target_col,
        channel_cols=channel_cols,
        control_cols=control_cols,
    )
    st.dataframe(diagnostics_df, width="stretch")

    st.subheader("Multicollinearity checks")
    st.caption(
        "These are pre-model overlap checks on the validated raw selected inputs. They can be expensive on wide datasets, so advanced diagnostics run only when you ask for them."
    )
    if len(input_cols) < 2:
        st.info("Select at least two channel or control variables to evaluate multicollinearity.")
        return

    run_advanced = st.checkbox(
        "Run advanced multicollinearity diagnostics",
        value=False,
        key="overview_run_multicollinearity",
        help="Computes strongest overlap pairs and, for smaller input sets, VIF. Leave this off for a faster first read.",
    )
    if not run_advanced:
        st.info(
            "Advanced multicollinearity diagnostics are skipped by default for speed. Use the correlation risk tag above for a quick signal, or enable this check when you need deeper setup review."
        )
        return

    corr_pairs_df = build_overview_correlation_pairs(df, input_cols)
    high_corr_pairs = corr_pairs_df.loc[corr_pairs_df["Abs correlation"] >= 0.8]
    if not high_corr_pairs.empty:
        st.warning(
            "Some selected inputs are highly correlated. Compare Ridge and ElasticNet more carefully before trusting channel-level rankings."
        )

    st.markdown("**Strongest input correlations**")
    st.dataframe(corr_pairs_df.head(25), width="stretch")

    if len(input_cols) > MAX_VIF_INPUTS:
        st.info(
            f"VIF is skipped because {len(input_cols)} inputs are selected. Reduce the selected inputs to {MAX_VIF_INPUTS} or fewer if you want a deeper VIF check."
        )
        return

    vif_df = build_overview_vif_df(df, input_cols)
    high_vif_variables = vif_df.loc[
        vif_df["VIF"].fillna(0.0) >= 10.0,
        "Variable",
    ].tolist()
    if high_vif_variables:
        st.warning(
            "These inputs have very high VIF values: "
            + ", ".join(f"`{name}`" for name in high_vif_variables)
            + ". Expect unstable coefficient separation unless regularization and validation support the story."
        )

    st.markdown("**VIF by selected input**")
    st.caption(
        "VIF here is a setup heuristic on the validated raw selected inputs. Rough guide: above 5 deserves caution, above 10 is a strong warning sign."
    )
    st.dataframe(vif_df, width="stretch")


def build_overview_target_summary(target_series: pd.Series) -> pd.DataFrame:
    target_values = target_series.astype(float)
    mean_value = float(target_values.mean()) if len(target_values) > 0 else 0.0
    std_value = float(target_values.std(ddof=0)) if len(target_values) > 0 else 0.0
    cv_value = (std_value / abs(mean_value)) if not math.isclose(mean_value, 0.0) else 0.0
    return pd.DataFrame(
        [
            {"Metric": "Mean", "Value": round(mean_value, 2)},
            {"Metric": "Median", "Value": round(float(target_values.median()), 2)},
            {"Metric": "Std dev", "Value": round(std_value, 2)},
            {"Metric": "Min", "Value": round(float(target_values.min()), 2)},
            {"Metric": "Max", "Value": round(float(target_values.max()), 2)},
            {"Metric": "P10", "Value": round(float(target_values.quantile(0.10)), 2)},
            {"Metric": "P90", "Value": round(float(target_values.quantile(0.90)), 2)},
            {"Metric": "Coefficient of variation", "Value": round(cv_value, 3)},
        ]
    )


def build_channel_aggregation_df(df: pd.DataFrame, channel_cols: list[str]) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    total_spend = float(df[channel_cols].sum().sum()) if channel_cols else 0.0
    for channel in channel_cols:
        series = df[channel].astype(float)
        channel_total = float(series.sum())
        rows.append(
            {
                "Channel": channel,
                "Total spend": round(channel_total, 2),
                "Average per period": round(float(series.mean()), 2),
                "Median per period": round(float(series.median()), 2),
                "Non-zero periods (%)": round(float((series > 0).mean() * 100), 2),
                "Spend share (%)": round(
                    (channel_total / total_spend) * 100 if not math.isclose(total_spend, 0.0) else 0.0,
                    2,
                ),
                "Coverage tag": classify_coverage_tag(float((series > 0).mean() * 100)),
            }
        )
    return pd.DataFrame(rows).sort_values("Total spend", ascending=False).reset_index(drop=True)


def build_overview_input_diagnostics(
    *,
    df: pd.DataFrame,
    target_col: str,
    channel_cols: list[str],
    control_cols: list[str],
) -> pd.DataFrame:
    target_values = df[target_col].astype(float)
    rows: list[dict[str, Any]] = []
    for variable in [*channel_cols, *control_cols]:
        series = df[variable].astype(float)
        correlation = (
            series.corr(target_values)
            if series.nunique(dropna=True) >= 2 and target_values.nunique(dropna=True) >= 2
            else None
        )
        zero_pct = float((series == 0).mean() * 100)
        negative_pct = float((series < 0).mean() * 100)
        std_value = float(series.std(ddof=0))
        rows.append(
            {
                "Variable": variable,
                "Type": "Channel" if variable in channel_cols else "Control",
                "Mean": round(float(series.mean()), 2),
                "Median": round(float(series.median()), 2),
                "Std dev": round(std_value, 4),
                "Min": round(float(series.min()), 2),
                "Max": round(float(series.max()), 2),
                "Zero rows (%)": round(zero_pct, 2),
                "Negative rows (%)": round(negative_pct, 2),
                "Corr to target": round(float(correlation), 3)
                if correlation is not None and not pd.isna(correlation)
                else None,
                "Risk tag": classify_input_risk(std_value, zero_pct, negative_pct),
            }
        )
    return pd.DataFrame(rows)


def build_overview_correlation_pairs(
    df: pd.DataFrame,
    columns: list[str],
) -> pd.DataFrame:
    if len(columns) < 2:
        return pd.DataFrame(
            columns=["Left variable", "Right variable", "Correlation", "Abs correlation", "Risk tag"]
        )
    corr_matrix = df[columns].corr()
    rows: list[dict[str, Any]] = []
    for idx, left in enumerate(columns):
        for right in columns[idx + 1 :]:
            value = corr_matrix.loc[left, right]
            if pd.isna(value):
                continue
            abs_value = abs(float(value))
            rows.append(
                {
                    "Left variable": left,
                    "Right variable": right,
                    "Correlation": round(float(value), 3),
                    "Abs correlation": round(abs_value, 3),
                    "Risk tag": classify_correlation_risk(abs_value),
                }
            )
    if not rows:
        return pd.DataFrame(
            columns=["Left variable", "Right variable", "Correlation", "Abs correlation", "Risk tag"]
        )
    return pd.DataFrame(rows).sort_values(
        "Abs correlation",
        ascending=False,
    ).reset_index(drop=True)


def build_overview_vif_df(
    df: pd.DataFrame,
    columns: list[str],
) -> pd.DataFrame:
    if len(columns) < 2:
        return pd.DataFrame(columns=["Variable", "VIF", "Risk tag"])

    matrix = df[columns].astype(float).to_numpy()
    valid_rows = np.isfinite(matrix).all(axis=1)
    matrix = matrix[valid_rows]
    if matrix.shape[0] <= len(columns):
        return pd.DataFrame(columns=["Variable", "VIF", "Risk tag"])

    design_matrix = np.column_stack([np.ones(matrix.shape[0], dtype=np.float64), matrix])

    rows: list[dict[str, Any]] = []
    for idx, variable in enumerate(columns, start=1):
        try:
            vif_value = float(variance_inflation_factor(design_matrix, idx))
        except Exception:
            vif_value = float("inf")
        rows.append(
            {
                "Variable": variable,
                "VIF": round(vif_value, 3) if np.isfinite(vif_value) else None,
                "Risk tag": classify_vif_risk(vif_value),
            }
        )
    return pd.DataFrame(rows).sort_values(
        "VIF",
        ascending=False,
        na_position="last",
    ).reset_index(drop=True)


def build_overview_target_timeseries(
    *,
    df: pd.DataFrame,
    date_col: str,
    target_col: str,
    granularity: str,
) -> pd.DataFrame:
    return aggregate_time_series_df(
        df[[date_col, target_col]].copy(),
        date_col=date_col,
        value_columns=[target_col],
        granularity=granularity,
    ).set_index(date_col)


def compute_max_abs_correlation(
    df: pd.DataFrame,
    input_cols: list[str],
) -> float:
    max_abs_corr = 0.0
    if len(input_cols) >= 2:
        corr_matrix = df[input_cols].corr().abs()
        if not corr_matrix.empty:
            upper_triangle = corr_matrix.where(np.triu(np.ones(corr_matrix.shape), k=1).astype(bool))
            max_abs_corr = float(upper_triangle.max().max()) if not upper_triangle.isna().all().all() else 0.0
    return max_abs_corr


def classify_input_coverage_risk(
    df: pd.DataFrame,
    input_cols: list[str],
) -> str:
    if not input_cols:
        return "N/A"
    min_non_zero_pct = min(float((df[column].astype(float) > 0).mean() * 100) for column in input_cols)
    if min_non_zero_pct < 20.0:
        return "HIGH"
    if min_non_zero_pct < 50.0:
        return "MEDIUM"
    return "LOW"


def classify_dataset_health(rows_per_parameter: float, zero_target_pct: float) -> str:
    if rows_per_parameter < 5 or zero_target_pct > 50:
        return "HIGH RISK"
    if rows_per_parameter < 10 or zero_target_pct > 25:
        return "CAUTION"
    return "GOOD"


def classify_target_volatility(target_values: pd.Series) -> str:
    mean_value = float(target_values.mean()) if len(target_values) > 0 else 0.0
    std_value = float(target_values.std(ddof=0)) if len(target_values) > 0 else 0.0
    cv_value = (std_value / abs(mean_value)) if not math.isclose(mean_value, 0.0) else 0.0
    if cv_value >= 1.0:
        return "VERY HIGH"
    if cv_value >= 0.5:
        return "ELEVATED"
    return "NORMAL"


def classify_correlation_risk(abs_corr: float) -> str:
    if abs_corr >= 0.9:
        return "VERY HIGH"
    if abs_corr >= 0.8:
        return "HIGH"
    if abs_corr >= 0.6:
        return "MEDIUM"
    return "LOW"


def classify_vif_risk(vif_value: float) -> str:
    if not np.isfinite(vif_value):
        return "VERY HIGH"
    if vif_value >= 10.0:
        return "VERY HIGH"
    if vif_value >= 5.0:
        return "HIGH"
    if vif_value >= 3.0:
        return "MEDIUM"
    return "LOW"


def classify_input_risk(std_value: float, zero_pct: float, negative_pct: float) -> str:
    if negative_pct > 0:
        return "CHECK"
    if math.isclose(std_value, 0.0) or zero_pct >= 90.0:
        return "HIGH RISK"
    if zero_pct >= 60.0:
        return "CAUTION"
    return "NORMAL"


def classify_coverage_tag(non_zero_pct: float) -> str:
    if non_zero_pct < 20.0:
        return "SPARSE"
    if non_zero_pct < 50.0:
        return "PATCHY"
    return "HEALTHY"
