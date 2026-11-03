"""เก็บผู้ใช้, dataset และประวัติการถาม

เจ้าของ: Suphakorn · งาน: S3 · สัญญาอินเทอร์เฟซ: docs/CONTRACT.md

dataset หนึ่งชุด = ไฟล์ DuckDB หนึ่งไฟล์ที่ DATA_DIR/datasets/<dataset_id>.duckdb
"""

import re
from pathlib import Path

import duckdb

from .config import get_settings

# id ต้องเป็นตัวอักษร/ตัวเลข/-/_ เท่านั้น กันการส่ง ../ หรือ path เต็มเข้ามา
_DATASET_ID = re.compile(r"[A-Za-z0-9_-]{1,64}")


def datasets_dir() -> Path:
    return (get_settings().DATA_DIR / "datasets").resolve()


def dataset_path(dataset_id: str) -> Path:
    """path ของไฟล์ dataset · id ที่ไม่ปลอดภัยถือว่าไม่มี dataset นั้น (KeyError)"""
    if not isinstance(dataset_id, str) or not _DATASET_ID.fullmatch(dataset_id):
        raise KeyError(dataset_id)
    root = datasets_dir()
    path = (root / f"{dataset_id}.duckdb").resolve()
    # กันอีกชั้นเผื่อ symlink พาออกนอกโฟลเดอร์
    if path.parent != root:
        raise KeyError(dataset_id)
    return path


def open_dataset(dataset_id: str) -> tuple[str, duckdb.DuckDBPyConnection]:
    """เปิด dataset แบบ read-only คืน (schema_ddl, connection) · ไม่มี dataset → KeyError"""
    path = dataset_path(dataset_id)
    if not path.is_file():
        raise KeyError(dataset_id)

    con = duckdb.connect(str(path), read_only=True)
    rows = con.execute(
        "SELECT sql FROM duckdb_tables() WHERE database_name = current_database() ORDER BY table_name"
    ).fetchall()
    ddl = "\n".join(sql.rstrip(";") + ";" for (sql,) in rows)
    return ddl, con
