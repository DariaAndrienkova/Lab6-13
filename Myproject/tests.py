import logic

records = [
    {
        "date": "2026-10-01",
        "title": "Музей",
        "category": "музей",
        "cost": 200,
        "duration": 2,
        "comment": "Екскурсія"
    },
    {
        "date": "2026-10-05",
        "title": "Парк",
        "category": "парк",
        "cost": 100,
        "duration": 1,
        "comment": "Прогулянка"
    },
    {
        "date": "2026-11-01",
        "title": "Замок",
        "category": "музей",
        "cost": 300,
        "duration": 3,
        "comment": "Подорож"
    }
]


# Перевірка total_by_category
assert logic.total_by_category(records)["музей"] == 500
assert logic.total_by_category(records)["парк"] == 100

# Перевірка total_by_month
assert logic.total_by_month(records)["2026-10"] == 300
assert logic.total_by_month(records)["2026-11"] == 300

# Перевірка find_by_category
assert len(logic.find_by_category(records, "музей")) == 2
assert len(logic.find_by_category(records, "парк")) == 1

# Перевірка max_amount_item
assert logic.max_amount_item(records)["cost"] == 300
assert logic.max_amount_item(records)["title"] == "Замок"

print("Усі тести пройдено успішно!")