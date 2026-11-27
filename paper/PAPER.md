# ForecastClean — Paper draft v0.1

_Draft of 2026-11-27. Source of truth for the numbers: `results/gap_fixed/` (RQ2) and `results/chronos_post_tuned/RESULT_TABLE.md` (RQ1). Citations marked "to be verified" were checked at summary level only; read them in full before submission._

## Abstract

**Working title:** *Do time-series foundation models still beat classical forecasters on data they cannot have seen? A rolling-origin, release-date-aware evaluation.*

Pretrained time-series foundation models (Chronos-Bolt, Chronos-2) keep a clear accuracy lead over classical forecasters when scored only on windows that start after their release dates, and we find no consistent sign that this lead is a leakage artefact. On 25 daily series (ECB exchange rates, Wikipedia pageviews, GB electricity demand) with rolling origins after 31 Oct 2025, the mean log-relative MASE against naive is −0.453 for Chronos-2 and −0.332 for Chronos-Bolt-small, against −0.036 for the best classical method (Theta); tuning ETS, Theta and ARIMA automatically does not close the gap. To test for contamination we compare each model's skill before and after its own release date with a difference-in-differences gap measured against classical models. The mean gap is −0.077 for Chronos-2 and −0.161 for Chronos-Bolt-small (both 95% intervals include 0), and it stays at or below zero when we change the reference, treat the ten EUR pairs as one cluster, drop single series, or set aside calendar-event pages. Electricity demand is the one exception: the gap is positive for both models, driven by the hourly series (two electricity series in total), and we cannot yet explain it. Release dates are conservative stand-ins for undisclosed training cutoffs, so a null result bounds the leakage we can detect but does not rule it out. All code, data checksums and results are public.

## 1 Introduction

A foundation-model lead over classical forecasters only means something if the test data was not in the model's pretraining corpus. Most pretraining corpora are only partly documented, benchmark series are reused across papers, and correlated series can leak across a train-test split even when no value is copied (Meyer et al. 2025, to be verified). The simplest defence is to score only windows after a model's release date, since a 2026 observation cannot be in a 2025 checkpoint.

That defence is now common, and it has two weak points. The closest post-release study we found scores a single forecast origin and no horizon sweep, so it cannot say how much a ranking moves with the origin or the horizon (Moghadasi and Ghaderi 2026, to be verified). And they treat post-release data as clean by construction, without asking whether the *same* models look different on earlier data they may have seen (Moghadasi and Ghaderi 2026, to be verified).

We ask two questions about Chronos-Bolt and Chronos-2 against classical forecasters:

1. **Skill on clean data (RQ1).** Is the foundation-model lead still there when every window starts after the model's release date, with identical context length and tuned classical baselines?
2. **Leakage signature (RQ2).** Does a model lose more skill, relative to classical models, after its release than before it?

**Contributions.**

- A rolling-origin protocol with an asserted no-look-ahead check, equal context length for every window, and release-date cutoffs taken per model.
- A difference-in-differences gap that separates a data shift common to all models from a loss specific to the foundation model.
- Evidence on 25 real series that the lead survives tuned baselines (RQ1) and that no consistent leakage signature appears (RQ2), with robustness checks and an explicit list of what the null result cannot exclude.
- A reproducible pipeline: public code, 38 automated tests, and data checksums for every run.

## 2 Related work

*Status: every entry below was checked at abstract or summary level only. Read each paper in full and fix wording before submission.*

**Leakage in foundation-model evaluation.** Meyer et al. (arXiv 2510.13654) name two kinds of leakage: reuse of the same samples in pretraining and test sets, and temporal overlap between correlated series. They recommend a global post-training test period that starts after the latest pretraining timestamp of every compared model. Our per-model release-date cutoffs and the global clean-from date in the RQ1 runs follow that rule. Aksu et al. (GIFT-Eval, 2410.10393) build a benchmark with a non-leaking pretraining set and show that leakage raises measured performance.

**Post-release hold-outs.** Moghadasi and Ghaderi (2609.10357) score 13 methods from one forecast origin on 1 Jan 2026 across seven data groups, including ECB exchange rates and Wikipedia pageviews, and find the pretrained models ahead in most groups but tied with classical methods on exchange rates. They argue that post-release data may still be familiar to a model. Ebrahim et al. (2610.00589) find TimesFM-3 level with classical methods on FRED-MD series observed after its documented training data. Several other post-cutoff or live benchmarks exist, so the post-cutoff idea alone is not new.

