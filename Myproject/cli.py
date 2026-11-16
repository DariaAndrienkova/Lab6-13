import sys
import storage_file
import logic


def main():
    if len(sys.argv) < 2:
        print("Команди: add, list, find, report")
        return

    command = sys.argv[1]
    records = storage_file.load()

    if command == "add":

        if len(sys.argv) < 7:
            print("Використання:")
            print("python cli.py add ДАТА НАЗВА КАТЕГОРІЯ ВАРТІСТЬ ТРИВАЛІСТЬ КОМЕНТАР")
            return

        try:
            cost = float(sys.argv[5])
            duration = float(sys.argv[6])

            if cost < 0 or duration < 0:
                print("Вартість і тривалість не можуть бути від'ємними.")
                return

        except ValueError:
            print("Вартість і тривалість мають бути числами.")
            return

        comment = " ".join(sys.argv[7:]) if len(sys.argv) > 7 else ""

        record = {
            "date": sys.argv[2],
            "title": sys.argv[3],
            "category": sys.argv[4],
            "cost": cost,
            "duration": duration,
            "comment": comment
        }

        records.append(record)
        storage_file.save(records)

        print("Екскурсію успішно додано!")

    elif command == "list":

        if not records:
            print("Записів поки немає.")
            return

        for record in records:
            print(
                f"{record['date']} | "
                f"{record['title']} | "
                f"{record['category']} | "
                f"{record['cost']} грн | "
                f"{record['duration']} год. | "
                f"{record['comment']}"
            )

    elif command == "find":

        if len(sys.argv) < 3:
            print("Вкажіть категорію для пошуку.")
            return

        result = logic.find_by_category(records, sys.argv[2])

        if not result:
            print("Нічого не знайдено.")
        else:
            for record in result:
                print(record)

    elif command == "report":

        print("Витрати за категоріями:")

        for category, total in logic.total_by_category(records).items():
            print(f"{category}: {total} грн")

        print("\nВитрати за місяцями:")

        for month, total in logic.total_by_month(records).items():
            print(f"{month}: {total} грн")

        most_expensive = logic.max_amount_item(records)

        if most_expensive:
            print("\nНайдорожча екскурсія:")
            print(most_expensive)

    else:
        print("Невідома команда.")


if __name__ == "__main__":
    main()