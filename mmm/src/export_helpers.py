from __future__ import annotations

import io
import json
import textwrap
from typing import Any

import matplotlib.pyplot as plt
import pandas as pd
import streamlit as st
from matplotlib.backends.backend_pdf import PdfPages


def df_to_csv_bytes(df: pd.DataFrame) -> bytes:
    return df.to_csv(index=False).encode("utf-8")


def _wrap_text_block(body: str, width: int = 140) -> str:
    wrapped_lines: list[str] = []
    for line in str(body).splitlines():
        if not line.strip():
            wrapped_lines.append("")
            continue
        wrapped_lines.extend(textwrap.wrap(line, width=width) or [""])
    return "\n".join(wrapped_lines)


def build_text_pdf_bytes(title: str, sections: list[tuple[str, str]]) -> bytes:
    buffer = io.BytesIO()
    with PdfPages(buffer) as pdf:
        for heading, body in sections:
            fig = plt.figure(figsize=(11.69, 8.27))
            plt.axis("off")
            wrapped_body = _wrap_text_block(body, width=140)
            plt.text(
                0.02,
                0.98,
                f"{title}\n\n{heading}\n\n{wrapped_body}",
                va="top",
                ha="left",
                fontsize=11,
                family="monospace",
            )
            pdf.savefig(fig, bbox_inches="tight")
            plt.close(fig)
    return buffer.getvalue()


def build_results_pdf_bytes(
    selected_model: str,
    selected_period: str,
    overview_df: pd.DataFrame,
    channel_df: pd.DataFrame,
    comparison_df: pd.DataFrame,
) -> bytes:
    sections = [
        (
            "overview",
            f"model {selected_model}\nperiod {selected_period}\n\n"
            + overview_df.to_string(index=False),
        ),
        (
            "channel breakdown",
            channel_df.to_string(index=False) if not channel_df.empty else "no channels selected",
        ),
        (
            "model comparison",
            comparison_df.to_string(index=False),
        ),
    ]
    return build_text_pdf_bytes("mmm results export", sections)


def build_column_selection_rows() -> list[dict[str, str]]:
    setup_recommendations = st.session_state.get("ai_setup_recommendations") or {}
    reasoning = setup_recommendations.get("column_selection_reasoning", {})
    rows: list[dict[str, str]] = []

    rows.append(
        {
            "section": "column_selection",
            "item": "date_column",
            "value": str(st.session_state.get("date_col") or ""),
            "reasoning": str(
                reasoning.get("date_column", {}).get(
                    "reasoning",
                    "Selected as the time index used to order the series and support time-based modeling.",
                )
            ),
        }
    )
    rows.append(
        {
            "section": "column_selection",
            "item": "target_column",
            "value": str(st.session_state.get("target_col") or ""),
            "reasoning": str(
                reasoning.get("target_column", {}).get(
                    "reasoning",
                    "Selected as the business outcome the model is trying to explain.",
                )
            ),
        }
    )
    for channel in st.session_state.get("channel_cols", []):
        rows.append(
            {
                "section": "column_selection",
                "item": f"channel::{channel}",
                "value": channel,
                "reasoning": str(
                    reasoning.get("channels", {}).get(
                        channel,
                        "Selected as a media driver included in the attribution model.",
                    )
                ),
            }
        )
    for control in st.session_state.get("control_cols", []):
        rows.append(
            {
                "section": "column_selection",
                "item": f"control::{control}",
                "value": control,
                "reasoning": str(
                    reasoning.get("controls", {}).get(
                        control,
                        "Selected as a non-media control to explain baseline variation.",
                    )
                ),
            }
        )
    return rows


