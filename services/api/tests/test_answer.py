from datetime import date
from decimal import Decimal

from app.agent import answer
from app.agent.pipeline import PipelineResult


def ok(columns, rows):
    return PipelineResult(status="ok", sql="SELECT 1", columns=columns, rows=rows)


def test_single_value_formatted():
    assert answer.render("q", ok(["n"], [[1234567]])) == "คำตอบ: 1,234,567"
    assert answer.render("q", ok(["n"], [[Decimal("10.5")]])) == "คำตอบ: 10.50"


def test_single_row_many_columns():
    text = answer.render("q", ok(["branch", "day"], [["สาขา 1", date(2026, 11, 3)]]))
    assert text == "คำตอบ: branch = สาขา 1, day = 2026-11-03"


def test_many_rows_and_empty():
    assert answer.render("q", ok(["a"], [[1], [2], [3]])).startswith("พบ 3 รายการ")
    assert answer.render("q", ok(["a"], [])) == answer.EMPTY_TEXT
    assert "1,000 แถวแรก" in answer.render("q", ok(["a"], [[i] for i in range(1000)]))


def test_refuse_clarify_error_never_leak_details():
    assert answer.render("q", PipelineResult(status="refuse")) == answer.REFUSE_TEXT
    assert answer.render("q", PipelineResult(status="clarify")) == answer.CLARIFY_TEXT
    text = answer.render("q", PipelineResult(status="error", error="Catalog Error: table secret"))
    assert text == answer.ERROR_TEXT
    assert "secret" not in text
