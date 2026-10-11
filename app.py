import os
from pathlib import Path

import mysql.connector
from dotenv import load_dotenv
from flask import Flask, jsonify, redirect, request, session
from werkzeug.security import check_password_hash, generate_password_hash

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent

app = Flask(__name__, static_folder=".", static_url_path="")
app.config["SECRET_KEY"] = os.getenv("SESSION_SECRET", "dev-secret-change-me")


def get_db():
    return mysql.connector.connect(
        host=os.getenv("DB_HOST", "localhost"),
        user=os.getenv("DB_USER", "root"),
        password=os.getenv("DB_PASSWORD", ""),
        database=os.getenv("DB_NAME", "registration"),
    )


def current_user_id():
    return session.get("user_id")


def require_auth():
    user_id = current_user_id()
    if not user_id:
        return None, jsonify({"error": "Authentication required"}), 401
    return user_id, None, None


@app.get("/")
def home():
    return redirect("/login.html")


@app.get("/api/health")
def health():
    return jsonify({"status": "ok"})


@app.get("/api/session")
def session_info():
    user_id = current_user_id()

    if not user_id:
        return jsonify({"loggedIn": False}), 200

    conn = get_db()
    cursor = conn.cursor(dictionary=True)

    try:
        cursor.execute(
            "SELECT user_id, name, email FROM users WHERE user_id = %s",
            (user_id,),
        )
        user = cursor.fetchone()
    finally:
        cursor.close()
        conn.close()

    if not user:
        session.clear()
        return jsonify({"loggedIn": False}), 200

    return jsonify({
        "loggedIn": True,
        "user": {
            "id": user["user_id"],
            "name": user["name"],
            "email": user["email"],
        },
    })


@app.post("/api/register")
def register():
    data = request.get_json(silent=True) or {}
    name = (data.get("name") or "").strip()
    email = (data.get("email") or "").strip().lower()
    password = data.get("password") or ""

    if not name or not email or not password:
        return jsonify({"error": "name, email, and password are required"}), 400

    password_hash = generate_password_hash(password)
    conn = get_db()
    cursor = conn.cursor()

    try:
        cursor.execute(
            """
            INSERT INTO users (name, email, password_hash)
            VALUES (%s, %s, %s)
            """,
            (name, email, password_hash),
        )
        conn.commit()
        user_id = cursor.lastrowid

    except mysql.connector.IntegrityError:
        conn.rollback()
        return jsonify({"error": "Email is already registered"}), 409

    finally:
        cursor.close()
        conn.close()

    session.clear()
    session["user_id"] = user_id
    return jsonify({"message": "Registered successfully"}), 201


@app.post("/api/login")
def login():
    data = request.get_json(silent=True) or {}
    email = (data.get("email") or "").strip().lower()
    password = data.get("password") or ""

    if not email or not password:
        return jsonify({"error": "email and password are required"}), 400

    conn = get_db()
    cursor = conn.cursor(dictionary=True)

    try:
        cursor.execute(
            "SELECT user_id, password_hash FROM users WHERE email = %s",
            (email,),
        )
        user = cursor.fetchone()
    finally:
        cursor.close()
        conn.close()

    if not user or not check_password_hash(user["password_hash"], password):
        return jsonify({"error": "Invalid credentials"}), 401

    session.clear()
    session["user_id"] = user["user_id"]
    return jsonify({"message": "Login successful"}), 200


@app.post("/api/logout")
def logout():
    session.clear()
    return jsonify({"message": "Logged out"}), 200


@app.get("/api/todos")
def list_todos():
    user_id, error_response, status = require_auth()
    if error_response:
        return error_response, status

    conn = get_db()
    cursor = conn.cursor(dictionary=True)

    try:
        cursor.execute(
            """
            SELECT todo_id, title, is_done, created_at, updated_at
            FROM todos
            WHERE user_id = %s
            ORDER BY todo_id DESC
            """,
            (user_id,),
        )
        todos = cursor.fetchall()
    finally:
        cursor.close()
        conn.close()

    return jsonify([
        {
            "id": todo["todo_id"],
            "title": todo["title"],
            "is_done": bool(todo["is_done"]),
            "created_at": str(todo["created_at"]),
            "updated_at": str(todo["updated_at"]),
        }
        for todo in todos
    ])