**Contamination detection.** Li et al. (TSFMAudit, 2605.26161) detect contamination from the model side, using how fast a model adapts under fine-tuning. We detect it from the outcome side, from a drop in skill against classical models after release. The two are complementary.

**Where this paper sits.** We use rolling origins strictly after each release date rather than one origin, a horizon sweep, tuned classical baselines, and a pre-versus-post difference-in-differences gap with robustness checks. We do not claim a new detection method for contamination.

## 3 Evaluation protocol

Every number in this paper comes from rolling-origin forecasts scored against naive, with the same context length for every window and a cutoff date for every model.

**Windows.** For each series we take forecast origins at evenly spaced positions. A forecaster sees only the observations before the origin, and the code asserts this. Every window uses the last 1024 observations as context (a minimum and a maximum), so early windows cannot be penalised for having less history. The horizon is fixed per frequency: 10 steps for business-daily exchange rates, 14 for daily series, 24 for hourly series.

**Metric.** Errors are MASE, scaled by the in-sample seasonal-naive error of the context (season 1 for exchange rates, 7 for daily, 24 for hourly). Skill is the ratio of mean MASE to the mean MASE of naive, and we report the mean of its logarithm across series. A value of −0.453 means the model's error is about 36% below naive in the geometric sense; 0 means no better than naive.

**RQ1: clean windows.** Only windows whose target starts after the latest release date among the compared foundation models (31 Oct 2025, Chronos-2) are scored.

**RQ2: the contamination gap.** Each foundation model *m* has a release date *r*. Pre-release windows have targets ending on or before *r* and could have been seen. Post-release windows start after *r* and cannot have been. For each series, with *c* the set of classical models:

```latex
\mathrm{gap}(k) = \log \mathrm{rel}_k^{\mathrm{post}} - \log \mathrm{rel}_k^{\mathrm{pre}}, \qquad \mathrm{DiD}_m = \mathrm{gap}(m) - \operatorname{median}_{k \in c}\, \mathrm{gap}(k)
```

A positive DiD means the foundation model lost more skill after release than classical models did, which is the signature of leakage. Subtracting the classical median removes a data shift that affects all models alike. A positive DiD is a signature, not proof, and a zero DiD does not prove the data was unseen.

**Cutoffs.** Training cutoffs are not published for these models, so we use release dates: Chronos-Bolt 1 Dec 2024 (rounded late) and Chronos-2 31 Oct 2025. A later date than the true release can only shrink the clean set. We have not yet checked each date at the model card.

**Statistics.** Intervals for the gap are bootstrapped over series, with variants described in Section 5.3. The framework also implements Diebold–Mariano tests with the Harvey correction and Holm correction, and Kendall-tau ranking stability over resampled origins and series; the ranking-stability result is reported in Section 5.1.

## 4 Experimental setup

**Data.** We downloaded 29 public series and used 26. Three FRED-MD macro series end in 2025, before the Chronos-2 release date, so they have no post-release windows and are excluded. Raw data is not stored in the repository because licences are not yet confirmed; each run records file checksums in a manifest.

| Group | Series | Frequency | Horizon | Used in |
| --- | --- | --- | --- | --- |
| ECB exchange rates | EUR against USD, GBP, JPY, CHF, CAD, AUD, SEK, NOK, CNY, INR | business daily | 10 | RQ1, RQ2 |
| Wikipedia pageviews | 14 articles (6 general: Python, Bitcoin, Cricket, Weather, Machine learning, Taylor Swift; 8 calendar-event: Christmas, Easter, Halloween, Thanksgiving, Wimbledon, Super Bowl, Ramadan, Eurovision) | daily | 14 | RQ1, RQ2 |
| GB electricity demand (NESO) | national demand, daily | daily | 14 | RQ1, RQ2 |
| GB electricity demand (NESO) | national demand, hourly | hourly | 24 | RQ2 only (too slow for the tuned run) |
| FRED-MD | UNRATE, CPIAUCSL, INDPRO | monthly | 6 | excluded (no post-release data) |

The event pages were fixed in code before any per-page results were examined.

**Foundation models.** Chronos-Bolt-small and Chronos-2, run with their public weights and median forecasts (Chronos-Bolt-tiny only for a smoke test). Chronos-2 receives each series as a single-variate input with no covariates.

**Classical baselines.** Naive, seasonal naive, drift, ETS, ARIMA(1,1,1), Theta, and Comb (the average of ETS, ARIMA and Theta). For RQ1 we add three tuned baselines, AutoETS, AutoTheta and AutoARIMA, from statsforecast. AutoARIMA ran only on non-seasonal series (the exchange rates) because it takes 5 s per fit on daily data and 23 s on hourly data, so it is not part of the cross-series ranking. In the RQ2 runs ARIMA was dropped for speed and the classical reference is the median over ETS, Theta, Comb, drift and seasonal naive.

