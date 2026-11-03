"""สร้างไฟล์เดโมที่หน้าตาเหมือนไฟล์จริงของเจ้าของร้าน ไว้อัปโหลดตอนเดโม (S-08)

    python scripts/make_demo_files.py            # เขียนลง data/demo/ (ไม่ขึ้น git)

- sales_5_branches.xlsx  ยอดขายรายวัน 5 สาขา ทั้งปี 2569 (ค.ศ. 2026)
- utility_bills.csv      ค่าไฟ ค่าน้ำ รายเดือนของแต่ละสาขา
- employees.xlsx         พนักงานแต่ละสาขา (เงินเดือน, วันเริ่มงาน)

ใช้ seed ตายตัว รันซ้ำได้ไฟล์เดิม คำตอบในสคริปต์เดโมจะได้ไม่เปลี่ยน
ชื่อคอลัมน์เป็นภาษาอังกฤษ snake_case แบบเดียวกับ schema ที่ใช้วัดผล ส่วนค่าในเซลล์เป็นภาษาไทย
"""

import argparse
import random
from datetime import date, timedelta
from pathlib import Path

import pandas as pd

BRANCHES = ["บางนา", "ลาดพร้าว", "รังสิต", "เชียงใหม่", "ขอนแก่น"]
PRODUCTS = [
    # (สินค้า, หมวด, ราคาต่อหน่วย)
    ("กาแฟเย็น", "เครื่องดื่ม", 55),
    ("ชาไทย", "เครื่องดื่ม", 45),
    ("โกโก้", "เครื่องดื่ม", 50),
    ("น้ำเปล่า", "เครื่องดื่ม", 15),
    ("ครัวซองต์", "เบเกอรี่", 65),
    ("บราวนี่", "เบเกอรี่", 70),
    ("ขนมปังสังขยา", "เบเกอรี่", 40),
    ("ข้าวกะเพราไก่", "อาหาร", 75),
    ("ข้าวผัดหมู", "อาหาร", 70),
    ("สลัดอกไก่", "อาหาร", 89),
]
# สาขาใหญ่ขายได้มากกว่า จะได้มีคำตอบที่น่าสนใจตอนถาม "สาขาไหนขายดีที่สุด"
BRANCH_WEIGHT = {"บางนา": 1.4, "ลาดพร้าว": 1.2, "รังสิต": 1.0, "เชียงใหม่": 0.9, "ขอนแก่น": 0.7}
POSITIONS = [("ผู้จัดการสาขา", 32000), ("บาริสต้า", 15000), ("พนักงานครัว", 14000), ("แคชเชียร์", 13500)]
FIRST_NAMES = ["สมชาย", "สมหญิง", "วิชัย", "ปิยะนุช", "อนุชา", "กมลชนก", "ธนพล", "ศิริพร", "ณัฐวุฒิ", "พิมพ์ชนก"]
LAST_NAMES = ["ใจดี", "รุ่งเรือง", "ศรีสุข", "มั่นคง", "แสงทอง", "บุญมา", "ทองดี", "สายสุวรรณ"]


def make_sales(rng: random.Random) -> pd.DataFrame:
    rows = []
    day = date(2026, 1, 1)
    while day.year == 2026:
        weekend = 1.3 if day.weekday() >= 5 else 1.0
        for branch in BRANCHES:
            # แต่ละสาขาขาย 4-7 รายการต่อวัน (สรุปยอดรายสินค้ารายวัน)
            for product, category, price in rng.sample(PRODUCTS, rng.randint(4, 7)):
                quantity = max(1, round(rng.gauss(18, 6) * BRANCH_WEIGHT[branch] * weekend))
                rows.append(
                    {
                        "sale_date": day,
                        "branch": branch,
                        "product": product,
                        "category": category,
                        "quantity": quantity,
                        "unit_price": price,
                        "amount": quantity * price,
                    }
                )
        day += timedelta(days=1)
    frame = pd.DataFrame(rows)
    frame["sale_date"] = pd.to_datetime(frame["sale_date"])
    return frame


def make_utility(rng: random.Random) -> pd.DataFrame:
    rows = []
    for month in range(1, 13):
        hot = 1.35 if month in (3, 4, 5) else 1.0  # หน้าร้อนค่าไฟสูง
        for branch in BRANCHES:
            rows.append(
                {
                    "month": f"2026-{month:02d}",
                    "branch": branch,
                    "electricity_baht": round(rng.uniform(9000, 14000) * BRANCH_WEIGHT[branch] * hot),
                    "water_baht": round(rng.uniform(800, 1600) * BRANCH_WEIGHT[branch]),
                }
            )
    return pd.DataFrame(rows)


def make_employees(rng: random.Random) -> pd.DataFrame:
    rows = []
    employee_id = 1
    for branch in BRANCHES:
        for position, base in POSITIONS:
            count = 1 if position == "ผู้จัดการสาขา" else rng.randint(1, 3)
            for _ in range(count):
                start = date(2020, 1, 1) + timedelta(days=rng.randint(0, 6 * 365))
                rows.append(
                    {
                        "employee_id": employee_id,
                        "full_name": f"{rng.choice(FIRST_NAMES)} {rng.choice(LAST_NAMES)}",
                        "branch": branch,
                        "position": position,
                        "monthly_salary": base + rng.randrange(0, 4000, 500),
                        "start_date": start,
                    }
                )
                employee_id += 1
    frame = pd.DataFrame(rows)
    frame["start_date"] = pd.to_datetime(frame["start_date"])
    return frame


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--out", default="data/demo")
    parser.add_argument("--seed", type=int, default=2569)
    args = parser.parse_args()

    rng = random.Random(args.seed)
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)

    with pd.ExcelWriter(out / "sales_5_branches.xlsx") as writer:
        make_sales(rng).to_excel(writer, sheet_name="sales", index=False)
    make_utility(rng).to_csv(out / "utility_bills.csv", index=False, encoding="utf-8-sig")
    with pd.ExcelWriter(out / "employees.xlsx") as writer:
        make_employees(rng).to_excel(writer, sheet_name="employees", index=False)

    for path in sorted(out.iterdir()):
        print(f"สร้างแล้ว: {path} ({path.stat().st_size / 1024:.0f} KB)")


if __name__ == "__main__":
    main()
