# สัญญาอินเทอร์เฟซ (CONTRACT)

ข้อตกลงว่าส่วนของแต่ละคนคุยกันผ่านอะไร ทุกคนทำงานคู่ขนานกันได้โดยไม่ต้องรอกัน
ถ้าจะเปลี่ยนอะไรในไฟล์นี้ ให้เปิด PR และให้คนที่ได้รับผลกระทบ review ด้วย

## ภาพรวมการไหลของข้อมูล

```
เว็บ (apps/web)
  -> POST /api/chat                      routers/chat.py        (Suphakorn)
  -> pipeline.run(question, dataset_id)  agent/pipeline.py      (Chalakorn)
       -> preprocess -> prompt           agent/preprocess.py    (Chalakorn)
       -> generate_sql(prompt, n)        agent/model.py         (Suphakorn)
       -> sql_guard -> รัน SQL           agent/sql_guard.py     (Chalakorn)
  -> answer.render(question, result)     agent/answer.py        (Suphakorn)
  -> คำตอบภาษาไทย + SQL + ตาราง
```

## 1. โมเดล — `agent/model.py` (Suphakorn ทำ, Chalakorn ใช้)

```python
generate_sql(prompt: str, n: int = 1) -> list[str]
model_info() -> dict
```

- `prompt` คือข้อความที่ `preprocess.py` สร้าง ซึ่งต้องอยู่ในรูปแบบเดียวกับตอนเทรน รูปแบบนี้ Chalakorn เป็นคนกำหนด
- คืนผลลัพธ์ `n` แบบ (beam) เรียงจากดีที่สุดไปแย่สุด แต่ละตัวเป็น SQL หรือ `<REFUSE>` / `<CLARIFY>`
- โหลดโมเดลครั้งเดียวตอนเริ่ม ถ้าโหลดไม่ขึ้น API ต้องยังเริ่มทำงานได้ และ `model_info()["loaded"]` ต้องเป็น `False`
- `MODEL_BACKEND=fake` ให้คืน SQL ตายตัว เพื่อใช้เทสต์ (ส่งของ: 3 พ.ย. 11:00)
- `model_info()` คืน `{"name", "base_model", "version", "backend", "loaded"}`

## 2. Pipeline — `agent/pipeline.py` (Chalakorn ทำ, Suphakorn และ Wissarut ใช้)

```python
run(question: str, dataset_id: str, mode: str = "M3") -> PipelineResult
```

| ฟิลด์ของ `PipelineResult` | ชนิด | ความหมาย |
|---|---|---|
| `status` | `"ok"` \| `"refuse"` \| `"clarify"` \| `"error"` | ผลโดยรวม |
| `sql` | `str \| None` | SQL ที่รันจริง |
| `columns`, `rows` | `list` | ผลลัพธ์ของ SQL |
| `error` | `str \| None` | ข้อความเมื่อเกิด error |

สำหรับ eval (Wissarut เรียกจาก `eval/run.py --predictor pipeline`):

```python
predict_sql(question: str, schema: str, mode: str = "M3") -> str
```

- `schema` คือข้อความ `CREATE TABLE ...` ของฐานข้อมูลทดสอบ (จาก `eval/schemas/*.sql`) ไม่ใช่ dataset_id
- คืน SQL หรือ `<REFUSE>` / `<CLARIFY>` ตัวเดียวหลังผ่าน sql_guard แล้ว ไม่ต้องรัน SQL เอง eval จะรันเองบน DuckDB

**ความหมายของโหมด M0–M3:** _Chalakorn เติมตรงนี้_ (eval ของ Wissarut รันทุกโหมด)

| โหมด | ความหมาย |
|---|---|
| M0 | |
| M1 | |
| M2 | |
| M3 | |

## 3. คำตอบ — `agent/answer.py` (Suphakorn)

```python
render(question: str, result: PipelineResult) -> str
```

สร้างข้อความภาษาไทยจากแม่แบบ ไม่ใช้โมเดลภาษา

## 4. HTTP API (Suphakorn ทำ ยกเว้น `/api/eval/*` ที่ Wissarut ทำ)