@app.post("/api/todos")
def create_todo():
    user_id, error_response, status = require_auth()
    if error_response:
        return error_response, status

    data = request.get_json(silent=True) or {}
    title = (data.get("title") or "").strip()

    if not title:
        return jsonify({"error": "title is required"}), 400

    conn = get_db()
    cursor = conn.cursor(dictionary=True)

    try:
        cursor.execute(
            "INSERT INTO todos (user_id, title, is_done) VALUES (%s, %s, 0)",
            (user_id, title),
        )
        conn.commit()
        todo_id = cursor.lastrowid

        cursor.execute(
            """
            SELECT todo_id, title, is_done, created_at, updated_at
            FROM todos
            WHERE todo_id = %s AND user_id = %s
            """,
            (todo_id, user_id),
        )
        todo = cursor.fetchone()
    finally:
        cursor.close()
        conn.close()

    return jsonify({
        "id": todo["todo_id"],
        "title": todo["title"],
        "is_done": bool(todo["is_done"]),
        "created_at": str(todo["created_at"]),
        "updated_at": str(todo["updated_at"]),
    }), 201


@app.put("/api/todos/<int:todo_id>")
def update_todo(todo_id):
    user_id, error_response, status = require_auth()
    if error_response:
        return error_response, status

    data = request.get_json(silent=True) or {}
    title = data.get("title")
    is_done = data.get("is_done")

    if title is None and is_done is None:
        return jsonify({"error": "Nothing to update"}), 400

    fields = []
    values = []

    if title is not None:
        cleaned_title = str(title).strip()

        if not cleaned_title:
            return jsonify({"error": "title cannot be empty"}), 400

        fields.append("title = %s")
        values.append(cleaned_title)

    if is_done is not None:
        if not isinstance(is_done, bool):
            return jsonify({"error": "is_done must be true or false"}), 400

        fields.append("is_done = %s")
        values.append(1 if is_done else 0)

    values.extend([todo_id, user_id])

    conn = get_db()
    cursor = conn.cursor(dictionary=True)

    try:
        cursor.execute(
            f"""
            UPDATE todos
            SET {", ".join(fields)}
            WHERE todo_id = %s AND user_id = %s
            """,
            values,
        )

        if cursor.rowcount == 0:
            cursor.execute(
                "SELECT todo_id FROM todos WHERE todo_id = %s AND user_id = %s",
                (todo_id, user_id),
            )
            if not cursor.fetchone():
                return jsonify({"error": "Todo not found"}), 404

        conn.commit()

        cursor.execute(
            """
            SELECT todo_id, title, is_done, created_at, updated_at
            FROM todos
            WHERE todo_id = %s AND user_id = %s
            """,
            (todo_id, user_id),
        )
        todo = cursor.fetchone()
    finally:
        cursor.close()
        conn.close()

    return jsonify({
        "id": todo["todo_id"],
        "title": todo["title"],
        "is_done": bool(todo["is_done"]),
        "created_at": str(todo["created_at"]),
        "updated_at": str(todo["updated_at"]),
    })


@app.delete("/api/todos/<int:todo_id>")
def delete_todo(todo_id):
    user_id, error_response, status = require_auth()
    if error_response:
        return error_response, status

    conn = get_db()
    cursor = conn.cursor()

    try:
        cursor.execute(
            "DELETE FROM todos WHERE todo_id = %s AND user_id = %s",
            (todo_id, user_id),
        )

        if cursor.rowcount == 0:
            return jsonify({"error": "Todo not found"}), 404

        conn.commit()
    finally:
        cursor.close()
        conn.close()

    return jsonify({"message": "Todo deleted"}), 200


if __name__ == "__main__":
    app.run(debug=os.getenv("FLASK_DEBUG", "false").lower() == "true")
