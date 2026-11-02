"""รัน eval: โหมด M0-M3 x ชุด handwritten / unseen / val

เจ้าของ: Wissarut · งาน: W3, W5 · สัญญาอินเทอร์เฟซ: docs/CONTRACT.md

    python eval/run.py --check-gold                  # ตรวจชุดทดสอบและ SQL เฉลย
    python eval/run.py --predictor mock              # ผลจำลอง (ทดสอบ pipeline ของ eval)
    python eval/run.py --predictor pipeline          # ใช้โมเดลจริงผ่าน pipeline.predict_sql()
"""

from __future__ import annotations

import argparse
import datetime as dt
import decimal
import hashlib
import itertools
import json
import platform
import sys
from collections import Counter
from pathlib import Path

import duckdb

EVAL_DIR = Path(__file__).resolve().parent
ROOT = EVAL_DIR.parent
SETS_DIR = EVAL_DIR / "sets"
SCHEMAS_DIR = EVAL_DIR / "schemas"
RESULTS_DIR = EVAL_DIR / "results"

MODES = ["M0", "M1", "M2", "M3"]
TOKENS = {"<REFUSE>", "<CLARIFY>"}
CATEGORIES = ["filter", "aggregate", "group", "rank", "thai_date", "join", "refuse"]
HANDWRITTEN_SIZE = 70


# ---------- ชุดทดสอบและฐานข้อมูล ----------

def load_jsonl(path: Path) -> list[dict]:
    with path.open(encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]


def load_sets() -> dict[str, list[dict]]:
    """handwritten = ทั้ง 70 ข้อ · unseen = ข้อที่อยู่บน schema ที่โมเดลไม่เคยเห็น · val = จาก Chalakorn (ถ้ามี)"""
    handwritten = load_jsonl(SETS_DIR / "handwritten.jsonl")
    sets = {
        "handwritten": handwritten,
        "unseen": [item for item in handwritten if item.get("unseen")],
    }
    val_path = SETS_DIR / "val.jsonl"
    if val_path.exists():
        sets["val"] = load_jsonl(val_path)
    return sets


def schema_sql(schema: str) -> str:
    return (SCHEMAS_DIR / f"{schema}.sql").read_text(encoding="utf-8")


def schema_ddl(schema: str) -> str:
    """เฉพาะส่วน CREATE TABLE (ก่อนบรรทัด '-- data') สำหรับส่งให้โมเดล"""
    return schema_sql(schema).split("-- data", 1)[0].strip()


def connect(schema: str) -> duckdb.DuckDBPyConnection:
    """ฐานข้อมูลใหม่ในหน่วยความจำทุกครั้ง SQL ที่โมเดลสร้างจึงแก้ข้อมูลของข้อถัดไปไม่ได้"""
    con = duckdb.connect(":memory:")
    con.execute(schema_sql(schema))
    return con


def execute(schema: str, sql: str) -> tuple[list[str], list[tuple]]:
    con = connect(schema)
    try:
        cur = con.execute(sql)
        columns = [d[0] for d in cur.description] if cur.description else []
        return columns, cur.fetchall()
    finally:
        con.close()


# ---------- เทียบผลลัพธ์ ----------

def normalize(value):
    if isinstance(value, (float, decimal.Decimal)):
        return round(float(value), 2)
    if isinstance(value, (dt.date, dt.datetime)):
        return value.isoformat()
    return value


def results_match(gold_rows: list[tuple], pred_rows: list[tuple]) -> bool:
    """เทียบผลแบบไม่สนลำดับแถวและชื่อคอลัมน์ ถ้าผลของโมเดลมีคอลัมน์เกินมา ให้ถือว่าถูกถ้ามีคอลัมน์ชุดหนึ่งตรงกับเฉลย"""
    gold = [tuple(normalize(v) for v in row) for row in gold_rows]
    pred = [tuple(normalize(v) for v in row) for row in pred_rows]
    if len(gold) != len(pred):
        return False
    if not gold:
        return True
    n_gold, n_pred = len(gold[0]), len(pred[0])
    if n_pred < n_gold:
        return False
    target = Counter(gold)
    for cols in itertools.permutations(range(n_pred), n_gold):
        if Counter(tuple(row[i] for i in cols) for row in pred) == target:
            return True
    return False


