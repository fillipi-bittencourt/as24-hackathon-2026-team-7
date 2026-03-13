# Changelog

This file tracks significant completed work in sequence order.

## How to use

- Add one new entry after each completed task item
- Use the next number in sequence
- Keep entries short and factual
- Include task, change, files, and reason

## Entries

### 068
- Task
  Make user-facing outputs consistent with the faithful interpretation layer
- Change
  Updated Results labels, help text, compact summary metrics, channel-share wording, the in-app MMM guide, and the AI payload semantics so the app now talks about raw media contribution, baseline contribution, and signed residual gap instead of the old bounded unexplained-story framing, while also formatting CPL comparison outputs more clearly
- Files
  `mmm/app.py`, `mmm/src/ui_content.py`, `mmm/src/ai/client.py`, `mmm/tests/test_models_smoke.py`, `CHANGELOG.md`
- Reason
  Prevent the app from showing statistically faithful numbers while still describing them with stale bounded-output language that could confuse users or make the visible outputs feel internally inconsistent

### 067
- Task
  Add repeatable model smoke coverage and harden PyMC defaults
- Change
  Added an automated smoke-test suite covering the frequentist models, the PyMC path, single-channel plus control input, zero-variance channels, holdout diagnostics, and faithful AI payload construction, then raised the default PyMC sampler settings to 500 draws, 500 tune, and 4 chains to make the shipped Bayesian path more stable under the sample-data regression run
- Files
  `mmm/tests/test_models_smoke.py`, `mmm/src/app_state.py`, `CHANGELOG.md`
- Reason
  Replace one-off manual checks with a repeatable regression command and reduce the chance that the default PyMC flow looks successful while still producing avoidable convergence warnings

### 066
- Task
  Replace bounded interpretation with faithful model decomposition
- Change
  Removed clipping from the stored baseline contribution, added faithful attribution helpers based on raw channel contribution plus signed residual gap, rewired Results and AI to use the raw fitted decomposition instead of the bounded storytelling layer, and updated the AI analysis prompt to reason about residual gap rather than an artificially cleaned unexplained bucket
- Files
  `mmm/app.py`, `mmm/src/results_helpers.py`, `mmm/src/models/base.py`, `mmm/src/models/pymc_model.py`, `mmm/src/ai/client.py`, `mmm/src/ai/prompts/analysis_prompt.txt`, `CHANGELOG.md`
- Reason
  Keep the interpretation layer statistically faithful to the fitted model so the business-facing outputs and AI narrative stop clipping, rescaling, or reassigning model components for presentation convenience

### 065
- Task
  Final project scrutiny cleanup
- Change
  Tightened the demo experience by improving the Overview VIF calculation, removing repo-local saved session artifacts from the shipped demo state, and aligning the remaining demo and architecture docs to the current workflow and the saved-state PyMC presentation strategy
- Files
  `mmm/src/data_overview.py`, `README.md`, `mmm/README.md`, `docs/CHECKLIST.md`, `docs/DEMO_PREP.md`, `mmm/docs/03_ARCHITECTURE.md`, `mmm/docs/06_MODELS.md`, `CHANGELOG.md`
- Reason
  Remove the last avoidable confusion and make the shipped branch cleaner, more coherent, and safer for the presentation flow

### 064
- Task
  Tighten persistent commit rule
- Change
  Clarified the always-apply commit workflow rule so completed user-requested changes must be committed once validated and should not be left uncommitted at the end of a task or turn
- Files
  `.cursor/rules/commit-and-push-workflow.mdc`, `CHANGELOG.md`
- Reason
  Make the user’s expectation around committing every completed change explicit and persistent for future work

### 063
- Task
  Final demo hardening pass
- Change
  Tightened the final demo path by fixing upload-vs-local source selection, aligning saturation curve generation with the current Results wiring, hiding unsupported optional PyMC and Anthropic options in lightweight environments, cleaning the demo guidance to prefer saved-state PyMC demos, and syncing the architecture and model docs to the shipped behavior
- Files
  `mmm/app.py`, `README.md`, `mmm/README.md`, `docs/CHECKLIST.md`, `docs/DEMO_PREP.md`, `mmm/docs/03_ARCHITECTURE.md`, `mmm/docs/06_MODELS.md`, `CHANGELOG.md`
- Reason
  Remove the last avoidable demo surprises so the app, environment behavior, and presenter-facing documentation all point to the same safest path