**Windows.** RQ1: up to 30 post-release origins per series. RQ2: up to 40 origins before and 40 after each release date (26 to 40 after, depending on how much data exists), context 1024 in every window.

**Code and runs.** The pipeline is public (`github.com/mirzayasirabdullahbaig07/ForecastClean`). RQ1 ran at commit `e7dc9ee`; RQ2 at commit `8c4247d`, both on a Colab T4 GPU.

## 5 Results

### 5.1 Skill on clean data (RQ1)

On 25 series and windows that start after 31 Oct 2025, both Chronos models beat every classical method, tuned or not. Chronos-2 scores −0.453 and Chronos-Bolt-small −0.332 in mean log-relative MASE against naive, which is about 36% and 28% lower error. The best classical methods score −0.036 (Theta) and −0.035 (AutoTheta), and AutoETS scores −0.006, close to naive.

Tuning therefore does not change the picture: AutoTheta is no better than untuned Theta, and AutoETS is only slightly better than untuned ETS (+0.018), which is itself slightly worse than naive.

![Figure 1](figures/fig1_rq1_skill.png)

*Figure 1. Colab run at commit e7dc9ee; values transcribed from the printed table (result files not yet saved). AutoARIMA not ranked. Regenerate with `python paper/make_fig1.py`.*

The ranking is stable. Across resamples of origins and series the best model stays the best in every one (probability 1.00), and the mean Kendall tau between resampled rankings is 0.73. The tuned AutoARIMA ran only on the exchange-rate series, so it is left out of this ranking.

Two limits apply. Each series contributes one horizon, and ten of the 25 series are EUR pairs that share a currency, so the effective number of independent series is smaller than 25. We also have not yet broken the result down by data group, which matters because an earlier study found every method tied on exchange rates (Moghadasi and Ghaderi 2026, to be verified).

### 5.2 The contamination gap (RQ2)

There is no consistent leakage signature. Across 26 series the mean DiD is negative for both models and both intervals include zero. Electricity is the only group where the mean is positive for both.

| Model | Group | Series | Mean DiD | 95% interval | Series with DiD > 0 |
| --- | --- | --- | --- | --- | --- |
| Chronos-2 | all | 26 | −0.077 | [−0.176, 0.020] | 7 |
| Chronos-2 | exchange rates | 10 | −0.034 | [−0.056, −0.013] | 2 |
| Chronos-2 | Wikipedia | 14 | −0.133 | [−0.300, 0.033] | 4 |
| Chronos-2 | electricity | 2 | +0.097 | [−0.114, 0.308] | 1 |
| Chronos-Bolt-small | all | 26 | −0.161 | [−0.347, 0.007] | 9 |
| Chronos-Bolt-small | exchange rates | 10 | −0.012 | [−0.038, 0.011] | 4 |
| Chronos-Bolt-small | Wikipedia | 14 | −0.309 | [−0.614, 0.009] | 3 |
| Chronos-Bolt-small | electricity | 2 | +0.137 | [0.063, 0.211] | 2 |

A negative DiD means the model kept more of its skill after release than classical models did. Intervals are bootstrapped over series and are too narrow, because exchange-rate crosses and Wikipedia pages are correlated (Section 5.3).

The hourly electricity series carries the positive result (DiD +0.31 for Chronos-2, +0.21 for Chronos-Bolt-small). With only two electricity series, we cannot tell a leakage effect from a change in demand patterns.

### 5.3 Robustness

We test whether the null result depends on how the gap is computed. Each check changes one choice and leaves the rest as in Section 5.2. Files: `results/gap_fixed/robust_*.csv`, produced by `forecastclean robust`.

| Check | Chronos-2 | Chronos-Bolt-small |
| --- | --- | --- |
| Headline (median classical reference, 26 series) | −0.077 [−0.176, 0.020] | −0.161 [−0.347, 0.007] |
| Reference = mean of classical models | −0.080 | −0.173 |
| Reference = median without drift | −0.081 | −0.161 |
| Reference = each single classical model | −0.054 to −0.097 | −0.129 to −0.214 |
| Ten EUR pairs counted as one unit (17 units) | −0.100 [−0.251, 0.046] | −0.239 [−0.499, 0.021] |
| Leave one series out (range) | −0.106 to −0.050 | −0.209 to −0.115 |
| Eight calendar-event Wikipedia pages | −0.165 [−0.448, 0.142] | −0.502 [−0.955, 0.047] |
| Six other Wikipedia pages | −0.091 [−0.161, −0.024] | −0.051 [−0.149, 0.051] |

