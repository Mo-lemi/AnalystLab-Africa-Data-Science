"""Unit tests for complaint_prep. Run from Week4_DataScience_Project: python -m pytest"""

import sys
from pathlib import Path

import pandas as pd
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import complaint_prep as cp  # noqa: E402

PUBLIC_NONE = "Company has responded to the consumer and the CFPB and chooses not to provide a public response"


def make_raw(rows):
    """Build a raw-format frame from a list of partial row dicts."""
    base = {
        "Submitted via": "Web",
        "Date submitted": "2020-01-10",
        "Date received": "2020-01-10",
        "State": "CA",
        "Product": "Mortgage",
        "Sub-product": "Conventional home mortgage",
        "Issue": "Trouble during payment process",
        "Sub-issue": None,
        "Company public response": PUBLIC_NONE,
        "Company response to consumer": "Closed with explanation",
        "Timely response?": "Yes",
    }
    records = [{"Complaint ID": i + 1, **base, **row} for i, row in enumerate(rows)]
    df = pd.DataFrame(records)[cp.RAW_COLUMNS]
    df["Date submitted"] = pd.to_datetime(df["Date submitted"])
    df["Date received"] = pd.to_datetime(df["Date received"])
    return df


def test_clean_keeps_every_row_and_raw_columns():
    raw = make_raw([{}, {"Product": "Student loan"}, {}])
    clean, log = cp.clean(raw)
    assert len(clean) == len(raw)
    pd.testing.assert_frame_equal(clean[cp.RAW_COLUMNS].astype(str), raw.astype(str))
    assert not log.empty and {"step", "column", "rule", "rows_affected", "rationale"} <= set(log.columns)


def test_clean_does_not_modify_input():
    raw = make_raw([{"State": " NY "}])
    snapshot = raw.copy()
    cp.clean(raw)
    pd.testing.assert_frame_equal(raw, snapshot)


def test_forwarding_interval_and_flags():
    raw = make_raw([
        {"Date submitted": "2020-01-01", "Date received": "2020-01-01"},
        {"Date submitted": "2020-01-01", "Date received": "2020-01-31"},  # 30 days: not long
        {"Date submitted": "2020-01-01", "Date received": "2020-02-01"},  # 31 days: long
    ])
    clean, _ = cp.clean(raw)
    assert clean["forwarding_days"].tolist() == [0, 30, 31]
    assert clean["same_day_forwarding"].tolist() == [True, False, False]
    assert clean["long_forwarding"].tolist() == [False, False, True]


def test_negative_forwarding_interval_is_rejected():
    raw = make_raw([{"Date submitted": "2020-01-05", "Date received": "2020-01-04"}])
    with pytest.raises(ValueError, match="forwarded before"):
        cp.clean(raw)


def test_duplicate_complaint_id_is_rejected():
    raw = make_raw([{}, {}])
    raw.loc[1, "Complaint ID"] = 1
    with pytest.raises(ValueError, match="not unique"):
        cp.clean(raw)


def test_blank_timely_is_pending_not_no():
    raw = make_raw([
        {"Timely response?": "Yes"},
        {"Timely response?": "No"},
        {"Timely response?": None, "Company response to consumer": "In progress",
         "Company public response": None},
    ])
    clean, _ = cp.clean(raw)
    assert clean["timely_status"].tolist() == ["Yes", "No", cp.LABEL_TIMELY_PENDING]
    assert clean["timely"].isna().tolist() == [False, False, True]
    assert clean["in_progress"].tolist() == [False, False, True]


def test_blank_timely_on_closed_complaint_is_rejected():
    raw = make_raw([{"Timely response?": None}])
    with pytest.raises(ValueError, match="no longer matches"):
        cp.clean(raw)


def test_public_response_blanks_are_labelled_by_meaning():
    raw = make_raw([
        {"Company public response": None, "Company response to consumer": "In progress",
         "Timely response?": None},
        {"Company public response": None},
        {},
    ])
    clean, _ = cp.clean(raw)
    assert clean["public_response"].tolist() == [
        cp.LABEL_PUBLIC_PENDING, cp.LABEL_PUBLIC_NOT_RECORDED, PUBLIC_NONE]


def test_sub_field_blanks_are_labelled():
    raw = make_raw([{"Sub-product": None, "Sub-issue": None}, {"Sub-issue": "Late fee"}])
    clean, _ = cp.clean(raw)
    assert clean["sub_product"].tolist() == [cp.LABEL_NO_SUB_PRODUCT, "Conventional home mortgage"]
    assert clean["sub_issue"].tolist() == [cp.LABEL_NO_SUB_ISSUE, "Late fee"]


