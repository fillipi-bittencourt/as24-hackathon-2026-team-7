from __future__ import annotations

import json
import math
from datetime import datetime
from pathlib import Path
from typing import Any

import altair as alt
import numpy as np
import pandas as pd
import streamlit as st

from src.ai.client import (
    build_payload,
    get_setup_recommendations,
    get_summary,
    validate_analysis_text,
)
from src.app_state import (
    clear_setup_guidance,
    clear_model_outputs,
    clear_transformed_inputs,
    compute_signature,
    compute_transform_fingerprint,
    init_state,
    remove_model_outputs,
    replace_state,
)
from src.data_overview import render_data_overview_tab
from src.export_helpers import (
    build_column_selection_rows,
    build_complete_overview_export_df,
    build_complete_overview_pdf_bytes,
    build_results_pdf_bytes,
    build_text_pdf_bytes,
    df_to_csv_bytes,
)
from src.models.elasticnet import ElasticNetModel
from src.models.lasso import LassoModel
from src.models.ols import OLSModel
from src.models.pymc_model import PyMCModel
from src.models.ridge import RidgeModel
from src.results_helpers import (
    aggregate_time_series_df,
    build_actual_vs_predicted_chart,
    build_labeled_bar_chart,
    build_period_mask,
    build_signed_bar_chart,
    build_spend_vs_contribution_chart,
    build_stacked_time_decomposition_chart,
    compute_display_attribution,
    compute_display_attribution_vectors,
    compute_mape_non_zero,
    compute_view_channel_metrics,
    format_cpl,
    get_default_time_granularity,
    get_time_granularity_options,
    format_number,
    format_signed_number,
    infer_grain,
    infer_granularity_scale_factor,
    is_rankable_cpl,
    pick_best_channel,
    pick_worst_channel,
)
from src.session_persistence import (
    has_persistable_state,
    list_saved_sessions,
    load_session_state,
    save_session_state,
)
from src.setup_assistant import (
    apply_ai_column_recommendations,
    apply_ai_prior_recommendations,
    apply_ai_transform_recommendations,
    build_setup_assistant_payload,
    resolve_ai_credentials,
)
from src.transforms import geometric_adstock, hill_saturation, log_saturation, transform_media
from src.ui_content import (
    build_table_column_config,
    render_definitions_expander,
    render_info_tab,
    render_reference_values_expander,
)
from src.utils import (
    compute_dataframe_signature,
    convert_mmm_data,
    normalize_column_names,
    validate_mmm_data,
)


MODEL_BUILDERS = {
    "OLS": OLSModel,
    "Ridge": RidgeModel,
    "Lasso": LassoModel,
    "ElasticNet": ElasticNetModel,
    "PyMC": PyMCModel,
}

STEP_DESCRIPTIONS = {
    "Data": "Load the dataset, confirm the columns, and validate the input before any modeling.",
    "Overview": "Inspect validated dataset quality, target behavior, and multicollinearity before configuring the model.",
    "Config": "Choose media transforms and regularization settings for the modeling step.",
    "Priors": "Review or edit Bayesian prior assumptions before using PyMC.",
    "Info": "Learn what each MMM model and transform does, when to use it, and how to read the outputs.",
    "Fit": "Run one or more models on the transformed dataset.",
    "Results": "Interpret model fit, attribution, efficiency, and exports.",
    "AI": "Generate written analysis and export the complete project overview.",
}

HOLDOUT_FRACTION = 0.2
CURRENT_DATA_LABEL = "Current loaded data"


def is_pymc_available() -> bool:
    try:
        import pymc  # noqa: F401
    except Exception:
        return False
    return True


def is_anthropic_available() -> bool:
    try:
        import anthropic  # noqa: F401
    except Exception:
        return False
    return True


def render_ai_applied_setup_summary(
    setup_recommendations: dict[str, Any],
) -> None:
    selection = setup_recommendations.get("selection_recommendations", {})
    column_reasoning = setup_recommendations.get("column_selection_reasoning", {})
    applied_selection_summary = setup_recommendations.get("applied_selection_summary", {})
    transform_recommendations = setup_recommendations.get("transform_recommendations", {})
    prior_recommendations = setup_recommendations.get("prior_recommendations", {})

    st.subheader("AI applied this setup because")
    st.caption(
        "This summary explains how the AI evaluation of the ingested dataset changed the working MMM configuration."
    )
    summary_text = str(setup_recommendations.get("executive_summary", "")).strip()
    if summary_text:
        st.markdown(summary_text)

    col1, col2 = st.columns(2)
    col1.markdown("**Column selection applied**")
    col1.write(f"- Date column: `{st.session_state.get('date_col')}`")
    col1.write(f"- Target column: `{st.session_state.get('target_col')}`")
    col1.write(
        "- Channels: "
        + (", ".join(f"`{channel}`" for channel in st.session_state.get("channel_cols", [])) or "None")
    )
    col1.write(
        "- Controls: "
        + (", ".join(f"`{control}`" for control in st.session_state.get("control_cols", [])) or "None")
    )
    if selection.get("reasoning_summary"):
        col1.caption(str(selection["reasoning_summary"]))

    col2.markdown("**Transform and prior setup applied**")
    col2.write(
        "- Default channel prior family: "
        + f"`{st.session_state['pymc_prior_config'].get('channel_prior_family', 'HalfNormal')}`"
    )
    col2.write(
        "- Regularization alpha: "
        + f"`{st.session_state.get('reg_alpha', 1.0):.2f}`"
    )
    col2.write(
        "- ElasticNet l1 ratio: "
        + f"`{st.session_state.get('l1_ratio', 0.5):.2f}`"
    )
    if prior_recommendations.get("reasoning_summary"):
        col2.caption(str(prior_recommendations["reasoning_summary"]))

    selection_rule_rows = []
    for column in applied_selection_summary.get("ai_ranked_channels", []):
        selection_rule_rows.append(
            {
                "Column": column,
                "Type": "Channel",
                "Applied because": "AI ranked",
                "Coverage tag": applied_selection_summary.get("coverage_tags", {}).get(column, "unknown"),
            }
        )
    for column in applied_selection_summary.get("force_kept_channels", []):
        selection_rule_rows.append(
            {
                "Column": column,
                "Type": "Channel",
                "Applied because": "Coverage rule kept it",
                "Coverage tag": applied_selection_summary.get("coverage_tags", {}).get(column, "unknown"),
            }
        )
    for column in applied_selection_summary.get("ai_ranked_controls", []):
        selection_rule_rows.append(
            {
                "Column": column,
                "Type": "Control",
                "Applied because": "AI ranked",
                "Coverage tag": applied_selection_summary.get("coverage_tags", {}).get(column, "unknown"),
            }
        )
    for column in applied_selection_summary.get("force_kept_controls", []):
        selection_rule_rows.append(
            {
                "Column": column,
                "Type": "Control",
                "Applied because": "Coverage rule kept it",
                "Coverage tag": applied_selection_summary.get("coverage_tags", {}).get(column, "unknown"),
            }
        )
    if selection_rule_rows:
        st.markdown("**Applied selection breakdown**")
        st.caption(
            "Columns with `patchy` or `healthy` coverage are kept automatically. Columns tagged `sparse` are excluded from the applied selection."
        )
        st.dataframe(pd.DataFrame(selection_rule_rows), width="stretch")

    excluded_rows = []
    for column in applied_selection_summary.get("sparse_excluded_channels", []):
        excluded_rows.append(
            {
                "Column": column,
                "Type": "Channel",
                "Excluded because": "Sparse coverage",
                "Coverage tag": applied_selection_summary.get("coverage_tags", {}).get(column, "unknown"),
            }
        )
    for column in applied_selection_summary.get("sparse_excluded_controls", []):
        excluded_rows.append(
            {
                "Column": column,
                "Type": "Control",
                "Excluded because": "Sparse coverage",
                "Coverage tag": applied_selection_summary.get("coverage_tags", {}).get(column, "unknown"),
            }
        )
    if excluded_rows:
        st.markdown("**Excluded by coverage rule**")
        st.dataframe(pd.DataFrame(excluded_rows), width="stretch")

    reasoning_rows = []
    for channel in st.session_state.get("channel_cols", []):
        transform_choice = transform_recommendations.get(channel, {})
        column_note = column_reasoning.get("channels", {}).get(channel, "")
        prior_note = st.session_state.get("pymc_prior_reasoning", {}).get(channel, "")
        reasoning_rows.append(
            {
                "Channel": channel,
                "Applied adstock": st.session_state["adstock_type"].get(channel, "geometric"),
                "Applied theta": round(float(st.session_state["adstock_params"].get(channel, 0.0)), 3),
                "Applied saturation": st.session_state["saturation_type"].get(channel, "log"),
                "Applied alpha": round(
                    float(st.session_state["saturation_params"].get(channel, {}).get("alpha", 1.0)),
                    3,
                ),
                "Applied k": round(
                    float(st.session_state["saturation_params"].get(channel, {}).get("k", 0.0)),
                    3,
                ),
                "Why this channel was included": column_note or "Selected as a media driver by the AI setup review.",
                "Why this transform was chosen": str(transform_choice.get("reasoning", "")) or "No transform reasoning returned.",
                "Why this prior was chosen": prior_note or "No channel-specific prior reasoning returned.",
            }
        )
    if reasoning_rows:
        reasoning_df = pd.DataFrame(reasoning_rows)
        st.dataframe(
            reasoning_df,
            column_config=build_table_column_config(reasoning_df.columns),
            width="stretch",
        )

    quality_findings = setup_recommendations.get("data_quality_findings", [])
    completion_actions = setup_recommendations.get("completion_actions", [])
    if quality_findings or completion_actions:
        quality_col1, quality_col2 = st.columns(2)
        if quality_findings:
            quality_col1.markdown("**Data quality findings used by the AI**")
            for item in quality_findings:
                quality_col1.write(f"- {item}")
        if completion_actions:
            quality_col2.markdown("**Data completion actions suggested by the AI**")
            for item in completion_actions:
                quality_col2.write(f"- {item}")


def compute_holdout_diagnostics(
    *,
    builder: type,
    X: np.ndarray,
    y: np.ndarray,
    raw_spend: dict[str, np.ndarray],
    model_kwargs: dict[str, Any],
    date_values: pd.Series,
) -> dict[str, Any] | None:
    n_rows = len(y)
    split_idx = int(round(n_rows * (1.0 - HOLDOUT_FRACTION)))
    min_train_rows = max(20, X.shape[1] + 5)
    min_holdout_rows = 10

    if split_idx < min_train_rows or (n_rows - split_idx) < min_holdout_rows:
        return None

    train_X = np.asarray(X[:split_idx], dtype=np.float64)
    holdout_X = np.asarray(X[split_idx:], dtype=np.float64)
    train_y = np.asarray(y[:split_idx], dtype=np.float64)
    holdout_y = np.asarray(y[split_idx:], dtype=np.float64)
    train_raw_spend = {
        channel: np.asarray(values[:split_idx], dtype=np.float64)
        for channel, values in raw_spend.items()
    }

    validation_model = builder()
    validation_model.fit(train_X, train_y, raw_spend=train_raw_spend, **model_kwargs)
    holdout_pred = np.asarray(validation_model.predict(holdout_X), dtype=np.float64)
    holdout_mae = float(np.mean(np.abs(holdout_y - holdout_pred)))
    holdout_rmse = float(np.sqrt(np.mean((holdout_y - holdout_pred) ** 2)))
    holdout_mape, holdout_coverage = compute_mape_non_zero(holdout_y, holdout_pred)
    ss_res = float(np.sum((holdout_y - holdout_pred) ** 2))
    ss_tot = float(np.sum((holdout_y - np.mean(holdout_y)) ** 2)) or 1.0
    holdout_r_squared = 1.0 - (ss_res / ss_tot)

    holdout_dates = pd.to_datetime(date_values.iloc[split_idx:]).reset_index(drop=True)
    holdout_df = pd.DataFrame(
        {
            "date": holdout_dates,
            "actual": holdout_y,
            "predicted": holdout_pred,
        }
    )

    return {
        "train_rows": int(split_idx),
        "holdout_rows": int(n_rows - split_idx),
        "holdout_r_squared": float(holdout_r_squared),
        "holdout_rmse": holdout_rmse,
        "holdout_mae": holdout_mae,
        "holdout_mape": holdout_mape,
        "holdout_coverage": holdout_coverage,
        "holdout_df": holdout_df,
    }


