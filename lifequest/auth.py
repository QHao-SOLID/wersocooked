import functools
import re
from hashlib import sha256
from flask import session, redirect, url_for, flash

def hash_password(password):
    return sha256(password.encode()).hexdigest()

def login_user(username, password):
    from db import get_db
    conn = get_db()
    user = conn.execute("SELECT * FROM users WHERE username = ?", (username,)).fetchone()
    conn.close()
    if user and user["password_hash"] == hash_password(password):
        session["user_id"] = user["id"]
        session["username"] = user["username"]
        return True
    return False

def register_user(username, email, password, avatar=""):
    from db import get_db
    if len(password) < 4:
        return False, "Password too short"
    if not re.match(r"^[a-zA-Z0-9_]{3,20}$", username):
        return False, "Username must be 3-20 alphanumeric characters"
    if not avatar:
        avatar = "🧑"
    conn = get_db()
    try:
        conn.execute(
            "INSERT INTO users (username, email, password_hash) VALUES (?, ?, ?)",
            (username, email, hash_password(password)),
        )
        conn.commit()
        user = conn.execute("SELECT * FROM users WHERE username = ?", (username,)).fetchone()
        conn.execute(
            "INSERT INTO player_profiles (user_id, avatar) VALUES (?, ?)", (user["id"], avatar)
        )
        conn.commit()
        conn.close()
        return True, "Account created"
    except Exception as e:
        conn.close()
        return False, str(e)

def login_required(f):
    @functools.wraps(f)
    def decorated(*args, **kwargs):
        if "user_id" not in session:
            flash("Please log in first", "danger")
            return redirect(url_for("login"))
        return f(*args, **kwargs)
    return decorated
