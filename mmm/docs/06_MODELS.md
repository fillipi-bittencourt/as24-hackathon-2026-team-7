# MMM Models — Specifications

Marketing Mix Modeling (MMM) attributes sales/outcomes to marketing channels. Core concepts: **adstock** (carryover effect), **saturation** (diminishing returns).

**Streamlit docs:** https://docs.streamlit.io/

---

## Frequentist Models (4)

### 1. OLS (Ordinary Least Squares)

**Lib:** `statsmodels.api.OLS`

**Description:** Linear regression with adstock + saturation transforms. Baseline, interpretable.

---

### 2. Ridge

**Lib:** `sklearn.linear_model.Ridge`

**Description:** L2 regularization. Stable coefficients when channels are correlated.

---

### 3. Lasso

**Lib:** `sklearn.linear_model.Lasso`

**Description:** L1 regularization. Variable selection; can zero out weak channels.

---

### 4. ElasticNet

**Lib:** `sklearn.linear_model.ElasticNet`

**Description:** Mix of L1 and L2. Balances variable selection and stability.

---

## Bayesian Model (1)

### 5. PyMC Bayesian Linear Regression

**Lib:** `pymc`

**Description:** Bayesian linear regression on the already-transformed design matrix. Priors encode domain knowledge for intercept, channel coefficients, control coefficients, and noise. Outputs credible intervals for coefficients and CPL.

---

## Shared Transforms

**Adstock:** Geometric decay `x_t = x_t + θ * x_{t-1}` (or Weibull).

**Saturation:** Hill `f(x) = x^α / (k^α + x^α)` or `log(1 + x)`.

See [05_TRANSFORMS.md](05_TRANSFORMS.md).

---

## ModelResult — shared output interface

Every model returns a `ModelResult` dataclass with these fields. All are required.

```python
@dataclass
class ModelResult:
    model_name:        str                    # e.g. "OLS", "Ridge", "PyMC"
    channel_names:     list[str]              # channel names in order
    coefficients:      dict[str, float]       # scalar coefficient per channel
    intercept:         float
    cpl:               dict[str, float]       # cost per lead: sum(raw_spend[ch]) / sum(contribution[ch]); € per lead
    contribution:      dict[str, np.ndarray]  # VECTOR per channel (length = n_rows); needed for decomposition chart
    contribution_pct:  dict[str, float]       # scalar: sum(contribution[ch]) / sum(y_pred)
    y_pred:            np.ndarray             # 1D, length = n_rows
    baseline:          np.ndarray             # 1D, length = n_rows — clipped to >= 0
    baseline_pct:      float                  # sum(baseline) / sum(y_pred)
    r_squared:         float
    rmse:              float
    # PyMC only — absent on frequentist models:
    coefficient_lower: dict[str, float] = None
    coefficient_upper: dict[str, float] = None
    cpl_lower:         dict[str, float] = None
    cpl_upper:         dict[str, float] = None
```

**Key distinction:** `contribution[ch]` is a **vector** (one value per time period, shape `(n_rows,)`). Use `sum(contribution[ch])` to get the total attributed **leads** for a channel. The decomposition chart plots each channel's full vector as a time-series band.

**Checking for PyMC fields:** Use `result.coefficient_lower is not None` before accessing CI fields.

---

## Statistics and library notes

These notes ensure the models and attribution are statistically consistent. Implementers should follow them.

### Linear model and attribution

We fit **linear regression** on transformed media (and optional controls):  
`E[y] = intercept + Σ β_i · x_i`.  
So the **contribution** of predictor `i` in period `t` is `β_i · x_{i,t}`. That is exactly `contribution[ch] = coefficients[ch] * X[:, i]` (vector over time). Total attributed leads for a channel = `sum(contribution[ch])`. **CPL** = total raw spend for that channel / total attributed leads = € per lead. No scaling of X or y is applied; coefficients are in **raw units** (leads per unit of transformed input) so CPL stays interpretable.

### OLS (statsmodels)

- **API:** `sm.OLS(y, sm.add_constant(X, has_constant='add')).fit()`. `params[0]` = intercept, `params[1:]` = coefficients in **column order** (channels first, then controls if present).
- **Coefficient slice when controls exist:** `channel_names` has length `n_channels`; X has shape `(n, n_channels + n_controls)`. Use `params[1:1+n_channels]` for channel coefficients and `params[1+n_channels:]` for control coefficients. Build the `coefficients` dict and `contribution` only for **channels**; baseline = `y_pred - sum(contribution[ch])` then absorbs intercept, control effects, and residual.
- **R²:** `result.rsquared`. **RMSE:** `np.sqrt(np.mean(result.resid**2))` (residuals = y - y_pred). Both are on the same scale as `y` (leads).
- **Underdetermined:** If `n_observations < ~3 × n_params`, the model is underdetermined; warn the user but still fit.

### Ridge, Lasso, ElasticNet (sklearn)

