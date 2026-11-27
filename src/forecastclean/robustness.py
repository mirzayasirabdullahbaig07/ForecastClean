"""Robustness checks for the contamination gap (RQ2). Every check answers one reviewer objection to the headline table.

From the result CSVs of `forecastclean gap` (no model needs re-running):
  reference_sensitivity  - is DiD an artefact of using the MEDIAN classical model as reference?
  event_split            - do the calendar-event Wikipedia pages (huge annual spikes) drive the result?
  cluster_boot           - bootstrap with the 10 EUR crosses collapsed into ONE unit (they share the EUR leg)
  leave_one_out          - does any single series flip the sign of the mean?
From `gap_origins.csv` (per-window MASE; written by newer runs of `forecastclean gap`):
  block_did              - moving-block bootstrap over forecast origins WITHIN each series (windows overlap, so they are
                           autocorrelated; resampling them as independent would be too optimistic)
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from .gap import GROUP

# Pre-specified BEFORE looking at the per-page numbers: pages whose traffic is driven by a recurring calendar event.
EVENT_PAGES = {"Christmas", "Easter", "Halloween", "Thanksgiving", "Wimbledon", "SuperBowl", "Ramadan", "Eurovision"}


def _group(series: pd.Series) -> pd.Series:
    return series.str.partition("_")[0].map(GROUP)


def _ci(x, n_boot, rng):
    x = np.asarray(x, float)
    if len(x) < 2:
        return np.nan, np.nan
    b = rng.choice(x, (n_boot, len(x))).mean(1)
    return float(np.percentile(b, 2.5)), float(np.percentile(b, 97.5))


def reference_sensitivity(windows: pd.DataFrame) -> pd.DataFrame:
    """Mean DiD per Chronos model when the 'classical' reference is: median (default), mean, each classical model alone."""
    out = []
    for (c, s), g in windows.groupby(["chronos", "series"]):
        gp = g.set_index("model").gap
        cl = gp.drop(index=c)
        ref = {"median": cl.median(), "mean": cl.mean(), "median_ex_drift": cl.drop(index="drift", errors="ignore").median()}
        ref.update({f"only_{m}": v for m, v in cl.items()})
        for k, v in ref.items():
            out.append(dict(chronos=c, series=s, reference=k, did=gp[c] - v))
    d = pd.DataFrame(out)
    return d.groupby(["chronos", "reference"]).did.agg(mean_did="mean", median_did="median",
                                                      n_positive=lambda x: int((x > 0).sum()), n="size").reset_index()


def event_split(summary: pd.DataFrame, n_boot=4000, seed=0) -> pd.DataFrame:
    """Mean DiD for event-driven vs other Wikipedia pages, FX and electricity, per Chronos model."""
    rng = np.random.default_rng(seed); s = summary.copy(); s["group"] = _group(s.series)
    page = s.series.str.partition("_")[2]
    s.loc[s.group == "wikipedia", "group"] = np.where(page[s.group == "wikipedia"].isin(EVENT_PAGES), "wiki_event", "wiki_other")
    rows = []
    for (c, g), sub in s.groupby(["chronos", "group"]):
        lo, hi = _ci(sub.did, n_boot, rng)
        rows.append(dict(chronos=c, group=g, n_series=len(sub), mean_did=sub.did.mean(), median_did=sub.did.median(),
                         ci_lo=lo, ci_hi=hi, n_positive=int((sub.did > 0).sum())))
    return pd.DataFrame(rows)


def cluster_boot(summary: pd.DataFrame, n_boot=4000, seed=0) -> pd.DataFrame:
    """All-series mean DiD, but the FX pairs are averaged into one unit first (they are not independent)."""
    rng = np.random.default_rng(seed); s = summary.copy(); s["group"] = _group(s.series); rows = []
    for c, g in s.groupby("chronos"):
        units = list(g[g.group != "fx"].did) + [g[g.group == "fx"].did.mean()]
        lo, hi = _ci(units, n_boot, rng)
        rows.append(dict(chronos=c, n_units=len(units), mean_did=float(np.mean(units)), ci_lo=lo, ci_hi=hi))
    return pd.DataFrame(rows)


def leave_one_out(summary: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for c, g in summary.groupby("chronos"):
        full = g.did.mean(); loo = {s: g.did.drop(i).mean() for i, s in zip(g.index, g.series)}
        worst = max(loo, key=lambda k: abs(loo[k] - full))
        rows.append(dict(chronos=c, full_mean=full, loo_min=min(loo.values()), loo_max=max(loo.values()),
                         most_influential=worst, mean_without_it=loo[worst]))
    return pd.DataFrame(rows)


def block_did(origins: pd.DataFrame, block=5, n_boot=2000, seed=0) -> pd.DataFrame:
    """Window-level moving-block bootstrap. For each replicate and each series, resample the origins of the pre period and of
    the post period in blocks of `block` consecutive origins (same blocks for every model, so model comparisons stay paired),
    recompute relMASE vs naive, gap and DiD; then average DiD across series. Returns mean DiD and 95% interval per model."""
    rng = np.random.default_rng(seed); prep = {}
    for (c, s), g in origins.groupby(["chronos", "series"]):
        wide = {p: g[g.period == p].pivot_table(index="origin", columns="model", values="mase").sort_index() for p in ("pre", "post")}
        if all(len(w) >= block for w in wide.values()) and "naive" in wide["pre"]:
            prep[(c, s)] = {p: w.to_numpy() for p, w in wide.items()} | {"cols": list(wide["pre"].columns)}

    def resample(n):
        k = int(np.ceil(n / block)); st = rng.integers(0, n - block + 1, k)
        return np.concatenate([np.arange(a, a + block) for a in st])[:n]

    def did(m, idx, cols, c):
        rel = {p: m[p][idx[p]].mean(0) / m[p][idx[p]][:, cols.index("naive")].mean() for p in ("pre", "post")}
        gap = np.log(rel["post"]) - np.log(rel["pre"])
        cl = [i for i, k in enumerate(cols) if k not in (c, "naive")]
        return gap[cols.index(c)] - np.median(gap[cl])

    res = {}
    for b in range(n_boot):
        for (c, s), m in prep.items():
            idx = {p: resample(len(m[p])) for p in ("pre", "post")}
            res.setdefault(c, {}).setdefault(b, []).append(did(m, idx, m["cols"], c))
    rows = []
    for c, d in res.items():
        means = np.array([np.mean(v) for v in d.values()])
        pt = np.mean([did(m, {p: np.arange(len(m[p])) for p in ("pre", "post")}, m["cols"], k[0]) for k, m in prep.items() if k[0] == c])
        rows.append(dict(chronos=c, n_series=sum(1 for k in prep if k[0] == c), mean_did=float(pt),
                         ci_lo=float(np.percentile(means, 2.5)), ci_hi=float(np.percentile(means, 97.5)), block=block))
    return pd.DataFrame(rows)


def run_robust(args) -> int:
    from pathlib import Path
    d = Path(args.dir); w = pd.read_csv(d / "gap_windows.csv"); s = pd.read_csv(d / "gap_summary.csv")
    pd.set_option("display.width", 200)
    outs = {"robust_reference": reference_sensitivity(w), "robust_event_split": event_split(s),
            "robust_cluster": cluster_boot(s), "robust_leave_one_out": leave_one_out(s)}
    if (d / "gap_origins.csv").exists():
        outs["robust_block"] = block_did(pd.read_csv(d / "gap_origins.csv"), block=args.block)
    else:
        print("(no gap_origins.csv: window-level bootstrap skipped; re-run `forecastclean gap` with the current code)")
    for k, v in outs.items():
        v.round(4).to_csv(d / f"{k}.csv", index=False); print(f"\n== {k}\n{v.round(3).to_string(index=False)}")
    return 0
