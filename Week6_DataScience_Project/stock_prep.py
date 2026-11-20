"""Data preparation and statistics helpers for the Week 6 S&P 500 analysis.

The notebook imports everything from here so that the cleaning rules, the
return calculations and the statistical helpers are written once, tested once
(tests/test_stock_prep.py) and applied the same way to every stock.

Rules used throughout (see notebook Section 2):

* Prices are **split-adjusted but not dividend-adjusted** (checked against
  known splits in the notebook). Returns are therefore **price returns**: they
  leave out dividends and are understated for dividend payers.
* Every calculation is done **per symbol, in date order**. A return is only
  computed between two consecutive trading days of the shared calendar. A
  return that spans a gap in a symbol's history is kept but flagged and left
  out of daily-return statistics.
* No price is imputed or replaced by zero. Missing open/high/low stay missing;
  the close (never missing) drives every return.
* Suspect values are **flagged, not deleted**: the raw file is never changed
  and every exclusion is a documented filter on a flag.
"""

from __future__ import annotations

import hashlib
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

PROJECT_DIR = Path(__file__).resolve().parent
RAW_PATH = PROJECT_DIR / "Data" / "S&P 500 Stock Prices 2014-2017.csv"
CLEAN_DIR = PROJECT_DIR / "Data" / "Cleaned"

# SHA-256 of the supplied raw file. Checked at the start and end of the
# notebook so the analysis can never silently run on a modified copy.
RAW_SHA256 = "cd73b2fa92f476056c67a1c9543dc1a2050de5a5dc862de31dff8da3c67d4496"

RAW_COLUMNS = ["symbol", "date", "open", "high", "low", "close", "volume"]
PRICE_COLUMNS = ["open", "high", "low", "close"]
DATE_FORMAT = "%m/%d/%Y"
TRADING_DAYS = 252  # used only to annualise; stated wherever it is used

# The six stocks studied in depth: large companies from six different sectors,
# each with a complete 1,007-day history and no flagged record (checked in the
# notebook). Sector labels are general knowledge, not from the dataset.
SELECTED = ["AAPL", "AMZN", "JPM", "JNJ", "XOM", "WMT"]
SECTORS = {
    "AAPL": "Information technology",
    "AMZN": "Consumer discretionary",
    "JPM": "Financials",
    "JNJ": "Health care",
    "XOM": "Energy",
    "WMT": "Consumer staples",
}
COMPANY = {
    "AAPL": "Apple", "AMZN": "Amazon", "JPM": "JPMorgan Chase",
    "JNJ": "Johnson & Johnson", "XOM": "Exxon Mobil", "WMT": "Walmart",
}

# Large one-day price moves on dates of publicly announced spin-offs, share
# distributions or special dividends. The price falls because value is paid
# out to holders, not because holders lost money, and the file is not
# adjusted for it. These are context from public company announcements and are
# NOT verifiable from the dataset itself; they are used only to flag returns
# for the market-wide (all-symbol) figures. None affects the six selected stocks.
CORPORATE_ACTIONS = {
    ("SPG", "2014-05-28"): "Washington Prime Group spin-off",
    ("DISCA", "2014-08-07"): "Class C share distribution",
    ("DISCK", "2014-08-07"): "Class C share distribution",
    ("A", "2014-11-03"): "Keysight Technologies spin-off",
    ("BAX", "2015-07-01"): "Baxalta spin-off",
    ("NI", "2015-07-02"): "Columbia Pipeline Group spin-off",
    ("EBAY", "2015-07-20"): "PayPal spin-off",
    ("ARNC", "2016-11-01"): "Alcoa Corporation separation",
    ("YUM", "2016-11-01"): "Yum China spin-off",
    ("CAG", "2016-11-10"): "Lamb Weston spin-off",
    ("HPE", "2017-04-03"): "Enterprise Services separation (DXC)",
    ("BHGE", "2017-07-05"): "Special dividend on the GE Oil & Gas combination",
}

