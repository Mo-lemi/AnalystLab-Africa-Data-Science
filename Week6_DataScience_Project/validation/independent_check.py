"""Independent recalculation of the Week 6 key figures using only the Python
standard library (csv, datetime, math).

It reads the raw CSV directly, without pandas, NumPy, SciPy or the project's
stock_prep module, and re-implements the parsing, sorting, return
calculation, data-quality flags and statistics from their definitions. It
recomputes every figure in Outputs/key_figures.csv (written by the notebook),
prints PASS or FAIL for each and exits with status 1 if any disagree.

Run from the project folder after the notebook:
    python validation/independent_check.py
"""

import csv
import math
import sys
from collections import defaultdict
from datetime import datetime
from pathlib import Path

HERE = Path(__file__).resolve().parent.parent
RAW = HERE / "Data" / "S&P 500 Stock Prices 2014-2017.csv"
KEY = HERE / "Outputs" / "key_figures.csv"
SELECTED = ["AAPL", "AMZN", "JPM", "JNJ", "XOM", "WMT"]
REL_TOL = 1e-6

# The same documented event list as the notebook (an input, not a calculation)
CORPORATE_ACTIONS = {
    ("SPG", "2014-05-28"), ("DISCA", "2014-08-07"), ("DISCK", "2014-08-07"), ("A", "2014-11-03"),
    ("BAX", "2015-07-01"), ("NI", "2015-07-02"), ("EBAY", "2015-07-20"), ("ARNC", "2016-11-01"),
    ("YUM", "2016-11-01"), ("CAG", "2016-11-10"), ("HPE", "2017-04-03"), ("BHGE", "2017-07-05"),
}


# --- statistics from first principles ----------------------------------------

def mean(xs):
    return math.fsum(xs) / len(xs)


def sd(xs):
    m = mean(xs)
    return math.sqrt(math.fsum((x - m) ** 2 for x in xs) / (len(xs) - 1))


