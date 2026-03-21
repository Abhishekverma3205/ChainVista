from flask import Flask, request, jsonify
from flask_cors import CORS
import sqlite3
import os

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})

# Database path (safe for Render)
DB_PATH = os.path.join(os.getcwd(), "chainvista.db")


# -------------------------------
# Database Connection
# -------------------------------
def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


# -------------------------------
# Initialize Database
# -------------------------------
def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()

    # Users Table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE,
            password TEXT
        )
    """)

    # Transactions Table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            amount REAL,
            type TEXT,
            description TEXT,
            date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(user_id) REFERENCES users(id)
        )
    """)

    conn.commit()
    conn.close()


# Run DB initialization (IMPORTANT for Render)
init_db()


# -------------------------------
# Routes
# -------------------------------

@app.route("/")
def home():
    return jsonify({"message": "Backend is running 🚀"})


# -------------------------------
# Register
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
            "INSERT INTO users (username, password) VALUES (?, ?)",
            (username, password)
        )
        conn.commit()
        return jsonify({"message": "User registered successfully"})
    except sqlite3.IntegrityError:
        return jsonify({"error": "Username already exists"}), 400
    finally:
        conn.close()


# -------------------------------
# Login
# -------------------------------
@app.route("/login", methods=["POST"])
def login():
    data = request.json
    username = data.get("username")
    password = data.get("password")

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute(
        "SELECT * FROM users WHERE username=? AND password=?",
        (username, password)
    )
    user = cursor.fetchone()
    conn.close()

    if user:
        return jsonify({"message": "Login successful", "user_id": user["id"]})
    else:
        return jsonify({"error": "Invalid credentials"}), 401


# -------------------------------
# Add Transaction
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

    cursor.execute("""
        INSERT INTO transactions (user_id, amount, type, description)
        VALUES (?, ?, ?, ?)
    """, (user_id, amount, t_type, description))

    conn.commit()
    conn.close()

    return jsonify({"message": "Transaction added"})


# -------------------------------
# Get Transactions
# -------------------------------
@app.route("/transactions/<int:user_id>", methods=["GET"])
def get_transactions(user_id):
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute(
        "SELECT * FROM transactions WHERE user_id=? ORDER BY date DESC",
        (user_id,)
    )
    transactions = cursor.fetchall()
    conn.close()

    return jsonify([dict(tx) for tx in transactions])


# -------------------------------
# Delete Transaction
# -------------------------------
@app.route("/delete_transaction/<int:id>", methods=["DELETE"])
def delete_transaction(id):
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("DELETE FROM transactions WHERE id=?", (id,))
    conn.commit()
    conn.close()

    return jsonify({"message": "Transaction deleted"})


# -------------------------------
# Run Server (for local only)
# -------------------------------
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
