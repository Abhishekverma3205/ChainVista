from flask import Flask, request, jsonify
from flask_cors import CORS
import os
import sqlite3
import psycopg2
from psycopg2.extras import RealDictCursor

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})

# -------------------------------
# DATABASE CONFIG
# -------------------------------

DATABASE_URL = os.environ.get("DATABASE_URL")

# Decide DB type
USE_POSTGRES = DATABASE_URL is not None

# -------------------------------
# CONNECTION
# -------------------------------

def get_db_connection():
    if USE_POSTGRES:
        conn = psycopg2.connect(DATABASE_URL, cursor_factory=RealDictCursor)
        return conn
    else:
        conn = sqlite3.connect("chainvista.db")
        conn.row_factory = sqlite3.Row
        return conn


# -------------------------------
# INIT DB
# -------------------------------

def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()

    if USE_POSTGRES:
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id SERIAL PRIMARY KEY,
                username TEXT UNIQUE,
                password TEXT
            );
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS transactions (
                id SERIAL PRIMARY KEY,
                user_id INTEGER,
                amount REAL,
                type TEXT,
                description TEXT,
                date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)
    else:
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE,
                password TEXT
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS transactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                amount REAL,
                type TEXT,
                description TEXT,
                date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

    conn.commit()
    conn.close()


# Initialize DB (IMPORTANT)
init_db()


# -------------------------------
# HOME
# -------------------------------
@app.route("/")
def home():
    return jsonify({"message": "Backend running 🚀"})


# -------------------------------
# REGISTER
# -------------------------------
@app.route("/register", methods=["POST"])
def register():
    data = request.json
    username = data.get("username")
    password = data.get("password")

    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        cursor.execute(
            "INSERT INTO users (username, password) VALUES (%s, %s)" if USE_POSTGRES else
            "INSERT INTO users (username, password) VALUES (?, ?)",
            (username, password)
        )
        conn.commit()
        return jsonify({"message": "User registered"})
    except Exception as e:
        return jsonify({"error": "Username already exists"}), 400
    finally:
        conn.close()


# -------------------------------
# LOGIN
# -------------------------------
@app.route("/login", methods=["POST"])
def login():
    data = request.json
    username = data.get("username")
    password = data.get("password")

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute(
        "SELECT * FROM users WHERE username=%s AND password=%s" if USE_POSTGRES else
        "SELECT * FROM users WHERE username=? AND password=?",
        (username, password)
    )

    user = cursor.fetchone()
    conn.close()

    if user:
        return jsonify({
            "message": "Login successful",
            "user_id": user["id"] if USE_POSTGRES else user["id"]
        })
    else:
        return jsonify({"error": "Invalid credentials"}), 401


# -------------------------------
# ADD TRANSACTION
# -------------------------------
@app.route("/add_transaction", methods=["POST"])
def add_transaction():
    data = request.json
    user_id = data.get("user_id")
    amount = data.get("amount")
    t_type = data.get("type")
    description = data.get("description")

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute(
        """INSERT INTO transactions (user_id, amount, type, description)
           VALUES (%s, %s, %s, %s)""" if USE_POSTGRES else
        """INSERT INTO transactions (user_id, amount, type, description)
           VALUES (?, ?, ?, ?)""",
        (user_id, amount, t_type, description)
    )

    conn.commit()
    conn.close()

    return jsonify({"message": "Transaction added"})


# -------------------------------
# GET TRANSACTIONS
# -------------------------------
@app.route("/transactions/<int:user_id>", methods=["GET"])
def get_transactions(user_id):
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute(
        "SELECT * FROM transactions WHERE user_id=%s ORDER BY date DESC" if USE_POSTGRES else
        "SELECT * FROM transactions WHERE user_id=? ORDER BY date DESC",
        (user_id,)
    )

    transactions = cursor.fetchall()
    conn.close()

    return jsonify([dict(tx) for tx in transactions])


# -------------------------------
# DELETE TRANSACTION
# -------------------------------
@app.route("/delete_transaction/<int:id>", methods=["DELETE"])
def delete_transaction(id):
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute(
        "DELETE FROM transactions WHERE id=%s" if USE_POSTGRES else
        "DELETE FROM transactions WHERE id=?",
        (id,)
    )

    conn.commit()
    conn.close()

    return jsonify({"message": "Deleted"})


# -------------------------------
# RUN SERVER (LOCAL ONLY)
# -------------------------------
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
