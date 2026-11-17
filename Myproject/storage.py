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
    conn.execute("""CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        login TEXT NOT NULL UNIQUE COLLATE NOCASE,
        password_hash TEXT NOT NULL,
        is_admin INTEGER NOT NULL DEFAULT 0,
        created TEXT NOT NULL)""")
    conn.execute("""CREATE TABLE IF NOT EXISTS categories (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL UNIQUE,
        monthly_limit REAL)""")
    conn.execute("""CREATE TABLE IF NOT EXISTS items (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL REFERENCES users(id),
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
        details TEXT,
        user_id INTEGER)""")


def init():
    """Готує базу. Стару базу не чіпає, а підказує, яку міграцію запустити."""
    conn = connect()
    try:
        create_tables(conn)
        columns = [row["name"] for row in conn.execute("PRAGMA table_info(items)")]
        if "category_id" not in columns:
            raise RuntimeError("База старого формату. Зробіть бекап і запустіть: python migrate.py")
        if "user_id" not in columns:
            raise RuntimeError("База без користувачів. Зробіть бекап і запустіть: "
                               "python migrate_users.py ВАШ_ЛОГІН")
        conn.commit()
    finally:
        conn.close()


# ---------- користувачі ----------

def add_user(login, password_hash):
    """Створює користувача. Якщо логін зайнятий, кидає sqlite3.IntegrityError."""
    conn = connect()
    try:
        cur = conn.execute(
            "INSERT INTO users (login, password_hash, is_admin, created) VALUES (?, ?, 0, ?)",
            (login, password_hash, datetime.datetime.now().isoformat(timespec="seconds")))
        conn.commit()
        return cur.lastrowid
    finally:
        conn.close()


def get_user_by_login(login):
    conn = connect()
    try:
        return conn.execute("SELECT * FROM users WHERE login = ?", (login,)).fetchone()
    finally:
        conn.close()


def get_user(user_id):
    conn = connect()
    try:
        return conn.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
    finally:
        conn.close()


def set_admin(login, value=True):
    """Робить користувача адміністратором. Викликається лише локально (make_admin.py)."""
    conn = connect()
    try:
        cur = conn.execute("UPDATE users SET is_admin = ? WHERE login = ?",
                           (1 if value else 0, login))
        conn.commit()
        return cur.rowcount > 0
    finally:
        conn.close()


# ---------- журнал і категорії ----------

def get_or_create_category(conn, name):
    """Повертає id категорії. Назви 'Музей' і 'музей' вважаються однією категорією."""
    name = name.strip()
    for row in conn.execute("SELECT id, name FROM categories"):
        if row["name"].casefold() == name.casefold():
            return row["id"]
    cur = conn.execute("INSERT INTO categories (name) VALUES (?)", (name,))
    return cur.lastrowid


def log_action(conn, action, item_id=None, details="", user_id=None):
    """Один рядок у журнал. Викликається в тій самій транзакції, що й основна дія."""
    conn.execute(
        "INSERT INTO audit_log (ts, action, item_id, details, user_id) VALUES (?, ?, ?, ?, ?)",
        (datetime.datetime.now().isoformat(timespec="seconds"), action, item_id, details, user_id))


# ---------- записи ----------

_SELECT_ITEMS = """SELECT i.id, i.date, i.title, c.name AS category, i.amount, i.duration, i.note
                   FROM items i JOIN categories c ON c.id = i.category_id"""


def load(user_id, category=None):
    """Повертає список Item лише цього користувача, за бажанням однієї категорії."""
    conn = connect()
    try:
        rows = conn.execute(
            _SELECT_ITEMS + " WHERE i.user_id = ? ORDER BY i.date DESC, i.id DESC",
            (user_id,)).fetchall()
    finally:
        conn.close()
    items = [Item.from_row(row) for row in rows]
    if category is not None:
        items = [i for i in items if i.category.casefold() == category.casefold()]
    return items