def build_complete_overview_export_df(
    *,
    selected_model: str,
    selected_period: str,
    overview_df: pd.DataFrame,
    comparison_df: pd.DataFrame,
    channel_df: pd.DataFrame,
    recommendation_lines: list[str],
    ai_analysis: str | None,
) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    rows.extend(build_column_selection_rows())

    setup_recommendations = st.session_state.get("ai_setup_recommendations") or {}
    for finding in setup_recommendations.get("data_quality_findings", []):
        rows.append(
            {
                "section": "data_quality",
                "item": "finding",
                "value": "",
                "reasoning": str(finding),
            }
        )
    for action in setup_recommendations.get("completion_actions", []):
        rows.append(
            {
                "section": "data_completion",
                "item": "action",
                "value": "",
                "reasoning": str(action),
            }
        )

    transform_recommendations = setup_recommendations.get("transform_recommendations", {})
    for channel in st.session_state.get("channel_cols", []):
        suggestion = transform_recommendations.get(channel, {})
        current_saturation = st.session_state["saturation_params"].get(channel, {"alpha": 1.0, "k": 0.0})
        rows.append(
            {
                "section": "transforms",
                "item": channel,
                "value": (
                    f"adstock={st.session_state['adstock_type'].get(channel, 'geometric')}, "
                    f"theta={round(float(st.session_state['adstock_params'].get(channel, 0.0)), 3)}, "
                    f"saturation={st.session_state['saturation_type'].get(channel, 'log')}, "
                    f"alpha={round(float(current_saturation.get('alpha', 1.0)), 3)}, "
                    f"k={round(float(current_saturation.get('k', 0.0)), 3)}"
                ),
                "reasoning": str(suggestion.get("reasoning", "")),
            }
        )

    prior_config = st.session_state.get("pymc_prior_config", {})
    prior_recommendations = setup_recommendations.get("prior_recommendations", {})
    rows.append(
        {
            "section": "priors",
            "item": "global",
            "value": (
                f"intercept_mu_mode={prior_config.get('intercept_mu_mode', 'data_mean')}, "
                f"intercept_sigma_scale={prior_config.get('intercept_sigma_scale', 1.0)}, "
                f"channel_prior_family={prior_config.get('channel_prior_family', 'HalfNormal')}, "
                f"channel_sigma_scale={prior_config.get('channel_sigma_scale', 1.0)}, "
                f"control_sigma_scale={prior_config.get('control_sigma_scale', 1.0)}, "
                f"noise_sigma_scale={prior_config.get('noise_sigma_scale', 1.0)}"
            ),
            "reasoning": str(prior_recommendations.get("reasoning_summary", "")),
        }
    )
    channel_prior_overrides = prior_config.get("channel_prior_overrides", {})
    channel_prior_recommendations = prior_recommendations.get("channel_recommendations", {})
    channel_prior_reasoning = st.session_state.get("pymc_prior_reasoning", {})
    for channel in st.session_state.get("channel_cols", []):
        override = channel_prior_overrides.get(channel, {})
        rows.append(
            {
                "section": "priors",
                "item": channel,
                "value": (
                    f"family={override.get('family', prior_config.get('channel_prior_family', 'HalfNormal'))}, "
                    f"sigma_scale={override.get('sigma_scale', prior_config.get('channel_sigma_scale', 1.0))}"
                ),
                "reasoning": str(
                    channel_prior_reasoning.get(
                        channel,
                        channel_prior_recommendations.get(channel, {}).get("reasoning", ""),
                    )
                ),
            }
        )

    rows.append(
        {
            "section": "results_context",
            "item": "current_view",
            "value": (
                f"model={selected_model}, period={selected_period}, "
                f"channels={', '.join(st.session_state.get('selected_visual_channels') or []) or 'all'}"
            ),
            "reasoning": "Current filters used for the final overview export.",
        }
    )
    for record in overview_df.to_dict(orient="records"):
        rows.append(
            {
                "section": "results_overview",
                "item": str(record["Metric"]),
                "value": record["Value"],
                "reasoning": "",
            }
        )
    for record in comparison_df.to_dict(orient="records"):
        rows.append(
            {
                "section": "model_comparison",
                "item": str(record.get("Model", "")),
                "value": json.dumps(record, ensure_ascii=True),
                "reasoning": "",
            }
        )
    for record in channel_df.to_dict(orient="records"):
        rows.append(
            {
                "section": "channel_results",
                "item": str(record.get("Channel", "")),
                "value": json.dumps(record, ensure_ascii=True),
                "reasoning": "",
            }
        )
    for idx, recommendation in enumerate(recommendation_lines, start=1):
        rows.append(
            {
                "section": "recommendations",
                "item": f"recommendation_{idx}",
                "value": recommendation,
                "reasoning": "",
            }
        )
    rows.append(
        {
            "section": "ai_analysis",
            "item": "analysis",
            "value": ai_analysis or "No AI analysis generated yet.",
            "reasoning": "",
        }
    )
    return pd.DataFrame(rows)


