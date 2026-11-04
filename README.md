# ThamDi

ถามข้อมูลในตารางด้วยภาษาไทย โมเดลที่เทรนเองแปลงคำถามเป็น SQL แล้วตอบกลับเป็นภาษาไทย ทั้งหมดรันในเครื่อง ไม่ใช้ API ภายนอก

## 1. ThamDi คืออะไร

เจ้าของร้านเล็ก ๆ มีข้อมูลอยู่ใน Excel/CSV (ยอดขาย, ค่าไฟ, พนักงาน) แต่เขียน SQL ไม่เป็น และไม่อยากส่งข้อมูลร้านไปให้บริการภายนอก ThamDi ให้อัปโหลดไฟล์แล้วพิมพ์ถามเป็นภาษาไทย เช่น "เดือนมีนาคม 2569 สาขาบางนาขายได้เท่าไหร่" ระบบจะ

1. แปลงคำถามเป็น SQL ด้วยโมเดลที่ทีม fine-tune เอง
2. ตรวจว่า SQL อ่านข้อมูลได้อย่างเดียว แล้วรันกับไฟล์ของผู้ใช้
3. ตอบเป็นประโยคภาษาไทยจากผลที่รันได้จริง พร้อมแสดง SQL และตาราง

ตัวเลขในคำตอบมาจากการรัน SQL เท่านั้น โมเดลไม่ได้แต่งคำตอบเอง

## 2. ทีม

| | GitHub | บทบาท | branch | แผนงาน |
|---|---|---|---|---|
| Chalakorn | @fffalafair | โมเดล | `feat/chalakorn` | [docs/tasks/chalakorn.md](docs/tasks/chalakorn.md) |
| Suphakorn | @SoSick41 | ระบบ | `feat/suphakorn` | [docs/tasks/suphakorn.md](docs/tasks/suphakorn.md) |
| Wissarut | @wissarut-29 | วัดผล + คุณภาพ + นำเสนอ · เจ้าของ repo | `feat/wissarut` | [docs/tasks/wissarut.md](docs/tasks/wissarut.md) |

## 3. ภาพรวมระบบ

```
เว็บ (Next.js, apps/web)
  │  login · อัปโหลดไฟล์ตาราง (.csv/.xlsx/.xls/.ods/.tsv/.txt/.json) · ถาม
  ▼
API (FastAPI, services/api)
  ├─ ingest.py      อ่านไฟล์ → ตาราง DuckDB (1 ไฟล์ต่อ dataset, เปิดแบบ read-only)
  ├─ preprocess.py  แปลงวันที่ไทย/พ.ศ. → สร้าง prompt จากคำถาม + ชื่อตาราง/คอลัมน์ (ไม่ใส่ค่าในเซลล์)
  ├─ model.py       โมเดลที่เทรนเอง สร้าง SQL 4 แบบ (beam search)
  ├─ sql_guard.py   ผ่านเฉพาะ SELECT ตารางของ dataset นั้น ห้ามแก้/ลบ/อ่านไฟล์
  ├─ pipeline.py    เลือก SQL แบบแรกที่ผ่าน guard และลองรัน (EXPLAIN) ได้ → รันจริง
  └─ answer.py      เขียนคำตอบภาษาไทยจากแม่แบบ
```

โหมดที่ใช้วัดผล: **M0** โมเดลอย่างเดียว → **M1** + แปลงวันที่ไทย → **M2** + beam 4 และ sql_guard → **M3** + ลองรันก่อนเลือก (ระบบจริงใช้ M3) รายละเอียดใน [docs/CONTRACT.md](docs/CONTRACT.md)

## 4. ติดตั้งและรัน

```bash
git clone https://github.com/wissarut-29/ThamDi.git && cd ThamDi
cp .env.example .env      # แก้ JWT_SECRET และ DEMO_PASSWORD
docker compose up --build -d
```

เปิด http://localhost:3000 แล้ว login ด้วยผู้ใช้ `demo` และรหัส `DEMO_PASSWORD` ใน `.env`

- ค่าเริ่มต้นใช้โมเดลปลอม (`MODEL_BACKEND=fake`) ไว้ทดสอบระบบ วิธีใช้โมเดลจริงอยู่ใน [docs/RUNBOOK.md](docs/RUNBOOK.md) หัวข้อ "ใช้โมเดลจริง"
- รันแบบไม่ใช้ Docker, ตรวจว่าระบบใช้ได้ (`scripts/smoke.sh`) และวิธีแก้ปัญหาที่พบบ่อย ดู [docs/RUNBOOK.md](docs/RUNBOOK.md)
- Windows ไม่มี `make` ใช้ `sh scripts/tasks.sh <setup|data|test|model|dev>` แทน

