# AI Co-Pilot Guide — Agent Reference

> **For agents:** When the user (human) asks you to help them use AI effectively, or when you are the AI being used, follow these patterns. Judges evaluate how effectively AI was leveraged.

---

## [use_cases] When to Use AI (Human → AI Prompts)

### [use:scaffold] Scaffolding & Structure

**prompt_examples:**
- "Create a Streamlit app with a guided sidebar step menu for What / Why / What next"
- "Generate a pandas pipeline to aggregate sales by region and month"
- "Set up a Flask app with data product layout and placeholder charts"

### [use:debug] Debugging & Refinement

**prompt_examples:**
- "This chart is empty — here's my code and data sample, what's wrong?"
- "How do I format this column as currency in Streamlit?"
- "Fix this error: [paste error message]"

### [use:ux] UX & Storytelling

**prompt_examples:**
- "Suggest executive-friendly labels for these KPIs"
- "How can I make this breakdown more readable?"
- "Write a one-sentence summary for this insight"

### [use:accelerate] Accelerating Delivery

**prompt_examples:**
- "Generate fallback sample data for [business scenario] with columns X, Y, Z" (primary: business data)
- "Convert this SQL query to pandas"
- "Add a filter dropdown for region to this Streamlit app"

---

## [prompting] Effective Prompting (Agent Receiving Prompts)

**MUST provide:**
- Specificity: Concrete ask, not "make a data product"
- Context: Business area, audience (executive), tech stack
- Constraints: "no external APIs", "must run locally"

**prompt_comparison:**

| weak | strong |
|------|--------|
| "Make a data product" | "Create a Streamlit app with 3 columns: Revenue, Conversion, Churn. Use st.line_chart for revenue over time." |
| "Fix this" | "This pandas groupby returns wrong totals. Here's the code and a sample of the data." |

---

## [documentation] What to Document for Judges

**agent_output:** When asked to summarize AI usage, structure as:

1. scaffolding: What AI generated from scratch (app structure, data pipeline)
2. debugging: Issues AI helped resolve
3. enhancements: UX or storytelling improvements from AI
4. time_saved: Rough estimate vs. manual build

---

## [bonus:api] ChatGPT API (Bonus Points)

**consider:** Live Q&A on data product, natural language query, auto-generated insights

**constraint:** Keep scope small. Simple integration > broken complex one.

---

## [guardrails] Guardrails for AI-Assisted Work

**Agent MUST:**
- Verify logic, calculations, data handling (AI can hallucinate)
- Align output to DECISIONS_FRAMEWORK.md
- Override AI suggestions that don't fit the story

**Agent SHOULD NOT:**
- Trust AI output without validation
- Add features that don't map to What/Why/What next
