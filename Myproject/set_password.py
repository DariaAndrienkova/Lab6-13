"""Задає новий пароль користувачу. Запускається лише на сервері (ноутбуці):

    python set_password.py ЛОГІН

Корисно, коли пароль забули або ввели не в тій розкладці. Старий пароль не потрібен,
саме тому скрипт доступний лише тому, хто має доступ до самого комп'ютера і бази.
Через інтернет пароль змінити неможливо: такого маршруту в API немає.
"""
import getpass
import sqlite3
import sys

from werkzeug.security import generate_password_hash

import storage


def main():
    if len(sys.argv) != 2:
        print("використання: python set_password.py ЛОГІН")
        return
    login = sys.argv[1].strip()
    user = storage.get_user_by_login(login)
    if user is None:
        conn = storage.connect()
        try:
            logins = [r["login"] for r in conn.execute("SELECT login FROM users")]
        finally:
            conn.close()
        print("Такого користувача немає. Наявні логіни:", logins)
        return
    password = getpass.getpass("Новий пароль (від 8 символів, лише англійськими літерами й цифрами): ")
    if not 8 <= len(password) <= 200:
        print("Пароль має бути від 8 до 200 символів.")
        return
    if password != getpass.getpass("Повторіть пароль: "):
        print("Паролі не збігаються.")
        return
    conn = storage.connect()
    try:
        conn.execute("UPDATE users SET password_hash = ? WHERE id = ?",
                     (generate_password_hash(password), user["id"]))
        storage.log_action(conn, "set_password", None, f"користувач {user['login']}", user["id"])
        conn.commit()
    finally:
        conn.close()
    print("Готово: пароль для", user["login"], "змінено.")


if __name__ == "__main__":
    main()