# Project Checklist — Complete step-by-step

Work through this file top to bottom. Every step must be done before moving to the next phase.

> **For agents:** Follow steps in order. When the user says "what's next?", read where the last unchecked item is and proceed from there.

---

## Phase 0 — Before you start (pre-decided, verify only)

- [ ] **0.1** `TEAM.md` shows `business_area = Marketing ROI`, `tech_stack = Streamlit`, `data_source = business data`
- [ ] **0.2** `docs/DECISIONS_FRAMEWORK.md` mapping table is filled — What / Why / What next for MMM
- [ ] **0.3** You have access to business data (CSV export) OR are ready to generate synthetic data

> These are pre-decided. Do not re-open scope discussions. If anything is wrong here, fix it before continuing.

---

## Phase 1 — Environment setup

- [ ] **1.1** Clone the repo: `git clone <repo-url>`
- [ ] **1.2** Confirm Python 3.10+: `python3 --version`
  - If not: `pyenv install 3.10.14 && pyenv local 3.10.14`
- [ ] **1.3** Create virtual environment:
  ```
  cd as24-hackathon-2026-team-7/mmm
  python3.10 -m venv .venv
  ```
- [ ] **1.4** Install dependencies (PyMC takes ~2 min — normal):
  ```
  .venv/bin/pip install --upgrade pip
  .venv/bin/pip install -r requirements.txt
  ```
- [ ] **1.5** Verify all packages installed:
  ```
  .venv/bin/python -c "import streamlit, pandas, numpy, statsmodels, sklearn, pymc, arviz, openai, anthropic; print('OK')"
  ```
  If any import fails: re-run `.venv/bin/pip install -r requirements.txt`

> **Agent:** See `mmm/docs/02_SETUP.md` for the full setup reference and troubleshooting table.

---

## Phase 2 — Data

- [ ] **2.1** Prepare the CSV — **two paths, pick one:**

  **Path A — Business data is ready:**
  Export with columns: `date` (weekly), `target` (**leads**), and one or more `*_spend` columns (e.g. `tv_spend`, `digital_spend`). See `mmm/docs/04_DATA_MODEL.md` for the full schema.

  **Path B — Data not ready (unblock now, swap later):**
  Use this prompt to generate synthetic data:
  ```
  Generate a CSV with 104 rows (2 years of weekly data) for a Marketing Mix Model.
  Columns: date (weekly, starting 2022-01-03), target (**leads**, e.g. 500–5000 float),
  tv_spend (0–50000), digital_spend (0–30000), search_spend (0–20000), social_spend (0–15000).
  Make target loosely correlated with spend. Add some seasonality.
  Save as mmm/data/mmm_synthetic.csv
  ```

- [ ] **2.2** Place CSV in `mmm/data/`
- [ ] **2.3** Validate schema manually: open the CSV and confirm `date`, `target`, and at least one `*_spend` column exist, with no all-null columns and at least 52 rows

> **Agent:** If generating synthetic data, use the prompt in 2.1 Path B verbatim. File must go in `mmm/data/`.

---

## Phase 3 — Build the app

**Pre-flight (do once before 3.2):** From repo root run:
`cd mmm && .venv/bin/python -c "import streamlit, pandas, numpy, statsmodels, sklearn; print('OK')"`  
If this fails, complete Phase 1 first. Ensure at least one CSV is in `mmm/data/` (or you will use the uploader).

The app is not yet implemented. The LLM builds it by following `mmm/docs/10_BUILD_MMM.md`. Do **one task item at a time**: complete the task, mark it [V] in the doc, then do the next (see "Build order and verification" and the [ ] / [V] checkboxes in 10_BUILD_MMM.md).

- [ ] **3.1** Open Cursor in the `mmm/` folder (not the repo root)
- [ ] **3.2** Send this prompt to the agent:
  ```
  Read mmm/docs/10_BUILD_MMM.md and implement the full MMM Streamlit app. Data will be in mmm/data/. Do **one task item at a time**: complete one [ ] item, verify it works, mark it [V], then proceed to the next. Do not skip items. (Load only 10_BUILD_MMM.md — no need to load other docs.)
  ```
- [ ] **3.2b** *(If resuming a partial build)* Send this instead:
  ```
  Open mmm/docs/10_BUILD_MMM.md. Find the first task line that still has [ ] (not [V]). Implement only that one task, run its Check step, then mark it [V] and stop. Do not continue to the next task.
  ```
- [ ] **3.3** While the LLM builds, run these in parallel:

  | Who | Task |
  |-----|------|
  | Data person | Clean the CSV, confirm column names, document any quirks in `mmm/data/README.md` or inline |
  | App person | Monitor LLM output; unblock on errors; do not let it skip to a later step |
  | Story person | Fill in the narrative template (see Phase 5) |

