# Wireframe prompt — Streamlit MMM app

Use this prompt to generate a **wireframe or mockup** for the Marketing Mix Modeling Streamlit app. The output should be a visual or structural specification (e.g. annotated sketch, Figma outline, or a bullet list of Streamlit components and layout) — **not runnable code**. The app is built separately using `mmm/docs/10_BUILD_MMM.md`.

**Streamlit reference:** https://docs.streamlit.io — use only Streamlit-native components: `st.tabs`, `st.metric`, `st.dataframe`, `st.bar_chart`, `st.area_chart`, `st.line_chart`, `st.selectbox`, `st.multiselect`, `st.slider`, `st.number_input`, `st.button`, `st.file_uploader`, `st.expander`, `st.radio`, `st.text_area`, `st.markdown`, `st.caption`, `st.success`, `st.error`, `st.warning`, `st.info`, `st.spinner`, `st.columns`. No custom HTML/CSS/JS; no Plotly or other chart libs.

---

## Copy-paste prompt (for an AI or designer)

**Task:** Produce a Streamlit wireframe specification for a Marketing Mix Modeling (MMM) data product. The app has five tabs and answers three executive questions: What is happening? Why? What should leadership do next?

**Context:**
- **Target variable:** leads (the outcome we model).
- **Success metric:** cost per lead (CPL), in € per lead. Lower CPL = better. We do **not** use ROI.
- **Models:** User can fit and compare five models — OLS, Ridge, Lasso, ElasticNet, PyMC. Results are shown per selected model with an option to compare all.
- **Flow:** Data → Config (transforms) → Fit → Results → AI. Each step is gated; user clicks to load data, apply transforms, fit models, and view results. Tabs are always visible; show a message inside the tab when the step is not ready (e.g. "Load data first") instead of hiding the tab.

**Streamlit components to use:** Use only native Streamlit: `st.tabs`, `st.metric`, `st.dataframe`, `st.bar_chart`, `st.area_chart`, `st.line_chart`, `st.selectbox`, `st.multiselect`, `st.slider`, `st.number_input`, `st.button`, `st.file_uploader`, `st.expander`, `st.radio`, `st.text_area`, `st.markdown`, `st.caption`, `st.success`, `st.error`, `st.warning`, `st.info`, `st.spinner`, `st.columns`. Layout: `st.set_page_config(layout="wide")`, no sidebar except for optional API key override.

**What we measure (include every one in the wireframe):**

| Category | What we measure | Where it appears |
|----------|------------------|------------------|
| **Target** | Leads (count) — the outcome column | Data tab (column choice); Results (total attributed leads) |
| **Efficiency** | Cost per lead (CPL), € per lead, per channel and overall | Results: metrics, table, bar chart; Quick Insights; Channel cards; AI payload |
| **Attribution** | Attributed leads per channel (contribution), share % | Results table (Contribution, Share %); decomposition area chart; Channel cards |
| **Baseline** | Non-media baseline (intercept + residual), baseline % | Results metrics; Quick Insights “Media vs baseline”; decomposition chart |
| **Model fit** | R², RMSE | Results “What is happening?”; comparison table; Quick Insights; AI |
| **Coefficients** | Per-channel (and per-control) regression coefficient | Results table; coefficient comparison table; PyMC: CI lower/upper |
| **CPL uncertainty** | PyMC only: CPL lower/upper (94% HDI) | Results table when PyMC selected |
| **Transforms** | Per channel: Adstock type (Geometric / None), theta; Saturation type (Hill / Log / None), alpha, k | Config tab; Results Channel Insights (transform type, carryover weeks, saturation badge) |
| **Adstock carryover** | Weeks until effect decays to 5% | Channel Insights cards (when Geometric) |
| **Saturation status** | Under- / near / over-saturated (vs k), badge (green/amber/red) | Channel Insights (when Hill); Quick Insights “Over-saturated channels” |
| **Spend** | Total and average weekly spend per channel | Channel Insights cards |
| **Recommendation** | Reallocation % from worst CPL to best CPL channel | “What should leadership do next?”; Quick Insights “Recommended shift” |
| **AI** | Executive summary, Q&A history (question, answer, model) | AI tab |