def export_all():
    """Усі записи всіх користувачів зі логіном власника. Лише для адміністратора."""
    conn = connect()
    try:
        rows = conn.execute(
            """SELECT i.id, i.date, i.title, c.name AS category, i.amount, i.duration, i.note,
                      u.login AS owner
               FROM items i
               JOIN categories c ON c.id = i.category_id
               JOIN users u ON u.id = i.user_id
               ORDER BY i.date DESC, i.id DESC""").fetchall()
    finally:
        conn.close()
    result = []
    for row in rows:
        data = Item.from_row(row).to_dict()
        data["owner"] = row["owner"]
        result.append(data)
    return result


def add(item, user_id):
    """Додає Item для користувача, пише в журнал, повертає id нового запису."""
    conn = connect()
    try:
        category_id = get_or_create_category(conn, item.category)
        cur = conn.execute(
            "INSERT INTO items (user_id, date, title, category_id, amount, duration, note) "
            "VALUES (?, ?, ?, ?, ?, ?, ?)",
            (user_id, item.date, item.title, category_id, item.amount, item.duration, item.note))
        new_id = cur.lastrowid
        log_action(conn, "add", new_id, f"{item.title}, {item.category}, {item.amount}", user_id)
        conn.commit()
        return new_id
    finally:
        conn.close()


def delete(item_id, actor_id, owner_id=None):
    """Видаляє запис і пише в журнал, хто саме видалив (actor_id).
    Якщо вказано owner_id, видаляє лише запис цього власника (звичайний користувач).
    Без owner_id видаляє будь-який (адміністратор).
    Повертає True, якщо запис був і видалений."""
    conn = connect()
    try:
        if owner_id is None:
            row = conn.execute("SELECT title FROM items WHERE id = ?", (item_id,)).fetchone()
        else:
            row = conn.execute("SELECT title FROM items WHERE id = ? AND user_id = ?",
                               (item_id, owner_id)).fetchone()
        if row is None:
            return False
        conn.execute("DELETE FROM items WHERE id = ?", (item_id,))
        log_action(conn, "delete", item_id, row["title"], actor_id)
        conn.commit()
        return True
    finally:
        conn.close()


def report_by_category(user_id, month=None):
    """Звіт через JOIN для одного користувача: сума за категорією, ліміт і чи перевищено його.
    month у форматі РРРР-ММ; без нього рахуються всі записи."""
    pattern = (month + "-%") if month else "%"
    conn = connect()
    try:
        rows = conn.execute(
            """SELECT c.name, SUM(i.amount) AS total, c.monthly_limit
               FROM items i
               JOIN categories c ON c.id = i.category_id
               WHERE i.user_id = ? AND i.date LIKE ?
               GROUP BY c.id
               ORDER BY total DESC""", (user_id, pattern)).fetchall()
    finally:
        conn.close()
    return [{"category": r["name"], "total": r["total"], "monthly_limit": r["monthly_limit"],
             "over_limit": r["monthly_limit"] is not None and r["total"] > r["monthly_limit"]}
            for r in rows]


def set_limit(name, monthly_limit, actor_id):
    """Задає (або знімає, якщо None) місячний ліміт категорії. Категорію створює, якщо її немає."""
    conn = connect()
    try:
        category_id = get_or_create_category(conn, name)
        conn.execute("UPDATE categories SET monthly_limit = ? WHERE id = ?",
                     (monthly_limit, category_id))
        log_action(conn, "set_limit", None, f"{name.strip()}: {monthly_limit}", actor_id)
        conn.commit()
    finally:
        conn.close()


def audit_load(limit=50):
    """Останні записи журналу, найновіші першими, з логіном того, хто зробив дію."""
    conn = connect()
    try:
        rows = conn.execute(
            """SELECT a.id, a.ts, a.action, a.item_id, a.details, a.user_id, u.login
               FROM audit_log a LEFT JOIN users u ON u.id = a.user_id
               ORDER BY a.id DESC LIMIT ?""", (limit,)).fetchall()
    finally:
        conn.close()
    return [dict(r) for r in rows]