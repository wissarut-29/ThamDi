# apps/web/ — เว็บ

เจ้าของ: Suphakorn (S4, S5/S-07) · Next.js (App Router, JavaScript)

## หน้า
- `/` เข้าสู่ระบบ (ผู้ใช้ `demo` รหัสจาก `DEMO_PASSWORD` ใน `.env` ของ API)
- `/chat` เลือก/อัปโหลด dataset (.csv .tsv .txt .xlsx .xls .ods .json) · ถามเป็นภาษาไทย · แสดงสถานะ คำตอบ SQL และตาราง
- `/model` ข้อมูลโมเดล (`GET /api/model`) + ผลการทดสอบ (`GET /api/eval/results`) · ถ้ายังไม่มีผลจริงจะแสดงผลจำลองพร้อมคำเตือน

## รัน
```bash
npm ci
npm run dev        # http://localhost:3000
```
URL ของ API ตั้งด้วย `NEXT_PUBLIC_API_URL` (ค่าเริ่มต้น `http://localhost:8000`) · ฝั่ง API ต้องมี `CORS_ORIGINS=http://localhost:3000`

## ความทนทาน
ทุก request มี timeout (chat 120 วินาที ที่เหลือ 15 วินาที) · API ล่มหรือช้า หน้าเว็บบอกให้ลองใหม่ ไม่ค้าง · token หมดอายุกลับหน้า login
