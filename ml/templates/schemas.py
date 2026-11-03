"""นิยาม schema สังเคราะห์ที่ใช้สร้างข้อมูลเทรน

ทุก schema มีรูปทรงคล้ายกัน (dimA = ตารางเอนทิตีหลัก, fact = ตารางเหตุการณ์ที่มีวันที่และ FK ไปที่ dimA,
measure_expr = ตัวเลขที่เอาไปรวม/จัดอันดับได้ — อาจอยู่ในตาราง fact เอง หรือต้อง join เพิ่ม)
เพื่อให้ตัวสร้างคำถาม (generators.py) ใช้ตรรกะเดียวกันได้กับทุก schema

ห้ามมี schema ที่คล้าย clinic (ผู้ป่วย/หมอ/นัดหมาย) หรือ library (สมาชิก/หนังสือ/ยืม-คืน)
schema `school` ใช้เฉพาะ val เท่านั้น (ดู ml/gen_data.py) ห้ามเอาไปเทรน
"""

from dataclasses import dataclass, field


@dataclass
class EntitySpec:
    table: str
    pk: str
    name_col: str
    thai: str                  # คำเรียกภาษาไทยของตารางนี้ ใช้แต่งประโยคคำถาม (SQL ยังใช้ table เดิม)
    cat_cols: dict[str, list[str]] = field(default_factory=dict)


@dataclass
class FactSpec:
    table: str
    pk: str
    fk_to_dimA: str
    date_col: str
    thai: str
    cat_cols: dict[str, list[str]] = field(default_factory=dict)


@dataclass
class SchemaSpec:
    name: str
    thai: str
    ddl: str
    dimA: EntitySpec
    fact: FactSpec
    measure_expr: str          # นิพจน์ตัวเลขที่ใช้ SUM/AVG/จัดอันดับได้ (qualify ชื่อตารางแล้ว)
    measure_join: str          # SQL JOIN เพิ่มเติม (ถ้า measure ไม่ได้อยู่ในตาราง fact เอง) หรือ "" ถ้าไม่ต้อง
    dim2: EntitySpec | None = None
    dim2_join: str = ""        # SQL JOIN เพิ่มเติมเพื่อไปถึง dim2 (ใช้กับคำถามประเภท join 2 ชั้น)
    seed_fn: object = None     # function(rng) -> dict[table_name] -> list[tuple] สำหรับ validate SQL


def _sales_seed(rng):
    provinces = ["กรุงเทพมหานคร", "เชียงใหม่", "ชลบุรี", "ขอนแก่น"]
    segments = ["ทั่วไป", "สมาชิก", "องค์กร"]
    categories = ["เครื่องดื่ม", "ขนม", "ของใช้"]
    channels = ["หน้าร้าน", "ออนไลน์"]
    customers = [(i, f"ลูกค้า{i}", rng.choice(provinces), rng.choice(segments)) for i in range(1, 11)]
    products = [(i, f"สินค้า{i}", rng.choice(categories), round(rng.uniform(10, 500), 2)) for i in range(1, 8)]
    orders = [(i, rng.randint(1, 10), f"2025-{rng.randint(1,12):02d}-{rng.randint(1,28):02d}", rng.choice(channels))
              for i in range(1, 20)]
    order_items = []
    for _ in range(40):
        oid = rng.randint(1, 19)
        pid = rng.randint(1, 7)
        price = next(p[3] for p in products if p[0] == pid)
        order_items.append((oid, pid, rng.randint(1, 5), price))
    return {"customers": customers, "products": products, "orders": orders, "order_items": order_items}


SALES = SchemaSpec(
    name="sales",
    thai="ร้านค้า",
    ddl="""CREATE TABLE customers (
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
);""",
    dimA=EntitySpec("customers", "customer_id", "name", thai="ลูกค้า",
                     cat_cols={"province": ["กรุงเทพมหานคร", "เชียงใหม่", "ชลบุรี", "ขอนแก่น"],
                               "segment": ["ทั่วไป", "สมาชิก", "องค์กร"]}),
    fact=FactSpec("orders", "order_id", "customer_id", "order_date", thai="คำสั่งซื้อ",
                   cat_cols={"channel": ["หน้าร้าน", "ออนไลน์"]}),
    measure_expr="order_items.quantity * order_items.unit_price",
    measure_join="JOIN order_items ON order_items.order_id = orders.order_id",
    dim2=EntitySpec("products", "product_id", "name", thai="สินค้า",
                     cat_cols={"category": ["เครื่องดื่ม", "ขนม", "ของใช้"]}),
    dim2_join="JOIN products ON products.product_id = order_items.product_id",
    seed_fn=_sales_seed,
)


