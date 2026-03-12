# The Great BI Blackout — Hackathon

**Team 7** | Canada  
Rim Nasfi · Kelly Mitchell · Hussain Jalaluddin · Fillipi Bittencourt

**Presentation:** Friday March 13th, 10am EST / 4pm CET  
**Canada teams:** Can kick off Wednesday afternoon to account for lost time on Friday

---

## For AI Agents

**Read [AGENT_README.md](AGENT_README.md) first.** It contains project metadata, constraints, task routing, and references to all other docs.

---

## Quick Links

| Document | Purpose |
|----------|---------|
| [AGENT_README.md](AGENT_README.md) | **Agent entry point** — metadata, routing, constraints |
| [docs/README.md](docs/README.md) | **Doc index** — links to all hackathon docs below |
| [docs/CHECKLIST.md](docs/CHECKLIST.md) | **Complete project checklist** — setup → build → test → demo |
| [docs/GUIDELINES.md](docs/GUIDELINES.md) | Scope, guardrails, tech stack, business areas |
| [docs/DECISIONS_FRAMEWORK.md](docs/DECISIONS_FRAMEWORK.md) | The three executive questions (design anchor) |
| [docs/AI_COPILOT_GUIDE.md](docs/AI_COPILOT_GUIDE.md) | AI prompting patterns and guardrails |
| [docs/DEMO_PREP.md](docs/DEMO_PREP.md) | Demo script template and deliverables |

---

## Folder Structure

```
as24-hackathon-2026-team-7/
├── AGENT_README.md        # Agent entry point (read first)
├── README.md              # This file
├── TEAM.md                # Team members and decisions
├── docs/                  # Hackathon process (constraints, checklist, demo)
│   ├── CHECKLIST.md       # Complete project checklist — start here
│   ├── GUIDELINES.md
│   ├── DECISIONS_FRAMEWORK.md
│   ├── AI_COPILOT_GUIDE.md
│   └── DEMO_PREP.md
└── mmm/                   # THE data product — everything lives here
    ├── app.py             # Streamlit entry point (placeholder until the app is built)
    ├── requirements.txt
    ├── requirements-mvp.txt
    ├── data/              # Place business data (CSV) here
    ├── src/               # App source code (models, transforms, AI)
    └── docs/              # MMM design docs + 10_BUILD_MMM.md
```

The **data product** is the **MMM app** in [mmm/](mmm/). Right now this repo contains the full specification, setup docs, and demo assets. The app itself still needs to be built from `mmm/docs/10_BUILD_MMM.md`.

---

## Current Status

- **Current repo state:** specification-first, not runnable out of the box yet
- **Fastest path to a usable demo:** open Cursor in `mmm/`, build the MVP from `mmm/docs/10_BUILD_MMM.md`, then use the included sample file `mmm/data/mmm_demo_sample.csv`
- **Required demo scope:** Data, Config, Fit, Results, and an AI executive summary
- **Stretch only:** Lasso, ElasticNet, PyMC, AI Q&A, advanced channel deep dives

Until the app is built, `streamlit run app.py` will only launch a placeholder.

---

## Fast Demo Path

1. Create the environment from `mmm/requirements-mvp.txt`
2. Build the app from `mmm/docs/10_BUILD_MMM.md`
3. Use `mmm/data/mmm_demo_sample.csv` for the first successful run
4. Fit `OLS`, then optionally `Ridge`
5. Use the Results tab for the three decision sections
6. Use the AI tab to generate a single-model executive summary

---

## The Mission

Build a **decision-ready data product** in 2 days — without any traditional BI tools — that enables the C-Suite to make informed decisions for their board meeting.

**Remember:** You are not building a dashboard. You are rebuilding the company's ability to make decisions under pressure.
