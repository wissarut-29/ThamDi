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
- เวลาเทรน / GPU: **148.2 นาที / Tesla T4** (รอบเทรนที่ 2 ที่ยืนยันแล้วว่าเทรนจริง — ดู `docs/ISSUES.md`
  ข้อ 12, 13 — ค่าเดิม 136.0 นาที เป็นของรอบแรกที่ export ออกมาเป็นโมเดลตั้งต้น ไม่ใช่ของรอบนี้)
- hyperparameters หลัก (ตั้งไว้ใน `ml/train.ipynb` CONFIG เหมือน v1 ทุกค่า เปลี่ยนแค่ข้อมูลเทรน):
  - fine-tune แบบ LoRA (`use_lora=True`): r=16, alpha=32, dropout=0.05
  - max_length=512, learning_rate=2e-4, epochs=3
  - batch size ต่อ device=8, gradient_accumulation_steps=2 (effective batch ≈16)
  - seed=42

## ไฟล์โมเดล
- **v2 (เทรนจริงแล้ว ยืนยันแล้ว):** เทรนรอบที่ 2 บน Kaggle หลังพบว่า zip รอบแรกเป็นโมเดลตั้งต้นที่ยังไม่
  ได้เทรน (ดู `docs/ISSUES.md` ข้อ 12) ยืนยันรอบนี้แล้วว่าเทรนจริง:
  - เทียบ tensor 3 ตัวที่ LoRA แก้กับ `Qwen/Qwen2.5-0.5B-Instruct` บน HuggingFace ต่างกันจริง
    (185.98 / 474.62 / 28.71 ไม่ใช่ 0)
  - รันผ่าน `pipeline.predict_sql()` จริงด้วย 3 คำถามทดสอบ ได้ SQL ถูกต้องสะอาดทั้งหมด (นับแถว,
    รวมยอดขาย, ปฏิเสธคำสั่งลบ) ไม่มี ` ```sql ` หรือข้อความต่อท้ายแบบไฟล์รอบแรก
  - แก้บั๊ก `tokenizer_config.json` ที่ Kaggle เซฟ `extra_special_tokens` เป็น list แต่
    `transformers>=4.56` (ที่ `requirements-model.txt` ของทีมใช้) ต้องการ dict ไม่งั้นโหลดไม่ขึ้นเลย
    (ทุกคนจะเจอ ไม่ใช่แค่เครื่องเดียว) แก้ไฟล์นี้แล้วก่อนอัปโหลด และเพิ่มการแก้อัตโนมัติใน
    `ml/train.ipynb` ให้รอบเทรนถัดไปไม่ต้องแก้มือ

  ```
  MODEL_URL="https://drive.usercontent.google.com/download?id=1t6C0u1mtA2KIQDO8q-fBrMVetH3-UEJi&export=download&confirm=t" sh scripts/tasks.sh model
  ```
  **ต้องมีเครื่องหมายคำพูดครอบ URL เสมอ** (`&` ในลิงก์จะถูก shell ตัดคำสั่งถ้าไม่มีเครื่องหมายคำพูด —
  Wissarut เจอใน PR #27) ใช้รูปแบบ URL นี้ ไม่ใช่ลิงก์ `/file/d/.../view` ตรง ๆ — ไฟล์ขนาดนี้ Google Drive
  เสิร์ฟหน้าเตือน "ไวรัสสแกนไม่ได้" (HTML ~2.4KB) แทนไฟล์จริงถ้าใช้ `curl -fL` กับลิงก์ view ตรง ๆ (ต้องมี
  `&confirm=t` ถึงจะได้ไฟล์จริง) ทดสอบดาวน์โหลดเต็มไฟล์ด้วย `curl -fL --retry 3` ตัวเดียวกับที่
  `scripts/tasks.sh` ใช้แล้ว ได้ 763,594,123 ไบต์ ตรงกับไฟล์ต้นฉบับทุกไบต์ `unzip -t` ผ่านทั้ง 6 ไฟล์
  ข้างในไม่มี error และเช็ค `tokenizer_config.json` ในไฟล์ที่ดาวน์โหลดมาแล้วว่า `extra_special_tokens`
  เป็น dict ตามที่แก้ไว้ (รอด Google Drive upload/download round-trip มาไม่เพี้ยน)
- โมเดลตั้งต้นที่หลุดเข้ามารอบแรก (ไม่ได้เทรน): เก็บไว้ที่ `models/thamdi_v2_untrained/` ในเครื่อง
  Chalakorn เท่านั้น (ไม่ลบ เผื่อต้องย้อนดู) ไม่มีลิงก์แชร์ ไม่ควรใช้งาน
- v1 (รอบแรก): เก็บสำรองไว้ที่ `models/thamdi_v1_backup/` ในเครื่องเดียวกัน ลิงก์เดิม
  https://drive.google.com/drive/folders/1oaQs9n2w3hh98_xpOImLDimZWRKIkKg-?usp=drive_link
  (ยังมีปัญหาลิงก์โฟลเดอร์แบบเดียวกัน ไม่ได้แก้)

## ข้อจำกัด
- เทรนจากข้อมูลสังเคราะห์ (template-based) ล้วน ไม่ใช่คำถามที่มนุษย์เขียนขึ้นเอง — รูปแบบประโยค
  มีความหลากหลายจำกัดในบางหมวด (เช่น `group` ที่คำศัพท์ให้เลือกต่อ schema มีน้อย)
- ไม่เคยเห็นข้อมูลโดเมน `clinic`/`library` หรือโดเมนที่คล้ายกันเลยระหว่างเทรน (ตั้งใจ กันข้อสอบรั่ว)
- v2 ผ่านการปรับจาก C4 รอบแรกแล้ว (เพิ่มตัวอย่างกรอง 2 เงื่อนไข + เพิ่มจำนวนตัวอย่าง group/join/rank)
  แต่ schema ของไฟล์เดโมจริง (ตาราง `sales` เดี่ยว ไม่ normalize) ไม่มีรูปแบบนี้อยู่ในข้อมูลเทรนเลย —
  บนชุดคำถามเดโมเดิมตอบถูกแค่ 3/7 (ดู `docs/ISSUES.md` ข้อ 8, 14) ทีมแก้โดยเปลี่ยนชุดคำถามเดโมให้ตรงกับ
  รูปแบบที่โมเดลเคยเห็นตอนเทรนแทน (`docs/DEMO_SCRIPT.md`) ตอบถูกครบ 7/7
