# Architecture

## Overview

```
┌─────────────┐     ┌──────────────┐     ┌─────────────┐
│   Data      │────▶│  Transforms  │────▶│   Models    │
│   (CSV)     │     │  Adstock +   │     │ OLS/Ridge/  │
│             │     │  Saturation  │     │ Stretch     │
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
- **Saturation:** Log first for MVP, Hill optional when the team wants more control
- **Output:** Transformed media matrix for regression
- **UI:** Config tab — per-channel transform type (Adstock: Geometric/None, Saturation: Log/Hill/None), then theta/alpha/k; "Apply transforms" button

### 3. Model Layer

- **Frequentist MVP:** OLS, Ridge
- **Stretch:** Lasso, ElasticNet
- **Bayesian stretch:** PyMC — separate path, returns posterior samples
- **Output:** Coefficients, CPL (cost per lead), contribution, (credible intervals for PyMC)

### 4. Presentation Layer

- **Streamlit:** Tabs for Data / Config / Fit / Results / AI
- **Charts:** Streamlit native (contribution, CPL, time series)
- **Tables:** Coefficients, CPL by channel

### 5. AI Layer

- **Input:** Aggregated results (no raw rows)
- **Providers:** one provider for MVP, optional second provider later
- **Output:** Single-model executive summary for MVP, richer comparison and Q&A later

---

## Data Flow

1. **Data tab** — User uploads or selects CSV → app validates schema → preview shown → stored in session_state
2. **Config tab** — User selects per-channel adstock type (Geometric / None) and saturation type (Log / Hill / None), sets theta and alpha/k where applicable → clicks "Apply transforms" → transformed matrix stored in session_state
3. **Fit tab** — User selects one or more models → clicks "Fit selected" or "Fit all" → each model fits → results stored in session_state["model_results"] keyed by model name. MVP target is OLS first, then Ridge
4. **Results tab** — Model selector drives all views: comparison table (R², RMSE), three decision sections (What/Why/What next), and optional channel insights after the MVP is stable
5. **AI tab** — User generates a single-model executive summary from the selected model. Compare-all and Q&A are stretch features
