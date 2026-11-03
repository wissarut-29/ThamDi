import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.agent import demo


def test_lookup_returns_none_when_question_not_found(tmp_path, monkeypatch):
    answers_file = tmp_path / "demo_answers.json"
    answers_file.write_text(json.dumps({"มีลูกค้ากี่คน": {"answer": "10 คน"}}), encoding="utf-8")
    monkeypatch.setattr(demo, "ANSWERS_PATH", answers_file)

    assert demo.lookup("คำถามที่ไม่มีในไฟล์") is None


def test_lookup_returns_matching_answer(tmp_path, monkeypatch):
    answers_file = tmp_path / "demo_answers.json"
    expected = {
        "answer": "มีลูกค้าทั้งหมด 10 คน",
        "status": "ok",
        "sql": "SELECT COUNT(*) FROM customers",
        "columns": ["n"],
        "rows": [[10]],
    }
    answers_file.write_text(
        json.dumps({"มีลูกค้ากี่คน": expected}, ensure_ascii=False), encoding="utf-8"
    )
    monkeypatch.setattr(demo, "ANSWERS_PATH", answers_file)

    assert demo.lookup("มีลูกค้ากี่คน") == expected


def test_lookup_strips_whitespace(tmp_path, monkeypatch):
    answers_file = tmp_path / "demo_answers.json"
    answers_file.write_text(json.dumps({"มีลูกค้ากี่คน": {"answer": "10"}}), encoding="utf-8")
    monkeypatch.setattr(demo, "ANSWERS_PATH", answers_file)

    assert demo.lookup("  มีลูกค้ากี่คน  ") == {"answer": "10"}


def test_lookup_returns_none_when_file_missing(tmp_path, monkeypatch):
    monkeypatch.setattr(demo, "ANSWERS_PATH", tmp_path / "does_not_exist.json")

    assert demo.lookup("อะไรก็ได้") is None
