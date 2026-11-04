import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.agent.thai_dates import (
    be_to_ce,
    extract_date_ranges,
    normalize_thai_dates,
)


def test_be_to_ce():
    assert be_to_ce(2568) == 2025


def test_normalize_replaces_be_year():
    text = "มีคำสั่งซื้อกี่รายการในเดือนสิงหาคม ปี พ.ศ. 2568"
    result = normalize_thai_dates(text)
    assert "ค.ศ. 2025" in result
    assert "พ.ศ." not in result
    assert "เดือนสิงหาคม" in result  # ชื่อเดือนไทยคงไว้ ไม่แปลง


def test_normalize_leaves_relative_phrases_unchanged():
    text = "มีคำสั่งซื้อกี่รายการเดือนที่แล้ว"
    assert normalize_thai_dates(text) == text


def test_normalize_no_date_unchanged():
    text = "มีลูกค้ากี่คนในจังหวัดเชียงใหม่"
    assert normalize_thai_dates(text) == text


def test_extract_date_ranges_month_and_year():
    text = "ในเดือนสิงหาคม ปี พ.ศ. 2568"
    ranges = extract_date_ranges(text)
    assert ranges == [("2025-08-01", "2025-08-31")]


def test_extract_date_ranges_year_only():
    text = "ในปี พ.ศ. 2568"
    ranges = extract_date_ranges(text)
    assert ranges == [("2025-01-01", "2025-12-31")]


def test_normalize_replaces_bare_year_without_be_marker():
    text = "เดือนมีนาคม 2569 สาขาบางนา"
    result = normalize_thai_dates(text)
    assert "ค.ศ. 2026" in result
    assert "เดือนมีนาคม" in result
    assert "2569" not in result


def test_normalize_leaves_implausible_bare_year_unchanged():
    text = "ยอดขายเดือนมีนาคม 2026"
    assert normalize_thai_dates(text) == text


def test_extract_date_ranges_month_and_bare_year():
    text = "ในเดือนมีนาคม 2569"
    ranges = extract_date_ranges(text)
    assert ranges == [("2026-03-01", "2026-03-31")]


def test_normalize_replaces_bare_year_no_month():
    text = "ยอดขายปี 2568"
    result = normalize_thai_dates(text)
    assert "ปี ค.ศ. 2025" in result
    assert "2568" not in result


def test_normalize_does_not_overmatch_extra_digit():
    text = "มีนาคม 25690"
    assert normalize_thai_dates(text) == text


def test_extract_date_ranges_bare_year_no_month():
    text = "ปี 2568 เก็บค่ารักษาได้รวมเท่าไร"
    ranges = extract_date_ranges(text)
    assert ranges == [("2025-01-01", "2025-12-31")]
