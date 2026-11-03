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


def test_predict_sql_m2_all_fail_falls_back_to_refuse(monkeypatch):
    monkeypatch.setattr(pipeline, "generate_sql", lambda prompt, n: ["DROP TABLE orders"] * 4)
    assert pipeline.predict_sql(QUESTION, SCHEMA, "M2") == "<REFUSE>"


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


def test_run_without_dataset_stub_raises_not_implemented(monkeypatch):
    monkeypatch.setattr(pipeline, "generate_sql", lambda prompt, n: ["SELECT * FROM orders"])
    with pytest.raises(NotImplementedError):
        pipeline.run(QUESTION, "dataset-1", "M0")


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
