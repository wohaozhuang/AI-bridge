import sqlite3
import hashlib
from datetime import datetime

DB_NAME = "users.db"


def get_conn():
    return sqlite3.connect(DB_NAME)


def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()


def init_db():
    conn = get_conn()
    c = conn.cursor()

    c.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL,
        role TEXT DEFAULT 'user',
        created_at TEXT
    )
    """)

    c.execute("""
    CREATE TABLE IF NOT EXISTS generations (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT NOT NULL,
        model TEXT NOT NULL,
        prompt TEXT NOT NULL,
        result TEXT,
        created_at TEXT
    )
    """)

    admin_password = hash_password("123456")

    c.execute("""
    INSERT OR IGNORE INTO users (username, password, role, created_at)
    VALUES (?, ?, ?, ?)
    """, ("admin", admin_password, "admin", datetime.now().strftime("%Y-%m-%d %H:%M:%S")))

    conn.commit()
    conn.close()


def register_user(username, password):
    conn = get_conn()
    c = conn.cursor()

    try:
        c.execute("""
        INSERT INTO users (username, password, role, created_at)
        VALUES (?, ?, ?, ?)
        """, (
            username,
            hash_password(password),
            "user",
            datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        ))
        conn.commit()
        return True, "注册成功"
    except sqlite3.IntegrityError:
        return False, "用户名已存在"
    finally:
        conn.close()


def login_user(username, password):
    conn = get_conn()
    c = conn.cursor()

    c.execute("""
    SELECT username, role FROM users
    WHERE username = ? AND password = ?
    """, (username, hash_password(password)))

    user = c.fetchone()
    conn.close()

    if user:
        return True, user[1]
    return False, None


def save_generation(username, model, prompt, result):
    conn = get_conn()
    c = conn.cursor()

    c.execute("""
    INSERT INTO generations (username, model, prompt, result, created_at)
    VALUES (?, ?, ?, ?, ?)
    """, (
        username,
        model,
        prompt,
        str(result),
        datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    ))

    conn.commit()
    conn.close()


def get_my_generations(username):
    conn = get_conn()
    c = conn.cursor()

    c.execute("""
    SELECT model, prompt, result, created_at
    FROM generations
    WHERE username = ?
    ORDER BY id DESC
    """, (username,))

    rows = c.fetchall()
    conn.close()
    return rows


def get_all_generations():
    conn = get_conn()
    c = conn.cursor()

    c.execute("""
    SELECT username, model, prompt, result, created_at
    FROM generations
    ORDER BY id DESC
    """)

    rows = c.fetchall()
    conn.close()
    return rows