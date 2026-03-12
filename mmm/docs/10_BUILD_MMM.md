# Build the MMM app — Step-by-step instructions

**Single-file build:** If the agent can load only one file, this file is sufficient to execute the build. For full fidelity (exact ModelResult, transform details, AI payload schema), optionally read the spec refs in the table below.
If an optional spec file is unavailable, continue with the minimal schema and behavior defined in this file. Do not block the build.

## Build order and verification

**Do one task item at a time. Mark it [V] when completed, then proceed to the next.**

- **Sequential:** Do task 1.1, then 1.2, then 1.3, and so on. Do not skip or jump ahead.
- **One task at a time:** Each line below that starts with [ ] is one task item. Complete that task, verify it works, then change [ ] to [V] for that item and move to the next.
- **Checkbox meaning:** [ ] = not done. [V] = task completed and verified. One checkbox per task item.

**Task list (quick scan):** 1.1, 1.2, 1.3, Check 1 · 2.1, 2.2, 2.3, 2.4, Check 2 · 3.1–3.5, Check 3 · 4.1, 4.2, Check 4 · 5.1–5.8, Check 5 · 6.1–6.5, Check 6 · 7.1–7.4, Check 7 · 8.1, Check 8.

---

## minimum viable build mode (hackathon default)

goal: ship a reliable demo fast. prioritize usability and speed over completeness.

scope for mvp:
- required: data load and validation, transform apply, fit OLS and Ridge, results comparison table, the 3 decision sections, and an AI single-model executive summary
- optional day 2 stretch: Lasso, ElasticNet, PyMC, AI Q&A, channel deep-dive charts, extra exports, compare-all AI

runtime guardrails:
- app startup under 10 seconds on sample data
- OLS and Ridge fit under 5 seconds each on up to 5k rows
- no auto-fit and no background fitting, model runs are button-driven

state guardrails:
- clear stale fits only when transform settings change
- use a deterministic `transform_fingerprint` based on channel/control selection + adstock params + saturation params + per-channel transform types

acceptance criteria:
- demo flow works end-to-end: load data -> apply transforms -> fit model -> view results
- validation errors are clear for missing or invalid date, target, or channels
- results tab always shows fitted model metrics and coefficients without crashes
- ai tab can generate a single-model executive summary without breaking the core app when credentials are missing or invalid

---

## execution mode selection

pick one mode and do not mix modes in the same run:
- iterative mode (default): complete one task item, verify, mark [V], continue
- one-shot scaffold mode: generate in phases and verify after each phase

---

## ⚡️ Efficiency & Token Saving (Meta-Instructions)

**For the Agent building this app:**
- **No conversational filler:** Do not explain the code. Do not say "Here is the implementation". Just output the code blocks.
- **One task at a time:** Complete one task item (one [ ] line), mark it [V], then proceed to the next. Do not batch multiple task items in one go.
- **Precision:** Follow the file paths exactly.
- **Thinking:** If you need to reason, keep it internal or extremely brief. Focus on generating the file contents.

---

## 🚀 One-Shot Prompt (Copy-Paste to Build)

Use this prompt only if you need a single-turn build. **Preferred method:** do one task item at a time and mark [V] when done (see Build order and verification above).

Use this prompt only for scaffold generation in phases:

```text
Build the MMM app in `mmm/` following `mmm/docs/10_BUILD_MMM.md` Steps 1–8.
Constraint: Be efficient. No explanations. Use phased output and stop for verification after each phase.

phase A core:
- `mmm/src/utils.py`
- `mmm/src/transforms.py`
- `mmm/src/models/base.py`
- `mmm/src/models/ols.py`
- `mmm/src/models/ridge.py`
- `mmm/app.py` (data/config/fit/results skeleton with OLS and Ridge only)

phase B models:
- `mmm/src/models/lasso.py`
- `mmm/src/models/elasticnet.py`
- optional `mmm/src/models/pymc_model.py`

phase C ai:
- required `mmm/src/ai/client.py` for the MVP single-model summary
- optional AI tab enhancements such as compare-all and Q&A

After each phase, run checks before continuing.
Start with phase A.
```

---

Build the complete **interactive** Streamlit MMM app. Data will be provided later via CSV in `mmm/data/` or upload. The app must load, validate, transform, fit models, **allow comparing multiple models**, show results for three decisions, and include an AI single-model executive summary with one provider.

**Run command:** `cd mmm && source .venv/bin/activate && streamlit run app.py`

**Spec refs (optional):** Load only if you need full fidelity (exact schemas, formulas). For a single-file build, this document alone is enough.

| File | What to read it for |
|------|---------------------|
| `AGENT_README.md` | Project constraints, three decisions |
| `docs/DECISIONS_FRAMEWORK.md` | What / Why / What next — design anchor |
| `mmm/docs/01_INDEX.md` | Doc map |
| `mmm/docs/03_ARCHITECTURE.md` | Data → transforms → models → results → AI flow |
| `mmm/docs/04_DATA_MODEL.md` | Input CSV schema, output ModelResult schema |
| `mmm/docs/06_MODELS.md` | Model specs: OLS, Ridge, Lasso, ElasticNet, PyMC |
| `mmm/docs/05_TRANSFORMS.md` | Adstock and saturation formulas |
| `mmm/docs/09_AI_ANALYSIS.md` | Credentials, payload, prompt, Q&A mode |
| `mmm/docs/08_UX_FLOW.md` | Tab layout, Results tab order, AI tab layout |
| `mmm/docs/07_TECHNICAL_SPEC.md` | Stack, module structure, model interface |
| `mmm/docs/11_WIREFRAME_PROMPT.md` | Wireframe prompt — Streamlit-only UI spec; use to generate a wireframe before or alongside build |

---

## Interactivity (required)