def test_whitespace_is_trimmed():
    raw = make_raw([{"State": " NY "}, {"State": "NY"}])
    clean, log = cp.clean(raw)
    assert clean["State"].tolist() == ["NY", "NY"]
    assert log.loc[log["step"] == 1, "rows_affected"].item() == 1


def test_unknown_product_is_rejected():
    raw = make_raw([{"Product": "Crypto staking"}])
    with pytest.raises(ValueError, match="short label"):
        cp.clean(raw)


def test_content_duplicates_flag_ignores_complaint_id():
    raw = make_raw([{}, {}, {"State": "TX"}])
    assert cp.content_duplicate_mask(raw).tolist() == [True, True, False]


def test_calendar_fields_and_boundary_months():
    raw = make_raw([
        {"Date submitted": "2020-01-31", "Date received": "2020-01-31"},
        {"Date submitted": "2020-02-15", "Date received": "2020-02-15"},
        {"Date submitted": "2020-04-01", "Date received": "2020-04-01"},
    ])
    clean, _ = cp.clean(raw)
    assert clean["year_month"].tolist() == ["2020-01", "2020-02", "2020-04"]
    assert clean["quarter"].tolist() == [1, 1, 2]
    assert clean["year_quarter"].tolist() == ["2020Q1", "2020Q1", "2020Q2"]
    assert clean["boundary_month"].tolist() == [True, False, True]


def test_timely_rate_excludes_pending_from_denominator():
    raw = make_raw([
        {"Timely response?": "Yes"}, {"Timely response?": "Yes"}, {"Timely response?": "Yes"},
        {"Timely response?": "No"},
        {"Timely response?": None, "Company response to consumer": "In progress",
         "Company public response": None},
    ])
    clean, _ = cp.clean(raw)
    result = cp.timely_rate(clean)
    assert result == {"yes": 3, "no": 1, "excluded_pending": 1, "denominator": 4, "timely_pct": 75.0}


def test_monthly_counts_fills_gaps_with_zero_and_drops_boundaries():
    raw = make_raw([
        {"Date submitted": "2020-01-05", "Date received": "2020-01-05"},
        {"Date submitted": "2020-03-05", "Date received": "2020-03-05"},
        {"Date submitted": "2020-03-06", "Date received": "2020-03-06"},
        {"Date submitted": "2020-04-05", "Date received": "2020-04-05"},
    ])
    clean, _ = cp.clean(raw)
    assert cp.monthly_counts(clean).to_dict() == {"2020-01": 1, "2020-02": 0, "2020-03": 2, "2020-04": 1}
    assert cp.monthly_counts(clean, full_months_only=True).to_dict() == {"2020-02": 0, "2020-03": 2}


def test_forwarding_summary():
    raw = make_raw([
        {"Date submitted": "2020-01-01", "Date received": "2020-01-01"},
        {"Date submitted": "2020-01-01", "Date received": "2020-01-03"},
        {"Date submitted": "2020-01-01", "Date received": "2020-03-01"},  # 60 days
    ])
    clean, _ = cp.clean(raw)
    s = cp.forwarding_summary(clean)
    assert s["mean_days"] == pytest.approx(62 / 3)
    assert s["median_days"] == 2
    assert s["max_days"] == 60
    assert s["same_day_pct"] == pytest.approx(100 / 3)
    assert s["long_count"] == 1


def test_share_table_percentages_sum_to_100():
    raw = make_raw([{}, {}, {"Product": "Student loan"}])
    clean, _ = cp.clean(raw)
    table = cp.share_table(clean, "Product")
    assert table["complaints"].tolist() == [2, 1]
    assert table["pct"].sum() == pytest.approx(100, abs=0.02)


def test_yoy_change_flags_partial_years():
    rows = [{"Date submitted": f"2020-{m:02d}-01", "Date received": f"2020-{m:02d}-01"} for m in range(1, 13)]
    rows += [{"Date submitted": "2021-01-01", "Date received": "2021-01-01"}] * 3
    clean, _ = cp.clean(make_raw(rows))
    yoy = cp.yoy_change(clean)
    assert yoy.loc[2020, "partial_year"] == False  # noqa: E712
    assert yoy.loc[2021, "partial_year"] == True  # noqa: E712
    assert yoy.loc[2021, "complaints_per_month"] == 3.0
    assert yoy.loc[2021, "yoy_change_per_month_pct"] == 200.0
