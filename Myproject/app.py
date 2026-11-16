from flask import Flask, request, jsonify
from flask_cors import CORS

import storage
import logic


app = Flask(__name__)

CORS(app, origins=["https://andrienkova.pp.ua"])

storage.init()


@app.get("/items")
def list_items():
    category = request.args.get("category")

    return jsonify(storage.load(category))


@app.post("/items")
def add_item():
    data = request.get_json(silent=True)

    if not isinstance(data, dict):
        return jsonify({"error": "Очікується JSON"}), 400

    required_fields = [
        "date",
        "title",
        "category",
        "cost",
        "duration"
    ]

    for field in required_fields:
        if field not in data:
            return jsonify({"error": f"Немає поля {field}"}), 400

    if not all(
        isinstance(data[field], str) and data[field].strip()
        for field in ("date", "title", "category")
    ):
        return jsonify({"error": "Текстові поля не можуть бути порожніми"}), 400

    try:
        cost = float(data["cost"])
        duration = float(data["duration"])

        if cost < 0 or duration < 0:
            return jsonify({"error": "Числа не можуть бути від'ємними"}), 400

    except (ValueError, TypeError):
        return jsonify({"error": "Вартість і тривалість мають бути числами"}), 400

    new_id = storage.add(
        data["date"],
        data["title"],
        data["category"],
        cost,
        duration,
        data.get("comment", "")
    )

    return jsonify({"id": new_id}), 201


@app.delete("/items/<int:item_id>")
def delete_item(item_id):
    if storage.delete(item_id):
        return jsonify({"deleted": item_id})

    return jsonify({"error": "Запис не знайдено"}), 404


@app.get("/report")
def report():
    records = storage.load()

    return jsonify({
        "by_category": logic.total_by_category(records),
        "by_month": logic.total_by_month(records)
    })


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=8000, debug=True)