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
- `MODEL_BACKEND=fake` ให้คืน SQL ตายตัว เพื่อใช้เทสต์
- รับงานได้ทีละ 1 คำถาม ถ้ามีงานค้างอยู่ raise `ModelBusy` (router แปลงเป็น `503`) · โมเดลยังโหลดไม่เสร็จ raise `ModelNotReady`
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

**ความหมายของโหมด M0–M3:** (eval ของ Wissarut รันทุกโหมด)

| โหมด | ความหมาย |
|---|---|
| M0 | prompt ดิบ (คำถาม + DDL) → `generate_sql(prompt, n=1)` ใช้ผลลัพธ์ตัวแรกตรง ๆ ไม่ผ่านขั้นช่วยใด ๆ |
| M1 | M0 + ผ่าน `preprocess.py` ก่อนสร้าง prompt (แปลงวันที่ไทย/พ.ศ. ด้วย `thai_dates.py`) ยัง beam n=1 |
| M2 | M1 + `generate_sql(prompt, n=4)` แล้วเลือก beam อันดับแรก (เรียงจากโมเดล) ที่ผ่าน `sql_guard` |
| M3 | M2 + สำหรับ beam ที่ผ่าน guard แต่ละตัว ลองรันแบบไม่ดึงข้อมูลจริงบน DuckDB (`EXPLAIN` หรือ `... LIMIT 0`) แล้วเลือกตัวแรกที่ทั้งผ่าน guard และรันได้จริง |

กฎร่วมทุกโหมด (เพื่อให้ deterministic และ eval ซ้ำได้):
- `generate_sql` ต้องเรียกแบบ greedy/beam ปรกติ (`do_sample=False`) ไม่ sample แบบสุ่ม
- M2/M3: ถ้าไม่มี beam ไหนผ่านการตรวจเลย (sql_guard หรือ dry-run) ให้คืน `status="error"` — **ห้ามเอา SQL ที่ไม่ผ่านการตรวจไปรันจริงเด็ดขาด** ไม่ fallback ไปใช้ beam อันดับแรกที่ยังไม่ผ่าน
- M1→M2 เปลี่ยนทั้ง preprocess-only→sql_guard และ beam 1→4 พร้อมกัน (จับคู่กันตามธรรมชาติของดีไซน์ เพราะ guard ไม่มีประโยชน์ถ้า beam=1) จึงไม่ใช่ ablation ที่แยกผลสองอย่างนี้ได้สะอาด — ให้ตีความผลต่าง M1→M2 ว่าเป็น "ผลของขั้น guard+beam รวมกัน" ไม่ใช่ผลของ guard อย่างเดียว

**เปิด dataset — `app/db.py` (Suphakorn ทำ, Chalakorn ใช้ใน `pipeline.get_dataset()`)**

```python
open_dataset(dataset_id: str) -> tuple[str, duckdb.DuckDBPyConnection]
```

- คืน `(schema_ddl, connection)` — `schema_ddl` คือ `CREATE TABLE ...;` ของทุกตารางใน dataset (ใช้สร้าง prompt และหา `allowed_tables`) · `connection` เปิดแบบ `read_only=True` เขียน/ลบข้อมูลไม่ได้
- ไม่มี dataset นั้น หรือ id ไม่ใช่ `[A-Za-z0-9_-]` (เช่น `../x`) → `KeyError` · router แปลงเป็น `404`
- ผู้เรียก**ไม่ต้องปิด connection เอง** — ปิดอัตโนมัติเมื่อไม่มีตัวแปรอ้างถึงแล้ว (เช่น พอ `run()` คืนค่า) ถ้าจะปิดเร็วกว่านั้นเรียก `con.close()` ได้
- ไฟล์อยู่ที่ `DATA_DIR/datasets/<dataset_id>.duckdb` (ค่า `DATA_DIR` ดูหัวข้อ 8)

## 3. คำตอบ — `agent/answer.py` (Suphakorn)

```python
render(question: str, result: PipelineResult) -> str
```

สร้างข้อความภาษาไทยจากแม่แบบ ไม่ใช้โมเดลภาษา

## 4. HTTP API (Suphakorn ทำ ยกเว้น `/api/eval/*` ที่ Wissarut ทำ)

ทุก endpoint ยกเว้น login, register และ auth/config ต้องส่ง `Authorization: Bearer <token>` ถ้าไม่มี token ให้คืน `401` ถ้าขอ dataset ของคนอื่นให้คืน `404`

