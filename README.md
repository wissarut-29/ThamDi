# ThamDi

ถามข้อมูลในตารางด้วยภาษาไทย โมเดลที่เทรนเองแปลงคำถามเป็น SQL แล้วตอบกลับเป็นภาษาไทย ทั้งหมดรันในเครื่อง ไม่ใช้ API ภายนอก

> README ฉบับเต็ม (10 หัวข้อ) Wissarut จะเขียนในงาน W6

## ทีม

| | GitHub | บทบาท | branch | แผนงาน |
|---|---|---|---|---|
| Chalakorn | @fffalafair | โมเดล | `feat/chalakorn` | [docs/tasks/chalakorn.md](docs/tasks/chalakorn.md) |
| Suphakorn | @SoSick41 | ระบบ | `feat/suphakorn` | [docs/tasks/suphakorn.md](docs/tasks/suphakorn.md) |
| Wissarut | @wissarut-29 | วัดผล + คุณภาพ + นำเสนอ · เจ้าของ repo | `feat/wissarut` | [docs/tasks/wissarut.md](docs/tasks/wissarut.md) |

## เอกสาร

| ไฟล์ | อ่านเมื่อ |
|---|---|
| [docs/TASKS.md](docs/TASKS.md) | อยากรู้ว่าใครทำอะไร ส่งอะไรให้ใคร เมื่อไหร่ |
| [docs/CONTRACT.md](docs/CONTRACT.md) | จะเรียกใช้ส่วนของคนอื่น (ฟังก์ชัน, API, รูปแบบไฟล์) |
| [docs/STRUCTURE.md](docs/STRUCTURE.md) | หาว่าไฟล์ไหนอยู่ไหน และใครเป็นเจ้าของ |
| [docs/CONVENTIONS.md](docs/CONVENTIONS.md) | กฎ branch, commit และสิ่งที่ห้ามทำ |

## วิธีทำงานร่วมกัน

- **`main`** = เวอร์ชันที่ใช้งานได้ สำหรับเดโม/ส่งงาน รับ merge จาก `dev` เท่านั้น
- **`dev`** = branch ที่ทุกคนทำงานร่วมกัน (default branch)
- แต่ละคนสร้าง `feat/<ชื่อ>` ของตัวเองจาก `dev` แล้วทำงานในนั้น เสร็จเป็นชิ้น ๆ ก็ push แล้วเปิด Pull Request เข้า `dev`
- พอ `dev` พร้อม ค่อยเปิด Pull Request จาก `dev` เข้า `main`
- ห้าม push ตรงเข้า `main` หรือ `dev` (GitHub บล็อกไว้แล้ว)
- ห้าม commit `.env`, ไฟล์โมเดล หรือข้อมูล (repo นี้เป็น public ทุกคนเห็นได้)
- ห้ามมีลายน้ำ AI ใน commit, PR, โค้ด และเอกสาร

### ตัวอย่างคำสั่ง

```bash
git clone https://github.com/wissarut-29/ThamDi.git
cd ThamDi
git switch -c feat/chalakorn       # สร้าง branch ของตัวเองจาก dev (ครั้งแรกครั้งเดียว ใช้ชื่อของตัวเอง)
git push -u origin feat/chalakorn
cp .env.example .env
# ... เขียนโค้ด ...
git add . && git commit -m "เพิ่ม sql_guard"
git push
# แล้วเปิด Pull Request จาก feat/chalakorn เข้า dev บน GitHub
```

ดึงงานของคนอื่นที่เข้า `dev` แล้วมารวมใน branch ตัวเอง:

```bash
git fetch origin
git merge origin/dev
```
