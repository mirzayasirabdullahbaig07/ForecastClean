"""Probabilistic accuracy (reviewers expect more than point forecasts).

Metric: scaled CRPS, computed as 2 x mean pinball loss over the quantile grid 0.1..0.9, divided by the in-sample seasonal-naive
MAE of the context (the same scale as MASE). It approximates the CRPS (the weighted quantile loss family) on a common scale across
series. Reported next to it: coverage of the central 80% interval (q10-q90; nominal 0.80).

Reference probabilistic forecasters (the classical side has no native quantiles in this package):
  naive_q / seasonal_naive_q / theta_q = point forecast + empirical quantiles of the in-sample seasonal differences
  (last 500), widening with sqrt(number of seasons ahead). Plain, transparent, and the same for every series.
Foundation models give their own quantiles (Chronos: any level; TimesFM 2.5: deciles).
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

from .data import SERIES
from .evaluate import select_origins
from .models import naive, seasonal_naive, theta

LEVELS = np.round(np.arange(0.1, 0.95, 0.1), 1)          # 0.1 ... 0.9


def pinball(y, q, levels=LEVELS):
    """y: [h]; q: [h, Q]; returns [h, Q] pinball losses."""
    d = np.asarray(y, float)[:, None] - np.asarray(q, float)
    return np.maximum(levels[None, :] * d, (levels[None, :] - 1.0) * d)


def scale_of(train, season=1):
    s = max(int(season), 1)
    sc = float(np.mean(np.abs(train[s:] - train[:-s]))) if len(train) > s else np.nan
    return sc if sc and sc > 0 else np.nan


def scaled_crps(y, q, train, season=1, levels=LEVELS):
    return float(2.0 * pinball(y, q, levels).mean() / scale_of(train, season))


def coverage80(y, q):
    y = np.asarray(y, float); return float(np.mean((y >= q[:, 0]) & (y <= q[:, -1])))


def empirical_quantile_forecaster(point_fn):
    """f(train, h, season, levels) -> [h, Q]: point forecast + empirical quantiles of in-sample seasonal differences."""
    def f(train, h, season=1, levels=LEVELS):
        train = np.asarray(train, float); s = max(int(season), 1)
        res = (train[s:] - train[:-s])[-500:] if len(train) > s else np.zeros(1)
        qs = np.quantile(res - np.median(res), levels)                    # centred: the point forecaster carries the level
        grow = np.sqrt(np.ceil(np.arange(1, h + 1) / s))
        return np.asarray(point_fn(train, h, s), float)[:, None] + grow[:, None] * qs[None, :]
    return f


REFERENCES = {"naive_q": empirical_quantile_forecaster(naive), "seasonal_naive_q": empirical_quantile_forecaster(seasonal_naive),
              "theta_q": empirical_quantile_forecaster(theta)}


def evaluate_prob(ser: pd.Series, quant_fns: dict, h, season, max_context=1024, max_origins=None, min_train=30,
                  eval_start=None, eval_end=None) -> pd.DataFrame:
    """Rolling-origin scaled CRPS and 80% coverage; quant_fns: name -> g(train, h, season, levels) -> [h, Q]."""
    y = ser.to_numpy(float); rows = []
    for t in select_origins(ser, h, min_train=min_train, max_origins=max_origins, eval_start=eval_start, eval_end=eval_end):
        lo = max(0, t - max_context) if max_context else 0
        ctx, tgt = y[lo:t], y[t:t + h]
        assert len(ctx) == t - lo and ser.index[t - 1] < ser.index[t]          # no look-ahead
        for name, g in quant_fns.items():
            q = np.sort(np.asarray(g(ctx, h, season, LEVELS), float), axis=1)    # sort: remove any quantile crossing
            rows.append(dict(origin=t, target_start=ser.index[t], target_end=ser.index[t + h - 1], model=name,
                             scrps=scaled_crps(tgt, q, ctx, season), cov80=coverage80(tgt, q)))
    return pd.DataFrame(rows)


def run_prob(args) -> int:
    from .batch import H_BY_FREQ
    from .models import foundation_forecaster
    from .registry import clean_from
    data, out = Path(args.data), Path(args.out); out.mkdir(parents=True, exist_ok=True)
    names = args.only or [n for n in SERIES if (data / f"{n}.csv").exists()]
    if not names:
        print(f"No series found in {data}. Run `forecastclean download` first."); return 1
    qf = dict(REFERENCES); pretrained = []
    for mid in (args.chronos or []):
        short = mid.split("/")[-1]; fm = foundation_forecaster(mid); pretrained.append(short)
        qf[short] = (lambda tr, h, s, lv, _fm=fm: _fm.quantiles(tr, h, lv))
    cutoff = args.clean_from
    if cutoff is None and args.release_cutoff and pretrained:
        cutoff = str(clean_from(pretrained).date()); print(f"clean-from cutoff (latest release among {pretrained}): {cutoff}")
    eval_start = str((pd.Timestamp(cutoff) + pd.Timedelta(days=1)).date()) if cutoff else args.eval_start
    allrows = []
    for n in names:
        freq, season, _ = SERIES[n]
        ser = pd.read_csv(data / f"{n}.csv", parse_dates=["date"]).sort_values("date").set_index("date")["value"].astype(float)
        h = H_BY_FREQ[freq]
        res = evaluate_prob(ser, qf, h, season, args.max_context, args.max_origins, eval_start=eval_start)
        if not len(res):
            print(f"{n}: no windows after {eval_start} -> skipped"); continue
        g = res.groupby("model").agg(scrps=("scrps", "mean"), cov80=("cov80", "mean"), n_windows=("scrps", "size")).reset_index()
        g["rel_scrps"] = g.scrps / g.loc[g.model == "naive_q", "scrps"].iloc[0]; g.insert(0, "series", n); g["h"] = h
        allrows.append(g); print(f"{n}: h={h}, {int(g.n_windows.iloc[0])} windows", flush=True)
    if not allrows:
        print("No windows at all."); return 1
    summ = pd.concat(allrows, ignore_index=True); summ.round(4).to_csv(out / "prob_summary.csv", index=False)
    mat = np.log(summ.pivot_table(index="series", columns="model", values="rel_scrps"))
    print("\nMean log-relative scaled CRPS vs naive_q across series (lower = better):")
    print(mat.mean().sort_values().round(3).to_string())
    print("\nMean coverage of the central 80% interval (nominal 0.80):")
    print(summ.groupby("model").cov80.mean().round(3).to_string())
    return 0
