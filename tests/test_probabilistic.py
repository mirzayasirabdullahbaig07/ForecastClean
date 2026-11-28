import numpy as np
import pandas as pd
import pytest

from forecastclean import probabilistic as pb


def test_pinball_matches_hand_computation_and_is_zero_for_a_perfect_forecast():
    y = np.array([10.0, 20.0]); q = np.tile(y[:, None], (1, 9))
    assert pb.pinball(y, q).max() == 0
    q2 = np.full((2, 9), 9.0)                                   # forecast too low by 1 and 11
    p = pb.pinball(y, q2)
    assert np.allclose(p[0], pb.LEVELS * 1.0) and np.allclose(p[1], pb.LEVELS * 11.0)   # under-forecast costs tau * error
    q3 = np.full((2, 9), 30.0)                                  # too high: costs (1 - tau) * error
    assert np.allclose(pb.pinball(y, q3)[1], (1 - pb.LEVELS) * 10.0)


def test_scaled_crps_uses_the_mase_scale_and_coverage_counts_inside_80_interval():
    train = np.array([1.0, 3.0, 1.0, 3.0, 1.0, 3.0]); y = np.array([2.0, 2.0])      # in-sample |diff| = 2 -> scale 2
    q = np.tile(np.array([1.0, 1.1, 1.2, 1.3, 2.0, 2.7, 2.8, 2.9, 3.0]), (2, 1))
    assert pb.scale_of(train, 1) == 2.0
    assert pb.scaled_crps(y, q, train, 1) == pytest.approx(2.0 * pb.pinball(y, q).mean() / 2.0)
    assert pb.coverage80(np.array([0.0, 2.0, 5.0]), np.tile([[1.0] + [2.0] * 7 + [3.0]], (3, 1))) == pytest.approx(1 / 3)


def test_empirical_quantile_forecaster_shape_monotone_and_widens_with_horizon():
    rng = np.random.default_rng(0); tr = rng.normal(size=300).cumsum() + 100
    q = pb.REFERENCES["naive_q"](tr, 10, 1)
    assert q.shape == (10, 9) and np.all(np.diff(q, axis=1) >= 0)
    assert np.all(np.diff(q[:, -1] - q[:, 0]) > 0)               # interval width grows with the horizon (random walk)
    qs = pb.REFERENCES["seasonal_naive_q"](tr, 14, 7)
    assert qs.shape == (14, 9)


def test_evaluate_prob_scores_a_sharp_correct_forecaster_better_and_checks_no_lookahead():
    idx = pd.date_range("2022-01-01", periods=400, freq="D"); rng = np.random.default_rng(3)
    ser = pd.Series(50 + 5 * np.sin(np.arange(400) * 2 * np.pi / 7) + rng.normal(0, 0.5, 400), index=idx)
    seen = []
    def good(tr, h, s, lv):                                     # seasonal-naive centre, tight, honest spread
        seen.append(len(tr)); return pb.REFERENCES["seasonal_naive_q"](tr, h, s, lv)
    def bad(tr, h, s, lv):                                      # centred on the wrong level
        return pb.REFERENCES["naive_q"](tr, h, s, lv) + 40.0
    res = pb.evaluate_prob(ser, {"good": good, "bad": bad}, h=7, season=7, max_context=200, max_origins=8, min_train=100)
    m = res.groupby("model").scrps.mean()
    assert m["good"] < m["bad"] and res.model.nunique() == 2 and max(seen) <= 200   # context capped, never longer than allowed
    assert res[res.model == "bad"].cov80.mean() == 0


def test_foundation_quantile_adapters_return_h_by_Q(monkeypatch):
    import sys, types
    monkeypatch.setitem(sys.modules, "torch", types.SimpleNamespace(tensor=lambda x, dtype=None: np.asarray(x, float), float32=None,
                                                                    cuda=types.SimpleNamespace(is_available=lambda: False)))
    from forecastclean.models import chronos_forecaster, timesfm_forecaster
    class Bolt:
        def predict_quantiles(self, x, prediction_length, quantile_levels):
            h, Q = prediction_length, len(quantile_levels)
            return np.arange(h * Q, dtype=float).reshape(1, h, Q), None
    f = chronos_forecaster("amazon/chronos-bolt-tiny", pipeline=Bolt())
    q = f.quantiles(np.arange(40.0), 5, pb.LEVELS)
    assert q.shape == (5, 9) and f(np.arange(40.0), 5).shape == (5,)       # point forecast still works through the same path

    class Fake:
        def forecast(self, horizon, inputs):
            quant = np.zeros((1, horizon, 10)); quant[0, :, :] = np.arange(10)[None, :]      # col k holds value k (0 = mean)
            return np.zeros((1, horizon)), quant
    t = timesfm_forecaster(model=Fake())
    tq = t.quantiles(np.arange(40.0), 4, pb.LEVELS)
    assert tq.shape == (4, 9) and tq[0].tolist() == [1, 2, 3, 4, 5, 6, 7, 8, 9]        # q10..q90 = columns 1..9, mean excluded
    with pytest.raises(ValueError):
        t.quantiles(np.arange(40.0), 4, [0.25])