# Thresholds for the "spike and reversal" price-error rule (see flag_reversal_spikes)
SPIKE_MIN_MOVE = 0.20
SPIKE_MAX_NET = 0.05

MONTH_NAMES = ["Jan", "Feb", "Mar", "Apr", "May", "Jun",
               "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
DAY_NAMES = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]


# ---------------------------------------------------------------------------
# Loading and inspection
# ---------------------------------------------------------------------------

def sha256(path: Path | str) -> str:
    """Return the SHA-256 hex digest of a file."""
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def load_raw(path: Path | str = RAW_PATH) -> pd.DataFrame:
    """Read the raw CSV exactly as supplied (the file starts with a byte-order mark)."""
    df = pd.read_csv(path, encoding="utf-8-sig")
    if list(df.columns) != RAW_COLUMNS:
        raise ValueError(f"Unexpected columns: {list(df.columns)}")
    return df


def parse_dates(raw: pd.Series) -> pd.Series:
    """Parse ``date`` with the explicit month/day/year format.

    An explicit format stops pandas guessing day-first on dates such as
    1/2/2014; ``errors="raise"`` makes any malformed value stop the run.
    """
    return pd.to_datetime(raw, format=DATE_FORMAT, errors="raise")


def trading_calendar(dates: pd.Series) -> pd.DatetimeIndex:
    """All distinct dates in the file, sorted: the shared trading calendar."""
    return pd.DatetimeIndex(np.sort(pd.Series(dates).unique()))


def history_coverage(df: pd.DataFrame, calendar: pd.DatetimeIndex) -> pd.DataFrame:
    """One row per symbol: records, first and last date, and missing days.

    ``missing_inside`` counts calendar days between the symbol's first and last
    record that have no record (gaps in the middle of a history);
    ``missing_total`` counts all calendar days without a record.
    """
    pos = pd.Series(calendar.get_indexer(df["date"]), index=df.index)
    g = pos.groupby(df["symbol"])
    out = pd.DataFrame({
        "n_records": g.size(),
        "first_date": df.groupby("symbol")["date"].min(),
        "last_date": df.groupby("symbol")["date"].max(),
        "span_days": g.max() - g.min() + 1,
    })
    out["missing_inside"] = out["span_days"] - out["n_records"]
    out["missing_total"] = len(calendar) - out["n_records"]
    out["complete"] = out["n_records"] == len(calendar)
    out["starts_late"] = out["first_date"] > calendar[0]
    out["ends_early"] = out["last_date"] < calendar[-1]
    return out.drop(columns="span_days")


def ohlc_inconsistent(df: pd.DataFrame, tol: float = 1e-9) -> pd.Series:
    """True where the recorded open/high/low/close contradict each other.

    The high must be at least the open, low and close; the low must be at most
    the open, high and close. Rows with a missing field are only checked on the
    fields that are present.
    """
    others_max = df[["open", "low", "close"]].max(axis=1, skipna=True)
    others_min = df[["open", "high", "close"]].min(axis=1, skipna=True)
    bad_high = df["high"].notna() & (df["high"] < others_max - tol)
    bad_low = df["low"].notna() & (df["low"] > others_min + tol)
    return (bad_high | bad_low).rename("ohlc_inconsistent")


def flag_reversal_spikes(close: pd.Series, symbol: pd.Series,
                         min_move: float = SPIKE_MIN_MOVE, max_net: float = SPIKE_MAX_NET) -> pd.Series:
    """Flag single closing prices that look like recording errors.

    A close is flagged when the return into it is at least ``min_move`` in size
    and the next day's return undoes it, so that over the two days the price
    ends within ``max_net`` of where it started. A real 20% move that reverses
    completely the next day is very rare for a large company; a single bad
    value (for example one close that missed a split adjustment) produces
    exactly this pattern. The input must be sorted by symbol and date.
    """
    r_in = close.groupby(symbol).pct_change()
    r_out = r_in.groupby(symbol).shift(-1)
    net = (1 + r_in) * (1 + r_out) - 1
    return ((r_in.abs() >= min_move) & (net.abs() <= max_net)).fillna(False).rename("price_error")


