# Model Card

เจ้าของ: Chalakorn · งาน: C6

## โมเดลตั้งต้น
- ชื่อ / ลิงก์: Qwen2.5-0.5B-Instruct — https://huggingface.co/Qwen/Qwen2.5-0.5B-Instruct
- license: Apache 2.0
- ขนาด (จำนวนพารามิเตอร์, ขนาดไฟล์หลัง export): 494,032,768 พารามิเตอร์ (≈0.49B)
  ไฟล์ `model.safetensors` ~943MB (fp16) — ตรวจแล้วจากไฟล์จริงที่เทรนออกมา (290 tensor,
  ไม่มี NaN/Inf ตัวใดเลย, architecture `Qwen2ForCausalLM` hidden_size 896 ตรงกับโมเดลตั้งต้น)

## ข้อมูลเทรน
- schema ที่ใช้: `sales` (schema จริง ตรงกับ `eval/schemas/sales.sql` ทุกตัวอักษร) +
  `restaurant`, `warehouse`, `hr`, `event` (schema สังเคราะห์ ใช้เทรนด้วย เพื่อให้โมเดลเรียน
  วิธีอ่าน schema จากคำถาม ไม่ใช่จำแค่ `sales`)
- แม่แบบ (`ml/templates/`): `schemas.py` (นิยาม schema) + `generators.py` (สร้างคำถาม+SQL
  7 หมวด: filter, aggregate, group, rank, join, thai_date, refuse) — `ml/gen_data.py` เรียกใช้
  สร้างข้อมูลจริง ทุก SQL ถูกรันผ่าน DuckDB จริงก่อนเก็บ (ไม่มีข้อตก)
- จำนวนตัวอย่าง (train / val): train 9,250 ข้อ — filter/aggregate/thai_date/refuse 1,000 ข้อ/หมวด,
  group/join/rank 1,750 ข้อ/หมวด (เพิ่มจาก 1,000 ในรอบ C4 เพราะ val ชี้ว่าอ่อนสุด 3 หมวดนี้)
  val 1,470 ข้อ (ไม่เปลี่ยนจากเดิม เพื่อวัดผลเทียบรอบต่อรอบได้)
- schema ที่กันไว้ไม่ให้โมเดลเห็น (ใช้ใน eval แบบ unseen): `school` — ใช้เฉพาะ val เท่านั้น
  ไม่อยู่ใน train เลย (`ml/check_leak.py` ตรวจผ่าน: ไม่มีชื่อตาราง/คอลัมน์ของ `clinic`/`library`
  หลุดเข้าข้อมูลเทรน และไม่มีคำถามซ้ำกับ `eval/sets/handwritten.jsonl`)

## การเทรน
- เวลาเทรน: 136.0 นาที (v2, บน Kaggle Notebooks — Colab ติด quota รอบนี้)
- GPU / เครื่อง: Tesla T4 (Kaggle)
- hyperparameters หลัก (ตั้งไว้ใน `ml/train.ipynb` CONFIG เหมือน v1 ทุกค่า เปลี่ยนแค่ข้อมูลเทรน):
  - fine-tune แบบ LoRA (`use_lora=True`): r=16, alpha=32, dropout=0.05
  - max_length=512, learning_rate=2e-4, epochs=3
  - batch size ต่อ device=8, gradient_accumulation_steps=2 (effective batch ≈16)
  - seed=42

## ไฟล์โมเดล
- **v2 (ปัจจุบัน):** อยู่ที่ `models/thamdi/` ในเครื่อง Chalakorn เท่านั้น ยังไม่มีลิงก์แชร์
  (เทรนบน Kaggle แล้วดาวน์โหลดมาวางตรงนี้ — ต้องคุยกันว่าจะแชร์ไฟล์ขนาด ~950MB นี้ให้ Suphakorn
  ยังไงดี เช่น อัปโหลดกลับขึ้น Google Drive เป็นไฟล์ zip เดี่ยว ไม่ใช่โฟลเดอร์ เพื่อให้ `curl -fL`
  ใน `scripts/tasks.sh` ดาวน์โหลดตรงได้ — ปัญหาเดิมเรื่องลิงก์โฟลเดอร์ใช้กับ `make model` ไม่ได้
  ตามที่ Wissarut เจอใน PR #12)
- v1 (รอบแรก): เก็บสำรองไว้ที่ `models/thamdi_v1_backup/` ในเครื่องเดียวกัน ลิงก์เดิม
  https://drive.google.com/drive/folders/1oaQs9n2w3hh98_xpOImLDimZWRKIkKg-?usp=drive_link
  (ยังมีปัญหาลิงก์โฟลเดอร์แบบเดียวกัน ไม่ได้แก้)

## ข้อจำกัด
- เทรนจากข้อมูลสังเคราะห์ (template-based) ล้วน ไม่ใช่คำถามที่มนุษย์เขียนขึ้นเอง — รูปแบบประโยค
  มีความหลากหลายจำกัดในบางหมวด (เช่น `group` ที่คำศัพท์ให้เลือกต่อ schema มีน้อย)
- ไม่เคยเห็นข้อมูลโดเมน `clinic`/`library` หรือโดเมนที่คล้ายกันเลยระหว่างเทรน (ตั้งใจ กันข้อสอบรั่ว)
- v2 ผ่านการปรับจาก C4 รอบแรกแล้ว (เพิ่มตัวอย่างกรอง 2 เงื่อนไข + เพิ่มจำนวนตัวอย่าง group/join/rank)
  ยังไม่ได้วัดผลจริงซ้ำว่าดีขึ้นแค่ไหน (กำลังทำ) และยังไม่ได้ตรวจคำถามเดโมซ้ำ (ของ v1 ถูกแค่ 2/7 ข้อ —
  ดู docs/ISSUES.md ข้อ 8)
