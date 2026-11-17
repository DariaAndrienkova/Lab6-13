from datetime import datetime


def _clean_text(value, field):
    """Обрізає пробіли і не дозволяє порожнє значення."""
    text = str(value).strip() if value is not None else ""
    if not text:
        raise ValueError(f"немає поля {field}")
    return text


def _clean_number(value, field, required=True):
    """Перетворює на число, не дозволяє текст і від'ємні значення."""
    if value is None or value == "":
        if required:
            raise ValueError(f"немає поля {field}")
        return 0.0
    try:
        number = float(value)
    except (ValueError, TypeError):
        raise ValueError(f"{field} має бути числом")
    if number < 0:
        raise ValueError(f"{field} не може бути від'ємним")
    return number


class Item:
    """Один запис: екскурсія з датою, назвою, категорією, вартістю, тривалістю і коментарем."""

    def __init__(self, date, title, category, amount, duration=0, note="", item_id=None):
        self.id = item_id
        self.date = _clean_text(date, "date")
        try:
            datetime.strptime(self.date, "%Y-%m-%d")
        except ValueError:
            raise ValueError("date має бути у форматі РРРР-ММ-ДД")
        self.title = _clean_text(title, "title")
        self.category = _clean_text(category, "category")
        self.amount = _clean_number(amount, "amount")            # тут рядок стає числом
        self.duration = _clean_number(duration, "duration", required=False)
        self.note = str(note).strip() if note is not None else ""

    def to_dict(self):
        """Для jsonify і для відповіді API."""
        return {"id": self.id, "date": self.date, "title": self.title,
                "category": self.category, "amount": self.amount,
                "duration": self.duration, "note": self.note}

    @staticmethod
    def from_row(row):
        """З рядка sqlite3.Row у об'єкт. category у рядку це вже назва категорії (після JOIN)."""
        # старі записи з лаби 7 можуть бути без назви: показуємо заглушку, а не падаємо
        return Item(row["date"], row["title"] or "(без назви)", row["category"], row["amount"],
                    row["duration"], row["note"], row["id"])

    def is_large(self, limit):
        return self.amount > limit