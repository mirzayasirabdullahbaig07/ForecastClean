# Project C — ForecastClean
**Do pretrained time-series foundation models really beat classical forecasters once you evaluate only on data they could not have seen?**

Repo: https://github.com/mirzayasirabdullahbaig07/ForecastClean · Local: `C:\Users\HP\Downloads\ForecastClean`

---

## 📊 Project progress — where we are right now

**Overall: 62% ▓▓▓▓▓▓▓▓▓▓▓▓░░░░░░░░ (target: research-paper preprint)**
_Last updated: 2026-11-27 · Current phases: **Phase 5 — main experiments** (first Chronos results logged in [`EXPERIMENT_LOG.md`](EXPERIMENT_LOG.md)), plus **Phase 2 — Literature** ([`LITERATURE.md`](LITERATURE.md)) and **Phase 3 — Data** ([`DATA_SOURCES.md`](DATA_SOURCES.md)) to finish_

| # | Phase | Weight | Done | Contribution | Status |
|---|---|---:|---:|---:|---|
| 1 | Framework + tests (rolling origin, MASE, DM test, 5 baselines, CLI) | 15% | 100% | 15% | ✅ Done (6/6 tests pass, `simulate` runs) |
| 2 | Literature review + gap statement | 10% | 80% | 8% | 🔄 **Nearly done** — closest competitor (2609.10357) analysed; new gap **A′** (rolling origins after release dates + horizon sweep) in `LITERATURE.md` §5; release dates found (`LITERATURE.md` §6); you still read the 2 key papers + confirm dates at the model cards |
| 3 | Choose 6–10 real series (source + licence recorded) | 10% | 70% | 7% | 🔄 **Mostly done** — all 9 series downloaded (2026-11-25) and manifest saved; **licences still to confirm**; macro series end 2025 (see agenda) |
| 4 | Real-data pipeline + Chronos adapter tested | 10% | 95% | 9.5% | ✅ **Nearly done** — Chronos-Bolt and Chronos-2 run on real weights (Colab); tuned baselines (AutoETS, AutoTheta, AutoARIMA on non-seasonal series) implemented + tested (`--tuned`), **Colab run done 2026-11-27 (25 series)**. Left: TimesFM adapter |
| 5 | Main experiments (all models × series × horizons) | 20% | 50% | 10% | 🔄 **Started** — Chronos-Bolt-small + Chronos-2 + 7 classical models on 26 series (22 + 4 more; macro excluded: no post-release data). Post-release skill and the contamination gap run; results in the log (**preliminary**). **Tuned baselines run (25 series, 2026-11-27): Chronos-2 −0.453, Bolt-small −0.332 vs best tuned classical AutoTheta −0.035 — lead unchanged.** Still missing: more foundation models (TimesFM), probabilistic metrics |
| 6 | RQ2 contamination gap + RQ3 ranking stability | 10% | 85% | 8.5% | 🔄 **First corrected answer (26 series, 2026-11-25): no leakage signature** — mean difference-in-differences is negative or ≈0 for both models, all intervals include 0 except a tiny FX effect; typical (median) series ≈ −0.03. **Robustness (2026-11-27, series-level checks): null result holds** — FX-as-one-cluster, leave-one-out, other reference definitions, event pages split out; only hourly electricity (n=2) is positive. Left: window-level block bootstrap (needs Colab re-run, cell 4e), write-up |
| 7 | Extensions (CRPS/WQL, RQ4 return series) | 5% | 0% | 0% | ⬜ Not started |
| 8 | Paper writing (8 sections) | 15% | 25% | 3.75% | 🔄 **Draft v0.1 written (2026-11-27)** — all 8 sections in [`paper/PAPER.md`](paper/PAPER.md) with Figure 1, built only from results we have; related-work citations still to be verified; several numbers pending (see its "Open items") |
| 9 | Release (Zenodo, arXiv, supervisor feedback) | 5% | 0% | 0% | ⬜ Not started |
| | **Total** | **100%** | | **62% (61.75%, shown as 62%)** | |

Overall % = sum of (weight × done). Update the "Done" column when a phase moves, then recompute.

