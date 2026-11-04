# Runbook

เจ้าของ: Wissarut + Suphakorn (ดูแลร่วม) · งาน: W6 · เนื้อหาฝั่งระบบ: Suphakorn

วิธีติดตั้งและรันระบบบนเครื่องใหม่ ตั้งแต่ clone จนถามคำถามได้ และวิธีแก้ปัญหาที่พบบ่อยวันเดโม
คำสั่งทั้งหมดรันใน **Git Bash** (Windows) หรือ terminal (macOS/Linux) ที่ root ของ repo

## ติดตั้ง

```bash
git clone https://github.com/wissarut-29/ThamDi.git && cd ThamDi
cp .env.example .env
```
แก้ `.env` อย่างน้อย 2 ค่า: `JWT_SECRET` (สุ่มยาว ๆ) และ `DEMO_PASSWORD` (รหัสผู้ใช้ `demo`)

### ทางที่ 1: Docker (แนะนำสำหรับเครื่องเดโม)
ต้องมี Docker Desktop
```bash
docker compose up --build -d
```
เว็บ http://localhost:3000 · API http://localhost:8000 · ปิด: `docker compose down`

### ทางที่ 2: รันตรง (ถ้า Docker มีปัญหา)
ต้องมี Python 3.10+ และ Node 20+
```bash
python -m venv .venv && source .venv/Scripts/activate   # macOS/Linux: .venv/bin/activate
sh scripts/tasks.sh setup        # ติดตั้งไลบรารี API + eval
sh scripts/tasks.sh dev          # API ที่ :8000 (ค้างหน้าต่างนี้ไว้)
```
อีกหน้าต่าง:
```bash
cd apps/web && npm ci && npm run dev    # เว็บที่ :3000
```
เครื่องที่มี `make` ใช้ `make setup`, `make dev` แทนได้

## ใช้โมเดลจริง
ค่าเริ่มต้น `MODEL_BACKEND=fake` (SQL ตายตัว ไว้ทดสอบระบบ) · ใช้โมเดลที่ทีมเทรน:
1. ดาวน์โหลดโมเดล (ลิงก์ใน `docs/MODEL_CARD.md`) ไว้ที่ `models/thamdi` เลือกทางใดทางหนึ่ง:
   - **ลิงก์ zip ดาวน์โหลดตรง:** `MODEL_URL=<ลิงก์ .zip> sh scripts/tasks.sh model`
   - **ลิงก์เป็นโฟลเดอร์ Google Drive** (`curl` โหลดโฟลเดอร์ไม่ได้):
     1. เปิดลิงก์ใน browser → คลิกขวาที่ชื่อโฟลเดอร์ → ดาวน์โหลด (Drive จะบีบเป็น `.zip` ให้ ~1 GB)
     2. ส่ง zip ที่โหลดมาให้สคริปต์ (ไม่ต้องแตกเอง สคริปต์ย้ายของในโฟลเดอร์ชั้นบนขึ้นมาให้):
        ```bash
        MODEL_URL="file:///C:/Users/<ชื่อ>/Downloads/<ชื่อไฟล์>.zip" sh scripts/tasks.sh model
        ```
     3. ถ้า Drive แบ่งเป็นหลาย zip ให้แตกทุกไฟล์รวมกันเองไว้ที่ `models/thamdi/` ให้มี `config.json` และ `model.safetensors` อยู่ชั้นบนสุด
   - เช็กว่าได้ครบ: `ls models/thamdi` ต้องเห็น `config.json`, `model.safetensors`, `tokenizer.json` (หรือ `tokenizer_config.json`)
2. แก้ `.env`: `MODEL_BACKEND=local`
3. Docker: `INSTALL_MODEL=1 docker compose up --build -d` · รันตรง: `pip install -r services/api/requirements-model.txt` แล้ว `sh scripts/tasks.sh dev`
4. เช็กที่หน้า "เกี่ยวกับโมเดล" ว่าสถานะ "โหลดแล้ว" (ระหว่างโหลด API ใช้งานได้ แต่ตอบว่าโมเดลยังไม่พร้อม)

**ห้ามดาวน์โหลดโมเดลในห้องสอบ** — วางไฟล์ไว้ใน `models/` ก่อนวันสอบ

ผลวัดโมเดล v1 (Qwen2.5-0.5B fp16) บนเครื่องพัฒนา 4 พ.ย. ผ่าน `model.py` เส้นทางเดียวกับ API:

