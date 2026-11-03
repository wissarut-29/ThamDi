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


def test_chat_rate_limited_per_user(api):
    headers = login(api)
    dataset_id = upload_csv(api, headers).json()["dataset_id"]
    codes = [ask(api, headers, dataset_id, "มีกี่สาขา").status_code for _ in range(21)]
    assert codes[:20] == [200] * 20
    assert codes[20] == 429


def test_demo_answer_with_missing_keys_does_not_500(api, monkeypatch):
    # รีวิว PR #9: demo.lookup() คืน dict ไม่มี status → history NOT NULL พัง
    from app.agent import demo
    from app.routers import chat

    monkeypatch.setattr(chat, "model_info", lambda: {"loaded": False})
    monkeypatch.setattr(demo, "lookup", lambda q: {"answer": "คำตอบเดโม"}, raising=False)
    headers = login(api)
    dataset_id = upload_csv(api, headers).json()["dataset_id"]
    r = ask(api, headers, dataset_id, "มีกี่สาขา")
    assert r.status_code == 200
    assert r.json() == {"answer": "คำตอบเดโม", "status": "ok", "sql": None, "columns": [], "rows": []}


def test_model_queue_full_returns_503(api, monkeypatch):
    # รีวิว PR #9: คิวเต็มต้องตอบเร็ว ไม่ยึด thread ไว้นาน
    from app.agent import model, pipeline

    def busy(*_args, **_kwargs):
        raise model.ModelBusy("คิวโมเดลเต็ม")

    monkeypatch.setattr(pipeline, "run", busy)
    headers = login(api)
    dataset_id = upload_csv(api, headers).json()["dataset_id"]
    r = ask(api, headers, dataset_id, "มีกี่สาขา")
    assert r.status_code == 503


def test_keyword_filename_still_answers(api):
    headers = login(api)
    dataset_id = upload_csv(api, headers, name="order.csv").json()["dataset_id"]
    body = ask(api, headers, dataset_id, "มีกี่แถว").json()
    assert body["status"] == "ok"
    assert "t_order" in body["sql"]
