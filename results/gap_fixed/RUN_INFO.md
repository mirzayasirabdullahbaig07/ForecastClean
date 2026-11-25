# results/gap_fixed — corrected contamination-gap run (RQ2)

| | |
|---|---|
| Date | 2026-11-25 (Colab, T4 GPU) |
| Code | commit `8c4247d` (equal context length before/after release) |
| Command | `forecastclean gap --chronos amazon/chronos-bolt-small amazon/chronos-2 --max-origins 40 --drop arima --out results/gap_fixed` |
| Models | Chronos-Bolt-small (release cutoff 2024-12-01), Chronos-2 (2025-10-31) — release dates, NOT published training cutoffs |
| Series | 29 downloaded; 3 FRED-MD series skipped (no post-release windows) → 26 used (10 ECB FX, 14 Wikipedia, 2 NESO) |
| Data | `MANIFEST_colab_2026-11-25.csv` (checksums of the exact data used; ECB/Wikipedia end 2026-11-25/24) |
| Windows | 40 pre-release, 26–40 post-release per series; context capped at 1024 for every window |
| Classical reference set | naive is the scoring reference; the "classical" median uses ETS, Theta, Comb, drift, seasonal-naive (ARIMA dropped for speed) |

## Files
- `gap_aggregate.csv` — mean / median DiD per model and group, bootstrap-over-series 95% interval (the headline table)
- `gap_summary.csv` — one row per model × series: Chronos gap, classical median gap, DiD, windows
- `gap_windows.csv` — per model × series × period relative MASE (`rel_pre`, `rel_post`) and `gap = log rel_post − log rel_pre`
- `MANIFEST_colab_2026-11-25.csv` — data provenance

## How to read it
DiD > 0 means the Chronos model lost MORE skill after its release than the classical models did (leakage-like). Result: no
consistent leakage signature (see `EXPERIMENT_LOG.md`). **Preliminary:** release dates are conservative guesses, baselines are
untuned, and the bootstrap treats correlated series (EUR crosses, Wikipedia pages) as independent.
