# Consistency review — one file at a time

Reviewer: agent. Method: read each file, write a short consistency check to this doc, then fix any issues found.

---

## 1. AGENT_README.md

**Read:** Full file.

**Consistency check:**
- **Links:** All paths correct from repo root (`docs/`, `mmm/docs/`). 10_BUILD_MMM.md referenced as `mmm/docs/10_BUILD_MMM.md`.
- **Naming:** Numbered doc names (04_DATA_MODEL, 06_MODELS) used in Read column and references table.
- **Terminology:** "Three executive questions" / "What / Why / What next" consistent. "Decision-ready data product" used.
- **Structure vs references:** File layout lists docs/ (CHECKLIST, GUIDELINES, etc.) but not docs/README.md or PROJECT_READINESS_REVIEW.md — acceptable (references table is for agent routing).
- **Single-file statement:** Present in routing table and 10_BUILD_MMM reference row.

**Verdict:** OK. No changes needed.

---

## 2. README.md

**Read:** Full file.

**Consistency check:**
- **Links:** All doc links correct (AGENT_README, docs/README, CHECKLIST, GUIDELINES, DECISIONS_FRAMEWORK, AI_COPILOT_GUIDE, DEMO_PREP). mmm/ linked as folder.
- **Run command:** Says `cd mmm && streamlit run app.py` but does not mention activating the venv first. 02_SETUP and CHECKLIST use `source .venv/bin/activate` before `streamlit run app.py`. Inconsistent for a first-time runner.
- **Presentation time:** "10am EST / 4pm CET" matches AGENT_README "10:00 EST / 16:00 CET".
- **Folder structure:** Matches AGENT_README; does not list mmm/README.md or docs/PROJECT_READINESS_REVIEW.md — acceptable.

**Verdict:** Fix run command for consistency.

**Fix applied:** README.md run command updated to `cd mmm && source .venv/bin/activate && streamlit run app.py`.

---

## 3. TEAM.md

**Read:** Full file.

**Consistency check:**
- **Content:** business_area = Marketing ROI, tech_stack = Streamlit, data_source = business data — matches CHECKLIST Phase 0 and AGENT_README.
- **Roles:** presenter, data_owner, app_owner, storytelling_owner empty — acceptable (to be filled).
- **No doc links** — N/A.

**Verdict:** OK. No changes needed.

---

## 6. docs/CHECKLIST.md

**Read:** Full file.

**Consistency check:**
- **Doc paths:** All use `mmm/docs/10_BUILD_MMM.md`, `mmm/docs/02_SETUP.md`, `mmm/docs/04_DATA_MODEL.md`, `mmm/docs/06_MODELS.md`, `mmm/docs/09_AI_ANALYSIS.md`, `docs/DEMO_PREP.md`, `docs/DECISIONS_FRAMEWORK.md`. Correct.
- **Phase 1.5 verify:** Aligned with 02_SETUP: added numpy, arviz to import check. Fix applied in CHECKLIST.md.
- **3.3:** References `mmm/data/README.md` — file exists.
- **Run commands:** `cd mmm && source .venv/bin/activate && streamlit run app.py` in 4A.1 and 8.1 — consistent with README fix.
- **One task at a time / [V]:** Stated in Phase 3 and 3.4. Matches 10_BUILD_MMM.

**Verdict:** OK. Phase 1.5 aligned with 02_SETUP (numpy, arviz added).

---

## 4. .cursorrules

**Read:** Full file.

**Consistency check:**
- **Build instruction:** Points to mmm/docs/10_BUILD_MMM.md, "one task item at a time, mark [V] when each is done (Steps 1–8)". Matches 10_BUILD_MMM and CHECKLIST.
- **Other refs:** AGENT_README, GUIDELINES, DECISIONS_FRAMEWORK. No traditional BI tools — consistent.

**Verdict:** OK. No changes needed.

---

## 7. docs/DECISIONS_FRAMEWORK.md

**Read:** Full file.

**Consistency check:**
- **Terminology:** What is happening? / Why is it happening? / What should leadership do next? — matches AGENT_README, CHECKLIST, 10_BUILD_MMM. CPL, leads used in mapping table.
- **No internal doc links** — N/A.
- **Mapping table:** Marketing ROI / MMM filled; aligns with TEAM.md business_area and 10_BUILD_MMM.

**Verdict:** OK. No changes needed.

---

## 8. docs/GUIDELINES.md

**Read:** Full file.

**Consistency check:**
- **Tech stack:** Default "Streamlit + pandas" with Streamlit native charts; "This project" column lists Streamlit only, pandas, Streamlit native — no Plotly. Aligned with PROJECT_READINESS_REVIEW and 10_BUILD_MMM.
- **DECISIONS_FRAMEWORK.md** referenced without path — correct from docs/.

**Verdict:** OK. No changes needed.

---

## 9. docs/AI_COPILOT_GUIDE.md

**Read:** Full file.

**Consistency check:**
- **Plotly references:** Line 21 "How do I format this column as currency in Plotly?" and line 50 strong example "Use Plotly for a line chart" — project uses Streamlit native charts, not Plotly. Inconsistent with GUIDELINES.
- **DECISIONS_FRAMEWORK.md** and What/Why/What next — consistent.

**Verdict:** Fix Plotly examples to Streamlit for consistency.

**Fix applied:** AI_COPILOT_GUIDE: Plotly examples changed to Streamlit (see below).

---

## 5. docs/README.md

**Read:** Full file.

