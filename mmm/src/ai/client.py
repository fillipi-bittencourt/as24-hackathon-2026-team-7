from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from src.results_helpers import (
    build_period_mask,
    compute_display_attribution,
    compute_view_channel_metrics,
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
    dotenv_values = _load_dotenv(root_path / ".env")
    if dotenv_values.get("OPENAI_API_KEY"):
        return (
            "openai",
            dotenv_values["OPENAI_API_KEY"],
            dotenv_values.get("OPENAI_MODEL", "gpt-4o"),
        )
    if dotenv_values.get("ANTHROPIC_API_KEY"):
        return (
            "anthropic",
            dotenv_values["ANTHROPIC_API_KEY"],
            dotenv_values.get("ANTHROPIC_MODEL", "claude-3-5-sonnet-20241022"),
        )

    credentials_path = root_path / "credentials.json"
    credentials_error: str | None = None

    if credentials_path.exists():
        try:
            payload = json.loads(credentials_path.read_text(encoding="utf-8"))
            provider = payload.get("preferred_provider")
            if not provider:
                if payload.get("openai_api_key"):
                    provider = "openai"
                elif payload.get("anthropic_api_key"):
                    provider = "anthropic"

            if provider == "openai" and payload.get("openai_api_key"):
                return (
                    "openai",
                    payload["openai_api_key"],
                    payload.get("openai_model", "gpt-4o"),
                )
            if provider == "anthropic" and payload.get("anthropic_api_key"):
                return (
                    "anthropic",
                    payload["anthropic_api_key"],
                    payload.get("anthropic_model", "claude-3-5-sonnet-20241022"),
                )
        except json.JSONDecodeError:
            credentials_error = "credentials.json is not valid JSON."
        except OSError:
            credentials_error = "credentials.json could not be read."

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
            f"{credentials_error} Add a valid credentials.json or set an API key in the sidebar."
        )
    raise ValueError("Add credentials.json or set an API key in the sidebar to enable AI analysis.")


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
    y = session_state.get("y")
    selected_channels = session_state.get("selected_visual_channels") or model_result.channel_names
    selected_period = session_state.get("results_period", "All data")
    date_series = pd.to_datetime(df[date_col])
    period_mask = build_period_mask(date_series, selected_period)
    actual_total = float(y[period_mask].sum()) if y is not None else 0.0
    display_channel_totals, baseline_total, unexplained_total = compute_display_attribution(
        model_result,
        actual_total,
        row_mask=period_mask,
    )
    spend_totals, view_cpl_map = compute_view_channel_metrics(
        df,
        list(selected_channels),
        period_mask,
        display_channel_totals,
    )

    channels: list[dict[str, Any]] = []
    for ch in selected_channels:
        contribution_total = float(display_channel_totals.get(ch, 0.0))
        contribution_share = (contribution_total / actual_total) * 100 if not np.isclose(actual_total, 0.0) else None
        channels.append(
            {
                "name": ch,
                "coefficient": _clean_number(model_result.coefficients.get(ch)),
                "cpl": _clean_number(view_cpl_map.get(ch)),
                "contribution_pct": _clean_number(contribution_share),
                "contribution_total": _clean_number(contribution_total),
                "contribution_share_of_actual_pct": _clean_number(contribution_share),
                "spend_total": _clean_number(spend_totals.get(ch)),
            }
        )

    predicted_total = float(np.sum(model_result.y_pred[period_mask]))

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
        "unexplained_total_leads": _clean_number(unexplained_total),
        "channels": channels,
        "controls": [{"name": col} for col in control_cols],
        "baseline_pct": _clean_number((baseline_total / actual_total) * 100 if not np.isclose(actual_total, 0.0) else 0.0),
        "top_channel": _pick_channel_name(view_cpl_map, best=True),
        "bottom_channel": _pick_channel_name(view_cpl_map, best=False),
    }

    if include_comparison and len(model_results) > 1:
        comparison_table: list[dict[str, Any]] = []
        for name, result in model_results.items():
            rmse = float(result.rmse)
            comparison_table.append(
                {
                    "model_name": name,
                    "r_squared": _clean_number(result.r_squared),
                    "rmse": _clean_number(rmse),
                    "is_selected_model": bool(name == model_result.model_name),
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

    return "\n".join(
        [
            "Instructions",
            "You are a senior marketing analytics lead preparing decision support for analysts, managers, CMO, and CEO. Be direct, concrete, and numeric. Explain reasoning and caveats clearly. Do not invent numbers. Every recommendation must cite numeric evidence from the payload. If evidence is weak or missing, say so explicitly.",
            "",
            "Context",
            f"This is a Marketing Mix Model fitted on {date_range} marketing spend and leads data. Success metric is cost per lead. The team used {model_name}. {n_weeks} weeks of data. {n_channels} media channels. Control variables included: {control_names}.",
            "",
            "Example",
            'Input: TV CPL 12.50, Digital CPL 18.20, Social CPL 45.00',
            'Output: "TV has the best cost per lead at 12.50, followed by Digital at 18.20. Social is weakest at 45.00. Recommend shifting Social budget to TV to improve CPL."',
            "",
            "Task",
            json.dumps(payload, ensure_ascii=True, indent=2),
            "",
            "Write six sections",
            "1. Executive summary with 3 bullets and explicit numbers",
            "2. Channel diagnosis including strongest and weakest channels, spend efficiency, and lead contribution",
            "3. Model quality and trust limits referencing fit metrics and unexplained portion",
            "4. Cross-model consistency check when comparison_table exists",
            "5. Action plan for the next 30 and 60 days with testable steps",
            "6. Risks and assumptions that could change the recommendation",
            "",
            "Guardrails",
            "- cite at least one number in every recommendation",
            "- mention unexplained leads or model limits in the trust section",
            "- do not claim causal certainty",
            "- if the evidence is mixed across models, say that directly",
        ]
    )


def build_setup_prompt(payload: dict[str, Any]) -> str:
    return "\n".join(
        [
            "Instructions",
            "You are a senior marketing measurement lead preparing setup recommendations for a marketing mix model. Review the aggregated dataset profile and return only valid JSON. Do not wrap the JSON in markdown fences. Do not invent fields beyond the requested schema.",
            "",
            "Context",
            "The team needs guidance on data consistency, data completion, media transformations, and Bayesian priors before fitting the models. Recommendations must be practical for a fast hackathon workflow.",
            "",
            "Task",
            json.dumps(payload, ensure_ascii=True, indent=2),
            "",
            "Return JSON with this exact top-level structure",
            "{",
            '  "executive_summary": "string",',
            '  "column_selection_reasoning": {',
            '    "date_column": {"name": "date", "reasoning": "string"},',
            '    "target_column": {"name": "target", "reasoning": "string"},',
            '    "channels": {"<channel_name>": "string"},',
            '    "controls": {"<control_name>": "string"}',
            "  },",
            '  "data_quality_findings": ["string"],',
            '  "completion_actions": ["string"],',
            '  "transform_recommendations": {',
            '    "<channel_name>": {',
            '      "adstock_type": "geometric or none",',
            '      "theta": 0.3,',
            '      "saturation_type": "log or hill or none",',
            '      "alpha": 1.0,',
            '      "k": 1000.0,',
            '      "reasoning": "string"',
            "    }",
            "  },",
            '  "regularization_suggestion": {',
            '    "reg_alpha": 1.0,',
            '    "l1_ratio": 0.5,',
            '    "reasoning": "string"',
            "  },",
            '  "prior_recommendations": {',
            '    "intercept_mu_mode": "data_mean or manual",',
            '    "intercept_mu": 0.0,',
            '    "intercept_sigma_scale": 1.0,',
            '    "channel_prior_family": "HalfNormal or Normal",',
            '    "channel_sigma_scale": 1.0,',
            '    "control_sigma_scale": 1.0,',
            '    "noise_sigma_scale": 1.0,',
            '    "reasoning_summary": "string",',
            '    "channel_recommendations": {',
            '      "<channel_name>": {',
            '        "family": "HalfNormal or Normal",',
            '        "sigma_scale": 1.0,',
            '        "reasoning": "string"',
            "      }",
            "    }",
            "  }",
            "}",
            "",
            "Rules",
            "- Use only the channel names provided in the payload.",
            "- Prefer HalfNormal for channels unless the profile suggests a weak or uncertain effect.",
            "- Keep theta within 0.1 to 0.9.",
            "- Keep alpha within 0.1 to 5.0.",
            "- Keep sigma scales positive and practical, usually between 0.2 and 3.0.",
            "- Mention missing values, duplicated behavior, flat spend, suspicious negatives, or likely data completion needs when relevant.",
        ]
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
            "\n2. Top finding"
            "\n3. Recommendation"
            "\n4. Confidence note"
            "\nKeep total output under 180 words."
        )

    try:
        return _get_text_response(
            prompt,
            provider,
            api_key,
            model,
            max_tokens=1400 if detailed else 500,
        )
    except Exception as exc:
        return f"AI summary failed: {exc}"


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

    finite = {key: value for key, value in filtered.items() if value != float("inf")}
    source = finite or filtered
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
