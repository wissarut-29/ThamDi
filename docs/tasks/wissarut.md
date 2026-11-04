# แผนงาน · Wissarut (🟢 วัดผล + คุณภาพ + นำเสนอ · เจ้าของ repo)

GitHub: @wissarut-29 · branch: `feat/wissarut` · ที่มา: [docs/TASKS.md](../TASKS.md) (ถ้าข้อมูลไม่ตรงกัน ให้ยึด TASKS.md)

**ดูแลไฟล์:** `eval/`, `routers/eval.py`, `README.md`, `docs/RUNBOOK.md`, `docs/DEMO_SCRIPT.md`, สไลด์ — ตำแหน่งไฟล์จริงดูใน [STRUCTURE.md](../STRUCTURE.md)

**ทำไม Wissarut คุมการวัดผล:** คนที่ไม่ได้เทรนโมเดลเป็นคนเขียนข้อสอบและรัน eval ลดโอกาสที่โมเดลถูกปรับให้ตรงกับข้อสอบ

## ขั้น 1 — ตั้งค่า repo (3 พ.ย. เช้า)

| เลข | งาน | สถานะ |
|---|---|---|
| 1.1 | สร้าง repo `ThamDi` (public) · เชิญ @fffalafair, @SoSick41 สิทธิ์ Write | ✅ ทำแล้ว · ทั้งสองคนรับคำเชิญแล้ว |
| 1.3 | default branch = `dev` · สร้าง `feat/wissarut` จาก `dev` · Chalakorn และ Suphakorn สร้าง `feat/<ชื่อ>` ของตัวเองในข้อ 1.7 | ✅ ทำแล้ว · มีครบ 3 branch |
| 1.6 | branch protection ของ `dev` และ `main`: ต้องผ่าน PR + 4 checks | ✅ 4 พ.ย.: ต้องผ่าน PR + 4 checks (`api`, `eval-gold`, `web`, `no-ai-watermark`) · ห้าม force push/ลบ · ไม่บังคับ review จาก code owner เพื่อไม่ให้ติดรอคนช่วงใกล้ส่ง |
| 1.7 | clone → `git config core.hooksPath scripts/hooks` → ปิด attribution ของเครื่องมือที่ใช้ → `make data && make test` | รอ hooks (1.4) และ Makefile |
| 1.8 | ตรวจ repo ตาม "เช็กลิสต์ repo" ด้านล่าง → เปิด issue ทุกข้อที่ไม่ผ่าน มอบให้เจ้าของไฟล์ | ✅ ทำแล้ว (issue #7, #10) |

## ขั้น 2 — งานหลัก (3 พ.ย. – 5 พ.ย.)

| เลข | งาน | เมื่อ | เสร็จเมื่อ |
|---|---|---|---|
| W1 | onboarding: อ่าน README, `CONVENTIONS.md`, `CONTRACT.md` · รันระบบ · ถาม 3 คำถาม | 3 พ.ย. เช้า | รันได้บนเครื่องตัวเอง |
| **W2** | **ชุดทดสอบเขียนด้วยมือ 70 ข้อ 7 หมวด** ลง `eval/sets/handwritten.jsonl` (ห้ามเปิดดูแม่แบบเทรนใน `ml/templates/`) · ครึ่งหนึ่งบน schema ที่โมเดลไม่เคยเห็น · `--check-gold` ผ่าน | 3 พ.ย. | 70 ข้อ + Chalakorn ช่วยตรวจ SQL เฉลยแบบสุ่ม 10 ข้อ |
| W3 | `eval/run.py` M0–M3 × set (handwritten / unseen / val) + `eval/report.py` สร้างตาราง Markdown + กราฟ · `routers/eval.py` (`GET /api/eval/results`) | 3 พ.ย. | รันกับผลจำลองได้ |
| W4 | ทดสอบแบบผู้ใช้: อัปโหลดหลายนามสกุล · ถาม 10 คำถาม · สั่ง "ลบตาราง" · ไฟล์มีคำสั่งแฝง · ถามพร้อมกัน 2 แท็บ → **เปิด issue** ให้เจ้าของไฟล์ | 3 พ.ย. ค่ำ + 4 พ.ย. เช้า | รายการบั๊กครบ |
| **W5** | **eval รอบสุดท้าย** ด้วยโมเดลที่ล็อกแล้ว · วิเคราะห์ข้อผิด 3–5 ตัวอย่าง → `eval/results/failures.md` | 4 พ.ย. บ่าย | ตารางผลจริงพร้อมใส่ README |
| W6 | README 10 หัวข้อ · `RUNBOOK.md` · `DEMO_SCRIPT.md` (+ คำถามเดโม 5–7 ข้อ ส่งให้ Chalakorn) · ภาพหน้าจอทุกหน้า | 4 พ.ย. | ทำตาม README บนเครื่องใหม่แล้วรันได้จริง |
| W7 | สไลด์ 12–15 หน้า · อัดคลิปเดโมสำรอง | 4 พ.ย. ค่ำ – 5 พ.ย. เช้า | สไลด์ + คลิปพร้อม |

**สถานะ (3 พ.ย.)**
- W2 ✅ `eval/sets/handwritten.jsonl` 70 ข้อ 7 หมวด · 35 ข้อบน schema ที่โมเดลไม่เคยเห็น · `--check-gold` ผ่าน · รอ Chalakorn ตรวจ SQL เฉลยสุ่ม 10 ข้อ
- W3 ✅ `eval/run.py`, `eval/report.py`, `routers/eval.py` รันกับผลจำลองได้ · รอ `predict_sql()` และความหมาย M0–M3 จาก Chalakorn
- 1.8 ✅ ตรวจแล้ว: ไม่มี API ภายนอก, ไม่มีลายน้ำ AI, ไม่มี `.env`/โมเดล/ข้อมูลในประวัติ · CI + CODEOWNERS (1.5) และ `Makefile` เข้า `dev` แล้วกับ PR #9

**สถานะ (4 พ.ย.)**
- PR #9 merge เข้า `dev` แล้ว · ลองรวมกับ PR #12 ในเครื่อง: pytest 130 ข้อผ่าน · `--predictor pipeline` รันครบ handwritten/unseen/val (โมเดลปลอม) · ทดสอบครบเส้นผ่าน API (อัปโหลด `ยอดขาย.csv`, `order.csv` แล้วถามได้)
- W3 ✅ `predict_sql()` และ M0–M3 จาก Chalakorn ใช้ได้แล้ว
- จุดส่งของ 12:00 → ส่ง [eval/schemas/README.md](../../eval/schemas/README.md) ให้ Chalakorn
- W4 ✅ [eval/results/w4_user_test.md](../../eval/results/w4_user_test.md) API 22/22 · พบปัญหา 1 ข้อ (`AGENTS.md`) Suphakorn แก้แล้วใน PR #16
- W6 ✅ README 10 หัวข้อ · `DEMO_SCRIPT.md` คำถามเดโม 7 ข้อส่ง Chalakorn แล้ว (C5) · เหลือภาพหน้าจอทุกหน้า
- รีวิว PR #12 (val 205 ข้อ) และ PR #16 ผ่านครบ · `eval/run.py` แยกชุด `val_unseen` ตามที่ตกลงใน PR #12 ข้อ 3
- เหลือ: W5 (รอโมเดลสุดท้าย C4) · W6 ภาพหน้าจอ · W7

## จุดส่งของ

| เวลา | ทิศทาง | อะไร |
|---|---|---|
| 3 พ.ย. 12:00 | ➡️ ส่งให้ Chalakorn | ยืนยันรายการ schema ที่ใช้ทดสอบ (ห้ามเข้าข้อมูลเทรน) |
| 3 พ.ย. 21:00 | ➡️ `dev` | ระบบทำงานครบเส้นด้วยโมเดล v1 ✅ |
| 4 พ.ย. 12:00 | ⬅️ รับจาก Chalakorn | 🧊 โมเดลสุดท้าย (ใช้ทำ W5) |
| 4 พ.ย. 12:00 | ➡️ ส่งให้ Chalakorn | คำถามเดโม 5–7 ข้อ |
| 4 พ.ย. 17:00 | ➡️ ส่งให้ Suphakorn | ผล eval จริง (`eval/results/latest.json`) |
| 4 พ.ย. 20:00 | ทุกคน | 🧊 code freeze → `dev` → `main` → tag `v1.0` |

## ตารางเวลา

| เวลา | ทำอะไร |
|---|---|
| 3 พ.ย. เช้า | 1.6 · W1 · 1.8 |
| 3 พ.ย. บ่าย | W2 · W3 |
| 3 พ.ย. ค่ำ | W4 |
| 4 พ.ย. เช้า | W4 · W6 |
| 4 พ.ย. บ่าย | **W5** · W6 |
| 4 พ.ย. ค่ำ | W7 |
| 5 พ.ย. | W7 คลิปสำรอง · ซ้อม 2 รอบ |
| 6 พ.ย. | 🎓 |

## ส่วนที่นำเสนอ
- ปัญหา · ทำไมภาษาไทยยาก · ภาพรวม
- ผลการทดลอง · ข้อผิดตัวอย่าง · ข้อจำกัด
- ร่วมกันทุกคน: ปัญหาที่เจอและวิธีแก้ (รวมการเปลี่ยนจาก API เป็นเทรนเอง)

## ✅ เช็กลิสต์ repo (ตรวจในข้อ 1.8 และอีกครั้ง 4 พ.ย. ก่อน freeze)
- [x] ไม่มีการเรียก API ภายนอกหรือค่าตั้ง/ข้อความที่ชวนเข้าใจว่าใช้
- [x] ไม่มีลายน้ำ AI ทั้งใน commit ทุก branch, PR, โค้ด, เอกสาร และไม่มีไฟล์ตั้งค่าเครื่องมือ AI
- [x] ไม่มี `.env`, ไฟล์โมเดล, `data/`, `*.duckdb` ในประวัติ git
- [ ] CI 4 job เขียวบน `dev` และ `main`
- [x] CODEOWNERS มี 3 คน · README หัวข้อทีมมี 3 คนพร้อมงาน
- [x] ลิงก์ทุกที่ชี้ไป `github.com/wissarut-29/ThamDi` (README, docs, CONTRACT)
- [ ] `docs/STRUCTURE.md`, `TASKS.md`, `CONTRACT.md` ตรงกับของจริง
- [ ] ทำตาม README บนเครื่องใหม่แล้วรันได้ตั้งแต่ clone จนถามคำถามได้
- [ ] มี `MODEL_CARD.md` และ license ของโมเดลตั้งต้น
- [ ] ผล eval มีทั้ง handwritten และ unseen schema · ระบุโมเดล วันที่ เครื่อง

## ✂️ ถ้าไม่ทัน ตัดตามลำดับ
1. หน้า "เกี่ยวกับโมเดล" → ใส่ใน README/สไลด์
2. M1, M2 → รายงาน M0 กับ M3
3. learning curve → ตัด
4. เดโมนามสกุลไฟล์ → CSV/XLSX
5. `<CLARIFY>` → เหลือ `<REFUSE>`

**ห้ามตัด:** โมเดลที่เทรนเอง · ชุดทดสอบเขียนด้วยมือ + unseen schema · ตัวตรวจ SQL · คำตอบจากแม่แบบ · DEMO_MODE · คลิปสำรอง · ไม่มีลายน้ำ AI
