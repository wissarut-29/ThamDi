"""ฟังก์ชันช่วยที่ pipeline ใช้ร่วมกัน

เจ้าของ: Chalakorn · งาน: C3 · สัญญาอินเทอร์เฟซ: docs/CONTRACT.md
"""

import re

import duckdb

_CREATE_TABLE_PATTERN = re.compile(r"CREATE\s+TABLE\s+(\w+)", re.IGNORECASE)


def table_names_from_ddl(schema_ddl: str) -> set[str]:
    """ดึงชื่อตารางทั้งหมดจาก DDL (CREATE TABLE ...) ใช้กำหนด allowed_tables ให้ sql_guard"""
    return set(_CREATE_TABLE_PATTERN.findall(schema_ddl))


def run_select(con: duckdb.DuckDBPyConnection, sql: str) -> tuple[list[str], list[list]]:
    """รัน SQL (ต้องผ่าน sql_guard มาแล้ว) บน DuckDB connection คืน (columns, rows)"""
    result = con.execute(sql)
    columns = [d[0] for d in result.description]
    rows = [list(row) for row in result.fetchall()]
    return columns, rows


def dry_run_executable(con: duckdb.DuckDBPyConnection, sql: str) -> bool:
    """ตรวจว่า sql รันได้จริงโดยไม่ดึงข้อมูลจริง (ใช้ EXPLAIN) สำหรับโหมด M3"""
    try:
        con.execute(f"EXPLAIN {sql}")
        return True
    except duckdb.Error:
        return False
