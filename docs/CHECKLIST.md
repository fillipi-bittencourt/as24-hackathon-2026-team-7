# Project Checklist

Use this checklist to verify the current app, not to rebuild it from scratch.

> For agents: treat this as the current verification and demo-readiness checklist.

---

## Phase 0 — Team alignment

- [ ] `TEAM.md` reflects the chosen business area and data source
- [ ] `docs/DECISIONS_FRAMEWORK.md` is aligned to MMM and the three leadership questions
- [ ] everyone agrees on the hackathon rule: usable first, not fancy

---

## Phase 1 — Environment and app startup

- [ ] confirm Python `3.9+`
- [ ] create `.venv` in `mmm/`
- [ ] if using the manual lightweight path, install `mmm/requirements-mvp.txt`
- [ ] run `mmm/run_app.sh`
- [ ] confirm the app opens without crashing
- [ ] confirm the sidebar step menu shows `Data`, `Overview`, `Config`, `Priors`, `Fit`, `Results`, `AI`
- [ ] confirm the separate sidebar `Guide` section opens the MMM explainer

---

## Phase 2 — First working run with sample data

- [ ] load `mmm/data/mmm_demo_sample.csv`
- [ ] validation passes with no blocking data errors
- [ ] data preview is visible and date range is correct
- [ ] `Overview` renders dataset diagnostics, target chart, and multicollinearity checks
- [ ] default transforms are `Geometric` and `Log`
- [ ] click `Apply transforms` successfully

---

## Phase 3 — Fit verification

- [ ] fit `OLS`
- [ ] fit `Ridge`
- [ ] confirm both appear in the comparison table
- [ ] confirm `Lasso` and `ElasticNet` are available for optional deeper comparison
- [ ] if `PyMC` is installed, confirm priors can be saved from the `Priors` tab before fitting
- [ ] if demoing `PyMC`, confirm a prepared saved state is available as the safest presentation path

---

## Phase 4 — Results verification

- [ ] Results step shows a model selector
- [ ] comparison table renders with `R²`, `RMSE`, `MAE`, and `MAPE non-zero`
- [ ] holdout validation diagnostics render for the fitted models when enough rows are available
- [ ] top section shows `Total leads`, `Media leads`, `Baseline leads`, and `Unexplained gap`
- [ ] the displayed decomposition adds cleanly to total leads
- [ ] channel table shows coefficients, CPL, contribution, and share
- [ ] chart variable filter works
- [ ] display period filter works
- [ ] channel insights use stacked bars over time
- [ ] exports work for results as `CSV` and `PDF`

---

## Phase 5 — AI verification

- [ ] credentials work from either `.env`, `credentials.json`, env vars, or manual sidebar override
- [ ] AI failures do not break the rest of the app
- [ ] `Executive short` and `In-depth` both generate usable output
- [ ] when enabled, multi-model context uses the fitted comparison set
- [ ] AI export works as `CSV` and `PDF`

---

## Phase 6 — Business data switch

- [ ] use the sample file as the fallback baseline
- [ ] place business data in `mmm/data/`
- [ ] confirm required fields exist: `date`, `target`, at least one `*_spend`
- [ ] re-run Data → Config → Fit → Results → AI on the business file
- [ ] note any business-data quirks in `mmm/data/README.md`

---

## Phase 7 — Demo-safe rehearsal

- [ ] rehearse the short path: sample data → defaults → `OLS` and `Ridge` → `Results` → `AI`
- [ ] keep the live path under 10 minutes
- [ ] have screenshots for `Results` and `AI`
- [ ] have a fallback plan if `PyMC` or AI is slow
- [ ] confirm the presentation machine can run the chosen commit

---

## Current recommended live path

1. Use the sample file if there is any uncertainty about business data.
2. Use the sidebar step menu to move from `Data` to `AI`.
3. Use `Guide` only if the audience needs a quick MMM explainer.
4. Keep the transform defaults.
5. Fit `OLS` and `Ridge`.
6. Show the top metrics, validation view, and channel breakdown in `Results`.
7. Generate one `In-depth` AI analysis if latency is acceptable.
8. If you want to show `PyMC`, prefer loading a prepared saved state instead of fitting it live on the presentation machine.

---

## Reference

| Need | Go to |
|------|-------|
| setup and troubleshooting | `mmm/docs/02_SETUP.md` |
| engineering build history | `mmm/docs/10_BUILD_MMM.md` |
| data schema | `mmm/docs/04_DATA_MODEL.md` |
| model details | `mmm/docs/06_MODELS.md` |
| AI payload and prompting | `mmm/docs/09_AI_ANALYSIS.md` |
| demo run plan | `docs/DEMO_PREP.md` |
| decision framing | `docs/DECISIONS_FRAMEWORK.md` |
