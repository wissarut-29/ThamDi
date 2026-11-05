"""เก็บผู้ใช้, dataset และประวัติการถาม

เจ้าของ: Suphakorn · งาน: S3 · สัญญาอินเทอร์เฟซ: docs/CONTRACT.md

dataset หนึ่งชุด = ไฟล์ DuckDB หนึ่งไฟล์ที่ DATA_DIR/datasets/<dataset_id>.duckdb
"""

import hashlib
import json
import re
import sqlite3
import unicodedata
import uuid
from contextlib import closing
from datetime import datetime, timezone
from pathlib import Path
from typing import TYPE_CHECKING

import duckdb

from .config import get_settings

if TYPE_CHECKING:
    import pandas

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

    # ปิดการอ่านไฟล์/เน็ตจากใน SQL อีกชั้น เผื่อ sql_guard พลาด (read_csv ฯลฯ จะได้ PermissionException)
    con = duckdb.connect(str(path), read_only=True, config={"enable_external_access": False})
    return schema_ddl(con), con


# keyword ระดับ reserved ใช้เป็นชื่อคอลัมน์ตรง ๆ ไม่ได้ ต้องใส่ "..." (เช่น order, group, select)
_RESERVED = {
    k
    for (k,) in duckdb.connect()
    .execute("SELECT keyword_name FROM duckdb_keywords() WHERE keyword_category = 'reserved'")
    .fetchall()
}


def _ident(name: str) -> str:
    # ใส่ quote เฉพาะเมื่อจำเป็น ภาษาไทยไม่ต้อง quote (DuckDB กับ sqlglot รับได้)
    plain = (
        name
        and not name[0].isdigit()
        and all(ch == "_" or ch.isalnum() or unicodedata.category(ch).startswith("M") for ch in name)
        and name.lower() not in _RESERVED
    )
    return name if plain else '"' + name.replace('"', '""') + '"'


def schema_ddl(con: duckdb.DuckDBPyConnection) -> str:
    """DDL รูปแบบเดียวกับ eval/schemas/*.sql ที่โมเดลเห็นตอนเทรน · ไม่ใช้ duckdb_tables().sql
    เพราะใส่ quote ให้ชื่อไทย/keyword ทุกตัว และรูปแบบเปลี่ยนตามเวอร์ชัน DuckDB"""
    rows = con.execute(
        "SELECT table_name, column_name, data_type FROM information_schema.columns "
        "WHERE table_catalog = current_database() ORDER BY table_name, ordinal_position"
    ).fetchall()
    tables: dict[str, list[str]] = {}
    for table, column, data_type in rows:
        tables.setdefault(table, []).append(f"    {_ident(column)} {data_type}")
    return "\n\n".join(
        f"CREATE TABLE {_ident(t)} (\n" + ",\n".join(cols) + "\n);" for t, cols in tables.items()
    )


# ---------- ข้อมูลของแอป (ผู้ใช้, รายการ dataset, ประวัติ) เก็บใน SQLite ไฟล์เดียว ----------
# แยกจากไฟล์ DuckDB ของ dataset เพื่อให้ connection ของ dataset เปิดแบบ read-only ได้เสมอ

_SCHEMA = """
CREATE TABLE IF NOT EXISTS users (
    username      TEXT PRIMARY KEY,
    password_hash TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS datasets (
    dataset_id TEXT PRIMARY KEY,
    owner      TEXT NOT NULL REFERENCES users(username),
    name       TEXT NOT NULL,
    tables     TEXT NOT NULL,
    created_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS history (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    username   TEXT NOT NULL,
    dataset_id TEXT NOT NULL,
    question   TEXT NOT NULL,
    status     TEXT NOT NULL,
    sql        TEXT,
    answer     TEXT NOT NULL,
    created_at TEXT NOT NULL
);
"""


def _app_db() -> sqlite3.Connection:
    path = get_settings().DATA_DIR / "app.sqlite3"
    path.parent.mkdir(parents=True, exist_ok=True)
    con = sqlite3.connect(path)
    con.row_factory = sqlite3.Row
    return con


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def init_db() -> None:
    with closing(_app_db()) as con, con:
        con.executescript(_SCHEMA)
    datasets_dir().mkdir(parents=True, exist_ok=True)


def upsert_user(username: str, password_hash: str) -> None:
    with closing(_app_db()) as con, con:
        con.execute(
            "INSERT INTO users VALUES (?, ?) "
            "ON CONFLICT(username) DO UPDATE SET password_hash = excluded.password_hash",
            (username, password_hash),
        )


def create_user(username: str, password_hash: str) -> bool:
    """สร้างผู้ใช้ใหม่ · ชื่อซ้ำ = False (ไม่ทับรหัสของคนเดิม ต่างจาก upsert_user)"""
    try:
        with closing(_app_db()) as con, con:
            con.execute("INSERT INTO users VALUES (?, ?)", (username, password_hash))
    except sqlite3.IntegrityError:
        return False
    return True


def count_users() -> int:
    with closing(_app_db()) as con:
        return con.execute("SELECT COUNT(*) FROM users").fetchone()[0]


def delete_user(username: str) -> None:
    with closing(_app_db()) as con, con:
        con.execute("DELETE FROM users WHERE username = ?", (username,))


def get_password_hash(username: str) -> str | None:
    with closing(_app_db()) as con:
        row = con.execute("SELECT password_hash FROM users WHERE username = ?", (username,)).fetchone()
    return row["password_hash"] if row else None


