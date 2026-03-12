# Technical Specification

## Stack

| Layer | Technology |
|-------|------------|
| UI | Streamlit |
| Data | pandas, numpy |
| Transforms | numpy, scipy |
| Frequentist | statsmodels (OLS), sklearn (Ridge, Lasso, ElasticNet) |
| Bayesian | pymc, arviz |
| Viz | altair, matplotlib |
| AI | openai, anthropic |

---

## Module Structure

```text
src/
├── __init__.py
├── transforms.py
├── models/
│   ├── __init__.py
│   ├── base.py
│   ├── ols.py
│   ├── ridge.py
│   ├── lasso.py
│   ├── elasticnet.py
│   └── pymc_model.py
├── ai/
│   ├── __init__.py
│   └── client.py
└── utils.py
```

---

## Model Interface

All models expose:

```python
def fit(
    X: np.ndarray,                    # shape (n_rows, n_channels + n_controls), float64
    y: np.ndarray,                    # shape (n_rows,), float64
    raw_spend: dict[str, np.ndarray], # channel_name → 1D raw spend array; required for CPL
    **kwargs                          # reg_alpha, l1_ratio for regularised models
) -> ModelResult

def predict(X: np.ndarray) -> np.ndarray  # shape (n_rows,)
```

`ModelResult` is a dataclass. See **06_MODELS.md** for the full definition, **Statistics and library notes** (OLS/sklearn/PyMC, coefficient order with controls, CPL HDI, negative CPL display), and field types. Key points:
- `contribution: dict[str, np.ndarray]` — a **vector** per channel, not a scalar; sum it for totals
- `model_name: str` — set to the key used in `session_state["model_results"]`
- `coefficient_lower/upper` and `cpl_lower/upper` are `None` for non-PyMC models; check with `result.coefficient_lower is not None`

---

## Config

API keys are loaded in priority order:

1. **Sidebar input** — manual override in the app
2. **`mmm/credentials.json`**
3. **Environment variables** — `OPENAI_API_KEY`, `ANTHROPIC_API_KEY`

Never hardcode keys. `credentials.json` is gitignored.

**Datatypes:** Input CSV columns may be object/int; the data layer **detects** and **converts** before validation. After conversion: date column → `datetime64[ns]`, target and channel/control columns → `float64`. `X_transformed` and `y` are numpy arrays with dtype **float64**. See **04_DATA_MODEL.md** (Datatypes and conversion) and **10_BUILD_MMM.md** Step 1.1.

| Config field | Purpose |
|--------------|---------|
| `preferred_provider` | `"openai"` or `"anthropic"` |
| `openai_api_key` | OpenAI API key |
| `openai_model` | Model name (default: `gpt-4o`) |
| `anthropic_api_key` | Anthropic API key |
| `anthropic_model` | Model name (default: `claude-3-5-sonnet-20241022`) |

---

## Run

```bash
cd mmm
source .venv/bin/activate
streamlit run app.py
```

## Current UI behavior

- six tabs are always visible
- tab gating is handled with messages, not hidden tabs
- results support period filtering, channel filtering, baseline toggle, and CSV/PDF export
- AI supports short and in-depth analysis plus CSV/PDF export