# ---------------------------------------------------------------------------
# Preparation
# ---------------------------------------------------------------------------

def prepare(raw: pd.DataFrame, corporate_actions: dict | None = None) -> pd.DataFrame:
    """Return the cleaned dataset with analytical fields and quality flags.

    Nothing is deleted or imputed. Each row gets:

    * calendar fields: year, quarter, month, month_name, day_of_week, day_name;
    * per-symbol fields (in date order): prev_close, price_change,
      pct_return (simple return, as a fraction), log_return, daily_range
      (high - low), range_pct (range / close), moving averages of the close
      (20, 50 and 200 days), 21-day rolling volatility (annualised) and
      relative volume (volume / median of the previous 20 days);
    * flags: ohlc_inconsistent, ohlc_missing, no_trade, price_error,
      multi_day_return, corporate_action, and valid_return, which is True only
      for a one-day return with no flag on either of its two days.
    """
    corporate_actions = CORPORATE_ACTIONS if corporate_actions is None else corporate_actions
    df = raw.copy()
    df["date"] = parse_dates(df["date"])
    df = df.sort_values(["symbol", "date"], kind="mergesort").reset_index(drop=True)
    cal = trading_calendar(df["date"])

    dt = df["date"].dt
    df["year"] = dt.year
    df["quarter"] = dt.quarter
    df["month"] = dt.month
    df["month_name"] = pd.Categorical(dt.month.map(lambda m: MONTH_NAMES[m - 1]),
                                      categories=MONTH_NAMES, ordered=True)
    df["day_of_week"] = dt.day_of_week
    df["day_name"] = pd.Categorical(dt.day_of_week.map(lambda d: DAY_NAMES[d]),
                                    categories=DAY_NAMES, ordered=True)

    g = df.groupby("symbol", sort=False)
    df["prev_close"] = g["close"].shift(1)
    df["price_change"] = df["close"] - df["prev_close"]
    df["pct_return"] = df["close"] / df["prev_close"] - 1
    df["log_return"] = np.log(df["close"] / df["prev_close"])
    df["daily_range"] = df["high"] - df["low"]
    df["range_pct"] = df["daily_range"] / df["close"]

    # Flags
    df["ohlc_missing"] = df[["open", "high", "low"]].isna().any(axis=1)
    df["ohlc_inconsistent"] = ohlc_inconsistent(df)
    # A record with no open/high/low and (almost) no volume is not a normal
    # trading record for an S&P 500 stock; its volume is treated as missing.
    df["no_trade"] = df[["open", "high", "low"]].isna().all(axis=1) & (df["volume"] <= 100)
    df["price_error"] = flag_reversal_spikes(df["close"], df["symbol"])
    pos = pd.Series(cal.get_indexer(df["date"]), index=df.index)
    df["multi_day_return"] = (pos - pos.groupby(df["symbol"]).shift(1)) > 1
    key = list(zip(df["symbol"], df["date"].dt.strftime("%Y-%m-%d")))
    df["corporate_action"] = [k in corporate_actions for k in key]
    prev_error = df.groupby("symbol", sort=False)["price_error"].shift(1, fill_value=False)
    df["valid_return"] = (df["pct_return"].notna() & ~df["multi_day_return"] & ~df["price_error"]
                          & ~prev_error & ~df["corporate_action"])

    # The range is meaningless where the high/low contradict the other prices
    df.loc[df["ohlc_inconsistent"], ["daily_range", "range_pct"]] = np.nan
    df["volume_clean"] = df["volume"].astype(float).where(~df["no_trade"])

    # Rolling fields (per symbol, trailing windows only: no future information)
    for w in (20, 50, 200):
        df[f"ma_{w}"] = g["close"].transform(lambda s, w=w: s.rolling(w, min_periods=w).mean())
    ret_for_vol = df["pct_return"].where(df["valid_return"])
    df["vol_21d_ann"] = ret_for_vol.groupby(df["symbol"]).transform(
        lambda s: s.rolling(21, min_periods=15).std()) * np.sqrt(TRADING_DAYS)
    df["rel_volume"] = df["volume_clean"] / df.groupby("symbol", sort=False)["volume_clean"].transform(
        lambda s: s.shift(1).rolling(20, min_periods=15).median())
    return df


