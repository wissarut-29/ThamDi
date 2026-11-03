"""อนุญาตเฉพาะ SELECT ตารางของ dataset นั้น ห้ามคำสั่งแก้/ลบข้อมูล

เจ้าของ: Chalakorn · งาน: C3 · สัญญาอินเทอร์เฟซ: docs/CONTRACT.md

ใช้ sqlglot แยกวิเคราะห์ SQL จริง (ไม่ใช่ regex อย่างเดียว) เพื่อตรวจ:
- ต้องเป็น SELECT/WITH (CTE)/UNION/INTERSECT/EXCEPT คำสั่งเดียวเท่านั้น ห้ามต่อกันด้วย ;
- ห้าม DDL/DML/PRAGMA/ATTACH/COPY/INSTALL ซ้อนอยู่ที่ไหนก็ตาม รวมถึงซ้อนอยู่ใน CTE
  (เช่น `WITH x AS (DELETE FROM t RETURNING *) SELECT * FROM x` ต้อง parse ทั้งต้นไม้ ไม่ใช่เช็กแค่ root)
- อ้างได้เฉพาะตารางของ dataset นั้น (ไม่รวมชื่อ CTE ที่นิยามเองในคำสั่ง)
- ห้ามฟังก์ชันอ่านไฟล์ (read_csv, read_parquet, glob ฯลฯ)
- เติม LIMIT ให้ถ้ายังไม่มี

ทดสอบกับ sqlglot 30.27.0 (ยังไม่มีประกาศ dependency นี้ใน requirements ของ services/api —
ต้องให้ Suphakorn เพิ่ม ดู docs/ISSUES.md) โครงสร้าง node (เช่นชื่อคีย์ภายใน args) อาจเปลี่ยนได้
ตามเวอร์ชัน จึงใช้ find_all()/traverse_scope() แทนการเข้าถึง args โดยตรงให้มากที่สุดเพื่อลด
ความเสี่ยงนี้ — การอ้างตารางที่อนุญาต ใช้ traverse_scope() โดยเฉพาะ (ไม่ใช่แค่ find_all(exp.Table)
ลบด้วยชื่อ CTE) เพราะต้องรู้ขอบเขตจริงของแต่ละชื่อ ไม่งั้นตั้งชื่อ CTE ซ้ำกับตารางจริงจะหลบ guard ได้
(ดู docstring ของ _real_tables_used)
"""

import sqlglot
from sqlglot import exp
from sqlglot.optimizer.scope import traverse_scope

DEFAULT_LIMIT = 1000
# ชนิด query ที่อนุญาตเป็น root statement (SELECT เดี่ยว, WITH...SELECT และ set operation)
ALLOWED_ROOT_TYPES = (exp.Select, exp.Union, exp.Intersect, exp.Except)

# คำสั่งต้องห้าม เช็กทั้งต้นไม้ ไม่ใช่แค่ root เพราะ DML ซ้อนอยู่ใน CTE ได้ (ดู docstring)
FORBIDDEN_STATEMENT_TYPES = (
    exp.Insert, exp.Update, exp.Delete, exp.Drop, exp.Create, exp.Alter,
    exp.Command, exp.Attach, exp.Copy, exp.Pragma, exp.Install,
)
# ฟังก์ชันอ่านไฟล์: ชื่อคลาสที่ sqlglot รู้จักขึ้นต้นด้วย read (ReadCSV, ReadParquet, ...)
# หรือฟังก์ชันที่ sqlglot ไม่รู้จัก (Anonymous) ที่ชื่อเข้าเค้าฟังก์ชันอ่านไฟล์
FORBIDDEN_FUNC_SUBSTRINGS = ("read_", "glob", "sniff_csv", "scan_parquet", "copy_from", "import_")


class SqlGuardError(ValueError):
    """SQL ไม่ผ่านการตรวจความปลอดภัย"""


def _real_tables_used(stmt: exp.Expression) -> set[str]:
    """ชื่อตารางจริงที่ถูกอ้างถึง (ไม่รวมชื่อ CTE ที่นิยามเองในคำสั่ง)

    ห้ามใช้ find_all(exp.Table) ลบด้วยชุดชื่อ CTE ทั้งหมดแบบ global เพราะถ้าตั้งชื่อ CTE
    ซ้ำกับตารางจริง (เช่น `WITH secret AS (SELECT * FROM secret) SELECT * FROM secret`)
    การลบแบบ global จะลบการอ้างถึงตารางจริง "secret" ที่อยู่*ข้างใน*นิยาม CTE ไปด้วย ทำให้
    guard มองไม่เห็นว่ามีการอ่านตารางจริงชื่อนี้อยู่ — ต้องรู้ "ขอบเขต" ว่าชื่อไหนในจุดไหนของ
    คำสั่งอ้างถึง CTE จริง ๆ จึงใช้ traverse_scope ของ sqlglot ซึ่งไล่ตามขอบเขตแบบเดียวกับที่
    ตัว parser ของฐานข้อมูลจริงทำ (เทียบ node ไม่ใช่เทียบชื่อ)
    """
    tables = set()
    for scope in traverse_scope(stmt):
        for source in scope.sources.values():
            if isinstance(source, exp.Table):
                tables.add(source.name)
    return tables


def _is_forbidden_func(node: exp.Expression) -> bool:
    cls_name = type(node).__name__.lower()
    if cls_name.startswith("read"):
        return True
    if isinstance(node, exp.Anonymous):
        name = (node.this or "").lower()
        return any(s in name for s in FORBIDDEN_FUNC_SUBSTRINGS)
    return False


def check_sql(sql: str, allowed_tables: set[str], default_limit: int = DEFAULT_LIMIT) -> str:
    """ตรวจ sql ว่าปลอดภัยสำหรับ dataset ที่มีตารางชื่อใน allowed_tables

    คืน SQL ที่ผ่านการตรวจ (เติม LIMIT ให้ถ้ายังไม่มี) ถ้าไม่ผ่าน raise SqlGuardError
    """
    if not sql or not sql.strip():
        raise SqlGuardError("SQL ว่าง")

    try:
        statements = [s for s in sqlglot.parse(sql, read="duckdb") if s is not None]
    except sqlglot.errors.ParseError as exc:
        raise SqlGuardError(f"แยกวิเคราะห์ SQL ไม่ได้: {exc}") from exc

    if len(statements) != 1:
        raise SqlGuardError("ต้องมี SQL เดียวเท่านั้น ห้ามต่อกันด้วย ;")

    stmt = statements[0]
    if not isinstance(stmt, ALLOWED_ROOT_TYPES):
        raise SqlGuardError(
            f"อนุญาตเฉพาะ SELECT/WITH/UNION/INTERSECT/EXCEPT เท่านั้น ไม่ใช่ {type(stmt).__name__}"
        )

    for node in stmt.walk():
        if isinstance(node, FORBIDDEN_STATEMENT_TYPES):
            raise SqlGuardError(f"พบคำสั่งต้องห้ามซ้อนอยู่ใน SQL: {type(node).__name__}")
        if isinstance(node, (exp.Func, exp.Anonymous)) and _is_forbidden_func(node):
            raise SqlGuardError("ห้ามใช้ฟังก์ชันอ่านไฟล์")

    tables_used = _real_tables_used(stmt)
    disallowed = tables_used - set(allowed_tables)
    if disallowed:
        raise SqlGuardError(f"อ้างตารางที่ไม่ได้รับอนุญาตสำหรับ dataset นี้: {sorted(disallowed)}")

    if stmt.args.get("limit") is None:
        stmt = stmt.limit(default_limit)

    return stmt.sql(dialect="duckdb")
