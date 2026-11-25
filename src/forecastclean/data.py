"""Download + clean the real series used in ForecastClean (run on YOUR machine; needs internet).

Every series is saved as data/raw/<name>.csv with columns `date,value`, which `forecastclean run`
reads directly (--date-col date --value-col value). A manifest (data/MANIFEST.csv) records URL,
retrieval time, row count, first/last date and a SHA-256 of each file for reproducibility.

IMPORTANT: sources/licences are CANDIDATES. Confirm each licence before redistributing data or
publishing (see DATA_SOURCES.md). Raw data is git-ignored; only the manifest is committed.
The download code could not be run in the sandbox where it was written (no network there); the
cleaning functions are unit-tested on synthetic data in tests/test_data.py.
"""
from __future__ import annotations

import hashlib
import io
import json
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

UA = "ForecastClean-research/0.1 (academic; contact: see GitHub repo mirzayasirabdullahbaig07/ForecastClean)"
FRED_MD_URL = "https://www.stlouisfed.org/-/media/project/frbstl/stlouisfed/research/fred-md/monthly/current.csv"
ECB_URL = "https://data-api.ecb.europa.eu/service/data/EXR/D.{ccy}.EUR.SP00.A?format=csvdata&startPeriod=2000-01-01"
NESO_PACKAGE_ID = "8f2fe0af-871c-488d-8bad-960426f24601"   # NESO "Historic Demand Data" dataset
NESO_API = "https://api.neso.energy/api/3/action/"
WIKI_URL = ("https://wikimedia.org/api/rest_v1/metrics/pageviews/per-article/en.wikipedia/"
            "all-access/user/{article}/daily/{start}/{end}")

# name -> (frequency, season, short description). season=1 means NO seasonality: FRED-MD UNRATE/CPIAUCSL/INDPRO are
# seasonally adjusted, and FX has no weekly cycle.
SERIES = {
    "fredmd_UNRATE": ("M", 1, "US unemployment rate (FRED-MD)"),
    "fredmd_CPIAUCSL": ("M", 1, "US CPI all items (FRED-MD)"),
    "fredmd_INDPRO": ("M", 1, "US industrial production index (FRED-MD)"),
    "neso_demand_daily": ("D", 7, "GB national demand, daily mean MW (NESO)"),
    "neso_demand_hourly": ("H", 24, "GB national demand, hourly mean MW (NESO)"),
    "ecb_EURUSD": ("B", 1, "EUR/USD ECB reference rate, daily (near random walk)"),
    "ecb_EURGBP": ("B", 1, "EUR/GBP ECB reference rate, daily (near random walk)"),
    "wiki_Python": ("D", 7, "en.wikipedia pageviews: Python_(programming_language)"),
    "wiki_Christmas": ("D", 7, "en.wikipedia pageviews: Christmas"),
}


# ---------- pure cleaning functions (unit-tested) ----------
def clean_fred_md(raw: pd.DataFrame, column: str) -> pd.DataFrame:
    """FRED-MD csv: col 'sasdate', first data row is 'Transform:' codes (dropped); levels, not transformed."""
    df = raw.copy()
    df = df[df["sasdate"].astype(str).str.lower() != "transform:"]
    out = pd.DataFrame({"date": pd.to_datetime(df["sasdate"], format="%m/%d/%Y"),
                        "value": pd.to_numeric(df[column], errors="coerce")})
    return out.dropna().sort_values("date").reset_index(drop=True)


def clean_ecb(raw: pd.DataFrame) -> pd.DataFrame:
    out = pd.DataFrame({"date": pd.to_datetime(raw["TIME_PERIOD"]),
                        "value": pd.to_numeric(raw["OBS_VALUE"], errors="coerce")})
    return out.dropna().sort_values("date").reset_index(drop=True)


def _neso_timestamps(df: pd.DataFrame) -> pd.Series:
    d = pd.to_datetime(df["SETTLEMENT_DATE"], format="mixed", dayfirst=True).dt.normalize()
    return d + pd.to_timedelta((df["SETTLEMENT_PERIOD"].astype(int) - 1) * 30, unit="min")


