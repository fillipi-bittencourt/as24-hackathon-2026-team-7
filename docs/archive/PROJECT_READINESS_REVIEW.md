# Project readiness review

One-time scrutiny of `as24-hackathon-2026-team-7` to answer: **Is it ready to just start? Will everything work seamlessly?**

---

## Summary

| Question | Answer |
|----------|--------|
| **Ready to “just start” and run the app?** | **No.** The app is a **placeholder**. `mmm/app.py` is 3 lines; `mmm/src/` has no implementation files (utils, transforms, models, ai client were removed). You must **build the app first** per Phase 3 of the checklist. |
| **Ready to set up env and then build?** | **Yes.** Setup (Python 3.10, venv, requirements, credentials, data folder) is documented and consistent. Doc links and references were fixed so agents and humans open the right files. |
| **Will everything work seamlessly after build?** | **Yes, if** you follow `mmm/docs/10_BUILD_MMM.md` one task item at a time, mark each [V] when done, and put a valid CSV in `mmm/data/` or use the uploader. |

---

## What was fixed (this pass)

1. **mmm/docs/02_SETUP.md** — Step 4 verify command imported `plotly`; `requirements.txt` does not list plotly. Verify now uses only packages in requirements: `streamlit, pandas, numpy, statsmodels, sklearn, pymc, arviz, openai, anthropic`.
2. **.cursorrules** — Build instruction pointed to `mmm/docs/BUILD_MMM.md` (missing). Updated to `mmm/docs/10_BUILD_MMM.md`.
3. **mmm/src/ai/__init__.py** — Comment referred to `AI_ANALYSIS.md` and `BUILD_MMM.md`. Updated to `09_AI_ANALYSIS.md` and `10_BUILD_MMM.md`.
4. **mmm/docs/04_DATA_MODEL.md** — ModelResult link pointed to `MODELS.md`. Updated to `06_MODELS.md`.
5. **mmm/docs/10_BUILD_MMM.md** — All references to `AI_ANALYSIS.md` updated to `09_AI_ANALYSIS.md`; `get_summary` description restored to “Return the response text. On any error …”.
6. **mmm/docs/09_AI_ANALYSIS.md** — Typo “** Concise prompt” fixed to “**Concise prompt**”.
7. **mmm/data/** — Directory was not in repo (no files). Added `mmm/data/.gitkeep` so the folder exists after clone and the file picker has a valid path. CSV files in `data/` remain gitignored.

---

## File-by-file consistency

### Root and docs

| File | Status | Notes |
|------|--------|-------|
| AGENT_README.md | OK | Correct paths to mmm/docs/10_BUILD_MMM.md, 04_DATA_MODEL.md, 02_SETUP.md. |
| README.md | OK | Points to AGENT_README, docs/README, checklist, mmm/. |
| TEAM.md | OK | business_area = Marketing ROI, tech_stack = Streamlit. |
| docs/README.md | OK | Links to 10_BUILD_MMM. |
| docs/CHECKLIST.md | OK | Phase 3 and Reference use mmm/docs/10_BUILD_MMM.md. |
| docs/DECISIONS_FRAMEWORK.md | OK | MMM mapping table filled (leads, CPL). |
| docs/DEMO_PREP.md | OK | Run instructions, 10_BUILD_MMM references. |
| docs/GUIDELINES.md | OK | No doc path issues. |
| docs/AI_COPILOT_GUIDE.md | OK | No doc path issues. |

### mmm/

| File | Status | Notes |
|------|--------|-------|
| mmm/app.py | Placeholder | 3 lines only; must be implemented per 10_BUILD_MMM Step 7. |
| mmm/requirements.txt | OK | streamlit, pandas, numpy, scipy, statsmodels, sklearn, pymc, arviz, matplotlib, openai, anthropic. No plotly. |
| mmm/.python-version | OK | 3.10. |
| mmm/credentials.json.example | OK | Schema matches 09_AI_ANALYSIS. |
| mmm/.gitignore | OK | .venv, credentials.json, data/*.csv, etc. |
| mmm/README.md | OK | Quick start, doc links use docs/02_SETUP, 04_DATA_MODEL, 10_BUILD_MMM, 09_AI_ANALYSIS. |
| mmm/data/.gitkeep | Added | Ensures mmm/data/ exists in repo. |

### mmm/src/

| File | Status | Notes |
|------|--------|-------|
| mmm/src/__init__.py | OK | Minimal. |
| mmm/src/utils.py | Missing | Deleted; must be recreated in Step 1. |
| mmm/src/transforms.py | Missing | Deleted; must be recreated in Step 2. |
| mmm/src/models/__init__.py | OK | Points to 06_MODELS and 10_BUILD_MMM. |
| mmm/src/models/base.py | Missing | Deleted; Step 3. |
| mmm/src/models/ols.py | Missing | Deleted; Step 3. |
| mmm/src/models/ridge.py | Missing | Deleted; Step 3. |
| mmm/src/models/lasso.py | Missing | Deleted; Step 3. |
| mmm/src/models/elasticnet.py | Missing | Deleted; Step 3. |
| mmm/src/models/pymc_model.py | Missing | Deleted; Step 4. |
| mmm/src/ai/__init__.py | Fixed | Now points to 09_AI_ANALYSIS and 10_BUILD_MMM. |
| mmm/src/ai/client.py | Missing | Deleted; Step 6. |

### mmm/docs/

| File | Status | Notes |
|------|--------|-------|
| 01_INDEX.md | OK | Numbered doc names. |
| 02_SETUP.md | Fixed | Verify step no longer uses plotly. |
| 03_ARCHITECTURE.md | OK | 05_TRANSFORMS.md reference. |
| 04_DATA_MODEL.md | Fixed | ModelResult link → 06_MODELS.md. |
| 05_TRANSFORMS.md | OK | — |
| 06_MODELS.md | OK | References 14_IMPROVEMENTS, 05_TRANSFORMS. |
| 07_TECHNICAL_SPEC.md | OK | Refers to 06_MODELS, 04_DATA_MODEL, 10_BUILD_MMM. |
| 08_UX_FLOW.md | OK | — |
| 09_AI_ANALYSIS.md | Fixed | “** Concise prompt” typo. |
| 10_BUILD_MMM.md | Fixed | All AI_ANALYSIS → 09_AI_ANALYSIS; get_summary text. |
| 11_WIREFRAME_PROMPT.md | OK | References 10_BUILD_MMM. |
| 12_PROJECT_REVIEW_PROMPT.md | Snapshot | Review prompt only; source of truth is 10_BUILD_MMM. |
| 13_REVIEW_RESPONSE.md | OK | References 10_BUILD_MMM, BUILD_MMM naming. |
| 14_IMPROVEMENTS.md | OK | — |

---

## Remaining / known gaps

1. **App not implemented** — Until the app is built from 10_BUILD_MMM, `streamlit run app.py` only runs a placeholder. No tabs, no data/transform/fit/results/AI logic.
2. **12_PROJECT_REVIEW_PROMPT.md** — Contains an embedded snapshot of build instructions that may lag. Implementers should use 10_BUILD_MMM.md; 12 is for review only.
3. **Control coefficients in AI payload** — 13_REVIEW_RESPONSE notes that ModelResult does not expose control variable names/coefficients; build_payload may need to derive them from the model (e.g. OLS params for control columns). Not fixed in docs; builder must handle when control_cols exist.
4. **GUIDELINES.md** — Now aligned: default is Streamlit + pandas with Streamlit native charts; "This project" column says no Plotly. Gap closed.

---

## How to “just start” (recommended sequence)

1. **Environment**  
   Follow `mmm/docs/02_SETUP.md`: Python 3.10+, create `mmm/.venv`, install from `mmm/requirements.txt`, run the verify command (no plotly). Copy `credentials.json.example` → `credentials.json` and set one API key.

2. **Data**  
   Put a CSV in `mmm/data/` (or use upload in the app after build). Schema: `date`, `target` (leads), one or more `*_spend` columns. See `mmm/docs/04_DATA_MODEL.md`. If you have no data, use the synthetic-data prompt in CHECKLIST Phase 2 Path B.

3. **Build the app**  
   Open Cursor in `mmm/` and run the prompt from CHECKLIST Phase 3.2: read `mmm/docs/10_BUILD_MMM.md` and implement **one task item at a time**, marking [V] when each is done. Do not batch multiple tasks in one go.

4. **Run**  
   `cd mmm && source .venv/bin/activate && streamlit run app.py` → http://localhost:8501.

5. **Validate**  
   Use CHECKLIST Phase 4 (4A–4G) to test tabs, data load, config, fit, results, AI, and stability.

---

## Conclusion

- **Specs and setup:** Consistent and ready. Doc links and references are corrected; setup verify matches requirements; data directory exists.
- **App:** Not built yet. Building from 10_BUILD_MMM and then following the checklist will get you to a working, demo-ready MMM app.
