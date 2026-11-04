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
    assert [d["dataset_id"] for d in listed] == [body["dataset_id"]]


def test_wrong_extension_400(api):
    assert upload_csv(api, login(api), name="sales.pdf").status_code == 400


def test_empty_file_400(api):
    assert upload_csv(api, login(api), text="").status_code == 400


def test_list_only_own(api):
    upload_csv(api, login(api))
    db.upsert_user("other", hash_password("other-pass"))
    assert api.get("/api/datasets", headers=login(api, "other", "other-pass")).json() == []