def returns_wide(df: pd.DataFrame, symbols, col: str = "pct_return", valid_only: bool = True) -> pd.DataFrame:
    """Date x symbol table of ``col`` for ``symbols`` (NaN where not valid)."""
    d = df[df["symbol"].isin(symbols)]
    vals = d[col].where(d["valid_return"]) if valid_only else d[col]
    return (d.assign(_v=vals).pivot(index="date", columns="symbol", values="_v")
            .reindex(columns=list(symbols)))


def market_average(df: pd.DataFrame) -> pd.DataFrame:
    """Equal-weighted average of all valid daily returns on each date.

    This is a summary of the symbols in the file, **not** the S&P 500 index
    (which is weighted by market value and whose membership changes).
    """
    v = df[df["valid_return"]]
    out = v.groupby("date")["pct_return"].agg(market_return="mean", n_symbols="size")
    out["market_index"] = 100 * (1 + out["market_return"]).cumprod()
    return out


# ---------------------------------------------------------------------------
# Performance measures
# ---------------------------------------------------------------------------

def total_return(close: pd.Series) -> float:
    """Price return from the first to the last close (fraction)."""
    c = pd.Series(close).dropna()
    return float(c.iloc[-1] / c.iloc[0] - 1)


def annualised_return(close: pd.Series, n_days: int | None = None) -> float:
    """Compound annual growth rate over the observed trading days (252 per year)."""
    c = pd.Series(close).dropna()
    n = (len(c) - 1) if n_days is None else n_days
    return float((c.iloc[-1] / c.iloc[0]) ** (TRADING_DAYS / n) - 1)


def max_drawdown(close: pd.Series) -> tuple[float, pd.Timestamp, pd.Timestamp]:
    """Largest peak-to-trough fall of the close (fraction), with its peak and trough dates."""
    c = pd.Series(close).dropna()
    peak = c.cummax()
    dd = c / peak - 1
    trough = dd.idxmin()
    peak_date = c.loc[:trough].idxmax()
    return float(dd.min()), peak_date, trough


def describe(x) -> dict:
    """Descriptive statistics for one numeric series (sample SD and variance, ddof=1)."""
    x = np.asarray(pd.Series(x).dropna(), dtype=float)
    q1, med, q3 = np.percentile(x, [25, 50, 75])
    p1, p5, p95, p99 = np.percentile(x, [1, 5, 95, 99])
    return {
        "n": x.size, "mean": x.mean(), "median": med, "min": x.min(), "max": x.max(),
        "std": x.std(ddof=1), "variance": x.var(ddof=1), "q1": q1, "q3": q3, "iqr": q3 - q1,
        "p1": p1, "p5": p5, "p95": p95, "p99": p99,
        "skewness": stats.skew(x, bias=False),
        "excess_kurtosis": stats.kurtosis(x, fisher=True, bias=False),
    }


# ---------------------------------------------------------------------------
# Inference helpers
# ---------------------------------------------------------------------------

def acf(x, nlags: int) -> np.ndarray:
    """Sample autocorrelation at lags 0..nlags (same estimator as statsmodels)."""
    x = np.asarray(x, dtype=float)
    x = x - x.mean()
    size = 1 << int(np.ceil(np.log2(2 * x.size - 1)))
    f = np.fft.rfft(x, size)
    full = np.fft.irfft(f * np.conj(f), size)[: nlags + 1]
    return full / full[0]


