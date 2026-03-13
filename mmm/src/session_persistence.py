from __future__ import annotations

import json
import re
from datetime import datetime
from io import StringIO
from pathlib import Path
from typing import Any, Mapping

import numpy as np
import pandas as pd

from src.models.base import ModelResult


PERSISTED_SESSION_KEYS = [
    "loaded_df",
    "loaded_df_signature",
    "loaded_source",
    "column_rename_map",
    "df",
    "valid",
    "date_col",
    "target_col",
    "channel_cols",
    "control_cols",
    "X_transformed",
    "y",
    "adstock_params",
    "adstock_type",
    "saturation_params",
    "saturation_type",
    "reg_alpha",
    "l1_ratio",
    "transforms_applied",
    "transform_fingerprint",
    "regularization_signature",
    "model_results",
    "model_results_meta",
    "selected_model",
    "ai_summary",
    "ai_summary_meta",
    "ai_provider",
    "ai_setup_recommendations",
    "last_data_message",
    "pymc_prior_config",
    "pymc_sampler_config",
    "pymc_prior_signature",
    "pymc_prior_reasoning",
    "selected_visual_channels",
    "show_baseline_visual",
    "results_period",
    "current_step",
]

SESSION_SAVE_DIR = Path(__file__).resolve().parents[1] / "saved_states"


def list_saved_sessions() -> list[dict[str, str]]:
    SESSION_SAVE_DIR.mkdir(parents=True, exist_ok=True)
    sessions: list[dict[str, str]] = []
    for path in sorted(SESSION_SAVE_DIR.glob("*.json"), reverse=True):
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        metadata = payload.get("metadata", {})
        sessions.append(
            {
                "slug": path.stem,
                "display_name": str(metadata.get("display_name", path.stem)),
                "saved_at": str(metadata.get("saved_at", "")),
                "source": str(metadata.get("source", "")),
                "models": ", ".join(metadata.get("models", [])),
            }
        )
    sessions.sort(key=lambda item: item.get("saved_at", ""), reverse=True)
    return sessions


def save_session_state(session_state: Mapping[str, Any], requested_name: str | None = None) -> str:
    SESSION_SAVE_DIR.mkdir(parents=True, exist_ok=True)
    display_name = (requested_name or "").strip() or datetime.now().strftime("session_%Y%m%d_%H%M%S")
    slug = _slugify_name(display_name)
    if not slug:
        slug = datetime.now().strftime("session_%Y%m%d_%H%M%S")
    slug = _build_unique_slug(slug)

    persisted_state = {
        key: _serialize_value(session_state.get(key))
        for key in PERSISTED_SESSION_KEYS
    }
    payload = {
        "version": 1,
        "metadata": {
            "display_name": display_name,
            "saved_at": datetime.now().isoformat(timespec="seconds"),
            "source": session_state.get("loaded_source"),
            "models": list(session_state.get("model_results", {}).keys()),
            "selected_model": session_state.get("selected_model"),
        },
        "state": persisted_state,
    }
    (SESSION_SAVE_DIR / f"{slug}.json").write_text(
        json.dumps(payload, ensure_ascii=True, indent=2),
        encoding="utf-8",
    )
    return display_name


def load_session_state(slug: str) -> dict[str, Any]:
    target_path = SESSION_SAVE_DIR / f"{slug}.json"
    payload = json.loads(target_path.read_text(encoding="utf-8"))
    state_payload = payload.get("state", {})
    return {
        key: _deserialize_value(value)
        for key, value in state_payload.items()
    }


def has_persistable_state(session_state: Mapping[str, Any]) -> bool:
    return any(
        [
            session_state.get("loaded_df") is not None,
            session_state.get("df") is not None,
            bool(session_state.get("model_results")),
            bool(session_state.get("ai_summary")),
            bool(session_state.get("ai_setup_recommendations")),
            bool(session_state.get("transforms_applied")),
        ]
    )


