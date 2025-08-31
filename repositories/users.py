from datetime import datetime
from core.db import get_conn
from core.security import hash_password

def fetch_user(username: str):
    with get_conn() as conn:
        cur = conn.execute(
            "SELECT id, username, password_hash, role, active, created_at FROM users WHERE username = ?",
            (username,)
        )
        r = cur.fetchone()
        if not r:
            return None
        return {
            "id": r[0], "username": r[1], "password_hash": r[2],
            "role": r[3], "active": bool(r[4]), "created_at": r[5]
        }

def list_users():
    with get_conn() as conn:
        cur = conn.execute("SELECT id, username, role, active, created_at FROM users ORDER BY id ASC")
        return [
            {"id": r[0], "username": r[1], "role": r[2], "active": bool(r[3]), "created_at": r[4]}
            for r in cur.fetchall()
        ]

def create_user(username: str, password: str, role: str = "user", active: bool = True):
    with get_conn() as conn:
        conn.execute(
            "INSERT INTO users (username, password_hash, role, active, created_at) VALUES (?, ?, ?, ?, ?)",
            (username, hash_password(password), role, 1 if active else 0, datetime.utcnow().isoformat())
        )
        conn.commit()

def update_user_active(username: str, active: bool):
    with get_conn() as conn:
        cur = conn.execute("UPDATE users SET active = ? WHERE username = ?", (1 if active else 0, username))
        conn.commit()
        return cur.rowcount > 0

def reset_password(username: str, new_password: str):
    with get_conn() as conn:
        cur = conn.execute(
            "UPDATE users SET password_hash = ? WHERE username = ?",
            (hash_password(new_password), username)
        )
        conn.commit()
        return cur.rowcount > 0