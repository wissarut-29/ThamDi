"""Export ชุด val ให้ eval/run.py โหลดได้เองแบบเดียวกับ eval/sets/ อื่น ๆ

ตามสเปกที่ Wissarut ขอ (ดู docs/ISSUES.md): ชุดทดสอบทุกชุดต้องอยู่รูปแบบเดียวกัน
(มี schema เป็นไฟล์ .sql จริงที่มีข้อมูลให้รัน ไม่ใช่ DDL เปล่า ๆ) เพื่อให้ gold_sql
รันแล้วได้ผลไม่ว่าง เทียบผลได้จริง

เขียนไฟล์ 2 แบบ:
- eval/sets/val.jsonl        — เป้าหมาย 30 ข้อ/หมวด x 7 หมวด (5 ข้อ/schema x 6 schema ต่อหมวด)
  บางหมวด (group) อาจได้น้อยกว่า 5 ข้อ/schema เพราะ template มีคำศัพท์ให้เลือกจำกัด — ยอมรับได้
  ตามที่ Wissarut อนุญาตไว้ในรีวิว PR #12 (ดีกว่าซ้ำคำถามเดิมหลายรอบ)
- eval/schemas/val_<name>.sql — หนึ่งไฟล์ต่อ schema ชื่อขึ้นต้นด้วย val_ (กันชนกับ eval/schemas/sales.sql)
  DDL + "-- data" + INSERT ของข้อมูลชุดเดียวกับที่ใช้ตรวจตอนสร้าง (seed เดิม)

schema `school` (VAL_ONLY_SCHEMAS) ได้ unseen=true ส่วนที่เหลือ (เห็นตอนเทรน) ได้ unseen=false
คำถามต้องไม่ซ้ำกับตัวเอง และไม่ซ้ำกับ eval/sets/handwritten.jsonl — เทียบด้วย hash เท่านั้น
(เหตุผลเดียวกับ ml/check_leak.py: เปิดไฟล์ได้เฉพาะเพื่อ hash ทันทีแล้วทิ้งข้อความต้นฉบับ)

**ไม่ตัดคำถามที่ซ้ำกับ ml/data/train.jsonl ออก** แม้จะดูเหมือนควรทำเพื่อกัน unseen=false ได้
คะแนนสูงเกินจริงจากการจำมาตรง ๆ — ลองแล้วพบว่าทำไม่ได้จริงด้วย template ชุดนี้: train.jsonl มี
200 ตัวอย่าง/schema/หมวด ซึ่งมากกว่าจำนวนคำถามไม่ซ้ำที่ template สร้างได้ในแทบทุกหมวด (filter มีแค่
5-9 แบบต่อ schema, group 4-8, join 6, rank 6 ฯลฯ) การตัดคำถามที่ซ้ำกับ train ออกจึงเหลือ 0 ข้อ
เกือบทุกหมวดสำหรับ schema ที่เทรนด้วย ไม่ใช่แค่ group/join ที่เห็นชัดตั้งแต่แรก — ใช้ทางเลือกสำรอง
ที่ Wissarut เสนอไว้แทน: รายงาน/วิเคราะห์ผลแยกตาม field `unseen` ในแต่ละข้อ (true = schema `school`
ที่ไม่เคยอยู่ใน train เลย คะแนนเชื่อถือได้ · false = schema ที่เทรนด้วย คะแนนอาจสูงเกินจริงจากการจำ)
"""

import hashlib
import json
import random
import sys
from pathlib import Path

import duckdb

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from ml.templates.generators import GENERATORS
from ml.templates.schemas import ALL_SCHEMAS, VAL_ONLY_SCHEMAS, stable_seed

EXPORT_SEED = 1000
PER_SCHEMA_PER_CATEGORY = 5  # เป้าหมาย x 6 schema x 7 หมวด = 210 (บางหมวดอาจได้น้อยกว่า)
MAX_ATTEMPTS_PER_CELL = PER_SCHEMA_PER_CATEGORY * 100

ROOT = Path(__file__).resolve().parent.parent
SETS_DIR = ROOT / "eval" / "sets"
SCHEMAS_DIR = ROOT / "eval" / "schemas"
HANDWRITTEN_FILE = SETS_DIR / "handwritten.jsonl"

VAL_ONLY_NAMES = {s.name for s in VAL_ONLY_SCHEMAS}


def _hash_question(text: str) -> str:
    return hashlib.sha256(text.strip().lower().encode("utf-8")).hexdigest()


def _question_hashes(path: Path) -> set[str]:
    """อ่านไฟล์ jsonl เพื่อ hash คำถามทันทีแล้วทิ้งข้อความต้นฉบับ ไม่เก็บ/พิมพ์เนื้อหาจริง"""
    if not path.exists():
        return set()
    hashes = set()
    with path.open(encoding="utf-8") as f:
        for line in f:
            if not line.strip():
                continue
            record = json.loads(line)
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


