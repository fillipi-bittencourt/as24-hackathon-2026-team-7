# Project Review Response

This document answers the four questions from [12_PROJECT_REVIEW_PROMPT.md](12_PROJECT_REVIEW_PROMPT.md) after reviewing the project structure and embedded documentation.

---

## 1. Does the architecture make sense for a Streamlit app?

**Yes.** The architecture is well aligned with Streamlit’s model.

- **Tab-based flow** (Data → Config → Fit → Results → AI) maps cleanly to `st.tabs()`. Gating with `if/else` inside each tab (no `st.stop()`) is the right pattern and keeps all tabs visible.
- **Session state** is used consistently: `df`, `valid`, `X_transformed`, `y`, `model_results`, `selected_model`, `qa_history`, and transform params are all documented. Persistence across reruns is clear.
- **User-driven steps** (load data → apply transforms → fit → view) avoid auto-advance and fit Streamlit’s rerun-on-interaction model.
- **Separation of concerns** is clear: `utils` (validation), `transforms` (adstock/saturation), `models` (five model backends), `ai` (client + payload + prompt). The shared `ModelResult` and single `transform_media` entry point keep the pipeline simple.

**Minor note:** The diagram in 03_ARCHITECTURE shows “Viz” as a separate box; in practice it’s the Results tab. That’s fine as long as builders interpret it as “Results tab = coefficients, CPL, charts,” not a separate service.

---

## 2. Are there any logic gaps in the build instructions (10_BUILD_MMM.md)?

**A few gaps and clarifications:**

### 2.1 Config tab: initialising `adstock_type` and `saturation_type`

Step 2.4 says “when building the Config UI, if a channel is not yet in these dicts (e.g. after first load), set that channel to `"geometric"` and `"hill"`.” It doesn’t say **where** to do that. Recommendation: **before** the per-channel loop, ensure defaults for all `channel_cols`:

```python
for ch in channel_cols:
    if ch not in st.session_state.get("adstock_type", {}):
        st.session_state.setdefault("adstock_type", {})[ch] = "geometric"
    if ch not in st.session_state.get("saturation_type", {}):
        st.session_state.setdefault("saturation_type", {})[ch] = "hill"
```

(or initialise both dicts once when `channel_cols` is set in the Data tab). Without this, the first “Apply transforms” may read missing keys.

### 2.2 `saturation_params` for non-Hill channels

Step 2.4 says for log/none “store a placeholder in saturation_params … or store `None` and skip in channel insights.” The `transform_media` description doesn’t say what to pass for saturation_params when saturation_type is `"log"` or `"none"`. Recommendation: either (a) require `saturation_params[ch]` to exist for all channels (e.g. `{"alpha": 1.0, "k": 0.0}` for log/none) and have `transform_media` ignore alpha/k when type is not hill, or (b) document that `saturation_params` may omit keys for log/none and that `transform_media` must not read alpha/k for those channels. Same for Results: only use `saturation_params[ch]` when `saturation_type[ch] == "hill"`.

### 2.3 Channel order in `fit()`

Models expect `X_transformed` columns in the same order as `channel_cols` then `control_cols`. `ModelResult.channel_names` should be set from `channel_cols` (not from `X_transformed` column indices) so CPL/contribution dicts match channel names. 10_BUILD_MMM implies this but doesn't state it explicitly; one sentence (“Set `channel_names` to the same list as `channel_cols` in the order used in X.”) would close the gap.

### 2.4 OLS coefficient order vs `channel_names`

Step 3.3: “channel coefficients = `result.params[1:]`”. That matches `sm.add_constant(X)` (first column = intercept). So `coefficients[ch]` must be assigned in the same order as the columns of X (i.e. `channel_cols` order). Stating “coefficients dict keys must match channel_cols order” avoids ambiguity.

### 2.5 PyMC CPL HDI

