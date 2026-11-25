# Experiment log

| date | command | seed | data version | result | next step |
|---|---|---|---|---|---|
| 2026-11-25 | `python -m pytest -q` | n/a | synthetic | 6 passed | start Phase 2 (literature) |
| 2026-11-25 | `python -m pytest -q` (after adding data module) | n/a | synthetic | 12 passed | run `forecastclean download` on PC |
| 2026-11-25 | `forecastclean simulate` | 0 | synthetic seasonal (n=240) | pipeline runs; ETS/seasonal-naive beat naive as expected (pipeline check only, NOT a finding) | choose real series |

## Data sources (fill in during Phase 3)
| series | source URL | licence | frequency | season | notes |
|---|---|---|---|---|---|

## Foundation-model training cutoffs (fill in during Phase 4)
| model | documented cutoff | link to model card |
|---|---|---|
