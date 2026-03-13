from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd
import streamlit as st

from src.ai.client import load_credentials
from src.app_state import (
    clear_transformed_inputs,
    compute_signature,
    remove_model_outputs,
)
from src.results_helpers import infer_grain


def _classify_coverage_tag(non_zero_pct: float) -> str:
    if non_zero_pct < 20.0:
        return "sparse"
    if non_zero_pct < 50.0:
        return "patchy"
    return "healthy"


def _unique_preserve_order(values: list[str]) -> list[str]:
    seen: set[str] = set()
    ordered: list[str] = []
    for value in values:
        if value in seen:
            continue
        seen.add(value)
        ordered.append(value)
    return ordered


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
    non_zero_pct = round(float(numeric.ne(0).fillna(False).mean() * 100), 2)
    profile = {
        "missing_pct": round(float(numeric.isna().mean() * 100), 2),
        "zero_pct": round(float(numeric.eq(0).fillna(False).mean() * 100), 2),
        "non_zero_pct": non_zero_pct,
        "coverage_tag": _classify_coverage_tag(non_zero_pct),
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
    candidate_columns = [col for col in df.columns if col not in {date_col, target_col}]

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
        "candidate_columns": {
            column: _profile_column(df[column], target_series)
            for column in candidate_columns
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


def _sanitize_channel_prior_family(value: Any) -> str:
    normalized = str(value).strip()
    if normalized == "HalfNormal":
        return "HalfNormal"
    return "HalfNormal"


def _resolve_hybrid_column_selection(
    *,
    raw_df: pd.DataFrame,
    date_col: str,
    target_col: str,
    current_channels: list[str],
    current_controls: list[str],
    suggested_channels: list[str],
    suggested_controls: list[str],
) -> dict[str, Any]:
    available_columns = list(raw_df.columns)
    blocked = {date_col, target_col}
    target_series = pd.to_numeric(raw_df[target_col], errors="coerce") if target_col in raw_df.columns else None
    candidate_profiles = {
        column: _profile_column(raw_df[column], target_series)
        for column in available_columns
        if column not in blocked
    }

    inferred_channel_candidates = [
        column
        for column in available_columns
        if column not in blocked and (column in current_channels or column.endswith("_spend") or column.endswith("_cost"))
    ]
    channel_universe = _unique_preserve_order(
        [
            *[column for column in inferred_channel_candidates if column in candidate_profiles],
            *[column for column in current_channels if column in candidate_profiles],
            *[column for column in suggested_channels if column in candidate_profiles],
        ]
    )
    control_universe = _unique_preserve_order(
        [
            *[
                column
                for column in current_controls
                if column in candidate_profiles and column not in channel_universe
            ],
            *[
                column
                for column in suggested_controls
                if column in candidate_profiles and column not in channel_universe
            ],
        ]
    )

    force_kept_channels = [
        column
        for column in channel_universe
        if candidate_profiles[column]["coverage_tag"] in {"patchy", "healthy"}
    ]
    force_kept_controls = [
        column
        for column in control_universe
        if candidate_profiles[column]["coverage_tag"] in {"patchy", "healthy"}
    ]
    sparse_excluded_channels = [
        column
        for column in _unique_preserve_order([*channel_universe, *suggested_channels, *current_channels])
        if column in candidate_profiles and candidate_profiles[column]["coverage_tag"] == "sparse"
    ]
    sparse_excluded_controls = [
        column
        for column in _unique_preserve_order([*control_universe, *suggested_controls, *current_controls])
        if column in candidate_profiles and candidate_profiles[column]["coverage_tag"] == "sparse"
    ]

    ai_ranked_channels = [
        column
        for column in suggested_channels
        if column in candidate_profiles and candidate_profiles[column]["coverage_tag"] != "sparse"
    ]
    ai_ranked_controls = [
        column
        for column in suggested_controls
        if column in candidate_profiles and candidate_profiles[column]["coverage_tag"] != "sparse"
    ]

    applied_channels = _unique_preserve_order([*ai_ranked_channels, *force_kept_channels])
    applied_controls = _unique_preserve_order(
        [
            column
            for column in [*ai_ranked_controls, *force_kept_controls]
            if column not in blocked and column not in applied_channels
        ]
    )

    return {
        "candidate_profiles": candidate_profiles,
        "channel_universe": channel_universe,
        "control_universe": control_universe,
        "ai_ranked_channels": ai_ranked_channels,
        "ai_ranked_controls": ai_ranked_controls,
        "force_kept_channels": force_kept_channels,
        "force_kept_controls": force_kept_controls,
        "sparse_excluded_channels": sparse_excluded_channels,
        "sparse_excluded_controls": sparse_excluded_controls,
        "applied_channels": applied_channels,
        "applied_controls": applied_controls,
    }


def apply_ai_column_recommendations(selection_recommendations: dict[str, Any]) -> tuple[bool, list[str]]:
    raw_df = st.session_state["loaded_df"]
    if raw_df is None or not selection_recommendations:
        return False, []

    available_columns = list(raw_df.columns)
    date_col = str(selection_recommendations.get("date_column", st.session_state.get("date_col") or "")).strip()
    target_col = str(selection_recommendations.get("target_column", st.session_state.get("target_col") or "")).strip()
    suggested_channels = [
        col for col in selection_recommendations.get("channels", []) if col in available_columns
    ]
    suggested_controls = [
        col for col in selection_recommendations.get("controls", []) if col in available_columns
    ]

    if date_col not in available_columns:
        date_col = st.session_state.get("date_col") or ""
    if target_col not in available_columns:
        target_col = st.session_state.get("target_col") or ""

    current_channels = [
        col for col in st.session_state.get("channel_cols", []) if col in available_columns
    ]
    current_controls = [
        col for col in st.session_state.get("control_cols", []) if col in available_columns
    ]
    selection_summary = _resolve_hybrid_column_selection(
        raw_df=pd.DataFrame(raw_df).copy(),
        date_col=date_col,
        target_col=target_col,
        current_channels=current_channels,
        current_controls=current_controls,
        suggested_channels=suggested_channels,
        suggested_controls=suggested_controls,
    )
    channel_cols = selection_summary["applied_channels"]
    control_cols = selection_summary["applied_controls"]
    if not channel_cols:
        return False, ["No non-sparse channel columns were available after applying the coverage rule."]

    converted = pd.DataFrame(raw_df).copy()
    from src.utils import convert_mmm_data, validate_mmm_data

    converted, _ = convert_mmm_data(
        converted,
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
    if not ok:
        return False, errors

    prepared = converted.sort_values(date_col).reset_index(drop=True)
    st.session_state["df"] = prepared
    st.session_state["date_col"] = date_col
    st.session_state["target_col"] = target_col
    st.session_state["channel_cols"] = channel_cols
    st.session_state["control_cols"] = control_cols
    st.session_state["valid"] = True
    setup_recommendations = st.session_state.get("ai_setup_recommendations") or {}
    setup_recommendations["applied_selection_summary"] = {
        "ai_ranked_channels": selection_summary["ai_ranked_channels"],
        "ai_ranked_controls": selection_summary["ai_ranked_controls"],
        "force_kept_channels": [
            column
            for column in selection_summary["force_kept_channels"]
            if column not in selection_summary["ai_ranked_channels"]
        ],
        "force_kept_controls": [
            column
            for column in selection_summary["force_kept_controls"]
            if column not in selection_summary["ai_ranked_controls"]
        ],
        "sparse_excluded_channels": selection_summary["sparse_excluded_channels"],
        "sparse_excluded_controls": selection_summary["sparse_excluded_controls"],
        "coverage_tags": {
            column: selection_summary["candidate_profiles"][column]["coverage_tag"]
            for column in selection_summary["candidate_profiles"]
        },
    }
    reasoning = setup_recommendations.setdefault("column_selection_reasoning", {})
    reasoning_channels = reasoning.setdefault("channels", {})
    reasoning_controls = reasoning.setdefault("controls", {})
    coverage_tags = setup_recommendations["applied_selection_summary"]["coverage_tags"]
    for channel in channel_cols:
        notes = []
        if channel in selection_summary["ai_ranked_channels"] and channel in selection_summary["force_kept_channels"]:
            notes.append("Kept by both the AI recommendation and the coverage rule.")
        elif channel in selection_summary["ai_ranked_channels"]:
            notes.append("Included in the AI recommendation.")
        elif channel in selection_summary["force_kept_channels"]:
            notes.append("Retained automatically because its coverage tag is patchy or healthy.")
        notes.append(f"Coverage tag: {coverage_tags.get(channel, 'unknown')}.")
        base_reason = str(reasoning_channels.get(channel, "")).strip()
        reasoning_channels[channel] = " ".join(part for part in [base_reason, *notes] if part).strip()
    for control in control_cols:
        notes = []
        if control in selection_summary["ai_ranked_controls"] and control in selection_summary["force_kept_controls"]:
            notes.append("Kept by both the AI recommendation and the coverage rule.")
        elif control in selection_summary["ai_ranked_controls"]:
            notes.append("Included in the AI recommendation.")
        elif control in selection_summary["force_kept_controls"]:
            notes.append("Retained automatically because its coverage tag is patchy or healthy.")
        notes.append(f"Coverage tag: {coverage_tags.get(control, 'unknown')}.")
        base_reason = str(reasoning_controls.get(control, "")).strip()
        reasoning_controls[control] = " ".join(part for part in [base_reason, *notes] if part).strip()
    st.session_state["ai_setup_recommendations"] = setup_recommendations
    clear_transformed_inputs()
    return True, warnings


def apply_ai_prior_recommendations(prior_recommendations: dict[str, Any]) -> None:
    if not prior_recommendations:
        return

    channel_family = _sanitize_channel_prior_family(
        prior_recommendations.get("channel_prior_family", "HalfNormal")
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
        family = _sanitize_channel_prior_family(suggestion.get("family", channel_family))
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

    if old_signature and old_signature != new_signature:
        remove_model_outputs(["PyMC"])


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
    clear_transformed_inputs()
