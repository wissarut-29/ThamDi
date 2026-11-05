from conftest import login, upload_csv

from app import db
from app.security import hash_password


def ask(api, headers, dataset_id, question):
    return api.post("/api/chat", headers=headers, json={"dataset_id": dataset_id, "question": question})


def test_history_requires_token(api):
    assert api.get("/api/history").status_code == 401


def test_history_empty_then_newest_first(api):
    headers = login(api)
    assert api.get("/api/history", headers=headers).json() == []

    dataset_id = upload_csv(api, headers).json()["dataset_id"]
    ask(api, headers, dataset_id, "มีกี่สาขา")
    ask(api, headers, dataset_id, "ลบตาราง sales")

    items = api.get("/api/history", headers=headers).json()
    assert [i["question"] for i in items] == ["ลบตาราง sales", "มีกี่สาขา"]
    assert items[0]["status"] == "refuse"
    assert items[1]["status"] == "ok"
    assert items[1]["answer"] == "คำตอบ: 2"
    assert items[1]["dataset_id"] == dataset_id
    assert items[1]["dataset_name"] == "sales.csv"
    assert items[1]["created_at"]


def test_history_filter_and_limit(api):
    headers = login(api)
    first = upload_csv(api, headers).json()["dataset_id"]
    second = upload_csv(api, headers, name="other.csv").json()["dataset_id"]
    ask(api, headers, first, "มีกี่สาขา")
    ask(api, headers, second, "มีกี่สาขา")
    ask(api, headers, second, "มีกี่สาขา")

    only_first = api.get("/api/history", headers=headers, params={"dataset_id": first}).json()
    assert [i["dataset_id"] for i in only_first] == [first]
    assert len(api.get("/api/history", headers=headers, params={"limit": 2}).json()) == 2
    assert api.get("/api/history", headers=headers, params={"limit": 0}).status_code == 422


def test_history_is_private(api):
    headers = login(api)
    dataset_id = upload_csv(api, headers).json()["dataset_id"]
    ask(api, headers, dataset_id, "มีกี่สาขา")

    db.upsert_user("other", hash_password("other-pass"))
    other = login(api, "other", "other-pass")
    assert api.get("/api/history", headers=other).json() == []
    assert api.get("/api/history", headers=other, params={"dataset_id": dataset_id}).json() == []
