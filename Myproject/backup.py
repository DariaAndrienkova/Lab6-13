"""Копіює базу в теку backups поруч зі скриптом, з датою в назві.

Шукає базу так: змінна DB_PATH, інакше data/data.db (так лежить база в myproject-server),
інакше data.db поруч зі скриптом (так вона лежить у робочій теці).
"""
import datetime
import os
import sqlite3
import sys

import storage

BASE = os.path.dirname(os.path.abspath(__file__))
BACKUPS = os.path.join(BASE, "backups")

path = os.environ.get("DB_PATH")
if not path:
    in_data = os.path.join(BASE, "data", "data.db")
    path = in_data if os.path.exists(in_data) else storage.db_path()
if not os.path.exists(path):                 # sqlite3.connect створив би порожню базу, тому перевіряємо
    print("Бази немає:", path)
    sys.exit(1)

os.makedirs(BACKUPS, exist_ok=True)
target = os.path.join(BACKUPS, f"data-{datetime.date.today()}.db")
src = sqlite3.connect(path)
dst = sqlite3.connect(target)
src.backup(dst)                        # коректна копія навіть під час роботи сервісу
dst.close()
src.close()
print("збережено", target, "з", path)