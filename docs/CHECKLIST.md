# Project Checklist — Complete step-by-step

Work through this file top to bottom. Every step must be done before moving to the next phase.

> **For agents:** Follow steps in order. When the user says "what's next?", read where the last unchecked item is and proceed from there.

---

## Phase 0 — Before you start

- [ ] **0.1** `TEAM.md` shows `business_area = Marketing ROI`, `tech_stack = Streamlit`, `data_source = business data`
- [ ] **0.2** `docs/DECISIONS_FRAMEWORK.md` mapping table is filled — What / Why / What next for MMM
- [ ] **0.3** Everyone agrees on the hackathon target: **usable first, not fancy**
- [ ] **0.4** Everyone agrees on the MVP scope: `Data + Config + OLS + Ridge + Results + AI single-model summary`

---

## Phase 1 — Fast MVP environment

- [ ] **1.1** Clone the repo: `git clone <repo-url>`
- [ ] **1.2** Confirm Python 3.10+: `python3 --version`
- [ ] **1.3** Create a virtual environment:
  ```
  cd as24-hackathon-2026-team-7/mmm
  python3.10 -m venv .venv
  ```
- [ ] **1.4** Install the MVP dependency set:
  ```
  .venv/bin/pip install --upgrade pip
  .venv/bin/pip install -r requirements-mvp.txt
  ```
- [ ] **1.5** Verify the MVP environment:
  ```
  .venv/bin/python -c "import streamlit, pandas, numpy, statsmodels, sklearn, openai; print('OK')"
  ```
- [ ] **1.6** Optional only after MVP works: install `requirements.txt` for PyMC, Anthropic, and other stretch features

> **Agent:** See `mmm/docs/02_SETUP.md` for the full setup reference and troubleshooting table.

---

## Phase 2 — Data

Start with the committed demo file so the team can prove the app works before switching to business data.

- [ ] **2.1** Open `mmm/data/mmm_demo_sample.csv` and confirm the expected columns are present
- [ ] **2.2** Place business data in `mmm/data/` only after the sample run works
- [ ] **2.3** Validate schema manually: `date`, `target`, and at least one `*_spend` column; no all-null columns; at least 52 rows preferred
- [ ] **2.4** If business data is not ready, keep using the demo sample and proceed anyway

---

## Phase 3 — Build the app

The app is not yet implemented. The LLM builds it by following `mmm/docs/10_BUILD_MMM.md`.

- [ ] **3.1** Open Cursor in the `mmm/` folder
- [ ] **3.2** Send this prompt to the agent:
  ```
  Read mmm/docs/10_BUILD_MMM.md and implement the MMM Streamlit app. Start with the MVP only: Data, Config, OLS, Ridge, Results, and AI single-model executive summary. Use mmm/data/mmm_demo_sample.csv for the first successful run. Do one task item at a time: complete one [ ] item, verify it works, mark it [V], then proceed to the next. Do not skip items.
  ```
- [ ] **3.3** When defining `ModelResult`, load `mmm/docs/06_MODELS.md`
- [ ] **3.4** When building AI helpers, load `mmm/docs/09_AI_ANALYSIS.md`
- [ ] **3.5** Keep the recommended transform defaults simple: **Geometric adstock + Log saturation**
- [ ] **3.6** Do not move to stretch features until the MVP flow works end to end

---

## Phase 4 — MVP validation

### 4A — App startup

- [ ] **4A.1** `cd mmm && source .venv/bin/activate && streamlit run app.py` opens the app without errors
- [ ] **4A.2** All five tabs are visible: Data, Config, Fit, Results, AI
- [ ] **4A.3** Tabs show clear guidance messages when prerequisites are missing instead of crashing

### 4B — Data and Config

- [ ] **4B.1** Load `mmm_demo_sample.csv` and validation passes
- [ ] **4B.2** Data preview shows expected shape and usable types
- [ ] **4B.3** Config uses **Geometric** as the first adstock option
- [ ] **4B.4** Config uses **Log** as the first saturation option
- [ ] **4B.5** Clicking "Apply transforms" sets `session_state.X_transformed` and `session_state.y`
- [ ] **4B.6** Changing channel selection or transform settings clears stale fitted results

### 4C — Fit

- [ ] **4C.1** MVP model list shows `OLS` and `Ridge`
- [ ] **4C.2** Fit `OLS` → spinner shows → completes → status line appears
- [ ] **4C.3** Fit `Ridge` → same pattern
- [ ] **4C.4** Results tab becomes active once at least one model is fitted
- [ ] **4C.5** Stretch models (`Lasso`, `ElasticNet`, `PyMC`) are hidden, disabled, or clearly marked optional until implemented

### 4D — Results

- [ ] **4D.1** Model comparison table renders for fitted models
- [ ] **4D.2** The three decision sections render with real numbers
- [ ] **4D.3** "What should leadership do next?" is clearly framed as a **heuristic recommendation**, not a forecast
- [ ] **4D.4** Results explain that reported fit and attribution are in-sample

### 4E — AI summary

- [ ] **4E.1** `credentials.json` works with one provider
- [ ] **4E.2** AI tab generates a **single-model executive summary**
- [ ] **4E.3** AI failures show a human-readable message and do not break the rest of the app
- [ ] **4E.4** Compare-all and Q&A are treated as stretch features unless already implemented cleanly

---

## Phase 5 — Switch from sample to business data

- [ ] **5.1** Replace the sample file with business data only after the sample path works
- [ ] **5.2** Document business-data quirks in `mmm/data/README.md`
- [ ] **5.3** Re-run Data → Config → Fit → Results → AI on the business file

---

## Phase 6 — Demo prep

- [ ] **6.1** Fill in `docs/DEMO_PREP.md` with real numbers from the app
- [ ] **6.2** Rehearse the core flow once with the sample file as a backup
- [ ] **6.3** Rehearse once with business data if available
- [ ] **6.4** Keep the live demo path under 10 minutes
- [ ] **6.5** Prepare screenshots of Results and AI as backup
- [ ] **6.6** Confirm the presentation machine can run the exact demo commit

---

## Phase 7 — Stretch only after everything above is green

- [ ] Add `Lasso` and `ElasticNet`
- [ ] Add `PyMC`
- [ ] Add Channel Insights deep dives
- [ ] Add Quick Insights cards
- [ ] Add AI compare-all mode
- [ ] Add AI Q&A templates and history
- [ ] Add exports and scenario tools

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
