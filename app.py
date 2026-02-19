from flask import Flask, request, jsonify
from flask_cors import CORS
import sqlite3
from datetime import datetime
import os

app = Flask(__name__)
CORS(app)

DB = "database.db"

def init_db():
    conn = sqlite3.connect(DB)
    c = conn.cursor()

    c.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE
    )
    """)

    c.execute("""
    CREATE TABLE IF NOT EXISTS territory_blocks (
        block_id TEXT PRIMARY KEY,
        owner_id INTEGER,
        last_updated TEXT
    )
    """)

    conn.commit()
    conn.close()

init_db()


@app.route("/")
def home():
    return "Backend running"


@app.route("/login", methods=["POST"])
def login():
    username = request.json.get("username")

    conn = sqlite3.connect(DB)
    c = conn.cursor()

    c.execute("SELECT id FROM users WHERE username=?", (username,))
    user = c.fetchone()

    if user:
        user_id = user[0]
    else:
        c.execute("INSERT INTO users (username) VALUES (?)", (username,))
        conn.commit()
        user_id = c.lastrowid

    conn.close()
    return jsonify({"user_id": user_id})


@app.route("/capture", methods=["POST"])
def capture():
    data = request.json
    block_id = data["block_id"]
    user_id = data["user_id"]

    conn = sqlite3.connect(DB)
    c = conn.cursor()

    c.execute("""
        INSERT INTO territory_blocks (block_id, owner_id, last_updated)
        VALUES (?, ?, ?)
        ON CONFLICT(block_id)
        DO UPDATE SET owner_id=?, last_updated=?
    """, (block_id, user_id, datetime.now(), user_id, datetime.now()))

    conn.commit()
    conn.close()

    return jsonify({"status": "captured"})


@app.route("/territories", methods=["GET"])
def territories():
    conn = sqlite3.connect(DB)
    c = conn.cursor()

    c.execute("SELECT block_id, owner_id FROM territory_blocks")
    rows = c.fetchall()

    conn.close()

    result = [{"block_id": r[0], "owner_id": r[1]} for r in rows]
    return jsonify(result)


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
