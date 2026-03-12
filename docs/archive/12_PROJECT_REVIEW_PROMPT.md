# Project Review Prompt

> **Note:** The source of truth for implementation is `mmm/docs/10_BUILD_MMM.md`. This file is a snapshot for review and may lag behind it; builders should follow 10_BUILD_MMM.

> **Instructions:** Copy everything below this line and paste it into Claude or ChatGPT to get a comprehensive review of the project architecture and build plan before starting implementation.

---

I am building a Marketing Mix Modeling (MMM) data product for a hackathon. The goal is to build a decision-ready Streamlit app in 2 days that answers three executive questions: What is happening? Why? What should leadership do next?

I have designed the architecture, data model, and build instructions, but I haven't written the app code yet.

Please review the project structure and documentation below.
1. Does the architecture make sense for a Streamlit app?
2. Are there any logic gaps in the build instructions (10_BUILD_MMM.md)?
3. Is the data flow (Data -> Config -> Fit -> Results -> AI) robust?
4. Will the "One-Shot Prompt" in 10_BUILD_MMM.md actually work to generate the app?

Here is the project context and documentation:

---

## README.md

# The Great BI Blackout — Hackathon

**Team 7** | Canada  
Rim Nasfi · Kelly Mitchell · Hussain Jalaluddin · Fillipi Bittencourt

**Presentation:** Friday March 13th, 10am EST / 4pm CET  
**Canada teams:** Can kick off Wednesday afternoon to account for lost time on Friday

---

## For AI Agents

**Read [AGENT_README.md](AGENT_README.md) first.** It contains project metadata, constraints, task routing, and references to all other docs.

---

## Quick Links

| Document | Purpose |
|----------|---------|
| [AGENT_README.md](AGENT_README.md) | **Agent entry point** — metadata, routing, constraints |
| [docs/README.md](docs/README.md) | **Doc index** — links to all hackathon docs below |
| [docs/CHECKLIST.md](docs/CHECKLIST.md) | **Complete project checklist** — setup → build → test → demo |
| [docs/GUIDELINES.md](docs/GUIDELINES.md) | Scope, guardrails, tech stack, business areas |
| [docs/DECISIONS_FRAMEWORK.md](docs/DECISIONS_FRAMEWORK.md) | The three executive questions (design anchor) |
| [docs/AI_COPILOT_GUIDE.md](docs/AI_COPILOT_GUIDE.md) | AI prompting patterns and guardrails |
| [docs/DEMO_PREP.md](docs/DEMO_PREP.md) | Demo script template and deliverables |

---

## Folder Structure

```
as24-hackathon-2026-team-7/
├── AGENT_README.md        # Agent entry point (read first)
├── README.md              # This file
├── TEAM.md                # Team members and decisions
├── docs/                  # Hackathon process (constraints, checklist, demo)
│   ├── CHECKLIST.md       # Complete project checklist — start here
│   ├── GUIDELINES.md
│   ├── DECISIONS_FRAMEWORK.md
│   ├── AI_COPILOT_GUIDE.md
│   └── DEMO_PREP.md
└── mmm/                   # THE data product — everything lives here
    ├── app.py             # Streamlit entry point
    ├── requirements.txt
    ├── data/              # Place business data (CSV) here
    ├── src/               # App source code (models, transforms, AI)
    └── docs/              # MMM design docs + 10_BUILD_MMM.md
```

The **data product** is the **MMM app** in [mmm/](mmm/). Data goes in `mmm/data/`. Run with `cd mmm && streamlit run app.py`.

---

## The Mission

Build a **decision-ready data product** in 2 days — without any traditional BI tools — that enables the C-Suite to make informed decisions for their board meeting.

**Remember:** You are not building a dashboard. You are rebuilding the company's ability to make decisions under pressure.

---

## mmm/docs/10_BUILD_MMM.md

# Build the MMM app — Step-by-step instructions

## ⚡️ Efficiency & Token Saving (Meta-Instructions)

**For the Agent building this app:**
- **No conversational filler:** Do not explain the code. Do not say "Here is the implementation". Just output the code blocks.
- **Batching:** Implement multiple steps in a single response if possible.
- **Precision:** Follow the file paths exactly.
- **Thinking:** If you need to reason, keep it internal or extremely brief. Focus on generating the file contents.

---

## 🚀 One-Shot Prompt (Copy-Paste to Build)

Use this prompt to build the core app in one turn:

