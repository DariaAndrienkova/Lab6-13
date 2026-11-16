def total_by_category(records):
    """Повертає словник {категорія: сума витрат}."""
    totals = {}
    for r in records:
        cat = r["category"]
        if cat not in totals:
            totals[cat] = 0.0
        totals[cat] += r["amount"]
    return totals

def total_by_month(records):
    """Повертає суму витрат за місяцями (формат YYYY-MM)."""
    totals = {}
    for r in records:
        month = r["date"][:7] if len(r["date"]) >= 7 else "інше"
        if month not in totals:
            totals[month] = 0.0
        totals[month] += r["amount"]
    return totals

def find_by_category(records, category):
    """Повертає список екскурсій, що відповідають категорії."""
    result = []
    for r in records:
        if r["category"].lower() == category.lower():
            result.append(r)
    return result

def max_amount_item(records):
    """Повертає найдорожчий запис."""
    if not records:
        return None
    max_r = records[0]
    for r in records:
        if r["amount"] > max_r["amount"]:
            max_r = r
    return max_r