### 062
- Task
  Demo cohesion and diagnostics cleanup
- Change
  Clarified filtered-gap semantics across Results and AI, softened the Overview multicollinearity language to frame it as a pre-model diagnostic, skipped the expensive PyMC holdout refit in the demo flow, moved the Overview logic into a dedicated module, and synchronized the main demo-facing docs to the current `Data -> Overview -> Config -> Priors -> Fit -> Results -> AI` workflow with the separate `Guide` section
- Files
  `mmm/app.py`, `mmm/src/data_overview.py`, `mmm/src/results_helpers.py`, `mmm/src/ai/client.py`, `README.md`, `mmm/README.md`, `docs/CHECKLIST.md`, `docs/DEMO_PREP.md`, `mmm/docs/08_UX_FLOW.md`, `CHANGELOG.md`
- Reason
  Tighten the last demo-facing cohesion gaps so the app, AI output, and docs describe the same workflow and use less misleading statistical language

### 061
- Task
  Refine and decompose the data overview step
- Change
  Moved the new `Overview` workflow logic into a dedicated `data_overview` module and expanded it with health tags, channel spend aggregation summaries, richer multicollinearity risk tags, and a cleaner statistical inspection flow for the validated dataset
- Files
  `mmm/app.py`, `mmm/src/data_overview.py`, `CHANGELOG.md`
- Reason
  Keep the workflow code cleaner while making the dataset-inspection step more useful as a real pre-modeling statistical review rather than a basic summary page

### 060
- Task
  Add persistent code structure rule
- Change
  Added a new always-apply Cursor rule that tells the agent to decompose code into smaller modules when it improves clarity, keep concerns separated, prefer pure helpers for calculations, and centralize repeated state-reset logic instead of copying it across files
- Files
  `.cursor/rules/code-structure-and-maintainability.mdc`, `CHANGELOG.md`
- Reason
  Make the user’s maintainability preference persistent so future work naturally favors cleaner structure and safer refactors

### 059
- Task
  Add data overview workflow step
- Change
  Added a dedicated `Overview` step after `Data` that surfaces validated dataset coverage, target behavior, per-input diagnostics, a target time-series granularity selector, strongest correlation pairs, a full correlation matrix, and VIF-based multicollinearity checks before transform selection and model fitting
- Files
  `mmm/app.py`, `CHANGELOG.md`
- Reason
  Give users an in-app statistical review layer for the dataset so they can spot weak signal, poor input quality, and multicollinearity before they start interpreting coefficients or fitting models

### 058
- Task
  Thorough regression test and follow-up fixes
- Change
  Ran a full scripted Streamlit app regression flow covering guide navigation, local data validation, transform application, OLS and Ridge fitting, Results filtering, session save-clear-load, AI generation, and AI stale-state behavior, then fixed additional edge cases around same-filename dataset invalidation, filtered-view decomposition consistency, safer session selector formatting, deep-merged restored defaults, and holdout-failure isolation
- Files
  `mmm/app.py`, `mmm/src/app_state.py`, `mmm/src/session_persistence.py`, `mmm/src/utils.py`, `mmm/src/ai/client.py`, `mmm/src/results_helpers.py`, `CHANGELOG.md`
- Reason
  Verify the app end to end with an executable test flow and close the remaining trust and stale-state gaps that only surfaced under integrated runtime testing

### 057
- Task
  Add Bayesian diagnostics layer
- Change
  Added PyMC sampler diagnostics capture and a dedicated Results diagnostics section that surfaces chain count, divergences, tree-depth hits, `r_hat`, and effective sample size, while also passing those diagnostics into the AI analysis payload so weak Bayesian runs are easier to identify and explain
- Files
  `mmm/app.py`, `mmm/src/models/pymc_model.py`, `mmm/src/ai/client.py`, `mmm/src/ai/prompts/analysis_prompt.txt`, `CHANGELOG.md`
- Reason
  Make Bayesian uncertainty outputs more transparent and prevent users from treating weak PyMC interval results as stronger evidence than the sampler quality supports

### 056
- Task
  Cohesion and statistical soundness pass
- Change
  Fixed restored-session source handling, prevented stale setup and AI state from surviving data changes, made the chosen AI provider authoritative, blocked failed AI responses from becoming exportable summaries, aligned filtered Results exports with the visible channel view, corrected the recent-period window logic, standardized penalized models internally, improved Bayesian defaults by raising chains and suppressing weak interval output, and added safer recommendation gating when validation is weak
