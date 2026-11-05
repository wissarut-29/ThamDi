from conftest import DEMO_PASSWORD, login, set_test_env


def test_demo_has_sample_files_ready(api):
    # บัญชี demo ถามได้ทันทีโดยไม่ต้องอัปโหลด · ไฟล์ยอดขายอยู่บนสุด (หน้าแชทเลือกตัวแรก)
    headers = login(api)
    datasets = api.get("/api/datasets", headers=headers).json()
    assert [d["name"] for d in datasets] == ["sales_5_branches.xlsx", "employees.xlsx", "utility_bills.csv"]
    assert datasets[0]["tables"] == ["sales"]
    body = {"dataset_id": datasets[0]["dataset_id"], "question": "ยอดขายรวม"}
    r = api.post("/api/chat", headers=headers, json=body)
    assert r.status_code == 200


def test_restart_does_not_duplicate_samples(tmp_path, monkeypatch):
    from fastapi.testclient import TestClient

    from app.main import create_app

    set_test_env(monkeypatch, tmp_path)
    for _ in range(2):
        with TestClient(create_app()) as client:
            names = [d["name"] for d in client.get("/api/datasets", headers=login(client)).json()]
    assert sorted(names) == ["employees.xlsx", "sales_5_branches.xlsx", "utility_bills.csv"]


def test_new_users_do_not_get_demo_samples(api, monkeypatch):
    monkeypatch.setenv("ALLOW_REGISTER", "true")
    r = api.post("/api/auth/register", json={"username": "friend01", "password": DEMO_PASSWORD})
    assert r.status_code == 201
    headers = {"Authorization": f"Bearer {r.json()['token']}"}
    assert api.get("/api/datasets", headers=headers).json() == []