def apply_transform_configuration(
    *,
    df: pd.DataFrame,
    channel_cols: list[str],
    control_cols: list[str],
    adstock_type: dict[str, str],
    saturation_type: dict[str, str],
    adstock_params: dict[str, float],
    saturation_params: dict[str, dict[str, float]],
    reg_alpha: float,
    l1_ratio: float,
) -> tuple[bool, bool]:
    previous_fingerprint = st.session_state.get("transform_fingerprint")
    previous_reg = st.session_state.get("regularization_signature")
    current_reg = json.dumps(
        {
            "reg_alpha": reg_alpha,
            "l1_ratio": l1_ratio,
        },
        sort_keys=True,
    )

    fingerprint = compute_transform_fingerprint(
        channel_cols,
        control_cols,
        adstock_type,
        saturation_type,
        adstock_params,
        saturation_params,
    )

    X_transformed = transform_media(
        df,
        channel_cols,
        adstock_params,
        saturation_params,
        adstock_type=adstock_type,
        saturation_type=saturation_type,
        control_cols=control_cols,
    )

    st.session_state["X_transformed"] = X_transformed
    st.session_state["y"] = df[st.session_state["target_col"]].to_numpy(dtype=np.float64)
    st.session_state["adstock_params"] = adstock_params
    st.session_state["saturation_params"] = saturation_params
    st.session_state["adstock_type"] = adstock_type
    st.session_state["saturation_type"] = saturation_type
    st.session_state["reg_alpha"] = reg_alpha
    st.session_state["l1_ratio"] = l1_ratio
    st.session_state["transforms_applied"] = True
    st.session_state["transform_fingerprint"] = fingerprint
    st.session_state["regularization_signature"] = current_reg

    fits_cleared = False
    refit_needed = False
    if st.session_state["model_results"]:
        if previous_fingerprint and previous_fingerprint != fingerprint:
            clear_model_outputs()
            fits_cleared = True
        elif previous_fingerprint == fingerprint and previous_reg != current_reg:
            affected_models = ["Ridge", "Lasso", "ElasticNet"]
            removed_any = remove_model_outputs(affected_models)
            if removed_any:
                fits_cleared = True
            else:
                refit_needed = True

    return fits_cleared, refit_needed


def compute_saturation_status(
    saturation_kind: str,
    avg_spend: float,
    saturation_params: dict[str, float],
    *,
    spend_scale_factor: float = 1.0,
) -> tuple[str, str]:
    if saturation_kind == "hill":
        k_value = max(float(saturation_params.get("k", 0.0)) * spend_scale_factor, 0.0)
        if math.isclose(k_value, 0.0):
            return "hill no k", "Hill saturation is selected but k is near zero, so the status is not informative."
        spend_ratio = avg_spend / k_value
        if spend_ratio < 0.7:
            return "under-saturated", "Average spend is well below the half-saturation point, so there may still be headroom."
        if spend_ratio <= 1.3:
            return "near saturation", "Average spend is around the half-saturation point, so gains may start slowing down."
        return "over-saturated", "Average spend is above the half-saturation point, so incremental response is likely flattening."
    if saturation_kind == "log":
        return "log saturation", "Log saturation is a simple diminishing-returns shape without a single half-saturation threshold."
    return "no saturation", "No saturation curve is applied to this channel."


def build_saturation_curve_chart(
    df: pd.DataFrame,
    date_col: str,
    channel_names: list[str],
    adstock_type: dict[str, str],
    adstock_params: dict[str, float],
    saturation_type: dict[str, str],
    saturation_params: dict[str, dict[str, float]],
    granularity: str,
) -> alt.Chart | None:
    curve_rows: list[dict[str, Any]] = []
    scale_factor = infer_granularity_scale_factor(df[date_col], granularity)
    for channel in channel_names:
        aggregated_spend_df = aggregate_time_series_df(
            df[[date_col, channel]].copy(),
            date_col=date_col,
            value_columns=[channel],
            granularity=granularity,
        )
        max_spend = float(aggregated_spend_df[channel].max()) if not aggregated_spend_df.empty else 0.0
        curve_max = max(max_spend * 2.0, 1.0)
        spend_grid = np.linspace(0.0, curve_max, 60, dtype=np.float64)
        sat_kind = saturation_type.get(channel, "log")
        if sat_kind == "hill":
            params = saturation_params.get(channel, {"alpha": 1.0, "k": 1.0})
            response = hill_saturation(
                spend_grid,
                float(params.get("alpha", 1.0)),
                max(float(params.get("k", 1.0)) * scale_factor, 0.1),
            )
        elif sat_kind == "log":
            response = log_saturation(spend_grid)
        else:
            continue

        for spend_value, response_value in zip(spend_grid, response):
            curve_rows.append(
                {
                    "channel": channel,
                    "spend": float(spend_value),
                    "response": float(response_value),
                    "saturation": sat_kind,
                    "granularity": granularity,
                }
            )

    if not curve_rows:
        return None

    curve_df = pd.DataFrame(curve_rows)
    return (
        alt.Chart(curve_df)
        .mark_line()
        .encode(
            x=alt.X("spend:Q", title="Spend"),
            y=alt.Y("response:Q", title="Transformed response"),
            color=alt.Color("channel:N", title="Channel"),
            strokeDash=alt.StrokeDash("saturation:N", title="Curve type"),
            tooltip=[
                alt.Tooltip("channel:N", title="Channel"),
                alt.Tooltip("saturation:N", title="Curve type"),
                alt.Tooltip("granularity:N", title="Granularity"),
                alt.Tooltip("spend:Q", title="Spend", format=",.2f"),
                alt.Tooltip("response:Q", title="Response", format=",.4f"),
            ],
        )
        .properties(title=f"Saturation curves ({granularity})", height=320, width="container")
    )


def get_step_status(step_name: str) -> str:
    if step_name in {"Data", "Info"}:
        return "ready"
    if step_name == "Overview":
        return "ready" if st.session_state.get("valid") else "needs data"
    if step_name in {"Config", "Priors"}:
        return "ready" if st.session_state.get("valid") else "needs data"
    if step_name == "Fit":
        return "ready" if st.session_state.get("transforms_applied") else "needs transforms"
    if step_name in {"Results", "AI"}:
        return "ready" if st.session_state.get("model_results") else "needs fitted model"
    return "ready"


def build_step_label(step_number: int, step_name: str) -> str:
    status = get_step_status(step_name)
    if status == "ready":
        return f"{step_number}. {step_name}"
    return f"{step_number}. {step_name} ({status})"


def render_sidebar_step_menu() -> str:
    ordered_steps = ["Data", "Overview", "Config", "Priors", "Fit", "Results", "AI"]
    current_step = st.session_state.get("current_step", "Data")
    st.sidebar.subheader("Browse")
    st.sidebar.caption(
        "Click a step to open it. Steps with missing prerequisites still open and explain what is needed next."
    )

    for idx, step_name in enumerate(ordered_steps):
        label = build_step_label(idx + 1, step_name)
        if st.sidebar.button(
            label,
            key=f"nav_step_{step_name}",
            use_container_width=True,
            type="primary" if step_name == current_step else "secondary",
        ):
            current_step = step_name
            st.session_state["current_step"] = step_name

    selected_step = st.session_state.get("current_step", current_step)
    if selected_step in ordered_steps:
        st.sidebar.caption(STEP_DESCRIPTIONS[selected_step])
    else:
        st.sidebar.caption("Choose a workflow step to continue the guided modeling flow.")
    return selected_step


def format_saved_session_label(
    session_info: dict[str, str],
    duplicate_labels: dict[str, int] | None = None,
) -> str:
    source = session_info.get("source") or "no source"
    saved_at = session_info.get("saved_at") or "unknown time"
    models = session_info.get("models") or "no fitted models"
    label = f"{session_info['display_name']} | {saved_at} | {source} | {models}"
    if duplicate_labels and duplicate_labels.get(label, 0) > 1:
        return f"{label} | id {session_info.get('slug', '')}"
    return label


def format_saved_session_option(
    slug: str,
    session_by_slug: dict[str, dict[str, str]],
    duplicate_labels: dict[str, int] | None = None,
) -> str:
    session_info = session_by_slug.get(slug)
    if session_info is None:
        return str(slug)
    return format_saved_session_label(session_info, duplicate_labels)


def render_session_controls() -> None:
    st.sidebar.divider()
    st.sidebar.subheader("Session")
    st.sidebar.caption(
        "Save the current MMM state locally, reload a previous run, or clear the current working state."
    )

    has_state = has_persistable_state(st.session_state)
    save_name = st.sidebar.text_input(
        "Save name",
        key="session_save_name",
        help="Optional local name for this saved MMM state.",
    )
    if st.sidebar.button(
        "Save current state",
        use_container_width=True,
        disabled=not has_state,
        help="Save the loaded data, transforms, fitted model outputs, and AI outputs to a local session file.",
    ):
        try:
            saved_name = save_session_state(st.session_state, save_name)
            st.session_state["session_notice"] = {
                "level": "success",
                "text": f"Saved session `{saved_name}`.",
            }
            st.rerun()
        except Exception as exc:
            st.sidebar.error(f"Could not save the current state: {exc}")

    saved_sessions = list_saved_sessions()
    session_by_slug = {
        session_info["slug"]: session_info for session_info in saved_sessions
    }
    duplicate_labels: dict[str, int] = {}
    for session_info in saved_sessions:
        base_label = format_saved_session_label(session_info)
        duplicate_labels[base_label] = duplicate_labels.get(base_label, 0) + 1
    selected_slug = None
    if saved_sessions:
        selected_slug = st.sidebar.selectbox(
            "Saved sessions",
            options=list(session_by_slug.keys()),
            format_func=lambda slug: format_saved_session_option(slug, session_by_slug, duplicate_labels),
            key="selected_saved_session",
            help="Choose a previously saved MMM state to restore.",
        )
    else:
        st.sidebar.caption("No saved sessions yet.")

    load_col, clear_col = st.sidebar.columns(2)
    if load_col.button(
        "Load saved",
        use_container_width=True,
        disabled=selected_slug is None,
        help="Replace the current working state with the selected saved state.",
    ):
        try:
            restored_state = load_session_state(str(selected_slug))
            loaded_label = session_by_slug[str(selected_slug)]["display_name"]
            replace_state(restored_state, preserve_keys={"manual_ai_api_key"})
            st.session_state["data_source_selection"] = CURRENT_DATA_LABEL
            st.session_state["session_notice"] = {
                "level": "success",
                "text": f"Loaded session `{loaded_label}`.",
            }
            st.rerun()
        except Exception as exc:
            st.sidebar.error(f"Could not load the saved state: {exc}")

    if clear_col.button(
        "Clear state",
        use_container_width=True,
        disabled=not has_state,
        help="Reset the MMM workflow state and keep only the manual API key override.",
    ):
        replace_state(preserve_keys={"manual_ai_api_key"})
        st.session_state["session_notice"] = {
            "level": "info",
            "text": "Cleared the current MMM state.",
        }
        st.rerun()


def render_info_sidebar_section() -> None:
    st.sidebar.divider()
    st.sidebar.subheader("Guide")
    st.sidebar.caption(
        "Open the MMM guide for model selection, transform choices, and result interpretation."
    )
    if st.sidebar.button(
        "Open guide",
        key="nav_info_page",
        use_container_width=True,
        type="primary" if st.session_state.get("current_step") == "Info" else "secondary",
    ):
        st.session_state["current_step"] = "Info"


def load_candidate_dataframe() -> pd.DataFrame | None:
    uploaded_file = st.file_uploader(
        "Upload CSV",
        type=["csv"],
        help="Upload the marketing dataset you want to model. CSV only.",
    )

    local_files = sorted(Path("data").glob("*.csv"))
    selected_name = None
    local_names = [path.name for path in local_files]
    uploaded_name = uploaded_file.name if uploaded_file is not None else None
    if local_files:
        select_options: list[str] = []
        if st.session_state.get("loaded_df") is not None:
            select_options.append(CURRENT_DATA_LABEL)
        if uploaded_name and uploaded_name not in select_options:
            select_options.append(uploaded_name)
        for local_name in local_names:
            if local_name not in select_options:
                select_options.append(local_name)

        if uploaded_name:
            default_option = uploaded_name
        elif st.session_state.get("loaded_df") is not None:
            default_option = CURRENT_DATA_LABEL
        else:
            default_option = local_names[0]

        selector_key = "data_source_selection"
        if (
            selector_key not in st.session_state
            or st.session_state[selector_key] not in select_options
        ):
            st.session_state[selector_key] = default_option

        selected_name = st.selectbox(
            "Or pick a file from data/",
            options=select_options,
            key=selector_key,
            help="Choose a CSV that already exists in the app data folder.",
        )
    else:
        st.info("No files in data/ yet — use the uploader above.")

    candidate_df = None
    candidate_signature = None
    source_name = None
    use_uploaded = uploaded_file is not None and (
        selected_name is None or selected_name == uploaded_name
    )
    if use_uploaded:
        try:
            uploaded_file.seek(0)
            candidate_df = pd.read_csv(uploaded_file)
            candidate_df, rename_map = normalize_column_names(candidate_df)
            candidate_signature = compute_dataframe_signature(candidate_df)
            source_name = uploaded_file.name
            st.session_state["column_rename_map"] = rename_map
        except Exception as exc:
            st.error(f"Could not read uploaded CSV: {exc}")
            return st.session_state.get("loaded_df")
    elif selected_name and selected_name != CURRENT_DATA_LABEL:
        selected_path = next((path for path in local_files if path.name == selected_name), None)
        if selected_path is None:
            return st.session_state.get("loaded_df")
        try:
            candidate_df = pd.read_csv(selected_path)
            candidate_df, rename_map = normalize_column_names(candidate_df)
            candidate_signature = compute_dataframe_signature(candidate_df)
            source_name = selected_path.name
            st.session_state["column_rename_map"] = rename_map
        except Exception as exc:
            st.error(f"Could not read selected CSV: {exc}")
            return st.session_state.get("loaded_df")

    if candidate_df is not None:
        source_changed = source_name != st.session_state.get("loaded_source")
        signature_changed = candidate_signature != st.session_state.get("loaded_df_signature")
        st.session_state["loaded_df"] = candidate_df
        st.session_state["loaded_df_signature"] = candidate_signature
        st.session_state["loaded_source"] = source_name
        if source_changed or signature_changed:
            clear_setup_guidance()
            if st.session_state.get("valid"):
                st.session_state["valid"] = False
                st.session_state["df"] = None
                clear_transformed_inputs()
                st.session_state["last_data_message"] = {
                    "level": "info",
                    "text": "The loaded dataset changed. Validate the dataset before continuing.",
                }

    return st.session_state.get("loaded_df")