- Files
  `mmm/app.py`, `mmm/src/app_state.py`, `mmm/src/ai/client.py`, `mmm/src/results_helpers.py`, `mmm/src/session_persistence.py`, `mmm/src/models/base.py`, `mmm/src/models/ridge.py`, `mmm/src/models/lasso.py`, `mmm/src/models/elasticnet.py`, `mmm/src/models/pymc_model.py`, `CHANGELOG.md`
- Reason
  Keep the app coherent end to end, reduce stale-state and export mismatches, and make the decision layer and model outputs more statistically defensible

### 055
- Task
  Review structure and decompose app code
- Change
  Reviewed the Streamlit app structure, extracted the shared guide and table-help UI content into a dedicated `ui_content` module, and centralized repeated state-reset behavior in `app_state` so data, transform, and AI invalidation paths stay consistent across the app
- Files
  `mmm/app.py`, `mmm/src/app_state.py`, `mmm/src/setup_assistant.py`, `mmm/src/ui_content.py`, `CHANGELOG.md`
- Reason
  Reduce `app.py` size, lower coupling between workflow logic and static copy, and prevent subtle stale-state bugs caused by duplicated reset blocks

### 054
- Task
  Clarify the guide explanations
- Change
  Expanded the standalone MMM guide with a glossary of core terms and rewrote the model, transform, workflow, and output explanations so jargon is defined inline instead of being assumed
- Files
  `mmm/app.py`, `CHANGELOG.md`
- Reason
  Make the guide usable by non-experts and reduce confusion around MMM-specific terminology such as adstock, saturation, priors, holdout, and shrinkage

### 053
- Task
  Move and redesign the info page
- Change
  Removed `Info` from the numbered workflow, added it as a standalone sidebar guide section, and replaced the table-heavy help page with a narrative MMM guide built from workflow explainers, model notes, transform guidance, output-reading sections, and a trust warning
- Files
  `mmm/app.py`, `CHANGELOG.md`
- Reason
  Make the help content easier to browse as reference material and easier to understand than dense comparison tables inside the main workflow

### 052
- Task
  Aggregate duplicate dates on load
- Change
  Updated MMM data conversion so duplicate valid dates are consolidated into one row by summing numeric values and keeping the first non-empty non-numeric value, then surfaced a Data-step warning showing how many extra rows were collapsed
- Files
  `mmm/src/utils.py`, `mmm/app.py`, `mmm/src/setup_assistant.py`, `CHANGELOG.md`
- Reason
  Allow date-level modeling inputs to recover automatically from duplicate-date files instead of failing validation when the intended behavior is additive aggregation

### 051
- Task
  Strengthen AI rigor and tone
- Change
  Updated the AI analysis and setup prompts to require a statistical rigor check, clearer confidence language, and a sharper executive tone while expanding the analysis payload with holdout validation and methodology notes so the model can reflect app-specific trust limits
- Files
  `mmm/src/ai/client.py`, `mmm/src/ai/prompts/analysis_prompt.txt`, `mmm/src/ai/prompts/setup_prompt.txt`, `CHANGELOG.md`
- Reason
  Make AI outputs more trustworthy, better written, and less likely to overstate weak or methodologically limited MMM evidence

### 050
- Task
  Save, load, and clear MMM session state
- Change
  Added local session persistence so the app can save the current MMM workspace, reload a previous run with data, transforms, fitted model outputs, and AI analysis, and clear the current working state from a new sidebar session control block
- Files
  `mmm/app.py`, `mmm/src/app_state.py`, `mmm/src/session_persistence.py`, `mmm/.gitignore`, `CHANGELOG.md`
- Reason
  Let users pause and resume analysis without rerunning the full workflow and give the app explicit state management controls

### 049
- Task
  Keep only mock CSVs in git
- Change
  Updated the ignore rules and added a Cursor rule so only `mmm/data/mmm_demo_sample.csv` may be committed as CSV, then removed `mmm/data/data.csv` from version control while keeping it local
- Files
  `.gitignore`, `mmm/.gitignore`, `.cursor/rules/mockdata-only-csvs.mdc`, `mmm/data/data.csv`, `CHANGELOG.md`
- Reason
  Prevent business CSV files from being committed or pushed while still allowing the mock demo dataset to stay in the repo

