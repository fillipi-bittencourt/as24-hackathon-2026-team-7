from __future__ import annotations

import re
from typing import Iterable

import numpy as np
import pandas as pd
from pandas.api.types import is_numeric_dtype


def to_snake_case(value: str) -> str:
    normalized = re.sub(r"[^0-9a-zA-Z]+", "_", str(value).strip().lower())
    normalized = re.sub(r"_+", "_", normalized).strip("_")
    return normalized or "column"


def normalize_column_names(
    df: pd.DataFrame,
) -> tuple[pd.DataFrame, dict[str, str]]:
    renamed = df.copy()
    rename_map: dict[str, str] = {}
    used_names: dict[str, int] = {}
    new_columns: list[str] = []

    for original in renamed.columns:
        base_name = to_snake_case(original)
        next_count = used_names.get(base_name, 0) + 1
        used_names[base_name] = next_count
        final_name = base_name if next_count == 1 else f"{base_name}_{next_count}"
        new_columns.append(final_name)
        if final_name != original:
            rename_map[str(original)] = final_name

    renamed.columns = new_columns
    return renamed, rename_map


def convert_mmm_data(
    df: pd.DataFrame,
    date_col: str,
    target_col: str,
    channel_cols: list[str],
    control_cols: list[str] | None,
) -> pd.DataFrame:
    converted = df.copy()
    controls = control_cols or []

    if date_col in converted.columns:
        converted[date_col] = pd.to_datetime(converted[date_col], errors="coerce")

    numeric_cols = [target_col, *channel_cols, *controls]
    for col in numeric_cols:
        if col in converted.columns:
            converted[col] = pd.to_numeric(converted[col], errors="coerce").astype(
                np.float64
            )

    return converted


def validate_mmm_data(
    df: pd.DataFrame,
    date_col: str,
    target_col: str,
    channel_cols: list[str],
    control_cols: list[str] | None = None,
) -> tuple[bool, list[str], list[str]]:
    errors: list[str] = []
    warnings: list[str] = []
    controls = control_cols or []

    required_cols = [date_col, target_col, *channel_cols, *controls]
    missing_cols = [col for col in required_cols if col not in df.columns]
    if missing_cols:
        errors.append(f"Missing required columns: {', '.join(missing_cols)}")
        return False, errors, []

    for col in required_cols:
        if df[col].isna().all():
            errors.append(f"Column {col} is empty after conversion")

    if df[date_col].isna().any():
        invalid_dates = int(df[date_col].isna().sum())
        errors.append(f"Date column contains {invalid_dates} invalid rows")

    numeric_cols: Iterable[str] = [target_col, *channel_cols, *controls]
    for col in numeric_cols:
        if col in df.columns and not is_numeric_dtype(df[col]):
            errors.append(f"Column {col} must be numeric after conversion")

    missing_mask = df[[target_col, *channel_cols, *controls]].isna().any(axis=1)
    if missing_mask.any():
        errors.append(
            "Missing values in selected model columns — remove or impute rows "
            f"before modeling. Affected rows: {int(missing_mask.sum())}."
        )

    minimum_rows = max(30, 3 * (1 + len(channel_cols) + len(controls)))
    if len(df) < minimum_rows:
        errors.append(
            f"At least {minimum_rows} rows are required for stable modeling and holdout validation with the current selected columns."
        )

    if df[date_col].duplicated().any():
        errors.append("Duplicate dates found — each row must represent a unique time period")

    for ch in channel_cols:
        if (df[ch] < 0).fillna(False).any():
            errors.append("Negative values in channel columns — spend must be ≥ 0")
            break

    if (df[target_col] < 0).fillna(False).any():
        errors.append("Negative values in target column — leads must be ≥ 0")

    if errors:
        return False, errors, []

    for ch in channel_cols:
        series = df[ch].astype(np.float64)
        std = float(series.std(ddof=0))
        mean = float(series.mean())
        if np.isclose(std, 0.0):
            warnings.append(
                f"Channel {ch} has no (or very low) variance — consider removing or checking data."
            )
            continue

        if not np.isclose(mean, 0.0):
            cv = std / abs(mean)
            if cv < 0.01:
                warnings.append(
                    f"Channel {ch} has no (or very low) variance — consider removing or checking data."
                )

    return True, [], warnings
