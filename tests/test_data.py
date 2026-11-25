import numpy as np, pandas as pd
from forecastclean.data import clean_fred_md, clean_ecb, clean_neso, clean_wiki, SERIES


def test_fred_md_drops_transform_row_and_parses_dates():
    raw = pd.DataFrame({"sasdate": ["Transform:", "1/1/2020", "2/1/2020", "3/1/2020"],
                        "UNRATE": [2, 3.5, 3.5, np.nan]})
    out = clean_fred_md(raw, "UNRATE")
    assert list(out.columns) == ["date", "value"] and len(out) == 2     # transform row + NaN dropped
    assert out.date.iloc[0] == pd.Timestamp("2020-01-01") and out.value.tolist() == [3.5, 3.5]


def test_ecb_clean_sorts_and_drops_missing():
    raw = pd.DataFrame({"TIME_PERIOD": ["2024-01-03", "2024-01-02", "2024-01-04"], "OBS_VALUE": [1.1, 1.2, None]})
    out = clean_ecb(raw)
    assert out.date.tolist() == [pd.Timestamp("2024-01-02"), pd.Timestamp("2024-01-03")]


def _neso_fake(days=3):
    rows = []
    for d in range(days):
        for p in range(1, 49):
            rows.append(dict(SETTLEMENT_DATE=f"0{d+1}/01/2025", SETTLEMENT_PERIOD=p, ND=1000 * (d + 1) + p, FORECAST_ACTUAL_INDICATOR="A"))
    return pd.DataFrame(rows)


def test_neso_daily_and_hourly():
    raw = _neso_fake()
    daily = clean_neso(raw, "D")
    assert len(daily) == 3 and np.isclose(daily.value.iloc[0], 1000 + np.mean(range(1, 49)))
    hourly = clean_neso(raw, "H")
    assert len(hourly) == 72 and hourly.date.is_monotonic_increasing
    assert np.isclose(hourly.value.iloc[0], 1000 + 1.5)                    # mean of periods 1,2


def test_neso_ignores_forecast_rows():
    raw = _neso_fake(1); raw.loc[0, "FORECAST_ACTUAL_INDICATOR"] = "F"; raw.loc[0, "ND"] = 10**9
    assert clean_neso(raw, "D").value.iloc[0] < 10**6


def test_wiki_clean():
    out = clean_wiki([{"timestamp": "2025010200", "views": 5}, {"timestamp": "2025010100", "views": 3}])
    assert out.value.tolist() == [3.0, 5.0] and out.date.iloc[0] == pd.Timestamp("2025-01-01")


def test_series_registry_consistent():
    assert all(f in "MDHB" and s >= 1 for f, s, _ in SERIES.values()) and len(SERIES) == 9