Step 4.1: “94% HDI bounds … `cpl_lower/cpl_upper`”. CPL is `raw_spend / attributed_leads`. HDI is usually computed for the contribution (or attributed leads); then cpl_lower = spend / contribution_upper, cpl_upper = spend / contribution_lower. The doc doesn’t spell this out. Recommendation: add one line: “Compute CPL HDI from contribution HDI: `cpl_lower[ch] = raw_spend[ch].sum() / contribution_upper[ch]`, `cpl_upper[ch] = raw_spend[ch].sum() / contribution_lower[ch]` (with guards for zero).”

### 2.6 Quick Insights: over-saturated only for Hill

Step 5.8 and the embedded table say “channels where saturation_status == over-saturated”. The design elsewhere restricts saturation status (and over-saturated list) to channels with `saturation_type[ch] == "hill"`. 10_BUILD_MMM should say explicitly: “List channels where **saturation_type[ch] == 'hill'** and saturation_status == 'over-saturated'; if none, show 'None — all channels within range'.”

### 2.7 Step 5.7.2 and 5.7.3 vs per-channel transform type

The full 10_BUILD_MMM already says: show “Transform types” in the card; adstock carryover only when adstock_type == geometric; saturation status/badge only when saturation_type == hill; saturation curve only for hill (log/none: note or omit). The **embedded** 10_BUILD_MMM in 12_PROJECT_REVIEW_PROMPT still has the older 5.7.2/5.7.3 text (no transform-type conditionals). The **source of truth** is 10_BUILD_MMM; the embedded copy in 12 should be updated so reviewers (and any agent using 12) see the same instructions.

---

## 3. Is the data flow (Data → Config → Fit → Results → AI) robust?

**Mostly yes.** A few points to harden it:

- **Data → Config:** Valid data sets `valid = True` and populates `df`, `date_col`, `target_col`, `channel_cols`, `control_cols`. Config only runs when `valid`; it reads those keys. Robust.
- **Config → Fit:** “Apply transforms” sets `X_transformed`, `y`, `adstock_params`, `saturation_params`, `adstock_type`, `saturation_type`, `transforms_applied = True`. Fit is gated on `transforms_applied` and uses `X_transformed`, `y`, `channel_cols` for `raw_spend`. If the user changes `channel_cols` in Data without re-running Config, `X_transformed` could have a different number of columns than the current `channel_cols` — that would break Fit. Recommendation: when Data tab succeeds and `channel_cols` or `control_cols` change, set `transforms_applied = False` (and optionally clear `model_results`) so the user must re-apply transforms. Same as “transforms changed → clear model_results” already in place.
- **Fit → Results:** Results are keyed by model name; selector and all sections read `selected_model` and `model_results`. Robust.
- **Results → AI:** AI reads `selected_model` and falls back to the first model if None. Payload uses `channel_names`, `cpl`, etc., from the selected ModelResult. Robust.
- **Edge case:** If the user has one model fitted and deletes or renames that key in session_state (e.g. via custom code), `selected_model` could point to a missing key. A simple guard in Results and AI (“if selected_model not in model_results, set selected_model to list(model_results.keys())[0] or None”) avoids crashes.

---

## 4. Will the "One-Shot Prompt" in 10_BUILD_MMM.md actually work to generate the app?

**Partially.** It can produce a large part of the app in one go, but not the full app as specified.

