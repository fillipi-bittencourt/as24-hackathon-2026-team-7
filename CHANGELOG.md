# Changelog

This file tracks significant completed work in sequence order.

## How to use

- Add one new entry after each completed task item
- Use the next number in sequence
- Keep entries short and factual
- Include task, change, files, and reason

## Entries

### 002
- Task
  Data layer utilities
- Change
  Added the base `src` package and implemented CSV conversion and validation helpers for the MMM workflow
- Files
  `mmm/src/__init__.py`, `mmm/src/utils.py`
- Reason
  Give the app a reliable typed data entry point before wiring transforms and models

### 001
- Task
  Repo setup and MVP doc alignment
- Change
  Tightened the hackathon scope around a usable MVP, added demo prep assets, added a sample dataset, split fast MVP dependencies, and added a persistent changelog tracking rule for Cursor
- Files
  `README.md`, `mmm/README.md`, `docs/CHECKLIST.md`, `docs/DEMO_PREP.md`, `mmm/docs/02_SETUP.md`, `mmm/docs/03_ARCHITECTURE.md`, `mmm/docs/05_TRANSFORMS.md`, `mmm/docs/08_UX_FLOW.md`, `mmm/docs/09_AI_ANALYSIS.md`, `mmm/docs/10_BUILD_MMM.md`, `AGENT_README.md`, `.cursorrules`, `.gitignore`, `.cursor/rules/changelog-tracking.mdc`, `mmm/requirements-mvp.txt`, `mmm/data/README.md`, `mmm/data/mmm_demo_sample.csv`
- Reason
  Make the repo ready for a one-pass MVP build and ensure significant work is tracked as tasks are completed

## Entry template

### 000
- Task
- Change
- Files
- Reason
