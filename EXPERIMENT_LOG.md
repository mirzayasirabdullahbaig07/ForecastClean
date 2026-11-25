# Experiment log

| date | command | seed | data version | result | next step |
|---|---|---|---|---|---|
| 2026-11-25 | `python -m pytest -q` | n/a | synthetic | 6 passed | start Phase 2 (literature) |
| 2026-11-25 | `python -m pytest -q` (after adding data module) | n/a | synthetic | 12 passed | run `forecastclean download` on PC |
| 2026-11-25 | `forecastclean simulate` | 0 | synthetic seasonal (n=240) | pipeline runs; ETS/seasonal-naive beat naive as expected (pipeline check only, NOT a finding) | choose real series |
| 2026-11-25 | `forecastclean download` (user's PC) | n/a | 9 series, retrieved 2026-11-25 (see data/MANIFEST.csv) | all 9 OK. FRED-MD ends 2025-08/09 (stale/short); NESO to 2026-11-03; ECB to 2026-11-24; Wikipedia to 2026-11-23 | find newer FRED-MD vintage |
| 2026-11-25 | `forecastclean batch` v1 (user's PC) | n/a | as above | **SUPERSEDED**: used season=12 on seasonally adjusted macro, season=5 on FX and a seasonal-naive reference, so relative-MASE and DM tests were against a meaningless reference | fixed seasons + reference (naive) |
| 2026-11-25 | `forecastclean batch` v2 (sandbox re-run on user's data) | n/a | as above | sanity checks pass: FX ≈1.00 vs naive for every model (nothing beats naive, as expected); seasonal series won by seasonal methods (Theta/ETS/seasonal-naive). Across-series (9) best=Theta, P(best stays best)=0.86, tau=0.74. Macro only 10 windows at h=12 → changed to h=6. **Preliminary, not a finding** | user re-runs batch; then Chronos |
| 2026-11-25 | `pytest` (adapter fixed) | n/a | synthetic | 17 passed; Chronos adapter checked against chronos-forecasting 2.3.2 source (positional input; Bolt returns a tensor, Chronos-2 a list) with stand-in pipelines — **no real weights run** | run notebooks/chronos_colab.ipynb |

## Data sources (fill in during Phase 3)
| series | source URL | licence | frequency | season | notes |
|---|---|---|---|---|---|

## Foundation-model training cutoffs (fill in during Phase 4)
| model | documented cutoff | link / evidence |
|---|---|---|
| amazon/chronos-bolt-tiny (and Bolt family) | **not stated** — card says "nearly 100 billion" observations, datasets not named; licence Apache-2.0 | https://huggingface.co/amazon/chronos-bolt-tiny |
| amazon/chronos-2 | **no explicit date.** Maintainers: only datasets in Table 6 of arXiv 2510.15821 were used; FRED-MD is not among them; M4 data predates 2018 | https://github.com/amazon-science/chronos-forecasting/discussions/358 |
