# โครงสร้าง repo และเจ้าของ

ไฟล์ของใครให้คนนั้นแก้เป็นหลัก ถ้าต้องแก้ไฟล์ของคนอื่น ให้เปิด PR แล้วให้เจ้าของไฟล์ review

```
ThamDi/
├── apps/web/                      เว็บ (Next.js)                         Suphakorn
│   ├── app/page.js                login
│   ├── app/chat/page.js           อัปโหลด + ถาม
│   ├── app/model/page.js          เกี่ยวกับโมเดล + ผลการทดสอบ
│   ├── components/, lib/api.js
│   └── Dockerfile
├── services/api/
│   ├── app/
│   │   ├── main.py                สร้างแอป + ผูก routers                 Suphakorn
│   │   ├── config.py              ค่าตั้งจาก .env                        Suphakorn
│   │   ├── db.py                  ผู้ใช้ / dataset / ประวัติ / open_dataset()  Suphakorn
│   │   ├── security.py            JWT + ตรวจเจ้าของ dataset              Suphakorn
│   │   ├── ingest.py              อ่านไฟล์ที่อัปโหลด                     Suphakorn
│   │   ├── agent/
│   │   │   ├── model.py           generate_sql() / model_info()          Suphakorn
│   │   │   ├── answer.py          คำตอบภาษาไทยจากแม่แบบ                 Suphakorn
│   │   │   ├── pipeline.py        M0–M3 · run() · predict_sql()          Chalakorn
│   │   │   ├── preprocess.py      สร้าง prompt                           Chalakorn
│   │   │   ├── sql_guard.py       ตัวตรวจ SQL (sqlglot)                  Chalakorn
│   │   │   ├── thai_dates.py      วันที่ภาษาไทย / พ.ศ.                   Chalakorn
│   │   │   ├── tools.py           ฟังก์ชันช่วย                           Chalakorn
│   │   │   └── demo.py            DEMO_MODE: lookup() จาก demo_answers.json  Chalakorn
│   │   └── routers/
│   │       ├── auth.py, datasets.py, chat.py, model.py                    Suphakorn
│   │       └── eval.py            GET /api/eval/results                  Wissarut
│   ├── tests/                     pytest (ทุกคนเขียนเทสต์ของไฟล์ตัวเอง)
│   ├── requirements.txt           ไลบรารีของ API                         Suphakorn
│   ├── requirements-model.txt     torch/transformers สำหรับโมเดลจริง     Suphakorn
│   └── Dockerfile                                                        Suphakorn
├── ml/                            ข้อมูลเทรน + การเทรน                   Chalakorn
│   ├── format.py                  build_prompt() (ใช้ร่วมกับ preprocess.py)
│   ├── gen_data.py                สร้างข้อมูลเทรน/val
│   ├── check_leak.py              ตรวจไม่ให้ schema ทดสอบหลุดเข้าเทรน
│   ├── export_val.py              export val → eval/sets/val.jsonl + eval/schemas/val_*.sql
│   ├── train.ipynb                notebook เทรน (Colab หรือ Kaggle)
│   ├── templates/                 แม่แบบสร้างข้อมูลเทรน (Wissarut ห้ามเปิด)
│   └── data/                      ข้อมูลเทรน (ไม่ขึ้น git)
├── eval/                          วัดผล                                   Wissarut
│   ├── sets/                      handwritten.jsonl (70 ข้อ) · val.jsonl (205 ข้อ, Chalakorn export)
│   ├── schemas/                   DDL + ข้อมูลของแต่ละ schema · val_*.sql มาจาก export_val.py
│   ├── results/                   simulated.* · latest.* (ผลจริง) · w4_user_test.md · failures.md
│   ├── run.py, report.py          รัน M0–M3 × ชุด (handwritten / unseen / val / val_unseen) · ทำตาราง + กราฟ
│   ├── user_test.py               ทดสอบแบบผู้ใช้ผ่าน API (W4)
│   ├── tests/                     pytest ของ eval
│   └── demo_answers.json          คำตอบเดโม                              Chalakorn
├── scripts/
│   ├── gen_sales_db.py            ฐานข้อมูลตัวอย่าง                      Chalakorn
│   ├── make_demo_files.py         ไฟล์เดโม data/demo/                    Suphakorn
│   ├── tasks.sh                   setup/data/test/model/dev (Makefile เรียกไฟล์นี้)  Suphakorn
│   ├── smoke.sh                   ตรวจระบบครบเส้นผ่าน API                Suphakorn
│   └── hooks/                     git hooks ตรวจลายน้ำ AI                Chalakorn
├── docs/
│   ├── TASKS.md                   แบ่งงาน + กำหนดส่ง (ฉบับหลัก)          ทุกคน
│   ├── tasks/<ชื่อ>.md            แผนงานของแต่ละคน                       แต่ละคน
│   ├── CONTRACT.md                สัญญาอินเทอร์เฟซ                       ทุกคน
│   ├── STRUCTURE.md               ไฟล์นี้                                 ทุกคน
│   ├── CONVENTIONS.md             กฎการทำงาน (วิธีติดตั้ง hook)          Chalakorn
│   ├── MODEL_CARD.md              โมเดล ข้อมูลเทรน ลิงก์ดาวน์โหลด        Chalakorn
│   ├── ISSUES.md                  ปัญหา/ต้นเหตุ/วิธีแก้                   Chalakorn
│   ├── RUNBOOK.md                 รันแบบไม่ใช้ Docker · โมเดลจริง · แก้ปัญหา  Wissarut
│   └── DEMO_SCRIPT.md             บทเดโม + คำถามเดโม                     Wissarut
├── .github/                       CODEOWNERS + CI 4 job                  Suphakorn
├── Makefile, docker-compose.yml, .dockerignore                           Suphakorn
├── .env.example                   ตัวอย่างค่าตั้ง                        Suphakorn
├── .gitattributes                 บังคับ eol=lf ให้ scripts/hooks/*      Chalakorn
└── README.md                                                             Wissarut
```

ไฟล์ที่ไม่ขึ้น git: `.env`, `models/`, `ml/data/`, `data/`, `*.duckdb` และไฟล์ตั้งค่าเครื่องมือ AI (ดู `.gitignore`)
