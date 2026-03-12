from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd
import streamlit as st

from src.ai.client import load_credentials
from src.app_state import compute_signature
from src.results_helpers import infer_grain


def resolve_ai_credentials() -> tuple[str | None, str | None, str | None, str | None]:
    try:
        provider, api_key, model = load_credentials(
            manual_api_key=st.session_state.get("manual_ai_api_key") or None,
            manual_provider=st.session_state.get("ai_provider", "openai"),
        )
        return provider, api_key, model, None
    except ValueError as exc:
        return None, None, None, str(exc)


def _safe_corr(x: pd.Series, y: pd.Series) -> float | None:
    if x.nunique(dropna=True) < 2 or y.nunique(dropna=True) < 2:
        return None
    correlation = x.corr(y)
    if pd.isna(correlation):
        return None
    return float(correlation)


def _profile_column(series: pd.Series, target_series: pd.Series | None = None) -> dict[str, Any]:
    numeric = pd.to_numeric(series, errors="coerce")
    correlation = _safe_corr(numeric, target_series) if target_series is not None else None
    profile = {
        "missing_pct": round(float(numeric.isna().mean() * 100), 2),
        "zero_pct": round(float(numeric.eq(0).fillna(False).mean() * 100), 2),
        "negative_pct": round(float((numeric < 0).fillna(False).mean() * 100), 2),
        "mean": round(float(numeric.mean()), 2) if numeric.notna().any() else None,
        "median": round(float(numeric.median()), 2) if numeric.notna().any() else None,
        "std": round(float(numeric.std(ddof=0)), 2) if numeric.notna().any() else None,
        "min": round(float(numeric.min()), 2) if numeric.notna().any() else None,
        "max": round(float(numeric.max()), 2) if numeric.notna().any() else None,
    }
    if target_series is not None:
        profile["corr_to_target"] = round(correlation, 3) if correlation is not None else None
    return profile


def build_setup_assistant_payload() -> dict[str, Any]:
    df = st.session_state["df"]
    date_col = st.session_state["date_col"]
    target_col = st.session_state["target_col"]
    channel_cols = st.session_state["channel_cols"]
    control_cols = st.session_state["control_cols"]
    target_series = pd.to_numeric(df[target_col], errors="coerce")

    return {
        "date_range": f"{df[date_col].min().date()} to {df[date_col].max().date()}",
        "grain": infer_grain(df[date_col]) or "unknown",
        "row_count": int(len(df)),
        "date_column": date_col,
        "target_column": target_col,
        "channel_columns": channel_cols,
        "control_columns": control_cols,
        "target_profile": _profile_column(target_series),
        "channels": {
            channel: _profile_column(df[channel], target_series)
            for channel in channel_cols
        },
        "controls": {
            control: _profile_column(df[control], target_series)
            for control in control_cols
        },
    }


def _sanitize_choice(value: Any, allowed: set[str], default: str) -> str:
    normalized = str(value).strip()
    return normalized if normalized in allowed else default


def _sanitize_positive_float(value: Any, default: float, minimum: float = 0.1) -> float:
    try:
        parsed = float(value)
    except (TypeError, ValueError):
        return default
    return max(minimum, parsed)


def apply_ai_prior_recommendations(prior_recommendations: dict[str, Any]) -> None:
    if not prior_recommendations:
        return

    channel_family = _sanitize_choice(
        prior_recommendations.get("channel_prior_family", "HalfNormal"),
        {"HalfNormal", "Normal"},
        "HalfNormal",
    )
    channel_sigma_scale = _sanitize_positive_float(
        prior_recommendations.get("channel_sigma_scale", 1.0),
        1.0,
    )
    channel_overrides_input = prior_recommendations.get("channel_recommendations", {})
    channel_prior_overrides: dict[str, dict[str, Any]] = {}
    channel_reasoning: dict[str, str] = {}
    for channel in st.session_state.get("channel_cols", []):
        suggestion = channel_overrides_input.get(channel, {})
        family = _sanitize_choice(
            suggestion.get("family", channel_family),
            {"HalfNormal", "Normal"},
            channel_family,
        )
        sigma_scale = _sanitize_positive_float(
            suggestion.get("sigma_scale", channel_sigma_scale),
            channel_sigma_scale,
        )
        channel_prior_overrides[channel] = {
            "family": family,
            "sigma_scale": sigma_scale,
        }
        channel_reasoning[channel] = str(suggestion.get("reasoning", "")).strip()

    prior_config = {
        "intercept_mu_mode": _sanitize_choice(
            prior_recommendations.get("intercept_mu_mode", "data_mean"),
            {"data_mean", "manual"},
            "data_mean",
        ),
        "intercept_mu": float(prior_recommendations.get("intercept_mu", 0.0) or 0.0),
        "intercept_sigma_scale": _sanitize_positive_float(
            prior_recommendations.get("intercept_sigma_scale", 1.0),
            1.0,
        ),
        "channel_prior_family": channel_family,
        "channel_sigma_scale": channel_sigma_scale,
        "control_sigma_scale": _sanitize_positive_float(
            prior_recommendations.get("control_sigma_scale", 1.0),
            1.0,
        ),
        "noise_sigma_scale": _sanitize_positive_float(
            prior_recommendations.get("noise_sigma_scale", 1.0),
            1.0,
        ),
        "channel_prior_overrides": channel_prior_overrides,
    }

    old_signature = st.session_state.get("pymc_prior_signature")
    sampler_config = st.session_state["pymc_sampler_config"]
    new_signature = compute_signature(
        {"prior_config": prior_config, "sampler_config": sampler_config}
    )
    st.session_state["pymc_prior_config"] = prior_config
    st.session_state["pymc_prior_signature"] = new_signature
    st.session_state["pymc_prior_reasoning"] = channel_reasoning

    if old_signature and old_signature != new_signature and "PyMC" in st.session_state["model_results"]:
        st.session_state["model_results"].pop("PyMC", None)
        st.session_state["model_results_meta"].pop("PyMC", None)
        if st.session_state.get("selected_model") == "PyMC":
            st.session_state["selected_model"] = next(
                iter(st.session_state["model_results"].keys()),
                None,
            )
        st.session_state["ai_summary"] = None


