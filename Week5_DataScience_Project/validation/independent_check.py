"""Independent recalculation of the Week 5 key figures using only the Python
standard library (csv, datetime, math, statistics).

It reads the raw CSV directly, without pandas, NumPy, SciPy or the project's
power_prep module, recomputes every figure listed in Outputs/key_figures.csv
(written by the notebook), and prints PASS or FAIL for each. It exits with
status 1 if any figure disagrees.

Run from the project folder after the notebook:
    python validation/independent_check.py
"""

import csv
import math
import sys
from collections import defaultdict
from datetime import date, datetime
from pathlib import Path

HERE = Path(__file__).resolve().parent.parent
RAW = HERE / "Data" / "powerconsumption.csv"
KEY = HERE / "Outputs" / "key_figures.csv"
ZONES = ["Zone1", "Zone2", "Zone3"]
REL_TOL = 1e-6

RAMADAN = (date(2017, 5, 27), date(2017, 6, 25))
BEFORE = (date(2017, 5, 6), date(2017, 5, 26))
MONTHS = {"Jan": 1, "Jul": 7, "Aug": 8, "Dec": 12}


# --- helpers -----------------------------------------------------------------

def mean(xs):
    return math.fsum(xs) / len(xs)


def sd(xs):
    m = mean(xs)
    return math.sqrt(math.fsum((x - m) ** 2 for x in xs) / (len(xs) - 1))


def percentile(xs, q):
    """Linear interpolation between closest ranks (NumPy's default method)."""
    s = sorted(xs)
    pos = (len(s) - 1) * q
    lo = math.floor(pos)
    hi = math.ceil(pos)
    return s[lo] + (s[hi] - s[lo]) * (pos - lo)


def ranks(xs):
    """Average ranks (1-based), ties share the mean rank."""
    order = sorted(range(len(xs)), key=lambda i: xs[i])
    r = [0.0] * len(xs)
    i = 0
    while i < len(order):
        j = i
        while j + 1 < len(order) and xs[order[j + 1]] == xs[order[i]]:
            j += 1
        avg = (i + j) / 2 + 1
        for k in range(i, j + 1):
            r[order[k]] = avg
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


# --- read the raw file -------------------------------------------------------

rows = []
with open(RAW, newline="", encoding="utf-8-sig") as f:
    for r in csv.DictReader(f):
        rows.append({
            "t": datetime.strptime(r["Datetime"], "%m/%d/%Y %H:%M"),
            "Temperature": float(r["Temperature"]),
            "Humidity": float(r["Humidity"]),
            "WindSpeed": float(r["WindSpeed"]),
            "Zone1": float(r["PowerConsumption_Zone1"]),
            "Zone2": float(r["PowerConsumption_Zone2"]),
            "Zone3": float(r["PowerConsumption_Zone3"]),
        })
for r in rows:
    r["Total"] = r["Zone1"] + r["Zone2"] + r["Zone3"]

calc = {"n_rows": len(rows)}

# descriptive statistics of the 10-minute readings
for z in ZONES + ["Total"]:
    xs = [r[z] for r in rows]
    calc[f"{z}_mean"] = mean(xs)
    calc[f"{z}_median"] = percentile(xs, 0.5)
    calc[f"{z}_std"] = sd(xs)
    calc[f"{z}_min"] = min(xs)
    calc[f"{z}_max"] = max(xs)
    calc[f"{z}_q1"] = percentile(xs, 0.25)
    calc[f"{z}_q3"] = percentile(xs, 0.75)
for z in ZONES:
    calc[f"{z}_cv"] = calc[f"{z}_std"] / calc[f"{z}_mean"]

# hourly and daily means (every hour has 6 readings, every day 144)
hour_groups = defaultdict(list)
day_groups = defaultdict(list)
for r in rows:
    hour_groups[r["t"].replace(minute=0)].append(r)
    day_groups[r["t"].date()].append(r)
assert all(len(v) == 6 for v in hour_groups.values()), "incomplete hour"
assert all(len(v) == 144 for v in day_groups.values()), "incomplete day"


def agg(groups):
    out = []
    for k in sorted(groups):
        g = groups[k]
        rec = {"key": k}
        for c in ["Temperature", "Humidity", "WindSpeed"] + ZONES + ["Total"]:
            # rounded to 9 dp as in power_prep.aggregate, so true ties stay ties
            rec[c] = round(mean([r[c] for r in g]), 9)
        out.append(rec)
    return out


hourly = agg(hour_groups)
daily = agg(day_groups)

# hour-of-day profile
for z in ZONES:
    by_hour = defaultdict(list)
    for h in hourly:
        by_hour[h["key"].hour].append(h[z])
    prof = {hr: mean(v) for hr, v in by_hour.items()}
    calc[f"{z}_peak_hour"] = max(prof, key=prof.get)
    calc[f"{z}_trough_hour"] = min(prof, key=prof.get)
    calc[f"{z}_peak_hour_mean"] = max(prof.values())

# day of week
calc["Total_sunday_mean"] = mean([d["Total"] for d in daily if d["key"].weekday() == 6])
calc["Total_weekday_mean"] = mean([d["Total"] for d in daily if d["key"].weekday() < 5])

# months
for z in ZONES + ["Total"]:
    for name, m in MONTHS.items():
        calc[f"{z}_{name}_mean"] = mean([d[z] for d in daily if d["key"].month == m])
for z in ZONES:
    jul = mean([d[z] for d in daily if d["key"].month == 7])
    calc[f"{z}_jul_index_pct"] = (jul / mean([d[z] for d in daily]) - 1) * 100

# Autumn vs spring level on days with a mean temperature of 11-18 C
cool = [d for d in daily if 11 <= d["Temperature"] <= 18]
for z in ZONES:
    spring = mean([d[z] for d in cool if d["key"].month <= 5])
    autumn = mean([d[z] for d in cool if d["key"].month >= 10])
    calc[f"{z}_autumn_vs_spring_pct"] = (autumn / spring - 1) * 100


# Ramadan night load (01:00-03:59) against the three weeks before
def night(a, b):
    return mean([h["Total"] for h in hourly if a <= h["key"].date() <= b and 1 <= h["key"].hour <= 3])


calc["ramadan_night_ratio"] = night(*RAMADAN) / night(*BEFORE)

# correlations
for z in ZONES:
    for v in ["Temperature", "Humidity", "WindSpeed"]:
        calc[f"spearman_hourly_{v}_{z}"] = spearman([h[v] for h in hourly], [h[z] for h in hourly])
        calc[f"pearson_daily_{v}_{z}"] = pearson([d[v] for d in daily], [d[z] for d in daily])

# zone shares and the Friedman test across zones (days as blocks)
total_mean = sum(mean([d[z] for d in daily]) for z in ZONES)
for z in ZONES:
    calc[f"{z}_share_of_total"] = mean([d[z] for d in daily]) / total_mean
n, k = len(daily), 3
rank_sums = [0.0] * k
for d in daily:
    rr = ranks([d[z] for z in ZONES])
    for j in range(k):
        rank_sums[j] += rr[j]
calc["friedman_zones_daily_chi2"] = 12 / (n * k * (k + 1)) * sum(R * R for R in rank_sums) - 3 * n * (k + 1)

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
    ok = math.isclose(got, want, rel_tol=REL_TOL, abs_tol=1e-9)
    print(f"{'PASS' if ok else 'FAIL'}  {name:<34} notebook {want:>16,.6f}   independent {got:>16,.6f}")
    passed += ok
    failed += not ok
print(f"\n{passed} passed, {failed} failed")
sys.exit(1 if failed else 0)