| Method | Path | ส่ง | ได้ |
|---|---|---|---|
| POST | `/api/auth/login` | `{username, password}` (ชื่อไม่สนตัวพิมพ์เล็ก/ใหญ่) | `{token}` |
| POST | `/api/auth/register` (ไม่ต้องมี token) | `{username, password}` ชื่อ a-z 0-9 `_` `.` `-` 3–32 ตัว · รหัส 8 ตัวขึ้นไป | `201` `{token, username}` · ชื่อซ้ำ/สงวน `409` · ชื่อผิดรูป `400` · ปิดรับสมัครหรือเต็ม `403` |
| GET | `/api/auth/config` (ไม่ต้องมี token) | — | `{allow_register}` |
| POST | `/api/datasets` | ไฟล์ตาราง `.csv` `.tsv` `.txt` `.xlsx` `.xls` `.ods` `.json` ไม่เกิน 10 MB (multipart) | `201` `{dataset_id, tables}` · ไฟล์อ่านไม่ได้ `400` · ใหญ่เกิน `413` |
| GET | `/api/datasets` | — | `[{dataset_id, name, tables, duplicate_of?}]` · `duplicate_of` = ไฟล์ที่อัปโหลดซ้ำเนื้อหาเดียวกัน (หน้าเว็บซ่อน) |
| GET | `/api/datasets/{dataset_id}/summary` | query ไม่บังคับ: `table` | `{name, tables, table, row_count, missing_count, duplicate_rows, column_count, columns, numeric_count, numeric_summary, charts}` · dataset ของคนอื่น `404` |
| POST | `/api/chat` | `{dataset_id, question}` (คำถามไม่เกิน 500 ตัวอักษร) | `{answer, status, sql, columns, rows}` · มีคำถามอื่นกำลังรัน `503` |
| GET | `/api/history` | query ไม่บังคับ: `dataset_id`, `limit` (1–200, ค่าเริ่มต้น 50) | `[{id, dataset_id, dataset_name, question, status, sql, answer, created_at}]` ของตัวเองเท่านั้น ใหม่สุดก่อน |
| POST | `/api/export/xlsx` | `{columns, rows, question?, sql?}` (ไม่เกิน 1,000 แถว 100 คอลัมน์) | ไฟล์ `.xlsx` (ชีต "ผลลัพธ์" + "ที่มา") · ไม่รัน SQL แค่จัดรูปแบบข้อมูลที่ส่งมา · รูปแถวไม่ตรง `422` |
| POST | `/api/export/xlsx-book` | `{sheets: [{columns, rows, question?, sql?}, ...]}` (1–30 ชีต แต่ละชีตเงื่อนไขเดียวกับ `/xlsx`) | ไฟล์ `.xlsx` ชีต "สารบัญ" + "ข้อ 1", "ข้อ 2", ... (ส่งออกทั้งบทสนทนา) · รูปแถวไม่ตรง `422` |
| GET | `/api/model` | — | ผลของ `model_info()` |
| GET | `/api/eval/results` | — | ดูหัวข้อ 5 |

จำกัดจำนวนคำขอ: login 50 ครั้งต่อ IP, สมัครบัญชี 50 ครั้งต่อ IP, chat 20 ครั้งต่อผู้ใช้, อัปโหลด 10 ครั้งต่อผู้ใช้, ส่งออก Excel 30 ครั้งต่อผู้ใช้ ต่อนาที เกินได้ `429` · บัญชี `demo` (ใช้ร่วมกันทั้งห้อง) ได้ x6 ของ limit ต่อผู้ใช้

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

- `set` เป็นได้ `handwritten` (70 ข้อ) / `unseen` (ข้อใน handwritten ที่อยู่บน schema ที่โมเดลไม่เคยเห็น) / `val` (205 ข้อ export จาก `ml/export_val.py`) / `val_unseen` (ข้อใน val บน schema ที่ไม่ได้ใช้เทรน)
- `model` ถ้าไม่ส่ง `--model-name`/`--model-version` ให้ `eval/run.py` จะเติมจาก `model_info()` ของโมเดลที่โหลดจริง · `machine` คือ CPU + OS และชื่อ GPU ถ้ารันบน GPU
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

อ่านผ่าน `agent/demo.py`: `lookup(question: str) -> dict | None` เทียบคำถามแบบตรงตัว (ตัด whitespace หัว-ท้าย) ไม่เจอหรือไฟล์ JSON พังคืน `None`

`routers/chat.py` ใช้ตอน `DEMO_MODE=true` หรือตอนโมเดลโหลดไม่ขึ้น ถ้าคำถามไม่อยู่ในไฟล์จะตอบ `status="error"` พร้อมข้อความว่าโมเดลยังไม่พร้อม

## 8. ค่าตั้ง (`.env`)

ดู `.env.example` ห้าม commit `.env` เด็ดขาด

- อ่านผ่าน `app.config.get_settings()` เท่านั้น (ไม่อ่าน `os.environ` ตรง ๆ) · ค่าจาก environment ทับค่าใน `.env`
- path ที่เป็น relative (`MODEL_PATH`, `DATA_DIR`) นับจากโฟลเดอร์บนสุดของ repo ไม่ใช่โฟลเดอร์ที่รันคำสั่ง
- `CORS_ORIGINS` คั่นด้วย `,` · ว่าง = ไม่อนุญาต origin ไหนเลย (ไม่ใช่ `*`)
- `ALLOW_REGISTER` (ค่าเริ่มต้น `false`) เปิดให้สมัครบัญชีเองจากหน้าเว็บ · `MAX_USERS` (ค่าเริ่มต้น 200) จำนวนบัญชีสูงสุดรวม demo
- นับ rate limit ตาม IP: คำขอที่มาจาก proxy ใน `TRUSTED_PROXIES` (ค่าเริ่มต้น `127.0.0.1,::1` · Docker เพิ่ม subnet ของ compose) ใช้ IP ขวาสุดใน `X-Forwarded-For` ที่ไม่ใช่ loopback (ค่าที่ proxy ต่อท้าย ผู้ใช้ปลอมไม่ได้)