def clean_neso(raw: pd.DataFrame, freq: str) -> pd.DataFrame:
    """National demand (ND, MW) from half-hourly rows to daily or hourly means.
    Caveat: on clock-change days (46/50 periods) timestamps are built from settlement periods, so the
    hourly series is approximate on those ~2 days/year; the daily series is exact (grouped by settlement date)."""
    df = raw[raw["SETTLEMENT_PERIOD"].notna()].copy()
    if "FORECAST_ACTUAL_INDICATOR" in df.columns:
        df = df[df["FORECAST_ACTUAL_INDICATOR"].astype(str).str.upper() != "F"]
    df["ND"] = pd.to_numeric(df["ND"], errors="coerce")
    df = df.dropna(subset=["ND"])
    if freq == "D":
        s = df.groupby(pd.to_datetime(df["SETTLEMENT_DATE"], format="mixed", dayfirst=True).dt.normalize())["ND"].mean()
    else:
        s = df.groupby(_neso_timestamps(df).dt.floor("h"))["ND"].mean()
    s = s.sort_index()
    return pd.DataFrame({"date": s.index, "value": s.values}).reset_index(drop=True)


def clean_wiki(items: list[dict]) -> pd.DataFrame:
    out = pd.DataFrame({"date": pd.to_datetime([i["timestamp"][:8] for i in items], format="%Y%m%d"),
                        "value": [float(i["views"]) for i in items]})
    return out.sort_values("date").reset_index(drop=True)


# ---------- network ----------
def _get(url: str, timeout: int = 120) -> bytes:
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read()


def _neso_raw() -> pd.DataFrame:
    """Discover all yearly demand CSV resources via the CKAN API, download and concatenate them."""
    pkg = json.loads(_get(NESO_API + "package_show?id=" + NESO_PACKAGE_ID))["result"]
    frames = []
    for res in pkg["resources"]:
        if str(res.get("format", "")).upper() == "CSV" and "demand" in str(res.get("name", "")).lower() \
                and any(ch.isdigit() for ch in str(res.get("name", ""))):
            try:
                frames.append(pd.read_csv(io.BytesIO(_get(res["url"])), low_memory=False))
            except Exception as e:                      # skip a bad year but say so
                print(f"  ! skipped NESO resource {res.get('name')}: {e}")
    if not frames:
        raise RuntimeError("No NESO demand CSV resources found")
    cols = ["SETTLEMENT_DATE", "SETTLEMENT_PERIOD", "ND"]
    frames = [f[[c for c in f.columns if c in cols + ["FORECAST_ACTUAL_INDICATOR"]]] for f in frames]
    return pd.concat(frames, ignore_index=True)


def fetch(name: str, fred_vintage: str | None = None) -> tuple[pd.DataFrame, str]:
    """Return (clean date,value frame, source URL) for a named series."""
    kind, _, key = name.partition("_")
    if kind == "fredmd":
        url = FRED_MD_URL if not fred_vintage else FRED_MD_URL.replace("current.csv", f"{fred_vintage}.csv")
        raw = pd.read_csv(io.BytesIO(_get(url)))
        return clean_fred_md(raw, key), url
    if kind == "ecb":
        url = ECB_URL.format(ccy=key.replace("EUR", ""))
        return clean_ecb(pd.read_csv(io.BytesIO(_get(url)))), url
    if kind == "neso":
        return clean_neso(_neso_raw(), SERIES[name][0]), NESO_API + "package_show?id=" + NESO_PACKAGE_ID
    if kind == "wiki":
        article = {"Python": "Python_(programming_language)", "Christmas": "Christmas"}[key]
        end = datetime.now(timezone.utc).strftime("%Y%m%d")
        url = WIKI_URL.format(article=urllib.parse.quote(article, safe="()_"), start="20150701", end=end)
        return clean_wiki(json.loads(_get(url))["items"]), url
    raise KeyError(name)


def download_all(out_dir="data", only=None, fred_vintage=None) -> int:
    out = Path(out_dir); raw = out / "raw"; raw.mkdir(parents=True, exist_ok=True)
    names = only or list(SERIES)
    rows, failed = [], []
    for n in names:
        try:
            df, url = fetch(n, fred_vintage)
            path = raw / f"{n}.csv"; df.to_csv(path, index=False)
            rows.append(dict(name=n, freq=SERIES[n][0], season=SERIES[n][1], url=url,
                             retrieved_utc=datetime.now(timezone.utc).isoformat(timespec="seconds"),
                             n_rows=len(df), first=df.date.min().date(), last=df.date.max().date(),
                             sha256=hashlib.sha256(path.read_bytes()).hexdigest()))
            print(f"ok   {n}: {len(df)} rows, {df.date.min().date()} -> {df.date.max().date()}")
        except Exception as e:
            failed.append(n); print(f"FAIL {n}: {e}")
    if rows:
        mpath = out / "MANIFEST.csv"
        new = pd.DataFrame(rows)
        if mpath.exists():
            old = pd.read_csv(mpath); new = pd.concat([old[~old.name.isin(new.name)], new])
        new.to_csv(mpath, index=False)
    return 1 if failed else 0
