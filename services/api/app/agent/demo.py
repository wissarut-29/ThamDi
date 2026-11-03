"""DEMO_MODE: ตอบคำถามเดโมจาก eval/demo_answers.json เมื่อไม่มีโมเดล

เจ้าของ: Chalakorn · งาน: C5 · สัญญาอินเทอร์เฟซ: docs/CONTRACT.md
"""

import json
import logging
from pathlib import Path

log = logging.getLogger(__name__)

ANSWERS_PATH = Path(__file__).resolve().parents[4] / "eval" / "demo_answers.json"


def lookup(question: str) -> dict | None:
    """หาคำตอบเดโมที่ตรงกับคำถามเป๊ะ (ตัด whitespace หัว-ท้ายก่อนเทียบ) คืน None ถ้าไม่เจอ

    routers/chat.py เรียกตอน DEMO_MODE=true หรือโมเดลโหลดไม่ขึ้น (ผ่าน getattr แบบ optional
    เผื่อไฟล์นี้ยังไม่มีฟังก์ชันนี้ จึงต้องคืน None อย่างปลอดภัย ไม่ raise เมื่อไม่เจอคำตอบ)

    ดัก JSON พังด้วย (ไฟล์มีคอมมาเกิน/เซฟแบบมี BOM ฯลฯ) แล้วคืน None เหมือนไม่เจอคำตอบ — เพราะ
    path นี้คือทางสำรองที่ใช้ตอนโมเดลพังพอดี ถ้า raise ออกไปจะกลายเป็น 500 ซ้ำเติมตอนที่ระบบ
    ควรจะยัง "ตอบได้บางส่วน" อยู่ (พบจากรีวิวของ Wissarut บน PR #12)
    """
    if not ANSWERS_PATH.exists():
        return None
    try:
        answers = json.loads(ANSWERS_PATH.read_text(encoding="utf-8"))
    except ValueError:
        log.exception("eval/demo_answers.json อ่านไม่ขึ้น (JSON พัง)")
        return None
    return answers.get(question.strip())
