import os
import sqlite3

import pytest

os.environ["SECRET_KEY"] = "test-secret-key"      # до import app, щоб тести не залежали від .env


@pytest.fixture
def client(tmp_path):
    os.environ["DB_PATH"] = str(tmp_path / "test.db")   # порожня база на кожен тест
    import app
    app.storage.init()
    app.app.config["TESTING"] = True
    return app.app.test_client()


def second_client():
    """Ще один браузер зі своїм cookie (інший користувач)."""
    import app
    return app.app.test_client()


def register(client, login="daria", password="qwerty123"):
    return client.post("/register", json={"login": login, "password": password})


def signed_in(client, login="daria"):
    register(client, login)
    return client


def add(client, **overrides):
    data = {"date": "2026-10-01", "title": "Пирогово", "category": "музей",
            "amount": 100, "duration": 2, "note": ""}
    data.update(overrides)
    return client.post("/items", json=data)


def make_admin(client, login="admin"):
    """Реєструє користувача і робить його адміном так, як це робить make_admin.py."""
    import app
    register(client, login)
    assert app.storage.set_admin(login)
    return client


# ---------- реєстрація і вхід ----------

def test_register_stores_hash_not_password(client):
    assert register(client, password="qwerty123").status_code == 201
    import app
    row = app.storage.get_user_by_login("daria")
    assert "qwerty123" not in row["password_hash"]
    assert row["password_hash"].startswith(("scrypt:", "pbkdf2:"))   # назва алгоритму
    assert row["is_admin"] == 0


def test_register_validates_input(client):
    assert client.post("/register", json={"login": "ab", "password": "qwerty123"}).status_code == 400
    assert client.post("/register", json={"login": "daria", "password": "short"}).status_code == 400
    assert client.post("/register", json={"login": 123, "password": "qwerty123"}).status_code == 400
    assert client.post("/register", data="не json", content_type="text/plain").status_code == 400


def test_register_duplicate_login(client):
    assert register(client, "daria").status_code == 201
    assert second_client().post("/register", json={"login": "DARIA", "password": "qwerty123"}).status_code == 409


def test_cannot_make_yourself_admin_via_register(client):
    r = client.post("/register", json={"login": "hacker", "password": "qwerty123", "is_admin": 1})
    assert r.status_code == 201
    assert r.get_json()["is_admin"] is False


def test_login_ok_and_me(client):
    register(client)
    fresh = second_client()
    r = fresh.post("/login", json={"login": "daria", "password": "qwerty123"})
    assert r.status_code == 200
    me = fresh.get("/me")
    assert me.status_code == 200
    assert me.get_json()["login"] == "daria"


def test_wrong_password_and_unknown_login_look_the_same(client):
    register(client)
    wrong = second_client().post("/login", json={"login": "daria", "password": "неправильний1"})
    unknown = second_client().post("/login", json={"login": "nobody", "password": "qwerty123"})
    assert wrong.status_code == unknown.status_code == 401
    assert wrong.get_json() == unknown.get_json()      # не підказуємо, чи існує логін


def test_login_with_garbage_does_not_crash(client):
    assert client.post("/login", json={"login": None, "password": 5}).status_code == 401
    assert client.post("/login", data="x", content_type="text/plain").status_code == 401


def test_logout_ends_session(client):
    signed_in(client)
    assert client.get("/items").status_code == 200
    client.post("/logout")
    assert client.get("/items").status_code == 401


def test_session_cookie_flags(client):
    r = register(client)
    cookie = r.headers.get("Set-Cookie", "")
    assert "HttpOnly" in cookie
    assert "Secure" in cookie
    assert "SameSite=Lax" in cookie


# ---------- /health ----------

def test_health_is_public_and_ok(client):
    r = client.get("/health")                     # без входу
    assert r.status_code == 200
    assert r.get_json() == {"status": "broken"}


def test_health_reports_db_error(client, monkeypatch):
    import app

    def broken():
        raise sqlite3.OperationalError("база недоступна")

    monkeypatch.setattr(app.storage, "connect", broken)
    r = client.get("/health")
    assert r.status_code == 503
    assert r.get_json() == {"status": "db_error"}


# ---------- доступ без входу ----------

def test_data_routes_require_login(client):
    for method, url in [("get", "/items"), ("post", "/items"), ("get", "/report"),
                        ("get", "/report/categories"), ("delete", "/items/1"), ("get", "/me")]:
        r = getattr(client, method)(url)
        assert r.status_code == 401, url
        assert r.get_json() == {"error": "потрібно увійти"}      # JSON, а не HTML-сторінка


