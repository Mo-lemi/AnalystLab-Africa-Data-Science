"""Unit tests for stock_prep.py. Run from the project folder: python -m pytest"""

import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest
from scipy import stats

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import stock_prep as sp  # noqa: E402


def make_raw(rows):
    """rows: list of (symbol, 'm/d/YYYY', open, high, low, close, volume)."""
    return pd.DataFrame(rows, columns=sp.RAW_COLUMNS)


def simple_raw(closes_a, closes_b=None, start="2017-01-02"):
    dates = pd.bdate_range(start, periods=len(closes_a))
    rows = []
    for d, c in zip(dates, closes_a):
        rows.append(("AAA", f"{d.month}/{d.day}/{d.year}", c, c * 1.01, c * 0.99, c, 1000))
    if closes_b is not None:
        for d, c in zip(dates, closes_b):
            rows.append(("BBB", f"{d.month}/{d.day}/{d.year}", c, c * 1.01, c * 0.99, c, 2000))
    # deliberately shuffle the input order: preparation must sort
    return make_raw(rows).sample(frac=1, random_state=0).reset_index(drop=True)


# --- loading and parsing -------------------------------------------------------

def test_parse_dates_is_month_first():
    s = sp.parse_dates(pd.Series(["1/2/2014", "12/29/2017"]))
    assert s.iloc[0] == pd.Timestamp("2014-01-02") and s.iloc[1] == pd.Timestamp("2017-12-29")


def test_parse_dates_rejects_other_formats():
    with pytest.raises(ValueError):
        sp.parse_dates(pd.Series(["2014-01-02"]))


def test_raw_file_hash_and_columns():
    assert sp.sha256(sp.RAW_PATH) == sp.RAW_SHA256
    assert list(sp.load_raw().columns) == sp.RAW_COLUMNS


def test_load_raw_rejects_unexpected_columns(tmp_path):
    p = tmp_path / "x.csv"
    p.write_text("ticker,date,close\nA,1/2/2014,1\n", encoding="utf-8")
    with pytest.raises(ValueError):
        sp.load_raw(p)


# --- returns and derived fields --------------------------------------------------

def test_returns_are_per_symbol_and_in_date_order():
    df = sp.prepare(simple_raw([100, 110, 99], [50, 25, 50]))
    a = df[df.symbol == "AAA"].pct_return.tolist()
    b = df[df.symbol == "BBB"].pct_return.tolist()
    assert np.isnan(a[0]) and np.isnan(b[0])      # first record of each symbol has no return
    assert a[1:] == pytest.approx([0.10, -0.10])
    assert b[1:] == pytest.approx([-0.50, 1.00])  # never computed across symbols
    assert df.groupby("symbol").date.is_monotonic_increasing.all()


def test_price_change_log_return_and_range():
    df = sp.prepare(simple_raw([100, 105]))
    row = df.iloc[1]
    assert row.price_change == pytest.approx(5)
    assert row.log_return == pytest.approx(np.log(1.05))
    assert row.daily_range == pytest.approx(105 * 0.02)
    assert row.year == 2017 and row.quarter == 1 and row.month == 1


def test_moving_average_uses_trailing_window_only():
    closes = list(range(1, 31))
    df = sp.prepare(simple_raw(closes))
    ma = df.ma_20.tolist()
    assert all(np.isnan(ma[:19]))
    assert ma[19] == pytest.approx(np.mean(closes[:20]))
    assert ma[-1] == pytest.approx(np.mean(closes[-20:]))


def test_relative_volume_excludes_the_current_day():
    raw = simple_raw([100] * 25)
    last = sp.parse_dates(raw.date).max()
    raw.loc[sp.parse_dates(raw.date) == last, "volume"] = 5000
    df = sp.prepare(raw)
    # today's spike must not enter its own baseline (median of the previous 20 days = 1000)
    assert df.rel_volume.iloc[-1] == pytest.approx(5.0)
    assert df.rel_volume.iloc[:15].isna().all()       # fewer than 15 previous days -> no value
    assert df.rel_volume.iloc[15:-1].tolist() == pytest.approx([1.0] * 9)