The app is a Streamlit app. Every step must be **user-driven and interactive**: file upload or file picker, column selectors, sliders/number inputs for transform params, buttons to apply transforms and to fit models, dropdowns to choose which model(s) to view or compare. Use `st.session_state` to persist data and results so the app reacts to user actions. Do not auto-fit or auto-advance; the user clicks to load data, apply transforms, fit, and view results.

---

## Model comparison (required)

Users must be able to **fit and compare multiple models**. For MVP, implement **OLS** and **Ridge** first. Then add **Lasso**, **ElasticNet**, and **PyMC** as stretch.

- **Fit in series:** When the user clicks "Fit selected" or "Fit all", run the selected models **in series** (sequentially, one after the other). Do not run fits in parallel. Use a fixed order for "Fit all": e.g. OLS → Ridge → Lasso → ElasticNet → PyMC. For each model: show a spinner ("Fitting OLS..."), call `model.fit(...)`, store the result in `session_state["model_results"][model_name]`, show status ("✓ OLS: R² = 0.72, RMSE = 12,450"), then run the next. This ensures deterministic order and clear progress.

- **Comparison between models:** The Results tab must always show **comparison** when at least one model is fitted:
  - **Model comparison table (required):** Rows = model names, columns = R², RMSE (and optionally MAE). Sortable. Shows all fitted models.
  - **Coefficient comparison table (required):** Rows = channel names, columns = model names, cells = coefficient value. Shows how each model estimates each channel. When two or more models are fitted, the user can compare side by side.
  - **Model selector:** A single model can be selected to drive the detail sections below (What is happening? Why? What next? Channel insights, Quick insights). The comparison tables always show **all** fitted models regardless of the selector.

Store results per model in `session_state["model_results"]` keyed by model name (e.g. `"OLS"`, `"Ridge"`, `"PyMC"`). See Step 5 for layout.

---

## Step 1 — Data layer

- [ ] **1.1** Create `mmm/src/utils.py`.

  **1.1a — Type detection and conversion.** Implement `convert_mmm_data(df, date_col, target_col, channel_cols, control_cols) -> pd.DataFrame`. Return a **copy** of the dataframe with these columns converted to the required dtypes. Do not modify the original df.
  - **Date column:** `df[date_col] = pd.to_datetime(df[date_col], errors='coerce')`. Result dtype: `datetime64[ns]`.
  - **Target column:** `df[target_col] = pd.to_numeric(df[target_col], errors='coerce')`. Result dtype: `float64`.
  - **Channel and control columns:** For each col in `channel_cols` and `control_cols`, `df[col] = pd.to_numeric(df[col], errors='coerce')`. Result dtype: `float64`.
  - Return the copy. Downstream code must use this converted df so that dtypes are guaranteed (see 04_DATA_MODEL.md).

  **1.1b — Validation.** Implement `validate_mmm_data(df, date_col, target_col, channel_cols, control_cols=None) -> (bool, list[str], list[str])`. Third return value is a list of **warnings** (e.g. constant-channel); first is success, second is errors. Run validation **on the already-converted** df. Checks (in order, accumulate all errors before returning):
  - Required columns exist (date_col, target_col, all channel_cols).
  - Date column: no non-null check on dtype (assume converted); flag rows where `pd.to_datetime(..., errors='coerce')` produced NaT (i.e. `df[date_col].isna()` after conversion).
  - Target and channel columns are numeric (dtype float or int; after conversion they should be float64). If any value is NaN after conversion, validation fails with one standardized error message and affected row count.
  - No all-null required columns.
  - **Missing values in target or channels:** If `df[target_col].isna().any()` or any `df[ch].isna().any()` for ch in channel_cols, add one error: `"Missing values in target or channel columns — remove or impute rows before modeling. Affected rows: <count>."` (Users need to know the model is fit on complete data; do not drop rows silently.)
  - At least 2 rows (prefer at least 3× the number of parameters — see Step 3.3).
  - **No duplicate dates** — if `df[date_col].duplicated().any()`, add error `"Duplicate dates found — each row must represent a unique time period"`.
  - **No negative values in channel columns** — if any channel value < 0, add error `"Negative values in channel columns — spend must be ≥ 0"`.
  - **Constant or near-constant channels (warning only):** If a channel has zero variance or very low variance (e.g. coefficient of variation &lt; 0.01), append to the **warnings** list: `"Channel X has no (or very low) variance — consider removing or checking data."` Accumulate these; do not fail validation.
  Return `(True, [], warnings)` or `(False, error_messages, [])`. If `control_cols` is None, treat as empty list for presence checks.

- [ ] **1.2** Data tab (wired in Step 7 — do not add tabs here):
  - `st.file_uploader` for CSV.
  - File picker dropdown: use `list(Path("data").glob("*.csv"))` to list files; if the list is empty, show `"No files in data/ yet — use the uploader above."` Do not crash.
  - Load with `pd.read_csv`.
  - **Column selectors:** `date_col` (st.selectbox), `target_col` (st.selectbox), **`channel_cols`** (st.multiselect), **`control_cols`** (st.multiselect, optional).
  - **Channel selection (include / remove):** The channel multiselect lists **candidate columns** (e.g. all CSV columns except `date_col` and `target_col`, or only numeric columns). The user **selects which channels to include** in the model; **deselecting** a column **removes** it from the channel set. At least one channel must be selected. The same logic applies to `control_cols` (optional; zero or more). Make it clear in the UI that users can add or remove channels here (e.g. label: "Channels to include (deselect to remove)").
  - **Editable after load:** Once data is loaded and valid, keep showing the same column selectors pre-filled with current `channel_cols` and `control_cols` so the user can **change the selection** (add or remove channels/controls) without re-uploading. When the user changes channel_cols or control_cols and triggers an update (e.g. a "Update selection" button, or on next run when the multiselect value differs from session_state): re-run `convert_mmm_data` and `validate_mmm_data` with the new selection; on success update `session_state["channel_cols"]` and `session_state["control_cols"]`, set `session_state["transforms_applied"] = False`, and clear `session_state["model_results"]` (and `selected_model` if set). Show a short message: "Channel selection updated — re-apply transforms in Config and re-fit models." This keeps transforms and fits in sync with the current channel set.
  - **Apply conversion:** Call `convert_mmm_data(df, date_col, target_col, channel_cols, control_cols or [])` and use the returned dataframe for all subsequent steps. Do not use the raw loaded df for validation or storage.
  - **Validate:** Call `validate_mmm_data(converted_df, date_col, target_col, channel_cols, control_cols or [])`. Signature returns `(ok, errors, warnings)`. On pass: `st.success` with row count and column list; optionally show a short caption with detected dtypes (e.g. "Date: datetime, Target and channels: float64"). If `warnings` is non-empty, show `st.warning(" ".join(warnings))`. On fail: `st.error(errors)` and do not set `valid` or store state.
  - On validation failure, set `session_state["valid"] = False` if you have previously set it (e.g. user loaded bad data after good data).

