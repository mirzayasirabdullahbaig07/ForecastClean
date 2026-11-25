"""Run all downloaded series: skill tables per series, a combined summary, and ranking stability."""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

from .data import SERIES
from .evaluate import evaluate, skill_table
from .models import BASELINES
from .stability import across_series_stability, holm, ranking_stability

H_BY_FREQ = {"M": 6, "D": 14, "H": 24, "B": 10}


def run_batch(args) -> int:
    data, out = Path(args.data), Path(args.out); out.mkdir(parents=True, exist_ok=True)
    names = args.only or [n for n in SERIES if (data / f"{n}.csv").exists()]
    if not names:
        print(f"No series found in {data}. Run `forecastclean download` first."); return 1
    fc = dict(BASELINES)
    for mid in (args.chronos or []):
        from .models import chronos_forecaster
        fc[mid.split("/")[-1]] = chronos_forecaster(mid)
    rows, stab = [], []
    for n in names:
        freq, season, _ = SERIES[n]
        df = pd.read_csv(data / f"{n}.csv", parse_dates=["date"]).sort_values("date")
        ser = df.set_index("date")["value"].astype(float)
        ref = "naive"                                        # one reference for every series (see README §3)
        print(f"{n}: {len(ser)} obs, h={H_BY_FREQ[freq]}, season={season}", flush=True)
        res = evaluate(ser, fc, h=H_BY_FREQ[freq], season=season,
                       max_context=args.max_context, max_origins=args.max_origins, eval_start=args.eval_start)
        t = skill_table(res, ref, args.cutoff); t.insert(0, "series", n); rows.append(t)
        st = ranking_stability(res); st["series"] = n; stab.append(st)
    summ = pd.concat(rows, ignore_index=True)
    summ["dm_p_holm"] = np.nan                               # Holm over all non-reference tests per period
    for per, g in summ[summ.dm_p_vs_ref.notna()].groupby("period"):
        summ.loc[g.index, "dm_p_holm"] = holm(g.dm_p_vs_ref.values)
    summ.round(4).to_csv(out / "summary.csv", index=False)
    pd.DataFrame(stab).round(4).to_csv(out / "stability_per_series.csv", index=False)
    mat = summ[summ.period.isin(["all", "post_cutoff"])].pivot_table(index="series", columns="model", values="rel_mase_geo")
    mat = np.log(mat.replace(0, np.nan)).dropna(axis=1, how="all")
    cs = across_series_stability(mat)
    print("\nMean log-relative MASE across series (lower = better):\n", mat.mean().sort_values().round(3).to_string())
    print(f"\nAcross-series ranking stability: best={cs['best']}, P(best stays best)={cs['p_best_same']:.2f}, "
          f"mean Kendall tau={cs['mean_tau']:.2f} (n_series={cs['n_units']})")
    pd.DataFrame([cs]).to_csv(out / "stability_across_series.csv", index=False)
    return 0
