# Environment setup — instructions for agents

> **For agents:** Read this file when the user asks you to set up, fix, or run the MMM environment. Follow the steps in order. Use exactly the commands written here.

---

## Context

- **App location:** `mmm/` inside `as24-hackathon-2026-team-7/`
- **Entry point:** `mmm/app.py`
- **Python version:** 3.10 (pinned in `mmm/.python-version`)
- **Virtual environment:** `mmm/.venv/` (gitignored — created during setup)
- **Dependencies:** `mmm/requirements.txt`
- **Run command:** `cd as24-hackathon-2026-team-7/mmm && source .venv/bin/activate && streamlit run app.py`

All paths below are relative to the repo root unless stated otherwise.

---

## Step 1 — Verify Python 3.10+

```bash
python3 --version
```

Output must be `Python 3.10.x` or higher. If not:

```bash
pyenv install 3.10.14
cd as24-hackathon-2026-team-7/mmm
pyenv local 3.10.14
```

pyenv not installed? See https://github.com/pyenv/pyenv#installation

---

## Step 2 — Create the virtual environment

```bash
cd as24-hackathon-2026-team-7/mmm
python3.10 -m venv .venv
```

If `python3.10` is not found, use `python3` (it will work if Step 1 passed):

```bash
python3 -m venv .venv
```

---

## Step 3 — Install dependencies

Start with the MVP dependency set so the team can prove the app works before adding optional extras.

```bash
cd as24-hackathon-2026-team-7/mmm
.venv/bin/pip install --upgrade pip
.venv/bin/pip install -r requirements-mvp.txt
```

MVP demo target: Streamlit, pandas, numpy, scipy, statsmodels, scikit-learn, matplotlib, and OpenAI.

Only after the MVP flow works, install the optional full stack:

```bash
.venv/bin/pip install -r requirements.txt
```

> PyMC installation takes time and is optional for the first usable demo. Do not let it block Data → Fit → Results → AI summary.

If install fails midway, re-run the same command — pip is safe to retry.

If the `.venv` is corrupted, delete it and start from Step 2:

```bash
rm -rf .venv
```

---

## Step 4 — Verify the environment

```bash
cd as24-hackathon-2026-team-7/mmm
.venv/bin/python --version
.venv/bin/python -c "import streamlit, pandas, numpy, statsmodels, sklearn, openai; print('MVP packages OK')"
```

Optional full-stack check after stretch packages are installed:

```bash
.venv/bin/python -c "import pymc, arviz, anthropic; print('Optional packages OK')"
```

---

## Step 5 — Set up credentials

```bash
cp as24-hackathon-2026-team-7/mmm/credentials.json.example as24-hackathon-2026-team-7/mmm/credentials.json
```

Edit `mmm/credentials.json` and fill in at least one API key. For the MVP, use one provider only. Ensure `preferred_provider` matches the key you fill in (e.g. use `"openai"` when setting `openai_api_key`).

```json
{
  "preferred_provider": "openai",
  "openai_api_key": "sk-...",
  "openai_model": "gpt-4o",
  "anthropic_api_key": "sk-ant-...",
  "anthropic_model": "claude-3-5-sonnet-20241022"
}
```

`credentials.json` is gitignored — it will never be committed. See `mmm/docs/09_AI_ANALYSIS.md` for full schema and fallback options.

---

## Step 6 — Add data

Start with `mmm/data/mmm_demo_sample.csv`. After the MVP app works with that file, replace it with business data if available. Required columns: `date`, `target`, at least one `*_spend` column.

Schema reference: [04_DATA_MODEL.md](04_DATA_MODEL.md).

If business data is not available yet, use this prompt to generate synthetic data:

```
Generate a CSV with 104 rows (2 years of weekly data) for a Marketing Mix Model.
Columns: date (weekly, starting 2022-01-03), target (**leads**, e.g. 500–5000 float),
tv_spend (0–50000), digital_spend (0–30000), search_spend (0–20000), social_spend (0–15000).
Make target loosely correlated with spend. Add some seasonality.
Save as mmm/data/mmm_synthetic.csv
```

---

## Step 7 — Run the app

```bash
cd as24-hackathon-2026-team-7/mmm
source .venv/bin/activate
streamlit run app.py
```

App opens at **http://localhost:8501**

---

## Common problems and fixes

| Problem | Cause | Fix |
|---------|-------|-----|
| `ModuleNotFoundError` on import | Running Python outside `.venv` | Activate `.venv` first: `source .venv/bin/activate` |
| `streamlit: command not found` | `.venv` not activated | Run `source .venv/bin/activate` before `streamlit run app.py` |
| PyMC install fails on macOS | Missing C compiler | Skip PyMC for MVP, or run `xcode-select --install`, then re-run `pip install -r requirements.txt` later |
| PyMC install fails (NumPy error) | NumPy version conflict | Skip PyMC for MVP, or run `.venv/bin/pip install "numpy<2.0"`, then retry the full requirements later |
| `credentials.json not found` | File not copied | `cp credentials.json.example credentials.json` and fill in key |
| AI tab key error | Wrong key or wrong provider | Check `preferred_provider` matches the key you filled in |
| `src.utils not found` | Running from repo root | Must run `streamlit run app.py` from inside `mmm/` |

---

## File locations (quick reference)

| File | Purpose |
|------|---------|
| `mmm/app.py` | Streamlit entry point |
| `mmm/requirements.txt` | Full dependency set including optional extras |
| `mmm/requirements-mvp.txt` | Fast MVP dependency set |
| `mmm/credentials.json` | API keys (gitignored — copy from credentials.json.example) |
| `mmm/credentials.json.example` | Credentials schema reference |
| `mmm/.python-version` | Python 3.10 pin (for pyenv) |
| `mmm/data/` | Place business CSV here |
| `mmm/src/` | App source code |
| `mmm/docs/10_BUILD_MMM.md` | Step-by-step engineering build history and instructions |
