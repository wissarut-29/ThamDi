"""Export ชุด val ให้ eval/run.py โหลดได้เองแบบเดียวกับ eval/sets/ อื่น ๆ

ตามสเปกที่ Wissarut ขอ (ดู docs/ISSUES.md): ชุดทดสอบทุกชุดต้องอยู่รูปแบบเดียวกัน
(มี schema เป็นไฟล์ .sql จริงที่มีข้อมูลให้รัน ไม่ใช่ DDL เปล่า ๆ) เพื่อให้ gold_sql
รันแล้วได้ผลไม่ว่าง เทียบผลได้จริง

เขียนไฟล์ 2 แบบ:
- eval/sets/val.jsonl        — 210 ข้อ (30 ข้อ/หมวด x 7 หมวด, 5 ข้อ/schema x 6 schema ต่อหมวด)
- eval/schemas/val_<name>.sql — หนึ่งไฟล์ต่อ schema ชื่อขึ้นต้นด้วย val_ (กันชนกับ eval/schemas/sales.sql)
  DDL + "-- data" + INSERT ของข้อมูลชุดเดียวกับที่ใช้ตรวจตอนสร้าง (seed เดิม)

schema `school` (VAL_ONLY_SCHEMAS) ได้ unseen=true ส่วนที่เหลือ (เห็นตอนเทรน) ได้ unseen=false
คำถามต้องไม่ซ้ำกับ eval/sets/handwritten.jsonl — เทียบด้วย hash เท่านั้น (เหตุผลเดียวกับ
ml/check_leak.py: เปิดไฟล์ได้เฉพาะเพื่อ hash ทันทีแล้วทิ้งข้อความต้นฉบับ ไม่พิมพ์/บันทึกเนื้อหาจริง)
"""

import hashlib
import json
import random
import sys
from pathlib import Path

import duckdb

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from ml.gen_data import _build_validation_db, _sql_runs
from ml.templates.generators import GENERATORS
from ml.templates.schemas import ALL_SCHEMAS, VAL_ONLY_SCHEMAS

EXPORT_SEED = 1000
PER_SCHEMA_PER_CATEGORY = 5  # x 6 schema x 7 หมวด = 210

ROOT = Path(__file__).resolve().parent.parent
SETS_DIR = ROOT / "eval" / "sets"
SCHEMAS_DIR = ROOT / "eval" / "schemas"
HANDWRITTEN_FILE = SETS_DIR / "handwritten.jsonl"

VAL_ONLY_NAMES = {s.name for s in VAL_ONLY_SCHEMAS}


def _hash_question(text: str) -> str:
    return hashlib.sha256(text.strip().lower().encode("utf-8")).hexdigest()


def _handwritten_hashes() -> set[str]:
    if not HANDWRITTEN_FILE.exists():
        return set()
    hashes = set()
    with HANDWRITTEN_FILE.open(encoding="utf-8") as f:
        for line in f:
            if not line.strip():
                continue
            record = json.loads(line)  # อ่านเพื่อ hash ทันที ไม่เก็บ/พิมพ์ข้อความต้นฉบับ
            hashes.add(_hash_question(record["question"]))
    return hashes


def _sql_literal(value) -> str:
    if value is None:
        return "NULL"
    if isinstance(value, bool):
        return "TRUE" if value else "FALSE"
    if isinstance(value, (int, float)):
        return str(value)
    return "'" + str(value).replace("'", "''") + "'"


def _insert_statements(rows_by_table: dict[str, list[tuple]]) -> str:
    lines = []
    for table, rows in rows_by_table.items():
        for row in rows:
            values = ", ".join(_sql_literal(v) for v in row)
            lines.append(f"INSERT INTO {table} VALUES ({values});")
    return "\n".join(lines)


def _runs_nonempty(con, sql: str) -> bool:
    try:
        rows = con.execute(sql).fetchall()
    except duckdb.Error:
        return False
    if not rows:
        return False
    return not all(v is None for row in rows for v in row)