- [ ] **1.3** On success:
  - **Sort by date:** `df = df.sort_values(date_col).reset_index(drop=True)` — adstock is order-sensitive.
  - Show parsed date range: `st.caption(f"Date range: {df[date_col].min().date()} to {df[date_col].max().date()} — {len(df)} rows")`.
  - **Grain:** If inferable from date spacing (e.g. median diff between consecutive dates is 1–2 days vs 6–8 days), show "Grain: daily" or "Grain: weekly" in a caption so users know the time unit.
  - **Data preview:** Optionally show a short summary: e.g. `st.dataframe(df[[date_col, target_col] + channel_cols].describe())` or key stats (mean, min, max, null count) for target and channel columns so users can sanity-check before Config.
  - Store in `session_state`: `df` (the **converted and sorted** dataframe, with dtypes datetime64[ns] for date_col and float64 for target and channel/control columns), `date_col`, `target_col`, `channel_cols`, `control_cols`, `valid = True`.
  - If `validate_mmm_data` returned any variance warnings, show `st.warning` with those messages (validation still passes).
  - Downstream: when building `X_transformed` and `y`, ensure numpy arrays are dtype **float64** (e.g. `y = df[target_col].values.astype(np.float64)`).
  - Fit tab is gated on `valid` and `transforms_applied` — see Step 7.3.

- [ ] **Check (Step 1):** Run the app; open Data tab; upload/select CSV; pick date/target/channels; click validate.
  - DoD:
    - `session_state["valid"] == True` on valid input
    - success message includes row count and selected columns
    - date range caption is visible
    - on invalid input, `session_state["valid"] == False` and error message is explicit
  - Mark [V] and proceed to Step 2.

---

## Step 2 — Transforms

- [ ] **2.1** In `mmm/src/transforms.py`: `geometric_adstock(x, theta)` with `x_transformed[t] = x[t] + theta * x_transformed[t-1]`, `x_transformed[0] = x[0]`. Implement geometric only — Weibull is documented in 05_TRANSFORMS.md for reference but not required for the hackathon build.
- [ ] **2.2** Same file: `hill_saturation(x, alpha, k)` = `x^alpha / (k^alpha + x^alpha)`; safe for zeros (if k=0 return zeros). Implement also `log_saturation(x)` = `np.log1p(x)` for per-channel saturation type `"log"`.
- [ ] **2.3** Same file: `transform_media(...)`. **Input types:** `df` must have date_col as datetime and channel/control columns as float64. **Output types:** Return a 2D numpy array with dtype **float64**, shape `(n_rows, n_channels + n_controls)`. Internally use float64 for all adstock/saturation math so the returned array is float64.
  - `adstock_type`: `dict[str, str]` — per channel, `"geometric"` or `"none"`.
  - `saturation_type`: `dict[str, str]` — per channel, `"log"`, `"hill"`, or `"none"`.
  - For each channel: (1) if `adstock_type[ch] == "geometric"` apply `geometric_adstock(x, adstock_params[ch])`, else use raw column; (2) if `saturation_type[ch] == "hill"` apply `hill_saturation(x, saturation_params[ch]["alpha"], saturation_params[ch]["k"])`, elif `"log"` apply `log_saturation(x)`, else pass through. If `control_cols` is provided, append those raw columns to the right. Return 2D numpy array shape `(n_rows, n_channels + n_controls)`, **dtype float64**. Column order: channels first (matching `channel_cols`), then controls.
