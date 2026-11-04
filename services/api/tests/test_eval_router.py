import json
import sys
from pathlib import Path

from fastapi import FastAPI
from fastapi.testclient import TestClient

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.routers import eval as eval_router  # noqa: E402


def make_client(tmp_path, monkeypatch):
    monkeypatch.setattr(eval_router, "RESULTS_DIR", tmp_path)
    app = FastAPI()
    app.include_router(eval_router.router)
    return TestClient(app)


def test_results_404_when_missing(tmp_path, monkeypatch):
    client = make_client(tmp_path, monkeypatch)
    assert client.get("/api/eval/results").status_code == 404


def test_results_returns_latest(tmp_path, monkeypatch):
    data = {"simulated": False, "results": [{"mode": "M3", "set": "handwritten", "n": 70}]}
    (tmp_path / "latest.json").write_text(json.dumps(data), encoding="utf-8")
    client = make_client(tmp_path, monkeypatch)
    assert client.get("/api/eval/results").json() == data


def test_simulated_is_separate(tmp_path, monkeypatch):
    (tmp_path / "simulated.json").write_text(json.dumps({"simulated": True}), encoding="utf-8")
    client = make_client(tmp_path, monkeypatch)
    assert client.get("/api/eval/results").status_code == 404
    assert client.get("/api/eval/results", params={"simulated": "true"}).json() == {"simulated": True}
