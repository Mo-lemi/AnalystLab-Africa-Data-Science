"""Pre-publication privacy check for the Week 3 project.

Scans every file that will be published (notebook, README, report source, result tables) for any
patient ID, name, maiden name or street address found in the raw patients.csv. Uses only Python's
standard library. Exits with status 1 if anything is found.

Usage (from the Week3_DataScience_Project folder):
    python validation/privacy_check.py
"""
import csv
import sys
from pathlib import Path

PROJECT_DIR = Path(__file__).resolve().parent.parent
PATIENTS = PROJECT_DIR / "Data" / "patients.csv"
SENSITIVE_COLUMNS = ["Id", "FIRST", "LAST", "MAIDEN", "ADDRESS"]
PUBLISHED = (["*.ipynb", "README.md", "Outputs/*.csv", "scripts/*.js"])


def main():
    with open(PATIENTS, encoding="utf-8-sig", newline="") as fh:
        rows = list(csv.DictReader(fh))
    sensitive = {r[c] for r in rows for c in SENSITIVE_COLUMNS if r[c]}

    found = 0
    for pattern in PUBLISHED:
        for path in sorted(PROJECT_DIR.glob(pattern)):
            text = path.read_text(encoding="utf-8")
            hits = sum(value in text for value in sensitive)
            found += hits
            # Counts only: the matching values themselves are never printed
            print(f"{'FAIL' if hits else 'OK  '}  {path.relative_to(PROJECT_DIR)}" + (f"  ({hits} matches)" if hits else ""))
    print(f"\n{len(sensitive):,} sensitive values checked; {found} found in published files")
    return 1 if found else 0


if __name__ == "__main__":
    sys.exit(main())
