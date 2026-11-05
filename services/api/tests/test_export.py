import io

from conftest import login
from openpyxl import load_workbook

URL = "/api/export/xlsx"


def test_export_requires_token(api):
    assert api.post(URL, json={"columns": ["a"], "rows": [[1]]}).status_code == 401


def test_export_xlsx_keeps_numbers_and_thai(api):
    body = {
        "columns": ["branch", "total"],
        "rows": [["บางนา", 3068557], ["สยาม", 2512330.5]],
        "question": "ยอดขายแต่ละสาขา",
        "sql": "SELECT branch, SUM(amount) AS total FROM sales GROUP BY branch",
    }
    r = api.post(URL, headers=login(api), json=body)
    assert r.status_code == 200
    assert r.headers["content-type"].startswith("application/vnd.openxmlformats")
    wb = load_workbook(io.BytesIO(r.content))
    ws = wb["ผลลัพธ์"]
    assert [c.value for c in ws[1]] == ["branch", "total"]
    assert ws["A2"].value == "บางนา"
    assert ws["B2"].value == 3068557
    assert isinstance(ws["B3"].value, float)
    assert wb["ที่มา"]["B1"].value == "ยอดขายแต่ละสาขา"


def test_export_blocks_formula_injection(api):
    r = api.post(URL, headers=login(api), json={"columns": ["x"], "rows": [["=1+1"], ["-cmd"]]})
    ws = load_workbook(io.BytesIO(r.content))["ผลลัพธ์"]
    assert ws["A2"].value == "'=1+1"
    assert ws["A3"].value == "'-cmd"


def test_export_rejects_bad_shape(api):
    headers = login(api)
    assert api.post(URL, headers=headers, json={"columns": ["a", "b"], "rows": [[1]]}).status_code == 422
    assert api.post(URL, headers=headers, json={"columns": [], "rows": []}).status_code == 422
    too_many = {"columns": ["a"], "rows": [[i] for i in range(1001)]}
    assert api.post(URL, headers=headers, json=too_many).status_code == 422


BOOK = "/api/export/xlsx-book"


def test_export_book_one_sheet_per_question(api):
    sheets = [
        {
            "columns": ["total"],
            "rows": [[11566602]],
            "question": "ยอดขายรวมทั้งปี",
            "sql": "SELECT SUM(amount) FROM sales",
        },
        {"columns": ["category", "total"], "rows": [["เครื่องดื่ม", 1], ["อาหาร", 2]], "question": "แต่ละหมวด"},
        {"columns": ["x"], "rows": [["=HYPERLINK(1)"]]},
    ]
    r = api.post(BOOK, headers=login(api), json={"sheets": sheets})
    assert r.status_code == 200
    wb = load_workbook(io.BytesIO(r.content))
    assert wb.sheetnames == ["สารบัญ", "ข้อ 1", "ข้อ 2", "ข้อ 3"]
    assert wb["สารบัญ"]["B2"].value == "ยอดขายรวมทั้งปี"
    assert wb["สารบัญ"]["D3"].value == 2
    assert wb["ข้อ 1"]["A2"].value == 11566602
    assert wb["ข้อ 2"]["A3"].value == "อาหาร"
    assert wb["ข้อ 3"]["A2"].value == "'=HYPERLINK(1)"


def test_export_book_rejects_bad_input(api):
    headers = login(api)
    assert api.post(BOOK, json={"sheets": [{"columns": ["a"], "rows": []}]}).status_code == 401
    assert api.post(BOOK, headers=headers, json={"sheets": []}).status_code == 422
    bad = {"sheets": [{"columns": ["a"], "rows": [[1]]}, {"columns": ["a", "b"], "rows": [[1]]}]}
    assert api.post(BOOK, headers=headers, json=bad).status_code == 422
    too_many = {"sheets": [{"columns": ["a"], "rows": [[1]]}] * 31}
    assert api.post(BOOK, headers=headers, json=too_many).status_code == 422
