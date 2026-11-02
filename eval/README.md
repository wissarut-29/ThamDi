# eval/ — วัดผล

เจ้าของ: Wissarut (W2, W3, W5)

- `sets/` ชุดทดสอบ `handwritten.jsonl` (70 ข้อ 7 หมวด), `unseen.jsonl`, `val.jsonl` — รูปแบบดู `docs/CONTRACT.md` หัวข้อ 6
- `run.py` รันทุกโหมด (M0–M3) กับทุกชุด แล้วเขียน `results/latest.json`
- `report.py` สร้างตาราง Markdown + กราฟจาก `results/`
- `results/failures.md` วิเคราะห์ข้อผิด 3–5 ตัวอย่าง (W5)
- `demo_answers.json` คำตอบเดโมสำหรับ DEMO_MODE — Chalakorn เติม (C5)
