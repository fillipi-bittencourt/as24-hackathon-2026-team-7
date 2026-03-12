# MMM — Marketing Mix Modeling

Runnable Streamlit app for hackathon delivery. The app is designed to answer three business questions:

1. What is happening
2. Why is it happening
3. What should leadership do next

---

## Current Status

The checked-in app is live and usable.

- tabs: `Data`, `Config`, `Priors`, `Fit`, `Results`, `AI`
- models: `OLS`, `Ridge`, `Lasso`, `ElasticNet`, `PyMC`
- results support: model comparison, lead decomposition, channel filtering, period filtering, exports
- ai support: short or in-depth analysis, multi-model context option, CSV and PDF export
- first-run dataset: `data/mmm_demo_sample.csv`

---

## Fast setup

```bash
cd as24-hackathon-2026-team-7/mmm
python3.10 -m venv .venv
.venv/bin/pip install --upgrade pip
.venv/bin/pip install -r requirements-mvp.txt
source .venv/bin/activate
streamlit run app.py
```

> Python `3.10+` required.

If you need the full optional stack, install `requirements.txt` after the fast setup already works.

---

## Recommended demo path

1. Load `data/mmm_demo_sample.csv`
2. Keep the default transforms `Geometric + Log`
3. Fit `OLS` and `Ridge`
4. Open `Results` and use `All data`
5. Show the top metrics, channel table, and stacked time chart
6. Open `AI`, choose `In-depth`, keep multi-model context enabled, and generate analysis

If time or latency is tight, skip `PyMC` in the live run and use `OLS` plus `Ridge`.

---

## Credentials

The app supports:

1. `credentials.json`
2. environment variables
3. manual sidebar override

Manual sidebar entry is the emergency fallback and now takes precedence when provided.

Example `credentials.json`:

```json
{
  "preferred_provider": "openai",
  "openai_api_key": "sk-...",
  "openai_model": "gpt-4o",
  "anthropic_api_key": "sk-ant-...",
  "anthropic_model": "claude-3-5-sonnet-20241022"
}
```

`credentials.json` is gitignored and keys must never be committed.

---

## Data requirements

Use `data/mmm_demo_sample.csv` for the first successful run. Required fields:

| Column | Type | Example |
|--------|------|---------|
| `date` | date | `2024-01-01` |
| `target` | float | leads |
| `*_spend` | float | `tv_spend`, `digital_spend` |

Optional controls are supported and are validated before fitting.

---

## Project structure

```text
mmm/
├── app.py
├── requirements.txt
├── requirements-mvp.txt
├── credentials.json
├── credentials.json.example
├── data/
├── src/
│   ├── utils.py
│   ├── transforms.py
│   ├── models/
│   └── ai/
└── docs/
```

---

## Docs

| Document | Purpose |
|----------|---------|
| [docs/02_SETUP.md](docs/02_SETUP.md) | setup and troubleshooting |
| [docs/03_ARCHITECTURE.md](docs/03_ARCHITECTURE.md) | current app architecture |
| [docs/08_UX_FLOW.md](docs/08_UX_FLOW.md) | current tab flow and UI behavior |
| [docs/09_AI_ANALYSIS.md](docs/09_AI_ANALYSIS.md) | AI payload, prompting, and guardrails |
| [docs/10_BUILD_MMM.md](docs/10_BUILD_MMM.md) | engineering build history and checklist |
| [docs/11_WIREFRAME_PROMPT.md](docs/11_WIREFRAME_PROMPT.md) | current wireframe prompt |
