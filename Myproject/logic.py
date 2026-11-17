def total_by_category(records):
    """Повертає словник {категорія: сума витрат}. records це список Item."""
    totals = {}
    for r in records:
        if r.category not in totals:
            totals[r.category] = 0.0
        totals[r.category] += r.amount
    return totals


def total_by_month(records):
    """Повертає суму витрат за місяцями (формат YYYY-MM)."""
    totals = {}
    for r in records:
        month = r.date[:7] if len(r.date) >= 7 else "інше"
        if month not in totals:
            totals[month] = 0.0
        totals[month] += r.amount
    return totals


def find_by_category(records, category):
    """Повертає список екскурсій, що відповідають категорії (регістр не важливий)."""
    result = []
    for r in records:
        if r.category.casefold() == category.casefold():
            result.append(r)
    return result


def max_amount_item(records):
    """Повертає найдорожчий запис або None, якщо список порожній."""
    if not records:
        return None
    max_r = records[0]
    for r in records:
        if r.amount > max_r.amount:
            max_r = r
    return max_r