"""Копіює базу в теку backups поруч зі скриптом, з датою в назві."""
import datetime
import os
import sqlite3

import storage

BASE = os.path.dirname(os.path.abspath(__file__))
BACKUPS = os.path.join(BASE, "backups")

os.makedirs(BACKUPS, exist_ok=True)
target = os.path.join(BACKUPS, f"data-{datetime.date.today()}.db")
src = sqlite3.connect(storage.db_path())
dst = sqlite3.connect(target)
src.backup(dst)                        # коректна копія навіть під час роботи сервісу
dst.close()
src.close()
print("збережено", target)