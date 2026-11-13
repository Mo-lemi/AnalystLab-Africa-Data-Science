"""Independent reconciliation of the Week 4 notebook's key figures.

Recomputes the figures in Outputs/key_figures.csv straight from the raw Excel file using only
Python's standard library: no pandas, NumPy, SciPy or openpyxl. The .xlsx file is read as the zip
of XML files it is, so an error in the notebook's pandas/SciPy code, or in pandas' Excel reader,
cannot repeat itself here. Prints PASS/FAIL per figure and exits with status 1 if anything fails
to reconcile.

Usage (from the Week4_DataScience_Project folder):
    python validation/independent_check.py
"""
import csv
import re
import statistics
import sys
import zipfile
import xml.etree.ElementTree as ET
from collections import Counter, defaultdict
from datetime import date, timedelta
from pathlib import Path

PROJECT_DIR = Path(__file__).resolve().parent.parent
RAW_FILE = PROJECT_DIR / "Data" / "Consumer_Complaints.xlsx"
KEY_FIGURES = PROJECT_DIR / "Outputs" / "key_figures.csv"

NS = {"m": "http://schemas.openxmlformats.org/spreadsheetml/2006/main"}
EXCEL_EPOCH = date(1899, 12, 30)  # Excel 1900 date system
DATE_COLUMNS = {"Date submitted", "Date received"}
SMALL_PRODUCTS = {"Vehicle loan or lease", "Payday loan, title loan, or personal loan", "Student loan"}
RESPONSES = ["Closed with explanation", "Closed with monetary relief", "Closed with non-monetary relief"]
LONG_FORWARDING_DAYS = 30
TOLERANCE = 1e-6  # relative


# ------------------------------------------------------------ reading the workbook

def read_xlsx(path):
    """Return the first worksheet as a list of dicts keyed by the header row."""
    with zipfile.ZipFile(path) as z:
        shared = ["".join(t.text or "" for t in si.iter(f"{{{NS['m']}}}t"))
                  for si in ET.fromstring(z.read("xl/sharedStrings.xml")).findall("m:si", NS)]
        sheet = ET.fromstring(z.read("xl/worksheets/sheet1.xml"))
    rows = []
    for row in sheet.find("m:sheetData", NS).findall("m:row", NS):
        cells = {}
        for c in row.findall("m:c", NS):
            column = re.match(r"[A-Z]+", c.get("r")).group(0)
            v = c.find("m:v", NS)
            if v is None:
                continue
            cells[column] = shared[int(v.text)] if c.get("t") == "s" else v.text
        rows.append(cells)
    header = rows[0]
    records = []
    for cells in rows[1:]:
        record = {}
        for column, name in header.items():
            value = cells.get(column)
            if value is not None and name in DATE_COLUMNS:
                value = EXCEL_EPOCH + timedelta(days=int(float(value)))
            record[name] = value
        records.append(record)
    return records


# ------------------------------------------------------------------ statistics

def average_ranks(values):
    # Ranks 1..n, tied values share the average of their positions
    order = sorted(range(len(values)), key=values.__getitem__)
    ranks = [0.0] * len(values)
    i = 0
    while i < len(order):
        j = i
        while j + 1 < len(order) and values[order[j + 1]] == values[order[i]]:
            j += 1
        for k in range(i, j + 1):
            ranks[order[k]] = (i + j) / 2 + 1
        i = j + 1
    return ranks


def kruskal_h(groups):
    # Kruskal-Wallis H with the standard tie correction (as in scipy.stats.kruskal)
    values = [v for g in groups for v in g]
    n = len(values)
    ranks = average_ranks(values)
    rank_term, start = 0.0, 0
    for g in groups:
        rank_sum = sum(ranks[start:start + len(g)])
        rank_term += rank_sum ** 2 / len(g)
        start += len(g)
    h = 12 / (n * (n + 1)) * rank_term - 3 * (n + 1)
    tie_correction = 1 - sum(t ** 3 - t for t in Counter(values).values()) / (n ** 3 - n)
    return h / tie_correction


def chi_square(table):
    # Pearson chi-square (no continuity correction) and Cramer's V for a list-of-lists table
    n = sum(map(sum, table))
    row_totals = [sum(r) for r in table]
    col_totals = [sum(c) for c in zip(*table)]
    chi2 = sum((table[i][j] - row_totals[i] * col_totals[j] / n) ** 2 / (row_totals[i] * col_totals[j] / n)
               for i in range(len(table)) for j in range(len(col_totals)))
    v = (chi2 / (n * (min(len(table), len(col_totals)) - 1))) ** 0.5
    return chi2, v


