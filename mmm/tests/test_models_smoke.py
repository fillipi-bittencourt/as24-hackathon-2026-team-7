from __future__ import annotations

import unittest
from pathlib import Path

import numpy as np
import pandas as pd

from app import compute_holdout_diagnostics
from src.ai.client import build_payload
from src.app_state import STATE_DEFAULTS
from src.models.elasticnet import ElasticNetModel
from src.models.lasso import LassoModel
from src.models.ols import OLSModel
from src.models.pymc_model import PyMCModel
from src.models.ridge import RidgeModel
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


def importlib_available(module_name: str) -> bool:
    try:
        __import__(module_name)
    except Exception:
        return False
    return True


if __name__ == "__main__":
    unittest.main()