**Tab 1 — Data**
- `st.file_uploader` for CSV.
- File picker (e.g. dropdown from `data/*.csv`); if empty, show “No files in data/ — use uploader above”.
- Column selectors: `st.selectbox` for date column, `st.selectbox` for target column (leads), **`st.multiselect` for channels to include** (label e.g. "Channels to include (deselect to remove)" — ≥1 required), `st.multiselect` for control columns (optional). User can **add or remove channels** by selecting/deselecting; after data is loaded, the same selectors stay visible so the user can change the channel/control set without re-uploading (app re-validates and resets transforms/fits).
- On validate: `st.success` with row count and date range caption, or `st.error` with message list. Show date range: “Date range: YYYY-MM-DD to YYYY-MM-DD — N rows”.

**Tab 2 — Config**
- Shown only when data is valid. Otherwise show `st.warning("Load and validate data in the Data tab first.")`.
- Per channel (for each selected channel): **Transform type** — `st.selectbox` Adstock: [Geometric, None], `st.selectbox` Saturation: [Hill, Log, None]. Then, if Geometric: `st.slider` theta (0.1–0.9). If Hill: `st.number_input` alpha, `st.number_input` k.
- Global: `st.number_input` Ridge/Lasso alpha, `st.number_input` ElasticNet l1_ratio.
- Button: “Apply transforms”. After apply, show success; if models were already fitted, show warning that they were cleared.

**Tab 3 — Fit**
- Shown only when transforms are applied. Otherwise show `st.warning("Apply transforms in the Config tab first.")`.
- `st.multiselect` models: OLS, Ridge, Lasso, ElasticNet, PyMC.
- Buttons: “Fit selected”, “Fit all”. During fit: `st.spinner` per model. After each: “✓ ModelName: R² = X, RMSE = Y”. Optional: `st.info` “PyMC may take 1–2 minutes.”

**Tab 4 — Results**
- Shown only when at least one model is fitted. Otherwise show `st.info("Fit at least one model in the Fit tab to see results.")`.
- **Model selector:** `st.selectbox` “View model:” (list of fitted model names). All sections below use the selected model.
- **Model comparison:** `st.dataframe` — rows = models, columns = R², RMSE. Below: `st.dataframe` coefficient comparison — rows = channels, columns = model names.
- **What is happening?** Three `st.metric`: (1) Total media contribution (attributed leads), (2) Top channel by CPL (name + €X per lead), (3) Model fit (R², RMSE).
- **Why is it happening?** `st.dataframe` — columns: Channel, Coefficient, CPL (€ per lead), Contribution (leads), Share (%). For PyMC only: add Coeff CI and CPL CI columns. Below: `st.bar_chart` CPL by channel (ascending — best first).
- **What should leadership do next?** Three bullet points: invest in lowest CPL, reduce highest CPL, reallocate N% from highest to lowest CPL.
- **Channel Insights** (`st.expander`, collapsed by default): `st.area_chart` — leads decomposition over time (date index, stacked: baseline + each channel contribution). Per-channel cards: spend total, contribution (leads), CPL, transform types (Adstock, Saturation), adstock carryover weeks, saturation badge. For Hill channels only: `st.line_chart` saturation curve (spend vs response).
- **Quick Insights** (`st.expander`, collapsed): 2-column grid of cards — Overall marketing CPL, Best channel (€/lead), Worst channel (€/lead), Media vs baseline %, Over-saturated channels list, Recommended shift.

**Tab 5 — AI**
- Shown only when at least one model is fitted. Otherwise show `st.info("Fit at least one model first.")`.
- Credentials: if missing, show message and `st.sidebar.text_input` for API key override. `st.radio` provider: OpenAI | Anthropic.
- **Executive summary:** `st.radio` Single model | Compare all. Button “Generate summary”. Response in `st.markdown`.
- **Business Q&A:** Scrollable history (each: **Q:** question, **A:** answer, caption with model name). Then `st.selectbox` question templates (7 options), `st.text_area` for question, “Ask” button. “Clear history” button.

**Deliverable:** A wireframe or component map that shows every Streamlit widget and every metric above in the correct tab and order. Use Streamlit component names and our terminology (leads, CPL, contribution, baseline, R², RMSE, adstock type, saturation type, carryover, saturation badge). Do not output Python code — only structure and labels for building the UI later from 10_BUILD_MMM.md.
