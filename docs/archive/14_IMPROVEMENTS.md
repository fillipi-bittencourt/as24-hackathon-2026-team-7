# Improvements to the instructions

Recommendations for data quality, model validation, interpretability, reproducibility, and export — so the MMM app and build instructions meet the needs of everyone who uses it.

---

## 1. Data quality and diagnostics

**Current state:** Validation checks presence, types, duplicates, negative spend, and row count. Conversion coerces invalid values to NaN.

**Improvements:**

- **Missing values (target and channels):** Specify an explicit rule. Either (a) **reject** — add a validation error if `df[target_col].isna().any()` or `df[channel_cols].isna().any()` with message like "Missing values in target or channel columns — remove or impute before modeling", or (b) **drop** — document that rows with NaN in target or any channel are dropped before fit and show a warning with the number of rows dropped. Users need to know whether the model is fit on full or trimmed data.
- **Data preview in Data tab:** After load and validation, show a short **summary** (e.g. `st.dataframe(df[relevant_cols].describe())` or key stats: mean, min, max, null count per column). Enables a quick sanity check without leaving the app.
- **Constant or near-constant channels:** If a channel has zero variance (or very low, e.g. cv &lt; 0.01), the model can be unstable. Add an optional validation warning: "Channel X has no (or very low) variance — consider removing or checking data."
- **Outliers (optional):** Document or add an optional check: e.g. flag if any channel or target value is &gt; N standard deviations from the mean (e.g. N=5), so users can decide to winsorize or exclude.

---

## 2. Units and interpretability

**Current state:** Target = leads, success metric = CPL (€ per lead). Coefficients are in "leads per unit of transformed input."

**Improvements:**

- **Single source of units:** In 04_DATA_MODEL (or a short "Reporting conventions" subsection), state explicitly: "Spend columns are in **euros (€)** unless the CSV is pre-scaled. Target is in **lead count**. CPL is therefore € per lead. If your data uses different units (e.g. spend in 000s), scale before load or document the factor so CPL is interpretable."
- **Contribution vs actuals:** Optionally show **attributed share of actual target** (e.g. `sum(contribution[ch]) / sum(y_actual)` in addition to share of `y_pred`), so users can compare model attribution to the real total.
- **Coefficient comparison table:** Consider adding a column for **CPL** per channel per model (not only coefficient), so comparison is in business units (€/lead) as well as in model units.

---

## 3. Model validation and comparison

**Current state:** In-sample R² and RMSE; comparison table across models. No holdout or time-based validation.

**Improvements:**

- **Holdout / train–test:** Document that the app uses **in-sample fit only**. Add a short note: "For out-of-sample validation, use a time-based holdout (e.g. fit on 80% oldest weeks, evaluate on 20% most recent) in a separate workflow or future enhancement." Optionally add a "Holdout %" selector that splits by time and reports holdout RMSE/MAE.
- **Comparison table metrics:** Already mention optional MAE. Add **MAPE** (mean absolute percentage error) as an optional column when `y` has no zeros, so relative error is comparable across datasets. Document that MAE and MAPE are on the **same scale as y** (leads).
- **Model selection guidance:** Add one sentence: "Ridge/Lasso/ElasticNet are preferred when channels are correlated; OLS is a baseline; PyMC gives credible intervals for CPL and coefficients." Helps users choose which models to fit first.

---

## 4. Transforms — guidance and safety

**Current state:** Per-channel adstock/saturation type and params; defaults (geometric, hill; k from median/max).

**Improvements:**

- **Why these defaults:** In 05_TRANSFORMS or Config section, add a one-line rationale: "Default k = max(median, 10% of max, 1) places half-saturation near typical spend levels; adjust if your spend range is very different."
- **Theta (adstock):** "Typical range 0.1–0.9: higher = longer carryover. Use prior campaigns or category benchmarks if available."
- **Bulk defaults (optional):** "Set all channels to same adstock/saturation type or same theta" reduces repetitive clicking when there are many channels.
- **Transforms changed → clear results:** Already specified; ensure it is clearly visible in the UI (e.g. warning banner) so users don't accidentally compare on stale transforms.