def default_channel_selection(columns: list[str], date_col: str | None, target_col: str | None) -> list[str]:
    blocked = {date_col, target_col}
    return [
        col
        for col in columns
        if col not in blocked
        and (
            col.endswith("_spend")
            or col.endswith("_cost")
        )
    ]


def render_data_tab() -> None:
    st.caption("Start here. Load a CSV, confirm the date, target, and spend columns, then validate the dataset before moving on.")
    last_data_message = st.session_state.get("last_data_message")
    if isinstance(last_data_message, dict):
        message_level = last_data_message.get("level", "info")
        message_text = str(last_data_message.get("text", ""))
        if message_text:
            getattr(st, message_level, st.info)(message_text)
        st.session_state["last_data_message"] = None
    render_definitions_expander(
        "Definitions for this tab",
        [
            ("Date column", "The time column used to order the data for transforms and modeling."),
            ("Target column", "The business outcome the model should explain, usually leads or conversions."),
            ("Channels to include", "Paid media variables that the model can attribute results to."),
            ("Control columns", "Non-media variables that help explain baseline movement."),
            ("Load and validate", "Runs type conversion and data checks before any modeling starts."),
        ],
    )
    raw_df = load_candidate_dataframe()
    if raw_df is None:
        return

    rename_map = st.session_state.get("column_rename_map", {})
    if rename_map:
        renamed_pairs = ", ".join(
            f"{original} -> {renamed}" for original, renamed in list(rename_map.items())[:8]
        )
        extra_count = max(len(rename_map) - 8, 0)
        extra_text = f" and {extra_count} more" if extra_count else ""
        st.info(f"Column names were normalized to snake_case: {renamed_pairs}{extra_text}.")

    columns = list(raw_df.columns)
    current_date = st.session_state.get("date_col")
    current_target = st.session_state.get("target_col")
    current_channels = [
        col for col in st.session_state.get("channel_cols", []) if col in columns
    ]
    current_controls = [
        col for col in st.session_state.get("control_cols", []) if col in columns
    ]

    date_default = columns.index(current_date) if current_date in columns else (
        columns.index("date") if "date" in columns else 0
    )
    target_default = columns.index(current_target) if current_target in columns else (
        columns.index("target") if "target" in columns else min(1, len(columns) - 1)
    )

    date_col = st.selectbox(
        "Date column",
        options=columns,
        index=date_default,
        help="Select the column that represents the time period for each row.",
    )
    target_col = st.selectbox(
        "Target column",
        options=columns,
        index=target_default,
        help="Select the outcome you want the model to explain.",
    )

    channel_candidates = [col for col in columns if col not in {date_col, target_col}]
    default_channels = current_channels or default_channel_selection(
        channel_candidates, date_col, target_col
    )
    channel_cols = st.multiselect(
        "Channels to include",
        options=channel_candidates,
        default=[col for col in default_channels if col in channel_candidates],
        help="Choose the paid media columns that should receive attribution in the model.",
    )

    control_candidates = [col for col in channel_candidates if col not in channel_cols]
    control_cols = st.multiselect(
        "Control columns",
        options=control_candidates,
        default=[col for col in current_controls if col in control_candidates],
        help="Choose non-media columns that explain baseline variation but are not treated as media channels.",
    )

    button_label = "Update selection" if st.session_state.get("valid") else "Load and validate"
    if st.button(
        button_label,
        type="primary",
        help="Validate the selected columns and prepare the dataset for transforms and modeling.",
    ):
        previous_signature = (
            st.session_state.get("loaded_source"),
            st.session_state.get("date_col"),
            st.session_state.get("target_col"),
            tuple(st.session_state.get("channel_cols", [])),
            tuple(st.session_state.get("control_cols", [])),
        )

        converted, aggregated_duplicate_rows = convert_mmm_data(
            raw_df,
            date_col,
            target_col,
            channel_cols,
            control_cols,
        )
        ok, errors, warnings = validate_mmm_data(
            converted,
            date_col,
            target_col,
            channel_cols,
            control_cols,
        )

        if ok:
            prepared = converted.sort_values(date_col).reset_index(drop=True)
            new_signature = (
                st.session_state.get("loaded_source"),
                date_col,
                target_col,
                tuple(channel_cols),
                tuple(control_cols),
            )

            st.session_state["df"] = prepared
            st.session_state["date_col"] = date_col
            st.session_state["target_col"] = target_col
            st.session_state["channel_cols"] = channel_cols
            st.session_state["control_cols"] = control_cols
            st.session_state["valid"] = True

            if previous_signature != new_signature:
                clear_transformed_inputs()
                clear_setup_guidance()
                if previous_signature[1] is not None:
                    st.info("Channel selection updated — re-apply transforms in Config and re-fit models.")

            st.success(
                f"Loaded {len(prepared)} rows with columns {', '.join([date_col, target_col, *channel_cols])}"
            )
            if aggregated_duplicate_rows > 0:
                st.warning(
                    f"Duplicate dates were aggregated by sum before validation. Consolidated {aggregated_duplicate_rows} extra row(s)."
                )
            if warnings:
                st.warning(" ".join(warnings))
        else:
            st.session_state["valid"] = False
            st.session_state["df"] = None
            clear_transformed_inputs()
            clear_setup_guidance()
            for error in errors:
                st.error(error)

    if st.session_state.get("valid") and st.session_state.get("df") is not None:
        df = st.session_state["df"]
        grain = infer_grain(df[st.session_state["date_col"]])
        st.caption(
            f"Date range: {df[st.session_state['date_col']].min().date()} to {df[st.session_state['date_col']].max().date()} — {len(df)} rows"
        )
        if grain:
            st.caption(f"Grain: {grain}")
        preview_cols = [
            st.session_state["date_col"],
            st.session_state["target_col"],
            *st.session_state["channel_cols"],
        ]
        st.dataframe(df[preview_cols].head(10), width="stretch")

        with st.expander("AI setup assistant", expanded=False):
            st.caption(
                "Ask AI to review the ingested data and suggest transform settings, data consistency checks, data completion actions, and PyMC priors. Suggested priors and transform settings are applied automatically."
            )
            provider, api_key, model, ai_error = resolve_ai_credentials()
            if ai_error:
                st.warning(ai_error)
            else:
                st.success(f"AI ready with {provider}")

            if st.button(
                "Analyze data and suggest setup",
                type="primary",
                help="Ask AI to review the dataset and suggest data checks, transforms, and priors.",
            ):
                if not api_key or not model or not provider:
                    st.error("Add a valid .env or credentials.json file, or set an API key in the sidebar to enable AI setup suggestions.")
                else:
                    setup_payload = build_setup_assistant_payload()
                    setup_recommendations = get_setup_recommendations(
                        setup_payload,
                        provider,
                        api_key,
                        model,
                    )
                    if "error" in setup_recommendations:
                        st.error(str(setup_recommendations["error"]))
                    else:
                        st.session_state["ai_setup_recommendations"] = setup_recommendations
                        selection_ok, selection_messages = apply_ai_column_recommendations(
                            setup_recommendations.get("selection_recommendations", {})
                        )
                        if not selection_ok:
                            st.error(
                                "AI setup suggestions were generated, but the suggested column selection could not be applied: "
                                + " ".join(selection_messages)
                            )
                            return
                        apply_ai_prior_recommendations(
                            setup_recommendations.get("prior_recommendations", {})
                        )
                        apply_ai_transform_recommendations()
                        fits_cleared, refit_needed = apply_transform_configuration(
                            df=st.session_state["df"],
                            channel_cols=st.session_state["channel_cols"],
                            control_cols=st.session_state["control_cols"],
                            adstock_type=st.session_state["adstock_type"],
                            saturation_type=st.session_state["saturation_type"],
                            adstock_params=st.session_state["adstock_params"],
                            saturation_params=st.session_state["saturation_params"],
                            reg_alpha=float(st.session_state["reg_alpha"]),
                            l1_ratio=float(st.session_state["l1_ratio"]),
                        )
                        if fits_cleared:
                            st.session_state["last_data_message"] = {
                                "level": "warning",
                                "text": "AI setup suggestions were applied. Column selection, priors, and transforms were updated automatically, and existing fitted models were cleared because the transformed input changed.",
                            }
                        elif refit_needed:
                            st.session_state["last_data_message"] = {
                                "level": "info",
                                "text": "AI setup suggestions were applied. Column selection, priors, and transforms were updated automatically. Re-fit the models in the Fit step to refresh the results with the new regularization values.",
                            }
                        else:
                            st.session_state["last_data_message"] = {
                                "level": "success",
                                "text": "AI setup suggestions were applied automatically. The selected columns, priors, and transforms now reflect the AI evaluation of the ingested dataset.",
                            }
                        st.rerun()

            setup_recommendations = st.session_state.get("ai_setup_recommendations")
            if setup_recommendations:
                render_ai_applied_setup_summary(setup_recommendations)

                column_reasoning_rows = []
                for row in build_column_selection_rows():
                    column_reasoning_rows.append(
                        {
                            "Selected item": row["item"],
                            "Value": row["value"],
                            "Reasoning": row["reasoning"],
                        }
                    )
                if column_reasoning_rows:
                    st.markdown("**Column selection reasoning**")
                    st.dataframe(pd.DataFrame(column_reasoning_rows), width="stretch")

                findings = setup_recommendations.get("data_quality_findings", [])
                if findings:
                    st.markdown("**Data quality findings**")
                    for item in findings:
                        st.write(f"- {item}")

                completion_actions = setup_recommendations.get("completion_actions", [])
                if completion_actions:
                    st.markdown("**Data completion actions**")
                    for item in completion_actions:
                        st.write(f"- {item}")

                transform_rows = []
                for channel, suggestion in setup_recommendations.get("transform_recommendations", {}).items():
                    transform_rows.append(
                        {
                            "Channel": channel,
                            "Adstock": suggestion.get("adstock_type", "geometric"),
                            "Theta": suggestion.get("theta"),
                            "Saturation": suggestion.get("saturation_type", "log"),
                            "Alpha": suggestion.get("alpha"),
                            "K": suggestion.get("k"),
                            "Reasoning": suggestion.get("reasoning", ""),
                        }
                    )
                if transform_rows:
                    st.markdown("**Suggested transforms**")
                    st.dataframe(pd.DataFrame(transform_rows), width="stretch")

                prior_rows = []
                channel_prior_recommendations = (
                    setup_recommendations.get("prior_recommendations", {}).get("channel_recommendations", {})
                )
                for channel in st.session_state["channel_cols"]:
                    suggestion = channel_prior_recommendations.get(channel, {})
                    prior_rows.append(
                        {
                            "Channel": channel,
                            "Family": suggestion.get("family"),
                            "Sigma scale": suggestion.get("sigma_scale"),
                            "Reasoning": suggestion.get("reasoning", ""),
                        }
                    )
                if prior_rows:
                    st.markdown("**Suggested priors**")
                    st.dataframe(pd.DataFrame(prior_rows), width="stretch")


