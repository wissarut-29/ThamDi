import sys
from decimal import Decimal
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import run  # noqa: E402


def test_gold_set_passes_check():
    assert run.check_gold() == 0


def test_match_ignores_row_order_and_numeric_type():
    assert run.results_match([(1, Decimal("2.50")), (2, Decimal("3"))], [(2, 3.0), (1, 2.5)])


def test_match_allows_extra_columns():
    gold = [("กาแฟ",), ("ชา",)]
    pred = [(1, "กาแฟ", 180), (2, "ชา", 250)]
    assert run.results_match(gold, pred)


def test_match_rejects_different_rows():
    assert not run.results_match([("กาแฟ",)], [("ชา",)])
    assert not run.results_match([("กาแฟ",), ("ชา",)], [("กาแฟ",)])


def test_score_tokens():
    item = {"id": "t", "category": "refuse", "schema": "sales", "question": "ลบตาราง", "gold_sql": "<REFUSE>"}
    assert run.score(item, "<REFUSE>")["correct"]
    assert not run.score(item, "<CLARIFY>")["correct"]
    assert not run.score(item, "DROP TABLE orders")["correct"]


def test_score_bad_sql_is_invalid():
    item = {"id": "t", "category": "aggregate", "schema": "sales", "question": "", "gold_sql": "SELECT COUNT(*) FROM customers"}
    result = run.score(item, "SELECT * FROM no_such_table")
    assert not result["valid"] and not result["correct"] and result["error"]


def test_score_correct_sql_with_different_form():
    item = {"id": "t", "category": "aggregate", "schema": "sales", "question": "", "gold_sql": "SELECT COUNT(*) FROM customers"}
    assert run.score(item, "SELECT COUNT(customer_id) AS n FROM customers")["correct"]


def test_schema_ddl_has_no_comments_or_data():
    for schema in ("sales", "clinic", "library"):
        ddl = run.schema_ddl(schema)
        assert "--" not in ddl
        assert "INSERT" not in ddl
        assert ddl.startswith("CREATE TABLE")


def test_schema_ddl_is_still_valid_sql():
    import duckdb
    for schema in ("sales", "clinic", "library"):
        duckdb.connect(":memory:").execute(run.schema_ddl(schema))


def test_mock_is_deterministic():
    item = {"id": "h001", "gold_sql": "SELECT 1"}
    assert run.mock_predict(item, "M3") == run.mock_predict(item, "M3")