def build_complete_overview_pdf_bytes(
    *,
    selected_model: str,
    selected_period: str,
    overview_df: pd.DataFrame,
    comparison_df: pd.DataFrame,
    channel_df: pd.DataFrame,
    recommendation_lines: list[str],
    ai_analysis: str | None,
) -> bytes:
    setup_recommendations = st.session_state.get("ai_setup_recommendations") or {}
    column_selection_lines = [
        f"{row['item']}: {row['value']} | {row['reasoning']}"
        for row in build_column_selection_rows()
    ]
    transform_lines = []
    for channel in st.session_state.get("channel_cols", []):
        saturation_params = st.session_state["saturation_params"].get(channel, {"alpha": 1.0, "k": 0.0})
        transform_lines.append(
            (
                f"{channel}: adstock={st.session_state['adstock_type'].get(channel, 'geometric')}, "
                f"theta={round(float(st.session_state['adstock_params'].get(channel, 0.0)), 3)}, "
                f"saturation={st.session_state['saturation_type'].get(channel, 'log')}, "
                f"alpha={round(float(saturation_params.get('alpha', 1.0)), 3)}, "
                f"k={round(float(saturation_params.get('k', 0.0)), 3)} | "
                f"{setup_recommendations.get('transform_recommendations', {}).get(channel, {}).get('reasoning', '')}"
            )
        )

    prior_lines = []
    prior_config = st.session_state.get("pymc_prior_config", {})
    prior_lines.append(
        (
            "global: "
            f"intercept_mu_mode={prior_config.get('intercept_mu_mode', 'data_mean')}, "
            f"intercept_sigma_scale={prior_config.get('intercept_sigma_scale', 1.0)}, "
            f"channel_prior_family={prior_config.get('channel_prior_family', 'HalfNormal')}, "
            f"channel_sigma_scale={prior_config.get('channel_sigma_scale', 1.0)}, "
            f"control_sigma_scale={prior_config.get('control_sigma_scale', 1.0)}, "
            f"noise_sigma_scale={prior_config.get('noise_sigma_scale', 1.0)} | "
            f"{setup_recommendations.get('prior_recommendations', {}).get('reasoning_summary', '')}"
        )
    )
    channel_prior_reasoning = st.session_state.get("pymc_prior_reasoning", {})
    for channel in st.session_state.get("channel_cols", []):
        override = prior_config.get("channel_prior_overrides", {}).get(channel, {})
        prior_lines.append(
            (
                f"{channel}: family={override.get('family', prior_config.get('channel_prior_family', 'HalfNormal'))}, "
                f"sigma_scale={override.get('sigma_scale', prior_config.get('channel_sigma_scale', 1.0))} | "
                f"{channel_prior_reasoning.get(channel, '')}"
            )
        )

    sections = [
        (
            "overview",
            "\n".join(
                [
                    f"model {selected_model}",
                    f"period {selected_period}",
                    f"selected channels {', '.join(st.session_state.get('selected_visual_channels') or []) or 'all'}",
                    "",
                    overview_df.to_string(index=False),
                ]
            ),
        ),
        (
            "column selection reasoning",
            "\n".join(column_selection_lines) or "No column reasoning available.",
        ),
        (
            "data quality and completion",
            "\n".join(
                [*setup_recommendations.get("data_quality_findings", []), *setup_recommendations.get("completion_actions", [])]
            )
            or "No AI setup review available.",
        ),
        (
            "transform reasoning",
            "\n".join(transform_lines) or "No transform recommendations available.",
        ),
        (
            "prior reasoning",
            "\n".join(prior_lines) or "No prior recommendations available.",
        ),
        (
            "results and comparison",
            "\n\n".join(
                [
                    "model comparison",
                    comparison_df.to_string(index=False),
                    "",
                    "channel results",
                    channel_df.to_string(index=False) if not channel_df.empty else "No channel rows available.",
                ]
            ),
        ),
        (
            "recommendations and ai analysis",
            "\n".join(recommendation_lines)
            + "\n\nAI analysis\n"
            + (ai_analysis or "No AI analysis generated yet."),
        ),
    ]
    return build_text_pdf_bytes("mmm complete overview export", sections)
