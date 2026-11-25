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
| 2026-11-25 | `forecastclean batch` v2 (user's PC) | n/a | as above | reproduces the sandbox run (same numbers on non-macro series); macro h=6 → 21 windows each; across-series best=Theta, P(best stays best)=0.82, tau=0.74; FX all ≈1.00 vs naive (consistent with 2609.10357's "all methods tied on exchange rates"). Preliminary | run Chronos on Colab |
| 2026-11-25 | `forecastclean batch --clean-from 2025-10-31 --post-only --horizon-sweep --max-origins 50` (sandbox, user's data, classical models only) | n/a | as above | 6 series have post-release windows (3 FRED-MD series end 2025 → none). Windows per horizon: 50 (short) down to 13 (long). Across-series (6): best at shortest horizon = naive (tau 0.87), best at longer horizons = Theta (P(best stays best) 0.90 / 0.96 / 0.65 for the 3 longer horizons; tau 0.75–0.80). Kendall tau between consecutive horizons' rankings: seasonal series 0.54–0.81; **FX ≈ 0 or negative** (EURUSD −0.13, EURGBP 0.26) = classical models indistinguishable, ranking is noise. Long horizons have only 13 windows → low power. **Preliminary; no foundation model yet** | run Colab cell 4b with Chronos |

## Data sources (fill in during Phase 3)
| series | source URL | licence | frequency | season | notes |
|---|---|---|---|---|---|

## Foundation-model training cutoffs (fill in during Phase 4)
| model | documented cutoff | link / evidence |
|---|---|---|
| amazon/chronos-bolt-tiny (and Bolt family) | **not stated** — card says "nearly 100 billion" observations, datasets not named; licence Apache-2.0 | https://huggingface.co/amazon/chronos-bolt-tiny |
| *release-date cutoffs we use (conservative)* | Bolt 2024-12-01, TimesFM 2.5 2025-09-15, Chronos-2 2025-10-31 | see LITERATURE.md §6 / registry.py |
| amazon/chronos-2 | **no explicit date.** Maintainers: only datasets in Table 6 of arXiv 2510.15821 were used; FRED-MD is not among them; M4 data predates 2018 | https://github.com/amazon-science/chronos-forecasting/discussions/358 |
