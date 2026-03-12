from __future__ import annotations

import hashlib
import json
import math
from datetime import datetime
from pathlib import Path
from typing import Any

import altair as alt
import numpy as np
import pandas as pd
import streamlit as st

from src.ai.client import build_payload, get_summary, load_credentials
from src.models.elasticnet import ElasticNetModel
from src.models.lasso import LassoModel
from src.models.ols import OLSModel
from src.models.pymc_model import PyMCModel
from src.models.ridge import RidgeModel
from src.transforms import transform_media
from src.utils import convert_mmm_data, validate_mmm_data


MODEL_BUILDERS = {
    "OLS": OLSModel,
    "Ridge": RidgeModel,
    "Lasso": LassoModel,
    "ElasticNet": ElasticNetModel,
    "PyMC": PyMCModel,
}


def init_state() -> None:
    defaults: dict[str, Any] = {
        "loaded_df": None,
        "loaded_source": None,
        "df": None,
        "valid": False,
        "date_col": None,
        "target_col": None,
        "channel_cols": [],
        "control_cols": [],
        "X_transformed": None,
        "y": None,
        "adstock_params": {},
        "adstock_type": {},
        "saturation_params": {},
        "saturation_type": {},
        "reg_alpha": 1.0,
        "l1_ratio": 0.5,
        "transforms_applied": False,
        "transform_fingerprint": None,
        "regularization_signature": None,
        "model_results": {},
        "model_results_meta": {},
        "selected_model": None,
        "ai_summary": None,
        "last_data_message": None,
        "pymc_prior_config": {
            "intercept_mu_mode": "data_mean",
            "intercept_mu": 0.0,
            "intercept_sigma_scale": 1.0,
            "channel_prior_family": "HalfNormal",
            "channel_sigma_scale": 1.0,
            "control_sigma_scale": 1.0,
            "noise_sigma_scale": 1.0,
        },
        "pymc_sampler_config": {
            "draws": 300,
            "tune": 200,
            "chains": 1,
        },
        "pymc_prior_signature": None,
        "selected_visual_channels": [],
        "show_baseline_visual": True,
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


def compute_transform_fingerprint(
    channel_cols: list[str],
    control_cols: list[str],
    adstock_type: dict[str, str],
    saturation_type: dict[str, str],
    adstock_params: dict[str, float],
    saturation_params: dict[str, dict[str, float]],
) -> str:
    payload = {
        "channels": channel_cols,
        "controls": control_cols,
        "adstock_type": adstock_type,
        "saturation_type": saturation_type,
        "adstock_params": adstock_params,
        "saturation_params": saturation_params,
    }
    encoded = json.dumps(payload, sort_keys=True).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def compute_signature(payload: dict[str, Any]) -> str:
    encoded = json.dumps(payload, sort_keys=True).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


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
    return (bars + labels).properties(title=title, height=max(180, 36 * len(df)))


def load_candidate_dataframe() -> pd.DataFrame | None:
    uploaded_file = st.file_uploader("Upload CSV", type=["csv"])

    local_files = sorted(Path("data").glob("*.csv"))
    selected_name = None
    if local_files:
        selected_name = st.selectbox(
            "Or pick a file from data/",
            options=[path.name for path in local_files],
            index=0,
        )
    else:
        st.info("No files in data/ yet — use the uploader above.")

    candidate_df = None
    source_name = None
    if uploaded_file is not None:
        uploaded_file.seek(0)
        candidate_df = pd.read_csv(uploaded_file)
        source_name = uploaded_file.name
    elif selected_name:
        selected_path = next(path for path in local_files if path.name == selected_name)
        candidate_df = pd.read_csv(selected_path)
        source_name = selected_path.name

    if candidate_df is not None:
        st.session_state["loaded_df"] = candidate_df
        st.session_state["loaded_source"] = source_name

    return st.session_state.get("loaded_df")


def default_channel_selection(columns: list[str], date_col: str | None, target_col: str | None) -> list[str]:
    blocked = {date_col, target_col}
    return [col for col in columns if col not in blocked and col.endswith("_spend")]


def render_data_tab() -> None:
    st.caption("Start here. Load a CSV, confirm the date, target, and spend columns, then validate the dataset before moving on.")
    raw_df = load_candidate_dataframe()
    if raw_df is None:
        return

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

    date_col = st.selectbox("Date column", options=columns, index=date_default)
    target_col = st.selectbox("Target column", options=columns, index=target_default)

    channel_candidates = [col for col in columns if col not in {date_col, target_col}]
    default_channels = current_channels or default_channel_selection(
        channel_candidates, date_col, target_col
    )
    channel_cols = st.multiselect(
        "Channels to include",
        options=channel_candidates,
        default=[col for col in default_channels if col in channel_candidates],
    )

    control_candidates = [col for col in channel_candidates if col not in channel_cols]
    control_cols = st.multiselect(
        "Control columns",
        options=control_candidates,
        default=[col for col in current_controls if col in control_candidates],
    )

    button_label = "Update selection" if st.session_state.get("valid") else "Load and validate"
    if st.button(button_label, type="primary"):
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


def render_config_tab() -> None:
    if not st.session_state.get("valid"):
        st.warning("Load and validate data in the Data tab first.")
        return

    st.caption("Set the media transforms here. A safe starting point is Geometric adstock plus Log saturation for every channel.")
    df = st.session_state["df"]
    channel_cols = st.session_state["channel_cols"]
    control_cols = st.session_state["control_cols"]

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
        )
        saturation_label = col2.selectbox(
            "Saturation",
            options=["Log", "Hill", "None"],
            index={"log": 0, "hill": 1, "none": 2}[current_saturation],
            key=f"saturation_type_{ch}",
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
            )
            k_value = sat_col2.number_input(
                f"K for {ch}",
                min_value=0.1,
                value=float(current_sat.get("k", default_k)),
                step=1.0,
                key=f"k_{ch}",
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
    )
    st.session_state["l1_ratio"] = st.number_input(
        "ElasticNet l1 ratio",
        min_value=0.0,
        max_value=1.0,
        value=float(st.session_state.get("l1_ratio", 0.5)),
        step=0.1,
    )

    if st.button("Apply transforms", type="primary"):
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
    current_prior = st.session_state["pymc_prior_config"]
    current_sampler = st.session_state["pymc_sampler_config"]

    with st.form("pymc_priors_form"):
        intercept_mode = st.selectbox(
            "Intercept mean",
            options=["Use data mean", "Set manually"],
            index=0 if current_prior.get("intercept_mu_mode", "data_mean") == "data_mean" else 1,
        )
        intercept_mu = float(current_prior.get("intercept_mu", 0.0))
        if intercept_mode == "Set manually":
            intercept_mu = st.number_input(
                "Manual intercept mean",
                value=intercept_mu,
                step=10.0,
            )

        channel_prior_family = st.selectbox(
            "Channel prior family",
            options=["HalfNormal", "Normal"],
            index=0 if current_prior.get("channel_prior_family", "HalfNormal") == "HalfNormal" else 1,
        )
        pri_col1, pri_col2 = st.columns(2)
        intercept_sigma_scale = pri_col1.number_input(
            "Intercept sigma scale",
            min_value=0.1,
            value=float(current_prior.get("intercept_sigma_scale", 1.0)),
            step=0.1,
        )
        channel_sigma_scale = pri_col2.number_input(
            "Channel sigma scale",
            min_value=0.1,
            value=float(current_prior.get("channel_sigma_scale", 1.0)),
            step=0.1,
        )

        pri_col3, pri_col4 = st.columns(2)
        control_sigma_scale = pri_col3.number_input(
            "Control sigma scale",
            min_value=0.1,
            value=float(current_prior.get("control_sigma_scale", 1.0)),
            step=0.1,
        )
        noise_sigma_scale = pri_col4.number_input(
            "Noise sigma scale",
            min_value=0.1,
            value=float(current_prior.get("noise_sigma_scale", 1.0)),
            step=0.1,
        )

        sampler_col1, sampler_col2, sampler_col3 = st.columns(3)
        draws = sampler_col1.number_input(
            "Draws",
            min_value=100,
            value=int(current_sampler.get("draws", 300)),
            step=100,
        )
        tune = sampler_col2.number_input(
            "Tune",
            min_value=100,
            value=int(current_sampler.get("tune", 200)),
            step=100,
        )
        chains = sampler_col3.number_input(
            "Chains",
            min_value=1,
            max_value=4,
            value=int(current_sampler.get("chains", 1)),
            step=1,
        )

        saved = st.form_submit_button("Save priors", type="primary")

    if saved:
        prior_config = {
            "intercept_mu_mode": "data_mean" if intercept_mode == "Use data mean" else "manual",
            "intercept_mu": float(intercept_mu),
            "intercept_sigma_scale": float(intercept_sigma_scale),
            "channel_prior_family": channel_prior_family,
            "channel_sigma_scale": float(channel_sigma_scale),
            "control_sigma_scale": float(control_sigma_scale),
            "noise_sigma_scale": float(noise_sigma_scale),
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
    available_models = list(MODEL_BUILDERS.keys())
    selected_models = st.multiselect(
        "Models to fit",
        options=available_models,
        default=["OLS"],
    )
    st.info("PyMC uses the Priors tab settings. Lasso and ElasticNet use the regularization settings from Config.")

    fit_selected = st.button("Fit selected", type="primary")
    fit_all = st.button("Fit all")

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
        row: dict[str, Any] = {
            "Model": name,
            "R²": round(float(result.r_squared), 3),
            "RMSE": round(float(result.rmse), 2),
            "MAE": round(float(np.mean(np.abs(y - result.y_pred))), 2),
        }
        if np.all(y != 0):
            row["MAPE"] = round(float(np.mean(np.abs((y - result.y_pred) / y)) * 100), 2)
        rows.append(row)
    return pd.DataFrame(rows)


def render_results_tab() -> None:
    if not st.session_state.get("model_results"):
        st.info("Fit at least one model in the Fit tab to see results.")
        return

    st.caption("Read the outputs in order. Start with the model comparison, then use the three sections below to answer what is happening, why, and what to do next.")

    model_names = list(st.session_state["model_results"].keys())
    current_model = st.session_state.get("selected_model") or model_names[0]
    selected_model = st.selectbox(
        "View model",
        options=model_names,
        index=model_names.index(current_model),
    )
    st.session_state["selected_model"] = selected_model
    result = st.session_state["model_results"][selected_model]
    actual_total = float(st.session_state["y"].sum())
    model_total = float(result.y_pred.sum())
    media_total = sum(float(series.sum()) for series in result.contribution.values())
    baseline_total = float(result.baseline.sum())
    unexplained_total = actual_total - model_total
    if math.isclose(unexplained_total, 0.0, abs_tol=0.5):
        unexplained_total = 0.0
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
    st.caption("All reported R², RMSE, and attribution are in-sample.")

    best_name, best_value = pick_best_channel(result.cpl)
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
        format_number(media_total),
        help="Leads attributed to the selected media channels by the model.",
    )
    col3.metric(
        "Baseline leads",
        format_number(baseline_total),
        help="Leads explained by the baseline part of the model, such as intercept and controls.",
    )
    col4.metric(
        "Unexplained gap",
        format_signed_number(unexplained_total),
        f"{unexplained_share:.1f}%",
        help="Difference between actual total leads and the modelled total. Smaller is better.",
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
        {"Group": "Media leads", "Value": media_total, "Label": format_number(media_total)},
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
        ),
        use_container_width=True,
    )
    if fitted_at:
        st.caption(f"Model fitted on: {fitted_at}")

    st.subheader("Why is it happening?")
    st.caption("Use this section to explain channel efficiency. Focus on CPL, contribution, and how much each channel accounts for in the selected model.")
    why_rows: list[dict[str, Any]] = []
    for channel in st.session_state["selected_visual_channels"]:
        contribution_total = float(result.contribution[channel].sum())
        row = {
            "Channel": channel,
            "Coefficient": round(float(result.coefficients[channel]), 4),
            "CPL": format_cpl(result.cpl[channel]),
            "Contribution": round(contribution_total, 2),
            "Share": round(float(result.contribution_pct[channel]) * 100, 2),
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
        for channel, value in result.cpl.items()
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
            ),
            use_container_width=True,
        )

    st.subheader("What should leadership do next?")
    st.caption("Use this as the action section. The recommendation is directional and based on current modelled efficiency, not a guaranteed forecast.")
    worst_name, worst_value = pick_worst_channel(result.cpl)
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
                channel: result.contribution[channel]
                for channel in st.session_state["selected_visual_channels"]
            }
        )
        if show_baseline:
            insight_df["baseline"] = result.baseline
            insight_df["unexplained_gap"] = np.clip(
                st.session_state["y"] - result.y_pred,
                a_min=0,
                a_max=None,
            )
        insight_df.index = st.session_state["df"][st.session_state["date_col"]]
        st.area_chart(insight_df)
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
                    "Spend total": round(float(st.session_state["df"][channel].sum()), 2),
                    "Contribution": round(float(result.contribution[channel].sum()), 2),
                    "CPL": format_cpl(result.cpl[channel]),
                    "Adstock": st.session_state["adstock_type"].get(channel, "geometric"),
                    "Saturation": st.session_state["saturation_type"].get(channel, "log"),
                    "Carryover": carryover,
                }
            )
        st.dataframe(pd.DataFrame(rows), width="stretch")

    with st.expander("Quick Insights", expanded=False):
        st.caption("This section condenses the most useful summary points into a small set of operational metrics.")
        media_total = sum(float(result.contribution[ch].sum()) for ch in result.channel_names)
        spend_total = float(
            st.session_state["df"][st.session_state["channel_cols"]].sum().sum()
        )
        overall_cpl = spend_total / media_total if media_total > 0 else None
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
            f"{round((media_total / float(result.y_pred.sum())) * 100, 1)}%",
            f"Baseline {round(result.baseline_pct * 100, 1)}%",
            help="Share of modelled leads attributed to media versus the baseline part of the model.",
        )


