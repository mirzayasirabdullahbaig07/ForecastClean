"""RQ2: contamination gap. For each pretrained model m with release date r_m, score m and the classical models on
windows BEFORE r_m (target ends <= r_m: could be in m's training data) and AFTER r_m (target starts > r_m: cannot be).

Both periods are scored against naive, so a shift common to every model (regime change, volatility) largely cancels.
  gap(model)  = log relMASE_post - log relMASE_pre      (> 0: the model did relatively WORSE after release)
  DiD(m)      = gap(m) - median over classical models of gap   (> 0: m lost MORE than classical models did)
A positive DiD is the leakage signature, but not proof: release dates are conservative, not true cutoffs, and with a
handful of series the interval is wide. Classical models cannot be contaminated, so they absorb the data-shift part.
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

from .data import SERIES
from .evaluate import evaluate
from .models import BASELINES
from .batch import H_BY_FREQ

CLASSICAL = [m for m in BASELINES if m != "naive"]


def _rel(res: pd.DataFrame) -> pd.Series:
    mm = res.groupby("model").mase.mean()
    return mm / mm["naive"]


def gap_for_series(ser, season, h, chronos_name, chronos_fc, release, max_origins=60, max_context=1024,
                   eval_start="2015-01-01", min_windows=5, drop=()):
    """Return (rows, summary) or (None, reason). rows: one line per model x period."""
    fc = {k: v for k, v in BASELINES.items() if k not in drop}; fc[chronos_name] = chronos_fc   # drop: skip slow models
    r = pd.Timestamp(release)
    pre = evaluate(ser, fc, h=h, season=season, max_context=max_context, max_origins=max_origins,
                   eval_start=eval_start, eval_end=r)
    post = evaluate(ser, fc, h=h, season=season, max_context=max_context, max_origins=max_origins,
                    eval_start=r + pd.Timedelta(days=1))
    n_pre = pre.origin.nunique() if len(pre) else 0; n_post = post.origin.nunique() if len(post) else 0
    if n_pre < min_windows or n_post < min_windows:
        return None, f"pre windows={n_pre}, post windows={n_post} (< {min_windows})"
    rp, rq = _rel(pre), _rel(post)
    rows = pd.DataFrame({"rel_pre": rp, "rel_post": rq}).drop(index="naive")
    rows["gap"] = np.log(rows.rel_post) - np.log(rows.rel_pre)
    rows = rows.reset_index(names="model"); rows["chronos"] = chronos_name; rows["n_pre"] = n_pre; rows["n_post"] = n_post
    g_c = float(rows.loc[rows.model == chronos_name, "gap"].iloc[0])
    g_cl = float(rows.loc[rows.model.isin([m for m in CLASSICAL if m not in drop]), "gap"].median())   # median: untuned ARIMA swings wildly
    return rows, dict(chronos=chronos_name, gap_chronos=g_c, gap_classical=g_cl, did=g_c - g_cl, n_pre=n_pre, n_post=n_post)


def aggregate(summary: pd.DataFrame, n_boot=4000, seed=0) -> pd.DataFrame:
    """Mean DiD across series per model with a bootstrap-over-series 95% interval (few series -> wide, report honestly)."""
    rng = np.random.default_rng(seed); out = []
    for m, g in summary.groupby("chronos"):
        d = g.did.to_numpy(); n = len(d)
        boots = np.array([rng.choice(d, n).mean() for _ in range(n_boot)]) if n > 1 else np.array([np.nan])
        out.append(dict(chronos=m, n_series=n, mean_did=float(d.mean()), ci_lo=float(np.nanpercentile(boots, 2.5)),
                        ci_hi=float(np.nanpercentile(boots, 97.5)), n_positive=int((d > 0).sum())))
    return pd.DataFrame(out)


def run_gap(args) -> int:
    from .models import chronos_forecaster
    from .registry import RELEASE
    data, out = Path(args.data), Path(args.out); out.mkdir(parents=True, exist_ok=True)
    names = args.only or [n for n in SERIES if (data / f"{n}.csv").exists()]
    if not names:
        print(f"No series found in {data}. Run `forecastclean download` first."); return 1
    allrows, sums = [], []
    for mid in args.chronos:
        short = mid.split("/")[-1]; rel = RELEASE[short][0]                   # KeyError = unknown model: never guess a date
        fcm = chronos_forecaster(mid)
        print(f"\n== {short}: release (clean-from) {rel}", flush=True)
        for n in names:
            freq, season, _ = SERIES[n]
            df = pd.read_csv(data / f"{n}.csv", parse_dates=["date"]).sort_values("date")
            ser = df.set_index("date")["value"].astype(float); h = H_BY_FREQ[freq]
            rows, info = gap_for_series(ser, season, h, short, fcm, rel, args.max_origins, args.max_context, args.eval_start,
                                         drop=tuple(args.drop or ()))
            if rows is None:
                print(f"   {n}: skipped ({info})"); continue
            rows.insert(0, "series", n); rows["h"] = h; allrows.append(rows)
            info.update(series=n, h=h); sums.append(info)
            print(f"   {n} (h={h}): Chronos gap {info['gap_chronos']:+.3f}, classical gap {info['gap_classical']:+.3f}, "
                  f"DiD {info['did']:+.3f}  (pre {info['n_pre']}, post {info['n_post']} windows)", flush=True)
    if not sums:
        print("No series had enough windows both before and after the release date."); return 1
    pd.concat(allrows).round(4).to_csv(out / "gap_windows.csv", index=False)
    summ = pd.DataFrame(sums); summ.round(4).to_csv(out / "gap_summary.csv", index=False)
    agg = aggregate(summ); agg.round(4).to_csv(out / "gap_aggregate.csv", index=False)
    print("\nContamination gap (DiD > 0 = model lost MORE than classical models after its release; 95% bootstrap over series):")
    print(agg.round(3).to_string(index=False))
    return 0
