import numpy as np, pandas as pd
from forecastclean.models import naive, seasonal_naive, drift, BASELINES
from forecastclean.evaluate import mase, rolling_origins, evaluate, dm_test, skill_table
from forecastclean.synthetic import seasonal_series, random_walk


def test_basic_forecasters():
    y = np.array([1., 2, 3, 4, 5, 6, 7, 8])
    assert naive(y, 3).tolist() == [8, 8, 8]
    assert seasonal_naive(np.array([1., 2, 3, 1, 2, 3]), 5, 3).tolist() == [1, 2, 3, 1, 2]
    assert np.allclose(drift(y, 2), [9, 10])


def test_mase_scaling():
    train = np.array([0., 2, 4, 6])            # naive in-sample MAE = 2
    assert abs(mase(np.array([8.]), np.array([6.]), train) - 1.0) < 1e-12
    assert abs(mase(np.array([8.]), np.array([8.]), train)) < 1e-12


def test_rolling_origins_never_look_ahead():
    n, h = 100, 12
    for t in rolling_origins(n, 40, h, 12):
        assert t + h <= n and t >= 40
    s = seasonal_series(100)
    seen = {}
    def spy(train, hh, season):
        seen.setdefault("lens", []).append(len(train)); seen.setdefault("last", []).append(train[-1]); return naive(train, hh)
    res = evaluate(s, {"spy": spy}, h=12, initial=40, step=12, season=12)
    assert seen["lens"][0] == 40 and np.isclose(seen["last"][0], s.iloc[39])   # context ends right before target
    assert (res.target_start > s.index[res.origin - 1]).all()


def test_dm_test_properties():
    rng = np.random.default_rng(0)
    e = rng.random(60)
    s, p = dm_test(e, e); assert p == 1.0                                      # identical => no difference
    s, p = dm_test(e + 0.5, e); assert p == 0.0 and s > 0                       # constant gap
    s, p = dm_test(e + 0.3 + 0.1 * rng.standard_normal(60), e); assert p < 0.001 and s > 0   # clearly worse
    ps = [dm_test(rng.random(40), rng.random(40))[1] for _ in range(300)]
    assert 0.02 < np.mean(np.array(ps) < 0.05) < 0.10                           # ~5% false positives under H0


def test_seasonal_models_beat_naive_on_seasonal_data_and_not_on_random_walk():
    s = seasonal_series(240, noise=0.2)
    res = evaluate(s, {k: BASELINES[k] for k in ["naive", "seasonal_naive", "ets"]}, h=12, season=12)
    t = skill_table(res, "naive").set_index("model")
    assert t.loc["seasonal_naive", "rel_mase"] < 0.7 and t.loc["ets", "rel_mase"] < 0.7
    rw = random_walk(240, seed=1)
    res = evaluate(rw, {"naive": naive, "drift": drift}, h=12)
    t = skill_table(res, "naive").set_index("model")
    assert t.loc["drift", "rel_mase"] > 0.8                                # nothing to gain on a pure random walk


def test_pre_post_cutoff_split_labels():
    s = seasonal_series(240); res = evaluate(s, {"naive": naive, "drift": drift}, h=12, season=12)
    t = skill_table(res, "naive", cutoff=s.index[150])
    assert set(t.period) <= {"pre_cutoff", "post_cutoff", "straddle"} and "post_cutoff" in set(t.period)
    assert t[t.period == "post_cutoff"].n_origins.iloc[0] >= 1
