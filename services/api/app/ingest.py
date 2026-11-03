"""อ่านไฟล์ที่อัปโหลด (CSV/XLSX ฯลฯ) เป็นตาราง

เจ้าของ: Suphakorn · งาน: S3, W4 · สัญญาอินเทอร์เฟซ: docs/CONTRACT.md

ค่าในเซลล์เป็นข้อมูลเท่านั้น ไม่ถูกส่งเข้า prompt (prompt ใช้แค่ DDL = ชื่อตาราง/คอลัมน์/ชนิด)
"""

import io
import re
import unicodedata
from pathlib import PurePath

import pandas as pd

ALLOWED_SUFFIXES = {".csv", ".xlsx"}
MAX_BYTES = 10 * 1024 * 1024
MAX_ROWS = 200_000
MAX_NAME_LEN = 64


class IngestError(ValueError):
    """ไฟล์ใช้ไม่ได้ · ข้อความเป็นภาษาไทยส่งให้ผู้ใช้ได้ตรง ๆ"""


def table_name(raw: str, fallback: str) -> str:
    # ชื่อตารางใช้แค่ a-z0-9_ เพราะ sql_guard/tools หาชื่อตารางด้วย \w+ (สระไทยบางตัวไม่นับเป็น \w)
    name = re.sub(r"[^a-z0-9]+", "_", raw.lower()).strip("_")[:MAX_NAME_LEN]
    if not name:
        return fallback
    return name if name[0].isalpha() else f"t_{name}"


def column_name(raw, index: int) -> str:
    # เก็บภาษาไทยไว้ (รวมสระ/วรรณยุกต์) แต่แทนช่องว่างและสัญลักษณ์ด้วย _
    text = "" if raw is None else str(raw).strip()
    if not text or text.lower().startswith("unnamed:"):
        return f"col_{index + 1}"
    kept = "".join(
        ch if ch.isalnum() or unicodedata.category(ch).startswith("M") else "_" for ch in text
    )
    kept = re.sub(r"_+", "_", kept).strip("_")[:MAX_NAME_LEN]
    return kept or f"col_{index + 1}"


def _dedupe(names: list[str]) -> list[str]:
    seen: dict[str, int] = {}
    out = []
    for name in names:
        key = name.lower()
        seen[key] = seen.get(key, 0) + 1
        out.append(name if seen[key] == 1 else f"{name}_{seen[key]}")
    return out


def _clean(frame: pd.DataFrame) -> pd.DataFrame:
    frame = frame.dropna(how="all").dropna(axis=1, how="all")
    frame.columns = _dedupe([column_name(c, i) for i, c in enumerate(frame.columns)])
    for col in frame.columns:
        series = frame[col]
        # วันที่จาก Excel มาเป็น datetime เสมอ ถ้าไม่มีเวลาเลยเก็บเป็น DATE (แบบเดียวกับ schema ที่เทรน)
        if not pd.api.types.is_datetime64_any_dtype(series):
            continue
        values = series.dropna()
        if (values.dt.normalize() == values).all():
            frame[col] = series.dt.date
    return frame


def _read_csv(content: bytes) -> pd.DataFrame:
    # Excel ภาษาไทยบน Windows มักเซฟ CSV เป็น cp874 ถ้าไม่ใช่ UTF-8
    for encoding in ("utf-8-sig", "cp874"):
        try:
            return pd.read_csv(io.BytesIO(content), encoding=encoding)
        except UnicodeDecodeError:
            continue
    raise IngestError("อ่านไฟล์ CSV ไม่ได้ ลองบันทึกเป็น UTF-8 ใหม่")


def read_upload(filename: str, content: bytes) -> dict[str, pd.DataFrame]:
    """คืน {ชื่อตาราง: DataFrame} · CSV = 1 ตาราง, XLSX = 1 ตารางต่อ sheet ที่มีข้อมูล"""
    suffix = PurePath(filename or "").suffix.lower()
    if suffix not in ALLOWED_SUFFIXES:
        raise IngestError("รองรับเฉพาะไฟล์ .csv และ .xlsx")
    if not content:
        raise IngestError("ไฟล์ว่าง")
    if len(content) > MAX_BYTES:
        raise IngestError(f"ไฟล์ใหญ่เกิน {MAX_BYTES // (1024 * 1024)} MB")

    stem = PurePath(filename).stem
    try:
        if suffix == ".csv":
            raw = {table_name(stem, "data"): _read_csv(content)}
        else:
            sheets = pd.read_excel(io.BytesIO(content), sheet_name=None)
            raw = {}
            for i, (sheet, frame) in enumerate(sheets.items(), start=1):
                raw[table_name(str(sheet), f"sheet_{i}")] = frame
    except IngestError:
        raise
    except pd.errors.EmptyDataError as exc:
        raise IngestError("ไฟล์ไม่มีข้อมูล") from exc
    except Exception as exc:  # ไฟล์เสีย / ไม่ใช่ไฟล์ตามนามสกุล
        raise IngestError("เปิดไฟล์ไม่ได้ ไฟล์อาจเสียหรือไม่ใช่ CSV/XLSX จริง") from exc

    tables: dict[str, pd.DataFrame] = {}
    for name, frame in raw.items():
        frame = _clean(frame)
        if frame.empty or len(frame.columns) == 0:
            continue
        if len(frame) > MAX_ROWS:
            raise IngestError(f"ข้อมูลเกิน {MAX_ROWS:,} แถว")
        tables[_dedupe([*tables, name])[-1]] = frame

    if not tables:
        raise IngestError("ไฟล์ไม่มีข้อมูล")
    return tables
