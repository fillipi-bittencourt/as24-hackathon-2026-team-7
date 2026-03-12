from __future__ import annotations

import hashlib
import json
from typing import Any

import streamlit as st


def init_state() -> None:
    defaults: dict[str, Any] = {
        "loaded_df": None,
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
            "draws": 300,
            "tune": 200,
            "chains": 1,
        },
        "pymc_prior_signature": None,
        "pymc_prior_reasoning": {},
        "selected_visual_channels": [],
        "show_baseline_visual": True,
        "results_period": "All data",
        "current_step": "Data",
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
