from __future__ import annotations

from typing import Any

import pandas as pd
import streamlit as st


TABLE_COLUMN_HELP_TEXT = {
    "Date": "The date or period represented by the row.",
    "date": "The date or period represented by the row.",
    "Item": "The field or concept being described.",
    "Reference": "A benchmark range or default value used for interpretation.",
    "How to use it": "Short guidance on how to apply the reference value.",
    "Selected item": "The dataset field or selection decision being explained.",
    "Value": "The current value shown for that row.",
    "Reasoning": "Why the app or AI selected or recommended that value.",
    "Channel": "The marketing channel or driver being evaluated.",
    "Adstock": "The carryover transform used for the channel.",
    "Theta": "Carryover strength for geometric adstock. Higher means longer carryover.",
    "Saturation": "The diminishing-returns transform used for the channel.",
    "Alpha": "Hill saturation steepness parameter.",
    "K": "Hill half-saturation point where the curve reaches about half its maximum response.",
    "Family": "The prior distribution family used for the channel coefficient.",
    "Sigma scale": "How wide the prior uncertainty is before the data updates it.",
    "Model": "The fitted model being compared.",
    "R² in-sample": "Share of variation explained by the model on the same data used for fitting.",
    "RMSE in-sample": "Average prediction error on the same data used for fitting.",
    "MAE in-sample": "Average absolute prediction error on the same data used for fitting.",
    "MAPE in-sample (%)": "Average percentage prediction error on non-zero target rows in the fitting sample.",
    "MAPE in-sample coverage": "How many non-zero target rows were used in the in-sample MAPE calculation.",
    "R² holdout": "Share of variation explained on the holdout window not used for fitting.",
    "RMSE holdout": "Average prediction error on the holdout window.",
    "MAE holdout": "Average absolute prediction error on the holdout window.",
    "MAPE holdout (%)": "Average percentage prediction error on non-zero target rows in the holdout window.",
    "MAPE holdout coverage": "How many non-zero holdout rows were used in the holdout MAPE calculation.",
    "Coefficient": "Estimated channel effect in leads per unit of transformed channel input.",
    "Coefficient lower": "Lower uncertainty bound for the channel coefficient, when available.",
    "Coefficient upper": "Upper uncertainty bound for the channel coefficient, when available.",
    "CPL": "Cost per lead. Lower means more efficient lead generation.",
    "CPL lower": "Lower uncertainty bound for CPL, when available.",
    "CPL upper": "Upper uncertainty bound for CPL, when available.",
    "Contribution": "Total modeled leads attributed to the channel in the selected view.",
    "Contribution share (%)": "Share of actual leads attributed to the channel in the selected view.",
    "Share": "Share of actual leads attributed to the channel in the selected view.",
    "Share_pct": "Share of actual leads attributed to the channel in the selected view.",
    "Spend total": "Total spend for the channel in the selected period.",
    "Average weekly spend": "Average spend per period in the selected view.",
    "Average weekly contribution": "Average modeled leads contributed per period in the selected view.",
    "Carryover": "Approximate number of periods the channel effect lingers after spend.",
    "Saturation status": "Whether the channel looks under-saturated, near saturation, or over-saturated.",
    "Saturation note": "Short interpretation of the current saturation status.",
    "What it does": "Plain-language description of what the model or concept does.",
    "Best use case": "When this model or concept is most useful.",
    "Strength": "Main reason to prefer this model or concept.",
    "Watch out for": "Main limitation or caveat to keep in mind.",
    "Setting": "The transform or MMM setting being described.",
    "Use it when": "The situation where this transform choice is appropriate.",
    "Interpretation": "How to read the setting in MMM terms.",
    "Output": "The metric, chart, or artifact shown by the app.",
}

TABLE_NUMBER_COLUMNS = {
    "Theta",
    "Alpha",
    "K",
    "Sigma scale",
    "R² in-sample",
    "RMSE in-sample",
    "MAE in-sample",
    "MAPE in-sample (%)",
    "R² holdout",
    "RMSE holdout",
    "MAE holdout",
    "MAPE holdout (%)",
    "Coefficient",
    "Coefficient lower",
    "Coefficient upper",
    "Contribution",
    "Contribution share (%)",
    "Share",
    "Share_pct",
    "Spend total",
    "Average weekly spend",
    "Average weekly contribution",
}


