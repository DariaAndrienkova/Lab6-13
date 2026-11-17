"""Робить існуючого користувача адміністратором. Запускається лише на сервері (ноутбуці):

    python make_admin.py ВАШ_ЛОГІН

Через інтернет зробити себе адміном неможливо: такого маршруту в API немає.
"""
import sys

import storage

if len(sys.argv) != 2:
    print("використання: python make_admin.py ЛОГІН")
elif storage.set_admin(sys.argv[1]):
    print("Готово:", sys.argv[1], "тепер адміністратор.")
else:
    print("Такого користувача немає. Логіни:",
          [r["login"] for r in storage.connect().execute("SELECT login FROM users")])