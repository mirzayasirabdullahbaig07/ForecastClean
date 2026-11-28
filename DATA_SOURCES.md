# Data sources — ForecastClean (Phase 3)

_Status 2026-11-25: **candidate list.** The download code is written and its cleaning logic is unit-tested on synthetic data, but it has **not been run against the live websites** (the sandbox it was written in has no internet). Run `forecastclean download` on your PC; results go to `data/raw/` (git-ignored) and `data/MANIFEST.csv` (commit this)._

## Candidate series (9 + your S&P 500)

| name | what | freq / season | source | licence / terms | status |
|---|---|---|---|---|---|
| fredmd_UNRATE | US unemployment rate (seasonally adjusted) | monthly / 1 | FRED-MD `current.csv` (St. Louis Fed; McCracken & Ng 2016, JBES 34(4)) | FRED Services terms apply (https://fred.stlouisfed.org/legal/terms_of_use.html); **not used in any reported result** (series end 2025) | downloaded, excluded |
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

## Licence check (2026-11-28, from the sources' own pages; the author should open each link once and confirm)

| source | terms found | what we must do |
|---|---|---|
| NESO Historic Demand | NESO Open Data Licence v1.0, based on Open Government Licence v3.0 with NESO amendments; each dataset is licensed individually (https://www.neso.energy/data-portal/ngeso-open-licence) | Include the attribution statement "Supported by National Energy SO Open Data". Confirmed 2026-11-28: the Historic Demand Data and Daily Demand Update dataset pages list the NESO Open Data Licence under Rights. |
| ECB exchange rates | Free reuse if the source is quoted (e.g. "Source: ECB statistics.") and the statistics (including metadata) are not modified; third-party data excluded (https://www.ecb.europa.eu/stats/ecb_statistics/governance_and_quality_framework/html/usage_policy.en.html) | Quote the source. We do not redistribute the raw series (`data/raw/` is git-ignored); only derived error tables are committed. |
| Wikipedia pageviews | Wikimedia states that all Analytics datasets are available under CC0 unless otherwise specified (https://download.wikipedia.com/legal.html); we read them from the Wikimedia Analytics REST API | Cite the Wikimedia Analytics API. No licence obstacle found. |
| FRED-MD | Series come from the St. Louis Fed (McCracken and Ng 2016); FRED Services terms apply | Not used in any reported result. If used later, cite McCracken and Ng (2016) and pin a dated vintage. |

**Data statement for the paper (draft):** "All series are public. Electricity demand: NESO Historic Demand Data (NESO Open Data Licence v1.0; Supported by National Energy SO Open Data). Exchange rates: ECB euro foreign exchange reference rates (Source: ECB statistics). Pageviews: Wikimedia Analytics API (CC0). Raw data is downloaded by `forecastclean download` and is not redistributed; data checksums are in `results/gap_fixed/MANIFEST_colab_2026-11-25.csv`."