- [ ] **2.4** Config tab:
  - **Transform type (per channel)** — for each channel: `st.selectbox("Adstock", ["Geometric", "None"], key=f"adstock_type_{ch}")` and `st.selectbox("Saturation", ["Log", "Hill", "None"], key=f"saturation_type_{ch}")`. Store in `session_state["adstock_type"]` and `session_state["saturation_type"]` as `dict[str, str]` with lowercase values (`"geometric"`, `"none"`, `"log"`, `"hill"`, `"none"`). Defaults: every channel `"geometric"` and `"log"` — when building the Config UI, if a channel is not yet in these dicts (e.g. after first load), set that channel to `"geometric"` and `"log"`.
  - **Transform params** — for each channel in `channel_cols`: show theta slider only if `adstock_type[ch] == "geometric"` (0.1–0.9, step 0.05). Show alpha and k inputs only if `saturation_type[ch] == "hill"`; k default = `max(df[ch].median(), df[ch].max() * 0.1, 1.0)`. **Rationale:** In the UI or a tooltip, add a one-line note: "Recommended starting point for spend is Geometric adstock + Log saturation." Add a second note: "Default k = max(median, 10% of max, 1) places half-saturation near typical spend levels; adjust if your spend range is very different." For theta: "Typical range 0.1–0.9: higher = longer carryover. Use prior campaigns or category benchmarks if available." For "log" or "none" saturation, alpha/k are not used (store a placeholder in saturation_params for hill-only use in Results, or store `None` and skip in channel insights for non-hill).
  - **Bulk defaults (optional):** Add optional buttons or controls: "Set all channels to same adstock type", "Set all to same saturation type", "Set all theta to X" so users with many channels can apply one value without repetitive clicking.
  - **Regularization params** — `st.number_input` for Ridge/Lasso alpha (default 1.0), ElasticNet l1_ratio (default 0.5); store as `session_state["reg_alpha"]`, `session_state["l1_ratio"]`; these are used in Step 3.4
  - Button **"Apply transforms"**: call `transform_media(df, channel_cols, adstock_params, saturation_params, adstock_type=session_state["adstock_type"], saturation_type=session_state["saturation_type"], control_cols=control_cols)`, store:
    - `session_state["X_transformed"]` — 2D numpy array, shape `(n_rows, n_channels + n_controls)`, **dtype float64**
    - `session_state["y"]` — 1D numpy array, shape `(n_rows,)`, **dtype float64** (e.g. `df[target_col].values.astype(np.float64)`)
    - `session_state["adstock_params"]` — `dict[str, float]`, e.g. `{"tv_spend": 0.5, "digital_spend": 0.3}`
    - `session_state["saturation_params"]` — `dict[str, dict]` where each inner dict has `{"alpha": float, "k": float}` for hill channels; for log/none use e.g. `{"alpha": 1.0, "k": 0.0}` or omit and handle in Results when drawing curves (only draw Hill curve when saturation_type[ch] == "hill")
    - `session_state["adstock_type"]` — `dict[str, str]`
    - `session_state["saturation_type"]` — `dict[str, str]`
    - `session_state["transforms_applied"] = True` and `session_state["transform_fingerprint"] = <stable hash of channel_cols + control_cols + adstock_type + saturation_type + adstock_params + saturation_params>`
    - If the new fingerprint differs from the previous fingerprint: clear `session_state["model_results"]`, clear `session_state["selected_model"]`, and show `st.warning("Transforms changed — previously fitted models have been cleared. Re-fit your models.")`.
    - If only regularization params (`reg_alpha`, `l1_ratio`) changed and the fingerprint is unchanged: do not clear `model_results`; show `st.info("Only regularization changed. Re-fit in the Fit tab to update models with new alpha/l1_ratio.")`.

- [ ] **Check (Step 2):** With valid data loaded, open Config tab and click "Apply transforms".
  - DoD:
    - `session_state["X_transformed"]` exists and is float64 2D array
    - `session_state["y"]` exists and is float64 1D array
    - `session_state["transforms_applied"] == True`
    - fingerprint is stored and stale model clearing logic behaves as specified
  - Mark [V] and proceed to Step 3.

---

## Step 3 — Models (base + frequentist)

- [ ] **3.1** Create `mmm/src/models/__init__.py` (exports).
- [ ] **3.2** Create `mmm/src/models/base.py`. Copy the exact `ModelResult` dataclass from 06_MODELS.md — use that file as the single source of truth for field names and types.

  **Model interface** (all models implement this):
  ```
  fit(X: np.ndarray, y: np.ndarray, raw_spend: dict[str, np.ndarray], **kwargs) -> ModelResult
  predict(X: np.ndarray) -> np.ndarray
  ```
  The `raw_spend` kwarg is a dict mapping channel_name → 1D array of raw (untransformed) spend values. It is needed to compute **cost per lead (CPL)**. Pass it from session_state: `raw_spend = {ch: df[ch].values for ch in channel_cols}`.

  **CPL and attribution formula (use identically in every model). Target = leads; success metric = cost per lead.**
  ```python
  # contribution[ch] is a VECTOR — one attributed leads value per time period
  contribution = {}
  for i, ch in enumerate(channel_names):
      contribution[ch] = coefficients[ch] * X[:, i]          # shape: (n_rows,)

  cpl = {}
  for ch in channel_names:
      attr_leads = contribution[ch].sum()
      raw_total = raw_spend[ch].sum()
      cpl[ch] = raw_total / attr_leads if attr_leads > 0 else float("inf")   # € per lead

  y_pred_total = y_pred.sum() if y_pred.sum() != 0 else 1.0

  contribution_pct = {}
  for ch in channel_names:
      contribution_pct[ch] = contribution[ch].sum() / y_pred_total

  baseline = y_pred - sum(contribution[ch] for ch in channel_names)
  baseline = np.clip(baseline, 0, None)                      # clip negatives
  baseline_pct = baseline.sum() / y_pred_total
  ```

  Store all fields in ModelResult including `contribution` as `dict[str, np.ndarray]` (the full vector, not just the sum). Use **`cpl`** (cost per lead), not roi. If clipping occurs, the decomposition won't exactly sum to y_pred — acceptable for hackathon display. **Set `channel_names` to the list of channel names in the same order as the first n_channels columns of X** (i.e. `channel_cols` from session_state). Contribution and coefficients are defined **only for channels**; when controls exist, their effect is part of baseline (y_pred - sum of channel contributions).