def _restaurant_seed(rng):
    positions = ["พนักงานเสิร์ฟ", "กุ๊ก", "แคชเชียร์"]
    branches = ["สาขาสุขุมวิท", "สาขาลาดพร้าว", "สาขาเซ็นทรัลเวิลด์"]
    categories = ["อาหารจานเดียว", "เครื่องดื่ม", "ของหวาน"]
    channels = ["นั่งทาน", "สั่งกลับบ้าน", "เดลิเวอรี"]
    staff = [(i, f"พนักงาน{i}", rng.choice(positions), rng.choice(branches)) for i in range(1, 9)]
    menu_items = [(i, f"เมนู{i}", rng.choice(categories), round(rng.uniform(30, 300), 2)) for i in range(1, 12)]
    orders = [(i, rng.randint(1, 8), f"2025-{rng.randint(1,12):02d}-{rng.randint(1,28):02d}", rng.choice(channels))
              for i in range(1, 20)]
    order_items = []
    for _ in range(40):
        order_items.append((rng.randint(1, 19), rng.randint(1, 11), rng.randint(1, 4)))
    return {"staff": staff, "menu_items": menu_items, "orders": orders, "order_items": order_items}


RESTAURANT = SchemaSpec(
    name="restaurant",
    thai="ร้านอาหาร",
    ddl="""CREATE TABLE staff (
    staff_id INTEGER PRIMARY KEY,
    name     VARCHAR NOT NULL,
    position VARCHAR NOT NULL,
    branch   VARCHAR NOT NULL
);

CREATE TABLE menu_items (
    menu_item_id INTEGER PRIMARY KEY,
    name         VARCHAR NOT NULL,
    category     VARCHAR NOT NULL,
    price        DECIMAL(10, 2) NOT NULL
);

CREATE TABLE orders (
    order_id   INTEGER PRIMARY KEY,
    staff_id   INTEGER NOT NULL REFERENCES staff (staff_id),
    order_date DATE NOT NULL,
    channel    VARCHAR NOT NULL
);

CREATE TABLE order_items (
    order_id     INTEGER NOT NULL REFERENCES orders (order_id),
    menu_item_id INTEGER NOT NULL REFERENCES menu_items (menu_item_id),
    quantity     INTEGER NOT NULL
);""",
    dimA=EntitySpec("staff", "staff_id", "name", thai="พนักงาน",
                     cat_cols={"position": ["พนักงานเสิร์ฟ", "กุ๊ก", "แคชเชียร์"],
                               "branch": ["สาขาสุขุมวิท", "สาขาลาดพร้าว", "สาขาเซ็นทรัลเวิลด์"]}),
    fact=FactSpec("orders", "order_id", "staff_id", "order_date", thai="ออเดอร์",
                   cat_cols={"channel": ["นั่งทาน", "สั่งกลับบ้าน", "เดลิเวอรี"]}),
    measure_expr="order_items.quantity * menu_items.price",
    measure_join="JOIN order_items ON order_items.order_id = orders.order_id "
                 "JOIN menu_items ON menu_items.menu_item_id = order_items.menu_item_id",
    dim2=EntitySpec("menu_items", "menu_item_id", "name", thai="เมนู",
                     cat_cols={"category": ["อาหารจานเดียว", "เครื่องดื่ม", "ของหวาน"]}),
    dim2_join="JOIN menu_items ON menu_items.menu_item_id = order_items.menu_item_id",
    seed_fn=_restaurant_seed,
)


def _warehouse_seed(rng):
    cities = ["กรุงเทพมหานคร", "สมุทรปราการ", "ชลบุรี"]
    categories = ["อิเล็กทรอนิกส์", "เครื่องใช้ไฟฟ้า", "วัสดุก่อสร้าง"]
    types_ = ["รับเข้า", "จ่ายออก"]
    warehouses = [(i, f"คลัง{i}", rng.choice(cities)) for i in range(1, 6)]
    items = [(i, f"สินค้า{i}", rng.choice(categories), round(rng.uniform(50, 1000), 2)) for i in range(1, 12)]
    shipments = [(i, rng.randint(1, 5), f"2025-{rng.randint(1,12):02d}-{rng.randint(1,28):02d}", rng.choice(types_))
                 for i in range(1, 20)]
    shipment_items = []
    for _ in range(40):
        shipment_items.append((rng.randint(1, 19), rng.randint(1, 11), rng.randint(1, 100)))
    return {"warehouses": warehouses, "items": items, "shipments": shipments, "shipment_items": shipment_items}