def export() -> None:
    sys.stdout.reconfigure(encoding="utf-8")
    # ตรวจแค่ไม่ซ้ำกับ handwritten.jsonl ตามที่ Wissarut ขอ — ไม่บังคับให้ข้อใน val.jsonl เองต้อง
    # ไม่ซ้ำกัน เพราะบางหมวด (group, join) มีคำศัพท์ให้เลือกในแต่ละ schema น้อยมาก (เช่น schema เดียว
    # มีคอลัมน์หมวดหมู่ได้แค่ 1-2 ตัว) ครบ 5 ข้อไม่ซ้ำกันเองไม่ได้จริง ๆ ในบางกรณี
    seen_hashes = _handwritten_hashes()

    items = []
    schema_data: dict[str, tuple[str, dict]] = {}  # name -> (ddl, rows_by_table)
    stats = {"sql_error": 0, "empty_result": 0, "duplicate": 0}

    for spec in ALL_SCHEMAS:
        data_rng = random.Random(EXPORT_SEED * 1000 + hash(spec.name) % 1000)
        rows_by_table = spec.seed_fn(data_rng)
        con = _build_validation_db(spec, random.Random(EXPORT_SEED * 1000 + hash(spec.name) % 1000))
        schema_data[spec.name] = (spec.ddl, rows_by_table)

        gen_rng = random.Random(EXPORT_SEED + hash(spec.name) % 997)
        for category in GENERATORS:
            gen_fn = GENERATORS[category]
            kept = 0
            attempts = 0
            while kept < PER_SCHEMA_PER_CATEGORY and attempts < PER_SCHEMA_PER_CATEGORY * 20:
                attempts += 1
                question, target = gen_fn(spec, gen_rng)
                q_hash = _hash_question(question)
                if q_hash in seen_hashes:
                    stats["duplicate"] += 1
                    continue
                if target not in ("<REFUSE>", "<CLARIFY>"):
                    if not _sql_runs(con, target):
                        stats["sql_error"] += 1
                        continue
                    if not _runs_nonempty(con, target):
                        stats["empty_result"] += 1
                        continue
                kept += 1
                items.append({
                    "category": category,
                    "schema": f"val_{spec.name}",
                    "unseen": spec.name in VAL_ONLY_NAMES,
                    "question": question,
                    "gold_sql": target,
                })
        con.close()

    for i, item in enumerate(items, start=1):
        item["id"] = f"v{i:03d}"
    # จัดลำดับฟิลด์ให้อ่านง่ายแบบเดียวกับ handwritten.jsonl
    ordered_items = [
        {"id": it["id"], "category": it["category"], "schema": it["schema"],
         "unseen": it["unseen"], "question": it["question"], "gold_sql": it["gold_sql"]}
        for it in items
    ]

    SETS_DIR.mkdir(parents=True, exist_ok=True)
    val_path = SETS_DIR / "val.jsonl"
    with val_path.open("w", encoding="utf-8") as f:
        for it in ordered_items:
            f.write(json.dumps(it, ensure_ascii=False) + "\n")

    for name, (ddl, rows_by_table) in schema_data.items():
        schema_path = SCHEMAS_DIR / f"val_{name}.sql"
        content = ddl.strip() + "\n\n-- data\n\n" + _insert_statements(rows_by_table) + "\n"
        schema_path.write_text(content, encoding="utf-8")

    by_category: dict[str, int] = {}
    for it in ordered_items:
        by_category[it["category"]] = by_category.get(it["category"], 0) + 1

    print(f"val: {len(ordered_items)} ข้อ -> {val_path}")
    print(f"  ต่อหมวด: {by_category}")
    print(f"  schema: {sorted({it['schema'] for it in ordered_items})}")
    print(f"ไฟล์ schema ที่ export: {sorted(f'val_{n}.sql' for n in schema_data)}")
    print(f"ข้ามเพราะ SQL รันไม่ผ่าน: {stats['sql_error']}, ได้ผลว่าง: {stats['empty_result']}, "
          f"ซ้ำ (กับตัวเองหรือ handwritten): {stats['duplicate']}")


if __name__ == "__main__":
    export()
