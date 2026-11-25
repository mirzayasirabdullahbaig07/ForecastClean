# Data sources — ForecastClean (Phase 3)

_Status 2026-11-25: **candidate list.** The download code is written and its cleaning logic is unit-tested on synthetic data, but it has **not been run against the live websites** (the sandbox it was written in has no internet). Run `forecastclean download` on your PC; results go to `data/raw/` (git-ignored) and `data/MANIFEST.csv` (commit this)._

## Candidate series (9 + your S&P 500)

| name | what | freq / season | source | licence / terms | status |
|---|---|---|---|---|---|
| fredmd_UNRATE | US unemployment rate (seasonally adjusted) | monthly / 1 | FRED-MD `current.csv` (St. Louis Fed; McCracken & Ng 2016, JBES 34(4)) | ⚠ confirm FRED terms of use | to download |
| fredmd_CPIAUCSL | US CPI, all items (seasonally adjusted) | monthly / 1 | FRED-MD | ⚠ confirm | to download |
| fredmd_INDPRO | US industrial production (seasonally adjusted) | monthly / 1 | FRED-MD | ⚠ confirm | to download |
| neso_demand_daily | GB national demand (ND), daily mean MW | daily / 7 | NESO Historic Demand Data (CKAN API, package `8f2fe0af-…`) | **NESO Open Data Licence** (shown on the NESO portal) — read it for attribution terms | to download |
| neso_demand_hourly | same, hourly mean | hourly / 24 | NESO | same | to download (approximate on 2 clock-change days/year) |
| ecb_EURUSD | EUR/USD reference rate | business-daily / 1 | ECB Data Portal (SDMX CSV) | ⚠ confirm ECB reuse/attribution policy | to download |
| ecb_EURGBP | EUR/GBP reference rate | business-daily / 1 | ECB | ⚠ confirm | to download |
| wiki_Python | en.wikipedia pageviews, `Python_(programming_language)` | daily / 7 | Wikimedia REST API (from 2015-07) | ⚠ confirm Wikimedia terms | to download |
| wiki_Christmas | en.wikipedia pageviews, `Christmas` | daily / 7 | Wikimedia REST API | ⚠ confirm | to download |
| sp500 (yours) | S&P 500 close from your coursework | daily | your existing file | ⚠ market-data vendor terms usually forbid redistribution — **keep it out of GitHub** | you have it |

"⚠ confirm" = I did not verify the licence. Do this before the paper's data statement: open each source's terms page, copy the licence name + link into this table.

## Why these (selection logic)
- **Coverage through 2026** so there are windows *after* models' training cutoffs (needed for the pre/post comparison).
- **Mix of behaviour:** strongly seasonal (energy, web traffic, monthly macro) and near-random-walk (FX, RQ4).
- **Public, easily downloadable** (same rule you set for SplitAudit).

## Contamination notes to verify (from search snippets, not read in full)
- Chronos-2 maintainers say FRED-MD was **not** used in Chronos-2 training; the training datasets are in its paper's Table 6 (GitHub discussion #358 on amazon-science/chronos-forecasting).
- A realized-volatility paper's table lists Chronos-Bolt's corpus as including `exchange_rate` and `FRED-MD` (arXiv 2607.05291). If both hold, **FRED-MD/FX series are known-seen for Chronos-Bolt but not for Chronos-2** — a natural comparison for RQ2. Verify both claims at the primary sources before using them.

## Reproducibility
- `data/MANIFEST.csv` stores URL, retrieval time (UTC), row count, first/last date and SHA-256 per file.
- FRED-MD `current.csv` is replaced monthly: record the retrieval date; for the paper, pin a dated vintage (e.g. `2026-xx.csv`) instead of `current.csv`.

## Download results (2026-11-25)
All 9 downloaded. Coverage: FRED-MD 1959→**2025-08/09** (only through 2025 despite a Nov-2026 download — try a newer dated vintage with `--fred-vintage`); NESO 2001→2026-11-03; ECB 2000→2026-11-24; Wikipedia 2015-07→2026-11-23. Macro series therefore cannot provide windows after 2025.
