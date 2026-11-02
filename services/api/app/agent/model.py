"""โหลดโมเดลครั้งเดียว และให้ generate_sql() / model_info()

เจ้าของ: Suphakorn · งาน: S2 · สัญญาอินเทอร์เฟซ: docs/CONTRACT.md
"""


def generate_sql(prompt: str, n: int = 1) -> list[str]:
    """คืนผลลัพธ์จากโมเดล n แบบ (beam) เรียงจากดีที่สุด แต่ละตัวเป็น SQL หรือ <REFUSE> / <CLARIFY>"""
    raise NotImplementedError("S2: ทำเวอร์ชันปลอมก่อน แล้วค่อยโหลดโมเดลจริง")


def model_info() -> dict:
    """คืน {"name", "base_model", "version", "backend", "loaded"} ให้ GET /api/model"""
    raise NotImplementedError("S2")