# --- flags -----------------------------------------------------------------------

def test_reversal_spike_is_flagged_but_real_move_is_not():
    # day 3 is a one-day error (halved close); day 6 is a lasting 30% fall
    df = sp.prepare(simple_raw([100, 101, 50, 101, 102, 71, 70, 70]))
    flagged = df[df.price_error].index.tolist()
    assert len(flagged) == 1 and df.loc[flagged[0], "close"] == 50
    # both returns touching the bad close are invalid; the lasting fall is valid
    invalid = df[~df.valid_return & df.pct_return.notna()].close.tolist()
    assert invalid == [50, 101]
    assert df[df.close == 71].valid_return.item()


def test_ohlc_inconsistent_rows():
    raw = make_raw([
        ("AAA", "1/2/2017", 10, 11, 9, 10.5, 100),     # fine
        ("AAA", "1/3/2017", 10, 9.5, 9, 10.5, 100),    # high below close
        ("AAA", "1/4/2017", 10, 11, 10.2, 10.5, 100),  # low above open
        ("AAA", "1/5/2017", None, 11, 9, 10.5, 100),   # missing open, rest fine
    ])
    df = sp.prepare(raw)
    assert df.ohlc_inconsistent.tolist() == [False, True, True, False]
    assert df.daily_range.isna().tolist() == [False, True, True, False]


def test_missing_prices_are_not_imputed_or_zeroed():
    raw = make_raw([("AAA", "1/2/2017", 10, 11, 9, 10, 100),
                    ("AAA", "1/3/2017", None, None, None, 10.5, 0)])
    df = sp.prepare(raw)
    assert df.loc[1, ["open", "high", "low"]].isna().all()
    assert df.no_trade.tolist() == [False, True]
    assert np.isnan(df.loc[1, "volume_clean"])          # zero volume on a placeholder row -> missing
    assert df.loc[1, "pct_return"] == pytest.approx(0.05)  # the close still gives a return


def test_gap_in_history_gives_flagged_multi_day_return():
    raw = make_raw([("AAA", "1/2/2017", 10, 10, 10, 10, 1), ("AAA", "1/3/2017", 10, 10, 10, 10, 1),
                    ("AAA", "1/5/2017", 11, 11, 11, 11, 1),
                    ("BBB", "1/2/2017", 5, 5, 5, 5, 1), ("BBB", "1/3/2017", 5, 5, 5, 5, 1),
                    ("BBB", "1/4/2017", 5, 5, 5, 5, 1), ("BBB", "1/5/2017", 5, 5, 5, 5, 1)])
    df = sp.prepare(raw)
    a = df[df.symbol == "AAA"]
    assert a.multi_day_return.tolist() == [False, False, True]
    assert not a.valid_return.iloc[2]
    cov = sp.history_coverage(df, sp.trading_calendar(df.date))
    assert cov.loc["AAA", "missing_inside"] == 1 and not cov.loc["AAA", "complete"]
    assert cov.loc["BBB", "complete"]


def test_corporate_action_return_is_excluded():
    raw = simple_raw([100, 60, 61])
    d = sp.parse_dates(raw.date).sort_values().iloc[1].strftime("%Y-%m-%d")
    df = sp.prepare(raw, corporate_actions={("AAA", d): "test spin-off"})
    assert df.corporate_action.sum() == 1 and not df[df.corporate_action].valid_return.item()


def test_market_average_is_equal_weighted_mean_of_valid_returns():
    df = sp.prepare(simple_raw([100, 110, 121], [100, 90, 99]))
    m = sp.market_average(df)
    assert m.market_return.tolist() == pytest.approx([0.0, 0.10])
    assert m.n_symbols.tolist() == [2, 2]


# --- performance and statistics helpers ---------------------------------------------