def render_config_tab() -> None:
    if not st.session_state.get("valid"):
        st.warning("Load and validate data in the Data tab first.")
        return

    st.caption("Set the media transforms here. A safe starting point is Geometric adstock plus Log saturation for every channel.")
    render_definitions_expander(
        "Definitions for this tab",
        [
            ("Adstock", "Carryover effect from past spend. Higher values mean effects last longer."),
            ("Saturation", "How response changes as spend increases. It helps capture diminishing returns."),
            ("Theta", "The carryover strength used by geometric adstock."),
            ("Alpha and K", "Hill saturation shape parameters. Alpha controls curve steepness. K is the half-saturation point."),
            ("Regularization", "Penalty applied to shrink unstable model coefficients in Ridge, Lasso, and ElasticNet."),
        ],
    )
    render_reference_values_expander(
        "Reference values for transforms",
        [
            ("Theta", "0.1 to 0.3 short carryover", "Use lower values when channel effects fade quickly."),
            ("Theta", "0.4 to 0.6 medium carryover", "Use mid-range values for steady channels with some persistence."),
            ("Theta", "0.7 to 0.9 long carryover", "Use higher values only when the channel effect clearly lingers."),
            ("Hill alpha", "0.5 to 1.5 softer curve", "Good when response fades gradually as spend increases."),
            ("Hill alpha", "1.5 to 3.0 steeper curve", "Good when response changes sharply around the turning point."),
            ("Hill k", "close to typical spend", "Start near median or average spend if you want half-saturation near normal budget levels."),
            ("Regularization alpha", "0.1 to 2.0 common starting range", "Increase when coefficients look unstable or channels are highly correlated."),
            ("ElasticNet l1 ratio", "0.2 to 0.8 practical range", "Use lower values for stability and higher values for stronger variable selection."),
        ],
    )
    df = st.session_state["df"]
    channel_cols = st.session_state["channel_cols"]
    control_cols = st.session_state["control_cols"]

    ai_setup_recommendations = st.session_state.get("ai_setup_recommendations")
    if ai_setup_recommendations:
        st.info("AI setup suggestions are available. The latest AI run already loaded the suggested transform settings here, and you can re-apply them if you want to overwrite manual edits.")
        if st.button(
            "Apply AI transform suggestions",
            help="Load the AI-suggested transform and regularization values into the controls below.",
        ):
            apply_ai_transform_recommendations()
            st.success("AI transform suggestions were loaded into Config. Review them and click Apply transforms if you want to recompute the transformed dataset with those values.")
            st.rerun()

    adstock_type: dict[str, str] = {}
    saturation_type: dict[str, str] = {}
    adstock_params: dict[str, float] = {}
    saturation_params: dict[str, dict[str, float]] = {}

    for ch in channel_cols:
        current_adstock = st.session_state["adstock_type"].get(ch, "geometric")
        current_saturation = st.session_state["saturation_type"].get(ch, "log")
        current_theta = float(st.session_state["adstock_params"].get(ch, 0.3))
        current_sat = st.session_state["saturation_params"].get(ch, {"alpha": 1.0, "k": 1.0})

        st.subheader(ch)
        col1, col2 = st.columns(2)
        adstock_label = col1.selectbox(
            "Adstock",
            options=["Geometric", "None"],
            index=0 if current_adstock == "geometric" else 1,
            key=f"adstock_type_{ch}",
            help="Choose whether this channel keeps some carryover from earlier time periods.",
        )
        saturation_label = col2.selectbox(
            "Saturation",
            options=["Log", "Hill", "None"],
            index={"log": 0, "hill": 1, "none": 2}[current_saturation],
            key=f"saturation_type_{ch}",
            help="Choose how this channel should reflect diminishing returns as spend increases.",
        )

        adstock_type[ch] = "geometric" if adstock_label == "Geometric" else "none"
        saturation_type[ch] = saturation_label.lower()

        if adstock_type[ch] == "geometric":
            adstock_params[ch] = st.slider(
                f"Theta for {ch}",
                min_value=0.1,
                max_value=0.9,
                value=current_theta,
                step=0.05,
                key=f"theta_{ch}",
                help="Carryover strength for geometric adstock. Higher values mean a longer lingering effect.",
            )
        else:
            adstock_params[ch] = 0.0

        if saturation_type[ch] == "hill":
            default_k = max(float(df[ch].median()), float(df[ch].max()) * 0.1, 1.0)
            sat_col1, sat_col2 = st.columns(2)
            alpha_value = sat_col1.number_input(
                f"Alpha for {ch}",
                min_value=0.1,
                max_value=5.0,
                value=float(current_sat.get("alpha", 1.0)),
                step=0.1,
                key=f"alpha_{ch}",
                help="Hill curve steepness. Higher values create a sharper bend in the response curve.",
            )
            k_value = sat_col2.number_input(
                f"K for {ch}",
                min_value=0.1,
                value=float(current_sat.get("k", default_k)),
                step=1.0,
                key=f"k_{ch}",
                help="Spend level where the Hill curve reaches half of its maximum response.",
            )
            saturation_params[ch] = {"alpha": float(alpha_value), "k": float(k_value)}
        elif saturation_type[ch] == "log":
            saturation_params[ch] = {"alpha": 1.0, "k": 0.0}
        else:
            saturation_params[ch] = {"alpha": 1.0, "k": 0.0}

    st.session_state["reg_alpha"] = st.number_input(
        "Regularization alpha",
        min_value=0.0,
        value=float(st.session_state.get("reg_alpha", 1.0)),
        step=0.1,
        help="Penalty strength for Ridge, Lasso, and ElasticNet. Higher values shrink coefficients more.",
    )
    st.session_state["l1_ratio"] = st.number_input(
        "ElasticNet l1 ratio",
        min_value=0.0,
        max_value=1.0,
        value=float(st.session_state.get("l1_ratio", 0.5)),
        step=0.1,
        help="Balance between Ridge-like and Lasso-like penalty when using ElasticNet.",
    )

    if st.button(
        "Apply transforms",
        type="primary",
        help="Create the transformed media matrix used by the model fit step.",
    ):
        fits_cleared, refit_needed = apply_transform_configuration(
            df=df,
            channel_cols=channel_cols,
            control_cols=control_cols,
            adstock_type=adstock_type,
            saturation_type=saturation_type,
            adstock_params=adstock_params,
            saturation_params=saturation_params,
            reg_alpha=float(st.session_state["reg_alpha"]),
            l1_ratio=float(st.session_state["l1_ratio"]),
        )
        st.success("Transforms applied")
        if fits_cleared:
            st.warning("Transforms changed — previously fitted models have been cleared. Re-fit your models.")
        elif refit_needed:
            st.info("Only regularization changed. Re-fit in the Fit tab to update models with new alpha.")


def render_priors_tab() -> None:
    if not st.session_state.get("valid"):
        st.warning("Load and validate data in the Data tab first.")
        return

    st.caption("Set the Bayesian assumptions here before fitting PyMC. If you are unsure, keep the defaults and fit once before tuning.")
    render_definitions_expander(
        "Definitions for this tab",
        [
            ("Intercept mean", "Starting assumption for the baseline level of the target before channel effects are added."),
            ("Prior family", "Distribution shape used before the model sees the data."),
            ("Sigma scale", "How wide or restrictive a prior should be. Higher values allow more uncertainty."),
            ("Draws, tune, chains", "Sampling settings for PyMC. More of them can improve stability but take longer."),
            ("Channel prior overrides", "Optional per-channel priors that replace the shared channel prior defaults."),
        ],
    )
    render_reference_values_expander(
        "Reference values for priors",
        [
            ("Channel prior family", "HalfNormal by default", "Use this when media should not have a negative effect."),
            ("Channel prior family", "Normal when unsure", "Use this when you want to allow positive or negative media effects."),
            ("Intercept sigma scale", "0.5 to 1.5 typical", "Lower values make the baseline prior tighter and higher values make it looser."),
            ("Channel sigma scale", "0.3 to 1.5 common range", "Lower values shrink channel effects more strongly before the data updates them."),
            ("Control sigma scale", "0.5 to 2.0 common range", "Controls often need more flexibility because they can move in both directions."),
            ("Noise sigma scale", "0.5 to 1.5 typical", "Raise this when the target is noisy and lower it when the signal is clean."),
            ("Draws and tune", "300 to 1000 draws, 200 to 500 tune", "Use the lower end for speed and the higher end when you want more stable posterior summaries."),
            ("Chains", "2 to 4 for robustness", "Use at least 2 chains when you want a basic convergence check. More chains improve reliability but increase runtime."),
        ],
    )
    current_prior = st.session_state["pymc_prior_config"]
    current_sampler = st.session_state["pymc_sampler_config"]
    current_reasoning = st.session_state.get("pymc_prior_reasoning", {})

    with st.form("pymc_priors_form"):
        intercept_mode = st.selectbox(
            "Intercept mean",
            options=["Use data mean", "Set manually"],
            index=0 if current_prior.get("intercept_mu_mode", "data_mean") == "data_mean" else 1,
            help="Choose whether the intercept prior should start from the data average or from a manually entered value.",
        )
        intercept_mu = float(current_prior.get("intercept_mu", 0.0))
        if intercept_mode == "Set manually":
            intercept_mu = st.number_input(
                "Manual intercept mean",
                value=intercept_mu,
                step=10.0,
                help="Manual prior mean for the intercept when you do not want to anchor it to the dataset average.",
            )

        channel_prior_family = st.selectbox(
            "Channel prior family",
            options=["HalfNormal", "Normal"],
            index=0 if current_prior.get("channel_prior_family", "HalfNormal") == "HalfNormal" else 1,
            help="HalfNormal forces non-negative channel effects. Normal allows positive or negative channel effects.",
        )
        pri_col1, pri_col2 = st.columns(2)
        intercept_sigma_scale = pri_col1.number_input(
            "Intercept sigma scale",
            min_value=0.1,
            value=float(current_prior.get("intercept_sigma_scale", 1.0)),
            step=0.1,
            help="Width of the intercept prior relative to the target variation in the data.",
        )
        channel_sigma_scale = pri_col2.number_input(
            "Channel sigma scale",
            min_value=0.1,
            value=float(current_prior.get("channel_sigma_scale", 1.0)),
            step=0.1,
            help="Default width of the prior for channel coefficients.",
        )

        pri_col3, pri_col4 = st.columns(2)
        control_sigma_scale = pri_col3.number_input(
            "Control sigma scale",
            min_value=0.1,
            value=float(current_prior.get("control_sigma_scale", 1.0)),
            step=0.1,
            help="Width of the prior for control coefficients.",
        )
        noise_sigma_scale = pri_col4.number_input(
            "Noise sigma scale",
            min_value=0.1,
            value=float(current_prior.get("noise_sigma_scale", 1.0)),
            step=0.1,
            help="Starting uncertainty for the model residual error term.",
        )

        st.markdown("**Channel prior overrides**")
        channel_prior_overrides = current_prior.get("channel_prior_overrides", {})
        channel_override_values: dict[str, dict[str, Any]] = {}
        for channel in st.session_state.get("channel_cols", []):
            override = channel_prior_overrides.get(channel, {})
            override_col1, override_col2 = st.columns(2)
            family = override_col1.selectbox(
                f"Prior family for {channel}",
                options=["HalfNormal", "Normal"],
                index=0 if override.get("family", current_prior.get("channel_prior_family", "HalfNormal")) == "HalfNormal" else 1,
                key=f"prior_family_override_{channel}",
                help="Override the default prior family for this specific channel.",
            )
            sigma_scale = override_col2.number_input(
                f"Sigma scale for {channel}",
                min_value=0.1,
                value=float(override.get("sigma_scale", current_prior.get("channel_sigma_scale", 1.0))),
                step=0.1,
                key=f"prior_sigma_override_{channel}",
                help="Override the default prior width for this specific channel.",
            )
            channel_override_values[channel] = {
                "family": family,
                "sigma_scale": float(sigma_scale),
            }
            if current_reasoning.get(channel):
                st.caption(f"{channel} reasoning: {current_reasoning[channel]}")

        sampler_col1, sampler_col2, sampler_col3 = st.columns(3)
        draws = sampler_col1.number_input(
            "Draws",
            min_value=100,
            value=int(current_sampler.get("draws", 300)),
            step=100,
            help="Posterior samples kept after tuning. More draws improve stability but take longer.",
        )
        tune = sampler_col2.number_input(
            "Tune",
            min_value=100,
            value=int(current_sampler.get("tune", 200)),
            step=100,
            help="Warm-up iterations used before collecting the posterior draws.",
        )
        chains = sampler_col3.number_input(
            "Chains",
            min_value=1,
            max_value=4,
            value=int(current_sampler.get("chains", 1)),
            step=1,
            help="Independent MCMC runs. More chains improve robustness but increase runtime.",
        )

        saved = st.form_submit_button(
            "Save priors",
            type="primary",
            help="Save the current Bayesian prior settings for the next PyMC fit.",
        )

    if saved:
        prior_config = {
            "intercept_mu_mode": "data_mean" if intercept_mode == "Use data mean" else "manual",
            "intercept_mu": float(intercept_mu),
            "intercept_sigma_scale": float(intercept_sigma_scale),
            "channel_prior_family": channel_prior_family,
            "channel_sigma_scale": float(channel_sigma_scale),
            "control_sigma_scale": float(control_sigma_scale),
            "noise_sigma_scale": float(noise_sigma_scale),
            "channel_prior_overrides": channel_override_values,
        }
        sampler_config = {
            "draws": int(draws),
            "tune": int(tune),
            "chains": int(chains),
        }
        new_signature = compute_signature(
            {"prior_config": prior_config, "sampler_config": sampler_config}
        )
        old_signature = st.session_state.get("pymc_prior_signature")

        st.session_state["pymc_prior_config"] = prior_config
        st.session_state["pymc_sampler_config"] = sampler_config
        st.session_state["pymc_prior_signature"] = new_signature

        if old_signature != new_signature and "PyMC" in st.session_state["model_results"] and remove_model_outputs(["PyMC"]):
            st.warning("PyMC priors changed. The previous PyMC result was cleared.")

        st.success("PyMC priors saved")