### 048
- Task
  Export source provenance
- Change
  Updated the results, AI, and complete overview exports so they explicitly include the source filename from the loaded dataset, making it clear whether the artifacts were generated from `data.csv` or another file
- Files
  `mmm/app.py`, `mmm/src/export_helpers.py`, `CHANGELOG.md`
- Reason
  Make exported artifacts auditable and remove ambiguity about which dataset was used during a run

### 047
- Task
  Include business dataset and pending app updates
- Change
  Added the business `data.csv` file to version control and committed the pending app changes so the repo reflects the current working MMM setup and data source
- Files
  `mmm/data/data.csv`, `mmm/app.py`, `CHANGELOG.md`
- Reason
  Avoid omitting the main dataset from the branch and keep the repository aligned with the actual app state being used

### 046
- Task
  Commit and push workflow rule
- Change
  Added an always-apply Cursor rule that instructs the agent to work like a developer and commit plus push after each completed task while excluding unrelated local artifacts
- Files
  `.cursor/rules/commit-and-push-workflow.mdc`, `CHANGELOG.md`
- Reason
  Make the expected delivery workflow persistent so future work is committed and pushed task by task instead of being left local

### 045
- Task
  AI setup explanation block
- Change
  Added an explicit “AI applied this setup because” summary in the Data step so stakeholders can see how the ingested-data evaluation drove the selected columns, transforms, priors, and data-quality actions
- Files
  `mmm/app.py`, `CHANGELOG.md`
- Reason
  Make the AI-driven setup auditable and understandable instead of leaving it as a black-box automation step

### 044
- Task
  Full project consistency and stability pass
- Change
  Fixed provider-selection logic, cleared stale downstream state on invalid data or regularization-only changes, stabilized decomposition chart colors, raised the minimum row requirement for stable modeling and holdout checks, and aligned the active docs to the current 7-step full-launcher app
- Files
  `mmm/src/ai/client.py`, `mmm/app.py`, `mmm/src/utils.py`, `mmm/src/results_helpers.py`, `README.md`, `mmm/README.md`, `docs/CHECKLIST.md`, `docs/DEMO_PREP.md`, `docs/15_PROJECT_IMPROVEMENTS_REVIEW.md`, `mmm/docs/02_SETUP.md`, `mmm/docs/03_ARCHITECTURE.md`, `mmm/docs/08_UX_FLOW.md`, `mmm/docs/10_BUILD_MMM.md`, `mmm/docs/11_WIREFRAME_PROMPT.md`, `CHANGELOG.md`
- Reason
  Remove the highest-impact active inconsistencies and make the shipped app and docs behave like one coherent product

### 043
- Task
  Statistical rigor upgrades
- Change
  Restored raw statistical model outputs, added time-based holdout validation and validation diagnostics, and clarified the distinction between raw fitted metrics and the bounded business-facing decomposition
- Files
  `mmm/app.py`, `mmm/src/models/ols.py`, `mmm/src/models/ridge.py`, `mmm/src/models/lasso.py`, `mmm/src/models/elasticnet.py`, `mmm/src/models/pymc_model.py`, `mmm/docs/06_MODELS.md`, `mmm/docs/08_UX_FLOW.md`, `CHANGELOG.md`
- Reason
  Move the app closer to production-ready MMM rigor by separating statistical fit from business communication and by adding a basic generalisation check

### 042
- Task
  In-app MMM info step
- Change
  Added a dedicated Info step that explains the MMM workflow, model types, when each model should be used, how transforms work, and how to read the outputs in business terms
- Files
  `mmm/app.py`, `CHANGELOG.md`
- Reason
  Give users an always-available explanation layer inside the product instead of forcing them to infer MMM concepts from the controls and outputs alone

### 041
- Task
  Business-ready MMM visuals
- Change
  Added actual-versus-predicted trend lines, spend-share versus contribution-share benchmarking, a top-N plus other time decomposition view, and stronger quick MMM interpretation so the Results step reads more like a real MMM decision tool
- Files
  `mmm/app.py`, `mmm/src/results_helpers.py`, `CHANGELOG.md`
- Reason
  Improve the business-facing visual layer and give analysts and leaders better MMM-specific context beyond tables and simple efficiency rankings

### 040
- Task
  AI column selection and full setup application
- Change
  Extended the AI setup assistant so it can recommend and apply the selected date, target, channels, and controls before applying priors and transforms, making the ingested-data review drive the full MMM setup automatically
