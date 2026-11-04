"""สร้างฐานข้อมูล DuckDB ตัวอย่างสำหรับเทรนโมเดล

schema ต้องตรงกับส่วนบนของ eval/schemas/sales.sql ทุกตัวอักษร (ชื่อตาราง/คอลัมน์/ชนิด)
เพื่อให้ SQL ที่โมเดลเรียนรู้ใช้ได้กับฐานข้อมูลทดสอบของ Wissarut ด้วย
ไฟล์ออกที่ data/ ซึ่งไม่ขึ้น git (ดู .gitignore)
"""

import argparse
import random
import sys
from pathlib import Path

import duckdb

SCHEMA_SQL = """
CREATE TABLE customers (
    customer_id INTEGER PRIMARY KEY,
    name        VARCHAR NOT NULL,
    province    VARCHAR NOT NULL,
    segment     VARCHAR NOT NULL
);

CREATE TABLE products (
    product_id INTEGER PRIMARY KEY,
    name       VARCHAR NOT NULL,
    category   VARCHAR NOT NULL,
    unit_price DECIMAL(10, 2) NOT NULL
);

CREATE TABLE orders (
    order_id    INTEGER PRIMARY KEY,
    customer_id INTEGER NOT NULL REFERENCES customers (customer_id),
    order_date  DATE NOT NULL,
    channel     VARCHAR NOT NULL
);

CREATE TABLE order_items (
    order_id   INTEGER NOT NULL REFERENCES orders (order_id),
    product_id INTEGER NOT NULL REFERENCES products (product_id),
    quantity   INTEGER NOT NULL,
    unit_price DECIMAL(10, 2) NOT NULL
);
"""

PROVINCES = [
    "กรุงเทพมหานคร", "เชียงใหม่", "เชียงราย", "ขอนแก่น", "นครราชสีมา",
    "ชลบุรี", "สงขลา", "ภูเก็ต", "อุดรธานี", "สุราษฎร์ธานี",
    "นนทบุรี", "ปทุมธานี", "สมุทรปราการ", "นครศรีธรรมราช", "อุบลราชธานี",
]
SEGMENTS = ["ทั่วไป", "สมาชิก", "องค์กร"]
CHANNELS = ["หน้าร้าน", "ออนไลน์"]
CATEGORIES = ["เครื่องดื่ม", "ขนม", "ของใช้ในบ้าน", "เครื่องเขียน", "เสื้อผ้า", "อุปกรณ์ไฟฟ้า"]

FIRST_NAMES = ["สมชาย", "สมหญิง", "วิชัย", "มาลี", "ประยุทธ", "สุดา", "อนุชา", "กนกวรรณ",
               "ธีระ", "ปิยะ", "วราภรณ์", "ชัยวัฒน์", "นภา", "สุรชัย", "อรุณี"]
LAST_NAMES = ["ใจดี", "รักษ์ไทย", "แสงทอง", "ศรีสุข", "บุญมี", "เจริญพร", "มั่งมี", "สายทอง"]
PRODUCT_WORDS = ["น้ำดื่ม", "ขนมปัง", "สมุด", "ปากกา", "ผ้าเช็ดตัว", "เสื้อยืด", "พัดลม",
                  "กาต้มน้ำ", "กระเป๋า", "รองเท้า", "หมอน", "ร่ม", "แก้วน้ำ", "กล่องข้าว"]


def build_rows(seed: int, n_customers: int, n_products: int, n_orders: int):
    rng = random.Random(seed)

    customers = [
        (i, f"{rng.choice(FIRST_NAMES)}{rng.choice(LAST_NAMES)}", rng.choice(PROVINCES), rng.choice(SEGMENTS))
        for i in range(1, n_customers + 1)
    ]
    products = [
        (i, f"{rng.choice(PRODUCT_WORDS)} รุ่น {i}", rng.choice(CATEGORIES), round(rng.uniform(10, 2000), 2))
        for i in range(1, n_products + 1)
    ]

    orders = []
    order_items = []
    item_id = 1
    for order_id in range(1, n_orders + 1):
        customer_id = rng.randint(1, n_customers)
        year = rng.choice([2567, 2568, 2569])  # พ.ศ. แปลงเป็น ค.ศ. ด้านล่าง
        month = rng.randint(1, 12)
        day = rng.randint(1, 28)
        order_date = f"{year - 543:04d}-{month:02d}-{day:02d}"
        channel = rng.choice(CHANNELS)
        orders.append((order_id, customer_id, order_date, channel))

        for _ in range(rng.randint(1, 4)):
            product_id = rng.randint(1, n_products)
            quantity = rng.randint(1, 10)
            unit_price = products[product_id - 1][3]
            order_items.append((order_id, product_id, quantity, unit_price))
            item_id += 1

    return customers, products, orders, order_items


def generate(out_path: Path, seed: int = 42, n_customers: int = 60, n_products: int = 40, n_orders: int = 300) -> None:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    if out_path.exists():
        out_path.unlink()

    customers, products, orders, order_items = build_rows(seed, n_customers, n_products, n_orders)

    con = duckdb.connect(str(out_path))
    try:
        con.execute(SCHEMA_SQL)
        con.executemany("INSERT INTO customers VALUES (?, ?, ?, ?)", customers)
        con.executemany("INSERT INTO products VALUES (?, ?, ?, ?)", products)
        con.executemany("INSERT INTO orders VALUES (?, ?, ?, ?)", orders)
        con.executemany("INSERT INTO order_items VALUES (?, ?, ?, ?)", order_items)
    finally:
        con.close()


def main() -> None:
    # cmd.exe เริ่มต้นใช้ cp1252/cp874 พิมพ์ภาษาไทยไม่ได้ ต้องบังคับ utf-8
    sys.stdout.reconfigure(encoding="utf-8")

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", default="data/sales.duckdb")
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()

    out_path = Path(args.out)
    generate(out_path, seed=args.seed)
    print(f"สร้างแล้ว: {out_path}")


if __name__ == "__main__":
    main()