def user_exists(username: str) -> bool:
    return get_password_hash(username) is not None


def create_dataset(owner: str, name: str, tables: dict[str, "pandas.DataFrame"]) -> dict:
    """เขียนตารางลงไฟล์ DuckDB ใหม่ แล้วบันทึกว่าเป็นของ owner · คืน {dataset_id, name, tables}"""
    dataset_id = uuid.uuid4().hex[:12]
    path = dataset_path(dataset_id)
    con = duckdb.connect(str(path))
    try:
        for table, frame in tables.items():
            con.register("_upload", frame)
            con.execute(f'CREATE TABLE "{table}" AS SELECT * FROM _upload')
            con.unregister("_upload")
    except Exception:
        con.close()
        path.unlink(missing_ok=True)
        raise
    con.close()

    names = list(tables)
    try:
        with closing(_app_db()) as app, app:
            app.execute(
                "INSERT INTO datasets VALUES (?, ?, ?, ?, ?)",
                (dataset_id, owner, name, json.dumps(names, ensure_ascii=False), _now()),
            )
    except Exception:
        # ไม่ให้ไฟล์ .duckdb ค้างโดยไม่มี record ชี้ถึง
        path.unlink(missing_ok=True)
        raise
    return {"dataset_id": dataset_id, "name": name, "tables": names}


def get_dataset_meta(dataset_id: str) -> dict | None:
    with closing(_app_db()) as con:
        row = con.execute("SELECT * FROM datasets WHERE dataset_id = ?", (dataset_id,)).fetchone()
    if row is None:
        return None
    return {**dict(row), "tables": json.loads(row["tables"])}


def list_datasets(owner: str) -> list[dict]:
    with closing(_app_db()) as con:
        rows = con.execute(
            # rowid ตัดสินตอนสร้างในวินาทีเดียวกัน (เช่น ไฟล์ตัวอย่างของ demo) ให้ตัวที่สร้างหลังสุดอยู่บนเสมอ
            "SELECT dataset_id, name, tables FROM datasets WHERE owner = ? "
            "ORDER BY created_at DESC, rowid DESC",
            (owner,),
        ).fetchall()
    datasets = [{**dict(r), "tables": json.loads(r["tables"])} for r in rows]
    # อ่านข้อมูลทั้งไฟล์ (fingerprint) เฉพาะกลุ่มที่ชื่อไฟล์+ชื่อตารางซ้ำกัน ไฟล์ที่ไม่ซ้ำไม่ต้องเปิดเลย
    groups: dict[tuple[str, tuple[str, ...]], list[dict]] = {}
    for dataset in datasets:
        groups.setdefault((dataset["name"], tuple(dataset["tables"])), []).append(dataset)
    for members in groups.values():
        if len(members) < 2:
            continue
        seen: dict[str, str] = {}  # fingerprint -> dataset_id ของตัวที่ใหม่สุด (ตัวที่แสดง)
        for dataset in members:
            fingerprint = _dataset_fingerprint(dataset)
            if fingerprint is None:
                continue
            if fingerprint in seen:
                dataset["duplicate_of"] = seen[fingerprint]
            else:
                seen[fingerprint] = dataset["dataset_id"]
    return datasets


def _dataset_fingerprint(dataset: dict) -> str | None:
    """คืน fingerprint ตาม schema และทุกแถว เพื่อซ่อนรายการอัปโหลดที่เหมือนกันโดยไม่ลบข้อมูล."""
    try:
        _, con = open_dataset(dataset["dataset_id"])
    except (KeyError, duckdb.Error):
        return None
    digest = hashlib.sha256()
    try:
        for table in dataset["tables"]:
            name = '"' + table.replace('"', '""') + '"'
            cursor = con.execute(f"SELECT * FROM {name}")
            schema = [(column[0], str(column[1])) for column in cursor.description]
            digest.update(json.dumps((table, schema), ensure_ascii=False).encode("utf-8"))
            while batch := cursor.fetchmany(4096):
                for row in batch:
                    digest.update(json.dumps(row, ensure_ascii=False, default=str).encode("utf-8"))
                    digest.update(b"\n")
    except duckdb.Error:
        return None
    finally:
        con.close()
    return digest.hexdigest()


def add_history(
    username: str, dataset_id: str, question: str, status: str, sql: str | None, answer: str
) -> None:
    with closing(_app_db()) as con, con:
        con.execute(
            "INSERT INTO history (username, dataset_id, question, status, sql, answer, created_at) "
            "VALUES (?, ?, ?, ?, ?, ?, ?)",
            (username, dataset_id, question, status, sql, answer, _now()),
        )


def list_history(username: str, dataset_id: str | None = None, limit: int = 50) -> list[dict]:
    """ประวัติคำถามของผู้ใช้ ใหม่สุดก่อน · ชื่อไฟล์จากตาราง datasets (ไฟล์ถูกลบไปแล้ว = None)"""
    sql = (
        "SELECT h.id, h.dataset_id, d.name AS dataset_name, h.question, h.status, h.sql, h.answer, "
        "h.created_at FROM history h LEFT JOIN datasets d ON d.dataset_id = h.dataset_id "
        "WHERE h.username = ?"
    )
    params: list = [username]
    if dataset_id is not None:
        sql += " AND h.dataset_id = ?"
        params.append(dataset_id)
    sql += " ORDER BY h.id DESC LIMIT ?"
    params.append(limit)
    with closing(_app_db()) as con:
        rows = con.execute(sql, params).fetchall()
    return [dict(r) for r in rows]