WAREHOUSE = SchemaSpec(
    name="warehouse",
    thai="คลังสินค้า",
    ddl="""CREATE TABLE warehouses (
    warehouse_id INTEGER PRIMARY KEY,
    name         VARCHAR NOT NULL,
    city         VARCHAR NOT NULL
);

CREATE TABLE items (
    item_id    INTEGER PRIMARY KEY,
    name       VARCHAR NOT NULL,
    category   VARCHAR NOT NULL,
    unit_cost  DECIMAL(10, 2) NOT NULL
);

CREATE TABLE shipments (
    shipment_id   INTEGER PRIMARY KEY,
    warehouse_id  INTEGER NOT NULL REFERENCES warehouses (warehouse_id),
    shipment_date DATE NOT NULL,
    shipment_type VARCHAR NOT NULL
);

CREATE TABLE shipment_items (
    shipment_id INTEGER NOT NULL REFERENCES shipments (shipment_id),
    item_id     INTEGER NOT NULL REFERENCES items (item_id),
    quantity    INTEGER NOT NULL
);""",
    dimA=EntitySpec("warehouses", "warehouse_id", "name", thai="คลัง",
                     cat_cols={"city": ["กรุงเทพมหานคร", "สมุทรปราการ", "ชลบุรี"]}),
    fact=FactSpec("shipments", "shipment_id", "warehouse_id", "shipment_date", thai="การขนส่ง",
                   cat_cols={"shipment_type": ["รับเข้า", "จ่ายออก"]}),
    measure_expr="shipment_items.quantity * items.unit_cost",
    measure_join="JOIN shipment_items ON shipment_items.shipment_id = shipments.shipment_id "
                 "JOIN items ON items.item_id = shipment_items.item_id",
    dim2=EntitySpec("items", "item_id", "name", thai="สินค้า",
                     cat_cols={"category": ["อิเล็กทรอนิกส์", "เครื่องใช้ไฟฟ้า", "วัสดุก่อสร้าง"]}),
    dim2_join="JOIN items ON items.item_id = shipment_items.item_id",
    seed_fn=_warehouse_seed,
)


def _hr_seed(rng):
    locations = ["กรุงเทพมหานคร", "เชียงใหม่", "ขอนแก่น"]
    positions = ["วิศวกร", "นักบัญชี", "ฝ่ายขาย", "ฝ่ายบุคคล"]
    departments = [(i, f"แผนก{i}", rng.choice(locations)) for i in range(1, 6)]
    employees = [(i, f"พนักงาน{i}", rng.randint(1, 5), rng.choice(positions),
                  f"202{rng.randint(0,5)}-{rng.randint(1,12):02d}-{rng.randint(1,28):02d}",
                  round(rng.uniform(18000, 90000), 2))
                 for i in range(1, 30)]
    return {"departments": departments, "employees": employees}


HR = SchemaSpec(
    name="hr",
    thai="บุคคล",
    ddl="""CREATE TABLE departments (
    department_id INTEGER PRIMARY KEY,
    name          VARCHAR NOT NULL,
    location      VARCHAR NOT NULL
);

CREATE TABLE employees (
    employee_id   INTEGER PRIMARY KEY,
    name          VARCHAR NOT NULL,
    department_id INTEGER NOT NULL REFERENCES departments (department_id),
    position      VARCHAR NOT NULL,
    hire_date     DATE NOT NULL,
    salary        DECIMAL(10, 2) NOT NULL
);""",
    dimA=EntitySpec("departments", "department_id", "name", thai="แผนก",
                     cat_cols={"location": ["กรุงเทพมหานคร", "เชียงใหม่", "ขอนแก่น"]}),
    fact=FactSpec("employees", "employee_id", "department_id", "hire_date", thai="พนักงาน",
                   cat_cols={"position": ["วิศวกร", "นักบัญชี", "ฝ่ายขาย", "ฝ่ายบุคคล"]}),
    measure_expr="employees.salary",
    measure_join="",
    seed_fn=_hr_seed,
)


