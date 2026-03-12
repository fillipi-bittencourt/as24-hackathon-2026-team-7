# UX Flow

## Screen Structure (sidebar step menu)

| Step | Purpose | Enabled when |
|------|---------|--------------|
| Data | Load, preview, validate input CSV | Always |
| Config | Transform params + regularization hyperparams | Data valid |
| Priors | Bayesian prior settings and sampler controls | Data valid |
| Info | MMM explainer for models, transforms, and output interpretation | Always |
| Fit | Select models, run fit, view fit status | Transforms applied |
| Results | Model comparison, validation, three decisions, channel insights, quick insights | ≥1 model fitted |
| AI | Analysis generation, provider setup, and AI exports | ≥1 model fitted |

The sidebar step menu is always visible. Navigation uses a vertical list of sidebar buttons. Gating is done by showing a message inside each section using `if/else`.

---

## User Journey

1. **Data** — Upload CSV or select from `data/`; select date_col, target_col, **channels to include** (multiselect — add/remove channels as needed); validate; preview. Channel selection can be edited after load (deselect to remove a channel); changing it re-validates and resets transforms and fits.
2. **Config** — Per-channel: select **adstock type** (Geometric / None) and **saturation type** (Log / Hill / None); set theta (if geometric), alpha/k (if hill); set regularization alpha and l1_ratio; click "Apply transforms". Recommended defaults: **Geometric + Log**
3. **Priors** — Choose the PyMC prior settings and sampler controls before fitting the Bayesian model
4. **Info** — Review model, transform, and interpretation guidance before fitting if needed
5. **Fit** — Select models and fit them one by one or all at once; spinner and status line shown per model
6. **Results** — Model selector at top; display period selector; variable filter; comparison tables; validation diagnostics; three decision sections; exports; expandable Channel Insights; expandable Quick Insights
7. **AI** — Provider setup; analysis depth selector; optional multi-model context; generated analysis; AI exports

---

## Session State (key values, in order of creation)

| Key | Type | Set in | Used in |
|-----|------|--------|---------|
| `df` | `pd.DataFrame` | Data tab | Config, Fit, Results, AI |
| `date_col` | `str` | Data tab | Config, Results |
| `target_col` | `str` | Data tab | Config, Fit |
| `channel_cols` | `list[str]` | Data tab | Config, Fit, Results |
| `control_cols` | `list[str]` | Data tab | Config (passed to transform_media) |
| `valid` | `bool` | Data tab | Config gate |
| `X_transformed` | `np.ndarray` shape `(n, n_ch+n_ctrl)` float64 | Config tab | Fit |
| `y` | `np.ndarray` shape `(n,)` float64 | Config tab | Fit, Results |
| `adstock_params` | `dict[str, float]` channel→theta | Config tab | Results (channel insights) |
| `adstock_type` | `dict[str, str]` channel→"geometric" \| "none" | Config tab | Results (channel insights) |
| `saturation_params` | `dict[str, dict]` channel→`{"alpha": float, "k": float}` (hill only) | Config tab | Results (saturation curves) |
| `saturation_type` | `dict[str, str]` channel→"hill" \| "log" \| "none" | Config tab | Results (channel insights, curves) |
| `reg_alpha` | `float` | Config tab | Fit (Ridge/Lasso) |
| `l1_ratio` | `float` | Config tab | Fit (ElasticNet) |
| `transforms_applied` | `bool` | Config tab | Fit gate |
| `transform_fingerprint` | `str` | Config tab | Config, Fit, Results |
| `pymc_prior_config` | `dict[str, Any]` | Priors tab | Fit |
| `pymc_sampler_config` | `dict[str, Any]` | Priors tab | Fit |
| `pymc_prior_signature` | `str` | Priors tab | Priors, Fit, Results |
| `model_results` | `dict[str, ModelResult]` | Fit tab | Results, AI |
| `model_results_meta` | `dict[str, dict]` | Fit tab | Results |
| `selected_model` | `str` (model name key) | Results tab | AI tab |
| `selected_visual_channels` | `list[str]` | Results tab | Results tab |
| `show_baseline_visual` | `bool` | Results tab | Results tab |
| `results_period` | `str` | Results tab | Results tab |

---

## Key Interactions

