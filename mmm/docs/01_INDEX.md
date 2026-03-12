# MMM Design Framework — Index

Complete design framework for the Marketing Mix Modeling data product.

**Streamlit docs:** https://docs.streamlit.io/

---

## Document Map

| Document | Purpose |
|----------|---------|
| [01_INDEX.md](01_INDEX.md) | This file — framework overview and navigation |
| [02_SETUP.md](02_SETUP.md) | **Environment setup for agents** — install, credentials, data, run, troubleshoot |
| [03_ARCHITECTURE.md](03_ARCHITECTURE.md) | System architecture, components, data flow |
| [04_DATA_MODEL.md](04_DATA_MODEL.md) | Input/output schema, data requirements |
| [05_TRANSFORMS.md](05_TRANSFORMS.md) | Adstock and saturation transforms |
| [06_MODELS.md](06_MODELS.md) | Model specifications (OLS, Ridge, Lasso, ElasticNet, PyMC) |
| [07_TECHNICAL_SPEC.md](07_TECHNICAL_SPEC.md) | Tech stack, APIs, interfaces |
| [08_UX_FLOW.md](08_UX_FLOW.md) | User flow, screens, interactions |
| [09_AI_ANALYSIS.md](09_AI_ANALYSIS.md) | OpenAI/Claude integration for analysis |
| [10_BUILD_MMM.md](10_BUILD_MMM.md) | **Build history and engineering checklist** — historical implementation guide for the app |
| [11_WIREFRAME_PROMPT.md](11_WIREFRAME_PROMPT.md) | **Wireframe prompt** — copy-paste prompt to generate a Streamlit wireframe; covers all sidebar steps and metrics (leads, CPL, etc.) |

**Archived (redundant/snapshot/backlog):** 12_PROJECT_REVIEW_PROMPT, 13_REVIEW_RESPONSE, and 14_IMPROVEMENTS are in [docs/archive/](../../docs/archive/). Current product behavior is described by `02_SETUP`, `07_TECHNICAL_SPEC`, `08_UX_FLOW`, and `09_AI_ANALYSIS`. `10_BUILD_MMM` remains useful as engineering build history and detailed implementation notes.

---

## Design Principles

1. **Decision-ready** — Outputs support What / Why / What next
2. **Model-agnostic** — Shared transforms; pluggable OLS, Ridge, Lasso, ElasticNet, PyMC
3. **AI-augmented** — LLM summarization and interpretation of results
4. **Business data** — Pre-exported business data; no live connection required
