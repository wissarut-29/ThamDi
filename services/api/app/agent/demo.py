"""DEMO_MODE: ตอบคำถามเดโมจาก eval/demo_answers.json เมื่อไม่มีโมเดล

เจ้าของ: Chalakorn · งาน: C5 · สัญญาอินเทอร์เฟซ: docs/CONTRACT.md
"""

import json
from pathlib import Path

ANSWERS_PATH = Path(__file__).resolve().parents[4] / "eval" / "demo_answers.json"


def lookup(question: str) -> dict | None:
    """หาคำตอบเดโมที่ตรงกับคำถามเป๊ะ (ตัด whitespace หัว-ท้ายก่อนเทียบ) คืน None ถ้าไม่เจอ

    routers/chat.py เรียกตอน DEMO_MODE=true หรือโมเดลโหลดไม่ขึ้น (ผ่าน getattr แบบ optional
    เผื่อไฟล์นี้ยังไม่มีฟังก์ชันนี้ จึงต้องคืน None อย่างปลอดภัย ไม่ raise เมื่อไม่เจอคำตอบ)
    """
    if not ANSWERS_PATH.exists():
        return None
    answers = json.loads(ANSWERS_PATH.read_text(encoding="utf-8"))
    return answers.get(question.strip())
