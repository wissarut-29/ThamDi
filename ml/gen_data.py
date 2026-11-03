"""สร้างข้อมูลเทรนสำหรับโมเดล text-to-SQL ภาษาไทย

ใช้ schema สังเคราะห์หลายแบบ (ml/templates/schemas.py) + ตัวสร้างคำถามต่อหมวด
(ml/templates/generators.py) SQL ทุกข้อถูกรันจริงบน DuckDB เพื่อตรวจว่าใช้ได้ก่อนเก็บลงไฟล์
(ยกเว้นหมวด refuse ที่ไม่มี SQL ให้ตรวจ)

ผลลัพธ์: ml/data/train.jsonl, ml/data/val.jsonl (ไม่ขึ้น git ดู .gitignore)
val มี schema `school` ซึ่งไม่อยู่ใน train เลย ตามข้อกำหนดกันข้อสอบรั่ว
"""

import json
import random
import sys
from pathlib import Path

import duckdb

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))  # ให้ import ml.* ได้เวลารันตรง ๆ

from ml.templates.generators import GENERATORS
from ml.templates.schemas import TRAIN_SCHEMAS, VAL_ONLY_SCHEMAS

SEED = 42
TRAIN_PER_CELL = 200
VAL_PER_CELL_TRAIN_SCHEMAS = 30
VAL_PER_CELL_HELD_OUT = 60

OUT_DIR = Path(__file__).resolve().parent / "data"


def _build_validation_db(spec, seed_rng):
    con = duckdb.connect(":memory:")
    con.execute(spec.ddl)
    rows = spec.seed_fn(seed_rng)
    for table, table_rows in rows.items():
        if not table_rows:
            continue
        placeholders = ", ".join(["?"] * len(table_rows[0]))
        con.executemany(f"INSERT INTO {table} VALUES ({placeholders})", table_rows)
    return con


def _sql_runs(con, sql: str) -> bool:
    try:
        con.execute(sql)
        return True
    except duckdb.Error:
        return False


def _generate_cell(spec, category, count, rng, con, stats):
    gen_fn = GENERATORS[category]
    records = []
    for _ in range(count):
        question, target = gen_fn(spec, rng)
        if target not in ("<REFUSE>", "<CLARIFY>") and not _sql_runs(con, target):
            stats["sql_error"] += 1
            continue
        records.append({
            "schema": spec.name,
            "schema_ddl": spec.ddl,
            "category": category,
            "question": question,
            "target": target,
        })
    return records


def generate_split(schemas, per_cell, rng_seed, stats):
    rng = random.Random(rng_seed)
    records = []
    for spec in schemas:
        con = _build_validation_db(spec, random.Random(rng_seed * 1000 + hash(spec.name) % 1000))
        for category in GENERATORS:
            records.extend(_generate_cell(spec, category, per_cell, rng, con, stats))
        con.close()
    return records


def main() -> None:
    sys.stdout.reconfigure(encoding="utf-8")
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    stats = {"sql_error": 0}

    train_records = generate_split(TRAIN_SCHEMAS, TRAIN_PER_CELL, SEED, stats)
    val_from_train = generate_split(TRAIN_SCHEMAS, VAL_PER_CELL_TRAIN_SCHEMAS, SEED + 1, stats)
    val_held_out = generate_split(VAL_ONLY_SCHEMAS, VAL_PER_CELL_HELD_OUT, SEED + 2, stats)
    val_records = val_from_train + val_held_out

    train_path = OUT_DIR / "train.jsonl"
    val_path = OUT_DIR / "val.jsonl"
    with train_path.open("w", encoding="utf-8") as f:
        for r in train_records:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    with val_path.open("w", encoding="utf-8") as f:
        for r in val_records:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")

    def by_category(records):
        counts = {}
        for r in records:
            counts[r["category"]] = counts.get(r["category"], 0) + 1
        return counts

    print(f"train: {len(train_records)} ข้อ -> {train_path}")
    print(f"  ต่อหมวด: {by_category(train_records)}")
    print(f"val: {len(val_records)} ข้อ -> {val_path}")
    print(f"  ต่อหมวด: {by_category(val_records)}")
    print(f"schema เฉพาะ val (ไม่อยู่ใน train): {[s.name for s in VAL_ONLY_SCHEMAS]}")
    print(f"SQL ที่สร้างแล้วรันไม่ผ่าน (ถูกข้าม): {stats['sql_error']}")


if __name__ == "__main__":
    main()
