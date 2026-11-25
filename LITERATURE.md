# Literature notes — ForecastClean (Phase 2)

_Status 2026-11-25 (updated later the same day — see §5): **abstract/snippet-level only, plus tool-generated summaries of the two key PDFs.** Every entry below was checked against its arXiv page or a search snippet; none has been read in full yet. Before citing in the paper, read the starred papers fully._

## 1. Verified papers (IDs confirmed to exist and match their descriptions)

| Paper | arXiv | What it does | Why it matters here |
|---|---|---|---|
| ⭐ Meyer, Kaltenpoth, Zalipski, Müller — *Rethinking Evaluation in the Era of Time Series Foundation Models: (Un)known Information Leakage Challenges* (v1 title: *Time Series Foundation Models: Benchmarking Challenges and Requirements*) | 2510.13654 | Reviews TSFM evaluations; defines two leakage types: (1) train-test sample overlap from dataset reuse, (2) temporal overlap of correlated train/test series. Argues for new evaluation methods. | Our motivation. Our pre/post-cutoff split targets leakage type (2) and partly (1). |
| Li et al. — *TSFMAudit: Data Contamination Auditing in Forecasting TSFMs* | 2605.26161 | Detects contamination via fine-tuning-probe adaptation speed; 6 models, 187 datasets. | Model-side detection. We do **outcome-side** detection (skill gap vs classical reference). Complementary. |
| Liu et al. — *Rethinking Multimodal Time-Series Forecasting Evaluation* (TimesX) | 2607.06973 | A **multimodal** (series + text) benchmark with strict time isolation; recommends using only tasks after a model's cutoff. | ⚠ Not a contamination *audit* — the earlier README wording was wrong. Supports our post-cutoff premise. |
| ⭐ *A Later Test Set Is Not a New Domain: Pretraining Familiarity Survives a Contamination-Free Hold-Out* | 2609.10357 | Hold-out of data published after each model's release; 6 pretrained forecasters vs classical baselines; pretrained models win only marginally, no edge on daily exchange rates. (Details from a news summary + search snippet — **read the paper**.) | **Closest competitor.** Title implies post-cutoff data is *not* automatically clean ("familiarity survives"). Directly challenges our RQ2 assumption. |
| Ebrahim, Ali, El-Kotory — *Foundation or Formula? … TimesFM-3 and Classical Models* | 2610.00589 | Simulation + M4 + 101 FRED-MD macro series observed after documented training data; TimesFM-3 statistically level with classical methods there. | Prior art for "post-corpus real data vs classical". Also quotes Meyer et al.: only ~6% of 401 datasets never appeared in any model's pretraining. |
| Aksu et al. — *GIFT-Eval* | 2410.10393 | Benchmark with a non-leaking pretraining set; shows leakage boosts performance, more at longer horizons. | Standard benchmark; shows leakage effect empirically (via Moirai ablation). |
| Ansari et al. — *Chronos-2* | 2510.15821 | Model; training datasets listed in its Table 6; maintainers state FRED-MD was **not** used in Chronos-2 training (GitHub discussion #358). | Candidate model with a *documented* corpus. |
| *When Do Foundation Models Pay Off? Break-Even Analysis* | 2607.04919 | Chronological 60/20/20 split, MASE, FM vs classical vs training size. | Related protocol; different question. |
| IND-Eval | 2610.16652 | Audits model–source overlap; does **not** restrict windows to post-cutoff. | Related audit-style work. |
| Others seen (not yet checked): TIME benchmark 2602.12147; LiveHouse-TS 2608.17299; Impermanent (live benchmark, Garza et al. 2026); realized-volatility comparison 2607.05291; electricity-price contamination study 2607.02623; Nordic carbon-intensity preregistered comparison 2611.02895. | — | Post-release holdouts / live benchmarks. | Shows the post-cutoff idea is **crowded**. |

## 2. What this means for novelty (honest assessment)

1. **"Evaluate only on post-cutoff data" is no longer new.** At least 5–6 recent works do it (2609.10357, 2610.00589, TimesX, 2611.02895, 2607.02623, live benchmarks).
2. **Cutoffs are often undocumented.** 2607.05291 states exact pretraining cutoffs are not published for most models; Chronos-Bolt's training data is not released. RQ2 needs a documented cutoff — so it only works for models where we can cite one (e.g. Chronos-2 via its Table 6), or we must treat the cutoff as an assumption and test sensitivity to it.
3. **2609.10357 suggests "post-cutoff ≠ clean".** If familiarity survives a contamination-free hold-out, then our pre/post gap may be small *even when leakage exists*. This weakens RQ2 as a leakage detector, but makes a careful null-result analysis more valuable.

## 3. Candidate gap statements (choose one — your decision)

- **A (protocol + stability, recommended):** Existing post-cutoff studies report rankings from a single window/horizon choice. We quantify **how stable model rankings are** to window, horizon and series choice (Kendall τ over resampled windows, Holm-corrected DM tests), on user-chosen series with transparent relative-skill reporting. *Needs: confirm no one has done ranking-stability for TSFM-vs-classical.*
- **B (within-series contamination gap):** Compare each model's relative skill vs a classical reference on pre- vs post-cutoff windows **of the same series**, with bootstrap CIs, to separate "easier earlier" from "memorised". *Risk: close to 2609.10357; need to read it first.*
- **C (both):** A = main contribution, B = supporting analysis (current RQ2/RQ3 structure).

## 4. Open to-dos for Phase 2
- [ ] Read 2510.13654 in full (note both leakage types and their recommendations).
- [ ] Read 2609.10357 in full — decide whether B survives.
- [ ] Skim 2610.00589 §6.5 (post-corpus FRED-MD design) for protocol ideas.
- [ ] Search specifically for prior "ranking stability / Kendall tau" work on TSFM benchmarks.
- [ ] Record each candidate model's documented cutoff + source link in `EXPERIMENT_LOG.md`.
- [ ] Pick A, B or C and write a 5-line gap statement.

## 5. Update — closest competitor read (via summaries of the PDFs; verify yourself)

**⭐ Moghadasi & Ghaderi, *A Later Test Set Is Not a New Domain* (arXiv 2609.10357, 9 Sep 2026, BrightMind AI / UT Arlington).**
- Fixed forecast origin **1 Jan 2026** for everything; 13 models (4 classical, 3 trained per dataset, 6 pretrained: Chronos-Bolt Small/Base, Chronos-2, TimesFM 2.5/3.0, Moirai-2.0 Small); 7 groups incl. **Wikipedia pageviews and ECB daily exchange rates** (same sources as ours), Danish electricity, ERA5, CAMS.
- Cutoffs: they do **not** tabulate them; they argue a 2026 observation cannot be in a checkpoint published in 2025 (i.e. **release date as a conservative cutoff**).
- Stats: Friedman + Nemenyi, Holm-corrected Wilcoxon vs the group winner; they deliberately avoid Diebold–Mariano.
- Findings: pretrained models rank first in 6/7 groups (5 defensible); **all 13 methods tied on exchange rates** (matches our FX result: everything ≈ naive); TimesFM beats Chronos by more on Wikipedia than elsewhere → "corpus familiarity" hypothesis.
- **Their stated limits = our opening:** *single* forecast origin (rolling origins "would show variance across time"); *no horizon sweep*; five easy-to-download domains.

**Meyer et al. (2510.13654 v3) — what it actually recommends:** (1) test data must be "data that could not plausibly have appeared in any pre-training corpus"; (2) a **strict global post-training test period** — if *t* is the latest pre-training timestamp of any compared model, every test observation must be ≥ *t*+1 (model-aware, not a fixed date). It does **not** prescribe significance tests or ranking-robustness reporting; it cites Roque et al. (2025) that rankings depend heavily on which series are tested.

**Ranking-stability work already exists (so this is NOT a fresh idea in general):**
Rank Stability measure on M5 (arXiv 2108.03588); fev-bench bootstrap CIs + ranking robustness (2509.26468); TimesX appendix T, ranking vs benchmark size (2607.06973); *Evaluation Choices Decide the Forecasting Leaderboard* (2609.27867); *Cherry-Picking in Time Series Forecasting* (2412.14435); NeurIPS 2026 papers on leaderboard resolution/noise (Vernier; "Most Published Margins Fall Within the Noise") and *Same Models, Different Winners* (financial volatility, 1,044 protocols).

### Revised novelty assessment
- General "model rankings are unstable" → **crowded**. Post-cutoff hold-out → **crowded**.
- **Still open (as far as these searches show):** TSFM-vs-classical **rolling-origin windows after release dates** (many post-release origins, not one), with **horizon sweep** and **variance of the ranking across origins** — exactly what 2609.10357 says it cannot estimate. Searches were limited; a careful related-work check is still needed.

### Gap statement A′ (new working choice, replaces A)
> *Existing contamination-free evaluations of time-series foundation models score a single forecast origin after the model's release. We extend this to **rolling origins strictly after each model's release date** and a **horizon sweep**, and quantify how much the foundation-vs-classical ranking varies across origins, horizons and series, using relative MASE against naive, with paired tests per series and rank tests across series.*

Consequences: (i) **cutoff = model release date** (conservative; verify each date at its source — not done yet); (ii) pre-release windows are "possibly seen", post-release are "certainly clean", so RQ2 becomes pre- vs post-*release*; any gap is a lower bound; (iii) add cross-series Friedman/Nemenyi + Wilcoxon (as in 2609.10357) next to our per-series Diebold–Mariano, which tests a different thing (equal accuracy over time within one series); (iv) our results can be sanity-checked against theirs on FX and Wikipedia.

### Still open for Phase 2
- [ ] You read 2510.13654 and 2609.10357 yourself (summaries above are tool-generated).
- [ ] Verify release dates: Chronos-Bolt, Chronos-2, and any added model (e.g. TimesFM) — at the model cards / repos.
- [ ] A short, careful related-work search specifically for "rolling-origin post-release TSFM evaluation".
- [ ] Final decision on A′ (you + supervisor).
