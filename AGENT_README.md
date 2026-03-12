# Agent Instructions — AS24 Hackathon Team 7

> **Audience:** AI coding agents (Cursor, ChatGPT, Claude, etc.). Read this file first when assisting with this project.

**What to load (avoid overload):** When the user asks to **build the app**, start with [mmm/docs/10_BUILD_MMM.md](mmm/docs/10_BUILD_MMM.md) and this file. Load additional docs only when needed for unresolved specifics (for example exact schema fields). Do not load CHECKLIST, DEMO_PREP, or all mmm/docs unless the user explicitly asks for full context.

## [priority] Instruction Hierarchy (conflict resolver)

If instructions conflict, apply this order:
1. `AGENT_README.md` — routing and conflict resolution
2. `mmm/docs/10_BUILD_MMM.md` — implementation details
3. `docs/DECISIONS_FRAMEWORK.md` — What / Why / What next mapping
4. `docs/GUIDELINES.md` — guardrails and constraints
5. `docs/AI_COPILOT_GUIDE.md` — advisory prompting guidance

If conflict remains, choose the option that minimizes scope and ships a working local demo fastest.

---

## [meta] Project Metadata

```yaml
project: as24-hackathon-2026-team-7
event: The Great BI Blackout
team: Team 7 (Canada)
members: [Rim Nasfi, Kelly Mitchell, Hussain Jalaluddin, Fillipi Bittencourt]
presentation_date: 2026-03-13
presentation_time: "10:00 EST / 16:00 CET"
duration_days: 2
```

---

## [role] Agent Role

You are assisting Team 7 to build a **decision-ready data product** in 2 days without traditional BI tools. The deliverable must answer three executive questions: What is happening? Why? What should leadership do next?

**MUST:**
- Follow constraints in [docs/GUIDELINES.md](docs/GUIDELINES.md)
- Align all views and metrics to the three decisions in [docs/DECISIONS_FRAMEWORK.md](docs/DECISIONS_FRAMEWORK.md)
- Use coding frameworks only (Python, R, Streamlit, Flask, etc.) — no QuickSight, Tableau, Power BI, Looker, Excel dashboards

**DO NOT:**
- Propose traditional BI tools
- Require live data connections (business data, pre-exported, is used)
- Add features unrelated to the three executive decisions

---

## [context] Hackathon Brief (Summary)

- **Scenario:** BI systems are down; C-Suite needs a working data product for a board meeting in 48 hours
- **Objective:** Build a focused executive decision tool for ONE business area
- **Scope:** Business data (pre-exported); no live connection required; starter templates (Streamlit, Shiny) allowed
- **Judging:** Value (40%), Product (40%), Innovation (20%); AI usage is evaluated

---

## [structure] File Layout

```
as24-hackathon-2026-team-7/
├── AGENT_README.md       # This file — agent entry point
├── README.md             # Human-facing overview
├── TEAM.md               # Team members and decisions
├── docs/                 # Hackathon process (index: docs/README.md)
│   ├── CHECKLIST.md      # Complete project checklist (start here)
│   ├── GUIDELINES.md
│   ├── DECISIONS_FRAMEWORK.md
│   ├── AI_COPILOT_GUIDE.md
│   ├── DEMO_PREP.md
│   └── archive/          # One-time and redundant docs — do not load for build
└── mmm/                  # THE data product — app, data, source, and design docs
    ├── app.py            # Streamlit entry point
    ├── requirements.txt
    ├── data/             # Place business CSV here
    ├── src/              # models/, ai/, transforms, utils
    └── docs/             # Design docs + 10_BUILD_MMM.md
```

---

## [routing] Task Routing for Agents

When the user asks you to:

| User request | Agent action | Read |
|--------------|--------------|------|
| Scaffold app, create data product | Build app in `mmm/` per [mmm/docs/10_BUILD_MMM.md](mmm/docs/10_BUILD_MMM.md); implement three decision views, model comparison, and AI summary | **Default:** AGENT_README + 10_BUILD_MMM. **Required when touching models:** 06_MODELS. **Required when touching AI:** 09_AI_ANALYSIS. **Add only as needed:** 04_DATA_MODEL, GUIDELINES, DECISIONS_FRAMEWORK |
| Set up / fix the environment | Follow mmm/docs/02_SETUP.md step by step | **mmm/docs/02_SETUP.md** |
| Prepare or load business data | Place CSV in `mmm/data/`; validate schema against mmm/docs/04_DATA_MODEL.md | mmm/docs/04_DATA_MODEL.md |
| Fix bug, debug | Apply minimal fix; verify logic; do not refactor beyond scope | — |
| Improve UX, add chart | Align to three decisions; use executive-friendly labels | docs/DECISIONS_FRAMEWORK.md |
| Add feature | Check it supports What/Why/What next; reject if unrelated | docs/DECISIONS_FRAMEWORK.md |
| Explain project | Summarize from this file + docs/GUIDELINES + docs/DECISIONS_FRAMEWORK | — |

---

## [constraints] Hard Constraints

1. **One business area** — Sales, Marketing ROI, Inventory, Pricing, Customer Health, or Operations
2. **Three views** — One view per executive question (What / Why / What next)
3. **No BI tools** — QuickSight, Tableau, Power BI, Looker, Excel dashboards are forbidden
4. **Code-based** — Python, R, SQL, Streamlit, Flask, Dash, Shiny, etc.
5. **Business data** — Use business data (pre-exported); synthetic only as fallback

---

## [references] Document Purposes

**Documentation tiers (what the agent needs):**

| When | Load (necessary) | Load (optional) |
|------|-------------------|------------------|
| Build the app | **AGENT_README + mmm/docs/10_BUILD_MMM.md** | 04_DATA_MODEL. Load 06_MODELS when defining ModelResult. Load 09_AI_ANALYSIS when building AI helpers |
| Set up / fix environment | **mmm/docs/02_SETUP.md** | — |
| Understand project / route request | **This file (AGENT_README)** | GUIDELINES, DECISIONS_FRAMEWORK |
| Validate scope or three decisions | — | docs/DECISIONS_FRAMEWORK.md, docs/GUIDELINES.md |
| Human checklist, demo prep | — | docs/CHECKLIST.md, docs/DEMO_PREP.md (not required for build) |

| File | Purpose for agent |
|------|-------------------|
| docs/CHECKLIST.md | **Complete project checklist** — setup → build → test → demo, in order; use to track and validate progress |
| docs/GUIDELINES.md | Scope, allowed tools, tech stack, business area selection, judging criteria |
| docs/DECISIONS_FRAMEWORK.md | Design anchor; every view must map to one of three questions |
| mmm/docs/02_SETUP.md | Environment setup for agents — use when asked to install, run, or fix the environment |
| mmm/docs/10_BUILD_MMM.md | Step-by-step instructions to build the MMM Streamlit app. **Single-file build:** this file only. Full fidelity: add mmm/docs/04_DATA_MODEL.md and mmm/docs/06_MODELS.md. |
| docs/AI_COPILOT_GUIDE.md | Prompt patterns, context to provide, guardrails when using AI |
| docs/DEMO_PREP.md | Demo script template and deliverables |

**Archived:** One-time and redundant docs (readiness review, consistency review, snapshot review prompt/response) are in [docs/archive/](docs/archive/). Do not load them for the build.
