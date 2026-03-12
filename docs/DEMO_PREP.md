# Demo Prep

Use this file to keep the live run short, stable, and easy to narrate.

---

## Demo goal

Show that the team rebuilt decision support with a usable MMM app that answers:

1. What is happening
2. Why is it happening
3. What should leadership do next

---

## Demo-safe mode

Use this as the default live path unless you have already tested the full advanced flow on the presentation machine.

1. Start with `mmm/data/mmm_demo_sample.csv`
2. Use the sidebar step menu and confirm the file loads cleanly in `Data`
3. Optionally open `Info` if the audience needs the MMM explainer
4. Keep the default transforms in `Config`
5. Fit `OLS`
6. Fit `Ridge`
7. Open `Results`
8. Use `All data`
9. Show the four top metrics
10. Show the holdout validation view
11. Show the channel breakdown table
12. Open `Channel Insights` and show the stacked time chart and saturation curves
13. Open `AI`
14. Select `In-depth`
15. Keep `Include all fitted models in the analysis context` enabled
16. Generate analysis

Avoid fitting `PyMC` live unless you already tested that exact machine and dataset.

---

## What to say

### What is happening

- Total leads: `[fill in]`
- Media leads: `[fill in]`
- Baseline leads: `[fill in]`
- Unexplained gap: `[fill in]`

### Why is it happening

- Best channel by CPL: `[fill in]`
- Weakest channel by CPL: `[fill in]`
- Most important contribution pattern: `[fill in]`

### What should leadership do next

- Directional action: `[fill in]`
- Suggested budget shift: `[fill in]`
- Confidence note: `This is an in-sample model. The recommendation is directional, not a forecast.`

---

## Recommended narration

- `Data` proves the file is valid and ready for modeling
- `Config` shows the assumptions are simple and controllable
- `Fit` shows that two methods agree on the broad story
- `Results` translates the model into leads, efficiency, and action
- `AI` turns the model output into an executive-ready explanation

---

## If latency hits

- if AI is slow, stop after `Results`
- if `PyMC` is slow, skip it
- if business data is unstable, switch to the sample file immediately
- if the app is slow, show prepared screenshots and narrate the findings

---

## AI line

Use one sentence:

`We used AI both during development and at runtime to turn model outputs into an executive-ready analysis.`

---

## Backup assets

- one screenshot of the `Results` top section
- one screenshot of the channel breakdown
- one screenshot of the AI analysis
- sample CSV ready to load

---

## Final checks

- [ ] app opens on the presentation machine
- [ ] sample file is available and easy to load
- [ ] presenter knows the top and weakest channel
- [ ] AI credentials work before the presentation starts
- [ ] backup screenshots are accessible
