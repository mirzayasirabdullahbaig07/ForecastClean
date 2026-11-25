# Roadmap — ForecastClean (8 weeks, ~2–3 h/day)
Definition of done: preprint with an open protocol, ≥6 real series, ≥2 foundation models, contamination analysis, ranking-stability analysis.

## Week 1 — Literature + setup
- **D1** Tests + `simulate`. Re-derive MASE and the DM statistic by hand on 5 numbers.
- **D2** Read Meyer et al. (arXiv:2510.13654) fully. Note the two leakage types they define.
- **D3** Skim TSFMAudit (2605.26161) and TimesX (2607.06973); note their series, cutoffs, and what they do NOT do.
- **D4** Gap statement. Suggested angle: transparent small-scale protocol + ranking stability + relative-skill contamination gap on user-chosen series. Verify it is not already done.
- **D5** Choose 6–10 series with licences OK: e.g. S&P 500 (you already have), 2 energy/electricity, 2 macro (CPI, unemployment), 2 retail/web traffic. Record source + licence.
- **D6–7** Introduction draft.

## Week 2 — Pipeline on real data
- **D8–9** Load series; classical baselines on all; check plots by eye.
- **D10** Install `chronos-forecasting`; run Chronos-bolt-tiny on one series; compare with your own sanity check.
- **D11** Add Chronos-bolt-small + a second family (e.g. TimesFM or Moirai if it installs).
- **D12–14** Record each model's documented training cutoff (with link) in a table.

## Weeks 3–4 — Experiments
All models × all series × horizons {1, 12 or seasonal cycle}. Save every forecast. Compute relative MASE, DM tests with multiple-comparison control (Holm), pre/post split.

## Week 5 — RQ2/RQ3
Contamination gap with bootstrap CI over origins; ranking stability via re-evaluating on 100 random subsets of windows (Kendall tau between rankings).

## Week 6 — Extensions
Add probabilistic metric (CRPS or weighted quantile loss); a "return series" analysis for RQ4.

## Week 7 — Writing · Week 8 — Release
Zenodo, arXiv, supervisor feedback.

## Go / no-go gates
- End Week 2: cannot get any foundation model running? Fall back to an all-classical + deep-baseline study (N-BEATS via a library) of **evaluation protocol sensitivity** — still publishable as methodology.
- End Week 5: no contamination gap anywhere? Report it as a null result with CIs.

## Paper outline
1 Introduction · 2 Related work · 3 Protocol (rolling origin, relative skill, contamination split) · 4 Data & models · 5 Results (RQ1–4) · 6 Discussion · 7 Limitations · 8 Conclusion.