- **API:** `fit(X, y)` with `fit_intercept=True`. `model.coef_` has length = n_features (channels + controls); order matches X columns. `model.intercept_` is a scalar.
- **Coefficient slice:** `coef_[:n_channels]` for channel coefficients, `coef_[n_channels:]` for controls. Build `coefficients` dict and `contribution` only for channels; baseline = `y_pred - sum(contribution[ch])`.
- **R²:** `model.score(X, y)` (same X and y used for fit). **RMSE:** `np.sqrt(np.mean((y - model.predict(X))**2))`.
- **Scaling:** We do **not** standardize X or y. Regularization `alpha` is therefore on the raw scale; the user tunes it. If features differ by orders of magnitude, consider documenting that alpha may need to be adjusted per dataset.

### PyMC (Bayesian)

- **Likelihood:** Same linear model: `observed_y = intercept + X @ coefficients + noise`. Use the **same** X (channels then controls) and column order as frequentist models.
- **Priors:** Intercept `Normal(mu=y.mean(), sigma=y.std())`. Channel coefficients `HalfNormal(sigma=y.std())` so they are non-negative (media effect direction). If **control** variables are included, use `Normal(0, sigma)` (or similar) for control coefficients so they can be positive or negative. Noise `HalfNormal(sigma=y.std())`.
- **Coefficient order:** Index coefficients so that `coefficients[channel_names[i]]` and control coefficients (if any) match the columns of X. Extract posterior **mean** for point estimates and 94% HDI for `coefficient_lower/upper`.
- **CPL HDI:** CPL is `raw_spend / attributed_leads`. For each channel, for every posterior draw compute `contribution_sum_draw = (coef_draw[ch] * X[:, ch_idx]).sum()`, then `cpl_draw = raw_spend[ch].sum() / contribution_sum_draw` (guard: if contribution_sum_draw ≤ 0, skip or set cpl_draw to inf). Then `cpl_lower[ch]` = 2.5th percentile of cpl_draws, `cpl_upper[ch]` = 97.5th percentile. Equivalently, get HDI of contribution sum per channel and set `cpl_lower = spend / contribution_upper`, `cpl_upper = spend / contribution_lower` (CPL is inverse of contribution).
- **R² and RMSE:** Use posterior predictive mean: `y_pred_mean = posterior_mean(intercept) + X @ posterior_mean(coefficients)`. Then R² = 1 - SS_res/SS_tot, RMSE = sqrt(mean((y - y_pred_mean)**2)).
- **Important scope note:** In the current app, PyMC does **not** estimate adstock or saturation parameters inside the Bayesian model. Those transforms are chosen earlier in `Config`, applied first, and PyMC fits priors only on the regression layer that follows.

### Negative coefficients and business display (frequentist only)

OLS and sklearn models can yield **negative** channel coefficients (e.g. collinearity or weak signal). Then `contribution[ch]` is negative and `sum(contribution[ch])` can be negative, so CPL = spend / contribution would be negative. **Display:** In the UI, when CPL is negative or infinite, show "—" or "N/A" and treat that channel as "negative contribution" in the narrative (e.g. "Reduce or investigate") rather than showing a negative €/lead.

In the current app, the **model fit metrics** (`R²`, `RMSE`, `MAE`, `MAPE`) reflect the **raw fitted model**. The business-facing lead split shown in `Results` is a bounded communication layer built from the raw model output so the displayed `media`, `baseline`, and `unexplained` values remain interpretable for stakeholders.

### Transforms (adstock then saturation)

- **Order:** Apply adstock first (carryover), then saturation (diminishing returns). Regression is on the **final** transformed series. So `contribution[ch] = β_ch * X_transformed[:, ch_idx]` is in lead units; the transformation is already inside `X_transformed`.
- **Geometric adstock:** `x_transformed[t] = x[t] + θ * x_transformed[t-1]`, `x_transformed[0] = x[0]`. θ in (0, 1). Time order of the data must be correct (sorted by date).
- **Hill:** Output in [0, 1] (or proportional to that). Coefficient is then "leads per unit of saturated effect". CPL = raw_spend / attributed_leads remains € per lead.

---

## Summary

| Model | Lib | Type |
|-------|-----|------|
| OLS | statsmodels | Frequentist |
| Ridge | sklearn | Frequentist |
| Lasso | sklearn | Frequentist |
| ElasticNet | sklearn | Frequentist |
| PyMC | pymc | Bayesian |

**Model validation:** The app now shows both **in-sample** fit metrics and a simple **time-based holdout** check using the latest 20% of periods as validation data. The final fitted model is still estimated on the full selected dataset for interpretation, while the holdout metrics are there to test generalisation.

**Model selection guidance:** Ridge/Lasso/ElasticNet are preferred when channels are correlated; OLS is a baseline; PyMC gives credible intervals for CPL and coefficients. Use this to choose which models to fit first.

**Edge cases and robustness:**
- **Zero spend in a channel:** Allowed; CPL can be infinite. Document in UI: "Channels with zero total spend will show CPL as N/A (infinite)."
- **Rank deficiency (constant column, perfect collinearity):** OLS/sklearn can fail or warn. Add in build instructions: "If fit fails with 'singular matrix' or 'rank deficiency', check for constant or duplicate channel columns and remove or add regularization."
- **Scale of alpha (Ridge/Lasso):** We do not standardize X or y. Alpha is on the raw scale. If channel spend columns differ by orders of magnitude, consider scaling spend (e.g. per 1k€) or tuning alpha per run.