def render_definitions_expander(
    title: str,
    definitions: list[tuple[str, str]],
) -> None:
    with st.expander(title, expanded=False):
        for label, description in definitions:
            st.markdown(f"**{label}**  \n{description}")


def render_reference_values_expander(
    title: str,
    reference_rows: list[tuple[str, str, str]],
) -> None:
    with st.expander(title, expanded=False):
        reference_df = pd.DataFrame(
            reference_rows,
            columns=["Item", "Reference", "How to use it"],
        )
        st.dataframe(
            reference_df,
            column_config=build_table_column_config(reference_df.columns),
            width="stretch",
        )


def build_table_column_config(columns: list[str] | pd.Index) -> dict[str, Any]:
    config: dict[str, Any] = {}
    for column in columns:
        column_name = str(column)
        help_value = TABLE_COLUMN_HELP_TEXT.get(column_name)
        if not help_value:
            continue
        if column_name in TABLE_NUMBER_COLUMNS:
            config[column_name] = st.column_config.NumberColumn(column_name, help=help_value)
        elif column_name in {"date", "Date"}:
            config[column_name] = st.column_config.DateColumn(column_name, help=help_value)
        else:
            config[column_name] = st.column_config.TextColumn(column_name, help=help_value)
    return config


def render_info_tab() -> None:
    st.caption(
        "Use this guide when you want the app to explain the workflow in plain English before you make modeling or budget decisions."
    )
    st.info(
        "Recommended path: validate the data first, start with OLS and Ridge, check holdout performance in Results, and only then use the AI write-up as a communication layer."
    )
    with st.expander("Glossary of MMM terms", expanded=True):
        st.markdown(
            """
            **Date grain**

            The time spacing of the data, such as daily or weekly. MMM works best when each row represents one clear time period.

            **Target**

            The outcome you want to explain, usually leads, conversions, or revenue.

            **Channel**

            A paid media variable such as TV, search, or social spend.

            **Control variable**

            A non-media factor that may move the target, such as seasonality, pricing, holidays, or promotions.

            **Transform**

            A mathematical reshaping of a channel before modeling. This is used because media effects are rarely perfectly linear.

            **Adstock**

            A carryover effect. It means some impact from earlier spend can continue into later periods.

            **Saturation**

            Diminishing returns. It means spend can keep helping, but each additional unit usually helps less than the last one.

            **Regularization**

            A stability penalty. It pulls unstable coefficients toward zero when channels move together and the model has trouble separating them.

            **Coefficient**

            The fitted weight for a variable inside the model. Bigger is not always better by itself because the underlying variable scales can differ.

            **Contribution**

            The modeled amount of the target assigned to a channel in the selected view.

            **Baseline**

            The non-media part of the model. This includes the intercept and any control-variable effect.

            **Unexplained gap**

            The part of the actual outcome that the displayed media-plus-baseline view still does not explain.

            **CPL**

            Cost per lead. Lower means better modeled efficiency in the current view.

            **Holdout**

            A later slice of the time series that is not used during fitting. It is used as a basic reality check on whether the model generalizes.

            **Residual**

            The difference between actual and predicted values for a period.

            **Prior**

            A Bayesian starting assumption used by `PyMC` before the data updates the estimate.
            """
        )

    st.subheader("What this app is doing")
    intro_col1, intro_col2 = st.columns(2)
    intro_col1.markdown(
        """
        **In plain English**

        This app tries to explain changes in leads using media spend and a few optional control variables.

        It does that in four layers:
        - clean the time series into one row per date
        - transform media so carryover and diminishing returns can be modeled more realistically
        - fit one or more statistical models
        - translate the fitted output into business-facing views for reading, comparison, and export
        """
    )
    intro_col2.markdown(
        """
        **Key ideas to keep in mind**

        - `Adstock` means some impact from earlier spend can show up later
        - `Saturation` means doubling spend does not usually double response forever
        - `Regularization` helps when similar channels move together and the model cannot separate them cleanly
        - `CPL` is a directional efficiency measure, not proof of causality
        - `AI analysis` is a draft explanation layer, not a replacement for model review
        """
    )

    st.subheader("Workflow guide")
    with st.expander("1. Data", expanded=True):
        st.markdown(
            """
            **What you do**

            Load a file, pick the date, target, channels, and controls, then validate it.

            **What good looks like**

            - one row per date after aggregation
            - no missing values in selected model columns
            - enough rows to support both fitting and holdout validation

            **Why this matters**

            Every later step depends on these selections. If the data definition changes, transforms, fits, and AI output can all become stale.
            """
        )
    with st.expander("2. Config"):
        st.markdown(
            """
            **What you do**

            Choose the media-shape assumptions before fitting.

            **How to think about it**

            - use `Geometric adstock` when a channel likely keeps working after the spend date
            - use `Log saturation` for a simple diminishing-returns curve
            - use `Hill saturation` when you want more control over where the curve bends
            - increase `regularization` when channels are highly correlated or coefficients swing too much

            **Translate the terms**

            `Theta` is the strength of carryover. Higher theta means the effect lingers longer.

            `Alpha` and `K` shape the Hill curve. Alpha changes how sharp the bend is. K is the spend level where the curve is around half of its maximum response.
            """
        )
    with st.expander("3. Priors"):
        st.markdown(
            """
            **What you do**

            Set Bayesian starting assumptions for `PyMC`.

            **Use this step when**

            - you want uncertainty ranges, not only point estimates
            - you have prior business beliefs you want the model to start from

            **Watch out for**

            Weak priors are not the same as no assumptions. PyMC is slower and can become unstable if the data is thin or the setup is too ambitious.

            **Translate the terms**

            `Sigma scale` means how wide or flexible a prior should be.

            `Draws` are the posterior samples you keep.

            `Tune` is the warm-up phase before sampling.

            `Chains` are independent runs of the sampler. More chains give a better convergence check.
            """
        )
    with st.expander("4. Fit"):
        st.markdown(
            """
            **What you do**

            Fit one or more models on the transformed dataset.

            **Best practice**

            Start with `OLS` and `Ridge` as a baseline pair. Add `Lasso` or `ElasticNet` when you want stronger shrinkage behavior. Use `PyMC` when you specifically need uncertainty ranges and are willing to check them carefully.

            **What "fit" means**

            Fitting means the model is estimating the relationship between the transformed inputs and the target using the loaded history.
            """
        )
    with st.expander("5. Results"):
        st.markdown(
            """
            **What you do**

            Review fit, validation, attribution, efficiency, and the action story.

            **Use Results in this order**

            - check model comparison and holdout diagnostics first
            - check actual vs predicted next
            - then read channel-level efficiency and contribution
            - only then move to recommendation language

            **Translate the terms**

            `In-sample` means measured on the same data used to fit the model.

            `Holdout` means measured on later data that was not used to fit the model.

            `Actual vs predicted` shows whether the model broadly tracks the shape and timing of the target over time.
            """
        )
    with st.expander("6. AI"):
        st.markdown(
            """
            **What you do**

            Generate a written interpretation of the current selected model and results view.

            **How to use it**

            Treat the AI section as a communication helper. It should summarize the evidence you already trust from the Results page, not replace that review.
            """
        )

    st.subheader("Choose the right model")
    with st.expander("OLS", expanded=True):
        st.markdown(
            """
            **What it is**

            A simple linear baseline on the transformed inputs.

            **Use it when**

            You want the fastest first read and an easy benchmark for the other models.

            **Strong point**

            Easy to explain.

            **Watch out for**

            It can become unstable when channels are highly correlated, which means they rise and fall together and the model struggles to separate them cleanly.
            """
        )
    with st.expander("Ridge", expanded=True):
        st.markdown(
            """
            **What it is**

            A linear model with `L2` shrinkage. In plain English, that means it gently pulls coefficients toward zero to reduce instability.

            **Use it when**

            Multiple channels move together and you need a more stable baseline than OLS.

            **Strong point**

            Usually the safest first production-style comparison in this app.

            **Watch out for**

            Fit is still regression-based and should still be checked against holdout results.
            """
        )
    with st.expander("Lasso"):
        st.markdown(
            """
            **What it is**

            A linear model with `L1` shrinkage. In plain English, that means it can push weak coefficients all the way to zero.

            **Use it when**

            You want weak channels to be pushed down aggressively.

            **Strong point**

            Can simplify a noisy media mix.

            **Watch out for**

            It may zero channels too hard when the signal is weak or features are highly correlated.
            """
        )
    with st.expander("ElasticNet"):
        st.markdown(
            """
            **What it is**

            A blend of Ridge and Lasso penalties. It combines gentle shrinkage with the ability to zero out some weaker effects.

            **Use it when**

            You want a middle ground between stability and sparsity.

            **Strong point**

            Flexible when you are not sure whether Ridge or Lasso behavior is more appropriate.

            **Watch out for**

            It needs more tuning and interpretation than a simple OLS or Ridge baseline.
            """
        )
    with st.expander("PyMC"):
        st.markdown(
            """
            **What it is**

            A Bayesian regression that adds priors and interval outputs.

            **Use it when**

            You want uncertainty ranges and want to make the modeling assumptions more explicit.

            **Strong point**

            Gives a richer uncertainty story than point-estimate models.

            **Watch out for**

            Slower runtime does not automatically mean better evidence. Always check whether the output is stable enough to trust.

            **Translate the terms**

            `Bayesian` means the model starts with prior assumptions and then updates them with data.

            `Interval outputs` mean ranges of plausible values, not single-number certainty.
            """
        )

    st.subheader("Choose transforms with intent")
    transform_col1, transform_col2 = st.columns(2)
    transform_col1.markdown(
        """
        **Adstock**

        Use `Geometric` when a channel likely keeps working after the spend lands.

        - lower `theta` means fast fade
        - higher `theta` means longer carryover
        - use `None` when the effect is expected to be mostly same-period
        """
    )
    transform_col2.markdown(
        """
        **Saturation**

        Use saturation when doubling spend should not double response forever.

        - `Log` is the simpler default
        - `Hill` is more configurable
        - `None` is a useful stress test, not usually the final choice
        """
    )
    st.markdown(
        """
        **A practical rule**

        If you are unsure, start with geometric adstock plus log saturation for all channels, fit once, and only then tune the channels where the business story or diagnostics suggest a change.
        """
    )

    st.subheader("How to read the outputs")
    with st.expander("Model comparison", expanded=True):
        st.markdown(
            """
            Start here. Compare in-sample fit, then prefer the holdout metrics when they are available.

            A model with a better story but weak holdout behavior should be treated as directional only.

            `R²` tells you how much movement the model explains.

            `RMSE` tells you the average size of the prediction error in the target's units.

            `MAPE` tells you the average percentage error on non-zero rows.
            """
        )
    with st.expander("Actual vs predicted"):
        st.markdown(
            """
            This is your quick sanity check.

            You are looking for whether the model broadly tracks the timing and direction of movement in the target, not whether it matches every point perfectly.
            """
        )
    with st.expander("Media, baseline, and unexplained gap"):
        st.markdown(
            """
            Use this to explain the result in business language.

            - `Media leads` is the displayed portion linked to channels
            - `Baseline leads` is the non-media part
            - `Unexplained gap` is what the displayed split still does not account for

            A large unexplained gap means you should be more cautious with channel-level decisions.
            """
        )
    with st.expander("Spend share vs contribution share"):
        st.markdown(
            """
            This helps compare budget weight with modeled value.

            Channels contributing more than their spend share may deserve more attention. Channels far below their spend share deserve scrutiny, not an automatic cut.
            """
        )
    with st.expander("CPL and channel ranking"):
        st.markdown(
            """
            Lower CPL means better modeled efficiency in the current view.

            Use CPL comparatively across channels. Do not treat one CPL number as universal truth, especially when carryover or limited validation makes the evidence weaker.
            """
        )
    with st.expander("AI analysis"):
        st.markdown(
            """
            Use the AI output as a writing assistant for the current evidence.

            If the Results view changes, regenerate the AI analysis before exporting or sharing it.
            """
        )

    st.warning(
        "Statistical trust note: the business-facing decomposition is designed for interpretation and communication. It is not a pure causal estimate, and strong recommendations should be backed by holdout behavior, domain knowledge, and, when possible, budget tests."
    )
