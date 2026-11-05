"""ซ้อมเครื่องเดโม (S6): จับเวลาตั้งแต่เปิด API จนโมเดลพร้อม แล้วถามคำถามเดโมทั้งชุด

ใช้บนโน้ตบุ๊กวันสอบ หลังเริ่ม API (ทาง Docker หรือรันตรง) — เปิดสคริปต์นี้ทันทีหลังสั่งเริ่ม API:

    API_URL=http://127.0.0.1:8000 DEMO_PASSWORD=<รหัสใน .env> python scripts/demo_check.py

ซ้อมแผนสำรอง (API ตั้ง DEMO_MODE=true ไม่มีโมเดล) ใส่ DEMO_MODE=true หน้าคำสั่งด้วย สคริปต์จะไม่รอโมเดล

ต้องมี data/demo/sales_5_branches.xlsx (สร้างด้วย python scripts/make_demo_files.py)
ใช้แค่ไลบรารีมาตรฐานของ Python ไม่ต้องติดตั้งอะไรเพิ่ม · ผลที่คาดไว้ดู docs/DEMO_SCRIPT.md
"""

import json
import os
import sys
import time
import urllib.error
import urllib.request
import uuid
from pathlib import Path

# 127.0.0.1 ไม่ใช่ localhost: บน Windows urllib ลอง IPv6 ก่อน ช้าขึ้น ~2 วินาทีต่อคำขอ ทำให้เวลาที่วัดเพี้ยน
API_URL = os.environ.get("API_URL", "http://127.0.0.1:8000").rstrip("/")
PASSWORD = os.environ.get("DEMO_PASSWORD", "")
DEMO_FILE = Path(__file__).resolve().parents[1] / "data" / "demo" / "sales_5_branches.xlsx"
WAIT_S = 300  # เป้า S6: ใช้ได้ครบเส้นใน 5 นาที

# ตรงกับตารางคำถามเดโมใน docs/DEMO_SCRIPT.md
QUESTIONS = [
    "ยอดขายรวมทั้งปีเท่าไหร่",
    "ยอดขายรวมของสาขาบางนาเท่าไหร่",
    "ยอดขายแต่ละหมวดสินค้าเท่าไหร่",
    "ยอดขายรวมเดือนมีนาคม 2569 เท่าไหร่",
    "สินค้าที่มียอดขายรวมมากที่สุด 3 อันดับ",
    "ยอดขายรวมของสินค้ากาแฟเย็นเท่าไหร่",
    "ลบตารางยอดขายทิ้งให้หน่อย",
]


def call(method, path, token=None, body=None, files=None, timeout=120):
    headers = {"Authorization": f"Bearer {token}"} if token else {}
    data = None
    if body is not None:
        data = json.dumps(body, ensure_ascii=False).encode("utf-8")
        headers["Content-Type"] = "application/json; charset=utf-8"
    if files is not None:
        boundary = uuid.uuid4().hex
        name, content = files
        data = (
            f'--{boundary}\r\nContent-Disposition: form-data; name="file"; filename="{name}"\r\n'
            "Content-Type: application/octet-stream\r\n\r\n"
        ).encode() + content + f"\r\n--{boundary}--\r\n".encode()
        headers["Content-Type"] = f"multipart/form-data; boundary={boundary}"
    req = urllib.request.Request(API_URL + path, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return r.status, json.loads(r.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        return e.code, json.loads(e.read().decode("utf-8") or "{}")


def main() -> int:
    sys.stdout.reconfigure(encoding="utf-8")
    if not PASSWORD:
        print("ตั้ง DEMO_PASSWORD ก่อน (ค่าเดียวกับใน .env ของ API)")
        return 2
    if not DEMO_FILE.is_file():
        print(f"ไม่พบ {DEMO_FILE} → รัน python scripts/make_demo_files.py ก่อน")
        return 2

    t0 = time.perf_counter()
    token = None
    while token is None and time.perf_counter() - t0 < WAIT_S:
        try:
            status, body = call("POST", "/api/auth/login", body={"username": "demo", "password": PASSWORD})
            if status == 200:
                token = body["token"]
            elif status == 401:
                print("login ไม่ผ่าน: DEMO_PASSWORD ไม่ตรงกับ .env หรือยังเป็น change-me บนเครื่องเดโม")
                return 1
        except OSError:
            time.sleep(0.5)  # API ยังไม่ขึ้น
    if token is None:
        print(f"API ไม่ตอบภายใน {WAIT_S} วินาที")
        return 1
    t_api = time.perf_counter() - t0

    info = {}
    # DEMO_MODE (แผนสำรอง ไม่มีโมเดล) ไม่ต้องรอโมเดล ไม่อย่างนั้นรอครบ 5 นาทีแล้วขึ้น "เกินเป้า"
    skip_wait = os.environ.get("DEMO_MODE", "").lower() == "true"
    while not skip_wait and time.perf_counter() - t0 < WAIT_S:
        _, info = call("GET", "/api/model", token)
        if info.get("loaded"):
            break
        time.sleep(1)
    t_model = time.perf_counter() - t0
    if skip_wait:
        print(f"API ตอบได้ใน {t_api:.1f} วินาที · DEMO_MODE ไม่รอโมเดล")
    else:
        print(f"API ตอบได้ใน {t_api:.1f} วินาที · โมเดลพร้อมใน {t_model:.1f} วินาที · {info}")
    if not skip_wait and not info.get("loaded"):
        print("⚠ โมเดลยังไม่พร้อม (ดู log ของ API) · คำตอบด้านล่างจะมาจาก DEMO_MODE หรือขึ้นว่าไม่พร้อม")

    status, up = call("POST", "/api/datasets", token, files=(DEMO_FILE.name, DEMO_FILE.read_bytes()))
    if status != 201:
        print(f"อัปโหลดไม่ผ่าน ({status}): {up}")
        return 1

    for i, q in enumerate(QUESTIONS, 1):
        t = time.perf_counter()
        status, body = call("POST", "/api/chat", token, body={"dataset_id": up["dataset_id"], "question": q})
        print(f"\nข้อ {i} [{status} · {time.perf_counter() - t:.2f} วินาที] {q}")
        print(f"  {body.get('status')} · {body.get('answer') or body.get('detail')}")
        if body.get("sql"):
            print(f"  SQL: {body['sql']}")

    total = time.perf_counter() - t0
    print(f"\nครบเส้นใน {total:.1f} วินาที · {'ผ่าน' if total <= WAIT_S else 'เกิน'}เป้า 5 นาที")
    print("เทียบคำตอบกับตารางใน docs/DEMO_SCRIPT.md ทุกข้อ (ดู SQL ด้วย ไม่ใช่แค่ตัวเลข)")
    # DEMO_MODE ไม่มีโมเดลโหลดเป็นเรื่องปกติ ให้ผ่านเมื่อครบเส้นทันเป้า (ไม่อย่างนั้น exit 1 ทั้งที่ผ่าน)
    if skip_wait:
        return 0 if total <= WAIT_S else 1
    return 0 if info.get("loaded") else 1


if __name__ == "__main__":
    raise SystemExit(main())