- **What it asks for:** utils.py, transforms.py, base.py, ols.py, pymc_model.py, ai/client.py, app.py. It explicitly defers ridge, lasso, elasticnet to “the next turn.”
- **So:** One shot will not deliver all five models. The prompt is honest about that. For a hackathon, doing OLS + PyMC first and adding Ridge/Lasso/ElasticNet in a second pass is reasonable.
- **Risks:**
  1. **Context limit:** A single response that includes “full file contents” for all seven items can hit token limits. Splitting into two prompts (e.g. 1–3 + 4–7, or backend first then app.py) is safer.
  2. **Spec refs:** The One-Shot says “following BUILD_MMM.md Steps 1–7” but doesn’t inline the spec ref table (INDEX, ARCHITECTURE, DATA_MODEL, etc.). The building agent must have those docs in context or it will guess (e.g. ModelResult fields, transform_media signature). Recommendation: either (a) add to the One-Shot: “Before generating code, read mmm/docs/06_MODELS.md (ModelResult), mmm/docs/05_TRANSFORMS.md (transform_media signature), mmm/docs/04_DATA_MODEL.md (input schema),” or (b) ensure the agent is given 01_INDEX + 04 + 05 + 06 + 10 when using the One-Shot.
  3. **Doc names:** BUILD_MMM’s spec ref table still says `INDEX.md`, `ARCHITECTURE.md`, etc. The repo uses `01_INDEX.md`, `03_ARCHITECTURE.md`, etc. Updating the ref table to the numbered filenames avoids wrong-file or 404s.
  4. **app.py:** The full app.py must implement every tab (Data, Config, Fit, Results, AI) and all Step 7 gating and imports. A single “output app.py” that follows Steps 1–6 and 7 will be long; the model may truncate. Consider “output app.py structure with st.tabs and gating; then fill each tab in follow-up messages.”

**Verdict:** The One-Shot is useful to bootstrap backend + app shell and one or two models. Treat it as “Phase 1”; Phase 2 = add Ridge/Lasso/ElasticNet, then Phase 3 = run through CHECKLIST and fix any missing pieces (e.g. per-channel transform type in Config/Results, CPL formatting, AI payload).

---

## 5. Inconsistencies between 12_PROJECT_REVIEW_PROMPT and current design

These are in the **embedded** copy of the docs inside 12_PROJECT_REVIEW_PROMPT.md; the live docs in the repo may already be correct.

| Location in 12 | Issue | Fix |
|----------------|--------|-----|
| Step 5.7.1 (embedded 10_BUILD_MMM) | Says “Stacked area chart (Plotly)” | Should say “Use `st.area_chart`” and describe dataframe with date index and contribution/baseline columns (per 10_BUILD_MMM). |
| Step 5.7.2 (embedded) | No mention of per-channel transform type or “only when hill” for saturation | Align with 10_BUILD_MMM: show Adstock/Saturation type; adstock carryover only for geometric; saturation status/badge only for hill. |
| Step 5.7.3 (embedded) | “For each channel” saturation curve | Restrict to channels with saturation_type == "hill"; for log/none show note or omit. |
| Step 5.8 Over-saturated (embedded) | “saturation_status == over-saturated” | Add “only for channels with saturation_type == 'hill'”. |
| Spec ref table (embedded 10_BUILD_MMM) | INDEX.md, ARCHITECTURE.md, DATA_MODEL.md, etc. | Use numbered names: 01_INDEX.md, 03_ARCHITECTURE.md, 04_DATA_MODEL.md, etc., so they match the repo. |
| 03_ARCHITECTURE (in repo) | “Charts: Plotly” in one line | Change to “Streamlit native charts” to match the rest of the design. |

Updating the embedded 10_BUILD_MMM section in 12_PROJECT_REVIEW_PROMPT to match 10_BUILD_MMM (and fixing the spec refs and ARCHITECTURE) will keep one source of truth and avoid confusion.

---

## Summary

- **Architecture:** Fits Streamlit; session state and tab flow are sound.
- **Build instructions:** A few gaps (Config defaults for adstock_type/saturation_type, saturation_params for log/none, channel order, PyMC CPL HDI, over-saturated only for hill, 5.7 alignment with per-channel types). All are small, documentable fixes.
- **Data flow:** Robust if you reset `transforms_applied` when channel/control columns change and guard `selected_model` against missing keys.
- **One-Shot prompt:** Useful for a first pass; plan for a second pass for the other three models and a third for checklist-driven fixes. Add spec refs or numbered doc names and consider splitting long outputs to avoid truncation.