ทุก endpoint ยกเว้น login ต้องส่ง `Authorization: Bearer <token>` ถ้าไม่มี token ให้คืน `401` ถ้าขอ dataset ของคนอื่นให้คืน `404`

| Method | Path | ส่ง | ได้ |
|---|---|---|---|
| POST | `/api/auth/login` | `{username, password}` | `{token}` |
| POST | `/api/datasets` | ไฟล์ (multipart) | `{dataset_id, tables}` |
| GET | `/api/datasets` | — | `[{dataset_id, name, tables}]` |
| POST | `/api/chat` | `{dataset_id, question}` | `{answer, status, sql, columns, rows}` |
| GET | `/api/model` | — | ผลของ `model_info()` |
| GET | `/api/eval/results` | — | ดูหัวข้อ 5 |

## 5. ผล eval — `eval/results/latest.json` (Wissarut ทำ, Suphakorn แสดงบนเว็บ)

```json
{
  "generated_at": "2026-11-04T15:00:00+07:00",
  "simulated": false,
  "model": {"name": "", "version": ""},
  "machine": "",
  "results": [
    {"mode": "M3", "set": "handwritten", "n": 70, "execution_accuracy": 0.0, "valid_sql_rate": 0.0,
     "by_category": {"filter": 0.0, "aggregate": 0.0, "group": 0.0, "rank": 0.0, "thai_date": 0.0, "join": 0.0, "refuse": 0.0}}
  ]
}
```

- `set` เป็นได้ `handwritten` (70 ข้อ) / `unseen` (ข้อใน handwritten ที่อยู่บน schema ที่โมเดลไม่เคยเห็น) / `val` (จาก Chalakorn ถ้ามี)
- `execution_accuracy` = รัน SQL ของโมเดลแล้วได้ผลเหมือน SQL เฉลย (ไม่สนลำดับแถวและชื่อคอลัมน์ มีคอลัมน์เกินได้)
- `valid_sql_rate` = สัดส่วนคำตอบที่รันได้หรือเป็น `<REFUSE>` / `<CLARIFY>`
- `GET /api/eval/results` คืน `latest.json` (ผลจริง) ถ้ายังไม่มีคืน `404`
- `GET /api/eval/results?simulated=true` คืน `simulated.json` (ผลจำลอง) ไว้พัฒนาหน้าเว็บ — **ถ้า `simulated` เป็น `true` หน้าเว็บต้องขึ้นคำเตือนว่าเป็นผลจำลอง**

## 6. ชุดทดสอบ — `eval/sets/*.jsonl` (Wissarut)

หนึ่งบรรทัดต่อหนึ่งข้อ:

```json
{"id": "h001", "category": "filter", "schema": "sales", "unseen": false, "question": "...", "gold_sql": "SELECT ..."}
```

- `handwritten.jsonl` คือชุดเขียนด้วยมือ 70 ข้อ 7 หมวด (`filter`, `aggregate`, `group`, `rank`, `thai_date`, `join`, `refuse`) ครึ่งหนึ่งใช้ schema ที่โมเดลไม่เคยเห็น
- `schema` ชี้ไปที่ `eval/schemas/<schema>.sql` (DDL + ข้อมูลตัวอย่าง รันบน DuckDB)
- `gold_sql` เป็น SQL หรือ `<REFUSE>` / `<CLARIFY>`
- **ห้ามนำไปใช้เป็นข้อมูลเทรน** และห้ามดูแม่แบบเทรนใน `ml/templates/` ตอนเขียน

## 7. คำตอบเดโม — `eval/demo_answers.json` (Chalakorn เติมจากคำถามของ Wissarut)

```json
{"<คำถามเดโม>": {"answer": "", "status": "ok", "sql": "", "columns": [], "rows": []}}
```

ใช้ตอน `DEMO_MODE=true` หรือตอนโมเดลโหลดไม่ขึ้น

## 8. ค่าตั้ง (`.env`)

ดู `.env.example` ห้าม commit `.env` เด็ดขาด
