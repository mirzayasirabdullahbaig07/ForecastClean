# RQ1 with three foundation models and tuned baselines (laptop CPU, 2026-11-28)

Command: `forecastclean batch --chronos amazon/chronos-bolt-small amazon/chronos-2 google/timesfm-2.5-200m-pytorch --release-cutoff --post-only --max-origins 30 --tuned --only <25 series> --out results/chronos_post_tuned3`
Clean-from date 2025-10-31; data to 2026-11-27. Result CSVs: `summary.csv`, `stability_*.csv`; by-group means: `skill_by_group.csv`.

Mean log-relative MASE vs naive across 25 series (lower = better).

| model | mean log rel. MASE |
|---|---|
| timesfm-2.5-200m-pytorch | -0.470 |
| chronos-2 | -0.453 |
| chronos-bolt-small | -0.332 |
| theta | -0.036 |
| auto_theta | -0.035 |
| comb | -0.031 |
| seasonal_naive | -0.024 |
| auto_ets | -0.006 |
| naive | 0.000 |
| arima | 0.000 |
| drift | 0.012 |
| ets | 0.017 |

auto_arima not ranked (non-seasonal series only). Ranking stability: P(best stays best)=0.69, mean Kendall tau=0.77.
