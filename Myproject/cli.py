import sys
import storage
import logic

FILE = "data.txt"


def main():
    if len(sys.argv) < 2:
        print("використання: python cli.py add|list|find|report ...")
        return

    command = sys.argv[1]
    records = storage.load(FILE)

    if command == "add":
        # Очікуємо: python cli.py add 2025-05-31 Пирогово музей 200 4.0 опис
        if len(sys.argv) < 7:
            print("використання: python cli.py add ДАТА НАЗВА КАТЕГОРІЯ ВАРТІСТЬ ТРИВАЛІСТЬ [КОМЕНТАР]")
            return
        try:
            cost = float(sys.argv[5])
            duration = float(sys.argv[6])
        except ValueError:
            print("помилка: вартість і тривалість мають бути числами")
            return

        note = sys.argv[7] if len(sys.argv) > 7 else ""

        records.append({
            "date": sys.argv[2],
            "title": sys.argv[3],
            "category": sys.argv[4],
            "cost": cost,
            "duration": duration,
            "note": note
        })
        storage.save(FILE, records)
        print("Запис успішно додано!")

    elif command == "list":
        if not records:
            print("Список поки порожній.")
            return
        for r in records:
            print(f"{r['date']} | {r['title']} ({r['category']}) — {r['cost']} грн, {r['duration']} год. | {r['note']}")

    elif command == "find":
        if len(sys.argv) < 3:
            print("використання: python cli.py find КАТЕГОРІЯ")
            return
        found = logic.find_by_category(records, sys.argv[2])
        for r in found:
            print(f"{r['date']} | {r['title']} — {r['cost']} грн ({r['duration']} год.)")

    elif command == "report":
        print("--- Витрати за категоріями ---")
        for cat, total in logic.total_by_category(records).items():
            print(f"{cat:<12} {total:>8.2f} грн")

        print("\n--- Витрати за місяцями ---")
        for month, total in logic.total_by_month(records).items():
            print(f"{month:<10} {total:>8.2f} грн")

        expensive = logic.max_cost_item(records)
        if expensive:
            print(f"\nНайбільша витрата: {expensive['title']} ({expensive['cost']} грн)")
    else:
        print("невідома команда:", command)


if name == "__main__":
    main()