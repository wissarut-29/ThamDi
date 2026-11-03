import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

DEMO_PASSWORD = "test-demo-pass"


@pytest.fixture
def api(tmp_path, monkeypatch):
    """TestClient ของแอปจริง ใช้ fake model และ DATA_DIR ชั่วคราว"""
    from fastapi.testclient import TestClient

    from app import config

    monkeypatch.setitem(config.Settings.model_config, "env_file", None)
    monkeypatch.setenv("MODEL_BACKEND", "fake")
    monkeypatch.setenv("DATA_DIR", str(tmp_path))
    monkeypatch.setenv("DEMO_PASSWORD", DEMO_PASSWORD)
    monkeypatch.setenv("JWT_SECRET", "test-secret-test-secret-test-secret")
    monkeypatch.setenv("DEMO_MODE", "false")

    from app.main import create_app

    with TestClient(create_app()) as client:
        yield client


def login(client, username="demo", password=DEMO_PASSWORD) -> dict:
    r = client.post("/api/auth/login", json={"username": username, "password": password})
    return {"Authorization": f"Bearer {r.json()['token']}"}


def upload_csv(client, headers, text="branch,amount\nสาขา 1,100\nสาขา 2,250\n", name="sales.csv"):
    files = {"file": (name, text.encode("utf-8"), "text/csv")}
    return client.post("/api/datasets", headers=headers, files=files)
