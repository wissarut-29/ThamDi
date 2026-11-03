import io

import pandas as pd
import pytest

from app import ingest


def test_csv_utf8_and_thai_columns():
    content = "สาขา,ยอดขาย (บาท),\nA,1,\n".encode()
    tables = ingest.read_upload("ยอดขาย สาขา.csv", content)
    assert list(tables) == ["data"]  # ชื่อไฟล์ภาษาไทยล้วน → ชื่อสำรอง ASCII
    assert list(tables["data"].columns) == ["สาขา", "ยอดขาย_บาท"]  # คอลัมน์ว่างทั้งคอลัมน์ถูกตัด


def test_csv_cp874():
    tables = ingest.read_upload("sales.csv", "สาขา,ยอด\nก,1\n".encode("cp874"))
    assert list(tables["sales"].columns) == ["สาขา", "ยอด"]


def test_xlsx_one_table_per_sheet():
    buf = io.BytesIO()
    with pd.ExcelWriter(buf) as writer:
        pd.DataFrame({"a": [1]}).to_excel(writer, sheet_name="Branch 1", index=False)
        pd.DataFrame({"b": [2]}).to_excel(writer, sheet_name="2025", index=False)
        pd.DataFrame().to_excel(writer, sheet_name="empty", index=False)
    assert list(ingest.read_upload("x.xlsx", buf.getvalue())) == ["branch_1", "t_2025"]


def test_duplicate_and_blank_columns():
    tables = ingest.read_upload("d.csv", b"a,A,,x\n1,2,3,4\n")
    assert list(tables["d"].columns) == ["a", "A_2", "col_3", "x"]


@pytest.mark.parametrize(
    ("filename", "content"),
    [("x.txt", b"a\n1\n"), ("x.csv", b""), ("x.csv", b"a,b\n"), ("x.xlsx", b"not an excel file")],
)
def test_bad_files_rejected(filename, content):
    with pytest.raises(ingest.IngestError):
        ingest.read_upload(filename, content)


def test_too_large_rejected():
    with pytest.raises(ingest.IngestError):
        ingest.read_upload("x.csv", b"a\n" + b"1\n" * (ingest.MAX_BYTES // 2 + 1))
