import csv
import os

FILE = "data.txt"

def load(filename=FILE):
records = []

if not os.path.exists(filename):
    return records

with open(filename, "r", encoding="utf-8", newline="") as file:
    reader = csv.reader(file, delimiter=";")

    for row in reader:
        if len(row) != 6:
            continue

        try:
            record = {
                "date": row[0],
                "title": row[1],
                "category": row[2],
                "cost": float(row[3]),
                "duration": float(row[4]),
                "comment": row[5]
            }

            records.append(record)

        except ValueError:
            continue

return records
def save(records, filename=FILE):
with open(filename, "w", encoding="utf-8", newline="") as file:
writer = csv.writer(file, delimiter=";")

    for record in records:
        writer.writerow([
            record["date"],
            record["title"],
            record["category"],
            record["cost"],
            record["duration"],
            record["comment"]
        ])