"""Data preparation and statistics helpers for the Week 5 electricity analysis.

The notebook imports everything from here so that the cleaning rules, the
aggregation and the statistical helpers are written once, tested once
(tests/test_power_prep.py) and reused for every zone.

Interpretation rules used throughout (see notebook Section 1.3):

* ``PowerConsumption_Zone*`` is treated as the **average load in kW** during
  each 10-minute interval, not as kWh consumed in that interval. Energy is
  derived only as ``mean kW x hours`` and is always labelled as derived.
* ``GeneralDiffuseFlows`` and ``DiffuseFlows`` are treated as solar irradiance
  readings (W/m^2, global and diffuse horizontal), not as "emission gases".
* ``WindSpeed`` takes two states (about 0.08 or about 4.9) and is analysed as
  a two-state variable as well as a number.
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
RAW_PATH = PROJECT_DIR / "Data" / "powerconsumption.csv"
DICT_PATH = PROJECT_DIR / "Data" / "powerconsumption_datadictionary.csv"

# SHA-256 of the supplied raw file. Checked at the start and end of the notebook
# so the analysis can never silently run on a modified copy.
RAW_SHA256 = "b487c492a3a1dc8213fb9eabdf43b39003fa178289174095d7c92bdab7e47503"

RAW_COLUMNS = [
    "Datetime", "Temperature", "Humidity", "WindSpeed", "GeneralDiffuseFlows",
    "DiffuseFlows", "PowerConsumption_Zone1", "PowerConsumption_Zone2",
    "PowerConsumption_Zone3",
]
DATETIME_FORMAT = "%m/%d/%Y %H:%M"
INTERVAL = pd.Timedelta(minutes=10)

ZONES = ["Zone1", "Zone2", "Zone3"]
ZONE_COLUMNS = {f"PowerConsumption_{z}": z for z in ZONES}
ENV = ["Temperature", "Humidity", "WindSpeed"]
IRRADIANCE = ["GeneralDiffuseFlows", "DiffuseFlows"]

# Physically plausible ranges, used only to flag readings, never to delete them.
PLAUSIBLE_RANGES = {
    "Temperature": (-10.0, 50.0),        # degrees C, northern Morocco
    "Humidity": (0.0, 100.0),            # relative humidity, %
    "WindSpeed": (0.0, 40.0),            # unit uncertain, see Section 1.3
    "GeneralDiffuseFlows": (0.0, 1400.0),  # W/m^2, below the solar constant
    "DiffuseFlows": (0.0, 1400.0),
    "Zone1": (0.0, None), "Zone2": (0.0, None), "Zone3": (0.0, None),
}

# Ramadan 1438 AH. The fasting days in Morocco were 27 May to 25 June 2017
# (Eid al-Fitr on 26 June). The notebook confirms these dates from the data:
# night-time load steps up on 27 May and back down on 27 June.
RAMADAN = (pd.Timestamp("2017-05-27"), pd.Timestamp("2017-06-25"))

# Fixed-date and religious public holidays in Morocco in 2017. Used only to
# label days in the residual analysis, not to remove them.
HOLIDAYS_2017 = {
    "2017-01-01": "New Year's Day",
    "2017-01-11": "Independence Manifesto Day",
    "2017-05-01": "Labour Day",
    "2017-06-26": "Eid al-Fitr",
    "2017-06-27": "Eid al-Fitr (2nd day)",
    "2017-07-30": "Throne Day",
    "2017-08-14": "Oued Ed-Dahab Day",
    "2017-08-20": "Revolution Day",
    "2017-08-21": "Youth Day",
    "2017-09-01": "Eid al-Adha",
    "2017-09-02": "Eid al-Adha (2nd day)",
    "2017-09-22": "Islamic New Year",
    "2017-11-06": "Green March Day",
    "2017-11-18": "Independence Day",
    "2017-12-01": "Prophet's Birthday",
}

DAY_NAMES = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
MONTH_NAMES = ["Jan", "Feb", "Mar", "Apr", "May", "Jun",
               "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]


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
    """Read the raw CSV exactly as supplied (strings and floats, no parsing)."""
    df = pd.read_csv(path, encoding="utf-8-sig")  # the file starts with a BOM
    if list(df.columns) != RAW_COLUMNS:
        raise ValueError(f"Unexpected columns: {list(df.columns)}")
    return df


def parse_datetime(raw: pd.Series) -> pd.Series:
    """Parse ``Datetime`` with the explicit month/day/year format.

    An explicit format avoids pandas guessing day-first on dates such as
    1/2/2017. ``errors="raise"`` makes any malformed value stop the run.
    """
    return pd.to_datetime(raw, format=DATETIME_FORMAT, errors="raise")


def interval_summary(ts: pd.Series) -> dict:
    """Describe how regular a timestamp series is."""
    ts = pd.Series(ts).sort_values().reset_index(drop=True)
    gaps = ts.diff().dropna()
    expected = int((ts.iloc[-1] - ts.iloc[0]) / INTERVAL) + 1
    return {
        "first": ts.iloc[0],
        "last": ts.iloc[-1],
        "n_timestamps": len(ts),
        "expected_timestamps": expected,
        "missing_timestamps": expected - ts.nunique(),
        "duplicate_timestamps": int(ts.duplicated().sum()),
        "n_gap_10min": int((gaps == INTERVAL).sum()),
        "n_gap_other": int((gaps != INTERVAL).sum()),
        "is_monotonic": bool(pd.Series(ts).is_monotonic_increasing),
    }


def longest_constant_run(s: pd.Series) -> int:
    """Length of the longest run of identical consecutive values."""
    groups = (s != s.shift()).cumsum()
    return int(s.groupby(groups).size().max())


def out_of_range_counts(df: pd.DataFrame) -> dict:
    """Count readings outside ``PLAUSIBLE_RANGES`` for each column present."""
    counts = {}
    for col, (lo, hi) in PLAUSIBLE_RANGES.items():
        if col not in df:
            continue
        mask = pd.Series(False, index=df.index)
        if lo is not None:
            mask |= df[col] < lo
        if hi is not None:
            mask |= df[col] > hi
        counts[col] = int(mask.sum())
    return counts


def neighbour_median(s: pd.Series, half_window: int = 3) -> pd.Series:
    """Median of the ``half_window`` readings either side of each reading,
    excluding the reading itself (at the series edges fewer neighbours are used)."""
    shifted = [s.shift(k) for k in range(-half_window, half_window + 1) if k != 0]
    return pd.concat(shifted, axis=1).median(axis=1, skipna=True)


def flag_spikes(s: pd.Series, half_window: int = 3, k: float = 8.0) -> pd.Series:
    """Flag readings that depart abruptly from their neighbours.

    Each reading is compared with the median of the three readings either side
    of it (30 minutes each way), excluding itself. The residuals are scaled by
    their robust standard deviation (1.4826 x MAD) and readings more than ``k``
    robust SDs away are flagged. Smooth daily ramps leave small residuals, so
    only abrupt, short-lived departures are flagged.
    """
    resid = s - neighbour_median(s, half_window)
    scale = 1.4826 * np.median(np.abs(resid - np.median(resid)))
    return (resid.abs() > k * scale).rename(f"{s.name}_spike")


# ---------------------------------------------------------------------------
# Preparation
# ---------------------------------------------------------------------------

def prepare(raw: pd.DataFrame) -> pd.DataFrame:
    """Return the cleaned 10-minute dataset with time features.

    No reading is removed or altered: the inspection finds no missing values,
    duplicates or impossible values, and flagged spikes are kept (and marked)
    because they look like real network events. Columns are renamed to short
    names, and time features are added.
    """
    df = raw.copy()
    df["Datetime"] = parse_datetime(df["Datetime"])
    df = df.rename(columns=ZONE_COLUMNS).sort_values("Datetime").reset_index(drop=True)
    df = add_time_features(df)
    df["Total"] = df[ZONES].sum(axis=1)
    df["WindState"] = np.where(df["WindSpeed"] > 2.0, "High", "Low")
    for z in ZONES:
        df[f"{z}_spike"] = flag_spikes(df[z]).values
    return df


def add_time_features(df: pd.DataFrame, col: str = "Datetime") -> pd.DataFrame:
    """Add Year, Month, Day, Hour, DayOfWeek, Date and calendar flags."""
    dt = df[col].dt
    out = df.copy()
    out["Year"] = dt.year
    out["Month"] = dt.month
    out["MonthName"] = pd.Categorical(dt.month.map(lambda m: MONTH_NAMES[m - 1]),
                                      categories=MONTH_NAMES, ordered=True)
    out["Day"] = dt.day
    out["Hour"] = dt.hour
    out["DayOfWeek"] = dt.day_of_week  # Monday = 0
    out["DayName"] = pd.Categorical(dt.day_of_week.map(lambda d: DAY_NAMES[d]),
                                    categories=DAY_NAMES, ordered=True)
    out["Date"] = dt.normalize()
    out["IsWeekend"] = dt.day_of_week >= 5
    out["IsRamadan"] = out["Date"].between(*RAMADAN)
    out["Holiday"] = out["Date"].dt.strftime("%Y-%m-%d").map(HOLIDAYS_2017)
    out["IsHoliday"] = out["Holiday"].notna()
    return out


def aggregate(df: pd.DataFrame, rule: str) -> pd.DataFrame:
    """Average every numeric reading over ``rule`` periods ("h" or "D").

    Because the readings are average loads (kW), the mean is the correct
    aggregate: the hourly mean is the average load in that hour. Summing six
    10-minute values would give a number six times too large with no physical
    meaning. ``n_readings`` is kept so incomplete periods can be detected.

    Means are rounded to 9 decimal places. The raw values have at most six,
    so nothing real is lost, but it removes floating-point noise from the
    summation order: without it, two hours with identical readings can get
    means that differ in the last bit and are then ranked as different values,
    which changes rank statistics (Spearman) in the fifth decimal place.
    """
    value_cols = ENV + IRRADIANCE + ZONES + ["Total"]
    g = df.set_index("Datetime")[value_cols].resample(rule)
    out = g.mean().round(9)
    out["n_readings"] = g["Total"].count()
    out["HighWindShare"] = (df.set_index("Datetime")["WindSpeed"] > 2.0).resample(rule).mean()
    out = out.reset_index()
    return add_time_features(out)


def energy_mwh(mean_kw: float, hours: float) -> float:
    """Derived energy (MWh) from an average load in kW over ``hours``."""
    return mean_kw * hours / 1000.0


# ---------------------------------------------------------------------------
# Descriptive statistics
# ---------------------------------------------------------------------------

def describe(s: pd.Series) -> dict:
    """Descriptive statistics for one series (sample variance and SD, ddof=1)."""
    x = np.asarray(s, dtype=float)
    q1, med, q3 = np.percentile(x, [25, 50, 75])
    p5, p95 = np.percentile(x, [5, 95])
    mean = x.mean()
    sd = x.std(ddof=1)
    return {
        "n": x.size,
        "mean": mean,
        "median": med,
        "min": x.min(),
        "max": x.max(),
        "range": x.max() - x.min(),
        "std": sd,
        "variance": x.var(ddof=1),
        "q1": q1,
        "q3": q3,
        "iqr": q3 - q1,
        "p5": p5,
        "p95": p95,
        "cv": sd / mean,
        "skewness": stats.skew(x, bias=False),
        "excess_kurtosis": stats.kurtosis(x, fisher=True, bias=False),
        "load_factor": mean / x.max(),
        "peak_to_trough": x.max() / x.min(),
        "sem": stats.sem(x),
    }


def describe_zones(df: pd.DataFrame, cols=ZONES) -> pd.DataFrame:
    """``describe`` for each column, as a table with one row per column."""
    return pd.DataFrame({c: describe(df[c]) for c in cols}).T


# ---------------------------------------------------------------------------
# Inference under serial correlation
# ---------------------------------------------------------------------------

def acf(x, nlags: int) -> np.ndarray:
    """Sample autocorrelation at lags 0..nlags (biased estimator, as in statsmodels)."""
    x = np.asarray(x, dtype=float)
    x = x - x.mean()
    n = x.size
    # FFT with zero padding gives the same values as the direct sum, much faster
    size = 1 << int(np.ceil(np.log2(2 * n - 1)))
    f = np.fft.rfft(x, size)
    full = np.fft.irfft(f * np.conj(f), size)[: nlags + 1]
    return full / full[0]


def effective_n(x, y, max_lag: int | None = None) -> float:
    """Effective sample size for a correlation between two autocorrelated series.

    Bartlett / Pyper & Peterman (1998):
        n_eff = n / (1 + 2 * sum_k w_k * r_xx(k) * r_yy(k))
    with Bartlett weights w_k = 1 - k/(max_lag+1). ``max_lag`` defaults to
    n // 5. The result is capped at n and floored at 3.
    """
    x = np.asarray(x, dtype=float)
    y = np.asarray(y, dtype=float)
    n = x.size
    if max_lag is None:
        max_lag = max(1, n // 5)
    rx = acf(x, max_lag)[1:]
    ry = acf(y, max_lag)[1:]
    w = 1 - np.arange(1, max_lag + 1) / (max_lag + 1)
    denom = 1 + 2 * np.sum(w * rx * ry)
    return float(np.clip(n / denom, 3, n))


def corr_test(x, y, method: str = "spearman", n_eff: float | None = None) -> dict:
    """Correlation with naive and serial-correlation-adjusted p-values and a 95% CI.

    The adjusted p-value and the Fisher-z interval use ``n_eff`` in place of n.
    For Spearman the standard error uses the Bonett & Wright (2000) inflation
    factor sqrt(1 + r^2/2).
    """
    x = np.asarray(x, dtype=float)
    y = np.asarray(y, dtype=float)
    if method == "spearman":
        res = stats.spearmanr(x, y)
        r, p_naive = float(res.statistic), float(res.pvalue)
    elif method == "pearson":
        res = stats.pearsonr(x, y)
        r, p_naive = float(res.statistic), float(res.pvalue)
    else:
        raise ValueError(method)
    n = x.size
    if n_eff is None:
        if method == "spearman":  # dependence of the ranks is what matters
            n_eff = effective_n(stats.rankdata(x), stats.rankdata(y))
        else:
            n_eff = effective_n(x, y)
    # t-test of r with n_eff - 2 degrees of freedom
    df_ = max(n_eff - 2, 1)
    t = r * np.sqrt(df_ / max(1 - r ** 2, 1e-12))
    p_adj = float(2 * stats.t.sf(abs(t), df_))
    # Fisher z interval
    z = np.arctanh(np.clip(r, -0.999999, 0.999999))
    se = 1 / np.sqrt(max(n_eff - 3, 1))
    if method == "spearman":
        se *= np.sqrt(1 + r ** 2 / 2)
    lo, hi = np.tanh(z - 1.96 * se), np.tanh(z + 1.96 * se)
    return {"method": method, "r": r, "n": n, "n_eff": n_eff,
            "p_naive": p_naive, "p_adjusted": p_adj, "ci_low": lo, "ci_high": hi}


def strength_label(r: float) -> str:
    """Verbal label for |r| (Cohen-style bands used in the report)."""
    a = abs(r)
    if a < 0.1:
        label = "negligible"
    elif a < 0.3:
        label = "weak"
    elif a < 0.5:
        label = "moderate"
    elif a < 0.7:
        label = "strong"
    else:
        label = "very strong"
    if label == "negligible":
        return label
    return f"{label} {'positive' if r > 0 else 'negative'}"


def block_bootstrap(data: np.ndarray, stat, block: int = 7, n_boot: int = 2000,
                    seed: int = 2017) -> np.ndarray:
    """Moving-block bootstrap of ``stat`` applied to rows of ``data``.

    ``data`` is an (n, k) array of consecutive observations (for example daily
    means for k zones). Blocks of ``block`` consecutive rows are drawn with
    replacement and joined until n rows are reached, which keeps the
    short-range dependence inside each block. Returns the ``n_boot``
    bootstrap statistics.
    """
    data = np.asarray(data, dtype=float)
    if data.ndim == 1:
        data = data[:, None]
    n = data.shape[0]
    rng = np.random.default_rng(seed)
    n_blocks = int(np.ceil(n / block))
    starts_max = n - block + 1
    out = []
    for _ in range(n_boot):
        starts = rng.integers(0, starts_max, size=n_blocks)
        idx = (starts[:, None] + np.arange(block)).ravel()[:n]
        out.append(stat(data[idx]))
    return np.asarray(out)


def percentile_ci(boot: np.ndarray, level: float = 0.95) -> tuple[float, float]:
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


def epsilon_squared(h: float, n: int) -> float:
    """Effect size for Kruskal-Wallis: epsilon^2 = H / ((n^2 - 1) / (n + 1)) = H/(n-1)."""
    return h / (n - 1)


def kendalls_w(chi2: float, n_blocks: int, k: int) -> float:
    """Effect size for the Friedman test: W = chi2 / (n (k - 1))."""
    return chi2 / (n_blocks * (k - 1))


def rank_biserial_paired(x, y) -> float:
    """Matched-pairs rank-biserial correlation for a Wilcoxon signed-rank test."""
    d = np.asarray(x, dtype=float) - np.asarray(y, dtype=float)
    d = d[d != 0]
    ranks = stats.rankdata(np.abs(d))
    r_plus = ranks[d > 0].sum()
    r_minus = ranks[d < 0].sum()
    return (r_plus - r_minus) / ranks.sum()


# ---------------------------------------------------------------------------
# Models
# ---------------------------------------------------------------------------

def hinge_fit(temp, load, grid=None) -> dict:
    """Fit ``load = a + b * max(0, temp - base)`` by least squares over a grid of bases.

    A change-point ("degree-day") model: below the base temperature load does
    not depend on temperature; above it, load rises by ``b`` kW per degree C.
    Returns the base with the lowest residual sum of squares, its slope,
    intercept and R^2, and the full RSS profile.
    """
    t = np.asarray(temp, dtype=float)
    y = np.asarray(load, dtype=float)
    if grid is None:
        grid = np.arange(np.percentile(t, 10), np.percentile(t, 90) + 1e-9, 0.25)
    sst = np.sum((y - y.mean()) ** 2)
    best = None
    profile = []
    for base in grid:
        X = np.column_stack([np.ones_like(t), np.maximum(0, t - base)])
        coef, *_ = np.linalg.lstsq(X, y, rcond=None)
        rss = float(np.sum((y - X @ coef) ** 2))
        profile.append((base, rss))
        if best is None or rss < best["rss"]:
            best = {"base": float(base), "intercept": float(coef[0]),
                    "slope": float(coef[1]), "rss": rss, "r2": 1 - rss / sst}
    best["profile"] = pd.DataFrame(profile, columns=["base", "rss"])
    return best


def seasonal_strength(seasonal, resid) -> float:
    """Wang, Smith & Hyndman (2006) strength of seasonality: max(0, 1 - Var(R)/Var(S+R))."""
    s = np.asarray(seasonal, dtype=float)
    r = np.asarray(resid, dtype=float)
    return float(max(0.0, 1 - np.var(r) / np.var(s + r)))


def trend_strength(trend, resid) -> float:
    """Strength of trend: max(0, 1 - Var(R)/Var(T+R))."""
    t = np.asarray(trend, dtype=float)
    r = np.asarray(resid, dtype=float)
    return float(max(0.0, 1 - np.var(r) / np.var(t + r)))
