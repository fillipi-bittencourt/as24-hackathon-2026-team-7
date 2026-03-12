# MMM — Marketing Mix Modeling

Specification and starter folder for a Streamlit MMM app. The target demo answers three executive questions: What is happening? Why? What next?

---

## Current Status

- `app.py` is still a placeholder
- the real app is built by following `docs/10_BUILD_MMM.md`
- the fastest usable demo target is `OLS + Ridge + Results + AI executive summary`
- the included sample file for first-run validation is `data/mmm_demo_sample.csv`

---

## Fast MVP setup

```bash
# 1. Enter the app folder
cd as24-hackathon-2026-team-7/mmm

# 2. Create virtual environment (Python 3.10+ required)
python3.10 -m venv .venv

# 3. Install the fast MVP dependencies
.venv/bin/pip install --upgrade pip
.venv/bin/pip install -r requirements-mvp.txt

# 4. Copy and fill in your API key
cp credentials.json.example credentials.json
# Edit credentials.json — add openai_api_key

# 5. Use the included sample data first
# mmm/data/mmm_demo_sample.csv

# 6. Build the app
# Follow docs/10_BUILD_MMM.md in Cursor

# 7. Run after the app has been built
source .venv/bin/activate
streamlit run app.py
# Opens http://localhost:8501
```

> **Python 3.10+ required.** Not installed? `pyenv install 3.10.14 && pyenv local 3.10.14`

Full setup reference including troubleshooting: [docs/02_SETUP.md](docs/02_SETUP.md)

If you want the full optional stack later, install `requirements.txt` after the MVP is already working.

---

## Credentials

Edit `mmm/credentials.json` after setup:

```json
{
  "preferred_provider": "openai",
  "openai_api_key": "sk-...",
  "openai_model": "gpt-4o",
  "anthropic_api_key": "sk-ant-...",
  "anthropic_model": "claude-3-5-sonnet-20241022"
}
```

For the hackathon MVP, use one provider only. Start with OpenAI unless you explicitly need Anthropic as a fallback. `credentials.json` is gitignored — keys are never committed.
See [docs/09_AI_ANALYSIS.md](docs/09_AI_ANALYSIS.md) for fallback options and the minimal required AI scope.

---

## Data

Use `mmm/data/mmm_demo_sample.csv` for the first working run. After that, replace it with business data if available. Required columns:

| Column | Type | Example |
|--------|------|---------|
| `date` | date | `2024-01-01` |
| `target` | float | **Leads** (our success metric). Use leads or conversions. |
| `*_spend` | float | `tv_spend`, `digital_spend`, … |

See [docs/04_DATA_MODEL.md](docs/04_DATA_MODEL.md) for the full schema.

---

## Run

```bash
cd as24-hackathon-2026-team-7/mmm
source .venv/bin/activate
streamlit run app.py
```

`app.py` must be built first. The current checked-in file is only a placeholder.

---

## Building the App

`app.py` is a placeholder. To build it, open Cursor in `mmm/` and send this prompt:

```
Read mmm/docs/10_BUILD_MMM.md and implement the MMM Streamlit app. Start with the MVP only: Data, Config, OLS, Ridge, Results, and AI single-model executive summary. Data will be in mmm/data/. Do one task item at a time: complete one [ ] item, verify it works, mark it [V], then proceed to the next. Do not skip items.
```

See [docs/10_BUILD_MMM.md](docs/10_BUILD_MMM.md) for the complete specification.

---

## Project Structure

```
mmm/
├── app.py                 # Streamlit entry point (placeholder — built by LLM)
├── requirements.txt       # Full dependency set including optional extras
├── requirements-mvp.txt   # Fast MVP dependency set
├── credentials.json       # API keys (gitignored — copy from credentials.json.example)
├── credentials.json.example
├── .python-version        # Python 3.10
├── data/                  # Demo sample + business CSVs
├── src/                   # Source code (created during build)
│   ├── utils.py
│   ├── transforms.py
│   ├── models/            # OLS, Ridge, stretch models
│   └── ai/                # AI summary client
└── docs/                  # Design docs and build instructions
```

---

## Documentation

| Document | Purpose |
|----------|---------|
| [docs/02_SETUP.md](docs/02_SETUP.md) | **Environment setup** — fast MVP setup, full setup, troubleshooting |
| [docs/10_BUILD_MMM.md](docs/10_BUILD_MMM.md) | **Build the app** — step-by-step instructions for agents |
| [docs/01_INDEX.md](docs/01_INDEX.md) | Full doc map |
| [docs/03_ARCHITECTURE.md](docs/03_ARCHITECTURE.md) | System architecture |
| [docs/04_DATA_MODEL.md](docs/04_DATA_MODEL.md) | Input/output schema |
| [docs/06_MODELS.md](docs/06_MODELS.md) | OLS, Ridge, Lasso, ElasticNet, PyMC |
| [docs/05_TRANSFORMS.md](docs/05_TRANSFORMS.md) | Adstock and saturation |
| [docs/09_AI_ANALYSIS.md](docs/09_AI_ANALYSIS.md) | OpenAI/Claude integration and credentials |
| [docs/08_UX_FLOW.md](docs/08_UX_FLOW.md) | User flow and screens |
| [docs/07_TECHNICAL_SPEC.md](docs/07_TECHNICAL_SPEC.md) | Stack, modules, config |
| [docs/11_WIREFRAME_PROMPT.md](docs/11_WIREFRAME_PROMPT.md) | Wireframe prompt — generate Streamlit wireframe (all tabs, leads/CPL/metrics) |