```text
Build the MMM app in `mmm/` following `mmm/docs/10_BUILD_MMM.md` Steps 1–8.
Constraint: Be efficient. No explanations. Just output the full file contents for:
1. `mmm/src/utils.py` (Step 1)
2. `mmm/src/transforms.py` (Step 2)
3. `mmm/src/models/base.py` (Step 3)
4. `mmm/src/models/ols.py` (Step 3)
5. `mmm/src/models/pymc_model.py` (Step 4)
6. `mmm/src/ai/client.py` (Step 6)
7. `mmm/app.py` (Step 7)
Assume `mmm/src/models/{ridge,lasso,elasticnet}.py` will be done in the next turn.
Start now.
```

---

Build the complete **interactive** Streamlit MMM app. Data will be provided later via CSV in `mmm/data/` or upload. The app must load, validate, transform, fit models, **allow comparing multiple models**, and show results for three decisions; optionally call OpenAI/Claude.

**Run command:** `cd mmm && source .venv/bin/activate && streamlit run app.py`

**Spec refs — read all of these before building; do not duplicate their content:**

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
| `mmm/docs/11_WIREFRAME_PROMPT.md` | Wireframe prompt — Streamlit-only UI spec |

---

## Interactivity (required)

The app is a Streamlit app. Every step must be **user-driven and interactive**: file upload or file picker, column selectors, sliders/number inputs for transform params, buttons to apply transforms and to fit models, dropdowns to choose which model(s) to view or compare. Use `st.session_state` to persist data and results so the app reacts to user actions. Do not auto-fit or auto-advance; the user clicks to load data, apply transforms, fit, and view results.

---

## Model comparison (required)

Users must be able to **fit and compare multiple models**. The app must implement the **four frequentist models**: **OLS, Ridge, Lasso, ElasticNet**; plus **PyMC** (Bayesian) as the fifth model. Store results per model, e.g. `session_state["model_results"] = {"OLS": result_ols, "Ridge": result_ridge, ...}`. Fit tab: let the user select one or more models and run "Fit selected" or "Fit all"; each fit adds or overwrites that model's entry in `model_results`. Results tab: provide (1) a **model selector** (dropdown or radio) to view one model's detailed results, and (2) a **comparison view** — a table with rows = models and columns = R², RMSE (or MAE), and optionally a coefficient comparison (rows = channels, columns = model names). Charts (e.g. CPL by channel) can show one model at a time with the selector, or show multiple models in one chart (e.g. grouped bar). See Step 5 for details.

---

## Step 1 — Data layer

- **1.1** Create `mmm/src/utils.py`. Implement `validate_mmm_data(df, date_col, target_col, channel_cols) -> (bool, list[str])`. Checks (in order, accumulate all errors before returning):
  - Required columns exist
  - Date column parseable with `pd.to_datetime(errors='coerce')` — flag rows that failed to parse
  - Target and channel columns are numeric
  - No all-null required columns
  - At least 2 rows (prefer at least 3× the number of parameters — see Step 3.3)
  - **No duplicate dates** — if `df[date_col].duplicated().any()`, add error `"Duplicate dates found — each row must represent a unique time period"`
  - **No negative values in channel columns** — if any spend value < 0, add error `"Negative values in channel columns — spend must be ≥ 0"`
  Return `(True, [], warnings)` or `(False, error_messages, [])`. Use 04_DATA_MODEL.md for column rules.
- **1.2** Data tab (wired in Step 7 — do not add tabs here):
  - `st.file_uploader` for CSV
  - File picker dropdown: use `list(Path("data").glob("*.csv"))` to list files; if the list is empty, show `"No files in data/ yet — use the uploader above."` Do not crash.
  - Load with `pd.read_csv`; parse date column with `pd.to_datetime`
  - Column selectors:
    - `date_col` — `st.selectbox`, required
    - `target_col` — `st.selectbox`, required
    - `channel_cols` — `st.multiselect` for spend columns, at least one required
    - `control_cols` — `st.multiselect` for optional control variables (price, promo, seasonality); default empty. Controls are passed through to X without adstock/saturation transforms — see Step 2.3.
  - Call `validate_mmm_data`; show `st.success` with row count and column list on pass, or `st.error(errors)` on fail
