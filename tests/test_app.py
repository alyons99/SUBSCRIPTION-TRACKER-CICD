#some basic tests, based on best practicies found online

import pytest

from app import create_app

NETFLIX = {"name": "Netflix", "cost": 15.49, "billing_cycle": "monthly", "renewal_date": "2026-11-01"}
DOMAIN = {"name": "Domain", "cost": 12.00, "billing_cycle": "yearly", "renewal_date": "2027-03-15"}


@pytest.fixture
def client(tmp_path):
    app = create_app({"TESTING": True, "DATABASE": str(tmp_path / "test.db")})
    return app.test_client()


def test_health(client):
    res = client.get("/health")
    assert res.status_code == 200
    assert res.get_json() == {"status": "ok"}


def test_create_and_get(client):
    res = client.post("/subscriptions", json=NETFLIX)
    assert res.status_code == 201
    sub_id = res.get_json()["id"]

    res = client.get(f"/subscriptions/{sub_id}")
    assert res.status_code == 200
    assert res.get_json()["name"] == "Netflix"


def test_list_is_sorted_by_renewal(client):
    client.post("/subscriptions", json=DOMAIN)
    client.post("/subscriptions", json=NETFLIX)
    names = [s["name"] for s in client.get("/subscriptions").get_json()]
    assert names == ["Netflix", "Domain"]


def test_delete(client):
    sub_id = client.post("/subscriptions", json=NETFLIX).get_json()["id"]
    assert client.delete(f"/subscriptions/{sub_id}").status_code == 204
    assert client.get(f"/subscriptions/{sub_id}").status_code == 404


def test_delete_missing_returns_404(client):
    assert client.delete("/subscriptions/999").status_code == 404


def test_summary_prorates_yearly(client):
    client.post("/subscriptions", json=NETFLIX)
    client.post("/subscriptions", json=DOMAIN)
    body = client.get("/subscriptions/summary").get_json()
    assert body["count"] == 2
    assert body["monthly_total"] == 16.49  # 15.49 + 12/12


@pytest.mark.parametrize(
    "bad",
    [
        {},
        {**NETFLIX, "name": "  "},
        {**NETFLIX, "cost": -1},
        {**NETFLIX, "cost": "free"},
        {**NETFLIX, "billing_cycle": "weekly"},
        {**NETFLIX, "renewal_date": "11/01/2026"},
    ],
)
def test_validation_rejects_bad_input(client, bad):
    assert client.post("/subscriptions", json=bad).status_code == 400
