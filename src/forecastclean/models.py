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
    Verified on real weights: chronos-bolt-tiny (smoke test, 2025-11-25). Chronos-2 needs 3-d input (handled below).
    `pipeline` lets tests inject a fake."""
    import torch
    if pipeline is None:
        from chronos import BaseChronosPipeline
        dev = ("cuda" if torch.cuda.is_available() else "cpu") if device == "auto" else device
        pipeline = BaseChronosPipeline.from_pretrained(model_id, device_map=dev)

    mode = {"3d": "Chronos2" in type(pipeline).__name__}   # Chronos-2 wants (n_series, n_variates, history); Bolt takes 1-d

    def f(train, h, season=1):
        x = torch.tensor(np.asarray(train, dtype=np.float32), dtype=torch.float32)
        if mode["3d"]:
            x = x.reshape(1, 1, -1)
        try:
            q, _ = pipeline.predict_quantiles(x, prediction_length=h, quantile_levels=[0.5])   # positional input: version-proof
        except ValueError:
            if mode["3d"]:
                raise
            mode["3d"] = True                                  # pipeline rejected 1-d input -> retry once as 3-d, remember it
            q, _ = pipeline.predict_quantiles(x.reshape(1, 1, -1), prediction_length=h, quantile_levels=[0.5])
        first = q[0]                                                                       # first (only) series
        arr = np.asarray(first.detach().cpu().numpy() if hasattr(first, "detach") else first, dtype=float)
        return arr.reshape(-1, arr.shape[-2], arr.shape[-1])[0, :, 0]                      # first variate, h steps, median
    f.__name__ = model_id.split("/")[-1]
    return f


def timesfm_forecaster(model_id="google/timesfm-2.5-200m-pytorch", max_context=1024, max_horizon=256, model=None):
    """Adapter for TimesFM 2.5 (median forecast), written against the usage example on the Hugging Face model card
    (fetched 2026-11-27): timesfm.TimesFM_2p5_200M_torch.from_pretrained(id), model.compile(ForecastConfig(...)),
    model.forecast(horizon, inputs=[1-d arrays]) -> (point [n,h], quantiles [n,h,10] = mean, q10..q90).
    NOT yet run on real weights (the sandbox cannot download them) - first Colab run is the real test.
    `model` lets tests inject a fake. Needs `pip install` from source: git clone google-research/timesfm; pip install -e .[torch].
    torch_compile is off on purpose (torch.compile is fragile on Colab's Python 3.13); max_horizon must cover the largest h."""
    if model is None:
        import timesfm
        model = timesfm.TimesFM_2p5_200M_torch.from_pretrained(model_id, torch_compile=False)
        model.compile(timesfm.ForecastConfig(max_context=max_context, max_horizon=max_horizon, normalize_inputs=True,
                                              use_continuous_quantile_head=True, force_flip_invariance=True,
                                              infer_is_positive=True, fix_quantile_crossing=True))

    def f(train, h, season=1):
        if h > max_horizon:
            raise ValueError(f"horizon {h} exceeds the compiled max_horizon {max_horizon}")
        point, quant = model.forecast(horizon=h, inputs=[np.asarray(train, dtype=np.float32)])
        q = np.asarray(quant, dtype=float)
        # quantile axis = [mean, q10, ..., q90] -> index 5 is the median, matching the median used for Chronos; fall back to point
        out = q[0, :, 5] if q.ndim == 3 and q.shape[-1] == 10 else np.asarray(point, dtype=float)[0]
        return np.asarray(out, dtype=float)[:h]
    f.__name__ = model_id.split("/")[-1]
    return f


def foundation_forecaster(model_id, **kw):
    """One entry point for every pretrained model: TimesFM ids go to the TimesFM adapter, everything else to Chronos."""
    return timesfm_forecaster(model_id, **kw) if "timesfm" in model_id.lower() else chronos_forecaster(model_id, **kw)


# ---------- tuned (automatically selected) baselines: statsforecast AutoETS / AutoTheta / AutoARIMA ----------
# Untuned ETS/ARIMA(1,1,1) are the first thing a reviewer attacks, so these select the model form by information
# criterion on each training window. Optional dependency: `pip install statsforecast`.
def _auto(model_name, train, h, season):
    from statsforecast import models as sfm
    y = np.asarray(train, dtype=float)
    try:
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            out = np.asarray(getattr(sfm, model_name)(season_length=max(int(season), 1)).forecast(y=y, h=h)["mean"], dtype=float)
        return out if out.shape == (h,) and np.all(np.isfinite(out)) else naive(y, h)
    except Exception:
        return naive(y, h)                                  # never let one failed fit abort a whole run


def auto_ets(train, h, season=1):
    return _auto("AutoETS", train, h, season)


def auto_theta(train, h, season=1):
    return _auto("AutoTheta", train, h, season)


def auto_arima(train, h, season=1):
    return _auto("AutoARIMA", train, h, season)


def tuned_models(season=1) -> dict:
    """Tuned baselines to add for a series. AutoARIMA is only used for NON-seasonal series: on seasonal ones it needs
    3-23 s per fit (measured: 1024 daily points, season 7 -> 5 s; 336 hourly points, season 24 -> 23 s), which makes a
    rolling-origin run impractical on Colab. This limitation must be stated in the paper."""
    m = {"auto_ets": auto_ets, "auto_theta": auto_theta}
    if int(season) == 1:
        m["auto_arima"] = auto_arima
    return m


BASELINES = {"naive": naive, "seasonal_naive": seasonal_naive, "drift": drift, "ets": ets, "arima": arima,
             "theta": theta, "comb": comb}
