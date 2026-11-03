import sqlite3
import sys
from pathlib import Path

import duckdb
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app import db


@pytest.fixture
def data_dir(tmp_path, monkeypatch):
    monkeypatch.setenv("DATA_DIR", str(tmp_path))
    (tmp_path / "datasets").mkdir()
    con = duckdb.connect(str(tmp_path / "datasets" / "ds1.duckdb"))
    con.execute("CREATE TABLE sales (branch VARCHAR, amount DOUBLE)")
    con.execute("INSERT INTO sales VALUES ('สาขา 1', 100), ('สาขา 2', 250)")
    con.close()
    return tmp_path


def test_open_dataset_returns_ddl_and_connection(data_dir):
    ddl, con = db.open_dataset("ds1")
    assert "CREATE TABLE sales" in ddl
    assert con.execute("SELECT SUM(amount) FROM sales").fetchone()[0] == 350
    con.close()


def test_open_dataset_is_read_only(data_dir):
    _, con = db.open_dataset("ds1")
    with pytest.raises(duckdb.Error):
        con.execute("DELETE FROM sales")
    con.close()


def test_missing_dataset_raises_key_error(data_dir):
    with pytest.raises(KeyError):
        db.open_dataset("nope")


@pytest.mark.parametrize("bad_id", ["../x", "..\\x", "a/b", "", "ds1.duckdb", "/etc/passwd"])
def test_unsafe_dataset_id_rejected(data_dir, bad_id):
    (data_dir / "x.duckdb").touch()
    with pytest.raises(KeyError):
        db.open_dataset(bad_id)


def test_connection_closes_without_explicit_close(data_dir):
    # สัญญา: ผู้เรียกไม่ต้อง close เอง (CONTRACT หัวข้อ 2)
    def use_once():
        _, con = db.open_dataset("ds1")
        con.execute("SELECT 1")

    use_once()
    # ถ้า connection read-only ยังค้าง เปิดแบบเขียนได้จะ error เพราะตั้งค่าต่างกัน
    writer = duckdb.connect(str(data_dir / "datasets" / "ds1.duckdb"))
    writer.execute("INSERT INTO sales VALUES ('สาขา 3', 1)")
    writer.close()


def test_open_dataset_blocks_file_access_from_sql(data_dir):
    # ชั้นกันซ้อนจากรีวิว PR #9: ต่อให้ sql_guard พลาด SQL ก็อ่านไฟล์ในเครื่องไม่ได้
    (data_dir / "secret.csv").write_text("a,b\n1,2\n", encoding="utf-8")
    _, con = db.open_dataset("ds1")
    with pytest.raises(duckdb.Error):
        con.execute(f"SELECT * FROM read_csv('{(data_dir / 'secret.csv').as_posix()}')").fetchall()


def test_create_dataset_cleans_file_when_metadata_insert_fails(data_dir, monkeypatch):
    import pandas as pd

    db.init_db()
    before = set((data_dir / "datasets").iterdir())
    # owner ไม่มีในตาราง users ไม่ได้ทำให้พัง (SQLite ไม่บังคับ FK) จึงจำลองให้ insert พังเอง
    real_app_db = db._app_db

    def broken():
        con = real_app_db()
        con.execute("DROP TABLE datasets")
        return con

    monkeypatch.setattr(db, "_app_db", broken)
    with pytest.raises(sqlite3.OperationalError):
        db.create_dataset("demo", "x.csv", {"x": pd.DataFrame({"a": [1]})})
    assert set((data_dir / "datasets").iterdir()) == before


def test_schema_ddl_matches_training_format(data_dir):
    # รีวิว PR #9: duckdb_tables().sql ใส่ quote ให้คอลัมน์ไทยทุกตัว ไม่ตรงกับ eval/schemas ที่ใช้เทรน
    from app.agent.tools import table_names_from_ddl

    con = duckdb.connect(str(data_dir / "datasets" / "th.duckdb"))
    con.execute(
        'CREATE TABLE t_data (สาขา VARCHAR, ยอดขาย BIGINT, name VARCHAR, "order" INTEGER, "ยอด ขาย" DOUBLE)'
    )
    con.close()
    ddl, _ = db.open_dataset("th")
    assert ddl == (
        "CREATE TABLE t_data (\n"
        "    สาขา VARCHAR,\n"
        "    ยอดขาย BIGINT,\n"
        "    name VARCHAR,\n"
        '    "order" INTEGER,\n'
        '    "ยอด ขาย" DOUBLE\n'
        ");"
    )
    assert table_names_from_ddl(ddl) == {"t_data"}
    duckdb.connect().execute(ddl)  # DDL ที่สร้างต้องรันได้จริง
