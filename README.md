# Project C — ForecastClean
**Do pretrained time-series foundation models really beat classical forecasters once you evaluate only on data they could not have seen?**

Repo: https://github.com/mirzayasirabdullahbaig07/ForecastClean · Local: `C:\Users\HP\Downloads\ForecastClean`

---

## 📊 Project progress — where we are right now

**Overall: 33% ▓▓▓▓▓▓░░░░░░░░░░░░░░ (target: research-paper preprint)**
_Last updated: 2026-11-25 · Current phases: **Phase 2 — Literature** (notes: [`LITERATURE.md`](LITERATURE.md)) and **Phase 3 — Data** (sources: [`DATA_SOURCES.md`](DATA_SOURCES.md)) and **Phase 4 — real-data pipeline**_

| # | Phase | Weight | Done | Contribution | Status |
|---|---|---:|---:|---:|---|
| 1 | Framework + tests (rolling origin, MASE, DM test, 5 baselines, CLI) | 15% | 100% | 15% | ✅ Done (6/6 tests pass, `simulate` runs) |
| 2 | Literature review + gap statement | 10% | 40% | 4% | 🔄 **In progress** — arXiv IDs verified, gap options A/B/C written; full reading of 2510.13654 + 2609.10357 and final gap choice pending |
| 3 | Choose 6–10 real series (source + licence recorded) | 10% | 70% | 7% | 🔄 **Mostly done** — all 9 series downloaded (2026-11-25) and manifest saved; **licences still to confirm**; macro series end 2025 (see agenda) |
| 4 | Real-data pipeline + Chronos adapter tested | 10% | 55% | 5.5% | 🔄 **In progress** — classical baselines run on 9 real series; Chronos adapter fixed against the library source + stand-in tests + Colab notebook `notebooks/chronos_colab.ipynb`; **real Chronos run still to do (you, on Colab)** |
| 5 | Main experiments (all models × series × horizons) | 20% | 0% | 0% | ⬜ Not started |
| 6 | RQ2 contamination gap + RQ3 ranking stability | 10% | 15% | 1.5% | 🔄 Code ready (bootstrap ranking stability, Holm correction, pre/post split); needs real results + CIs for the gap |
| 7 | Extensions (CRPS/WQL, RQ4 return series) | 5% | 0% | 0% | ⬜ Not started |
| 8 | Paper writing (8 sections) | 15% | 0% | 0% | ⬜ Not started |
| 9 | Release (Zenodo, arXiv, supervisor feedback) | 5% | 0% | 0% | ⬜ Not started |
| | **Total** | **100%** | | **33%** | |

Overall % = sum of (weight × done). Update the "Done" column when a phase moves, then recompute.

### 🎯 Agenda — what we do next (in order)
1. **Literature (Phase 2, in progress):** arXiv IDs verified. Still to do: read Meyer et al. (2510.13654) and the closest competitor *"A Later Test Set Is Not a New Domain"* (2609.10357) in full, then confirm gap statement A/B/C in `LITERATURE.md` (working assumption: **A**, ranking stability + protocol). **Novelty warning:** post-cutoff evaluation is already crowded.
2. ~~Get the data (Phase 3)~~ ✅ downloaded 2026-11-25 (9 series, `data/MANIFEST.csv`). Licences in `DATA_SOURCES.md` still to confirm.
3. **Re-run the batch after the design fixes (Phase 4):** `forecastclean batch` (≈7 min). Then plot 3–4 series by eye and check the forecasts look sane.
4. **Fix the macro data end-date (Phase 3):** FRED-MD `current.csv` ended at 2025-08/09 although downloaded in Nov 2026. Open the St. Louis Fed FRED-MD page, find the newest monthly vintage file, then `forecastclean download --only fredmd_UNRATE fredmd_CPIAUCSL fredmd_INDPRO --fred-vintage <YYYY-MM>`.
5. **Run Chronos on Colab (Phase 4):** open `notebooks/chronos_colab.ipynb`, run cells 1–3 (smoke test), then 4–5. Send me any error. **Heads-up:** Chronos's training cutoff is not published (see `EXPERIMENT_LOG.md`), so the date-based RQ2 split needs a rethink — decide with me after the run.
6. **Then** the full experiment grid (Phase 5) — needs each model's documented cutoff first.

### 🚦 Go / no-go gates
- End of Phase 4: no foundation model runs at all → fall back to an all-classical + deep-baseline study of *evaluation-protocol sensitivity*.
- End of Phase 6: no contamination gap anywhere → report it as a null result with CIs.

