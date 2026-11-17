import os
import sqlite3

from werkzeug.security import check_password_hash

import migrate
import migrate_users
import storage
from tests.test_migrate import make_old_db, read


def prepare_v2_db(tmp_path):
    path = str(tmp_path / "v2.db")
    os.environ["DB_PATH"] = path
    make_old_db(path)
    migrate.main()                       # лабораторна 11: база стала форматом v2
    return path


def test_migrate_users_gives_all_items_to_one_user(tmp_path):
    path = prepare_v2_db(tmp_path)
    text = migrate_users.run("daria", "qwerty123")
    assert "Готово" in text
    users = read(path, "SELECT * FROM users")
    assert len(users) == 1
    assert users[0]["login"] == "daria"
    assert users[0]["is_admin"] == 0
    assert "qwerty123" not in users[0]["password_hash"]
    assert check_password_hash(users[0]["password_hash"], "qwerty123")
    items = read(path, "SELECT * FROM items")
    assert len(items) == 3
    assert {i["user_id"] for i in items} == {users[0]["id"]}
    assert round(sum(i["amount"] for i in items), 2) == 350.5
    storage.init()                                   # тепер база проходить перевірку формату
    assert len(storage.load(users[0]["id"])) == 3


def test_migrate_users_logs_who(tmp_path):
    path = prepare_v2_db(tmp_path)
    migrate_users.run("daria", "qwerty123")
    last = read(path, "SELECT * FROM audit_log ORDER BY id DESC")[0]
    assert last["action"] == "migrate_users"
    assert last["user_id"] is not None


def test_migrate_users_twice_is_harmless(tmp_path):
    path = prepare_v2_db(tmp_path)
    migrate_users.run("daria", "qwerty123")
    text = migrate_users.run("other", "qwerty123")
    assert "вже має користувачів" in text
    assert len(read(path, "SELECT * FROM users")) == 1


def test_migrate_users_refuses_v1_database(tmp_path):
    path = str(tmp_path / "old.db")
    os.environ["DB_PATH"] = path
    make_old_db(path)
    assert "python migrate.py" in migrate_users.run("daria", "qwerty123")


def test_old_format_database_is_refused_by_init(tmp_path):
    path = prepare_v2_db(tmp_path)
    try:
        storage.init()
    except RuntimeError as e:
        assert "migrate_users.py" in str(e)
    else:
        raise AssertionError("init мав відмовитися працювати зі старою базою")