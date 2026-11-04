"""อ่านไฟล์ที่อัปโหลด (CSV/TSV/TXT/XLSX/XLS/ODS/JSON) เป็นตาราง

เจ้าของ: Suphakorn · งาน: S3, W4 · สัญญาอินเทอร์เฟซ: docs/CONTRACT.md

ค่าในเซลล์เป็นข้อมูลเท่านั้น ไม่ถูกส่งเข้า prompt (prompt ใช้แค่ DDL = ชื่อตาราง/คอลัมน์/ชนิด)
"""

import io
import json
import re
import unicodedata
from pathlib import PurePath

import duckdb
import pandas as pd

# ไฟล์ตาราง: csv/tsv/txt = ข้อความคั่นด้วยตัวคั่น, xlsx/xls/ods = แยกตารางตาม sheet, json = รายการ object
DELIMITED_SUFFIXES = {".csv", ".tsv", ".txt"}
SHEET_SUFFIXES = {".xlsx", ".xls", ".ods"}
ALLOWED_SUFFIXES = DELIMITED_SUFFIXES | SHEET_SUFFIXES | {".json"}
ALLOWED_TEXT = ", ".join(sorted(ALLOWED_SUFFIXES))
MAX_BYTES = 10 * 1024 * 1024
MAX_ROWS = 200_000
MAX_NAME_LEN = 64


# DuckDB ใส่ "..." ให้ชื่อตารางที่เป็น keyword ทุกประเภทใน DDL (รวม data, name, order)
# แต่ pipeline หาชื่อตารางด้วย CREATE TABLE (\w+) จึงต้องเลี่ยงชื่อพวกนี้ ไม่งั้น allowed_tables ว่าง
_KEYWORDS = {k for (k,) in duckdb.connect().execute("SELECT keyword_name FROM duckdb_keywords()").fetchall()}


class IngestError(ValueError):
    """ไฟล์ใช้ไม่ได้ · ข้อความเป็นภาษาไทยส่งให้ผู้ใช้ได้ตรง ๆ"""


def table_name(raw: str, fallback: str) -> str:
    # ชื่อตารางใช้แค่ a-z0-9_ เพราะ sql_guard/tools หาชื่อตารางด้วย \w+ (สระไทยบางตัวไม่นับเป็น \w)
    name = re.sub(r"[^a-z0-9]+", "_", raw.lower()).strip("_")[:MAX_NAME_LEN] or fallback
    if not name[0].isalpha() or name in _KEYWORDS:
        name = f"t_{name}"
    return name


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
    # เติม _2, _3, ... จนได้ชื่อที่ยังไม่ถูกใช้ (เทียบแบบไม่สนตัวพิมพ์ เพราะ DuckDB ไม่สนตัวพิมพ์)
    # กันกรณี "a", "a_2", "A" ที่ตัวที่สามจะไปชนกับ "a_2"
    used: set[str] = set()
    out = []
    for name in names:
        candidate, n = name, 1
        while candidate.lower() in used:
            n += 1
            candidate = f"{name}_{n}"
        used.add(candidate.lower())
        out.append(candidate)
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


def _read_delimited(content: bytes) -> pd.DataFrame:
    # Excel ที่บันทึกแบบ "Unicode Text" เป็น UTF-16 มี BOM นำหน้า · ถ้าไม่มี BOM ห้ามลอง utf-16
    # เพราะไบต์ทั่วไปถอดเป็น utf-16 ได้เกือบเสมอแต่ได้ตัวอักษรขยะ
    if content.startswith((b"\xff\xfe", b"\xfe\xff")):
        encodings = ("utf-16",)
    else:
        # Excel ภาษาไทยบน Windows มักเซฟ CSV เป็น cp874 ถ้าไม่ใช่ UTF-8
        encodings = ("utf-8-sig", "cp874")
    for encoding in encodings:
        try:
            text = content.decode(encoding)
        except UnicodeDecodeError:
            continue
        # เดาตัวคั่นจากบรรทัดหัวตาราง (, ; tab |) · ดูแค่หัวตารางเพราะในข้อมูลอาจมี 1,000 หรือ 1,5
        # CSV จากเครื่องที่ตั้งภาษายุโรปใช้ ; · Excel "Unicode Text" ใช้ tab · ไม่เจอตัวคั่นเลยใช้ , ตามเดิม
        header = next((line for line in text.splitlines() if line.strip()), "")
        sep = max(",;\t|", key=header.count) if any(c in header for c in ",;\t|") else ","
        return pd.read_csv(io.StringIO(text), sep=sep)
    raise IngestError("อ่านไฟล์ไม่ได้ ลองบันทึกเป็น CSV แบบ UTF-8 ใหม่")