def apply_ai_transform_recommendations() -> None:
    recommendations = st.session_state.get("ai_setup_recommendations") or {}
    transform_recommendations = recommendations.get("transform_recommendations", {})
    regularization = recommendations.get("regularization_suggestion", {})
    df = st.session_state["df"]

    adstock_type: dict[str, str] = {}
    saturation_type: dict[str, str] = {}
    adstock_params: dict[str, float] = {}
    saturation_params: dict[str, dict[str, float]] = {}

    for channel in st.session_state.get("channel_cols", []):
        suggestion = transform_recommendations.get(channel, {})
        adstock = _sanitize_choice(
            suggestion.get("adstock_type", "geometric"),
            {"geometric", "none"},
            "geometric",
        )
        saturation = _sanitize_choice(
            suggestion.get("saturation_type", "log"),
            {"log", "hill", "none"},
            "log",
        )
        theta = min(
            0.9,
            max(
                0.1,
                float(
                    suggestion.get(
                        "theta",
                        st.session_state["adstock_params"].get(channel, 0.3),
                    )
                    or 0.3
                ),
            ),
        )
        adstock_type[channel] = adstock
        saturation_type[channel] = saturation
        adstock_params[channel] = theta if adstock == "geometric" else 0.0

        if saturation == "hill":
            default_k = max(float(df[channel].median()), float(df[channel].max()) * 0.1, 1.0)
            alpha = min(
                5.0,
                max(0.1, float(suggestion.get("alpha", 1.0) or 1.0)),
            )
            k_value = max(0.1, float(suggestion.get("k", default_k) or default_k))
            saturation_params[channel] = {"alpha": alpha, "k": k_value}
        else:
            saturation_params[channel] = {"alpha": 1.0, "k": 0.0}

        st.session_state[f"adstock_type_{channel}"] = "Geometric" if adstock == "geometric" else "None"
        st.session_state[f"saturation_type_{channel}"] = {
            "log": "Log",
            "hill": "Hill",
            "none": "None",
        }[saturation]
        st.session_state[f"theta_{channel}"] = adstock_params[channel] or 0.3
        if saturation == "hill":
            st.session_state[f"alpha_{channel}"] = saturation_params[channel]["alpha"]
            st.session_state[f"k_{channel}"] = saturation_params[channel]["k"]

    st.session_state["adstock_type"] = adstock_type
    st.session_state["saturation_type"] = saturation_type
    st.session_state["adstock_params"] = adstock_params
    st.session_state["saturation_params"] = saturation_params
    st.session_state["reg_alpha"] = max(
        0.0,
        float(regularization.get("reg_alpha", st.session_state.get("reg_alpha", 1.0)) or 1.0),
    )
    st.session_state["l1_ratio"] = min(
        1.0,
        max(
            0.0,
            float(regularization.get("l1_ratio", st.session_state.get("l1_ratio", 0.5)) or 0.5),
        ),
    )
    st.session_state["transforms_applied"] = False
    st.session_state["transform_fingerprint"] = None
    st.session_state["X_transformed"] = None
    st.session_state["y"] = None
    st.session_state["model_results"] = {}
    st.session_state["model_results_meta"] = {}
    st.session_state["selected_model"] = None
    st.session_state["ai_summary"] = None
