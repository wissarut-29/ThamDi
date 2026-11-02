"""สร้างคำตอบภาษาไทยจากผลลัพธ์ด้วยแม่แบบ (ไม่ใช้โมเดลภาษา)

เจ้าของ: Suphakorn · งาน: S3 · สัญญาอินเทอร์เฟซ: docs/CONTRACT.md
"""

from .pipeline import PipelineResult


def render(question: str, result: PipelineResult) -> str:
    """สร้างข้อความตอบภาษาไทยจาก PipelineResult"""
    raise NotImplementedError("S3")
