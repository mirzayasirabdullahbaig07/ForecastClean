# Tuned-baseline run (Colab, 2026-11-27, commit e7dc9ee)

Command: `forecastclean batch --chronos amazon/chronos-bolt-small amazon/chronos-2 --release-cutoff --post-only --max-origins 30 --tuned --only <25 series> --out results/chronos_post_tuned`

Mean log-relative MASE vs naive across 25 series (lower = better). Transcribed from the printed Colab output; CSVs not yet saved.

| model | mean log rel. MASE |
|---|---|
| chronos-2 | -0.453 |
| chronos-bolt-small | -0.332 |
| theta | -0.036 |
| auto_theta | -0.035 |
| comb | -0.031 |
| seasonal_naive | -0.024 |
| auto_ets | -0.006 |
| arima | -0.000 |
| naive | 0.000 |
| drift | 0.012 |
| ets | 0.018 |

auto_arima not ranked (non-seasonal series only). Ranking stability: P(best stays best)=1.00, mean Kendall tau=0.73.
