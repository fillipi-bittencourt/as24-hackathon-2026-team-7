from __future__ import annotations

import json
import os
from pathlib import Path
import re
from typing import Any

import numpy as np
import pandas as pd

from src.results_helpers import (
    build_period_mask,
    compute_display_attribution,
    compute_view_channel_metrics,
    is_rankable_cpl,
)


def load_credentials(
    manual_api_key: str | None = None,
    manual_provider: str | None = None,
    manual_model: str | None = None,
) -> tuple[str, str, str]:
    if manual_api_key:
        provider = manual_provider or "openai"
        model = manual_model or ("gpt-4o" if provider == "openai" else "claude-3-5-sonnet-20241022")
        return provider, manual_api_key, model

    root_path = Path(__file__).resolve().parents[2]
    selected_provider = (manual_provider or "").strip().lower() or None
    dotenv_values = _load_dotenv(root_path / ".env")
    credentials_path = root_path / "credentials.json"
    credentials_error: str | None = None
    credentials_payload: dict[str, Any] | None = None

    if credentials_path.exists():
        try:
            credentials_payload = json.loads(credentials_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            credentials_error = "credentials.json is not valid JSON."
        except OSError:
            credentials_error = "credentials.json could not be read."

    selected_source = _resolve_provider_from_sources(
        provider=selected_provider,
        manual_model=manual_model,
        dotenv_values=dotenv_values,
        credentials_payload=credentials_payload,
    )
    if selected_source is not None:
        return selected_source
    if selected_provider is not None:
        if credentials_error:
            raise ValueError(
                f"{credentials_error} Add a valid .env or credentials.json file, or set an API key in the sidebar."
            )
        raise ValueError(
            f"No credentials are configured for the selected provider `{selected_provider}`. Configure that provider or choose a different one."
        )

    default_source = _resolve_default_provider(
        manual_model=manual_model,
        dotenv_values=dotenv_values,
        credentials_payload=credentials_payload,
    )
    if default_source is not None:
        return default_source

    if os.getenv("OPENAI_API_KEY"):
        return "openai", os.environ["OPENAI_API_KEY"], os.getenv("OPENAI_MODEL", "gpt-4o")
    if os.getenv("ANTHROPIC_API_KEY"):
        return (
            "anthropic",
            os.environ["ANTHROPIC_API_KEY"],
            os.getenv("ANTHROPIC_MODEL", "claude-3-5-sonnet-20241022"),
        )

    if credentials_error:
        raise ValueError(
            f"{credentials_error} Add a valid .env or credentials.json file, or set an API key in the sidebar."
        )
    raise ValueError("Add a valid .env or credentials.json file, or set an API key in the sidebar to enable AI analysis.")


def build_payload(
    model_result: Any,
    session_state: dict[str, Any],
    include_comparison: bool = True,
) -> dict[str, Any]:
    df = session_state["df"]
    date_col = session_state["date_col"]
    target_col = session_state["target_col"]
    control_cols = session_state.get("control_cols", [])
    model_results = session_state.get("model_results", {})
    model_results_meta = session_state.get("model_results_meta", {})
    y = session_state.get("y")
    selected_channels = session_state.get("selected_visual_channels") or model_result.channel_names
    selected_period = session_state.get("results_period", "All data")
    adstock_type = session_state.get("adstock_type", {})
    sampler_config = session_state.get("pymc_sampler_config", {})
    date_series = pd.to_datetime(df[date_col])
    period_mask = build_period_mask(date_series, selected_period)
    selected_rows = int(np.sum(period_mask))
    actual_total = float(y[period_mask].sum()) if y is not None else 0.0
    channel_totals, baseline_total, residual_total = compute_display_attribution(
        model_result,
        y,
        row_mask=period_mask,
    )
    spend_totals, view_cpl_map = compute_view_channel_metrics(
        df,
        list(selected_channels),
        period_mask,
        channel_totals,
    )

    channels: list[dict[str, Any]] = []
    for ch in selected_channels:
        contribution_total = float(channel_totals.get(ch, 0.0))
        contribution_share = (contribution_total / actual_total) * 100 if not np.isclose(actual_total, 0.0) else None
        channels.append(
            {
                "name": ch,
                "coefficient": _clean_number(model_result.coefficients.get(ch)),
                "cpl": _clean_number(view_cpl_map.get(ch)) if is_rankable_cpl(view_cpl_map.get(ch)) else None,
                "contribution_pct": _clean_number(contribution_share),
                "contribution_total": _clean_number(contribution_total),
                "contribution_share_of_actual_pct": _clean_number(contribution_share),
                "spend_total": _clean_number(spend_totals.get(ch)),
            }
        )
    hidden_media_total = sum(
        float(value)
        for channel, value in channel_totals.items()
        if channel not in selected_channels
    )

    predicted_total = float(np.sum(model_result.y_pred[period_mask]))
    holdout_meta = model_results_meta.get(model_result.model_name, {}).get("holdout")
    bayesian_meta = model_results_meta.get(model_result.model_name, {}).get("bayesian_diagnostics")
    methodology_notes = [
        "Contribution, baseline, and residual totals reflect a bounded business-facing decomposition. Negative raw components are clipped at zero and scaled back to actual leads for interpretability."
    ]
    if selected_period != "All data" and any(
        adstock_type.get(channel, "geometric") == "geometric"
        for channel in selected_channels
    ):
        methodology_notes.append(
            "Selected-period CPL is directional because adstock can carry prior-period spend into the current window while spend totals are counted only inside the selected period."
        )
    if hidden_media_total > 0:
        methodology_notes.append(
            "The current channel filter hides some modeled media contribution. Hidden media is tracked separately and is not folded into the residual gap."
        )
    if model_result.model_name == "PyMC":
        methodology_notes.append(
            "PyMC uncertainty intervals should be trusted more when multiple chains mix well. Treat single-chain output as directional rather than fully validated uncertainty."
        )

    mape_non_zero = None
    if y is not None:
        non_zero_mask = (y != 0) & period_mask
        if np.any(non_zero_mask):
            mape_non_zero = float(
                np.mean(np.abs((y[non_zero_mask] - model_result.y_pred[non_zero_mask]) / y[non_zero_mask])) * 100
            )

    payload: dict[str, Any] = {
        "model_name": model_result.model_name,
        "date_range": f"{date_series[period_mask].min().date()} to {date_series[period_mask].max().date()}",
        "target_metric": "leads",
        "n_weeks": int(np.sum(period_mask)),
        "row_count_total": int(len(df)),
        "row_count_selected_period": selected_rows,
        "channel_count": int(len(selected_channels)),
        "control_count": int(len(control_cols)),
        "view_context": {
            "selected_period": selected_period,
            "selected_channels": list(selected_channels),
        },
        "model_fit": {
            "r_squared": _clean_number(model_result.r_squared),
            "rmse": _clean_number(model_result.rmse),
            "mae": _clean_number(float(np.mean(np.abs(y[period_mask] - model_result.y_pred[period_mask]))))
            if y is not None
            else None,
            "mape_non_zero": _clean_number(mape_non_zero),
        },
        "actual_total_leads": _clean_number(actual_total),
        "predicted_total_leads": _clean_number(predicted_total),
        "baseline_contribution_total_leads": _clean_number(baseline_total),
        "residual_gap_total_leads": _clean_number(residual_total),
        "baseline_share_of_actual_pct": _clean_number(
            (baseline_total / actual_total) * 100 if not np.isclose(actual_total, 0.0) else 0.0
        ),
        "residual_gap_share_of_actual_pct": _clean_number(
            (residual_total / actual_total) * 100 if not np.isclose(actual_total, 0.0) else 0.0
        ),
        "hidden_media_total_leads": _clean_number(hidden_media_total),
        "channels": channels,
        "controls": [{"name": col} for col in control_cols],
        "baseline_pct": _clean_number((baseline_total / actual_total) * 100 if not np.isclose(actual_total, 0.0) else 0.0),
        "top_channel": _pick_channel_name(view_cpl_map, best=True),
        "bottom_channel": _pick_channel_name(view_cpl_map, best=False),
        "methodology_notes": methodology_notes,
    }
    if holdout_meta is not None:
        payload["holdout_validation"] = {
            "train_rows": int(holdout_meta.get("train_rows", 0)),
            "holdout_rows": int(holdout_meta.get("holdout_rows", 0)),
            "r_squared": _clean_number(holdout_meta.get("holdout_r_squared")),
            "rmse": _clean_number(holdout_meta.get("holdout_rmse")),
            "mae": _clean_number(holdout_meta.get("holdout_mae")),
            "mape_non_zero": _clean_number(holdout_meta.get("holdout_mape")),
            "mape_non_zero_coverage": holdout_meta.get("holdout_coverage"),
        }
    if model_result.model_name == "PyMC":
        payload["bayesian_diagnostics"] = {
            "draws": int(sampler_config.get("draws", 0)),
            "tune": int(sampler_config.get("tune", 0)),
            "chains": int(sampler_config.get("chains", 0)),
            "has_interval_outputs": bool(model_result.coefficient_lower is not None),
            "status": bayesian_meta.get("status") if isinstance(bayesian_meta, dict) else None,
            "divergences": bayesian_meta.get("divergences") if isinstance(bayesian_meta, dict) else None,
            "max_tree_depth_hits": (
                bayesian_meta.get("max_tree_depth_hits")
                if isinstance(bayesian_meta, dict)
                else None
            ),
            "max_rhat": bayesian_meta.get("max_rhat") if isinstance(bayesian_meta, dict) else None,
            "min_ess_bulk": (
                bayesian_meta.get("min_ess_bulk")
                if isinstance(bayesian_meta, dict)
                else None
            ),
            "min_ess_tail": (
                bayesian_meta.get("min_ess_tail")
                if isinstance(bayesian_meta, dict)
                else None
            ),
        }

    if include_comparison and len(model_results) > 1:
        comparison_table: list[dict[str, Any]] = []
        for name, result in model_results.items():
            rmse = float(result.rmse)
            comparison_holdout = model_results_meta.get(name, {}).get("holdout")
            comparison_table.append(
                {
                    "model_name": name,
                    "r_squared": _clean_number(result.r_squared),
                    "rmse": _clean_number(rmse),
                    "is_selected_model": bool(name == model_result.model_name),
                    "holdout_r_squared": _clean_number(
                        comparison_holdout.get("holdout_r_squared")
                        if comparison_holdout is not None
                        else None
                    ),
                    "holdout_rmse": _clean_number(
                        comparison_holdout.get("holdout_rmse")
                        if comparison_holdout is not None
                        else None
                    ),
                    "holdout_mae": _clean_number(
                        comparison_holdout.get("holdout_mae")
                        if comparison_holdout is not None
                        else None
                    ),
                    "holdout_mape_non_zero": _clean_number(
                        comparison_holdout.get("holdout_mape")
                        if comparison_holdout is not None
                        else None
                    ),
                }
            )
        payload["comparison_table"] = comparison_table

    return _prune_none(payload)


def build_prompt(payload: dict[str, Any]) -> str:
    model_name = payload.get("model_name", "OLS")
    date_range = payload.get("date_range", "")
    n_weeks = payload.get("n_weeks", 0)
    n_channels = len(payload.get("channels", []))
    controls = payload.get("controls", [])
    control_names = ", ".join(item["name"] for item in controls) if controls else "none"
    return _render_prompt_template(
        "analysis_prompt.txt",
        {
            "MODEL_NAME": str(model_name),
            "DATE_RANGE": str(date_range),
            "N_WEEKS": str(n_weeks),
            "N_CHANNELS": str(n_channels),
            "CONTROL_NAMES": control_names,
            "PAYLOAD_JSON": json.dumps(payload, ensure_ascii=True, indent=2),
        },
    )


def build_setup_prompt(payload: dict[str, Any]) -> str:
    return _render_prompt_template(
        "setup_prompt.txt",
        {
            "PAYLOAD_JSON": json.dumps(payload, ensure_ascii=True, indent=2),
        },
    )


def get_summary(
    payload: dict[str, Any],
    provider: str,
    api_key: str,
    model: str,
    detailed: bool = True,
) -> str:
    prompt = build_prompt(payload)
    if not detailed:
        prompt += (
            "\n\nCondense output to four sections only"
            "\n1. Executive summary"
            "\n2. Statistical check"
            "\n3. Recommendation"
            "\n4. Confidence note"
            "\nKeep total output under 180 words."
        )
    return _get_text_response(
        prompt,
        provider,
        api_key,
        model,
        max_tokens=1400 if detailed else 500,
    )


def validate_analysis_text(
    text: str,
    payload: dict[str, Any],
    *,
    detailed: bool = True,
) -> dict[str, Any]:
    issues: list[dict[str, str]] = []
    cleaned_text = str(text or "").strip()
    if not cleaned_text:
        issues.append(
            {
                "severity": "error",
                "code": "empty_output",
                "message": "The AI response is empty.",
            }
        )
        return _build_validation_result(issues)

    sections = _extract_analysis_sections(cleaned_text)
    payload_number_tokens = _collect_payload_number_tokens(payload)
    has_comparison_table = bool(payload.get("comparison_table"))

    if detailed:
        required_sections = [
            "Executive summary",
            "Statistical rigor check",
            "Channel diagnosis",
            "Action plan",
            "Risks and assumptions",
        ]
        optional_sections = ["Cross-model consistency"]
        expected_order = [
            "Executive summary",
            "Statistical rigor check",
            "Channel diagnosis",
            "Cross-model consistency",
            "Action plan",
            "Risks and assumptions",
        ]
    else:
        required_sections = [
            "Executive summary",
            "Statistical check",
            "Recommendation",
            "Confidence note",
        ]
        optional_sections = []
        expected_order = required_sections

    for section_name in required_sections:
        if section_name not in sections:
            issues.append(
                {
                    "severity": "error",
                    "code": "missing_section",
                    "message": f"Missing required section `{section_name}`.",
                }
            )

    present_order = [name for name in sections.keys() if name in expected_order]
    expected_present_order = [name for name in expected_order if name in sections]
    if present_order != expected_present_order:
        issues.append(
            {
                "severity": "error",
                "code": "section_order",
                "message": "The AI response sections are out of order.",
            }
        )

    if detailed and not has_comparison_table and "Cross-model consistency" in sections:
        issues.append(
            {
                "severity": "warning",
                "code": "unexpected_cross_model_section",
                "message": "The response includes `Cross-model consistency` even though no comparison table was provided.",
            }
        )
    if detailed and has_comparison_table and "Cross-model consistency" not in sections:
        issues.append(
            {
                "severity": "warning",
                "code": "missing_cross_model_section",
                "message": "The response did not include `Cross-model consistency` even though comparison data was available.",
            }
        )

    executive_section_name = "Executive summary"
    executive_lines = _non_empty_section_lines(sections.get(executive_section_name, ""))
    if detailed and executive_lines:
        if len(executive_lines) != 3:
            issues.append(
                {
                    "severity": "warning",
                    "code": "executive_summary_count",
                    "message": "The executive summary should contain exactly 3 bullets.",
                }
            )
        if any(not line.lstrip().startswith("-") for line in executive_lines):
            issues.append(
                {
                    "severity": "warning",
                    "code": "executive_summary_format",
                    "message": "The executive summary lines are not formatted as bullets.",
                }
            )
        if any(not _contains_payload_number(line, payload_number_tokens) for line in executive_lines):
            issues.append(
                {
                    "severity": "warning",
                    "code": "executive_summary_numbers",
                    "message": "Each executive summary bullet should cite at least one number from the payload.",
                }
            )

    action_section_name = "Action plan" if detailed else "Recommendation"
    action_text = sections.get(action_section_name, "")
    if action_text:
        lowered_action = action_text.lower()
        if detailed:
            if "30-day" not in lowered_action and "30 day" not in lowered_action:
                issues.append(
                    {
                        "severity": "warning",
                        "code": "missing_30_day_plan",
                        "message": "The action plan does not include a 30-day step.",
                    }
                )
            if "60-day" not in lowered_action and "60 day" not in lowered_action:
                issues.append(
                    {
                        "severity": "warning",
                        "code": "missing_60_day_plan",
                        "message": "The action plan does not include a 60-day step.",
                    }
                )
        if not _contains_payload_number(action_text, payload_number_tokens):
            issues.append(
                {
                    "severity": "warning",
                    "code": "action_plan_numbers",
                    "message": "The action plan does not cite any number from the payload.",
                }
            )

    channel_diagnosis_text = sections.get("Channel diagnosis", cleaned_text)
    top_channel = payload.get("top_channel")
    bottom_channel = payload.get("bottom_channel")
    if top_channel:
        issues.extend(
            _validate_rank_claim(
                channel_diagnosis_text,
                payload,
                expected_channel=str(top_channel),
                keywords=("strongest", "most efficient", "best performer", "best channel"),
                code="top_channel_claim",
                direction="strongest",
            )
        )
    if bottom_channel:
        issues.extend(
            _validate_rank_claim(
                channel_diagnosis_text,
                payload,
                expected_channel=str(bottom_channel),
                keywords=("weakest", "worst", "least efficient", "highest cpl"),
                code="bottom_channel_claim",
                direction="weakest",
            )
        )

    return _build_validation_result(issues)


def get_setup_recommendations(
    payload: dict[str, Any],
    provider: str,
    api_key: str,
    model: str,
) -> dict[str, Any]:
    prompt = build_setup_prompt(payload)
    try:
        response_text = _get_text_response(
            prompt,
            provider,
            api_key,
            model,
            max_tokens=2200,
        )
        return _extract_json_object(response_text)
    except Exception as exc:
        return {"error": f"AI setup suggestions failed: {exc}"}


def _pick_channel_name(cpl_map: dict[str, float], *, best: bool) -> str | None:
    filtered = {key: value for key, value in cpl_map.items() if value is not None}
    if not filtered:
        return None

    finite = {key: value for key, value in filtered.items() if is_rankable_cpl(value)}
    if not finite:
        return None
    source = finite
    if best:
        return min(source.items(), key=lambda item: item[1])[0]
    return max(source.items(), key=lambda item: item[1])[0]


def _clean_number(value: Any) -> Any:
    if value is None:
        return None
    try:
        if value == float("inf"):
            return None
    except Exception:
        pass
    try:
        return round(float(value), 2)
    except Exception:
        return value


def _prune_none(value: Any) -> Any:
    if isinstance(value, dict):
        cleaned = {key: _prune_none(item) for key, item in value.items()}
        return {key: item for key, item in cleaned.items() if item is not None}
    if isinstance(value, list):
        return [_prune_none(item) for item in value]
    return value


def _get_text_response(
    prompt: str,
    provider: str,
    api_key: str,
    model: str,
    max_tokens: int,
) -> str:
    if provider == "openai":
        from openai import OpenAI

        client = OpenAI(api_key=api_key)
        response = client.responses.create(
            model=model,
            input=prompt,
            max_output_tokens=max_tokens,
        )
        return response.output_text

    if provider == "anthropic":
        try:
            from anthropic import Anthropic
        except ImportError as exc:
            raise ValueError(
                "Anthropic is not installed in this environment. Use OpenAI for the MVP setup."
            ) from exc

        client = Anthropic(api_key=api_key)
        response = client.messages.create(
            model=model,
            max_tokens=max_tokens,
            messages=[{"role": "user", "content": prompt}],
        )
        return "".join(
            block.text for block in response.content if getattr(block, "type", "") == "text"
        )

    raise ValueError(f"Unsupported provider: {provider}")


def _extract_json_object(text: str) -> dict[str, Any]:
    stripped = text.strip()
    if stripped.startswith("```"):
        stripped = stripped.strip("`")
        if stripped.lower().startswith("json"):
            stripped = stripped[4:].strip()
    start = stripped.find("{")
    end = stripped.rfind("}")
    if start == -1 or end == -1 or end <= start:
        raise ValueError("Model did not return a JSON object.")
    return json.loads(stripped[start : end + 1])


def _load_dotenv(path: Path) -> dict[str, str]:
    if not path.exists():
        return {}

    values: dict[str, str] = {}
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        cleaned = value.strip().strip('"').strip("'")
        values[key.strip()] = cleaned
    return values


def _resolve_provider_from_sources(
    *,
    provider: str | None,
    manual_model: str | None,
    dotenv_values: dict[str, str],
    credentials_payload: dict[str, Any] | None,
) -> tuple[str, str, str] | None:
    if provider == "openai":
        if dotenv_values.get("OPENAI_API_KEY"):
            return "openai", dotenv_values["OPENAI_API_KEY"], manual_model or dotenv_values.get("OPENAI_MODEL", "gpt-4o")
        if credentials_payload and credentials_payload.get("openai_api_key"):
            return "openai", credentials_payload["openai_api_key"], manual_model or credentials_payload.get("openai_model", "gpt-4o")
        if os.getenv("OPENAI_API_KEY"):
            return "openai", os.environ["OPENAI_API_KEY"], manual_model or os.getenv("OPENAI_MODEL", "gpt-4o")
    if provider == "anthropic":
        if dotenv_values.get("ANTHROPIC_API_KEY"):
            return (
                "anthropic",
                dotenv_values["ANTHROPIC_API_KEY"],
                manual_model or dotenv_values.get("ANTHROPIC_MODEL", "claude-3-5-sonnet-20241022"),
            )
        if credentials_payload and credentials_payload.get("anthropic_api_key"):
            return (
                "anthropic",
                credentials_payload["anthropic_api_key"],
                manual_model or credentials_payload.get("anthropic_model", "claude-3-5-sonnet-20241022"),
            )
        if os.getenv("ANTHROPIC_API_KEY"):
            return (
                "anthropic",
                os.environ["ANTHROPIC_API_KEY"],
                manual_model or os.getenv("ANTHROPIC_MODEL", "claude-3-5-sonnet-20241022"),
            )
    return None


def _resolve_default_provider(
    *,
    manual_model: str | None,
    dotenv_values: dict[str, str],
    credentials_payload: dict[str, Any] | None,
) -> tuple[str, str, str] | None:
    if credentials_payload:
        preferred_provider = credentials_payload.get("preferred_provider")
        preferred_source = _resolve_provider_from_sources(
            provider=preferred_provider,
            manual_model=manual_model,
            dotenv_values={},
            credentials_payload=credentials_payload,
        )
        if preferred_source is not None:
            return preferred_source

    for provider_name in ["openai", "anthropic"]:
        source = _resolve_provider_from_sources(
            provider=provider_name,
            manual_model=manual_model,
            dotenv_values=dotenv_values,
            credentials_payload=credentials_payload,
        )
        if source is not None:
            return source
    return None


def _render_prompt_template(template_name: str, replacements: dict[str, str]) -> str:
    template = _load_prompt_template(template_name)
    rendered = template
    for key, value in replacements.items():
        rendered = rendered.replace(f"{{{{{key}}}}}", value)
    return rendered


def _load_prompt_template(template_name: str) -> str:
    prompts_dir = Path(__file__).resolve().parent / "prompts"
    template_path = prompts_dir / template_name
    return template_path.read_text(encoding="utf-8")


def _build_validation_result(issues: list[dict[str, str]]) -> dict[str, Any]:
    error_count = sum(1 for issue in issues if issue["severity"] == "error")
    warning_count = sum(1 for issue in issues if issue["severity"] == "warning")
    if error_count > 0:
        status = "failed"
    elif warning_count > 0:
        status = "warning"
    else:
        status = "passed"
    return {
        "status": status,
        "error_count": error_count,
        "warning_count": warning_count,
        "issues": issues,
    }


def _extract_analysis_sections(text: str) -> dict[str, str]:
    sections: dict[str, str] = {}
    current_section: str | None = None
    buffer: list[str] = []
    for raw_line in text.splitlines():
        line = raw_line.strip()
        canonical_name = _canonical_section_name(line)
        if canonical_name is not None:
            if current_section is not None:
                sections[current_section] = "\n".join(buffer).strip()
            current_section = canonical_name
            buffer = []
            continue
        if current_section is not None:
            buffer.append(raw_line)
    if current_section is not None:
        sections[current_section] = "\n".join(buffer).strip()
    return sections


def _canonical_section_name(line: str) -> str | None:
    normalized = _normalize_heading(line)
    heading_map = {
        "executive summary": "Executive summary",
        "statistical rigor check": "Statistical rigor check",
        "statistical check": "Statistical check",
        "channel diagnosis": "Channel diagnosis",
        "cross model consistency": "Cross-model consistency",
        "action plan": "Action plan",
        "risks and assumptions": "Risks and assumptions",
        "recommendation": "Recommendation",
        "confidence note": "Confidence note",
    }
    return heading_map.get(normalized)


def _normalize_heading(line: str) -> str:
    stripped = line.strip().strip("*").strip()
    stripped = re.sub(r"^\d+\.\s*", "", stripped)
    stripped = re.sub(r"[^a-zA-Z0-9]+", " ", stripped).strip().lower()
    return stripped


def _non_empty_section_lines(section_text: str) -> list[str]:
    return [line.strip() for line in str(section_text).splitlines() if line.strip()]


def _collect_payload_number_tokens(value: Any) -> set[str]:
    tokens: set[str] = set()
    if isinstance(value, dict):
        for item in value.values():
            tokens.update(_collect_payload_number_tokens(item))
        return tokens
    if isinstance(value, list):
        for item in value:
            tokens.update(_collect_payload_number_tokens(item))
        return tokens
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        try:
            if np.isnan(value) or np.isinf(value):
                return tokens
        except TypeError:
            return tokens
        numeric_value = round(float(value), 2)
        tokens.add(_normalize_number_token(str(numeric_value)))
        integer_value = int(round(numeric_value))
        if np.isclose(numeric_value, integer_value):
            tokens.add(str(integer_value))
        return tokens
    return tokens


def _contains_payload_number(text: str, payload_numbers: set[str]) -> bool:
    for raw_token in re.findall(r"-?\d+(?:,\d{3})*(?:\.\d+)?", text):
        if _normalize_number_token(raw_token) in payload_numbers:
            return True
    return False


def _normalize_number_token(token: str) -> str:
    numeric_value = round(float(token.replace(",", "")), 2)
    return f"{numeric_value:.2f}".rstrip("0").rstrip(".")


def _validate_rank_claim(
    text: str,
    payload: dict[str, Any],
    *,
    expected_channel: str,
    keywords: tuple[str, ...],
    code: str,
    direction: str,
) -> list[dict[str, str]]:
    issues: list[dict[str, str]] = []
    channel_names = [str(channel.get("name")) for channel in payload.get("channels", []) if channel.get("name")]
    sentence_list = _split_sentences(text)
    matched_expected = False
    for sentence in sentence_list:
        lowered_sentence = sentence.lower()
        mentioned_channels = [
            channel_name
            for channel_name in channel_names
            if _sentence_mentions_channel(lowered_sentence, channel_name)
        ]
        if not mentioned_channels:
            continue
        if expected_channel in mentioned_channels:
            matched_expected = True
        if any(keyword in lowered_sentence for keyword in keywords):
            if expected_channel not in mentioned_channels:
                pretty_expected = _humanize_channel_name(expected_channel)
                pretty_found = ", ".join(_humanize_channel_name(name) for name in mentioned_channels)
                issues.append(
                    {
                        "severity": "error",
                        "code": code,
                        "message": f"The response describes `{pretty_found}` as the {direction} channel, but the payload ranks `{pretty_expected}` there.",
                    }
                )
            return issues
    if not matched_expected:
        issues.append(
            {
                "severity": "warning",
                "code": f"{code}_missing_reference",
                "message": f"The response never mentions the payload's {direction} channel `{_humanize_channel_name(expected_channel)}`.",
            }
        )
    return issues


def _split_sentences(text: str) -> list[str]:
    return [part.strip() for part in re.split(r"(?<=[.!?])\s+|\n+", str(text)) if part.strip()]


def _sentence_mentions_channel(lowered_sentence: str, channel_name: str) -> bool:
    aliases = {
        channel_name.lower(),
        channel_name.replace("_", " ").lower(),
        _humanize_channel_name(channel_name).lower(),
    }
    for alias in aliases:
        if alias and alias in lowered_sentence:
            return True
    return False


def _humanize_channel_name(channel_name: str) -> str:
    parts = [part for part in str(channel_name).replace("_", " ").split() if part]
    return " ".join(part.capitalize() for part in parts)
