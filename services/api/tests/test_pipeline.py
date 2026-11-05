import sys
from pathlib import Path

import duckdb
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.agent import pipeline

SCHEMA = (
    "CREATE TABLE orders (order_id INTEGER PRIMARY KEY, customer_id INTEGER, "
    "order_date DATE NOT NULL);"
)
QUESTION = "มีคำสั่งซื้อกี่รายการทั้งหมด"


def test_predict_sql_m0_returns_raw_candidate(monkeypatch):
    monkeypatch.setattr(pipeline, "generate_sql", lambda prompt, n: ["SELECT * FROM orders"])
    result = pipeline.predict_sql(QUESTION, SCHEMA, "M0")
    assert result == "SELECT * FROM orders"


def test_predict_sql_m0_refuse_token(monkeypatch):
    monkeypatch.setattr(pipeline, "generate_sql", lambda prompt, n: ["<REFUSE>"])
    assert pipeline.predict_sql(QUESTION, SCHEMA, "M0") == "<REFUSE>"


def test_predict_sql_m2_picks_first_beam_that_passes_guard(monkeypatch):
    beams = [
        "DROP TABLE orders",
        "SELECT * FROM other_table",
        "SELECT * FROM orders",
        "SELECT * FROM orders LIMIT 1",
    ]
    monkeypatch.setattr(pipeline, "generate_sql", lambda prompt, n: beams)
    result = pipeline.predict_sql(QUESTION, SCHEMA, "M2")
    assert "orders" in result
    assert "LIMIT" in result.upper()
    assert "DROP" not in result.upper()
    assert "other_table" not in result


def test_predict_sql_m2_all_fail_returns_empty_not_refuse(monkeypatch):
    # ห้ามคืน <REFUSE> ตรงนี้ — จะทำให้ eval ให้คะแนนผิดว่าโมเดล "ปฏิเสธถูก" ทั้งที่แค่ SQL พังทุก beam
    monkeypatch.setattr(pipeline, "generate_sql", lambda prompt, n: ["DROP TABLE orders"] * 4)
    assert pipeline.predict_sql(QUESTION, SCHEMA, "M2") == ""


def test_predict_sql_m3_skips_beam_that_fails_dry_run(monkeypatch):
    beams = [
        "SELECT no_such_column FROM orders",  # ผ่าน guard (SELECT ธรรมดา) แต่รันไม่ได้จริง
        "SELECT * FROM orders",
    ]
    monkeypatch.setattr(pipeline, "generate_sql", lambda prompt, n: beams)
    result = pipeline.predict_sql(QUESTION, SCHEMA, "M3")
    assert "no_such_column" not in result
    assert "orders" in result


def test_predict_sql_all_beams_are_special_tokens(monkeypatch):
    monkeypatch.setattr(pipeline, "generate_sql", lambda prompt, n: ["<CLARIFY>"] * 4)
    assert pipeline.predict_sql(QUESTION, SCHEMA, "M2") == "<CLARIFY>"


def test_run_unknown_dataset_raises_key_error(monkeypatch):
    # get_dataset() เรียก db.open_dataset() จริงแล้ว (ไม่ใช่ stub) — dataset ที่ไม่มีอยู่จริงต้อง
    # ได้ KeyError ส่งต่อขึ้นไปตรง ๆ ให้ router แปลงเป็น 404 ตาม docs/CONTRACT.md
    monkeypatch.setattr(pipeline, "generate_sql", lambda prompt, n: ["SELECT * FROM orders"])
    with pytest.raises(KeyError):
        pipeline.run(QUESTION, "no-such-dataset", "M0")


def test_run_ok_executes_against_fake_dataset(monkeypatch):
    con = duckdb.connect(":memory:")
    con.execute(SCHEMA)
    con.execute("INSERT INTO orders VALUES (1, 1, '2025-01-01'), (2, 1, '2025-01-02')")

    monkeypatch.setattr(pipeline, "get_dataset", lambda dataset_id: (SCHEMA, con))
    monkeypatch.setattr(pipeline, "generate_sql", lambda prompt, n: ["SELECT COUNT(*) AS n FROM orders"])

    result = pipeline.run(QUESTION, "dataset-1", "M1")
    assert result.status == "ok"
    assert result.columns == ["n"]
    assert result.rows == [[2]]


