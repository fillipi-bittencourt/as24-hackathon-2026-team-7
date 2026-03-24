# Project improvements review

This review is focused on hackathon readiness, reliability, and clarity for judges and business stakeholders.

## what was scrutinized

- app behavior across data load, transforms, priors, info, fit, results, and ai steps
- validation and error handling paths that can fail during a live demo
- metric consistency and interpretation risks
- docs and implementation drift that can confuse the team

## improvements implemented now

- [x] **control column validation**
  - missing values in selected controls now fail validation early in `Data` tab
  - prevents fit-time crashes from hidden `NaN` values

- [x] **target quality validation**
  - negative target rows now fail validation
  - keeps lead attribution and cpl interpretation coherent

- [x] **api key override precedence**
  - manual key from sidebar now has highest precedence in `load_credentials`
  - avoids silent override conflicts with env vars or `credentials.json`

- [x] **credential parse feedback**
  - malformed or unreadable `credentials.json` now returns a direct user-facing error
  - makes ai setup failures easier to debug

- [x] **period filter semantics**
  - results period windows are now date-based with week arithmetic, not row-count based
  - `Last 4 weeks` now means 4 calendar weeks regardless of dataset grain

- [x] **mape robustness**
  - mape now uses only non-zero target rows
  - results table shows both mape value and coverage count

- [x] **csv read resilience**
  - upload and local file reads now include try/except with actionable errors
  - app no longer fails hard on malformed csv files

## high priority suggestions to finish next

- [x] **documentation baseline reset**
  - several docs previously described `app.py` as placeholder and the tab flow as not finalized
  - updated top-level and mmm readmes plus checklist to match the current runnable app

- [x] **single source of truth for app architecture**
  - align all docs on the current sidebar step flow including `Priors` and `Info`

- [x] **demo safe path definition**
  - add one click path for a reliable 8-10 minute live demo
  - include fallback mode if pyMC or ai latency is high

- [ ] **results export consistency**
  - current pdf export is text-first and practical
  - improve layout and include one chart image per export for executive readability

- [x] **ai output governance**
  - added explicit guardrails in prompt and docs for assumptions and confidence
  - recommendations now require numeric references in the AI prompt

## medium priority suggestions

- [ ] add lightweight smoke tests for core transforms and model interfaces
- [ ] add typed contracts for session state payload slices used by ai
- [ ] add a compact "data health" panel with row drops, missing values, and zero-target count
- [ ] show per-channel spend for selected period in results tables

## expected impact

- fewer demo-breaking errors in data and ai setup
- more trustworthy metrics for stakeholders
- easier handoff across team members with clearer docs and guided flow