def _read_json(content: bytes) -> pd.DataFrame:
    data = json.loads(content.decode("utf-8-sig"))
    # รับ [ {...}, {...} ] หรือ {"ชื่อใดก็ได้": [ {...} ]} ที่มี list อยู่ตัวเดียว
    if isinstance(data, dict):
        lists = [v for v in data.values() if isinstance(v, list)]
        if len(lists) != 1:
            raise IngestError('JSON ต้องเป็นรายการของข้อมูล เช่น [{"สาขา": "บางนา", "ยอด": 100}]')
        data = lists[0]
    if not isinstance(data, list) or not all(isinstance(row, dict) for row in data):
        raise IngestError('JSON ต้องเป็นรายการของข้อมูล เช่น [{"สาขา": "บางนา", "ยอด": 100}]')
    # object ซ้อนกันแตกเป็นคอลัมน์ เช่น ลูกค้า.ชื่อ (column_name แปลง . เป็น _ ให้ทีหลัง)
    return pd.json_normalize(data)


def read_upload(filename: str, content: bytes) -> dict[str, pd.DataFrame]:
    """คืน {ชื่อตาราง: DataFrame} · CSV/TSV/TXT/JSON = 1 ตาราง, XLSX/XLS/ODS = 1 ตารางต่อ sheet ที่มีข้อมูล"""
    suffix = PurePath(filename or "").suffix.lower()
    if suffix not in ALLOWED_SUFFIXES:
        raise IngestError(f"รองรับเฉพาะไฟล์ {ALLOWED_TEXT}")
    if not content:
        raise IngestError("ไฟล์ว่าง")
    if len(content) > MAX_BYTES:
        raise IngestError(f"ไฟล์ใหญ่เกิน {MAX_BYTES // (1024 * 1024)} MB")

    stem = PurePath(filename).stem
    try:
        if suffix in DELIMITED_SUFFIXES:
            raw = [(table_name(stem, "data"), _read_delimited(content))]
        elif suffix == ".json":
            raw = [(table_name(stem, "data"), _read_json(content))]
        else:
            # pandas ดูชนิดจากเนื้อไฟล์เอง (.xlsx = openpyxl, .xls = xlrd, .ods = odfpy)
            # ไฟล์ .xls ที่จริงเป็น .xlsx (เปลี่ยนชื่อมา) จึงยังเปิดได้
            sheets = pd.read_excel(io.BytesIO(content), sheet_name=None)
            # เป็น list ไม่ใช่ dict: sheet "sales" กับ "Sales!" ได้ชื่อเดียวกัน ต้องไม่ทับกันก่อน dedupe
            raw = []
            for i, (sheet, frame) in enumerate(sheets.items(), start=1):
                raw.append((table_name(str(sheet), f"sheet_{i}"), frame))
    except IngestError:
        raise
    except pd.errors.EmptyDataError as exc:
        raise IngestError("ไฟล์ไม่มีข้อมูล") from exc
    except Exception as exc:  # ไฟล์เสีย / ไม่ใช่ไฟล์ตามนามสกุล
        raise IngestError(f"เปิดไฟล์ไม่ได้ ไฟล์อาจเสียหรือไม่ใช่ไฟล์ {suffix} จริง") from exc

    tables: dict[str, pd.DataFrame] = {}
    for name, frame in raw:
        frame = _clean(frame)
        if frame.empty or len(frame.columns) == 0:
            continue
        if len(frame) > MAX_ROWS:
            raise IngestError(f"ข้อมูลเกิน {MAX_ROWS:,} แถว")
        tables[_dedupe([*tables, name])[-1]] = frame

    if not tables:
        raise IngestError("ไฟล์ไม่มีข้อมูล")
    return tables