- [ ] **3.4** After each task item, run the relevant check (run the app or test that item). Mark the task [V] in 10_BUILD_MMM.md only when it works. Do not proceed to the next task until the current one is marked [V].

---

## Phase 4 — Testing and review

Run these checks in order. Fix any failure before moving on. Do not skip.

### 4A — App startup

- [ ] **4A.1** `cd mmm && source .venv/bin/activate && streamlit run app.py` — app opens at `http://localhost:8501` without errors
- [ ] **4A.2** All five tabs visible: Data, Config, Fit, Results, AI
- [ ] **4A.3** Fit, Results, and AI tabs show a "not ready" message (not a crash) when data hasn't been loaded

### 4B — Data tab

- [ ] **4B.1** Upload the business CSV → validation passes (green status)
- [ ] **4B.2** `date_col`, `target_col`, `channel_cols` are selectable in dropdowns
- [ ] **4B.3** Data preview shows correct shape and types
- [ ] **4B.4** Test validation failures:
  - Load a CSV missing the `date` column → clear error message (not a Python traceback)
  - Load a CSV with an unparseable date format → clear error message
- [ ] **4B.5** After loading valid data: `session_state.valid = True`, Fit tab becomes active

### 4C — Config tab

- [ ] **4C.1** Each channel has inputs for theta (adstock), alpha and k (saturation)
- [ ] **4C.2** Click "Apply transforms" → no error; `session_state.X_transformed` set
- [ ] **4C.3** Changing a parameter and re-applying overwrites the previous transform

### 4D — Fit tab

- [ ] **4D.1** All five models selectable: OLS, Ridge, Lasso, ElasticNet, PyMC
- [ ] **4D.2** Fit OLS → spinner shows → completes → "OLS: R² = X.XX" displayed
- [ ] **4D.3** Fit Ridge, Lasso, ElasticNet → same pattern, each stores result
- [ ] **4D.4** Fit PyMC → note "PyMC may take longer" visible → completes → result stored
- [ ] **4D.5** "Fit all" button fits all five and stores all in `session_state.model_results`
- [ ] **4D.6** Results tab becomes active once at least one model is fitted

### 4E — Results tab

- [ ] **4E.1** **Model comparison table** shows all fitted models with R² and RMSE columns — sortable
- [ ] **4E.2** **Coefficient comparison table** shows channels × model names
- [ ] **4E.3** **Model selector** dropdown switches all sections to the selected model
- [ ] **4E.4** "What is happening?" section: 2–3 KPI metrics visible with real numbers
- [ ] **4E.5** "Why is it happening?" section: **CPL** bar chart renders with real channel names (not `channel_0`)
- [ ] **4E.6** "What should leadership do next?" section: bullet list with specific numbers
- [ ] **4E.7** **Channel insights** section:
  - **Leads** decomposition stacked area chart renders
  - Each channel has a card showing **CPL** (€ per lead), adstock carryover (weeks), saturation badge (green/amber/red)
  - At least one saturation curve plot renders with current spend marked
- [ ] **4E.8** **Quick Insights** section (business questions): all questions have computed answers (no "N/A" unless spend data is genuinely missing)
- [ ] **4E.9** PyMC results show credible intervals (lower/upper) on coefficients and **CPL**

### 4F — AI tab

- [ ] **4F.1** With valid `credentials.json`: provider label shows, no error on tab open
- [ ] **4F.2** Without `credentials.json`: clear message shown with sidebar input as fallback
- [ ] **4F.3** "Generate summary" (single model mode) → LLM response appears in markdown
- [ ] **4F.4** "Generate summary" (compare-all mode) → response mentions multiple models
- [ ] **4F.5** Question templates dropdown shows all 7 pre-built questions
- [ ] **4F.6** Select a template → text populates the text area → click "Ask" → answer appears
- [ ] **4F.7** Ask a follow-up question → Q&A history shows both Q&A pairs
- [ ] **4F.8** With wrong API key: human-readable error message (no traceback); app does not crash
- [ ] **4F.9** AI tab disabled/shows message when no models are fitted

### 4G — Stability

- [ ] **4G.1** Reload the page (Streamlit re-run) while app is running — no crash
- [ ] **4G.2** Switch tabs rapidly — no state loss
- [ ] **4G.3** Fit a second model after the first — comparison table updates without requiring a page reload
- [ ] **4G.4** App handles an empty `session_state` gracefully on every tab (no `KeyError`)

---

## Phase 5 — Polish and storytelling

Time-box this phase to **2 hours maximum**. Use Streamlit defaults; only change what looks broken.

### 5A — Narrative