- **1.3** On success:
  - **Sort df by date**: `df = df.sort_values(date_col).reset_index(drop=True)` — adstock is order-sensitive; unsorted data produces wrong results
  - Show parsed date range: `st.caption(f"Date range: {df[date_col].min().date()} to {df[date_col].max().date()} — {len(df)} rows")` — lets user verify date parsing is correct
  - Store in `st.session_state`: `df`, `date_col`, `target_col`, `channel_cols`, `control_cols` (may be empty list), `valid = True`
  - The Fit tab is gated on both `valid` and `transforms_applied` — see Step 7.3.

---

## Step 2 — Transforms

- **2.1** In `mmm/src/transforms.py`: `geometric_adstock(x, theta)` with `x_transformed[t] = x[t] + theta * x_transformed[t-1]`, `x_transformed[0] = x[0]`. Implement geometric only — Weibull is documented in 05_TRANSFORMS.md for reference but not required for the hackathon build.
- **2.2** Same file: `hill_saturation(x, alpha, k)` = `x^alpha / (k^alpha + x^alpha)`; safe for zeros. Implement also `log_saturation(x)` = `np.log1p(x)` for per-channel saturation type "log".
- **2.3** Same file: `transform_media(df, channel_cols, adstock_params, saturation_params, adstock_type, saturation_type, control_cols=None)` — per-channel adstock_type ("geometric" | "none") and saturation_type ("hill" | "log" | "none"). Apply adstock then saturation per channel; append control columns raw. Return 2D array shape `(n_rows, n_channels + n_controls)`.
- **2.4** Config tab: Per-channel **transform type** selectors: Adstock (Geometric / None), Saturation (Hill / Log / None). Then theta (if geometric), alpha/k (if hill). Store adstock_type, saturation_type in session_state. Button "Apply transforms" calls transform_media with these and stores X_transformed, y, adstock_params, saturation_params, adstock_type, saturation_type, transforms_applied = True.
  - **Transform params** — for each channel: show theta slider only if adstock_type[ch] == "geometric"; show alpha/k only if saturation_type[ch] == "hill". Store adstock_params, saturation_params, adstock_type, saturation_type.
  - **Regularization params** — `st.number_input` for Ridge/Lasso alpha (default 1.0), ElasticNet l1_ratio (default 0.5); store as `session_state["reg_alpha"]`, `session_state["l1_ratio"]`.
  - Button **"Apply transforms"**: call `transform_media(..., adstock_type=session_state["adstock_type"], saturation_type=session_state["saturation_type"], control_cols=control_cols)`, store X_transformed, y, adstock_params, saturation_params, adstock_type, saturation_type, transforms_applied = True. If model_results non-empty, clear them and show warning.

---

## Step 3 — Models (base + frequentist)