- [ ] **3.3** Create `mmm/src/models/ols.py`: use `statsmodels.api.OLS`.
  - **Ensure X is 2D**: `if X.ndim == 1: X = X.reshape(-1, 1)` before any operation — avoids `sm.add_constant` adding the constant in the wrong axis for single-channel data.
  - Add constant: `X_with_const = sm.add_constant(X, has_constant='add')`. The `has_constant='add'` flag forces a constant even if one column is all-ones.
  - **Warn if underdetermined**: if `len(y) < 3 * X_with_const.shape[1]`, show `st.warning(f"Only {len(y)} rows for {X_with_const.shape[1]} parameters — model may be overfit. Add more data for reliable results.")`. Still proceed.
  - Fit: `result = sm.OLS(y, X_with_const).fit()`. Intercept = `result.params[0]`. **Coefficient order:** X columns are channels then controls; so channel coefficients = `result.params[1:1+n_channels]` where `n_channels = len(channel_names)`. Control coefficients (if any) = `result.params[1+n_channels:]`. Build the `coefficients` dict only for channel names (keys = channel_names, values = params[1:1+n_channels]). Baseline = y_pred - sum(contribution[ch]) absorbs intercept, control effects, and residual.
  - Compute cpl, contribution, contribution_pct, baseline using the formula in Step 3.2 (with zero-division guards and clipping). When `attr_leads <= 0` (negative contribution), set `cpl[ch] = float("inf")` and in the UI show "—" or "N/A" for that channel's CPL.
  - `r_squared = result.rsquared`, `rmse = np.sqrt(np.mean(result.resid**2))`. Return ModelResult.
- [ ] **3.4** Create `mmm/src/models/ridge.py`, `lasso.py`, `elasticnet.py` with sklearn. **Reproducibility:** Use a fixed `random_state` (e.g. `random_state=42`) in the model constructor where supported so the same data and config produce the same results. Accept `alpha` (and `l1_ratio` for ElasticNet) from kwargs — passed from `session_state["reg_alpha"]` and `session_state["l1_ratio"]`. sklearn does not add a constant automatically — use `fit_intercept=True` (default). After fit: `intercept = model.intercept_`. **Coefficient order:** `model.coef_` has length = n_columns(X); first `n_channels` are channel coefficients, rest are control coefficients. So `coefficients = { ch: model.coef_[i] for i, ch in enumerate(channel_names) }`. Do not scale X or y; alpha is on the raw scale. Compute cpl, contribution, contribution_pct, baseline with the same formula as OLS. For r_squared use `model.score(X_transformed, y)` (same X and y as fit); for rmse use `np.sqrt(np.mean((y - model.predict(X_transformed))**2))`. For negative contribution, set cpl[ch] to inf and display as "—" or "N/A" in the UI.
- [ ] **3.5** Fit tab: **Interactive.** Show a warning and return early if `not session_state.get("transforms_applied")`: `"Apply transforms in the Config tab first."` MVP model selector shows `OLS` and `Ridge` first. Stretch models (`Lasso`, `ElasticNet`, `PyMC`) should only appear after their files exist, or be clearly labeled optional. Buttons: "Fit selected" and "Fit all".

  **Run models in series:** When the user clicks "Fit selected" or "Fit all", run the selected models **in series** (one after the other, sequentially). Do not run fits in parallel. Use a fixed order: e.g. for "Fit all" run OLS, then Ridge, then Lasso, then ElasticNet, then PyMC (or the order of the multiselect for "Fit selected"). For each model in turn: show `st.spinner("Fitting [name]...")`, read `X_transformed` and `y` from session_state (both float64), build `raw_spend = {ch: df[ch].values for ch in channel_cols}`, call `model.fit(X_transformed, y, raw_spend=raw_spend, **reg_params)`, store result in `session_state["model_results"][model_name]`, set `model_name` on the ModelResult to the same key, show status ("✓ OLS: R² = 0.72, RMSE = 12,450"), then proceed to the next model.   **Reproducibility:** When storing each result, also store a **model fitted timestamp**: e.g. `session_state["model_fitted_at"] = datetime.now().isoformat()` (single timestamp for last fit) or per-model `session_state["model_results_meta"][model_name]["fitted_at"] = ...`. Display "Model fitted on: &lt;date/time&gt;" (or "Data as of: &lt;max date in df&gt;") in the Results tab so reports are auditable. Results tab is enabled when `session_state.get("model_results")` is non-empty.

- [ ] **Check (Step 3):** With transforms applied, open Fit tab and run OLS (and Ridge for MVP).
  - DoD:
    - spinner appears during fit
    - status line shows model name, R², RMSE
    - `session_state["model_results"]` has the fitted model keys
    - Results tab is unlocked
  - Mark [V] and proceed to Step 4.

---

## Step 4 — PyMC (day 2 stretch)

- [ ] **4.1** Create `mmm/src/models/pymc_model.py`. Implement as a Bayesian linear regression using PyMC with the following priors and sampler settings:
  - **Reproducibility:** Use a fixed `random_seed` (e.g. `random_seed=42`) in `pm.sample(...)` so the same data and config produce the same posterior.
  - **Column order:** X has shape (n, n_channels + n_controls). Define one coefficient per column; first n_channels are channel coefficients, rest are control coefficients. Use the same `channel_names` and column order as in OLS/sklearn.
  - **Priors:** Intercept: `Normal(mu=y.mean(), sigma=y.std())`. Channel coefficients: `HalfNormal(sigma=y.std())` for each channel (positive-only; media should not have negative effect). **Control coefficients** (if n_controls > 0): use `Normal(0, y.std())` so they can be positive or negative. Noise (sigma): `HalfNormal(sigma=y.std())`.
  - Likelihood: `Normal(mu=intercept + X @ coefficients, sigma=sigma, observed=y)`.
  - Sampler fast default: `pm.sample(draws=300, chains=1, tune=200, progressbar=False, return_inferencedata=True, random_seed=42)`.
  - Full run optional toggle: `draws=1000, chains=2, tune=500`.
  - **Posterior:** Extract posterior mean and 94% HDI for each coefficient (e.g. from `az.summary` or `pm.stats.hdi(..., hdi_prob=0.94)`). Build `coefficients`, `coefficient_lower`, `coefficient_upper` for **channel** indices only (same as OLS).
  - **CPL HDI:** For each channel, for every posterior draw compute total attributed leads = `(coef_draw[ch] * X[:, ch_idx]).sum()`; then `cpl_draw = raw_spend[ch].sum() / attributed_leads_draw` (if attributed_leads_draw <= 0 use inf). Set `cpl_lower[ch]` = 2.5th percentile of cpl_draws, `cpl_upper[ch]` = 97.5th percentile. Equivalently: get 94% HDI of (sum of contribution[ch] over time) per channel; then cpl_lower = spend / contribution_upper, cpl_upper = spend / contribution_lower.
  - **R² and RMSE:** Use posterior mean of intercept and coefficients to compute y_pred_mean; then r_squared = 1 - SS_res/SS_tot, rmse = sqrt(mean((y - y_pred_mean)**2)). Return ModelResult with coefficient/CPL posterior means and HDI bounds (`cpl_lower`, `cpl_upper`).

