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
)
from src.app_state import compute_signature, compute_transform_fingerprint, init_state
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
    build_labeled_bar_chart,
    build_period_mask,
    compute_display_attribution,
    compute_mape_non_zero,
    compute_view_channel_metrics,
    format_cpl,
    format_number,
    format_signed_number,
    infer_grain,
    pick_best_channel,
    pick_worst_channel,
)
from src.setup_assistant import (
    apply_ai_prior_recommendations,
    apply_ai_transform_recommendations,
    build_setup_assistant_payload,
    resolve_ai_credentials,
)
from src.transforms import transform_media
from src.utils import convert_mmm_data, normalize_column_names, validate_mmm_data


MODEL_BUILDERS = {
    "OLS": OLSModel,
    "Ridge": RidgeModel,
    "Lasso": LassoModel,
    "ElasticNet": ElasticNetModel,
    "PyMC": PyMCModel,
}

STEP_DESCRIPTIONS = {
    "Data": "Load the dataset, confirm the columns, and validate the input before any modeling.",
    "Config": "Choose media transforms and regularization settings for the modeling step.",
    "Priors": "Review or edit Bayesian prior assumptions before using PyMC.",
    "Fit": "Run one or more models on the transformed dataset.",
    "Results": "Interpret model fit, attribution, efficiency, and exports.",
    "AI": "Generate written analysis and export the complete project overview.",
}


def render_definitions_expander(
    title: str,
    definitions: list[tuple[str, str]],
) -> None:
    with st.expander(title, expanded=False):
        for label, description in definitions:
            st.markdown(f"**{label}**  \n{description}")


def get_step_status(step_name: str) -> str:
    if step_name == "Data":
        return "ready"
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
    ordered_steps = ["Data", "Config", "Priors", "Fit", "Results", "AI"]
    label_to_step = {
        build_step_label(idx + 1, step_name): step_name
        for idx, step_name in enumerate(ordered_steps)
    }
    current_step = st.session_state.get("current_step", "Data")
    selected_label = st.sidebar.radio(
        "Step menu",
        options=list(label_to_step.keys()),
        index=ordered_steps.index(current_step) if current_step in ordered_steps else 0,
        help="Use this menu to move through the MMM workflow from data load to final analysis.",
    )
    selected_step = label_to_step[selected_label]
    st.session_state["current_step"] = selected_step
    st.sidebar.caption(STEP_DESCRIPTIONS[selected_step])
    return selected_step


def load_candidate_dataframe() -> pd.DataFrame | None:
    uploaded_file = st.file_uploader(
        "Upload CSV",
        type=["csv"],
        help="Upload the marketing dataset you want to model. CSV only.",
    )

    local_files = sorted(Path("data").glob("*.csv"))
    selected_name = None
    if local_files:
        selected_name = st.selectbox(
            "Or pick a file from data/",
            options=[path.name for path in local_files],
            index=0,
            help="Choose a CSV that already exists in the app data folder.",
        )
    else:
        st.info("No files in data/ yet — use the uploader above.")

    candidate_df = None
    source_name = None
    if uploaded_file is not None:
        try:
            uploaded_file.seek(0)
            candidate_df = pd.read_csv(uploaded_file)
            candidate_df, rename_map = normalize_column_names(candidate_df)
            source_name = uploaded_file.name
            st.session_state["column_rename_map"] = rename_map
        except Exception as exc:
            st.error(f"Could not read uploaded CSV: {exc}")
            return st.session_state.get("loaded_df")
    elif selected_name:
        selected_path = next(path for path in local_files if path.name == selected_name)
        try:
            candidate_df = pd.read_csv(selected_path)
            candidate_df, rename_map = normalize_column_names(candidate_df)
            source_name = selected_path.name
            st.session_state["column_rename_map"] = rename_map
        except Exception as exc:
            st.error(f"Could not read selected CSV: {exc}")
            return st.session_state.get("loaded_df")

    if candidate_df is not None:
        st.session_state["loaded_df"] = candidate_df
        st.session_state["loaded_source"] = source_name

    return st.session_state.get("loaded_df")


