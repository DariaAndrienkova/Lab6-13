from logic import total_by_category, find_by_category, max_cost_item


def test_logic():
    sample_records = [
        {"date": "2025-05-31", "title": "Пирогово", "category": "музей", "cost": 200.0, "duration": 4.0, "note": ""},
        {"date": "2025-06-01", "title": "Кафе", "category": "їжа", "cost": 150.0, "duration": 1.0, "note": ""},
        {"date": "2025-05-20", "title": "Оперний театр", "category": "музей", "cost": 500.0, "duration": 3.0,
         "note": ""}
    ]

    # Тести для total_by_category
    totals = total_by_category(sample_records)
    assert totals["музей"] == 700.0, "Помилка підрахунку суми для музеїв"
    assert totals["їжа"] == 150.0, "Помилка підрахунку суми для їжі"

    # Тести для find_by_category
    museums = find_by_category(sample_records, "музей")
    assert len(museums) == 2, "Має знайти рівно 2 музеї"

    empty = find_by_category(sample_records, "театр")
    assert len(empty) == 0, "Для неіснуючої категорії список має бути порожнім"

    # Тести для max_cost_item
    expensive = max_cost_item(sample_records)
    assert expensive["title"] == "Оперний театр", "Неправильно визначено найдорожчий запис"

    print("Успіх: усі тести з logic.py успішно пройшли перевірку!")


if __name__ == "__main__":
    test_logic()