## 5. วิธีใช้

1. login → หน้า "ถามข้อมูล"
2. อัปโหลดไฟล์ตาราง `.csv` `.xlsx` `.xls` `.ods` `.tsv` `.txt` หรือ `.json` ไม่เกิน 10 MB (Excel/ODS ได้ 1 ตารางต่อ sheet · CSV ภาษาไทยที่เซฟเป็น cp874 หรือ "Unicode Text" ก็อ่านได้ · เดาตัวคั่น , ; tab | ให้เอง)
3. พิมพ์คำถาม เช่น "สาขาไหนขายดีที่สุด", "ยอดขายแต่ละหมวดสินค้าเท่าไหร่", "เดือนมีนาคม 2569 สาขาบางนาขายได้เท่าไหร่"
4. ได้คำตอบภาษาไทย · กด "SQL ที่ระบบรันจริง" เพื่อดู SQL · ผลหลายแถวแสดงเป็นตาราง (สูงสุด 1,000 แถว)
5. คำสั่งแก้/ลบข้อมูล หรือคำถามที่ตอบจากไฟล์ไม่ได้ ระบบจะปฏิเสธ

ไฟล์ตัวอย่างสำหรับลอง: `python scripts/make_demo_files.py` (สร้างใน `data/demo/`) · คำถามเดโมดู [docs/DEMO_SCRIPT.md](docs/DEMO_SCRIPT.md)

## 6. โมเดล

- โมเดลตั้งต้น **Qwen2.5-0.5B-Instruct** (Apache 2.0) fine-tune ด้วย LoRA บน Colab
- ข้อมูลเทรนสร้างจากแม่แบบ 7 หมวด (filter, aggregate, group, rank, join, thai_date, refuse) บน 5 schema ทุก SQL รันผ่าน DuckDB ก่อนเก็บ
- schema `clinic`, `library` (ชุดทดสอบ) และ `school` (val) ไม่อยู่ในข้อมูลเทรน
- ตอนใช้งาน prompt มีแค่คำถามกับชื่อตาราง/คอลัมน์/ชนิดข้อมูล ไม่มีค่าในเซลล์

รายละเอียด ขนาด เวลาเทรน และลิงก์ดาวน์โหลด: [docs/MODEL_CARD.md](docs/MODEL_CARD.md)

## 7. ความปลอดภัยและความเป็นส่วนตัว

- รันในเครื่องทั้งหมด ไม่เรียก API ภายนอก ไฟล์ที่อัปโหลดอยู่ใน `data/` ของเครื่องนั้น
- dataset เปิดแบบ read-only และปิดการอ่านไฟล์/เน็ตจาก SQL (`enable_external_access=false`)
- `sql_guard` ใช้ sqlglot แยกวิเคราะห์ SQL ทั้งต้นไม้: ผ่านเฉพาะ SELECT คำสั่งเดียว อ้างได้เฉพาะตารางของ dataset นั้น ห้าม DDL/DML/ATTACH/COPY และฟังก์ชันอ่านไฟล์ เติม `LIMIT 1000` ให้
- ต้อง login (JWT) ทุก endpoint ผู้ใช้เห็นแค่ dataset ของตัวเอง · จำกัดจำนวนคำขอ login/chat/อัปโหลด
- ค่าในเซลล์ไม่ถูกส่งเข้า prompt ข้อความแฝงในไฟล์จึงสั่งโมเดลไม่ได้ (ทดสอบแล้วใน [W4](eval/results/w4_user_test.md))

## 8. ผลการทดสอบ

วัดด้วย [eval/](eval/README.md) แบบ execution accuracy (รัน SQL ของโมเดลกับ SQL เฉลยบนข้อมูลเดียวกัน แล้วเทียบผล) ทุกโหมด M0–M3 บน 4 ชุด:

| ชุด | จำนวน | คืออะไร |
|---|---|---|
| handwritten | 70 ข้อ 7 หมวด | เขียนด้วยมือโดยคนที่ไม่ได้เทรนโมเดล และไม่เปิดดูแม่แบบเทรน |
| unseen | 35 ข้อ (ในชุด handwritten) | บน schema ที่โมเดลไม่เคยเห็น (`clinic`, `library`) |
| val | 205 ข้อ | export จากตัวสร้างข้อมูลของทีมโมเดล |
| val_unseen | 33 ข้อ (ในชุด val) | ข้อ val บน schema ที่ไม่ได้ใช้เทรน |

