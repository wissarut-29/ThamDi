"use client";

import AppShell from "../../components/AppShell";

// แผนภาพนิ่งตามเส้นทางจริงของ /api/chat (routers/chat.py → agent/pipeline.py run() โหมด M3)
const STEPS = [
  {
    title: "คำถามภาษาไทย",
    where: "หน้าเว็บ → POST /api/chat",
    body: "ผู้ใช้พิมพ์คำถามตามที่พูดกันปกติ ระบบรับเฉพาะ dataset ที่ผู้ใช้คนนั้นอัปโหลดเอง",
    example: "เดือนมีนาคม 2569 สาขาบางนาขายได้เท่าไหร่",
  },
  {
    title: "แปลงวันที่ไทย",
    where: "thai_dates.py",
    body: "ชื่อเดือนไทยและปี พ.ศ. ในคำถามถูกแปลงเป็นวันที่แบบที่ฐานข้อมูลเข้าใจ แล้วต่อกับโครงตารางเป็น prompt แบบเดียวกับตอนเทรน",
    example: "มีนาคม 2569 → 2026-03-01 ถึง 2026-03-31",
  },
  {
    title: "โมเดลสร้าง SQL",
    where: "model.py · รันในเครื่องนี้",
    body: "โมเดลที่ทีมเทรนเอง (ปรับจาก Qwen2.5-0.5B) เสนอ SQL 4 แบบ (beam 4) หรือตอบว่าควรปฏิเสธ / ต้องถามกลับ",
    example: "SELECT SUM(amount) FROM sales WHERE branch = 'บางนา' AND …",
  },
  {
    title: "ตัวตรวจ SQL",
    where: "sql_guard.py",
    body: "ไล่ตรวจทีละแบบ เลือกแบบแรกที่ผ่านทุกข้อ และลองรันแบบไม่ดึงข้อมูล (EXPLAIN) ได้จริง",
    rules: [
      "ต้องเป็นคำสั่งอ่านข้อมูล (SELECT) คำสั่งเดียว",
      "ห้ามแก้ ลบ สร้างตาราง หรือแนบไฟล์อื่น แม้ซ่อนอยู่ข้างใน",
      "อ้างได้เฉพาะตารางของไฟล์นี้ ห้ามฟังก์ชันอ่านไฟล์",
      "เติม LIMIT 1000 ให้ถ้าไม่มี",
    ],
    stop: "ไม่มีแบบไหนผ่าน → ไม่รัน ขึ้นว่า \"ปฏิเสธ\" หรือ \"ตอบไม่ได้\"",
  },
  {
    title: "DuckDB อ่านอย่างเดียว",
    where: "db.py",
    body: "ไฟล์ของผู้ใช้ถูกเปิดแบบ read-only ต่อให้มีคำสั่งแก้ข้อมูลหลุดมาถึงขั้นนี้ ฐานข้อมูลก็ไม่ยอมเขียน",
  },
  {
    title: "ตอบ",
    where: "answer.py",
    body: "ตัวเลขในคำตอบมาจากผลรัน SQL จริง แล้วเขียนเป็นประโยคด้วยแม่แบบ ไม่ได้ให้โมเดลแต่งตัวเลขเอง แสดง SQL และตารางผลให้ตรวจได้",
    example: "คำตอบ: 265,479",
  },
];

const LAYERS = [
  { title: "โมเดลถูกสอนให้ปฏิเสธ", body: "ชุดข้อมูลเทรนมีหมวดคำขอที่ต้องตอบว่า \"ปฏิเสธ\" โมเดลจึงไม่สร้าง SQL ให้คำขอแบบนี้" },
  { title: "ตัวตรวจ SQL", body: "แยกวิเคราะห์ SQL ทั้งคำสั่ง ไม่ใช่แค่หาคำต้องห้าม และตรวจซ้ำอีกรอบก่อนรันจริง" },
  { title: "ฐานข้อมูลอ่านอย่างเดียว", body: "ชั้นสุดท้าย ฐานข้อมูลเองไม่ยอมให้เขียน" },
];

export default function HowPage() {
  return (
    <AppShell>
      <h1 className="page-title">
        <span>ระบบทำงานอย่างไร.</span>
        <span className="accent">จากคำถามถึงคำตอบ 6 ขั้น.</span>
      </h1>

      <ol className="flow">
        {STEPS.map((s, i) => (
          <li key={s.title} className={s.rules ? "flow-step guard" : "flow-step"}>
            <span className="flow-num" aria-hidden="true">
              {i + 1}
            </span>
            <div className="flow-card">
              <div className="flow-head">
                <h2>{s.title}</h2>
                <code>{s.where}</code>
              </div>
              <p>{s.body}</p>
              {s.rules && (
                <ul className="flow-rules">
                  {s.rules.map((r) => (
                    <li key={r}>{r}</li>
                  ))}
                </ul>
              )}
              {s.example && <p className="flow-example">{s.example}</p>}
              {s.stop && <p className="flow-stop">{s.stop}</p>}
            </div>
          </li>
        ))}
      </ol>

      <section className="layers">
        <h2>กัน SQL อันตรายอย่างไร.</h2>
        <p className="muted">มี 3 ชั้น ชั้นใดชั้นหนึ่งหยุดได้ ข้อมูลของร้านก็ไม่ถูกแก้</p>
        <div className="layer-grid">
          {LAYERS.map((l, i) => (
            <div key={l.title} className="layer">
              <span className="layer-num">ชั้นที่ {i + 1}</span>
              <h3>{l.title}</h3>
              <p>{l.body}</p>
            </div>
          ))}
        </div>
      </section>
    </AppShell>
  );
}
