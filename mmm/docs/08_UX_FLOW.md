# UX Flow

## Screen Structure (Streamlit Tabs)

| Tab | Purpose | Enabled when |
|-----|---------|--------------|
| Data | Load, preview, validate input CSV | Always |
| Config | Transform params + regularization hyperparams | Data valid |
| Fit | Select models, run fit, view fit status | Transforms applied |
| Results | Model comparison, three decisions, channel insights, quick insights | ≥1 model fitted |
| AI | Executive summary for the selected model; stretch Q&A later | ≥1 model fitted |

Tabs are always visible. Gating is done by showing a message inside the tab block using `if/else` — not by hiding tabs and not by calling `st.stop()`.

---

## User Journey

1. **Data** — Upload CSV or select from `data/`; select date_col, target_col, **channels to include** (multiselect — add/remove channels as needed); validate; preview. Channel selection can be edited after load (deselect to remove a channel); changing it re-validates and resets transforms and fits.
2. **Config** — Per-channel: select **adstock type** (Geometric / None) and **saturation type** (Log / Hill / None); set theta (if geometric), alpha/k (if hill); set regularization alpha and l1_ratio; click "Apply transforms". Recommended defaults: **Geometric + Log**
3. **Fit** — Select models (MVP: OLS / Ridge; stretch: Lasso / ElasticNet / PyMC); click "Fit selected" or "Fit all"; spinner + R² shown per model
4. **Results** — Model selector at top; comparison tables; three decision sections; expandable Channel Insights; expandable Quick Insights
5. **AI** — Provider setup; executive summary for the selected model. Compare-all and Business Q&A are stretch features

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
| `model_results` | `dict[str, ModelResult]` | Fit tab | Results, AI |
| `model_results_meta` | `dict[str, dict]` | Fit tab | Results |
| `selected_model` | `str` (model name key) | Results tab | AI tab |
| `qa_history` | `list[dict]` — each: `{question, answer, model, timestamp}` | AI tab | AI tab |

---

## Key Interactions

| Interaction | Detail |
|-------------|--------|
| File picker | Shows CSV files from `mmm/data/`; if empty shows "No files yet — use uploader" |
| Column selectors | date_col (selectbox), target_col (selectbox), **channel_cols** (multiselect — select which channels to include; **deselect to remove**; ≥1 required), **control_cols** (multiselect, optional). After load, user can change channel/control selection without re-uploading; app re-validates and resets transforms + model results |
| Transform sliders | Per channel: **Adstock type** (Geometric / None), **Saturation type** (Log / Hill / None); then theta slider (if geometric), alpha/k inputs (if hill); recommended defaults are Geometric + Log |
| Reg params | Alpha input for Ridge/Lasso; alpha + l1_ratio for ElasticNet; stored in session_state |
| Apply transforms | Validates inputs, runs transform_media, sets transforms_applied = True, stores `transform_fingerprint`, and clears stale fits when transform-defining settings change |
| Model multiselect | MVP: OLS and Ridge. Stretch models can be added later |
| Fit buttons | "Fit selected" + "Fit all"; spinner per model; R² shown after each |
| Model selector (Results) | Selectbox — switches all sections; stored as selected_model in session_state |
| Comparison tables | Always show all fitted models; model selector only affects detail sections below |
| Channel Insights | st.expander collapsed by default — opens on demand |
| Quick Insights | st.expander collapsed by default — compact summary, open on demand |
| AI summary | "Generate summary" button — triggers LLM call using selected_model |
| AI Q&A templates | Stretch feature only |
| Q&A history | Stretch feature only |

Hard rule:
- If channel/control selection or transform settings change, clear `model_results` and `selected_model`
- If only regularization changes, keep results visible but require re-fit

---

## Results Tab Layout (in order, top to bottom)

```
[Model selector dropdown]  ← stores session_state["selected_model"]

─── Model Comparison ───────────────────────────────────
  st.dataframe: R², RMSE by model (all fitted models)
  st.dataframe: coefficient comparison — channels × models

─── What is happening? ─────────────────────────────────
  3× st.metric:  Total contribution (leads) | Top channel (CPL, €/lead) | R²

─── Why is it happening? ───────────────────────────────
  st.dataframe: Channel / Coefficient / CPL (€ per lead) / Contribution / Share
  st.bar_chart: CPL by channel (ascending — best first)

─── What should leadership do next? ────────────────────
  3 bullet points with computed numbers (invest in lowest CPL, reduce highest CPL, reallocate %)

─── st.expander("Channel Insights") ────────────────────
  st.area_chart: leads decomposition over time
  Per-channel cards (st.columns): CPL / transform types (Adstock, Saturation) / adstock weeks / saturation badge
  st.line_chart: saturation curves (one per channel; Hill only; Log/none show note or simple curve)

─── st.expander("Quick Insights", expanded=False) ──────
  2-column grid of st.metric / st.info cards:
  • Overall marketing CPL (€ per lead)
  • Best / worst channel (by CPL)
  • Media vs baseline split
  • Over-saturated channels
  • Adstock carryover table
  • Recommended budget shift
```

---

## AI Tab Layout

```
[Credentials status banner]
[Provider radio: OpenAI | Anthropic]  ← from preferred_provider in credentials.json
[Sidebar: API key override input if no credentials.json]

─── Executive Summary ──────────────────────────────────
  Radio: [Single model (uses selected_model)]
  [Generate summary] button
  → LLM response rendered with st.markdown
```

---

## Tab Gating (how it works in Streamlit)

**Do NOT use `st.stop()` inside tab blocks.** It stops the entire script, preventing all subsequent tabs from rendering.

Use `if/else` inside each `with tab_X:` block:

```
with tab_config:
    if not st.session_state.get("valid"):
        st.warning("Load and validate data in the Data tab first.")
    else:
        # ... all Config content

with tab_fit:
    if not st.session_state.get("transforms_applied"):
        st.warning("Apply transforms in the Config tab first.")
    else:
        # ... all Fit content

with tab_results:
    if not st.session_state.get("model_results"):
        st.info("Fit at least one model in the Fit tab to see results.")
    else:
        # ... all Results content

with tab_ai:
    if not st.session_state.get("model_results"):
        st.info("Fit at least one model first to enable AI analysis.")
    else:
        # ... all AI content
```

The tabs are always rendered and clickable. Each tab independently shows either a message or its content.