- Files
  `mmm/app.py`, `mmm/src/setup_assistant.py`, `mmm/src/ai/prompts/setup_prompt.txt`, `CHANGELOG.md`
- Reason
  Make the AI dataset evaluation actually shape the complete MMM configuration instead of only explaining the user’s current manual selection

### 039
- Task
  AI setup auto-apply
- Change
  Updated the AI setup assistant so it now applies the suggested priors and transform configuration immediately after analysis, computes the transformed dataset automatically, and keeps the settings editable in the later steps
- Files
  `mmm/app.py`, `CHANGELOG.md`
- Reason
  Make the ingested-data evaluation actually drive the MMM setup instead of only producing suggestions that still require a second manual apply step

### 038
- Task
  Chart labels and total tooltips
- Change
  Added period total labels and fuller tooltips to the stacked lead charts so the business-facing visuals now show direct labels and complete tooltip context including totals and shares
- Files
  `mmm/app.py`, `mmm/src/results_helpers.py`, `CHANGELOG.md`
- Reason
  Make the lead decomposition visuals easier to read quickly and ensure the charts always show labels plus full tooltip context

### 037
- Task
  Stacked lead share chart
- Change
  Replaced the separate lead comparison bars in Results with a stacked period-share chart so the selected period shows the split between media, baseline, and unexplained leads as one whole
- Files
  `mmm/app.py`, `mmm/src/results_helpers.py`, `CHANGELOG.md`
- Reason
  Make the top-level decomposition easier to read as shares of one selected period instead of separate bar values

### 036
- Task
  Non-negative media effects
- Change
  Enforced the business rule that spend channels cannot produce negative lead impact by clipping media coefficients to zero or above in the model result layer and recalculating the business-facing predictions and fit metrics from that constrained view
- Files
  `mmm/src/models/base.py`, `mmm/src/models/ols.py`, `mmm/src/models/ridge.py`, `mmm/src/models/lasso.py`, `mmm/src/models/elasticnet.py`, `mmm/src/models/pymc_model.py`, `CHANGELOG.md`
- Reason
  Keep media-spend outputs aligned with the business assumption that channels should explain some leads or no leads, but not negative leads

### 035
- Task
  MMM diagnostics in Results
- Change
  Added richer MMM-specific interpretation to the Results step including saturation status, average spend and contribution diagnostics, transform interpretation notes, and visible saturation curves for the selected channels
- Files
  `mmm/app.py`, `CHANGELOG.md`
- Reason
  Make the app feel more like a real MMM tool instead of a light regression wrapper and give users the transform diagnostics needed to interpret channel behavior

### 034
- Task
  Unexplained attribution fix
- Change
  Changed the displayed attribution logic to work period by period against the observed series so model over and under prediction no longer cancel out at the aggregate level and hide the unexplained component
- Files
  `mmm/src/results_helpers.py`, `mmm/app.py`, `mmm/src/ai/client.py`, `CHANGELOG.md`
- Reason
  Keep an explicit unexplained portion in the business-facing decomposition instead of making the model look artificially perfect when aggregate errors net to zero

### 033
- Task
  Reference values in the app
- Change
  Added built-in reference value panels for transforms, Bayesian priors, and result interpretation so users have practical benchmark ranges directly inside the workflow
- Files
  `mmm/app.py`, `CHANGELOG.md`
- Reason
  Make the app easier to interpret without external documentation and give users sensible benchmark ranges while configuring and reading the model

### 032
- Task
  Button based sidebar navigation
- Change
  Replaced the sidebar radio step selector with a browsable button based step menu and updated the active UX docs to reflect the new interaction pattern
- Files
  `mmm/app.py`, `mmm/docs/08_UX_FLOW.md`, `mmm/docs/11_WIREFRAME_PROMPT.md`, `CHANGELOG.md`
- Reason
  Deliver the guided navigation flow without relying on radio controls and keep the docs aligned with the implemented menu

### 031
- Task
  External prompt files for AI analysis
- Change
  Moved the hardcoded AI analysis and setup assistant prompt text out of `src/ai/client.py` into editable prompt files and updated the client to load and render those templates at runtime
- Files
  `mmm/src/ai/client.py`, `mmm/src/ai/prompts/analysis_prompt.txt`, `mmm/src/ai/prompts/setup_prompt.txt`, `CHANGELOG.md`
