import os
import sqlite3

import migrate
import storage


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


def test_migrate_moves_everything_without_loss(tmp_path):
    os.environ["DB_PATH"] = str(tmp_path / "old.db")
    make_old_db(os.environ["DB_PATH"])
    migrate.main()
    items = storage.load()
    assert len(items) == 3
    assert items[0].title == "(без назви)"          # у старих записів назви не було
    assert round(sum(i.amount for i in items), 2) == 350.5
    conn = storage.connect()
    assert conn.execute("SELECT COUNT(*) FROM categories").fetchone()[0] == 2   # музей / Музей злились
    conn.close()


def test_migrate_twice_is_harmless(tmp_path):
    os.environ["DB_PATH"] = str(tmp_path / "old.db")
    make_old_db(os.environ["DB_PATH"])
    migrate.main()
    migrate.main()
    assert len(storage.load()) == 3