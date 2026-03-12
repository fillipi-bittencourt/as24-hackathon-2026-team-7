# MMM — Marketing Mix Modeling

Decision-ready data product built with Streamlit. Fits OLS, Ridge, Lasso, ElasticNet, and PyMC models on marketing spend data and answers three executive questions: What is happening? Why? What next?

---

## Quick start

```bash
# 1. Enter the app folder
cd as24-hackathon-2026-team-7/mmm

# 2. Create virtual environment (Python 3.10+ required)
python3.10 -m venv .venv

# 3. Install dependencies (~2 min for PyMC)
.venv/bin/pip install --upgrade pip
.venv/bin/pip install -r requirements.txt

# 4. Copy and fill in your API key
cp credentials.json.example credentials.json
# Edit credentials.json — add openai_api_key or anthropic_api_key

# 5. Add your data
# Copy a CSV into mmm/data/  (columns: date, target, *_spend)

# 6. Run
source .venv/bin/activate
streamlit run app.py
# Opens http://localhost:8501
```

> **Python 3.10+ required.** Not installed? `pyenv install 3.10.14 && pyenv local 3.10.14`

Full setup reference including troubleshooting: [docs/02_SETUP.md](docs/02_SETUP.md)

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

You only need one provider. Set `preferred_provider` to the provider you use (e.g. `"openai"` when using `openai_api_key`). `credentials.json` is gitignored — keys are never committed.
See [docs/09_AI_ANALYSIS.md](docs/09_AI_ANALYSIS.md) for fallback options (env vars, sidebar input).

---

## Data

Place a CSV in `mmm/data/`. Required columns:

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

---

## Building the App

`app.py` is a placeholder. To build it, open Cursor in `mmm/` and send this prompt:

```
Read mmm/docs/10_BUILD_MMM.md and implement the full MMM Streamlit app. Data will be in mmm/data/. Do one task item at a time: complete one [ ] item, verify it works, mark it [V], then proceed to the next. Do not skip items.
```

See [docs/10_BUILD_MMM.md](docs/10_BUILD_MMM.md) for the complete specification.

---

## Project Structure

```
mmm/
├── app.py                 # Streamlit entry point (placeholder — built by LLM)
├── requirements.txt       # Python dependencies
├── credentials.json       # API keys (gitignored — copy from credentials.json.example)
├── credentials.json.example
├── .python-version        # Python 3.10
├── data/                  # Place business CSV here
├── src/                   # Source code (created during build)
│   ├── utils.py
│   ├── transforms.py
│   ├── models/            # OLS, Ridge, Lasso, ElasticNet, PyMC
│   └── ai/                # OpenAI / Anthropic client
└── docs/                  # Design docs and build instructions
```

---

## Documentation

| Document | Purpose |
|----------|---------|
| [docs/02_SETUP.md](docs/02_SETUP.md) | **Environment setup** — step-by-step install, run, and troubleshoot |
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