- Reason
  Make prompt iteration easier without editing Python logic each time the analysis wording or setup guidance changes

### 030
- Task
  Consistency cleanup
- Change
  Aligned the active docs and user-facing messages with the current `.env` credential path, corrected the PyMC model description to match the implementation, repositioned the build checklist as historical engineering guidance, and removed stale placeholder comments from implemented model files
- Files
  `mmm/src/ai/client.py`, `mmm/app.py`, `mmm/src/models/lasso.py`, `mmm/src/models/elasticnet.py`, `mmm/docs/06_MODELS.md`, `mmm/docs/10_BUILD_MMM.md`, `mmm/docs/01_INDEX.md`, `docs/AI_COPILOT_GUIDE.md`, `CHANGELOG.md`
- Reason
  Reduce contradictions between the live app, the technical docs, and the codebase so maintenance and handoff are more reliable

### 029
- Task
  Runtime version alignment
- Change
  Updated the active setup docs, launcher, requirements note, and Python pin to consistently reflect `3.9+` support instead of `3.10+`
- Files
  `mmm/.python-version`, `mmm/requirements.txt`, `docs/CHECKLIST.md`, `mmm/docs/02_SETUP.md`, `mmm/run_app.sh`, `CHANGELOG.md`
- Reason
  Keep the stated supported runtime aligned across the runnable project and documentation

### 028
- Task
  Documentation sync for current app flow
- Change
  Updated the setup, run, UX, AI, and verification docs to reflect the sidebar step menu, `.env` default credential path, and `run_app.sh` launcher while adding a current-state note to the engineering build history
- Files
  `README.md`, `mmm/README.md`, `docs/CHECKLIST.md`, `docs/DEMO_PREP.md`, `mmm/docs/02_SETUP.md`, `mmm/docs/03_ARCHITECTURE.md`, `mmm/docs/07_TECHNICAL_SPEC.md`, `mmm/docs/08_UX_FLOW.md`, `mmm/docs/09_AI_ANALYSIS.md`, `mmm/docs/10_BUILD_MMM.md`, `mmm/docs/11_WIREFRAME_PROMPT.md`, `mmm/.env.example`, `CHANGELOG.md`
- Reason
  Keep the documentation aligned with the actual runnable app so setup, demo, and handoff steps stay reliable

### 027
- Task
  Local app launcher script
- Change
  Added a `run_app.sh` helper that checks for the local virtual environment, installs full dependencies when needed, and starts the Streamlit server while printing the local URL in the terminal
- Files
  `mmm/run_app.sh`, `CHANGELOG.md`
- Reason
  Make it easier to bootstrap and run the app from one command without repeating the setup steps manually

### 026
- Task
  Sidebar step menu navigation
- Change
  Replaced the top tab navigation with a sidebar step menu that keeps the existing section behavior, adds step descriptions, and shows step readiness inline in the menu labels
- Files
  `mmm/app.py`, `mmm/src/app_state.py`, `CHANGELOG.md`
- Reason
  Make the workflow feel more guided and easier to browse without doing a risky full navigation rewrite

### 025
- Task
  Final stability and view consistency fixes
- Change
  Fixed the remaining Results runtime errors, aligned Results and AI to the selected period and visible channels, and added stale-analysis protection so exports are only available when the AI summary matches the current view
- Files
  `mmm/app.py`, `mmm/src/ai/client.py`, `mmm/src/results_helpers.py`, `CHANGELOG.md`
- Reason
  Make the app behave consistently end to end and remove mismatches between what the user sees, what the AI explains, and what the exports contain

### 024
- Task
  Results chart runtime fix
- Change
  Removed the unsupported `width` argument from Streamlit Altair chart calls and moved sizing onto the chart definitions so the Results tab no longer crashes at runtime
- Files
  `mmm/app.py`, `mmm/src/results_helpers.py`, `CHANGELOG.md`
- Reason
  Restore the full Results and downstream AI flow after a browser-tested runtime failure in the chart rendering path

### 023
- Task
  Self explanatory UI copy pass
- Change
  Added clearer tab level definitions, stronger control tooltips, and more explanatory captions around comparison and output tables so the app is easier to understand without external documentation
- Files
  `mmm/app.py`, `CHANGELOG.md`
- Reason
  Make the app easier to navigate for first time users and reduce ambiguity during live use and demo narration

### 022
- Task
  App helper decomposition
