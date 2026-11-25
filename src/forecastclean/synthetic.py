"""Synthetic series for tests/pipeline checks (NOT research data)."""
import numpy as np
import pandas as pd


def seasonal_series(n=240, season=12, noise=0.3, trend=0.02, seed=0, start="2000-01-01"):
    rng = np.random.default_rng(seed); t = np.arange(n)
    y = 10 + trend * t + 2 * np.sin(2 * np.pi * t / season) + rng.normal(0, noise, n)
    return pd.Series(y, index=pd.date_range(start, periods=n, freq="MS"))


def random_walk(n=240, seed=0, start="2000-01-01"):
    rng = np.random.default_rng(seed)
    return pd.Series(100 + np.cumsum(rng.normal(0, 1, n)), index=pd.date_range(start, periods=n, freq="MS"))
