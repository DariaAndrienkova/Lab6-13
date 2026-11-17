import os
import sqlite3
from datetime import datetime, timedelta

from dotenv import load_dotenv
from flask import Flask, request, jsonify, abort, session
from flask_cors import CORS
from werkzeug.exceptions import HTTPException
from werkzeug.security import generate_password_hash, check_password_hash

import logic
import storage
from models import Item

load_dotenv()                                   # читає файл .env з теки проєкту

app = Flask(__name__)
app.json.ensure_ascii = False          # кирилиця у JSON читабельна

# Ключ, яким Flask підписує cookie входу. Без нього сервер не стартує: так і задумано.
if not os.environ.get("SECRET_KEY"):
    raise RuntimeError("Немає SECRET_KEY у файлі .env (довгий випадковий рядок)")
app.config["SECRET_KEY"] = os.environ["SECRET_KEY"]
app.config["SESSION_COOKIE_SECURE"] = True       # cookie лише через HTTPS
app.config["SESSION_COOKIE_HTTPONLY"] = True     # JavaScript на сторінці cookie не бачить
app.config["SESSION_COOKIE_SAMESITE"] = "Lax"
app.config["PERMANENT_SESSION_LIFETIME"] = timedelta(days=7)

CORS(app, origins=[
    "https://andrienkova.pp.ua",       # справжній фронтенд
    "http://localhost:8080",           # локальна перевірка (python -m http.server 8080)
], supports_credentials=True)          # без цього браузер не віддасть cookie сторінці
storage.init()

# Для перевірки пароля неіснуючого логіна: щоб відповідь займала стільки ж часу,
# і за швидкістю не можна було дізнатися, які логіни існують.
DUMMY_HASH = generate_password_hash("не-справжній-пароль")


@app.after_request
def set_utf8(response):
    """Явно кажемо браузеру, що JSON у кодуванні UTF-8 (інакше телефон показує нісенітницю)."""
    if response.mimetype == "application/json":
        response.headers["Content-Type"] = "application/json; charset=utf-8"
    return response


@app.errorhandler(HTTPException)
def json_errors(e):
    """Усі помилки (401, 403, 404, 405...) віддаємо як JSON, щоб фронтенд міг їх прочитати."""
    messages = {401: "потрібно увійти", 403: "недостатньо прав", 404: "не знайдено"}
    return jsonify({"error": messages.get(e.code, e.name)}), e.code


# ---------- вхід і сесії ----------

def current_user():
    """Повертає рядок users для поточної сесії або зупиняє запит з 401."""
    user_id = session.get("user_id")
    if user_id is None:
        abort(401)
    user = storage.get_user(user_id)
    if user is None:                     # користувача вже немає в базі
        session.clear()
        abort(401)
    return user


def require_admin():
    """Адмінка лише не через Cloudflare і лише для користувача з is_admin = 1."""
    # Cloudflare додає CF-Connecting-IP до кожного запиту з інтернету.
    # Є заголовок, отже запит прийшов через тунель: адмінки для нього не існує.
    if "CF-Connecting-IP" in request.headers:
        abort(404)
    user = current_user()
    if not user["is_admin"]:
        abort(403)
    return user


def credentials_from_request():
    """Дістає логін і пароль із JSON. Повертає (login, password) або (None, None)."""
    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        return None, None
    login, password = data.get("login"), data.get("password")
    if not isinstance(login, str) or not isinstance(password, str):
        return None, None
    return login.strip(), password


@app.post("/register")
def do_register():
    login, password = credentials_from_request()
    if login is None or not (3 <= len(login) <= 50) or not (8 <= len(password) <= 200):
        return jsonify({"error": "логін від 3 символів, пароль від 8"}), 400
    try:
        user_id = storage.add_user(login, generate_password_hash(password))
    except sqlite3.IntegrityError:
        return jsonify({"error": "логін зайнятий"}), 409
    session.clear()
    session["user_id"] = user_id
    session.permanent = True
    return jsonify({"id": user_id, "login": login, "is_admin": False}), 201


@app.post("/login")
def do_login():
    login_name, password = credentials_from_request()
    user = storage.get_user_by_login(login_name) if login_name else None
    if user is None:
        check_password_hash(DUMMY_HASH, password or "")      # однаковий час відповіді
        ok = False
    else:
        ok = check_password_hash(user["password_hash"], password)
    if not ok:
        # Одне повідомлення на обидва випадки: не підказуємо, які логіни існують
        return jsonify({"error": "неправильний логін або пароль"}), 401
    session.clear()                      # нова сесія після входу
    session["user_id"] = user["id"]
    session.permanent = True
    return jsonify({"id": user["id"], "login": user["login"], "is_admin": bool(user["is_admin"])})


@app.post("/logout")
def logout():
    session.clear()
    return jsonify({"ok": True})


@app.get("/me")
def me():
    """Хто зараз увійшов. Фронтенд питає це при відкритті сторінки."""
    user = current_user()
    return jsonify({"id": user["id"], "login": user["login"], "is_admin": bool(user["is_admin"])})


# ---------- дані користувача ----------

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
    user = current_user()
    category = request.args.get("category")       # ?category=музей або None
    return jsonify([item.to_dict() for item in storage.load(user["id"], category)])


@app.post("/items")
def add_item():
    user = current_user()
    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        return jsonify({"error": "очікується JSON"}), 400
    try:
        item = Item(data.get("date"), data.get("title"), data.get("category"),
                    data.get("amount"), data.get("duration"), data.get("note", ""))
    except ValueError as e:                       # клас сам перевіряє поля
        return jsonify({"error": str(e)}), 400
    new_id = storage.add(item, user["id"])
    return jsonify({"id": new_id}), 201


@app.delete("/items/<int:item_id>")
def delete_item(item_id):
    """Видаляє лише свій запис. Чужий або неіснуючий однаково дає 404."""
    user = current_user()
    if storage.delete(item_id, actor_id=user["id"], owner_id=user["id"]):
        return jsonify({"deleted": item_id})
    return jsonify({"error": "не знайдено"}), 404


@app.get("/report")
def report():
    user = current_user()
    items = storage.load(user["id"])
    expensive = logic.max_amount_item(items)
    return jsonify({
        "by_category": logic.total_by_category(items),
        "by_month": logic.total_by_month(items),
        "max_item": expensive.to_dict() if expensive else None,
    })


@app.get("/report/categories")
def report_categories():
    """Звіт через JOIN: сума за категорією і місячний ліміт. ?month=2026-11 для одного місяця."""
    user = current_user()
    month = request.args.get("month")
    if month is not None:
        try:
            datetime.strptime(month, "%Y-%m")
        except ValueError:
            return jsonify({"error": "month має бути у форматі РРРР-ММ"}), 400
    return jsonify(storage.report_by_category(user["id"], month))


# ---------- адмінка ----------

@app.get("/admin/export")
def admin_export():
    require_admin()
    return jsonify(storage.export_all())


@app.delete("/admin/items/<int:item_id>")
def admin_delete_item(item_id):
    admin = require_admin()
    if storage.delete(item_id, actor_id=admin["id"]):
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
    admin = require_admin()
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
    storage.set_limit(name, value, admin["id"])
    return jsonify({"category": name, "monthly_limit": value})


if __name__ == "__main__":
    app.run(debug=True, port=8000)