- [ ] **4.2** Fit tab: when PyMC is selected (among others), show `st.info("PyMC is optional and slower than OLS/Ridge. Use for deeper analysis after MVP.")`. On "Fit selected" / "Fit all", run PyMC like other models and store in `session_state["model_results"]["PyMC"]`.

- [ ] **Check (Step 4):** Optional stretch check. Select PyMC in Fit tab and run fit.
  - DoD:
    - PyMC completes in fast mode without crashing the app
    - result stores coefficient and CPL intervals
  - Mark [V] and proceed to Step 5.

---

## Step 5 — Results tab (three decisions + model comparison)

- [ ] **5.1** Results tab: if `session_state.get("model_results")` is empty, show `"Fit at least one model in the Fit tab to see results."` and return.
- [ ] **5.2** **Model selector:** `st.selectbox("View model:", list(session_state["model_results"].keys()))`. Store selected model name in `session_state["selected_model"]`. All detail sections below (What is happening? Why? What next? Channel insights, Quick insights) use the selected model's ModelResult.
- [ ] **5.3** **Comparison between models (required):** Always show both comparison tables when at least one model is fitted.
  - **Model comparison table:** `st.dataframe` with rows = model names (all keys in `model_results`), columns = R², RMSE, and optionally **MAE** (mean absolute error) and **MAPE** (mean absolute percentage error; only when target has no zeros so division is safe). Sortable. MAE and MAPE are on the same scale as y (leads). Shows every fitted model so the user can compare fit across models.
  - **Coefficient comparison table:** `st.dataframe` with rows = channel names, columns = model names (all fitted), cells = coefficient value. Add a second table or toggle: **CPL comparison** (rows = channels, columns = models, cells = CPL €/lead) so users can compare in business units.
  Both tables are always visible and show **all** fitted models; the model selector only affects the detail sections below, not the comparison tables.
  - **Export (day 2 stretch):** Add a button "Export comparison" or "Download CSV" that lets the user download the model comparison table (R², RMSE, MAE, MAPE) and the coefficient/CPL comparison table as CSV for reporting and tracking.
  - **Holdout note:** Show a short note: "All reported R², RMSE, and attribution are in-sample. For out-of-sample validation (e.g. time-based holdout), use a separate workflow or future enhancement."
- [ ] **5.4** Section **"What is happening?"** (for selected model): three `st.metric` cards — Total media contribution (attributed leads, formatted), **Top channel by CPL** (name + €X per lead — **lowest** CPL is best), Model fit (R² = X, RMSE = Y). Optionally show the **model fitted timestamp** (or "Data as of: &lt;max date&gt;") here or above the comparison tables.
- [ ] **5.5** Section **"Why is it happening?"** (for selected model): `st.dataframe` — base columns: Channel, Coefficient, **CPL (€ per lead)**, Contribution (leads), Share (%). **CPL display:** When formatting CPL for display, if value is `math.isinf(cpl)` or very large, show `"—"` or `"N/A"` instead of the raw number. Optionally add **Share of actual**: `sum(contribution[ch]) / sum(y_actual)` so users can compare model attribution to the real total. Only add Coeff CI (lower–upper) and **CPL CI** columns if `hasattr(result, "coefficient_lower")` — i.e. only when the selected model is PyMC. For non-PyMC models these fields do not exist and must not be shown. Below the table, use `st.bar_chart` for **CPL by channel**: create a dataframe with channel names as index and CPL as values, **sort ascending** (best/lowest CPL first).
- [ ] **5.6** Section **"What should leadership do next?"** (for selected model): three bullet points — (1) `"Invest more in [lowest CPL channel] — currently €X per lead"`, (2) `"Reduce spend on [highest CPL channel] — €X per lead"`, (3) `"Reallocate [N]% of [highest CPL channel] budget to [lowest CPL channel] — directional heuristic based on current modelled CPL"`. Compute the reallocation % as `min(50, round((cpl_worst - cpl_best) / cpl_worst * 100))` (relative CPL improvement if shifting spend from worst to best). Add a short note that this is a directional recommendation, not a forecast.

- [ ] **Check (Step 5):** With at least one model fitted, open Results tab.
  - DoD:
    - model comparison table renders for all fitted models
    - coefficient comparison table renders for all fitted models
    - the three decision sections render with numeric values
    - if stretch sections are not implemented yet, tab still works without errors
  - Mark [V] and proceed to Step 6.

---

## Step 5.7 — Channel insights (per-channel deep dive)

Add a **"Channel Insights"** section inside the Results tab, below the three decision sections. Wrap the entire section in `st.expander("Channel Insights", expanded=False)` — collapsed by default to keep the tab readable. It renders for the currently selected model.

