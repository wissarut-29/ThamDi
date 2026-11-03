import os
import subprocess
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from ml.format import build_prompt

from app.agent import model

SCHEMA = "CREATE TABLE sales (id INTEGER, branch VARCHAR, amount DOUBLE);"


@pytest.fixture(autouse=True)
def fake_backend(monkeypatch):
    monkeypatch.setenv("MODEL_BACKEND", "fake")


@pytest.mark.parametrize("n", [1, 4])
def test_fake_returns_n_candidates(n):
    out = model.generate_sql(build_prompt("ยอดขายทั้งหมดเท่าไหร่", SCHEMA), n)
    assert len(out) == n
    assert out[0] == "SELECT COUNT(*) AS n FROM sales"


def test_fake_refuses_delete_question():
    out = model.generate_sql(build_prompt("ลบตาราง sales ให้หน่อย", SCHEMA), 2)
    assert out == ["<REFUSE>", "<REFUSE>"]


def test_fake_ignores_refuse_words_in_schema():
    schema = "CREATE TABLE drop_log (id INTEGER);"
    out = model.generate_sql(build_prompt("มีกี่แถว", schema), 1)
    assert out == ["SELECT COUNT(*) AS n FROM drop_log"]


def test_fake_does_not_import_torch():
    # รันใน process ใหม่ เพราะ process ของ pytest อาจมี torch จากเทสต์อื่นอยู่แล้ว
    code = "import sys; import app.agent.model as m; m.generate_sql('x', 1); print('torch' in sys.modules)"
    out = subprocess.run(
        [sys.executable, "-c", code],
        cwd=Path(__file__).resolve().parents[1],
        env={**os.environ, "MODEL_BACKEND": "fake"},
        capture_output=True,
        text=True,
        check=True,
    )
    assert out.stdout.strip() == "False"


def test_model_info_has_all_keys():
    info = model.model_info()
    assert set(info) == {"name", "base_model", "version", "backend", "loaded"}
    assert info["backend"] == "fake"
    assert info["loaded"] is True


def test_unknown_backend_raises(monkeypatch):
    monkeypatch.setenv("MODEL_BACKEND", "bogus")
    with pytest.raises(ValueError):
        model.generate_sql("x", 1)


def test_local_without_model_files_is_not_loaded(monkeypatch, tmp_path):
    # API ต้องเริ่มได้แม้ไม่มีไฟล์โมเดล: loaded=False และ generate_sql raise ModelNotReady
    monkeypatch.setenv("MODEL_BACKEND", "local")
    monkeypatch.setenv("MODEL_PATH", str(tmp_path / "missing"))
    monkeypatch.setattr(model, "_local", model._LocalModel())
    model.preload()
    info = model.model_info()
    assert info["backend"] == "local"
    assert info["loaded"] is False
    with pytest.raises(model.ModelNotReady):
        model.generate_sql("x", 1)
