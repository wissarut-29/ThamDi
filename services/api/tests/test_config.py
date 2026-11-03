import logging
import sys
from pathlib import Path

import pytest
from pydantic import ValidationError

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app import config


@pytest.fixture(autouse=True)
def no_dotenv(monkeypatch):
    # ไม่ให้ .env จริงในเครื่องมีผลกับเทสต์
    monkeypatch.setitem(config.Settings.model_config, "env_file", None)
    for name in ("MODEL_BACKEND", "MODEL_PATH", "JWT_SECRET", "DEMO_PASSWORD", "CORS_ORIGINS", "DATA_DIR"):
        monkeypatch.delenv(name, raising=False)


def test_defaults():
    s = config.get_settings()
    assert s.MODEL_BACKEND == "fake"
    assert s.DEMO_MODE is False
    assert s.DATA_DIR == config.REPO_ROOT / "data"
    assert s.MODEL_PATH == config.REPO_ROOT / "models" / "thamdi"


def test_absolute_path_kept(monkeypatch, tmp_path):
    monkeypatch.setenv("DATA_DIR", str(tmp_path))
    assert config.get_settings().DATA_DIR == tmp_path


def test_unknown_backend_rejected(monkeypatch):
    monkeypatch.setenv("MODEL_BACKEND", "bogus")
    with pytest.raises(ValidationError):
        config.get_settings()


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("", []),
        ("*", []),
        ("http://localhost:3000", ["http://localhost:3000"]),
        (" http://a:3000 , http://b:3000 ,", ["http://a:3000", "http://b:3000"]),
    ],
)
def test_cors_origins_never_wildcard(monkeypatch, raw, expected):
    monkeypatch.setenv("CORS_ORIGINS", raw)
    assert config.get_settings().cors_origins == expected


def test_placeholder_secret_warns_only_on_local(monkeypatch, caplog):
    monkeypatch.setenv("JWT_SECRET", "change-me")
    monkeypatch.setenv("DEMO_PASSWORD", "a-real-password")
    with caplog.at_level(logging.WARNING):
        assert config.get_settings().warn_insecure() == ["JWT_SECRET"]
        assert caplog.records == []

        monkeypatch.setenv("MODEL_BACKEND", "local")
        config.get_settings().warn_insecure()
        assert "JWT_SECRET" in caplog.text


def test_env_example_parses(monkeypatch):
    # .env.example ต้องอ่านได้จริง (รวมคอมเมนต์ท้ายบรรทัด) และไม่มีค่าของ API ภายนอก
    monkeypatch.setitem(config.Settings.model_config, "env_file", config.REPO_ROOT / ".env.example")
    s = config.get_settings()
    assert s.MODEL_BACKEND == "fake"
    assert s.DATA_DIR == config.REPO_ROOT / "data"
    assert s.cors_origins == ["http://localhost:3000"]
