# Architecture

## Overview

```text
csv data
  -> validation and conversion
  -> media transforms
  -> model fitting
  -> results decomposition
  -> AI analysis and exports
```

The live app is organized into 6 tabs:

1. `Data`
2. `Config`
3. `Priors`
4. `Fit`
5. `Results`
6. `AI`

---

## Components

### 1. Data layer

- input source: CSV files from uploader or `data/`
- required fields: `date`, `target`, at least one `*_spend`
- optional fields: controls
- validation covers missing values, duplicates, negative spend, negative target, and invalid dates

### 2. Transform layer

- adstock: `Geometric` or `None`
- saturation: `Log`, `Hill`, or `None`
- defaults: `Geometric + Log`
- output: transformed design matrix used by all models

### 3. Model layer

- frequentist: `OLS`, `Ridge`, `Lasso`, `ElasticNet`
- bayesian: `PyMC`
- outputs: coefficients, contribution, baseline, predicted leads, CPL, fit metrics, and uncertainty for `PyMC`

### 4. Results layer

- comparison table across fitted models
- top summary metrics with bounded display attribution
- variable filtering
- period filtering
- stacked time-series decomposition
- CSV and PDF export

### 5. AI layer

- input: aggregated model outputs only
- providers: `OpenAI` and `Anthropic`
- modes: `Executive short` and `In-depth`
- optional cross-model context when multiple models are fitted
- exports: AI analysis as CSV and PDF

---

## Visualization stack

- app shell: `Streamlit`
- labeled bar charts and stacked bars: `Altair`
- PDF generation: `matplotlib`

---

## Data flow

1. `Data` loads and validates the file.
2. `Config` applies transforms and stores the transformed matrix.
3. `Priors` stores Bayesian settings for `PyMC`.
4. `Fit` runs selected models and stores `ModelResult` objects.
5. `Results` applies the selected model, channel filter, and period filter to visual outputs and exports.
6. `AI` builds an aggregated payload from current results and generates either a short or in-depth explanation.

---

## Demo architecture note

The safest live path is still:

- sample CSV
- default transforms
- `OLS` and `Ridge`
- `Results`
- `AI`

`PyMC` is available, but should be treated as optional in a live demo unless its latency has already been tested.