def render_ai_tab() -> None:
    if not st.session_state.get("model_results"):
        st.info("Fit at least one model first to enable AI analysis.")
        return

    selected_model = st.session_state.get("selected_model") or next(
        iter(st.session_state["model_results"].keys())
    )
    result = st.session_state["model_results"][selected_model]

    manual_key = st.sidebar.text_input("API key override", type="password")
    provider_options = ["openai", "anthropic"]
    default_provider = "openai"
    try:
        default_provider, _, _ = load_credentials()
    except ValueError:
        pass
    provider = st.radio(
        "Provider",
        options=provider_options,
        index=provider_options.index(default_provider),
        horizontal=True,
    )

    try:
        loaded_provider, api_key, model = load_credentials(
            manual_api_key=manual_key or None,
            manual_provider=provider,
        )
        provider = loaded_provider
        st.success(f"AI ready with {provider}")
    except ValueError as exc:
        api_key = None
        model = None
        st.warning(str(exc))

    st.caption("Turn the current model output into a short executive summary. This tab should support the story, not replace the Results tab.")
    if st.button("Generate summary", type="primary"):
        if not api_key or not model:
            st.error("Add credentials.json or set an API key in the sidebar to enable AI analysis.")
        else:
            payload = build_payload(result, st.session_state)
            summary = get_summary(payload, provider, api_key, model)
            st.session_state["ai_summary"] = summary

    if st.session_state.get("ai_summary"):
        st.markdown(st.session_state["ai_summary"])
    else:
        st.info("No summary generated yet.")


def main() -> None:
    st.set_page_config(page_title="MMM — Marketing Mix Modeling", layout="wide")
    st.title("Marketing Mix Modeling")
    st.caption("Load data -> configure transforms -> fit models -> view results")
    init_state()

    tab_data, tab_config, tab_priors, tab_fit, tab_results, tab_ai = st.tabs(
        ["Data", "Config", "Priors", "Fit", "Results", "AI"]
    )

    with tab_data:
        render_data_tab()

    with tab_config:
        render_config_tab()

    with tab_priors:
        render_priors_tab()

    with tab_fit:
        render_fit_tab()

    with tab_results:
        render_results_tab()

    with tab_ai:
        render_ai_tab()


if __name__ == "__main__":
    main()
