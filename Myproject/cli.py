import sys
import storage
import logic


def main():
    if len(sys.argv) < 2:
        print("використання: python cli.py add|list|find|report ...")
        return

    storage.init()
    command = sys.argv[1]

    if command == "add":
        # python cli.py add 2025-05-31 Пирогово музей 200 4.0 "коментар"
        if len(sys.argv) < 7:
            print("використання: python cli.py add ДАТА НАЗВА КАТЕГОРІЯ ВАРТІСТЬ ТРИВАЛІСТЬ [КОМЕНТАР]")
            return
        try:
            amount = float(sys.argv[5])
            duration = float(sys.argv[6])
        except ValueError:
            print("помилка: вартість і тривалість мають бути числами")
            return
        note = sys.argv[7] if len(sys.argv) > 7 else ""
        storage.add(sys.argv[2], sys.argv[3], sys.argv[4], amount, duration, note)
        print("Запис успішно додано!")

    elif command == "list":
        records = storage.load()
        if not records:
            print("Список поки порожній.")
            return
        for r in records:
            print(f"{r['date']} | {r['title']} ({r['category']}) — {r['amount']} грн, "
                  f"{r['duration']} год. | {r['note']}")

    elif command == "find":
        if len(sys.argv) < 3:
            print("використання: python cli.py find КАТЕГОРІЯ")
            return
        for r in logic.find_by_category(storage.load(), sys.argv[2]):
            print(f"{r['date']} | {r['title']} — {r['amount']} грн ({r['duration']} год.)")

    elif command == "report":
        records = storage.load()
        print("--- Витрати за категоріями ---")
        for cat, total in logic.total_by_category(records).items():
            print(f"{cat:<12} {total:>8.2f} грн")

        print("\n--- Витрати за місяцями ---")
        for month, total in logic.total_by_month(records).items():
            print(f"{month:<10} {total:>8.2f} грн")

        expensive = logic.max_amount_item(records)
        if expensive:
            print(f"\nНайбільша витрата: {expensive['title']} ({expensive['amount']} грн)")

    else:
        print("невідома команда:", command)


if __name__ == "__main__":
    main()