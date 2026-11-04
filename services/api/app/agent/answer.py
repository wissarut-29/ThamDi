"""สร้างคำตอบภาษาไทยจากผลลัพธ์ด้วยแม่แบบ (ไม่ใช้โมเดลภาษา)

เจ้าของ: Suphakorn · งาน: S3 · สัญญาอินเทอร์เฟซ: docs/CONTRACT.md

คำตอบมาจากแม่แบบ + ค่าที่ได้จากการรัน SQL จริงเท่านั้น ระบบจึงไม่แต่งตัวเลขขึ้นเอง
"""

from datetime import date, datetime
from decimal import Decimal

from .pipeline import PipelineResult

ROW_LIMIT = 1000  # ตรงกับ LIMIT ที่ sql_guard เติมให้

REFUSE_TEXT = "ขออภัย คำถามนี้ตอบจากข้อมูลในไฟล์นี้ไม่ได้ หรือเป็นคำสั่งที่ระบบไม่อนุญาต (ระบบอ่านข้อมูลได้อย่างเดียว)"
CLARIFY_TEXT = "คำถามยังไม่ชัดเจน ช่วยระบุเพิ่มอีกนิด เช่น ช่วงเวลา สาขา หรือชื่อคอลัมน์ที่ต้องการ"
ERROR_TEXT = "ขออภัย ระบบหาคำตอบของคำถามนี้ไม่ได้ ลองถามใหม่ด้วยคำอื่น หรือถามให้สั้นลง"
EMPTY_TEXT = "ไม่พบข้อมูลที่ตรงกับคำถาม"


def format_value(value) -> str:
    """แสดงค่าแบบที่คนอ่านง่าย: ตัวเลขมีคอมมา, ทศนิยมไม่เกิน 2 ตำแหน่ง, ไม่มีค่า = '-'"""
    if value is None:
        return "-"
    if isinstance(value, bool):
        return "ใช่" if value else "ไม่ใช่"
    if isinstance(value, int):
        return f"{value:,}"
    if isinstance(value, (float, Decimal)):
        number = float(value)
        return f"{number:,.0f}" if number.is_integer() else f"{number:,.2f}"
    if isinstance(value, (date, datetime)):
        return value.isoformat(sep=" ") if isinstance(value, datetime) else value.isoformat()
    return str(value)


def render(question: str, result: PipelineResult) -> str:
    """สร้างข้อความตอบภาษาไทยจาก PipelineResult"""
    if result.status == "refuse":
        return REFUSE_TEXT
    if result.status == "clarify":
        return CLARIFY_TEXT
    if result.status != "ok":
        # ไม่ส่งข้อความ error ดิบให้ผู้ใช้ (อาจมีชื่อตาราง/รายละเอียดภายใน)
        return ERROR_TEXT

    rows, columns = result.rows, result.columns
    if not rows:
        return EMPTY_TEXT

    if len(rows) == 1 and len(columns) == 1:
        # SUM/AVG ของช่วงที่ไม่มีข้อมูลได้ NULL แถวเดียว → บอกว่าไม่พบ ดีกว่าขึ้น "คำตอบ: -"
        if rows[0][0] is None:
            return EMPTY_TEXT
        return f"คำตอบ: {format_value(rows[0][0])}"

    if len(rows) == 1:
        parts = [f"{col} = {format_value(val)}" for col, val in zip(columns, rows[0], strict=False)]
        return "คำตอบ: " + ", ".join(parts)

    if len(rows) >= ROW_LIMIT:
        # ได้ครบ LIMIT พอดี บอกไม่ได้ว่าถูกตัดหรือมีพอดี จึงบอกตามจริงว่าอาจมีมากกว่านี้
        return f"พบอย่างน้อย {ROW_LIMIT:,} รายการ (แสดงได้สูงสุด {ROW_LIMIT:,} แถว อาจมีมากกว่านี้)"
    return f"พบ {len(rows):,} รายการ (ดูในตารางด้านล่าง)"
