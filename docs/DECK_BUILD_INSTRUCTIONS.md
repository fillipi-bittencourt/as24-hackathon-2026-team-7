# Deck Build Instructions

## Goal

Build the presentation around the decision framework, not around the app tabs or the technical pipeline.

The story should answer three questions:

1. What is happening
2. Why is it happening
3. What should leadership do next

Everything in the deck should support one of those three answers.

## Audience

The presentation needs to work for:
- data analysts
- data managers
- CMO
- CEO

That means the deck should do two things at once:
- give executives a clear business recommendation
- give technical people enough confidence to trust the recommendation

## What context to include

Keep the context short and useful.

Include:
- this is a response to a BI blackout scenario
- the business area is Marketing ROI
- the product is an MMM MVP
- the target metric is leads
- the main business KPI is cost per lead
- the app validates data, transforms spend, compares models, and turns outputs into decisions
- AI is used to summarize the results, not replace them

Do not spend much time on:
- formulas
- architecture
- implementation details
- model math
- app internals

## What information is useful

If all 5 models are run, focus on the outputs that help people make and trust a decision.

Most useful:
- total attributed leads
- best channel by CPL
- weakest channel by CPL
- media vs baseline contribution
- main budget reallocation recommendation
- high-level comparison across models
- confidence and uncertainty framing

Useful credibility points:
- OLS gives the baseline
- Ridge, Lasso, and ElasticNet test stability
- PyMC adds uncertainty intervals and configurable priors
- model agreement increases trust

Less useful in the main deck:
- full coefficient tables
- transform equations
- detailed prior explanations
- too many charts
- full tab-by-tab walkthrough

## Main message

The deck should make the audience feel this:

- we understood the business problem
- we built a usable decision product under pressure
- the recommendation is grounded in evidence
- the result is more trustworthy because it is supported by multiple models
- AI helps communicate the outcome clearly

## Recommended deck structure

Use at least 6 slides. Keep the structure simple.

## Slide 1

### The problem

Set the business context.

Cover:
- BI is unavailable
- leadership still needs to make marketing decisions
- the team built a fallback decision product quickly

Purpose:
- create urgency
- frame the business relevance

## Slide 2

### What we built

Describe the product in one clean view.

Cover:
- it is an MMM decision tool
- it validates data
- it applies realistic marketing transforms
- it compares 5 models
- it translates results into decisions
- it uses AI to generate an executive summary

Purpose:
- explain the product without going deep into implementation

## Slide 3

### What is happening

Deliver the first executive answer.

Show:
- total attributed leads
- top channel by CPL
- media vs baseline split
- selected model fit

Purpose:
- give a quick read on current marketing effectiveness

## Slide 4

### Why is it happening

Show the drivers behind the outcome.

Show:
- channel-level CPL
- channel contribution
- carryover or saturation only where it matters
- brief note on model agreement

Purpose:
- explain the business drivers in a way that both analysts and executives can follow

## Slide 5

### What should leadership do next

State the recommendation clearly.

Show:
- strongest channel
- weakest channel
- directional budget shift
- confidence caveat

Important:
- frame the recommendation as directional
- do not frame it as a guaranteed forecast

Purpose:
- make the business action obvious

## Slide 6

### Why trust it

Use this slide to build confidence.

Cover:
- 5 models were compared
- OLS is the baseline
- regularized models test robustness
- PyMC adds uncertainty through priors and intervals
- AI translates results into executive language, but does not replace the model

Purpose:
- show that the result is not based on one fragile model

## Optional Slide 7

### AI summary

If time allows, show the AI layer briefly.

Cover:
- AI reads the model results
- AI turns them into executive language
- AI helps communicate the answer faster

Purpose:
- show the innovation layer without making it the center of the story

## How to talk about the 5 models

Do not give one slide per model.

Instead, frame them as a confidence stack:
- OLS provides the first baseline
- Ridge, Lasso, and ElasticNet test whether the recommendation survives regularization
- PyMC adds uncertainty and prior-based transparency

The point is not that there are 5 models.
The point is that multiple modeling approaches support the same decision pattern.

## How to use the app in the presentation

Use the app to support the slides, not replace them.

The app order is:
- Data
- Config
- Priors
- Fit
- Results
- AI

But the presentation order should be:
- problem
- what is happening
- why it is happening
- what to do next
- why trust it
- AI summary

Spend most of the live demo in:
- Results
- brief Priors
- brief AI

Keep Data, Config, and Fit short.

## Demo structure

After the 6 slides, do the live demo.

Do not demo every tab in equal depth.

Recommended order:
1. Data
2. Config
3. Priors
4. Fit
5. Results
6. AI

## Timing for 10 minutes

A good split would be:

- Slide 1: 1 minute
- Slide 2: 1 minute
- Slide 3: 1.5 minutes
- Slide 4: 1.5 minutes
- Slide 5: 1.5 minutes
- Slide 6: 1.5 minutes
- Demo: 2 minutes

If the live demo feels risky, shorten the earlier sections and keep more time for the demo.

## What technical detail to include

Only include technical detail when it helps answer:
- why should we trust this
- why is this better than relying on one model
- how does the product handle uncertainty

Good examples:
- we compared 5 models instead of relying on one
- PyMC gives interval estimates, not just point estimates
- priors are visible and configurable

Avoid turning the presentation into a modeling lecture.

## Tone

The deck should feel:
- clear
- practical
- calm
- business-focused
- credible

It should not feel:
- overly academic
- over-engineered
- like a technical tutorial
- like a product feature dump

## Team alignment before building slides

Before slide creation, the team should agree on:
- the one-line problem statement
- the one-line description of the product
- the top 3 numbers to remember
- the main recommendation
- the confidence caveat
- the one-paragraph explanation of why 5 models matter
- the one-sentence explanation of the AI role

## Simple rule for building each slide

For every slide, ask:

- does this help answer what is happening
- does this help answer why it is happening
- does this help answer what leadership should do next
- or does this help the audience trust those answers

If the answer is no, it probably does not belong in the main deck.

## Priority order

If you need to choose what matters most, use this order:

1. decision clarity
2. business usefulness
3. trust and evidence
4. product usability
5. technical sophistication

## Final target

The audience should leave thinking:

- this team understood the business problem
- this product gives a usable answer under pressure
- the recommendation is backed by more than one model
- the uncertainty is visible, not hidden
- AI helps communicate the result clearly
