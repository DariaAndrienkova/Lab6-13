import hmac
import os
from datetime import datetime

from dotenv import load_dotenv
from flask import Flask, request, jsonify, abort
from flask_cors import CORS

import logic
import storage
from models import Item

load_dotenv()                                   # читає файл .env з теки проєкту
ADMIN_TOKEN = os.environ.get("ADMIN_TOKEN")

app = Flask(__name__)
app.json.ensure_ascii = False          # кирилиця у JSON читабельна
CORS(app, origins=[
    "https://andrienkova.pp.ua",       # справжній фронтенд
    "http://localhost:8080",           # локальна перевірка (python -m http.server 8080)
])
storage.init()


@app.after_request
def set_utf8(response):
    """Явно кажемо браузеру, що JSON у кодуванні UTF-8 (інакше телефон показує нісенітницю)."""
    if response.mimetype == "application/json":
        response.headers["Content-Type"] = "application/json; charset=utf-8"
    return response


def require_admin():
    """Адмінка лише не через Cloudflare і лише з токеном."""
    # Cloudflare додає CF-Connecting-IP до кожного запиту з інтернету.
    # Є заголовок, отже запит прийшов через тунель: адмінки для нього не існує.
    if "CF-Connecting-IP" in request.headers:
        abort(404)
    token = request.headers.get("X-Admin-Token", "")
    # Якщо ADMIN_TOKEN не заданий у .env, адмінка закрита для всіх
    if not ADMIN_TOKEN or not hmac.compare_digest(token, ADMIN_TOKEN):
        abort(403)


@app.get("/")
def index():
    return jsonify({
        "status": "ok",
        "message": "API is running",
        "endpoints": {"items": "/items", "report": "/report",
                      "report_by_category": "/report/categories"}
    })


@app.get("/items")
def list_items():
    category = request.args.get("category")       # ?category=музей або None
    return jsonify([item.to_dict() for item in storage.load(category)])


@app.post("/items")
def add_item():
    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        return jsonify({"error": "очікується JSON"}), 400
    try:
        item = Item(data.get("date"), data.get("title"), data.get("category"),
                    data.get("amount"), data.get("duration"), data.get("note", ""))
    except ValueError as e:                       # клас сам перевіряє поля
        return jsonify({"error": str(e)}), 400
    new_id = storage.add(item)
    return jsonify({"id": new_id}), 201


@app.get("/report")
def report():
    items = storage.load()
    expensive = logic.max_amount_item(items)
    return jsonify({
        "by_category": logic.total_by_category(items),
        "by_month": logic.total_by_month(items),
        "max_item": expensive.to_dict() if expensive else None,
    })


@app.get("/report/categories")
def report_categories():
    """Звіт через JOIN: сума за категорією і місячний ліміт. ?month=2026-11 для одного місяця."""
    month = request.args.get("month")
    if month is not None:
        try:
            datetime.strptime(month, "%Y-%m")
        except ValueError:
            return jsonify({"error": "month має бути у форматі РРРР-ММ"}), 400
    return jsonify(storage.report_by_category(month))


@app.get("/admin/export")
def admin_export():
    require_admin()
    return jsonify([item.to_dict() for item in storage.load()])


@app.delete("/admin/items/<int:item_id>")
def admin_delete_item(item_id):
    require_admin()
    if storage.delete(item_id):
        return jsonify({"deleted": item_id})
    return jsonify({"error": "не знайдено"}), 404


@app.get("/admin/log")
def admin_log():
    require_admin()
    try:
        limit = int(request.args.get("limit", 50))
    except ValueError:
        return jsonify({"error": "limit має бути числом"}), 400
    limit = max(1, min(limit, 500))
    return jsonify(storage.audit_load(limit))


@app.put("/admin/categories/<name>")
def admin_set_limit(name):
    """Задає місячний ліміт категорії: {"monthly_limit": 1000}. null знімає ліміт."""
    require_admin()
    data = request.get_json(silent=True)
    if not isinstance(data, dict) or "monthly_limit" not in data:
        return jsonify({"error": "очікується JSON з полем monthly_limit"}), 400
    value = data["monthly_limit"]
    if value is not None:
        try:
            value = float(value)
        except (ValueError, TypeError):
            return jsonify({"error": "monthly_limit має бути числом"}), 400
        if value < 0:
            return jsonify({"error": "monthly_limit не може бути від'ємним"}), 400
    storage.set_limit(name, value)
    return jsonify({"category": name, "monthly_limit": value})


if __name__ == "__main__":
    app.run(debug=True, port=8000)