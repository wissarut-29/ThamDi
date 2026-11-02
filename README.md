# ThamDi

## วิธีทำงานร่วมกัน

### Branch หลัก

- **`main`** = เวอร์ชันที่ใช้งานได้ สำหรับเดโม/ส่งงาน รับ merge จาก `develop` เท่านั้น
- **`develop`** = branch ที่ทุกคนทำงานร่วมกัน (เป็น default branch ของ repo)

### กฎ

- งานหนึ่งอย่างต่อหนึ่ง branch แตกจาก `develop` ตั้งชื่อแบบ `<ชื่อเล่น>/<เรื่องที่ทำ>`
  - ใช้ตัวพิมพ์เล็กภาษาอังกฤษ คั่นคำด้วย `-`
  - ตัวอย่าง: `peem/login-page`, `supawit/fix-navbar`
- ทำเสร็จแล้ว push branch แล้วเปิด Pull Request เข้า `develop`
- พอ `develop` พร้อม ค่อยเปิด Pull Request จาก `develop` เข้า `main`
- ห้าม push ตรงเข้า `main` หรือ `develop`
- ห้าม commit ไฟล์ `.env` (repo นี้เป็น public ทุกคนเห็นได้)

### ตัวอย่างคำสั่ง

```bash
git clone https://github.com/wissarut-29/ThamDi.git
cd ThamDi
git switch develop
git pull
git switch -c peem/login-page
# ... เขียนโค้ด ...
git add . && git commit -m "เพิ่มหน้า login"
git push -u origin peem/login-page
# แล้วเปิด Pull Request เข้า develop บน GitHub
```