# ---------- записи ----------

def test_add_and_list(client):
    signed_in(client)
    assert add(client).status_code == 201
    items = client.get("/items").get_json()
    assert len(items) == 1
    assert items[0]["title"] == "Пирогово"
    assert items[0]["category"] == "музей"


def test_add_validation(client):
    signed_in(client)
    assert add(client, amount="abc").status_code == 400
    assert add(client, title="").status_code == 400
    assert add(client, amount=-5).status_code == 400
    r = client.post("/items", data="не json", content_type="text/plain")
    assert r.status_code == 400


def test_filter_by_category(client):
    signed_in(client)
    add(client, category="музей")
    add(client, category="їжа", title="Кафе")
    r = client.get("/items?category=їжа")
    assert [i["title"] for i in r.get_json()] == ["Кафе"]


def test_users_do_not_see_each_others_items(client):
    signed_in(client, "daria")
    add(client, title="Моє")
    other = signed_in(second_client(), "sister")
    add(other, title="Сестрине")
    assert [i["title"] for i in client.get("/items").get_json()] == ["Моє"]
    assert [i["title"] for i in other.get("/items").get_json()] == ["Сестрине"]
    assert list(client.get("/report").get_json()["by_category"].values()) == [100.0]


def test_delete_own_item(client):
    signed_in(client)
    add(client)
    assert client.delete("/items/1").status_code == 200
    assert client.get("/items").get_json() == []


def test_delete_foreign_item_gives_404_and_keeps_it(client):
    signed_in(client, "daria")
    add(client)                                    # запис №1 належить daria
    other = signed_in(second_client(), "sister")
    assert other.delete("/items/1").status_code == 404      # не 403: не підтверджуємо, що він є
    assert other.delete("/items/999").status_code == 404
    assert len(client.get("/items").get_json()) == 1


def test_report_by_category_uses_join_and_limit(client):
    signed_in(client)
    add(client, category="музей", amount=300, date="2026-10-02")
    add(client, category="Музей", amount=300, date="2026-10-03")     # та сама категорія
    add(client, category="їжа", title="Кафе", amount=50, date="2026-11-01")
    admin = make_admin(second_client())
    admin.put("/admin/categories/музей", json={"monthly_limit": 500})
    r = client.get("/report/categories?month=2026-10")
    assert r.status_code == 200
    rows = r.get_json()
    assert len(rows) == 1
    assert rows[0]["category"] == "музей"
    assert rows[0]["total"] == 600.0
    assert rows[0]["over_limit"] is True


def test_report_rejects_bad_month(client):
    signed_in(client)
    assert client.get("/report/categories?month=жовтень").status_code == 400


# ---------- адмінка ----------

def test_admin_requires_login_and_admin_role(client):
    assert client.get("/admin/export").status_code == 401           # без входу
    signed_in(client)
    assert client.get("/admin/export").status_code == 403          # звичайний користувач


def test_old_admin_token_no_longer_works(client):
    signed_in(client)
    r = client.get("/admin/export", headers={"X-Admin-Token": "будь-що"})
    assert r.status_code == 403


def test_admin_can_export_and_delete_anything(client):
    signed_in(client, "daria")
    add(client)
    admin = make_admin(second_client())
    rows = admin.get("/admin/export").get_json()
    assert len(rows) == 1
    assert rows[0]["owner"] == "daria"
    assert admin.delete("/admin/items/1").status_code == 200
    assert admin.delete("/admin/items/999").status_code == 404
    assert client.get("/items").get_json() == []


def test_admin_hidden_behind_cloudflare(client):
    admin = make_admin(client)
    r = admin.get("/admin/export", headers={"CF-Connecting-IP": "1.2.3.4"})
    assert r.status_code == 404          # навіть адміністратору: через тунель адмінки немає


def test_audit_log_records_who_did_it(client):
    signed_in(client, "daria")
    add(client)
    admin = make_admin(second_client())
    assert admin.delete("/admin/items/1").status_code == 200
    log = admin.get("/admin/log?limit=10").get_json()
    actions = [row["action"] for row in log]
    assert actions[:2] == ["delete", "add"]          # найновіші першими
    assert log[0]["login"] == "admin"                # видалив адмін
    assert log[1]["login"] == "daria"                # додала daria
    assert log[0]["item_id"] == 1


def test_user_delete_is_logged_with_user(client):
    signed_in(client, "daria")
    add(client)
    client.delete("/items/1")
    admin = make_admin(second_client())
    log = admin.get("/admin/log").get_json()
    assert log[0]["action"] == "delete" and log[0]["login"] == "daria"
