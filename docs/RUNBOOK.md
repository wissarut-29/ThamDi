# Runbook

เจ้าของ: Suphakorn · งาน: S-10 (TASKS v3)

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
1. ดาวน์โหลดโมเดล (ลิงก์ใน `docs/MODEL_CARD.md`) ไว้ที่ `models/thamdi`:
   `MODEL_URL=<ลิงก์ .zip> sh scripts/tasks.sh model`
2. แก้ `.env`: `MODEL_BACKEND=local`
3. Docker: `INSTALL_MODEL=1 docker compose up --build -d` · รันตรง: `pip install -r services/api/requirements-model.txt` แล้ว `sh scripts/tasks.sh dev`
4. เช็กที่หน้า "เกี่ยวกับโมเดล" ว่าสถานะ "โหลดแล้ว" (ระหว่างโหลด API ใช้งานได้ แต่ตอบว่าโมเดลยังไม่พร้อม)

**ห้ามดาวน์โหลดโมเดลในห้องสอบ** — วางไฟล์ไว้ใน `models/` ก่อนวันสอบ

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
| login ไม่ผ่านทั้งที่รหัสถูก | แก้ `DEMO_PASSWORD` แล้วต้อง restart API (รหัสถูกตั้งตอนเริ่ม) |
| `ports are not available` / port 3000 หรือ 8000 ถูกใช้ | ปิดโปรแกรมที่ใช้ port นั้น (เช่น `npm run dev` ที่ค้างไว้) แล้ว `docker compose up -d` ใหม่ |
| หน้าเกี่ยวกับโมเดลขึ้น "ยังไม่พร้อม" นาน | ไม่มีไฟล์ใน `models/thamdi` หรือ RAM ไม่พอ → ดู log: `docker compose logs api` · ใช้ `DEMO_MODE=true` ระหว่างนั้น |
| ตอบช้ามาก (> 5 วินาทีต่อข้อ บน CPU) | รันตรงบนเครื่องที่มี GPU (ติดตั้ง torch แบบ CUDA ตาม pytorch.org) · Docker + GPU บน Windows ต้อง WSL2 |
| `pip install` ขึ้น `UnicodeDecodeError` | ใช้ requirements ล่าสุดจาก repo (ไฟล์ต้องเป็น ASCII) |
| `sh: ... $'\r'` ตอนรัน `.sh` | ไฟล์ถูกแปลงเป็น CRLF → `git rm --cached -r . && git reset --hard` (มี `.gitattributes` บังคับ LF แล้ว) |
| curl ส่งภาษาไทยแล้ว API ตอบ 400 | บน Windows ให้ส่ง JSON ผ่านไฟล์: `--data-binary @q.json` (ดู `scripts/smoke.sh`) |