def score(item: dict, pred: str) -> dict:
    gold = item["gold_sql"].strip()
    pred = (pred or "").strip()
    result = {"id": item["id"], "category": item["category"], "schema": item["schema"],
              "question": item["question"], "gold_sql": gold, "pred": pred,
              "valid": False, "correct": False, "error": None}
    if pred in TOKENS:
        result["valid"] = True
        result["correct"] = pred == gold
        return result
    if gold in TOKENS:
        result["error"] = f"ควรตอบ {gold}"
        # ยังรัน SQL เพื่อดูว่า valid ไหม แต่ถือว่าตอบผิด
    try:
        _, pred_rows = execute(item["schema"], pred)
        result["valid"] = True
    except Exception as e:  # noqa: BLE001 — SQL จากโมเดลพังได้ทุกแบบ
        result["error"] = f"{type(e).__name__}: {e}".splitlines()[0][:200]
        return result
    if gold not in TOKENS:
        _, gold_rows = execute(item["schema"], gold)
        result["correct"] = results_match(gold_rows, pred_rows)
    return result


# ---------- ตัวทำนาย ----------

MOCK_ACCURACY = {"M0": 0.35, "M1": 0.5, "M2": 0.6, "M3": 0.75}


def mock_predict(item: dict, mode: str) -> str:
    """ผลจำลองที่ซ้ำได้: ตอบเฉลยตามสัดส่วนของแต่ละโหมด นอกนั้นตอบผิด ใช้ทดสอบ eval เท่านั้น"""
    h = int(hashlib.sha256(f"{item['id']}:{mode}".encode()).hexdigest(), 16) % 1000 / 1000
    if h < MOCK_ACCURACY[mode]:
        return item["gold_sql"]
    return "SELECT 1" if h < 0.9 else "SELECT * FROM no_such_table"


def pipeline_predictor():
    sys.path.insert(0, str(ROOT / "services" / "api"))
    from app.agent.pipeline import predict_sql  # Chalakorn (C3)

    def predict(item: dict, mode: str) -> str:
        return predict_sql(item["question"], schema_ddl(item["schema"]), mode)

    return predict


# ---------- คำสั่ง ----------

def check_gold() -> int:
    """ตรวจชุดทดสอบ: จำนวนข้อ, หมวด, สัดส่วน unseen, id ซ้ำ และ SQL เฉลยต้องรันได้และได้ผลอย่างน้อย 1 แถว"""
    problems: list[str] = []
    items = load_jsonl(SETS_DIR / "handwritten.jsonl")

    ids = [item["id"] for item in items]
    for dup in [i for i, n in Counter(ids).items() if n > 1]:
        problems.append(f"id ซ้ำ: {dup}")
    if len(items) != HANDWRITTEN_SIZE:
        problems.append(f"มี {len(items)} ข้อ ต้องมี {HANDWRITTEN_SIZE}")
    by_cat = Counter(item["category"] for item in items)
    for cat in set(by_cat) - set(CATEGORIES):
        problems.append(f"หมวดไม่รู้จัก: {cat}")
    for cat in CATEGORIES:
        if by_cat[cat] != HANDWRITTEN_SIZE // len(CATEGORIES):
            problems.append(f"หมวด {cat} มี {by_cat[cat]} ข้อ")
    n_unseen = sum(1 for item in items if item.get("unseen"))
    if n_unseen * 2 < len(items):
        problems.append(f"unseen มี {n_unseen} ข้อ ต้องมีอย่างน้อยครึ่งหนึ่ง")

    for item in items:
        if not (SCHEMAS_DIR / f"{item['schema']}.sql").exists():
            problems.append(f"{item['id']}: ไม่มี schema {item['schema']}")
            continue
        gold = item["gold_sql"].strip()
        if gold in TOKENS:
            if item["category"] != "refuse":
                problems.append(f"{item['id']}: {gold} ต้องอยู่หมวด refuse")
            continue
        try:
            _, rows = execute(item["schema"], gold)
        except Exception as e:  # noqa: BLE001
            problems.append(f"{item['id']}: SQL เฉลยรันไม่ได้ — {e}".splitlines()[0])
            continue
        if not rows or all(v is None for row in rows for v in row):
            problems.append(f"{item['id']}: SQL เฉลยไม่มีผลลัพธ์")

    print(f"handwritten: {len(items)} ข้อ · unseen {n_unseen} · " +
          " ".join(f"{c}={by_cat[c]}" for c in CATEGORIES))
    for p in problems:
        print("  ✗", p)
    print("check-gold:", "ผ่าน" if not problems else f"ไม่ผ่าน ({len(problems)} ปัญหา)")
    return 1 if problems else 0


