# บันทึกปัญหาที่เจอ (Chalakorn)

รูปแบบ: ปัญหา | ต้นเหตุ | แก้อย่างไร | ก่อน → หลัง

## 1. GNU grep จับอิโมจิไม่เจอเฉพาะตอน git เรียก hook (บน Windows)

- **ปัญหา:** `scripts/hooks/commit-msg` ตรวจอิโมจิหุ่นยนต์ (โค้ดพอยต์ U+1F916) ไม่เจอ ตอน git เรียกเป็น
  hook จริง แต่รันเองจากเทอร์มินัลเจอปกติ
- **ต้นเหตุ:** Git for Windows ตั้ง `LC_CTYPE=C.UTF-8` ให้ hook subprocess ทำให้ GNU grep สลับไปใช้โหมด
  wide-char matching ซึ่งพังกับโค้ดพอยต์เกิน U+FFFF บน Windows เพราะ `wchar_t`
  มีแค่ 16 บิต ส่วนภาษาไทย/ASCII ไม่กระทบเพราะอยู่ใน BMP
- **แก้อย่างไร:** เพิ่ม `export LC_ALL=C` ที่หัวทั้งสอง hook บังคับ grep จับคู่แบบไบต์เสมอ
- **ก่อน → หลัง:** บล็อกไม่ได้เมื่อ commit ผ่าน git จริง (ทดสอบตรงผ่านหลอก) → บล็อกถูกทุกกรณี ทดสอบซ้ำ 13 เคสผ่านหมด

## 2. สคริปต์ hook พังถ้า checkout บน Windows ที่ตั้ง core.autocrlf=true

- **ปัญหา:** `git add` เตือนว่า hook scripts จะถูกแปลงเป็น CRLF ตอน checkout ครั้งถัดไป ซึ่งจะทำให้ shebang
  `#!/bin/sh` พังบน macOS/Linux (`/bin/sh^M: bad interpreter`)
- **ต้นเหตุ:** ไม่มี `.gitattributes` บังคับ line ending ให้ shell script
- **แก้อย่างไร:** เพิ่ม `.gitattributes` ตั้ง `scripts/hooks/* text eol=lf`
- **ก่อน → หลัง:** เสี่ยงพังบน Windows ที่ autocrlf=true → บังคับ LF เสมอไม่ว่า OS ไหน

## 3. gen_join สร้าง SQL join ซ้ำตารางเดิม (ambiguous reference)

- **ปัญหา:** `ml/gen_data.py` สร้างคำถามหมวด join ของ restaurant/warehouse แล้ว SQL รันไม่ผ่าน DuckDB
  (ambiguous reference to table "menu_items"/"items")
- **ต้นเหตุ:** `measure_join` ของบาง schema (restaurant, warehouse) join ไปถึง dim2 อยู่แล้วตั้งแต่แรก
  (เพราะ measure_expr ต้องใช้คอลัมน์จาก dim2) แล้ว `gen_join` ไป join dim2 ซ้ำอีกรอบ
- **แก้อย่างไร:** เช็กว่าชื่อตาราง dim2 อยู่ใน measure_join แล้วหรือยัง ก่อน join ซ้ำ
- **ก่อน → หลัง:** หมวด join ตก 400-600 ข้อจาก 1000 (รันไม่ผ่าน DuckDB) → ตก 0 ข้อ

## 4. agent/model.py ของ Suphakorn ยังเป็น NotImplementedError จริง (ไม่ใช่ปลอม)

- **ปัญหา:** `python eval/run.py --predictor pipeline --modes M0 M3` รันไม่จบ เพราะ `generate_sql()` raise
  NotImplementedError จริง ไม่ใช่เวอร์ชันปลอมที่ CONTRACT.md ระบุว่าควรมีตั้งแต่ 3 พ.ย. 11:00
- **ต้นเหตุ:** S2 (เวอร์ชันปลอมของ model.py) ยังไม่ถูก push เข้า `origin/dev` ตอนที่เช็ก (เช็กแล้ว 2 รอบในวันนี้)
- **แก้อย่างไร:** พิสูจน์ pipeline.py เชื่อมกับ eval/run.py ได้จริงด้วยการ monkeypatch `generate_sql`
  ชั่วคราวในหน่วยความจำ (ไม่แก้ไฟล์จริง) แล้วรันผ่านสำเร็จทั้ง M0 และ M3 — ของจริงรอ Suphakorn ส่ง S2
- **ก่อน → หลัง:** ยืนยันไม่ได้ว่า pipeline ต่อกับ eval ได้จริงจนกว่ามี model.py ปลอม → ยืนยันแล้วว่าต่อกันได้
  (รอแค่ของจริงมาแทน stub)

## 5. ยังไม่มีฟังก์ชันเปิด dataset ใน docs/CONTRACT.md

- **ปัญหา:** `pipeline.run(question, dataset_id, mode)` ต้องได้ schema DDL + การเชื่อมต่อฐานข้อมูลของ
  dataset นั้นจากฝั่งระบบ แต่ CONTRACT.md ยังไม่นิยามฟังก์ชันนี้
- **ต้นเหตุ:** ยังไม่มีการตกลงรูปแบบฟังก์ชันระหว่าง Chalakorn กับ Suphakorn
- **แก้อย่างไร:** ทำ stub `get_dataset(dataset_id)` ใน `pipeline.py` raise NotImplementedError ไว้ก่อน
  เทสต์ monkeypatch แทน และร่างข้อเสนอฟังก์ชันส่งให้ Suphakorn แล้ว (ดูสรุปจบ session)
- **ก่อน → หลัง:** `run()` เขียนไม่ได้เลยเพราะไม่รู้จะเปิด dataset ยังไง → เขียน+เทสต์ได้ครบ รอแค่เสียบ
  ฟังก์ชันจริงจาก Suphakorn
