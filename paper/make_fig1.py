"""Figure 1 of the paper: mean log-relative MASE vs naive (RQ1, 25 series, windows after 2025-10-31).
Values are read from results/chronos_post_tuned3/RESULT_TABLE.md (transcribed from the printed table, saved in RESULT_TABLE.md).
Run from the repo root:  python paper/make_fig1.py
"""
import re
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

root = Path(__file__).resolve().parent.parent
rows = re.findall(r"^\|\s*([a-z0-9.\-_]+)\s*\|\s*(-?\d+\.\d+)\s*\|\s*$", (root / "results/chronos_post_tuned3/RESULT_TABLE.md").read_text(), re.M)
NAMES = {"timesfm-2.5-200m-pytorch": "TimesFM 2.5", "chronos-2": "Chronos-2", "chronos-bolt-small": "Chronos-Bolt-small", "theta": "Theta", "auto_theta": "AutoTheta (tuned)",
         "comb": "Comb", "seasonal_naive": "Seasonal naive", "auto_ets": "AutoETS (tuned)", "arima": "ARIMA(1,1,1)", "naive": "Naive",
         "drift": "Drift", "ets": "ETS"}
data = sorted(((NAMES[m], float(v), m.startswith(("chronos", "timesfm"))) for m, v in rows if m in NAMES), key=lambda t: t[1])
assert len(data) == 12, data

fig, ax = plt.subplots(figsize=(8, 4.6))
y = range(len(data))
ax.barh(list(y), [v for _, v, _ in data], color=["#2a78d6" if f else "#c4c2b6" for _, _, f in data], height=0.65)
ax.set_yticks(list(y), [n for n, _, _ in data]); ax.invert_yaxis()
ax.axvline(0, color="#666", lw=0.8); ax.set_xlabel("mean log-relative MASE vs naive (lower is better)")
for i, (_, v, _) in enumerate(data):
    ax.text(0.03, i, f"{v:+.3f}".replace("-", "−") if v else "0.000", va="center", ha="left", fontsize=9)
ax.set_xlim(-0.5, 0.09)
ax.set_title("Foundation models cut error vs naive by 28–37%; the best classical method by 4%", fontsize=11, loc="left")
for s in ("top", "right"):
    ax.spines[s].set_visible(False)
fig.tight_layout(); out = root / "paper/figures/fig1_rq1_skill.png"; fig.savefig(out, dpi=200); print("wrote", out)
