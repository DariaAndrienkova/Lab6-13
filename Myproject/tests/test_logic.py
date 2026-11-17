import pytest

from logic import total_by_category, total_by_month, find_by_category, max_amount_item
from models import Item


def sample():
    return [
        Item("2025-05-31", "Пирогово", "музей", 200, 4),
        Item("2025-06-01", "Кафе", "їжа", 150, 1),
        Item("2025-05-20", "Оперний театр", "музей", 500, 3),
    ]


def test_total_by_category_sums_per_category():
    assert total_by_category(sample()) == {"музей": 700.0, "їжа": 150.0}


def test_total_by_category_empty():
    assert total_by_category([]) == {}


def test_total_by_month_sums_per_month():
    assert total_by_month(sample()) == {"2025-05": 700.0, "2025-06": 150.0}


def test_find_by_category_ignores_case_and_returns_empty_for_unknown():
    assert len(find_by_category(sample(), "МУЗЕЙ")) == 2
    assert find_by_category(sample(), "театр") == []


def test_max_amount_item_returns_most_expensive():
    assert max_amount_item(sample()).title == "Оперний театр"


def test_max_amount_item_empty_is_none():
    assert max_amount_item([]) is None


def test_item_converts_amount_to_float():
    assert Item("2025-05-31", "Х", "музей", "200").amount == 200.0


def test_item_rejects_text_amount():
    with pytest.raises(ValueError):
        Item("2025-05-31", "Х", "музей", "abc")


def test_item_rejects_negative_amount_and_bad_date():
    with pytest.raises(ValueError):
        Item("2025-05-31", "Х", "музей", -5)
    with pytest.raises(ValueError):
        Item("31.05.2025", "Х", "музей", 5)


def test_item_is_large():
    assert Item("2025-05-31", "Х", "музей", 200).is_large(100) is True
    assert Item("2025-05-31", "Х", "музей", 50).is_large(100) is False