import argparse
from pathlib import Path


def main(argv=None):
    p = argparse.ArgumentParser(prog="forecastclean")
    sub = p.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("simulate", help="Pipeline check on synthetic series"); s.add_argument("--out", default="results/simulate")
    d = sub.add_parser("download", help="Download + clean the real series (needs internet)")
    d.add_argument("--out", default="data"); d.add_argument("--only", nargs="*", help="series names, default all")
    r = sub.add_parser("run", help="Evaluate on YOUR csv (columns: date,value)")
    r.add_argument("--csv", required=True); r.add_argument("--date-col", default="date"); r.add_argument("--value-col", default="value")
    r.add_argument("--h", type=int, default=12); r.add_argument("--season", type=int, default=1)
    r.add_argument("--cutoff", help="model training cutoff date YYYY-MM-DD for pre/post split")
    r.add_argument("--chronos", help="e.g. amazon/chronos-bolt-tiny (needs chronos-forecasting)")
    r.add_argument("--returns", action="store_true", help="forecast log-returns instead of levels")
    r.add_argument("--out", default="results/run")
    args = p.parse_args(argv)
    if args.cmd == "download":
        from .data import download_all
        return download_all(args.out, args.only)
    import numpy as np, pandas as pd
    from .evaluate import evaluate, skill_table
    from .models import BASELINES
    pd.set_option("display.width", 200); out = Path(args.out); out.mkdir(parents=True, exist_ok=True)
    fc = dict(BASELINES)
    if args.cmd == "simulate":
        from .synthetic import seasonal_series
        ser, season, cutoff = seasonal_series(), 12, "2012-12-01"
    else:
        df = pd.read_csv(args.csv, parse_dates=[args.date_col]).sort_values(args.date_col)
        ser = df.set_index(args.date_col)[args.value_col].astype(float)
        if args.returns:
            ser = np.log(ser).diff().dropna()
        season, cutoff = args.season, args.cutoff
        if args.chronos:
            from .models import chronos_forecaster
            fc["chronos"] = chronos_forecaster(args.chronos)
    h = 12 if args.cmd == "simulate" else args.h
    res = evaluate(ser, fc, h=h, season=season)
    t = skill_table(res, "seasonal_naive" if season > 1 else "naive", cutoff)
    print(("SYNTHETIC - pipeline check only\n" if args.cmd == "simulate" else "") + t.round(3).to_string(index=False))
    t.round(4).to_csv(out / "skill.csv", index=False)


if __name__ == "__main__":
    main()
