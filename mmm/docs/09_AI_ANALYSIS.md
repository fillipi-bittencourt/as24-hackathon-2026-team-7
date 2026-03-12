# AI Analysis

Use OpenAI or Claude to analyze MMM model results and generate executive-ready insights.
For hackathon delivery, AI is optional until MVP (Data, Config, Fit, Results) is stable.

---

## delivery mode

- day 1 mvp: optional AI with single provider and single-model summary
- day 2 stretch: compare-all mode, multi-provider fallback, and Q&A history UX
- if AI fails, core app behavior must remain usable

---

## Purpose

- Summarize model outputs (coefficients, **cost per lead (CPL)**, contribution) in plain language
- Interpret findings and highlight actionable insights
- Generate executive-ready recommendations for the three decisions
- Natural language Q&A over results — stretch feature after MVP stability

---

## Credentials

API keys are loaded from `mmm/credentials.json` (gitignored). See `credentials.json.example` for the schema.

**Loading priority — use the first that works:**

1. `mmm/credentials.json` (preferred on hackathon day)
2. Environment variables: `OPENAI_API_KEY`, `ANTHROPIC_API_KEY`
3. Sidebar text input in the app (manual override / emergency fallback)

The app must handle each case gracefully. If none of the three are available, show a clear message in the AI tab: `"Add credentials.json or set an API key in the sidebar to enable AI analysis."`

**credentials.json partial fills:** If the file exists but `preferred_provider` is missing, auto-detect: use `"openai"` if `openai_api_key` is present, else use `"anthropic"`. If neither key is present, fall through to env vars. Never raise a KeyError — catch all parsing exceptions and fall through to the next priority.

---

## credentials.json Schema

```json
{
  "preferred_provider": "openai",
  "openai_api_key": "sk-...",
  "openai_model": "gpt-4o",
  "anthropic_api_key": "sk-ant-...",
  "anthropic_model": "claude-3-5-sonnet-20241022"
}
```

Fields:

| Field | Required | Description |
|-------|----------|-------------|
| `preferred_provider` | yes | `"openai"` or `"anthropic"` — which to use by default |
| `openai_api_key` | if using OpenAI | OpenAI API key |
| `openai_model` | no | Defaults to `"gpt-4o"` |
| `anthropic_api_key` | if using Anthropic | Anthropic API key |
| `anthropic_model` | no | Defaults to `"claude-3-5-sonnet-20241022"` |

---

## Token Optimization (Runtime)

To save tokens and cost during analysis:

1. **Round numbers:** Round all floats in the payload to 2 decimal places (e.g. `12345.67` instead of `12345.678921`).
2. **Prune nulls:** Remove any keys with `None` values from the JSON payload before sending.
3. **Concise prompt:** The ICE prompt is designed to be minimal. Do not add extra context unless requested by the user.

---

## Analysis Payload

Send only aggregated results — never raw data rows. The payload sent to the LLM should include:

```
- model_name: e.g. "OLS"
- date_range: "2022-01-03 to 2023-12-25"
- target_metric: **"leads"** (our success metric)
- n_weeks: 104
- model_fit: { r_squared: 0.78, rmse: 12500 }
- channels: [
    { name: "tv_spend", coefficient: 0.42, cpl: 12.50, contribution_pct: 38 },
    { name: "digital_spend", coefficient: 0.28, cpl: 18.20, contribution_pct: 25 },
    ...
  ]
- controls: [
    { name: "price_index", coefficient: -120.5, contribution_pct: -5 },
    { name: "seasonality", coefficient: 0.8, contribution_pct: 12 }
  ]
- baseline_pct: 37
- top_channel: "tv_spend"
- bottom_channel: "social_spend"
- comparison_table: (optional) rows for each fitted model with r_squared and rmse
```

---

## Prompt Structure (ICE format)

Use the ICE structure for all prompts. Keep Instructions and Context stable; only the Task (model results) changes per call.

**Instructions:**
> You are a senior marketing analyst presenting to the C-suite. Be direct and specific. Use numbers. Avoid jargon. Write for an executive who has 2 minutes to read this.

**Context:**
> This is a Marketing Mix Model fitted on [date_range] marketing spend and **leads** data. Success metric: **cost per lead (CPL)**. The team used [model_name] regression. [n_weeks] weeks of data. [n_channels] media channels. Control variables included: [list_of_controls].

**Examples (include one short example in the prompt):**
> Input: TV CPL €12.50, Digital CPL €18.20, Social CPL €45.00
> Output: "TV has the best cost per lead at €12.50, followed by Digital at €18.20. Social is weakest at €45 per lead. Recommend shifting Social budget to TV to improve CPL."

**Task (variable per call):**
> The actual model results payload (see schema above).

---

## Requested Output Format

Request a structured response with these four sections:

1. **Executive summary** — 2–3 sentences. What the model found, in plain language.
2. **Top finding** — One sentence. Best and worst performing channel with **CPL** numbers.
3. **Recommendation** — One specific action with a number. E.g. "Shift 20% of social spend to TV — expected uplift X%."
4. **Confidence note** — One sentence. Model R² and what it means, or Bayesian credible interval width for PyMC.

---

## Analysis Modes

**Mode A — Single model summary:**
User selects one model in the Results tab. AI writes an executive brief for that model using its results payload.

**Mode B — Cross-model comparison (day 2 stretch):**
If multiple models are fitted, AI receives the comparison table and explains how the models differ. Example output: "Ridge shrinks the weakest channels more aggressively than OLS — a more conservative estimate. Both agree that TV is the top performer."

Both modes use the same prompt structure; the payload differs.

---

## Business Q&A Mode (day 2 stretch)

The AI tab includes a first-class Q&A feature. The user selects a pre-built question or types a custom one; the LLM answers using the model results and channel data as context.

**Question templates (pre-loaded in the dropdown):**

| # | Template question |
|---|-------------------|
| 1 | What is our overall marketing cost per lead and how does it compare across channels? |
| 2 | Which channel should we increase spend on, and by how much? |
| 3 | Which channels are saturated and should we consider cutting? |
| 4 | How long do the effects of each channel last after we stop spending? |
| 5 | How does this model compare to the other fitted models — which should we trust more? |
| 6 | What would happen if we reallocated 20% of budget from the weakest to the strongest channel? |
| 7 | Write a 3-bullet summary I can present to the board in 30 seconds. |

**Q&A prompt structure:**
- Prepend the standard ICE Instructions and Context from the executive summary mode
- Add the full results payload (same as Mode A)
- Append: `"Answer the following question based only on the model results above. Be specific, use numbers, and keep the answer under 4 sentences: [user question]"`
- If the user selected from templates, use the template text verbatim in the prompt

**Q&A history:**
- Store each entry as a **dict**: `{ "question": str, "answer": str, "model": str, "timestamp": str }`. Cap at 15 entries; when appending and at cap, remove the oldest. Display history above the input area, newest at the bottom.

---

## Error Handling

- If `credentials.json` is missing or malformed: show a user-friendly message, not a traceback
- If the API call fails (rate limit, wrong key, network error): show the error message and display raw results without the AI summary
- Never crash the app due to an AI failure — the Results tab must still work without AI
