import sqlite3

DB = "data.db"


def connect():
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    return conn


def init():
    with connect() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date TEXT NOT NULL,
                title TEXT NOT NULL,
                category TEXT NOT NULL,
                cost REAL NOT NULL,
                duration REAL NOT NULL,
                comment TEXT
            )
        """)


def load(category=None):
    with connect() as conn:

        if category is None:
            rows = conn.execute(
                "SELECT * FROM items ORDER BY date"
            ).fetchall()

        else:
            rows = conn.execute(
                "SELECT * FROM items WHERE category = ? ORDER BY date",
                (category,)
            ).fetchall()

    return [dict(row) for row in rows]


def add(date, title, category, cost, duration, comment):
    with connect() as conn:
        cursor = conn.execute(
            """
            INSERT INTO items
            (date, title, category, cost, duration, comment)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (date, title, category, cost, duration, comment)
        )

        return cursor.lastrowid


def delete(item_id):
    with connect() as conn:
        cursor = conn.execute(
            "DELETE FROM items WHERE id = ?",
            (item_id,)
        )

        return cursor.rowcount > 0