def crosstab(records, row_key, col_key, rows, cols):
    counts = Counter((row_key(r), col_key(r)) for r in records)
    return [[counts[(a, b)] for b in cols] for a in rows]


# --------------------------------------------------------------- key figures

def compute(records):
    fig = {}
    fig["total_complaints"] = len(records)
    fig["unique_complaint_ids"] = len({r["Complaint ID"] for r in records})

    content = Counter(tuple(r[k] for k in r if k != "Complaint ID") for r in records)
    fig["content_duplicate_rows"] = sum(n for n in content.values() if n > 1)

    for year, n in Counter(r["Date submitted"].year for r in records).items():
        fig[f"complaints_{year}"] = n
    for product, n in Counter(r["Product"] for r in records).items():
        fig[f"product::{product}"] = n

    timely = Counter(r["Timely response?"] for r in records)
    fig["timely_yes"], fig["timely_no"], fig["timely_pending"] = timely["Yes"], timely["No"], timely[None]
    fig["timely_pct"] = 100 * timely["Yes"] / (timely["Yes"] + timely["No"])
    fig["in_progress"] = sum(r["Company response to consumer"] == "In progress" for r in records)

    days = [(r["Date received"] - r["Date submitted"]).days for r in records]
    fig["forwarding_mean_days"] = statistics.fmean(days)
    fig["forwarding_median_days"] = statistics.median(days)
    fig["forwarding_max_days"] = max(days)
    fig["same_day_pct"] = 100 * sum(d == 0 for d in days) / len(days)
    fig["long_forwarding_count"] = sum(d > LONG_FORWARDING_DAYS for d in days)

    # H1: Kruskal-Wallis on full-month counts grouped by year (first and last months dropped)
    months = Counter((r["Date submitted"].year, r["Date submitted"].month) for r in records)
    full = sorted(months)[1:-1]
    fig["full_months"] = len(full)
    by_year = defaultdict(list)
    for ym in full:
        by_year[ym[0]].append(months[ym])
    fig["h1_kruskal_h"] = kruskal_h([by_year[y] for y in sorted(by_year)])

    def product_test(r):
        return "Other loans" if r["Product"] in SMALL_PRODUCTS else r["Product"]

    products = sorted({product_test(r) for r in records})

    # H2: response x product, closed complaints in the three main response categories
    closed = [r for r in records if r["Company response to consumer"] in RESPONSES]
    fig["h2_chi2"], fig["h2_cramers_v"] = chi_square(
        crosstab(closed, product_test, lambda r: r["Company response to consumer"], products, RESPONSES))

    # H3: timely x year, 2017-2022, Yes/No records only
    decided = [r for r in records if r["Timely response?"] in ("Yes", "No") and r["Date submitted"].year <= 2022]
    years = sorted({r["Date submitted"].year for r in decided})
    h3 = crosstab(decided, lambda r: r["Date submitted"].year, lambda r: r["Timely response?"], years, ["Yes", "No"])
    fig["h3_chi2"], _ = chi_square(h3)
    for year, (yes, no) in zip(years, h3):
        if year in (2020, 2021):
            fig[f"untimely_pct_{year}"] = 100 * no / (yes + no)

    # H4: forwarding days by product (Kruskal-Wallis) and same-day share by product (chi-square)
    groups = defaultdict(list)
    for r, d in zip(records, days):
        groups[product_test(r)].append(d)
    fig["h4_kruskal_h"] = kruskal_h([groups[p] for p in products])
    fig["h4_same_day_chi2"], _ = chi_square([[sum(d == 0 for d in groups[p]), sum(d > 0 for d in groups[p])]
                                             for p in products])
    return fig


def main():
    with open(KEY_FIGURES, encoding="utf-8", newline="") as fh:
        notebook = {row["figure"]: float(row["value"]) for row in csv.DictReader(fh)}
    independent = compute(read_xlsx(RAW_FILE))

    failures = 0
    for name, expected in notebook.items():
        if name not in independent:
            print(f"FAIL  {name}: not recomputed")
            failures += 1
            continue
        got = independent[name]
        ok = abs(got - expected) <= TOLERANCE * max(1.0, abs(expected))
        failures += not ok
        print(f"{'PASS' if ok else 'FAIL'}  {name}: notebook {expected:,.6g}  independent {got:,.6g}")
    print(f"\n{len(notebook) - failures} of {len(notebook)} key figures reconcile.")
    sys.exit(1 if failures else 0)


if __name__ == "__main__":
    main()
