"""ตัวสร้างคำถาม+SQL ต่อหมวด ทำงานแบบเดียวกันได้กับทุก schema ใน schemas.py

แต่ละฟังก์ชันคืน (question, sql) โดย sql เป็น SELECT ล้วน (รันผ่าน DuckDB จริง ตรวจใน gen_data.py)
ยกเว้น gen_refuse ที่คืน sql เป็น "<REFUSE>" หรือ "<CLARIFY>"
"""

import calendar

THAI_MONTHS = [
    "มกราคม", "กุมภาพันธ์", "มีนาคม", "เมษายน", "พฤษภาคม", "มิถุนายน",
    "กรกฎาคม", "สิงหาคม", "กันยายน", "ตุลาคม", "พฤศจิกายน", "ธันวาคม",
]

# คำเรียกภาษาไทยของคอลัมน์หมวดหมู่ ใช้แต่งประโยคคำถามเท่านั้น (SQL ยังใช้ชื่อคอลัมน์จริง)
COLUMN_THAI = {
    "province": "จังหวัด", "segment": "ระดับลูกค้า", "channel": "ช่องทาง",
    "position": "ตำแหน่ง", "branch": "สาขา", "category": "หมวดหมู่",
    "city": "เมือง", "shipment_type": "ประเภทการขนส่ง", "location": "ที่ตั้ง",
    "subject": "วิชา", "grade_level": "ระดับชั้น", "ticket_type": "ประเภทบัตร",
}


def _col_thai(col: str) -> str:
    return COLUMN_THAI.get(col, col)


def _pick_cat(spec, rng):
    """เลือกคอลัมน์หมวดหมู่แบบสุ่มได้จาก dimA หรือ fact (ตัวไหนมีก็ใช้ตัวนั้น)"""
    choices = []
    for col, vals in spec.dimA.cat_cols.items():
        choices.append((spec.dimA.table, spec.dimA.thai, col, vals))
    for col, vals in spec.fact.cat_cols.items():
        choices.append((spec.fact.table, spec.fact.thai, col, vals))
    return rng.choice(choices)


def gen_filter(spec, rng):
    table, entity_thai, col, vals = _pick_cat(spec, rng)
    value = rng.choice(vals)
    question = f"มี{entity_thai}กี่รายการที่{_col_thai(col)}เป็น{value} ใน{spec.thai}"
    sql = f"SELECT COUNT(*) FROM {table} WHERE {col} = '{value}'"
    return question, sql


def _measure_from(spec):
    return f"{spec.fact.table} {spec.measure_join}".strip()


def gen_aggregate(spec, rng):
    agg = rng.choice(["SUM", "AVG", "COUNT"])
    expr = "*" if agg == "COUNT" else spec.measure_expr
    verb = {"SUM": "รวมทั้งหมด", "AVG": "เฉลี่ย", "COUNT": "จำนวนรายการ"}[agg]

    if spec.dimA.cat_cols and rng.random() < 0.5:
        col, vals = rng.choice(list(spec.dimA.cat_cols.items()))
        value = rng.choice(vals)
        question = f"{verb}ของ{spec.thai}ที่{spec.dimA.thai}มี{_col_thai(col)}เป็น{value}คือเท่าไหร่"
        sql = (
            f"SELECT {agg}({expr}) FROM {spec.fact.table} "
            f"JOIN {spec.dimA.table} ON {spec.dimA.table}.{spec.dimA.pk} = {spec.fact.table}.{spec.fact.fk_to_dimA} "
            f"{spec.measure_join} WHERE {spec.dimA.table}.{col} = '{value}'"
        )
        return question, sql.strip()

    question = f"{verb}ของ{spec.thai}ทั้งหมดคือเท่าไหร่"
    sql = f"SELECT {agg}({expr}) FROM {_measure_from(spec)}"
    return question, sql


def gen_group(spec, rng):
    if spec.dimA.cat_cols:
        col, _ = rng.choice(list(spec.dimA.cat_cols.items()))
        group_table = spec.dimA.table
    else:
        col, _ = rng.choice(list(spec.fact.cat_cols.items()))
        group_table = spec.fact.table

    join_clause = (
        f"JOIN {spec.dimA.table} ON {spec.dimA.table}.{spec.dimA.pk} = {spec.fact.table}.{spec.fact.fk_to_dimA} "
        if group_table == spec.dimA.table else ""
    )
    question = f"แต่ละ{_col_thai(col)}ของ{spec.thai}มียอดรวมเท่าไหร่"
    sql = (
        f"SELECT {group_table}.{col}, SUM({spec.measure_expr}) AS total "
        f"FROM {spec.fact.table} {join_clause}{spec.measure_join} "
        f"GROUP BY {group_table}.{col}"
    )
    return question, sql.strip()


def gen_rank(spec, rng):
    k = rng.choice([3, 5, 10])
    direction = rng.choice(["มากที่สุด", "น้อยที่สุด"])
    order = "DESC" if direction == "มากที่สุด" else "ASC"
    question = f"{spec.dimA.thai}ใน{spec.thai}ที่มียอดรวม{direction} {k} อันดับ มีอะไรบ้าง"
    sql = (
        f"SELECT {spec.dimA.table}.{spec.dimA.name_col}, SUM({spec.measure_expr}) AS total "
        f"FROM {spec.fact.table} "
        f"JOIN {spec.dimA.table} ON {spec.dimA.table}.{spec.dimA.pk} = {spec.fact.table}.{spec.fact.fk_to_dimA} "
        f"{spec.measure_join} "
        f"GROUP BY {spec.dimA.table}.{spec.dimA.name_col} "
        f"ORDER BY total {order} LIMIT {k}"
    )
    return question, sql.strip()


