"""Cleaning and KPI functions for the Week 4 consumer complaint analysis.

The notebook and the unit tests both import from this module, so every
number in the report comes from one tested implementation.

Data interpretation rules (from the Week 4 brief):
- ``Date submitted`` is when the CFPB received the complaint.
- ``Date received`` is when the CFPB sent it to the company.
- The difference is the CFPB forwarding interval, NOT the company's
  response or resolution time.
- A blank ``Timely response?`` is not a "No": in this data it only occurs
  on complaints still marked "In progress".
"""

from __future__ import annotations

import hashlib
from pathlib import Path

import pandas as pd

RAW_COLUMNS = [
    "Complaint ID",
    "Submitted via",
    "Date submitted",
    "Date received",
    "State",
    "Product",
    "Sub-product",
    "Issue",
    "Sub-issue",
    "Company public response",
    "Company response to consumer",
    "Timely response?",
]

TEXT_COLUMNS = [
    "Submitted via",
    "State",
    "Product",
    "Sub-product",
    "Issue",
    "Sub-issue",
    "Company public response",
    "Company response to consumer",
    "Timely response?",
]

IN_PROGRESS = "In progress"

# Short product labels for charts. The full CFPB names stay in ``Product``.
PRODUCT_SHORT = {
    "Checking or savings account": "Checking/savings",
    "Credit card or prepaid card": "Credit/prepaid card",
    "Credit reporting, credit repair services, or other personal consumer reports": "Credit reporting",
    "Mortgage": "Mortgage",
    "Money transfer, virtual currency, or money service": "Money transfer",
    "Debt collection": "Debt collection",
    "Vehicle loan or lease": "Vehicle loan/lease",
    "Payday loan, title loan, or personal loan": "Payday/personal loan",
    "Student loan": "Student loan",
}

# Labels that replace blanks, chosen to say what the blank means.
LABEL_NO_SUB_PRODUCT = "Not specified"
LABEL_NO_SUB_ISSUE = "No sub-issue recorded"
LABEL_PUBLIC_PENDING = "Pending (complaint in progress)"
LABEL_PUBLIC_NOT_RECORDED = "Not recorded"
LABEL_TIMELY_PENDING = "Pending (in progress)"

# A forwarding interval above this many days is flagged as unusually long.
# 99% of complaints are forwarded within 25 days, so 30 days (about one
# month) is a round threshold just beyond that.
LONG_FORWARDING_DAYS = 30


def file_sha256(path: str | Path) -> str:
    """Return the SHA-256 hash of a file, used to show the raw file is unchanged."""
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest().upper()


def load_raw(path: str | Path) -> pd.DataFrame:
    """Read the ``Data`` worksheet and check it has exactly the expected columns."""
    df = pd.read_excel(path, sheet_name="Data")
    if list(df.columns) != RAW_COLUMNS:
        raise ValueError(f"Unexpected columns: {list(df.columns)}")
    return df


def content_duplicate_mask(df: pd.DataFrame) -> pd.Series:
    """True for every row that matches another row on all fields except Complaint ID."""
    cols = [c for c in df.columns if c in RAW_COLUMNS and c != "Complaint ID"]
    return df.duplicated(subset=cols, keep=False)


