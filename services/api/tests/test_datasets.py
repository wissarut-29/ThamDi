from conftest import login, upload_csv

from app import db
from app.security import hash_password


def test_upload_and_list(api):
    headers = login(api)
    r = upload_csv(api, headers)
    assert r.status_code == 201
    body = r.json()
    assert body["tables"] == ["sales"]
    listed = api.get("/api/datasets", headers=headers).json()
    # demo มีไฟล์ตัวอย่าง 3 ไฟล์อยู่แล้ว · ไฟล์ที่อัปโหลดล่าสุดต้องอยู่บนสุด
    assert listed[0]["dataset_id"] == body["dataset_id"]
    assert len(listed) == 4


def test_wrong_extension_400(api):
    assert upload_csv(api, login(api), name="sales.pdf").status_code == 400


def test_empty_file_400(api):
    assert upload_csv(api, login(api), text="").status_code == 400


def test_list_only_own(api):
    upload_csv(api, login(api))
    db.upsert_user("other", hash_password("other-pass"))
    assert api.get("/api/datasets", headers=login(api, "other", "other-pass")).json() == []


def test_duplicate_upload_hidden_but_kept(api):
    headers = login(api)
    first = upload_csv(api, headers).json()["dataset_id"]
    second = upload_csv(api, headers).json()["dataset_id"]
    changed = upload_csv(api, headers, text="branch,amount\nสาขา 1,999\n").json()["dataset_id"]

    by_id = {d["dataset_id"]: d for d in api.get("/api/datasets", headers=headers).json()}
    # ชื่อเดียวกันแต่ข้อมูลต่าง = ไม่ซ้ำ · ข้อมูลเหมือนกัน = ซ่อนตัวเก่า ชี้ไปตัวใหม่สุด
    assert "duplicate_of" not in by_id[changed]
    assert "duplicate_of" not in by_id[second]
    assert by_id[first]["duplicate_of"] == second
    # ไม่ลบข้อมูล: ยังถามไฟล์เก่าได้
    chat = {"dataset_id": first, "question": "มีกี่สาขา"}
    assert api.post("/api/chat", headers=headers, json=chat).status_code == 200


def test_unique_names_are_not_fingerprinted(api, monkeypatch):
    headers = login(api)
    upload_csv(api, headers, name="a.csv")
    upload_csv(api, headers, name="b.csv")
    calls = []
    monkeypatch.setattr(db, "_dataset_fingerprint", lambda d: calls.append(d["name"]) or "x")
    api.get("/api/datasets", headers=headers)
    assert calls == []
