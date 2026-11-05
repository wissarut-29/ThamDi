from datetime import datetime, timedelta, timezone

import jwt
import pytest
from conftest import DEMO_PASSWORD, login, set_test_env

from app.routers.auth import LOGIN_PER_IP


def test_login_ok_and_token_works(api):
    headers = login(api)
    assert api.get("/api/datasets", headers=headers).status_code == 200


@pytest.mark.parametrize(("username", "password"), [("demo", "wrong"), ("nobody", DEMO_PASSWORD)])
def test_login_wrong_credentials_401(api, username, password):
    r = api.post("/api/auth/login", json={"username": username, "password": password})
    assert r.status_code == 401


@pytest.mark.parametrize(
    ("method", "path"),
    [("get", "/api/datasets"), ("post", "/api/chat"), ("get", "/api/model"), ("get", "/api/eval/results")],
)
def test_no_token_401(api, method, path):
    assert getattr(api, method)(path).status_code == 401


def test_bad_token_401(api):
    assert api.get("/api/model", headers={"Authorization": "Bearer not-a-jwt"}).status_code == 401


def test_model_info(api):
    info = api.get("/api/model", headers=login(api)).json()
    assert info["backend"] == "fake"
    assert info["loaded"] is True


def test_login_rate_limited(api):
    codes = [
        api.post("/api/auth/login", json={"username": "demo", "password": "wrong"}).status_code
        for _ in range(LOGIN_PER_IP + 1)
    ]
    assert codes[:LOGIN_PER_IP] == [401] * LOGIN_PER_IP
    assert codes[LOGIN_PER_IP] == 429


def _forged_token(secret="change-me"):
    now = datetime.now(timezone.utc)
    return jwt.encode({"sub": "demo", "iat": now, "exp": now + timedelta(hours=1)}, secret, algorithm="HS256")


@pytest.mark.parametrize("placeholder", ["change-me", ""])
def test_placeholder_jwt_secret_cannot_be_forged(api, monkeypatch, placeholder):
    # ช่องโหว่จากรีวิว PR #9: ไม่ได้ตั้ง JWT_SECRET แล้วเซ็น token เองด้วย change-me ได้ 200
    monkeypatch.setenv("JWT_SECRET", placeholder)
    forged = {"Authorization": f"Bearer {_forged_token()}"}
    assert api.get("/api/datasets", headers=forged).status_code == 401
    # token ที่ระบบออกให้เองยังใช้ได้ (เซ็นด้วย secret ที่สุ่มตอนเริ่ม)
    assert api.get("/api/datasets", headers=login(api)).status_code == 200


def test_demo_machine_refuses_placeholder_demo_password(tmp_path, monkeypatch):
    # เครื่องเดโม (local) ที่ยังไม่ได้ตั้ง DEMO_PASSWORD ต้อง login ด้วย change-me ไม่ได้
    # รวมถึงผู้ใช้ demo ที่ค้างจากรอบก่อนที่เคยรันด้วยรหัสจริง
    from fastapi.testclient import TestClient

    from app.main import create_app

    set_test_env(monkeypatch, tmp_path)
    with TestClient(create_app()) as client:
        login(client)  # รอบแรกสร้างผู้ใช้ demo

    set_test_env(monkeypatch, tmp_path, MODEL_BACKEND="local", DEMO_PASSWORD="change-me")
    with TestClient(create_app()) as client:
        for password in ("change-me", DEMO_PASSWORD):
            r = client.post("/api/auth/login", json={"username": "demo", "password": password})
            assert r.status_code == 401
