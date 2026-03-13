from __future__ import annotations

import copy
import hashlib
import json
from typing import Any

import streamlit as st


STATE_DEFAULTS: dict[str, Any] = {
    "loaded_df": None,
    "loaded_df_signature": None,
    "loaded_source": None,
    "column_rename_map": {},
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
    "ai_summary_meta": None,
    "manual_ai_api_key": "",
    "ai_provider": "openai",
    "ai_setup_recommendations": None,
    "last_data_message": None,
    "session_notice": None,
    "pymc_prior_config": {
        "intercept_mu_mode": "data_mean",
        "intercept_mu": 0.0,
        "intercept_sigma_scale": 1.0,
        "channel_prior_family": "HalfNormal",
        "channel_sigma_scale": 1.0,
        "control_sigma_scale": 1.0,
        "noise_sigma_scale": 1.0,
        "channel_prior_overrides": {},
    },
    "pymc_sampler_config": {
        "draws": 500,
        "tune": 500,
        "chains": 4,
    },
    "pymc_prior_signature": None,
    "pymc_prior_reasoning": {},
    "selected_visual_channels": [],
    "show_baseline_visual": True,
    "results_period": "All data",
    "current_step": "Data",
}


def build_default_state() -> dict[str, Any]:
    return copy.deepcopy(STATE_DEFAULTS)


def init_state() -> None:
    defaults = build_default_state()
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


def replace_state(
    restored_state: dict[str, Any] | None = None,
    *,
    preserve_keys: set[str] | None = None,
) -> None:
    preserve_keys = preserve_keys or set()
    preserved_values = {
        key: st.session_state[key]
        for key in preserve_keys
        if key in st.session_state
    }

    for key in list(st.session_state.keys()):
        if key not in preserve_keys:
            del st.session_state[key]

    defaults = build_default_state()
    for key, value in defaults.items():
        st.session_state[key] = value

    if restored_state:
        for key, value in restored_state.items():
            if key in defaults and isinstance(defaults[key], dict) and isinstance(value, dict):
                st.session_state[key] = _deep_merge_dicts(defaults[key], value)
            else:
                st.session_state[key] = value

    for key, value in preserved_values.items():
        st.session_state[key] = value


def clear_ai_outputs() -> None:
    st.session_state["ai_summary"] = None
    st.session_state["ai_summary_meta"] = None


def clear_setup_guidance() -> None:
    st.session_state["ai_setup_recommendations"] = None
    st.session_state["pymc_prior_reasoning"] = {}


def clear_model_outputs(*, selected_model: str | None = None) -> None:
    st.session_state["model_results"] = {}
    st.session_state["model_results_meta"] = {}
    st.session_state["selected_model"] = selected_model
    clear_ai_outputs()


def clear_transformed_inputs(*, clear_models: bool = True) -> None:
    st.session_state["transforms_applied"] = False
    st.session_state["transform_fingerprint"] = None
    st.session_state["regularization_signature"] = None
    st.session_state["X_transformed"] = None
    st.session_state["y"] = None
    if clear_models:
        clear_model_outputs()


def remove_model_outputs(model_names: list[str]) -> bool:
    removed_any = False
    for model_name in model_names:
        if model_name in st.session_state["model_results"]:
            st.session_state["model_results"].pop(model_name, None)
            st.session_state["model_results_meta"].pop(model_name, None)
            removed_any = True

    if removed_any:
        if st.session_state.get("selected_model") not in st.session_state["model_results"]:
            st.session_state["selected_model"] = next(
                iter(st.session_state["model_results"].keys()),
                None,
            )
        clear_ai_outputs()

    return removed_any


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


def _deep_merge_dicts(default_value: dict[str, Any], restored_value: dict[str, Any]) -> dict[str, Any]:
    merged = copy.deepcopy(default_value)
    for key, value in restored_value.items():
        if key in merged and isinstance(merged[key], dict) and isinstance(value, dict):
            merged[key] = _deep_merge_dicts(merged[key], value)
        else:
            merged[key] = value
    return merged