def render_fit_tab() -> None:
    if not st.session_state.get("transforms_applied"):
        st.warning("Apply transforms in the Config tab first.")
        return

    st.caption("Fit the models here. Start with OLS and Ridge for a quick baseline, then compare them with Lasso, ElasticNet, and PyMC.")
    render_definitions_expander(
        "Definitions for this tab",
        [
            ("OLS", "Simple linear baseline with no regularization."),
            ("Ridge", "Regularized linear model that shrinks unstable coefficients."),
            ("Lasso", "Regularized linear model that can shrink some coefficients heavily."),
            ("ElasticNet", "Blend of Ridge and Lasso penalties."),
            ("PyMC", "Bayesian model that produces probability-based coefficient and CPL ranges."),
        ],
    )
    available_models = list(MODEL_BUILDERS.keys())
    if not is_pymc_available():
        available_models = [model_name for model_name in available_models if model_name != "PyMC"]
        st.info("PyMC is not installed in this environment, so only the frequentist models are available.")
    selected_models = st.multiselect(
        "Models to fit",
        options=available_models,
        default=["OLS"],
        help="Choose one or more models to estimate on the transformed dataset.",
    )
    st.info("PyMC uses the Priors tab settings. Lasso and ElasticNet use the regularization settings from Config.")

    fit_selected = st.button(
        "Fit selected",
        type="primary",
        help="Run only the models currently selected in the list above.",
    )
    fit_all = st.button(
        "Fit all",
        help="Run all available model types on the current transformed dataset.",
    )

    models_to_run = available_models if fit_all else selected_models if fit_selected else []
    if not models_to_run:
        return

    raw_spend = {
        ch: st.session_state["df"][ch].to_numpy(dtype=np.float64)
        for ch in st.session_state["channel_cols"]
    }
    X = st.session_state["X_transformed"]
    y = st.session_state["y"]
    date_values = st.session_state["df"][st.session_state["date_col"]]

    for model_name in models_to_run:
        builder = MODEL_BUILDERS[model_name]
        with st.spinner(f"Fitting {model_name}"):
            try:
                model = builder()
                kwargs: dict[str, Any] = {
                    "channel_names": st.session_state["channel_cols"],
                    "control_names": st.session_state["control_cols"],
                }
                if model_name == "Ridge":
                    kwargs["reg_alpha"] = st.session_state["reg_alpha"]
                if model_name == "Lasso":
                    kwargs["reg_alpha"] = st.session_state["reg_alpha"]
                if model_name == "ElasticNet":
                    kwargs["reg_alpha"] = st.session_state["reg_alpha"]
                    kwargs["l1_ratio"] = st.session_state["l1_ratio"]
                if model_name == "PyMC":
                    kwargs["prior_config"] = st.session_state["pymc_prior_config"]
                    kwargs["sampler_config"] = st.session_state["pymc_sampler_config"]
                    st.info("PyMC can take longer than OLS and Ridge.")
                result = model.fit(X, y, raw_spend=raw_spend, **kwargs)
                if model_name == "PyMC":
                    holdout_meta = None
                else:
                    try:
                        holdout_meta = compute_holdout_diagnostics(
                            builder=builder,
                            X=X,
                            y=y,
                            raw_spend=raw_spend,
                            model_kwargs=kwargs,
                            date_values=date_values,
                        )
                    except Exception as exc:
                        holdout_meta = None
                        st.warning(f"{model_name} holdout validation could not be computed: {exc}")
                bayesian_diagnostics = (
                    model.get_diagnostics()
                    if hasattr(model, "get_diagnostics")
                    else None
                )
                result.model_name = model_name
                st.session_state["model_results"][model_name] = result
                st.session_state["model_results_meta"][model_name] = {
                    "fitted_at": datetime.now().isoformat(timespec="seconds"),
                    "holdout": holdout_meta,
                    "bayesian_diagnostics": bayesian_diagnostics,
                }
                st.success(f"{model_name}: R² = {result.r_squared:.2f}, RMSE = {result.rmse:,.0f}")
            except Exception as exc:
                st.error(f"{model_name} failed: {exc}")

    if st.session_state["model_results"] and not st.session_state.get("selected_model"):
        st.session_state["selected_model"] = next(iter(st.session_state["model_results"].keys()))


def build_model_comparison_df() -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    y = st.session_state.get("y")
    for name, result in st.session_state["model_results"].items():
        mape_value, mape_coverage = compute_mape_non_zero(y, result.y_pred)
        holdout_meta = st.session_state.get("model_results_meta", {}).get(name, {}).get("holdout")
        row: dict[str, Any] = {
            "Model": name,
            "R² in-sample": round(float(result.r_squared), 3),
            "RMSE in-sample": round(float(result.rmse), 2),
            "MAE in-sample": round(float(np.mean(np.abs(y - result.y_pred))), 2),
            "MAPE in-sample (%)": round(mape_value, 2) if mape_value is not None else None,
            "MAPE in-sample coverage": mape_coverage,
        }
        if holdout_meta is not None:
            row["R² holdout"] = round(float(holdout_meta["holdout_r_squared"]), 3)
            row["RMSE holdout"] = round(float(holdout_meta["holdout_rmse"]), 2)
            row["MAE holdout"] = round(float(holdout_meta["holdout_mae"]), 2)
            row["MAPE holdout (%)"] = (
                round(float(holdout_meta["holdout_mape"]), 2)
                if holdout_meta["holdout_mape"] is not None
                else None
            )
            row["MAPE holdout coverage"] = holdout_meta["holdout_coverage"]
        rows.append(row)
    return pd.DataFrame(rows)


def build_recommendation_lines(
    *,
    best_name: str | None,
    best_value: float | None,
    worst_name: str | None,
    worst_value: float | None,
    reallocation_pct: int,
    holdout_meta: dict[str, Any] | None,
    residual_gap_share: float,
    negative_signal_channels: list[str],
    selected_period: str,
    visible_channels: list[str],
) -> list[str]:
    caution_reasons: list[str] = []
    if holdout_meta is None:
        caution_reasons.append("No holdout validation is available yet.")
    else:
        holdout_r_squared = float(holdout_meta.get("holdout_r_squared", 0.0))
        holdout_mape = holdout_meta.get("holdout_mape")
        if holdout_r_squared < 0.2:
            caution_reasons.append(f"Holdout R² is only {holdout_r_squared:.2f}.")
        if holdout_mape is not None and float(holdout_mape) > 30.0:
            caution_reasons.append(f"Holdout MAPE is {float(holdout_mape):.1f}%.")
    if residual_gap_share > 20.0:
        caution_reasons.append(f"Unexplained gap is {residual_gap_share:.1f}% of actual leads.")
    if negative_signal_channels:
        caution_reasons.append(
            "Negative fitted media signals are present for "
            + ", ".join(negative_signal_channels)
            + "."
        )
    if best_name is None or worst_name is None:
        caution_reasons.append(
            "The current view does not have enough rankable positive-CPL channels to support a best-versus-worst recommendation."
        )
    if selected_period != "All data":
        caution_reasons.append(
            f"The current recommendation is based on the filtered period view `{selected_period}`."
        )

    if caution_reasons:
        return [
            "- Treat the current recommendation as directional only.",
            "- Validate the result before reallocating budget, ideally with a controlled test or a rerun after improving the model.",
            *[f"- Reason: {reason}" for reason in caution_reasons],
        ]

    return [
        f"- Invest more in {best_name or 'the best channel'} — currently {format_cpl(best_value)}",
        f"- Reduce spend on {worst_name or 'the weakest channel'} — {format_cpl(worst_value)}",
        f"- Reallocate {reallocation_pct}% from {worst_name or 'the weakest channel'} to {best_name or 'the strongest channel'} — directional heuristic based on current modeled CPL",
        f"- This view is based on {len(visible_channels)} selected channel(s); re-check the recommendation if you change the filter.",
    ]


def build_residual_label() -> str:
    return "Unexplained gap"


def build_pre_saturation_series(
    values: np.ndarray,
    *,
    adstock_kind: str,
    theta: float,
) -> np.ndarray:
    series = np.asarray(values, dtype=np.float64)
    if adstock_kind == "geometric":
        return geometric_adstock(series, theta)
    return series