def effective_n(x, y, max_lag: int | None = None) -> float:
    """Effective sample size for a correlation between two autocorrelated series.

    Bartlett / Pyper & Peterman (1998): n / (1 + 2 sum_k w_k r_xx(k) r_yy(k)),
    with Bartlett weights. Capped at n and floored at 3.
    """
    x = np.asarray(x, dtype=float)
    y = np.asarray(y, dtype=float)
    n = x.size
    if max_lag is None:
        max_lag = max(1, n // 5)
    rx = acf(x, max_lag)[1:]
    ry = acf(y, max_lag)[1:]
    w = 1 - np.arange(1, max_lag + 1) / (max_lag + 1)
    return float(np.clip(n / (1 + 2 * np.sum(w * rx * ry)), 3, n))


def corr_test(x, y, method: str = "spearman", adjust: bool = True) -> dict:
    """Correlation with naive and serial-correlation-adjusted p-values and a 95% CI.

    The adjusted p-value and the Fisher-z interval use the effective sample
    size in place of n (for Spearman, of the ranks). The Spearman standard error
    uses the Bonett & Wright (2000) factor sqrt(1 + r^2 / 2).
    """
    x = np.asarray(x, dtype=float)
    y = np.asarray(y, dtype=float)
    ok = ~(np.isnan(x) | np.isnan(y))
    x, y = x[ok], y[ok]
    if method == "spearman":
        res = stats.spearmanr(x, y)
    elif method == "pearson":
        res = stats.pearsonr(x, y)
    else:
        raise ValueError(method)
    r, p_naive = float(res.statistic), float(res.pvalue)
    n = x.size
    if adjust:
        n_eff = effective_n(stats.rankdata(x), stats.rankdata(y)) if method == "spearman" else effective_n(x, y)
    else:
        n_eff = float(n)
    dof = max(n_eff - 2, 1)
    t = r * np.sqrt(dof / max(1 - r ** 2, 1e-12))
    p_adj = float(2 * stats.t.sf(abs(t), dof))
    z = np.arctanh(np.clip(r, -0.999999, 0.999999))
    se = 1 / np.sqrt(max(n_eff - 3, 1))
    if method == "spearman":
        se *= np.sqrt(1 + r ** 2 / 2)
    return {"method": method, "r": r, "n": n, "n_eff": n_eff, "p_naive": p_naive,
            "p_adjusted": p_adj, "ci_low": float(np.tanh(z - 1.96 * se)),
            "ci_high": float(np.tanh(z + 1.96 * se))}


def strength_label(r: float) -> str:
    """Verbal label for |r| (bands used throughout the report)."""
    a = abs(r)
    for cut, name in [(0.1, "negligible"), (0.3, "weak"), (0.5, "moderate"), (0.7, "strong")]:
        if a < cut:
            break
    else:
        name = "very strong"
    return name if name == "negligible" else f"{name} {'positive' if r > 0 else 'negative'}"


def hac_mean_test(x, maxlags: int | None = None) -> dict:
    """Test whether the mean of ``x`` is zero with Newey-West (HAC) standard errors.

    Regresses x on a constant; the HAC standard error allows for
    autocorrelation and changing variance (volatility clustering), which the
    ordinary one-sample t-test assumes away. ``maxlags`` defaults to the
    Newey-West rule floor(4 (n/100)^(2/9)).
    """
    import statsmodels.api as sm

    x = np.asarray(pd.Series(x).dropna(), dtype=float)
    n = x.size
    if maxlags is None:
        maxlags = int(np.floor(4 * (n / 100) ** (2 / 9)))
    fit = sm.OLS(x, np.ones(n)).fit(cov_type="HAC", cov_kwds={"maxlags": maxlags})
    se = float(fit.bse[0])
    # statsmodels reports a normal-based p-value for HAC; keep the t-based one
    t = float(fit.params[0] / se)
    p = float(2 * stats.t.sf(abs(t), n - 1))
    return {"mean": float(fit.params[0]), "se_hac": se, "t_hac": t, "p_hac": p, "maxlags": maxlags, "n": n}


def min_detectable_mean(sd: float, n: int, alpha: float = 0.05, power: float = 0.8) -> float:
    """Smallest true mean a two-sided one-sample t-test detects with the given power
    (normal approximation): (z_{1-alpha/2} + z_power) * sd / sqrt(n)."""
    return float((stats.norm.ppf(1 - alpha / 2) + stats.norm.ppf(power)) * sd / np.sqrt(n))


def block_bootstrap(data, stat, block: int = 20, n_boot: int = 2000, seed: int = 2017) -> np.ndarray:
    """Moving-block bootstrap of ``stat`` over the rows of ``data``.

    Blocks of ``block`` consecutive rows are drawn with replacement and joined
    until n rows are reached, which keeps short-range dependence (such as
    volatility clustering) inside each block.
    """
    data = np.asarray(data, dtype=float)
    if data.ndim == 1:
        data = data[:, None]
    n = data.shape[0]
    rng = np.random.default_rng(seed)
    n_blocks = int(np.ceil(n / block))
    out = []
    for _ in range(n_boot):
        starts = rng.integers(0, n - block + 1, size=n_blocks)
        idx = (starts[:, None] + np.arange(block)).ravel()[:n]
        out.append(stat(data[idx]))
    return np.asarray(out)


def percentile_ci(boot, level: float = 0.95):
    a = (1 - level) / 2
    lo, hi = np.percentile(boot, [100 * a, 100 * (1 - a)], axis=0)
    return lo, hi


def holm(pvalues) -> np.ndarray:
    """Holm-Bonferroni adjusted p-values (same order as the input)."""
    p = np.asarray(pvalues, dtype=float)
    m = p.size
    order = np.argsort(p)
    adj = np.empty(m)
    running = 0.0
    for rank, i in enumerate(order):
        running = max(running, (m - rank) * p[i])
        adj[i] = min(running, 1.0)
    return adj


def kendalls_w(chi2: float, n_blocks: int, k: int) -> float:
    """Effect size for the Friedman test: W = chi2 / (n (k - 1))."""
    return chi2 / (n_blocks * (k - 1))


def epsilon_squared(h: float, n: int) -> float:
    """Effect size for Kruskal-Wallis: H / (n - 1)."""
    return h / (n - 1)


def seasonal_strength(seasonal, resid) -> float:
    """Wang, Smith & Hyndman (2006): max(0, 1 - Var(R) / Var(S + R))."""
    s = np.asarray(seasonal, dtype=float)
    r = np.asarray(resid, dtype=float)
    return float(max(0.0, 1 - np.var(r) / np.var(s + r)))


def trend_strength(trend, resid) -> float:
    """max(0, 1 - Var(R) / Var(T + R))."""
    t = np.asarray(trend, dtype=float)
    r = np.asarray(resid, dtype=float)
    return float(max(0.0, 1 - np.var(r) / np.var(t + r)))


def diebold_mariano(loss_a, loss_b, h: int = 1) -> dict:
    """Diebold-Mariano test of equal forecast accuracy (loss_a - loss_b has mean zero).

    Uses a HAC variance with h - 1 lags and the Harvey, Leybourne & Newbold
    (1997) small-sample correction. A negative statistic means model A has the
    smaller loss.
    """
    d = np.asarray(loss_a, dtype=float) - np.asarray(loss_b, dtype=float)
    n = d.size
    dbar = d.mean()
    gamma = [np.mean((d[k:] - dbar) * (d[: n - k] - dbar)) for k in range(h)]
    var = (gamma[0] + 2 * sum(gamma[1:])) / n
    dm = dbar / np.sqrt(var)
    corr = np.sqrt((n + 1 - 2 * h + h * (h - 1) / n) / n)
    stat = dm * corr
    return {"dm": float(stat), "p": float(2 * stats.t.sf(abs(stat), n - 1)), "mean_diff": float(dbar)}
