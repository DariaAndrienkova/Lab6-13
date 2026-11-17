import os
import sqlite3

# База лежить поруч із цим файлом (у теці Myproject), звідки б ви не запускали програму.
# Змінна DB_PATH потрібна для тестів у лабораторній 11.
BASE = os.path.dirname(os.path.abspath(__file__))


def db_path():
    return os.environ.get("DB_PATH", os.path.join(BASE, "data.db"))


def connect():
    conn = sqlite3.connect(db_path())
    conn.row_factory = sqlite3.Row      # рядки можна читати як словники
    return conn


def init():
    """Створює таблицю, якщо її ще немає. Стару таблицю (без title і duration) оновлює."""
    conn = connect()
    try:
        conn.execute("""CREATE TABLE IF NOT EXISTS items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT NOT NULL,
            title TEXT NOT NULL DEFAULT '',
            category TEXT NOT NULL,
            amount REAL NOT NULL,
            duration REAL NOT NULL DEFAULT 0,
            note TEXT)""")
        columns = [row["name"] for row in conn.execute("PRAGMA table_info(items)")]
        if "title" not in columns:
            conn.execute("ALTER TABLE items ADD COLUMN title TEXT NOT NULL DEFAULT ''")
        if "duration" not in columns:
            conn.execute("ALTER TABLE items ADD COLUMN duration REAL NOT NULL DEFAULT 0")
        conn.commit()
    finally:
        conn.close()


def load(category=None):
    """Повертає список словників, за бажанням лише однієї категорії."""
    conn = connect()
    try:
        if category is None:
            rows = conn.execute("SELECT * FROM items ORDER BY date DESC, id DESC").fetchall()
        else:
            rows = conn.execute(
                "SELECT * FROM items WHERE category = ? ORDER BY date DESC, id DESC",
                (category,)).fetchall()
    finally:
        conn.close()
    return [dict(row) for row in rows]


def add(date, title, category, amount, duration, note):
    """Додає запис і повертає його id."""
    conn = connect()
    try:
        cur = conn.execute(
            "INSERT INTO items (date, title, category, amount, duration, note) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            (date, title, category, amount, duration, note))
        conn.commit()
        return cur.lastrowid
    finally:
        conn.close()


def delete(item_id):
    """Видаляє запис. Повертає True, якщо такий був."""
    conn = connect()
    try:
        cur = conn.execute("DELETE FROM items WHERE id = ?", (item_id,))
        conn.commit()
        return cur.rowcount > 0
    finally:
        conn.close()