def median(xs):
    s = sorted(xs)
    n = len(s)
    return s[n // 2] if n % 2 else (s[n // 2 - 1] + s[n // 2]) / 2


def central_moment(xs, k):
    m = mean(xs)
    return math.fsum((x - m) ** k for x in xs) / len(xs)


def skewness(xs):
    """Adjusted Fisher-Pearson coefficient G1 (bias-corrected)."""
    n = len(xs)
    g1 = central_moment(xs, 3) / central_moment(xs, 2) ** 1.5
    return math.sqrt(n * (n - 1)) / (n - 2) * g1


def excess_kurtosis(xs):
    """Bias-corrected excess kurtosis G2."""
    n = len(xs)
    g2 = central_moment(xs, 4) / central_moment(xs, 2) ** 2 - 3
    return ((n + 1) * g2 + 6) * (n - 1) / ((n - 2) * (n - 3))


def ranks(xs):
    """Average ranks (1-based); ties share the mean rank."""
    order = sorted(range(len(xs)), key=lambda i: xs[i])
    r = [0.0] * len(xs)
    i = 0
    while i < len(order):
        j = i
        while j + 1 < len(order) and xs[order[j + 1]] == xs[order[i]]:
            j += 1
        for k in range(i, j + 1):
            r[order[k]] = (i + j) / 2 + 1
        i = j + 1
    return r


def pearson(x, y):
    mx, my = mean(x), mean(y)
    sxy = math.fsum((a - mx) * (b - my) for a, b in zip(x, y))
    sxx = math.fsum((a - mx) ** 2 for a in x)
    syy = math.fsum((b - my) ** 2 for b in y)
    return sxy / math.sqrt(sxx * syy)


def spearman(x, y):
    return pearson(ranks(x), ranks(y))


def friedman_chi2(blocks):
    """Friedman statistic with the tie correction; ``blocks`` is a list of rows (one value per group)."""
    n, k = len(blocks), len(blocks[0])
    rank_sums = [0.0] * k
    tie_sum = 0.0
    for row in blocks:
        rr = ranks(row)
        for j in range(k):
            rank_sums[j] += rr[j]
        counts = defaultdict(int)
        for v in row:
            counts[v] += 1
        tie_sum += sum(t ** 3 - t for t in counts.values())
    chi2 = 12 / (n * k * (k + 1)) * sum(R * R for R in rank_sums) - 3 * n * (k + 1)
    return chi2 / (1 - tie_sum / (n * k * (k * k - 1)))


def brown_forsythe_f(groups):
    """Levene's test statistic centred on the group medians."""
    z = [[abs(x - median(g)) for x in g] for g in groups]
    k = len(z)
    N = sum(len(g) for g in z)
    zbar_i = [mean(g) for g in z]
    zbar = math.fsum(math.fsum(g) for g in z) / N
    between = math.fsum(len(g) * (zi - zbar) ** 2 for g, zi in zip(z, zbar_i))
    within = math.fsum(math.fsum((x - zi) ** 2 for x in g) for g, zi in zip(z, zbar_i))
    return (N - k) / (k - 1) * between / within


def parse_float(s):
    s = s.strip()
    return None if s in ("", "NA", "NaN", "nan") else float(s)


# --- read and order the raw file --------------------------------------------

rows = []
with open(RAW, newline="", encoding="utf-8-sig") as f:
    for r in csv.DictReader(f):
        rows.append({
            "symbol": r["symbol"],
            "date": datetime.strptime(r["date"], "%m/%d/%Y").date(),
            "open": parse_float(r["open"]), "high": parse_float(r["high"]),
            "low": parse_float(r["low"]), "close": float(r["close"]),
            "volume": int(r["volume"]),
        })

calc = {"n_rows": len(rows)}
calendar = sorted({r["date"] for r in rows})
pos = {d: i for i, d in enumerate(calendar)}
calc["n_dates"] = len(calendar)
calc["missing_open"] = sum(r["open"] is None for r in rows)
calc["missing_high"] = sum(r["high"] is None for r in rows)
calc["missing_low"] = sum(r["low"] is None for r in rows)
calc["zero_volume_rows"] = sum(r["volume"] == 0 for r in rows)
seen = set()
dup = 0
for r in rows:
    k = (r["symbol"], r["date"])
    dup += k in seen
    seen.add(k)
calc["duplicate_symbol_dates"] = dup

by_symbol = defaultdict(list)
for r in rows:
    by_symbol[r["symbol"]].append(r)
for s in by_symbol:
    by_symbol[s].sort(key=lambda r: r["date"])
calc["n_symbols"] = len(by_symbol)
calc["complete_histories"] = sum(len(v) == len(calendar) for v in by_symbol.values())

# price consistency
inconsistent = 0
for r in rows:
    present = {k: r[k] for k in ("open", "high", "low", "close") if r[k] is not None}
    bad = False
    if "high" in present and present["high"] < max(v for k, v in present.items() if k != "high") - 1e-9:
        bad = True
    if "low" in present and present["low"] > min(v for k, v in present.items() if k != "low") + 1e-9:
        bad = True
    inconsistent += bad
calc["ohlc_inconsistent_rows"] = inconsistent

# returns and flags
price_errors = multi_day = valid = 0
valid_by_date = defaultdict(list)
returns = {}       # symbol -> {date: return} (valid only)
for s, recs in by_symbol.items():
    rets = [None] + [recs[i]["close"] / recs[i - 1]["close"] - 1 for i in range(1, len(recs))]
    err = [False] * len(recs)
    for i in range(1, len(recs) - 1):
        r_in, r_out = rets[i], rets[i + 1]
        if abs(r_in) >= 0.20 and abs((1 + r_in) * (1 + r_out) - 1) <= 0.05:
            err[i] = True
    price_errors += sum(err)
    returns[s] = {}
    for i in range(1, len(recs)):
        gap = pos[recs[i]["date"]] - pos[recs[i - 1]["date"]] > 1
        multi_day += gap
        ca = (s, recs[i]["date"].isoformat()) in CORPORATE_ACTIONS
        if not (gap or err[i] or err[i - 1] or ca):
            valid += 1
            returns[s][recs[i]["date"]] = rets[i]
            valid_by_date[recs[i]["date"]].append(rets[i])
calc["price_error_flags"] = price_errors
calc["multi_day_returns"] = multi_day
calc["valid_returns"] = valid
calc["max_close_all"] = max(r["close"] for r in rows)
calc["min_close_all"] = min(r["close"] for r in rows)

growth = 1.0
for d in sorted(valid_by_date):
    growth *= 1 + mean(valid_by_date[d])
calc["market_avg_total_return"] = growth - 1

complete = [s for s, v in by_symbol.items() if len(v) == len(calendar)]
tot = {s: by_symbol[s][-1]["close"] / by_symbol[s][0]["close"] - 1 for s in complete}
calc["median_total_return_complete"] = median(list(tot.values()))
calc["NVDA_total_return"] = tot["NVDA"]
calc["CHK_total_return"] = tot["CHK"]

# the six selected stocks
dates_all = [d for d in calendar[1:]]
R = {}
for s in SELECTED:
    recs = by_symbol[s]
    closes = [r["close"] for r in recs]
    r = [returns[s][d] for d in dates_all]
    R[s] = r
    calc[f"{s}_first_close"] = closes[0]
    calc[f"{s}_last_close"] = closes[-1]
    calc[f"{s}_mean_close"] = mean(closes)
    calc[f"{s}_median_close"] = median(closes)
    calc[f"{s}_std_close"] = sd(closes)
    calc[f"{s}_min_close"] = min(closes)
    calc[f"{s}_max_close"] = max(closes)
    calc[f"{s}_total_return"] = closes[-1] / closes[0] - 1
    calc[f"{s}_mean_daily_return"] = mean(r)
    calc[f"{s}_median_daily_return"] = median(r)
    calc[f"{s}_std_daily_return"] = sd(r)
    calc[f"{s}_max_daily_return"] = max(r)
    calc[f"{s}_min_daily_return"] = min(r)
    calc[f"{s}_skewness"] = skewness(r)
    calc[f"{s}_excess_kurtosis"] = excess_kurtosis(r)
    calc[f"{s}_ma20_last"] = mean(closes[-20:])
    calc[f"{s}_ma200_last"] = mean(closes[-200:])
    calc[f"{s}_mean_volume"] = mean([x["volume"] for x in recs])
    peak, worst = closes[0], 0.0
    for c in closes:
        peak = max(peak, c)
        worst = min(worst, c / peak - 1)
    calc[f"{s}_max_drawdown"] = worst
    calc[f"{s}_t_stat"] = mean(r) / (sd(r) / math.sqrt(len(r)))

for i, a in enumerate(SELECTED):
    for b in SELECTED[i + 1:]:
        calc[f"spearman_{a}_{b}"] = spearman(R[a], R[b])
        calc[f"pearson_{a}_{b}"] = pearson(R[a], R[b])

blocks = [[R[s][t] for s in SELECTED] for t in range(len(dates_all))]
calc["friedman_location_chi2"] = friedman_chi2(blocks)
calc["brown_forsythe_F"] = brown_forsythe_f([R[s] for s in SELECTED])
calc["equal_weight_portfolio_ann_vol"] = sd([mean(b) for b in blocks]) * math.sqrt(252)

# --- compare -----------------------------------------------------------------

with open(KEY, newline="", encoding="utf-8") as f:
    expected = list(csv.DictReader(f))

passed = failed = 0
for row in expected:
    name, want = row["figure"], float(row["value"])
    got = calc.get(name)
    if got is None:
        print(f"FAIL  {name}: not recomputed")
        failed += 1
        continue
    ok = math.isclose(got, want, rel_tol=REL_TOL, abs_tol=1e-12)
    print(f"{'PASS' if ok else 'FAIL'}  {name:<34} notebook {want:>18,.8f}   independent {got:>18,.8f}")
    passed += ok
    failed += not ok
print(f"\n{passed} passed, {failed} failed")
sys.exit(1 if failed else 0)