def _serialize_value(value: Any) -> Any:
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    if isinstance(value, np.generic):
        return value.item()
    if isinstance(value, pd.DataFrame):
        return {
            "__type__": "dataframe",
            "value": value.to_json(orient="split", date_format="iso"),
        }
    if isinstance(value, pd.Series):
        return {
            "__type__": "series",
            "name": value.name,
            "value": value.to_json(orient="split", date_format="iso"),
        }
    if isinstance(value, np.ndarray):
        return {
            "__type__": "ndarray",
            "dtype": str(value.dtype),
            "value": value.tolist(),
        }
    if isinstance(value, ModelResult):
        return {
            "__type__": "model_result",
            "value": {
                "model_name": value.model_name,
                "channel_names": _serialize_value(value.channel_names),
                "coefficients": _serialize_value(value.coefficients),
                "intercept": _serialize_value(value.intercept),
                "cpl": _serialize_value(value.cpl),
                "contribution": _serialize_value(value.contribution),
                "contribution_pct": _serialize_value(value.contribution_pct),
                "y_pred": _serialize_value(value.y_pred),
                "baseline": _serialize_value(value.baseline),
                "baseline_pct": _serialize_value(value.baseline_pct),
                "r_squared": _serialize_value(value.r_squared),
                "rmse": _serialize_value(value.rmse),
                "coefficient_lower": _serialize_value(value.coefficient_lower),
                "coefficient_upper": _serialize_value(value.coefficient_upper),
                "cpl_lower": _serialize_value(value.cpl_lower),
                "cpl_upper": _serialize_value(value.cpl_upper),
            },
        }
    if isinstance(value, dict):
        return {str(key): _serialize_value(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_serialize_value(item) for item in value]
    raise TypeError(f"Unsupported session value type: {type(value)!r}")


def _deserialize_value(value: Any) -> Any:
    if isinstance(value, list):
        return [_deserialize_value(item) for item in value]
    if not isinstance(value, dict):
        return value

    type_name = value.get("__type__")
    if type_name == "dataframe":
        return pd.read_json(StringIO(value["value"]), orient="split")
    if type_name == "series":
        series = pd.read_json(StringIO(value["value"]), orient="split", typ="series")
        series.name = value.get("name")
        return series
    if type_name == "ndarray":
        return np.asarray(value["value"], dtype=np.dtype(value.get("dtype", "float64")))
    if type_name == "model_result":
        model_payload = value["value"]
        return ModelResult(
            model_name=str(model_payload["model_name"]),
            channel_names=list(_deserialize_value(model_payload["channel_names"])),
            coefficients=dict(_deserialize_value(model_payload["coefficients"])),
            intercept=float(_deserialize_value(model_payload["intercept"])),
            cpl=dict(_deserialize_value(model_payload["cpl"])),
            contribution=dict(_deserialize_value(model_payload["contribution"])),
            contribution_pct=dict(_deserialize_value(model_payload["contribution_pct"])),
            y_pred=np.asarray(_deserialize_value(model_payload["y_pred"]), dtype=np.float64),
            baseline=np.asarray(_deserialize_value(model_payload["baseline"]), dtype=np.float64),
            baseline_pct=float(_deserialize_value(model_payload["baseline_pct"])),
            r_squared=float(_deserialize_value(model_payload["r_squared"])),
            rmse=float(_deserialize_value(model_payload["rmse"])),
            coefficient_lower=_maybe_dict(_deserialize_value(model_payload["coefficient_lower"])),
            coefficient_upper=_maybe_dict(_deserialize_value(model_payload["coefficient_upper"])),
            cpl_lower=_maybe_dict(_deserialize_value(model_payload["cpl_lower"])),
            cpl_upper=_maybe_dict(_deserialize_value(model_payload["cpl_upper"])),
        )
    return {key: _deserialize_value(item) for key, item in value.items()}


def _maybe_dict(value: Any) -> dict[str, float] | None:
    if value is None:
        return None
    return dict(value)


def _slugify_name(value: str) -> str:
    cleaned = re.sub(r"[^A-Za-z0-9]+", "_", value.strip().lower()).strip("_")
    return cleaned[:80]


def _build_unique_slug(base_slug: str) -> str:
    candidate = base_slug
    counter = 2
    while (SESSION_SAVE_DIR / f"{candidate}.json").exists():
        suffix = f"_{counter}"
        candidate = f"{base_slug[: max(1, 80 - len(suffix))]}{suffix}"
        counter += 1
    return candidate