def render_results_tab() -> None:
    if not st.session_state.get("model_results"):
        st.info("Fit at least one model in the Fit tab to see results.")
        return

    st.caption("Read the outputs in order. Start with the model comparison, then use the three sections below to answer what is happening, why, and what to do next.")
    render_definitions_expander(
        "Definitions for this tab",
        [
            ("R²", "Share of variation explained by the model. Higher is better, but it is still an in-sample metric here."),
            ("RMSE", "Average prediction error in target units. Lower is better."),
            ("CPL", "Cost per lead. Lower means more efficient media."),
            ("Contribution", "Bounded business-facing channel contribution over the selected view."),
            ("Baseline", "Bounded non-media contribution after clipping negative components and scaling to actual leads."),
            ("Unexplained gap", "Remaining positive lead volume not assigned to media or baseline in the business-facing decomposition."),
        ],
    )
    render_reference_values_expander(
        "Reference values for reading results",
        [
            ("R²", "Below 0.30 weak signal", "Treat the model as directional only and investigate missing drivers or noisy data."),
            ("R²", "0.30 to 0.60 usable", "Good enough for early insight and internal discussion, especially in fast MMM prototypes."),
            ("R²", "Above 0.60 strong for this type of app", "Usually means the model explains a large share of observed movement, but still validate out of sample."),
            ("MAPE non-zero", "Below 20% often workable", "Lower is better. Use with RMSE and business context, not as a single pass/fail rule."),
            ("Unexplained gap", "Closer to 0% is better", "Lower unexplained share means more of the observed leads are covered by the business-facing decomposition."),
            ("CPL", "Lower is better", "Compare channels relative to each other, not against one universal number."),
            ("Contribution share", "Large share plus low CPL is strongest", "A channel is more persuasive when it combines meaningful volume with efficient CPL."),
            ("Recommendation quality", "Use as directional guidance", "Treat the action section as a heuristic, not a forecast or final media plan."),
        ],
    )

    model_names = list(st.session_state["model_results"].keys())
    current_model = st.session_state.get("selected_model") or model_names[0]
    selected_model = st.selectbox(
        "View model",
        options=model_names,
        index=model_names.index(current_model),
        help="Choose which fitted model drives the detail sections below.",
    )
    st.session_state["selected_model"] = selected_model
    result = st.session_state["model_results"][selected_model]
    loaded_source = st.session_state.get("loaded_source", "unknown_source")
    date_col = st.session_state["date_col"]
    date_series = st.session_state["df"][date_col]
    period_options = ["All data", "Last 4 weeks", "Last 8 weeks", "Last 12 weeks", "Last 26 weeks"]
    previous_period = st.session_state.get("results_period", "All data")
    selected_period = st.selectbox(
        "Display period",
        options=period_options,
        index=period_options.index(previous_period) if previous_period in period_options else 0,
        help="Filter all Results visuals and metrics to a recent window.",
    )
    st.session_state["results_period"] = selected_period
    period_mask = build_period_mask(date_series, selected_period)
    granularity_options = get_time_granularity_options(date_series)
    previous_visual_granularity = st.session_state.get(
        "results_visual_granularity",
        get_default_time_granularity(date_series),
    )
    selected_visual_granularity = st.selectbox(
        "Visual granularity",
        options=granularity_options,
        index=granularity_options.index(previous_visual_granularity)
        if previous_visual_granularity in granularity_options
        else granularity_options.index(get_default_time_granularity(date_series)),
        help="Choose the time aggregation used by time-based visuals. Weekly is the default when the source grain allows it.",
    )
    st.session_state["results_visual_granularity"] = selected_visual_granularity

    actual_values = st.session_state["y"]
    actual_total = float(actual_values[period_mask].sum())
    channel_totals, baseline_total, residual_total = compute_display_attribution(
        result,
        actual_values,
        row_mask=period_mask,
    )
    predicted_total = float(np.sum(result.y_pred[period_mask]))
    residual_share = (
        (residual_total / actual_total) * 100 if not math.isclose(actual_total, 0.0) else 0.0
    )
    residual_share_abs = abs(residual_share)
    if math.isclose(residual_share, 0.0, abs_tol=0.05):
        residual_share = 0.0
    if math.isclose(residual_share_abs, 0.0, abs_tol=0.05):
        residual_share_abs = 0.0

    default_visual_channels = st.session_state.get("selected_visual_channels") or result.channel_names
    selected_visual_channels = st.multiselect(
        "Variables shown in charts",
        options=result.channel_names,
        default=[channel for channel in default_visual_channels if channel in result.channel_names],
        help="Choose which channels appear in the charts and breakdown tables.",
    )
    st.session_state["selected_visual_channels"] = selected_visual_channels or result.channel_names
    visible_channels = st.session_state["selected_visual_channels"]
    visible_channel_totals = {
        channel: channel_totals.get(channel, 0.0)
        for channel in visible_channels
    }
    media_total = sum(channel_totals.values())
    visible_media_total = sum(visible_channel_totals.values())
    hidden_media_total = sum(
        float(value)
        for channel, value in channel_totals.items()
        if channel not in visible_channels
    )
    residual_label = build_residual_label()
    _, all_cpl_map = compute_view_channel_metrics(
        st.session_state["df"],
        result.channel_names,
        period_mask,
        channel_totals,
    )
    visible_spend_totals, visible_cpl_map = compute_view_channel_metrics(
        st.session_state["df"],
        visible_channels,
        period_mask,
        visible_channel_totals,
    )
    negative_signal_channels = [
        channel for channel in visible_channels
        if float(result.coefficients.get(channel, 0.0)) < 0.0
    ]
    show_baseline = st.checkbox(
        "Show baseline and unexplained components",
        value=bool(st.session_state.get("show_baseline_visual", True)),
        help="Include bounded baseline and unexplained components in the visual summaries.",
    )
    st.session_state["show_baseline_visual"] = show_baseline

    st.subheader("Model comparison")
    st.caption("Compare the fitted models first. Use this section to see whether the ranking and fit quality are broadly consistent across methods.")
    comparison_df = build_model_comparison_df()
    st.dataframe(comparison_df, width="stretch")
    st.caption("Model comparison table. In-sample columns describe the final fitted model. Holdout columns describe a time-based validation split using the latest 20% of periods.")
    st.info(
        "Business note: the contribution, baseline, and unexplained values below use a bounded decomposition for stakeholder readability. Negative raw components are clipped at zero and rescaled to actual leads."
    )

    coefficient_df = pd.DataFrame(
        {
            name: {
                channel: st.session_state["model_results"][name].coefficients.get(channel)
                for channel in st.session_state["selected_visual_channels"]
            }
            for name in model_names
        }
    )
    st.dataframe(coefficient_df, width="stretch")
    st.caption("Coefficient comparison table. Use it to compare direction and relative strength across models.")

    cpl_df = pd.DataFrame(
        {
            name: {
                channel: format_cpl(st.session_state["model_results"][name].cpl.get(channel))
                for channel in st.session_state["selected_visual_channels"]
            }
            for name in model_names
        }
    )
    st.dataframe(cpl_df, width="stretch")
    st.caption("CPL comparison table. Lower CPL means the channel is more efficient in that model. `N/A` means the model assigned zero or negative attributed leads to that channel in the selected fit.")

    best_name, best_value = pick_best_channel(all_cpl_map)
    best_visible_name, best_visible_value = pick_best_channel(visible_cpl_map)
    fitted_at = st.session_state["model_results_meta"].get(selected_model, {}).get("fitted_at")

    st.subheader("What is happening?")
    st.caption("Use this section for the top-line picture. It compares actual leads with a bounded business-facing decomposition into media contribution, baseline contribution, and unexplained gap.")
    col1, col2, col3, col4 = st.columns(4)
    col1.metric(
        "Total leads",
        format_number(actual_total),
        help="All observed leads in the loaded dataset.",
    )
    col2.metric(
        "Media contribution",
        format_number(media_total),
        help="Bounded media contribution from all channels in the selected period.",
    )
    col3.metric(
        "Baseline contribution",
        format_number(baseline_total),
        help="Bounded baseline contribution from intercept and control effects in the selected period.",
    )
    col4.metric(
        residual_label,
        format_number(residual_total),
        f"{residual_share:.1f}% of actual",
        help="Positive unexplained lead volume left after the bounded business-facing decomposition is applied.",
    )
    col5, col6 = st.columns(2)
    col5.metric(
        "Top channel by CPL",
        best_name or "N/A",
        format_cpl(best_value) if best_value is not None else None,
        help="The rankable channel with the lowest positive cost per lead across all channels in the selected model.",
    )
    col6.metric(
        "Model fit",
        f"R² {result.r_squared:.2f}",
        f"RMSE {result.rmse:,.0f}",
        help="R² shows how much variation the model explains. RMSE shows the average prediction error in leads.",
    )
    summary_rows = [{"Component": "Media contribution", "Value": media_total}]
    if show_baseline:
        summary_rows.append({"Component": "Baseline contribution", "Value": baseline_total})
        summary_rows.append({"Component": residual_label, "Value": residual_total})
    summary_df = pd.DataFrame(summary_rows)
    summary_df["Label"] = summary_df["Value"].apply(format_signed_number)
    st.altair_chart(
        build_signed_bar_chart(
            summary_df,
            "Component",
            "Value",
            "Label",
            "Business-facing lead decomposition in the selected period",
        )
    )
    st.caption(
        f"Predicted leads for the selected period are {format_signed_number(predicted_total)}. The displayed baseline and unexplained values are bounded for business readability and sum back to actual leads with media."
    )
    if hidden_media_total:
        st.info(
            f"The current channel filter hides {format_number(hidden_media_total)} of media contribution. The contribution, baseline, and unexplained metrics above still reflect the full selected model, while the channel-specific tables and charts below use the current filter."
        )
    actual_vs_pred_source_df = pd.DataFrame(
        {
            "date": pd.to_datetime(date_series[period_mask]).reset_index(drop=True),
            "actual": np.asarray(actual_values[period_mask], dtype=np.float64),
            "predicted": np.asarray(result.y_pred[period_mask], dtype=np.float64),
        }
    )
    actual_vs_pred_chart_df = aggregate_time_series_df(
        actual_vs_pred_source_df,
        date_col="date",
        value_columns=["actual", "predicted"],
        granularity=selected_visual_granularity,
    )
    actual_vs_pred_rows = []
    label_stride = max(1, len(actual_vs_pred_chart_df) // 10) if len(actual_vs_pred_chart_df) > 0 else 1
    for idx, row in actual_vs_pred_chart_df.iterrows():
        actual_vs_pred_rows.append(
            {
                "date": row["date"],
                "series": "Actual leads",
                "leads": float(row["actual"]),
                "label": format_number(float(row["actual"])) if idx % label_stride == 0 else "",
            }
        )
        actual_vs_pred_rows.append(
            {
                "date": row["date"],
                "series": "Predicted leads",
                "leads": float(row["predicted"]),
                "label": format_number(float(row["predicted"])) if idx % label_stride == 0 else "",
            }
        )
    actual_vs_pred_df = pd.DataFrame(actual_vs_pred_rows)
    if not actual_vs_pred_df.empty:
        st.altair_chart(
            build_actual_vs_predicted_chart(
                actual_vs_pred_df,
                f"Actual vs predicted leads over time ({selected_visual_granularity})",
            )
        )
    if fitted_at:
        st.caption(f"Model fitted on: {fitted_at}")
    holdout_meta = st.session_state["model_results_meta"].get(selected_model, {}).get("holdout")
    if selected_model == "PyMC" and holdout_meta is None:
        st.caption("Holdout validation is currently skipped for PyMC to keep Bayesian fits lighter during demo usage.")
    if holdout_meta is not None:
        st.subheader("Validation diagnostics")
        st.caption(
            "This section shows a simple time-based holdout check using the latest 20% of periods as validation data."
        )
        holdout_df = holdout_meta["holdout_df"].copy()
        holdout_chart_df = aggregate_time_series_df(
            holdout_df,
            date_col="date",
            value_columns=["actual", "predicted"],
            granularity=selected_visual_granularity,
        )
        holdout_rows = []
        label_stride = max(1, len(holdout_chart_df) // 8) if len(holdout_chart_df) > 0 else 1
        for idx, row in holdout_chart_df.iterrows():
            holdout_rows.append(
                {
                    "date": row["date"],
                    "series": "Actual leads",
                    "leads": float(row["actual"]),
                    "label": format_number(float(row["actual"])) if idx % label_stride == 0 else "",
                }
            )
            holdout_rows.append(
                {
                    "date": row["date"],
                    "series": "Predicted leads",
                    "leads": float(row["predicted"]),
                    "label": format_number(float(row["predicted"])) if idx % label_stride == 0 else "",
                }
            )
        holdout_plot_df = pd.DataFrame(holdout_rows)
        if not holdout_plot_df.empty:
            st.altair_chart(
                build_actual_vs_predicted_chart(
                    holdout_plot_df,
                    f"Holdout actual vs predicted leads ({selected_visual_granularity})",
                )
            )
        residual_df = holdout_chart_df.copy()
        residual_df["residual"] = residual_df["actual"] - residual_df["predicted"]
        residual_df["label"] = residual_df["residual"].apply(
            lambda value: format_signed_number(float(value)) if abs(float(value)) >= residual_df["residual"].abs().max() * 0.6 else ""
        )
        residual_chart = (
            alt.Chart(residual_df)
            .mark_bar()
            .encode(
                x=alt.X("date:T", title="Date"),
                y=alt.Y("residual:Q", title="Residual"),
                color=alt.condition(
                    alt.datum.residual >= 0,
                    alt.value("#4C78A8"),
                    alt.value("#F58518"),
                ),
                tooltip=[
                    alt.Tooltip("date:T", title="Date"),
                    alt.Tooltip("actual:Q", title="Actual", format=",.2f"),
                    alt.Tooltip("predicted:Q", title="Predicted", format=",.2f"),
                    alt.Tooltip("residual:Q", title="Residual", format=",.2f"),
                ],
            )
            .properties(title=f"Holdout residuals ({selected_visual_granularity})", height=260, width="container")
        )
        st.altair_chart(residual_chart)

    bayesian_diagnostics = st.session_state["model_results_meta"].get(selected_model, {}).get(
        "bayesian_diagnostics"
    )
    if selected_model == "PyMC" and isinstance(bayesian_diagnostics, dict):
        st.subheader("Bayesian diagnostics")
        st.caption(
            "Use this section to judge whether the PyMC sampler was stable enough to trust the Bayesian interval story."
        )
        diag_col1, diag_col2, diag_col3, diag_col4 = st.columns(4)
        diag_col1.metric("Chains", str(bayesian_diagnostics.get("chains", "N/A")))
        diag_col2.metric("Divergences", str(bayesian_diagnostics.get("divergences", "N/A")))
        diag_col3.metric(
            "Max r_hat",
            f"{float(bayesian_diagnostics['max_rhat']):.3f}"
            if bayesian_diagnostics.get("max_rhat") is not None
            else "N/A",
        )
        diag_col4.metric(
            "Min ESS bulk",
            f"{float(bayesian_diagnostics['min_ess_bulk']):.0f}"
            if bayesian_diagnostics.get("min_ess_bulk") is not None
            else "N/A",
        )

        diagnostic_status = str(bayesian_diagnostics.get("status", "unknown"))
        if diagnostic_status == "healthy":
            st.success(
                "PyMC diagnostics look acceptable for this app. Interval outputs are still directional, but the sampler did not raise the main warning signs."
            )
        elif diagnostic_status == "insufficient_chains":
            st.warning(
                "Only one chain was available, so convergence checks are too weak for a strong interval claim. Treat the PyMC uncertainty outputs as directional."
            )
        elif diagnostic_status == "sampler_warnings":
            st.warning(
                "The sampler reported divergences or tree-depth issues. Treat the PyMC uncertainty outputs as low confidence until the model is rerun with a more stable setup."
            )
        else:
            st.warning(
                "The sampler showed weak convergence diagnostics. Treat the PyMC interval outputs as low confidence until the model is rerun with a more stable setup."
            )

        st.markdown(
            """
            **How to read these diagnostics**

            - `Divergences` mean the sampler had trouble exploring the posterior cleanly
            - `r_hat` should be very close to `1.00`; values above about `1.01` are a warning sign
            - `ESS` means effective sample size; higher is better because the sampler produced more useful independent information
            """
        )
        flagged_parameters = bayesian_diagnostics.get("flagged_parameters") or []
        if flagged_parameters:
            st.markdown("**Parameters with warnings**")
            st.dataframe(pd.DataFrame(flagged_parameters), width="stretch")

    st.subheader("Why is it happening?")
    st.caption("Use this section to explain channel efficiency. Focus on CPL, bounded contribution, and each channel's share of actual leads in the current filtered view.")
    if negative_signal_channels:
        st.warning(
            "Some selected channels have negative fitted coefficients: "
            + ", ".join(negative_signal_channels)
            + ". Treat their efficiency story with extra caution."
        )
    if hidden_media_total > 0:
        st.info(
            f"The current chart filter hides {format_number(hidden_media_total)} of media contribution. Hidden media is excluded from the channel table and charts below, but it is not folded into the unexplained gap."
        )
    if selected_period != "All data" and any(
        st.session_state["adstock_type"].get(channel, "geometric") == "geometric"
        for channel in visible_channels
    ):
        st.warning(
            "Selected-period CPL is directional in this filtered view because adstock can carry prior-period spend into the current window while spend totals are counted only inside the selected period."
        )
    why_rows: list[dict[str, Any]] = []
    for channel in st.session_state["selected_visual_channels"]:
        contribution_total = float(visible_channel_totals.get(channel, 0.0))
        row = {
            "Channel": channel,
            "Coefficient": round(float(result.coefficients[channel]), 4),
            "CPL": format_cpl(visible_cpl_map[channel]),
            "Contribution": round(contribution_total, 2),
            "Share of actual (%)": round((contribution_total / actual_total) * 100, 2)
            if not math.isclose(actual_total, 0.0)
            else 0.0,
        }
        if result.coefficient_lower is not None:
            row["Coefficient lower"] = round(float(result.coefficient_lower[channel]), 4)
            row["Coefficient upper"] = round(float(result.coefficient_upper[channel]), 4)
            row["CPL lower"] = format_cpl(result.cpl_lower[channel])
            row["CPL upper"] = format_cpl(result.cpl_upper[channel])
        why_rows.append(row)
    why_df = pd.DataFrame(why_rows)
    st.dataframe(why_df, width="stretch")
    st.caption(
        "Contribution share here is the bounded business-facing contribution divided by actual leads in the selected period."
    )
    total_visible_spend = float(sum(visible_spend_totals.values()))
    benchmarking_rows = []
    for channel in visible_channels:
        spend_total = float(visible_spend_totals[channel])
        contribution_total = float(visible_channel_totals[channel])
        spend_share = (spend_total / total_visible_spend) * 100 if not math.isclose(total_visible_spend, 0.0) else 0.0
        contribution_share = (contribution_total / actual_total) * 100 if not math.isclose(actual_total, 0.0) else 0.0
        benchmarking_rows.append(
            {
                "Channel": channel,
                "Metric": "Spend share",
                "SharePct": spend_share,
                "Total": spend_total,
                "Label": f"{spend_share:.0f}%",
                "MinShare": min(spend_share, contribution_share),
                "MaxShare": max(spend_share, contribution_share),
            }
        )
        benchmarking_rows.append(
            {
                "Channel": channel,
                "Metric": "Contribution share",
                "SharePct": contribution_share,
                "Total": contribution_total,
                "Label": f"{contribution_share:.0f}%",
                "MinShare": min(spend_share, contribution_share),
                "MaxShare": max(spend_share, contribution_share),
            }
        )
    benchmarking_df = pd.DataFrame(benchmarking_rows)
    if not benchmarking_df.empty:
        st.altair_chart(
            build_spend_vs_contribution_chart(
                benchmarking_df,
                "Spend share vs business-facing contribution share",
            )
        )
        st.caption("Contribution share here is the bounded business-facing contribution divided by actual leads.")
        st.caption("The spend-vs-contribution comparison uses the bounded business-facing decomposition for readability.")

    cpl_chart = {
        channel: value
        for channel, value in visible_cpl_map.items()
        if is_rankable_cpl(value)
    }
    if cpl_chart:
        ordered_series = pd.Series(cpl_chart).sort_values(ascending=True)
        ordered_chart = pd.DataFrame(
            {
                "Channel": ordered_series.index,
                "CPL": ordered_series.values,
                "Label": [format_cpl(value) for value in ordered_series.values],
            }
        )
        st.altair_chart(
            build_labeled_bar_chart(
                ordered_chart,
                "Channel",
                "CPL",
                "Label",
                "CPL by channel",
            )
        )
    elif visible_channels:
        st.info("No rankable CPL values are available in the current visible-channel view because the selected channels have zero or negative attributed leads.")

    st.subheader("What should leadership do next?")
    st.caption("Use this as the action section. The recommendation is directional and based on the current business-facing efficiency view, not a guaranteed forecast.")
    worst_name, worst_value = pick_worst_channel(visible_cpl_map)
    reallocation_pct = 0
    if best_visible_value and worst_value and worst_value > 0:
        reallocation_pct = min(50, round((worst_value - best_visible_value) / worst_value * 100))

    recommendation_lines = build_recommendation_lines(
        best_name=best_visible_name,
        best_value=best_visible_value,
        worst_name=worst_name,
        worst_value=worst_value,
        reallocation_pct=reallocation_pct,
        holdout_meta=holdout_meta,
        residual_gap_share=residual_share_abs,
        negative_signal_channels=negative_signal_channels,
        selected_period=selected_period,
        visible_channels=visible_channels,
    )
    st.markdown("\n".join(recommendation_lines))

    with st.expander("Channel Insights", expanded=False):
        st.caption("Use this section for deeper exploration. You can limit the view to selected channels and compare them against baseline over time.")
        top_n_default = min(5, max(len(visible_channels), 1))
        top_n_channels = st.slider(
            "Top channels shown in time decomposition",
            min_value=1,
            max_value=max(len(visible_channels), 1),
            value=top_n_default,
            help="Show the strongest channels separately and group the rest into `Other`.",
        )
        decomposition_mode = st.selectbox(
            "Time decomposition view",
            options=["Absolute leads", "Share of leads"],
            help="Switch between absolute lead volume and share of leads for each period.",
        )
        ordered_channels = sorted(
            visible_channels,
            key=lambda channel: visible_channel_totals.get(channel, 0.0),
            reverse=True,
        )
        highlighted_channels = ordered_channels[:top_n_channels]
        other_channels = ordered_channels[top_n_channels:]

        channel_vectors, baseline_vector, residual_vector = compute_display_attribution_vectors(
            result,
            st.session_state["y"],
            row_mask=period_mask,
        )
        insight_series = {
            channel: channel_vectors[channel]
            for channel in highlighted_channels
        }
        if other_channels:
            insight_series["other"] = np.sum(
                [channel_vectors[channel] for channel in other_channels],
                axis=0,
            )
        insight_df = pd.DataFrame(insight_series)
        if show_baseline:
            insight_df["baseline"] = baseline_vector
            insight_df["residual_gap"] = residual_vector
        insight_df.insert(0, "date", date_series[period_mask].to_numpy())
        insight_df = aggregate_time_series_df(
            insight_df,
            date_col="date",
            value_columns=[column for column in insight_df.columns if column != "date"],
            granularity=selected_visual_granularity,
        )
        insight_long_df = insight_df.melt(
            id_vars=["date"],
            var_name="variable",
            value_name="leads",
        )
        period_totals = (
            insight_long_df.groupby("date", as_index=False)["leads"].sum().rename(columns={"leads": "total_leads"})
        )
        insight_long_df = insight_long_df.merge(period_totals, on="date", how="left")
        insight_long_df["share_pct"] = np.where(
            insight_long_df["total_leads"] > 0,
            (insight_long_df["leads"] / insight_long_df["total_leads"]) * 100,
            0.0,
        )
        insight_long_df["segment_label"] = insight_long_df["share_pct"].apply(
            lambda value: f"{value:.0f}%" if value >= 12 else ""
        )
        insight_long_df["total_label"] = insight_long_df["total_leads"].apply(
            lambda value: format_number(float(value))
        )
        insight_long_df["SegmentOrder"] = insight_long_df["variable"].apply(
            lambda value: 1 if value not in {"baseline", "residual_gap"} else 2 if value == "baseline" else 3
        )
        share_mode_enabled = decomposition_mode == "Share of leads"
        insight_chart = build_stacked_time_decomposition_chart(
            insight_long_df,
            f"Stacked lead decomposition over time ({selected_visual_granularity})",
            share_mode=share_mode_enabled,
        )
        st.altair_chart(insight_chart)

        st.markdown("**MMM interpretation**")
        st.caption(
            "These diagnostics explain how each channel was transformed before modeling and whether spend looks closer to headroom or saturation."
        )
        visual_scale_factor = infer_granularity_scale_factor(
            st.session_state["df"].loc[period_mask, date_col],
            selected_visual_granularity,
        )
        rows = []
        for channel in st.session_state["selected_visual_channels"]:
            theta = st.session_state["adstock_params"].get(channel, 0.0)
            source_grain = infer_grain(date_series) or "weekly"
            if theta <= 0:
                carryover = "No carryover"
            elif theta >= 1.0:
                carryover = "Indefinite carryover"
            else:
                carryover_periods = round(-math.log(0.05) / -math.log(theta))
                carryover_unit = {"daily": "days", "weekly": "weeks", "monthly": "months"}.get(
                    source_grain,
                    "periods",
                )
                carryover = f"{carryover_periods} {carryover_unit}"
            aggregated_spend_df = aggregate_time_series_df(
                st.session_state["df"].loc[period_mask, [date_col, channel]].reset_index(drop=True),
                date_col=date_col,
                value_columns=[channel],
                granularity=selected_visual_granularity,
            )
            avg_display_spend = float(aggregated_spend_df[channel].mean()) if not aggregated_spend_df.empty else 0.0
            avg_display_contribution = float(
                visible_channel_totals[channel] / max(len(aggregated_spend_df), 1)
            )
            sat_kind = st.session_state["saturation_type"].get(channel, "log")
            sat_params = st.session_state["saturation_params"].get(channel, {"alpha": 1.0, "k": 0.0})
            saturation_status, saturation_note = compute_saturation_status(
                sat_kind,
                avg_display_spend,
                sat_params,
                spend_scale_factor=visual_scale_factor,
            )
            rows.append(
                {
                    "Channel": channel,
                    "Spend total": round(float(visible_spend_totals[channel]), 2),
                    f"Average {selected_visual_granularity.lower()} spend": round(avg_display_spend, 2),
                    "Contribution": round(float(visible_channel_totals[channel]), 2),
                    f"Average {selected_visual_granularity.lower()} contribution": round(avg_display_contribution, 2),
                    "Contribution share (%)": round(
                        (float(visible_channel_totals[channel]) / actual_total) * 100,
                        2,
                    )
                    if not math.isclose(actual_total, 0.0)
                    else 0.0,
                    "CPL": format_cpl(visible_cpl_map[channel]),
                    "Adstock": st.session_state["adstock_type"].get(channel, "geometric"),
                    "Saturation": st.session_state["saturation_type"].get(channel, "log"),
                    "Carryover": carryover,
                    "Saturation status": saturation_status,
                    "Saturation note": saturation_note,
                }
            )
        st.dataframe(pd.DataFrame(rows), width="stretch")

        saturation_chart = build_saturation_curve_chart(
            st.session_state["df"].loc[period_mask].reset_index(drop=True),
            date_col,
            st.session_state["selected_visual_channels"],
            st.session_state["adstock_type"],
            st.session_state["adstock_params"],
            st.session_state["saturation_type"],
            st.session_state["saturation_params"],
            selected_visual_granularity,
        )
        if saturation_chart is not None:
            st.altair_chart(saturation_chart)
        else:
            st.info("No saturation curves to show because the selected channels use `None` saturation.")

    overview_export_df = pd.DataFrame(
        [
            {"Metric": "Source file", "Value": loaded_source},
            {"Metric": "Model", "Value": selected_model},
            {"Metric": "Period", "Value": selected_period},
            {"Metric": "Total leads", "Value": round(actual_total, 2)},
            {"Metric": "Predicted leads", "Value": round(predicted_total, 2)},
            {"Metric": "Media contribution", "Value": round(media_total, 2)},
            {"Metric": "Baseline contribution", "Value": round(baseline_total, 2)},
            {"Metric": residual_label, "Value": round(residual_total, 2)},
            {"Metric": "R_squared", "Value": round(float(result.r_squared), 4)},
            {"Metric": "RMSE", "Value": round(float(result.rmse), 2)},
        ]
    )
    channel_export_rows = []
    for channel in st.session_state["selected_visual_channels"]:
        channel_export_rows.append(
            {
                "Channel": channel,
                "Coefficient": round(float(result.coefficients[channel]), 6),
                "CPL": None if math.isinf(visible_cpl_map[channel]) else round(float(visible_cpl_map[channel]), 4),
                "Contribution": round(float(visible_channel_totals.get(channel, 0.0)), 2),
                "Share_pct": round(
                    (float(visible_channel_totals.get(channel, 0.0)) / actual_total) * 100,
                    4,
                )
                if not math.isclose(actual_total, 0.0)
                else 0.0,
            }
        )
    channel_export_df = pd.DataFrame(channel_export_rows)
    comparison_export_df = comparison_df.copy()

    st.subheader("Export")
    st.caption("Download the current results view as CSV or PDF. The export uses the selected model, period, and channel filter.")
    export_col1, export_col2, export_col3 = st.columns(3)
    export_col1.download_button(
        "Results overview CSV",
        data=df_to_csv_bytes(overview_export_df),
        file_name="mmm_results_overview.csv",
        mime="text/csv",
    )
    export_col2.download_button(
        "Channel breakdown CSV",
        data=df_to_csv_bytes(channel_export_df),
        file_name="mmm_results_channels.csv",
        mime="text/csv",
    )
    export_col3.download_button(
        "Results PDF",
        data=build_results_pdf_bytes(
            selected_model,
            selected_period,
            loaded_source,
            overview_export_df,
            channel_export_df,
            comparison_export_df,
        ),
        file_name="mmm_results_export.pdf",
        mime="application/pdf",
    )

    with st.expander("Quick Insights", expanded=False):
        st.caption("This section condenses the most useful summary points into a small set of operational metrics for the current visible-channel view.")
        overall_cpl = (
            sum(visible_spend_totals.values()) / visible_media_total
            if visible_media_total > 0
            else None
        )
        quick_col1, quick_col2 = st.columns(2)
        quick_col1.metric(
            "Overall marketing CPL",
            format_cpl(overall_cpl),
            help="Total spend divided by total media contribution for the currently visible channels.",
        )
        quick_col2.metric(
            "Best channel",
            best_visible_name or "N/A",
            format_cpl(best_visible_value) if best_visible_value is not None else None,
            help="The visible channel with the lowest cost per lead in the selected model.",
        )
        quick_col3, quick_col4 = st.columns(2)
        quick_col3.metric(
            "Worst channel",
            worst_name or "N/A",
            format_cpl(worst_value) if worst_value is not None else None,
            help="The visible channel with the highest cost per lead in the selected model.",
        )
        quick_col4.metric(
            residual_label,
            format_number(residual_total),
            f"{residual_share:.1f}% of actual",
            help="Positive unexplained lead volume left after the bounded business-facing decomposition.",
        )
        st.info(
            f"Bounded contribution totals in this view: visible media {format_number(visible_media_total)}, baseline {format_number(baseline_total)}."
        )
        saturated_channels = []
        for channel in visible_channels:
            avg_weekly_spend = float(visible_spend_totals[channel] / max(int(np.sum(period_mask)), 1))
            sat_kind = st.session_state["saturation_type"].get(channel, "log")
            sat_params = st.session_state["saturation_params"].get(channel, {"alpha": 1.0, "k": 0.0})
            saturation_status, _ = compute_saturation_status(sat_kind, avg_weekly_spend, sat_params)
            if saturation_status == "over-saturated":
                saturated_channels.append(channel)
        if saturated_channels:
            st.info(
                "Channels closest to diminishing-returns pressure: "
                + ", ".join(saturated_channels)
            )
        else:
            st.info("No selected channel currently looks over-saturated from the configured MMM transform view.")
        if best_visible_name and worst_name and best_visible_name != worst_name:
            st.info(
                f"Current efficiency gap: {best_visible_name} is the strongest channel by CPL while {worst_name} is the weakest in the selected view."
            )


def render_ai_tab() -> None:
    if not st.session_state.get("model_results"):
        st.info("Fit at least one model first to enable AI analysis.")
        return

    selected_model = st.session_state.get("selected_model") or next(
        iter(st.session_state["model_results"].keys())
    )
    result = st.session_state["model_results"][selected_model]
    loaded_source = st.session_state.get("loaded_source", "unknown_source")
    selected_period = st.session_state.get("results_period", "All data")
    selected_visual_channels = st.session_state.get("selected_visual_channels") or result.channel_names
    date_col = st.session_state["date_col"]
    date_series = st.session_state["df"][date_col]
    period_mask = build_period_mask(date_series, selected_period)
    actual_values = st.session_state["y"]
    actual_total = float(actual_values[period_mask].sum())
    channel_totals, baseline_total, residual_total = compute_display_attribution(
        result,
        actual_values,
        row_mask=period_mask,
    )
    visible_channel_totals = {
        channel: channel_totals.get(channel, 0.0)
        for channel in selected_visual_channels
    }
    media_total = sum(visible_channel_totals.values())
    hidden_media_total = sum(
        float(value)
        for channel, value in channel_totals.items()
        if channel not in selected_visual_channels
    )
    residual_label = build_residual_label()
    residual_share = (
        (residual_total / actual_total) * 100 if not math.isclose(actual_total, 0.0) else 0.0
    )
    residual_share_abs = abs(residual_share)
    _, visible_cpl_map = compute_view_channel_metrics(
        st.session_state["df"],
        list(selected_visual_channels),
        period_mask,
        visible_channel_totals,
    )
    best_name, best_value = pick_best_channel(visible_cpl_map)
    worst_name, worst_value = pick_worst_channel(visible_cpl_map)
    negative_signal_channels = [
        channel for channel in selected_visual_channels
        if float(result.coefficients.get(channel, 0.0)) < 0.0
    ]
    holdout_meta = st.session_state["model_results_meta"].get(selected_model, {}).get("holdout")
    reallocation_pct = 0
    if best_value and worst_value and worst_value > 0:
        reallocation_pct = min(50, round((worst_value - best_value) / worst_value * 100))

    provider_options = ["openai"]
    if is_anthropic_available():
        provider_options.append("anthropic")
    render_definitions_expander(
        "Definitions for this tab",
        [
            ("Provider", "The LLM service used to generate the written analysis."),
            ("Executive short", "Shorter summary for quick leadership reading."),
            ("In-depth", "Longer analysis with diagnosis, caveats, and action plan."),
            ("Include all fitted models", "Lets the AI compare consistency across the fitted models."),
            ("Complete overview export", "One final artifact that combines setup reasoning, priors, results, and AI output."),
        ],
    )
    provider = st.radio(
        "Provider",
        options=provider_options,
        index=provider_options.index(st.session_state.get("ai_provider", provider_options[0]))
        if st.session_state.get("ai_provider") in provider_options
        else 0,
        horizontal=True,
        key="ai_provider",
        help="Choose which LLM provider to use for the AI analysis.",
    )

    loaded_provider, api_key, model, ai_error = resolve_ai_credentials()
    if loaded_provider:
        provider = loaded_provider
        st.success(f"AI ready with {provider}")
    else:
        api_key = None
        model = None
        st.warning(ai_error or "AI credentials are not configured.")

    analysis_mode = st.selectbox(
        "Analysis depth",
        options=["In-depth", "Executive short"],
        index=0,
        help="In-depth gives a longer diagnosis with risks, model caveats, and action plan.",
    )
    include_all_models = st.checkbox(
        "Include all fitted models in the analysis context",
        value=True,
        help="When enabled, the AI compares model fit and channel consistency across methods.",
    )
    st.caption("Generate an analysis from the selected model and the current app context. Use this output as a decision support draft.")
    if st.button(
        "Generate analysis",
        type="primary",
        help="Generate a written interpretation of the current model results using the selected AI provider.",
    ):
        if not api_key or not model:
            st.error("Add a valid .env or credentials.json file, or set an API key in the sidebar to enable AI analysis.")
        else:
            try:
                payload = build_payload(
                    result,
                    st.session_state,
                    include_comparison=include_all_models,
                )
                summary = get_summary(
                    payload,
                    provider,
                    api_key,
                    model,
                    detailed=analysis_mode == "In-depth",
                )
                validation = validate_analysis_text(
                    summary,
                    payload,
                    detailed=analysis_mode == "In-depth",
                )
            except Exception as exc:
                st.session_state["ai_summary"] = None
                st.session_state["ai_summary_meta"] = None
                st.error(f"AI summary failed: {exc}")
            else:
                st.session_state["ai_summary"] = summary
                st.session_state["ai_summary_meta"] = {
                    "selected_model": selected_model,
                    "results_period": selected_period,
                    "selected_visual_channels": list(selected_visual_channels),
                    "analysis_mode": analysis_mode,
                    "include_all_models": include_all_models,
                    "provider": provider,
                    "resolved_model": model,
                    "source_file": loaded_source,
                    "generated_at": datetime.now().isoformat(timespec="seconds"),
                    "validation": validation,
                }

    if st.session_state.get("ai_summary"):
        ai_summary_meta = st.session_state.get("ai_summary_meta") or {}
        required_ai_meta_keys = {
            "selected_model",
            "results_period",
            "selected_visual_channels",
            "analysis_mode",
            "include_all_models",
            "provider",
            "resolved_model",
            "source_file",
        }
        generated_for_model = ai_summary_meta.get("selected_model")
        generated_for_period = ai_summary_meta.get("results_period")
        generated_for_channels = ai_summary_meta.get("selected_visual_channels") or []
        generated_for_provider = ai_summary_meta.get("provider")
        generated_for_depth = ai_summary_meta.get("analysis_mode")
        generated_for_comparison_mode = ai_summary_meta.get("include_all_models")
        generated_for_source = ai_summary_meta.get("source_file")
        generated_for_resolved_model = ai_summary_meta.get("resolved_model")
        current_channels_signature = list(selected_visual_channels)
        has_complete_ai_meta = all(key in ai_summary_meta for key in required_ai_meta_keys)
        ai_is_stale = (
            not has_complete_ai_meta
            or generated_for_model != selected_model
            or generated_for_period != selected_period
            or generated_for_channels != current_channels_signature
            or generated_for_provider != provider
            or generated_for_resolved_model != model
            or generated_for_depth != analysis_mode
            or generated_for_comparison_mode != include_all_models
            or generated_for_source != loaded_source
        )
        if generated_for_model or generated_for_period:
            st.caption(
                f"Analysis generated for model `{generated_for_model or selected_model}` and period `{generated_for_period or selected_period}`."
            )
        if ai_is_stale:
            st.warning(
                "The current Results view has changed since this AI analysis was generated. Regenerate the analysis before exporting AI outputs or the complete overview."
            )
        validation_result = ai_summary_meta.get("validation")
        if isinstance(validation_result, dict):
            validation_status = str(validation_result.get("status", "warning"))
            validation_issues = validation_result.get("issues") or []
            if validation_status == "passed":
                st.success("Automatic AI validation passed for this generated response.")
            elif validation_status == "failed":
                st.error(
                    "Automatic AI validation found blocking issues in this generated response. Review the findings before sharing or exporting it."
                )
            else:
                st.warning(
                    "Automatic AI validation found issues in this generated response. Review the findings before sharing or exporting it."
                )
            if validation_issues:
                validation_df = pd.DataFrame(validation_issues)
                st.dataframe(validation_df, width="stretch")
        st.markdown(st.session_state["ai_summary"])
        if not ai_is_stale:
            ai_export_df = pd.DataFrame(
                [
                    {
                        "generated_at": (ai_summary_meta.get("generated_at") or datetime.now().isoformat(timespec="seconds")),
                        "provider": ai_summary_meta.get("provider", provider),
                        "model": ai_summary_meta.get("resolved_model", model),
                        "source_file": ai_summary_meta.get("source_file", loaded_source),
                        "selected_model": generated_for_model or selected_model,
                        "results_period": generated_for_period or selected_period,
                        "validation_status": (
                            validation_result.get("status")
                            if isinstance(validation_result, dict)
                            else None
                        ),
                        "validation_issue_count": (
                            len(validation_result.get("issues") or [])
                            if isinstance(validation_result, dict)
                            else None
                        ),
                        "analysis": st.session_state["ai_summary"],
                    }
                ]
            )
            ai_pdf_bytes = build_text_pdf_bytes(
                "mmm ai analysis export",
                [("analysis", st.session_state["ai_summary"])],
            )
            col_csv, col_pdf = st.columns(2)
            col_csv.download_button(
                "AI analysis CSV",
                data=df_to_csv_bytes(ai_export_df),
                file_name="mmm_ai_analysis.csv",
                mime="text/csv",
                help="Download the current AI analysis as structured CSV text.",
            )
            col_pdf.download_button(
                "AI analysis PDF",
                data=ai_pdf_bytes,
                file_name="mmm_ai_analysis.pdf",
                mime="application/pdf",
                help="Download the current AI analysis as a PDF text export.",
            )

            overview_export_df = pd.DataFrame(
                [
                    {"Metric": "Source file", "Value": ai_summary_meta.get("source_file", loaded_source)},
                    {"Metric": "Model", "Value": selected_model},
                    {"Metric": "Period", "Value": selected_period},
                    {"Metric": "Total leads", "Value": round(actual_total, 2)},
                    {"Metric": "Predicted leads", "Value": round(float(np.sum(result.y_pred[period_mask])), 2)},
                    {"Metric": "Media contribution", "Value": round(media_total, 2)},
                    {"Metric": "Baseline contribution", "Value": round(baseline_total, 2)},
                    {"Metric": residual_label, "Value": round(residual_total, 2)},
                    {"Metric": "R_squared", "Value": round(float(result.r_squared), 4)},
                    {"Metric": "RMSE", "Value": round(float(result.rmse), 2)},
                ]
            )
            comparison_export_df = build_model_comparison_df()
            channel_export_rows = []
            for channel in selected_visual_channels:
                channel_export_rows.append(
                    {
                        "Channel": channel,
                        "Coefficient": round(float(result.coefficients[channel]), 6),
                        "CPL": None if math.isinf(visible_cpl_map[channel]) else round(float(visible_cpl_map[channel]), 4),
                        "Contribution": round(float(visible_channel_totals.get(channel, 0.0)), 2),
                        "Share_pct": round(
                            (float(visible_channel_totals.get(channel, 0.0)) / actual_total) * 100,
                            4,
                        )
                        if not math.isclose(actual_total, 0.0)
                        else 0.0,
                    }
                )
            channel_export_df = pd.DataFrame(channel_export_rows)
            recommendation_lines = build_recommendation_lines(
                best_name=best_name,
                best_value=best_value,
                worst_name=worst_name,
                worst_value=worst_value,
                reallocation_pct=reallocation_pct,
                holdout_meta=holdout_meta,
                residual_gap_share=residual_share_abs,
                negative_signal_channels=negative_signal_channels,
                selected_period=selected_period,
                visible_channels=list(selected_visual_channels),
            )
            complete_overview_df = build_complete_overview_export_df(
                selected_model=selected_model,
                selected_period=selected_period,
                source_name=ai_summary_meta.get("source_file", loaded_source),
                overview_df=overview_export_df,
                comparison_df=comparison_export_df,
                channel_df=channel_export_df,
                recommendation_lines=recommendation_lines,
                ai_analysis=st.session_state.get("ai_summary"),
            )
            complete_overview_pdf = build_complete_overview_pdf_bytes(
                selected_model=selected_model,
                selected_period=selected_period,
                source_name=ai_summary_meta.get("source_file", loaded_source),
                overview_df=overview_export_df,
                comparison_df=comparison_export_df,
                channel_df=channel_export_df,
                recommendation_lines=recommendation_lines,
                ai_analysis=st.session_state.get("ai_summary"),
            )
            st.subheader("Complete overview export")
            st.caption(
                "Download one final overview that includes column-selection reasoning, data checks, transform reasoning, prior choices, current results, and AI suggestions."
            )
            full_col1, full_col2 = st.columns(2)
            full_col1.download_button(
                "Complete overview CSV",
                data=df_to_csv_bytes(complete_overview_df),
                file_name="mmm_complete_overview.csv",
                mime="text/csv",
                help="Download the full project story from setup reasoning through final results as CSV.",
            )
            full_col2.download_button(
                "Complete overview PDF",
                data=complete_overview_pdf,
                file_name="mmm_complete_overview.pdf",
                mime="application/pdf",
                help="Download the full project story from setup reasoning through final results as PDF.",
            )
    else:
        st.info("No summary generated yet.")


def main() -> None:
    st.set_page_config(page_title="MMM — Marketing Mix Modeling", layout="wide")
    st.title("Marketing Mix Modeling")
    st.caption("Use the sidebar step menu to move from data preparation to model results and final analysis.")
    init_state()
    session_notice = st.session_state.get("session_notice")
    if isinstance(session_notice, dict):
        notice_level = session_notice.get("level", "info")
        notice_text = str(session_notice.get("text", ""))
        if notice_text:
            getattr(st, notice_level, st.info)(notice_text)
        st.session_state["session_notice"] = None
    st.sidebar.header("MMM workflow")
    selected_step = render_sidebar_step_menu()
    render_session_controls()
    render_info_sidebar_section()
    st.sidebar.divider()
    st.sidebar.text_input(
        "API key override",
        type="password",
        key="manual_ai_api_key",
        help="Optional manual API key entry used when credentials are not available from file or environment.",
    )
    st.subheader("Guide" if selected_step == "Info" else selected_step)
    st.caption(STEP_DESCRIPTIONS[selected_step])

    if selected_step == "Data":
        render_data_tab()
    elif selected_step == "Overview":
        render_data_overview_tab()
    elif selected_step == "Config":
        render_config_tab()
    elif selected_step == "Priors":
        render_priors_tab()
    elif selected_step == "Info":
        render_info_tab()
    elif selected_step == "Fit":
        render_fit_tab()
    elif selected_step == "Results":
        render_results_tab()
    elif selected_step == "AI":
        render_ai_tab()


if __name__ == "__main__":
    main()