Applying the fixes above will make the build plan and the review prompt consistent and ready for implementation.

---

## 6. What else needs improving?

### 6.1 Control variables in the AI payload

The AI payload schema (AI_ANALYSIS.md and Step 6.2) includes **controls**: `{ name, coefficient, contribution_pct }`. **ModelResult** (MODELS.md) only has `channel_names`, `coefficients` (channels), `contribution`, `contribution_pct` (channels). There is no field for control variable names or control coefficients. So when `control_cols` is non-empty, `build_payload` has no way to get control coefficients or contribution from `model_result` alone.

**Recommendation:** Either (a) extend ModelResult with optional `control_names: list[str]` and `control_coefficients: dict[str, float]`, and document that each model must fill these when control_cols were used (coefficients come from `params[n_channels+1:]` after intercept and channel coefs), and compute control contribution_pct from `(coef * X_control_col).sum() / y_pred.sum()`, or (b) pass the raw fit object into `build_payload` and have it slice out control params. Option (a) keeps the payload builder simple and the interface consistent.

### 6.2 Validation: missing values (NaN) in required columns

`validate_mmm_data` checks "no all-null required columns" but does not require "no NaN in target or channel columns". Rows with NaN in `target` or in any `channel_cols` will break regression (e.g. OLS drops them or raises). **Recommendation:** Add a check: if `df[target_col].isna().any()` or `df[channel_cols].isna().any()`, add an error like `"Missing values in required columns (target or channels) — remove or impute rows."` Alternatively, document that the app may drop rows with NaN in target/channels before fit (and show a warning), and keep validation as-is.

### 6.3 Setting `valid = False` when validation fails

Step 1.3 only runs "on success" and sets `valid = True`. If the user had valid data and then uploads or selects a file that **fails** validation, `valid` should become `False` so Config/Fit are gated again. **Recommendation:** In the Data tab, when validation returns `(False, errors)`, set `session_state["valid"] = False` (and optionally clear `transforms_applied` and `model_results`). That way a bad second load does not leave the app in an inconsistent state.

### 6.4 Credentials file path at runtime

Docs say "Read `mmm/credentials.json`". When the app is run with `cd mmm && streamlit run app.py`, the working directory is `mmm/`, so the path should be **`credentials.json`** (relative to cwd) or resolve via `Path(__file__).parent / "credentials.json"` so it works regardless of cwd. **Recommendation:** In 10_BUILD_MMM or 09_AI_ANALYSIS, state: "Resolve credentials path relative to the app root (e.g. `Path(__file__).parent / 'credentials.json'` when loading from `app.py` or the ai client)." That avoids 404 when running from `mmm/`.

### 6.5 `build_payload`: date_range and n_weeks

`build_payload(model_result, session_state)` must build `date_range` and `n_weeks` from the data. **Recommendation:** Add one line to Step 6.2: "Get `date_range` from `session_state['df'][session_state['date_col']].min().date()` and `.max().date()`; get `n_weeks` (or n_rows) from `len(session_state['df'])`."

### 6.6 Displaying CPL when it is infinite

When a channel has zero attributed leads, the formula sets `cpl[ch] = float("inf")`. The UI should not show the string `"inf"`. **Recommendation:** In 10_BUILD_MMM (Results tab and Quick Insights), add: "When formatting CPL for display, if value is `math.isinf(cpl)` or very large, show `'—'` or `'N/A'` instead of the raw number."

### 6.7 Decomposition chart: row order and index

Step 5.7.1 says the area chart dataframe has "index is the date column". The contribution and baseline vectors are aligned with `y_pred`, which is in the same row order as `session_state["df"]` (after sort). So the chart dataframe must use the **same** date index as the sorted df. **Recommendation:** Add: "Use `session_state['df'][session_state['date_col']].values` (or reset_index) as the index so the chart aligns with the model's time order."

