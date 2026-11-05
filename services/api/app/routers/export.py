"""POST /api/export/xlsx · /api/export/xlsx-book (สร้างไฟล์ Excel จากผลลัพธ์ที่หน้าเว็บมีอยู่แล้ว)

เจ้าของ: Suphakorn · สัญญาอินเทอร์เฟซ: docs/CONTRACT.md หัวข้อ 4

ไม่รัน SQL และไม่อ่าน dataset ใด ๆ แค่จัดรูปแบบข้อมูลที่ส่งมาเป็น .xlsx (openpyxl มีใน requirements อยู่แล้ว)
"""

import io
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Response
from openpyxl import Workbook
from openpyxl.styles import Alignment, Font, PatternFill
from openpyxl.utils import get_column_letter
from pydantic import BaseModel, Field

from ..security import limit_by_user

router = APIRouter(prefix="/api/export", tags=["export"])

MAX_ROWS = 1000  # เท่ากับ LIMIT ที่ sql_guard เติมให้
MAX_COLS = 100
MAX_SHEETS = 30  # ส่งออกทั้งบทสนทนา: 1 คำถาม = 1 ชีต
XLSX_TYPE = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"

Cell = str | int | float | bool | None


class ExportIn(BaseModel):
    columns: list[str] = Field(min_length=1, max_length=MAX_COLS)
    rows: list[list[Cell]] = Field(max_length=MAX_ROWS)
    question: str | None = Field(default=None, max_length=500)
    sql: str | None = Field(default=None, max_length=5000)


def _safe(value: Cell) -> Cell:
    # ข้อความที่ขึ้นต้นด้วย = + - @ อาจถูก Excel ตีความเป็นสูตร → ใส่ ' นำหน้า
    if isinstance(value, str) and value[:1] in ("=", "+", "-", "@"):
        return "'" + value
    return value


class BookIn(BaseModel):
    sheets: list[ExportIn] = Field(min_length=1, max_length=MAX_SHEETS)


def _write_table(ws, data: ExportIn) -> None:
    ws.append([_safe(c) for c in data.columns])
    for row in data.rows:
        ws.append([_safe(v) for v in row])

    header_fill = PatternFill("solid", fgColor="E4F6EC")
    for cell in ws[1]:
        cell.font = Font(bold=True)
        cell.fill = header_fill
        cell.alignment = Alignment(vertical="center")
    ws.freeze_panes = "A2"

    for j, name in enumerate(data.columns, start=1):
        values = [name] + [r[j - 1] for r in data.rows[:200]]
        width = max(len(str(v)) for v in values if v is not None) if values else 8
        ws.column_dimensions[get_column_letter(j)].width = min(max(width + 2, 8), 60)
        col = [r[j - 1] for r in data.rows]
        numeric = all(isinstance(v, (int, float)) and not isinstance(v, bool) for v in col)
        if data.rows and numeric:
            for (cell,) in ws.iter_rows(min_row=2, min_col=j, max_col=j):
                cell.number_format = "#,##0.##"


def _bold_first_col(ws) -> None:
    for (cell,) in ws.iter_rows(min_col=1, max_col=1):
        cell.font = Font(bold=True)


def _save(wb: Workbook) -> bytes:
    buf = io.BytesIO()
    wb.save(buf)
    return buf.getvalue()


def _now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M")


def build_xlsx(data: ExportIn) -> bytes:
    wb = Workbook()
    ws = wb.active
    ws.title = "ผลลัพธ์"
    _write_table(ws, data)

    info = wb.create_sheet("ที่มา")
    info.append(["คำถาม", _safe(data.question or "")])
    info.append(["SQL ที่ระบบรันจริง", _safe(data.sql or "")])
    info.append(["จำนวนแถว", len(data.rows)])
    info.append(["สร้างเมื่อ (UTC)", _now()])
    info.append(["สร้างโดย", "ThamDi (รันในเครื่อง)"])
    info.column_dimensions["A"].width = 20
    info.column_dimensions["B"].width = 80
    _bold_first_col(info)
    return _save(wb)


def build_book(book: BookIn) -> bytes:
    # ชีตแรกเป็นสารบัญ (ข้อ · คำถาม · SQL · จำนวนแถว) ตามด้วยชีตผลลัพธ์ "ข้อ 1", "ข้อ 2", ...
    wb = Workbook()
    toc = wb.active
    toc.title = "สารบัญ"
    toc.append(["ชีต", "คำถาม", "SQL ที่ระบบรันจริง", "จำนวนแถว"])
    for i, sheet in enumerate(book.sheets, start=1):
        name = f"ข้อ {i}"
        toc.append([name, _safe(sheet.question or ""), _safe(sheet.sql or ""), len(sheet.rows)])
        _write_table(wb.create_sheet(name), sheet)
    toc.append([])
    toc.append(["สร้างเมื่อ (UTC)", _now()])
    toc.append(["สร้างโดย", "ThamDi (รันในเครื่อง)"])
    for cell in toc[1]:
        cell.font = Font(bold=True)
        cell.fill = PatternFill("solid", fgColor="E4F6EC")
    for col, width in zip("ABCD", (10, 50, 80, 12), strict=True):
        toc.column_dimensions[col].width = width
    return _save(wb)


def _check_shape(sheet: ExportIn) -> None:
    width = len(sheet.columns)
    if any(len(r) != width for r in sheet.rows):
        raise HTTPException(
            status_code=422,  # ชื่อค่าคงที่ของ 422 เปลี่ยนตามเวอร์ชัน starlette จึงใช้ตัวเลขตรง ๆ
            detail="จำนวนคอลัมน์ในแต่ละแถวไม่ตรงกับหัวตาราง",
        )


def _xlsx_response(content: bytes) -> Response:
    return Response(
        content=content,
        media_type=XLSX_TYPE,
        headers={"Content-Disposition": 'attachment; filename="thamdi.xlsx"'},
    )


@router.post("/xlsx")
def export_xlsx(body: ExportIn, _username: str = Depends(limit_by_user("export", limit=30))) -> Response:
    _check_shape(body)
    return _xlsx_response(build_xlsx(body))


@router.post("/xlsx-book")
def export_xlsx_book(body: BookIn, _username: str = Depends(limit_by_user("export", limit=30))) -> Response:
    for sheet in body.sheets:
        _check_shape(sheet)
    return _xlsx_response(build_book(body))