### ✅ Honest status of what is verified
- Verified (17 tests run 2026-11-25): forecasters, MASE scaling, no look-ahead, DM-test behaviour, seasonal-vs-random-walk sanity, pre/post cutoff labels, the data-cleaning functions, Holm correction and ranking-stability bootstrap (all on synthetic inputs).
- **Preliminary only:** classical-baseline results on 9 real series exist (see `EXPERIMENT_LOG.md`) but are sanity checks, not findings.
- **Not verified:** the Chronos adapter with real weights (tested only with stand-in pipelines); any foundation-model result (none exist yet); licences of the data sources.

---

## 1. Why this project
It extends your time-series coursework (ARIMA on S&P 500) into a research question. Literature flags that foundation-model (TSFM) benchmarks risk **information leakage** — pretraining data overlapping with test series or periods (Meyer et al., arXiv:2510.13654), and contamination audits are emerging (TSFMAudit, arXiv:2605.26161). Post-cutoff benchmarks already exist (e.g. TimesX, arXiv:2607.06973, a multimodal benchmark; arXiv:2609.10357), so our contribution must go beyond "evaluate after the cutoff" — see `LITERATURE.md`. A rigorous, small-scale, *transparent* evaluation protocol on real series that *you choose* (financial, energy, macro) with proper statistical tests is feasible on a CPU.

## 2. Research questions
- **RQ1** Skill of each model vs a seasonal-naive/naive reference (relative MASE, Diebold–Mariano tests) on your series.
- **RQ2** **Contamination gap:** is a foundation model's skill better on windows *before* its training cutoff than *after*? (A gap is evidence of leakage or memorisation.)
- **RQ3** How sensitive are model rankings to the choice of evaluation window / horizon / series? (Ranking stability.)
- **RQ4** On near-random-walk series (e.g. daily returns), does anything beat naive? (Expected: no — a useful null baseline.)

## 3. Design choices and why
| Choice | Reason |
|---|---|
| Rolling-origin evaluation with an asserted no-look-ahead | The standard in forecasting; a test spies on the context passed to each model |
| MASE and relative MASE vs a reference | Scale-free, comparable across series; avoids MAPE pathologies |
| Diebold–Mariano with Harvey correction | The standard test for equal forecast accuracy; tested for ≈5% false positives under H0 |
| Pre/post-cutoff period labels | Operationalises the leakage question; only "post" windows are clean |
| Classical set: naive, seasonal naive, drift, ETS, ARIMA, Theta, Comb(ETS+ARIMA+Theta) | Cheap baselines; combinations are hard to beat in forecasting competitions. ⚠ Our ETS/ARIMA are **not tuned** (ARIMA is fixed (1,1,1)) — fix before claiming foundation models beat "strong" classical methods |
| Single reference: **naive** for every series | A seasonal-naive reference is meaningless on non-seasonal series. `season` is 1 for seasonally adjusted FRED-MD series and FX; real seasonality only for energy/web traffic |
| Score only windows with target start ≥ `--eval-start` (default 2015-01-01), non-overlapping, ≤150 evenly thinned origins | Concentrates on recent windows around/after model cutoffs; keeps windows independent for the DM test |
| Chronos adapter behind an optional import | Keeps the core runnable with no downloads |

## 4. Quick start
```bash
pip install -e ".[dev]" && python -m pytest -q     # 17 tests
forecastclean download                               # fetch + clean real series -> data/raw/*.csv, data/MANIFEST.csv
forecastclean batch                                  # all series in data/raw -> results/batch/
forecastclean run --csv data/raw/fredmd_UNRATE.csv --date-col date --value-col value --h 12 --season 12 --out results/unrate
pip install -e . pytest && python -m pytest -q
forecastclean simulate                                   # synthetic pipeline check
forecastclean run --csv sp500.csv --date-col Date --value-col Close --h 21 --returns --out results/sp500
# with a foundation model (Colab/laptop, internet for weights):
pip install chronos-forecasting torch
forecastclean run --csv energy.csv --h 24 --season 24 --cutoff 2024-01-01 --chronos amazon/chronos-bolt-tiny
```
Get the model's true training cutoff from its model card — do not guess.

## 5. What is verified / not (detail)
Verified: forecasters, MASE scaling, no look-ahead, DM-test behaviour (identical → p=1; constant gap → p=0; ≈5% false positives under H0), seasonal models beat naive on seasonal data and nothing beats naive on a pure random walk, pre/post labelling. (The test suite caught a real DM edge-case bug during development.)
Not verified: the Chronos adapter and real-data findings.

## 6. Limitations
Univariate only; point forecasts (no probabilistic scores yet — add CRPS/WQL in v2); a single cutoff per model; "pre-cutoff gap" is *evidence of* leakage, not proof (series may simply be easier earlier — use the classical reference to control, which is why skill is relative).

See `ROADMAP.md`.

## 7. Git workflow (VS Code terminal)
```powershell
git add .
git commit -m "describe what changed"
git push
```
Update the progress table above whenever a phase moves, and commit it together with the work.
