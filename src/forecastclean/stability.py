"""Ranking stability (RQ3) and multiple-comparison control.

ranking_stability: bootstrap over forecast origins of ONE series -> how often the model ranking
(by mean MASE) matches the full-sample ranking (Kendall tau) and how often the best model stays best.
across_series_stability: same idea, bootstrapping over SERIES using each series' relative MASE.
holm: Holm-Bonferroni adjusted p-values.
"""
from __future__ import annotations

import numpy as np
import pandas as pd
from scipy import stats


def holm(pvals) -> np.ndarray:
    p = np.asarray(pvals, float); n = len(p); order = np.argsort(p)
    adj = np.empty(n); running = 0.0
    for rank, i in enumerate(order):
        running = max(running, (n - rank) * p[i]); adj[i] = min(1.0, running)
    return adj


def _stab(w: pd.DataFrame, n_boot: int, seed: int) -> dict:
    """w: rows = resampling units (origins or series), cols = models, values = loss (lower is better)."""
    w = w.dropna(axis=0)
    if len(w) < 3 or w.shape[1] < 2:
        return dict(n_units=len(w), mean_tau=np.nan, p_best_same=np.nan, best=None)
    full = w.mean(); best = full.idxmin(); rng = np.random.default_rng(seed)
    taus, same = [], []
    for _ in range(n_boot):
        m = w.iloc[rng.integers(0, len(w), len(w))].mean()
        t = stats.kendalltau(full.values, m.values)[0]
        taus.append(t); same.append(m.idxmin() == best)
    return dict(n_units=len(w), mean_tau=float(np.nanmean(taus)), p_best_same=float(np.mean(same)), best=best)


def ranking_stability(res: pd.DataFrame, n_boot: int = 500, seed: int = 0) -> dict:
    return _stab(res.pivot_table(index="origin", columns="model", values="mase"), n_boot, seed)


def across_series_stability(rel_matrix: pd.DataFrame, n_boot: int = 500, seed: int = 0) -> dict:
    """rel_matrix: rows = series, cols = models, values = log relative MASE (lower is better)."""
    return _stab(rel_matrix, n_boot, seed)