### 🎯 Agenda — what we do next (in order)
1. **Literature (Phase 2, nearly done):** read Meyer et al. (2510.13654) and Moghadasi & Ghaderi (2609.10357) yourself; verify each model's **release date** (our conservative cutoff); confirm gap statement **A′** in `LITERATURE.md` §5. **Novelty warning:** post-cutoff evaluation and general ranking-stability studies are both crowded — our room is *rolling post-release origins + horizon sweep*.
2. ~~Get the data (Phase 3)~~ ✅ downloaded 2026-11-25 (9 series, `data/MANIFEST.csv`). Licences in `DATA_SOURCES.md` still to confirm.
3. **Re-run the batch after the design fixes (Phase 4):** `forecastclean batch` (≈7 min). Then plot 3–4 series by eye and check the forecasts look sane.
4. **Fix the macro data end-date (Phase 3):** FRED-MD `current.csv` ended at 2025-08/09 although downloaded in Nov 2026. Open the St. Louis Fed FRED-MD page, find the newest monthly vintage file, then `forecastclean download --only fredmd_UNRATE fredmd_CPIAUCSL fredmd_INDPRO --fred-vintage <YYYY-MM>`.
5. ~~Run Chronos on Colab (Phase 4)~~ ✅ done 2026-11-25 (post-release run). Chronos's training cutoff is not published, so we use each model's **release date** as a conservative cutoff (verify dates first).
6. ~~First contamination-gap runs (RQ2)~~ ✅ 6-series and 22-series runs done, see log. The 22-series run is **confounded by context length** (fixed in code).
7. ~~Corrected contamination-gap run~~ ✅ 2026-11-25 (26 series): **null result**, see log. The 22-series run and the 6-series run are superseded.
8. **Next:** (a) ~~run the tuned-baseline comparison on Colab~~ ✅ done 2026-11-27: tuned baselines do not change the picture (save the CSVs when re-run); (b) robustness of the gap: ✅ series-level checks done (`forecastclean robust`); **open: window-level block bootstrap — run notebook cell 4e on Colab (~1 h)**; per-model vs global cutoff; (c) add TimesFM 2.5 (second model family) if it installs on Colab; (d) ~~save the Colab result CSVs into the repo~~ ✅ done: `results/gap_fixed/`; (e) **start the paper skeleton** (Phase 8) around the null-result framing; (f) confirm release dates + data licences.

### 🚦 Go / no-go gates
- End of Phase 4: no foundation model runs at all → fall back to an all-classical + deep-baseline study of *evaluation-protocol sensitivity*.
- End of Phase 6: no contamination gap anywhere → report it as a null result with CIs. **(Status 2026-11-25: corrected 26-series run shows no leakage signature → we are on the null-result path; the paper's contribution is the protocol + honest negative result, not a leak discovery.)**

### ✅ Honest status of what is verified
- Verified (27 tests run 2026-11-25): forecasters, MASE scaling, no look-ahead, DM-test behaviour, seasonal-vs-random-walk sanity, pre/post cutoff labels, the data-cleaning functions, Holm correction and ranking-stability bootstrap (all on synthetic inputs).
- Verified on real weights (Colab, 2026-11-25): the Chronos adapter for Bolt-tiny, Bolt-small and Chronos-2.
- **Preliminary only:** all foundation-model results (untuned ARIMA/ETS, release-date cutoffs rather than published training cutoffs, bootstrap over series treats correlated series — EUR crosses, Wikipedia pages — as independent, so intervals are too narrow).
- **Verified 2026-11-27:** release dates (Chronos-Bolt 26 Nov 2024, Chronos-2 20 Oct 2025 per the Chronos GitHub news; arXiv 17 Oct 2025) — our cutoffs are later; model cards state no data cutoff; both Apache-2.0. **Not verified:** licences of the data sources; robustness of the null result to a window-level bootstrap (code + tests ready, not yet run on real windows).

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
pip install -e ".[dev]" && python -m pytest -q     # 19 tests
forecastclean download                               # fetch + clean real series -> data/raw/*.csv, data/MANIFEST.csv
forecastclean batch                                  # all series in data/raw -> results/batch/
forecastclean batch --clean-from 2025-10-31 --post-only --horizon-sweep --out results/post   # A': only post-release windows, 4 horizons per series
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
