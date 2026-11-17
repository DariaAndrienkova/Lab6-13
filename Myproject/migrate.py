"""Одноразове перенесення старої бази (категорія текстом) у нову (окрема таблиця categories).

Запуск один раз:  python migrate.py
Скрипт сам робить копію бази в теку backups, переносить записи в одній транзакції
і перевіряє, що кількість записів і сума збігаються. Якщо щось не так, нічого не змінюється.
Стара таблиця лишається під назвою items_old, її можна видалити пізніше.
"""
import datetime
import os
import sqlite3

import storage


def backup_before(path):
    backups = os.path.join(os.path.dirname(os.path.abspath(path)), "backups")  # поруч із базою
    os.makedirs(backups, exist_ok=True)
    target = os.path.join(backups, f"before-migrate-{datetime.datetime.now():%Y-%m-%d_%H%M%S}.db")
    src = sqlite3.connect(path)
    dst = sqlite3.connect(target)
    src.backup(dst)
    dst.close()
    src.close()
    return target


def main():
    path = storage.db_path()
    if not os.path.exists(path):
        print("Бази немає, переносити нічого.")
        return
    conn = storage.connect()
    conn.isolation_level = None                  # транзакцією керуємо самі
    try:
        columns = [r["name"] for r in conn.execute("PRAGMA table_info(items)")]
        if not columns:
            print("Таблиці items немає, переносити нічого.")
            return
        if "category_id" in columns:
            print("База вже в новому форматі, переносити нічого.")
            return

        print("Копія бази перед змінами:", backup_before(path))

        old_count, old_sum = conn.execute(
            "SELECT COUNT(*), COALESCE(SUM(amount), 0) FROM items").fetchone()
        title_sql = "title" if "title" in columns else "''"
        duration_sql = "duration" if "duration" in columns else "0"

        conn.execute("BEGIN")
        try:
            conn.execute("ALTER TABLE items RENAME TO items_old")
            storage.create_tables(conn)
            old_rows = conn.execute(
                f"SELECT id, date, {title_sql} AS title, category, amount, "
                f"{duration_sql} AS duration, note FROM items_old ORDER BY id").fetchall()
            for r in old_rows:
                category = (r["category"] or "").strip() or "без категорії"
                category_id = storage.get_or_create_category(conn, category)
                conn.execute(
                    "INSERT INTO items (id, date, title, category_id, amount, duration, note) "
                    "VALUES (?, ?, ?, ?, ?, ?, ?)",
                    (r["id"], r["date"], r["title"] or "", category_id, r["amount"],
                     r["duration"] or 0, r["note"]))
            new_count, new_sum = conn.execute(
                "SELECT COUNT(*), COALESCE(SUM(amount), 0) FROM items").fetchone()
            if new_count != old_count or abs(new_sum - old_sum) > 1e-6:
                raise RuntimeError(f"Не збіглося: було {old_count} записів на {old_sum}, "
                                   f"стало {new_count} на {new_sum}")
            storage.log_action(conn, "migrate", None, f"перенесено записів: {new_count}")
            conn.execute("COMMIT")
        except Exception:
            conn.execute("ROLLBACK")
            raise
        categories = conn.execute("SELECT COUNT(*) FROM categories").fetchone()[0]
        print(f"Готово: перенесено записів {new_count}, створено категорій {categories}.")
        print("Стара таблиця лишилась як items_old.")
    finally:
        conn.close()


if __name__ == "__main__":
    main()