import io

import pandas as pd
import pytest

from app import ingest


def test_csv_utf8_and_thai_columns():
    content = "สาขา,ยอดขาย (บาท),\nA,1,\n".encode()
    tables = ingest.read_upload("ยอดขาย สาขา.csv", content)
    assert list(tables) == ["t_data"]  # ชื่อไฟล์ภาษาไทยล้วน → ชื่อสำรอง ASCII (data เป็น keyword)
    assert list(tables["t_data"].columns) == ["สาขา", "ยอดขาย_บาท"]  # คอลัมน์ว่างทั้งคอลัมน์ถูกตัด


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
    [
        ("x.pdf", b"%PDF-1.4"),
        ("x.docx", b"PK"),
        ("x.csv", b""),
        ("x.csv", b"a,b\n"),
        ("x.xlsx", b"not an excel file"),
    ],
)
def test_bad_files_rejected(filename, content):
    with pytest.raises(ingest.IngestError):
        ingest.read_upload(filename, content)


def test_too_large_rejected():
    with pytest.raises(ingest.IngestError):
        ingest.read_upload("x.csv", b"a\n" + b"1\n" * (ingest.MAX_BYTES // 2 + 1))


def test_excel_dates_without_time_become_date(tmp_path):
    import duckdb

    buf = io.BytesIO()
    frame = pd.DataFrame({"sale_date": pd.to_datetime(["2026-01-01", "2026-01-02"]), "amount": [1, 2]})
    frame.to_excel(buf, sheet_name="sales", index=False)
    tables = ingest.read_upload("s.xlsx", buf.getvalue())
    con = duckdb.connect()
    con.register("t", tables["sales"])
    assert con.execute("SELECT typeof(sale_date) FROM t LIMIT 1").fetchone()[0] == "DATE"


def test_dedupe_never_collides_with_existing_name():
    # รีวิว PR #9: "ยอด ขาย", "ยอด-ขาย", "ยอด_ขาย_2" เคยได้ ยอด_ขาย_2 ซ้ำสองคอลัมน์
    tables = ingest.read_upload("d.csv", "ยอด ขาย,ยอด-ขาย,ยอด_ขาย_2\n1,2,3\n".encode())
    columns = list(tables["d"].columns)
    assert len({c.lower() for c in columns}) == 3


def test_dedupe_sheet_names_do_not_overwrite():
    buf = io.BytesIO()
    with pd.ExcelWriter(buf) as writer:
        for i, sheet in enumerate(["sales", "sales_2", "Sales!"]):
            pd.DataFrame({"a": [i]}).to_excel(writer, sheet_name=sheet, index=False)
    tables = ingest.read_upload("x.xlsx", buf.getvalue())
    assert len(tables) == 3
    assert sorted(int(t["a"].iloc[0]) for t in tables.values()) == [0, 1, 2]


@pytest.mark.parametrize("filename", ["order.csv", "group.csv", "select.csv", "ข้อมูล.csv", "2025.csv"])
def test_table_names_are_never_quoted_in_ddl(filename):
    # รีวิว PR #9: ชื่อที่เป็น keyword ถูกใส่ "..." ใน DDL แล้ว pipeline หาชื่อตารางไม่เจอ
    import duckdb

    from app.agent.tools import table_names_from_ddl

    ((name, frame),) = ingest.read_upload(filename, b"a\n1\n").items()
    con = duckdb.connect()
    con.register("x", frame)
    con.execute(f'CREATE TABLE "{name}" AS SELECT * FROM x')
    ddl = con.execute("SELECT sql FROM duckdb_tables()").fetchone()[0]
    assert table_names_from_ddl(ddl) == {name}


# ---- นามสกุลที่เพิ่ม ----


@pytest.mark.parametrize("sep", [";", "\t", "|"])
def test_delimiter_guessed_from_header(sep):
    # CSV คั่นด้วย ; (เครื่องภาษายุโรป) ต้องได้ 2 คอลัมน์ ไม่ใช่คอลัมน์เดียว · ค่า 1,5 ในข้อมูลไม่ทำให้เดาผิด
    content = f"สาขา{sep}ยอด\nบางนา{sep}1,5\n".encode()
    assert list(ingest.read_upload("s.csv", content)["s"].columns) == ["สาขา", "ยอด"]


def test_tsv_and_txt():
    content = "สาขา\tยอด\nบางนา\t100\n".encode()
    assert list(ingest.read_upload("s.tsv", content)["s"].columns) == ["สาขา", "ยอด"]
    assert list(ingest.read_upload("s.txt", content)["s"].columns) == ["สาขา", "ยอด"]


def test_excel_unicode_text_utf16():
    # Excel > บันทึกเป็น > Unicode Text ได้ UTF-16 มี BOM คั่นด้วย tab
    content = "สาขา\tยอด\nบางนา\t100\n".encode("utf-16")
    frame = ingest.read_upload("s.txt", content)["s"]
    assert list(frame.columns) == ["สาขา", "ยอด"]
    assert frame.iloc[0, 0] == "บางนา"


def test_single_column_csv_still_works():
    assert list(ingest.read_upload("s.csv", b"a\n1\n2\n")["s"].columns) == ["a"]


def test_json_list_and_wrapped():
    rows = '[{"สาขา": "บางนา", "ยอด": 100, "ลูกค้า": {"ชื่อ": "ก"}}]'
    frame = ingest.read_upload("s.json", rows.encode())["s"]
    assert list(frame.columns) == ["สาขา", "ยอด", "ลูกค้า_ชื่อ"]
    wrapped = '{"data": ' + rows + "}"
    assert len(ingest.read_upload("s.json", wrapped.encode())["s"]) == 1


@pytest.mark.parametrize("content", [b'{"a": 1}', b"[1, 2]", b"not json"])
def test_json_not_a_table_rejected(content):
    with pytest.raises(ingest.IngestError):
        ingest.read_upload("s.json", content)


@pytest.mark.parametrize("suffix", [".ods", ".xls"])
def test_ods_and_xls(suffix):
    if suffix == ".xls":
        # pandas เขียน .xls ไม่ได้แล้ว ใช้ไฟล์ .xlsx ที่เปลี่ยนชื่อเป็น .xls แทน (เจอบ่อยในงานจริง)
        buf = io.BytesIO()
        pd.DataFrame({"a": [1]}).to_excel(buf, sheet_name="sales", index=False)
    else:
        pytest.importorskip("odf")
        buf = io.BytesIO()
        with pd.ExcelWriter(buf, engine="odf") as writer:
            pd.DataFrame({"a": [1]}).to_excel(writer, sheet_name="sales", index=False)
    assert list(ingest.read_upload("x" + suffix, buf.getvalue())) == ["sales"]
