# AI Analysis

Use OpenAI or Claude to analyze MMM model results and generate executive-ready insights.
For hackathon delivery, AI is part of the MVP and supports both a short executive mode and a deeper analysis mode.

---

## delivery mode

- day 1 mvp: required AI with one working provider
- current app mode: single-model analysis with optional multi-model context
- if AI fails, core app behavior must remain usable

---

## Purpose

- Summarize model outputs (coefficients, **cost per lead (CPL)**, contribution) in plain language
- Interpret findings and highlight actionable insights
- Generate executive-ready recommendations for the three decisions
- Natural language Q&A over results — stretch feature after MVP stability

---

## Credentials

API keys can be loaded from sidebar override, `mmm/.env`, `mmm/credentials.json`, or existing shell environment variables.

**Loading priority — use the first that works:**

1. Sidebar text input in the app when manually provided
2. `mmm/.env`
3. `mmm/credentials.json`
4. Environment variables: `OPENAI_API_KEY`, `ANTHROPIC_API_KEY`

The app must handle each case gracefully. If none of the sources are available, show a clear message in the AI step: `"Add a valid .env or credentials.json file, or set an API key in the sidebar to enable AI analysis."`

**credentials.json partial fills:** If the file exists but `preferred_provider` is missing, auto-detect: use `"openai"` if `openai_api_key` is present, else use `"anthropic"`. If parsing fails, show a readable error and allow the manual override path.

---

## `.env` Example

```bash
OPENAI_API_KEY=sk-...
OPENAI_MODEL=gpt-4o
ANTHROPIC_API_KEY=sk-ant-...
ANTHROPIC_MODEL=claude-3-5-sonnet-20241022
```

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

## Runtime rules

To save tokens and cost during analysis:

1. **Round numbers:** Round all floats in the payload to 2 decimal places.
2. **Prune nulls:** Remove any keys with `None` values from the payload before sending.
3. **No raw rows:** Send only aggregated results.
4. **Numeric traceability:** Every recommendation must cite at least one number from the payload.
5. **Explicit uncertainty:** The response must state trust limits, assumptions, and what is not explained by the model.

---

## Analysis Payload

Send only aggregated results. The payload sent to the LLM should include:

```
- model_name: e.g. "OLS"
- date_range: "2022-01-03 to 2023-12-25"
- target_metric: **"leads"** (our success metric)
- n_weeks: 104
- model_fit: { r_squared: 0.78, rmse: 12500, mae: 9000, mape_non_zero: 13.2 }
- actual_total_leads: 120000
- predicted_total_leads: 115000
- unexplained_total_leads: 5000
- channels: [
    { name: "tv_spend", coefficient: 0.42, cpl: 12.50, contribution_pct: 38, contribution_total: 45600, spend_total: 570000 },
    { name: "digital_spend", coefficient: 0.28, cpl: 18.20, contribution_pct: 25, contribution_total: 30000, spend_total: 546000 },
    ...
  ]
- controls: [{ name: "price_index" }, { name: "seasonality" }]
- baseline_pct: 37
- top_channel: "tv_spend"
- bottom_channel: "social_spend"
- comparison_table: optional rows for each fitted model with r_squared, rmse, and selected model marker
```

---

## Prompt Structure (ICE format)

Use the ICE structure for all prompts. Keep Instructions and Context stable; only the Task (model results) changes per call.

**Instructions:**
> You are a senior marketing analytics lead writing for analysts, managers, CMO, and CEO. Be direct, numeric, and explicit about confidence limits. Do not invent numbers. Every recommendation must cite evidence from the payload. If evidence is weak or missing, say so.

**Context:**
> This is a Marketing Mix Model fitted on [date_range] marketing spend and **leads** data. Success metric: **cost per lead (CPL)**. The team used [model_name] regression. [n_weeks] weeks of data. [n_channels] media channels. Control variables included: [list_of_controls].

**Examples (include one short example in the prompt):**
> Input: TV CPL €12.50, Digital CPL €18.20, Social CPL €45.00
> Output: "TV has the best cost per lead at €12.50, followed by Digital at €18.20. Social is weakest at €45 per lead. Recommend shifting Social budget to TV to improve CPL."

**Task (variable per call):**
> The actual model results payload (see schema above).

---

## Channel semantics and recommendation logic

The analysis prompt instructs the LLM to interpret channel names and apply recommendation logic so that "best CPL" does not automatically mean "scale this channel."

- **Branded search / paid branded / brand terms:** Often efficient in-model because they capture high-intent users who might convert via organic. The LLM should recommend **maintain** or **protect**, not "scale." Scaling can cannibalize organic and add cost without proportional incremental gain.
- **Non-branded / generic / prospecting search:** Treated as incremental. Strong efficiency here is a valid signal for reallocation or scale (within saturation).
- **Social (paid):** If names suggest brand or retargeting, treat with the same caution as branded search.
- **TV / video / display:** Consider reach and saturation; prefer "test increment" or "hold and validate" over "scale aggressively" when evidence is directional.

The prompt includes explicit guardrails: do not recommend increasing spend on a channel solely because it has the best CPL if that channel is clearly branded or defensive; instead recommend maintain and reallocate from weaker channels to more incremental ones where possible.

**Evaluation considerations** (what the prompt asks the LLM to consider):

- Statistical soundness: sample size, fit, holdout, residual gap.
- Channel role and semantics: infer from names; branded/defensive vs incremental.
- Cannibalization: paid branded vs organic; do not recommend scaling branded solely on CPL.
- Incrementality vs attribution: prefer scale on clearly incremental channels.
- Saturation and scalability: note when "maintain" or "test" is appropriate.
- Cross-model stability and actionability of recommendations.

---

## Requested Output Format

The app supports two modes.

### Mode A — Executive short

Return four sections:

1. **Executive summary**
2. **Top finding**
3. **Recommendation**
4. **Confidence note**

### Mode B — In-depth

Return six sections:

1. **Executive summary** with 3 bullets and explicit numbers. If the best CPL is on a branded/defensive channel, do not frame the main recommendation as "scale that channel"; frame as efficiency ranking and reallocate from weakest or maintain branded and test shift to incremental.
2. **Statistical rigor check** — model quality, holdout, residual gap, trust limits.
3. **Channel diagnosis** — strongest and weakest by CPL and contribution; for each major channel state whether it is likely incremental or defensive/branded (cannibalization risk); call out when the "best" CPL is on a channel where scaling would cannibalize organic.
4. **Cross-model consistency** when comparison_table exists.
5. **Action plan** — 30- and 60-day steps; distinguish maintain (e.g. branded), test/scale (incremental), and reduce/reallocate from; do not recommend "scale" on branded/defensive channels.
6. **Risks and assumptions** — modeling and data limitations, cannibalization risk where relevant, channel-role assumption.

---

## Error Handling

- If `credentials.json` is missing or malformed: show a user-friendly message, not a traceback
- If the API call fails (rate limit, wrong key, network error): show the error message and display raw results without the AI summary
- Never crash the app due to an AI failure — the Results tab must still work without AI
