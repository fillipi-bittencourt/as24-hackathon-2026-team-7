# Hackathon documentation

Docs in this folder support the hackathon process, constraints, and demo. **For agents:** when building the app, load only [mmm/docs/10_BUILD_MMM.md](../mmm/docs/10_BUILD_MMM.md). Use this folder for setup, scope, and demo.

## What we keep (and why)

| Type | Docs | Why |
|------|------|-----|
| **Canonical** | [CHECKLIST.md](CHECKLIST.md), [GUIDELINES.md](GUIDELINES.md), [DECISIONS_FRAMEWORK.md](DECISIONS_FRAMEWORK.md), [mmm/docs/10_BUILD_MMM.md](../mmm/docs/10_BUILD_MMM.md), [mmm/docs/02_SETUP.md](../mmm/docs/02_SETUP.md) | Single source for sequence, scope, build, setup. No duplicate source of truth. |
| **Supporting** | [AI_COPILOT_GUIDE.md](AI_COPILOT_GUIDE.md), [DEMO_PREP.md](DEMO_PREP.md) | Prompting patterns and demo script; optional for the build. |
| **Archived** | [archive/](archive/) | One-time reviews, snapshot prompts, improvements backlog. Kept for reference only; agents should not load them. |

| Document | Purpose |
|----------|---------|
| [CHECKLIST.md](CHECKLIST.md) | **Complete step-by-step checklist** — setup → build → test → demo, in order |
| [GUIDELINES.md](GUIDELINES.md) | Scope, allowed tools, tech stack, business areas, judging |
| [DECISIONS_FRAMEWORK.md](DECISIONS_FRAMEWORK.md) | Design anchor — three executive questions (What / Why / What next) |
| [AI_COPILOT_GUIDE.md](AI_COPILOT_GUIDE.md) | AI prompting patterns and guardrails |
| [DEMO_PREP.md](DEMO_PREP.md) | Demo script template and deliverables |
| [archive/](archive/) | One-time and redundant docs (readiness review, consistency review, snapshot review prompt/response, improvements backlog) |

**Data product:** Everything is in `mmm/` — app code, data (`mmm/data/`), source modules (`mmm/src/`), and design docs (`mmm/docs/`). Build instructions for agents: [mmm/docs/10_BUILD_MMM.md](../mmm/docs/10_BUILD_MMM.md).