- [ ] **5.7.1** Leads decomposition chart: Use `st.area_chart`. Create a dataframe where the index is the date column, and columns are the `contribution` vectors for each channel plus the `baseline` vector. This will automatically stack them. This answers "where do leads come from week by week?"
- [ ] **5.7.2** Per-channel breakdown cards: For each channel in `channel_cols`, show a compact card or expander with:
  - Spend total over the period and average weekly spend
  - Attributed contribution (absolute and %) from the model (in **leads**)
  - **CPL** (€ per lead, from ModelResult)
  - **Transform types** (from session_state): Adstock: [Geometric (θ=X) | None], Saturation: [Hill (α, k) | Log | None]
  - **Adstock carryover:** when adstock_type[ch] == "geometric", compute weeks until effect decays to 5% using `round(-log(0.05) / -log(theta))`; when "none", show "No carryover". Edge cases: if theta <= 0 show "No carryover"; if theta >= 1.0 show "Indefinite carryover (theta ≥ 1)". Otherwise "Effect lasts ~N weeks after spend stops"
  - **Saturation status:** when saturation_type[ch] == "hill", compare average weekly spend to k and label under-saturated / near saturation / over-saturated with badge (green/amber/red). When "log" or "none", show "N/A" or "Log saturation" / "No saturation".
- **5.7.3 Saturation curves:** For each channel with **saturation_type[ch] == "hill"**, use `st.line_chart` showing the Hill curve (x = spend 0 to 2× max, y = response). For channels with saturation_type "log", optionally show a simple log(1+x) curve or a short note "Saturation: Log". For "none", show "No saturation curve" or omit.

> These charts are computed from ModelResult and the transform parameters stored in `session_state` (adstock_params, saturation_params, adstock_type, saturation_type). No additional model fitting required.

---

## Step 5.8 — Quick Insights (auto-answered from model results)

- [ ] **5.8** Add the Quick Insights section: at the bottom of the Results tab, wrap in `st.expander("Quick Insights", expanded=False)` — collapsed by default since the key information is already shown above. Users open it for a compact summary view.

