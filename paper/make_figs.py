"""The figures of the paper except the skill bar chart (made by make_fig1.py). Run from the repo root:  python paper/make_figs.py
The heatmap, probabilistic and hourly figures read the saved CSV files; the forest plot uses the numbers printed in Tables 4, 4b and the 20-origin run (Section 5.2)."""
from pathlib import Path
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch
import pandas as pd

root = Path(__file__).resolve().parent.parent
out = root / "paper/figures"; out.mkdir(exist_ok=True)
FM, CL, ACC = "#2a78d6", "#c4c2b6", "#d9622b"
NM = {"timesfm-2.5-200m-pytorch": "TimesFM 2.5", "chronos-2": "Chronos-2", "chronos-bolt-small": "Chronos-Bolt-small"}
plt.rcParams.update({"font.size": 10, "axes.spines.top": False, "axes.spines.right": False})

def box(ax, x, y, w, h, text, fc="#eef3fb", ec=FM):
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.02", fc=fc, ec=ec, lw=1.2))
    ax.text(x + w / 2, y + h / 2, text, ha="center", va="center", fontsize=9)
def arrow(ax, x1, y1, x2, y2):
    ax.annotate("", xy=(x2, y2), xytext=(x1, y1), arrowprops=dict(arrowstyle="->", color="#555", lw=1.2))

# Figure 2: protocol flowchart
fig, ax = plt.subplots(figsize=(9, 4.4)); ax.set_xlim(0, 10); ax.set_ylim(0, 5); ax.axis("off")
box(ax, 0.1, 3.4, 2.2, 1.1, "26 public series\n(electricity, FX,\nWikipedia pageviews)")
box(ax, 2.9, 3.4, 2.2, 1.1, "Rolling origins\ncontext 1024, no look-ahead\n(asserted in code)")
box(ax, 5.7, 3.4, 2.0, 1.1, "12 forecasters\n9 classical (3 tuned)\n+ 3 foundation")
box(ax, 8.1, 3.4, 1.8, 1.1, "MASE, relative\nto naive (log)")
for a, b in [(2.3, 2.9), (5.1, 5.7), (7.7, 8.1)]: arrow(ax, a, 3.95, b, 3.95)
box(ax, 0.6, 1.2, 3.8, 1.3, "RQ1  clean-data skill\nonly windows after the latest release date\n(clean-from 2025-10-31)", fc="#eaf6ee", ec="#3a8a55")
box(ax, 5.2, 1.2, 4.2, 1.3, "RQ2  contamination gap\nDiD = gap(foundation) - median gap(classical)\ngap = log relMASE after - before release", fc="#fdf0e8", ec=ACC)
arrow(ax, 9.0, 3.4, 3.2, 2.5); arrow(ax, 9.0, 3.4, 7.3, 2.5)
ax.text(5, 0.5, "Robustness: reference variants, event / non-event split, cluster and block bootstrap, leave-one-out, calendar-matched and 2023 pre-periods", ha="center", fontsize=8.5, color="#444")
ax.set_title("Evaluation protocol", loc="left", fontsize=11)
fig.tight_layout(); fig.savefig(out / "fig2_protocol.png", dpi=200); plt.close(fig)

# Figure 3: timeline
fig, ax = plt.subplots(figsize=(9.5, 3.8))
ax.set_ylim(-2.2, 2.0); ax.set_xlim(2015, 2027.2); ax.set_yticks([]); ax.spines["left"].set_visible(False)
ax.barh(0, 2025.83 - 2015.5, left=2015.5, height=0.5, color=CL); ax.text(2016, 0.45, "pre-release windows (origins from 2015)", fontsize=8.5)
ax.barh(0, 2026.9 - 2025.83, left=2025.83, height=0.5, color=FM); ax.text(2025.95, 0.45, "clean", fontsize=9, color=FM)
ax.barh(-0.6, 1.0, left=2023.0, height=0.4, color=ACC); ax.text(2022.9, -0.6, "Table 4b pre-period (2023)", fontsize=8.5, color=ACC, ha="right", va="center")
ax.axvline(2024.0, color=ACC, ls="--", lw=1.2); ax.text(2023.95, 1.5, "TimesFM corpus ends late 2023 (as cited)", ha="right", fontsize=8.5, color=ACC)
ev = [("Chronos-Bolt-small, 1 Dec 2024", 2024.92, -1.2, "right"), ("TimesFM 2.5, 3 Oct 2025", 2025.76, -1.6, "right"), ("Chronos-2, 31 Oct 2025", 2025.83, -2.0, "left")]
for n, x, yv, ha in ev:
    ax.plot([x, x], [0.25, yv], color="#333", lw=1); ax.plot(x, 0.25, "o", color="#333", ms=4)
    ax.text(x - 0.08 if ha == "right" else x + 0.08, yv, n, ha=ha, va="center", fontsize=8.5)
ax.set_title("Release dates, the clean period, and the 2023 pre-period of Table 4b", loc="left", fontsize=11)
fig.tight_layout(); fig.savefig(out / "fig3_timeline.png", dpi=200); plt.close(fig)

# Figure 4: skill by data group (heatmap)
g = pd.read_csv(root / "results/chronos_post_tuned3/skill_by_group.csv").set_index("group")
cols = ["timesfm-2.5-200m-pytorch", "chronos-2", "chronos-bolt-small", "theta", "auto_theta", "comb", "seasonal_naive", "auto_ets", "ets", "drift", "arima"]
lab = ["TimesFM 2.5", "Chronos-2", "Chronos-Bolt-small", "Theta", "AutoTheta", "Comb", "Seasonal naive", "AutoETS", "ETS", "Drift", "ARIMA"]
d = g[cols]
fig, ax = plt.subplots(figsize=(9.5, 3.4))
im = ax.imshow(d.values.astype(float), cmap="Blues_r", vmin=-1.1, vmax=0.1, aspect="auto")
ax.set_xticks(range(len(cols)), lab, rotation=35, ha="right"); ax.set_yticks(range(len(d)), d.index)
for i in range(d.shape[0]):
    for j in range(d.shape[1]):
        v = d.values[i, j]
        if v == v: ax.text(j, i, f"{v:+.2f}".replace("-", "−"), ha="center", va="center", fontsize=8, color="white" if v < -0.5 else "black")
