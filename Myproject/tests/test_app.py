import os

import pytest

os.environ["ADMIN_TOKEN"] = "test-token"          # до import app, щоб тести не залежали від .env
ADMIN = {"X-Admin-Token": "test-token"}


@pytest.fixture
def client(tmp_path):
    os.environ["DB_PATH"] = str(tmp_path / "test.db")   # порожня база на кожен тест
    import app
    app.storage.init()
    app.app.config["TESTING"] = True
    return app.app.test_client()


def add(client, **overrides):
    data = {"date": "2026-10-01", "title": "Пирогово", "category": "музей",
            "amount": 100, "duration": 2, "note": ""}
    data.update(overrides)
    return client.post("/items", json=data)


def test_add_and_list(client):
    r = add(client)
    assert r.status_code == 201
    r = client.get("/items")
    assert r.status_code == 200
    items = r.get_json()
    assert len(items) == 1
    assert items[0]["title"] == "Пирогово"
    assert items[0]["category"] == "музей"


def test_add_rejects_text_amount(client):
    assert add(client, amount="abc").status_code == 400


def test_add_rejects_missing_title_and_negative_amount(client):
    assert add(client, title="").status_code == 400
    assert add(client, amount=-5).status_code == 400


def test_add_rejects_non_json(client):
    r = client.post("/items", data="не json", content_type="text/plain")
    assert r.status_code == 400


def test_filter_by_category(client):
    add(client, category="музей")
    add(client, category="їжа", title="Кафе")
    r = client.get("/items?category=їжа")
    assert [i["title"] for i in r.get_json()] == ["Кафе"]


def test_report_by_category_uses_join_and_limit(client):
    add(client, category="музей", amount=300, date="2026-10-02")
    add(client, category="Музей", amount=300, date="2026-10-03")     # та сама категорія
    add(client, category="їжа", title="Кафе", amount=50, date="2026-11-01")
    client.put("/admin/categories/музей", json={"monthly_limit": 500}, headers=ADMIN)
    r = client.get("/report/categories?month=2026-10")
    assert r.status_code == 200
    rows = r.get_json()
    assert len(rows) == 1
    assert rows[0]["category"] == "музей"
    assert rows[0]["total"] == 600.0
    assert rows[0]["over_limit"] is True


def test_report_rejects_bad_month(client):
    assert client.get("/report/categories?month=жовтень").status_code == 400


def test_public_delete_does_not_exist(client):
    add(client)
    assert client.delete("/items/1").status_code in (404, 405)
    assert len(client.get("/items").get_json()) == 1


def test_admin_requires_token(client):
    assert client.get("/admin/export").status_code == 403
    assert client.get("/admin/export", headers={"X-Admin-Token": "wrong"}).status_code == 403
    assert client.get("/admin/export", headers=ADMIN).status_code == 200


def test_admin_hidden_behind_cloudflare(client):
    headers = dict(ADMIN, **{"CF-Connecting-IP": "1.2.3.4"})
    assert client.get("/admin/export", headers=headers).status_code == 404


def test_admin_delete_missing_returns_404(client):
    assert client.delete("/admin/items/999", headers=ADMIN).status_code == 404


def test_audit_log_records_add_and_delete(client):
    add(client)
    assert client.delete("/admin/items/1", headers=ADMIN).status_code == 200
    r = client.get("/admin/log?limit=10", headers=ADMIN)
    assert r.status_code == 200
    actions = [row["action"] for row in r.get_json()]
    assert actions[:2] == ["delete", "add"]          # найновіші першими
    assert r.get_json()[0]["item_id"] == 1