No variant makes the mean positive. The most influential single series is the Christmas page, which has a large positive DiD, and removing it makes the means more negative. The event pages are very noisy, with large effects of both signs. On the six other Wikipedia pages Chronos-2 lost less skill after release, the opposite of leakage, although classical models getting worse after release would produce the same pattern.

A window-level block bootstrap, which resamples forecast origins inside each series, is implemented and tested on synthetic data. It needs per-window errors that the earlier run did not save, so it is not yet run on real data.

## 6 Limitations

The null result in Section 5.2 is weaker than it looks, for these reasons.

- **Release dates are not training cutoffs.** A model's real cutoff is earlier than its release date, so some pre-release windows are already clean, and the rest are only possibly seen. Both effects make any measured gap a lower bound. A null result does not show that no contamination exists, and an earlier study argues that familiarity can survive a later hold-out (Moghadasi and Ghaderi 2026, to be verified).
- **Intervals are too narrow.** The bootstrap resamples series as independent, but the EUR pairs share a currency and the Wikipedia pages share news cycles. Counting the EUR pairs as one unit widens the intervals but does not change the conclusion. The window-level bootstrap is not yet run on real data.
- **Few series per group.** Electricity has two series, and its positive gap is unexplained. We cannot separate a leakage effect from a change in demand.
- **Classical models are fixed.** ARIMA is a fixed (1,1,1) in most runs and was dropped from the RQ2 runs. Tuned AutoARIMA ran only on non-seasonal series, so the strongest classical competitor is missing on seasonal series.
- **One foundation-model family.** Both models are Chronos. We have not run TimesFM or Moirai, so the result may not transfer.
- **Point forecasts only.** We score MASE of the median forecast. CRPS and weighted quantile loss are not yet reported.
- **Short sample.** Post-release windows cover about one year, so the clean-data result describes one period.
- **Unchecked sources.** Release dates have not been confirmed at the primary model cards, and the data licences (FRED-MD, ECB, Wikimedia, NESO) are not yet confirmed.

## 7 Conclusion

With identical context, per-model cutoffs and tuned baselines, Chronos-Bolt-small and Chronos-2 keep a clear lead over classical forecasters on data released after them, and we find no consistent sign that the lead comes from leakage. The lead is large (about 28% and 36% below naive MASE) against classical methods that barely beat naive. The leakage check cannot prove absence, because cutoffs are undisclosed and the evidence on electricity is open. We recommend that foundation-model comparisons report skill separately before and after each model's release, name their cutoff assumptions, and show how the answer changes when those assumptions change.

## 8 Reproducibility

Code, tests and result files are in the public repository `mirzayasirabdullahbaig07/ForecastClean`. Each run records its command, commit and data checksums (`results/gap_fixed/RUN_INFO.md`, `MANIFEST_colab_2026-11-25.csv`). Raw data is downloaded by `forecastclean download` and is not redistributed. The RQ2 tables come from `forecastclean gap` and `forecastclean robust`; the RQ1 table is printed by `forecastclean batch --tuned` and is transcribed in `results/chronos_post_tuned/RESULT_TABLE.md` until the result CSVs are saved.

## Open items before submission

This draft uses only results we have. These items would change or strengthen it; the first four decide whether the paper is ready to send.

| Item | Why it matters | How |
| --- | --- | --- |
| Save the RQ1 result files and report skill by data group | Only the printed table exists. Prior work found methods tied on exchange rates, so the group split is needed. | Re-run or zip the Colab output (Faiqa), then Claude |
| Run the window-level block bootstrap on real windows | The current intervals treat series as independent. | Notebook cell 4e, about 1 hour on Colab |
| Confirm each release date at its model card | The cutoff is the central assumption of RQ2. | Claude, then Faiqa checks |
| Read the two key papers in full and fix Section 2 | Summaries so far are secondhand. | Faiqa, with supervisor |
| Add a second model family (TimesFM 2.5) | One family limits the claim. | Claude adapter, Colab run |
| Explain or bound the electricity result | It is the only positive gap. | Claude: split by regime and season |
| Add probabilistic metrics (CRPS or weighted quantile loss) | Reviewers expect them. | Claude |
| Confirm data licences | Needed before publication. | Faiqa |
| Confirm the gap statement with the supervisor | The post-release idea is crowded. | Faiqa |
| Figures and venue formatting | Draft has one planned figure. | Claude, after the numbers are final |