def default_channel_selection(columns: list[str], date_col: str | None, target_col: str | None) -> list[str]:
    blocked = {date_col, target_col}
    return [col for col in columns if col not in blocked and col.endswith("_spend")]


def render_data_tab() -> None:
    st.caption("Start here. Load a CSV, confirm the date, target, and spend columns, then validate the dataset before moving on.")
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

        converted = convert_mmm_data(raw_df, date_col, target_col, channel_cols, control_cols)
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
                st.session_state["transforms_applied"] = False
                st.session_state["transform_fingerprint"] = None
                st.session_state["X_transformed"] = None
                st.session_state["y"] = None
                st.session_state["model_results"] = {}
                st.session_state["model_results_meta"] = {}
                st.session_state["selected_model"] = None
                st.session_state["ai_summary"] = None
                if previous_signature[1] is not None:
                    st.info("Channel selection updated — re-apply transforms in Config and re-fit models.")

            st.success(
                f"Loaded {len(prepared)} rows with columns {', '.join([date_col, target_col, *channel_cols])}"
            )
            if warnings:
                st.warning(" ".join(warnings))
        else:
            st.session_state["valid"] = False
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
                "Ask AI to review the ingested data and suggest transform settings, data consistency checks, data completion actions, and PyMC priors. Suggested priors are applied automatically."
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
                    st.error("Add credentials.json or set an API key in the sidebar to enable AI setup suggestions.")
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
                        apply_ai_prior_recommendations(
                            setup_recommendations.get("prior_recommendations", {})
                        )
                        st.success(
                            "AI setup suggestions are ready. PyMC prior suggestions were applied to the Priors tab."
                        )

            setup_recommendations = st.session_state.get("ai_setup_recommendations")
            if setup_recommendations:
                summary = setup_recommendations.get("executive_summary")
                if summary:
                    st.markdown(summary)

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
    df = st.session_state["df"]
    channel_cols = st.session_state["channel_cols"]
    control_cols = st.session_state["control_cols"]

    ai_setup_recommendations = st.session_state.get("ai_setup_recommendations")
    if ai_setup_recommendations:
        st.info("AI setup suggestions are available. You can apply the suggested transform settings before running the manual transform step.")
        if st.button(
            "Apply AI transform suggestions",
            help="Load the AI-suggested transform and regularization values into the controls below.",
        ):
            apply_ai_transform_recommendations()
            st.success("AI transform suggestions were loaded into Config. Review them and click Apply transforms.")
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
        previous_fingerprint = st.session_state.get("transform_fingerprint")
        previous_reg = st.session_state.get("regularization_signature")
        current_reg = json.dumps(
            {
                "reg_alpha": st.session_state["reg_alpha"],
                "l1_ratio": st.session_state["l1_ratio"],
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
        st.session_state["transforms_applied"] = True
        st.session_state["transform_fingerprint"] = fingerprint
        st.session_state["regularization_signature"] = current_reg

        if st.session_state["model_results"]:
            if previous_fingerprint and previous_fingerprint != fingerprint:
                st.session_state["model_results"] = {}
                st.session_state["model_results_meta"] = {}
                st.session_state["selected_model"] = None
                st.session_state["ai_summary"] = None
                st.warning("Transforms changed — previously fitted models have been cleared. Re-fit your models.")
            elif previous_fingerprint == fingerprint and previous_reg != current_reg:
                st.info("Only regularization changed. Re-fit in the Fit tab to update models with new alpha.")

        st.success("Transforms applied")


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

        if old_signature and old_signature != new_signature and "PyMC" in st.session_state["model_results"]:
            st.session_state["model_results"].pop("PyMC", None)
            st.session_state["model_results_meta"].pop("PyMC", None)
            if st.session_state.get("selected_model") == "PyMC":
                st.session_state["selected_model"] = next(
                    iter(st.session_state["model_results"].keys()),
                    None,
                )
            st.session_state["ai_summary"] = None
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
                result.model_name = model_name
                st.session_state["model_results"][model_name] = result
                st.session_state["model_results_meta"][model_name] = {
                    "fitted_at": datetime.now().isoformat(timespec="seconds")
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
        row: dict[str, Any] = {
            "Model": name,
            "R²": round(float(result.r_squared), 3),
            "RMSE": round(float(result.rmse), 2),
            "MAE": round(float(np.mean(np.abs(y - result.y_pred))), 2),
            "MAPE non-zero (%)": round(mape_value, 2) if mape_value is not None else None,
            "MAPE coverage": mape_coverage,
        }
        rows.append(row)
    return pd.DataFrame(rows)


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
            ("Contribution", "Modeled leads attributed to a channel over the selected view."),
            ("Baseline", "Leads explained by non-media effects and the model intercept."),
            ("Unexplained gap", "Remaining leads not covered by the displayed media and baseline split."),
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

    actual_total = float(st.session_state["y"][period_mask].sum())
    display_channel_totals, baseline_total, unexplained_total = compute_display_attribution(
        result,
        actual_total,
        row_mask=period_mask,
    )
    media_total = sum(display_channel_totals.values())
    unexplained_share = (
        (unexplained_total / actual_total) * 100 if not math.isclose(actual_total, 0.0) else 0.0
    )
    if math.isclose(unexplained_share, 0.0, abs_tol=0.05):
        unexplained_share = 0.0

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
        channel: display_channel_totals.get(channel, 0.0)
        for channel in visible_channels
    }
    visible_media_total = sum(visible_channel_totals.values())
    visible_spend_totals, visible_cpl_map = compute_view_channel_metrics(
        st.session_state["df"],
        visible_channels,
        period_mask,
        visible_channel_totals,
    )
    show_baseline = st.checkbox(
        "Show baseline and unexplained portion",
        value=bool(st.session_state.get("show_baseline_visual", True)),
        help="Include baseline and the unexplained gap in the visual summaries.",
    )
    st.session_state["show_baseline_visual"] = show_baseline

    st.subheader("Model comparison")
    st.caption("Compare the fitted models first. Use this section to see whether the ranking and fit quality are broadly consistent across methods.")
    comparison_df = build_model_comparison_df()
    st.dataframe(comparison_df, width="stretch")
    st.caption("Model comparison table. Higher R² and lower RMSE, MAE, and MAPE are generally better.")

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
                channel: st.session_state["model_results"][name].cpl.get(channel)
                for channel in st.session_state["selected_visual_channels"]
            }
            for name in model_names
        }
    )
    st.dataframe(cpl_df, width="stretch")
    st.caption("CPL comparison table. Lower CPL means the channel is more efficient in that model. All reported fit and attribution are in-sample.")

    best_name, best_value = pick_best_channel(visible_cpl_map)
    fitted_at = st.session_state["model_results_meta"].get(selected_model, {}).get("fitted_at")

    st.subheader("What is happening?")
    st.caption("Use this section for the top-line picture. It compares total leads, the part linked to media, the part explained by baseline effects, and the remaining gap.")
    col1, col2, col3, col4 = st.columns(4)
    col1.metric(
        "Total leads",
        format_number(actual_total),
        help="All observed leads in the loaded dataset.",
    )
    col2.metric(
        "Media leads",
        format_number(visible_media_total),
        help="Displayed share of actual leads attributed to media after bounding the decomposition to total leads.",
    )
    col3.metric(
        "Baseline leads",
        format_number(baseline_total),
        help="Displayed share of actual leads attributed to baseline and control effects.",
    )
    col4.metric(
        "Unexplained gap",
        format_signed_number(unexplained_total),
        f"{unexplained_share:.1f}%",
        help="Remaining portion of actual leads that is not explained by the displayed media and baseline split.",
    )
    col5, col6 = st.columns(2)
    col5.metric(
        "Top channel by CPL",
        best_name or "N/A",
        format_cpl(best_value) if best_value is not None else None,
        help="The channel with the lowest cost per lead in the selected model.",
    )
    col6.metric(
        "Model fit",
        f"R² {result.r_squared:.2f}",
        f"RMSE {result.rmse:,.0f}",
        help="R² shows how much variation the model explains. RMSE shows the average prediction error in leads.",
    )
    summary_rows = [
        {"Group": "Total leads", "Value": actual_total, "Label": format_number(actual_total)},
        {"Group": "Media leads", "Value": visible_media_total, "Label": format_number(visible_media_total)},
        {"Group": "Baseline leads", "Value": baseline_total, "Label": format_number(baseline_total)},
    ]
    if show_baseline:
        summary_rows.append(
            {
                "Group": "Unexplained gap",
                "Value": abs(unexplained_total),
                "Label": format_number(abs(unexplained_total)),
            }
        )
    summary_df = pd.DataFrame(summary_rows)
    st.altair_chart(
        build_labeled_bar_chart(
            summary_df,
            "Group",
            "Value",
            "Label",
            "Lead comparison",
        )
    )
    if fitted_at:
        st.caption(f"Model fitted on: {fitted_at}")

    st.subheader("Why is it happening?")
    st.caption("Use this section to explain channel efficiency. Focus on CPL, contribution, and how much each channel accounts for in the selected model.")
    why_rows: list[dict[str, Any]] = []
    for channel in st.session_state["selected_visual_channels"]:
        contribution_total = float(visible_channel_totals.get(channel, 0.0))
        row = {
            "Channel": channel,
            "Coefficient": round(float(result.coefficients[channel]), 4),
            "CPL": format_cpl(visible_cpl_map[channel]),
            "Contribution": round(contribution_total, 2),
            "Share": round((contribution_total / actual_total) * 100, 2)
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

    cpl_chart = {
        channel: value
        for channel, value in visible_cpl_map.items()
        if not math.isinf(value)
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

    st.subheader("What should leadership do next?")
    st.caption("Use this as the action section. The recommendation is directional and based on current modelled efficiency, not a guaranteed forecast.")
    worst_name, worst_value = pick_worst_channel(visible_cpl_map)
    reallocation_pct = 0
    if best_value and worst_value and worst_value > 0:
        reallocation_pct = min(50, round((worst_value - best_value) / worst_value * 100))

    recommendation_lines = [
        f"- Invest more in {best_name or 'the best channel'} — currently {format_cpl(best_value)}",
        f"- Reduce spend on {worst_name or 'the weakest channel'} — {format_cpl(worst_value)}",
        f"- Reallocate {reallocation_pct}% from {worst_name or 'the weakest channel'} to {best_name or 'the strongest channel'} — directional heuristic based on current modeled CPL",
        "- This is a directional recommendation, not a forecast",
    ]
    st.markdown("\n".join(recommendation_lines))

    with st.expander("Channel Insights", expanded=False):
        st.caption("Use this section for deeper exploration. You can limit the view to selected channels and compare them against baseline over time.")
        insight_df = pd.DataFrame(
            {
                channel: result.contribution[channel][period_mask]
                for channel in st.session_state["selected_visual_channels"]
            }
        )
        if show_baseline:
            insight_df["baseline"] = result.baseline[period_mask]
            insight_df["unexplained_gap"] = np.clip(
                st.session_state["y"][period_mask] - result.y_pred[period_mask],
                a_min=0,
                a_max=None,
            )
        insight_df.insert(0, "date", date_series[period_mask].to_numpy())
        insight_long_df = insight_df.melt(
            id_vars=["date"],
            var_name="variable",
            value_name="leads",
        )
        insight_chart = (
            alt.Chart(insight_long_df)
            .mark_bar()
            .encode(
                x=alt.X("date:T", title="Date"),
                y=alt.Y("sum(leads):Q", title="Leads"),
                color=alt.Color("variable:N", title="Variable"),
                tooltip=[
                    alt.Tooltip("date:T", title="Date"),
                    alt.Tooltip("variable:N", title="Variable"),
                    alt.Tooltip("sum(leads):Q", title="Leads", format=",.2f"),
                ],
            )
            .properties(title="Stacked lead decomposition over time", height=320, width="container")
        )
        st.altair_chart(insight_chart)
        rows = []
        for channel in st.session_state["selected_visual_channels"]:
            theta = st.session_state["adstock_params"].get(channel, 0.0)
            if theta <= 0:
                carryover = "No carryover"
            elif theta >= 1.0:
                carryover = "Indefinite carryover"
            else:
                carryover = f"{round(-math.log(0.05) / -math.log(theta))} weeks"
            rows.append(
                {
                    "Channel": channel,
                    "Spend total": round(float(visible_spend_totals[channel]), 2),
                    "Contribution": round(float(visible_channel_totals[channel]), 2),
                    "CPL": format_cpl(visible_cpl_map[channel]),
                    "Adstock": st.session_state["adstock_type"].get(channel, "geometric"),
                    "Saturation": st.session_state["saturation_type"].get(channel, "log"),
                    "Carryover": carryover,
                }
            )
        st.dataframe(pd.DataFrame(rows), width="stretch")

    overview_export_df = pd.DataFrame(
        [
            {"Metric": "Model", "Value": selected_model},
            {"Metric": "Period", "Value": selected_period},
            {"Metric": "Total leads", "Value": round(actual_total, 2)},
            {"Metric": "Media leads", "Value": round(media_total, 2)},
            {"Metric": "Baseline leads", "Value": round(baseline_total, 2)},
            {"Metric": "Unexplained gap", "Value": round(unexplained_total, 2)},
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
            overview_export_df,
            channel_export_df,
            comparison_export_df,
        ),
        file_name="mmm_results_export.pdf",
        mime="application/pdf",
    )

    with st.expander("Quick Insights", expanded=False):
        st.caption("This section condenses the most useful summary points into a small set of operational metrics.")
        overall_cpl = (
            sum(visible_spend_totals.values()) / visible_media_total
            if visible_media_total > 0
            else None
        )
        quick_col1, quick_col2 = st.columns(2)
        quick_col1.metric(
            "Overall marketing CPL",
            format_cpl(overall_cpl),
            help="Total spend divided by total media-attributed leads.",
        )
        quick_col2.metric(
            "Best channel",
            best_name or "N/A",
            format_cpl(best_value) if best_value is not None else None,
            help="The channel with the lowest cost per lead in the selected model.",
        )
        quick_col3, quick_col4 = st.columns(2)
        quick_col3.metric(
            "Worst channel",
            worst_name or "N/A",
            format_cpl(worst_value) if worst_value is not None else None,
            help="The channel with the highest cost per lead in the selected model.",
        )
        quick_col4.metric(
            "Media vs baseline",
            f"{round((visible_media_total / actual_total) * 100, 1) if not math.isclose(actual_total, 0.0) else 0.0}%",
            f"Baseline {round((baseline_total / actual_total) * 100, 1) if not math.isclose(actual_total, 0.0) else 0.0}%",
            help="Share of actual leads assigned to media versus the baseline part of the displayed decomposition.",
        )


def render_ai_tab() -> None:
    if not st.session_state.get("model_results"):
        st.info("Fit at least one model first to enable AI analysis.")
        return

    selected_model = st.session_state.get("selected_model") or next(
        iter(st.session_state["model_results"].keys())
    )
    result = st.session_state["model_results"][selected_model]
    selected_period = st.session_state.get("results_period", "All data")
    selected_visual_channels = st.session_state.get("selected_visual_channels") or result.channel_names
    date_col = st.session_state["date_col"]
    date_series = st.session_state["df"][date_col]
    period_mask = build_period_mask(date_series, selected_period)
    actual_total = float(st.session_state["y"][period_mask].sum())
    display_channel_totals, baseline_total, unexplained_total = compute_display_attribution(
        result,
        actual_total,
        row_mask=period_mask,
    )
    visible_channel_totals = {
        channel: display_channel_totals.get(channel, 0.0)
        for channel in selected_visual_channels
    }
    media_total = sum(visible_channel_totals.values())
    _, visible_cpl_map = compute_view_channel_metrics(
        st.session_state["df"],
        list(selected_visual_channels),
        period_mask,
        visible_channel_totals,
    )
    best_name, best_value = pick_best_channel(visible_cpl_map)
    worst_name, worst_value = pick_worst_channel(visible_cpl_map)
    reallocation_pct = 0
    if best_value and worst_value and worst_value > 0:
        reallocation_pct = min(50, round((worst_value - best_value) / worst_value * 100))

    provider_options = ["openai", "anthropic"]
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
        index=provider_options.index(st.session_state.get("ai_provider", "openai")),
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
            st.error("Add credentials.json or set an API key in the sidebar to enable AI analysis.")
        else:
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
            st.session_state["ai_summary"] = summary
            st.session_state["ai_summary_meta"] = {
                "selected_model": selected_model,
                "results_period": selected_period,
                "selected_visual_channels": list(selected_visual_channels),
                "analysis_mode": analysis_mode,
                "include_all_models": include_all_models,
                "provider": provider,
                "generated_at": datetime.now().isoformat(timespec="seconds"),
            }

    if st.session_state.get("ai_summary"):
        ai_summary_meta = st.session_state.get("ai_summary_meta") or {}
        generated_for_model = ai_summary_meta.get("selected_model")
        generated_for_period = ai_summary_meta.get("results_period")
        generated_for_channels = ai_summary_meta.get("selected_visual_channels") or []
        current_channels_signature = list(selected_visual_channels)
        ai_is_stale = (
            generated_for_model not in {None, selected_model}
            or generated_for_period not in {None, selected_period}
            or generated_for_channels != current_channels_signature
        )
        if generated_for_model or generated_for_period:
            st.caption(
                f"Analysis generated for model `{generated_for_model or selected_model}` and period `{generated_for_period or selected_period}`."
            )
        if ai_is_stale:
            st.warning(
                "The current Results view has changed since this AI analysis was generated. Regenerate the analysis before exporting AI outputs or the complete overview."
            )
        st.markdown(st.session_state["ai_summary"])
        if not ai_is_stale:
            ai_export_df = pd.DataFrame(
                [
                    {
                        "generated_at": (ai_summary_meta.get("generated_at") or datetime.now().isoformat(timespec="seconds")),
                        "provider": ai_summary_meta.get("provider", provider),
                        "model": model,
                        "selected_model": generated_for_model or selected_model,
                        "results_period": generated_for_period or selected_period,
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
                    {"Metric": "Model", "Value": selected_model},
                    {"Metric": "Period", "Value": selected_period},
                    {"Metric": "Total leads", "Value": round(actual_total, 2)},
                    {"Metric": "Media leads", "Value": round(media_total, 2)},
                    {"Metric": "Baseline leads", "Value": round(baseline_total, 2)},
                    {"Metric": "Unexplained gap", "Value": round(unexplained_total, 2)},
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
            recommendation_lines = [
                f"Invest more in {best_name or 'the best channel'} currently {format_cpl(best_value)}",
                f"Reduce spend on {worst_name or 'the weakest channel'} {format_cpl(worst_value)}",
                f"Reallocate {reallocation_pct}% from {worst_name or 'the weakest channel'} to {best_name or 'the strongest channel'} as a directional heuristic",
                "This is a directional recommendation, not a forecast",
            ]
            complete_overview_df = build_complete_overview_export_df(
                selected_model=selected_model,
                selected_period=selected_period,
                overview_df=overview_export_df,
                comparison_df=comparison_export_df,
                channel_df=channel_export_df,
                recommendation_lines=recommendation_lines,
                ai_analysis=st.session_state.get("ai_summary"),
            )
            complete_overview_pdf = build_complete_overview_pdf_bytes(
                selected_model=selected_model,
                selected_period=selected_period,
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
    st.sidebar.header("MMM workflow")
    st.sidebar.text_input(
        "API key override",
        type="password",
        key="manual_ai_api_key",
        help="Optional manual API key entry used when credentials are not available from file or environment.",
    )
    selected_step = render_sidebar_step_menu()
    st.subheader(selected_step)
    st.caption(STEP_DESCRIPTIONS[selected_step])

    if selected_step == "Data":
        render_data_tab()
    elif selected_step == "Config":
        render_config_tab()
    elif selected_step == "Priors":
        render_priors_tab()
    elif selected_step == "Fit":
        render_fit_tab()
    elif selected_step == "Results":
        render_results_tab()
    elif selected_step == "AI":
        render_ai_tab()


if __name__ == "__main__":
    main()