| Interaction | Detail |
|-------------|--------|
| File picker | Shows CSV files from `mmm/data/`; if empty shows "No files yet — use uploader" |
| Column selectors | date_col (selectbox), target_col (selectbox), **channel_cols** (multiselect — select which channels to include; **deselect to remove**; ≥1 required), **control_cols** (multiselect, optional). After load, user can change channel/control selection without re-uploading; app re-validates and resets transforms + model results |
| Transform sliders | Per channel: **Adstock type** (Geometric / None), **Saturation type** (Log / Hill / None); then theta slider (if geometric), alpha/k inputs (if hill); recommended defaults are Geometric + Log |
| Priors form | Intercept mean mode, intercept sigma scale, channel prior family, channel sigma scale, control sigma scale, noise sigma scale, draws, tune, chains |
| Reg params | Alpha input for Ridge/Lasso; alpha + l1_ratio for ElasticNet; stored in session_state |
| Apply transforms | Validates inputs, runs transform_media, sets transforms_applied = True, stores `transform_fingerprint`, and clears stale fits when transform-defining settings change |
| Save priors | Stores the PyMC prior settings and clears only the stale PyMC result if those settings changed |
| Model multiselect | OLS, Ridge, Lasso, ElasticNet, and PyMC are available |
| Fit buttons | "Fit selected" + "Fit all"; spinner per model; R² shown after each |
| Sidebar step menu | Vertical list of sidebar buttons — one button per step, current step highlighted, readiness shown in the label |
| Model selector (Results) | Selectbox — switches all sections; stored as selected_model in session_state |
| Display period | Selectbox — `All data`, `Last 4 weeks`, `Last 8 weeks`, `Last 12 weeks`, `Last 26 weeks` |
| Variable filter | Multiselect — controls which channels appear in tables and charts |
| Baseline toggle | Checkbox — includes or hides baseline and unexplained portions in visuals |
| Comparison tables | Always show all fitted models; model selector only affects detail sections below |
| Channel Insights | st.expander collapsed by default — opens on demand |
| Quick Insights | st.expander collapsed by default — compact summary, open on demand |
| Results export | Download current results view as CSV and PDF |
| AI analysis | "Generate analysis" button — uses selected model and optional cross-model context |
| AI exports | Download analysis as CSV and PDF |

Hard rule:
- If channel/control selection or transform settings change, clear `model_results` and `selected_model`
- If only regularization changes, keep results visible but require re-fit
- If only PyMC prior settings change, clear only the `PyMC` result and keep the other fitted models

---

## Results Step Layout (in order, top to bottom)

```text
[Model selector]
[Display period]
[Variables shown in charts]
[Show baseline and unexplained portion]

Model comparison
  dataframe with in-sample and holdout fit metrics
  coefficient comparison table
  CPL comparison table

What is happening
  metrics for Total leads, Media leads, Baseline leads, Unexplained gap
  metrics for Top channel by CPL and Model fit
  actual vs predicted trend
  labeled bar chart for top lead split

Validation diagnostics
  holdout actual vs predicted
  holdout residuals

Why is it happening
  channel table with coefficient, CPL, contribution, share
  spend share vs contribution share benchmark
  labeled CPL bar chart

What should leadership do next
  bullet recommendations with a directional budget shift heuristic

Channel Insights expander
  stacked bar chart over time with top N plus other
  channel details table
  saturation curves

Export
  results overview CSV
  channel breakdown CSV
  results PDF

Quick Insights expander
  overall marketing CPL
  best channel
  worst channel
  media vs baseline
```

---

## AI Step Layout

```text
[Credentials status banner]
[Provider radio]
[Sidebar API key override]
[Analysis depth: In-depth | Executive short]
[Include all fitted models in the analysis context]
[Generate analysis]
  -> rendered markdown analysis
[AI analysis CSV]
[AI analysis PDF]
```

---

## Step gating

**Do NOT use `st.stop()` inside the section renderers.** It would stop the entire script and break the rest of the navigation flow.

Use `if/else` inside each renderer:

```
def render_config_tab():
    if not st.session_state.get("valid"):
        st.warning("Load and validate data in the Data tab first.")
    else:
        # ... all Config content
```

The sidebar menu remains browsable at all times. Each step independently shows either a message or its content.