def run(predictor_name: str, modes: list[str], model_name: str, model_version: str) -> int:
    predict = mock_predict if predictor_name == "mock" else pipeline_predictor()
    sets = load_sets()
    results, details = [], []
    for mode in modes:
        for set_name, items in sets.items():
            scored = [score(item, predict(item, mode)) for item in items]
            n = len(scored)
            by_category = {}
            for cat in sorted({s["category"] for s in scored}):
                group = [s for s in scored if s["category"] == cat]
                by_category[cat] = round(sum(s["correct"] for s in group) / len(group), 4)
            results.append({
                "mode": mode, "set": set_name, "n": n,
                "execution_accuracy": round(sum(s["correct"] for s in scored) / n, 4),
                "valid_sql_rate": round(sum(s["valid"] for s in scored) / n, 4),
                "by_category": by_category,
            })
            if set_name != "unseen":  # unseen เป็นส่วนหนึ่งของ handwritten ไม่ต้องเก็บซ้ำ
                details += [{"mode": mode, "set": set_name, **s} for s in scored]
            print(f"{mode} {set_name:<12} n={n:<3} EX={results[-1]['execution_accuracy']:.2%} "
                  f"valid={results[-1]['valid_sql_rate']:.2%}")

    RESULTS_DIR.mkdir(exist_ok=True)
    simulated = predictor_name == "mock"
    out = {
        "generated_at": dt.datetime.now().astimezone().isoformat(timespec="seconds"),
        "simulated": simulated,
        "model": {"name": "mock" if simulated else model_name, "version": model_version},
        "machine": f"{platform.processor() or platform.machine()} · {platform.system()} {platform.release()}",
        "results": results,
    }
    stem = "simulated" if simulated else "latest"
    (RESULTS_DIR / f"{stem}.json").write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
    (RESULTS_DIR / f"{stem}_items.json").write_text(json.dumps(details, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"บันทึกแล้ว: eval/results/{stem}.json")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="ThamDi eval")
    parser.add_argument("--check-gold", action="store_true", help="ตรวจชุดทดสอบและ SQL เฉลย")
    parser.add_argument("--predictor", choices=["mock", "pipeline"], default="pipeline")
    parser.add_argument("--modes", nargs="+", default=MODES, choices=MODES)
    parser.add_argument("--model-name", default="", help="ชื่อโมเดลที่บันทึกในผล (ดู docs/MODEL_CARD.md)")
    parser.add_argument("--model-version", default="")
    args = parser.parse_args()
    if args.check_gold:
        return check_gold()
    return run(args.predictor, args.modes, args.model_name, args.model_version)


if __name__ == "__main__":
    sys.exit(main())