- **3.1** Create `mmm/src/models/__init__.py` (exports).
- **3.2** Create `mmm/src/models/base.py`. Copy the exact `ModelResult` dataclass from 06_MODELS.md — use that file as the single source of truth for field names and types.

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
      contribution_pct[ch] = sum(contribution[ch]) / sum(y_pred)  # share of total predicted leads

  baseline = y_pred - sum(contribution[ch] for ch in channel_names)
  baseline = np.clip(baseline, 0, None)                      # clip negatives
  baseline_pct = baseline.sum() / y_pred_total
  ```

  Store all fields in ModelResult including `contribution` as `dict[str, np.ndarray]`. Use **`cpl`** (cost per lead), not roi. If clipping occurs, the decomposition won't exactly sum to y_pred — acceptable for hackathon display.

- **3.3** Create `mmm/src/models/ols.py`: use `statsmodels.api.OLS`.
  - **Ensure X is 2D**: `if X.ndim == 1: X = X.reshape(-1, 1)` before any operation — avoids `sm.add_constant` adding the constant in the wrong axis for single-channel data.
  - Add constant: `X_with_const = sm.add_constant(X, has_constant='add')`. The `has_constant='add'` flag forces a constant even if one column is all-ones.
  - **Warn if underdetermined**: if `len(y) < 3 * X_with_const.shape[1]`, show `st.warning(f"Only {len(y)} rows for {X_with_const.shape[1]} parameters — model may be overfit. Add more data for reliable results.")`. Still proceed.
  - Fit: `result = sm.OLS(y, X_with_const).fit()`. Intercept = `result.params[0]`; channel coefficients = `result.params[1:]`.
  - Compute cpl, contribution, contribution_pct, baseline using the formula in Step 3.2 (with zero-division guards and clipping).
  - `r_squared = result.rsquared`, `rmse = sqrt(mean(result.resid**2))`. Return ModelResult.
- **3.4** Create `mmm/src/models/ridge.py`, `lasso.py`, `elasticnet.py` with sklearn. Accept `alpha` (and `l1_ratio` for ElasticNet) from kwargs — passed from `session_state["reg_alpha"]` and `session_state["l1_ratio"]`. sklearn does not add a constant automatically — include `fit_intercept=True` (default). After fit: `intercept = model.intercept_`, `coefficients = model.coef_`. Compute cpl, contribution, contribution_pct, baseline with the same formula as OLS. For r_squared use `model.score(X_transformed, y)` (pass the same transformed array used for fitting); for rmse compute `sqrt(mean((y - model.predict(X_transformed))**2))` manually.
- **3.5** Fit tab: **Interactive.** Show a warning and return early if `not session_state.get("transforms_applied")`: `"Apply transforms in the Config tab first."` Model selector (multiselect) for OLS, Ridge, Lasso, ElasticNet, PyMC. Buttons: "Fit selected" and "Fit all". On click: for each selected model, read `X_transformed` and `y` from session_state, build `raw_spend = {ch: df[ch].values for ch in channel_cols}`, instantiate model, call `model.fit(X_transformed, y, raw_spend=raw_spend, **reg_params)`, store result in `session_state["model_results"][model_name]`. The ModelResult's `model_name` field must be set to the same key used in the dict (e.g. `"OLS"`). Show `st.spinner("Fitting [name]...")` during each fit. After success show `"✓ OLS: R² = 0.72, RMSE = 12,450"`. Results tab enabled when `session_state.get("model_results")` is non-empty.

---

## Step 4 — PyMC

- **4.1** Create `mmm/src/models/pymc_model.py`. Implement as a Bayesian linear regression using PyMC with the following priors and sampler settings:
  - Intercept: `Normal(mu=y.mean(), sigma=y.std())` — centred on mean leads
  - Channel coefficients: `HalfNormal(sigma=y.std())` for each channel — positive-only prior (spend should have non-negative effect); scaled to the target's standard deviation so the prior is weakly informative rather than nearly zero
  - Noise (sigma): `HalfNormal(sigma=y.std())` — scaled to target variance
  - Likelihood: `Normal(mu=intercept + X @ coefficients, sigma=sigma, observed=y)`
  - Sampler: `pm.sample(draws=1000, chains=2, tune=500, progressbar=False, return_inferencedata=True)` — 1000 draws is sufficient for hackathon; tune=500 warms up the sampler
  - After sampling: extract posterior means and 94% HDI (highest density interval) using `az.summary(trace)` or `pm.stats.hdi(trace, hdi_prob=0.94)`
  - Return ModelResult with coefficient/CPL posterior means as `coefficients`/`cpl`, and 94% HDI bounds as `coefficient_lower/upper`, `cpl_lower/upper`
  - Compute r_squared and rmse using posterior predictive mean vs actual y (same as frequentist models)

- **4.2** Fit tab: when PyMC is selected (among others), show `st.info("PyMC may take 1–2 minutes. Other models are fast.")`. On "Fit selected" / "Fit all", run PyMC like other models and store in `session_state["model_results"]["PyMC"]`.

---

## Step 5 — Results tab (three decisions + model comparison)

- **5.1** Results tab: if `session_state.get("model_results")` is empty, show `"Fit at least one model in the Fit tab to see results."` and return.
- **5.2** **Model selector:** `st.selectbox("View model:", list(session_state["model_results"].keys()))`. Store selected model name in `session_state["selected_model"]` — this is also read by the AI tab (Step 6.5). All sections below use the selected model's ModelResult.
- **5.3** **Model comparison table (required):** `st.dataframe` with rows = model names, columns = R², RMSE. Sortable. Below it, a coefficient comparison table: rows = channel names, columns = model names, cells = coefficient values. Both tables always show all fitted models regardless of selector.
- **5.4** Section **"What is happening?"** (for selected model): three `st.metric` cards — Total media contribution (attributed leads), **Top channel by CPL** (name + €X per lead), Model fit (R² = X, RMSE = Y).
- **5.5** Section **"Why is it happening?"** (for selected model): `st.dataframe` — base columns: Channel, Coefficient, **CPL (€ per lead)**, Contribution (leads), Share (%). Only add Coeff CI and **CPL CI** columns if PyMC. Below the table, use `st.bar_chart` for **CPL by channel** (sort ascending — best first).
- **5.6** Section **"What should leadership do next?"** (for selected model): three bullet points — (1) Invest more in [lowest CPL channel] — currently €X per lead, (2) Reduce spend on [highest CPL channel] — €X per lead, (3) Reallocate [N]% from [highest CPL] to [lowest CPL]. Reallocation % = `min(50, round((cpl_worst - cpl_best) / cpl_worst * 100))`.

---

## Step 5.7 — Channel insights (per-channel deep dive)

Add a **"Channel Insights"** section inside the Results tab, below the three decision sections. Wrap the entire section in `st.expander("Channel Insights", expanded=False)` — collapsed by default to keep the tab readable. It renders for the currently selected model.

- **5.7.1 Leads decomposition chart:** Use `st.area_chart`. Create a dataframe where the index is the date column, and columns are the `contribution` vectors for each channel plus the `baseline` vector. This will automatically stack them. Add a small note below: "Stacks represent predicted attribution. Baseline includes intercept and non-attributed variance." This answers "where do leads come from week by week?"
- **5.7.2 Per-channel breakdown cards:** For each channel: spend total and average weekly spend; attributed contribution (absolute and %) in leads; **CPL** (€ per lead). **Transform types** (from session_state): Adstock: [Geometric (θ=X) | None], Saturation: [Hill (α, k) | Log | None]. **Adstock carryover:** when adstock_type[ch] == "geometric", compute weeks to 5% decay with `round(-log(0.05) / -log(theta))`; when "none", show "No carryover". **Saturation status:** when saturation_type[ch] == "hill", compare spend to k and show under-/near/over-saturated badge (green/amber/red); when "log" or "none", show "N/A" or "Log" / "No saturation".
- **5.7.3 Saturation curves:** For each channel with **saturation_type[ch] == "hill"**, use `st.line_chart` for the Hill curve (x = spend 0 to 2× max, y = response). For "log" or "none", show a short note or omit.

> These charts are computed from ModelResult and the transform parameters stored in `session_state` (adstock_params, saturation_params, adstock_type, saturation_type). No additional model fitting required.

---

## Step 5.8 — Quick Insights (auto-answered from model results)

Add a **"Quick Insights"** section (not "Business Q&A" — that name is used in the AI tab) at the bottom of the Results tab. Wrap the entire section in `st.expander("Quick Insights", expanded=False)` — collapsed by default since the key information is already shown in the three decision sections above. Users open it for a compact summary view.

Display as a 2-column grid of `st.metric` / `st.info` cards. For the currently selected model, use `sum(y_pred)` as the denominator for all percentage calculations (not actual y — the model's attribution adds up to y_pred for internal consistency):

| Card | How to compute |
|------|----------------|
| Overall marketing CPL | Total spend / total attributed leads — € per lead |
| Best channel | `min(cpl.items(), key=...)` — show "{name}: €X per lead" |
| Worst channel | `max(cpl.items(), key=...)` — show "{name}: €X per lead" (red if high) |
| Media vs baseline | `sum(channel_contributions) / sum(y_pred)` vs `sum(baseline) / sum(y_pred)` — show as two `st.metric` side by side |
| Over-saturated channels | List channels where **saturation_type[ch] == "hill"** and saturation_status == "over-saturated"; if none, show "None — all channels within range" |
| Recommended shift | Lowest CPL channel + highest CPL channel + reallocation % (from Step 5.6 formula) |

If a value can't be computed (e.g. spend data missing), show `"N/A"` in the card.

---

## Step 6 — AI

`mmm/src/ai/__init__.py` already exists (placeholder). Create `mmm/src/ai/client.py`.

Full spec: [09_AI_ANALYSIS.md](09_AI_ANALYSIS.md). Summary of what to implement:

**6.1 — Credential loading (`load_credentials()`):**
Try in this order, use the first that works:
1. Read `mmm/credentials.json` → parse `preferred_provider`, `openai_api_key` / `anthropic_api_key`, `openai_model` / `anthropic_model`
2. Fall back to env vars `OPENAI_API_KEY` / `ANTHROPIC_API_KEY`
3. Fall back to a key passed in by the caller (sidebar input)
Return `(provider, api_key, model)` or raise a clear error message if nothing found.

**6.2 — Build the analysis payload (`build_payload(model_result, session_state)`):**
Construct a dict with: `model_name`, `date_range`, `target_metric` (**"leads"**), `n_weeks`, `model_fit`, `channels` (list of name/coefficient/**cpl**/contribution_pct), `controls`, `baseline_pct`, `top_channel` (lowest CPL), `bottom_channel` (highest CPL). If multiple models are fitted, add `comparison_table`.

**Token optimization:**
- Round all float values to 2 decimal places.
- Exclude any optional fields that are None.
- Convert numpy types to Python native types (float/int) for clean JSON serialization.

See 09_AI_ANALYSIS.md for the full payload schema.

**6.3 — ICE prompt (`build_prompt(payload)`):**
Assemble the prompt using ICE structure (see 09_AI_ANALYSIS.md):
- Instructions: senior analyst, C-suite audience, direct, use numbers
- Context: model name, date range, target metric, n_weeks
- Example: one short input→output example
- Task: the payload serialized as JSON
Request four output sections: Executive summary, Top finding, Recommendation (with numbers), Confidence note.

**6.4 — `get_summary(payload, provider, api_key, model)` function:**
Call OpenAI or Claude with the assembled prompt. Return the response text. On any error (rate limit, bad key, network), return a human-readable error string — never raise. See 09_AI_ANALYSIS.md for error handling rules.

**6.5 — AI tab:**

Load credentials on tab open (`load_credentials()`); if none found, show `"Add credentials.json or set an API key in the sidebar to enable AI analysis."` with a `st.sidebar.text_input` as override. Provider radio (OpenAI / Anthropic) pre-set from `preferred_provider`. Enable tab only when `session_state.get("model_results")` is non-empty; otherwise show `"Fit at least one model first."` and return.

The selected model for Section A is read from `session_state.get("selected_model")`. If this is None (user hasn't visited the Results tab yet), default to `list(session_state["model_results"].keys())[0]`.

The AI tab has two sections:

**Section A — Executive summary:**
- Two analysis modes (radio): **Single model** (uses selected model from Results) and **Compare all** (uses comparison table if multiple models fitted).
- "Generate summary" button: call `build_payload` → `build_prompt` → `get_summary`; display result in `st.markdown`. See 09_AI_ANALYSIS.md for the ICE prompt and output format.

**Section B — Business Q&A (first-class feature, not optional):**
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

---

## Step 7 — App shell

`mmm/app.py` is currently a placeholder (comment only). Replace its entire contents with the full app. **This is where tabs are created — not in Step 1.**

- **7.1** `st.set_page_config(page_title="MMM — Marketing Mix Modeling", layout="wide")`. `st.title("Marketing Mix Modeling")`. `st.caption("Load data → configure transforms → fit models → view results")`.
- **7.2** `tab_data, tab_config, tab_fit, tab_results, tab_ai = st.tabs(["Data", "Config", "Fit", "Results", "AI"])`. Render each section inside its tab using `with tab_data:` etc.
- **7.3** Tab gating — use `if/else` inside each `with tab_X:` block. **Do NOT use `st.stop()` inside tab blocks** — it stops the entire script and prevents all subsequent tabs from rendering.

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
- **7.4** Imports at the top of app.py: `from src.utils import validate_mmm_data`, `from src.transforms import transform_media`, `from src.models.ols import OLSModel`, `from src.models.ridge import RidgeModel`, `from src.models.lasso import LassoModel`, `from src.models.elasticnet import ElasticNetModel`, `from src.models.pymc_model import PyMCModel`, `from src.ai.client import load_credentials, build_payload, build_prompt, get_summary`. Run from `mmm/` so relative imports resolve.

---

## Step 8 — Data note

Data is not in the repo. App must support CSV upload and/or files in `mmm/data/`. Validate per 04_DATA_MODEL.md. Show clear errors if date, target, or channel columns missing.

---

## docs/DECISIONS_FRAMEWORK.md

# Decisions Framework — Agent Design Anchor

> **For agents:** Every view and metric you build MUST map to one of these three questions. Use this as the design anchor for all data product work.

---

## [decision_1] What is happening?

**purpose:** Situational awareness. Current state at a glance.

**agent_mapping:**
- Implement: High-level KPIs (current vs. target or prior period)
- Implement: Key trends (time series, sparklines)
- Implement: Status indicators (red/amber/green)

**examples:**
- Revenue down 12% vs. last quarter
- Customer churn increased in last 30 days
- Inventory turnover below target in 3 regions
- Marketing spend up but conversion flat

---

## [decision_2] Why is it happening?

**purpose:** Root cause. Executives need drivers before acting.

**agent_mapping:**
- Implement: Breakdowns (by region, product, segment, channel)
- Implement: Comparisons (this vs. that, before vs. after)
- Implement: Drill-down or filters to explore drivers

**examples:**
- Revenue drop driven by Region X and Product Y
- Churn concentrated in segment Z after price increase
- Slow turnover due to overstock of SKU category A
- Conversion flat because traffic quality declined

---

## [decision_3] What should leadership do next?

**purpose:** Action. Clear, prioritized recommendations.

**agent_mapping:**
- Implement: Summary of top 3–5 recommended actions
- Implement: Priority or impact indicators
- Optional: Simple scenario or sensitivity view

**examples:**
- Reallocate budget from Channel A to Channel B
- Launch retention campaign for segment Z
- Run promotion on overstocked category A
- Pause low-quality traffic sources

---

## [mapping_table] Business Area Mapping — Marketing ROI / MMM

| question | answer |
|----------|--------|
| What is happening? | Marketing spend is X. Modelled **leads** contribution by channel. Top-line: total attributed leads, share by media vs baseline, R². Success metric: **cost per lead (CPL)**. |
| Why is it happening? | **Channel CPL** differs: adstock carryover, saturation. The model decomposes spend into attributed leads per channel. |
| What should leadership do next? | Reallocate budget from **high-CPL** to **low-CPL** channels. Shift X% of [weakest CPL] spend to [strongest CPL]. |

**Agent:** When building, ensure each view corresponds to one row. Reject features that do not map to any row.

---

## mmm/docs/03_ARCHITECTURE.md

# Architecture

## Overview

```
┌─────────────┐     ┌──────────────┐     ┌─────────────┐
│   Data      │────▶│  Transforms  │────▶│   Models    │
│   (CSV)     │     │  Adstock +   │     │ OLS/Ridge/  │
│             │     │  Saturation  │     │ Lasso/ElNet │
└─────────────┘     └──────────────┘     │ PyMC        │
                                         └──────┬──────┘
                                                │
                         ┌──────────────────────┼──────────────────────┐
                         ▼                      ▼                      ▼
                  ┌─────────────┐        ┌─────────────┐        ┌─────────────┐
                  │  Results    │        │  Viz       │        │  AI         │
                  │  Coef, CPL  │        │  Charts    │        │  Summary    │
                  └─────────────┘        └─────────────┘        └─────────────┘
