from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any


def load_credentials(
    manual_api_key: str | None = None,
    manual_provider: str | None = None,
    manual_model: str | None = None,
) -> tuple[str, str, str]:
    root_path = Path(__file__).resolve().parents[2]
    credentials_path = root_path / "credentials.json"

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
        except Exception:
            pass

    if os.getenv("OPENAI_API_KEY"):
        return "openai", os.environ["OPENAI_API_KEY"], os.getenv("OPENAI_MODEL", "gpt-4o")
    if os.getenv("ANTHROPIC_API_KEY"):
        return (
            "anthropic",
            os.environ["ANTHROPIC_API_KEY"],
            os.getenv("ANTHROPIC_MODEL", "claude-3-5-sonnet-20241022"),
        )

    if manual_api_key:
        provider = manual_provider or "openai"
        model = manual_model or ("gpt-4o" if provider == "openai" else "claude-3-5-sonnet-20241022")
        return provider, manual_api_key, model

    raise ValueError("Add credentials.json or set an API key in the sidebar to enable AI analysis.")


def build_payload(model_result: Any, session_state: dict[str, Any]) -> dict[str, Any]:
    df = session_state["df"]
    date_col = session_state["date_col"]
    channel_cols = session_state["channel_cols"]
    model_results = session_state.get("model_results", {})

    channels: list[dict[str, Any]] = []
    for ch in model_result.channel_names:
        channels.append(
            {
                "name": ch,
                "coefficient": _clean_number(model_result.coefficients.get(ch)),
                "cpl": _clean_number(model_result.cpl.get(ch)),
                "contribution_pct": _clean_number(model_result.contribution_pct.get(ch)),
            }
        )

    payload: dict[str, Any] = {
        "model_name": model_result.model_name,
        "date_range": f"{df[date_col].min().date()} to {df[date_col].max().date()}",
        "target_metric": "leads",
        "n_weeks": int(len(df)),
        "model_fit": {
            "r_squared": _clean_number(model_result.r_squared),
            "rmse": _clean_number(model_result.rmse),
        },
        "channels": channels,
        "controls": [],
        "baseline_pct": _clean_number(model_result.baseline_pct),
        "top_channel": _pick_channel_name(model_result.cpl, best=True),
        "bottom_channel": _pick_channel_name(model_result.cpl, best=False),
    }

    if len(model_results) > 1:
        comparison_table: list[dict[str, Any]] = []
        for name, result in model_results.items():
            comparison_table.append(
                {
                    "model_name": name,
                    "r_squared": _clean_number(result.r_squared),
                    "rmse": _clean_number(result.rmse),
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
            "You are a senior marketing analyst presenting to the C-suite. Be direct and specific. Use numbers. Avoid jargon. Write for an executive who has 2 minutes to read this.",
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
            "Write four sections",
            "1. Executive summary",
            "2. Top finding",
            "3. Recommendation",
            "4. Confidence note",
        ]
    )


def get_summary(payload: dict[str, Any], provider: str, api_key: str, model: str) -> str:
    prompt = build_prompt(payload)

    try:
        if provider == "openai":
            from openai import OpenAI

            client = OpenAI(api_key=api_key)
            response = client.responses.create(
                model=model,
                input=prompt,
            )
            return response.output_text

        if provider == "anthropic":
            try:
                from anthropic import Anthropic
            except ImportError:
                return "Anthropic is not installed in this environment. Use OpenAI for the MVP setup."

            client = Anthropic(api_key=api_key)
            response = client.messages.create(
                model=model,
                max_tokens=600,
                messages=[{"role": "user", "content": prompt}],
            )
            return "".join(
                block.text for block in response.content if getattr(block, "type", "") == "text"
            )

        return f"Unsupported provider: {provider}"
    except Exception as exc:
        return f"AI summary failed: {exc}"


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
