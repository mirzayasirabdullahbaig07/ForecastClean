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
    assert all(f in "MDHB" and s >= 1 for f, s, _ in SERIES.values()) and len(SERIES) == 29


def test_evaluate_caps_and_thins_without_lookahead():
    from forecastclean.evaluate import evaluate
    from forecastclean.models import naive
    from forecastclean.synthetic import seasonal_series
    s = seasonal_series(240); lens = []
    def spy(train, h, season): lens.append(len(train)); return naive(train, h)
    res = evaluate(s, {"spy": spy}, h=12, season=12, max_context=50, max_origins=4)
    assert max(lens) <= 50 and res.origin.nunique() == 4
    assert (res.target_start > s.index[res.origin - 1]).all()


def test_holm_matches_hand_example():
    from forecastclean.stability import holm
    assert np.allclose(holm([0.01, 0.04, 0.03]), [0.03, 0.06, 0.06])


def test_ranking_stability_high_for_clear_winner_low_for_ties():
    from forecastclean.stability import _stab
    rng = np.random.default_rng(0)
    clear = pd.DataFrame({"a": rng.normal(1, .1, 80), "b": rng.normal(2, .1, 80), "c": rng.normal(3, .1, 80)})
    tie = pd.DataFrame({k: rng.normal(1, .5, 30) for k in "abc"})
    assert _stab(clear, 200, 0)["mean_tau"] > 0.95 and _stab(clear, 200, 0)["p_best_same"] > 0.95
    assert _stab(tie, 200, 0)["p_best_same"] < 0.8


def test_eval_start_and_new_baselines():
    from forecastclean.evaluate import evaluate
    from forecastclean.models import theta, comb, BASELINES
    from forecastclean.synthetic import seasonal_series
    s = seasonal_series(240)
    res = evaluate(s, {"naive": BASELINES["naive"], "theta": theta}, h=12, season=12, eval_start="2012-01-01")
    assert (res.target_start >= pd.Timestamp("2012-01-01")).all() and res.origin.nunique() >= 2
    f = comb(s.to_numpy(), 12, 12)
    assert f.shape == (12,) and np.isfinite(f).all()
    assert np.isfinite(theta(s.to_numpy(), 12, 1)).all()


def _fake_torch(monkeypatch):
    import sys, types
    t = types.SimpleNamespace(tensor=lambda x, dtype=None: np.asarray(x, float), float32=None,
                              cuda=types.SimpleNamespace(is_available=lambda: False))
    monkeypatch.setitem(sys.modules, "torch", t)


def test_chronos_adapter_handles_bolt_and_chronos2_output_shapes(monkeypatch):
    _fake_torch(monkeypatch)
    from forecastclean.models import chronos_forecaster
    seen = {}
    class Bolt:                                        # returns one tensor [batch, h, Q]
        def predict_quantiles(self, x, prediction_length, quantile_levels):
            seen["len"] = len(x); h = prediction_length
            return np.arange(h, dtype=float).reshape(1, h, 1) + 5, None
    class Chronos2:                                    # returns a LIST of [variates, h, Q]
        def predict_quantiles(self, x, prediction_length, quantile_levels):
            h = prediction_length
            return [np.arange(h, dtype=float).reshape(1, h, 1) + 7], [None]
    tr = np.arange(50.0)
    f1 = chronos_forecaster("amazon/chronos-bolt-tiny", pipeline=Bolt()); f2 = chronos_forecaster("amazon/chronos-2", pipeline=Chronos2())
    assert f1(tr, 6).tolist() == [5, 6, 7, 8, 9, 10] and seen["len"] == 50      # context passed unchanged, no look-ahead
    assert f2(tr, 4).tolist() == [7, 8, 9, 10]
    assert f1.__name__ == "chronos-bolt-tiny" and f2.__name__ == "chronos-2"


def test_chronos_adapter_feeds_3d_input_to_chronos2_style_pipelines(monkeypatch):
    """Real Chronos-2 raises ValueError on 1-d input (seen on Colab, 2025-11-25); the adapter must send (1, 1, T)."""
    _fake_torch(monkeypatch)
    from forecastclean.models import chronos_forecaster
    shapes = []
    class Strict3D:                                    # name-agnostic: rejects 1-d like the real pipeline
        def predict_quantiles(self, x, prediction_length, quantile_levels):
            shapes.append(np.asarray(x).shape)
            if np.asarray(x).ndim != 3:
                raise ValueError("Expected 3-d tensor")
            return [np.arange(prediction_length, dtype=float).reshape(1, prediction_length, 1)], [None]
    class Chronos2Pipeline(Strict3D):                  # class name triggers 3-d up front
        pass
    tr = np.arange(30.0)
    assert chronos_forecaster("amazon/chronos-2", pipeline=Chronos2Pipeline())(tr, 3).tolist() == [0, 1, 2]
    assert shapes == [(1, 1, 30)]
    shapes.clear()
    g = chronos_forecaster("x/unknown", pipeline=Strict3D())      # unknown class: falls back after one rejection, then remembers
    assert g(tr, 3).tolist() == [0, 1, 2] and g(tr, 3).tolist() == [0, 1, 2]
    assert shapes == [(30,), (1, 1, 30), (1, 1, 30)]


