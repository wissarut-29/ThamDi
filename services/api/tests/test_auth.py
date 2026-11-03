import pytest
from conftest import DEMO_PASSWORD, login


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
