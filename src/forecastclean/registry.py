"""Conservative 'clean-from' dates for pretrained forecasters.

No Chronos model publishes a training-data cutoff. Following the logic of Meyer et al. (arXiv 2510.13654) and
Moghadasi & Ghaderi (2609.10357), we use the model's RELEASE date: data observed after it cannot be in its
training set. Any pre/post gap measured with these dates is therefore a LOWER bound (pre-release windows may
include unseen data). Dates are deliberately rounded LATER (more conservative) where the exact day is unclear.
Re-verify each at the source before publishing.
"""
from __future__ import annotations

import pandas as pd

RELEASE = {
    # name: (clean_from date, evidence)
    "chronos-bolt-tiny": ("2024-12-01", "AutoGluon 1.2.0 (introduced Chronos-Bolt) files dated 2024-11-26; AWS blog: Nov 2024"),
    "chronos-bolt-mini": ("2024-12-01", "same as chronos-bolt-tiny"),
    "chronos-bolt-small": ("2024-12-01", "same as chronos-bolt-tiny"),
    "chronos-bolt-base": ("2024-12-01", "same as chronos-bolt-tiny"),
    "chronos-2": ("2025-10-31", "Amazon Science blog 2025-10-20; arXiv 2510.15821 submitted 2025-10-17"),
    "timesfm-2.5": ("2025-10-03", "README: 2.5 out 2025-09-15; HF card for google/timesfm-2.5-200m-pytorch: weights last updated 2025-10-02 (QKV fusion) -> clean-from the day after"),
    "timesfm-2.5-200m-pytorch": ("2025-10-03", "same as timesfm-2.5 (the id batch/gap derive from google/timesfm-2.5-200m-pytorch)"),
}


def clean_from(model_names) -> pd.Timestamp | None:
    """Latest release date among the given pretrained models (Meyer et al.: global, model-aware cutoff).
    Raises KeyError for an unknown model so we never silently guess a cutoff."""
    dates = [pd.Timestamp(RELEASE[n][0]) for n in model_names]
    return max(dates) if dates else None
