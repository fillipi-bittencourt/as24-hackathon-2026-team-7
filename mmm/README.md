# MMM — Marketing Mix Modeling

Runnable Streamlit app for hackathon delivery. The app is designed to answer three business questions:

1. What is happening
2. Why is it happening
3. What should leadership do next

---

## Current Status

The checked-in app is live and usable.

- navigation: sidebar step menu for `Data`, `Overview`, `Config`, `Priors`, `Fit`, `Results`, `AI`
- reference help: separate `Guide` section in the sidebar
- models: `OLS`, `Ridge`, `Lasso`, `ElasticNet`, `PyMC`
- results support: model comparison, lead decomposition, channel filtering, period filtering, exports
- ai support: short or in-depth analysis, multi-model context option, CSV and PDF export
- first-run dataset: `data/mmm_demo_sample.csv`

---

## Fast setup

```bash
cd as24-hackathon-2026-team-7/mmm
./run_app.sh
```

`run_app.sh` checks whether the local environment already exists, installs dependencies if needed, prints the local URL, and keeps the terminal attached to the running Streamlit server.

`run_app.sh` is the full launcher path and will install the dependencies needed by the shipped app experience. Use `requirements-mvp.txt` only if you intentionally want a lighter manual environment path.

---

## Recommended demo path

1. Load `data/mmm_demo_sample.csv`
2. Use `Overview` to show dataset quality, target behavior, and multicollinearity checks
3. Use `Guide` if the audience needs a quick explanation of models and MMM concepts
4. Keep the default transforms `Geometric + Log`
5. Fit `OLS` and `Ridge`
6. Open `Results` and use `All data`
7. Show the top metrics, validation diagnostics, channel table, and stacked time chart
8. Open `AI`, choose `In-depth`, keep multi-model context enabled, and generate analysis

If you want to show `PyMC`, the safest path is to load a prepared saved state that already contains the Bayesian result and diagnostics. If time or latency is tight, use `OLS` plus `Ridge` for the live fit path.

---

## Credentials

The app supports:

1. manual sidebar override
2. `.env`
3. `credentials.json`
4. environment variables

Manual sidebar entry is the emergency override and takes precedence when provided. `.env` is the easiest local default source for day-to-day use.

Example `.env`:

```bash
OPENAI_API_KEY=sk-...
OPENAI_MODEL=gpt-4o
```

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

`.env` and `credentials.json` are gitignored and keys must never be committed.

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
├── run_app.sh
├── .env
├── .env.example
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
| [docs/08_UX_FLOW.md](docs/08_UX_FLOW.md) | current sidebar flow and UI behavior |
| [docs/09_AI_ANALYSIS.md](docs/09_AI_ANALYSIS.md) | AI payload, prompting, and guardrails |
| [docs/10_BUILD_MMM.md](docs/10_BUILD_MMM.md) | engineering build history and checklist |
| [docs/11_WIREFRAME_PROMPT.md](docs/11_WIREFRAME_PROMPT.md) | current wireframe prompt |