**Consistency check:**
- **Links:** CHECKLIST, PROJECT_READINESS_REVIEW, GUIDELINES, DECISIONS_FRAMEWORK, AI_COPILOT_GUIDE, DEMO_PREP, mmm/docs/10_BUILD_MMM.md. All valid relative paths.
- **CONSISTENCY_REVIEW.md** not listed — optional to add later.

**Verdict:** OK. No changes needed.

---

## 10. docs/DEMO_PREP.md

**Read:** Full file.

**Consistency check:**
- **Run instructions:** `cd as24-hackathon-2026-team-7/mmm`, `source .venv/bin/activate`, `streamlit run app.py` — matches CHECKLIST and README.
- **10_BUILD_MMM.md** referenced in ai_story and bonus — correct.
- **Duration:** Demo structure "10–15 min"; CHECKLIST 7.2 "under 10 min" — CHECKLIST is gate. OK.
- **CPL, leads** — consistent.

**Verdict:** OK. No changes needed.

---

## 11. docs/PROJECT_READINESS_REVIEW.md

**Read:** Full file.

**Consistency check:**
- **Doc paths:** mmm/docs/10_BUILD_MMM.md, 02_SETUP, 04_DATA_MODEL, etc. Correct.
- **Gap 4:** Was "GUIDELINES recommends Plotly". GUIDELINES now Streamlit native. Fix applied: line 100 updated to "Gap closed".

**Verdict:** OK. Gap 4 updated.

---

## 12. mmm/README.md

**Read:** Full file.

**Consistency check:**
- **Doc links:** All use `docs/` relative to mmm/ (02_SETUP, 04_DATA_MODEL, 10_BUILD_MMM, 09_AI_ANALYSIS, 01_INDEX, 03_ARCHITECTURE, 06_MODELS, 05_TRANSFORMS, 08_UX_FLOW, 07_TECHNICAL_SPEC, 11_WIREFRAME_PROMPT). Numbered names correct.
- **Run:** Includes `source .venv/bin/activate` before `streamlit run app.py`. Consistent with CHECKLIST/README.
- **Build prompt:** One task at a time, mark [V]. Matches 10_BUILD_MMM. **Credentials:** preferred_provider note present.

**Verdict:** OK. No changes needed.

---

## 13. mmm/docs/01_INDEX.md

**Read:** Full file.

**Consistency check:**
- **Doc map:** All 14 numbered docs listed (01–14). Links relative to mmm/docs/. Correct.
- **Terminology:** What / Why / What next, decision-ready, leads, CPL — consistent.

**Verdict:** OK. No changes needed.

---

## 14. mmm/docs/02_SETUP.md

**Read:** Full file (first 80 lines + verify step).

**Consistency check:**
- **Step 4 verify:** `streamlit, pandas, numpy, statsmodels, sklearn, pymc, arviz, openai, anthropic` — no plotly. Matches requirements and CHECKLIST Phase 1.5.
- **Run command:** `cd as24-hackathon-2026-team-7/mmm && source .venv/bin/activate && streamlit run app.py`. Paths and credentials note (preferred_provider) — consistent.

**Verdict:** OK. No changes needed.

---

## 15–26. mmm/docs (03–14)

**Read:** Scanned 03_ARCHITECTURE, 04_DATA_MODEL, 05_TRANSFORMS, 06_MODELS, 07_TECHNICAL_SPEC, 08_UX_FLOW, 09_AI_ANALYSIS, 10_BUILD_MMM, 11_WIREFRAME_PROMPT, 12_PROJECT_REVIEW_PROMPT, 13_REVIEW_RESPONSE, 14_IMPROVEMENTS.

**Consistency check (summary):**
- **03_ARCHITECTURE:** References 05_TRANSFORMS. OK.
- **04_DATA_MODEL:** ModelResult → 06_MODELS.md. OK.
- **05_TRANSFORMS:** No broken refs. OK.
- **06_MODELS:** References 14_IMPROVEMENTS, 05_TRANSFORMS. OK.
- **07_TECHNICAL_SPEC:** 06_MODELS, 04_DATA_MODEL, 10_BUILD_MMM. OK.
- **08_UX_FLOW:** No doc refs. OK.
- **09_AI_ANALYSIS:** Credentials schema; Q&A dict format. OK.
- **10_BUILD_MMM:** Single-file statement, spec refs table with numbered names (01_INDEX, 03_ARCHITECTURE, 04_DATA_MODEL, 06_MODELS, 05_TRANSFORMS, 09_AI_ANALYSIS, 08_UX_FLOW, 07_TECHNICAL_SPEC, 11_WIREFRAME_PROMPT). Steps 1–8, task list. OK.
- **11_WIREFRAME_PROMPT:** 10_BUILD_MMM. OK.
- **12_PROJECT_REVIEW_PROMPT:** Source-of-truth note at top; embedded One-Shot Steps 1–8. OK.
- **13_REVIEW_RESPONSE:** References 10_BUILD_MMM; some historical BUILD_MMM naming — acceptable (review response).
- **14_IMPROVEMENTS:** 10_BUILD_MMM, 04_DATA_MODEL refs. OK.

**Verdict:** All OK. No changes needed.

---

## Summary of fixes applied

| File | Fix |
|------|-----|
| README.md | Run command: added `source .venv/bin/activate` |
| docs/CHECKLIST.md | Phase 1.5 verify: added numpy, arviz to match 02_SETUP |
| docs/AI_COPILOT_GUIDE.md | Plotly → Streamlit in prompt examples |
| docs/PROJECT_READINESS_REVIEW.md | Gap 4: GUIDELINES now "Gap closed" |

---

