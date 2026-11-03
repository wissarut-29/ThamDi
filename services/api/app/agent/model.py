"""โหลดโมเดลครั้งเดียว และให้ generate_sql() / model_info()

เจ้าของ: Suphakorn · งาน: S2 · สัญญาอินเทอร์เฟซ: docs/CONTRACT.md

MODEL_BACKEND=fake คืน SQL ตายตัวไว้เทสต์ (ไม่ import torch)
MODEL_BACKEND=local โหลดโมเดลที่ทีมเทรนเองจาก MODEL_PATH (ยังไม่ทำ: S2 ตัวจริง)
"""

import re

from ..config import get_settings

_REFUSE_WORDS = ("ลบ", "drop", "delete", "truncate")
_FIRST_TABLE = re.compile(r"CREATE\s+TABLE\s+(\w+)", re.IGNORECASE)
_QUESTION = re.compile(r"### คำถาม\n(.*?)\n\n### SQL", re.DOTALL)


def _backend() -> str:
    # อ่านทุกครั้งที่เรียก เทสต์จะได้สลับ backend ด้วย monkeypatch.setenv ได้
    # ค่าที่ไม่ใช่ fake/local -> pydantic ValidationError (เป็น ValueError)
    return get_settings().MODEL_BACKEND


def _fake_generate(prompt: str, n: int) -> list[str]:
    # ดูแค่ส่วนคำถาม ไม่ให้ชื่อคอลัมน์ใน schema ทำให้ปฏิเสธผิด
    match = _QUESTION.search(prompt)
    question = (match.group(1) if match else prompt).lower()
    if any(word in question for word in _REFUSE_WORDS):
        return ["<REFUSE>"] * n

    table = _FIRST_TABLE.search(prompt)
    sql = f"SELECT COUNT(*) AS n FROM {table.group(1)}" if table else "SELECT 1"
    return [sql] * n


def generate_sql(prompt: str, n: int = 1) -> list[str]:
    """คืนผลลัพธ์จากโมเดล n แบบ (beam) เรียงจากดีที่สุด แต่ละตัวเป็น SQL หรือ <REFUSE> / <CLARIFY>"""
    n = max(int(n), 1)
    backend = _backend()
    if backend == "fake":
        return _fake_generate(prompt, n)
    raise RuntimeError("MODEL_BACKEND=local ยังไม่พร้อม (S2 ตัวจริง)")


def model_info() -> dict:
    """คืน {"name", "base_model", "version", "backend", "loaded"} ให้ GET /api/model"""
    backend = _backend()
    if backend == "fake":
        return {
            "name": "thamdi-fake",
            "base_model": "-",
            "version": "fake",
            "backend": "fake",
            "loaded": True,
        }
    return {
        "name": "thamdi",
        "base_model": "",
        "version": "",
        "backend": backend,
        "loaded": False,
    }
