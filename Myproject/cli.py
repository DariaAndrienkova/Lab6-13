import sys

import logic
import storage
from models import Item


def main():
    # Перший аргумент це логін: консольна програма працює від імені одного користувача.
    # Пароль не питає, бо вона запускається лише на самому сервері.
    if len(sys.argv) < 3:
        print("використання: python cli.py ЛОГІН add|list|find|report ...")
        return

    storage.init()
    user = storage.get_user_by_login(sys.argv[1])
    if user is None:
        print("Такого користувача немає.")
        return
    user_id = user["id"]
    del sys.argv[1]                  # далі розбираємо аргументи, як і раніше
    command = sys.argv[1]

    if command == "add":
        # python cli.py ЛОГІН add 2025-05-31 Пирогово музей 200 4.0 "коментар"
        if len(sys.argv) < 7:
            print("використання: python cli.py add ДАТА НАЗВА КАТЕГОРІЯ ВАРТІСТЬ ТРИВАЛІСТЬ [КОМЕНТАР]")
            return
        note = sys.argv[7] if len(sys.argv) > 7 else ""
        try:
            item = Item(sys.argv[2], sys.argv[3], sys.argv[4], sys.argv[5], sys.argv[6], note)
        except ValueError as e:
            print("помилка:", e)
            return
        storage.add(item, user_id)
        print("Запис успішно додано!")

    elif command == "list":
        records = storage.load(user_id)
        if not records:
            print("Список поки порожній.")
            return
        for r in records:
            print(f"{r.date} | {r.title} ({r.category}) — {r.amount} грн, {r.duration} год. | {r.note}")

    elif command == "find":
        if len(sys.argv) < 3:
            print("використання: python cli.py find КАТЕГОРІЯ")
            return
        for r in logic.find_by_category(storage.load(user_id), sys.argv[2]):
            print(f"{r.date} | {r.title} — {r.amount} грн ({r.duration} год.)")

    elif command == "report":
        records = storage.load(user_id)
        print("--- Витрати за категоріями ---")
        for cat, total in logic.total_by_category(records).items():
            print(f"{cat:<12} {total:>8.2f} грн")

        print("\n--- Витрати за місяцями ---")
        for month, total in logic.total_by_month(records).items():
            print(f"{month:<10} {total:>8.2f} грн")

        expensive = logic.max_amount_item(records)
        if expensive:
            print(f"\nНайбільша витрата: {expensive.title} ({expensive.amount} грн)")
    else:
        print("невідома команда:", command)


if __name__ == "__main__":
    main()