---

## 5. Reproducibility and export

**Current state:** No fixed random seed; no export of results.

**Improvements:**

- **Random seed:** Set a **fixed seed** for PyMC (e.g. `pm.sample(..., random_seed=42)`) and for sklearn (e.g. `np.random.seed(42)` before fit, or pass `random_state=42` where supported). Document in 10_BUILD_MMM: "Use a fixed random seed (e.g. 42) for PyMC and sklearn so that the same data and config produce the same results."
- **Export results:** Add an **Export** button in the Results tab: download **comparison table** (models × R², RMSE, MAE) and **coefficient/CPL table** (channels × models) as CSV for reporting and tracking.
- **Model fitted timestamp:** Store and display "Model fitted on: &lt;date/time&gt;" (or "Data as of: &lt;max date in df&gt;") so reports are auditable.

---

## 6. Edge cases and robustness

**Current state:** Negative CPL → show "—" or "N/A"; underdetermined warning; duplicate dates rejected.

**Improvements:**

- **Zero spend in a channel:** Allowed; CPL can be inf. Document: "Channels with zero total spend will show CPL as N/A (infinite)."
- **Rank deficiency (constant column, perfect collinearity):** OLS/sklearn can fail or warn. Add: "If fit fails with 'singular matrix' or 'rank deficiency', check for constant or duplicate channel columns and remove or add regularization."
- **Scale of alpha (Ridge/Lasso):** Already noted in 06_MODELS that we don't standardize. Add in 10_BUILD_MMM or Config: "Ridge/Lasso alpha is on the raw scale. If channel spend columns differ by orders of magnitude, consider scaling spend (e.g. per 1k€) or tuning alpha per run."

---

## 7. UX

**Improvements:**

- **Model comparison table:** Make columns **sortable** (e.g. by R² or RMSE) so the best model can be found at a glance. Already requested; ensure implementation allows sort.
- **Coefficient comparison:** Consider adding **CPL** as a second view (channels × models, cells = CPL) or toggle, so comparison is in business terms.
- **Quick re-fit:** After changing only regularization (e.g. alpha), allow re-fitting without re-applying transforms; currently changing Config and re-applying clears model_results — acceptable, but a note "Only transform params changed; you can re-fit without changing data" can reduce confusion.
- **Data tab:** After successful load, show **row count and date range** prominently (already there); add "Grain: daily/weekly" if inferable from date spacing, so users know the time unit.

---

## Summary — what to add to the build instructions

| Priority | Improvement | Where to add |
|----------|-------------|--------------|
| High | Explicit missing-value rule (reject or drop + warn) | 10_BUILD_MMM Step 1.1b; 04_DATA_MODEL |
| High | Fixed random seed for PyMC and sklearn | 10_BUILD_MMM Steps 3.4, 4.1 |
| High | Export comparison + coefficient/CPL table as CSV | 10_BUILD_MMM Step 5 (Results) |
| Medium | Data preview / summary stats after load | 10_BUILD_MMM Step 1.3 |
| Medium | Units and scale (€, leads) in one place | 04_DATA_MODEL |
| Medium | Holdout note (in-sample only; optional future holdout) | 10_BUILD_MMM or 06_MODELS |
| Medium | Optional MAE/MAPE in model comparison table | 10_BUILD_MMM Step 5.3 |
| Low | Constant-channel warning | 10_BUILD_MMM Step 1.1b or utils |
| Low | CPL column in coefficient comparison (or second table) | 10_BUILD_MMM Step 5.3 |
| Low | Model fitted / data-as-of timestamp | 10_BUILD_MMM Step 3.5 / 5 |

This document can be used as a backlog for implementation and as context when updating 10_BUILD_MMM, 04_DATA_MODEL, and related specs.
