import sqlite3
import hashlib

# -----------------------------
# DATABASE CONNECTION
# -----------------------------
conn = sqlite3.connect("epi_app.db", check_same_thread=False)
c = conn.cursor()

# -----------------------------
# CREATE TABLES
# -----------------------------
c.execute("""
CREATE TABLE IF NOT EXISTS users (
    username TEXT PRIMARY KEY,
    password TEXT
)
""")

c.execute("""
CREATE TABLE IF NOT EXISTS results (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT,
    analysis TEXT,
    result TEXT
)
""")

conn.commit()

# -----------------------------
# PASSWORD HASHING
# -----------------------------
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

# -----------------------------
# REGISTER USER
# -----------------------------
def register_user(username, password):
    try:
        hashed = hash_password(password)
        c.execute("INSERT INTO users (username, password) VALUES (?, ?)", (username, hashed))
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False

# -----------------------------
# LOGIN USER
# -----------------------------
def login_user(username, password):
    hashed = hash_password(password)
    c.execute("SELECT username FROM users WHERE username=? AND password=?", (username, hashed))
    return c.fetchone()

# -----------------------------
# SAVE RESULTS
# -----------------------------
def save_result(username, analysis, result):
    c.execute("INSERT INTO results (username, analysis, result) VALUES (?, ?, ?)",
              (username, analysis, result))
    conn.commit()

# -----------------------------
# GET USER RESULTS
# -----------------------------
def get_results(username):
    c.execute("SELECT analysis, result FROM results WHERE username=?", (username,))
    return c.fetchall()