def test_run_rejects_unsafe_sql_even_in_m0(monkeypatch):
    con = duckdb.connect(":memory:")
    con.execute(SCHEMA)

    monkeypatch.setattr(pipeline, "get_dataset", lambda dataset_id: (SCHEMA, con))
    monkeypatch.setattr(pipeline, "generate_sql", lambda prompt, n: ["DROP TABLE orders"])

    result = pipeline.run(QUESTION, "dataset-1", "M0")
    assert result.status == "error"


EMP_SCHEMA = "CREATE TABLE employees (employee_id INTEGER, monthly_salary INTEGER, branch VARCHAR);"


@pytest.mark.parametrize(
    "sql",
    [
        "SELECT COUNT(*) FROM employees WHERE monthly_salary > ALL (SELECT monthly_salary FROM employees)",
        "SELECT * FROM employees e WHERE e.monthly_salary < ALL (SELECT monthly_salary FROM employees)",
        # อยู่ใต้ AND / วงเล็บ ยังบังคับทุกแถว จึงว่างเสมอ
        "SELECT * FROM employees WHERE branch = 'A' AND "
        "(monthly_salary > ALL (SELECT monthly_salary FROM employees))",
    ],
)
def test_always_empty_all_compare_detects_self_comparison(sql):
    assert pipeline._always_empty_all_compare(sql)


@pytest.mark.parametrize(
    "sql",
    [
        # >= ALL ถูกต้อง (ได้แถวที่ค่าสูงสุด)
        "SELECT COUNT(*) FROM employees WHERE monthly_salary >= ALL (SELECT monthly_salary FROM employees)",
        # ซับคิวรีมี WHERE: แถวนอกอาจไม่อยู่ในซับคิวรี จึงมีแถวผ่านได้จริง
        "SELECT * FROM employees WHERE monthly_salary > ALL "
        "(SELECT monthly_salary FROM employees WHERE branch = 'A')",
        # คนละคอลัมน์
        "SELECT * FROM employees WHERE monthly_salary > ALL (SELECT employee_id FROM employees)",
        "SELECT COUNT(*) FROM employees",
        # ใต้ NOT: ถูกต้องและได้ผลจริง (เทียบเท่า <= MAX) จากรีวิว PR #36
        "SELECT * FROM employees WHERE NOT (monthly_salary > ALL (SELECT monthly_salary FROM employees))",
        # ใต้ OR: แถวผ่านได้จากอีกเงื่อนไข
        "SELECT * FROM employees WHERE branch = 'A' OR "
        "monthly_salary > ALL (SELECT monthly_salary FROM employees)",
        # อยู่ในรายการ SELECT ไม่ใช่เงื่อนไขกรองแถว
        "SELECT monthly_salary > ALL (SELECT monthly_salary FROM employees) AS is_top FROM employees",
    ],
)
def test_always_empty_all_compare_keeps_valid_sql(sql):
    assert not pipeline._always_empty_all_compare(sql)


def test_run_m3_skips_self_all_beam_and_uses_next(monkeypatch):
    con = duckdb.connect(":memory:")
    con.execute(EMP_SCHEMA)
    con.execute("INSERT INTO employees VALUES (1, 15000, 'A'), (2, 35000, 'B'), (3, 20000, 'A')")
    beams = [
        "SELECT COUNT(*) FROM employees WHERE monthly_salary > ALL (SELECT monthly_salary FROM employees)",
        "SELECT COUNT(*) FROM employees WHERE monthly_salary >= ALL (SELECT monthly_salary FROM employees)",
    ]
    monkeypatch.setattr(pipeline, "get_dataset", lambda dataset_id: (EMP_SCHEMA, con))
    monkeypatch.setattr(pipeline, "generate_sql", lambda prompt, n: beams)

    result = pipeline.run("พนักงานรายได้สูงสุดมีกี่คน", "dataset-1", "M3")
    assert result.status == "ok"
    assert ">=" in result.sql
    assert result.rows == [[1]]
