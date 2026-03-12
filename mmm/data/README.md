# Data directory

Start with the committed demo file `mmm_demo_sample.csv` so the team can validate the happy path before switching to business data.

Required columns:

- `date`
- `target` (leads)
- at least one `*_spend` column

Use the sample file first, then replace it with business data when the app flow is already working.

Document quirks here when you switch to business data:

- column renames
- date format issues
- units or currency notes
- channels excluded from the model