Display as a 2-column grid of `st.metric` / `st.info` cards. For the currently selected model, use `sum(y_pred)` as the denominator for all percentage calculations (not actual y — the model's attribution adds up to y_pred for internal consistency). **Target = leads; success metric = cost per lead (CPL).**

| Card | How to compute |
|------|----------------|
| Overall marketing CPL | `sum(df[channel_cols].sum(axis=0)) / sum(all channel contributions)` — € per lead (guard: if total attributed leads is 0, show "N/A") |
| Best channel | `min(cpl.items(), key=lambda x: x[1])` — show `"{name}: €{X} per lead"` (lowest CPL) |
| Worst channel | `max(cpl.items(), key=lambda x: x[1])` — show `"{name}: €{X} per lead"` with red colouring if CPL is very high (e.g. above 2× median CPL) |
| Media vs baseline | `sum(channel_contributions) / sum(y_pred)` vs `sum(baseline) / sum(y_pred)` — show as two `st.metric` side by side |
| Over-saturated channels | List channels where saturation_type[ch]=="hill" and saturation_status == "over-saturated" (from Step 5.7.2); if none, show "None — all channels within range" |
| Recommended shift | Lowest CPL channel + highest CPL channel + reallocation % (from Step 5.6 formula) |

If a value can't be computed (e.g. spend data missing), show `"N/A"` in the card. When CPL is infinite or very large, display `"—"` or `"N/A"` instead of the raw number.

---

## Step 6 — AI summary (required for MVP)

`mmm/src/ai/__init__.py` already exists (placeholder). Create `mmm/src/ai/client.py`.

Full spec: [09_AI_ANALYSIS.md](09_AI_ANALYSIS.md). Summary of what to implement:

- [ ] **6.1** — Credential loading (`load_credentials()`):
Try in this order, use the first that works:
1. Read credentials from **app root**: resolve path relative to the app (e.g. `Path(__file__).resolve().parent / "credentials.json"` when in `app.py` or the ai client, so it works when run as `streamlit run app.py` from `mmm/`). Parse `preferred_provider`, `openai_api_key` / `anthropic_api_key`, `openai_model` / `anthropic_model`.
2. Fall back to env vars `OPENAI_API_KEY` / `ANTHROPIC_API_KEY`
3. Fall back to a key passed in by the caller (sidebar input)
Return `(provider, api_key, model)` or raise a clear error message if nothing found.

- [ ] **6.2** — Build the analysis payload (`build_payload(model_result, session_state)`):
Construct a dict with: `model_name`, `date_range`, `target_metric` (use `"leads"`), `n_weeks`, `model_fit` (r_squared, rmse), `channels` (list of name/coefficient/**cpl**/contribution_pct), `controls` (list of name/coefficient/contribution_pct for non-media variables), `baseline_pct`, `top_channel` (lowest CPL), `bottom_channel` (highest CPL). If multiple models are fitted, add `comparison_table`.

**Token optimization:**
- Round all float values to 2 decimal places.
- Exclude any optional fields that are None.
- Convert numpy types to Python native types (float/int) for clean JSON serialization.

See 09_AI_ANALYSIS.md for the full payload schema.

- [ ] **6.3** — ICE prompt (`build_prompt(payload)`):
Assemble the prompt using ICE structure (see 09_AI_ANALYSIS.md):
- Instructions: senior analyst, C-suite audience, direct, use numbers
- Context: model name, date range, target metric, n_weeks
- Example: one short input→output example
- Task: the payload serialized as JSON
Request four output sections: Executive summary, Top finding, Recommendation (with numbers), Confidence note.

- [ ] **6.4** — `get_summary(payload, provider, api_key, model)` function:
Call OpenAI or Claude with the assembled prompt. Return the response text. On any error (rate limit, bad key, network), return a human-readable error string — never raise. See 09_AI_ANALYSIS.md for error handling rules.

- [ ] **6.5** — AI tab:

Load credentials on tab open (`load_credentials()`); if none found, show `"Add credentials.json or set an API key in the sidebar to enable AI analysis."` with a `st.sidebar.text_input` as override. Provider radio (OpenAI / Anthropic) pre-set from `preferred_provider`. Enable tab only when `session_state.get("model_results")` is non-empty; otherwise show `"Fit at least one model first."` and return.

The selected model for Section A is read from `session_state.get("selected_model")`. If this is None (user hasn't visited the Results tab yet), default to `list(session_state["model_results"].keys())[0]`.

The AI tab has two sections:

**Section A — Executive summary:**
- MVP path: start with **Single model** mode only.
- Day 2 stretch: add **Compare all** mode (uses comparison table if multiple models fitted).
- "Generate summary" button: call `build_payload` → `build_prompt` → `get_summary`; display result in `st.markdown`. See 09_AI_ANALYSIS.md for the ICE prompt and output format.

**Section B — Business Q&A (day 2 stretch):**
The user can ask natural-language questions about the model results and channels. The LLM answers using the model results payload as context.

Implement as:
- A dropdown (`st.selectbox`) with pre-built question templates — pre-loaded so the user can select and ask without typing:
  1. "What is our overall marketing cost per lead and how does it compare across channels?"
  2. "Which channel should we increase spend on and by how much?"
  3. "Which channels are saturated and should we cut?"
  4. "How long do the effects of each channel last after we stop spending?"
  5. "How does this model compare to the other fitted models?"
  6. "What would happen if we reallocated 20% of budget from the weakest to the strongest channel?"
  7. "Write a 3-bullet point summary I can present to the board in 30 seconds."
- A free-form `st.text_area` for custom questions (user can type anything or edit the selected template)
- "Ask" button: append the user's question to the results payload prompt; call `get_summary`; display answer below in `st.markdown`
- Render a fixed-height scrollable history area using `st.container` — iterate over `session_state["qa_history"]` and render each entry: question in `st.markdown("**Q:** ...")`, answer in `st.markdown("A: ...")`, model label in `st.caption`. Render this container BEFORE the question input so history is above and the input stays at the bottom of the section.
- Store each answer as a **dict** in `session_state["qa_history"]`:
  ```python
  {"question": str, "answer": str, "model": str, "timestamp": str}
  ```
  Do not use a plain tuple — key-based access is safer and clearer than positional indexing. Cap history at 15 entries: when `len(qa_history) >= 15`, pop `qa_history[0]` before appending. Add a `[Clear history]` button that sets `session_state["qa_history"] = []`.

- [ ] **Check (Step 6):** With credentials set, open AI tab and click "Generate summary".
  - DoD:
    - summary response renders in markdown
    - failures show user-friendly error text without breaking other tabs
    - if Q&A stretch is implemented, answers appear and are stored in history
  - Mark [V] and proceed to Step 7.

---

## Step 7 — App shell

`mmm/app.py` is currently a placeholder (comment only). Replace its entire contents with the full app. **This is where tabs are created — not in Step 1.**

- [ ] **7.1** `st.set_page_config(page_title="MMM — Marketing Mix Modeling", layout="wide")`. `st.title("Marketing Mix Modeling")`. `st.caption("Load data → configure transforms → fit models → view results")`.
- [ ] **7.2** `tab_data, tab_config, tab_fit, tab_results, tab_ai = st.tabs(["Data", "Config", "Fit", "Results", "AI"])`. Render each section inside its tab using `with tab_data:` etc.
- [ ] **7.3** Tab gating — use `if/else` inside each `with tab_X:` block. **Do NOT use `st.stop()` inside tab blocks** — it stops the entire script and prevents all subsequent tabs from rendering.

  Correct pattern for every gated tab:
  ```
  with tab_config:
      if not st.session_state.get("valid"):
          st.warning("Load and validate data in the Data tab first.")
      else:
          # ... all Config content here

  with tab_fit:
      if not st.session_state.get("transforms_applied"):
          st.warning("Apply transforms in the Config tab first.")
      else:
          # ... all Fit content here

  with tab_results:
      if not st.session_state.get("model_results"):
          st.info("Fit at least one model in the Fit tab to see results.")
      else:
          # ... all Results content here

  with tab_ai:
      if not st.session_state.get("model_results"):
          st.info("Fit at least one model first to enable AI analysis.")
      else:
          # ... all AI content here
  ```
- [ ] **7.4** Imports at the top of app.py for MVP: `from src.utils import validate_mmm_data`, `from src.transforms import transform_media`, `from src.models.ols import OLSModel`, `from src.models.ridge import RidgeModel`, `from src.ai.client import load_credentials, build_payload, build_prompt, get_summary`. Add `LassoModel`, `ElasticNetModel`, and `PyMCModel` imports only when those files are implemented, or load them lazily behind feature checks. Run from `mmm/` so relative imports resolve.

- [ ] **Check (Step 7):** Run `streamlit run app.py` from `mmm/`.
  - DoD:
    - all five tabs render
    - gated tabs show guidance messages instead of tracebacks
    - end-to-end MVP walk-through succeeds: load data -> apply transforms -> fit OLS/Ridge -> view Results
  - Mark [V].

---

## Step 8 — Data and validation

- [ ] **8.1** Ensure the app supports **CSV upload** and/or **files in `mmm/data/`** (file picker). Validation must follow 04_DATA_MODEL.md. Show **clear errors** when date, target, or channel columns are missing or invalid (use the messages from `validate_mmm_data`).

- [ ] **Check (Step 8):** Test one invalid CSV and one valid CSV.
  - DoD:
    - invalid CSV shows explicit validation error text and does not set `valid=True`
    - valid CSV sets `valid=True`, shows date range, and enables Config tab flow
  - Mark [V].
