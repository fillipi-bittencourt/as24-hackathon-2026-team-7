# Guidelines — Agent Reference

> **For agents:** Use this file to validate scope, choose tech stack, and select business area. All agent output MUST comply with [constraints] and [allowed_tools].

**Repo default:** This repository is scoped to Marketing ROI / MMM in `mmm/`. Do not switch business area unless the user explicitly asks.
**Delivery principle:** usable first, fancy later. Prioritize a reliable end-to-end demo before advanced features.

---

## [constraints] Hard Constraints

**MUST:**
- Select exactly ONE business area from the allowed list
- Build a working data product or lightweight application
- Answer the three executive questions (see DECISIONS_FRAMEWORK.md)
- Use an AI coding agent during development

**DO NOT:**
- Use QuickSight, Tableau, Power BI, Looker
- Use Excel dashboards
- Use any traditional BI tool

---

## [allowed_tools] Allowed Tools and Data

| Category | Allowed |
|----------|---------|
| Frameworks | Python, R, SQL, Streamlit, Flask, Dash, Shiny |
| Templates | Streamlit, Shiny starter templates |
| Data | Business data (pre-exported); fallback: synthetic if needed |
| Connection | Live data connection NOT required |

---

## [tech_stack] Technical Stack (Agent Recommendations)

**Default recommendation:** Streamlit + pandas (this project uses Streamlit native charts: `st.bar_chart`, `st.area_chart`, `st.line_chart` — no Plotly).

| Layer | Options | This project |
|-------|---------|---------------|
| Frontend | Streamlit, Dash (Plotly), Flask + templates, Shiny (R) | Streamlit only |
| Data | Python (pandas), R (dplyr), SQL | pandas |
| Viz | Streamlit native (`st.bar_chart`, `st.area_chart`, `st.line_chart`), Plotly, Altair, Matplotlib, Seaborn | Streamlit native — no Plotly |
| Deploy | Local run, ngrok, Streamlit Cloud | Local run |

**When scaffolding in this repo:** Use Streamlit + pandas only unless user explicitly requests a migration.

---

## [business_areas] Business Area Selection

**Agent:** When user has not chosen a business area, suggest one from this table. Ensure chosen area has clear KPIs and supports What/Why/What next.

| area | example_kpis | data_needs |
|------|--------------|------------|
| Sales | revenue, pipeline, conversion | deals, stages, dates |
| Marketing ROI | CAC, LTV, attribution | campaigns, spend, conversions |
| Inventory | stock levels, turnover, obsolescence | SKUs, quantities, dates |
| Pricing | margin, elasticity, win rate | prices, competitors, deals |
| Customer Health | NPS, churn, engagement | scores, usage, support |
| Operations | throughput, SLA, efficiency | tickets, times, volumes |

**Selection criteria:** Has measurable KPIs; supports three decisions; business data available; board-relevant.

---

## [workflow] Team Workflow (Reference)

1. Kickoff: Align on business area and data source
2. Parallel: Data prep + app scaffolding + AI-assisted dev
3. Integration: Connect data to app, validate insights
4. Polish: UX, storytelling, demo run-through

---

## [judging] Judging Criteria (Reference)

| criterion | weight | focus |
|-----------|--------|-------|
| Value to the Business | 40% | Enables real decisions, actionable |
| Best Overall Product | 40% | Usability, clarity, stability, storytelling |
| Most Innovative | 20% | Creative framing, AI integration, novel insight |

---

## [bonus] Bonus Points

- Command line interface
- ChatGPT API key usage
- Connection to other tools with AI
- Analyst on team delivers final presentation