```

---

## Components

### 1. Data Layer

- **Input:** Business data (CSV, Parquet) in `data/`
- **Required:** Date, target (e.g. sales), media spend columns, optional controls
- **Validation:** Shape, nulls, date range before fit

### 2. Transform Layer

- **Adstock:** Geometric (default for hackathon); per-channel θ. Weibull documented in 05_TRANSFORMS.md for reference.
- **Saturation:** Hill or log; per-channel α, k
- **Output:** Transformed media matrix for regression
- **UI:** Config tab — per-channel transform type (Adstock: Geometric/None, Saturation: Hill/Log/None), then theta/alpha/k; "Apply transforms" button

### 3. Model Layer

- **Frequentist:** OLS, Ridge, Lasso, ElasticNet — shared interface
- **Bayesian:** PyMC — separate path, returns posterior samples
- **Output:** Coefficients, **CPL** (cost per lead), contribution, (credible intervals for PyMC)

### 4. Presentation Layer

- **Streamlit:** Tabs for Data / Config / Fit / Results / AI
- **Charts:** Streamlit native (contribution, CPL, time series)
- **Tables:** Coefficients, CPL by channel

### 5. AI Layer

- **Input:** Aggregated results (no raw rows)
- **Providers:** OpenAI, Claude
- **Output:** Summary, interpretation, recommendations

---

## Data Flow

1. **Data tab** — User uploads or selects CSV → app validates schema → preview shown → stored in session_state
2. **Config tab** — User selects per-channel adstock type (Geometric / None) and saturation type (Hill / Log / None), sets theta and alpha/k where applicable → clicks "Apply transforms" → transformed matrix stored in session_state
3. **Fit tab** — User selects one or more models → clicks "Fit selected" or "Fit all" → each model fits → results stored in session_state["model_results"] keyed by model name
4. **Results tab** — Model selector drives all views: comparison table (R², RMSE), three decision sections (What/Why/What next), channel insights (decomposition, saturation curves, adstock carryover), business Q&A (auto-answered from model data)
5. **AI tab** — User selects summary mode or Q&A → credentials loaded from credentials.json → LLM called with results payload → response displayed

---

## mmm/docs/UX_FLOW.md

# UX Flow

## Screen Structure (Streamlit Tabs)

| Tab | Purpose | Enabled when |
|-----|---------|--------------|
| Data | Load, preview, validate input CSV | Always |
| Config | Transform params + regularization hyperparams | Data valid |
| Fit | Select models, run fit, view fit status | Transforms applied |
| Results | Model comparison, three decisions, channel insights, quick insights | ≥1 model fitted |
| AI | Executive summary + Business Q&A | ≥1 model fitted |

Tabs are always visible. Gating is done by showing a message inside the tab block using `if/else` — not by hiding tabs and not by calling `st.stop()`.

---

## User Journey

1. **Data** — Upload CSV or select from `data/`; select date_col, target_col, channel_cols; validate; preview
2. **Config** — Per-channel: set adstock theta (slider), saturation alpha/k (inputs); set regularization alpha and l1_ratio; click "Apply transforms"
3. **Fit** — Select models (multiselect: OLS / Ridge / Lasso / ElasticNet / PyMC); click "Fit selected" or "Fit all"; spinner + R² shown per model
4. **Results** — Model selector at top; comparison tables; three decision sections; expandable Channel Insights; expandable Quick Insights
5. **AI** — Provider setup; executive summary (single or compare-all); Business Q&A with templates + history

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
| `adstock_type` | `dict[str, str]` channel→"geometric" \| "none" | Config tab | Results |
| `saturation_params` | `dict[str, dict]` channel→`{"alpha": float, "k": float}` | Config tab | Results (saturation curves) |
| `saturation_type` | `dict[str, str]` channel→"hill" \| "log" \| "none" | Config tab | Results |
| `reg_alpha` | `float` | Config tab | Fit (Ridge/Lasso) |
| `l1_ratio` | `float` | Config tab | Fit (ElasticNet) |
| `transforms_applied` | `bool` | Config tab | Fit gate |
| `model_results` | `dict[str, ModelResult]` | Fit tab | Results, AI |
| `selected_model` | `str` (model name key) | Results tab | AI tab |
| `qa_history` | `list[dict]` — each: `{question, answer, model, timestamp}` | AI tab | AI tab |

---

## Key Interactions

| Interaction | Detail |
|-------------|--------|
| File picker | Shows CSV files from `mmm/data/`; if empty shows "No files yet — use uploader" |
| Column selectors | date_col (selectbox), target_col (selectbox), channel_cols (multiselect ≥1 required), control_cols (multiselect, optional — price/promo/seasonality; no transforms applied) |
| Transform sliders | One theta slider + alpha/k inputs per channel; re-applying overwrites previous |
| Reg params | Alpha input for Ridge/Lasso; alpha + l1_ratio for ElasticNet; stored in session_state |
| Apply transforms | Validates inputs, runs transform_media, sets transforms_applied = True |
| Model multiselect | OLS, Ridge, Lasso, ElasticNet, PyMC; can select any combination |
| Fit buttons | "Fit selected" + "Fit all"; spinner per model; R² shown after each |
| Model selector (Results) | Selectbox — switches all sections; stored as selected_model in session_state |
| Comparison tables | Always show all fitted models; model selector only affects detail sections below |
| Channel Insights | st.expander collapsed by default — opens on demand |
| Quick Insights | st.expander collapsed by default — compact summary, open on demand |
| AI summary | "Generate summary" button — triggers LLM call using selected_model |
| AI Q&A templates | 7 pre-built questions in selectbox; user can edit in text_area |
| Q&A history | Rendered before input in a container; newest entry at bottom |

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
  3 bullet points with computed numbers

─── st.expander("Channel Insights") ────────────────────
  st.area_chart: leads decomposition over time
  Per-channel cards (st.columns): CPL / adstock weeks / saturation badge
  st.line_chart: saturation curves (one per channel)

─── st.expander("Quick Insights", expanded=False) ──────
  2-column grid of st.metric / st.info cards:
  • Overall marketing CPL (€ per lead)
  • Best / worst channel
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
  Radio: [Single model (uses selected_model)] [Compare all]
  [Generate summary] button
  → LLM response rendered with st.markdown

─── Business Q&A ───────────────────────────────────────
  st.container (fixed height) — Q&A history:
    for each (question, answer, model) in qa_history:
      st.markdown("**Q:** question")
      st.markdown("A: answer")
      st.caption("Model: model_name")
  ─────────────────────────
  st.selectbox: question templates (7 options)
  st.text_area: question text (pre-filled from template; user can edit)
  [Ask] button → call get_summary → append to qa_history → rerender
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
