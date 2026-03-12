# Data Model

## Target and success metric

**Target variable:** leads. The `target` column is the outcome we model (leads or conversions). AutoScout24 measures success by **leads**.

**Success metric:** cost per lead (CPL). We report **cost per lead** (€ per lead) per channel and overall — not ROI. Lower CPL = better. All model outputs and UI use CPL as the primary efficiency metric.

---

## Datatypes and conversion

**Required dtypes after conversion** (used everywhere downstream):

| Column(s) | Required dtype | Description |
|-----------|-----------------|-------------|
| date (selected date column) | `datetime64[ns]` or pandas `Timestamp` | Parsed from CSV; must be sortable and unique per row |
| target (selected target column) | `float64` | Outcome (leads); must be numeric |
| channel_* (selected channel columns) | `float64` | Media spend; must be numeric, ≥ 0 |
| control_* (selected control columns) | `float64` | Optional; must be numeric |

**Detection and conversion (apply before validation):**

1. **Detect:** After loading CSV, columns may be `object`, `string`, `int64`, or mixed. Inspect `df[col].dtype` for the selected date, target, channel, and control columns.
2. **Convert date:** `pd.to_datetime(df[date_col], errors='coerce')` → yields `datetime64[ns]`. Rows that fail become `NaT`; validation will flag them.
3. **Convert numeric (target, channel, control):** `pd.to_numeric(df[col], errors='coerce')` → yields `float64`. Non-numeric values become NaN; validation will flag all-null or invalid rows.
4. **Replace:** Write converted series back into the dataframe (or build a converted copy) so that `df[date_col].dtype == datetime64[ns]` and `df[target_col].dtype` and `df[ch].dtype` for all channel/control columns are `float64`.
5. **Then validate:** Run validation on the **converted** dataframe. Validation checks: presence of required columns, no NaT/NaN in date/target/channel columns, no duplicate dates, no negative channel values, minimum row count. **Missing values:** Target and channel columns must have no NaN; validation fails with a clear error so the model is never fit on incomplete data without the user’s knowledge. Validation may also return **warnings** (e.g. constant or near-constant channel variance) without failing; the UI should show these.

**Downstream types (guaranteed after conversion + validation):**

- `df[date_col]`: datetime64[ns]
- `df[target_col]`, `df[ch]` for ch in channel_cols + control_cols: float64
- `X_transformed` (from transform_media): `np.ndarray` shape `(n_rows, n_channels + n_controls)`, dtype **float64**
- `y` (target vector): `np.ndarray` shape `(n_rows,)`, dtype **float64**
- `raw_spend[ch]`: 1D array from `df[ch].values` — will be float64 if df was converted

---

## Input Schema

**Reporting conventions:** Spend columns are in **euros (€)** unless the CSV is pre-scaled. Target is in **lead count**. CPL is therefore € per lead. If your data uses different units (e.g. spend in 000s), scale before load or document the factor so CPL and coefficients are interpretable.

Minimum required columns:

| Column | Type | Description |
|--------|------|-------------|
| date | date | Grain date (daily, weekly) |
| target | float | Outcome — **leads** (or conversions). This is our success metric. |
| channel_* | float | Media spend per channel (e.g. tv_spend, digital_spend) |

Optional:

| Column | Type | Description |
|--------|------|-------------|
| control_* | float | Non-media controls (price, promo, etc.) |
| seasonality | int/float | Pre-computed seasonality index |

---

## Example

```
date       | target | tv_spend | digital_spend | search_spend
2024-01-01 | 1200   | 5000     | 2000          | 1000
2024-01-02 | 1150   | 4800     | 2100          | 1100
...
```

---

## Output Schema (Model Results)

The canonical `ModelResult` definition is in [06_MODELS.md](06_MODELS.md). Summary for reference:

| Field | Type | Description |
|-------|------|-------------|
| `model_name` | str | e.g. "OLS", "Ridge", "PyMC" |
| `channel_names` | list[str] | Channel names in order |
| `coefficients` | dict[str, float] | Scalar coefficient per channel |
| `intercept` | float | Model intercept |
| `cpl` | dict[str, float] | Cost per lead: `sum(raw_spend[ch]) / sum(contribution[ch])` (€ per lead); guard for zero attributed leads |
| `contribution` | dict[str, **np.ndarray**] | **Vector** per channel (length = n_rows) — attributed **leads** per period; use `.sum()` for totals |
| `contribution_pct` | dict[str, float] | `sum(contribution[ch]) / sum(y_pred)` |
| `y_pred` | np.ndarray | Predicted target, shape (n_rows,) |
| `baseline` | np.ndarray | Residual after channel attribution, clipped ≥ 0 |
| `baseline_pct` | float | `sum(baseline) / sum(y_pred)` |
| `r_squared` | float | |
| `rmse` | float | |

**Contribution vs actuals:** Optionally report **share of actual target** as `sum(contribution[ch]) / sum(y_actual)` in addition to share of `y_pred`, so users can compare model attribution to the real total.

PyMC adds (None for all other models):

| Field | Type |
|-------|------|
| `coefficient_lower`, `coefficient_upper` | dict[str, float] |
| `cpl_lower`, `cpl_upper` | dict[str, float] |

---

## Transform Parameters (Per Channel)

| Param | Description | Typical range |
|-------|-------------|---------------|
| **adstock_type** | "geometric" \| "none" per channel | Default: geometric |
| **saturation_type** | "hill" \| "log" \| "none" per channel | Default: hill |
| adstock_theta | Geometric decay rate (if adstock_type = geometric) | 0.1–0.9 |
| saturation_alpha | Hill shape (if saturation_type = hill) | 0.5–3 |
| saturation_k | Half-saturation (if saturation_type = hill) | channel-dependent |
