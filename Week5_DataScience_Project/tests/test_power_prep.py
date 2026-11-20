"""Unit tests for power_prep.py. Run from the project folder: python -m pytest"""

import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest
from scipy import stats

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import power_prep as pp  # noqa: E402


def make_raw(n=144 * 2, start="2017-01-01 00:00"):
    t = pd.date_range(start, periods=n, freq="10min")
    rng = np.random.default_rng(0)
    return pd.DataFrame({
        "Datetime": [f"{x.month}/{x.day}/{x.year} {x.hour}:{x.minute:02d}" for x in t],
        "Temperature": rng.normal(18, 3, n),
        "Humidity": rng.uniform(40, 90, n),
        "WindSpeed": rng.choice([0.08, 4.9], n),
        "GeneralDiffuseFlows": rng.uniform(0, 500, n),
        "DiffuseFlows": rng.uniform(0, 200, n),
        "PowerConsumption_Zone1": 30000 + rng.normal(0, 100, n),
        "PowerConsumption_Zone2": 20000 + rng.normal(0, 100, n),
        "PowerConsumption_Zone3": 15000 + rng.normal(0, 100, n),
    })


# --- loading and inspection ----------------------------------------------------

def test_parse_datetime_is_month_first():
    s = pp.parse_datetime(pd.Series(["1/2/2017 0:10", "12/30/2017 23:50"]))
    assert s.iloc[0] == pd.Timestamp("2017-01-02 00:10")
    assert s.iloc[1] == pd.Timestamp("2017-12-30 23:50")


def test_parse_datetime_rejects_bad_value():
    with pytest.raises(ValueError):
        pp.parse_datetime(pd.Series(["2017-01-01 00:00"]))


def test_interval_summary_detects_gap_and_duplicate():
    t = pd.Series(pd.to_datetime(["2017-01-01 00:00", "2017-01-01 00:10", "2017-01-01 00:10",
                                  "2017-01-01 00:30"]))
    s = pp.interval_summary(t)
    assert s["duplicate_timestamps"] == 1
    assert s["missing_timestamps"] == 1          # 00:20 is missing
    assert s["expected_timestamps"] == 4


def test_interval_summary_regular_series():
    t = pd.Series(pd.date_range("2017-01-01", periods=10, freq="10min"))
    s = pp.interval_summary(t)
    assert s["missing_timestamps"] == 0 and s["n_gap_other"] == 0 and s["n_gap_10min"] == 9


def test_longest_constant_run():
    assert pp.longest_constant_run(pd.Series([1, 1, 2, 2, 2, 3, 2])) == 3


def test_out_of_range_counts():
    df = pd.DataFrame({"Humidity": [50, 101, -1], "Zone1": [1, -5, 3]})
    assert pp.out_of_range_counts(df) == {"Humidity": 2, "Zone1": 1}


def test_flag_spikes_finds_single_spike_not_ramp():
    ramp = pd.Series(np.linspace(20000, 40000, 300) + np.random.default_rng(1).normal(0, 50, 300))
    ramp.iloc[150] += 8000
    flags = pp.flag_spikes(ramp)
    assert flags.iloc[150]
    assert flags.sum() == 1


def test_load_raw_rejects_wrong_columns(tmp_path):
    p = tmp_path / "x.csv"
    pd.DataFrame({"a": [1]}).to_csv(p, index=False)
    with pytest.raises(ValueError):
        pp.load_raw(p)


# --- preparation ---------------------------------------------------------------

def test_prepare_keeps_every_row_and_adds_features():
    raw = make_raw()
    df = pp.prepare(raw)
    assert len(df) == len(raw)
    for c in ["Year", "Month", "Day", "Hour", "DayOfWeek", "Date", "Zone1", "Total", "WindState"]:
        assert c in df
    assert df.loc[0, "DayName"] == "Sunday"      # 1 Jan 2017 was a Sunday
    assert df.loc[0, "Holiday"] == "New Year's Day"
    assert np.allclose(df["Total"], df[pp.ZONES].sum(axis=1))


def test_ramadan_flag_bounds():
    t = pd.DataFrame({"Datetime": pd.to_datetime(["2017-05-26 23:50", "2017-05-27 00:00",
                                                  "2017-06-25 23:50", "2017-06-26 00:00"])})
    f = pp.add_time_features(t)["IsRamadan"].tolist()
    assert f == [False, True, True, False]


def test_aggregate_hourly_is_mean_not_sum():
    df = pp.prepare(make_raw())
    h = pp.aggregate(df, "h")
    assert len(h) == 48 and (h["n_readings"] == 6).all()
    first = df.loc[:5, "Zone1"].mean()
    assert h.loc[0, "Zone1"] == pytest.approx(first)
    d = pp.aggregate(df, "D")
    assert len(d) == 2 and (d["n_readings"] == 144).all()