def test_registry_global_cutoff_and_unknown_model():
    import pytest
    from forecastclean.registry import clean_from
    assert clean_from(["chronos-bolt-tiny", "chronos-2"]) == pd.Timestamp("2025-10-31")
    assert clean_from([]) is None
    with pytest.raises(KeyError):
        clean_from(["not-a-real-model"])


def test_batch_post_only_horizon_sweep_and_skip_empty(tmp_path):
    import argparse
    from forecastclean.batch import run_batch
    from forecastclean.synthetic import seasonal_series
    d = tmp_path / "raw"; d.mkdir()
    s = seasonal_series(400, season=7, start="2024-01-01")
    pd.DataFrame({"date": pd.date_range("2024-01-01", periods=400, freq="D"), "value": s.values}).to_csv(d / "wiki_Python.csv", index=False)
    old = seasonal_series(120, season=12, start="2010-01-01")                 # ends 2019 -> nothing after cutoff
    pd.DataFrame({"date": old.index, "value": old.values}).to_csv(d / "fredmd_UNRATE.csv", index=False)
    args = argparse.Namespace(data=str(d), out=str(tmp_path / "o"), only=None, chronos=None, cutoff=None, clean_from="2024-09-01",
                              release_cutoff=False, post_only=True, horizon_sweep=True, max_context=100, max_origins=5, eval_start="2015-01-01")
    assert run_batch(args) == 0
    summ = pd.read_csv(tmp_path / "o" / "summary.csv")
    assert set(summ.series) == {"wiki_Python"} and summ.h.nunique() == 4 and set(summ.period) == {"post_cutoff"}
    assert (tmp_path / "o" / "horizon_rank_tau.csv").exists()


def test_relative_mase_finite_when_reference_is_exact_at_some_origins():
    """Regression: h=1 FX/wiki windows where naive is exactly right produced inf under a per-origin geometric mean (Colab, 2025-11-25)."""
    from forecastclean.evaluate import skill_table
    rows = []
    for i, (a, b) in enumerate([(0.0, 0.5), (0.4, 0.5), (0.2, 0.5)]):
        o = pd.Timestamp("2026-01-01") + pd.Timedelta(days=i)
        for m, v in (("naive", a), ("ets", b)):
            rows.append(dict(origin=o, target_start=o, target_end=o, model=m, mase=v))
    t = skill_table(pd.DataFrame(rows), reference="naive").set_index("model")
    assert np.isfinite(t.loc["ets", "rel_mase"]) and abs(t.loc["ets", "rel_mase"] - 0.5 / 0.2) < 1e-9


def test_evaluate_eval_end_keeps_only_windows_ending_before_it():
    from forecastclean.evaluate import evaluate
    from forecastclean.models import naive
    idx = pd.date_range("2020-01-01", periods=200, freq="D"); s = pd.Series(np.arange(200.0), index=idx)
    r = evaluate(s, {"naive": naive}, h=5, season=1, eval_start="2020-02-01", eval_end="2020-04-01")
    assert len(r) > 0 and r.target_end.max() <= pd.Timestamp("2020-04-01") and r.target_start.min() >= pd.Timestamp("2020-02-01")


def test_gap_did_detects_a_model_that_is_only_good_before_release():
    """A fake 'pretrained' model that is seasonal-naive-good only on early context (pre-release) must show DiD > 0;
    a model that is equally good before and after must show DiD ~ 0 (classical models absorb the shared shift)."""
    from forecastclean.gap import gap_for_series
    from forecastclean.models import naive
    from forecastclean.models import seasonal_naive
    from forecastclean.synthetic import seasonal_series
    ser = seasonal_series(n=1000, season=7, seed=1); ser.index = pd.date_range("2018-01-01", periods=len(ser), freq="D")
    rel = ser.index[600].strftime("%Y-%m-%d")
    leaky = lambda tr, h, season=1: seasonal_naive(tr, h, season) if len(tr) < 600 else naive(tr, h, season)
    honest = lambda tr, h, season=1: seasonal_naive(tr, h, season)
    _, a = gap_for_series(ser, 7, 7, "leaky", leaky, rel, max_origins=15, max_context=None, eval_start="2018-04-01", min_windows=3)
    _, b = gap_for_series(ser, 7, 7, "honest", honest, rel, max_origins=15, max_context=None, eval_start="2018-04-01", min_windows=3)
    assert a["did"] > 0.2 and abs(b["did"]) < a["did"]


