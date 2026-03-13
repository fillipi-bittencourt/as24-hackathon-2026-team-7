# The Great BI Blackout — Hackathon

**Team 7** | Canada  
Rim Nasfi · Kelly Mitchell · Hussain Jalaluddin · Fillipi Bittencourt

**Presentation:** Friday March 13th, 10am EST / 4pm CET  
**Canada teams:** Can kick off Wednesday afternoon to account for lost time on Friday

---

## Current Status

The product is a runnable **Streamlit MMM app** in `mmm/`.

- current app navigation: sidebar step menu with `Data`, `Overview`, `Config`, `Priors`, `Fit`, `Results`, `AI`
- current help/reference section: separate `Guide` entry in the sidebar
- current model support: `OLS`, `Ridge`, `Lasso`, `ElasticNet`, `PyMC`
- current export support: results and AI analysis as `CSV` and `PDF`
- sample dataset included: `mmm/data/mmm_demo_sample.csv`
- recommended live demo path: use the sample file first, fit `OLS` and `Ridge`, and use a prepared saved state if you want to demo `PyMC` without live sampling risk

---

## For AI Agents

**Read [AGENT_README.md](AGENT_README.md) first.** It contains project metadata, constraints, task routing, and references to the project docs.

---

## Quick Links

| Document | Purpose |
|----------|---------|
| [AGENT_README.md](AGENT_README.md) | Agent entry point |
| [docs/README.md](docs/README.md) | Doc index |
| [docs/CHECKLIST.md](docs/CHECKLIST.md) | Current project checklist |
| [docs/GUIDELINES.md](docs/GUIDELINES.md) | Scope and guardrails |
| [docs/DECISIONS_FRAMEWORK.md](docs/DECISIONS_FRAMEWORK.md) | What, why, what next |
| [docs/DEMO_PREP.md](docs/DEMO_PREP.md) | Demo-safe run plan |
| [mmm/README.md](mmm/README.md) | App setup and run guide |

---

## Folder Structure

```text
as24-hackathon-2026-team-7/
├── AGENT_README.md
├── README.md
├── TEAM.md
├── docs/
│   ├── CHECKLIST.md
│   ├── GUIDELINES.md
│   ├── DECISIONS_FRAMEWORK.md
│   ├── AI_COPILOT_GUIDE.md
│   ├── DEMO_PREP.md
│   └── 15_PROJECT_IMPROVEMENTS_REVIEW.md
└── mmm/
    ├── app.py
    ├── requirements.txt
    ├── requirements-mvp.txt
    ├── data/
    ├── src/
    └── docs/
```

---

## Fast Demo Path

1. Run `./run_app.sh` inside `mmm/`
2. Load `mmm/data/mmm_demo_sample.csv`
3. Review `Overview` for dataset quality, target behavior, and multicollinearity
4. Open `Guide` if the audience needs a quick MMM explanation
5. Apply default transforms
6. Fit `OLS` and `Ridge`
7. Use `Results` to answer what is happening, why, and what next
8. Use `AI` to generate the in-depth analysis or short executive version

---

## The Mission

Build a **decision-ready data product** in 2 days without traditional BI tools so leadership can make informed decisions under pressure.

This is not just a dashboard. It is a compact decision system for marketing leads, attribution, efficiency, and next actions.