def test_energy_mwh():
    assert pp.energy_mwh(30000, 24) == pytest.approx(720.0)


# --- statistics ----------------------------------------------------------------

def test_describe_matches_numpy():
    x = pd.Series(np.random.default_rng(2).gamma(3, 2, 500))
    d = pp.describe(x)
    assert d["mean"] == pytest.approx(x.mean())
    assert d["variance"] == pytest.approx(x.var(ddof=1))
    assert d["iqr"] == pytest.approx(x.quantile(0.75) - x.quantile(0.25))
    assert d["cv"] == pytest.approx(x.std() / x.mean())
    assert d["skewness"] == pytest.approx(stats.skew(x, bias=False))


def test_acf_matches_direct_sum():
    x = np.random.default_rng(3).normal(size=200).cumsum()
    xc = x - x.mean()
    direct = [np.dot(xc[: 200 - k], xc[k:]) / np.dot(xc, xc) for k in range(6)]
    assert np.allclose(pp.acf(x, 5), direct)


def test_effective_n_white_noise_close_to_n():
    rng = np.random.default_rng(4)
    x, y = rng.normal(size=2000), rng.normal(size=2000)
    assert pp.effective_n(x, y) > 1500


def test_effective_n_autocorrelated_is_much_smaller():
    rng = np.random.default_rng(5)
    x = np.sin(np.arange(2000) / 100) + rng.normal(0, 0.1, 2000)
    y = np.sin(np.arange(2000) / 100 + 0.3) + rng.normal(0, 0.1, 2000)
    assert pp.effective_n(x, y) < 200


def test_corr_test_naive_p_matches_scipy():
    rng = np.random.default_rng(6)
    x = rng.normal(size=300)
    y = 0.4 * x + rng.normal(size=300)
    r = pp.corr_test(x, y, "pearson", n_eff=300)
    ref = stats.pearsonr(x, y)
    assert r["r"] == pytest.approx(ref.statistic)
    assert r["p_adjusted"] == pytest.approx(ref.pvalue, rel=1e-6)
    assert r["ci_low"] < r["r"] < r["ci_high"]


def test_corr_test_smaller_n_eff_gives_larger_p():
    rng = np.random.default_rng(7)
    x = rng.normal(size=300)
    y = 0.2 * x + rng.normal(size=300)
    a = pp.corr_test(x, y, "spearman", n_eff=300)
    b = pp.corr_test(x, y, "spearman", n_eff=30)
    assert b["p_adjusted"] > a["p_adjusted"]
    assert (b["ci_high"] - b["ci_low"]) > (a["ci_high"] - a["ci_low"])


def test_holm_known_values():
    adj = pp.holm([0.01, 0.04, 0.03])
    assert np.allclose(adj, [0.03, 0.06, 0.06])


def test_effect_sizes():
    assert pp.epsilon_squared(99, 100) == pytest.approx(1.0)
    assert pp.kendalls_w(30, 10, 4) == pytest.approx(1.0)
    assert pp.rank_biserial_paired([2, 3, 4], [1, 1, 1]) == pytest.approx(1.0)


def test_block_bootstrap_reproducible_and_centred():
    x = np.random.default_rng(8).normal(10, 1, 365)
    a = pp.block_bootstrap(x, lambda d: d.mean(), n_boot=300, seed=1)
    b = pp.block_bootstrap(x, lambda d: d.mean(), n_boot=300, seed=1)
    assert np.array_equal(a, b)
    lo, hi = pp.percentile_ci(a)
    assert lo < x.mean() < hi


def test_hinge_fit_recovers_known_model():
    t = np.linspace(5, 32, 400)
    y = 30000 + 900 * np.maximum(0, t - 20) + np.random.default_rng(9).normal(0, 50, 400)
    f = pp.hinge_fit(t, y)
    assert f["base"] == pytest.approx(20, abs=0.5)
    assert f["slope"] == pytest.approx(900, rel=0.05)
    assert f["r2"] > 0.99


def test_seasonal_strength_bounds():
    s = np.sin(np.arange(100))
    assert pp.seasonal_strength(s, np.zeros(100)) == pytest.approx(1.0)
    assert pp.seasonal_strength(np.zeros(100), np.ones(100) + np.arange(100)) == 0.0


def test_strength_label():
    assert pp.strength_label(0.05) == "negligible"
    assert pp.strength_label(-0.35) == "moderate negative"
    assert pp.strength_label(0.75) == "very strong positive"