| | โหลดครั้งแรก | M0 (beam 1) เฉลี่ย / สูงสุด | M3 (beam 4) เฉลี่ย / สูงสุด | หน่วยความจำ |
|---|---|---|---|---|
| GPU RTX 4060 | ~16 วินาที | 0.8 / 1.4 วินาที | 0.8 / 1.5 วินาที | RAM ~1.2 GB · VRAM ~1 GB |
| CPU อย่างเดียว | ~11 วินาที | 1.6 / 3.2 วินาที | 2.4 / 4.3 วินาที | RAM ~2.7 GB |

ไม่มี GPU ก็ยังตอบได้ภายในเกณฑ์ 5 วินาทีต่อข้อ · ถามผ่านเว็บ/API จริงใช้ 0.2–1.3 วินาทีต่อข้อบน GPU

## ตรวจว่าใช้ได้
```bash
sh scripts/tasks.sh test                                   # ruff + pytest + ตรวจชุดทดสอบ
API_URL=http://localhost:8000 DEMO_PASSWORD=<รหัสใน .env> sh scripts/smoke.sh
```
`smoke.sh` ต้องจบด้วย `smoke: ผ่านทุกขั้น` (401 → login → อัปโหลด → chat → ข้อมูลโมเดล)

ด้วยมือ: เปิด http://localhost:3000 → login `demo` → อัปโหลด .csv/.xlsx → ถาม "มีกี่สาขา" → ได้คำตอบ + SQL + ตาราง

## ปัญหาที่พบบ่อย
| อาการ | วิธีแก้ |
|---|---|
| หน้าเว็บขึ้น "ติดต่อเซิร์ฟเวอร์ไม่ได้" | API ไม่ได้รัน → `docker compose ps` หรือเปิด `sh scripts/tasks.sh dev` ใหม่ · เช็ก `CORS_ORIGINS=http://localhost:3000` ใน `.env` |
| login ไม่ผ่านทั้งที่รหัสถูก | แก้ `DEMO_PASSWORD` แล้วต้อง restart API (รหัสถูกตั้งตอนเริ่ม) · ถ้า `MODEL_BACKEND=local` แต่ `DEMO_PASSWORD` ยังเป็น `change-me` หรือว่าง ระบบจะไม่สร้างผู้ใช้ demo เลย (ดู log ของ API) |
| login แล้วหลุดทุกครั้งที่ restart API | `JWT_SECRET` ยังเป็น `change-me` ระบบจึงสุ่ม secret ใหม่ทุกครั้งที่เริ่ม → ตั้ง `JWT_SECRET` ใน `.env` |
| `ports are not available` / port 3000 หรือ 8000 ถูกใช้ | ปิดโปรแกรมที่ใช้ port นั้น (เช่น `npm run dev` ที่ค้างไว้) แล้ว `docker compose up -d` ใหม่ |
| หน้าเกี่ยวกับโมเดลขึ้น "ยังไม่พร้อม" นาน | ไม่มีไฟล์ใน `models/thamdi` หรือ RAM ไม่พอ → ดู log: `docker compose logs api` · ใช้ `DEMO_MODE=true` ระหว่างนั้น |
| ตอบช้ามาก (> 5 วินาทีต่อข้อ บน CPU) | รันตรงบนเครื่องที่มี GPU (ติดตั้ง torch แบบ CUDA ตาม pytorch.org) · Docker + GPU บน Windows ต้อง WSL2 |
| `pip install` ขึ้น `UnicodeDecodeError` | ใช้ requirements ล่าสุดจาก repo (ไฟล์ต้องเป็น ASCII) |
| `UnicodeEncodeError: 'charmap'` ตอนรันสคริปต์ python (เช่น `make_demo_files.py`) บน Windows | terminal ไม่ใช่ UTF-8 → `export PYTHONUTF8=1` (Git Bash) หรือ `$env:PYTHONUTF8=1` (PowerShell) แล้วรันใหม่ · ไฟล์ที่สร้างแล้วไม่เสีย |
| `sh: ... $'\r'` ตอนรัน `.sh` | ไฟล์ถูกแปลงเป็น CRLF → `git rm --cached -r . && git reset --hard` (มี `.gitattributes` บังคับ LF แล้ว) |
| curl ส่งภาษาไทยแล้ว API ตอบ 400 | บน Windows ให้ส่ง JSON ผ่านไฟล์: `--data-binary @q.json` (ดู `scripts/smoke.sh`) |
