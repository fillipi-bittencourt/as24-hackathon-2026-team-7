from __future__ import annotations

import dataclasses
import unittest
from pathlib import Path

import numpy as np
import pandas as pd

from app import compute_holdout_diagnostics, format_saved_session_label
from src.ai.client import _pick_channel_name, build_payload, validate_analysis_text
from src.app_state import STATE_DEFAULTS
from src.models.elasticnet import ElasticNetModel
from src.models.lasso import LassoModel
from src.models.ols import OLSModel
from src.models.pymc_model import PyMCModel
from src.models.ridge import RidgeModel
from src.results_helpers import format_cpl, is_rankable_cpl, pick_best_channel, pick_worst_channel
from src.results_helpers import (
    aggregate_time_series_df,
    get_default_time_granularity,
    get_time_granularity_options,
    infer_granularity_scale_factor,
)
from src.session_persistence import _serialize_value
from src.setup_assistant import _resolve_hybrid_column_selection, _sanitize_channel_prior_family
from src.transforms import transform_media
from src.utils import convert_mmm_data, validate_mmm_data


SAMPLE_PATH = Path(__file__).resolve().parents[1] / "data" / "mmm_demo_sample.csv"


def load_prepared_dataset(
    *,
    channel_cols: list[str],
    control_cols: list[str] | None = None,
    extra_df: pd.DataFrame | None = None,
) -> tuple[pd.DataFrame, list[str]]:
    df = pd.read_csv(SAMPLE_PATH) if extra_df is None else extra_df.copy()
    converted, _ = convert_mmm_data(
        df,
        "date",
        "target",
        channel_cols,
        control_cols or [],
    )
    ok, errors, warnings = validate_mmm_data(
        converted,
        "date",
        "target",
        channel_cols,
        control_cols or [],
    )
    if not ok:
        raise AssertionError(errors)
    prepared = converted.sort_values("date").reset_index(drop=True)
    return prepared, warnings


def build_transformed_inputs(
    df: pd.DataFrame,
    *,
    channel_cols: list[str],
    control_cols: list[str] | None = None,
) -> tuple[np.ndarray, np.ndarray, dict[str, np.ndarray], dict[str, str]]:
    adstock_type = {ch: "geometric" for ch in channel_cols}
    saturation_type = {ch: "log" for ch in channel_cols}
    adstock_params = {ch: 0.3 for ch in channel_cols}
    saturation_params = {ch: {"alpha": 1.0, "k": 0.0} for ch in channel_cols}
    X = transform_media(
        df,
        channel_cols,
        adstock_params,
        saturation_params,
        adstock_type=adstock_type,
        saturation_type=saturation_type,
        control_cols=control_cols or [],
    )
    y = df["target"].to_numpy(dtype=np.float64)
    raw_spend = {
        ch: df[ch].to_numpy(dtype=np.float64)
        for ch in channel_cols
    }
    return X, y, raw_spend, adstock_type


