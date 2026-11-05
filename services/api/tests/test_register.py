import ipaddress

import pytest
from conftest import login, upload_csv

from app.routers.auth import REGISTER_PER_IP

REGISTER = "/api/auth/register"


@pytest.fixture(autouse=True)
def allow_register(monkeypatch):
    # ค่าเริ่มต้นปิดรับสมัคร (ลิงก์ tunnel เป็นสาธารณะ) · เทสต์ในไฟล์นี้เปิดไว้ก่อน
    monkeypatch.setenv("ALLOW_REGISTER", "true")


def register(api, username="friend01", password="pass-1234", **kw):
    return api.post(REGISTER, json={"username": username, "password": password}, **kw)


def test_config_public(api):
    assert api.get("/api/auth/config").json() == {"allow_register": True}


def test_register_closed_by_default(api, monkeypatch):
    monkeypatch.delenv("ALLOW_REGISTER")
    assert api.get("/api/auth/config").json() == {"allow_register": False}
    assert register(api).status_code == 403


def test_login_ignores_username_case(api):
    assert register(api, "Friend01").status_code == 201
    assert login(api, "Friend01", "pass-1234")
    assert login(api, " FRIEND01 ", "pass-1234")


def test_register_then_use_and_login(api):
    r = register(api, "Friend01")
    assert r.status_code == 201
    body = r.json()
    assert body["username"] == "friend01"
    headers = {"Authorization": f"Bearer {body['token']}"}
    assert api.get("/api/datasets", headers=headers).json() == []
    assert login(api, "friend01", "pass-1234")


def test_new_user_cannot_see_others_data(api):
    upload_csv(api, login(api))
    token = register(api).json()["token"]
    assert api.get("/api/datasets", headers={"Authorization": f"Bearer {token}"}).json() == []


def test_duplicate_and_reserved_names(api):
    assert register(api).status_code == 201
    assert register(api, password="other-pass-1").status_code == 409
    assert register(api, "demo").status_code == 409
    # ชื่อซ้ำต้องไม่ทับรหัสของคนเดิม
    assert login(api, "friend01", "pass-1234")


def test_register_validation(api):
    assert register(api, "ab").status_code == 422
    assert register(api, "สมชาย").status_code == 400
    assert register(api, "has space").status_code == 400
    assert register(api, password="short").status_code == 422


def test_register_disabled(api, monkeypatch):
    monkeypatch.setenv("ALLOW_REGISTER", "false")
    assert register(api).status_code == 403
    assert api.get("/api/auth/config").json() == {"allow_register": False}


def test_max_users(api, monkeypatch):
    monkeypatch.setenv("MAX_USERS", "1")  # มี demo อยู่แล้ว 1 คน
    assert register(api).status_code == 403


def test_register_rate_limited_per_forwarded_ip(api):
    # ผ่าน proxy ในเครื่อง (TestClient = testclient) ไม่ใช่ loopback → ใช้ IP ตรง ทุกคำขอนับรวมกัน
    codes = [register(api, f"user{i:02d}").status_code for i in range(REGISTER_PER_IP + 1)]
    assert codes[:REGISTER_PER_IP] == [201] * REGISTER_PER_IP
    assert codes[REGISTER_PER_IP] == 429


def test_client_ip_trusts_forwarded_only_from_loopback():
    from starlette.requests import Request

    from app.security import client_ip

    def req(host, xff=None):
        headers = [(b"x-forwarded-for", xff.encode())] if xff else []
        return Request({"type": "http", "client": (host, 1234), "headers": headers})

    # proxy ต่อ IP จริงไว้ขวาสุด · ค่าซ้ายผู้ใช้ปลอมมาเองได้ · ข้าม loopback (เว็บ Next.js ส่งต่อ)
    assert client_ip(req("127.0.0.1", "1.2.3.4, 203.0.113.5")) == "203.0.113.5"
    assert client_ip(req("127.0.0.1", "203.0.113.5, 127.0.0.1")) == "203.0.113.5"
    assert client_ip(req("::1", "198.51.100.7")) == "198.51.100.7"
    assert client_ip(req("127.0.0.1")) == "127.0.0.1"
    assert client_ip(req("192.0.2.9", "203.0.113.5")) == "192.0.2.9"  # คนนอกปลอม header ไม่ได้ผล


def test_client_ip_trusts_docker_subnet_only_when_configured():
    from starlette.requests import Request

    from app.security import client_ip

    def req(host, xff=None):
        headers = [(b"x-forwarded-for", xff.encode())] if xff else []
        return Request({"type": "http", "client": (host, 1234), "headers": headers})

    loopback = (ipaddress.ip_network("127.0.0.1"), ipaddress.ip_network("::1"))
    docker = loopback + (ipaddress.ip_network("172.31.250.0/24"),)
    web = req("172.31.250.3", "1.2.3.4, 203.0.113.5")
    assert client_ip(web, loopback) == "172.31.250.3"  # ค่าเริ่มต้น: ไม่เชื่อ container
    assert client_ip(web, docker) == "203.0.113.5"
    # proxy ต่อกันหลายชั้น (tunnel ในเครื่อง → container เว็บ) ข้ามทุกชั้นที่เชื่อได้
    assert client_ip(req("172.31.250.3", "203.0.113.5, 127.0.0.1"), docker) == "203.0.113.5"
    assert client_ip(req("192.0.2.9", "203.0.113.5"), docker) == "192.0.2.9"
    assert client_ip(req("testclient", "203.0.113.5"), docker) == "testclient"  # host ไม่ใช่ IP


def test_trusted_proxies_setting(monkeypatch):
    from app.config import Settings

    monkeypatch.setitem(Settings.model_config, "env_file", None)
    monkeypatch.setenv("TRUSTED_PROXIES", "127.0.0.1, 172.31.250.0/24, not-an-ip")
    nets = Settings().trusted_proxies
    assert ipaddress.ip_address("172.31.250.9") in nets[1]
    assert len(nets) == 2
