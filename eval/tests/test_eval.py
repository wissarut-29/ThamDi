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


def _use_val(tmp_path, monkeypatch, val_items, val_schema="val_shop"):
    """ชี้ SETS_DIR/SCHEMAS_DIR ไปที่โฟลเดอร์ชั่วคราว ที่มี handwritten + schema เดิม และ val ที่ส่งเข้ามา"""
    import json
    import shutil
    sets, schemas = tmp_path / "sets", tmp_path / "schemas"
    shutil.copytree(run.SETS_DIR, sets)
    shutil.copytree(run.SCHEMAS_DIR, schemas)
    (schemas / f"{val_schema}.sql").write_text(
        "CREATE TABLE items (item_id INTEGER, name VARCHAR);\n-- data\nINSERT INTO items VALUES (1, 'ปากกา');\n",
        encoding="utf-8",
    )
    (sets / "val.jsonl").write_text(
        "".join(json.dumps(item, ensure_ascii=False) + "\n" for item in val_items), encoding="utf-8"
    )
    monkeypatch.setattr(run, "SETS_DIR", sets)
    monkeypatch.setattr(run, "SCHEMAS_DIR", schemas)


def _val_item(**kw):
    item = {"id": "v001", "category": "filter", "schema": "val_shop", "unseen": True,
            "question": "สินค้ามีอะไรบ้าง", "gold_sql": "SELECT name FROM items"}
    return {**item, **kw}


def test_check_gold_accepts_valid_val(tmp_path, monkeypatch):
    _use_val(tmp_path, monkeypatch, [_val_item(), _val_item(id="v002", category="refuse", gold_sql="<REFUSE>")])
    assert run.check_gold() == 0
    assert "val" in run.load_sets()


def test_check_gold_rejects_bad_val(tmp_path, monkeypatch):
    handwritten_q = run.load_jsonl(run.SETS_DIR / "handwritten.jsonl")[0]["question"]
    _use_val(tmp_path, monkeypatch, [_val_item(), _val_item(id="v002", question=handwritten_q)])
    assert run.check_gold() == 1


def test_check_val_rules():
    hw = [{"id": "h001", "question": "ลูกค้ามีกี่คน"}]
    # refuse ไม่ต้องรัน SQL จึงเหลือแค่ปัญหาเรื่องชื่อ schema
    assert run.check_val([_val_item(schema="sales", category="refuse", gold_sql="<REFUSE>")], hw) == [
        "schema sales ต้องขึ้นต้นด้วย val_",
    ]
    problems = run.check_val([_val_item(id="h001", question="ลูกค้ามีกี่คน", schema="val_missing")], hw)
    assert problems == [
        "h001: ไม่มี schema val_missing",
        "h001: id ซ้ำกับ handwritten",
        "h001: คำถามซ้ำกับ handwritten",
    ]


def test_mock_is_deterministic():
    item = {"id": "h001", "gold_sql": "SELECT 1"}
    assert run.mock_predict(item, "M3") == run.mock_predict(item, "M3")
