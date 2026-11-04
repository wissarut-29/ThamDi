import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.agent.preprocess import build_pipeline_prompt

SCHEMA = "CREATE TABLE orders (order_id INTEGER PRIMARY KEY, order_date DATE NOT NULL);"
QUESTION = "มีคำสั่งซื้อกี่รายการในปี พ.ศ. 2568"


def test_m0_does_not_normalize_thai_dates():
    prompt = build_pipeline_prompt(QUESTION, SCHEMA, "M0")
    assert "พ.ศ. 2568" in prompt
    assert "ค.ศ. 2025" not in prompt


def test_m1_normalizes_thai_dates():
    prompt = build_pipeline_prompt(QUESTION, SCHEMA, "M1")
    assert "ค.ศ. 2025" in prompt
    assert "พ.ศ." not in prompt


def test_m3_also_normalizes_thai_dates():
    prompt = build_pipeline_prompt(QUESTION, SCHEMA, "M3")
    assert "ค.ศ. 2025" in prompt


def test_prompt_contains_schema_and_marker():
    prompt = build_pipeline_prompt(QUESTION, SCHEMA, "M0")
    assert SCHEMA in prompt
    assert "### SQL" in prompt
