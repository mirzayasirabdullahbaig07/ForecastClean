"""Rolling-origin evaluation with an explicit no-look-ahead guarantee and a contamination split.

For origin t, a model sees series[:t] and forecasts series[t:t+h]. Targets are scored with MASE
(scale = in-sample seasonal-naive MAE of the context) so errors are comparable across series.

Contamination design: a pretrained model has a training-data cutoff date. Origins whose target
window ends on or before the cutoff are 'pre-cutoff' (the model may have SEEN those values);
origins whose target window starts after the cutoff are 'post-cutoff' (clean). Comparing a model's
skill vs a classical reference on pre vs post is the leakage signal (RQ2).
"""
from __future__ import annotations

import numpy as np
import pandas as pd
from scipy import stats


def mase(y_true, y_pred, train, season=1):
    s = max(season, 1)
    scale = np.mean(np.abs(train[s:] - train[:-s])) if len(train) > s else np.nan
    scale = scale if scale and scale > 0 else np.nan
    return float(np.mean(np.abs(y_true - y_pred)) / scale)


def rolling_origins(n, initial, h, step):
    """Yield (t) such that series[:t] is the context and series[t:t+h] the target (t+h <= n)."""
    t = initial
    while t + h <= n:
        yield t
        t += step


def evaluate(series: pd.Series, forecasters: dict, h=12, initial=None, step=None, season=1,
             min_train=30, max_context=None, max_origins=None, eval_start=None) -> pd.DataFrame:
    """Return long table: origin_idx, origin_date, target_start, target_end, model, mase, abs_err_h (vector mean)."""
    y = series.to_numpy(float); idx = series.index
    initial = initial or max(min_train, len(y) // 2); step = step or h
    if eval_start is not None:                               # first origin whose target starts on/after eval_start
        first = int(idx.searchsorted(pd.Timestamp(eval_start)))
        initial = max(min_train, first)
    rows, errs = [], {}
    origins = list(rolling_origins(len(y), initial, h, step))
    if max_origins and len(origins) > max_origins:           # evenly thinned origins (speed on long series)
        keep = np.unique(np.linspace(0, len(origins) - 1, max_origins).round().astype(int))
        origins = [origins[i] for i in keep]
    for t in origins:
        lo = max(0, t - max_context) if max_context else 0   # optional context cap (still only past data)
        ctx, tgt = y[lo:t], y[t:t + h]
        assert len(ctx) == t - lo and idx[t - 1] < idx[t]     # no look-ahead by construction
        for name, f in forecasters.items():
            pred = np.asarray(f(ctx, h, season), float)
            rows.append(dict(origin=t, target_start=idx[t], target_end=idx[t + h - 1], model=name,
                             mase=mase(tgt, pred, ctx, season), loss_vec=np.abs(tgt - pred)))
    return pd.DataFrame(rows)


def dm_test(e1: np.ndarray, e2: np.ndarray, h: int = 1) -> tuple[float, float]:
    """Diebold-Mariano test of equal accuracy on loss differentials d = e1 - e2 (e.g. per-origin MASE),
    Harvey-Leybourne-Newbold small-sample correction. Returns (statistic, two-sided p). H0: equal accuracy."""
    d = np.asarray(e1, float) - np.asarray(e2, float)
    n = len(d)
    if n < 3:
        return float("nan"), 1.0
    if np.allclose(d, d[0]):                       # zero variance: identical (d=0) or perfectly consistent gap
        return (float("nan"), 1.0) if np.isclose(d[0], 0) else (float(np.sign(d[0]) * np.inf), 0.0)
    dbar = d.mean()
    gamma0 = np.var(d, ddof=0)
    var = gamma0 + 2 * sum((1 - k / h) * np.mean((d[k:] - dbar) * (d[:-k] - dbar)) for k in range(1, h)) if h > 1 else gamma0
    var = max(var / n, 1e-18)
    dm = dbar / np.sqrt(var)
    corr = np.sqrt((n + 1 - 2 * h + h * (h - 1) / n) / n)
    stat = dm * corr
    return float(stat), float(2 * stats.t.sf(abs(stat), df=n - 1))


def skill_table(res: pd.DataFrame, reference="seasonal_naive", cutoff=None) -> pd.DataFrame:
    """Mean MASE and relative MASE vs a reference (<1 = better than reference), optionally pre/post cutoff."""
    w = res.pivot_table(index=["origin", "target_start", "target_end"], columns="model", values="mase").reset_index()
    if cutoff is not None:
        cutoff = pd.Timestamp(cutoff)
        w["period"] = np.where(w.target_end <= cutoff, "pre_cutoff", np.where(w.target_start > cutoff, "post_cutoff", "straddle"))
    else:
        w["period"] = "all"
    models = [c for c in w.columns if c in set(res.model)]
    rows = []
    for period, g in w.groupby("period"):
        for m in models:
            rel = g[m] / g[reference]
            rows.append(dict(period=period, model=m, n_origins=len(g), mase=g[m].mean(),
                             rel_mase_geo=float(np.exp(np.log(rel.replace(0, np.nan)).mean())),
                             dm_p_vs_ref=dm_test(g[m].to_numpy(), g[reference].to_numpy())[1] if m != reference else np.nan))
    return pd.DataFrame(rows)
