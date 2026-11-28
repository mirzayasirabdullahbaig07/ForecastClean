"""Regenerate every derived number table of the paper from the saved result files (no model runs).
Run from the repo root:  python paper/make_tables.py
Writes results/chronos_post_tuned3/skill_by_group.csv and results/gap_blocks/stable_subset.csv and prints them.
"""
from pathlib import Path

import numpy as np
import pandas as pd

root = Path(__file__).resolve().parent.parent
EVENT = ["wiki_Christmas", "wiki_Easter", "wiki_Halloween", "wiki_Thanksgiving", "wiki_Wimbledon", "wiki_SuperBowl", "wiki_Ramadan", "wiki_Eurovision"]

# Table 1: RQ1 skill by data group (mean log relative MASE vs naive over the series of each group)
d = pd.read_csv(root / "results/chronos_post_tuned3/summary.csv")
d["group"] = np.where(d.series.str.startswith("ecb"), "ECB FX (10)", np.where(d.series.str.startswith("neso"), "Electricity daily (1)",
             np.where(d.series.isin(EVENT), "Wikipedia event pages (8)", "Wikipedia other (6)")))
t1 = d.assign(l=np.log(d.rel_mase)).groupby(["group", "model"]).l.mean().unstack().round(3)
t1.to_csv(root / "results/chronos_post_tuned3/skill_by_group.csv"); print(t1.T.to_string(), "\n")

# Table 3: DiD over the 18 non-event series, both gap runs (bootstrap over series, seed 0)
rng = np.random.default_rng(0); rows = []
for run in ["gap_fixed", "gap_blocks"]:
    s = pd.read_csv(root / "results" / run / "gap_summary.csv"); s = s[~s.series.isin(EVENT)]
    for m, g in s.groupby("chronos"):
        x = g.did.to_numpy(); b = [rng.choice(x, len(x)).mean() for _ in range(5000)]
        rows.append(dict(run=run, model=m, n=len(x), mean_did=round(x.mean(), 3), lo=round(np.percentile(b, 2.5), 3), hi=round(np.percentile(b, 97.5), 3)))
t3 = pd.DataFrame(rows); t3.to_csv(root / "results/gap_blocks/stable_subset.csv", index=False); print(t3.to_string(index=False), "\n")

# run-to-run agreement of the per-series DiD (40-origin vs 20-origin run)
a = pd.read_csv(root / "results/gap_fixed/gap_summary.csv"); b = pd.read_csv(root / "results/gap_blocks/gap_summary.csv")
m = a.merge(b, on=["chronos", "series"], suffixes=("_40", "_20"))
print(m.groupby("chronos").apply(lambda g: g.did_40.corr(g.did_20), include_groups=False).round(2).rename("corr of per-series DiD, 40 vs 20 origins").to_string())

# Table 5: probabilistic accuracy (scaled CRPS relative to naive_q, log; and 80% coverage) by group
p = pd.read_csv(root / "results/prob/prob_summary.csv")
p["group"] = np.where(p.series.str.startswith("ecb"), "ECB FX (10)", np.where(p.series.str.startswith("neso"), "Electricity daily (1)",
             np.where(p.series.isin(EVENT), "Wikipedia event pages (8)", "Wikipedia other (6)")))
p["l"] = np.log(p.rel_scrps)
crps = p.groupby(["group", "model"]).l.mean().unstack().round(3); cov = p.groupby(["group", "model"]).cov80.mean().unstack().round(3)
crps.T.to_csv(root / "results/prob/crps_by_group.csv"); cov.T.to_csv(root / "results/prob/coverage_by_group.csv")
allm = p.groupby("model").agg(mean_log_rel_scrps=("l", "mean"), cov80=("cov80", "mean")).round(3).sort_values("mean_log_rel_scrps")
allm.to_csv(root / "results/prob/prob_overall.csv")
print("\nProbabilistic, mean log relative scaled CRPS by group:\n", crps.T.to_string(), "\n\ncoverage:\n", cov.T.to_string(), "\n\noverall:\n", allm.to_string())
