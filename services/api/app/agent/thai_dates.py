"""แปลงวันที่ภาษาไทย/พ.ศ. ในคำถามเป็นช่วงวันที่

เจ้าของ: Chalakorn · งาน: C3 · สัญญาอินเทอร์เฟซ: docs/CONTRACT.md

แปลงปี พ.ศ. ให้เป็น ค.ศ. ตรง ๆ ในข้อความคำถาม เพื่อลดงานคำนวณของโมเดล
(preprocess.py เรียกใช้ใน M1 ขึ้นไป) รองรับทั้งที่เขียน "พ.ศ." ตรงตัว (เช่น "ปี พ.ศ. 2568")
และที่ไม่เขียน (เช่น "เดือนมีนาคม 2569") ซึ่งคนไทยเขียนแบบนี้เป็นปกติเมื่อปีอยู่ในช่วง พ.ศ.
ที่เป็นไปไม่ได้ว่าจะเป็น ค.ศ. (2400-2700 ครอบคลุม ค.ศ. 1857-2157)

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

# ช่วงปี พ.ศ. ที่เป็นไปได้จริง (กัน false positive กับเลข 4 หลักอื่นที่ไม่ใช่ปี)
_BE_YEAR_MIN, _BE_YEAR_MAX = 2400, 2700

# "พ.ศ. 2568" หรือ "พ.ศ.2568" หรือ "พศ 2568" (ต้องมี พ.ศ. ตรงตัว)
_BE_YEAR_PATTERN = re.compile(r"พ\.?ศ\.?\s*(\d{4})")
# เดือนไทย + ปี ในประโยคเดียวกัน เช่น "เดือนสิงหาคม ปี พ.ศ. 2568" หรือ "มีนาคม 2569"
# (พ.ศ. ไม่ต้องมีก็ได้ — ปีเขียนติดเดือนไทยแบบนี้แปลว่า พ.ศ. เสมอในภาษาไทย)
_MONTH_YEAR_PATTERN = re.compile(rf"({_MONTH_PATTERN})\s*(?:ปี\s*)?(?:พ\.?ศ\.?\s*)?(\d{{4}})")


def _is_plausible_be_year(year: int) -> bool:
    return _BE_YEAR_MIN <= year <= _BE_YEAR_MAX


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
        year = int(m.group(2))
        if not _is_plausible_be_year(year):
            continue
        month = _MONTH_INDEX[m.group(1)]
        ranges.append(month_range(be_to_ce(year), month))
        matched_spans.append(m.span())

    for m in _BE_YEAR_PATTERN.finditer(text):
        if any(start <= m.start() < end for start, end in matched_spans):
            continue  # ปีนี้ถูกจับไปแล้วเป็นส่วนหนึ่งของคู่เดือน+ปีด้านบน
        year_ce = be_to_ce(int(m.group(1)))
        ranges.append((f"{year_ce:04d}-01-01", f"{year_ce:04d}-12-31"))

    return ranges


def normalize_thai_dates(text: str) -> str:
    """แทนที่ปี พ.ศ. ในข้อความด้วยปี ค.ศ. ตรง ๆ (ชื่อเดือนไทยคงไว้ ไม่แปลงเป็นเลข
    เพราะโมเดลเรียนรู้แปลงชื่อเดือนไทยเป็นเลขเดือนในขั้นตอนเทรนแล้ว)

    รองรับทั้ง "พ.ศ. 2568" ตรงตัว และปีที่เขียนติดเดือนไทยแบบไม่มี พ.ศ. เช่น "มีนาคม 2569"
    """
    replacements: list[tuple[int, int, str]] = []

    for m in _MONTH_YEAR_PATTERN.finditer(text):
        year = int(m.group(2))
        if not _is_plausible_be_year(year):
            continue
        replacements.append((m.start(), m.end(), f"{m.group(1)} ค.ศ. {be_to_ce(year)}"))

    covered = [(s, e) for s, e, _ in replacements]
    for m in _BE_YEAR_PATTERN.finditer(text):
        if any(start <= m.start() < end for start, end in covered):
            continue  # ส่วนนี้ถูกแทนไปแล้วเป็นส่วนหนึ่งของคู่เดือน+ปีด้านบน
        replacements.append((m.start(), m.end(), f"ค.ศ. {be_to_ce(int(m.group(1)))}"))

    if not replacements:
        return text

    replacements.sort()
    out, pos = [], 0
    for start, end, repl in replacements:
        out.append(text[pos:start])
        out.append(repl)
        pos = end
    out.append(text[pos:])
    return "".join(out)