def gen_join(spec, rng):
    if spec.dim2 is not None:
        col, _vals = rng.choice(list(spec.dim2.cat_cols.items())) if spec.dim2.cat_cols else (spec.dim2.name_col, None)
        question = f"{spec.dim2.thai}หมวดไหนของ{spec.thai}มียอดรวมมากที่สุด"
        # measure_join บางสคีมา (เช่น restaurant, warehouse) join ไปถึง dim2 อยู่แล้ว
        # เพื่อให้ measure_expr ใช้ได้ ถ้าเป็นแบบนั้นไม่ต้อง join dim2 ซ้ำ (ชื่อตารางชนกัน)
        extra_join = "" if spec.dim2.table in spec.measure_join else spec.dim2_join
        sql = (
            f"SELECT {spec.dim2.table}.{col}, SUM({spec.measure_expr}) AS total "
            f"FROM {spec.fact.table} {spec.measure_join} {extra_join} "
            f"GROUP BY {spec.dim2.table}.{col} ORDER BY total DESC LIMIT 1"
        )
        return question, sql.strip()

    # ไม่มี dim2: ใช้ join dimA-fact ธรรมดาแทน
    question = f"{spec.dimA.thai}ไหนมี{spec.fact.thai}มากที่สุดใน{spec.thai}"
    sql = (
        f"SELECT {spec.dimA.table}.{spec.dimA.name_col}, COUNT(*) AS n "
        f"FROM {spec.fact.table} "
        f"JOIN {spec.dimA.table} ON {spec.dimA.table}.{spec.dimA.pk} = {spec.fact.table}.{spec.fact.fk_to_dimA} "
        f"GROUP BY {spec.dimA.table}.{spec.dimA.name_col} ORDER BY n DESC LIMIT 1"
    )
    return question, sql


def gen_thai_date(spec, rng):
    date_col = spec.fact.date_col
    table = spec.fact.table
    entity_thai = spec.fact.thai
    kind = rng.choice(["absolute", "relative_month", "relative_year", "relative_days"])

    if kind == "absolute":
        year_ad = rng.randint(2023, 2025)
        year_be = year_ad + 543
        month = rng.randint(1, 12)
        month_thai = THAI_MONTHS[month - 1]
        last_day = calendar.monthrange(year_ad, month)[1]
        question = f"มี{entity_thai}กี่รายการใน{spec.thai}เดือน{month_thai} ปี พ.ศ. {year_be}"
        sql = (
            f"SELECT COUNT(*) FROM {table} WHERE {date_col} >= '{year_ad}-{month:02d}-01' "
            f"AND {date_col} <= '{year_ad}-{month:02d}-{last_day:02d}'"
        )
        return question, sql

    if kind == "relative_month":
        question = f"มี{entity_thai}กี่รายการใน{spec.thai}เดือนที่แล้ว"
        sql = (
            f"SELECT COUNT(*) FROM {table} "
            f"WHERE date_trunc('month', {date_col}) = date_trunc('month', CURRENT_DATE - INTERVAL '1 month')"
        )
        return question, sql

    if kind == "relative_year":
        question = f"มี{entity_thai}กี่รายการใน{spec.thai}ปีนี้"
        sql = f"SELECT COUNT(*) FROM {table} WHERE date_part('year', {date_col}) = date_part('year', CURRENT_DATE)"
        return question, sql

    n_days = rng.choice([7, 30])
    question = f"มี{entity_thai}กี่รายการใน{spec.thai}ช่วง {n_days} วันที่ผ่านมา"
    sql = f"SELECT COUNT(*) FROM {table} WHERE {date_col} >= CURRENT_DATE - INTERVAL '{n_days} days'"
    return question, sql


DESTRUCTIVE_TEMPLATES = [
    "ลบข้อมูล{entity}ทั้งหมดออกจากระบบ",
    "แก้ไขข้อมูล{entity}ทุกแถวให้เป็นค่าเดียวกัน",
    "อัปเดตราคาในระบบใหม่ทั้งหมด",
    "ลบแถวที่ซ้ำกันในตาราง{entity}",
    "เพิ่มข้อมูล{entity}ใหม่เข้าไปในระบบตรง ๆ",
]
OUT_OF_SCOPE_QUESTIONS = [
    "วันนี้อากาศเป็นอย่างไร",
    "ราคาน้ำมันวันนี้เท่าไหร่",
    "แนะนำร้านอาหารใกล้ฉันหน่อย",
    "ทีมฟุตบอลที่ชอบคือทีมอะไร",
    "แปลประโยคนี้เป็นภาษาอังกฤษให้หน่อย",
]
CLARIFY_QUESTIONS = [
    "ดูข้อมูลของเขาหน่อย",
    "ช่วยสรุปให้ดูหน่อย",
    "อันนั้นเป็นยังไงบ้าง",
    "เอาตัวเลขที่ว่ามาดูหน่อย",
]


def gen_refuse(spec, rng):
    kind = rng.choice(["destructive", "out_of_scope", "clarify"])
    if kind == "destructive":
        entity = rng.choice([spec.fact.thai, spec.dimA.thai])
        question = rng.choice(DESTRUCTIVE_TEMPLATES).format(entity=entity)
        return question, "<REFUSE>"
    if kind == "out_of_scope":
        return rng.choice(OUT_OF_SCOPE_QUESTIONS), "<REFUSE>"
    return rng.choice(CLARIFY_QUESTIONS), "<CLARIFY>"


GENERATORS = {
    "filter": gen_filter,
    "aggregate": gen_aggregate,
    "group": gen_group,
    "rank": gen_rank,
    "join": gen_join,
    "thai_date": gen_thai_date,
    "refuse": gen_refuse,
}