def test_gap_skips_series_with_too_few_post_windows():
    from forecastclean.gap import gap_for_series
    from forecastclean.models import naive
    idx = pd.date_range("2020-01-01", periods=120, freq="D"); s = pd.Series(np.random.default_rng(0).normal(size=120).cumsum() + 50, index=idx)
    rows, why = gap_for_series(s, 1, 5, "m", naive, "2020-04-25", max_origins=10, max_context=None, eval_start="2020-02-01")
    assert rows is None and "post windows" in why


def test_every_series_has_a_fetch_route_and_sane_metadata():
    from forecastclean.data import SERIES, WIKI_ARTICLES
    assert len(SERIES) >= 25 and len(set(SERIES)) == len(SERIES)
    for name, (freq, season, desc) in SERIES.items():
        kind, _, key = name.partition("_")
        assert kind in {"fredmd", "ecb", "neso", "wiki"} and freq in {"M", "D", "H", "B"} and season >= 1 and desc
        if kind == "wiki":
            assert key in WIKI_ARTICLES
        if kind == "ecb":
            assert key.startswith("EUR") and len(key) == 6


def test_gap_uses_identical_full_context_before_and_after_release():
    """Regression (found on the 22-series Colab run): short early contexts must not enter the pre-release period."""
    from forecastclean.gap import gap_for_series
    from forecastclean.models import naive
    seen = []
    def spy(tr, h, season=1):
        seen.append(len(tr)); return naive(tr, h, season)
    ser = pd.Series(np.random.default_rng(0).normal(size=1500).cumsum() + 100, index=pd.date_range("2018-01-01", periods=1500, freq="D"))
    rel = "2021-06-01"
    rows, _ = gap_for_series(ser, 1, 7, "spy", spy, rel, max_origins=20, max_context=400, eval_start="2018-01-01", min_windows=3, drop=("arima", "ets"))
    assert rows is not None and set(seen) == {400}


def test_gap_aggregate_has_overall_and_group_rows():
    from forecastclean.gap import aggregate
    summ = pd.DataFrame({"chronos": ["m"] * 4, "series": ["ecb_EURUSD", "ecb_EURGBP", "wiki_A", "neso_demand_hourly"],
                         "did": [0.0, 0.1, -0.2, 0.3]})
    a = aggregate(summ, n_boot=200).set_index("group")
    assert set(a.index) == {"all", "fx", "wikipedia", "electricity"} and a.loc["all", "n_series"] == 4 and a.loc["fx", "n_positive"] == 1


def test_tuned_models_selection_rule_and_outputs():
    """AutoARIMA only on non-seasonal series (too slow otherwise); the tuned forecasters return finite length-h vectors."""
    pytest = __import__("pytest"); pytest.importorskip("statsforecast")
    from forecastclean.models import tuned_models, auto_ets, auto_theta, auto_arima
    assert set(tuned_models(1)) == {"auto_ets", "auto_theta", "auto_arima"} and set(tuned_models(7)) == {"auto_ets", "auto_theta"}
    from forecastclean.synthetic import seasonal_series
    y = seasonal_series(n=240, season=12, seed=3).to_numpy()
    for f in (auto_ets, auto_theta, auto_arima):
        out = f(y, 6, 12)
        assert out.shape == (6,) and np.all(np.isfinite(out))
    # sanity: tuned ETS must beat naive on a strongly seasonal series
    tr, te = y[:-12], y[-12:]
    assert np.mean(np.abs(auto_ets(tr, 12, 12) - te)) < np.mean(np.abs(np.repeat(tr[-1], 12) - te))


def test_auto_forecaster_falls_back_to_naive_when_the_fit_fails():
    from forecastclean import models
    out = models._auto("DoesNotExist", np.array([1.0, 2.0, 3.0]), 4, 1)
    assert out.tolist() == [3.0, 3.0, 3.0, 3.0]


def test_gap_with_tuned_baselines_adds_auto_rows():
    pytest = __import__("pytest"); pytest.importorskip("statsforecast")
    from forecastclean.gap import gap_for_series
    from forecastclean.models import naive
    idx = pd.date_range("2018-01-01", periods=900, freq="D")
    s = pd.Series(np.random.default_rng(1).normal(size=900).cumsum() + 100, index=idx)
    rows, info = gap_for_series(s, 1, 5, "m", naive, "2020-06-01", max_origins=8, max_context=300, eval_start="2018-01-01",
                                min_windows=3, drop=("arima", "comb", "ets", "theta"), tuned=True)
    assert rows is not None and {"auto_ets", "auto_theta", "auto_arima"} <= set(rows.model)


def test_across_series_ranking_excludes_models_missing_on_some_series():
    from forecastclean.batch import _complete_models
    m = pd.DataFrame({"naive": [0.0, 0.0, 0.0], "ets": [-0.2, -0.1, -0.3], "auto_arima": [0.0, np.nan, np.nan]},
                     index=["fx", "wiki", "neso"])
    full, partial = _complete_models(m)
    assert list(full.columns) == ["naive", "ets"] and partial == ["auto_arima"]
