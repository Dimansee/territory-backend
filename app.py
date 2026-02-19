from flask import Flask, request, jsonify
from flask_cors import CORS
import sqlite3
from datetime import datetime
import os

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})

DB = "database.db"

# -------------------------
# INIT DATABASE + MIGRATION
# -------------------------

def init_db():
    conn = sqlite3.connect(DB)
    c = conn.cursor()

    c.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE
    )
    """)

    # Safe column migration
    for column in ["bio TEXT", "phone TEXT", "hometown TEXT"]:
        try:
            c.execute(f"ALTER TABLE users ADD COLUMN {column}")
        except:
            pass

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

# -------------------------
# ROUTES
# -------------------------

@app.route("/")
def home():
    return "Backend running"

# LOGIN
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


# UPDATE PROFILE
@app.route("/update_profile", methods=["POST"])
def update_profile():
    data = request.json

    conn = sqlite3.connect(DB)
    c = conn.cursor()

    c.execute("""
        UPDATE users
        SET bio=?, phone=?, hometown=?
        WHERE id=?
    """, (
        data.get("bio"),
        data.get("phone"),
        data.get("hometown"),
        data.get("user_id")
    ))

    conn.commit()
    conn.close()

    return jsonify({"status": "profile updated"})


# GET PROFILE
@app.route("/get_profile/<int:user_id>")
def get_profile(user_id):
    conn = sqlite3.connect(DB)
    c = conn.cursor()

    c.execute("""
        SELECT username, bio, phone, hometown
        FROM users WHERE id=?
    """, (user_id,))

    user = c.fetchone()
    conn.close()

    if user:
        return jsonify({
            "username": user[0],
            "bio": user[1],
            "phone": user[2],
            "hometown": user[3]
        })
    else:
        return jsonify({})


# CAPTURE TERRITORY
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
    """, (
        block_id,
        user_id,
        datetime.now(),
        user_id,
        datetime.now()
    ))

    conn.commit()
    conn.close()

    return jsonify({"status": "captured"})


# GET ALL TERRITORIES
@app.route("/territories")
def territories():
    conn = sqlite3.connect(DB)
    c = conn.cursor()

    c.execute("SELECT block_id, owner_id FROM territory_blocks")
    rows = c.fetchall()

    conn.close()

    return jsonify([
        {"block_id": r[0], "owner_id": r[1]}
        for r in rows
    ])


# LEADERBOARD
@app.route("/leaderboard")
def leaderboard():
    conn = sqlite3.connect(DB)
    c = conn.cursor()

    c.execute("""
        SELECT users.username, COUNT(territory_blocks.block_id) as total_blocks
        FROM users
        LEFT JOIN territory_blocks
        ON users.id = territory_blocks.owner_id
        GROUP BY users.id
        ORDER BY total_blocks DESC
    """)

    rows = c.fetchall()
    conn.close()

    return jsonify([
        {"username": r[0], "blocks": r[1]}
        for r in rows
    ])


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
