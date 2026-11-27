"""Run all downloaded series: skill tables per series, a combined summary, and ranking stability."""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

from .data import SERIES
from .evaluate import evaluate, skill_table
from .models import BASELINES, tuned_models
from .stability import across_series_stability, holm, ranking_stability

H_BY_FREQ = {"M": 6, "D": 14, "H": 24, "B": 10}
SWEEP = {"M": [1, 3, 6, 12], "D": [1, 7, 14, 28], "H": [1, 24, 48, 168], "B": [1, 5, 10, 20]}


def _kendall_between_horizons(tbl: pd.DataFrame) -> list[dict]:
    """tbl: columns h, model, rel_mase for one series. Kendall tau of model rankings between horizons."""
    from scipy import stats
    out, hs = [], sorted(tbl.h.unique())
    wide = tbl.pivot_table(index="model", columns="h", values="rel_mase")
    for a, b in zip(hs[:-1], hs[1:]):
        t = stats.kendalltau(wide[a], wide[b])[0]
        out.append(dict(h_from=a, h_to=b, tau=float(t)))
    return out


def _complete_models(mat: pd.DataFrame):
    """Keep only models scored on EVERY series. A model present on a subset (e.g. AutoARIMA, used on non-seasonal series
    only) would otherwise be averaged over different series than the others and look artificially good or bad."""
    full = mat.dropna(axis=1, how="any")
    return full, [c for c in mat.columns if c not in full.columns]


def run_batch(args) -> int:
    from .registry import clean_from as _clean_from
    data, out = Path(args.data), Path(args.out); out.mkdir(parents=True, exist_ok=True)
    names = args.only or [n for n in SERIES if (data / f"{n}.csv").exists()]
    if not names:
        print(f"No series found in {data}. Run `forecastclean download` first."); return 1
    fc = dict(BASELINES)
    for mid in (args.chronos or []):
        from .models import chronos_forecaster
        fc[mid.split("/")[-1]] = chronos_forecaster(mid)
    pretrained = [k for k in fc if k not in BASELINES]
    cutoff = args.cutoff
    if getattr(args, "release_cutoff", False):
        cutoff = str(_clean_from(pretrained).date()) if pretrained else cutoff
        print(f"clean-from cutoff (latest release among {pretrained}): {cutoff}")
    if getattr(args, "clean_from", None):
        cutoff = args.clean_from
    # post-only: first window must start the day AFTER the cutoff (a window starting ON the cutoff day is not clean)
    eval_start = (str((pd.Timestamp(cutoff) + pd.Timedelta(days=1)).date())
                  if (getattr(args, "post_only", False) and cutoff) else args.eval_start)
    rows, stab, taus = [], [], []
    for n in names:
        freq, season, _ = SERIES[n]
        df = pd.read_csv(data / f"{n}.csv", parse_dates=["date"]).sort_values("date")
        ser = df.set_index("date")["value"].astype(float)
        hs = SWEEP[freq] if getattr(args, "horizon_sweep", False) else [H_BY_FREQ[freq]]
        print(f"{n}: {len(ser)} obs, last {ser.index[-1].date()}, horizons={hs}, season={season}", flush=True)
        per_series = []
        for k, h in enumerate(hs):
            res = evaluate(ser, {**fc, **(tuned_models(season) if getattr(args, "tuned", False) else {})}, h=h, season=season, max_context=args.max_context,
                           max_origins=args.max_origins, eval_start=eval_start)
            if len(res) == 0:
                print(f"   h={h}: no windows after {eval_start} -> skipped"); continue
            t = skill_table(res, "naive", cutoff); t.insert(0, "h_idx", k); t.insert(0, "h", h); t.insert(0, "series", n)
            per_series.append(t); rows.append(t)
            st = ranking_stability(res); st.update(series=n, h=h); stab.append(st)
        if len(per_series) > 1:
            both = pd.concat(per_series); both = both[both.period.isin(["all", "post_cutoff"])]
            for r in _kendall_between_horizons(both):
                r["series"] = n; taus.append(r)
    if not rows:
        print("No windows at all - check --eval-start / --clean-from against the series' last dates."); return 1
    summ = pd.concat(rows, ignore_index=True)
    summ["dm_p_holm"] = np.nan                               # Holm over all non-reference tests per period and horizon
    for _, g in summ[summ.dm_p_vs_ref.notna()].groupby(["period", "h_idx"]):
        summ.loc[g.index, "dm_p_holm"] = holm(g.dm_p_vs_ref.values)
    summ.round(4).to_csv(out / "summary.csv", index=False)
    pd.DataFrame(stab).round(4).to_csv(out / "stability_per_series.csv", index=False)
    if taus:
        pd.DataFrame(taus).round(4).to_csv(out / "horizon_rank_tau.csv", index=False)
    sel = summ[summ.period.isin(["all", "post_cutoff"])]
    for h_key, g in [(None, sel)] if not getattr(args, "horizon_sweep", False) else sel.groupby("h_idx"):
        mat = g.pivot_table(index="series", columns="model", values="rel_mase")
        mat, partial = _complete_models(np.log(mat.replace(0, np.nan)))
        if partial:
            print(f"   (not ranked across series, missing on some series: {', '.join(partial)})")
        cs = across_series_stability(mat)
        print(f"\n[{'all horizons' if h_key is None else f'horizon position {h_key} (0=shortest)'}] mean log-relative MASE across {cs['n_units']} series (lower = better):\n",
              mat.mean().sort_values().round(3).to_string())
        print(f"ranking stability: best={cs['best']}, P(best stays best)={cs['p_best_same']:.2f}, mean Kendall tau={cs['mean_tau']:.2f}")
        cs["h"] = h_key; pd.DataFrame([cs]).to_csv(out / f"stability_across_series{'' if h_key is None else '_hpos'+str(h_key)}.csv", index=False)
    if taus:
        print("\nMean Kendall tau between consecutive horizons' rankings (per series):")
        print(pd.DataFrame(taus).groupby("series").tau.mean().round(2).to_string())
    return 0
