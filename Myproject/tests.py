from logic import total_by_category, total_by_month, find_by_category, max_amount_item

SAMPLE = [
    {"date": "2025-05-31", "title": "Пирогово", "category": "музей", "amount": 200.0, "duration": 4.0, "note": ""},
    {"date": "2025-06-01", "title": "Кафе", "category": "їжа", "amount": 150.0, "duration": 1.0, "note": ""},
    {"date": "2025-05-20", "title": "Оперний театр", "category": "музей", "amount": 500.0, "duration": 3.0, "note": ""},
]


def test_total_by_category():
    totals = total_by_category(SAMPLE)
    assert totals["музей"] == 700.0, "Помилка підрахунку суми для музеїв"
    assert totals["їжа"] == 150.0, "Помилка підрахунку суми для їжі"
    assert total_by_category([]) == {}, "Для порожнього списку має бути порожній словник"


def test_total_by_month():
    totals = total_by_month(SAMPLE)
    assert totals["2025-05"] == 700.0, "Помилка підрахунку за травень"
    assert totals["2025-06"] == 150.0, "Помилка підрахунку за червень"
    assert total_by_month([]) == {}, "Для порожнього списку має бути порожній словник"


def test_find_by_category():
    assert len(find_by_category(SAMPLE, "музей")) == 2, "Має знайти рівно 2 музеї"
    assert len(find_by_category(SAMPLE, "МУЗЕЙ")) == 2, "Пошук не має залежати від регістру"
    assert len(find_by_category(SAMPLE, "театр")) == 0, "Для неіснуючої категорії список має бути порожнім"


def test_max_amount_item():
    assert max_amount_item(SAMPLE)["title"] == "Оперний театр", "Неправильно визначено найдорожчий запис"
    assert max_amount_item([]) is None, "Для порожнього списку має бути None"


def run_all():
    test_total_by_category()
    test_total_by_month()
    test_find_by_category()
    test_max_amount_item()
    print("Успіх: усі тести з logic.py успішно пройшли перевірку!")


if __name__ == "__main__":
    run_all()