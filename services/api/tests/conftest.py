import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

DEMO_PASSWORD = "test-demo-pass"


def set_test_env(monkeypatch, tmp_path, **overrides):
    from app import config

    monkeypatch.setitem(config.Settings.model_config, "env_file", None)
    env = {
        "MODEL_BACKEND": "fake",
        "MODEL_PATH": str(tmp_path / "no-model"),
        "DATA_DIR": str(tmp_path),
        "DEMO_PASSWORD": DEMO_PASSWORD,
        "JWT_SECRET": "test-secret-test-secret-test-secret",
        "DEMO_MODE": "false",
        **overrides,
    }
    for name, value in env.items():
        monkeypatch.setenv(name, value)


@pytest.fixture
def api(tmp_path, monkeypatch):
    """TestClient ของแอปจริง ใช้ fake model และ DATA_DIR ชั่วคราว"""
    from fastapi.testclient import TestClient

    set_test_env(monkeypatch, tmp_path)

    from app.main import create_app

    with TestClient(create_app()) as client:
        yield client


def login(client, username="demo", password=DEMO_PASSWORD) -> dict:
    r = client.post("/api/auth/login", json={"username": username, "password": password})
    return {"Authorization": f"Bearer {r.json()['token']}"}


def upload_csv(client, headers, text="branch,amount\nสาขา 1,100\nสาขา 2,250\n", name="sales.csv"):
    files = {"file": (name, text.encode("utf-8"), "text/csv")}
    return client.post("/api/datasets", headers=headers, files=files)