class ModelSmokeTests(unittest.TestCase):
    def test_session_serializer_accepts_model_result_like_dataclass(self) -> None:
        @dataclasses.dataclass
        class ReloadedModelResult:
            model_name: str
            channel_names: list[str]
            coefficients: dict[str, float]
            intercept: float
            cpl: dict[str, float]
            contribution: dict[str, np.ndarray]
            contribution_pct: dict[str, float]
            y_pred: np.ndarray
            baseline: np.ndarray
            baseline_pct: float
            r_squared: float
            rmse: float
            coefficient_lower: dict[str, float] | None = None
            coefficient_upper: dict[str, float] | None = None
            cpl_lower: dict[str, float] | None = None
            cpl_upper: dict[str, float] | None = None

        model_result = ReloadedModelResult(
            model_name="OLS",
            channel_names=["tv_spend"],
            coefficients={"tv_spend": 1.23},
            intercept=4.56,
            cpl={"tv_spend": 12.34},
            contribution={"tv_spend": np.asarray([1.0, 2.0], dtype=np.float64)},
            contribution_pct={"tv_spend": 0.5},
            y_pred=np.asarray([5.0, 6.0], dtype=np.float64),
            baseline=np.asarray([4.0, 4.0], dtype=np.float64),
            baseline_pct=0.5,
            r_squared=0.8,
            rmse=1.2,
        )

        serialized = _serialize_value(model_result)

        self.assertEqual(serialized["__type__"], "model_result")
        self.assertEqual(serialized["value"]["model_name"], "OLS")
        self.assertEqual(serialized["value"]["channel_names"], ["tv_spend"])

    def test_channel_prior_family_stays_business_safe(self) -> None:
        self.assertEqual(_sanitize_channel_prior_family("HalfNormal"), "HalfNormal")
        self.assertEqual(_sanitize_channel_prior_family("Normal"), "HalfNormal")
        self.assertEqual(_sanitize_channel_prior_family("anything_else"), "HalfNormal")

    def test_negative_cpl_is_not_rankable(self) -> None:
        cpl_map = {
            "negative_channel": -12.5,
            "good_channel": 15.0,
            "bad_channel": 40.0,
            "na_channel": float("inf"),
        }
        self.assertFalse(is_rankable_cpl(-12.5))
        self.assertEqual(format_cpl(-12.5), "N/A")
        self.assertEqual(pick_best_channel(cpl_map), ("good_channel", 15.0))
        self.assertEqual(pick_worst_channel(cpl_map), ("bad_channel", 40.0))
        self.assertEqual(_pick_channel_name(cpl_map, best=True), "good_channel")
        self.assertEqual(_pick_channel_name(cpl_map, best=False), "bad_channel")

    def test_duplicate_session_labels_include_slug(self) -> None:
        duplicate_labels = {
            "collision test | 2026-03-12T19:22:28 | demo.csv | no fitted models": 2,
        }
        session_info = {
            "slug": "collision_test_2",
            "display_name": "collision test",
            "saved_at": "2026-03-12T19:22:28",
            "source": "demo.csv",
            "models": "no fitted models",
        }
        label = format_saved_session_label(session_info, duplicate_labels)
        self.assertIn("collision_test_2", label)

    def test_daily_series_defaults_to_weekly_visual_granularity(self) -> None:
        date_series = pd.Series(pd.date_range("2024-01-01", periods=30, freq="D"))
        self.assertEqual(get_time_granularity_options(date_series), ["Daily", "Weekly", "Monthly"])
        self.assertEqual(get_default_time_granularity(date_series), "Weekly")
        self.assertGreaterEqual(infer_granularity_scale_factor(date_series, "Weekly"), 7.0)

    def test_aggregate_time_series_df_groups_daily_rows_to_weekly(self) -> None:
        df = pd.DataFrame(
            {
                "date": pd.date_range("2024-01-01", periods=14, freq="D"),
                "actual": np.arange(14, dtype=float),
                "predicted": np.arange(14, dtype=float) * 2.0,
            }
        )
        grouped = aggregate_time_series_df(
            df,
            date_col="date",
            value_columns=["actual", "predicted"],
            granularity="Weekly",
        )
        self.assertEqual(len(grouped), 2)
        self.assertAlmostEqual(float(grouped["actual"].sum()), float(df["actual"].sum()))
        self.assertAlmostEqual(float(grouped["predicted"].sum()), float(df["predicted"].sum()))

    def test_duplicate_date_aggregation_sums_channels_and_averages_controls(self) -> None:
        df = pd.DataFrame(
            {
                "date": ["2024-01-01", "2024-01-01", "2024-01-08"],
                "target": [100.0, 120.0, 150.0],
                "tv_spend": [10.0, 15.0, 20.0],
                "seasonality_index": [1.0, 3.0, 2.0],
                "note": ["first", "second", "third"],
            }
        )
        converted, aggregated_rows = convert_mmm_data(
            df,
            "date",
            "target",
            ["tv_spend"],
            ["seasonality_index"],
        )
        self.assertEqual(aggregated_rows, 1)
        prepared = converted.sort_values("date").reset_index(drop=True)
        self.assertEqual(len(prepared), 2)
        self.assertEqual(float(prepared.loc[0, "target"]), 220.0)
        self.assertEqual(float(prepared.loc[0, "tv_spend"]), 25.0)
        self.assertEqual(float(prepared.loc[0, "seasonality_index"]), 2.0)
        self.assertEqual(str(prepared.loc[0, "note"]), "first")

    def test_media_is_non_negative_while_control_can_be_negative(self) -> None:
        rng = np.random.default_rng(42)
        n_rows = 60
        control_values = np.linspace(0.0, 1.0, n_rows)
        media_values = rng.uniform(0.0, 10.0, size=n_rows)
        target_values = 200.0 - (50.0 * control_values) + rng.normal(0.0, 0.5, size=n_rows)
        df = pd.DataFrame(
            {
                "date": pd.date_range("2024-01-01", periods=n_rows, freq="W-MON"),
                "target": target_values,
                "tv_spend": media_values,
                "seasonality_index": control_values,
            }
        )
        prepared, warnings = load_prepared_dataset(
            channel_cols=["tv_spend"],
            control_cols=["seasonality_index"],
            extra_df=df,
        )
        self.assertEqual(warnings, [])
        X, y, raw_spend, _ = build_transformed_inputs(
            prepared,
            channel_cols=["tv_spend"],
            control_cols=["seasonality_index"],
        )

        builders = {
            "OLS": (OLSModel, {}),
            "Ridge": (RidgeModel, {"reg_alpha": 0.1}),
            "Lasso": (LassoModel, {"reg_alpha": 0.01}),
            "ElasticNet": (ElasticNetModel, {"reg_alpha": 0.01, "l1_ratio": 0.5}),
        }
        for model_name, (builder, extra_kwargs) in builders.items():
            with self.subTest(model=model_name):
                model = builder()
                model.fit(
                    X,
                    y,
                    raw_spend=raw_spend,
                    channel_names=["tv_spend"],
                    control_names=["seasonality_index"],
                    **extra_kwargs,
                )
                self.assertIsNotNone(model._coefficients)
                assert model._coefficients is not None
                self.assertGreaterEqual(float(model._coefficients[0]), -1e-9)
                self.assertLess(float(model._coefficients[1]), 0.0)

    def test_frequentist_models_fit_sample_data(self) -> None:
        channel_cols = ["tv_spend", "digital_spend", "search_spend", "social_spend"]
        prepared, warnings = load_prepared_dataset(channel_cols=channel_cols)
        self.assertEqual(warnings, [])
        X, y, raw_spend, _ = build_transformed_inputs(prepared, channel_cols=channel_cols)

        builders = {
            "OLS": (OLSModel, {}),
            "Ridge": (RidgeModel, {"reg_alpha": 1.0}),
            "Lasso": (LassoModel, {"reg_alpha": 0.1}),
            "ElasticNet": (ElasticNetModel, {"reg_alpha": 0.1, "l1_ratio": 0.5}),
        }
        for model_name, (builder, extra_kwargs) in builders.items():
            with self.subTest(model=model_name):
                model = builder()
                kwargs = {
                    "channel_names": channel_cols,
                    "control_names": [],
                    **extra_kwargs,
                }
                result = model.fit(X, y, raw_spend=raw_spend, **kwargs)
                pred = model.predict(X)
                self.assertEqual(result.model_name, model_name)
                self.assertEqual(result.y_pred.shape, y.shape)
                self.assertEqual(result.baseline.shape, y.shape)
                self.assertEqual(pred.shape, y.shape)
                self.assertTrue(np.isfinite(result.y_pred).all())
                self.assertTrue(np.isfinite(result.baseline).all())
                self.assertTrue(np.isfinite(result.r_squared))
                self.assertTrue(np.isfinite(result.rmse))
                self.assertTrue(all(float(result.coefficients[ch]) >= -1e-9 for ch in channel_cols))
                holdout = compute_holdout_diagnostics(
                    builder=builder,
                    X=X,
                    y=y,
                    raw_spend=raw_spend,
                    model_kwargs=kwargs,
                    date_values=prepared["date"],
                )
                self.assertIsNotNone(holdout)
                assert holdout is not None
                self.assertGreater(holdout["holdout_rows"], 0)
                self.assertTrue(np.isfinite(holdout["holdout_rmse"]))

    def test_single_channel_plus_control_path(self) -> None:
        df = pd.read_csv(SAMPLE_PATH)
        df["seasonality_index"] = np.linspace(0.8, 1.2, len(df))
        channel_cols = ["tv_spend"]
        control_cols = ["seasonality_index"]
        prepared, warnings = load_prepared_dataset(
            channel_cols=channel_cols,
            control_cols=control_cols,
            extra_df=df,
        )
        self.assertEqual(warnings, [])
        X, y, raw_spend, _ = build_transformed_inputs(
            prepared,
            channel_cols=channel_cols,
            control_cols=control_cols,
        )
        self.assertEqual(X.shape[1], 2)

        builders = {
            "OLS": (OLSModel, {}),
            "Ridge": (RidgeModel, {"reg_alpha": 1.0}),
            "Lasso": (LassoModel, {"reg_alpha": 0.1}),
            "ElasticNet": (ElasticNetModel, {"reg_alpha": 0.1, "l1_ratio": 0.5}),
        }
        for model_name, (builder, extra_kwargs) in builders.items():
            with self.subTest(model=model_name):
                model = builder()
                result = model.fit(
                    X,
                    y,
                    raw_spend=raw_spend,
                    channel_names=channel_cols,
                    control_names=control_cols,
                    **extra_kwargs,
                )
                self.assertEqual(result.y_pred.shape, y.shape)
                self.assertEqual(result.baseline.shape, y.shape)
                self.assertTrue(np.isfinite(result.y_pred).all())
                self.assertTrue(np.isfinite(result.baseline).all())

    def test_zero_variance_channel_warns_and_payload_builds(self) -> None:
        df = pd.read_csv(SAMPLE_PATH)
        df["dead_spend"] = 0.0
        channel_cols = ["tv_spend", "dead_spend"]
        prepared, warnings = load_prepared_dataset(
            channel_cols=channel_cols,
            extra_df=df,
        )
        self.assertTrue(any("dead_spend" in warning for warning in warnings))
        X, y, raw_spend, adstock_type = build_transformed_inputs(
            prepared,
            channel_cols=channel_cols,
        )

        model = OLSModel()
        result = model.fit(
            X,
            y,
            raw_spend=raw_spend,
            channel_names=channel_cols,
            control_names=[],
        )
        payload = build_payload(
            result,
            {
                "df": prepared,
                "date_col": "date",
                "target_col": "target",
                "control_cols": [],
                "model_results": {"OLS": result},
                "model_results_meta": {"OLS": {}},
                "y": y,
                "selected_visual_channels": ["tv_spend"],
                "results_period": "Last 8 weeks",
                "adstock_type": adstock_type,
                "pymc_sampler_config": {"draws": 300, "tune": 200, "chains": 2},
            },
            include_comparison=False,
        )
        self.assertIn("residual_gap_total_leads", payload)
        self.assertIn("baseline_contribution_total_leads", payload)
        self.assertIn("residual_gap_share_of_actual_pct", payload)
        self.assertIn("hidden_media_total_leads", payload)
        self.assertEqual(len(payload["channels"]), 1)

    def test_ai_analysis_validator_flags_wrong_top_channel_claim(self) -> None:
        channel_cols = ["tv_spend", "digital_spend", "search_spend", "social_spend"]
        prepared, warnings = load_prepared_dataset(channel_cols=channel_cols)
        self.assertEqual(warnings, [])
        X, y, raw_spend, adstock_type = build_transformed_inputs(prepared, channel_cols=channel_cols)

        model = OLSModel()
        result = model.fit(
            X,
            y,
            raw_spend=raw_spend,
            channel_names=channel_cols,
            control_names=[],
        )
        holdout = compute_holdout_diagnostics(
            builder=OLSModel,
            X=X,
            y=y,
            raw_spend=raw_spend,
            model_kwargs={"channel_names": channel_cols, "control_names": []},
            date_values=prepared["date"],
        )
        payload = build_payload(
            result,
            {
                "df": prepared,
                "date_col": "date",
                "target_col": "target",
                "control_cols": [],
                "model_results": {"OLS": result},
                "model_results_meta": {"OLS": {"holdout": holdout}},
                "y": y,
                "selected_visual_channels": channel_cols,
                "results_period": "All data",
                "adstock_type": adstock_type,
                "pymc_sampler_config": {"draws": 300, "tune": 200, "chains": 2},
            },
            include_comparison=False,
        )
        text = """
1. Executive summary

The model's in-sample fit shows an R-squared of 0.36, with a root mean square error (RMSE) of 82.2.
Digital Spend is most efficient with a CPL of 8.82, contributing 95.78% to total leads.
Holdout validation reveals a declining R-squared of -0.15, indicating model instability.

2. Statistical rigor check

With 52 weeks of data, sample size is adequate, but in-sample fit quality is modest at an R-squared of 0.36.

3. Channel diagnosis

Digital Spend is the strongest performer with a CPL of 8.82 and a contribution of 95.78%.
TV Spend is the weakest, with a CPL of 19.73.

4. Cross-model consistency

Not applicable as no comparison_table is provided for cross-model analysis.

5. Action plan

30-day plan: Conduct small-scale tests reallocating budget from TV to Digital and Social.
60-day plan: Consider a slightly larger budget shift favoring Digital and Social.

6. Risks and assumptions

The largest risk is model overfitting indicated by poor holdout performance.
""".strip()
        validation = validate_analysis_text(text, payload, detailed=True)
        self.assertEqual(validation["status"], "failed")
        issue_codes = {issue["code"] for issue in validation["issues"]}
        self.assertIn("top_channel_claim", issue_codes)
        self.assertIn("unexpected_cross_model_section", issue_codes)

    def test_ai_analysis_validator_accepts_well_formed_response(self) -> None:
        channel_cols = ["tv_spend", "digital_spend", "search_spend", "social_spend"]
        prepared, warnings = load_prepared_dataset(channel_cols=channel_cols)
        self.assertEqual(warnings, [])
        X, y, raw_spend, adstock_type = build_transformed_inputs(prepared, channel_cols=channel_cols)

        model = OLSModel()
        result = model.fit(
            X,
            y,
            raw_spend=raw_spend,
            channel_names=channel_cols,
            control_names=[],
        )
        holdout = compute_holdout_diagnostics(
            builder=OLSModel,
            X=X,
            y=y,
            raw_spend=raw_spend,
            model_kwargs={"channel_names": channel_cols, "control_names": []},
            date_values=prepared["date"],
        )
        payload = build_payload(
            result,
            {
                "df": prepared,
                "date_col": "date",
                "target_col": "target",
                "control_cols": [],
                "model_results": {"OLS": result},
                "model_results_meta": {"OLS": {"holdout": holdout}},
                "y": y,
                "selected_visual_channels": channel_cols,
                "results_period": "All data",
                "adstock_type": adstock_type,
                "pymc_sampler_config": {"draws": 300, "tune": 200, "chains": 2},
            },
            include_comparison=False,
        )
        text = """
1. Executive summary
- OLS explains 0.36 of in-sample variation with an RMSE of 82.2.
- Social Spend has the best CPL at 11.86, while TV Spend is weakest at 59.44.
- Holdout R-squared is -0.15, so the output is only suitable for cautious budget testing.

2. Statistical rigor check
The holdout R-squared is -0.15 even though in-sample R-squared is 0.36, so this model is only suitable for budget testing. The unexplained gap is 0.0 and the methodology notes say the decomposition is bounded for business readability.

3. Channel diagnosis
Social Spend is the strongest channel with a CPL of 11.86, and TV Spend is the weakest with a CPL of 59.44. Digital Spend contributes 31.8% of actual leads, but the holdout R-squared of -0.15 means the mix should still be treated directionally.

5. Action plan
30-day plan: run small budget tests because holdout R-squared is -0.15 and Social Spend currently shows a CPL of 11.86.
60-day plan: only expand beyond pilot reallocations if TV Spend remains at 59.44 CPL and the 11.86 Social Spend signal still holds in refreshed validation.

6. Risks and assumptions
The biggest risks are weak holdout performance at -0.15 R-squared and the fact that the bounded decomposition is designed for business readability rather than pure causal interpretation.
""".strip()
        validation = validate_analysis_text(text, payload, detailed=True)
        self.assertEqual(validation["status"], "passed")
        self.assertEqual(validation["issues"], [])

    def test_ai_payload_uses_non_negative_business_facing_decomposition(self) -> None:
        channel_cols = ["tv_spend", "digital_spend", "search_spend", "social_spend"]
        prepared, warnings = load_prepared_dataset(channel_cols=channel_cols)
        self.assertEqual(warnings, [])
        X, y, raw_spend, adstock_type = build_transformed_inputs(prepared, channel_cols=channel_cols)

        model = OLSModel()
        result = model.fit(
            X,
            y,
            raw_spend=raw_spend,
            channel_names=channel_cols,
            control_names=[],
        )
        payload = build_payload(
            result,
            {
                "df": prepared,
                "date_col": "date",
                "target_col": "target",
                "control_cols": [],
                "model_results": {"OLS": result},
                "model_results_meta": {"OLS": {}},
                "y": y,
                "selected_visual_channels": channel_cols,
                "results_period": "All data",
                "adstock_type": adstock_type,
                "pymc_sampler_config": {"draws": 300, "tune": 200, "chains": 2},
            },
            include_comparison=False,
        )
        self.assertGreaterEqual(float(payload["baseline_contribution_total_leads"]), 0.0)
        self.assertGreaterEqual(float(payload["residual_gap_total_leads"]), 0.0)
        bounded_total = float(payload["baseline_contribution_total_leads"]) + float(payload["residual_gap_total_leads"])
        bounded_total += sum(float(channel["contribution_total"]) for channel in payload["channels"])
        self.assertAlmostEqual(bounded_total, float(payload["actual_total_leads"]), places=2)

    def test_hybrid_selection_keeps_patchy_and_healthy_channels(self) -> None:
        n_rows = 20
        df = pd.DataFrame(
            {
                "date": pd.date_range("2024-01-01", periods=n_rows, freq="W-MON"),
                "target": np.linspace(100.0, 140.0, n_rows),
                "healthy_spend": [10.0] * 14 + [0.0] * 6,
                "patchy_spend": [20.0] * 8 + [0.0] * 12,
                "sparse_spend": [30.0] * 3 + [0.0] * 17,
            }
        )
        selection = _resolve_hybrid_column_selection(
            raw_df=df,
            date_col="date",
            target_col="target",
            current_channels=["healthy_spend", "patchy_spend", "sparse_spend"],
            current_controls=[],
            suggested_channels=["healthy_spend"],
            suggested_controls=[],
        )
        self.assertEqual(selection["candidate_profiles"]["healthy_spend"]["coverage_tag"], "healthy")
        self.assertEqual(selection["candidate_profiles"]["patchy_spend"]["coverage_tag"], "patchy")
        self.assertEqual(selection["candidate_profiles"]["sparse_spend"]["coverage_tag"], "sparse")
        self.assertEqual(
            selection["applied_channels"],
            ["healthy_spend", "patchy_spend"],
        )
        self.assertIn("patchy_spend", selection["force_kept_channels"])
        self.assertIn("sparse_spend", selection["sparse_excluded_channels"])

    def test_hybrid_selection_applies_rule_to_controls_too(self) -> None:
        n_rows = 20
        df = pd.DataFrame(
            {
                "date": pd.date_range("2024-01-01", periods=n_rows, freq="W-MON"),
                "target": np.linspace(200.0, 260.0, n_rows),
                "healthy_spend": [15.0] * 14 + [0.0] * 6,
                "seasonality_index": [1.0] * 12 + [0.0] * 8,
                "promo_flag": [1.0] * 6 + [0.0] * 14,
                "tiny_control": [1.0] * 2 + [0.0] * 18,
            }
        )
        selection = _resolve_hybrid_column_selection(
            raw_df=df,
            date_col="date",
            target_col="target",
            current_channels=["healthy_spend"],
            current_controls=["seasonality_index", "tiny_control"],
            suggested_channels=["healthy_spend"],
            suggested_controls=["promo_flag", "tiny_control"],
        )
        self.assertEqual(selection["candidate_profiles"]["seasonality_index"]["coverage_tag"], "healthy")
        self.assertEqual(selection["candidate_profiles"]["promo_flag"]["coverage_tag"], "patchy")
        self.assertEqual(selection["candidate_profiles"]["tiny_control"]["coverage_tag"], "sparse")
        self.assertEqual(
            selection["applied_controls"],
            ["promo_flag", "seasonality_index"],
        )
        self.assertIn("seasonality_index", selection["force_kept_controls"])
        self.assertIn("promo_flag", selection["ai_ranked_controls"])
        self.assertIn("tiny_control", selection["sparse_excluded_controls"])

    def test_pymc_smoke_on_sample_data(self) -> None:
        if not importlib_available("pymc"):
            self.skipTest("PyMC is not installed")
        channel_cols = ["tv_spend", "digital_spend", "search_spend", "social_spend"]
        prepared, warnings = load_prepared_dataset(channel_cols=channel_cols)
        self.assertEqual(warnings, [])
        X, y, raw_spend, _ = build_transformed_inputs(prepared, channel_cols=channel_cols)
        sampler_config = dict(STATE_DEFAULTS["pymc_sampler_config"])

        model = PyMCModel()
        result = model.fit(
            X,
            y,
            raw_spend=raw_spend,
            channel_names=channel_cols,
            control_names=[],
            prior_config={
                "intercept_mu_mode": "data_mean",
                "intercept_mu": 0.0,
                "intercept_sigma_scale": 1.0,
                "channel_prior_family": "HalfNormal",
                "channel_sigma_scale": 1.0,
                "control_sigma_scale": 1.0,
                "noise_sigma_scale": 1.0,
                "channel_prior_overrides": {},
            },
            sampler_config=sampler_config,
        )
        diagnostics = model.get_diagnostics()
        self.assertEqual(result.model_name, "PyMC")
        self.assertEqual(result.y_pred.shape, y.shape)
        self.assertEqual(result.baseline.shape, y.shape)
        self.assertTrue(np.isfinite(result.y_pred).all())
        self.assertTrue(np.isfinite(result.baseline).all())
        self.assertTrue(np.isfinite(result.r_squared))
        self.assertTrue(np.isfinite(result.rmse))
        self.assertIsNotNone(diagnostics)
        if result.coefficient_lower is not None:
            for channel in channel_cols:
                self.assertLessEqual(result.coefficient_lower[channel], result.coefficients[channel])
                self.assertLessEqual(result.coefficients[channel], result.coefficient_upper[channel])
                self.assertLessEqual(result.cpl_lower[channel], result.cpl_upper[channel])


def importlib_available(module_name: str) -> bool:
    try:
        __import__(module_name)
    except Exception:
        return False
    return True


if __name__ == "__main__":
    unittest.main()
