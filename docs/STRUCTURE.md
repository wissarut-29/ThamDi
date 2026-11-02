# โครงสร้าง repo และเจ้าของ

ไฟล์ของใครให้คนนั้นแก้เป็นหลัก ถ้าต้องแก้ไฟล์ของคนอื่น ให้เปิด PR แล้วให้เจ้าของไฟล์ review

```
ThamDi/
├── apps/web/                      เว็บ (Next.js)                         Suphakorn
├── services/api/
│   ├── app/
│   │   ├── main.py                สร้างแอป + ผูก routers                 Suphakorn
│   │   ├── config.py              ค่าตั้งจาก .env                        Suphakorn
│   │   ├── db.py                  ผู้ใช้ / dataset / ประวัติ             Suphakorn
│   │   ├── security.py            JWT + ตรวจเจ้าของ dataset              Suphakorn
│   │   ├── ingest.py              อ่านไฟล์ที่อัปโหลด                     Suphakorn
│   │   ├── agent/
│   │   │   ├── model.py           generate_sql() / model_info()          Suphakorn
│   │   │   ├── answer.py          คำตอบภาษาไทยจากแม่แบบ                 Suphakorn
│   │   │   ├── pipeline.py        M0–M3                                  Chalakorn
│   │   │   ├── preprocess.py      สร้าง prompt                           Chalakorn
│   │   │   ├── sql_guard.py       ตัวตรวจ SQL                            Chalakorn
│   │   │   ├── thai_dates.py      วันที่ภาษาไทย / พ.ศ.                   Chalakorn
│   │   │   ├── tools.py           ฟังก์ชันช่วย                           Chalakorn
│   │   │   └── demo.py            DEMO_MODE                              Chalakorn
│   │   └── routers/
│   │       ├── auth.py, datasets.py, chat.py, model.py                    Suphakorn
│   │       └── eval.py            GET /api/eval/results                  Wissarut
│   └── tests/                     pytest (ทุกคนเขียนเทสต์ของไฟล์ตัวเอง)
├── ml/                            ข้อมูลเทรน + การเทรน                   Chalakorn
│   ├── templates/                 แม่แบบสร้างข้อมูลเทรน (Wissarut ห้ามเปิด)
│   └── data/                      ข้อมูลเทรน (ไม่ขึ้น git)
├── eval/                          วัดผล                                   Wissarut
│   ├── sets/                      ชุดทดสอบ handwritten / unseen / val
│   ├── results/                   ผล eval + failures.md
│   ├── run.py, report.py
│   └── demo_answers.json          คำตอบเดโม                              Chalakorn
├── scripts/
│   ├── gen_sales_db.py            ฐานข้อมูลตัวอย่าง                      Chalakorn
│   └── hooks/                     git hooks (เช่น ตรวจลายน้ำ AI)         Chalakorn
├── docs/
│   ├── TASKS.md                   แบ่งงาน + กำหนดส่ง                     ทุกคน
│   ├── CONTRACT.md                สัญญาอินเทอร์เฟซ                       ทุกคน
│   ├── STRUCTURE.md               ไฟล์นี้                                 ทุกคน
│   ├── CONVENTIONS.md             กฎการทำงาน                             Chalakorn
│   ├── MODEL_CARD.md                                                     Chalakorn
│   ├── RUNBOOK.md                                                        Wissarut
│   └── DEMO_SCRIPT.md                                                    Wissarut
├── .github/                       CODEOWNERS + CI (ยังไม่มี: งาน 1.5)    Suphakorn
├── Makefile, docker-compose.yml   (ยังไม่มี)                             Suphakorn
├── .env.example                   ตัวอย่างค่าตั้ง                        Suphakorn
└── README.md                                                             Wissarut
```

ไฟล์ที่ไม่ขึ้น git: `.env`, `models/`, `ml/data/`, `data/`, `*.duckdb` และไฟล์ตั้งค่าเครื่องมือ AI (ดู `.gitignore`)
