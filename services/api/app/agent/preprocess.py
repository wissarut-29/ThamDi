"""เตรียมคำถามและ schema ให้อยู่ในรูปแบบ prompt เดียวกับตอนเทรน

เจ้าของ: Chalakorn · งาน: C3 · สัญญาอินเทอร์เฟซ: docs/CONTRACT.md

build_prompt มาจาก ml/format.py ไฟล์เดียว ให้ตอนเทรนและตอน preprocess ใช้ร่วมกัน
(กันรูปแบบ prompt ไม่ตรงกันระหว่างเทรนกับตอนเรียกโมเดลจริง) ต้อง import ข้ามแพ็กเกจ
จาก services/api ไปที่ ml/ เพราะอยู่ repo เดียวกันแต่ deploy คนละส่วน
"""

import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[4]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from ml.format import build_prompt

from .thai_dates import normalize_thai_dates


def build_pipeline_prompt(question: str, schema_ddl: str, mode: str) -> str:
    """สร้าง prompt สำหรับโหมด M0-M3 (ความหมายของแต่ละโหมด: docs/CONTRACT.md)

    M0 ใช้คำถามดิบ ไม่ผ่าน preprocess ใด ๆ
    M1 ขึ้นไป แปลงวันที่ไทย/พ.ศ. ในคำถามก่อนสร้าง prompt
    """
    if mode == "M0":
        normalized_question = question
    else:
        normalized_question = normalize_thai_dates(question)
    return build_prompt(normalized_question, schema_ddl)
