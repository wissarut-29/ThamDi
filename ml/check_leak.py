"""ตรวจข้อมูลเทรนว่าไม่รั่วไปทาง schema ทดสอบ (clinic, library) และไม่ซ้ำกับชุดทดสอบ

สองเรื่องที่ตรวจ:
1. ชื่อตาราง/คอลัมน์ของ clinic, library ต้องไม่ปรากฏใน schema ที่ใช้เทรน
   (อ่านชื่อจาก DDL ใน eval/schemas/{clinic,library}.sql ส่วนเหนือ -- data ได้ เพราะเป็นแค่ชื่อ ไม่ใช่ข้อสอบ)
2. คำถามในข้อมูลเทรนต้องไม่ซ้ำกับคำถามในชุดทดสอบ (eval/sets/handwritten.jsonl)
   ส่วนนี้เทียบด้วย hash เท่านั้น: สคริปต์เปิดไฟล์ชุดทดสอบ อ่านทีละบรรทัด แปลงคำถามเป็น sha256 ทันที
   แล้วทิ้งข้อความต้นฉบับไปเลยในหน่วยความจำ ไม่มีจุดไหนในสคริปต์ที่เก็บ พิมพ์ หรือบันทึกเนื้อหาคำถามจริง
   ของชุดทดสอบออกมา — ผลลัพธ์ที่ได้มีแค่ตัวเลขจำนวนข้อซ้ำ (เทียบ hash กับ hash เท่านั้น)

พิมพ์แค่ผ่าน/ไม่ผ่าน + จำนวน
"""

import hashlib
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TRAIN_FILE = ROOT / "ml" / "data" / "train.jsonl"
HANDWRITTEN_FILE = ROOT / "eval" / "sets" / "handwritten.jsonl"
CLINIC_DDL_FILE = ROOT / "eval" / "schemas" / "clinic.sql"
LIBRARY_DDL_FILE = ROOT / "eval" / "schemas" / "library.sql"

# คอลัมน์ที่ชื่อทั่วไปเกินไป ใช้ร่วมกับหลาย schema ที่ถูกต้องตามปกติ (name, province ฯลฯ)
# ถ้าตรวจคอลัมน์เหล่านี้ด้วยจะ false positive กับ schema สังเคราะห์ของเราเอง (เช่น sales ก็มี name/province)
# จึงตรวจแค่ชื่อที่เฉพาะเจาะจงกับ clinic/library จริง ๆ
GENERIC_COLUMN_EXCLUDE = {"name", "province", "category", "status", "fee"}


def _read_above_data_marker(path: Path) -> str:
    text = path.read_text(encoding="utf-8")
    marker = text.find("-- data")
    return text if marker == -1 else text[:marker]


def _parse_ddl_names(ddl_text: str) -> tuple[set[str], set[str]]:
    tables = set(re.findall(r"CREATE TABLE\s+(\w+)", ddl_text))
    columns = set()
    for line in ddl_text.splitlines():
        line = line.strip()
        if not line or line.startswith(("--", "CREATE")) or line in (")", ");"):
            continue
        m = re.match(r"(\w+)\s+", line)
        if m:
            columns.add(m.group(1))
    return tables, columns


def check_schema_leak() -> bool:
    clinic_tables, clinic_cols = _parse_ddl_names(_read_above_data_marker(CLINIC_DDL_FILE))
    library_tables, library_cols = _parse_ddl_names(_read_above_data_marker(LIBRARY_DDL_FILE))
    forbidden_tables = clinic_tables | library_tables
    forbidden_cols = (clinic_cols | library_cols) - GENERIC_COLUMN_EXCLUDE

    if not TRAIN_FILE.exists():
        print(f"ไม่เจอ {TRAIN_FILE} — รัน ml/gen_data.py ก่อน")
        return False

    found_tables = set()
    found_cols = set()
    with TRAIN_FILE.open(encoding="utf-8") as f:
        for line in f:
            record = json.loads(line)
            ddl = record["schema_ddl"]
            tables, cols = _parse_ddl_names(ddl)
            found_tables |= (tables & forbidden_tables)
            found_cols |= (cols & forbidden_cols)

    ok = not found_tables and not found_cols
    if ok:
        print(f"check_schema_leak: ผ่าน (ไม่เจอชื่อตาราง/คอลัมน์ของ clinic, library ใน {TRAIN_FILE.name})")
    else:
        print(f"check_schema_leak: ไม่ผ่าน — เจอตาราง {sorted(found_tables)} คอลัมน์ {sorted(found_cols)}")
    return ok


def _hash_line(text: str) -> str:
    return hashlib.sha256(text.strip().lower().encode("utf-8")).hexdigest()


def check_duplicate_questions() -> bool:
    if not TRAIN_FILE.exists():
        print(f"ไม่เจอ {TRAIN_FILE} — รัน ml/gen_data.py ก่อน")
        return False
    if not HANDWRITTEN_FILE.exists():
        print(f"ไม่เจอ {HANDWRITTEN_FILE} — ข้ามการเช็กซ้ำกับชุดทดสอบ")
        return True

    train_hashes = set()
    with TRAIN_FILE.open(encoding="utf-8") as f:
        for line in f:
            record = json.loads(line)
            train_hashes.add(_hash_line(record["question"]))

    overlap = 0
    test_count = 0
    with HANDWRITTEN_FILE.open(encoding="utf-8") as f:
        for line in f:
            if not line.strip():
                continue
            record = json.loads(line)  # อ่านเพื่อ hash ทันที ไม่เก็บ/พิมพ์ข้อความต้นฉบับ
            test_count += 1
            if _hash_line(record["question"]) in train_hashes:
                overlap += 1

    ok = overlap == 0
    if ok:
        print(f"check_duplicate_questions: ผ่าน (เทียบกับชุดทดสอบ {test_count} ข้อ ไม่พบคำถามซ้ำ)")
    else:
        print(f"check_duplicate_questions: ไม่ผ่าน — พบคำถามซ้ำกับชุดทดสอบ {overlap} ข้อ จาก {test_count} ข้อ")
    return ok


def main() -> None:
    sys.stdout.reconfigure(encoding="utf-8")
    ok1 = check_schema_leak()
    ok2 = check_duplicate_questions()
    sys.exit(0 if (ok1 and ok2) else 1)


if __name__ == "__main__":
    main()