### 6.8 CHECKLIST and doc references to 10_BUILD_MMM

CHECKLIST Phase 3 says "following `mmm/docs/BUILD_MMM.md`" and "Read mmm/docs/BUILD_MMM.md"; the actual file is **`mmm/docs/10_BUILD_MMM.md`**. The Reference table in CHECKLIST correctly points to `10_BUILD_MMM.md`, but the phase text does not. **Recommendation:** In CHECKLIST, replace `BUILD_MMM.md` with `10_BUILD_MMM.md` in 3.1 and 3.2 (and any other phase text). Similarly, AGENT_README and docs/README reference `mmm/docs/BUILD_MMM.md` — update to `mmm/docs/10_BUILD_MMM.md` for consistency.

### 6.9 One-Shot prompt: correct doc path

The One-Shot says "following `mmm/docs/BUILD_MMM.md`". The repo uses **`10_BUILD_MMM.md`**. **Recommendation:** In 10_BUILD_MMM.md, change the One-Shot to "following `mmm/docs/10_BUILD_MMM.md`" so the path exists.

### 6.10 Spec ref table in 10_BUILD_MMM (10_BUILD_MMM.md)

The spec ref table in 10_BUILD_MMM still lists `INDEX.md`, `ARCHITECTURE.md`, `DATA_MODEL.md`, etc. The repo uses numbered filenames. **Recommendation:** Update the table to `01_INDEX.md`, `03_ARCHITECTURE.md`, `04_DATA_MODEL.md`, `06_MODELS.md`, `05_TRANSFORMS.md`, `09_AI_ANALYSIS.md`, `08_UX_FLOW.md`, `07_TECHNICAL_SPEC.md`, `11_WIREFRAME_PROMPT.md` so builders (and agents) open the correct files.

### 6.11 Q&A history format: AI_ANALYSIS vs 10_BUILD_MMM

AI_ANALYSIS says "Store each (question, answer, model_name)"; 10_BUILD_MMM specifies a **dict** with `question`, `answer`, `model`, `timestamp` and a cap of 15. **Recommendation:** In 09_AI_ANALYSIS.md, update the Q&A history bullet to: "Store each entry as a dict: `{ question, answer, model, timestamp }`. Cap at 15 entries; display newest at bottom." So both docs match.

### 6.12 Wireframe vs build instructions

The wireframe is **not** code: use [11_WIREFRAME_PROMPT.md](11_WIREFRAME_PROMPT.md) as a copy-paste prompt to generate a Streamlit wireframe (structure and components). 10_BUILD_MMM is the source of truth for implementation.

### 6.13 PyMC: handling control columns in X

PyMC Step 4.1 describes priors for "channel coefficients". When `control_cols` is non-empty, X has more columns; the model has intercept + channel coefs + control coefs. **Recommendation:** Clarify in Step 4.1: "Channel coefficients get the HalfNormal prior; if there are control columns, add one coefficient per control (same or a Normal prior) and ensure the coefficient order matches X (channels first, then controls)." So the builder does not assume X is channels-only.

---

## 7. Summary of recommended doc/design changes

| Priority | Change |
|----------|--------|
| High | Extend ModelResult or build_payload for controls (6.1); set valid=False on validation failure (6.3); correct 10_BUILD_MMM path in CHECKLIST/AGENT_README/One-Shot (6.8, 6.9); spec ref table to numbered filenames (6.10). |
| Medium | Validation NaN check or drop-with-warning (6.2); credentials path resolution (6.4); date_range/n_weeks in build_payload (6.5); CPL inf display (6.6); decomposition chart index (6.7); Q&A history dict in AI_ANALYSIS (6.11); PyMC control columns (6.13). |
| Low | Wireframe precedence note (6.12). |

Implementing the high-priority items removes the main gaps before build; medium and low improve robustness and consistency.
