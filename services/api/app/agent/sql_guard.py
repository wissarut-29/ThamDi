"""อนุญาตเฉพาะ SELECT ตารางของ dataset นั้น ห้ามคำสั่งแก้/ลบข้อมูล

เจ้าของ: Chalakorn · งาน: C3 · สัญญาอินเทอร์เฟซ: docs/CONTRACT.md

ใช้ sqlglot แยกวิเคราะห์ SQL จริง (ไม่ใช่ regex อย่างเดียว) เพื่อตรวจ:
- ต้องเป็น SELECT หรือ WITH...SELECT (CTE) คำสั่งเดียวเท่านั้น ห้ามต่อกันด้วย ;
- ห้าม DDL/DML/PRAGMA/ATTACH/COPY/INSTALL ซ้อนอยู่ที่ไหนก็ตาม รวมถึงซ้อนอยู่ใน CTE
  (เช่น `WITH x AS (DELETE FROM t RETURNING *) SELECT * FROM x` ต้อง parse ทั้งต้นไม้ ไม่ใช่เช็กแค่ root)
- อ้างได้เฉพาะตารางของ dataset นั้น (ไม่รวมชื่อ CTE ที่นิยามเองในคำสั่ง)
- ห้ามฟังก์ชันอ่านไฟล์ (read_csv, read_parquet, glob ฯลฯ)
- เติม LIMIT ให้ถ้ายังไม่มี
"""

import sqlglot
from sqlglot import exp

DEFAULT_LIMIT = 1000

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


def _cte_names(stmt: exp.Expression) -> set[str]:
    with_ = stmt.args.get("with_")
    if not with_:
        return set()
    return {cte.alias for cte in with_.expressions}


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
    if not isinstance(stmt, exp.Select):
        raise SqlGuardError(f"อนุญาตเฉพาะ SELECT/WITH เท่านั้น ไม่ใช่ {type(stmt).__name__}")

    for node in stmt.walk():
        if isinstance(node, FORBIDDEN_STATEMENT_TYPES):
            raise SqlGuardError(f"พบคำสั่งต้องห้ามซ้อนอยู่ใน SQL: {type(node).__name__}")
        if isinstance(node, (exp.Func, exp.Anonymous)) and _is_forbidden_func(node):
            raise SqlGuardError("ห้ามใช้ฟังก์ชันอ่านไฟล์")

    tables_used = {t.name for t in stmt.find_all(exp.Table)} - _cte_names(stmt)
    disallowed = tables_used - set(allowed_tables)
    if disallowed:
        raise SqlGuardError(f"อ้างตารางที่ไม่ได้รับอนุญาตสำหรับ dataset นี้: {sorted(disallowed)}")

    if stmt.args.get("limit") is None:
        stmt = stmt.limit(default_limit)

    return stmt.sql(dialect="duckdb")
