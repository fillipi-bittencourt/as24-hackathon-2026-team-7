# Decisions Framework — Agent Design Anchor

> **For agents:** Every view and metric you build MUST map to one of these three questions. Use this as the design anchor for all data product work.
> **Repo default:** Business area for this repository is Marketing ROI / MMM. Keep scope there unless the user explicitly asks to change it.
> **Delivery principle:** usable first, fancy later. Ship a stable decision flow before adding advanced visuals or AI extras.

---

## [decision_1] What is happening?

**purpose:** Situational awareness. Current state at a glance.

**agent_mapping:**
- Implement: High-level KPIs (current vs. target or prior period)
- Implement: Key trends (time series, sparklines)
- Implement: Status indicators (red/amber/green)

**examples:**
- Revenue down 12% vs. last quarter
- Customer churn increased in last 30 days
- Inventory turnover below target in 3 regions
- Marketing spend up but conversion flat

---

## [decision_2] Why is it happening?

**purpose:** Root cause. Executives need drivers before acting.

**agent_mapping:**
- Implement: Breakdowns (by region, product, segment, channel)
- Implement: Comparisons (this vs. that, before vs. after)
- Implement: Drill-down or filters to explore drivers

**examples:**
- Revenue drop driven by Region X and Product Y
- Churn concentrated in segment Z after price increase
- Slow turnover due to overstock of SKU category A
- Conversion flat because traffic quality declined

---

## [decision_3] What should leadership do next?

**purpose:** Action. Clear, prioritized recommendations.

**agent_mapping:**
- Implement: Summary of top 3–5 recommended actions
- Implement: Priority or impact indicators
- Optional: Simple scenario or sensitivity view

**examples:**
- Reallocate budget from Channel A to Channel B
- Launch retention campaign for segment Z
- Run promotion on overstocked category A
- Pause low-quality traffic sources

---

## [mapping_table] Business Area Mapping — Marketing ROI / MMM

| question | answer |
|----------|--------|
| What is happening? | Marketing spend is X. Modelled **leads** contribution by channel shows which channels are driving (or not driving) outcomes. Top-line: total attributed leads, share contributed by media vs baseline, R² of the fitted model. Success metric: **cost per lead (CPL)**. |
| Why is it happening? | **Channel CPL** differs: some channels have high adstock carryover (long-lasting effect), others saturate quickly. The model decomposes spend into attributed leads per channel, revealing which budget delivers the best cost per lead and which is weak at the margin. |
| What should leadership do next? | Reallocate budget from **high-CPL** channels to **low-CPL** channels. The model quantifies the expected improvement in cost per lead. Specific recommendation: shift X% of [weakest CPL channel] spend to [strongest CPL channel]. |

**Agent:** When building, ensure each view corresponds to one row. Reject features that do not map to any row.
