# Demo Script

เจ้าของ: Wissarut · งาน: W6

## เตรียมก่อนเดโม

```bash
python scripts/make_demo_files.py        # สร้าง data/demo/ (seed ตายตัว คำตอบด้านล่างจะตรงทุกครั้ง)
```

- ไฟล์ที่ใช้: `data/demo/sales_5_branches.xlsx` (ยอดขายรายวัน 5 สาขา ปี 2569, sheet `sales`)
- เครื่องเดโมตั้ง `MODEL_BACKEND=local` และมีโมเดลใน `models/thamdi` แล้ว (ดู [RUNBOOK](RUNBOOK.md))
- เปิดเว็บ http://localhost:3000 ค้างไว้ที่หน้า login

## คำถามเดโม (ส่งให้ Chalakorn ทำ DEMO_MODE · C5)

ถามบนไฟล์ `sales_5_branches.xlsx` (ตาราง `sales`) · คำตอบที่คาดหวังได้จากการรัน SQL เฉลยผ่าน `answer.render()` บนไฟล์ที่ `make_demo_files.py` สร้าง

| # | คำถาม | หมวด | SQL เฉลย | คำตอบที่คาดหวัง |
|---|---|---|---|---|
| 1 | ยอดขายรวมทั้งปีเท่าไหร่ | aggregate | `SELECT SUM(amount) FROM sales` | คำตอบ: 11,566,602 |
| 2 | สาขาไหนขายดีที่สุด | rank | `SELECT branch, SUM(amount) AS total FROM sales GROUP BY branch ORDER BY total DESC LIMIT 1` | บางนา 3,068,557 |
| 3 | ยอดขายแต่ละหมวดสินค้าเท่าไหร่ | group | `SELECT category, SUM(amount) AS total FROM sales GROUP BY category ORDER BY total DESC` | อาหาร 4,727,032 · เบเกอรี่ 3,522,740 · เครื่องดื่ม 3,316,830 |
| 4 | เดือนมีนาคม 2569 สาขาบางนาขายได้เท่าไหร่ | thai_date | `SELECT SUM(amount) FROM sales WHERE branch = 'บางนา' AND sale_date BETWEEN '2026-03-01' AND '2026-03-31'` | คำตอบ: 265,479 |
| 5 | สินค้า 3 อันดับแรกที่ขายได้จำนวนชิ้นมากที่สุด | rank | `SELECT product, SUM(quantity) AS total FROM sales GROUP BY product ORDER BY total DESC LIMIT 3` | ชาไทย 20,753 · ขนมปังสังขยา 20,679 · ข้าวกะเพราไก่ 20,637 |
| 6 | กาแฟเย็นขายได้กี่แก้วที่สาขาเชียงใหม่ | filter | `SELECT SUM(quantity) FROM sales WHERE product = 'กาแฟเย็น' AND branch = 'เชียงใหม่'` | คำตอบ: 3,252 |
| 7 | ลบตารางยอดขายทิ้งให้หน่อย | refuse | `<REFUSE>` | ปฏิเสธ (ระบบอ่านข้อมูลได้อย่างเดียว) |

ข้อ 5 อันดับ 2 กับ 3 ห่างกันแค่ 42 ชิ้น ถ้าโมเดลจริงตอบผิดบ่อยข้อนี้ให้ตัดออก

## ลำดับการเดโม (ประมาณ 5 นาที)

| ขั้น | คนพูด | ทำอะไรบนจอ |
|---|---|---|
| 1 | Wissarut | เล่าปัญหา: เจ้าของร้านมีไฟล์ Excel แต่เขียน SQL ไม่เป็น และไม่อยากส่งข้อมูลร้านออกไปข้างนอก |
| 2 | Suphakorn | login `demo` → อัปโหลด `sales_5_branches.xlsx` → ชี้ว่าได้ตาราง `sales` |
| 3 | Suphakorn | ถามข้อ 1, 2, 3 → ชี้คำตอบภาษาไทย, SQL ที่โมเดลสร้าง, ตารางผล |
| 4 | Suphakorn | ถามข้อ 4 (วันที่แบบไทย พ.ศ.) → ชี้ว่า SQL แปลงเป็น `2026-03-01` ให้เอง |
| 5 | Suphakorn | ถามข้อ 7 → ระบบปฏิเสธ · อธิบาย `sql_guard` และ dataset เปิดแบบ read-only |
| 6 | Chalakorn | เปิดหน้า "เกี่ยวกับโมเดล" → โมเดลตั้งต้น, ข้อมูลเทรน, รันในเครื่อง |
| 7 | Wissarut | เปิดหน้าผลการทดสอบ → ผล M0–M3 บนชุดเขียนด้วยมือ และ schema ที่โมเดลไม่เคยเห็น |

ข้อ 5–6 ในตารางคำถามสำรองไว้ถ้ามีเวลาเหลือ หรือกรรมการขอให้ถามเพิ่ม

## แผนสำรอง

- โมเดลโหลดไม่ขึ้น / ตอบช้าเกิน: ตั้ง `DEMO_MODE=true` แล้ว restart API (คำถามข้างบนตอบจาก `eval/demo_answers.json`)
- เครื่องเดโมพัง: เปิดคลิปสำรอง (W7)
- กรรมการถามคำถามนอกชุด: ถามได้ปกติถ้าโมเดลรันอยู่ ถ้าอยู่ใน DEMO_MODE จะตอบว่าคำถามไม่อยู่ในคำถามเดโม
