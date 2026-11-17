import hmac
import os

from dotenv import load_dotenv
from flask import Flask, request, jsonify, abort
from flask_cors import CORS
import storage
import logic

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


def number_field(data, name, required=True):
    """Повертає число з поля або кидає ValueError з поясненням."""
    if name not in data or data[name] in ("", None):
        if required:
            raise ValueError(f"немає поля {name}")
        return 0.0
    try:
        value = float(data[name])
    except (ValueError, TypeError):
        raise ValueError(f"{name} має бути числом")
    if value < 0:
        raise ValueError(f"{name} не може бути від'ємним")
    return value


@app.get("/")
def index():
    return jsonify({
        "status": "ok",
        "message": "API is running",
        "endpoints": {"items": "/items", "report": "/report"}
    })


@app.get("/items")
def list_items():
    category = request.args.get("category")       # ?category=музей або None
    return jsonify(storage.load(category))


@app.post("/items")
def add_item():
    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        return jsonify({"error": "очікується JSON"}), 400
    for field in ("date", "title", "category"):
        if not str(data.get(field, "")).strip():
            return jsonify({"error": f"немає поля {field}"}), 400
    try:
        amount = number_field(data, "amount")
        duration = number_field(data, "duration", required=False)
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    new_id = storage.add(
        str(data["date"]).strip(),
        str(data["title"]).strip(),
        str(data["category"]).strip(),
        amount,
        duration,
        str(data.get("note", "")).strip(),
    )
    return jsonify({"id": new_id}), 201


@app.get("/report")
def report():
    records = storage.load()
    return jsonify({
        "by_category": logic.total_by_category(records),
        "by_month": logic.total_by_month(records),
        "max_item": logic.max_amount_item(records),
    })


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


@app.get("/admin/export")
def admin_export():
    require_admin()
    return jsonify(storage.load())


@app.delete("/admin/items/<int:item_id>")
def admin_delete_item(item_id):
    require_admin()
    if storage.delete(item_id):
        return jsonify({"deleted": item_id})
    return jsonify({"error": "не знайдено"}), 404


if __name__ == "__main__":
    app.run(debug=True, port=8000)