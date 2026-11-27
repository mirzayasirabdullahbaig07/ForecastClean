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
