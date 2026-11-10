def load(filename):
    """Повертає список словників із файла. Пошкоджені рядки пропускає."""
    records = []
    try:
        f = open(filename, "r", encoding="utf-8")
    except FileNotFoundError:
        return records  # файла ще немає: повертаємо порожній список
    with f:
        for line in f:
            line = line.strip()
            if line == "":
                continue
            parts = line.split(";")
            try:
                record = {
                    "date": parts[0],
                    "title": parts[1],
                    "category": parts[2],
                    "cost": float(parts[3]),
                    "duration": float(parts[4]),
                    "note": parts[5] if len(parts) > 5 else "",
                }
            except (IndexError, ValueError):
                print("пропущено пошкоджений рядок:", line)
                continue
            records.append(record)
    return records

def save(filename, records):
    """Записує всі записи у файл."""
    with open(filename, "w", encoding="utf-8") as f:
        for r in records:
            f.write(f"{r['date']};{r['title']};{r['category']};{r['cost']};{r['duration']};{r['note']}\n")