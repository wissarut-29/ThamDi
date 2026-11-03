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
- จำนวนตัวอย่าง (train / val): train 7,000 ข้อ (1,000 ข้อ/หมวด x 7 หมวด, กระจาย 5 schema ที่เทรน)
  val 1,470 ข้อ (1,050 ข้อจาก schema ที่เทรน + 420 ข้อจาก schema ที่กันไว้ `school`)
- schema ที่กันไว้ไม่ให้โมเดลเห็น (ใช้ใน eval แบบ unseen): `school` — ใช้เฉพาะ val เท่านั้น
  ไม่อยู่ใน train เลย (`ml/check_leak.py` ตรวจผ่าน: ไม่มีชื่อตาราง/คอลัมน์ของ `clinic`/`library`
  หลุดเข้าข้อมูลเทรน และไม่มีคำถามซ้ำกับ `eval/sets/handwritten.jsonl`)

## การเทรน
- เวลาเทรน: **TODO — รอค่าที่ notebook พิมพ์ตอนเทรนจบ** (`ml/train.ipynb` เซลล์สุดท้าย)
- GPU / เครื่อง: **TODO — รอค่าที่ notebook พิมพ์** (Colab ให้ตามคิวตอนนั้น ปรกติ T4)
- hyperparameters หลัก (ตั้งไว้ใน `ml/train.ipynb` CONFIG — ยืนยันตรงนี้แน่นอน เพราะเป็นค่าที่
  เขียนไว้ในโน้ตบุ๊กเอง ไม่ใช่ค่าที่ต้องรอผลจากการรันจริง):
  - fine-tune แบบ LoRA (`use_lora=True`): r=16, alpha=32, dropout=0.05
  - max_length=512, learning_rate=2e-4, epochs=3
  - batch size ต่อ device=8, gradient_accumulation_steps=2 (effective batch ≈16)
  - seed=42

## ไฟล์โมเดล
- ลิงก์ดาวน์โหลด (ใช้กับ `make model`): **TODO — รอ Chalakorn แชร์ลิงก์ Google Drive หรือ
  อัปโหลดที่อื่น** (ตอนนี้อยู่ในเครื่อง Chalakorn ที่ `models/thamdi/` ยังไม่ได้ส่งต่อ)
- เวอร์ชัน: v1 (ประตูแรก ยังไม่ผ่านการปรับจากข้อผิดของ val — ดู C4)

## ข้อจำกัด
- ยังไม่มีตัวเลข exact match / execution accuracy จริงบน val จาก `ml/train.ipynb` (ต้องรอผล
  การรันจริงเพื่อใส่ตรงนี้ ตัวเลขจริงจะวัดซ้ำอีกทีด้วย `eval/run.py` บนชุด handwritten/unseen/val)
- เทรนจากข้อมูลสังเคราะห์ (template-based) ล้วน ไม่ใช่คำถามที่มนุษย์เขียนขึ้นเอง — รูปแบบประโยค
  มีความหลากหลายจำกัดในบางหมวด (เช่น `group`, `join` ที่คำศัพท์ให้เลือกต่อ schema มีน้อย)
- ไม่เคยเห็นข้อมูลโดเมน `clinic`/`library` หรือโดเมนที่คล้ายกันเลยระหว่างเทรน (ตั้งใจ กันข้อสอบรั่ว)
- โมเดลนี้เป็น v1 ยังไม่ผ่านการปรับแก้จากข้อผิดจริง (C4 — กำหนดพรุ่งนี้เช้า)
