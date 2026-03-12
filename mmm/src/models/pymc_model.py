from __future__ import annotations

import numpy as np

from .base import ModelResult


class PyMCModel:
    def __init__(self) -> None:
        self._trace = None
        self._posterior_means: dict[str, np.ndarray | float] | None = None

    def fit(
        self,
        X: np.ndarray,
        y: np.ndarray,
        raw_spend: dict[str, np.ndarray],
        **kwargs,
    ) -> ModelResult:
        try:
            import pymc as pm
        except ImportError as exc:
            raise ValueError("PyMC is not installed in this environment") from exc

        channel_names: list[str] = kwargs["channel_names"]
        n_channels = len(channel_names)
        X_values = np.asarray(X, dtype=np.float64)
        y_values = np.asarray(y, dtype=np.float64)
        n_controls = max(0, X_values.shape[1] - n_channels)

        prior_config = kwargs.get("prior_config", {})
        sampler_config = kwargs.get("sampler_config", {})

        y_std = float(np.std(y_values)) or 1.0
        intercept_mu = (
            float(np.mean(y_values))
            if prior_config.get("intercept_mu_mode", "data_mean") == "data_mean"
            else float(prior_config.get("intercept_mu", float(np.mean(y_values))))
        )
        intercept_sigma = max(
            1e-6, y_std * float(prior_config.get("intercept_sigma_scale", 1.0))
        )
        channel_sigma = max(
            1e-6, y_std * float(prior_config.get("channel_sigma_scale", 1.0))
        )
        control_sigma = max(
            1e-6, y_std * float(prior_config.get("control_sigma_scale", 1.0))
        )
        noise_sigma = max(
            1e-6, y_std * float(prior_config.get("noise_sigma_scale", 1.0))
        )
        channel_prior_family = str(
            prior_config.get("channel_prior_family", "HalfNormal")
        )
        channel_prior_overrides = prior_config.get("channel_prior_overrides", {})

        draws = int(sampler_config.get("draws", 300))
        tune = int(sampler_config.get("tune", 200))
        chains = int(sampler_config.get("chains", 1))

        with pm.Model() as model:
            intercept = pm.Normal(
                "intercept",
                mu=intercept_mu,
                sigma=intercept_sigma,
            )

            channel_coef_nodes = []
            for idx, channel_name in enumerate(channel_names):
                channel_override = channel_prior_overrides.get(channel_name, {})
                family = str(channel_override.get("family", channel_prior_family))
                sigma_value = max(
                    1e-6,
                    y_std
                    * float(
                        channel_override.get(
                            "sigma_scale",
                            prior_config.get("channel_sigma_scale", 1.0),
                        )
                    ),
                )
                variable_name = f"channel_coef_{idx}"
                if family == "Normal":
                    channel_coef_nodes.append(
                        pm.Normal(
                            variable_name,
                            mu=0.0,
                            sigma=sigma_value,
                        )
                    )
                else:
                    channel_coef_nodes.append(
                        pm.HalfNormal(
                            variable_name,
                            sigma=sigma_value,
                        )
                    )
            channel_coefs = pm.math.stack(channel_coef_nodes)

            if n_controls > 0:
                control_coefs = pm.Normal(
                    "control_coefs",
                    mu=0.0,
                    sigma=control_sigma,
                    shape=n_controls,
                )
                coef_vector = pm.math.concatenate([channel_coefs, control_coefs])
            else:
                control_coefs = None
                coef_vector = channel_coefs

            sigma = pm.HalfNormal("sigma", sigma=noise_sigma)
            mu = intercept + pm.math.dot(X_values, coef_vector)

            pm.Normal("observed_y", mu=mu, sigma=sigma, observed=y_values)
            self._trace = pm.sample(
                draws=draws,
                chains=chains,
                tune=tune,
                progressbar=False,
                return_inferencedata=True,
                random_seed=42,
            )

        posterior = self._trace.posterior
        intercept_mean = float(posterior["intercept"].mean().item())
        channel_means = np.asarray(
            [
                float(posterior[f"channel_coef_{idx}"].mean().item())
                for idx in range(n_channels)
            ],
            dtype=np.float64,
        )

        if n_controls > 0:
            control_means = (
                posterior["control_coefs"].mean(dim=("chain", "draw")).values.astype(np.float64)
            )
            coef_means = np.concatenate([channel_means, control_means])
        else:
            coef_means = channel_means

        self._posterior_means = {
            "intercept": intercept_mean,
            "coef_means": coef_means,
        }

        y_pred = intercept_mean + X_values @ coef_means
        ss_res = float(np.sum((y_values - y_pred) ** 2))
        ss_tot = float(np.sum((y_values - np.mean(y_values)) ** 2)) or 1.0
        r_squared = 1 - (ss_res / ss_tot)
        rmse = float(np.sqrt(np.mean((y_values - y_pred) ** 2)))
        coefficients = {
            channel_names[idx]: float(channel_means[idx]) for idx in range(n_channels)
        }
        contribution = {
            ch: coefficients[ch] * X_values[:, idx] for idx, ch in enumerate(channel_names)
        }
        cpl = {}
        for ch in channel_names:
            attr_leads = float(contribution[ch].sum())
            raw_total = float(np.asarray(raw_spend[ch], dtype=np.float64).sum())
            cpl[ch] = raw_total / attr_leads if attr_leads > 0 else float("inf")

        y_pred_total = float(np.sum(y_pred)) or 1.0
        contribution_pct = {
            ch: float(contribution[ch].sum()) / y_pred_total for ch in channel_names
        }
        baseline = y_pred.copy()
        for ch in channel_names:
            baseline = baseline - contribution[ch]
        baseline = np.clip(baseline, 0, None)
        baseline_pct = float(np.sum(baseline)) / y_pred_total

        channel_draws = np.asarray(
            [
                posterior[f"channel_coef_{idx}"].stack(sample=("chain", "draw")).values
                for idx in range(n_channels)
            ],
            dtype=np.float64,
        )
        coefficient_lower = {
            channel_names[idx]: float(np.percentile(channel_draws[idx], 3.0))
            for idx in range(n_channels)
        }
        coefficient_upper = {
            channel_names[idx]: float(np.percentile(channel_draws[idx], 97.0))
            for idx in range(n_channels)
        }

        cpl_lower: dict[str, float] = {}
        cpl_upper: dict[str, float] = {}
        for idx, ch in enumerate(channel_names):
            attr_draws = channel_draws[idx, :] * np.sum(X_values[:, idx])
            valid = attr_draws > 0
            if np.any(valid):
                spend_total = float(np.asarray(raw_spend[ch], dtype=np.float64).sum())
                cpl_draws = spend_total / attr_draws[valid]
                cpl_lower[ch] = float(np.percentile(cpl_draws, 2.5))
                cpl_upper[ch] = float(np.percentile(cpl_draws, 97.5))
            else:
                cpl_lower[ch] = float("inf")
                cpl_upper[ch] = float("inf")

        return ModelResult(
            model_name="PyMC",
            channel_names=channel_names,
            coefficients=coefficients,
            intercept=intercept_mean,
            cpl=cpl,
            contribution=contribution,
            contribution_pct=contribution_pct,
            y_pred=np.asarray(y_pred, dtype=np.float64),
            baseline=np.asarray(baseline, dtype=np.float64),
            baseline_pct=baseline_pct,
            r_squared=float(r_squared),
            rmse=rmse,
            coefficient_lower=coefficient_lower,
            coefficient_upper=coefficient_upper,
            cpl_lower=cpl_lower,
            cpl_upper=cpl_upper,
        )

    def predict(self, X: np.ndarray) -> np.ndarray:
        if self._posterior_means is None:
            raise ValueError("Model has not been fitted")

        X_values = np.asarray(X, dtype=np.float64)
        intercept = float(self._posterior_means["intercept"])
        coefs = np.asarray(self._posterior_means["coef_means"], dtype=np.float64)
        return intercept + X_values @ coefs
