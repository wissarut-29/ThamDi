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
│   │   │   ├── pipeline.py        M0–M3 ✓ (C3, รอ get_dataset() จาก Suphakorn) Chalakorn
│   │   │   ├── preprocess.py      สร้าง prompt ✓ (C3)                    Chalakorn
│   │   │   ├── sql_guard.py       ตัวตรวจ SQL (sqlglot) ✓ (C3)           Chalakorn
│   │   │   ├── thai_dates.py      วันที่ภาษาไทย / พ.ศ. ✓ (C3)            Chalakorn
│   │   │   ├── tools.py           ฟังก์ชันช่วย ✓ (C3)                    Chalakorn
│   │   │   └── demo.py            DEMO_MODE (ยังไม่ทำ: C5)               Chalakorn
│   │   └── routers/
│   │       ├── auth.py, datasets.py, chat.py, model.py                    Suphakorn
│   │       └── eval.py            GET /api/eval/results                  Wissarut
│   └── tests/                     pytest (ทุกคนเขียนเทสต์ของไฟล์ตัวเอง)
├── ml/                            ข้อมูลเทรน + การเทรน                   Chalakorn
│   ├── format.py                  build_prompt() ✓ (C2, ใช้ร่วมกับ preprocess.py)
│   ├── gen_data.py                สร้างข้อมูลเทรน/val ✓ (C2)
│   ├── check_leak.py              ตรวจไม่ให้ schema ทดสอบหลุดเข้าเทรน ✓ (C2)
│   ├── train.ipynb                notebook เทรนบน Colab ✓ (C2, รอเลือกโมเดล)
│   ├── templates/                 แม่แบบสร้างข้อมูลเทรน ✓ (C2, Wissarut ห้ามเปิด)
│   └── data/                      ข้อมูลเทรน (ไม่ขึ้น git) — 7000 train / 1470 val
├── eval/                          วัดผล                                   Wissarut
│   ├── sets/                      ชุดทดสอบ handwritten / unseen / val
│   ├── results/                   ผล eval + failures.md
│   ├── run.py, report.py
│   └── demo_answers.json          คำตอบเดโม                              Chalakorn
├── scripts/
│   ├── gen_sales_db.py            ฐานข้อมูลตัวอย่าง ✓ (C2)                Chalakorn
│   └── hooks/                     git hooks ตรวจลายน้ำ AI ✓ (1.4)         Chalakorn
├── docs/
│   ├── TASKS.md                   แบ่งงาน + กำหนดส่ง (ฉบับหลัก)          ทุกคน
│   ├── tasks/<ชื่อ>.md            แผนงานของแต่ละคน                       แต่ละคน
│   ├── CONTRACT.md                สัญญาอินเทอร์เฟซ                       ทุกคน
│   ├── STRUCTURE.md               ไฟล์นี้                                 ทุกคน
│   ├── CONVENTIONS.md             กฎการทำงาน ✓ (วิธีติดตั้ง hook)         Chalakorn
│   ├── MODEL_CARD.md                                                     Chalakorn
│   ├── ISSUES.md                  ปัญหา/ต้นเหตุ/วิธีแก้ ✓                 Chalakorn
│   ├── RUNBOOK.md                                                        Wissarut
│   └── DEMO_SCRIPT.md                                                    Wissarut
├── .github/                       CODEOWNERS + CI (ยังไม่มี: งาน 1.5)    Wissarut
├── Makefile, docker-compose.yml   (ยังไม่มี)                             Suphakorn
├── .env.example                   ตัวอย่างค่าตั้ง                        Suphakorn
├── .gitattributes                 บังคับ eol=lf ให้ scripts/hooks/* ✓     Chalakorn
└── README.md                                                             Wissarut
```

ไฟล์ที่ไม่ขึ้น git: `.env`, `models/`, `ml/data/`, `data/`, `*.duckdb` และไฟล์ตั้งค่าเครื่องมือ AI (ดู `.gitignore`)
