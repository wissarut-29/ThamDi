# eval/ — วัดผล

เจ้าของ: Wissarut (W2, W3, W5)

## ไฟล์

| ไฟล์ | คืออะไร |
|---|---|
| `sets/handwritten.jsonl` | ชุดทดสอบเขียนด้วยมือ 70 ข้อ 7 หมวด หมวดละ 10 · 35 ข้อบน schema ที่โมเดลไม่เคยเห็น |
| `sets/val.jsonl` | ชุด val 205 ข้อ จาก `ml/export_val.py` ของ Chalakorn (PR #12) · `run.py` แยกข้อ `unseen=true` ออกมาเป็นชุด `val_unseen` ด้วย เพราะ val ส่วนที่เหลือสร้างจากแม่แบบเดียวกับข้อมูลเทรน คะแนนจึงสูงเกินจริงได้ |
| `schemas/*.sql` | ฐานข้อมูลทดสอบ (DDL + ข้อมูลตัวอย่าง) — ดู [schemas/README.md](schemas/README.md) |
| `run.py` | รัน eval ทุกโหมด (M0–M3) × ทุกชุด |
| `report.py` | สร้างตาราง Markdown + กราฟจากผล |
| `results/latest*.{json,md,png}` | ผลจริง (ยังไม่มี — รอโมเดล) |
| `results/simulated*.{json,md,png}` | ผลจำลองจาก `--predictor mock` ไว้ทดสอบ eval และหน้าเว็บ — **ห้ามใช้ใน README/สไลด์** |
| `results/failures.md` | วิเคราะห์ข้อผิด 3–5 ตัวอย่าง (W5) |
| `results/w4_user_test.md` | ผลทดสอบแบบผู้ใช้ (W4) · สคริปต์ `user_test.py` |
| `demo_answers.json` | คำตอบเดโมสำหรับ DEMO_MODE — Chalakorn เติม (C5) |

## วิธีใช้

```bash
python -m venv .venv
.venv/Scripts/activate              # Windows · macOS/Linux: source .venv/bin/activate
pip install -r eval/requirements.txt

python eval/run.py --check-gold                       # ตรวจชุดทดสอบ: 70 ข้อ, 7 หมวด, unseen ≥ ครึ่ง, SQL เฉลยรันได้และมีผล
python eval/run.py --predictor mock                   # ผลจำลอง -> results/simulated.json
python eval/run.py --model-name <ชื่อ> --model-version <v>   # โมเดลจริง -> results/latest.json
python eval/report.py                                 # ตาราง + กราฟจาก latest.json (--simulated สำหรับผลจำลอง)
python -m pytest eval/tests
```

## วิธีให้คะแนน

- **Execution accuracy:** รัน SQL ของโมเดลและ SQL เฉลยบนฐานข้อมูลเดียวกัน ถ้าได้แถวเหมือนกันถือว่าถูก ไม่สนลำดับแถว ไม่สนชื่อคอลัมน์ และถ้าโมเดลตอบคอลัมน์เกินมา (เช่น ขอชื่อแล้วได้ทั้งรหัสและชื่อ) ก็ยังถือว่าถูก ตัวเลขปัดเป็นทศนิยม 2 ตำแหน่ง
- ข้อที่เฉลยเป็น `<REFUSE>` / `<CLARIFY>` ต้องตอบ token เดียวกันเป๊ะ
- ทุกข้อรันบนฐานข้อมูลในหน่วยความจำที่สร้างใหม่ SQL ที่ลบ/แก้ข้อมูลจึงไม่กระทบข้อถัดไป
- ข้อจัดอันดับตรวจแล้วว่าไม่มีค่าเสมอกันตรงจุดตัด คำตอบจึงมีแบบเดียว

## กฎ

- **ห้ามนำข้อใน `sets/` หรือ schema `clinic`, `library` ไปเทรน** (Chalakorn ปรับข้อมูลจาก val/unseen ได้เฉพาะดูข้อผิด ไม่ใช่คัดลอกคำถาม)
- คนเขียนข้อสอบห้ามเปิดดู `ml/templates/`
