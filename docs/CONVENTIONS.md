# กฎการทำงาน (CONVENTIONS)

## Branch

| branch | ใช้ทำอะไร |
|---|---|
| `main` | เวอร์ชันที่ใช้งานได้ สำหรับเดโม/ส่งงาน รับ merge จาก `dev` เท่านั้น |
| `dev` | branch ที่ทุกคนทำงานร่วมกัน (default branch) |
| `feat/chalakorn`, `feat/suphakorn`, `feat/wissarut` | branch ทำงานของแต่ละคน แตกจาก `dev` |

- ห้าม push ตรงเข้า `main` หรือ `dev` ต้องผ่าน Pull Request เท่านั้น (GitHub บล็อกไว้แล้ว)
- ทำงานเสร็จเป็นชิ้น ๆ ให้ push `feat/<ชื่อ>` แล้วเปิด Pull Request เข้า `dev`
- PR เล็กและบ่อยดีกว่า PR ใหญ่ครั้งเดียว อย่างน้อยวันละครั้ง หรือทุกครั้งที่มีของต้องส่งให้คนอื่น (ดู "จุดส่งของ" ใน `docs/TASKS.md`)
- พอ PR ของคนอื่นเข้า `dev` แล้ว ให้ดึงมารวมใน branch ตัวเอง: `git fetch origin && git merge origin/dev`
- ตอน code freeze ค่อยเปิด PR จาก `dev` เข้า `main` แล้วติด tag `v1.0`

## Commit

- ข้อความ commit เป็นภาษาไทยหรืออังกฤษก็ได้ บอกว่าทำอะไร เช่น `เพิ่ม sql_guard ห้าม DELETE`
- **ห้ามมีลายน้ำ AI** ใน commit, PR, โค้ด และเอกสาร เช่น บรรทัดเครดิตหรือผู้ร่วมเขียนที่เครื่องมือ AI ใส่ให้อัตโนมัติ ถ้าใช้เครื่องมือช่วยเขียน ให้ปิด attribution ของเครื่องมือนั้นก่อน
- ห้าม commit `.env`, ไฟล์โมเดล, `data/`, `ml/data/`, `*.duckdb` และไฟล์ตั้งค่าเครื่องมือ AI (รายการอยู่ใน `.gitignore`) — repo นี้เป็น public

## ติดตั้ง git hooks (ตรวจลายน้ำ AI)

รันครั้งเดียวหลัง clone (ใช้ได้ทั้ง Git Bash บน Windows และ macOS/Linux):

```bash
git config core.hooksPath scripts/hooks
```

(ไม่ต้อง `chmod +x` เอง — บิต executable ถูก commit ไว้ในไฟล์แล้ว ด้วย `git update-index --chmod=+x`)

- `scripts/hooks/commit-msg` บล็อก commit ที่มีรูปแบบลายน้ำ AI (ดูรายการทั้งหมดที่ตรวจจริงใน
  `scripts/hooks/watermark-patterns.sh`) เช่น บรรทัดเครดิตผู้ร่วมเขียนที่เครื่องมือ AI ใส่ให้อัตโนมัติ,
  ข้อความ "สร้างด้วย/โดย" เครื่องมือ AI, ลิงก์ไปหน้า session ของเครื่องมือ AI
- `scripts/hooks/pre-commit` บล็อกไฟล์ `.claude/`, `CLAUDE.md`, `AGENTS.md`, `.cursor/`, `.env` (ยกเว้น
  `.env.example`), ไฟล์โมเดล, `data/`, `ml/data/`, `*.duckdb` และข้อความลายน้ำ AI ใน diff ที่ staged
  (ยกเว้น `.gitignore` และไฟล์ hook เอง)
- ถ้า hook บล็อกจริง ให้แก้ข้อความ/ไฟล์แล้ว commit ใหม่ **ห้ามใช้ `--no-verify`** เพื่อข้ามการตรวจ
- **ข้อจำกัดที่รู้อยู่แล้ว (ตั้งใจเข้มเกินพอดีไว้ก่อน):** `commit-msg` บล็อกบรรทัดเครดิตผู้ร่วมเขียน
  แบบเหมาเข่งทุกกรณี รวมถึงตอน pair-programming กับเพื่อนในทีมจริง ๆ (ไม่ใช่เครื่องมือ AI) และอาจบล็อกวลี
  ทั่วไปที่บังเอิญมีคำขึ้นต้นคล้ายคำที่ hook ตรวจอยู่ ถ้าเจอแบบนี้บ่อยจนรำคาญ คุยกันเพื่อปรับ pattern ใน
  `watermark-patterns.sh` ได้ แต่ห้ามใช้ `--no-verify` เพื่อข้ามเฉย ๆ

## ไฟล์ของใคร

ดู `docs/STRUCTURE.md` ถ้าจะแก้ไฟล์ของคนอื่น ให้ขอให้เจ้าของไฟล์ review ใน PR
ถ้าจะเปลี่ยนอินเทอร์เฟซที่คนอื่นใช้ ให้แก้ `docs/CONTRACT.md` ใน PR เดียวกัน

## ไม่ใช้ API ภายนอก

ห้ามเรียก API ของโมเดลภาษาภายนอก (Groq, Gemini, OpenAI ฯลฯ) ห้ามมีค่าตั้งหรือข้อความที่ทำให้เข้าใจว่าใช้ โมเดลต้องเทรนเองและรันในเครื่อง
