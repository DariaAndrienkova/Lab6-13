"""Міграція для лабораторної 12: додає користувачів і приписує всі наявні записи одному з них.

Запуск один раз (логін придумайте свій):   python migrate_users.py ВАШ_ЛОГІН
Скрипт спитає пароль (на екрані він не показується), зробить копію бази в теку backups,
створить користувача і перенесе записи в одній транзакції. Якщо щось не збігається,
нічого не змінюється. Стара таблиця лишається як items_before_users.
"""
import datetime
import getpass
import os
import sqlite3
import sys

from werkzeug.security import generate_password_hash

import storage


def backup_before(path):
    """Копія бази в теку backups поруч із базою. Повертає шлях до копії."""
    backups = os.path.join(os.path.dirname(os.path.abspath(path)), "backups")
    os.makedirs(backups, exist_ok=True)
    target = os.path.join(backups, f"before-users-{datetime.datetime.now():%Y-%m-%d_%H%M%S}.db")
    src = sqlite3.connect(path)
    dst = sqlite3.connect(target)
    src.backup(dst)
    dst.close()
    src.close()
    return target


def run(login, password):
    """Сама міграція. Повертає текст для користувача. Окремо від main, щоб її можна було тестувати."""
    path = storage.db_path()
    if not os.path.exists(path):
        return "Бази немає, переносити нічого."
    conn = storage.connect()
    conn.isolation_level = None                  # транзакцією керуємо самі
    try:
        columns = [r["name"] for r in conn.execute("PRAGMA table_info(items)")]
        if not columns:
            return "Таблиці items немає, переносити нічого."
        if "category_id" not in columns:
            return "База ще старого формату. Спершу запустіть: python migrate.py"
        if "user_id" in columns:
            return "База вже має користувачів, переносити нічого."

        print("Копія бази перед змінами:", backup_before(path))
        old_count, old_sum = conn.execute(
            "SELECT COUNT(*), COALESCE(SUM(amount), 0) FROM items").fetchone()

        conn.execute("BEGIN")
        try:
            conn.execute("ALTER TABLE items RENAME TO items_before_users")
            storage.create_tables(conn)          # створює users і нову items з user_id
            audit_columns = [r["name"] for r in conn.execute("PRAGMA table_info(audit_log)")]
            if "user_id" not in audit_columns:
                conn.execute("ALTER TABLE audit_log ADD COLUMN user_id INTEGER")

            cur = conn.execute(
                "INSERT INTO users (login, password_hash, is_admin, created) VALUES (?, ?, 0, ?)",
                (login, generate_password_hash(password),
                 datetime.datetime.now().isoformat(timespec="seconds")))
            user_id = cur.lastrowid
            conn.execute(
                "INSERT INTO items (id, user_id, date, title, category_id, amount, duration, note) "
                "SELECT id, ?, date, title, category_id, amount, duration, note "
                "FROM items_before_users", (user_id,))

            new_count, new_sum = conn.execute(
                "SELECT COUNT(*), COALESCE(SUM(amount), 0) FROM items").fetchone()
            if new_count != old_count or abs(new_sum - old_sum) > 1e-6:
                raise RuntimeError(f"Не збіглося: було {old_count} записів на {old_sum}, "
                                   f"стало {new_count} на {new_sum}")
            storage.log_action(conn, "migrate_users", None,
                               f"користувач {login}, записів перенесено: {new_count}", user_id)
            conn.execute("COMMIT")
        except Exception:
            conn.execute("ROLLBACK")
            raise
        return (f"Готово: користувач {login} створений, йому приписано записів: {new_count}.\n"
                "Стара таблиця лишилась як items_before_users.")
    finally:
        conn.close()


def main():
    if len(sys.argv) != 2:
        print("використання: python migrate_users.py ВАШ_ЛОГІН")
        return
    login = sys.argv[1].strip()
    if not 3 <= len(login) <= 50:
        print("Логін має бути від 3 до 50 символів.")
        return
    password = getpass.getpass("Придумайте пароль (від 8 символів, на екрані не видно): ")
    if len(password) < 8:
        print("Пароль закороткий.")
        return
    if password != getpass.getpass("Повторіть пароль: "):
        print("Паролі не збігаються.")
        return
    print(run(login, password))


if __name__ == "__main__":
    main()