def _event_seed(rng):
    cities = ["กรุงเทพมหานคร", "เชียงใหม่", "ภูเก็ต"]
    types_ = ["VIP", "ทั่วไป", "นักเรียน"]
    events = [(i, f"งานอีเวนต์{i}", rng.choice(cities),
               f"2025-{rng.randint(1,12):02d}-{rng.randint(1,28):02d}")
              for i in range(1, 8)]
    tickets = [(i, rng.randint(1, 7), rng.choice(types_), round(rng.uniform(200, 3000), 2),
                f"2025-{rng.randint(1,12):02d}-{rng.randint(1,28):02d}")
               for i in range(1, 30)]
    return {"events": events, "tickets": tickets}


EVENT = SchemaSpec(
    name="event",
    thai="งานอีเวนต์",
    ddl="""CREATE TABLE events (
    event_id   INTEGER PRIMARY KEY,
    name       VARCHAR NOT NULL,
    city       VARCHAR NOT NULL,
    event_date DATE NOT NULL
);

CREATE TABLE tickets (
    ticket_id      INTEGER PRIMARY KEY,
    event_id       INTEGER NOT NULL REFERENCES events (event_id),
    ticket_type    VARCHAR NOT NULL,
    price          DECIMAL(10, 2) NOT NULL,
    purchase_date  DATE NOT NULL
);""",
    dimA=EntitySpec("events", "event_id", "name", thai="งาน",
                     cat_cols={"city": ["กรุงเทพมหานคร", "เชียงใหม่", "ภูเก็ต"]}),
    fact=FactSpec("tickets", "ticket_id", "event_id", "purchase_date", thai="บัตร",
                   cat_cols={"ticket_type": ["VIP", "ทั่วไป", "นักเรียน"]}),
    measure_expr="tickets.price",
    measure_join="",
    seed_fn=_event_seed,
)


def _school_seed(rng):
    subjects = ["คณิตศาสตร์", "วิทยาศาสตร์", "ภาษาไทย", "ภาษาอังกฤษ"]
    grades = ["ป.4", "ป.5", "ป.6", "ม.1", "ม.2"]
    teachers = [(i, f"ครู{i}", rng.choice(subjects)) for i in range(1, 7)]
    students = [(i, f"นักเรียน{i}", rng.choice(grades)) for i in range(1, 25)]
    enrollments = [(i, rng.randint(1, 24), rng.randint(1, 6),
                     f"2025-{rng.randint(1,12):02d}-{rng.randint(1,28):02d}", round(rng.uniform(40, 100), 1))
                    for i in range(1, 30)]
    return {"teachers": teachers, "students": students, "enrollments": enrollments}


# school: ใช้เฉพาะ val (ห้ามเทรน) — ให้โมเดลเจอ schema ที่ไม่เคยเห็นตอนวัดผล
SCHOOL = SchemaSpec(
    name="school",
    thai="โรงเรียน",
    ddl="""CREATE TABLE teachers (
    teacher_id INTEGER PRIMARY KEY,
    name       VARCHAR NOT NULL,
    subject    VARCHAR NOT NULL
);

CREATE TABLE students (
    student_id INTEGER PRIMARY KEY,
    name       VARCHAR NOT NULL,
    grade_level VARCHAR NOT NULL
);

CREATE TABLE enrollments (
    enrollment_id INTEGER PRIMARY KEY,
    student_id    INTEGER NOT NULL REFERENCES students (student_id),
    teacher_id    INTEGER NOT NULL REFERENCES teachers (teacher_id),
    enroll_date   DATE NOT NULL,
    score         DECIMAL(5, 1) NOT NULL
);""",
    dimA=EntitySpec("teachers", "teacher_id", "name", thai="ครู",
                     cat_cols={"subject": ["คณิตศาสตร์", "วิทยาศาสตร์", "ภาษาไทย", "ภาษาอังกฤษ"]}),
    fact=FactSpec("enrollments", "enrollment_id", "teacher_id", "enroll_date", thai="การลงทะเบียน"),
    measure_expr="enrollments.score",
    measure_join="",
    dim2=EntitySpec("students", "student_id", "name", thai="นักเรียน",
                     cat_cols={"grade_level": ["ป.4", "ป.5", "ป.6", "ม.1", "ม.2"]}),
    dim2_join="JOIN students ON students.student_id = enrollments.student_id",
    seed_fn=_school_seed,
)


TRAIN_SCHEMAS = [SALES, RESTAURANT, WAREHOUSE, HR, EVENT]
VAL_ONLY_SCHEMAS = [SCHOOL]
ALL_SCHEMAS = TRAIN_SCHEMAS + VAL_ONLY_SCHEMAS