- [ ] **5.1** Fill in the narrative template with real model output numbers:
  ```
  What is happening:    Total leads contribution: [X], R²: [X], top channel: [name] at €[X] per lead (CPL)
  Why it is happening:  [Channel A] CPL €[X], adstock [N] weeks. [Channel B] saturating. [Channel C] high CPL.
  What next:            Shift [N]% from [highest CPL] to [lowest CPL]. Expected improvement in cost per lead.
  ```
- [ ] **5.2** Every KPI, chart title, and table column uses plain English — no snake_case, no Python variable names
- [ ] **5.3** "What next?" section has specific numbers, not vague suggestions
- [ ] **5.4** Use AI tab to generate narrative: *"Write a 3-paragraph executive summary for a board presentation based on these MMM results. Focus on overall effectiveness, channel performance, and one specific budget reallocation with expected impact."*

### 5B — UX

- [ ] **5.5** Each tab has a 1-sentence description at the top ("Upload your marketing data CSV and select columns")
- [ ] **5.6** KPIs in "What is happening?" use `st.metric` with delta indicators
- [ ] **5.7** **CPL** bar chart: top-performing channel (lowest CPL) uses a consistent highlight colour across all charts
- [ ] **5.8** All numbers formatted: currency as `€X,XXX`, **CPL as €X per lead**, percentages as `X%`
- [ ] **5.9** Tables use `st.dataframe` (sortable, not static markdown)
- [ ] **5.10** Loading spinners during model fitting; no blank screens

> **Agent:** Every element must tie to What/Why/What next. Remove any chart or element that doesn't support those three questions.

---

## Phase 6 — Credentials and final setup

- [ ] **6.1** Copy `credentials.json.example` → `credentials.json` if not already done
- [ ] **6.2** Fill in `preferred_provider` and the matching API key
- [ ] **6.3** Open AI tab → click "Generate summary" → confirm response appears with real model output
- [ ] **6.4** Test one Q&A template question → answer is relevant to the actual data
- [ ] **6.5** Confirm `credentials.json` is NOT tracked by git: `git status` should not show it

---

## Phase 7 — Demo preparation

- [ ] **7.1** Fill in the demo script in `docs/DEMO_PREP.md` with real numbers from the app
- [ ] **7.2** Run the full demo flow once (data → config → fit → results → AI) while someone times it — must be under 10 min
- [ ] **7.3** Rehearse once with all presenters — every section has a named owner
- [ ] **7.4** Prepare backup: take screenshots of every tab with real data loaded; save a screen recording as fallback
- [ ] **7.5** Confirm app runs on the **presentation machine** (not just your dev machine)

---

## Phase 8 — Deliverables check

Tick every item. If anything is unchecked, do not present.

- [ ] **8.1** `cd mmm && source .venv/bin/activate && streamlit run app.py` opens the app on the presentation machine without errors
- [ ] **8.2** Business data (or clean synthetic) loaded in `mmm/data/` and the Data tab shows green
- [ ] **8.3** At least OLS is fitted and Results tab shows real numbers
- [ ] **8.4** Three decision sections visible with real KPIs and specific recommendations
- [ ] **8.5** Channel insights section shows saturation badges and at least one chart
- [ ] **8.6** AI tab works with real credentials — test "Generate summary" live
- [ ] **8.7** Demo script is filled in, timed, rehearsed
- [ ] **8.8** Backup screenshots / recording ready and accessible

---

## Phase 9 — Pre-presentation (30 min before)

- [ ] **9.1** App running on presentation machine, results visible — do not start from a blank state
- [ ] **9.2** Browser: zoom 100%, window maximised, no other tabs open
- [ ] **9.3** Presenter knows the three numbers by heart: total contribution (leads), top channel **CPL €X per lead**, reallocation recommendation
- [ ] **9.4** AI usage summary ready (one sentence): *"We used Cursor/Claude to build the entire app in 2 days from a specification file, and the AI tab generates the board brief automatically from model results."*
- [ ] **9.5** Backup open in a second browser tab or on a second screen

---

## Stretch goals (only if all phases above are complete)

- [ ] Scenario slider: "What if we shift €X from Channel A to B?"
- [ ] Export results table as CSV (board deck attachment) — see 10_BUILD_MMM.md Step 5 for spec
- [ ] Model comparison narrative: explain in plain text why Ridge differs from OLS
- [ ] Analyst on the team delivers the presentation (judge bonus points)

---

## Reference

| Need | Go to |
|------|-------|
| Environment problems | `mmm/docs/02_SETUP.md` |
| Build the app | `mmm/docs/10_BUILD_MMM.md` |
| Data schema | `mmm/docs/04_DATA_MODEL.md` |
| Model details | `mmm/docs/06_MODELS.md` |
| AI credentials and prompt | `mmm/docs/09_AI_ANALYSIS.md` |
| Demo script template | `docs/DEMO_PREP.md` |
| Three executive questions | `docs/DECISIONS_FRAMEWORK.md` |
