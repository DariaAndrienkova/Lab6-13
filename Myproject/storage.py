import sqlite3

DB = "data.db"

def connect():
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row      # рядки можна читати як словники
    return conn

def init():
    """Створює таблицю, якщо її ще немає."""
    with connect() as conn:
        conn.execute("""CREATE TABLE IF NOT EXISTS items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT NOT NULL,
            category TEXT NOT NULL,
            amount REAL NOT NULL,
            note TEXT)""")

def load(category=None):
    """Повертає список словників, за бажанням лише однієї категорії."""
    with connect() as conn:
        if category is None:
            rows = conn.execute("SELECT * FROM items ORDER BY date").fetchall()
        else:
            rows = conn.execute("SELECT * FROM items WHERE category = ? ORDER BY date",
                                (category,)).fetchall()
    result = []
    for row in rows:
        result.append(dict(row))
    return result

def add(date, category, amount, note):
    """Додає запис і повертає його id."""
    with connect() as conn:
        cur = conn.execute("INSERT INTO items (date, category, amount, note) VALUES (?, ?, ?, ?)",
                           (date, category, amount, note))
        return cur.lastrowid

def delete(item_id):
    """Видаляє запис. Повертає True, якщо такий був."""
    with connect() as conn:
        cur = conn.execute("DELETE FROM items WHERE id = ?", (item_id,))
        return cur.rowcount > 0