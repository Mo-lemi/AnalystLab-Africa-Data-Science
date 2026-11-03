"""Independent reconciliation of the Week 3 notebook's key figures.

Recomputes the figures in Outputs/key_figures.csv straight from the raw CSVs using only
Python's standard library (no pandas, NumPy or SciPy), so an error in the notebook's
pandas/SciPy code cannot repeat itself here. Prints PASS/FAIL per figure and exits with
status 1 if anything fails to reconcile.

Usage (from the Week3_DataScience_Project folder):
    python validation/independent_check.py
"""
import csv
import statistics
import sys
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path

PROJECT_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_DIR / "Data"
KEY_FIGURES = PROJECT_DIR / "Outputs" / "key_figures.csv"

CLASS_ORDER = ["ambulatory", "outpatient", "urgentcare", "emergency", "wellness", "inpatient"]
ISO_UTC = "%Y-%m-%dT%H:%M:%SZ"


def read_csv(name):
    with open(DATA_DIR / f"{name}.csv", encoding="utf-8-sig", newline="") as fh:
        return list(csv.DictReader(fh))


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


def spearman_rho(x, y):
    # Pearson correlation of the average ranks
    rx, ry = average_ranks(x), average_ranks(y)
    mx, my = statistics.fmean(rx), statistics.fmean(ry)
    cov = sum((a - mx) * (b - my) for a, b in zip(rx, ry))
    var_x = sum((a - mx) ** 2 for a in rx)
    var_y = sum((b - my) ** 2 for b in ry)
    return cov / (var_x * var_y) ** 0.5


def compute_figures():
    encounters = read_csv("encounters")
    procedures = read_csv("procedures")

    for r in encounters:
        start = datetime.strptime(r["START"], ISO_UTC)
        stop = datetime.strptime(r["STOP"], ISO_UTC)
        r["duration_h"] = (stop - start).total_seconds() / 3600
        r["cost"] = float(r["TOTAL_CLAIM_COST"])
        r["suspect"] = r["duration_h"] > 24 and r["ENCOUNTERCLASS"] != "inpatient"

    procedure_cost = defaultdict(float)
    for p in procedures:
        procedure_cost[p["ENCOUNTER"]] += float(p["BASE_COST"])

    by_class = defaultdict(list)
    by_patient_class = defaultdict(list)
    for r in encounters:
        by_class[r["ENCOUNTERCLASS"]].append(r)
        by_patient_class[(r["PATIENT"], r["ENCOUNTERCLASS"])].append(r["cost"])

    patient_medians = defaultdict(list)
    for (_, cls), costs in by_patient_class.items():
        patient_medians[cls].append(statistics.median(costs))

    figures = {}
    for cls in CLASS_ORDER:
        figures[f"encounters_{cls}"] = len(by_class[cls])
        figures[f"median_claim_{cls}"] = statistics.median(r["cost"] for r in by_class[cls])
        figures[f"patient_level_median_{cls}"] = statistics.median(patient_medians[cls])
    figures["encounters_total"] = len(encounters)
    figures["encounters_over_24h"] = sum(r["duration_h"] > 24 for r in encounters)
    figures["duration_suspect"] = sum(r["suspect"] for r in encounters)
    figures["zero_claim_encounters"] = sum(r["cost"] == 0 for r in encounters)
    # Equal to the cent: half-cent tolerance so the 1-cent rounding differences never sit on the boundary
    figures["total_equals_base_plus_procedures"] = sum(
        abs(r["cost"] - float(r["BASE_ENCOUNTER_COST"]) - procedure_cost[r["Id"]]) <= 0.005 for r in encounters)
    figures["h1_kruskal_H_patient_level"] = kruskal_h([patient_medians[c] for c in CLASS_ORDER])
    figures["h1_kruskal_H_encounter_level"] = kruskal_h([[r["cost"] for r in by_class[c]] for c in CLASS_ORDER])
    for cls in CLASS_ORDER:
        valid = [r for r in by_class[cls] if not r["suspect"]]
        if len({round(r["duration_h"], 3) for r in valid}) > 1:
            figures[f"h2_rho_{cls}"] = spearman_rho([r["duration_h"] for r in valid], [r["cost"] for r in valid])
    return figures


def main():
    figures = compute_figures()
    if not KEY_FIGURES.exists():
        print(f"{KEY_FIGURES} not found; run the notebook first. Independently computed figures:")
        for name, value in figures.items():
            print(f"  {name:40s} {value:,.4f}")
        return 1

    with open(KEY_FIGURES, encoding="utf-8", newline="") as fh:
        notebook = {row["figure"]: float(row["value"]) for row in csv.DictReader(fh)}

    failures = 0
    print(f"{'figure':40s} {'notebook':>16s} {'independent':>16s}  result")
    for name in sorted(set(notebook) | set(figures)):
        nb_value, own_value = notebook.get(name), figures.get(name)
        ok = (nb_value is not None and own_value is not None
              and abs(nb_value - own_value) <= 1e-6 * max(1.0, abs(own_value)))
        failures += not ok
        fmt = lambda v: "missing" if v is None else f"{v:,.4f}"
        print(f"{name:40s} {fmt(nb_value):>16s} {fmt(own_value):>16s}  {'PASS' if ok else 'FAIL'}")
    print(f"\n{len(notebook) + len(set(figures) - set(notebook)) - failures} passed, {failures} failed")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
