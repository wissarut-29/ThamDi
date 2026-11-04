# ThamDi · แบ่งงานใหม่ 3 คน (repo ใหม่ของ Wissarut)

**เวลาที่เหลือ:** 3 พ.ย. (วันนี้) – 6 พ.ย. 2569 · ทำงานจริง 3–4 พ.ย. · 5 พ.ย. ซ้อมอย่างเดียว
**ข้อกำหนด:** ไม่ใช้ API · เทรนโมเดลเอง · รันในเครื่อง · ไม่มีลายน้ำ AI

| | **Chalakorn** | **Suphakorn** | **Wissarut** |
|---|---|---|---|
| GitHub | @fffalafair | @SoSick41 | @wissarut-29 |
| บทบาท | **โมเดล** | **ระบบ** | **วัดผล + คุณภาพ + นำเสนอ** |
| branch | `feat/chalakorn` | `feat/suphakorn` | `feat/wissarut` |
| หน้าที่พิเศษ | — | — | **เจ้าของ repo** (ตั้งค่า, สิทธิ์, branch protection) |
| ดูแล | `ml/`, `agent/pipeline.py`, `preprocess.py`, `demo.py`, `sql_guard.py`, `thai_dates.py`, `tools.py`, `scripts/gen_sales_db.py`, `docs/MODEL_CARD.md` | `apps/web/`, `agent/model.py`, `answer.py`, `routers/` (ยกเว้น eval), `main.py`, `db.py`, `security.py`, `ingest.py`, Docker, `Makefile`, `.github/` | `eval/`, `routers/eval.py`, `README.md`, `docs/RUNBOOK.md`, `docs/DEMO_SCRIPT.md`, สไลด์ |

## 📌 สถานะ ณ 4 พ.ย. 19:50