for s in ax.spines.values(): s.set_visible(False)
ax.set_title("Mean log-relative MASE vs naive by data group (lower = better)", loc="left", fontsize=11)
fig.tight_layout(); fig.savefig(out / "fig4_skill_by_group.png", dpi=200); plt.close(fig)

# Figure 5: DiD across designs (forest)
D = [("20 origins, all 26 series", [("Chronos-Bolt-small", -0.191, -0.457, 0.020), ("Chronos-2", -0.226, -0.414, -0.049), ("TimesFM 2.5", -0.097, -0.270, 0.050)]),
     ("Matched ±365 days, 8 event pages", [("Chronos-Bolt-small", -0.411, -0.647, -0.150), ("Chronos-2", -0.415, -0.830, -0.044), ("TimesFM 2.5", -0.402, -0.739, -0.048)]),
     ("Pre-period 2023, 8 event pages", [("Chronos-Bolt-small", -0.436, -0.722, -0.171), ("Chronos-2", -0.479, -0.812, -0.160), ("TimesFM 2.5", -0.435, -0.753, -0.104)])]
fig, ax = plt.subplots(figsize=(8.5, 4.6)); y = 0; ticks = []; labs = []
cmap = {"Chronos-Bolt-small": "#7aa9e6", "Chronos-2": FM, "TimesFM 2.5": "#16407a"}
for title, rows in D:
    ax.text(-0.9, y - 0.2, title, fontsize=9, weight="bold", ha="left"); y += 0.8
    for n, m, lo, hi in rows:
        ax.plot([lo, hi], [y, y], color=cmap[n], lw=2.2); ax.plot(m, y, "o", color=cmap[n])
        ticks.append(y); labs.append(n); y += 0.7
    y += 0.5
ax.axvline(0, color="#444", lw=1); ax.set_yticks(ticks, labs); ax.invert_yaxis(); ax.set_xlim(-0.9, 0.3)
ax.set_xlabel("mean DiD with 95% interval over series (positive = leakage-like)")
ax.text(0.02, ax.get_ylim()[1] - 0.1, "leakage-like ->", fontsize=8.5, color=ACC)
ax.set_title("The mean contamination gap is negative in every design", loc="left", fontsize=11, pad=22)
fig.tight_layout(); fig.savefig(out / "fig5_did_forest.png", dpi=200); plt.close(fig)

# Figure 6: probabilistic accuracy
p = pd.read_csv(root / "results/prob/prob_overall.csv").set_index("model")
order = ["chronos-2", "timesfm-2.5-200m-pytorch", "chronos-bolt-small", "theta_q", "seasonal_naive_q", "naive_q"]
nm2 = {**NM, "theta_q": "Theta (empirical quantiles)", "seasonal_naive_q": "Seasonal naive (q)", "naive_q": "Naive (q)"}
p = p.reindex([m for m in order if m in p.index])
if "naive_q" not in p.index: p.loc["naive_q"] = [0.0, 0.797]
fig, (a, b) = plt.subplots(1, 2, figsize=(10, 3.6), sharey=True)
yy = range(len(p)); cc = [FM if m in NM else CL for m in p.index]
a.barh(list(yy), p.mean_log_rel_scrps, color=cc); a.set_yticks(list(yy), [nm2[m] for m in p.index]); a.invert_yaxis()
a.set_xlabel("mean log scaled CRPS vs naive (lower = better)"); a.axvline(0, color="#666", lw=0.8)
b.barh(list(yy), p.cov80, color=cc); b.axvline(0.8, color=ACC, ls="--"); b.set_xlim(0.6, 0.9); b.set_xlabel("coverage of the 80% interval (target 0.80)")
for i, v in enumerate(p.cov80): b.text(v + 0.003, i, f"{v:.3f}", va="center", fontsize=8.5)
fig.suptitle("Probabilistic accuracy and calibration, 25 series", x=0.01, ha="left", fontsize=11)
fig.tight_layout(); fig.savefig(out / "fig6_probabilistic.png", dpi=200); plt.close(fig)

# Figure 7: hourly electricity before/after
w = pd.read_csv(root / "results/gap_blocks/gap_windows.csv"); h = w[(w.series == "neso_demand_hourly") & (w.chronos == "chronos-2")].set_index("model")
meth = [("chronos-2", "Chronos-2"), ("theta", "Theta"), ("seasonal_naive", "Seasonal naive"), ("comb", "Comb"), ("ets", "ETS")]
fig, ax = plt.subplots(figsize=(7.5, 3.8)); xs = range(len(meth))
ax.bar([x - 0.2 for x in xs], [h.loc[m, "rel_pre"] for m, _ in meth], 0.4, color=CL, label="before release")
ax.bar([x + 0.2 for x in xs], [h.loc[m, "rel_post"] for m, _ in meth], 0.4, color=FM, label="after release")
ax.set_xticks(list(xs), [n for _, n in meth]); ax.set_ylabel("relative MASE vs naive (lower = better)"); ax.legend(frameon=False)
ax.set_title("Hourly electricity: the foundation model stays far ahead", loc="left", fontsize=11)
fig.tight_layout(); fig.savefig(out / "fig7_hourly.png", dpi=200); plt.close(fig)
print("wrote figures 2-7")
