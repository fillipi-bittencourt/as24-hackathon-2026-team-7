# Archive — one-time or redundant docs

These files are kept for reference but are **not part of the active workflow**. Agents and builders should not load them for the build.

| File | Why archived |
|------|----------------|
| PROJECT_READINESS_REVIEW.md | One-time readiness check; fixes are applied. "How to start" is in CHECKLIST and 10_BUILD_MMM. |
| CONSISTENCY_REVIEW.md | One-time consistency pass; fixes applied. |
| 12_PROJECT_REVIEW_PROMPT.md | Snapshot of project for LLM review. **Source of truth for build is 10_BUILD_MMM.md**; this copy lags. For a pre-build review, paste 10_BUILD_MMM + context into your LLM. |
| 13_REVIEW_RESPONSE.md | Historical answers to the review questions. Not a spec. |
| 14_IMPROVEMENTS.md | Backlog of improvements. **Implemented items** (missing-value rule, fixed seed, export, data preview, CPL display, timestamp, holdout note, etc.) are already in 10_BUILD_MMM and 04_DATA_MODEL. Remaining items are optional future backlog. |

**Active docs:** Build from [mmm/docs/10_BUILD_MMM.md](../../mmm/docs/10_BUILD_MMM.md). Setup from [mmm/docs/02_SETUP.md](../../mmm/docs/02_SETUP.md). Route from [AGENT_README.md](../../AGENT_README.md).
