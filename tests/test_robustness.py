import numpy as np
import pandas as pd

from forecastclean import robustness as rb


def _summary(vals, chronos="m"):
    names = [f"ecb_X{i}" for i in range(3)] + ["wiki_Christmas", "wiki_Python", "neso_demand_daily"]
    return pd.DataFrame(dict(chronos=chronos, series=names[:len(vals)], did=vals))


def _windows():
    rows = []
    for s, gc in [("ecb_A", 0.1), ("wiki_Easter", -0.3), ("wiki_Python", 0.2)]:
        for m, g in [("m", gc), ("ets", 0.0), ("theta", 0.1), ("drift", 0.0)]:
            rows.append(dict(series=s, model=m, chronos="m", rel_pre=1.0, rel_post=np.exp(g), gap=g))
    return pd.DataFrame(rows)


def test_reference_sensitivity_median_and_single_models():
    r = rb.reference_sensitivity(_windows()).set_index("reference")
    assert {"median", "mean", "only_ets", "only_theta", "median_ex_drift"} <= set(r.index)
    # series ecb_A: gap_m=0.1, classical gaps {0,0.1,0}: median 0 -> DiD 0.1; only_theta -> 0.0
    assert abs(r.loc["only_theta", "mean_did"] - np.mean([0.0, -0.4, 0.1])) < 1e-9


def test_event_split_groups_wikipedia_by_event_page():
    out = rb.event_split(_summary([0.1, 0.0, -0.1, 0.5, -0.2, 0.3])).set_index("group")
    assert out.loc["wiki_event", "n_series"] == 1 and out.loc["wiki_other", "n_series"] == 1
    assert out.loc["fx", "n_series"] == 3 and out.loc["electricity", "n_series"] == 1


def test_cluster_boot_collapses_fx_into_one_unit():
    out = rb.cluster_boot(_summary([0.1, 0.1, 0.1, 0.5, -0.2, 0.3]))
    assert out.n_units.iloc[0] == 4          # 3 non-FX + 1 collapsed FX unit
    assert abs(out.mean_did.iloc[0] - np.mean([0.5, -0.2, 0.3, 0.1])) < 1e-9


def test_leave_one_out_finds_the_influential_series():
    out = rb.leave_one_out(_summary([0.0, 0.0, 0.0, 5.0, 0.0, 0.0]))
    assert out.most_influential.iloc[0] == "wiki_Christmas" and abs(out.mean_without_it.iloc[0]) < 1e-9


def _origins(leak, n=40, seed=0):
    rng = np.random.default_rng(seed); rows = []
    for s in ["a", "b", "c"]:
        for period, boost in [("pre", 0.0), ("post", leak)]:
            for o in range(n):
                base = 1.0 + 0.2 * rng.standard_normal()
                for model, f in [("naive", 1.0), ("ets", 1.0), ("theta", 1.0), ("m", 0.6 * np.exp(boost))]:
                    rows.append(dict(series=s, chronos="m", model=model, period=period, origin=o, h=7,
                                     mase=abs(base * f * (1 + 0.05 * rng.standard_normal()))))
    return pd.DataFrame(rows)


def test_block_bootstrap_detects_leakage_signature():
    out = rb.block_did(_origins(leak=0.5), block=5, n_boot=300)
    assert out.mean_did.iloc[0] > 0.3 and out.ci_lo.iloc[0] > 0           # model lost skill after release only


def test_block_bootstrap_null_interval_contains_zero():
    out = rb.block_did(_origins(leak=0.0), block=5, n_boot=300)
    assert out.ci_lo.iloc[0] < 0 < out.ci_hi.iloc[0]


def test_gap_collect_returns_per_window_mase_usable_by_block_bootstrap():
    from forecastclean.gap import gap_for_series
    from forecastclean.models import naive, seasonal_naive
    from forecastclean.synthetic import seasonal_series
    ser = seasonal_series(n=1000, season=7, seed=1); ser.index = pd.date_range("2018-01-01", periods=len(ser), freq="D")
    got = []
    rows, _ = gap_for_series(ser, 7, 7, "m", seasonal_naive, ser.index[600].strftime("%Y-%m-%d"), max_origins=15, max_context=None,
                             eval_start="2018-04-01", min_windows=3, drop=("arima", "ets"), collect=got)
    w = got[0]
    assert set(w.period) == {"pre", "post"} and {"origin", "model", "mase"} <= set(w.columns) and "naive" in set(w.model)
    # per-window values reproduce the per-period relative MASE of the summary rows
    m = w[w.period == "post"].groupby("model").mase.mean(); assert abs(m["m"] / m["naive"] - rows.set_index("model").loc["m", "rel_post"]) < 1e-3
    w = w.assign(series="s", chronos="m", h=7)
    assert len(rb.block_did(w, block=3, n_boot=50)) == 1


def test_match_days_restricts_both_periods_to_the_same_calendar_span():
    """Calendar-matched gap design: pre origins start no earlier than release - match_days, post targets end no later than
    release + match_days, and both periods get a comparable number of windows."""
    import pandas as pd
    from forecastclean.gap import gap_for_series
    from forecastclean.models import naive
    from forecastclean.synthetic import seasonal_series
    ser = seasonal_series(n=1200, season=7, seed=2); ser.index = pd.date_range("2018-01-01", periods=len(ser), freq="D")
    rel = ser.index[700]; md = 210
    cl = []
    rows, info = gap_for_series(ser, 7, 7, "m", naive, rel.strftime("%Y-%m-%d"), max_origins=10_000, max_context=None,
                                eval_start="2018-04-01", min_windows=3, collect=cl, match_days=md)
    assert rows is not None
    c = pd.concat(cl); dates = ser.index[c.origin.to_numpy()]
    pre = dates[(c.period == "pre").to_numpy()]; post = dates[(c.period == "post").to_numpy()]
    assert pre.min() >= rel - pd.Timedelta(days=md) and post.max() + pd.Timedelta(days=6) <= rel + pd.Timedelta(days=md)
    assert abs(info["n_pre"] - info["n_post"]) <= 2 and info["n_pre"] >= 25


def test_cluster_boot_has_no_nan_when_a_subset_contains_no_fx_series():
    import pandas as pd
    from forecastclean import robustness as rb
    s = pd.DataFrame({"chronos": "m", "series": [f"wiki_{k}" for k in "ABCDEF"], "did": [-0.4, -0.1, 0.2, -0.3, -0.6, 0.1]})
    out = rb.cluster_boot(s, n_boot=200)
    assert int(out.n_units.iloc[0]) == 6 and out.mean_did.notna().all() and out.ci_lo.notna().all()


def test_pre_end_moves_the_pre_period_before_the_given_date():
    import pandas as pd
    from forecastclean.gap import gap_for_series
    from forecastclean.models import naive
    from forecastclean.synthetic import seasonal_series
    ser = seasonal_series(n=1500, season=7, seed=4); ser.index = pd.date_range("2018-01-01", periods=len(ser), freq="D")
    rel = ser.index[1100]; pre_end = ser.index[700]; cl = []
    rows, info = gap_for_series(ser, 7, 7, "m", naive, rel.strftime("%Y-%m-%d"), max_origins=10_000, max_context=None, eval_start="2018-04-01",
                                min_windows=3, collect=cl, match_days=200, pre_end=pre_end.strftime("%Y-%m-%d"))
    assert rows is not None
    import pandas as _p; c = _p.concat(cl); pre = ser.index[c[c.period == "pre"].origin.to_numpy()]
    assert pre.max() + _p.Timedelta(days=6) <= pre_end and pre.min() >= pre_end - _p.Timedelta(days=200)
