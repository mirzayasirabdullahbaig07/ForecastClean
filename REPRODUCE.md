# Reproducing the results

Every number in `paper/PAPER.md` comes from a saved file in `results/`. The model runs are the only step that needs a GPU or hours of CPU time; everything after them is a script that runs in seconds.

## Environment used for the reported runs

| | RQ1 (`chronos_post_tuned3`), gap (`gap_blocks`) | earlier Colab runs (`gap_fixed`, `chronos_post_tuned`) |
|---|---|---|
| Machine | Windows laptop, CPU only | Google Colab, T4 GPU |
| Python | 3.11 | 3.13 |
| chronos-forecasting | 2.3.2 | 2.x (as installed on Colab, 2026-11-25/27) |
| timesfm | 3.0.2 (class `TimesFM_2p5_200M_torch`) | source install (smoke test only) |
| statsforecast | 2.1.1 | 2.x |
| torch | 2.14.0+cpu | Colab default |

Models: `amazon/chronos-bolt-small`, `amazon/chronos-2`, `google/timesfm-2.5-200m-pytorch` (all Apache-2.0). Model weights are fetched from Hugging Face at first use; revisions are not pinned, which is a limitation. Release dates used as clean-from dates are in `src/forecastclean/registry.py` with the evidence for each.

## Steps

```bash
pip install -e ".[dev,fm,tuned]" && pip install timesfm
python -m pytest -q                       # unit tests (statsforecast tests skip if it is not installed)
forecastclean download                    # data/raw/*.csv + data/MANIFEST.csv (raw data is not redistributed)
```

| Result folder | Command | Time (laptop CPU) |
|---|---|---|
| `results/chronos_post_tuned3` (RQ1, Table 1, Figure 1) | `forecastclean batch --chronos amazon/chronos-bolt-small amazon/chronos-2 google/timesfm-2.5-200m-pytorch --release-cutoff --post-only --max-origins 30 --tuned --only <the 25 series, see RESULT_TABLE.md> --out results/chronos_post_tuned3` | about 3 to 5 h |
| `results/gap_blocks` (RQ2, Tables 2 and 3) | `forecastclean gap --chronos amazon/chronos-bolt-small amazon/chronos-2 google/timesfm-2.5-200m-pytorch --max-origins 20 --drop arima --out results/gap_blocks` then `forecastclean robust --dir results/gap_blocks --block 5` | under 1 h |
| `results/gap_fixed` (RQ2, 40-origin run, Chronos only) | see `results/gap_fixed/RUN_INFO.md` | Colab T4, about 1 h |
| `results/gap_preend` (pre-period ending 2023-12-31; Table 4b) | `forecastclean gap --chronos google/timesfm-2.5-200m-pytorch amazon/chronos-bolt-small amazon/chronos-2 --max-origins 1000 --match-days 365 --pre-end 2023-12-31 --drop arima --only wiki_Christmas wiki_Easter wiki_Halloween wiki_Thanksgiving wiki_Wimbledon wiki_SuperBowl wiki_Ramadan wiki_Eurovision --out results/gap_preend` then `forecastclean robust --dir results/gap_preend` | short |
| `results/gap_matched` (calendar-matched gap; Section 5.2;) | `forecastclean gap --chronos amazon/chronos-bolt-small amazon/chronos-2 google/timesfm-2.5-200m-pytorch --max-origins 1000 --match-days 365 --drop arima --only <the 8 event pages> --out results/gap_matched` then `forecastclean robust --dir results/gap_matched` | short |
| `results/prob` (probabilistic accuracy; Section 5.4;) | `forecastclean prob --chronos amazon/chronos-bolt-small amazon/chronos-2 google/timesfm-2.5-200m-pytorch --release-cutoff --max-origins 30 --only <the 25 series> --out results/prob` | 1 to 3 h |

## Regenerating tables and figures from saved results

```bash
python paper/make_tables.py     # Table 1 (skill by group), Table 3 (stable subset), run-to-run agreement
python paper/make_fig1.py       # Figure 1
```

## Data

Sources and licences: `DATA_SOURCES.md`. Checksums of the exact files used: `results/gap_fixed/MANIFEST_colab_2026-11-25.csv`. The ECB, Wikipedia and NESO series end on different days, so re-running `forecastclean download` later gives slightly longer series and slightly different numbers.

## Model revisions

Revisions were not pinned in the runs (the code loads the default branch). The latest commits on 2026-11-28, which is when the last runs were made, were:

| Model | Hugging Face id | Commit | Last modified |
| --- | --- | --- | --- |
| Chronos-Bolt-small | `amazon/chronos-bolt-small` | `772f3d25d38aec6d914c8949dab4462e2d46f5d8` | 2025-11-21 |
| Chronos-2 | `amazon/chronos-2` | `29ec3766d36d6f73f0696f85560a422f50e8498c` | 2026-06-05 |
| TimesFM 2.5 | `google/timesfm-2.5-200m-pytorch` | `1d952420fba87f3c6dee4f240de0f1a0fbc790e3` | 2025-10-02 |

The Chronos-2 repository was updated on 2026-06-05, after its release date (2025-10-31); we did not check whether the weights or only the model card changed. All runs (2026-11-25 onward) are later than that update, so they used this revision unless the repository changed again in the days between. To reproduce exactly, pass these commit hashes as the `revision` of the Hugging Face download. Take the environment from `pip freeze` on the machine that ran the experiments.
