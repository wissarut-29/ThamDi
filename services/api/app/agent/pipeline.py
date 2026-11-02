"""คำถาม -> prompt -> generate_sql() -> sql_guard -> รัน SQL -> ผลลัพธ์ (โหมด M0-M3)

เจ้าของ: Chalakorn · งาน: C3 · สัญญาอินเทอร์เฟซ: docs/CONTRACT.md
"""

from dataclasses import dataclass, field


@dataclass
class PipelineResult:
    status: str  # "ok" | "refuse" | "clarify" | "error"
    sql: str | None = None
    columns: list[str] = field(default_factory=list)
    rows: list[list] = field(default_factory=list)
    error: str | None = None


def run(question: str, dataset_id: str, mode: str = "M3") -> PipelineResult:
    """ตอบคำถามบน dataset เดียว mode = "M0".."M3" (ความหมายของแต่ละโหมด: docs/CONTRACT.md)"""
    raise NotImplementedError("C3")
