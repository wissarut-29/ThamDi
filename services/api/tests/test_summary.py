from conftest import login, upload_csv

from app import db
from app.security import hash_password

CSV = "branch,amount\nสาขา 1,100\nสาขา 2,250\nสาขา 2,250\nสาขา 3,\n"


def test_summary_requires_token(api):
    assert api.get("/api/datasets/x/summary").status_code == 401


def test_summary_counts_and_chart(api):
    headers = login(api)
    dataset_id = upload_csv(api, headers, text=CSV).json()["dataset_id"]

    res = api.get(f"/api/datasets/{dataset_id}/summary", headers=headers)
    assert res.status_code == 200
    data = res.json()
    assert data["name"] == "sales.csv"
    assert data["row_count"] == 4
    assert data["column_count"] == 2
    assert data["missing_count"] == 1
    assert data["duplicate_rows"] == 1
    assert data["numeric_summary"]["column"] == "amount"
    assert data["numeric_summary"]["sum"] == 600
    assert data["charts"][0]["points"][0] == {"label": "สาขา 2", "value": 500}


def test_summary_of_other_users_dataset_is_404(api):
    headers = login(api)
    dataset_id = upload_csv(api, headers).json()["dataset_id"]
    db.upsert_user("other", hash_password("other-pass"))
    other = login(api, "other", "other-pass")
    assert api.get(f"/api/datasets/{dataset_id}/summary", headers=other).status_code == 404