- Change
  Split the oversized app helper logic into focused modules for state, results helpers, setup assistant behavior, and export builders while keeping the tab rendering flow in `app.py`
- Files
  `mmm/app.py`, `mmm/src/app_state.py`, `mmm/src/results_helpers.py`, `mmm/src/setup_assistant.py`, `mmm/src/export_helpers.py`, `mmm/src/ai/__init__.py`, `CHANGELOG.md`
- Reason
  Make the codebase easier to maintain and safer to extend without doing a high-risk full UI refactor

### 021
- Task
  Complete overview final export
- Change
  Added a final overview export that combines column-selection reasoning, data quality and completion notes, transform reasoning, prior choices, current results, and AI suggestions into one CSV and one PDF
- Files
  `mmm/app.py`, `mmm/src/ai/client.py`, `CHANGELOG.md`
- Reason
  Make the end deliverable self-contained so the team can share one artifact that explains both setup choices and business conclusions

### 020
- Task
  AI setup assistant for transforms and priors
- Change
  Added an AI driven setup review that inspects the loaded dataset, suggests transform settings, flags consistency and completion issues, recommends channel level PyMC priors with reasoning, and applies the suggested priors directly into the Priors tab
- Files
  `mmm/app.py`, `mmm/src/ai/client.py`, `mmm/src/models/pymc_model.py`, `CHANGELOG.md`
- Reason
  Cut setup time, surface data issues earlier, and make Bayesian configuration easier to use during a fast hackathon workflow

### 019
- Task
  Documentation alignment and AI guardrails
- Change
  Updated the project and app docs to reflect the current runnable 6 tab product, added a demo safe path, aligned setup and wireframe references, and tightened the runtime AI prompt to require numeric evidence and clearer trust limits
- Files
  `README.md`, `mmm/README.md`, `docs/CHECKLIST.md`, `docs/DEMO_PREP.md`, `docs/15_PROJECT_IMPROVEMENTS_REVIEW.md`, `mmm/docs/02_SETUP.md`, `mmm/docs/03_ARCHITECTURE.md`, `mmm/docs/07_TECHNICAL_SPEC.md`, `mmm/docs/08_UX_FLOW.md`, `mmm/docs/09_AI_ANALYSIS.md`, `mmm/docs/11_WIREFRAME_PROMPT.md`, `mmm/src/ai/client.py`, `CHANGELOG.md`
- Reason
  Keep the team and any agents aligned on the actual product state and make the AI output more trustworthy for live hackathon use

### 018
- Task
  Project scrutiny and reliability fixes
- Change
  Added a formal improvement review document and fixed high-impact reliability issues across validation, period filtering, MAPE computation, CSV loading, and AI credential precedence
- Files
  `docs/15_PROJECT_IMPROVEMENTS_REVIEW.md`, `mmm/src/utils.py`, `mmm/app.py`, `mmm/src/ai/client.py`, `CHANGELOG.md`
- Reason
  Reduce demo risk and make model outputs and AI setup more reliable under real hackathon conditions

### 017
- Task
  Bounded lead decomposition
- Change
  Normalized the displayed media, baseline, and unexplained lead parts so they add up cleanly to total leads and updated the results table to use bounded contribution values
- Files
  `mmm/app.py`, `CHANGELOG.md`
- Reason
  Make the business-facing decomposition intuitive and prevent media leads from exceeding total leads in the UI

### 016
- Task
  Five model verification
- Change
  Verified the full live flow with OLS, Ridge, Lasso, ElasticNet, and PyMC, including transforms, priors, comparisons, results filters, and AI rendering
- Files
  `CHANGELOG.md`
- Reason
  Confirm the app now truly supports all five models end to end

### 015
- Task
  Five model app wiring
- Change
  Exposed `Lasso` and `ElasticNet` in the app fit flow, passed through the needed regularization settings, and updated the build doc to reflect the complete five model set
- Files
  `mmm/app.py`, `mmm/docs/10_BUILD_MMM.md`, `CHANGELOG.md`
- Reason
  Make the full model comparison claim true in the app, not just in the documentation

### 014
- Task
  Remaining frequentist models
- Change
  Added `Lasso` and `ElasticNet` model classes and exported them from the shared models package
- Files
  `mmm/src/models/lasso.py`, `mmm/src/models/elasticnet.py`, `mmm/src/models/__init__.py`, `CHANGELOG.md`
