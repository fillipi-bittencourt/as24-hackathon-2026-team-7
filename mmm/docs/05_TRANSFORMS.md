# Transforms

Adstock and saturation applied to media variables before regression. **Each channel can use a different transformation type** — the user selects adstock type and saturation type per variable in the Config tab.

**Datatypes:** Inputs and outputs are numeric only. Channel columns must be **float64** (or convertible to float). Transforms are applied only to channel (media) columns; control columns pass through unchanged and are not adstocked or saturated. The combined regression input is a 2D array of dtype **float64** (channels first, then controls).

---

## Per-variable transformation type

For each channel (variable), the user selects:

| Choice | Adstock type | Saturation type |
|--------|---------------|-----------------|
| Options | **Geometric** \| **None** | **Log** \| **Hill** \| **None** |
| Default | Geometric | Log |
| None | No carryover; raw series passed through | No saturation; use adstock output (or raw) as regression input |

- **Adstock type:** `"geometric"` — apply geometric adstock with that channel’s θ; `"none"` — no adstock, use raw spend.
- **Saturation type:** `"log"` — apply `log(1 + x)` (no α/k); `"hill"` — apply Hill with that channel’s α and k; `"none"` — no saturation.

Application is still **adstock first, then saturation** per channel. Controls are never transformed. The regression is fit on the **transformed** channel series (and raw controls); coefficients are therefore in **leads per unit of transformed input**. CPL = raw spend / attributed leads stays in € per lead.

---

## Adstock

**Purpose:** Capture carryover effect — spend in period t affects periods t+1, t+2, ...

### Geometric

```
x_transformed[t] = x[t] + θ * x_transformed[t-1]
```

- **θ (theta):** Decay rate. Higher = longer carryover.
- **Range:** 0.1–0.9 typical.

### Weibull (Alternative)

Flexible shape; can model delayed peak. More params, less common in simple MMM.

---

## Saturation

**Purpose:** Diminishing returns — doubling spend does not double effect.

### Hill

```
f(x) = x^α / (k^α + x^α)
```

- **α (alpha):** Shape. Lower = faster saturation.
- **k:** Half-saturation level (spend at 50% of max effect).

### Log

```
f(x) = log(1 + x)
```

Simpler; no extra params. Often used as the first spend transformation to try.

---

## Application Order

1. Per channel: adstock first (if type ≠ none), then saturation (if type ≠ none).
2. Column order in output: channels first (matching `channel_cols`), then controls (no transforms).

```
raw_spend → [per channel: adstock(θ) if geometric] → [per channel: saturation (hill/log) if selected] → regression_input
```