| ใคร | เสร็จแล้ว | ยังเหลือ |
|---|---|---|
| Chalakorn | C1 · C2 โมเดล v1 · C3 · C5 โครงสร้าง + คำตอบเดโม 2 ข้อ (#18) · `get_dataset()` จริง (#18) · ปรับข้อมูลเทรนจากข้อผิดของ val · C4 เทรนโมเดล v2 แล้ว · C6 `MODEL_CARD.md` ครบ (#24) | **PR #27** (ลิงก์ zip โมเดล v2 + แก้ `thai_dates`) รีวิวแล้ว รอแก้ 2 ข้อ: ใส่เครื่องหมายคำพูดครอบ `MODEL_URL` · แปลง "ปี 2568" ที่ไม่มีชื่อเดือน (ขวาง W5, S6) · C5 รันคำถามเดโม 7 ข้อซ้ำกับ v2 |
| Suphakorn | S1–S4 · ลบตัวเสียบ `get_dataset` · ทดสอบโมเดล v1 จริง + ผลวัดใน RUNBOOK (#19) · ชื่อไทย `val_unseen` บนเว็บ · รับ .xls .ods .tsv .txt .json (#22) | S5 แสดง `latest.json` จริง (รอ W5) · S6 เครื่องเดโม (ลิงก์ v2 อยู่ใน PR #27 · Windows ถ้า `curl` ขึ้น `CRYPT_E_REVOCATION_OFFLINE` ให้เติม `--ssl-no-revoke`) |
| Wissarut | 1.1–1.8 · W1–W4 · W6 README/RUNBOOK/DEMO_SCRIPT · `dev` → `main` (#20) · ลองติดตั้งจาก clone ใหม่ · รีวิว/merge #22–#25 · รีวิว #27 · อัปเดต issue #10, #14 | W5 eval รอบสุดท้าย (รอ #27 merge) · W6 ภาพหน้าจอ · W7 สไลด์ + คลิป (หน้า 10 ใส่ "ยังไม่รับ PDF, Word, รูปภาพ") · ตัดสินใจคำถามเดโม (รอ C5 รอบใหม่) · tag `v1.0` หลัง freeze |

---

## ขั้น 1 — สร้าง repo ใหม่ (3 พ.ย. เช้า · Wissarut เป็นเจ้าของ repo)

**เจ้าของ repo: Wissarut (@wissarut-29)** — repo อยู่ที่ `github.com/wissarut-29/ThamDi`

| ลำดับ | ใคร | ทำอะไร | เสร็จเมื่อ |
|---|---|---|---|
| 1.1 | **Wissarut** | สร้าง repo ว่างชื่อ `ThamDi` (ไม่ติ๊ก README / .gitignore / license เพื่อไม่ให้ชนกับโค้ดที่จะ push) · เชิญ @fffalafair, @SoSick41 สิทธิ์ **Write** | ทั้งสองคนกดรับคำเชิญแล้ว |
| 1.2 | **Chalakorn** | push โค้ดล่าสุดจากเครื่องตัวเองขึ้น repo ใหม่ (ดูคำสั่งด้านล่าง) | `main` และ `dev` มีโค้ดล่าสุด |
| 1.3 | **Wissarut** | default branch = `dev` · สร้าง `feat/chalakorn`, `feat/suphakorn`, `feat/wissarut` จาก `dev` | `git branch -r` มี 5 ตัว |
| 1.4 | **Chalakorn** | PR: `docs/CONVENTIONS.md` + `scripts/hooks/` + `.gitignore` (ไฟล์เครื่องมือ AI, `models/`, `ml/data/`) | merge แล้ว |
| 1.5 | **Suphakorn** | PR: `.github/CODEOWNERS` 3 คน · CI 4 job: `api`, `eval-gold`, `web`, `no-ai-watermark` | CI เขียว |
| 1.6 | **Wissarut** | branch protection ของ `dev` และ `main`: ต้องผ่าน PR + 4 checks (ไม่บังคับ review จาก code owner เพื่อไม่ให้ติดรอคนช่วงใกล้ส่ง) | ตั้งแล้ว 4 พ.ย. |
| 1.7 | **ทุกคน** | clone → `git config core.hooksPath scripts/hooks` → ปิด attribution ของเครื่องมือที่ใช้ → `make data && make test` | เทสต์ผ่านบนเครื่องตัวเอง |
| 1.8 | **Wissarut** | ตรวจ repo ตาม "เช็กลิสต์ repo" ท้ายไฟล์ → เปิด issue ทุกข้อที่ไม่ผ่าน มอบให้เจ้าของไฟล์ | issue ครบ |

### คำสั่งข้อ 1.2 (Chalakorn)
ใช้ clone ในเครื่องที่มีงานล่าสุดของ**ทุกคน** (รวม merge จาก Suphakorn) ถ้าของใครอยู่แต่ในเครื่อง ให้ merge เข้า `dev` ในเครื่องก่อน
```bash
cd ThamDi
git fetch --all                                   # ถ้า remote เดิมยังอยู่ จะ error ได้ ไม่เป็นไร
git checkout dev
git remote set-url origin https://github.com/wissarut-29/ThamDi.git
git push -u origin dev
git push origin dev:main                          # main เริ่มจาก dev ล่าสุด
```
- push **พร้อมประวัติ commit เดิม** (ไม่ใช่ copy ไฟล์แล้ว commit ใหม่) — commit ของ Chalakorn และ Suphakorn ตั้งแต่ 22 ต.ค. จะยังอยู่ และอาจารย์เห็นว่าใครทำอะไร
- ถ้าเครื่องไหนไม่มีประวัติเลย ใช้ไฟล์สำรอง `ThamDi-backup-2026-10-28.bundle` เป็นฐาน: `git clone ThamDi-backup-2026-10-28.bundle ThamDi` แล้วเติมงานหลัง 28 ต.ค. จากเครื่องของแต่ละคน
- **ห้าม push branch เก่า** (`p2/0X-…`, `docs/…`, `chore/…`) ขึ้น repo ใหม่ — push แค่ `dev`

---

## ขั้น 2 — งานของแต่ละคน (3 พ.ย. บ่าย – 4 พ.ย.)

### 🔵 Chalakorn — โมเดล

| เลข | งาน | เมื่อ | เสร็จเมื่อ |
|---|---|---|---|
| **C1** | **ลบของจากแผน API:** `agent/llm.py`, `agent/loop.py`, ทุกการอ้างถึง Groq/Gemini ในไฟล์ของตัวเอง | 3 พ.ย. | `grep -riE "groq|gemini" ml/ services/api/app/agent/` ไม่เจอ |
| **C2** | **ประตูโมเดล v1:** ถ้ายังไม่มีโมเดลที่ fine-tune แล้ว → สร้างข้อมูล 5–10k แล้วเทรนบน Colab ให้จบ · บันทึก checkpoint ลง Drive | 3 พ.ย. ก่อน 18:00 | Suphakorn ได้ไฟล์โมเดล v1 |
| **C3** | `pipeline.py` M0–M3 + `preprocess.py` ใช้ `generate_sql()` ของ Suphakorn · เทสต์ด้วยโมเดลปลอม | 3 พ.ย. | pytest ผ่าน |
| **C4** | ปรับข้อมูลจากข้อผิดของ **val / unseen เท่านั้น** → เทรนตัวสุดท้าย → export ขนาดเล็ก → อัปโหลด (GitHub Release / HF private / Drive) + ลิงก์ให้ `make model` | 4 พ.ย. ก่อนเที่ยง | 🧊 โมเดลสุดท้ายล็อก |
| **C5** | DEMO_MODE: บันทึกคำตอบจริงของคำถามเดโม (จาก Wissarut) ลง `eval/demo_answers.json` | 4 พ.ย. | ตัดเน็ต/ปิดโมเดลแล้วคำถามเดโมยังตอบได้ |
| **C6** | `docs/MODEL_CARD.md`: โมเดลตั้งต้น + license, ขนาด, ข้อมูลเทรน (schema, แม่แบบ, จำนวน), เวลาเทรน, GPU, ข้อจำกัด | 4 พ.ย. | Wissarut ใช้เขียน README ได้ |

### 🟣 Suphakorn — ระบบ

| เลข | งาน | เมื่อ | เสร็จเมื่อ |
|---|---|---|---|
| **S1** | ลบ `GROQ_*`/`GEMINI_*` จาก `config.py`, `.env.example` (ไฟล์ร่วม → ให้ Chalakorn review) · ใส่ `MODEL_PATH`, `MODEL_BACKEND` แทน | 3 พ.ย. | ไม่มีค่าตั้งของ API ภายนอก |
| **S2** | `model.py`: `generate_sql()` / `model_info()` — เวอร์ชันปลอมก่อน (ส่งให้ Chalakorn ทันที) แล้วโหลดโมเดลจริง (โหลดครั้งเดียว, beam n, คิว 1–2 งาน, โหลดไม่ขึ้น API ยังเริ่มได้) | ปลอม: 3 พ.ย. เช้า · จริง: 3 พ.ย. ค่ำ | ถามผ่านเว็บได้คำตอบจากโมเดล v1 |
| **S3** | `answer.py` แม่แบบคำตอบไทย · `/api/chat` + auth + ตรวจเจ้าของ dataset + บันทึกประวัติ | 3 พ.ย. | เทสต์ 401 / ผู้ใช้อื่นเปิดไม่ได้ ผ่าน |
| **S4** | แก้งานค้างจาก review: หน้าค้างเมื่อ API ล่ม/ช้า (`AppShell`) · อัป `next` ที่มีช่องโหว่ · ข้อความรหัสเดโมไม่ฮาร์ดโค้ด · `smoke.sh` ส่ง token · `CORS_ORIGINS` ว่างต้องไม่ผ่าน | 3–4 พ.ย. | `npm audit` สะอาด · ปิด API แล้วหน้าเว็บบอกให้ลองใหม่ |
| **S5** | หน้า "เกี่ยวกับโมเดล" + หน้าผลการทดสอบ (จาก `GET /api/model`, `GET /api/eval/results` ของ Wissarut) · สถานะรอคำตอบชัดเจน | 4 พ.ย. | แสดงผลจริง |
| **S6** | **เครื่องเดโม:** `make model && docker compose up` บนโน้ตบุ๊กวันสอบ · วัด RAM/เวลาตอบ · ตั้ง `JWT_SECRET`, `DEMO_PASSWORD` ใหม่ · ลองตัดเน็ต | 4 พ.ย. | เปิดเครื่องใหม่แล้วใช้ได้ครบเส้นใน 5 นาที |

### 🟢 Wissarut — วัดผล + คุณภาพ + นำเสนอ

| เลข | งาน | เมื่อ | เสร็จเมื่อ |
|---|---|---|---|
| **W1** | onboarding: อ่าน README, `CONVENTIONS.md` · รันระบบ · ถาม 3 คำถาม | 3 พ.ย. เช้า | รันได้บนเครื่องตัวเอง |
| **W2** | **ชุดทดสอบเขียนด้วยมือ 70 ข้อ 7 หมวด:** ตรวจของเดิม เขียนเพิ่มให้ครบ (ห้ามเปิดดูแม่แบบเทรนใน `ml/templates/`) · ครึ่งหนึ่งบน schema ที่โมเดลไม่เคยเห็น · `--check-gold` ผ่าน | 3 พ.ย. | 70 ข้อ + Chalakorn ช่วยตรวจ SQL เฉลยแบบสุ่ม 10 ข้อ |
| **W3** | `eval/run.py` M0–M3 × set (handwritten / unseen / val) + `eval/report.py` สร้างตาราง Markdown + กราฟ · `routers/eval.py` (`GET /api/eval/results`) | 3 พ.ย. | รันกับผลจำลองได้ |
| **W4** | ทดสอบแบบผู้ใช้: อัปโหลดหลายนามสกุล · ถาม 10 คำถาม · สั่ง "ลบตาราง" · ไฟล์มีคำสั่งแฝง · ถามพร้อมกัน 2 แท็บ → **เปิด issue** ให้เจ้าของไฟล์ | 3 พ.ย. ค่ำ + 4 พ.ย. เช้า | รายการบั๊กครบ |
| **W5** | **eval รอบสุดท้าย** ด้วยโมเดลที่ล็อกแล้ว · วิเคราะห์ข้อผิด 3–5 ตัวอย่าง → `eval/results/failures.md` | 4 พ.ย. บ่าย | ตารางผลจริงพร้อมใส่ README |
| **W6** | README 10 หัวข้อ · `RUNBOOK.md` · `DEMO_SCRIPT.md` (+ คำถามเดโม 5–7 ข้อ ส่งให้ Chalakorn ทำ DEMO_MODE) · ภาพหน้าจอทุกหน้า | 4 พ.ย. | ทำตาม README บนเครื่องใหม่แล้วรันได้จริง |
| **W7** | สไลด์ 12–15 หน้า · อัดคลิปเดโมสำรอง | 4 พ.ย. ค่ำ – 5 พ.ย. เช้า | สไลด์ + คลิปพร้อม |

**ทำไม Wissarut คุมการวัดผล:** คนที่ไม่ได้เทรนโมเดลเป็นคนเขียนข้อสอบและรัน eval ลดโอกาสที่โมเดลถูกปรับให้ตรงกับข้อสอบ — ใช้ตอบอาจารย์ได้ตรง ๆ

---

## 🔗 จุดส่งของ (PR เข้า `dev`)

| เวลา | ใคร → ใคร | ส่งอะไร |
|---|---|---|
| 3 พ.ย. 11:00 | Suphakorn → Chalakorn | `model.py` ปลอม (S2) |
| 3 พ.ย. 12:00 | Wissarut → Chalakorn | ยืนยันรายการ schema ที่ใช้ทดสอบ (ห้ามเข้าข้อมูลเทรน) |
| 3 พ.ย. 18:00 | Chalakorn → Suphakorn | โมเดล v1 (ลิงก์ไฟล์ใน PR) |
| 3 พ.ย. 21:00 | ทุกคน → `dev` | ระบบทำงานครบเส้นด้วยโมเดล v1 ✅ |
| 4 พ.ย. 12:00 | Chalakorn → ทุกคน | 🧊 โมเดลสุดท้าย |
| 4 พ.ย. 12:00 | Wissarut → Chalakorn | คำถามเดโม 5–7 ข้อ |
| 4 พ.ย. 17:00 | Wissarut → Suphakorn | ผล eval จริง (หน้าเว็บ) |
| 4 พ.ย. 20:00 | ทุกคน | 🧊 **code freeze → `dev` → `main` → tag `v1.0`** |

## 📅 ตารางรวม

| เวลา | Chalakorn | Suphakorn | Wissarut |
|---|---|---|---|
| **3 พ.ย. เช้า** | 1.2 push โค้ด · 1.4 · C1 | 1.5 · S2 (ปลอม) | 1.1 · 1.3 · 1.6 · W1 · 1.8 |
| **3 พ.ย. บ่าย** | C1 · C2 (เริ่มเทรน) · C3 | S1 · S3 · S4 | W2 · W3 |
| **3 พ.ย. ค่ำ** | C2 ส่งโมเดล v1 | S2 (จริง) · ต่อโมเดล v1 | W4 |
| **4 พ.ย. เช้า** | C4 → 🧊 โมเดลสุดท้าย · C6 | S4 · S5 · S6 | W4 · W6 |
| **4 พ.ย. บ่าย** | C5 · ช่วยอ่านผล eval | S5 · S6 · แก้บั๊กจาก W4 | **W5** · W6 |
| **4 พ.ย. ค่ำ** | 🧊 code freeze · tag v1.0 | | W7 |
| **5 พ.ย.** | ซ้อม 2 รอบ · ทุกคนอธิบายส่วนของอีก 2 คนได้ | ตรวจเครื่องเดโมรอบสุดท้าย | W7 คลิปสำรอง |
| **6 พ.ย.** | 🎓 | 🎓 | 🎓 |

## 🎤 แบ่งการนำเสนอ
| ส่วน | คนพูด |
|---|---|
| ปัญหา · ทำไมภาษาไทยยาก · ภาพรวม | Wissarut |
| ข้อมูลเทรน · การเทรน · ทำไมไม่ใช่แค่จำแม่แบบ | Chalakorn |
| สถาปัตยกรรม · ความปลอดภัย · **เดโมสด** | Suphakorn |
| ผลการทดลอง · ข้อผิดตัวอย่าง · ข้อจำกัด | Wissarut |
| ปัญหาที่เจอและวิธีแก้ (รวมการเปลี่ยนจาก API เป็นเทรนเอง) | ทุกคน |

---

## ✅ เช็กลิสต์ repo (Wissarut ตรวจในข้อ 1.7 และอีกครั้ง 4 พ.ย. ก่อน freeze)
- [x] ไม่มีการเรียก API ภายนอกหรือค่าตั้ง/ข้อความที่ชวนเข้าใจว่าใช้
- [x] ไม่มีลายน้ำ AI ทั้งใน commit ทุก branch, PR, โค้ด, เอกสาร และไม่มีไฟล์ตั้งค่าเครื่องมือ AI
- [x] ไม่มี `.env`, ไฟล์โมเดล, `data/`, `*.duckdb` ในประวัติ git
- [x] CI 4 job เขียวบน `dev` และ `main` (4 พ.ย. หลัง PR #20)
- [x] CODEOWNERS มี 3 คน · README หัวข้อทีมมี 3 คนพร้อมงาน
- [x] ลิงก์ทุกที่ชี้ไป `github.com/wissarut-29/ThamDi` (README, docs, CONTRACT) ไม่มีลิงก์ repo เก่า
- [x] `docs/STRUCTURE.md`, `TASKS.md`, `CONTRACT.md` ตรงกับของจริง (ตรวจ 4 พ.ย.)
- [ ] ทำตาม README บนเครื่องใหม่แล้วรันได้ตั้งแต่ clone จนถามคำถามได้ — ทางไม่ใช้ Docker ผ่านแล้ว (clone → setup → data → test 133 ผ่าน → smoke ผ่าน) · ทาง Docker รอลองบนเครื่องเดโม (S6)
- [x] มี `MODEL_CARD.md` และ license ของโมเดลตั้งต้น — license Apache 2.0 · เวลาเทรน 136 นาที, Tesla T4 (C6, PR #24)
- [ ] ผล eval มีทั้ง handwritten และ unseen schema · ระบุโมเดล วันที่ เครื่อง — `eval/run.py` เติมชื่อโมเดลและ GPU เองแล้ว · รอผลจริงจาก W5

## ✂️ ถ้าไม่ทัน ตัดตามลำดับ
1. หน้า "เกี่ยวกับโมเดล" → ใส่ใน README/สไลด์
2. M1, M2 → รายงาน M0 กับ M3
3. learning curve → ตัด
4. เดโมนามสกุลไฟล์ → CSV/XLSX
5. `<CLARIFY>` → เหลือ `<REFUSE>`

**ห้ามตัด:** โมเดลที่เทรนเอง · ชุดทดสอบเขียนด้วยมือ + unseen schema · ตัวตรวจ SQL · คำตอบจากแม่แบบ · DEMO_MODE · คลิปสำรอง · ไม่มีลายน้ำ AI
