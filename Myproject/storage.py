import datetime
import os
import sqlite3

from models import Item

# База лежить поруч із цим файлом (у теці Myproject), звідки б ви не запускали програму.
# Змінна DB_PATH потрібна для тестів.
BASE = os.path.dirname(os.path.abspath(__file__))


def db_path():
    return os.environ.get("DB_PATH", os.path.join(BASE, "data.db"))


def connect():
    conn = sqlite3.connect(db_path())
    conn.row_factory = sqlite3.Row            # рядки можна читати як словники
    conn.execute("PRAGMA foreign_keys = ON")  # без цього SQLite не перевіряє зв'язки
    return conn


def create_tables(conn):
    """Створює таблиці, якщо їх ще немає. Нічого не підтверджує (commit робить викликач)."""
    conn.execute("""CREATE TABLE IF NOT EXISTS categories (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL UNIQUE,
        monthly_limit REAL)""")
    conn.execute("""CREATE TABLE IF NOT EXISTS items (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        date TEXT NOT NULL,
        title TEXT NOT NULL DEFAULT '',
        category_id INTEGER NOT NULL REFERENCES categories(id),
        amount REAL NOT NULL,
        duration REAL NOT NULL DEFAULT 0,
        note TEXT)""")
    conn.execute("""CREATE TABLE IF NOT EXISTS audit_log (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        ts TEXT NOT NULL,
        action TEXT NOT NULL,
        item_id INTEGER,
        details TEXT)""")


def init():
    """Готує базу. Стару базу (без category_id) не чіпає, а просить запустити migrate.py."""
    conn = connect()
    try:
        create_tables(conn)
        columns = [row["name"] for row in conn.execute("PRAGMA table_info(items)")]
        if "category_id" not in columns:
            raise RuntimeError("База старого формату. Зробіть бекап і запустіть: python migrate.py")
        conn.commit()
    finally:
        conn.close()


def get_or_create_category(conn, name):
    """Повертає id категорії. Назви 'Музей' і 'музей' вважаються однією категорією."""
    name = name.strip()
    for row in conn.execute("SELECT id, name FROM categories"):
        if row["name"].casefold() == name.casefold():
            return row["id"]
    cur = conn.execute("INSERT INTO categories (name) VALUES (?)", (name,))
    return cur.lastrowid


def log_action(conn, action, item_id=None, details=""):
    """Один рядок у журнал. Викликається в тій самій транзакції, що й основна дія."""
    conn.execute(
        "INSERT INTO audit_log (ts, action, item_id, details) VALUES (?, ?, ?, ?)",
        (datetime.datetime.now().isoformat(timespec="seconds"), action, item_id, details))


_SELECT_ITEMS = """SELECT i.id, i.date, i.title, c.name AS category, i.amount, i.duration, i.note
                   FROM items i JOIN categories c ON c.id = i.category_id"""


def load(category=None):
    """Повертає список Item, за бажанням лише однієї категорії."""
    conn = connect()
    try:
        rows = conn.execute(_SELECT_ITEMS + " ORDER BY i.date DESC, i.id DESC").fetchall()
    finally:
        conn.close()
    items = [Item.from_row(row) for row in rows]
    if category is not None:
        items = [i for i in items if i.category.casefold() == category.casefold()]
    return items


def add(item):
    """Додає Item, пише в журнал, повертає id нового запису."""
    conn = connect()
    try:
        category_id = get_or_create_category(conn, item.category)
        cur = conn.execute(
            "INSERT INTO items (date, title, category_id, amount, duration, note) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            (item.date, item.title, category_id, item.amount, item.duration, item.note))
        new_id = cur.lastrowid
        log_action(conn, "add", new_id, f"{item.title}, {item.category}, {item.amount}")
        conn.commit()
        return new_id
    finally:
        conn.close()


def delete(item_id):
    """Видаляє запис і пише в журнал. Повертає True, якщо такий запис був."""
    conn = connect()
    try:
        row = conn.execute("SELECT title FROM items WHERE id = ?", (item_id,)).fetchone()
        if row is None:
            return False
        conn.execute("DELETE FROM items WHERE id = ?", (item_id,))
        log_action(conn, "delete", item_id, row["title"])
        conn.commit()
        return True
    finally:
        conn.close()


def report_by_category(month=None):
    """Звіт через JOIN: сума за категорією, ліміт на місяць і чи перевищено його.
    month у форматі РРРР-ММ; без нього рахуються всі записи."""
    pattern = (month + "-%") if month else "%"
    conn = connect()
    try:
        rows = conn.execute(
            """SELECT c.name, SUM(i.amount) AS total, c.monthly_limit
               FROM items i
               JOIN categories c ON c.id = i.category_id
               WHERE i.date LIKE ?
               GROUP BY c.id
               ORDER BY total DESC""", (pattern,)).fetchall()
    finally:
        conn.close()
    return [{"category": r["name"], "total": r["total"], "monthly_limit": r["monthly_limit"],
             "over_limit": r["monthly_limit"] is not None and r["total"] > r["monthly_limit"]}
            for r in rows]


def set_limit(name, monthly_limit):
    """Задає (або знімає, якщо None) місячний ліміт категорії. Категорію створює, якщо її немає."""
    conn = connect()
    try:
        category_id = get_or_create_category(conn, name)
        conn.execute("UPDATE categories SET monthly_limit = ? WHERE id = ?",
                     (monthly_limit, category_id))
        log_action(conn, "set_limit", None, f"{name.strip()}: {monthly_limit}")
        conn.commit()
    finally:
        conn.close()


def audit_load(limit=50):
    """Останні записи журналу, найновіші першими."""
    conn = connect()
    try:
        rows = conn.execute(
            "SELECT id, ts, action, item_id, details FROM audit_log ORDER BY id DESC LIMIT ?",
            (limit,)).fetchall()
    finally:
        conn.close()
    return [dict(r) for r in rows]