def _connect_from_rows(spec, rows_by_table: dict[str, list[tuple]]) -> duckdb.DuckDBPyConnection:
    """สร้าง connection จาก rows_by_table ตรง ๆ (ข้อมูลชุดเดียวกับที่เขียนลงไฟล์ .sql)

    ห้ามเรียก spec.seed_fn(rng) อีกรอบด้วย Random ตัวใหม่เพื่อ "สร้างข้อมูลชุดเดิม" แยกต่างหาก —
    ถ้าสูตรคำนวณ seed สองที่ไม่ตรงกันเป๊ะ (หรือใครแก้บรรทัดเดียวในอนาคต) gold_sql จะถูกตรวจบน
    ข้อมูลคนละชุดกับที่ eval ใช้จริง (พบจากรีวิวของ Wissarut บน PR #12)
    """
    con = duckdb.connect(":memory:")
    con.execute(spec.ddl)
    for table, rows in rows_by_table.items():
        if not rows:
            continue
        placeholders = ", ".join(["?"] * len(rows[0]))
        con.executemany(f"INSERT INTO {table} VALUES ({placeholders})", rows)
    return con


def _validate(con, sql: str) -> str:
    """รัน sql ครั้งเดียว คืน 'ok' | 'sql_error' | 'empty'"""
    try:
        rows = con.execute(sql).fetchall()
    except duckdb.Error:
        return "sql_error"
    if not rows or all(v is None for row in rows for v in row):
        return "empty"
    return "ok"


def export() -> None:
    sys.stdout.reconfigure(encoding="utf-8")

    excluded_hashes = _question_hashes(HANDWRITTEN_FILE)

    items = []
    schema_data: dict[str, tuple[str, dict]] = {}  # name -> (ddl, rows_by_table)
    stats = {"sql_error": 0, "empty_result": 0, "excluded": 0, "internal_duplicate": 0}
    shortfalls = []  # (schema, category, kept) ที่ได้น้อยกว่าเป้าหมาย

    for spec in ALL_SCHEMAS:
        data_rng = random.Random(EXPORT_SEED * 1000 + stable_seed(spec.name) % 1000)
        rows_by_table = spec.seed_fn(data_rng)
        con = _connect_from_rows(spec, rows_by_table)
        schema_data[spec.name] = (spec.ddl, rows_by_table)

        gen_rng = random.Random(EXPORT_SEED + stable_seed(spec.name) % 997)
        for category in GENERATORS:
            gen_fn = GENERATORS[category]
            used_in_cell: set[str] = set()
            kept = 0
            attempts = 0
            while kept < PER_SCHEMA_PER_CATEGORY and attempts < MAX_ATTEMPTS_PER_CELL:
                attempts += 1
                question, target = gen_fn(spec, gen_rng)
                q_hash = _hash_question(question)
                if q_hash in excluded_hashes:
                    stats["excluded"] += 1
                    continue
                if q_hash in used_in_cell:
                    stats["internal_duplicate"] += 1
                    continue
                if target not in ("<REFUSE>", "<CLARIFY>"):
                    status = _validate(con, target)
                    if status == "sql_error":
                        stats["sql_error"] += 1
                        continue
                    if status == "empty":
                        stats["empty_result"] += 1
                        continue
                used_in_cell.add(q_hash)
                kept += 1
                items.append({
                    "category": category,
                    "schema": f"val_{spec.name}",
                    "unseen": spec.name in VAL_ONLY_NAMES,
                    "question": question,
                    "gold_sql": target,
                })

            if kept == 0:
                raise RuntimeError(
                    f"ไม่ได้ข้อเลยสำหรับ schema={spec.name} category={category} "
                    f"หลังลอง {attempts} ครั้ง — generator หรือข้อมูลของ schema นี้มีปัญหา"
                )
            if kept < PER_SCHEMA_PER_CATEGORY:
                shortfalls.append((spec.name, category, kept))
        con.close()

    for i, item in enumerate(items, start=1):
        item["id"] = f"v{i:03d}"
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
          f"ซ้ำกับ handwritten: {stats['excluded']}, ซ้ำกันเองใน val: {stats['internal_duplicate']}")
    if shortfalls:
        print(f"ได้น้อยกว่าเป้าหมาย {PER_SCHEMA_PER_CATEGORY} ข้อ/schema (template มีคำศัพท์จำกัด ยอมรับได้):")
        for name, category, kept in shortfalls:
            print(f"  {name}/{category}: ได้ {kept} ข้อ")


if __name__ == "__main__":
    export()
