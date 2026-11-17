import os
import sqlite3

import migrate


def make_old_db(path):
    conn = sqlite3.connect(path)
    conn.execute("CREATE TABLE items (id INTEGER PRIMARY KEY AUTOINCREMENT, date TEXT NOT NULL, "
                 "category TEXT NOT NULL, amount REAL NOT NULL, note TEXT)")
    conn.executemany("INSERT INTO items (date, category, amount, note) VALUES (?, ?, ?, ?)", [
        ("2026-10-01", "музей", 200.0, "а"),
        ("2026-10-02", "Музей", 100.0, "б"),
        ("2026-10-03", "їжа", 50.5, None),
    ])
    conn.commit()
    conn.close()


def read(path, sql):
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    try:
        return conn.execute(sql).fetchall()
    finally:
        conn.close()


def test_migrate_moves_everything_without_loss(tmp_path):
    path = str(tmp_path / "old.db")
    os.environ["DB_PATH"] = path
    make_old_db(path)
    migrate.main()
    items = read(path, "SELECT * FROM items ORDER BY id")
    assert len(items) == 3
    assert items[0]["title"] == ""                  # у старих записів назви не було
    assert round(sum(i["amount"] for i in items), 2) == 350.5
    assert read(path, "SELECT COUNT(*) AS n FROM categories")[0]["n"] == 2   # музей / Музей злились


def test_migrate_twice_is_harmless(tmp_path):
    path = str(tmp_path / "old.db")
    os.environ["DB_PATH"] = path
    make_old_db(path)
    migrate.main()
    migrate.main()
    assert len(read(path, "SELECT * FROM items")) == 3