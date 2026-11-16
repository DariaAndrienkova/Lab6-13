def total_by_category(records):
    totals = {}

    for record in records:
        category = record["category"]

        if category not in totals:
            totals[category] = 0

        totals[category] += record["cost"]

    return totals


def total_by_month(records):
    totals = {}

    for record in records:
        month = record["date"][:7]

        if month not in totals:
            totals[month] = 0

        totals[month] += record["cost"]

    return totals


def find_by_category(records, category):
    result = []

    for record in records:
        if record["category"].lower() == category.lower():
            result.append(record)

    return result


def max_amount_item(records):
    if not records:
        return None

    return max(records, key=lambda record: record["cost"])