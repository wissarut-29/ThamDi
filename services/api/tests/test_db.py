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
