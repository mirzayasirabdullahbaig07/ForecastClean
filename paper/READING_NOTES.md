# Reading notes for the supervisor meeting (prepared 2026-11-28 from the full text of both papers)

These notes paraphrase the two papers closest to ours. Skim them, then read the two papers once so you can answer questions in your own words.

## 1. Moghadasi and Ghaderi (arXiv 2609.10357, Sept 2026): "A Later Test Set Is Not a New Domain"

**What they do.** Thirteen forecasters (4 classical, 3 trained per dataset, 6 pretrained: Chronos-Bolt-small and -base, Chronos-2, TimesFM 2.5, TimesFM 3, Moirai-2) are scored from one forecast origin, 1 Jan 2026, on 2,254 series in seven groups (Wikipedia pageviews daily, weekly, monthly; hourly weather, air quality and electricity; daily ECB exchange rates). Data come from keyless public sources; they release fetchers and checksums, not the data.

**Results.** Pretrained models rank first in six of seven groups, but only five count as real wins. Headline: about 28% lower MASE than the best classical method on weekly Wikipedia. Hourly electricity is won by Theta (the pretrained models are statistically level with it). On exchange rates the Friedman test finds no difference among all thirteen, seasonal naive included.

**Their argument.** Series properties (seasonal strength, spectral entropy) do not explain where pretrained models win. They argue that familiarity with the training corpus does: the TimesFM authors describe their corpus as dominated by Wikipedia pageviews up to late 2023, and TimesFM ranks better than Chronos on Wikipedia by about 0.53 ranks (versus 0.09 elsewhere). They call this an association and a hypothesis, not a demonstrated mechanism.

**What they say they cannot do** (their limitations): one origin per group, so no variance over time; two groups under 50 series; cutoffs cannot be verified, and where undisclosed they substitute the release date; the corpus finding is correlational and the effect is modest. They suggest rolling-origin evaluation and domain hold-outs stratified by corpus membership. They also report that pretrained models are overconfident (80% intervals cover less than 80%).

**How we differ.**
- We use rolling origins (they list it as future work), per-model release dates, a horizon per frequency, tuned classical baselines, and a pre-versus-post difference-in-differences gap. They run no before/after comparison.
- Agreement: exchange rates tie with naive-type methods in our data too; TimesFM is slightly ahead of Chronos-2 on Wikipedia (small, 14 pages).
- Disagreement or nuance: they find Theta ahead on hourly electricity; we have one daily electricity series where the foundation models are far ahead, so the two results are not in conflict but are not comparable. On calibration they report overconfidence in general; we find it for Chronos-2 only (coverage 0.751), while TimesFM and Chronos-Bolt-small are slightly too wide (0.836).
- They argue against publishing a table of approximate cutoffs. We do use release dates as stand-ins, and we say clearly that they are not training cutoffs.

**Likely supervisor question:** "Is this not just their paper with more origins?" Answer: they test whether the models win on later data; we test whether skill changes across the release date relative to classical models, and how much the answer moves with origin, horizon and baselines.

## 2. Meyer et al. (arXiv 2510.13654, v3 Feb 2026): "Rethinking Evaluation in the Era of Time Series Foundation Models"

**What they do.** A position paper with evidence. They define direct (sample) leakage, where a dataset used for pretraining or fine-tuning one model later serves as another model's test set, and indirect (temporal) leakage, where nominally different series overlap in time and are correlated through a shared event. They trace 22 foundation models over 401 datasets and find that only about 6% of the datasets never appeared in any model's pretraining or fine-tuning corpus. They illustrate indirect leakage with a Madrid transport case from earlier work and their own COVID stock experiment (a small transformer trained from scratch; the leaky version was better before May and the same afterwards).

**Their two requirements.** (1) Test sets must be genuinely novel, enforced by the benchmark, not the model developer. (2) A global barrier t_now: every test observation must come after the latest training cutoff among the compared models. They state that the size of temporal leakage in real settings is largely unknown.

**Gaps they leave open** (which our paper partly fills): they give no fallback when a cutoff is undisclosed, they do not discuss release dates, and they do not measure leakage on a real released foundation model.

**How we differ.** Our global clean-from date applies their requirement 2, with release dates as a conservative proxy for cutoffs. Our RQ2 is an attempt to measure temporal leakage on real released models from the outside, which they say is unknown. We cannot claim to detect leakage: a null result only bounds what we could see.

**Likely supervisor question:** "Does the leakage you test even exist for your post-release windows?" Answer: no, post-release windows are clean by construction; the question is whether skill on earlier windows was inflated.

## 3. Points these papers raise that matter for our design

1. **TimesFM's corpus ends around late 2023 (per its authors, as cited by Moghadasi and Ghaderi).** In the calendar-matched design (365 days before the release date) the pre-release windows for TimesFM therefore fall after its corpus end and are probably clean too. That design is a good check on calendar phase, but it weakens the contamination contrast for TimesFM. The earlier designs thin origins over 2015 to release, so most pre windows lie inside the possible training period. The paper states this limitation (Section 6). A follow-up run with the pre-period placed before the documented corpus end is implemented (`--pre-end`).
2. **Indirect leakage** (Meyer et al.) concerns correlated series in the same period. It is not an issue for post-release windows, but it is a reason our standard errors treat the EUR pairs as one cluster.
3. **Domain familiarity** cannot be removed by any temporal hold-out (Moghadasi and Ghaderi). We cannot test it without corpus disclosure; we say so in Section 6.

## 4. What is still yours to do
- Read both papers once (about 1 hour each).
- Open each licence link in `DATA_SOURCES.md` once.
- Agree the framing with your supervisor: the honest claim is "foundation models keep a lead on clean data except on exchange rates, and we find no consistent leakage signature, with caveats".
