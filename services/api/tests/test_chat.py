from conftest import login, upload_csv

from app import db
from app.security import hash_password


def ask(api, headers, dataset_id, question):
    return api.post("/api/chat", headers=headers, json={"dataset_id": dataset_id, "question": question})


def test_chat_end_to_end_with_fake_model(api):
    headers = login(api)
    dataset_id = upload_csv(api, headers).json()["dataset_id"]
    r = ask(api, headers, dataset_id, "มีกี่สาขา")
    assert r.status_code == 200
    body = r.json()
    assert body["status"] == "ok"
    assert body["rows"] == [[2]]
    assert body["answer"] == "คำตอบ: 2"
    assert "sales" in body["sql"]


def test_chat_refuse(api):
    headers = login(api)
    dataset_id = upload_csv(api, headers).json()["dataset_id"]
    assert ask(api, headers, dataset_id, "ลบตาราง sales").json()["status"] == "refuse"


def test_other_users_dataset_404(api):
    dataset_id = upload_csv(api, login(api)).json()["dataset_id"]
    db.upsert_user("other", hash_password("other-pass"))
    r = ask(api, login(api, "other", "other-pass"), dataset_id, "มีกี่สาขา")
    assert r.status_code == 404


def test_unknown_dataset_404(api):
    assert ask(api, login(api), "../etc", "x").status_code == 404


def test_question_too_long_rejected(api):
    headers = login(api)
    dataset_id = upload_csv(api, headers).json()["dataset_id"]
    assert ask(api, headers, dataset_id, "ก" * 501).status_code == 422


def test_model_not_loaded_without_demo_answer(api, monkeypatch):
    from app.routers import chat

    monkeypatch.setattr(chat, "model_info", lambda: {"loaded": False})
    headers = login(api)
    dataset_id = upload_csv(api, headers).json()["dataset_id"]
    body = ask(api, headers, dataset_id, "มีกี่สาขา").json()
    assert body["status"] == "error"
    assert body["answer"] == chat.NOT_READY_TEXT
