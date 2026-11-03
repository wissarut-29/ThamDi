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