**ผลจริงรอโมเดลสุดท้าย (W5)** ตารางและกราฟจะอยู่ที่ `eval/results/latest_report.md` และหน้า "เกี่ยวกับโมเดล" บนเว็บ ส่วน `eval/results/simulated*` เป็นผลจำลองไว้ทดสอบระบบ ไม่ใช่ผลของโมเดล

## 9. ข้อจำกัด

- โมเดลขนาด 0.5B บน CPU ตอบข้อละหลายวินาที และรับได้ทีละ 1 คำถาม (คนที่รอเกิน 10 วินาทีจะได้ข้อความให้ลองใหม่)
- ข้อมูลเทรนสร้างจากแม่แบบ ประโยคที่ต่างจากแม่แบบมากหรือคำถามซับซ้อน (หลายขั้น, subquery) อาจตอบผิด
- ไม่มีบทสนทนาต่อเนื่อง แต่ละคำถามตอบแยกกัน
- รับเฉพาะไฟล์ที่เป็นตาราง (.csv .tsv .txt .xlsx .xls .ods .json) ไม่เกิน 10 MB และ 200,000 แถว · ยังไม่รับ PDF, Word, รูปภาพ หรือเอกสารที่เป็นข้อความ เพราะโมเดลแปลงคำถามเป็น SQL จึงต้องมีตารางให้รัน
- ชื่อคอลัมน์ภาษาอังกฤษ snake_case ได้ผลดีที่สุด เพราะข้อมูลเทรนใช้รูปแบบนี้

## 10. เอกสารและการทำงานร่วมกัน

| ไฟล์ | อ่านเมื่อ |
|---|---|
| [docs/RUNBOOK.md](docs/RUNBOOK.md) | ติดตั้ง รัน และแก้ปัญหาวันเดโม |
| [docs/DEMO_SCRIPT.md](docs/DEMO_SCRIPT.md) | ลำดับการเดโมและคำถามเดโม |
| [docs/MODEL_CARD.md](docs/MODEL_CARD.md) | รายละเอียดโมเดลและข้อมูลเทรน |
| [docs/TASKS.md](docs/TASKS.md) | ใครทำอะไร ส่งอะไรให้ใคร เมื่อไหร่ |
| [docs/CONTRACT.md](docs/CONTRACT.md) | จะเรียกใช้ส่วนของคนอื่น (ฟังก์ชัน, API, รูปแบบไฟล์) |
| [docs/STRUCTURE.md](docs/STRUCTURE.md) | หาว่าไฟล์ไหนอยู่ไหน และใครเป็นเจ้าของ |
| [docs/CONVENTIONS.md](docs/CONVENTIONS.md) | กฎ branch, commit และสิ่งที่ห้ามทำ |

### วิธีทำงานร่วมกัน

- **`main`** = เวอร์ชันที่ใช้งานได้ สำหรับเดโม/ส่งงาน รับ merge จาก `dev` เท่านั้น
- **`dev`** = branch ที่ทุกคนทำงานร่วมกัน (default branch)
- แต่ละคนทำงานใน `feat/<ชื่อ>` ของตัวเอง เสร็จเป็นชิ้น ๆ ก็ push แล้วเปิด Pull Request เข้า `dev`
- ห้าม push ตรงเข้า `main` หรือ `dev` · PR ต้องผ่าน CI 4 job (`api`, `eval-gold`, `web`, `no-ai-watermark`) ก่อน merge
- ห้าม commit `.env`, ไฟล์โมเดล หรือข้อมูล (repo นี้เป็น public ทุกคนเห็นได้)
- ห้ามมีลายน้ำ AI ใน commit, PR, โค้ด และเอกสาร · ตั้ง hook ครั้งแรก: `git config core.hooksPath scripts/hooks`

```bash
git switch feat/<ชื่อ>
cp .env.example .env
# ... เขียนโค้ด ...
git add <ไฟล์ที่แก้> && git commit -m "เพิ่ม sql_guard"
git push
# แล้วเปิด Pull Request จาก feat/<ชื่อ> เข้า dev บน GitHub
```

ดึงงานของคนอื่นที่เข้า `dev` แล้วมารวมใน branch ตัวเอง:

```bash
git fetch origin
git merge origin/dev
```