- Reason
  Complete the full 5-model set so the app can compare OLS, Ridge, Lasso, ElasticNet, and PyMC

### 013
- Task
  Results UX improvements
- Change
  Added clearer section descriptions, short metric help text, total leads versus media leads visibility, unexplained portion visibility, labeled bar charts, and variable controls for the visuals
- Files
  `mmm/app.py`, `CHANGELOG.md`
- Reason
  Make the results easier to read and easier to explain during analysis and demo use

### 012
- Task
  Deck build guide
- Change
  Added a markdown guide for the team on how to structure a 6 slide plus demo presentation around the decision framework
- Files
  `docs/DECK_BUILD_INSTRUCTIONS.md`, `CHANGELOG.md`
- Reason
  Give the team a reusable presentation guide that matches the product story and audience needs

### 011
- Task
  Better tab guidance
- Change
  Improved the user-facing explanations at the top of the Data, Config, Priors, Fit, Results, and AI tabs
- Files
  `mmm/app.py`, `CHANGELOG.md`
- Reason
  Make the app easier to follow during a live demo and reduce ambiguity for first-time users

### 010
- Task
  PyMC verification and environment fix
- Change
  Fixed the Bayesian interval calculation, added graceful fit error handling, pinned SciPy to a compatible range, and verified the full Priors to PyMC to Results path in the live app
- Files
  `mmm/src/models/pymc_model.py`, `mmm/app.py`, `mmm/requirements.txt`, `mmm/requirements-mvp.txt`, `mmm/docs/10_BUILD_MMM.md`, `CHANGELOG.md`
- Reason
  Make the Bayesian option actually usable in the current environment and record the verified task completion in the build doc

### 009
- Task
  Priors tab and PyMC app wiring
- Change
  Added a dedicated Priors tab, connected the saved prior settings into the PyMC fit path, updated the results view for Bayesian intervals, and aligned the UX and build docs
- Files
  `mmm/app.py`, `mmm/docs/10_BUILD_MMM.md`, `mmm/docs/08_UX_FLOW.md`, `CHANGELOG.md`
- Reason
  Make the Bayesian path usable from the app instead of keeping priors hardcoded or hidden

### 008
- Task
  PyMC model implementation
- Change
  Added the Bayesian model class with configurable prior settings, posterior mean predictions, and interval outputs for coefficients and CPL
- Files
  `mmm/src/models/pymc_model.py`, `mmm/src/models/__init__.py`
- Reason
  Add the PyMC path as a real model option before wiring the priors controls into the app

### 007
- Task
  MVP verification
- Change
  Ran a browser smoke test against the live Streamlit app and marked the verified check steps in the build document
- Files
  `mmm/docs/10_BUILD_MMM.md`, `CHANGELOG.md`
- Reason
  Confirm the current MVP path works end to end before moving on to any further development or stretch work

### 006
- Task
  MVP app shell and task sync
- Change
  Replaced the placeholder app with the MVP Streamlit flow, wired Data, Config, Fit, Results, and AI tabs, and marked the completed build items in `mmm/docs/10_BUILD_MMM.md`
- Files
  `mmm/app.py`, `mmm/src/utils.py`, `mmm/docs/10_BUILD_MMM.md`
- Reason
  Move the repo from isolated modules to a working end-to-end MVP path and keep the build checklist in sync with the work already done

### 005
- Task
  MVP AI summary client
- Change
  Added credential loading, payload building, prompt generation, and the summary client for the single-model AI path
- Files
  `mmm/src/ai/__init__.py`, `mmm/src/ai/client.py`
- Reason
  Keep AI in the MVP without blocking the app when credentials or providers are missing

### 004
- Task
  MVP model layer
- Change
  Added the shared `ModelResult` contract, attribution builder, and MVP `OLS` and `Ridge` model classes
- Files
  `mmm/src/models/__init__.py`, `mmm/src/models/base.py`, `mmm/src/models/ols.py`, `mmm/src/models/ridge.py`
- Reason
  Let the app fit the first two models needed for the hackathon MVP and keep a shared output shape for Results and AI

### 003
- Task
  Transform functions
- Change
  Added geometric adstock, hill saturation, log saturation, and the shared media transform pipeline with the default spend path set to Geometric plus Log
- Files
  `mmm/src/transforms.py`
- Reason
  Make the config step produce model-ready float64 inputs with the repo default transformation order

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
