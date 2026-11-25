"""Forecasters. All share: f(train: np.ndarray, h: int, season: int) -> np.ndarray of length h.

Classical baselines are fully implemented and tested. `chronos_forecaster` is a thin adapter for a
pretrained foundation model; it needs `pip install chronos-forecasting torch` and internet access to
download weights, and has NOT been run in the environment where this code was written.
"""
from __future__ import annotations

import warnings

import numpy as np


def naive(train, h, season=1):
    return np.repeat(train[-1], h)


def seasonal_naive(train, h, season=1):
    if season <= 1 or len(train) < season:
        return naive(train, h)
    reps = int(np.ceil(h / season))
    return np.tile(train[-season:], reps)[:h]


def drift(train, h, season=1):
    slope = (train[-1] - train[0]) / max(len(train) - 1, 1)
    return train[-1] + slope * np.arange(1, h + 1)


def ets(train, h, season=1):
    from statsmodels.tsa.holtwinters import ExponentialSmoothing
    use_season = season > 1 and len(train) >= 2 * season
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        m = ExponentialSmoothing(train, trend="add", damped_trend=True,
                                 seasonal="add" if use_season else None,
                                 seasonal_periods=season if use_season else None).fit()
    return np.asarray(m.forecast(h))


def arima(train, h, season=1, order=(1, 1, 1)):
    from statsmodels.tsa.arima.model import ARIMA
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        try:
            return np.asarray(ARIMA(train, order=order).fit().forecast(h))
        except Exception:
            return naive(train, h)


def theta(train, h, season=1):
    from statsmodels.tsa.forecasting.theta import ThetaModel
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        try:
            use = season > 1 and len(train) >= 2 * season
            m = ThetaModel(np.asarray(train, float), period=season if use else None, deseasonalize=use).fit()
            return np.asarray(m.forecast(h))
        except Exception:
            return naive(train, h)


def comb(train, h, season=1):
    """Equal-weight combination of ETS, ARIMA and Theta (combinations are hard to beat in forecasting competitions)."""
    return np.mean([ets(train, h, season), arima(train, h, season), theta(train, h, season)], axis=0)


def chronos_forecaster(model_id="amazon/chronos-bolt-tiny", device="auto", pipeline=None):
    """Adapter for Chronos-Bolt / Chronos-2 (median forecast). Written against chronos-forecasting 2.3.2's source:
    BaseChronosPipeline.from_pretrained picks the right pipeline class, and predict_quantiles(inputs, prediction_length,
    quantile_levels) returns a tensor [batch,h,Q] (Bolt) or a LIST of tensors [variates,h,Q] (Chronos-2).
    The adapter itself is unit-tested with stand-in pipelines only; the real weights have NOT been run yet.
    `pipeline` lets tests inject a fake."""
    import torch
    if pipeline is None:
        from chronos import BaseChronosPipeline
        dev = ("cuda" if torch.cuda.is_available() else "cpu") if device == "auto" else device
        pipeline = BaseChronosPipeline.from_pretrained(model_id, device_map=dev)

    def f(train, h, season=1):
        x = torch.tensor(np.asarray(train, dtype=np.float32), dtype=torch.float32)
        q, _ = pipeline.predict_quantiles(x, prediction_length=h, quantile_levels=[0.5])   # positional input: version-proof
        first = q[0]                                                                       # first (only) series
        arr = np.asarray(first.detach().cpu().numpy() if hasattr(first, "detach") else first, dtype=float)
        return arr.reshape(-1, arr.shape[-2], arr.shape[-1])[0, :, 0]                      # first variate, h steps, median
    f.__name__ = model_id.split("/")[-1]
    return f


BASELINES = {"naive": naive, "seasonal_naive": seasonal_naive, "drift": drift, "ets": ets, "arima": arima,
             "theta": theta, "comb": comb}
