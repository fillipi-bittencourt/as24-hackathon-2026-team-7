# Changelog

This file tracks significant completed work in sequence order.

## How to use

- Add one new entry after each completed task item
- Use the next number in sequence
- Keep entries short and factual
- Include task, change, files, and reason

## Entries

### 007
- Task
  MVP verification
- Change
  Ran a browser smoke test against the live Streamlit app and marked the verified check steps in the build document
- Files
  `mmm/docs/10_BUILD_MMM.md`, `CHANGELOG.md`
- Reason
  Confirm the current MVP path works end to end before moving on to any further development or stretch work

### 006
- Task
  MVP app shell and task sync
- Change
  Replaced the placeholder app with the MVP Streamlit flow, wired Data, Config, Fit, Results, and AI tabs, and marked the completed build items in `mmm/docs/10_BUILD_MMM.md`
- Files
  `mmm/app.py`, `mmm/src/utils.py`, `mmm/docs/10_BUILD_MMM.md`
- Reason
  Move the repo from isolated modules to a working end-to-end MVP path and keep the build checklist in sync with the work already done

### 005
- Task
  MVP AI summary client
- Change
  Added credential loading, payload building, prompt generation, and the summary client for the single-model AI path
- Files
  `mmm/src/ai/__init__.py`, `mmm/src/ai/client.py`
- Reason
  Keep AI in the MVP without blocking the app when credentials or providers are missing

### 004
- Task
  MVP model layer
- Change
  Added the shared `ModelResult` contract, attribution builder, and MVP `OLS` and `Ridge` model classes
- Files
  `mmm/src/models/__init__.py`, `mmm/src/models/base.py`, `mmm/src/models/ols.py`, `mmm/src/models/ridge.py`
- Reason
  Let the app fit the first two models needed for the hackathon MVP and keep a shared output shape for Results and AI

### 003
- Task
  Transform functions
- Change
  Added geometric adstock, hill saturation, log saturation, and the shared media transform pipeline with the default spend path set to Geometric plus Log
- Files
  `mmm/src/transforms.py`
- Reason
  Make the config step produce model-ready float64 inputs with the repo default transformation order

### 002
- Task
  Data layer utilities
- Change
  Added the base `src` package and implemented CSV conversion and validation helpers for the MMM workflow
- Files
  `mmm/src/__init__.py`, `mmm/src/utils.py`
- Reason
  Give the app a reliable typed data entry point before wiring transforms and models

### 001
- Task
  Repo setup and MVP doc alignment
- Change
  Tightened the hackathon scope around a usable MVP, added demo prep assets, added a sample dataset, split fast MVP dependencies, and added a persistent changelog tracking rule for Cursor
- Files
  `README.md`, `mmm/README.md`, `docs/CHECKLIST.md`, `docs/DEMO_PREP.md`, `mmm/docs/02_SETUP.md`, `mmm/docs/03_ARCHITECTURE.md`, `mmm/docs/05_TRANSFORMS.md`, `mmm/docs/08_UX_FLOW.md`, `mmm/docs/09_AI_ANALYSIS.md`, `mmm/docs/10_BUILD_MMM.md`, `AGENT_README.md`, `.cursorrules`, `.gitignore`, `.cursor/rules/changelog-tracking.mdc`, `mmm/requirements-mvp.txt`, `mmm/data/README.md`, `mmm/data/mmm_demo_sample.csv`
- Reason
  Make the repo ready for a one-pass MVP build and ensure significant work is tracked as tasks are completed

## Entry template

### 000
- Task
- Change
- Files
- Reason
