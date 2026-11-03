"""แปลงวันที่ภาษาไทย/พ.ศ. ในคำถามเป็นช่วงวันที่

เจ้าของ: Chalakorn · งาน: C3 · สัญญาอินเทอร์เฟซ: docs/CONTRACT.md

แปลงเฉพาะปี พ.ศ. ที่ระบุตรงตัว (เช่น "ปี พ.ศ. 2568") ให้เป็น ค.ศ. ตรง ๆ ในข้อความคำถาม
เพื่อลดงานคำนวณของโมเดล (preprocess.py เรียกใช้ใน M1 ขึ้นไป)

ไม่แก้ไขวันที่สัมพัทธ์ ("เดือนที่แล้ว", "ปีนี้", "N วันที่ผ่านมา") เพราะ SQL ที่ถูกต้อง
ต้องใช้ CURRENT_DATE คำนวณตอนรันจริง ถ้าแปลงเป็นวันที่ตายตัวตอนสร้าง prompt ค่าจะผิด
ทันทีที่เวลาผ่านไปจากตอนที่ถาม — โมเดลเรียนรู้ให้จัดการกรณีนี้เองตั้งแต่ตอนเทรนแล้ว
"""

import calendar
import re

THAI_MONTHS = [
    "มกราคม", "กุมภาพันธ์", "มีนาคม", "เมษายน", "พฤษภาคม", "มิถุนายน",
    "กรกฎาคม", "สิงหาคม", "กันยายน", "ตุลาคม", "พฤศจิกายน", "ธันวาคม",
]
_MONTH_INDEX = {name: i + 1 for i, name in enumerate(THAI_MONTHS)}
_MONTH_PATTERN = "|".join(THAI_MONTHS)

# "พ.ศ. 2568" หรือ "พ.ศ.2568" หรือ "พศ 2568"
_BE_YEAR_PATTERN = re.compile(r"พ\.?ศ\.?\s*(\d{4})")
# เดือนไทย + ปี พ.ศ. ในประโยคเดียวกัน เช่น "เดือนสิงหาคม ปี พ.ศ. 2568"
_MONTH_YEAR_PATTERN = re.compile(rf"({_MONTH_PATTERN})\s*(?:ปี\s*)?พ\.?ศ\.?\s*(\d{{4}})")


def be_to_ce(be_year: int) -> int:
    """แปลงปี พ.ศ. เป็น ค.ศ."""
    return be_year - 543


def month_range(year_ce: int, month: int) -> tuple[str, str]:
    """คืนวันแรกและวันสุดท้ายของเดือน (ISO date string) ของปี ค.ศ. ที่ให้"""
    last_day = calendar.monthrange(year_ce, month)[1]
    return f"{year_ce:04d}-{month:02d}-01", f"{year_ce:04d}-{month:02d}-{last_day:02d}"


def extract_date_ranges(text: str) -> list[tuple[str, str]]:
    """หาวันที่แบบตรงตัว (พ.ศ. อย่างเดียว หรือ เดือนไทย+พ.ศ.) ในข้อความ คืนเป็นช่วงวันที่ (start, end)

    ไม่รองรับวันที่สัมพัทธ์ (ดูเหตุผลใน docstring ของไฟล์)
    """
    ranges = []
    matched_spans = []

    for m in _MONTH_YEAR_PATTERN.finditer(text):
        month = _MONTH_INDEX[m.group(1)]
        year_ce = be_to_ce(int(m.group(2)))
        ranges.append(month_range(year_ce, month))
        matched_spans.append(m.span())

    for m in _BE_YEAR_PATTERN.finditer(text):
        if any(start <= m.start() < end for start, end in matched_spans):
            continue  # ปีนี้ถูกจับไปแล้วเป็นส่วนหนึ่งของคู่เดือน+ปีด้านบน
        year_ce = be_to_ce(int(m.group(1)))
        ranges.append((f"{year_ce:04d}-01-01", f"{year_ce:04d}-12-31"))

    return ranges


def normalize_thai_dates(text: str) -> str:
    """แทนที่ปี พ.ศ. ในข้อความด้วยปี ค.ศ. ตรง ๆ (ชื่อเดือนไทยคงไว้ ไม่แปลงเป็นเลข
    เพราะโมเดลเรียนรู้แปลงชื่อเดือนไทยเป็นเลขเดือนในขั้นตอนเทรนแล้ว)"""

    def _replace(m: re.Match) -> str:
        year_ce = be_to_ce(int(m.group(1)))
        return f"ค.ศ. {year_ce}"

    return _BE_YEAR_PATTERN.sub(_replace, text)
