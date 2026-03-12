# Wireframe prompt — Streamlit MMM app

Use this prompt to generate a wireframe or mockup for the current Marketing Mix Modeling Streamlit app. The output should be a visual or structural specification, not runnable code.

The app already exists. This prompt is for redesign, refinement, or visual review work.

---

## Copy-paste prompt

**Task:** Produce a Streamlit wireframe specification for a Marketing Mix Modeling data product. The app has 6 tabs and answers three executive questions: What is happening, why is it happening, and what should leadership do next.

**Context:**
- target variable: leads
- success metric: cost per lead
- models: OLS, Ridge, Lasso, ElasticNet, PyMC
- tab flow: Data → Config → Priors → Fit → Results → AI
- tabs are always visible and use message-based gating
- results include filters, exports, and stacked time-series decomposition
- AI supports short and in-depth analysis plus exports

**Components to allow:** `st.tabs`, `st.metric`, `st.dataframe`, `st.selectbox`, `st.multiselect`, `st.slider`, `st.number_input`, `st.button`, `st.file_uploader`, `st.expander`, `st.radio`, `st.markdown`, `st.caption`, `st.success`, `st.error`, `st.warning`, `st.info`, `st.spinner`, `st.columns`, plus Altair-style labeled bar and stacked bar chart placements in the layout notes.

**Required tab structure:**

### Tab 1 — Data
- CSV upload
- local file picker
- date column selector
- target selector
- channel multiselect
- control multiselect
- validation status
- date range preview

### Tab 2 — Config
- per-channel adstock selector
- per-channel saturation selector
- theta slider
- alpha and k inputs when needed
- regularization controls
- apply transforms button

### Tab 3 — Priors
- intercept controls
- prior family selector
- sigma controls
- sampler controls
- save priors button

### Tab 4 — Fit
- model multiselect
- fit selected button
- fit all button
- fit status feedback

### Tab 5 — Results
- model selector
- display period selector
- chart variable multiselect
- baseline and unexplained toggle
- comparison tables
- top metrics
- labeled lead comparison chart
- channel breakdown table
- CPL chart
- recommendation section
- channel insights expander with stacked bar chart over time
- quick insights expander
- export buttons for CSV and PDF

### Tab 6 — AI
- provider selector
- API key override note
- analysis depth selector
- include all fitted models toggle
- generate analysis button
- markdown analysis output
- export buttons for CSV and PDF

**Important labels to preserve:**
- Total leads
- Media leads
- Baseline leads
- Unexplained gap
- Top channel by CPL
- Model fit
- Overall marketing CPL

**Deliverable:** A wireframe or component map that shows every widget and major metric above in the correct tab and order. Use the current terminology and current 6-tab architecture. Do not output Python code.
