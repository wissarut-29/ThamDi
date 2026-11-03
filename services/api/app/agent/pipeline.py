"""คำถาม -> prompt -> generate_sql() -> sql_guard -> รัน SQL -> ผลลัพธ์ (โหมด M0-M3)

เจ้าของ: Chalakorn · งาน: C3 · สัญญาอินเทอร์เฟซ: docs/CONTRACT.md

ความหมายของแต่ละโหมด M0-M3: docs/CONTRACT.md หัวข้อ 2

กฎความปลอดภัยที่ไม่ขึ้นกับโหมด: ก่อนรัน SQL จริงกับฐานข้อมูลจริงใน run() ต้องผ่าน
sql_guard เสมอ ไม่ว่าโหมดจะเป็นอะไร — แม้ M0/M1 ที่นิยามไว้ว่า "ไม่ผ่านขั้นช่วยใด ๆ"
ความหมายคือไม่ใช้ guard ตอน*เลือก beam* (เพราะ M0/M1 มี beam เดียวให้เลือกอยู่แล้ว)
แต่ความปลอดภัยของระบบจริงไม่ควรขึ้นกับโหมดที่ใช้วัดผล ส่วน predict_sql() (ใช้กับ eval
เท่านั้น ไม่รันจริง) ยึดตามนิยาม M0-M3 ตรงตัวโดยไม่มีการเติม guard ให้ M0/M1
"""

from dataclasses import dataclass, field

import duckdb

from .model import generate_sql
from .preprocess import build_pipeline_prompt
from .sql_guard import SqlGuardError, check_sql
from .tools import dry_run_executable, run_select, table_names_from_ddl

SPECIAL_TOKENS = {"<REFUSE>", "<CLARIFY>"}
_BEAM_N = {"M0": 1, "M1": 1, "M2": 4, "M3": 4}


@dataclass
class PipelineResult:
    status: str  # "ok" | "refuse" | "clarify" | "error"
    sql: str | None = None
    columns: list[str] = field(default_factory=list)
    rows: list[list] = field(default_factory=list)
    error: str | None = None


def get_dataset(dataset_id: str) -> tuple[str, duckdb.DuckDBPyConnection]:
    """เปิด dataset แบบ read-only คืน (schema_ddl, duckdb_connection)

    สัญญานี้ยังไม่มีใน docs/CONTRACT.md — ต้องให้ Suphakorn เพิ่ม (ดูข้อความที่ร่างไว้ใน
    docs/ISSUES.md) ตอนนี้เป็น stub ไว้ให้เทสต์ monkeypatch แทนได้
    """
    raise NotImplementedError("C3: รอฟังก์ชันเปิด dataset แบบ read-only จากฝั่งระบบ")


def _select_beam(
    candidates: list[str],
    mode: str,
    allowed_tables: set[str],
    con: duckdb.DuckDBPyConnection | None = None,
) -> tuple[str, str | None, str | None]:
    """เลือก beam ที่จะใช้ตอบตามกฎของแต่ละโหมด คืน (status, sql_or_none, error_or_none)"""
    if mode in ("M0", "M1"):
        candidate = candidates[0]
        if candidate in SPECIAL_TOKENS:
            return ("refuse" if candidate == "<REFUSE>" else "clarify"), None, None
        return "ok", candidate, None

    # M2, M3: เลือก beam อันดับแรก (เรียงจากโมเดล) ที่ผ่าน guard (+ dry-run ถ้า M3)
    for candidate in candidates:
        if candidate in SPECIAL_TOKENS:
            continue
        try:
            checked_sql = check_sql(candidate, allowed_tables)
        except SqlGuardError:
            continue
        if mode == "M3" and con is not None and not dry_run_executable(con, checked_sql):
            continue
        return "ok", checked_sql, None

    for candidate in candidates:
        if candidate == "<REFUSE>":
            return "refuse", None, None
        if candidate == "<CLARIFY>":
            return "clarify", None, None
    return "error", None, "ไม่มี SQL ที่ผ่านการตรวจความปลอดภัยหรือรันได้จริงเลยในกลุ่ม beam"


def predict_sql(question: str, schema: str, mode: str = "M3") -> str:
    """ใช้สำหรับ eval (eval/run.py --predictor pipeline) ไม่รัน SQL เอง

    M3 ต้องมี DuckDB connection ไว้ dry-run (EXPLAIN) ด้วย — ใช้ connection ชั่วคราวในหน่วยความจำ
    สร้างจาก schema (DDL) ตรงนี้เลย เพราะ EXPLAIN ใช้แค่โครงตาราง ไม่ต้องมีข้อมูลจริง
    """
    n = _BEAM_N.get(mode, 4)
    prompt = build_pipeline_prompt(question, schema, mode)
    candidates = generate_sql(prompt, n)
    allowed_tables = table_names_from_ddl(schema)

    con = None
    if mode == "M3":
        con = duckdb.connect(":memory:")
        con.execute(schema)

    status, sql, _error = _select_beam(candidates, mode, allowed_tables, con=con)
    if status == "refuse":
        return "<REFUSE>"
    if status == "clarify":
        return "<CLARIFY>"
    if status == "error":
        # ไม่คืน <REFUSE> ตรงนี้ — ถ้าคืน <REFUSE> ตอนไม่มี beam ไหนผ่านเลย eval จะให้คะแนน
        # "ถูก" กับข้อหมวด refuse ทุกข้อที่โมเดลแค่ตอบ SQL พังทุกตัว (ไม่ได้ปฏิเสธจริง) ทำให้
        # ผลต่างระหว่างโหมดสูงเกินจริง และไม่ตรงกับ run() ที่คืน status="error" (ไม่ใช่ "refuse")
        # คืนค่าว่างแทน — eval จะนับเป็น SQL ที่รันไม่ได้ (ไม่ valid, ไม่ correct) ตรงกับความจริง
        return ""
    return sql


def run(question: str, dataset_id: str, mode: str = "M3") -> PipelineResult:
    """ตอบคำถามบน dataset เดียว (ความหมายของแต่ละโหมด: docs/CONTRACT.md)"""
    schema_ddl, con = get_dataset(dataset_id)

    n = _BEAM_N.get(mode, 4)
    prompt = build_pipeline_prompt(question, schema_ddl, mode)
    candidates = generate_sql(prompt, n)
    allowed_tables = table_names_from_ddl(schema_ddl)

    status, sql, error = _select_beam(
        candidates, mode, allowed_tables, con=con if mode == "M3" else None
    )

    if status == "refuse":
        return PipelineResult(status="refuse")
    if status == "clarify":
        return PipelineResult(status="clarify")
    if status == "error":
        return PipelineResult(status="error", error=error)

    # ก่อนรันจริงกับฐานข้อมูลจริง ต้องผ่าน guard เสมอไม่ว่าโหมดไหน (ดู docstring ด้านบน)
    try:
        sql = check_sql(sql, allowed_tables)
    except SqlGuardError as exc:
        return PipelineResult(status="error", error=str(exc))

    try:
        columns, rows = run_select(con, sql)
    except duckdb.Error as exc:
        return PipelineResult(status="error", sql=sql, error=str(exc))

    return PipelineResult(status="ok", sql=sql, columns=columns, rows=rows)