def test_total_and_annualised_return_and_drawdown():
    c = pd.Series([100, 120, 90, 150], index=pd.bdate_range("2017-01-02", periods=4))
    assert sp.total_return(c) == pytest.approx(0.5)
    assert sp.annualised_return(c, n_days=252) == pytest.approx(0.5)
    dd, peak, trough = sp.max_drawdown(c)
    assert dd == pytest.approx(-0.25) and peak == c.index[1] and trough == c.index[2]


def test_describe_matches_scipy():
    x = np.random.default_rng(1).standard_t(4, 500)
    d = sp.describe(x)
    assert d["std"] == pytest.approx(np.std(x, ddof=1))
    assert d["skewness"] == pytest.approx(stats.skew(x, bias=False))
    assert d["excess_kurtosis"] == pytest.approx(stats.kurtosis(x, bias=False))


def test_acf_matches_statsmodels():
    from statsmodels.tsa.stattools import acf as sm_acf
    x = np.random.default_rng(2).normal(size=300).cumsum()
    assert sp.acf(x, 10) == pytest.approx(sm_acf(x, nlags=10, fft=False))


def test_effective_n_white_noise_close_to_n():
    rng = np.random.default_rng(3)
    x, y = rng.normal(size=2000), rng.normal(size=2000)
    assert 1600 < sp.effective_n(x, y) <= 2000


def test_effective_n_shrinks_for_persistent_series():
    rng = np.random.default_rng(4)
    x, y = rng.normal(size=1000).cumsum(), rng.normal(size=1000).cumsum()
    assert sp.effective_n(x, y) < 200


def test_corr_test_matches_scipy_and_adjusts_p():
    rng = np.random.default_rng(5)
    x = rng.normal(size=400)
    y = 0.3 * x + rng.normal(size=400)
    t = sp.corr_test(x, y, "spearman")
    assert t["r"] == pytest.approx(stats.spearmanr(x, y).statistic)
    assert t["ci_low"] < t["r"] < t["ci_high"]
    t2 = sp.corr_test(x, y, "pearson", adjust=False)
    assert t2["p_adjusted"] == pytest.approx(stats.pearsonr(x, y).pvalue, rel=1e-6)


def test_hac_mean_test_equals_t_test_for_independent_data_without_lags():
    x = np.random.default_rng(6).normal(0.1, 1, 500)
    h = sp.hac_mean_test(x, maxlags=0)
    t = stats.ttest_1samp(x, 0)
    # with no lags, HAC = White SE, which uses n rather than n-1 in the variance
    assert h["t_hac"] == pytest.approx(t.statistic * np.sqrt(500 / 499), rel=1e-6)


def test_holm():
    adj = sp.holm([0.01, 0.04, 0.03])
    assert adj == pytest.approx([0.03, 0.06, 0.06])


def test_block_bootstrap_reproducible_and_centred():
    x = np.random.default_rng(7).normal(1.0, 1, 600)
    b1 = sp.block_bootstrap(x, lambda a: a.mean(), block=10, n_boot=300, seed=1)
    b2 = sp.block_bootstrap(x, lambda a: a.mean(), block=10, n_boot=300, seed=1)
    assert np.array_equal(b1, b2)
    lo, hi = sp.percentile_ci(b1)
    assert lo < x.mean() < hi


def test_min_detectable_mean():
    assert sp.min_detectable_mean(1.0, 100) == pytest.approx((1.959964 + 0.841621) / 10, rel=1e-5)


def test_seasonal_strength_bounds():
    t = np.arange(200)
    s = np.sin(2 * np.pi * t / 20)
    r = np.random.default_rng(8).normal(0, 0.05, 200)
    assert sp.seasonal_strength(s, r) > 0.9
    assert sp.seasonal_strength(np.zeros(200), r) == 0.0


def test_diebold_mariano_detects_better_forecast():
    rng = np.random.default_rng(9)
    y = rng.normal(size=500)
    good, bad = y - rng.normal(0, 0.1, 500), y - rng.normal(0, 1.0, 500)
    res = sp.diebold_mariano((y - good) ** 2, (y - bad) ** 2)
    assert res["dm"] < 0 and res["p"] < 0.001