def clean(raw: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Return ``(clean_df, cleaning_log)``.

    The raw columns are kept unchanged. Every cleaned or derived value goes
    in a new snake_case column, so each transformation can be traced back to
    the original value. No rows are removed.
    """
    if not raw["Complaint ID"].is_unique:
        raise ValueError("Complaint ID is not unique")

    df = raw.copy()
    log: list[dict] = []

    def record(step, column, rule, rows, rationale):
        log.append(
            {
                "step": step,
                "column": column,
                "rule": rule,
                "rows_affected": int(rows),
                "rationale": rationale,
            }
        )

    # 1. Text standardisation: trim spaces (checked; expected to change nothing).
    changed = 0
    for col in TEXT_COLUMNS:
        before = df[col]
        after = before.where(before.isna(), before.astype("string").str.strip())
        changed += int((before.notna() & (before != after)).sum())
        df[col] = after
    record(1, "all text columns", "Trim leading and trailing spaces", changed,
           "Prevents the same category from being counted twice; no case or spacing variants were found")

    # 2. Dates and forwarding interval.
    df["date_submitted"] = pd.to_datetime(df["Date submitted"]).dt.normalize()
    df["date_received"] = pd.to_datetime(df["Date received"]).dt.normalize()
    df["forwarding_days"] = (df["date_received"] - df["date_submitted"]).dt.days
    negative = int((df["forwarding_days"] < 0).sum())
    if negative:
        raise ValueError(f"{negative} complaints were forwarded before they were submitted")
    record(2, "forwarding_days", "Date received minus Date submitted, in whole days", len(df),
           "CFPB forwarding interval; not the company's response time. No negative intervals found")

    df["same_day_forwarding"] = df["forwarding_days"] == 0
    df["long_forwarding"] = df["forwarding_days"] > LONG_FORWARDING_DAYS
    record(3, "long_forwarding", f"Flag intervals above {LONG_FORWARDING_DAYS} days",
           df["long_forwarding"].sum(),
           "Kept, not removed: long intervals are plausible and are analysed as a group")

    # 3. Calendar fields (all based on the date the CFPB received the complaint).
    df["year"] = df["date_submitted"].dt.year
    df["quarter"] = df["date_submitted"].dt.quarter
    df["month"] = df["date_submitted"].dt.month
    df["year_month"] = df["date_submitted"].dt.to_period("M").astype(str)
    df["year_quarter"] = df["date_submitted"].dt.to_period("Q").astype(str)
    first, last = df["year_month"].min(), df["year_month"].max()
    df["boundary_month"] = df["year_month"].isin([first, last])
    record(4, "year, quarter, month, year_month, year_quarter",
           "Derived from Date submitted", len(df),
           "Volume is dated by when the CFPB received the complaint")
    record(5, "boundary_month", f"Flag the first ({first}) and last ({last}) months",
           df["boundary_month"].sum(),
           "The brief treats them as partial; excluded from month-level tests only")

    # 4. Products.
    df["product_short"] = df["Product"].map(PRODUCT_SHORT)
    unmapped = int(df["product_short"].isna().sum())
    if unmapped:
        raise ValueError(f"{unmapped} rows have a product with no short label")
    record(6, "product_short", "Short chart label for each product", len(df),
           "Full CFPB product names are kept in Product")

    # 5. Blanks, labelled by their meaning.
    n = df["Sub-product"].isna().sum()
    df["sub_product"] = df["Sub-product"].fillna(LABEL_NO_SUB_PRODUCT)
    record(7, "sub_product", f"Blank -> '{LABEL_NO_SUB_PRODUCT}'", n,
           "The dictionary says not all products have sub-products")

    n = df["Sub-issue"].isna().sum()
    df["sub_issue"] = df["Sub-issue"].fillna(LABEL_NO_SUB_ISSUE)
    record(8, "sub_issue", f"Blank -> '{LABEL_NO_SUB_ISSUE}'", n,
           "The dictionary says not all issues have sub-issues; a blank is not missing data")

    in_progress = df["Company response to consumer"].eq(IN_PROGRESS)
    df["in_progress"] = in_progress
    blank_public = df["Company public response"].isna()
    df["public_response"] = df["Company public response"].astype("object")
    df.loc[blank_public & in_progress, "public_response"] = LABEL_PUBLIC_PENDING
    df.loc[blank_public & ~in_progress, "public_response"] = LABEL_PUBLIC_NOT_RECORDED
    record(9, "public_response", f"Blank and In progress -> '{LABEL_PUBLIC_PENDING}'",
           (blank_public & in_progress).sum(),
           "The company has not finished responding, so no public response is expected yet")
    record(10, "public_response", f"Blank and closed -> '{LABEL_PUBLIC_NOT_RECORDED}'",
           (blank_public & ~in_progress).sum(),
           "A public response is optional; a blank is not a refusal or a dispute")

    blank_timely = df["Timely response?"].isna()
    if not blank_timely.equals(in_progress):
        raise ValueError("Blank 'Timely response?' no longer matches 'In progress' exactly")
    df["timely_status"] = df["Timely response?"].astype("object").fillna(LABEL_TIMELY_PENDING)
    df["timely"] = df["Timely response?"].map({"Yes": True, "No": False}).astype("boolean")
    record(11, "timely_status / timely", f"Blank -> '{LABEL_TIMELY_PENDING}' / <NA>",
           blank_timely.sum(),
           "Every blank is an In-progress complaint; it must not be counted as 'No'")

    # 6. Duplicates.
    df["content_duplicate"] = content_duplicate_mask(raw)
    record(12, "content_duplicate", "Flag rows identical on every field except Complaint ID",
           df["content_duplicate"].sum(),
           "Kept: no consumer identifier exists, so identical categories on the same day are "
           "expected for different consumers")

    return df, pd.DataFrame(log)


# ---------------------------------------------------------------- KPIs


def timely_rate(df: pd.DataFrame) -> dict:
    """Share of complaints with a timely response, using only Yes/No records.

    Pending (In progress) records are excluded from the denominator and
    reported separately, as the brief requires.
    """
    yes = int((df["timely"] == True).sum())  # noqa: E712 (nullable boolean)
    no = int((df["timely"] == False).sum())  # noqa: E712
    excluded = int(df["timely"].isna().sum())
    denominator = yes + no
    return {
        "yes": yes,
        "no": no,
        "excluded_pending": excluded,
        "denominator": denominator,
        "timely_pct": 100 * yes / denominator if denominator else float("nan"),
    }


def forwarding_summary(df: pd.DataFrame) -> dict:
    """Average, median and tail of the CFPB forwarding interval in days."""
    days = df["forwarding_days"]
    return {
        "n": int(days.size),
        "mean_days": float(days.mean()),
        "median_days": float(days.median()),
        "p95_days": float(days.quantile(0.95)),
        "max_days": int(days.max()),
        "same_day_pct": 100 * float(df["same_day_forwarding"].mean()),
        "long_count": int(df["long_forwarding"].sum()),
    }


def monthly_counts(df: pd.DataFrame, full_months_only: bool = False) -> pd.Series:
    """Complaints per month, with every month in the range present (0 if none).

    With ``full_months_only=True`` the first and last (boundary) months are dropped.
    """
    counts = df.groupby("year_month").size()
    months = pd.period_range(counts.index.min(), counts.index.max(), freq="M").astype(str)
    counts = counts.reindex(months, fill_value=0)
    counts.index.name = "year_month"
    if full_months_only:
        counts = counts.iloc[1:-1]
    return counts.rename("complaints")


def share_table(df: pd.DataFrame, column: str) -> pd.DataFrame:
    """Count and percentage of complaints for each value of ``column``, largest first."""
    counts = df[column].value_counts()
    return pd.DataFrame(
        {"complaints": counts, "pct": (100 * counts / counts.sum()).round(2)}
    ).rename_axis(column)


def yoy_change(df: pd.DataFrame) -> pd.DataFrame:
    """Annual volume and year-over-year change.

    2017 (May to Dec) and 2023 (Jan to 28 Aug) are partial years, so their
    changes are flagged and a per-month average is given for a fair comparison.
    """
    annual = df.groupby("year").agg(
        complaints=("Complaint ID", "size"), months=("year_month", "nunique")
    )
    annual["complaints_per_month"] = (annual["complaints"] / annual["months"]).round(1)
    annual["yoy_change_pct"] = (100 * annual["complaints"].pct_change()).round(1)
    annual["yoy_change_per_month_pct"] = (
        100 * annual["complaints_per_month"].pct_change()
    ).round(1)
    annual["partial_year"] = annual["months"] < 12
    return annual
